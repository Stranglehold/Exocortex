"""
Sleep Trigger — Agent-Zero Sleep Consolidation
===============================================
Hook: tool_execute_after (_60_)

Detects when the agent completes a response (response tool fires) and
schedules an asyncio idle-timeout task. Any subsequent tool activity
cancels the timer — the agent is still active. On timeout, Phase 1
consolidation runs: procedural memory deduplication + utility counter
initialization.

This is the idle detection mechanism. No wall-clock polling is needed:
the response tool firing = agent finished responding = idle window begins.
Any tool call = idle window ends.

Config: /a0/usr/Exocortex/sleep_config.json
  enabled: true/false (default: true)
  idle_threshold_minutes: 10 (default)

Phase 1 only. Phases 2-4 are future development.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Optional

from agent import LoopData
from helpers.extension import Extension

# Path injection for Exocortex modules
_EXOCORTEX_PATH = "/a0/usr/Exocortex"
if _EXOCORTEX_PATH not in sys.path:
    sys.path.insert(0, _EXOCORTEX_PATH)

CONFIG_PATH = "/a0/usr/Exocortex/sleep_config.json"
DEFAULT_IDLE_MINUTES = 10

# Per-context task registry — keyed by agent context ID so subagent response
# tool calls don't cancel or own the top-level agent's sleep timer.
_sleep_tasks: Dict[str, asyncio.Task] = {}


def _ctx_id(agent) -> str:
    """Stable identifier for this agent's context. Falls back to 'default'."""
    try:
        return str(agent.context.id)
    except Exception:
        return "default"


class SleepTrigger(Extension):
    """Idle trigger: schedules sleep consolidation after response tool fires."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            tool_name = kwargs.get("tool_name", "")
            ctx = _ctx_id(self.agent)

            # Prune completed tasks from registry (prevents unbounded growth)
            for k in list(_sleep_tasks):
                if _sleep_tasks[k].done():
                    del _sleep_tasks[k]

            # Any tool activity for this context cancels its pending sleep
            if ctx in _sleep_tasks and not _sleep_tasks[ctx].done():
                _sleep_tasks[ctx].cancel()
                del _sleep_tasks[ctx]

            # Response tool: this context's agent finished responding → schedule sleep
            if tool_name == "response":
                config = _load_config()
                if not config.get("enabled", True):
                    return
                if not config.get("phases", {}).get("phase1", {}).get("enabled", True):
                    return

                idle_minutes = config.get("idle_threshold_minutes", DEFAULT_IDLE_MINUTES)
                print(
                    f"[SLEEP] Response complete (ctx={ctx}). "
                    f"Scheduling consolidation in {idle_minutes}m.",
                    flush=True,
                )
                _sleep_tasks[ctx] = asyncio.create_task(
                    _idle_sleep(self.agent, idle_minutes, ctx)
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


# ── Async Sleep Coroutine ────────────────────────────────────────────────────

async def _idle_sleep(agent, idle_minutes: float, ctx: str) -> None:
    """
    Wait idle_minutes, then run Phase 1 consolidation.
    CancelledError is expected and handled gracefully — it means the operator
    sent a new message before the threshold elapsed.
    """
    try:
        await asyncio.sleep(idle_minutes * 60)
        print(f"[SLEEP] Idle threshold reached (ctx={ctx}). Starting consolidation.", flush=True)
        await _run_phase1(agent, ctx)
    except asyncio.CancelledError:
        print(f"[SLEEP] Sleep cancelled (ctx={ctx}) — new operator activity detected.", flush=True)
    except Exception as e:
        print(f"[SLEEP] Idle sleep error (ctx={ctx}): {e}", flush=True)


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
