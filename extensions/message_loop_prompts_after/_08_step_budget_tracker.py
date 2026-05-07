"""
Step Budget Tracker — Progressive Turn-Count Awareness Injection
================================================================
Hook: message_loop_prompts_after (_08_)
Tier 1: Mechanical Safety — zero model calls, fires every turn

Tracks turn count per agent instance. Injects a [Step N/M] annotation
into the last user message in history_output every turn. Fires progressive
warning injections when the budget runs low:
  - 50% remaining: gentle advisory
  - 25% remaining: strong warning to consolidate and respond
  - 0% remaining: final-answer demand

Prevents silent budget exhaustion — a model aware it has 8 steps left
plans and prioritizes differently than one that thinks turns are unlimited.

Default budget: 80 turns (configurable via /a0/usr/Exocortex/config.json
under "step_budget_tracker": {"enabled": true, "max_steps": 80}).

Pattern source: OpenPlanter progressive warnings at 50%/25% + Claude Code
max_turns hard ceiling. Does NOT hard-stop — warns and lets the agent decide.
No LLM calls.
"""

import json
import os
from typing import Optional

from agent import LoopData
from helpers.extension import Extension

_CONFIG_PATH = "/a0/usr/Exocortex/config.json"
_DEFAULT_MAX_STEPS = 80

_WARN_50 = "[STEP-BUDGET] Advisory: you have used {used} of {max} steps ({pct}%). Consider consolidating findings before context grows further."
_WARN_25 = "[STEP-BUDGET] Warning: only {remaining} steps remain ({pct}% of budget). Begin wrapping up. Summarize findings and call response unless the task requires more steps."
_WARN_0 = "[STEP-BUDGET] Budget exhausted: {used}/{max} steps used. Report what you have found so far and stop. Do not call additional tools."


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

            history_output = getattr(loop_data, "history_output", None)
            user_msg = _get_last_user_msg(history_output)
            if not user_msg:
                return

            remaining = max_steps - step
            pct_used = int(100 * step / max_steps)
            pct_remaining = 100 - pct_used

            # Always inject step counter prefix
            step_tag = f"[Step {step}/{max_steps}]"

            # Determine if a warning block should be prepended too
            warning: str = ""
            if step >= max_steps:
                warning = _WARN_0.format(used=step, max=max_steps)
            elif pct_remaining <= 25:
                warning = _WARN_25.format(
                    remaining=remaining, pct=pct_remaining
                )
            elif pct_remaining <= 50:
                warning = _WARN_50.format(
                    used=step, max=max_steps, pct=pct_used
                )

            existing = str(user_msg.get("content", ""))
            if warning:
                user_msg["content"] = f"{warning}\n\n{step_tag} {existing}"
            else:
                user_msg["content"] = f"{step_tag} {existing}"

            if step % 10 == 0 or warning:
                print(
                    f"[STEP-BUDGET] Step {step}/{max_steps} "
                    f"({pct_remaining}% remaining)"
                    + (f" — warning injected" if warning else ""),
                    flush=True,
                )

        except Exception as e:
            print(f"[STEP-BUDGET] Error (passthrough): {e}", flush=True)
