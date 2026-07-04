"""
Idle Watch Bootstrap — Daemon Launcher (clone-and-go)
=====================================================
Hook: before_main_llm_call (_00_, earliest)

A0 plugins ship extensions, not supervisord programs — so this extension keeps
the idle_watch daemon alive itself. On each turn (throttled to once/60s) it
checks a pidfile and, if the daemon is not running, spawns it DETACHED
(start_new_session=True) so the daemon:
  - survives run_ui restarts (reparented to init, not killed with the UI process)
  - ships with the plugin (clone the plugin → the daemon runs)
  - survives A0 image rebuilds (no /etc/supervisor edit to be wiped)

Why not /etc/supervisor/conf.d: that file is container-level and is replaced on
an A0 image rebuild or a fresh clone — exactly the persistence gap the plugin
migration closed for extensions. Launching from an extension makes the idle
engine part of the self-contained plugin, consistent with the rest of the stack.

Safety: the daemon force-disables idle *cycles* on every start (cost-safety in
idle_watch._disable_cycles_on_start), so a running daemon never auto-resumes
paid cycles. Arming is explicit via the Office panel / idle_control API. Keeping
the daemon up is therefore free and safe — it only polls timestamps until armed.

Concurrency: a double-spawn is harmless — the daemon's fcntl.flock on the cycle
lock guarantees only one holder ever fires a cycle. The pidfile guard below
prevents duplicates in the normal path anyway.

Trade-off vs. v16's supervisord launch: the daemon starts on first agent
activity rather than container boot. Since cycles are armed explicitly and only
make sense after the agent has done work, this loses nothing in practice.
"""

import os
import subprocess
import time

from agent import LoopData
from helpers.extension import Extension

# The daemon interpreter — A0's venv (matches v16's proven supervisord command).
_PYTHON   = "/opt/venv-a0/bin/python3"
_DAEMON   = "/a0/usr/plugins/_exocortex/services/idle_watch.py"
_OFFICE   = "/a0/usr/workdir/workspace/office"
_PIDFILE  = "/a0/usr/workdir/workspace/office/.idle_watch.pid"
_LOGFILE  = "/a0/usr/workdir/workspace/office/idle_watch.log"

_CHECK_INTERVAL = 60          # seconds between liveness checks (module-global throttle)
_last_check     = 0.0         # persists across turns within the A0 process


class IdleWatchBootstrap(Extension):
    """Spawns and keeps the idle_watch daemon alive. Clone-and-go launcher."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        global _last_check
        try:
            # Top-level agent only — never bootstrap from subordinate/child contexts
            if self.agent.get_data(self.agent.__class__.DATA_NAME_SUPERIOR) is not None:
                return

            now = time.time()
            if now - _last_check < _CHECK_INTERVAL:
                return
            _last_check = now

            if not os.path.exists(_DAEMON) or not os.path.exists(_PYTHON):
                return  # nothing to launch (plugin not fully present)

            if _daemon_alive():
                return

            _spawn_daemon()

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[IDLE-BOOT] bootstrap error (passthrough): {e}",
                )
            except Exception:
                pass


def _daemon_alive() -> bool:
    """True iff the pidfile points at a live idle_watch.py process."""
    try:
        if not os.path.exists(_PIDFILE):
            return False
        with open(_PIDFILE, "r", encoding="utf-8") as f:
            pid = int((f.read() or "0").strip())
        if pid <= 0:
            return False
        os.kill(pid, 0)  # raises ProcessLookupError if the pid is dead
        # Pid-reuse guard: confirm the live pid is actually our daemon
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                if b"idle_watch.py" not in f.read():
                    return False
        except Exception:
            pass  # /proc unreadable — trust the os.kill liveness check
        return True
    except (ProcessLookupError, ValueError, PermissionError):
        return False
    except Exception:
        return False


def _spawn_daemon() -> None:
    """Spawn idle_watch.py detached; record its pid."""
    os.makedirs(_OFFICE, exist_ok=True)
    logf = open(_LOGFILE, "ab")
    proc = subprocess.Popen(
        [_PYTHON, "-u", _DAEMON],
        stdout=logf,
        stderr=logf,
        stdin=subprocess.DEVNULL,
        start_new_session=True,   # detach: survives run_ui restart; reparented to init
        cwd="/a0",
    )
    try:
        with open(_PIDFILE, "w", encoding="utf-8") as f:
            f.write(str(proc.pid))
    except Exception:
        pass
    print(f"[IDLE-BOOT] Spawned idle_watch daemon (pid {proc.pid}).", flush=True)
