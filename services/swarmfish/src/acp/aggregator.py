"""
aggregator.py — Weighted consensus extraction and operator brief generation

Takes per-profile predictions from a prediction session and produces:
  - Weighted consensus confidence (calibration-weighted mean)
  - Disagreement level (std dev of confidences)
  - Meta-confidence: HIGH / MEDIUM / LOW
  - Formatted operator brief per OPERATOR_BRIEF_FORMAT.md spec

The brief format: decision-speed, surfaces disagreement, calibration context,
monitoring checklist (what would change this), one screen always.
"""

import json
import uuid
from math import sqrt
from statistics import stdev, mean
from typing import Optional
from datetime import datetime, timezone


# ============================================================
# Weighted consensus
# ============================================================

def aggregate_predictions(predictions: list, profiles: dict) -> dict:
    """
    Produce weighted consensus from per-profile prediction dicts.

    predictions: list of dicts from predictor.run_profile()
    profiles:    dict of profile_name → profile dict (from DB, has consensus_weight)

    Returns consensus dict matching design note aggregate_predictions() signature.
    """
    valid = [p for p in predictions if p.get("confidence") is not None and p.get("error") is None]
    if not valid:
        return {"error": "No valid predictions to aggregate"}

    weighted_preds = []
    total_weight = 0.0

    for p in valid:
        profile = profiles.get(p["profile_name"], {})
        domain  = p.get("domain", "general")

        # Get domain-specific weight, fall back to default
        weight_map = profile.get("consensus_weight", {})
        if isinstance(weight_map, str):
            import json as _json
            weight_map = _json.loads(weight_map)
        weight = weight_map.get(domain, weight_map.get("default", 1.0))

        # Apply calibration correction
        calib_map = profile.get("confidence_calibration", {})
        if isinstance(calib_map, str):
            import json as _json
            calib_map = _json.loads(calib_map)
        calib_bias = calib_map.get(domain, calib_map.get("default", 0.0))

        adjusted_confidence = max(0.01, min(0.99, p["confidence"] + calib_bias))

        weighted_preds.append({
            "profile_name": p["profile_name"],
            "prediction": p.get("prediction", ""),
            "confidence": adjusted_confidence,
            "weight": weight,
            "reasoning_summary": p.get("reasoning_summary", ""),
            "falsification_conditions": p.get("falsification_conditions", []),
            "confidence_capped": p.get("confidence_capped", False),
            "analogue_reference": p.get("analogue_reference"),
            "overall_similarity_score": p.get("overall_similarity_score"),
            "relevant_similarity_score": p.get("relevant_similarity_score"),
        })
        total_weight += weight

    consensus = sum(wp["confidence"] * wp["weight"] for wp in weighted_preds) / total_weight

    confidences = [wp["confidence"] for wp in weighted_preds]
    disagreement = stdev(confidences) if len(confidences) > 1 else 0.0

    uncertainty_adj = disagreement * 0.5
    range_low  = max(0.01, consensus - uncertainty_adj)
    range_high = min(0.99, consensus + uncertainty_adj)

    if disagreement > 0.20:
        meta_confidence = "LOW"
    elif disagreement > 0.10:
        meta_confidence = "MEDIUM"
    else:
        meta_confidence = "HIGH"

    # High-confidence dissenters: profiles that diverge >0.20 from consensus
    dissenters = [
        wp for wp in weighted_preds
        if abs(wp["confidence"] - consensus) > 0.20
    ]

    return {
        "consensus_confidence": round(consensus, 3),
        "range_low":  round(range_low, 3),
        "range_high": round(range_high, 3),
        "disagreement_level": round(disagreement, 3),
        "meta_confidence": meta_confidence,
        "individual_predictions": weighted_preds,
        "high_confidence_dissenters": dissenters,
    }


# ============================================================
# Falsification checklist compilation
# ============================================================

def compile_falsification_checklist(predictions: list) -> list:
    """
    Compile falsification conditions across all profiles into a monitoring checklist.
    Deduplicates similar conditions and ranks by max impact_magnitude.
    """
    all_conditions = []
    for p in predictions:
        if not p.get("falsification_conditions"):
            continue
        for fc in p.get("falsification_conditions", []):
            if isinstance(fc, dict):
                all_conditions.append({
                    "condition": fc.get("condition", ""),
                    "impact": fc.get("impact", ""),
                    "impact_magnitude": fc.get("impact_magnitude", 0.5),
                    "from_profile": p.get("profile_name", ""),
                })

    # Sort by impact magnitude descending, take top 8
    all_conditions.sort(key=lambda x: x.get("impact_magnitude", 0), reverse=True)
    return all_conditions[:8]


# ============================================================
# Operator brief generation
# ============================================================

def format_pct(f: float) -> str:
    return f"{round(f * 100)}%"


def format_brief(question: str, domain: str, consensus: dict,
                 predictions: list, profiles: dict,
                 checklist: list, timestamp: Optional[str] = None) -> str:
    """
    Format the operator brief per OPERATOR_BRIEF_FORMAT.md spec.
    One screen. Decision-speed. Surfaces disagreement.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    cons_pct     = format_pct(consensus["consensus_confidence"])
    range_str    = f"{format_pct(consensus['range_low'])} – {format_pct(consensus['range_high'])}"
    meta         = consensus["meta_confidence"]
    disagreement = consensus["disagreement_level"]

    if meta == "HIGH":
        conf_note = "agents broadly agree"
    elif meta == "MEDIUM":
        conf_note = f"moderate spread (σ={disagreement:.2f})"
    else:
        conf_note = f"agents disagree significantly (σ={disagreement:.2f})"

    lines = [
        f"PREDICTION BRIEF: {question[:80]}",
        f"Domain: {domain} | Generated: {timestamp}",
        "━" * 54,
        "",
        f"CONSENSUS: {cons_pct}",
        f"Range: {range_str}",
        f"Confidence: {meta} ({conf_note})",
    ]

    # KEY DISAGREEMENT — only when MEDIUM or LOW
    if meta in ("MEDIUM", "LOW") and len(consensus["individual_predictions"]) >= 2:
        sorted_preds = sorted(consensus["individual_predictions"],
                              key=lambda x: x["confidence"])
        lowest  = sorted_preds[0]
        highest = sorted_preds[-1]

        if highest["profile_name"] != lowest["profile_name"]:
            # Get calibration info for each
            low_profile  = profiles.get(lowest["profile_name"], {})
            high_profile = profiles.get(highest["profile_name"], {})

            lines += [
                "",
                "KEY DISAGREEMENT:",
                f"• {lowest['profile_name']}: {format_pct(lowest['confidence'])}",
                f"  says: {lowest['prediction'][:120]}",
                f"• {highest['profile_name']}: {format_pct(highest['confidence'])}",
                f"  says: {highest['prediction'][:120]}",
            ]

    # CONFIDENCE CAPPED notices
    capped_profiles = [p for p in predictions if p.get("confidence_capped")]
    if capped_profiles:
        lines.append("")
        for cp in capped_profiles:
            cap_reason = cp.get("confidence_cap_reason", "constraint applied")
            # Truncate to keep brief readable
            reason_short = cap_reason[:120] if len(cap_reason) > 120 else cap_reason
            lines.append(f"⚠ {cp['profile_name']} CONFIDENCE CAPPED: {reason_short}")

    # WHAT WOULD CHANGE THIS
    if checklist:
        lines += ["", "WHAT WOULD CHANGE THIS:"]
        for item in checklist[:4]:
            lines.append(f"• {item['condition']}: {item['impact']}")

    # CALIBRATION NOTES
    lines += ["", "CALIBRATION NOTES:"]
    for pred in consensus["individual_predictions"]:
        pname   = pred["profile_name"]
        profile = profiles.get(pname, {})

        weight_map = profile.get("consensus_weight", {})
        if isinstance(weight_map, str):
            weight_map = json.loads(weight_map)
        weight = weight_map.get("default", 1.0)

        calib_map = profile.get("confidence_calibration", {})
        if isinstance(calib_map, str):
            calib_map = json.loads(calib_map)
        bias = calib_map.get("default", 0.0)

        if weight == 1.0 and bias == 0.0:
            calib_note = "uncalibrated (insufficient history)"
        else:
            bias_str = f"bias {bias:+.2f}" if bias != 0.0 else "well-calibrated"
            calib_note = f"weight {weight:.2f}, {bias_str}"

        lines.append(f"• {pname}: {format_pct(pred['confidence'])} — {calib_note}")

    lines += [
        "",
        "━" * 54,
    ]

    return "\n".join(lines)


# ============================================================
# Write aggregated session to DB + return full result
# ============================================================

def finalize_session(db_conn, session_id: str, question: str, domain: str,
                     context_summary: Optional[str],
                     predictions: list, profiles: dict) -> dict:
    """
    Compute consensus, compile checklist, generate brief, persist to session row.
    Returns complete result dict.
    """
    consensus = aggregate_predictions(predictions, profiles)
    if "error" in consensus:
        return consensus

    checklist = compile_falsification_checklist(predictions)
    brief = format_brief(question, domain, consensus, predictions, profiles, checklist)

    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE acp_sessions SET
            consensus_confidence = %s,
            consensus_range_low  = %s,
            consensus_range_high = %s,
            meta_confidence      = %s,
            disagreement_level   = %s,
            operator_brief       = %s,
            falsification_checklist = %s,
            profiles_used        = %s
        WHERE id = %s
    """, (
        consensus["consensus_confidence"],
        consensus["range_low"],
        consensus["range_high"],
        consensus["meta_confidence"],
        consensus["disagreement_level"],
        brief,
        json.dumps(checklist),
        json.dumps([p.get("profile_name") for p in predictions if p.get("profile_name")]),
        session_id,
    ))
    db_conn.commit()
    cursor.close()

    return {
        "session_id": session_id,
        "question": question,
        "domain": domain,
        "consensus": consensus,
        "falsification_checklist": checklist,
        "operator_brief": brief,
        "individual_predictions": predictions,
    }
