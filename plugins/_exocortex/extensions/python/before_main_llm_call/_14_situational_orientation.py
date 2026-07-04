"""
Situational Orientation Protocol — Orientation Stack Wave 2
===========================================================
Hook: before_main_llm_call
Priority: _14 (after reasoning state at _13, before HTN at _15)

Integration layer for the orientation stack. Reads from task tracker,
reasoning state, staging canaries, and tool registry. Injects a structured
[ORIENT] block at critical moments — not every turn.

Trigger-based design: orientation fires at moments where positional
awareness degrades most. Firing on every turn is overhead that cancels
the benefit (per Session 060 analysis).

Triggers:
  A. Phase boundary  — task tracker signals a completed phase
  B. Tool failure    — error diagnosis set, or repeated tool failures
  C. Post-compression — history length dropped significantly
  D. Session start   — first turn of a new session

What this addresses (from ST-005):
  - Trigger A: 7-turn comprehension loop at Phase 1→2 boundary
  - Trigger B: String-replace called 4x with same params; dead-end recycling
  - Trigger C: Compression strips dead-end map; agent retries failed approaches
  - Trigger D: Agent restarts session without knowing prior progress

Design principle: The orientation block provides information and options.
The agent still decides. No LLM calls. All trigger detection is deterministic.

Reads:
  - agent._task_tracker (from _48)
  - agent._reasoning_state (from _49 / _13)
  - agent._error_diagnosis (from _20_error_comprehension)
  - agent._layer_signals (from _48)
  - /a0/usr/Exocortex/staging.jsonl (dead ends / canaries)
Writes:
  - user message content (prepend)
  - agent._orient_last_trigger (cooldown tracking)
Log tag: [ORIENT]
"""

import json
import os
import re
import time
from typing import Any

from agent import LoopData
from helpers.extension import Extension

# ── Constants ─────────────────────────────────────────────────────────────────

TRACKER_KEY     = "_task_tracker"
REASONING_KEY   = "_reasoning_state"
SIGNALS_KEY     = "_layer_signals"
DIAGNOSIS_KEY   = "_error_diagnosis"
ORIENT_LAST_KEY = "_orient_last_trigger"
HIST_LEN_KEY    = "_orient_last_hist_len"

STAGING_PATH    = "/a0/usr/Exocortex/staging.jsonl"

# Cooldown: minimum turns between orientation injections of the same trigger type
TRIGGER_COOLDOWN = 3

# Compression detection threshold
COMPRESSION_SHRINK = 0.35

# Tool alternatives (for Trigger B OPTIONS section)
TOOL_ALTERNATIVES = {
    "code_execution_tool": [
        "Split into smaller steps — run one command at a time",
        "Use runtime: 'python' for Python code instead of mixing bash+python",
    ],
    "memory_save": [
        "Check that you're using a tool call (JSON), not a Python import",
        "Use a shorter text — memory_save has a content size limit",
    ],
    "document_query": [
        "Use code_execution_tool with cat/head to read the file directly",
        "Use search_engine if it's a web resource",
    ],
}


class SituationalOrientation(Extension):
    """before_main_llm_call: trigger-based orientation injection."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            turn = _estimate_turn(loop_data)
            last_triggers = getattr(self.agent, ORIENT_LAST_KEY, {}) or {}
            hist_len = len(loop_data.history_output or [])

            # ── Detect compression ──
            last_hist = getattr(self.agent, HIST_LEN_KEY, hist_len)
            compressed = (
                last_hist > 10
                and hist_len < last_hist * (1 - COMPRESSION_SHRINK)
            )
            setattr(self.agent, HIST_LEN_KEY, hist_len)

            # ── Check triggers ──
            trigger = None
            trigger_data = {}

            # Trigger D: Session start (first turn)
            if turn <= 1 and not last_triggers:
                trigger = "session_start"

            # Trigger A: Phase boundary (set by _48_task_tracker)
            if trigger is None:
                signals = getattr(self.agent, SIGNALS_KEY, {}) or {}
                phase_tx = signals.get("task_phase_transition")
                if phase_tx:
                    last_a = last_triggers.get("phase_boundary", -TRIGGER_COOLDOWN)
                    if (turn - last_a) >= TRIGGER_COOLDOWN:
                        trigger = "phase_boundary"
                        trigger_data = phase_tx
                        # Consume the signal
                        signals.pop("task_phase_transition", None)
                        setattr(self.agent, SIGNALS_KEY, signals)

            # Trigger C: Post-compression
            if trigger is None and compressed:
                last_c = last_triggers.get("post_compression", -TRIGGER_COOLDOWN)
                if (turn - last_c) >= TRIGGER_COOLDOWN:
                    trigger = "post_compression"

            # Trigger B: Tool failure
            if trigger is None:
                diagnosis = getattr(self.agent, DIAGNOSIS_KEY, None)
                if diagnosis:
                    last_b = last_triggers.get("tool_failure", -TRIGGER_COOLDOWN)
                    if (turn - last_b) >= TRIGGER_COOLDOWN:
                        trigger = "tool_failure"
                        trigger_data = diagnosis

            if trigger is None:
                return

            # ── Gather state ──
            tracker   = getattr(self.agent, TRACKER_KEY, {}) or {}
            reasoning = getattr(self.agent, REASONING_KEY, {}) or {}
            canaries  = _load_canaries()

            # ── Build orientation block ──
            block = _build_block(trigger, trigger_data, tracker, reasoning, canaries)
            if not block:
                return

            # ── Inject ──
            user_msg = _get_last_user_message(loop_data.history_output)
            if user_msg:
                existing = user_msg.get("content", "")
                user_msg["content"] = block + "\n\n" + str(existing)

            # ── Update cooldown ──
            last_triggers[trigger] = turn
            setattr(self.agent, ORIENT_LAST_KEY, last_triggers)

            self.agent.context.log.log(
                type="info",
                content=f"[ORIENT] Trigger: {trigger} (turn {turn})",
            )

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[ORIENT] Error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Block Assembly ─────────────────────────────────────────────────────────────

def _build_block(
    trigger: str,
    trigger_data: dict,
    tracker: dict,
    reasoning: dict,
    canaries: list[str],
) -> str:

    if trigger == "phase_boundary":
        return _block_phase_boundary(trigger_data, tracker, canaries)
    elif trigger == "tool_failure":
        return _block_tool_failure(trigger_data, tracker, reasoning)
    elif trigger == "post_compression":
        return _block_post_compression(tracker, reasoning, canaries)
    elif trigger == "session_start":
        return _block_session_start(tracker, reasoning, canaries)
    return ""


def _block_phase_boundary(data: dict, tracker: dict, canaries: list[str]) -> str:
    completed_name = data.get("completed_name", "previous phase")
    entering_name  = data.get("entering_name", "next phase")

    lines = ["[ORIENT — Phase transition]"]
    lines.append(f"COMPLETED: {completed_name}")
    lines.append(f"ENTERING:  {entering_name}")

    # First subtask of next phase
    phases = tracker.get("phases", [])
    entering_idx = data.get("entering_phase", 0)
    if entering_idx < len(phases):
        subtasks = phases[entering_idx].get("subtasks", [])
        if subtasks:
            first = subtasks[0]
            lines.append(f"FIRST STEP: {first.get('task', subtasks[0])}")
        else:
            lines.append(f"FIRST STEP: Begin {entering_name}")

    if canaries:
        lines.append("DEAD ENDS (from staging):")
        for c in canaries[:3]:
            lines.append(f"  • {c}")

    lines.append(f"Do not re-analyze {completed_name}. Begin executing the first step of {entering_name}.")
    return "\n".join(lines)


def _block_tool_failure(diagnosis: dict, tracker: dict, reasoning: dict) -> str:
    tool_name = diagnosis.get("error_class", "tool")
    causal    = diagnosis.get("causal_chain", "")
    anti      = diagnosis.get("anti_actions", [])

    lines = [f"[ORIENT — Tool failure: {tool_name}]"]
    if causal:
        lines.append(f"ERROR: {causal}")

    tried = reasoning.get("tried", [])
    if tried:
        lines.append("TRIED SO FAR:")
        for t in tried[-3:]:
            lines.append(f"  • {t.get('approach', '')} → {t.get('outcome', '')}")

    # Buildplan context
    phases = tracker.get("phases", [])
    current_idx = tracker.get("current_phase", 0)
    if current_idx < len(phases):
        phase_name = phases[current_idx].get("name", f"Phase {current_idx + 1}")
        lines.append(f"BUILDPLAN: Currently in {phase_name}")

    # PACE options
    raw_tool = _extract_tool_from_error_class(tool_name)
    alternatives = TOOL_ALTERNATIVES.get(raw_tool, [])
    lines.append("OPTIONS:")
    if alternatives:
        for i, alt in enumerate(alternatives[:2], ord("A")):
            lines.append(f"  {chr(i)}) {alt}")
        next_letter = chr(ord("A") + len(alternatives[:2]))
    else:
        next_letter = "A"
    lines.append(f"  {next_letter}) Use staging_note to record this dead end, then try a fundamentally different approach")
    last_letter = chr(ord(next_letter) + 1)
    lines.append(f"  {last_letter}) If stuck after 2 alternatives, use response tool to report progress and ask for guidance")

    if anti:
        lines.append("DO NOT:")
        for a in anti[:3]:
            lines.append(f"  - {a}")

    return "\n".join(lines)


def _block_post_compression(tracker: dict, reasoning: dict, canaries: list[str]) -> str:
    lines = ["[ORIENT — Context compressed. Your memory of failed approaches may be incomplete.]"]

    # Buildplan status
    phases = tracker.get("phases", [])
    if phases:
        lines.append("BUILDPLAN STATUS:")
        for i, phase in enumerate(phases):
            status = phase.get("status", "pending")
            symbol = "✓" if status == "completed" else "→" if status == "in-progress" else " "
            lines.append(f"  {symbol} Phase {i + 1}: {phase.get('name', '')} [{status}]")

    # Dead ends from staging
    if canaries:
        lines.append("DEAD ENDS (from staging — survived compression):")
        for c in canaries[:4]:
            lines.append(f"  • {c}")

    # Reasoning state snapshot
    current = reasoning.get("current", "")
    theory  = reasoning.get("theory", "")
    if current or theory:
        lines.append("LAST KNOWN STATE:")
        if theory:
            lines.append(f"  Theory: {theory}")
        if current:
            lines.append(f"  Current: {current}")

    lines.append("Check staging notes before retrying any approach you are uncertain about.")
    return "\n".join(lines)


def _block_session_start(tracker: dict, reasoning: dict, canaries: list[str]) -> str:
    phases = tracker.get("phases", [])
    if not phases and not canaries and not reasoning.get("current"):
        return ""  # Nothing to orient to at start of fresh session

    lines = ["[ORIENT — Session start]"]

    if phases:
        lines.append("PRIOR TASK STATE:")
        for i, phase in enumerate(phases):
            status = phase.get("status", "pending")
            symbol = "✓" if status == "completed" else "→" if status == "in-progress" else " "
            lines.append(f"  {symbol} Phase {i + 1}: {phase.get('name', '')} [{status}]")

    current = reasoning.get("current", "")
    if current:
        lines.append(f"LAST ACTION: {current}")

    if canaries:
        lines.append("PRIOR DEAD ENDS:")
        for c in canaries[:3]:
            lines.append(f"  • {c}")

    tried = reasoning.get("tried", [])
    if tried:
        lines.append("PRIOR FAILURES (do not retry):")
        for t in tried[-3:]:
            lines.append(f"  • {t.get('approach', '')} → {t.get('outcome', '')}")

    return "\n".join(lines)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _extract_tool_from_error_class(error_class: str) -> str:
    """Map error class name to the tool it came from."""
    mapping = {
        "terminal_early_exit_heredoc": "code_execution_tool",
        "interactive_prompt": "code_execution_tool",
        "terminal_session_hung": "code_execution_tool",
    }
    return mapping.get(error_class, error_class)


def _load_canaries() -> list[str]:
    """Load active staging entries tagged as dead ends / canaries / high-importance observations."""
    if not os.path.exists(STAGING_PATH):
        return []
    results = []
    try:
        with open(STAGING_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if e.get("status") != "active":
                        continue
                    cat = e.get("category", "")
                    importance = e.get("importance", 0)
                    # Include canaries and high-importance observations
                    if cat in ("canary",) or (cat == "observation" and importance >= 0.7):
                        text = e.get("text", "")
                        if text:
                            results.append(text[:120])
                except Exception:
                    pass
    except Exception:
        pass
    return results


def _estimate_turn(loop_data: LoopData) -> int:
    if not loop_data.history_output:
        return 0
    return len([m for m in loop_data.history_output if isinstance(m, dict) and m.get("ai", True)])


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
