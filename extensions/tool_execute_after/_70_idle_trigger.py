"""
Idle Time Engine — Trigger (Sensor)
====================================
Hook: tool_execute_after (_70_)

This extension is a SENSOR only. It writes two timestamps to engine_state.json:
  last_user_ts    — updated on every real-user response() call
  cycle_heartbeat — updated on every tool call in an idle cycle context

The firing decision (whether and when to start a cycle) lives entirely in
idle_watch.py, a separate process managed by supervisord. This separation
eliminates the bootstrap dependency: the watcher starts on container boot
regardless of whether anyone has sent a message.

What this extension does:
  1. Bootstrap: initialize state file on first-ever tool call if missing
  2. Heartbeat: update cycle_heartbeat on tool calls during idle cycle contexts
  3. Session close: on real-user response(), update last_user_ts + reset window
  4. Cycle close: on idle-cycle response(), clear cycle_active flag

What this extension does NOT do:
  - Start any asyncio task or background thread
  - Read idle threshold or fire conditions
  - Call the A0 REST API

State file: /a0/usr/Exocortex/office/engine_state.json
Lock file:  /a0/usr/Exocortex/office/.idle_engine.lock (written by idle_watch only)
"""

import json
import os
import sys
import time

from agent import LoopData
from helpers.extension import Extension

_EXOCORTEX_PATH = "/a0/usr/Exocortex"
if _EXOCORTEX_PATH not in sys.path:
    sys.path.insert(0, _EXOCORTEX_PATH)

_CONFIG_PATH  = "/a0/usr/Exocortex/config.json"
_OFFICE_DIR   = "/a0/usr/Exocortex/office"
_STATUS_PATH  = "/a0/usr/Exocortex/office/status.json"
_STATE_PATH   = "/a0/usr/Exocortex/office/engine_state.json"

_ACTIVATION_SENTINEL = "## IDLE-TIME CYCLE ACTIVATED"


class IdleTrigger(Extension):
    """Sensor: writes last_user_ts and cycle_heartbeat to engine_state.json."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            tool_name = kwargs.get("tool_name", "")
            agent     = self.agent

            # Never run in subordinate/child agent contexts
            if agent.get_data(agent.__class__.DATA_NAME_SUPERIOR) is not None:
                return

            config = _load_config()
            if not config.get("enabled", False):
                return

            # Bootstrap state file on first-ever tool call
            state = _read_state()
            if not state.get("last_user_ts"):
                state["last_user_ts"]             = time.time()
                state.setdefault("last_cycle_start",         0)
                state.setdefault("cycle_count",              0)
                state.setdefault("cold_start_grace",         True)
                state.setdefault("total_cycles_since_clear", 0)
                _write_state(state)
                print("[IDLE] Engine state initialized.", flush=True)

            # Heartbeat — update on every tool call in idle cycle context
            # Prevents idle_watch stale-cycle detection from clearing a live cycle.
            if not _last_user_msg_is_real(agent):
                state = _read_state()
                if state.get("cycle_active", False):
                    state["cycle_heartbeat"] = time.time()
                    _write_state(state)

            # Session and cycle tracking — only on response tool
            if tool_name != "response":
                return

            if _last_user_msg_is_real(agent):
                # Real user closed the session — reset idle window for next cycle
                state = _read_state()
                state["last_user_ts"]       = time.time()
                state["cycles_this_window"] = 0
                state["cold_start_grace"]   = True
                _write_state(state)
                _write_status({"state": "idle", "label": "Available"})
            else:
                # Idle cycle completed normally — clear the active flag
                state = _read_state()
                if state.get("cycle_active", False):
                    state["cycle_active"] = False
                    _write_state(state)
                    print("[IDLE] Cycle complete — cycle_active cleared.", flush=True)
                _write_status({"state": "idle", "label": "Available"})

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[IDLE] Trigger error (passthrough): {e}",
                )
            except Exception:
                pass


def _last_user_msg_is_real(agent) -> bool:
    """Walk history backwards to the most recent user message. True if not an idle activation.

    The API message arrives JSON-wrapped as {"user_message": "## IDLE-TIME CYCLE ACTIVATED..."},
    so check sentinel appears anywhere in the content, not just at the start.
    """
    try:
        for msg in reversed(agent.history.output()):
            if msg.get("ai", True):
                continue
            content = msg.get("content", "")
            if isinstance(content, dict):
                content = content.get("text", "") or content.get("user_message", "") or str(content)
            return _ACTIVATION_SENTINEL not in str(content)
    except Exception:
        pass
    return False


def _read_state() -> dict:
    try:
        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _write_state(state: dict) -> None:
    try:
        os.makedirs(_OFFICE_DIR, exist_ok=True)
        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _STATE_PATH)
    except Exception:
        pass


def _write_status(status: dict) -> None:
    try:
        os.makedirs(_OFFICE_DIR, exist_ok=True)
        tmp = _STATUS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(status, f)
        os.replace(tmp, _STATUS_PATH)
    except Exception:
        pass


def _load_config() -> dict:
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                return json.load(f).get("idle_time_engine", {})
    except Exception:
        pass
    return {}
