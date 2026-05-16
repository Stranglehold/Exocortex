"""
Reasoning State Injector — Working-Hook Pair to _13
====================================================
Hook: message_loop_prompts_after
Priority: _22 (after _21_constraint_heartbeat, before _55_memory_relevance_filter)

This is the consumer side of the reasoning state pair.

  Generator side (turn N, message_loop_end):
    _49_reasoning_state_update — compresses turn N's reasoning into agent._reasoning_state

  Generator side (turn N+1, before_main_llm_call):
    _13_reasoning_state — bootstrap from staging if needed, also attempts injection
                          (its injection is silently discarded — seam #7)

  THIS FILE (turn N+1, message_loop_prompts_after):
    Reads agent._reasoning_state and injects into loop_data.history_output[-1].
    This is the hook where history_output writes actually reach the LLM.

Why this exists: _13's injection in before_main_llm_call is discarded because
prepare_prompt() has already assembled the prompt by the time that hook fires.
Without this consumer, the model never sees its own reasoning state across turns
and re-derives the same conclusions every turn — the regenerate-identical-preamble
loop pattern. See state/wiring/exocortex_wiring_and_logic.html §09 for the full
finding and chain diagram.

Reads:
  - agent._reasoning_state (set by _49 in message_loop_end; bootstrapped by _13 if needed)
Writes:
  - loop_data.history_output[-1]["content"] (prepend reasoning state block)
Log tag: [REASON-INJ-22]
"""

from typing import Any

from agent import Agent, LoopData
from helpers.extension import Extension

REASONING_KEY  = "_reasoning_state"
MAX_TRIED_SHOW = 4


class ReasoningStateInjector(Extension):
    """message_loop_prompts_after: inject reasoning state into the user message."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            # Subordinate context — skip per DEC-028 (subagents don't inherit reasoning state)
            if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
                return

            state = getattr(self.agent, REASONING_KEY, None)
            if not state:
                return

            step      = state.get("step", 0)
            current   = state.get("current", "")
            tried     = state.get("tried", [])
            theory    = state.get("theory", "")
            open_q    = state.get("open", "")
            artifacts = state.get("artifacts", [])

            # Nothing meaningful to inject
            if not current and not tried and not theory and not artifacts:
                return

            block = _format_block(step, current, tried, theory, open_q, artifacts)
            if not block:
                return

            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)

            print(
                f"[REASON-INJ-22] step={step} tried={len(tried)} "
                f"artifacts={len(artifacts)} current={'yes' if current else 'no'}",
                flush=True,
            )
        except Exception as e:
            # Graceful degradation — never crash the prompt assembly path
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[REASON-INJ-22] error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Inline helpers (no cross-extension imports) ───────────────────────────────

def _format_block(
    step: int,
    current: str,
    tried: list,
    theory: str,
    open_q: str,
    artifacts: list,
) -> str:
    """Build the [REASONING STATE] injection block.

    Mirrors _13_reasoning_state._format_block. Inlined here to keep the extension
    self-contained — Sonnet implementation rule: provide all utility functions
    inline, no cross-extension imports.
    """
    lines = [f"[REASONING STATE — step {step}]"]

    if theory:
        lines.append(f"Theory: {theory}")

    # Most recent failed approaches first (up to MAX_TRIED_SHOW)
    recent_tried = tried[-MAX_TRIED_SHOW:]
    for t in recent_tried:
        approach = t.get("approach", "")
        outcome  = t.get("outcome", "")
        lines.append(f"Tried: {approach} → {outcome}")

    if current:
        lines.append(f"Current: {current}")

    if open_q:
        lines.append(f"Open: {open_q}")

    if artifacts:
        lines.append("[ARTIFACTS — files created this session]")
        for a in artifacts:
            lines.append(f"  {a['path']} ({a.get('description', 'File')})")
        lines.append("These files exist on disk. Check them before rebuilding.")

    if len(lines) == 1:
        # Only header — nothing meaningful to inject
        return ""

    lines.append(
        "Update your theory if your understanding has changed. "
        "Do not retry approaches listed in Tried."
    )
    return "\n".join(lines)


def _get_last_user_message(history: list) -> dict | None:
    """Find the most recent user message in the assembled history_output."""
    if not history:
        return None
    for msg in reversed(history):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            return msg
    return None
