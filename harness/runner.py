#!/usr/bin/env python3
"""
BP-02 Evaluation & Backtest Harness — Runner
============================================

Runs each task in the battery N times against a deployed Agent-Zero container,
records pass/fail against a goal-state verifier, and writes an append-only JSONL
results log. report.py then computes pass^1 and pass^k.

Design (per Opus's BP-02 kickoff — decisions already made):
  - pass^k, not pass@1: consistency matters more than average success (tau-bench).
  - Verifiers check OUTCOMES, not process.
  - Environment reset between trials so each trial is independent.
  - Results are append-only JSONL.
  - The harness is a TOOL that runs OUTSIDE the agent (calls A0's /api/api_message).
    The agent does not know it is being tested.

Implementation decision (mine, flagged to Opus): the verifier signature is
  verify(container: str, response: str, context_id: str) -> tuple[bool, str]
i.e. extended to also receive the agent's response. Opus's illustrative signature
was verify(container) — state-only — which fits tasks that MUTATE the environment.
The starter tasks (T01/T03) are reporting tasks whose outcome IS the response, so
the verifier needs it. Mutation-task verifiers can simply ignore response/context_id
and inspect container state. The extended signature is a superset.

Usage:
  python runner.py                 # run the full battery from config.json
  python runner.py --task T03      # run one task
  python runner.py --n 1           # override N (quick smoke run)
  python runner.py --dry-run       # print the plan, don't call the agent
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HARNESS_DIR, "config.json")
RESULTS_DIR = os.path.join(HARNESS_DIR, "results")

# verifiers/ must be importable as a package
if HARNESS_DIR not in sys.path:
    sys.path.insert(0, HARNESS_DIR)


# ── Container access helpers (host-side; subprocess calls docker.exe directly) ──

def get_port(container: str) -> str | None:
    """Return the host port mapped to the container's 80/tcp, or None."""
    try:
        out = subprocess.run(["docker", "port", container, "80"],
                             capture_output=True, text=True, timeout=15)
        # lines like: 0.0.0.0:32774  /  [::]:32774
        for line in out.stdout.splitlines():
            line = line.strip()
            if ":" in line:
                return line.rsplit(":", 1)[1].strip()
    except Exception as e:
        print(f"[runner] get_port({container}) failed: {e}", file=sys.stderr)
    return None


def get_token(container: str) -> str | None:
    """Compute the container's API auth token (stable per runtime_id)."""
    code = ("import sys; sys.path.insert(0,'/a0/python'); sys.path.insert(0,'/a0'); "
            "from helpers.settings import create_auth_token; print(create_auth_token())")
    try:
        out = subprocess.run(
            ["docker", "exec", container, "/opt/venv-a0/bin/python3", "-c", code],
            capture_output=True, text=True, timeout=30)
        for line in out.stdout.splitlines():
            line = line.strip()
            if line and " " not in line:
                return line
    except Exception as e:
        print(f"[runner] get_token({container}) failed: {e}", file=sys.stderr)
    return None


def container_up(container: str) -> bool:
    try:
        out = subprocess.run(["docker", "ps", "--format", "{{.Names}}"],
                             capture_output=True, text=True, timeout=15)
        return container in out.stdout.split()
    except Exception:
        return False


# ── Task execution ──

def reset_env(container: str, mode: str) -> None:
    """Reset the environment between trials so each trial is independent.

    Modes:
      "none"           — no-op (correct for read-only/reporting tasks)
      "restart"        — docker restart + settle wait (for tasks that mutate state)
      "script:/path"   — run a host command (workspace restore, etc.)
      "exec:<cmd>"     — run a shell command INSIDE the container

    `exec:` exists for Pool B's HB-08, which creates one artifact that must be removed
    between trials. `restart` would do it at the cost of a container bounce plus an
    8-second settle per trial, and `script:` runs host-side with shell=True, so it
    would need its own `docker exec` and would land on the MSYS path-translation seam
    (wiring seam #30) where a mangled path fails silently. A first-class in-container
    mode avoids both, and MSYS_NO_PATHCONV is set explicitly here for the same reason.
    """
    if not mode or mode == "none":
        return
    if mode == "restart":
        subprocess.run(["docker", "restart", container], capture_output=True, timeout=120)
        time.sleep(8)  # settle
        return
    if mode.startswith("exec:"):
        cmd = mode.split(":", 1)[1]
        env = dict(os.environ, MSYS_NO_PATHCONV="1")
        r = subprocess.run(["docker", "exec", container, "sh", "-lc", cmd],
                           capture_output=True, text=True, timeout=120, env=env)
        if r.returncode != 0:
            # A reset that silently fails makes every subsequent trial dirty, and the
            # results look like agent behaviour rather than a broken fixture.
            print(f"[runner] reset exec FAILED rc={r.returncode}: "
                  f"{(r.stderr or '').strip()[:160]}", file=sys.stderr)
        return
    if mode.startswith("script:"):
        path = mode.split(":", 1)[1]
        subprocess.run(path, shell=True, capture_output=True, timeout=120)
        return
    print(f"[runner] unknown reset mode '{mode}' — treating as none", file=sys.stderr)


def send_task(port: str, token: str, prompt: str, timeout: int) -> dict:
    """POST the task to /api/api_message and block until the agent finishes.

    api_message is synchronous — it returns the agent's final response after the
    full message loop completes. Returns {context_id, response, duration, error}.
    """
    url = f"http://localhost:{port}/api/api_message"
    body = json.dumps({"message": prompt}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-API-KEY", token)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {
            "context_id": data.get("context_id", ""),
            "response": data.get("response", ""),
            "duration": round(time.time() - t0, 2),
            "error": None,
        }
    except urllib.error.HTTPError as e:
        return {"context_id": "", "response": "", "duration": round(time.time() - t0, 2),
                "error": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"}
    except Exception as e:
        return {"context_id": "", "response": "", "duration": round(time.time() - t0, 2),
                "error": f"{type(e).__name__}: {e}"}


def run_verifier(name: str, container: str, response: str, context_id: str):
    """Dynamically import verifiers.<name> and run verify(container, response, context_id)."""
    try:
        mod = importlib.import_module(f"verifiers.{name}")
        importlib.reload(mod)
        passed, notes = mod.verify(container, response, context_id)
        return bool(passed), str(notes)
    except Exception as e:
        return False, f"verifier-error: {type(e).__name__}: {e}"


# ── Results ──

def append_result(results_path: str, rec: dict) -> None:
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec) + "\n")


# ── Main ──

def main():
    ap = argparse.ArgumentParser(description="BP-02 evaluation harness runner")
    ap.add_argument("--task", default=None, help="run only this task id")
    ap.add_argument("--n", type=int, default=None, help="override N for all tasks")
    ap.add_argument("--container", default=None, help="override target container")
    ap.add_argument("--dry-run", action="store_true", help="print plan, don't call the agent")
    ap.add_argument("--run-id", default=None, help="results filename stamp (default: passed-in or 'manual')")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)

    default_container = args.container or cfg.get("default_container", "exocortex_v16")
    timeout = cfg.get("api_timeout_seconds", 300)
    tasks = cfg["tasks"]
    if args.task:
        tasks = [t for t in tasks if t["id"] == args.task]
        if not tasks:
            print(f"[runner] no task '{args.task}' in battery"); return 1

    run_id = args.run_id or "manual"
    results_path = os.path.join(RESULTS_DIR, f"results_{run_id}.jsonl")

    # Resolve container access once per container
    containers = {}
    for t in tasks:
        c = t.get("container", default_container)
        if c not in containers:
            containers[c] = {"up": container_up(c)}
            if containers[c]["up"] and not args.dry_run:
                containers[c]["port"] = get_port(c)
                containers[c]["token"] = get_token(c)

    print(f"=== BP-02 harness run '{run_id}' ===")
    print(f"results -> {results_path}\n")

    summary = {}
    for t in tasks:
        c = t.get("container", default_container)
        n = args.n if args.n is not None else t.get("N", cfg.get("default_N", 5))
        cinfo = containers[c]
        print(f"--- {t['id']}  (container={c}, N={n}, verifier={t['verifier']}) ---")

        if not cinfo["up"]:
            print(f"  SKIP: container {c} is not running.")
            summary[t["id"]] = {"available": False}
            continue
        if args.dry_run:
            print(f"  DRY-RUN prompt: {t['prompt'][:90]}...")
            continue
        if not cinfo.get("port") or not cinfo.get("token"):
            print(f"  SKIP: could not resolve port/token for {c}.")
            summary[t["id"]] = {"available": False}
            continue

        passes = 0
        for trial in range(1, n + 1):
            reset_env(c, t.get("reset", "none"))
            r = send_task(cinfo["port"], cinfo["token"], t["prompt"], timeout)
            if r["error"]:
                passed, notes = False, f"api-error: {r['error']}"
            else:
                passed, notes = run_verifier(t["verifier"], c, r["response"], r["context_id"])
            passes += 1 if passed else 0
            rec = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "run_id": run_id,
                "task_id": t["id"],
                "trial": trial,
                "passed": passed,
                "duration_s": r["duration"],
                "container": c,
                "context_id": r["context_id"],
                "response_chars": len(r["response"]),
                "response_excerpt": (r["response"] or "")[:800],
                "notes": notes,
                "steps_taken": None,   # best-effort; populated by a future context-reader
                "tokens_used": None,
            }
            append_result(results_path, rec)
            mark = "PASS" if passed else "FAIL"
            print(f"  trial {trial}/{n}: {mark}  ({r['duration']}s)  {notes[:100]}")
        summary[t["id"]] = {"available": True, "passes": passes, "n": n,
                            "pass_at_1": round(passes / n, 3)}

    print("\n=== run complete ===")
    for tid, s in summary.items():
        if not s.get("available"):
            print(f"  {tid}: unavailable")
        else:
            print(f"  {tid}: {s['passes']}/{s['n']} passed (pass@1={s['pass_at_1']})")
    print(f"\nRun report:  python report.py --run-id {run_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
