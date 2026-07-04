"""
Exocortex Stack Context — System Prompt Injection
==================================================
Hook: system_prompt
Priority: _15 (after stock framework sections _10–_14)

Appends two static Exocortex context blocks to the system prompt:

  1. agent.system.model_awareness.md  — self-awareness notes (confabulation
     risk, finite context, memory system)
  2. agent.system.capabilities.md    — extended capabilities summary (memory,
     planning, self-monitoring, skills)

Why system_prompt instead of before_main_llm_call:
  - These blocks are static — they don't change turn to turn.
  - System prompt content is persistent and doesn't consume user-message
    space or compete with turn-level injections.
  - Dynamic per-turn injections (_13_operator_profile, _13_reasoning_state,
    etc.) remain in before_main_llm_call where they belong.

Graceful degradation: if either prompt file is missing, the extension skips
it silently. No crash, no warning — the agent just runs without that section.

Log tag: [SYS-EXOCORTEX]
"""

from typing import Any

from agent import Agent, LoopData
from helpers.extension import Extension

PROMPT_FILES = [
    "agent.system.model_awareness.md",
    "agent.system.capabilities.md",
]


class ExocortexStackContext(Extension):

    async def execute(
        self,
        system_prompt: list = [],
        loop_data: LoopData = LoopData(),
        **kwargs: Any,
    ):
        if not self.agent:
            return

        sections = []
        loaded = []

        for fname in PROMPT_FILES:
            try:
                content = self.agent.read_prompt(fname)
                if content and content.strip():
                    sections.append(content.strip())
                    loaded.append(fname)
            except Exception:
                pass  # Missing file — skip silently

        if not sections:
            return

        system_prompt.append("\n\n".join(sections))

        print(
            f"[SYS-EXOCORTEX] Injected {len(loaded)} section(s): "
            f"{', '.join(loaded)}",
            flush=True,
        )
