"""
constraints.py — Mechanical constraint enforcement for ACP profiles

Per design note Step 2.5 (Eitan's review): profiles whose analytical method always
produces an answer need hard constraints enforced by the aggregation layer,
not left to behavioral compliance of the LLM.

Active constraints:
  Historian            — dual similarity scoring, confidence scaled by relevant_similarity
  Reflexivity Modeler  — feedback_direction required; missing = cap at 0.50
  Decomposer           — components list required; missing or <2 components = cap at 0.60
  Risk Manager         — tail_weight required; fat-tail cap at 0.70; missing = cap at 0.55

Planned (stub only):
  Sentinel             — attribution evidence threshold (Sprint 4+)

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
# Reflexivity Modeler: feedback_direction required
# ============================================================

def apply_reflexivity_constraints(prediction: dict) -> dict:
    """
    Enforce the Reflexivity Modeler's feedback direction requirement.

    The core claim of the Reflexivity Modeler is that a feedback loop is operating.
    If the model does not specify which direction the loop is running, the claim
    is ungrounded. Missing feedback_direction → confidence capped at 0.50.

    Valid feedback_direction values: self-reinforcing, self-correcting, transitioning,
    unclear. Returning "unclear" with explanation is acceptable and does not trigger
    the cap — the model acknowledged the ambiguity explicitly.
    """
    feedback_direction = prediction.get("feedback_direction")
    original_confidence = prediction.get("confidence", 0.5)

    if not feedback_direction:
        prediction["confidence"] = min(original_confidence, 0.50)
        prediction["confidence_capped"] = True
        prediction["confidence_cap_reason"] = (
            "Reflexivity constraint: feedback_direction not provided. "
            "The reflexivity framework requires identifying whether the loop is "
            "self-reinforcing, self-correcting, transitioning, or unclear. "
            "Confidence capped at 0.50 until direction is specified."
        )
        prediction["constraints_applied"] = [
            {"constraint": "missing_feedback_direction", "original_confidence": original_confidence}
        ]
    else:
        prediction.setdefault("confidence_capped", False)
        prediction.setdefault("confidence_cap_reason", None)
        prediction.setdefault("constraints_applied", [])

    return prediction


# ============================================================
# Decomposer: components list required (minimum 2)
# ============================================================

def apply_decomposer_constraints(prediction: dict) -> dict:
    """
    Enforce the Decomposer's decomposition requirement.

    The Decomposer's value is explicit component-by-component estimation. If no
    components are provided, the prediction is just an opaque judgment — it has
    not used its analytical method. Missing or single-component decomposition
    is a constraint violation.

    - No components field: cap at 0.60
    - Only 1 component: cap at 0.65 (minimal decomposition)
    - 2+ components: no cap applied
    """
    components = prediction.get("components", [])
    original_confidence = prediction.get("confidence", 0.5)

    if not components:
        prediction["confidence"] = min(original_confidence, 0.60)
        prediction["confidence_capped"] = True
        prediction["confidence_cap_reason"] = (
            "Decomposer constraint: no components provided. "
            "The Decomposer must break the question into independently estimable "
            "sub-components with explicit ranges. Without decomposition, the prediction "
            "is an opaque judgment rather than a Fermi estimate. "
            "Confidence capped at 0.60."
        )
        prediction["constraints_applied"] = [
            {"constraint": "missing_decomposition", "original_confidence": original_confidence}
        ]
    elif len(components) == 1:
        prediction["confidence"] = min(original_confidence, 0.65)
        prediction["confidence_capped"] = True
        prediction["confidence_cap_reason"] = (
            "Decomposer constraint: only 1 component provided. "
            "Fermi methodology requires at least 2 independently estimable components. "
            "Confidence capped at 0.65."
        )
        prediction["constraints_applied"] = [
            {"constraint": "insufficient_decomposition",
             "components_provided": 1,
             "original_confidence": original_confidence}
        ]
    else:
        prediction.setdefault("confidence_capped", False)
        prediction.setdefault("confidence_cap_reason", None)
        prediction.setdefault("constraints_applied", [])

    return prediction


# ============================================================
# Risk Manager: tail_weight required; fat-tail confidence cap
# ============================================================

RISK_MANAGER_FAT_TAIL_CAP = 0.70

def apply_risk_manager_constraints(prediction: dict) -> dict:
    """
    Enforce the Risk Manager's distribution characterization requirements.

    The Risk Manager's core contribution is tail risk assessment. Two constraints:

    1. tail_weight required — if missing, the distribution hasn't been characterized.
       Missing → cap at 0.55.

    2. Fat-tail cap — if tail_weight == "fat", the domain is extremistan (power-law).
       In extremistan, point estimates of confidence are systematically misleading.
       Fat tail → cap at 0.70 (still allows moderate confidence on directional calls,
       but forces acknowledgment that the distribution limits precision).
    """
    tail_weight = prediction.get("tail_weight")
    original_confidence = prediction.get("confidence", 0.5)

    if not tail_weight:
        prediction["confidence"] = min(original_confidence, 0.55)
        prediction["confidence_capped"] = True
        prediction["confidence_cap_reason"] = (
            "Risk Manager constraint: tail_weight not provided. "
            "The Risk Manager must characterize the outcome distribution as "
            "fat, normal, or thin before expressing confidence. "
            "Confidence capped at 0.55."
        )
        prediction["constraints_applied"] = [
            {"constraint": "missing_tail_weight", "original_confidence": original_confidence}
        ]
    elif tail_weight.lower() == "fat":
        capped = min(original_confidence, RISK_MANAGER_FAT_TAIL_CAP)
        if capped < original_confidence:
            prediction["confidence"] = capped
            prediction["confidence_capped"] = True
            prediction["confidence_cap_reason"] = (
                f"Risk Manager constraint: tail_weight=fat (extremistan domain). "
                f"Power-law distributions render high-precision confidence claims "
                f"misleading. Confidence capped at {RISK_MANAGER_FAT_TAIL_CAP}."
            )
            prediction["constraints_applied"] = [
                {"constraint": "fat_tail_cap",
                 "cap": RISK_MANAGER_FAT_TAIL_CAP,
                 "original_confidence": original_confidence}
            ]
        else:
            prediction.setdefault("confidence_capped", False)
            prediction.setdefault("confidence_cap_reason", None)
            prediction.setdefault("constraints_applied", [])
    else:
        prediction.setdefault("confidence_capped", False)
        prediction.setdefault("confidence_cap_reason", None)
        prediction.setdefault("constraints_applied", [])

    return prediction


# ============================================================
# Dispatcher — apply the right constraints for each profile
# ============================================================

CONSTRAINT_MAP = {
    "Historian":           apply_historian_constraints,
    "Reflexivity Modeler": apply_reflexivity_constraints,
    "Decomposer":          apply_decomposer_constraints,
    "Risk Manager":        apply_risk_manager_constraints,
    "Sentinel":            apply_sentinel_constraints,   # stub — Sprint 4+
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
