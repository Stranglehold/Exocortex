"""
Methodology Tracker — Automatic Per-Cycle Execution Instrumentation
====================================================================
Hook: message_loop_prompts_after (_09_)
Tier 1: Mechanical — zero LLM calls, fires every turn

Automatically tracks execution methodology per IDLE cycle:
- Cycle type (EXPLORE/BUILD/MAINTAIN, from engine_state.json last_cycle_type)
- Strategy tag (from PACE plan domain)
- Affect state transitions (from _12 classifier, read via agent.get_data)
- Steps taken, tool calls, outcome

Data accumulates on agent attrs during the cycle. Tool call tracking happens in
the companion _32_tool_call_tracker (tool_execute_after). Finalization to
methodology_tracker.jsonl is triggered by _33_methodology_finalizer on the
cycle-closing response() call, OR by this extension's boundary detection when a
cycle ends abnormally (a new idle cycle starts without a clean response).

Design: Opus — Methodology Learning Layer spec, June 2026
Pattern source: _08_step_budget_tracker (same hook, attr-accumulation)
Kestrel gap fixes (2026-06-21, verified against running code):
  - cycle_type from engine_state.json (the nonexistent _idle_current_mode attr was the original read)
  - affect via agent.get_data("_affect_state") — the affect layer STORES with set_data, not setattr
  - idle-cycle gating (cycle_active) so interactive turns don't pollute the data
  - cycle-boundary detection via last_cycle_start → captures abnormal (no-response) cycles as "incomplete"
  - outcome inference so the strategy advisor has success/failure signal, not all-"completed"
"""

import json
import os
import time

from agent import Agent, LoopData
from helpers.extension import Extension

CONFIG_PATH   = "/a0/usr/Exocortex/config.json"
TRACKER_FILE  = "/a0/usr/workdir/methodology_tracker.jsonl"
ENGINE_STATE  = "/a0/usr/workdir/workspace/office/engine_state.json"

# Agent attr key (persists across turns within a session)
CYCLE_DATA_KEY = "_methodology_cycle_data"
AFFECT_DATA_KEY = "_affect_state"   # set via agent.set_data by reasoning_stream_end/_12

_DEFAULTS = {"enabled": True}


def _cfg() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            return json.load(fh).get("methodology_tracker", _DEFAULTS)
    except Exception:
        return _DEFAULTS


def _engine_state() -> dict:
    try:
        with open(ENGINE_STATE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


class MethodologyTracker(Extension):
    """message_loop_prompts_after: accumulate per-idle-cycle methodology data."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            if not _cfg().get("enabled", True):
                return
            if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
                return  # skip subordinates

            state = _engine_state()
            active = bool(state.get("cycle_active", False))
            cur_start = state.get("last_cycle_start", 0)

            data = getattr(self.agent, CYCLE_DATA_KEY, None)

            # Boundary: a tracked cycle we've moved past ended abnormally (no clean
            # response → _33 never finalized it). Flush it as "incomplete".
            if data is not None and (not active or data.get("_cycle_start_id") != cur_start):
                finalize(self.agent, outcome="incomplete")
                data = None

            # Only track idle cycles (EXPLORE/BUILD/MAINTAIN) — not interactive turns.
            if not active:
                return

            # Init a new cycle on first tracked turn
            if data is None:
                data = self._init_cycle(state, cur_start)

            # Per-turn accumulation
            data["steps_taken"] = data.get("steps_taken", 0) + 1

            affect = self._read_affect()
            if affect != "unknown":
                tr = data.get("affect_transitions", [])
                if not tr or tr[-1] != affect:
                    tr.append(affect)
                    data["affect_transitions"] = tr
                data["affect_current"] = affect

            strategy = self._read_strategy()
            if strategy and strategy != "default":
                data["strategy_tag"] = strategy

            setattr(self.agent, CYCLE_DATA_KEY, data)

        except Exception as e:
            print(f"[METHOD-TRACK] Error (passthrough): {e}", flush=True)

    def _init_cycle(self, state: dict, cur_start) -> dict:
        data = {
            "cycle_id": f"cycle_{int(time.time())}",
            "_cycle_start_id": cur_start,                       # internal: boundary key (stripped at finalize)
            "ts_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cycle_type": str(state.get("last_cycle_type", "unknown")),
            "strategy_tag": self._read_strategy(),
            "affect_start": self._read_affect(),
            "affect_transitions": [],
            "steps_taken": 0,
            "tools": [],          # per-call detail, compacted away at finalize
            "tool_ok": 0,
            "tool_fail": 0,
        }
        setattr(self.agent, CYCLE_DATA_KEY, data)
        print(f"[METHOD-TRACK] Cycle init: type={data['cycle_type']} strategy={data['strategy_tag']}", flush=True)
        return data

    def _read_strategy(self) -> str:
        try:
            plan = getattr(self.agent, "_pace_plan", None)
            if isinstance(plan, dict):
                domain = str(plan.get("domain", "")).strip()
                if domain:
                    return domain
        except Exception:
            pass
        return "default"

    def _read_affect(self) -> str:
        try:
            a = self.agent.get_data(AFFECT_DATA_KEY)   # affect layer stores via set_data
            if a:
                return str(a)
        except Exception:
            pass
        return "unknown"


# === Public API for companion extensions (operate on the shared agent object) ===

def record_tool(agent, tool_name: str, success: bool):
    """Called from _32_tool_call_tracker (tool_execute_after)."""
    data = getattr(agent, CYCLE_DATA_KEY, None)
    if data is None:
        return
    data["tools"].append({"tool": tool_name, "ok": success, "step": data.get("steps_taken", 0)})
    if success:
        data["tool_ok"] = data.get("tool_ok", 0) + 1
    else:
        data["tool_fail"] = data.get("tool_fail", 0) + 1


def _infer_outcome(data: dict) -> str:
    """Derive a meaningful outcome so the advisor can distinguish good/bad strategies.
    A cycle that delivered a response but ended in struggle is NOT a clean success."""
    affect = data.get("affect_current", "unknown")
    if affect == "DESPERATION":
        return "desperation"
    if affect == "STAGNATION":
        return "stalled"
    total = data.get("tool_ok", 0) + data.get("tool_fail", 0)
    if total and (data.get("tool_ok", 0) / total) < 0.5:
        return "error"
    return "completed"


def finalize(agent, outcome: str = None, artifacts: list = None):
    """Write the per-cycle record to JSONL. Called by _33 on response (outcome inferred)
    or by the boundary detector above (outcome='incomplete'). Resets cycle state."""
    data = getattr(agent, CYCLE_DATA_KEY, None)
    if data is None:
        return

    if outcome is None:
        outcome = _infer_outcome(data)

    data["ts_end"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    data["outcome"] = outcome
    data["affect_end"] = data.get("affect_current", "unknown")
    data["artifacts"] = artifacts or []

    total = data.get("tool_ok", 0) + data.get("tool_fail", 0)
    data["tool_count"] = total
    data["tool_success_rate"] = round(data["tool_ok"] / total, 3) if total else None
    data["unique_tools"] = sorted(set(t["tool"] for t in data.get("tools", [])))
    data["tools_summary"] = data["unique_tools"]
    data.pop("tools", None)             # don't store every individual call
    data.pop("_cycle_start_id", None)   # internal boundary key

    try:
        os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
        with open(TRACKER_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
        print(f"[METHOD-TRACK] Finalized: {data.get('cycle_type')}/{data.get('strategy_tag')} "
              f"steps={data.get('steps_taken')} tools={total} outcome={outcome}", flush=True)
    except Exception as e:
        print(f"[METHOD-TRACK] Write error: {e}", flush=True)

    setattr(agent, CYCLE_DATA_KEY, None)
