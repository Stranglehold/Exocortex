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
  idle_threshold_seconds: 1800      # 30 min — time since last real user session
  cooldown_seconds: 3600            # 60 min — minimum gap between cycles
  max_steps_per_cycle: 20
  workshop_field_ratio: "3:1"

State keys (stored on agent.data):
  _idle_last_user_ts      — float: time.time() set at end of any real user session
  _idle_last_cycle_end_ts — float: time.time() set at end of each idle cycle
  idle_mode               — bool: True while an idle cycle is active
  idle_cycle_count        — int: total completed cycles (drives cycle type selection)

Design notes:
  - Monitor starts on the FIRST tool call after restart (not only on response tool).
    This bootstraps the engine without requiring a user message post-restart.
  - _idle_last_user_ts is initialized to time.time() on first run so the agent
    waits the full idle threshold before the first cycle (grace period).
  - The monitor is a PERSISTENT LOOP — it never exits. No need for the response
    tool to restart it after each cycle.
  - State transitions (cycle end, interrupt detection) still happen on response tool.

Office panel feed: /a0/usr/Exocortex/office/feed.jsonl (agent writes at cycle end)
Status indicator:  /a0/usr/Exocortex/office/status.json (trigger writes on transitions)
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

# Prefix injected at the start of every idle activation prompt.
# Used to distinguish idle-cycle user messages from real user messages.
_ACTIVATION_SENTINEL = "## IDLE-TIME CYCLE ACTIVATED"

_POLL_INTERVAL = 60  # seconds between idle monitor checks

# Per-context asyncio monitor task registry
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

            # ── Bootstrap: initialize timestamp on first-ever tool call ──────
            # Sets _idle_last_user_ts to now if never set, so the engine waits
            # the full idle threshold before firing (grace period after restart).
            if agent.get_data(_KEY_LAST_USER_TS) is None:
                agent.set_data(_KEY_LAST_USER_TS, time.time())
                print("[IDLE] Engine initialized. Idle clock starts now.", flush=True)

            # ── Start persistent monitor on ANY tool call if not running ─────
            # The monitor is a perpetual loop; no restart needed after each cycle.
            for k in list(_idle_tasks):
                if _idle_tasks[k].done():
                    del _idle_tasks[k]

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

            # ── State transitions only happen on response tool ───────────────
            if tool_name != "response":
                return

            idle_mode = agent.get_data(_KEY_IDLE_MODE)

            if idle_mode:
                # An idle cycle just ended (completed or interrupted by user).
                interrupted = _last_user_msg_is_real(agent)
                agent.set_data(_KEY_IDLE_MODE, False)
                cycle_n = (agent.get_data(_KEY_CYCLE_COUNT) or 0) + 1
                agent.set_data(_KEY_CYCLE_COUNT, cycle_n)
                agent.set_data(_KEY_LAST_CYCLE_END, time.time())

                if interrupted:
                    # Real user message arrived mid-cycle — reset idle timer too
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
                # Real user session just ended — reset idle clock
                agent.set_data(_KEY_LAST_USER_TS, time.time())
                _write_status({"state": "idle", "label": "Available"})

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
    Persistent loop that checks idle conditions every _POLL_INTERVAL seconds.

    Fires an autonomous idle cycle when:
      - time since last real user session >= idle_threshold_seconds
      - time since last idle cycle end >= cooldown_seconds
      - agent is not currently in an idle cycle

    Never exits — restarts after each cycle without needing a response tool trigger.
    Reloads config every iteration so live threshold changes take effect.
    """
    print(f"[IDLE] Monitor running (ctx={ctx}).", flush=True)
    try:
        while True:
            await asyncio.sleep(_POLL_INTERVAL)

            # Reload config so live edits (e.g. threshold changes for testing) take effect
            config = _load_config()
            if not config.get("enabled", True):
                continue

            # Skip if already in an idle cycle
            if agent.get_data(_KEY_IDLE_MODE):
                continue

            threshold = config.get("idle_threshold_seconds", 1800)
            cooldown = config.get("cooldown_seconds", 3600)

            now = time.time()
            last_user = agent.get_data(_KEY_LAST_USER_TS) or 0
            last_cycle = agent.get_data(_KEY_LAST_CYCLE_END) or 0

            idle_seconds = now - last_user
            since_cycle = now - last_cycle

            if idle_seconds < threshold:
                continue
            if since_cycle < cooldown:
                continue

            # ── Fire idle cycle ──────────────────────────────────────────────
            cycle_count = agent.get_data(_KEY_CYCLE_COUNT) or 0
            cycle_type = _determine_cycle_type(cycle_count, config)
            max_steps = config.get("max_steps_per_cycle", 20)

            print(
                f"[IDLE] Activating {cycle_type} cycle #{cycle_count + 1} "
                f"(idle={idle_seconds:.0f}s >= {threshold}s, ctx={ctx}).",
                flush=True,
            )

            # Set flag BEFORE communicate() so the first tool-use inside the
            # cycle sees idle_mode=True immediately
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
                print(f"[IDLE] communicate() failed: {e}", flush=True)
                agent.set_data(_KEY_IDLE_MODE, False)
                # Back off before trying again — update last_cycle so cooldown applies
                agent.set_data(_KEY_LAST_CYCLE_END, time.time())
                _write_status({"state": "idle", "label": "Available"})

            # Loop continues — next cycle will be gated by cooldown and idle_mode

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
    True means the idle cycle was interrupted by the user.
    """
    try:
        for msg in reversed(agent.history.output()):
            if msg.get("ai", True):  # ai=True = AI message, skip
                continue
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
