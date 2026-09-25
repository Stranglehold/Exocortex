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
  4. Cycle close: on idle-cycle response(), write the Office status only (the daemon owns
     cycle_active since 2026-07-15)
  Which calls belong to an idle cycle is decided by helpers/attendedness (2026-09-25).

What this extension does NOT do:
  - Start any asyncio task or background thread
  - Read idle threshold or fire conditions
  - Call the A0 REST API

State file: /a0/usr/workdir/workspace/office/engine_state.json
Lock file:  /a0/usr/workdir/workspace/office/.idle_engine.lock (written by idle_watch only)
"""

import json
import os
import sys
import time

from agent import LoopData
from helpers.extension import Extension

_EXOCORTEX_PATH = "/a0/usr/plugins/_exocortex/helpers"
if _EXOCORTEX_PATH not in sys.path:
    sys.path.insert(0, _EXOCORTEX_PATH)

# Whether a tool call belongs to an idle cycle is answered by the shared rule in
# helpers/attendedness.py (2026-09-25), the third consumer after _07 and _10. The history walk it
# replaces (_last_user_msg_is_real, retired below) saw a PARALLEL WORKER as a real user:
# helpers/parallel_tools.py runs each inner call in a fresh AgentContext whose history has no
# activation message. That stamped last_user_ts from inside a cycle and shut the daemon's idle
# gate for 30 min. 5 of 5 late-recorded deaths between 09-15 and 09-25 followed that stamp.
try:
    import attendedness as att
except Exception:  # pragma: no cover - helper missing
    att = None  # type: ignore[assignment]

_CONFIG_PATH  = "/a0/usr/plugins/_exocortex/config/config.json"
_OFFICE_DIR   = "/a0/usr/workdir/workspace/office"
_STATUS_PATH  = "/a0/usr/workdir/workspace/office/status.json"
_STATE_PATH   = "/a0/usr/workdir/workspace/office/engine_state.json"

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

            # One classification per call, used by both branches below.
            idle_cycle = _is_idle_cycle(agent)

            # Heartbeat — update on every tool call in idle cycle context
            # Prevents idle_watch stale-cycle detection from clearing a live cycle.
            if idle_cycle:
                state = _read_state()
                if state.get("cycle_active", False):
                    state["cycle_heartbeat"] = time.time()
                    _write_state(state)
            else:
                # Activity signal — keep idle timer fresh during long user tasks.
                # Throttled to once per 60s so we don't write JSON on every tool call.
                # Prevents idle cycle firing while the agent is actively working.
                if tool_name != "response":
                    state = _read_state()
                    if time.time() - state.get("last_user_ts", 0) > 60:
                        state["last_user_ts"] = time.time()
                        _write_state(state)

            # Session and cycle tracking — only on response tool
            if tool_name != "response":
                return

            if not idle_cycle:
                # Real user closed the session — reset idle window for next cycle
                state = _read_state()
                state["last_user_ts"]       = time.time()
                state["cycles_this_window"] = 0
                state["cold_start_grace"]   = True
                _write_state(state)
                _write_status({"state": "idle", "label": "Available"})
            else:
                # Idle cycle's response() fired. The idle_watch DAEMON is now the SOLE
                # authority over cycle_active — it deasserts on the self-report signal
                # (cycle_close.py) only once the context has FULLY finished. This hook
                # must NOT clear the flag: tool_execute_after on response() runs while the
                # context is still alive finishing monologue_end (memory/ontology/sleep),
                # so clearing here orphaned still-running contexts as un-reaped zombies —
                # the concurrency pile-up (2026-07-15). It also double-charged the budget
                # (daemon._clear_cycle_slot already increments total_cycles_since_clear).
                # Status only.
                _write_status({"state": "idle", "label": "Available"})

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[IDLE] Trigger error (passthrough): {e}",
                )
            except Exception:
                pass


def _is_idle_cycle(agent) -> bool:
    """True only when helpers/attendedness positively reports UNATTENDED. That means the idle
    marker is on this context or, through the parallel-worker parent chain, on its parent; or
    engine_state names this context as the cycle.

    ATTENDED and UNDETERMINED both read as a USER (Opus, 2026-09-25). Misreading a user as a
    cycle can fire a cycle over a live session, which is unbounded harm. Misreading a cycle as a
    user costs bounded engine time, and the daemon now resolves the slot ahead of its gates.
    A missing helper cannot say UNATTENDED, so it reads as a user too. A walk fault is printed,
    because silent safety and observed safety are different categories."""
    if att is None:
        print("[IDLE] attendedness helper unavailable — reading this call as a user.", flush=True)
        return False
    try:
        observation, _marker, fault = att.attendedness(agent)
    except Exception as e:
        print(f"[IDLE] attendedness raised {type(e).__name__} — reading this call as a user.", flush=True)
        return False
    if fault:
        print(f"[IDLE] attendedness walk fault: {fault}", flush=True)
    return observation == att.UNATTENDED


def _last_user_msg_is_real_RETIRED(agent) -> bool:
    """RETIRED 2026-09-25 — superseded by _is_idle_cycle (helpers/attendedness.py). Kept
    unreferenced for one release so the change is auditable against the original, the same
    convention as _07's _marker_inline_RETIRED. It read a parallel worker's empty history as a
    real user, and its fail-open default ("no user message found → real") is why.

    Walk history backwards to find the most recent actual user message.

    Only stops at messages with a "user_message" key — the format produced by
    hist_add_user_message (fw.user_message.md). Skips tool results (tool_name key),
    system warnings (system_warning key), and all other injected non-AI messages.

    Why: tool_execute_after fires BEFORE hist_add_tool_result, so the most recent
    non-AI message is often a previous tool result or a LOOP DETECTED warning, not
    the actual user message. Stopping at those would freeze the heartbeat after the
    first tool call and misidentify idle cycles as real-user sessions.
    """
    try:
        for msg in reversed(agent.history.output()):
            if msg.get("ai", True):
                continue
            content = msg.get("content", "")
            if isinstance(content, dict):
                if "user_message" in content:
                    return _ACTIVATION_SENTINEL not in str(content.get("user_message", ""))
                # Tool results, system warnings, and other injections — skip
                continue
            elif isinstance(content, str):
                if _ACTIVATION_SENTINEL in content:
                    return False
                # Plain string without sentinel — skip (could be a warning or other injection)
                continue
    except Exception:
        pass
    return True  # No user message found — assume real-user context (conservative)


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
