"""
Idle Engine Control API
=======================
Route (auto-registered by A0's dispatch): POST /api/idle_control

Actions:
  pause  — pause the idle engine for duration_seconds (default 3600, max 86400)
  resume — clear pause, engine resumes normal operation

Writes pause state to /a0/usr/Exocortex/office/control.json.
The idle trigger's monitor reads this file each poll cycle and skips activation
while time.time() < paused_until. A currently-running cycle will complete before
the pause takes effect.
"""

import json
import os
import time
from datetime import datetime, timezone

from helpers.api import ApiHandler, Request, Response

_CONTROL_PATH = "/a0/usr/Exocortex/office/control.json"
_STATUS_PATH = "/a0/usr/Exocortex/office/status.json"
_OFFICE_DIR = "/a0/usr/Exocortex/office"


class IdleControl(ApiHandler):
    """POST /api/idle_control — pause or resume the idle engine."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = (input.get("action") or "").strip().lower()

        if action == "pause":
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
                "error": f"Unknown action {action!r}. Use 'pause' or 'resume'."
            }


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
