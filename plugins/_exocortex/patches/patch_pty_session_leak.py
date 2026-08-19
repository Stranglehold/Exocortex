#!/usr/bin/env python3
"""
patch_pty_session_leak.py — Exocortex post-update patch for an Agent-Zero core bug
=================================================================================

THE BUG (A0 v2.9, reproducible on demand)
-----------------------------------------
Every AgentContext that runs `code_execution` allocates a PTY master fd + a child
shell (`asyncio.create_subprocess_shell`) in
`plugins/_code_execution/helpers/tty_session.py`. The session is stored on the
agent (`code_execution_tool.py` -> `agent.set_data("_cet_state", ...)`), the agent
lives on the context, and **contexts are never destroyed**. Nothing ever calls
`TTYSession.close()`, so the PTY and the child leak — exactly one per context.

Measured on VekV2 (three api_message calls, one `echo` each, new context per call):

    baseline        ptmx=0  pidfds=0  threads=64
    after msg #1    ptmx=1  pidfds=1  threads=84
    after msg #2    ptmx=2  pidfds=2  threads=100
    after msg #3    ptmx=3  pidfds=3  threads=101

Because every idle cycle creates a fresh context, this is one leaked handle per
cycle. In the field: 30 cycles / 17 hours -> 38 handles, ~360 threads, and then a
TOTAL DEADLOCK — A0 serves its UI from a bounded worker pool, and once the pool is
consumed by blocked session threads, every request queues forever. `GET /health`
from *inside* the container returns nothing. A browser refresh cannot help; there
is no server left to answer. Observed twice, 2026-08-14 and 2026-08-18.

WHY THIS SHAPE OF FIX
---------------------
`TTYSession.close()` is CORRECT — it cancels the pump task, SIGTERM/SIGKILLs the
process group, waits, and releases the PTY master. The bug is not broken cleanup,
it is cleanup that is never invoked. So this patch does not rewrite close(); it
adds an idle reaper that CALLS it.

Two alternatives were tested against the live system and BOTH FAILED — do not
re-try them:
  * `POST /api/api_terminate_chat` returns {"success": true} and releases nothing
    (handle count unchanged). Chat deletion does not close the shell.
  * `code_execution_tool` with `reset` — no net reduction; `prepare_state`
    recreates a session on the next command.

WHY REAPING IS SAFE
-------------------
`code_execution_tool.py` already handles a dead session:

    if self.state.shells[session].session.is_terminated():
        await self.prepare_state(cfg, reset=True, session=session)

and `prepare_state` recreates a missing session on demand. `TTYSession.is_terminated()`
returns True once `_proc` is None or has a returncode — which is the state close()
leaves behind. So a reaped shell is transparently rebuilt on next use. The reaper
only touches sessions idle longer than the threshold, so an in-flight command is
never interrupted.

USAGE
-----
    python3 patch_pty_session_leak.py --check     # report status, change nothing
    python3 patch_pty_session_leak.py --apply     # apply (idempotent)
    python3 patch_pty_session_leak.py --revert    # restore from the .orig backup
    python3 patch_pty_session_leak.py --apply --idle-seconds 900

Idempotent: re-running --apply on a patched file is a no-op.
Reversible: --apply writes <target>.exocortex-orig once and never overwrites it.
Version-gated: refuses to apply if the anchors are missing (A0 changed the file).

Upstream: report to Agent-Zero. When upstream ships a fix, run --revert and delete
this script. See team-comms/kestrel-to-opus/pty_session_leak_20260818.md.
"""

import argparse
import os
import shutil
import sys

DEFAULT_TARGET = "/a0/plugins/_code_execution/helpers/tty_session.py"
BACKUP_SUFFIX = ".exocortex-orig"
MARKER = "EXOCORTEX-PTY-REAPER"
SUPPORTED_A0 = ("v2.9",)

# ── anchors we must find, or the file has changed and we must not guess ───────
ANCHOR_CONST = "_CLOSE_TIMEOUT_SECONDS = 2"
ANCHOR_START = "    async def start(self):"
ANCHOR_SEND = "    async def send(self, data: str | bytes):"
ANCHOR_READ = "    async def read(self, timeout=None):"

REAPER_BLOCK = '''
# ─────────────────── {marker} (Exocortex patch) ───────────────────
# A0 core never calls TTYSession.close(), so every context that runs
# code_execution leaks a PTY master + child shell. See
# plugins/_exocortex/patches/patch_pty_session_leak.py for the full writeup.
# Safe because code_execution_tool rebuilds a terminated session on next use.
import time as _exo_time
import weakref as _exo_weakref

_EXO_IDLE_LIMIT_SECONDS = {idle}
_EXO_REAP_INTERVAL_SECONDS = {interval}
_exo_live_sessions = _exo_weakref.WeakSet()
_exo_reaper_task = None


def _exo_touch(session):
    """Stamp last-use so the reaper never closes an active shell."""
    try:
        session._exo_last_used = _exo_time.monotonic()
    except Exception:
        pass


async def _exo_reaper_loop():
    while True:
        try:
            await asyncio.sleep(_EXO_REAP_INTERVAL_SECONDS)
            now = _exo_time.monotonic()
            for sess in list(_exo_live_sessions):
                try:
                    if sess.is_terminated():
                        continue
                    last = getattr(sess, "_exo_last_used", None)
                    if last is None or (now - last) < _EXO_IDLE_LIMIT_SECONDS:
                        continue
                    print(
                        f"[{marker}] closing idle shell "
                        f"(idle {{int(now - last)}}s >= {{_EXO_IDLE_LIMIT_SECONDS}}s)",
                        flush=True,
                    )
                    await sess.close()
                except Exception as e:
                    print(f"[{marker}] reap failed: {{e!r}}", flush=True)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[{marker}] reaper loop error: {{e!r}}", flush=True)


def _exo_ensure_reaper():
    """Start the reaper lazily, inside whatever loop A0 is actually running."""
    global _exo_reaper_task
    try:
        if _exo_reaper_task is not None and not _exo_reaper_task.done():
            return
        _exo_reaper_task = asyncio.get_running_loop().create_task(_exo_reaper_loop())
        print(
            f"[{marker}] reaper armed "
            f"(idle_limit={{_EXO_IDLE_LIMIT_SECONDS}}s interval={{_EXO_REAP_INTERVAL_SECONDS}}s)",
            flush=True,
        )
    except Exception as e:
        print(f"[{marker}] could not arm reaper: {{e!r}}", flush=True)
# ────────────────── end {marker} ──────────────────
'''

REGISTER_LINE = (
    "        _exo_live_sessions.add(self); _exo_touch(self); _exo_ensure_reaper()"
    "  # {marker}\n"
)
TOUCH_LINE = "        _exo_touch(self)  # {marker}\n"


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def detect_a0_version():
    for p in ("/a0/VERSION", "/a0/conf/version.txt"):
        try:
            return read(p).strip()
        except OSError:
            continue
    return "unknown"


def is_applied(text):
    return MARKER in text


def check(target):
    if not os.path.exists(target):
        print(f"  MISSING target: {target}")
        return 2
    text = read(target)
    ver = detect_a0_version()
    applied = is_applied(text)
    print(f"  target   : {target}")
    print(f"  a0 ver   : {ver}")
    print(f"  patched  : {'YES' if applied else 'no'}")
    print(f"  backup   : {'present' if os.path.exists(target + BACKUP_SUFFIX) else 'none'}")
    missing = [a for a in (ANCHOR_CONST, ANCHOR_START, ANCHOR_SEND, ANCHOR_READ)
               if a not in text]
    if missing and not applied:
        print("  ANCHORS MISSING — A0 changed this file, patch is NOT safe:")
        for m in missing:
            print(f"    - {m!r}")
        return 3
    return 0 if applied else 1


def apply(target, idle, interval):
    text = read(target)
    if is_applied(text):
        print("  already patched — no-op")
        return 0

    for a in (ANCHOR_CONST, ANCHOR_START, ANCHOR_SEND, ANCHOR_READ):
        if a not in text:
            print(f"  ABORT: anchor not found: {a!r}")
            print("  A0 core changed. Re-derive the patch before applying.")
            return 3

    ver = detect_a0_version()
    if ver != "unknown" and not any(ver.startswith(v) for v in SUPPORTED_A0):
        print(f"  WARNING: A0 version {ver!r} is outside tested {SUPPORTED_A0}.")
        print("  Anchors matched, proceeding — verify behaviour after deploy.")

    backup = target + BACKUP_SUFFIX
    if not os.path.exists(backup):
        shutil.copy2(target, backup)
        print(f"  backup written: {backup}")
    else:
        print(f"  backup already exists (kept): {backup}")

    block = REAPER_BLOCK.format(marker=MARKER, idle=idle, interval=interval)
    text = text.replace(ANCHOR_CONST, ANCHOR_CONST + "\n" + block, 1)
    text = text.replace(
        ANCHOR_START, ANCHOR_START + "\n" + REGISTER_LINE.format(marker=MARKER), 1
    )
    text = text.replace(
        ANCHOR_SEND, ANCHOR_SEND + "\n" + TOUCH_LINE.format(marker=MARKER), 1
    )
    text = text.replace(
        ANCHOR_READ, ANCHOR_READ + "\n" + TOUCH_LINE.format(marker=MARKER), 1
    )

    import py_compile
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8", newline="\n") as tf:
        tf.write(text)
        probe = tf.name
    try:
        py_compile.compile(probe, doraise=True)
    except Exception as e:
        print(f"  ABORT: patched source does not compile: {e}")
        return 4
    finally:
        try:
            os.unlink(probe)
        except OSError:
            pass

    write(target, text)
    print(f"  APPLIED (idle_limit={idle}s interval={interval}s)")
    print("  RESTART the container for it to take effect (module already imported).")
    return 0


def revert(target):
    backup = target + BACKUP_SUFFIX
    if not os.path.exists(backup):
        print(f"  no backup at {backup} — cannot revert")
        return 2
    shutil.copy2(backup, target)
    print(f"  REVERTED from {backup}")
    print("  RESTART the container for it to take effect.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Patch A0's PTY session leak (v2.9).")
    ap.add_argument("--target", default=DEFAULT_TARGET)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--revert", action="store_true")
    ap.add_argument("--idle-seconds", type=int, default=600,
                    help="close shells idle this long (default 600)")
    ap.add_argument("--interval-seconds", type=int, default=120,
                    help="how often the reaper sweeps (default 120)")
    a = ap.parse_args()

    print(f"[patch_pty_session_leak] {MARKER}")
    if a.check:
        return check(a.target)
    if a.revert:
        return revert(a.target)
    rc = check(a.target)
    if rc == 3:
        return rc
    return apply(a.target, a.idle_seconds, a.interval_seconds)


if __name__ == "__main__":
    sys.exit(main())
