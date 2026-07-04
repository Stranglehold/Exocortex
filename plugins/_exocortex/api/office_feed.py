"""
Office Feed API Handler
=======================
Serves idle-time engine activity data for the Office panel.

Route (auto-registered by A0's dispatch): GET /api/office_feed

Feed source:    /a0/usr/workdir/workspace/office/feed.jsonl
Status source:  /a0/usr/workdir/workspace/office/status.json
Control source: /a0/usr/workdir/workspace/office/control.json
Config source:  /a0/usr/plugins/_exocortex/config/config.json

Returns:
  {
    "entries":      list[dict],   # last 50 feed entries, newest first
    "total_cycles": int,          # lifetime cycle_count from engine_state.json
                                  # (was incorrectly len(entries) capped at 50 — fixed 2026-05-20)
    "status":       dict,         # current engine state (includes paused_until when paused)
    "enabled":      bool          # master on/off from config.json
  }
"""

import json
import os
import time

from helpers.api import ApiHandler, Request, Response

_FEED_PATH = "/a0/usr/workdir/workspace/office/feed.jsonl"
_STATUS_PATH = "/a0/usr/workdir/workspace/office/status.json"
_CONTROL_PATH = "/a0/usr/workdir/workspace/office/control.json"
_CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"
_ENGINE_STATE_PATH = "/a0/usr/workdir/workspace/office/engine_state.json"
_MAX_ENTRIES = 50


class OfficeFeed(ApiHandler):
    """GET /api/office_feed — returns activity feed and current engine status."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        entries = _read_feed()
        status = _read_status()
        enabled = _read_enabled()
        engine_state = _read_engine_state()

        # If permanently disabled, override state regardless of status.json
        if not enabled:
            status["state"] = "disabled"
            status["label"] = "Disabled"

        # If enabled but paused, override state (timed pause wins over idle)
        control = _read_control()
        paused_until = control.get("paused_until", 0)
        if enabled and paused_until and time.time() < paused_until:
            status["state"] = "paused"
            status["label"] = "Paused"
            status["paused_until"] = status.get("paused_until") or str(paused_until)

        # total_cycles = lifetime cycle_count from engine_state (real counter).
        # Falls back to len(entries) if engine_state can't be read — preserves the
        # old behavior when the state file is missing rather than reporting 0.
        total_cycles = engine_state.get("cycle_count")
        if total_cycles is None:
            total_cycles = len(entries)

        return {
            "entries": entries,
            "total_cycles": total_cycles,
            "status": status,
            "enabled": enabled,
        }


def _read_feed() -> list[dict]:
    """Read feed.jsonl, return last _MAX_ENTRIES entries newest-first."""
    entries: list[dict] = []
    try:
        if os.path.exists(_FEED_PATH):
            with open(_FEED_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
    except Exception:
        pass
    entries.reverse()
    return entries[:_MAX_ENTRIES]


def _read_status() -> dict:
    """Read status.json, return default if missing."""
    try:
        if os.path.exists(_STATUS_PATH):
            with open(_STATUS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"state": "idle", "label": "Available"}


def _read_control() -> dict:
    """Read control.json for pause state."""
    try:
        if os.path.exists(_CONTROL_PATH):
            with open(_CONTROL_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _read_engine_state() -> dict:
    """Read engine_state.json for the live cycle counters. Returns {} if missing."""
    try:
        if os.path.exists(_ENGINE_STATE_PATH):
            with open(_ENGINE_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _read_enabled() -> bool:
    """Read config.json idle_time_engine.enabled. Defaults to False (safe default)."""
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                cfg = json.load(f)
            return bool(cfg.get("idle_time_engine", {}).get("enabled", False))
    except Exception:
        pass
    return False
