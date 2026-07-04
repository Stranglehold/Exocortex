"""
Constraint Heartbeat — Periodic Constraint + Epistemic Principle Re-injection
==============================================================================
Hook: message_loop_prompts_after (_21_)

NOTE: This extension must live in message_loop_prompts_after/, NOT before_main_llm_call/.
message_loop_prompts_after fires inside prepare_prompt() so history_output modifications
reach the model. before_main_llm_call fires AFTER prepare_prompt() — any history_output
changes there are silently discarded before the LLM call.
(Same hook timing issue that caused _17_orchestration_gate and _19_context_pruner to be
tombstoned. See their docstrings for details.)

Re-injects a compact hard-constraint block every N turns (default: 10) and
immediately after context compression. Counteracts recency bias in long-context
inference: rules stated at turn 1 lose behavioral influence by turn 20+.

Two injection triggers:
  1. Turn interval — fires when turn_count % interval == 0 (not turn 0)
  2. Post-compression — fires when history length drops > 30% since last turn,
     indicating context compression wiped the original constraints from context.

Two constraint sets (selected by mode config):
  "always"           — operational + epistemic principles for any long session
  "self_improvement" — harder operational rules + five self-interrogation questions

Epistemic principles informed by:
  I-CALM (arXiv:2604.03904) — confidence-before-answer + explicit abstention reward
  SAVeR (arXiv:2604.08401) — verify-before-commit against evidential constraints
  research/EPISTEMIC_FORCING_FUNCTIONS.md — full literature review

Category C (Behavioral Guardrail, Scheduled) per v18 demand-driven architecture:
fires on a fixed schedule regardless of model performance. Not demand-driven.

Layer 1 (behavioral) of the self-improvement guardrail stack.
Layer 2 (mechanical): extensions/tool_execute_before/_16_py_write_guard.py

Spec: specs/CONSTRAINT_HEARTBEAT_SPEC_L3.md
Design review: team-comms/opus-to-kestrel/review_constraint_heartbeat_20260428.md
No LLM calls. No file writes.
"""

import json
import os
from typing import Optional

from agent import Agent, LoopData
from helpers.extension import Extension

# ── Constraint Content (from Opus, expanded_heartbeat_content_20260428.md) ────

GENERAL_CONSTRAINTS = """[BEHAVIORAL CONSTRAINTS — REFRESHED]
These instructions were given at session start. They are restated here
because long sessions cause early instructions to lose influence.

OPERATIONAL:
• Complete tasks you were given. Do not expand scope without explicit instruction.
• Do not spawn subordinate agents without explicit instruction to do so.
• If you are uncertain whether an action is authorized, stop and ask.

EPISTEMIC:
• Report only what you have measured or verified. If you estimated it, say "estimated."
• Before reporting any number: did you compute it, or generate a plausible-sounding one?
  If generated — either run the computation or report it as an estimate.
• "I haven't measured this" is a valid and valuable answer. It is better than a
  fabricated measurement.
• Every factual claim should be traceable to a source: tool output, search result,
  file read, or explicit reasoning. If you cannot name the source, the claim is
  unverified — say so.
• Do not present estimates as measurements, inferences as observations, or
  assumptions as facts.
[/BEHAVIORAL CONSTRAINTS]"""

SELF_IMPROVEMENT_CONSTRAINTS = """[SELF-IMPROVEMENT CONSTRAINTS — REFRESHED]
These rules are from program.md. They are restated here because turn
distance causes early rules to lose influence.

HARD LIMITS — no exceptions:
• Never modify .py files. Config JSON, skill SKILL.md, wiki pages only.
• Every wiki page requires an immediate memory_save call (Rule 13).
• Never stop between priorities. Completing one means cycling to the next.
• Do not spawn subordinates without instruction.

EPISTEMIC DISCIPLINE — the difference between good work and fabricated work:
• Report actual metrics ONLY. If you did not run `wc -l`, do not report a line count.
  If you did not run a benchmark, do not report a performance number.
• Before writing any metric to the journal, answer in your thinking:
  1. "What tool output produced this number?" — cite the specific output.
  2. "Did I measure this or estimate it?" — if estimated, label it "estimated."
  3. "What would contradict this claim?" — name one piece of evidence that would
     disprove it.
• Honest uncertainty is more valuable than confident fabrication. "I believe this
  improved performance but I have no measurement" is a useful journal entry.
  "Performance improved by 19%" without a measurement is a trust violation.
• If you notice you've written a specific number without a tool output to back it,
  STOP and either run the measurement or change the number to "estimated" or
  "not measured."

CHECK: Is the number you're about to report backed by a tool output you can cite?
CHECK: Did you just modify or attempt to modify a .py file? If yes — stop and revert.
[/SELF-IMPROVEMENT CONSTRAINTS]"""


def _load_config(agent) -> dict:
    try:
        cfg_path = "/a0/usr/plugins/_exocortex/config/config.json"
        if os.path.exists(cfg_path):
            with open(cfg_path) as fh:
                return json.load(fh).get("constraint_heartbeat", {})
    except Exception:
        pass
    return {}


def _get_last_user_msg(history_output: list) -> Optional[dict]:
    for msg in reversed(history_output or []):
        if isinstance(msg, dict) and not msg.get("ai", True):
            if msg.get("content"):
                return msg
    return None


def _history_len(loop_data: LoopData) -> int:
    return len(getattr(loop_data, "history_output", None) or [])


class ConstraintHeartbeat(Extension):
    """Re-injects hard constraints + epistemic principles every N turns and post-compression."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
                return  # subordinate context — skip heartbeat (DEC-028)
            cfg = _load_config(self.agent)
            if not cfg.get("enabled", True):
                return

            interval: int = int(cfg.get("interval", 10))
            mode: str = cfg.get("mode", "always")

            # Mode gate — self_improvement requires the flag in extras_persistent
            if mode == "self_improvement":
                ep = getattr(loop_data, "extras_persistent", None) or {}
                if not ep.get("_self_improvement_active"):
                    return

            # Increment turn counter (persists across context compressions)
            count: int = getattr(self.agent, "_heartbeat_turn_count", 0) + 1
            self.agent._heartbeat_turn_count = count

            # Compression detection: significant drop in history length means
            # context was compressed and original instructions are gone
            current_len = _history_len(loop_data)
            last_len: int = getattr(self.agent, "_heartbeat_last_history_len", current_len)
            self.agent._heartbeat_last_history_len = current_len
            compression_fired = (
                last_len > 0
                and current_len < last_len * 0.7  # > 30% drop
            )

            # Fire on interval (not turn 0) or immediately after compression
            should_fire = (count % interval == 0) or compression_fired
            if not should_fire:
                return

            # Select constraint set
            block = (
                SELF_IMPROVEMENT_CONSTRAINTS
                if mode == "self_improvement"
                else GENERAL_CONSTRAINTS
            )

            reason = "post-compression" if compression_fired else f"turn {count}"
            print(
                f"[HEARTBEAT] Firing ({reason}, mode={mode}, interval={interval})",
                flush=True,
            )

            # Inject — prepend to last user message in history_output
            user_msg = _get_last_user_msg(getattr(loop_data, "history_output", None))
            if not user_msg:
                print(f"[HEARTBEAT] No user message found — skipping injection", flush=True)
                return

            existing = str(user_msg.get("content", ""))
            user_msg["content"] = block + "\n\n" + existing
            print(f"[HEARTBEAT] Injected constraint block ({len(block)//4} tokens)", flush=True)

        except Exception as e:
            print(f"[HEARTBEAT] Error (passthrough): {e}", flush=True)
