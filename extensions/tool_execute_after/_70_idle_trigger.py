"""
Idle Time Engine — Trigger
==========================
Hook: tool_execute_after (_70_)

When the agent has been idle (no real user messages) for idle_threshold_seconds,
activates an autonomous work cycle (Workshop or Field mode) by injecting the
idle activation prompt via agent.context.communicate(UserMessage(...)).

Workshop mode (3 of every 4 cycles by default): self-improvement per program.md
Field mode (1 of every 4 cycles): interest research per interests.md

Cycle type selection (3:1 ratio):
  - Cycles 0,1,2 → WORKSHOP; cycle 3 → FIELD; cycle 4,5,6 → WORKSHOP; etc.

Config: /a0/usr/Exocortex/config.json → "idle_time_engine" section
  enabled: true
  idle_threshold_seconds: 1800      # 30 min — time since last real user message
  cooldown_seconds: 3600            # 60 min — minimum gap between cycles
  max_steps_per_cycle: 20
  workshop_field_ratio: "3:1"

State keys (stored on agent.data):
  _idle_last_user_ts      — float: time.time() of last REAL user session end
  _idle_last_cycle_end_ts — float: time.time() of last idle cycle end
  idle_mode               — bool: True while an idle cycle is active
  idle_cycle_count        — int: total completed cycles (drives cycle type selection)

Office panel feed: /a0/usr/Exocortex/office/feed.jsonl (agent writes at cycle end)
Status indicator: /a0/usr/Exocortex/office/status.json (trigger writes on transitions)
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict

from agent import LoopData, UserMessage
from helpers.extension import Extension

_EXOCORTEX_PATH = "/a0/usr/Exocortex"
if _EXOCORTEX_PATH not in sys.path:
    sys.path.insert(0, _EXOCORTEX_PATH)

_CONFIG_PATH = "/a0/usr/Exocortex/config.json"
_OFFICE_DIR = "/a0/usr/Exocortex/office"
_STATUS_PATH = "/a0/usr/Exocortex/office/status.json"
_PROMPT_PATH = "/a0/usr/Exocortex/prompts/idle_activation.md"

# Agent data keys
_KEY_LAST_USER_TS = "_idle_last_user_ts"
_KEY_LAST_CYCLE_END = "_idle_last_cycle_end_ts"
_KEY_IDLE_MODE = "idle_mode"
_KEY_CYCLE_COUNT = "idle_cycle_count"

# Marker injected at the start of every idle activation prompt.
# Used to distinguish idle-cycle user messages from real user messages
# when walking history backwards.
_ACTIVATION_SENTINEL = "## IDLE-TIME CYCLE ACTIVATED"

_POLL_INTERVAL = 60  # seconds between idle monitor checks

# Per-context asyncio monitor task registry (same pattern as _60_sleep_trigger.py)
_idle_tasks: Dict[str, asyncio.Task] = {}


def _ctx_id(agent) -> str:
    try:
        return str(agent.context.id)
    except Exception:
        return "default"


class IdleTrigger(Extension):
    """Activates autonomous work cycles (Workshop or Field) during agent idle time."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            tool_name = kwargs.get("tool_name", "")
            agent = self.agent

            # Never fire in subordinate/child agent contexts
            if agent.get_data(agent.__class__.DATA_NAME_SUPERIOR) is not None:
                return

            config = _load_config()
            if not config.get("enabled", True):
                return

            ctx = _ctx_id(agent)

            # Only act at end-of-monologue (response tool)
            if tool_name != "response":
                return

            # Prune completed monitor tasks from registry
            for k in list(_idle_tasks):
                if _idle_tasks[k].done():
                    del _idle_tasks[k]

            # Determine whether we're ending an idle cycle or a real user session.
            # Walk history backwards to find the most recent user message and check
            # whether it's our idle activation (sentinel prefix) or a real user message.
            idle_mode = agent.get_data(_KEY_IDLE_MODE)

            if idle_mode:
                # We were in an idle cycle. Check if a real user message interrupted it.
                interrupted = _last_user_msg_is_real(agent)
                agent.set_data(_KEY_IDLE_MODE, False)
                cycle_n = (agent.get_data(_KEY_CYCLE_COUNT) or 0) + 1
                agent.set_data(_KEY_CYCLE_COUNT, cycle_n)
                agent.set_data(_KEY_LAST_CYCLE_END, time.time())

                if interrupted:
                    # Real user message arrived mid-cycle — also reset idle timer
                    agent.set_data(_KEY_LAST_USER_TS, time.time())
                    print(f"[IDLE] Cycle {cycle_n} interrupted by user.", flush=True)
                    _write_status({"state": "idle", "label": "Available"})
                else:
                    print(f"[IDLE] Cycle {cycle_n} complete.", flush=True)
                    cooldown_s = config.get("cooldown_seconds", 3600)
                    next_ts = datetime.fromtimestamp(
                        time.time() + cooldown_s, tz=timezone.utc
                    ).isoformat()
                    _write_status({"state": "cooldown", "label": "Cooldown",
                                   "next_cycle": next_ts})
            else:
                # Real user session just ended
                agent.set_data(_KEY_LAST_USER_TS, time.time())
                _write_status({"state": "idle", "label": "Available"})

            # Start idle monitor if no monitor is currently running for this context
            if ctx not in _idle_tasks:
                _idle_tasks[ctx] = asyncio.create_task(
                    _idle_monitor(agent, config, ctx)
                )
                print(
                    f"[IDLE] Monitor started (ctx={ctx}, "
                    f"threshold={config.get('idle_threshold_seconds', 1800)}s, "
                    f"cooldown={config.get('cooldown_seconds', 3600)}s).",
                    flush=True,
                )

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[IDLE] Trigger error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Idle Monitor ──────────────────────────────────────────────────────────────

async def _idle_monitor(agent, config: dict, ctx: str) -> None:
    """
    Poll every _POLL_INTERVAL seconds. Fire an autonomous idle cycle when:
      - time since last real user message >= idle_threshold_seconds
      - time since last idle cycle end >= cooldown_seconds
      - agent is not currently in an idle cycle

    Exits after injecting one activation (one monitor per response-tool fire).
    The next response-tool in execute() restarts a fresh monitor.
    """
    threshold = config.get("idle_threshold_seconds", 1800)
    cooldown = config.get("cooldown_seconds", 3600)

    try:
        while True:
            await asyncio.sleep(_POLL_INTERVAL)

            # Guard: already in an idle cycle (activation still processing)
            if agent.get_data(_KEY_IDLE_MODE):
                continue

            now = time.time()
            last_user = agent.get_data(_KEY_LAST_USER_TS) or 0
            last_cycle = agent.get_data(_KEY_LAST_CYCLE_END) or 0

            idle_seconds = now - last_user
            since_cycle = now - last_cycle

            if idle_seconds < threshold:
                continue
            if since_cycle < cooldown:
                continue

            # ── Fire idle cycle ──
            cycle_count = agent.get_data(_KEY_CYCLE_COUNT) or 0
            cycle_type = _determine_cycle_type(cycle_count, config)
            max_steps = config.get("max_steps_per_cycle", 20)

            print(
                f"[IDLE] Activating {cycle_type} cycle #{cycle_count + 1} "
                f"(idle={idle_seconds:.0f}s >= {threshold}s, ctx={ctx}).",
                flush=True,
            )

            # Set flag BEFORE communicate() so the first tool-use inside the cycle
            # sees idle_mode=True
            agent.set_data(_KEY_IDLE_MODE, True)
            _write_status({
                "state": "working",
                "label": "Working",
                "cycle_type": cycle_type.lower(),
                "started": datetime.now(timezone.utc).isoformat(),
            })

            activation = _build_activation_prompt(cycle_type, max_steps)
            try:
                agent.context.communicate(UserMessage(activation))
            except Exception as e:
                # If injection fails, clear flag so the system doesn't get stuck
                print(f"[IDLE] Failed to inject activation: {e}", flush=True)
                agent.set_data(_KEY_IDLE_MODE, False)
                _write_status({"state": "idle", "label": "Available"})

            break  # one activation per monitor task

    except asyncio.CancelledError:
        print(f"[IDLE] Monitor cancelled (ctx={ctx}).", flush=True)
    except Exception as e:
        print(f"[IDLE] Monitor error (ctx={ctx}): {e}", flush=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _determine_cycle_type(cycle_count: int, config: dict) -> str:
    """Return 'WORKSHOP' or 'FIELD' based on cycle count and configured ratio."""
    ratio = config.get("workshop_field_ratio", "3:1")
    try:
        workshop_n, field_n = map(int, ratio.split(":"))
        total = workshop_n + field_n
        if total == 0:
            return "WORKSHOP"
        return "FIELD" if (cycle_count % total >= workshop_n) else "WORKSHOP"
    except Exception:
        return "WORKSHOP"


def _last_user_msg_is_real(agent) -> bool:
    """
    Walk history output() backwards to find the most recent user message (ai=False).
    Return True if it's a real user message, False if it's our idle activation.
    A return value of True indicates the idle cycle was interrupted by the user.
    """
    try:
        for msg in reversed(agent.history.output()):
            if msg.get("ai", True):  # ai=True = AI message, skip
                continue
            # Found a user message — check if it's our idle activation
            content = msg.get("content", "")
            if isinstance(content, dict):
                content = content.get("text", "") or str(content)
            return not str(content).startswith(_ACTIVATION_SENTINEL)
    except Exception:
        pass
    return False


def _build_activation_prompt(cycle_type: str, max_steps: int) -> str:
    """Load and format the idle activation prompt template from disk."""
    try:
        if os.path.exists(_PROMPT_PATH):
            with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
                template = f.read()
            return (template
                    .replace("{cycle_type}", cycle_type)
                    .replace("{max_steps}", str(max_steps)))
    except Exception:
        pass
    # Minimal fallback if prompt file is missing
    return (
        f"{_ACTIVATION_SENTINEL}\n\n"
        f"Cycle type: {cycle_type}\n"
        f"Step budget: {max_steps} steps maximum.\n\n"
        f"Read /a0/usr/Exocortex/self-improvement/program.md for operating rules.\n"
        f"Read /a0/usr/Exocortex/interests.md for field-mode directives.\n"
        f"Log everything to /a0/usr/Exocortex/self-improvement/journal.jsonl.\n"
        f"At cycle end write to /a0/usr/Exocortex/office/feed.jsonl.\n\n"
        f"Begin."
    )


def _write_status(status: dict) -> None:
    """Atomically write current engine state to office/status.json."""
    try:
        os.makedirs(_OFFICE_DIR, exist_ok=True)
        tmp = _STATUS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(status, f)
        os.replace(tmp, _STATUS_PATH)
    except Exception:
        pass


def _load_config() -> dict:
    """Load idle engine config section from config.json, return {} on any error."""
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("idle_time_engine", {})
    except Exception:
        pass
    return {}
