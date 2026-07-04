"""
Step Budget Tracker — Progressive Turn-Count Awareness Injection
================================================================
Hook: message_loop_prompts_after (_08_)
Tier 1: Mechanical Safety — zero model calls, fires every turn

Tracks turn count per agent instance. Injects a [Step N/M] annotation
into the last user message in history_output every turn. Fires progressive
warning injections when the budget runs low:

  - 50% used  (once): gentle advisory — plan remaining work
  - 75% used  (once): escalated warning — begin wrapping up
  - ≥90% used (every turn): hard pressure — write output now
  - 100% used (every turn): exhaustion demand — stop all tools

Warnings at 50% and 75% fire exactly once (tracked in _step_budget_fired).
Per-turn pressure only activates at ≥90% — genuine emergency territory.
This prevents advisory noise during normal task execution.

Default budget: 80 turns (configurable via /a0/usr/plugins/_exocortex/config/config.json
under "step_budget_tracker": {"enabled": true, "max_steps": 80}).

Pattern source: OpenPlanter progressive warnings + Opus ST-012 guidance.
Does NOT hard-stop — warns and lets the agent decide. No LLM calls.
"""

import json
import os
from typing import Optional

from agent import LoopData
from helpers.extension import Extension

_CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"
_DEFAULT_MAX_STEPS = 80

_WARN_50 = "[STEP-BUDGET] BUDGET NOTE: 50% of step budget used ({used}/{max} steps). Plan your remaining work accordingly."
_WARN_75 = "[STEP-BUDGET] BUDGET WARNING: 75% of step budget used ({used}/{max} steps). Prioritize completing your current output. A partial result is better than no result."
_WARN_90 = "[STEP-BUDGET] BUDGET CRITICAL: {remaining} steps remaining. Write your output NOW. Do not start new sub-tasks."
_WARN_0 = "[STEP-BUDGET] BUDGET EXHAUSTED: {used}/{max} steps used. Report what you have found so far and stop. Do not call additional tools."


def _load_config(agent) -> dict:
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH) as fh:
                return json.load(fh).get("step_budget_tracker", {})
    except Exception:
        pass
    return {}


def _get_last_user_msg(history_output: list) -> Optional[dict]:
    for msg in reversed(history_output or []):
        if isinstance(msg, dict) and not msg.get("ai", True):
            if msg.get("content"):
                return msg
    return None


class StepBudgetTracker(Extension):
    """Injects step count and budget warnings into conversation context."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            cfg = _load_config(self.agent)
            if not cfg.get("enabled", True):
                return

            max_steps: int = int(cfg.get("max_steps", _DEFAULT_MAX_STEPS))

            # Increment turn counter
            step: int = getattr(self.agent, "_step_budget_count", 0) + 1
            self.agent._step_budget_count = step

            # Track which one-shot thresholds have already fired
            if not hasattr(self.agent, "_step_budget_fired"):
                self.agent._step_budget_fired = set()
            fired: set = self.agent._step_budget_fired

            history_output = getattr(loop_data, "history_output", None)
            user_msg = _get_last_user_msg(history_output)
            if not user_msg:
                return

            remaining = max_steps - step
            pct_used = int(100 * step / max_steps)

            step_tag = f"[Step {step}/{max_steps}]"

            # Determine warning to inject (if any)
            warning: str = ""
            if step >= max_steps:
                # Always fire on exhaustion
                warning = _WARN_0.format(used=step, max=max_steps)
            elif pct_used >= 90:
                # Per-turn pressure in final 10%
                warning = _WARN_90.format(remaining=remaining)
            elif pct_used >= 75 and "75" not in fired:
                # Fire once at 75%
                warning = _WARN_75.format(used=step, max=max_steps)
                fired.add("75")
            elif pct_used >= 50 and "50" not in fired:
                # Fire once at 50%
                warning = _WARN_50.format(used=step, max=max_steps)
                fired.add("50")

            # Cache-safe injection (2026-05-18). Previously this prepended
            # `{step_tag} {warning}` into user_msg["content"] — i.e. into the
            # last message of loop_data.history_output, which sits inside the
            # KV-cache-able prefix region. Because the tag rode whatever message
            # was current each turn, the SAME historical message rendered WITH
            # the tag the turn it was current and WITHOUT it every later turn —
            # shifting the prompt prefix and destroying server prefix-cache
            # reuse (measured: first turn-to-turn divergence at ~82.7%, ~9 min
            # cold prefill every turn). Volatile per-turn content must live
            # AFTER the stable prefix. extras_temporary is appended after
            # history by prepare_prompt() and cleared each turn, so it stays
            # per-turn fresh without mutating the cacheable prefix.
            try:
                if getattr(loop_data, "extras_temporary", None) is None:
                    loop_data.extras_temporary = {}
                loop_data.extras_temporary["step_budget"] = (
                    step_tag if not warning else f"{step_tag}\n{warning}"
                )
            except Exception:
                # Never fall back to history mutation — that reintroduces the
                # cache-busting prefix shift. Skipping the annotation for one
                # turn is strictly preferable.
                pass

            if step % 10 == 0 or warning:
                print(
                    f"[STEP-BUDGET] Step {step}/{max_steps} "
                    f"({100 - pct_used}% remaining)"
                    + (" — warning injected" if warning else ""),
                    flush=True,
                )

        except Exception as e:
            print(f"[STEP-BUDGET] Error (passthrough): {e}", flush=True)
