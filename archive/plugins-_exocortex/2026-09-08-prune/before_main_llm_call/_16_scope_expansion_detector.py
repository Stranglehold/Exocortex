"""
_16_scope_expansion_detector.py — A2, OBSERVE-ONLY by default

Hook: before_main_llm_call
Priority: _16 — after _14_pace_plan_generator has created/loaded the plan this reads.
          (`_13` was the number in the spec; it is taken by `_13_reasoning_state`.)

SCOPE: DIRECTED TASKS ONLY
--------------------------
Jake rescoped this and the reasoning is worth carrying: the idle engine exists to give
the agent discretion, and "scope creep" during an autonomous cycle may be the agent
correctly following a dependency we never thought to assign. Vek's 300+ wiki pages came
from unassigned judgment. The BUILD-budget-creep anti-pattern was flagged five times and
never verified to be an actual problem.

So this fires only when the turn is a directed assignment. Autonomous output is governed
at the OUTPUT — the Phase B acceptor gate — not by watching the agent think.

OBSERVE-ONLY BY DEFAULT
-----------------------
`inject` defaults to FALSE. Detections are logged, nothing is said to the agent.

That is deliberate and follows DEC-045, which is now standing doctrine: advisory works
when the corrective action is a RARE branch and fails when it is the DEFAULT path. We do
not yet know scope expansion's base rate. If it turns out to be common, an advisory would
fail exactly the way the oversized-write lesson did — 300 recurrences against 302
surfacings with a flat learning curve — and we would only discover that after burning
another measurement window. So: measure first, then decide whether to speak.

Flip `scope_expansion.inject` to true once the 100-cycle rate justifies it.

WHAT IT DOES NOT DO
-------------------
- Does not block, gate, or modify anything. Ever. Not even with inject on — the
  strongest action available to it is appending an advisory line.
- Does not fire on idle-engine cycles.
- Does not call an LLM.
- Does not use word-count growth. See helpers/scope_expansion.py for why that heuristic
  does not transfer to this comparison.
"""

import json
import os
import sys
import time
from typing import Any

from agent import LoopData
from helpers.extension import Extension

_EXOCORTEX_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _EXOCORTEX_HELPERS not in sys.path:
    sys.path.insert(0, _EXOCORTEX_HELPERS)

CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"
ENGINE_STATE = "/a0/usr/workdir/workspace/office/engine_state.json"
DEFAULT_LOG = "/a0/usr/workdir/workspace/office/scope_expansion_log.jsonl"

_DEFAULTS = {
    "enabled": True,
    "inject": False,          # observe-only until the base rate says otherwise
    "min_signals": 2,         # of 3 heuristics, to call it a detection
    "log_path": DEFAULT_LOG,
}


def _cfg() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            c = json.load(fh).get("scope_expansion", {})
    except Exception:
        c = {}
    return {**_DEFAULTS, **(c if isinstance(c, dict) else {})}


def _engine_state() -> dict | None:
    """{} = file absent (no idle daemon here), None = present but unparseable.

    The distinction matters: absent is positive evidence that no autonomous cycles
    exist, whereas unparseable is a genuine unknown. See is_directed().
    """
    if not os.path.exists(ENGINE_STATE):
        return {}
    try:
        with open(ENGINE_STATE, encoding="utf-8") as fh:
            d = json.load(fh)
            return d if isinstance(d, dict) else None
    except Exception:
        return None


def _last_ai_message(history: list) -> str:
    """The agent's most recent statement — where drift actually shows up.

    Role discrimination matches _14_pace_plan_generator: user messages carry
    ai=False, agent messages ai=True.
    """
    if not history:
        return ""
    for msg in reversed(history):
        if not isinstance(msg, dict) or not msg.get("ai", False):
            continue
        content = msg.get("content", "")
        if isinstance(content, dict):
            for k in ("thoughts", "text", "message", "tool_args"):
                v = content.get(k)
                if isinstance(v, str) and v.strip():
                    return v
                if isinstance(v, list) and v:
                    return " ".join(str(x) for x in v)
            return json.dumps(content)[:4000]
        if isinstance(content, str) and content.strip():
            return content
    return ""


class ScopeExpansionDetector(Extension):
    """before_main_llm_call: observe scope drift on directed tasks."""

    def _log(self, msg: str) -> None:
        print(f"[SCOPE-EXP] {msg}", flush=True)

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            conf = _cfg()
            if not conf.get("enabled", True):
                return

            import scope_expansion as se

            plan = getattr(self.agent, "_pace_plan", None)
            if not isinstance(plan, dict):
                return          # no locked commitment to compare against

            anchor = str(plan.get("task_summary") or "")
            if not anchor:
                return

            ctx_id = ""
            try:
                ctx_id = str(self.agent.context.id)
            except Exception:
                pass

            directed, reason = se.is_directed(ctx_id, _engine_state())
            if not directed:
                return          # autonomous cycle, or unprovable — stay silent

            current = _last_ai_message(getattr(loop_data, "history_output", None) or [])
            if not current.strip():
                return

            result = se.detect(anchor, current)
            if result["count"] < int(conf["min_signals"]):
                return

            self._record(conf, plan, anchor, current, result, reason)

            if conf.get("inject", False):
                # The strongest thing this component may ever do.
                try:
                    self.agent.hist_add_warning(
                        "[SCOPE] Scope expansion detected against the original "
                        f"objective: \"{anchor[:160]}\". Signals: "
                        f"{', '.join(result['signals'])}. Confirm the expanded scope is "
                        "intentional, or narrow back to the original objective."
                    )
                except Exception:
                    pass
                self._log(f"detected + INJECTED ({result['count']} signals)")
            else:
                self._log(
                    f"detected (observe-only, not injected) — {result['count']} signals: "
                    f"{', '.join(result['signals'])}"
                )

        except Exception as e:
            try:
                self._log(f"skipped — {type(e).__name__}: {str(e)[:100]}")
            except Exception:
                pass

    def _record(self, conf: dict, plan: dict, anchor: str, current: str,
                result: dict, reason: str) -> None:
        """Append the detection with before/after text, for the 100-cycle rate analysis.

        Both texts are stored because the acceptance criterion is a FALSE-POSITIVE rate,
        and that cannot be judged from a signal name alone — someone has to be able to
        read what was actually said and disagree with the detector.
        """
        try:
            rec = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "plan_id": plan.get("plan_id", ""),
                "domain": plan.get("domain", ""),
                "current_step": plan.get("current_step"),
                "directed_reason": reason,
                "signals": result["signals"],
                "detail": result["detail"],
                "injected": bool(conf.get("inject", False)),
                "anchor": anchor[:400],
                "current": current[:1200],
            }
            path = conf.get("log_path") or DEFAULT_LOG
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
        except Exception as e:
            self._log(f"log write failed: {type(e).__name__}")
