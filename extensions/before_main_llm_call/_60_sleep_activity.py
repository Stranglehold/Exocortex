"""
Sleep Activity — Idle timer reset on LLM call start
====================================================
Hook: before_main_llm_call (_60_)

Updates the shared _sleep_last_activity timestamp at the start of every
agent LLM call. This fires as soon as the agent begins processing a user
message — before any tool calls — so the idle clock resets immediately
when the operator sends input, not after the first tool call fires.

Paired with tool_execute_after/_60_sleep_trigger.py, which resets the
same key on every tool call. Together they ensure any agent or operator
activity prevents sleep consolidation from firing mid-work.

State key: _sleep_last_activity (float, unix timestamp)
"""

import time
from agent import LoopData
from python.helpers.extension import Extension

ACTIVITY_KEY = "_sleep_last_activity"


class SleepActivity(Extension):
    """Resets idle clock at the start of every agent LLM call."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            self.agent.set_data(ACTIVITY_KEY, time.time())
        except Exception:
            pass
