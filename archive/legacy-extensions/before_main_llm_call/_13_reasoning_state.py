"""
Reasoning State Injector — Orientation Stack Wave 2
=====================================================
Hook: before_main_llm_call
Priority: _13 (after completion tracker at _12, before orientation at _14)

Injects the current reasoning state into the user message context before
each LLM call. Provides the model with:
  - What it's currently working on (Current)
  - What approaches have already failed (Tried)
  - The working theory (Theory)
  - Any open questions (Open)

This is the read side of the reasoning state pair:
  - _49_reasoning_state_update.py writes the state (message_loop_end)
  - This file reads and injects it (before_main_llm_call)

Only injects when there's meaningful state to show. No injection on the
first turn (state is empty). Lightweight: single dict read + string format.

Reads:
  - agent._reasoning_state (set by _49)
Writes:
  - user message content (prepend)
Log tag: [REASON-INJ]
"""

import json
import os
from typing import Any

from agent import Agent, LoopData
from helpers.extension import Extension

REASONING_KEY = "_reasoning_state"
STAGING_PATH  = "/a0/usr/Exocortex/staging.jsonl"
MAX_TRIED_SHOW = 4  # Max failed attempts to show in injection


class ReasoningStateInjector(Extension):
    """before_main_llm_call: inject compressed reasoning state into context."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
                return  # subordinate context — skip reasoning state injection (DEC-028)
            state = getattr(self.agent, REASONING_KEY, None)
            if not state:
                # First turn: attempt artifact bootstrap from staging.jsonl
                prior_artifacts = _load_artifacts_from_staging()
                if not prior_artifacts:
                    return
                # Inline schema — avoids cross-extension import across A0's loader boundary
                state = {
                    "step": 0,
                    "theory": "",
                    "tried": [],
                    "current": "",
                    "open": "",
                    "artifacts": prior_artifacts,
                }
                setattr(self.agent, REASONING_KEY, state)
                print(f"[REASON-INJ] Bootstrapped {len(prior_artifacts)} artifact(s) from staging", flush=True)

            step = state.get("step", 0)
            current = state.get("current", "")
            tried = state.get("tried", [])
            theory = state.get("theory", "")
            open_q = state.get("open", "")
            artifacts = state.get("artifacts", [])

            # Don't inject if state is essentially empty
            if not current and not tried and not theory and not artifacts:
                return

            block = _format_block(step, current, tried, theory, open_q, artifacts)
            if not block:
                return

            user_msg = _get_last_user_message(loop_data.history_output)
            if user_msg:
                existing = user_msg.get("content", "")
                user_msg["content"] = block + "\n\n" + str(existing)

            print(
                f"[REASON-INJ] step={step} tried={len(tried)} "
                f"artifacts={len(artifacts)} current={'yes' if current else 'no'}",
                flush=True,
            )

        except Exception as e:
            print(f"[REASON-INJ] Error (passthrough): {e}", flush=True)


# ── Block Formatting ───────────────────────────────────────────────────────────

def _format_block(
    step: int,
    current: str,
    tried: list,
    theory: str,
    open_q: str,
    artifacts: list,
) -> str:
    """Build the [REASONING STATE] injection block."""
    lines = [f"[REASONING STATE — step {step}]"]

    if theory:
        lines.append(f"Theory: {theory}")

    # Show failed approaches (most recent first, up to MAX_TRIED_SHOW)
    recent_tried = tried[-MAX_TRIED_SHOW:]
    for t in recent_tried:
        approach = t.get("approach", "")
        outcome = t.get("outcome", "")
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
        # Only header — nothing meaningful
        return ""

    lines.append(
        "Update your theory if your understanding has changed. "
        "Do not retry approaches listed in Tried."
    )
    return "\n".join(lines)


# ── Staging Bootstrap ──────────────────────────────────────────────────────────

def _load_artifacts_from_staging() -> list[dict]:
    """
    Read staging.jsonl and return all active artifact entries.
    Called once on first turn when agent._reasoning_state is None.
    Returns empty list on any error (graceful degradation).
    """
    artifacts = []
    try:
        if not os.path.exists(STAGING_PATH):
            return artifacts
        with open(STAGING_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if (
                        e.get("_artifact_entry")
                        and e.get("status") == "active"
                        and e.get("path")
                    ):
                        artifacts.append({
                            "path": e["path"],
                            "description": e.get("description", "File"),
                            "step": e.get("artifact_step", 0),
                        })
                except Exception:
                    pass
    except Exception:
        pass
    return artifacts


# ── Message Helper ─────────────────────────────────────────────────────────────

def _get_last_user_message(history: list) -> dict | None:
    if not history:
        return None
    for msg in reversed(history):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            content = msg.get("content", "")
            if isinstance(content, dict) and "user_message" in content:
                return msg
            if isinstance(content, str) and content:
                return msg
    return None
