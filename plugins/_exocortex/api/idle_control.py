"""
Idle Engine Control API
=======================
Route (auto-registered by A0's plugin dispatch): POST /api/plugins/_exocortex/idle_control

(This docstring previously said /api/idle_control. That is wrong — verified live
2026-08-19 on VekV2: POST /api/idle_control -> 404, POST /api/plugins/_exocortex/idle_control
-> 200. Plugin API modules register under /api/plugins/<plugin>/<module>.)

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
    """POST /api/plugins/_exocortex/idle_control — enable, disable, pause, resume."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = (input.get("action") or "").strip().lower()

        if action == "enable":
            # Arm the config, AND stamp an explicit-arm marker the daemon's
            # disable-on-start respects (so this arm survives the daemon (re)spawn
            # below). Then ensure the daemon is actually running — clicking enable
            # must START the engine, not just set a flag nothing reads.
            _update_config_enabled(True)
            # Arm WITHOUT clearing a pause. Enable and pause are different questions — "is the
            # engine switched on" and "is it held right now" — and the old wholesale write
            # answered the second by erasing it. Anyone who wants to run now calls resume.
            ok = _merge_control(armed_at=time.time())
            spawned = False
            if not _daemon_alive():
                spawned = _spawn_daemon()
            _write_file(_STATUS_PATH, {"state": "idle", "label": "Available"})
            held = _read_control().get("paused_until", 0) or 0
            paused = held > time.time()
            if paused:
                _write_file(_STATUS_PATH, {"state": "paused", "label": "Paused"})
            return {
                "success": ok,
                "status": "enabled",
                "enabled": True,
                "daemon_alive": _daemon_alive(),
                "daemon_spawned": spawned,
                "paused_until": datetime.fromtimestamp(held, tz=timezone.utc).isoformat() if paused else None,
                "note": ("enabled, but a pause is still in force until the time above — "
                         "call resume to run now") if paused else "",
            }

        elif action == "disable":
            # Clear the arm marker so a later daemon start won't treat a stale
            # arm as intent to run.
            _update_config_enabled(False)
            ok = _merge_control(armed_at=0)   # zeroed deliberately: a stale arm must not read as intent
            _write_file(_STATUS_PATH, {"state": "disabled", "label": "Disabled"})
            return {"success": ok, "status": "disabled", "enabled": False}

        elif action == "pause":
            duration = int(input.get("duration_seconds", 3600))
            duration = max(60, min(duration, 86400))  # clamp: 1 min – 24 hrs
            paused_until = time.time() + duration
            paused_until_iso = datetime.fromtimestamp(
                paused_until, tz=timezone.utc
            ).isoformat()
            reason = (input.get("reason") or "").strip() or None
            ok = _merge_control(paused_until=paused_until, pause_reason=reason)
            _write_file(_STATUS_PATH, {
                "state": "paused",
                "label": "Paused",
                "paused_until": paused_until_iso,
            })
            return {
                "success": ok,
                "status": "paused" if ok else "FAILED",
                "paused_until": paused_until_iso if ok else None,
                "duration_seconds": duration,
                "pause_reason": reason,
                "note": "" if ok else "the control file could not be written — nothing changed",
            }

        elif action == "resume":
            ok = _merge_control(paused_until=0, pause_reason=None)
            _write_file(_STATUS_PATH, {"state": "idle", "label": "Available"})
            return {"success": ok, "status": "resumed" if ok else "FAILED",
                    "note": "" if ok else "the control file could not be written — nothing changed"}

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


def _write_file(path: str, data: dict) -> bool:
    """Atomically write a JSON file. RETURNS whether it worked.

    This used to be `except Exception: pass`, so a failed write returned HTTP 200 with
    status "paused" and nothing on disk — the endpoint reporting a pause that did not
    exist. A control that can lie about whether it acted is worse than one that cannot act
    (Kestrel, 2026-09-14)."""
    try:
        os.makedirs(_OFFICE_DIR, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, path)
        return True
    except Exception as e:
        print(f"[IDLE-CONTROL] write FAILED {path}: {e}", flush=True)
        return False


def _read_control() -> dict:
    try:
        with open(_CONTROL_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _merge_control(**updates) -> bool:
    """READ-MERGE-WRITE. control.json is shared: paused_until belongs to pause/resume and
    armed_at belongs to enable/disable, and every action used to write the whole file, so
    each silently destroyed the other's key.

    Two real failures came from that on 2026-09-14. `enable` wrote {paused_until: 0,...},
    so the daemon-restart sequence silently un-paused an engine that was deliberately held
    — 578 was one poll from firing into a saturated GPU. And `pause` dropped armed_at,
    which _disable_cycles_on_start reads to honour a recent arm, so pausing quietly removed
    the arm's protection and the next daemon start force-disabled.

    Pass only the keys you mean to change. A key you do not name survives."""
    cur = _read_control()
    for k, v in updates.items():
        if v is None:
            cur.pop(k, None)
        else:
            cur[k] = v
    return _write_file(_CONTROL_PATH, cur)


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
