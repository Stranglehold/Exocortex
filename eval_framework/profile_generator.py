"""
Profile Generator — Agent-Zero Model Evaluation Framework
==========================================================
Aggregates per-module metrics into the final model profile JSON
that hardening extensions consume at runtime.
"""

from datetime import datetime, timezone


def generate_profile(model_name: str, raw_metrics: dict) -> dict:
    """Generate a model profile from evaluation metrics.

    Args:
        model_name: Model identifier (e.g. "qwen3-14b-q4_k_m")
        raw_metrics: Dict of module_key → metrics dict

    Returns:
        Complete profile dict ready to write as JSON.
    """
    bst = raw_metrics.get("bst", {})
    tool = raw_metrics.get("tool_reliability", {})
    graph = raw_metrics.get("graph_compliance", {})
    pace = raw_metrics.get("pace_calibration", {})
    ctx = raw_metrics.get("context_sensitivity", {})
    mem = raw_metrics.get("memory_utilization", {})

    # ── Evaluation summary ─────────────────────────────────────────────
    summary = _build_summary(bst, tool, graph, pace, ctx, mem)

    # ── BST section ────────────────────────────────────────────────────
    bst_section = {
        "confidence_adjustment": bst.get("bst_confidence_adjustment", 0),
        "disabled_domains": bst.get("bst_domains_where_enrichment_hurts", []),
        "enrichment_verbosity": _enrichment_verbosity(bst),
    }

    # ── Meta-gate section ──────────────────────────────────────────────
    strictness = tool.get("meta_gate_strictness", "moderate")
    meta_gate_section = {
        "strictness": strictness,
        "json_repair_enabled": strictness in ("aggressive", "moderate"),
        "parameter_validation": strictness != "permissive",
    }

    # ── Tool fallback section ──────────────────────────────────────────
    recovery_rate = tool.get("tool_recovery_rate", 0.5)
    if recovery_rate > 0.70:
        tool_max_retries = 4
    elif recovery_rate > 0.40:
        tool_max_retries = 3
    else:
        tool_max_retries = 2

    tool_section = {
        "max_retries": tool_max_retries,
        "priority_patterns": tool.get("tool_fallback_priority_patterns", []),
        "escalation_after": 5 if recovery_rate > 0.50 else 3,
    }

    # ── Graph workflow section ─────────────────────────────────────────
    adherence = graph.get("graph_instruction_adherence", 0.5)
    premature = graph.get("graph_premature_completion_rate", 0.1)

    graph_section = {
        "max_retries_per_node": graph.get("graph_max_retries_per_node", 2),
        "stale_after_turns": graph.get("graph_stale_detection_turns", 12),
        "node_instruction_verbosity": (
            "explicit" if premature > 0.20 else "standard"
        ),
        "inject_boundary_warnings": premature > 0.20,
    }

    # ── PACE section ───────────────────────────────────────────────────
    pace_section = {
        "primary_threshold": pace.get("pace_primary_threshold", 2),
        "alternate_threshold": pace.get("pace_alternate_threshold", 4),
        "contingency_threshold": pace.get("pace_contingency_threshold", 7),
        "emergency_threshold": pace.get("pace_emergency_threshold", 10),
    }

    # ── Context section ────────────────────────────────────────────────
    ctx_section = {
        "max_injection_tokens": ctx.get("max_context_injection_tokens", 2000),
        "layer_priority": ctx.get("context_layer_priority", [
            "bst_enrichment", "graph_node", "role_profile",
            "recalled_memories", "personality",
        ]),
        "instruction_compliance_warning_threshold": _compliance_threshold(ctx),
    }

    # ── Memory section ─────────────────────────────────────────────────
    noise_disc = mem.get("memory_noise_discrimination", 0.5)
    if noise_disc > 0.70:
        similarity_threshold = 0.60
        noise_level = "good"
    elif noise_disc > 0.40:
        similarity_threshold = 0.70
        noise_level = "moderate"
    else:
        similarity_threshold = 0.80
        noise_level = "poor"

    memory_section = {
        "max_injected": mem.get("memory_max_injected",
                                ctx.get("memory_max_injected", 6)),
        "similarity_threshold": similarity_threshold,
        "noise_discrimination": noise_level,
    }

    # ── Assemble profile ───────────────────────────────────────────────
    profile = {
        "profile_version": "1.0",
        "model_id": model_name,
        "model_family": _extract_family(model_name),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "fixtures_version": "1.0.0",
        "evaluation_summary": summary,
        "bst": bst_section,
        "meta_gate": meta_gate_section,
        "tool_fallback": tool_section,
        "graph_workflow": graph_section,
        "pace": pace_section,
        "context": ctx_section,
        "memory": memory_section,
        "raw_metrics": {
            k: v for k, v in raw_metrics.items()
            if not isinstance(v, dict) or "error" not in v
        },
    }

    return profile


# ── Helpers ────────────────────────────────────────────────────────────────

def _build_summary(bst, tool, graph, pace, ctx, mem) -> dict:
    """Build the evaluation_summary section."""
    # Compute area scores
    area_scores = {}

    if bst and "error" not in bst:
        area_scores["bst"] = bst.get("bst_enrichment_compliance_rate", 0)
    if tool and "error" not in tool:
        area_scores["tool_reliability"] = (
            tool.get("tool_json_validity_rate", 0) * 0.4 +
            tool.get("tool_parameter_accuracy", 0) * 0.3 +
            tool.get("tool_selection_accuracy", 0) * 0.3
        )
    if graph and "error" not in graph:
        area_scores["graph_compliance"] = graph.get("graph_instruction_adherence", 0)
    if pace and "error" not in pace:
        area_scores["pace_calibration"] = (
            pace.get("pace_alternate_recovery_rate", 0) * 0.5 +
            pace.get("pace_emergency_compliance", 0) * 0.5
        )
    if ctx and "error" not in ctx:
        area_scores["context_sensitivity"] = ctx.get("context_baseline_quality", 0)
    if mem and "error" not in mem:
        area_scores["memory_utilization"] = (
            mem.get("memory_reference_rate", 0) * 0.5 +
            mem.get("memory_accuracy_rate", 0) * 0.5
        )

    if not area_scores:
        return {
            "overall_capability": "unknown",
            "strongest_area": "unknown",
            "weakest_area": "unknown",
            "recommended_prosthetic_level": "full",
        }

    avg_score = sum(area_scores.values()) / len(area_scores)
    strongest = max(area_scores, key=area_scores.get)
    weakest = min(area_scores, key=area_scores.get)

    if avg_score > 0.80:
        overall = "high"
        prosthetic = "light"
    elif avg_score > 0.60:
        overall = "medium"
        prosthetic = "moderate"
    elif avg_score > 0.40:
        overall = "low"
        prosthetic = "full"
    else:
        overall = "minimal"
        prosthetic = "maximum"

    return {
        "overall_capability": overall,
        "strongest_area": strongest,
        "weakest_area": weakest,
        "recommended_prosthetic_level": prosthetic,
    }


def _enrichment_verbosity(bst: dict) -> str:
    """Determine BST enrichment verbosity level."""
    confusion = bst.get("bst_enrichment_confusion_rate", 0)
    compliance = bst.get("bst_enrichment_compliance_rate", 0)

    if confusion > 0.15:
        return "minimal"   # Model confused — reduce enrichment
    if compliance > 0.85:
        return "standard"  # Handles enrichment well
    return "verbose"       # Needs more explicit instructions


def _compliance_threshold(ctx: dict) -> float:
    """Determine instruction compliance warning threshold."""
    at_2k = ctx.get("context_instruction_compliance_at_2k", 0.8)
    at_4k = ctx.get("context_instruction_compliance_at_4k", 0.5)

    if at_4k > 0.70:
        return 0.50  # Handles high context well
    if at_2k > 0.70:
        return 0.60  # OK at moderate context
    return 0.70      # Degrades quickly


def _extract_family(model_name: str) -> str:
    """Extract model family from model name."""
    name_lower = model_name.lower()
    families = [
        "qwen3", "qwen2", "qwen", "llama3", "llama2", "llama",
        "mistral", "mixtral", "phi", "gemma", "deepseek", "codellama",
        "command-r", "yi", "internlm", "vicuna", "starcoder",
    ]
    for fam in families:
        if fam in name_lower:
            return fam
    return "unknown"
