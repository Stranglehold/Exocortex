#!/usr/bin/env python3
"""Smoke test a FreeToken server: readiness, generation, reasoning split, native tool
calls, throughput, and whether an A0 container can actually reach it.

    python scripts/freetoken_smoke.py [--port 1235] [--model qwen3.8-27b]

The last check is the one that decides whether this stack is usable at all here.
FreeToken runs inside WSL2 Ubuntu; A0 runs in Docker Desktop's own WSL2 distro and reaches
the host via host.docker.internal. Whether that routes through has never been verified,
and this project has been bitten by WSL2 networking before.
"""

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:%d"


def post(port, path, payload, timeout=300):
    req = urllib.request.Request((BASE % port) + path,
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode()), time.time() - t0


def get(port, path, timeout=15):
    with urllib.request.urlopen((BASE % port) + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def wait_ready(port, limit=1800):
    """Poll /health until it stops reporting 'loading'. FreeToken 503s on completions
    while the engine warms, so hitting it early proves nothing."""
    t0 = time.time()
    last = None
    while time.time() - t0 < limit:
        try:
            h = get(port, "/health")
            st = h.get("status")
            if st != last:
                p = h.get("progress") or {}
                extra = ""
                if p.get("total_bytes"):
                    extra = " %.1f/%.1f GB" % (p.get("done_bytes", 0) / 1e9,
                                               p["total_bytes"] / 1e9)
                print("   [%4.0fs] status=%s phase=%s%s"
                      % (time.time() - t0, st, h.get("phase"), extra), flush=True)
                last = st
            if st in ("ready", "ok", "running", "serving"):
                return True, time.time() - t0
        except Exception as e:
            print("   health error: %s" % type(e).__name__, flush=True)
        time.sleep(10)
    return False, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=1235)
    ap.add_argument("--model", default="qwen3.8-27b")
    ap.add_argument("--container", default="agent-zero-v2")
    a = ap.parse_args()
    P, M = a.port, a.model

    print("=== 0. wait for ready ===", flush=True)
    ok, secs = wait_ready(P)
    if not ok:
        print("   NEVER BECAME READY after %.0fs — stopping." % secs)
        return 1
    print("   ready after %.0fs" % secs, flush=True)

    print("\n=== 1. minimal completion ===", flush=True)
    try:
        d, s = post(P, "/v1/chat/completions",
                    {"model": M, "max_tokens": 64,
                     "messages": [{"role": "user", "content": "Reply with exactly: ok"}]})
        m = d["choices"][0]["message"]
        print("   %.1fs | content=%r" % (s, (m.get("content") or "")[:80]))
        rc = m.get("reasoning_content")
        print("   reasoning_content: %s (%d chars) <- separated, as the model card describes"
              % (rc is not None, len(rc or "")))
        print("   usage:", d.get("usage"))
    except Exception as e:
        print("   FAILED:", type(e).__name__, str(e)[:200])
        return 1

    print("\n=== 2. NATIVE tool_calls (the channel A0 does not currently use) ===", flush=True)
    tools = [{"type": "function", "function": {
        "name": "write_file",
        "description": "Write text to a file",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"},
                                      "content": {"type": "string"}},
                       "required": ["path", "content"]}}}]
    try:
        d, s = post(P, "/v1/chat/completions",
                    {"model": M, "tools": tools, "max_tokens": 400,
                     "messages": [{"role": "user",
                                   "content": "Write 'hello' to /tmp/a.txt. Use the tool."}]})
        m = d["choices"][0]["message"]
        tc = m.get("tool_calls")
        print("   %.1fs | tool_calls: %s" % (s, "YES" if tc else "no"))
        if tc:
            f = tc[0].get("function", {})
            print("   name=%s args=%s" % (f.get("name"), str(f.get("arguments"))[:100]))
            print("   -> emitted as a STRUCTURED field, not JSON inside content.")
            print("      A0 asks for JSON-in-content, which is what produced the prose-leak")
            print("      failure. This channel sidesteps it entirely.")
        else:
            print("   content=%r" % (m.get("content") or "")[:150])
    except Exception as e:
        print("   FAILED:", type(e).__name__, str(e)[:200])

    print("\n=== 3. throughput (baseline: llama.cpp ~35 tok/s decode) ===", flush=True)
    try:
        d, s = post(P, "/v1/chat/completions",
                    {"model": M, "max_tokens": 300, "temperature": 1.0,
                     "messages": [{"role": "user",
                                   "content": "Count from 1 to 100, one number per line."}]})
        u = d.get("usage") or {}
        out = u.get("completion_tokens") or 0
        print("   %.1fs | completion_tokens=%s -> %.1f tok/s%s"
              % (s, out, (out / s if s else 0),
                 "  (includes reasoning tokens if any)" if out else ""))
    except Exception as e:
        print("   FAILED:", type(e).__name__, str(e)[:200])

    print("\n=== 4. CAN A CONTAINER REACH IT? (the decisive one) ===", flush=True)
    # Three candidates, because "unreachable" and "wrong address" are different findings:
    #   host.docker.internal -> 192.168.65.254 here, Docker Desktop's gateway to Windows.
    #     WSL2 publishes the port on Windows LOOPBACK only (netstat showed 127.0.0.1:1235),
    #     so this may well be refused even though the server is healthy.
    #   172.27.151.86        -> the WSL Ubuntu VM directly (hostname -I). Different subnet
    #     from the container, so this only works if the host routes between them.
    #   172.17.0.1           -> the classic docker0 bridge gateway.
    for host in ("host.docker.internal", "172.27.151.86", "172.17.0.1"):
        cmd = ["docker", "exec", a.container, "sh", "-c",
               "curl -s -m 8 -o /dev/null -w '%%{http_code}' http://%s:%d/v1/models" % (host, P)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            code = (r.stdout or "").strip()
            verdict = "REACHABLE" if code == "200" else "NOT reachable (%s)" % (code or "no response")
            print("   %-24s %s" % (host, verdict))
        except Exception as e:
            print("   %-24s error: %s" % (host, type(e).__name__))
    print("   If neither works, FreeToken bound inside WSL2 Ubuntu is not visible to")
    print("   Docker Desktop's distro. Fix is the Ubuntu VM's IP (hostname -I) or a")
    print("   port proxy — NOT a launcher change.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
