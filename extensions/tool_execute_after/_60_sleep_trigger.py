"""
Sleep Trigger — Agent-Zero Sleep Consolidation
===============================================
Hook: tool_execute_after (_60_)

Detects idle periods and runs sleep consolidation when neither the agent
nor the operator has been active for idle_threshold_minutes.

Mechanism:
  - Every tool call writes time.time() to _sleep_last_activity agent data.
  - The companion before_main_llm_call/_60_sleep_activity.py writes the
    same key at the start of every LLM call, so user messages reset the
    clock immediately — not after the first tool call fires.
  - On response tool: if no idle monitor is running for this context,
    start one. The monitor polls every POLL_INTERVAL_SECONDS and compares
    current time against _sleep_last_activity. When the gap exceeds
    idle_threshold_minutes, consolidation runs.

This replaces the old countdown-cancel approach. The key difference:
activity is recorded by timestamp, not by task cancellation, so the
full window of user + agent quiescence is measured correctly.

Config: /a0/usr/Exocortex/sleep_config.json
  enabled: true/false (default: true)
  idle_threshold_minutes: 10 (default)
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict

from agent import LoopData
from helpers.extension import Extension

# Path injection for Exocortex modules
_EXOCORTEX_PATH = "/a0/usr/Exocortex"
if _EXOCORTEX_PATH not in sys.path:
    sys.path.insert(0, _EXOCORTEX_PATH)

ACTIVITY_KEY = "_sleep_last_activity"
CONFIG_PATH = "/a0/usr/Exocortex/sleep_config.json"
DEFAULT_IDLE_MINUTES = 10
POLL_INTERVAL_SECONDS = 60

# Per-context monitor registry — keyed by context ID so subagent activity
# doesn't interfere with the top-level agent's idle monitor.
_sleep_tasks: Dict[str, asyncio.Task] = {}


def _ctx_id(agent) -> str:
    """Stable identifier for this agent's context. Falls back to 'default'."""
    try:
        return str(agent.context.id)
    except Exception:
        return "default"


class SleepTrigger(Extension):
    """Records tool activity and starts the idle monitor after response tool."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            tool_name = kwargs.get("tool_name", "")
            ctx = _ctx_id(self.agent)

            # Always record this tool call as activity
            self.agent.set_data(ACTIVITY_KEY, time.time())

            # Prune completed monitor tasks from registry
            for k in list(_sleep_tasks):
                if _sleep_tasks[k].done():
                    del _sleep_tasks[k]

            # Response tool: start idle monitor if not already running
            if tool_name == "response":
                config = _load_config()
                if not config.get("enabled", True):
                    return
                if not config.get("phases", {}).get("phase1", {}).get("enabled", True):
                    return
                if ctx in _sleep_tasks:
                    return  # monitor already running for this context

                idle_minutes = config.get("idle_threshold_minutes", DEFAULT_IDLE_MINUTES)
                print(
                    f"[SLEEP] Response complete (ctx={ctx}). "
                    f"Idle monitor started (threshold={idle_minutes}m, "
                    f"poll={POLL_INTERVAL_SECONDS}s).",
                    flush=True,
                )
                _sleep_tasks[ctx] = asyncio.create_task(
                    _idle_monitor(self.agent, idle_minutes, ctx)
                )

        except Exception as e:
            # Passthrough — never crash the agent for sleep logic failures
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[SLEEP] Trigger error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Idle Monitor ─────────────────────────────────────────────────────────────

async def _idle_monitor(agent, idle_minutes: float, ctx: str) -> None:
    """
    Poll every POLL_INTERVAL_SECONDS. Fire consolidation once the gap
    between now and _sleep_last_activity exceeds idle_threshold_minutes.

    Stays alive across agent activity — the timestamp check handles it.
    Exits after consolidation runs (new response will restart the monitor).
    """
    threshold = idle_minutes * 60
    try:
        while True:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            last = agent.get_data(ACTIVITY_KEY) or 0
            idle_seconds = time.time() - last
            if idle_seconds >= threshold:
                print(
                    f"[SLEEP] Idle {idle_seconds:.0f}s >= threshold {threshold:.0f}s "
                    f"(ctx={ctx}). Starting consolidation.",
                    flush=True,
                )
                await _run_phase1(agent, ctx)
                break  # one consolidation per idle period; next response restarts monitor
    except asyncio.CancelledError:
        print(f"[SLEEP] Monitor cancelled (ctx={ctx}).", flush=True)
    except Exception as e:
        print(f"[SLEEP] Monitor error (ctx={ctx}): {e}", flush=True)


async def _run_phase1(agent, ctx: str) -> None:
    """Run Phase 0 through Phase 4 consolidation."""
    from sleep_consolidation import (
        run_phase0_consolidation,
        run_phase1_consolidation,
        run_phase2_consolidation,
        run_phase3_consolidation,
        run_phase4_consolidation,
    )

    # Prefer context ID as session identifier; fall back to env var
    session_id = ctx if ctx != "default" else os.environ.get("A0_CHAT_ID", "unknown")

    # Phase 0: staging tier lifecycle (promotion, archival, carry-forward)
    try:
        r0 = run_phase0_consolidation(session_id)
        summary0 = (
            f"Phase 0 — promoted={r0['observations_promoted']}, "
            f"intentions={r0['intentions_carried']}, "
            f"relational={r0['relationals_anchored']}, "
            f"canaries_archived={r0['canaries_archived']}, "
            f"active={r0['total_active']}"
        )
        print(f"[SLEEP] {summary0}", flush=True)
        try:
            agent.context.log.log(type="info", content=f"[SLEEP] {summary0}")
        except Exception:
            pass
    except Exception as e:
        print(f"[SLEEP] Phase 0 error: {e}", flush=True)

    # Phase 1: dedup + utility init
    try:
        r1 = run_phase1_consolidation(session_id)
        summary1 = (
            f"Phase 1 — utility_init={r1['utility_fields_initialized']}, "
            f"dedup_removed={r1['duplicates_removed']}, "
            f"entries={r1['total_entries_before']}→{r1['total_entries_after']}"
        )
        print(f"[SLEEP] {summary1}", flush=True)
        try:
            agent.context.log.log(type="info", content=f"[SLEEP] {summary1}")
        except Exception:
            pass
    except Exception as e:
        print(f"[SLEEP] Phase 1 error: {e}", flush=True)

    # Phase 2: episode chunking + missed anti-pattern capture
    try:
        r2 = run_phase2_consolidation(session_id)
        summary2 = (
            f"Phase 2 — sessions={r2['sessions_analyzed']}, "
            f"episodes={r2['episodes_chunked']}, "
            f"loops_found={r2['loop_patterns_found']}, "
            f"captured={r2['anti_patterns_captured']}, "
            f"already_covered={r2['already_covered']}"
        )
        print(f"[SLEEP] {summary2}", flush=True)
        try:
            agent.context.log.log(type="info", content=f"[SLEEP] {summary2}")
        except Exception:
            pass
    except Exception as e:
        print(f"[SLEEP] Phase 2 error: {e}", flush=True)

    # Phase 3: operator interaction modeling
    try:
        r3 = run_phase3_consolidation(session_id)
        summary3 = (
            f"Phase 3 — sessions={r3['sessions_analyzed']}, "
            f"avg_turn_len={r3['avg_operator_turn_length']}, "
            f"floor_giving_rate={r3['floor_giving_rate']}, "
            f"avg_corrections={r3['avg_corrections']}, "
            f"profile_updated={r3['profile_updated']}"
        )
        print(f"[SLEEP] {summary3}", flush=True)
        try:
            agent.context.log.log(type="info", content=f"[SLEEP] {summary3}")
        except Exception:
            pass
    except Exception as e:
        print(f"[SLEEP] Phase 3 error: {e}", flush=True)

    # Phase 4: loop-period memory adjudication
    try:
        r4 = await run_phase4_consolidation(agent, session_id)
        summary4 = (
            f"Phase 4 — found={r4['loop_period_found']}, "
            f"promoted={r4['promoted_to_inferred']}, "
            f"deprecated={r4['deprecated']}, "
            f"ambiguous={r4['left_ambiguous']}"
        )
        print(f"[SLEEP] {summary4}", flush=True)
        try:
            agent.context.log.log(type="info", content=f"[SLEEP] {summary4}")
        except Exception:
            pass
    except Exception as e:
        print(f"[SLEEP] Phase 4 error: {e}", flush=True)


# ── Config Loader ────────────────────────────────────────────────────────────

def _load_config() -> dict:
    """Load sleep config, returning defaults if the file is missing or malformed."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "enabled": True,
        "idle_threshold_minutes": DEFAULT_IDLE_MINUTES,
        "phases": {
            "phase1": {
                "enabled": True,
                "deduplicate_anti_patterns": True,
                "initialize_utility_fields": True,
            }
        },
    }
