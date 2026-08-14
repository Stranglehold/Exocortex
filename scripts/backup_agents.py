#!/usr/bin/env python3
"""backup_agents.py — durable, incremental, READ-ONLY snapshots of each agent's data.

WHY THIS EXISTS
---------------
All Agent-Zero containers run with ZERO volume mounts: every agent's wiki, memory
(FAISS), journals, skills, chats and self-authored identity doc live in the container's
writable layer. A single `docker rm` is total, unrecoverable loss. Volume mounts were
considered and rejected — they require recreating all three containers and protect
against only ONE failure (container removal). Backups additionally cover agent
self-deletion, torn writes, corruption and disk failure.

WHY TARBALLS AND NOT A FILE MIRROR
----------------------------------
The first implementation copied files onto the host with `docker cp`. It silently lost
Vek's ENTIRE workdir. Cause: the agents write ISO-8601 timestamps into filenames
(`..._baseline_2026-05-10T19:30:53Z.md`). Colons are legal on Linux and ILLEGAL on NTFS,
so `docker cp` aborted on the first such file — reporting one truncated warning while
skipping wiki, journals and the identity doc. Aporia had no colon filenames and looked
perfectly healthy, which is exactly how this would have gone unnoticed.

Capturing tar STREAMS avoids the host filesystem's naming rules entirely, preserves
permissions and byte-exact names, and restores cleanly into a Linux container. A backup
must store what the source actually contains, not what the backup host can represent.

SAFETY MODEL (structural, not promised)
---------------------------------------
1. READ-ONLY toward containers. Only three container operations are used —
   `docker inspect` (status), `docker exec` running `find`/`sha256sum`/`tar -c`
   (all read-only), and nothing else. There is deliberately NO code path here that
   writes into a container: no `docker cp` inward, no `rm`, no redirection.
2. RESTORE LIVES ELSEWHERE. Restoring is the dangerous direction, so it is a separate
   script that is never scheduled, requires an explicit target, and defaults to a
   throwaway container. Most data-loss incidents are a restore firing unexpectedly.
3. DELETION IS FENCED. The only deletes are retention sweeps, guarded by
   _assert_under_dest(), which refuses any path not inside the backup root.

LAYOUT
------
    <dest>/<agent>/full/<ts>.tar.gz       periodic full capture (also the first run)
    <dest>/<agent>/delta/<ts>.tar.gz      ONLY files changed since the last run
    <dest>/<agent>/<ts>.manifest.json     what changed, FAISS status, counts
    <dest>/<agent>/state.json             current signature (relpath -> size|mtime)

Incremental by design: deltas store only changed files, so history accumulates without
re-storing unchanged data. A full is taken on the first run and every FULL_EVERY runs so
a restore never needs to replay an unbounded delta chain.

FAISS CONSISTENCY
-----------------
`index.faiss` and `index.pkl` must be captured as a CONSISTENT PAIR — a torn copy looks
fine and restores broken, which is worse than no backup. The sha256 sidecar is verified
IN-CONTAINER before capture; a mismatch is recorded as DEGRADED rather than silently
accepted.

USAGE
    python scripts/backup_agents.py                  # all live agents
    python scripts/backup_agents.py --dry-run        # report the delta, write nothing
    python scripts/backup_agents.py --agent vek
    python scripts/backup_agents.py --full           # force a full capture
    python scripts/backup_agents.py --include-secrets
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys

DEFAULT_DEST = r"D:\Vibecode\Agent-Zero\_agent_backups"

AGENTS = {"aporia": "agent-zero-v2", "vek": "VekV2"}
RETIRED = {"v17": "exocortex_v17"}

SRC_ROOT = "/a0/usr"

# DENYLIST, deliberately — an allowlist backup silently misses data added later.
# The first version listed 6 paths and missed chats_archive (1 GB of conversation
# history), uploads (inter-agent letters), knowledge, ontology, swarmfish and oss.
# Capture everything under /a0/usr; exclude only what is regenerable, huge, or secret.
PRUNE = [
    ".time_travel",      # A0 file-version cache: 460 MB (Aporia) / 171 MB (Vek), regenerable
    "obsidian-runtime",  # runtime cache; the vault itself lives under obsidian/
    "logs",              # regenerable
    "downloads",         # transient
    "__pycache__", "*.pyc", "*.pyo", "node_modules", ".git",
]
SECRETS = [".env", "secrets.env"]   # note: the file is secrets.env, not .env, on v2

RETENTION_KEEP = 40      # archives kept per agent (fulls + deltas)
FULL_EVERY = 12          # force a full capture every N runs

_ENV = dict(os.environ, MSYS_NO_PATHCONV="1")


def _run(args, **kw):
    return subprocess.run(args, capture_output=True, env=_ENV, **kw)


def _assert_under_dest(path, dest):
    p, d = os.path.abspath(path), os.path.abspath(dest)
    if not (p == d or p.startswith(d + os.sep)):
        raise RuntimeError(f"REFUSING to delete outside backup root: {p!r}")
    if len(d) < 8:
        raise RuntimeError(f"backup root suspiciously short: {d!r}")


def _find_expr(include_secrets):
    """A single read-only find. Prune junk; optionally exclude secrets."""
    ex = list(PRUNE) + ([] if include_secrets else SECRETS)
    parts = []
    for pat in ex:
        parts.append(f'-name "{pat}" -prune -o')
    return " ".join(parts)


def remote_manifest(container, include_secrets):
    """relpath -> 'size|mtime', computed INSIDE the container (read-only)."""
    cmd = (f'cd {SRC_ROOT} 2>/dev/null || exit 0; '
           f'find . {_find_expr(include_secrets)} -type f -printf "%P|%s|%T@\\n" 2>/dev/null')
    r = _run(["docker", "exec", container, "bash", "-lc", cmd])
    man = {}
    for line in r.stdout.decode("utf-8", "replace").splitlines():
        try:
            p, size, mtime = line.rsplit("|", 2)
            man[p] = f"{size}|{int(float(mtime))}"
        except ValueError:
            continue
    return man


def faiss_status(container):
    """Verify the FAISS pair in-container before capture."""
    cmd = ('d=/a0/usr/memory/default; '
           '[ -f "$d/index.faiss" ] && [ -f "$d/index.pkl" ] || { echo ABSENT; exit 0; }; '
           '[ -f "$d/index.faiss.sha256" ] || { echo UNVERIFIED; exit 0; }; '
           'exp=$(cut -d" " -f1 "$d/index.faiss.sha256"); act=$(sha256sum "$d/index.faiss" | cut -d" " -f1); '
           '[ "$exp" = "$act" ] && echo OK || echo DEGRADED')
    r = _run(["docker", "exec", container, "bash", "-lc", cmd])
    return (r.stdout.decode("utf-8", "replace").strip() or "UNKNOWN").split()[-1]


def capture_tar(container, out_path, file_list=None, include_secrets=False):
    """Stream a tar.gz OUT of the container. file_list=None -> full capture."""
    if file_list is None:
        cmd = (f'cd {SRC_ROOT} && tar -czf - '
               + " ".join(f'--exclude="{p}"' for p in PRUNE + ([] if include_secrets else SECRETS))
               + " .")
        proc = _run(["docker", "exec", container, "bash", "-lc", cmd])
    else:
        listing = "\n".join(file_list)
        proc = subprocess.run(
            ["docker", "exec", "-i", container, "bash", "-lc", f"cd {SRC_ROOT} && tar -czf - -T -"],
            input=listing.encode("utf-8", "replace"), capture_output=True, env=_ENV)
    if proc.returncode != 0 or not proc.stdout:
        return None, (proc.stderr.decode("utf-8", "replace")[:120] if proc.stderr else "empty stream")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(proc.stdout)
    return len(proc.stdout), None


def backup_agent(label, container, dest, include_secrets, dry_run, force_full):
    print(f"\n=== {label} ({container}) ===", flush=True)
    if _run(["docker", "inspect", "-f", "{{.State.Status}}", container]).returncode != 0:
        print("  container not found — skipped")
        return None

    root = os.path.join(dest, label)
    state_path = os.path.join(root, "state.json")
    os.makedirs(root, exist_ok=True)

    new_man = remote_manifest(container, include_secrets)
    if not new_man:
        print("  manifest empty — aborting this agent (nothing captured)")
        return None
    fs = faiss_status(container)

    old = {}
    run_no = 0
    if os.path.exists(state_path):
        try:
            st = json.load(open(state_path, encoding="utf-8"))
            old, run_no = st.get("manifest", {}), int(st.get("run_no", 0))
        except Exception:
            pass

    added = sorted(k for k in new_man if k not in old)
    modified = sorted(k for k in new_man if k in old and new_man[k] != old[k])
    deleted = sorted(k for k in old if k not in new_man)
    changed = added + modified
    total_mb = sum(int(v.split("|")[0]) for v in new_man.values()) / (1 << 20)

    need_full = force_full or not old or (run_no % FULL_EVERY == 0)
    print(f"  files={len(new_man)} ({total_mb:.1f} MB) | +{len(added)} ~{len(modified)} -{len(deleted)} "
          f"| FAISS={fs} | {'FULL' if need_full else 'delta'}")

    if dry_run:
        print("  --dry-run: nothing written")
        return {"agent": label, "dry_run": True, "added": len(added),
                "modified": len(modified), "deleted": len(deleted), "faiss": fs}

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    written, kind = None, None
    if need_full:
        out = os.path.join(root, "full", f"{ts}.tar.gz")
        written, err = capture_tar(container, out, None, include_secrets)
        kind = "full"
    elif changed:
        out = os.path.join(root, "delta", f"{ts}.tar.gz")
        written, err = capture_tar(container, out, changed, include_secrets)
        kind = "delta"
    else:
        print("  no changes — nothing captured")
        json.dump({"run_no": run_no + 1, "manifest": new_man, "last_ts": ts},
                  open(state_path, "w", encoding="utf-8"))
        return {"agent": label, "files": len(new_man), "mb": round(total_mb, 1),
                "added": 0, "modified": 0, "deleted": len(deleted), "faiss": fs, "archive": None}

    if written is None:
        print(f"  CAPTURE FAILED ({err}) — state NOT advanced, will retry next run")
        return {"agent": label, "failed": True, "error": err, "faiss": fs}

    json.dump({"timestamp": ts, "agent": label, "container": container, "kind": kind,
               "bytes": written, "files_total": len(new_man),
               "added": added, "modified": modified, "deleted": deleted,
               "faiss": fs, "secrets_included": include_secrets},
              open(os.path.join(root, f"{ts}.manifest.json"), "w", encoding="utf-8"), indent=2)
    json.dump({"run_no": run_no + 1, "manifest": new_man, "last_ts": ts, "last_kind": kind},
              open(state_path, "w", encoding="utf-8"))
    print(f"  {kind} archive: {ts}.tar.gz ({written/(1<<20):.1f} MB)")

    # retention — the ONLY delete, fenced to the backup root
    arcs = []
    for sub in ("full", "delta"):
        d = os.path.join(root, sub)
        if os.path.isdir(d):
            arcs += [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".tar.gz")]
    arcs.sort(key=lambda p: os.path.basename(p))
    for victim in arcs[:-RETENTION_KEEP] if len(arcs) > RETENTION_KEEP else []:
        _assert_under_dest(victim, dest)
        os.remove(victim)
        print(f"  retention: pruned {os.path.basename(victim)}")

    return {"agent": label, "files": len(new_man), "mb": round(total_mb, 1),
            "added": len(added), "modified": len(modified), "deleted": len(deleted),
            "faiss": fs, "archive": f"{kind}/{ts}.tar.gz"}


def main():
    ap = argparse.ArgumentParser(description="Read-only incremental tar backups of agent data.")
    ap.add_argument("--dest", default=DEFAULT_DEST)
    ap.add_argument("--agent", action="append")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--full", action="store_true", help="force a full capture")
    ap.add_argument("--include-secrets", action="store_true", help="also capture .env (API keys)")
    a = ap.parse_args()

    known = dict(AGENTS); known.update(RETIRED)
    chosen = {k: v for k, v in known.items() if k in a.agent} if a.agent else dict(AGENTS)
    if not chosen:
        sys.exit(f"no matching agents. known: {sorted(known)}")

    os.makedirs(a.dest, exist_ok=True)
    print(f"backup root: {a.dest}")
    if not a.include_secrets:
        print("secrets (.env) EXCLUDED — pass --include-secrets to capture API keys")

    results = [r for r in (backup_agent(k, v, a.dest, a.include_secrets, a.dry_run, a.full)
                           for k, v in chosen.items()) if r]

    print("\n============ SUMMARY ============")
    for r in results:
        if r.get("failed"):
            print(f"  {r['agent']:<8} FAILED — {r['error']}")
        elif r.get("dry_run"):
            print(f"  {r['agent']:<8} DRY-RUN  +{r['added']} ~{r['modified']} -{r['deleted']}  FAISS={r['faiss']}")
        else:
            print(f"  {r['agent']:<8} {r['files']} files ({r['mb']} MB)  "
                  f"+{r['added']} ~{r['modified']} -{r['deleted']}  FAISS={r['faiss']}  "
                  f"archive={r['archive'] or 'none'}")
    bad = [r for r in results if r.get("faiss") == "DEGRADED"]
    if bad:
        print("\n  WARNING: FAISS pair DEGRADED for " + ", ".join(r["agent"] for r in bad) +
              " — a torn index restores broken while looking fine. Re-run when the agent is idle.")
    if any(r.get("failed") for r in results):
        sys.exit(1)


main()
