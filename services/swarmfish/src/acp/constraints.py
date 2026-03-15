"""
constraints.py — Mechanical constraint enforcement for ACP profiles

Per design note Step 2.5 (Eitan's review): profiles whose analytical method always
produces an answer need hard constraints enforced by the aggregation layer,
not left to behavioral compliance of the LLM.

Sprint 1: Historian constraint (dual similarity scoring, confidence capping).
Sprint 4+: Sentinel attribution guard, Reflexivity Modeler magnitude constraint.

The apply_constraints() function is called on raw LLM output before the prediction
is stored. It modifies confidence and adds constraint metadata. The LLM cannot
circumvent this — the math runs after the LLM returns.
"""

from typing import Optional


# ============================================================
# Historian: dual similarity scoring + confidence scaling
# ============================================================

HISTORIAN_MIN_RELEVANT_SIMILARITY = 0.40

def apply_historian_constraints(prediction: dict) -> dict:
    """
    Enforce the Historian's analogue quality constraint.

    If relevant_similarity_score < 0.40: flag as weak analogue, cap confidence.
    If relevant_similarity_score is present: scale confidence proportionally.
    If fields are missing: cap confidence at 0.50 (insufficient information).

    The Historian must always provide both similarity scores. If it doesn't,
    the missing fields are treated as a constraint violation.

    Returns modified prediction dict with constraint metadata added.
    """
    overall   = prediction.get("overall_similarity_score")
    relevant  = prediction.get("relevant_similarity_score")
    original_confidence = prediction.get("confidence", 0.5)

    constraints_applied = []
    capped = False
    cap_reason = None

    # Missing fields: LLM failed to provide required scores
    if relevant is None:
        prediction["confidence"] = min(original_confidence, 0.50)
        prediction["confidence_capped"] = True
        prediction["confidence_cap_reason"] = (
            "Historian constraint: relevant_similarity_score not provided. "
            "Confidence capped at 0.50 until analogue quality is specified."
        )
        prediction["constraints_applied"] = [
            {"constraint": "missing_relevant_similarity", "original_confidence": original_confidence}
        ]
        return prediction

    if overall is None:
        # Overall is informational, not load-bearing — allow with warning
        constraints_applied.append({"constraint": "missing_overall_similarity", "severity": "warning"})

    # Weak analogue: below minimum relevant similarity threshold
    if relevant < HISTORIAN_MIN_RELEVANT_SIMILARITY:
        # Cap at 0.45 — below the threshold of load-bearing confidence
        cap = min(original_confidence, 0.45)
        prediction["confidence"] = cap
        capped = True
        cap_reason = (
            f"Historian constraint: relevant_similarity_score {relevant:.2f} "
            f"is below minimum threshold {HISTORIAN_MIN_RELEVANT_SIMILARITY}. "
            f"Analogue flagged as weak. Confidence capped at 0.45."
        )
        constraints_applied.append({
            "constraint": "weak_analogue",
            "relevant_similarity": relevant,
            "threshold": HISTORIAN_MIN_RELEVANT_SIMILARITY,
            "original_confidence": original_confidence,
            "capped_to": cap
        })

    # Confidence scaling: scale proportionally to relevant similarity quality
    # relevant=0.40 → scale factor 0.80; relevant=0.80 → scale factor 1.00
    # Linear interpolation: scale = 0.5 + 0.5 * relevant
    # This means even a strong analogue (0.80) doesn't inflate confidence beyond
    # what the LLM output already expressed.
    elif relevant >= HISTORIAN_MIN_RELEVANT_SIMILARITY:
        scale = 0.5 + 0.5 * relevant
        scale = min(scale, 1.0)
        scaled_confidence = original_confidence * scale
        prediction["confidence"] = round(scaled_confidence, 3)
        constraints_applied.append({
            "constraint": "confidence_scaled_by_relevance",
            "relevant_similarity": relevant,
            "scale_factor": round(scale, 3),
            "original_confidence": original_confidence,
            "scaled_to": round(scaled_confidence, 3)
        })

    prediction["confidence_capped"] = capped
    prediction["confidence_cap_reason"] = cap_reason
    prediction["constraints_applied"] = constraints_applied
    return prediction


# ============================================================
# Sentinel: attribution evidence threshold (Sprint 4+)
# ============================================================

SENTINEL_CONFIDENCE_CAP_WITHOUT_MECHANISM = 0.40

def apply_sentinel_constraints(prediction: dict) -> dict:
    """
    Enforce the Sentinel's attribution evidence threshold.
    "Entity X benefits from Y" != "Entity X caused Y".
    Named actor attribution requires: 2+ independent sources,
    observable mechanism, alternative explanation specified.
    Without mechanism: confidence capped at 0.40.

    Not yet active — placeholder for Sprint 4 when Sentinel profile is added.
    """
    # Stub — implement when Sentinel profile is added in Sprint 4
    return prediction


# ============================================================
# Reflexivity Modeler: magnitude constraint (Sprint 4+)
# ============================================================

def apply_reflexivity_constraints(prediction: dict) -> dict:
    """
    Enforce the Reflexivity Modeler's magnitude requirement.
    Cannot claim a feedback loop is the dominant driver without quantifying effect size.
    Without magnitude: confidence capped at 0.50 on dominant-driver claims.

    Not yet active — placeholder for Sprint 4 when Reflexivity Modeler is added.
    """
    # Stub — implement when Reflexivity Modeler profile is added in Sprint 4
    return prediction


# ============================================================
# Dispatcher — apply the right constraints for each profile
# ============================================================

CONSTRAINT_MAP = {
    "Historian":           apply_historian_constraints,
    "Sentinel":            apply_sentinel_constraints,
    "Reflexivity Modeler": apply_reflexivity_constraints,
}

def apply_constraints(profile_name: str, prediction: dict) -> dict:
    """
    Apply profile-specific constraints to a raw LLM prediction.
    Profiles not in CONSTRAINT_MAP pass through unchanged.
    Called by predictor.py after parsing LLM output, before DB write.
    """
    fn = CONSTRAINT_MAP.get(profile_name)
    if fn is None:
        return prediction
    return fn(prediction)
