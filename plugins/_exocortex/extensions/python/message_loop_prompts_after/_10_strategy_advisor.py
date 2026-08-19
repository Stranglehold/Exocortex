"""
Strategy Advisor — Methodology-Aware Strategy Recommendation
=============================================================
Hook: message_loop_prompts_after (_10_)
Companion to: _09_methodology_tracker (provides the data)
              _24_skill_surfacer (provides failure-lesson surfacing)

Reads the methodology_tracker.jsonl history and recommends strategies
based on what has worked for similar task types in the past. Injects
into extras_temporary (cache-safe, cleared each turn).

Affect-gated:
  FLOW       → skip (model is performing well, don't add noise)
  FRICTION   → recommend best-known strategy + explore prompt
  STAGNATION → recommend explicit alternative + "break the stall"
  FRUSTRATION → full strategy analysis + escalation suggestion

Design: Opus — Methodology Learning Layer spec, June 2026
"""

import json
import os
from typing import Optional, Tuple

from agent import Agent, LoopData
from helpers.extension import Extension

TRACKER_FILE  = "/a0/usr/workdir/methodology_tracker.jsonl"
# Portable across container layouts: plugin (v2) and agent-path/Exocortex (v16/v17).
CONFIG_PATH   = next(
    (_p for _p in ("/a0/usr/plugins/_exocortex/config/config.json",
                   "/a0/usr/Exocortex/config.json") if os.path.exists(_p)),
    "/a0/usr/plugins/_exocortex/config/config.json",
)
ENGINE_STATE  = "/a0/usr/workdir/workspace/office/engine_state.json"
AFFECT_DATA_KEY = "_affect_state"   # set via agent.set_data by reasoning_stream_end/_12
MIN_RECORDS   = 5    # minimum history records before making recommendations
MIN_RECOMMEND = 3    # minimum records for a specific strategy before recommending it

_DEFAULTS = {"enabled": True}

# Conversational / reflective / meta turns don't want strategy advice — stay quiet.
# Uses the CURRENT-turn BST domain (loop_data.extras_persistent["_bst_domain"]).
_SKIP_DOMAINS = {"conversation", "philosophical", "meta_cognitive"}


def _cfg() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            return json.load(fh).get("strategy_advisor", _DEFAULTS)
    except Exception:
        return _DEFAULTS


def _read_history() -> list:
    """Read all methodology tracker records."""
    records = []
    try:
        if not os.path.exists(TRACKER_FILE):
            return records
        with open(TRACKER_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        pass
    return records


def _analyze_strategies(records: list, cycle_type: str) -> dict:
    """
    Analyze strategy performance for a given cycle type.
    
    Returns: {
        "best": (strategy_tag, success_rate, count),
        "worst": (strategy_tag, success_rate, count),
        "all": {strategy_tag: {"total": N, "completed": N, "rate": float}},
        "total_records": int
    }
    """
    relevant = [r for r in records if r.get("cycle_type") == cycle_type]
    
    if len(relevant) < MIN_RECORDS:
        return {"best": None, "worst": None, "all": {}, "total_records": len(relevant)}
    
    strategies = {}
    for r in relevant:
        tag = r.get("strategy_tag", "default")
        if tag not in strategies:
            strategies[tag] = {"total": 0, "completed": 0}
        strategies[tag]["total"] += 1
        if r.get("outcome") == "completed":
            strategies[tag]["completed"] += 1
    
    # Compute rates
    for tag, data in strategies.items():
        data["rate"] = round(data["completed"] / data["total"], 3) if data["total"] > 0 else 0.0
    
    # Find best and worst (with minimum record threshold)
    qualified = {k: v for k, v in strategies.items() if v["total"] >= MIN_RECOMMEND}
    
    best = max(qualified.items(), key=lambda x: x[1]["rate"]) if qualified else None
    worst = min(qualified.items(), key=lambda x: x[1]["rate"]) if qualified else None
    
    return {
        "best": (best[0], best[1]["rate"], best[1]["total"]) if best else None,
        "worst": (worst[0], worst[1]["rate"], worst[1]["total"]) if worst else None,
        "all": strategies,
        "total_records": len(relevant),
    }


def _format_recommendation(analysis: dict, affect: str, cycle_type: str) -> Optional[str]:
    """
    Format a strategy recommendation based on analysis and affect state.
    Returns None if no recommendation warranted.
    """
    if affect == "FLOW" or affect == "unknown":
        return None  # Don't add noise during FLOW
    
    best = analysis.get("best")
    if not best:
        return None  # Not enough data
    
    tag, rate, count = best
    pct = int(rate * 100)
    
    if affect == "FRICTION":
        return (
            f"[STRATEGY NOTE] For {cycle_type} tasks, "
            f"'{tag}' approach has succeeded {pct}% of the time "
            f"(over {count} cycles). Consider adopting this approach. "
            f"If your current approach isn't working, try switching."
        )
    
    elif affect in ("STAGNATION", "FRUSTRATION", "DESPERATION"):
        # More assertive — suggest a specific change
        worst = analysis.get("worst")
        avoid_note = ""
        if worst:
            w_tag, w_rate, w_count = worst
            if w_tag != tag:  # Don't say "avoid X" if X is also the best
                avoid_note = f" Avoid '{w_tag}' ({int(w_rate*100)}% success over {w_count} cycles)."
        
        return (
            f"[STRATEGY ALERT] You appear stuck. On {cycle_type} tasks, "
            f"'{tag}' has the highest success rate ({pct}%, n={count}).{avoid_note} "
            f"Switch to this approach now. Start with one concrete step rather than "
            f"re-planning."
        )
    
    return None


class StrategyAdvisor(Extension):
    """message_loop_prompts_after: recommend strategies based on execution history."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            if not _cfg().get("enabled", True):
                return
            if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
                return

            # Turn-type gate: no strategy advice on conversational / reflective / meta turns
            # (Vek: it fires when I'm not stuck and don't need it). Current-turn domain.
            _ep = getattr(loop_data, "extras_persistent", {}) or {}
            _dom = (_ep.get("_bst_domain") or "").split("+")[0].strip()
            if _dom in _SKIP_DOMAINS:
                print(f"[STRATEGY] silent — {_dom} turn (no advice on conversational turns)", flush=True)
                return

            # Read current affect state (affect layer stores via set_data, not setattr)
            affect = self.agent.get_data(AFFECT_DATA_KEY) or "unknown"

            # Skip during FLOW — no noise when things are working
            if affect in ("FLOW", "unknown"):
                return

            # Read cycle type
            cycle_type = self._get_cycle_type()
            if cycle_type == "unknown":
                return

            # Analyze history
            history = _read_history()
            if len(history) < MIN_RECORDS:
                return  # Not enough data yet

            analysis = _analyze_strategies(history, cycle_type)
            
            # Format recommendation
            rec = _format_recommendation(analysis, affect, cycle_type)
            if not rec:
                return

            # Inject into extras_temporary (cache-safe, same pattern as _08)
            try:
                if getattr(loop_data, "extras_temporary", None) is None:
                    loop_data.extras_temporary = {}
                loop_data.extras_temporary["strategy_advisor"] = rec
            except Exception:
                pass

            print(
                f"[STRATEGY] {affect}/{cycle_type}: recommended '{analysis['best'][0]}' "
                f"({int(analysis['best'][1]*100)}% over {analysis['best'][2]} cycles)",
                flush=True,
            )

        except Exception as e:
            print(f"[STRATEGY] Error (passthrough): {e}", flush=True)

    def _get_cycle_type(self) -> str:
        # Canonical source: engine_state.json last_cycle_type (EXPLORE/BUILD/MAINTAIN).
        # Must match the value _09 records, so the advisor groups on the same key.
        try:
            with open(ENGINE_STATE, encoding="utf-8") as fh:
                ct = json.load(fh).get("last_cycle_type")
                if ct:
                    return str(ct)
        except Exception:
            pass
        return "unknown"
