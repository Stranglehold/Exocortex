"""
Proactive Reasoning Supervisor — Injection Hook
================================================
Hook: before_main_llm_call
Priority: _12 (v1.6 path: extensions/python/before_main_llm_call/)

Reads the intervention flags set by the reasoning_stream_end hook
on the PREVIOUS turn and injects a targeted correction block into
the user message before the LLM call for the CURRENT turn.

Timing (relative to _50_supervisor_loop):
  - Turn N: reasoning_stream_end sets _ps_fired=True, _ps_signal={...}
  - Turn N: message_loop_end (_50) reads _ps_fired, defers Tier 1 if True
  - Turn N+1: before_main_llm_call (THIS FILE) reads flags, injects correction
  - Turn N+1: flags cleared — new turn starts clean

The injection block uses task-oriented language only. It NEVER quotes
or references the model's reasoning content directly (reasoning privacy
principle — Design Note §2 Principle 4).

Intervention templates:
  repeated_tool        — suggest alternatives, report-if-blocked
  repeated_sentence    — progress check, try different angle
  self_reference_loop  — approach change required, different strategy
  hedge_without_commit — commit to action, choose simplest first
  excessive_deliberation — simplify, direct approach first

Injection pattern: same prepend-to-last-user-message pattern as
_13_reasoning_state, _14_situational_orientation, _16_tool_registry.

Log tag: [PS-INJECT]
"""

from typing import Optional

from agent import LoopData
from helpers.extension import Extension

# ── Agent data keys (shared with buffer and analysis hooks) ───────────────────

PS_SIGNAL_KEY = "_ps_signal"    # dict: signal result from previous turn
PS_FIRED_KEY  = "_ps_fired"     # bool: True if intervention was queued
AFFECT_INTERVENTION_KEY = "_affect_intervention"  # dict: FRUSTRATION/DESPERATION queued by reasoning_stream_end (Phase 2)

# ── Affect-layer intervention templates (Phase 2) ─────────────────────────────
# Verbatim intent from AFFECT_LAYER_DESIGN_NOTE §4/§5. Non-destructive prompt
# injections: FRUSTRATION is a metacognitive reframe; DESPERATION is a
# pre-fabrication hard-stop. Affect interventions TAKE PRECEDENCE over the tactical
# _ps_signal block (predictive/metacognitive > tactical course-correction).

_AFFECT_INTERVENTIONS = {
    "FRUSTRATION": (
        "[SUPERVISOR: REFRAME]\n"
        "You have encountered several obstacles on the current approach. "
        "Step back and consider whether the task as currently framed is solvable, "
        "or whether the framing needs adjustment. Reporting that the current approach "
        "is blocked and proposing a different one is a valid, useful outcome."
    ),
    "DESPERATION": (
        "[SUPERVISOR: PAUSE]\n"
        "Before proceeding, review your last 3 tool calls and their actual results. "
        "If you cannot cite specific tool output supporting your current claim, do not "
        "proceed with it. It is better to report 'I could not determine this' than to "
        "produce an unsupported estimate, assumption, or plausible-sounding figure."
    ),
}

# ── Intervention text templates ───────────────────────────────────────────────
# Task-oriented language only. No reference to reasoning content.

_INTERVENTIONS = {
    "repeated_tool": (
        "[SUPERVISOR: STRATEGY SHIFT RECOMMENDED]\n"
        "The current approach may not be producing results. "
        "Alternative tools for this task type: {alternatives}. "
        "If the task cannot be completed with available tools, "
        "report what you have and explain the limitation clearly."
    ),
    "repeated_sentence": (
        "[SUPERVISOR: PROGRESS CHECK]\n"
        "Ensure each turn produces measurable progress toward the goal. "
        "If the current approach is blocked, try a different angle or "
        "report the specific blocking condition."
    ),
    "self_reference_loop": (
        "[SUPERVISOR: APPROACH CHANGE REQUIRED]\n"
        "Previous approach has been attempted. Do not retry the same method. "
        "Choose a fundamentally different strategy or report that the task "
        "cannot be completed with currently available resources."
    ),
    "hedge_without_commit": (
        "[SUPERVISOR: COMMIT TO ACTION]\n"
        "Select the most promising approach and execute it. "
        "If uncertain between options, choose the simplest one first. "
        "Deliberation without action does not advance the task."
    ),
    "excessive_deliberation": (
        "[SUPERVISOR: SIMPLIFY]\n"
        "This task may be simpler than current analysis suggests. "
        "Commit to the most direct approach. Elaborate only if the "
        "direct approach fails."
    ),
}

# Fallback alternatives when specific tool is unknown
_DEFAULT_ALTERNATIVES = "response (report current findings), code_execution_tool, search_engine"

# Per-tool alternative suggestions (mirrors analysis hook map for self-containment)
_TOOL_ALTERNATIVES = {
    "code_execution_tool": "response (report what you know), search_engine (verify facts first)",
    "search_engine":       "code_execution_tool (compute directly), response (answer from knowledge)",
    "memory_load":         "response (use current context), code_execution_tool (read file directly)",
    "memory_save":         "response (confirm and continue)",
    "call_subordinate":    "code_execution_tool (do it directly), response (report current findings)",
    "browser_agent":       "search_engine, code_execution_tool (curl/requests)",
    "document_query":      "code_execution_tool (read file), memory_load",
}


# ── Extension ─────────────────────────────────────────────────────────────────

class ProactiveSupervisorInjector(Extension):
    """before_main_llm_call: inject correction from previous turn's reasoning analysis."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            # Read flags set by reasoning_stream_end on the previous turn
            fired  = bool(self.agent.get_data(PS_FIRED_KEY))
            signal = self.agent.get_data(PS_SIGNAL_KEY)
            affect_iv = self.agent.get_data(AFFECT_INTERVENTION_KEY)

            # Always clear all flags — this turn starts clean regardless of what we inject
            self.agent.set_data(PS_FIRED_KEY, False)
            self.agent.set_data(PS_SIGNAL_KEY, None)
            self.agent.set_data(AFFECT_INTERVENTION_KEY, None)

            # Affect-layer intervention (Phase 2) takes precedence over the tactical
            # _ps_signal block — it is a higher-order predictive redirect (FRUSTRATION
            # reframe / DESPERATION hard-stop). Injected via the same prepend pattern.
            if affect_iv and isinstance(affect_iv, dict):
                state = affect_iv.get("affect", "")
                block = _AFFECT_INTERVENTIONS.get(state, "")
                if block:
                    user_msg = _get_last_user_message(loop_data.history_output)
                    if user_msg:
                        existing = user_msg.get("content", "")
                        user_msg["content"] = block + "\n\n" + str(existing)
                        print(
                            f"[PS-AFFECT-INJECT] Injected {state} intervention "
                            f"(step={affect_iv.get('step')}/{affect_iv.get('step_budget')} "
                            f"failures={affect_iv.get('consecutive_tool_failures')} "
                            f"hedge:commit={affect_iv.get('hedge_commit_ratio')})",
                            flush=True,
                        )
                        return  # affect supersedes the tactical signal this turn

            if not fired or not signal or not isinstance(signal, dict):
                return

            signal_class = signal.get("signal_class", "")
            tool_name    = signal.get("tool_name", "")
            severity     = signal.get("severity", 0.0)

            block = _build_intervention_block(signal_class, tool_name)
            if not block:
                return

            # Inject into the last user message (same pattern as _13, _14, _16)
            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)

            print(
                f"[PS-INJECT] Injected {signal_class} intervention "
                f"(severity={severity:.2f} tool={tool_name or 'n/a'})",
                flush=True,
            )

        except Exception as e:
            print(f"[PS-INJECT] Error (passthrough): {e}", flush=True)


# ── Block Construction ─────────────────────────────────────────────────────────

def _build_intervention_block(signal_class: str, tool_name: str) -> str:
    """
    Build the intervention text for the given signal class.
    For repeated_tool: fill in alternatives for the specific repeating tool.
    """
    template = _INTERVENTIONS.get(signal_class, "")
    if not template:
        return ""

    if signal_class == "repeated_tool" and tool_name:
        alternatives = _TOOL_ALTERNATIVES.get(tool_name, _DEFAULT_ALTERNATIVES)
        return template.format(alternatives=alternatives)

    # Other templates have no placeholders
    return template


# ── Message Helper ─────────────────────────────────────────────────────────────

def _get_last_user_message(history_output: list) -> Optional[dict]:
    """Find the most recent operator message in loop history."""
    if not history_output:
        return None
    for msg in reversed(history_output):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            content = msg.get("content", "")
            if isinstance(content, dict) and "user_message" in content:
                return msg
            if isinstance(content, str) and content:
                return msg
    return None
