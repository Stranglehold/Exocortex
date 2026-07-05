"""
Idle Engine Control API
=======================
Route (auto-registered by A0's dispatch): POST /api/idle_control

Actions:
  enable  — permanently enable the idle engine (sets config.json enabled: true)
  disable — permanently disable the idle engine (sets config.json enabled: false)
  pause   — pause the idle engine for duration_seconds (default 3600, max 86400)
  resume  — clear pause, engine resumes normal operation

enable/disable write to config.json and survive container restarts.
pause/resume write to control.json and are time-bounded.

The idle trigger's monitor reads config.json each poll cycle and skips all
activation while enabled is false. A currently-running cycle will complete
before disable takes effect (next poll check).
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone

from helpers.api import ApiHandler, Request, Response

_CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"
_CONTROL_PATH = "/a0/usr/workdir/workspace/office/control.json"
_STATUS_PATH = "/a0/usr/workdir/workspace/office/status.json"
_OFFICE_DIR = "/a0/usr/workdir/workspace/office"

# Daemon launch (mirrors _00_idle_watch_bootstrap) — so `enable` can start the
# engine itself instead of waiting for the next agent turn to spawn it.
_PYTHON = "/opt/venv-a0/bin/python3"
_DAEMON = "/a0/usr/plugins/_exocortex/services/idle_watch.py"
_PIDFILE = "/a0/usr/workdir/workspace/office/.idle_watch.pid"
_LOGFILE = "/a0/usr/workdir/workspace/office/idle_watch.log"


class IdleControl(ApiHandler):
    """POST /api/idle_control — enable, disable, pause, or resume the idle engine."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = (input.get("action") or "").strip().lower()

        if action == "enable":
            # Arm the config, AND stamp an explicit-arm marker the daemon's
            # disable-on-start respects (so this arm survives the daemon (re)spawn
            # below). Then ensure the daemon is actually running — clicking enable
            # must START the engine, not just set a flag nothing reads.
            _update_config_enabled(True)
            _write_file(_CONTROL_PATH, {"paused_until": 0, "armed_at": time.time()})
            spawned = False
            if not _daemon_alive():
                spawned = _spawn_daemon()
            _write_file(_STATUS_PATH, {"state": "idle", "label": "Available"})
            return {
                "status": "enabled",
                "enabled": True,
                "daemon_alive": _daemon_alive(),
                "daemon_spawned": spawned,
            }

        elif action == "disable":
            # Clear the arm marker so a later daemon start won't treat a stale
            # arm as intent to run.
            _update_config_enabled(False)
            _write_file(_CONTROL_PATH, {"paused_until": 0, "armed_at": 0})
            _write_file(_STATUS_PATH, {"state": "disabled", "label": "Disabled"})
            return {"status": "disabled", "enabled": False}

        elif action == "pause":
            duration = int(input.get("duration_seconds", 3600))
            duration = max(60, min(duration, 86400))  # clamp: 1 min – 24 hrs
            paused_until = time.time() + duration
            paused_until_iso = datetime.fromtimestamp(
                paused_until, tz=timezone.utc
            ).isoformat()
            _write_file(_CONTROL_PATH, {"paused_until": paused_until})
            _write_file(_STATUS_PATH, {
                "state": "paused",
                "label": "Paused",
                "paused_until": paused_until_iso,
            })
            return {
                "status": "paused",
                "paused_until": paused_until_iso,
                "duration_seconds": duration,
            }

        elif action == "resume":
            _write_file(_CONTROL_PATH, {"paused_until": 0})
            _write_file(_STATUS_PATH, {"state": "idle", "label": "Available"})
            return {"status": "resumed"}

        else:
            return {
                "error": f"Unknown action {action!r}. Use 'enable', 'disable', 'pause', or 'resume'."
            }


def _update_config_enabled(enabled: bool) -> None:
    """Read-merge-write config.json to set idle_time_engine.enabled."""
    try:
        cfg: dict = {}
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                cfg = json.load(f)
        section = cfg.setdefault("idle_time_engine", {})
        section["enabled"] = enabled
        tmp = _CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp, _CONFIG_PATH)
    except Exception:
        pass


def _write_file(path: str, data: dict) -> None:
    """Atomically write a JSON file."""
    try:
        os.makedirs(_OFFICE_DIR, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except Exception:
        pass


def _daemon_alive() -> bool:
    """True iff the pidfile points at a live idle_watch.py process (mirrors the
    bootstrap's check)."""
    try:
        if not os.path.exists(_PIDFILE):
            return False
        with open(_PIDFILE, "r", encoding="utf-8") as f:
            pid = int((f.read() or "0").strip())
        if pid <= 0:
            return False
        os.kill(pid, 0)  # ProcessLookupError if dead
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                if b"idle_watch.py" not in f.read():
                    return False
        except Exception:
            pass
        return True
    except (ProcessLookupError, ValueError, PermissionError):
        return False
    except Exception:
        return False


def _spawn_daemon() -> bool:
    """Spawn idle_watch.py detached (start_new_session) and record its pid —
    same launch the bootstrap uses. Returns True on success."""
    try:
        if not (os.path.exists(_DAEMON) and os.path.exists(_PYTHON)):
            return False
        os.makedirs(_OFFICE_DIR, exist_ok=True)
        logf = open(_LOGFILE, "ab")
        proc = subprocess.Popen(
            [_PYTHON, "-u", _DAEMON],
            stdout=logf,
            stderr=logf,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            cwd="/a0",
        )
        try:
            with open(_PIDFILE, "w", encoding="utf-8") as f:
                f.write(str(proc.pid))
        except Exception:
            pass
        return True
    except Exception:
        return False
