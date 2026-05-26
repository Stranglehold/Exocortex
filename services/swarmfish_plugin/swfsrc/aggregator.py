"""
aggregator.py — SWARMFISH V2 consensus aggregation

V2 changes from V1:
  - SQLite storage
  - dissent is a first-class object with full reasoning reference
  - finalize_session returns dissent list with assessment_ids for follow-up
"""

import json
import sqlite3
from datetime import datetime, timezone
from math import sqrt
from statistics import mean, stdev
from typing import Optional


# ─────────────────────────────────────────────────────────────
# Weighted consensus
# ─────────────────────────────────────────────────────────────

def aggregate_assessments(assessments: list, profiles: list) -> dict:
    """
    Weighted consensus from per-profile assessment dicts.

    assessments: list of dicts from predictor.run_profile()
    profiles:    list of profile dicts from DB (has consensus_weight, confidence_calibration)

    Returns consensus dict. V2: dissenters have assessment_id for follow-up.
    """
    profile_map = {p["name"]: p for p in profiles}

    valid = [a for a in assessments if a.get("confidence") is not None and not a.get("error")]
    if not valid:
        return {"error": "No valid assessments to aggregate"}

    weighted = []
    total_weight = 0.0

    for a in valid:
        profile = profile_map.get(a["profile_name"], {})
        domain  = a.get("domain", "general")

        weight_map = profile.get("consensus_weight", '{"default": 1.0}')
        if isinstance(weight_map, str):
            weight_map = json.loads(weight_map)
        weight = weight_map.get(domain, weight_map.get("default", 1.0))

        calib_map = profile.get("confidence_calibration", '{"default": 0.0}')
        if isinstance(calib_map, str):
            calib_map = json.loads(calib_map)
        calib_bias = calib_map.get(domain, calib_map.get("default", 0.0))

        adjusted = max(0.01, min(0.99, a["confidence"] + calib_bias))

        weighted.append({
            "assessment_id": a.get("assessment_id"),
            "profile_name": a["profile_name"],
            "prediction": a.get("prediction", ""),
            "confidence": adjusted,
            "weight": weight,
            "reasoning_summary": a.get("reasoning_summary", ""),
            "falsification_conditions": a.get("falsification_conditions", []),
            "confidence_capped": a.get("confidence_capped", False),
            "analogue_reference": a.get("analogue_reference"),
            "overall_similarity_score": a.get("overall_similarity_score"),
            "relevant_similarity_score": a.get("relevant_similarity_score"),
        })
        total_weight += weight

    consensus_conf = sum(wp["confidence"] * wp["weight"] for wp in weighted) / total_weight

    confidences   = [wp["confidence"] for wp in weighted]
    disagreement  = stdev(confidences) if len(confidences) > 1 else 0.0

    uncertainty_adj = disagreement * 0.5
    range_low  = max(0.01, consensus_conf - uncertainty_adj)
    range_high = min(0.99, consensus_conf + uncertainty_adj)

    if len(confidences) < 2:
        meta_confidence = "LOW"  # a single voice can't corroborate — no committee agreement to assess
    elif disagreement > 0.20:
        meta_confidence = "LOW"
    elif disagreement > 0.10:
        meta_confidence = "MEDIUM"
    else:
        meta_confidence = "HIGH"

    # V2: dissenters have assessment_id for analyst follow-up
    dissenters = [
        {
            "assessment_id": wp["assessment_id"],
            "profile_name": wp["profile_name"],
            "confidence": wp["confidence"],
            "prediction": wp["prediction"],
            "reasoning_summary": wp["reasoning_summary"],
            "divergence": round(abs(wp["confidence"] - consensus_conf), 3),
        }
        for wp in weighted
        if abs(wp["confidence"] - consensus_conf) > 0.20
    ]

    return {
        "consensus_confidence": round(consensus_conf, 3),
        "range_low":  round(range_low, 3),
        "range_high": round(range_high, 3),
        "disagreement_level": round(disagreement, 3),
        "meta_confidence": meta_confidence,
        "individual_assessments": weighted,
        "dissenters": dissenters,
    }


# ─────────────────────────────────────────────────────────────
# Falsification checklist
# ─────────────────────────────────────────────────────────────

def compile_falsification_checklist(assessments: list) -> list:
    """Compile falsification conditions across all profiles, top 8 by impact."""
    all_conditions = []
    for a in assessments:
        for fc in (a.get("falsification_conditions") or []):
            if isinstance(fc, dict):
                all_conditions.append({
                    "condition": fc.get("condition", ""),
                    "impact": fc.get("impact", ""),
                    "impact_magnitude": fc.get("impact_magnitude", 0.5),
                    "from_profile": a.get("profile_name", ""),
                })
    all_conditions.sort(key=lambda x: x.get("impact_magnitude", 0), reverse=True)
    return all_conditions[:8]


# ─────────────────────────────────────────────────────────────
# Operator brief
# ─────────────────────────────────────────────────────────────

def _pct(f: float) -> str:
    return f"{round(f * 100)}%"


def format_operator_brief(question: str, domain: str, consensus: dict,
                           assessments: list, profiles: list,
                           checklist: list) -> str:
    """Format the operator brief. One screen, decision-speed, surfaces dissent."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    profile_map = {p["name"]: p for p in profiles}

    cons_pct = _pct(consensus["consensus_confidence"])
    range_str = f"{_pct(consensus['range_low'])} – {_pct(consensus['range_high'])}"
    meta = consensus["meta_confidence"]
    disagreement = consensus["disagreement_level"]

    conf_note = {
        "HIGH": "committee broadly agrees",
        "MEDIUM": f"moderate spread (σ={disagreement:.2f})",
        "LOW": f"committee disagrees significantly (σ={disagreement:.2f})",
    }[meta]

    lines = [
        f"PREDICTION BRIEF: {question[:80]}",
        f"Domain: {domain} | Generated: {ts}",
        "━" * 54,
        "",
        f"CONSENSUS: {cons_pct}",
        f"Range: {range_str}",
        f"Confidence: {meta} ({conf_note})",
    ]

    # Key disagreement
    if meta in ("MEDIUM", "LOW") and len(consensus["individual_assessments"]) >= 2:
        sorted_a = sorted(consensus["individual_assessments"], key=lambda x: x["confidence"])
        lowest, highest = sorted_a[0], sorted_a[-1]
        if highest["profile_name"] != lowest["profile_name"]:
            lines += [
                "",
                "KEY DISAGREEMENT:",
                f"• {lowest['profile_name']}: {_pct(lowest['confidence'])}",
                f"  says: {lowest['prediction'][:120]}",
                f"• {highest['profile_name']}: {_pct(highest['confidence'])}",
                f"  says: {highest['prediction'][:120]}",
            ]

    # Dissenters (V2: with assessment_id for follow-up)
    if consensus.get("dissenters"):
        lines.append("")
        lines.append("DISSENTERS (use swarmfish_session for full reasoning):")
        for d in consensus["dissenters"]:
            lines.append(f"⚡ {d['profile_name']}: {_pct(d['confidence'])} "
                         f"(divergence: {_pct(d['divergence'])})")
            lines.append(f"  {d['reasoning_summary'][:120]}")

    # Confidence-capped notices
    capped = [a for a in assessments if a.get("confidence_capped")]
    if capped:
        lines.append("")
        for a in capped:
            reason = (a.get("confidence_cap_reason") or "constraint applied")[:120]
            lines.append(f"⚠ {a['profile_name']} CONFIDENCE CAPPED: {reason}")

    # What would change this
    if checklist:
        lines += ["", "WHAT WOULD CHANGE THIS:"]
        for item in checklist[:4]:
            lines.append(f"• {item['condition']}: {item['impact']}")

    # Calibration notes
    lines += ["", "CALIBRATION NOTES:"]
    for a in consensus["individual_assessments"]:
        profile = profile_map.get(a["profile_name"], {})
        weight_map = profile.get("consensus_weight", '{"default": 1.0}')
        if isinstance(weight_map, str):
            weight_map = json.loads(weight_map)
        weight = weight_map.get("default", 1.0)

        calib_map = profile.get("confidence_calibration", '{"default": 0.0}')
        if isinstance(calib_map, str):
            calib_map = json.loads(calib_map)
        bias = calib_map.get("default", 0.0)

        if weight == 1.0 and bias == 0.0:
            calib_note = "uncalibrated (insufficient history)"
        else:
            bias_str = f"bias {bias:+.2f}" if bias != 0.0 else "well-calibrated"
            calib_note = f"weight {weight:.2f}, {bias_str}"

        lines.append(f"• {a['profile_name']}: {_pct(a['confidence'])} — {calib_note}")

    lines += ["", "━" * 54]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Finalize session — write consensus to DB and return result
# ─────────────────────────────────────────────────────────────

def finalize_session(conn: sqlite3.Connection, session_id: str, question: str,
                     domain: str, context_summary: Optional[str],
                     assessments: list, profiles: list) -> dict:
    """
    Compute consensus, compile checklist, generate brief, update session row.
    Returns complete result dict for the API response.
    """
    consensus = aggregate_assessments(assessments, profiles)
    if "error" in consensus:
        return consensus

    checklist = compile_falsification_checklist(assessments)
    brief = format_operator_brief(question, domain, consensus, assessments, profiles, checklist)

    conn.execute("""
        UPDATE acp_sessions SET
            consensus_confidence    = ?,
            consensus_range_low     = ?,
            consensus_range_high    = ?,
            meta_confidence         = ?,
            disagreement_level      = ?,
            operator_brief          = ?,
            falsification_checklist = ?,
            profiles_used           = ?,
            updated_at              = datetime('now')
        WHERE id = ?
    """, (
        consensus["consensus_confidence"],
        consensus["range_low"],
        consensus["range_high"],
        consensus["meta_confidence"],
        consensus["disagreement_level"],
        brief,
        json.dumps(checklist),
        json.dumps([a.get("profile_name") for a in assessments if a.get("profile_name")]),
        session_id,
    ))
    conn.commit()

    return {
        "session_id": session_id,
        "question": question,
        "domain": domain,
        "consensus": consensus,
        "falsification_checklist": checklist,
        "operator_brief": brief,
        "assessments": assessments,
    }
