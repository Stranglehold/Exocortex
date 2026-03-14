"""
stack_status.py — Exocortex Stack Introspection Tool
=====================================================

Reports the live state of the Exocortex stack: which extensions are present
in the container, and what runtime state the active layers have accumulated.

Call this tool when:
  - Something isn't behaving as expected and you need to confirm which layers
    are actually running.
  - You want a snapshot of current classification state, EI verdicts, or
    supervisor anomaly counts.
  - After a deployment, to verify all extensions landed correctly.

No arguments required. No LLM calls. No external dependencies.
Output is deterministic: file presence checks + agent attribute reads.
"""

import os
from datetime import datetime, timezone

from python.helpers.tool import Tool, Response

# ---------------------------------------------------------------------------
# Extension registry — canonical list of all Exocortex extensions
# ---------------------------------------------------------------------------

EXT_ROOT = "/a0/python/extensions"

EXTENSIONS = {
    "before_main_llm_call": [
        ("_11_bst",      "_11_belief_state_tracker.py"),
        ("_12_org",      "_12_org_dispatcher.py"),
        ("_13_profile",  "_13_operator_profile.py"),
        ("_14_meta",     "_14_metacognitive_injection.py"),
        ("_15_htn",      "_15_htn_plan_selector.py"),
        ("_20_watchdog", "_20_context_watchdog.py"),
    ],
    "monologue_end": [
        ("_25_ei",          "_25_epistemic_integrity.py"),
        ("_52_memorizer",   "_52_selective_memorizer.py"),
        ("_53_insight",     "_53_insight_capture.py"),
        ("_55_classifier",  "_55_memory_classifier.py"),
        ("_57_maint",       "_57_memory_maintenance.py"),
        ("_59_ontology",    "_59_ontology_maintenance.py"),
    ],
    "tool_execute_after": [
        ("_20_error",    "_20_error_comprehension.py"),
        ("_20_reset",    "_20_reset_failure_counter.py"),
        ("_25_ledger",   "_25_evidence_ledger_recorder.py"),
        ("_30_fallback", "_30_tool_fallback_logger.py"),
        ("_60_sleep",    "_60_sleep_trigger.py"),
    ],
    "tool_execute_before": [
        ("_15_action",    "_15_action_boundary.py"),
        ("_20_meta_gate", "_20_meta_reasoning_gate.py"),
        ("_30_advisor",   "_30_tool_fallback_advisor.py"),
    ],
    "message_loop_end": [
        ("_50_supervisor", "_50_supervisor_loop.py"),
    ],
    "message_loop_prompts_after": [
        ("_55_recall",   "_55_memory_relevance_filter.py"),
        ("_56_enhance",  "_56_memory_enhancement.py"),
        ("_58_ontology", "_58_ontology_query.py"),
        ("_95_tools",    "_95_tiered_tool_injection.py"),
    ],
    "hist_add_before": [
        ("_11_wm", "_11_working_memory.py"),
    ],
}


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class StackStatus(Tool):
    """
    Report the live state of the Exocortex extension stack.

    Returns:
      - Which extensions are present in the container (file check)
      - Runtime state accumulated by active layers this session
    """

    async def execute(self, **kwargs) -> Response:
        try:
            report = _build_report(self.agent)
            print("[STACK] Status report generated.", flush=True)
            return Response(message=report, break_loop=False)
        except Exception as e:
            return Response(message=f"[STACK] Error generating report: {e}", break_loop=False)


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _build_report(agent) -> str:
    lines = ["[EXOCORTEX STACK STATUS]", ""]

    # ── Section 1: Extension presence ──────────────────────────────────────
    total = sum(len(v) for v in EXTENSIONS.values())
    present = 0
    ext_lines = []

    for hook, exts in EXTENSIONS.items():
        row_parts = []
        for label, filename in exts:
            path = os.path.join(EXT_ROOT, hook, filename)
            exists = os.path.exists(path)
            if exists:
                present += 1
            mark = "✓" if exists else "✗"
            row_parts.append(f"{mark}{label}")
        ext_lines.append(f"  {hook:<32}  {' '.join(row_parts)}")

    lines.append(f"Extensions ({present}/{total} present)")
    lines.extend(ext_lines)
    lines.append("")

    # ── Section 2: Runtime state ────────────────────────────────────────────
    lines.append("Runtime state")

    # BST
    bst_line = _read_bst(agent)
    lines.append(f"  BST            {bst_line}")

    # Evidence ledger
    ev_line = _read_evidence(agent)
    lines.append(f"  Evidence       {ev_line}")

    # Epistemic Integrity
    ei_line = _read_ei(agent)
    lines.append(f"  EI             {ei_line}")

    # Action gate
    gate_line = _read_action_gate(agent)
    lines.append(f"  Action gate    {gate_line}")

    # Supervisor
    sup_line = _read_supervisor(agent)
    lines.append(f"  Supervisor     {sup_line}")

    # Working memory
    wm_line = _read_working_memory(agent)
    lines.append(f"  Working mem    {wm_line}")

    # Operator profile
    op_line = _read_operator_profile(agent)
    lines.append(f"  Operator       {op_line}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Runtime state readers — all safe, return "not yet fired" on missing attr
# ---------------------------------------------------------------------------

def _read_bst(agent) -> str:
    try:
        store = getattr(agent, "_bst_store", None)
        if not store:
            return "not yet fired"
        belief = store.get("__bst_belief_state__")
        if not belief:
            return "store present, belief state empty"
        primary = getattr(belief, "primary_domain", None) or store.get("_bst_domain", "?")
        secondary = getattr(belief, "secondary_domain", None)
        if secondary and secondary != primary:
            return f"domain={primary} | secondary={secondary}"
        return f"domain={primary}"
    except Exception as e:
        return f"read error: {e}"


def _read_evidence(agent) -> str:
    try:
        ledger = None
        # Try get_data first, then direct attr
        try:
            ledger = agent.get_data("_evidence_ledger")
        except Exception:
            pass
        if ledger is None:
            ledger = getattr(agent, "_evidence_ledger", None)
        if not ledger:
            return "not yet fired"
        entries = ledger.get("entries", [])
        kv = ledger.get("key_values", [])
        return f"{len(entries)} entries | {len(kv)} key values this session"
    except Exception as e:
        return f"read error: {e}"


def _read_ei(agent) -> str:
    try:
        ei = None
        try:
            ei = agent.get_data("_epistemic_integrity")
        except Exception:
            pass
        if ei is None:
            ei = getattr(agent, "_epistemic_integrity", None)
        if not ei:
            return "not yet fired"
        total   = ei.get("total_claims", 0)
        high    = ei.get("high_risk_count", 0)
        claims  = ei.get("claims", [])
        # Most recent verdict
        last_verdict = "none"
        if claims:
            last_verdict = claims[-1].get("verdict", "?")
        return f"{total} claims | {high} high-risk | last={last_verdict}"
    except Exception as e:
        return f"read error: {e}"


def _read_action_gate(agent) -> str:
    try:
        gate = None
        try:
            gate = agent.get_data("_action_gate_active")
        except Exception:
            pass
        if gate is None:
            gate = getattr(agent, "_action_gate_active", None)
        if gate is None:
            return "not yet fired"
        return "ACTIVE — awaiting authorization" if gate else "inactive"
    except Exception as e:
        return f"read error: {e}"


def _read_supervisor(agent) -> str:
    try:
        state = getattr(agent, "_supervisor_state", None)
        if not state:
            return "not yet fired"
        turn      = state.get("turn", 0)
        loop_tier = state.get("loop_tier", "none") or "none"
        cooldowns = state.get("cooldowns", {})
        fired = [k for k, v in cooldowns.items() if isinstance(v, int) and v > 0]
        anomaly_str = (", ".join(fired)) if fired else "none"
        return f"turn={turn} | loop_tier={loop_tier} | anomalies fired={anomaly_str}"
    except Exception as e:
        return f"read error: {e}"


def _read_working_memory(agent) -> str:
    try:
        wm = getattr(agent, "_working_memory", None)
        if not wm:
            return "not yet fired"
        entities  = wm.get("entities", [])
        promoted  = wm.get("promoted", {})
        return f"{len(entities)} entities ({len(promoted)} promoted)"
    except Exception as e:
        return f"read error: {e}"


def _read_operator_profile(agent) -> str:
    try:
        cache = getattr(agent, "_operator_profile_cache", None)
        if not cache:
            return "not loaded (no approved profile)"
        profile = cache.get("profile", {})
        if not profile:
            return "cache present, profile empty"
        comm    = profile.get("communication_patterns", {})
        avg_len = comm.get("avg_turn_length_chars", 0)
        floor   = profile.get("floor_giving", {})
        return f"loaded (avg {avg_len:.0f} chars/turn)"
    except Exception as e:
        return f"read error: {e}"
