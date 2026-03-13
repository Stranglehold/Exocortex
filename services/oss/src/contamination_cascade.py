"""
contamination_cascade.py — Core trust remediation engine.

Called when a source's trust score drops catastrophically. Traces
downstream contamination through the promotion snapshot ledger.
Severity is proportional to the source's load at the moment of promotion,
not its current load — the snapshot captures the decision as it was made.

Thresholds (from CDS v2 spec):
  SOLE_CORROBORATOR       >= 0.80  immediate return, no analyst needed
  DECISIVE_CONTRIBUTION   >= 0.50  urgent flag, operator decides
  PARTIAL                  < 0.50  confidence haircut, flag for review

Redemption path: if >= 2 falsification predictions were confirmed through
sources independently of the compromised source, the claim's corroboration
path was contaminated but the claim itself survived. Re-promote with
adjusted confidence stripping the compromised source's weight.

Requires source_intel network topology for _verify_independence().
Without topology, independence checks return False (conservative assumption).

SWARMFISH simulated topology: Phase 4 integration point. Not yet operational.
See: COGNITIVE_DEFENSE_SYSTEM_v2.md dependency graph.
"""

import os
import uuid
import logging
from typing import Optional

import psycopg2
import psycopg2.extras

import audit
import retcon_ledger
import source_intel

log = logging.getLogger(__name__)

DB_URL = os.environ.get(
    "OSS_DB_URL",
    "postgresql://oss_app:oss_app_dev_password@localhost:5433/oss"
)

# Tier thresholds — from CDS v2 spec
SOLE_CORROBORATOR_THRESHOLD       = 0.80
DECISIVE_CONTRIBUTION_THRESHOLD   = 0.50
INDEPENDENT_CONFIRMATION_THRESHOLD = 2

# Confidence boost per independently confirmed prediction
PREDICTION_CONFIRMATION_BOOST = 0.05
PREDICTION_CONFIRMATION_BOOST_CAP = 0.15


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_cascade(source_id: int, new_trust_score: float, session_id=None) -> dict:
    """
    Run the contamination cascade for a source whose trust score has dropped.

    1. Update the source's confidence_score in the DB.
    2. Find all PROMOTED claims where this source appears in source_weights.
    3. For each: apply tier logic based on source load at promotion time.
    4. Return a contamination report.

    Args:
        source_id:       ID of the compromised source
        new_trust_score: New confidence score (0.0–1.0)
        session_id:      UUID for audit trail

    Returns:
        Contamination report dict.

    Raises:
        ValueError: if source_id not found
    """
    sid = session_id or uuid.uuid4()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, confidence_score FROM sources WHERE id = %s",
                (source_id,)
            )
            source = cur.fetchone()
            if not source:
                raise ValueError(f"Source {source_id} not found")
            original_trust = source["confidence_score"]

            cur.execute(
                "UPDATE sources SET confidence_score = %s WHERE id = %s",
                (new_trust_score, source_id)
            )

    log.info(
        f"[CASCADE] Source {source_id} ({source['name']}): "
        f"trust {original_trust:.3f} → {new_trust_score:.3f}"
    )

    contaminated = _get_claims_with_source_contribution(source_id)

    report = {
        "source_id":      source_id,
        "source_name":    source["name"],
        "original_trust": original_trust,
        "new_trust_score": new_trust_score,
        "survived":        [],  # predictions confirmed independently → re-promoted
        "immediate_return": [], # sole corroborator → returned without analyst review
        "urgent_flag":     [],  # decisive contribution → analyst must decide
        "review_flag":     [],  # partial contribution → confidence haircut
    }

    for claim in contaminated:
        snapshot    = claim["snapshot"]
        source_load = float(snapshot["source_weights"].get(str(source_id), 0.0))

        if source_load == 0.0:
            continue

        independently_confirmed = _count_independent_confirmations(
            snapshot["falsification_predictions"], source_id
        )

        if independently_confirmed >= INDEPENDENT_CONFIRMATION_THRESHOLD:
            _handle_survived(claim, snapshot, source_id, source["name"],
                             independently_confirmed, sid, report)

        elif source_load >= SOLE_CORROBORATOR_THRESHOLD:
            _handle_sole_corroborator(claim, source_id, source["name"],
                                      source_load, sid, report)

        elif source_load >= DECISIVE_CONTRIBUTION_THRESHOLD:
            _handle_decisive(claim, source_id, source["name"],
                             source_load, sid, report)

        else:
            _handle_partial(claim, source_id, source["name"],
                            source_load, original_trust, sid, report)

    report["total_affected"] = (
        len(report["survived"])
        + len(report["immediate_return"])
        + len(report["urgent_flag"])
        + len(report["review_flag"])
    )

    audit.log_event(
        session_id=sid,
        event_type="cascade_complete",
        actor="cascade",
        action=(
            f"Cascade complete for source {source_id} ({source['name']}): "
            f"{report['total_affected']} claims affected"
        ),
        data_accessed={
            "source_id":       source_id,
            "original_trust":  original_trust,
            "new_trust":       new_trust_score,
            "survived":        len(report["survived"]),
            "immediate_return": len(report["immediate_return"]),
            "urgent_flag":     len(report["urgent_flag"]),
            "review_flag":     len(report["review_flag"]),
        },
    )

    log.info(
        f"[CASCADE] Complete: survived={len(report['survived'])} "
        f"immediate_return={len(report['immediate_return'])} "
        f"urgent_flag={len(report['urgent_flag'])} "
        f"review_flag={len(report['review_flag'])}"
    )

    return report


# ---------------------------------------------------------------------------
# Tier handlers
# ---------------------------------------------------------------------------

def _handle_survived(claim, snapshot, source_id, source_name,
                     independently_confirmed, sid, report):
    """Predictions survived through independent channels. Re-promote."""
    adjusted = _adjusted_confidence_without_source(
        snapshot, source_id, independently_confirmed
    )

    # Return to staged first (required to re-promote)
    retcon_ledger.return_to_staged(
        claim_id=claim["id"],
        reason=(
            f"cascade_intermediate: evaluating re-promotion after "
            f"{source_name} compromise"
        ),
        immediate=True,
        session_id=sid,
    )
    retcon_ledger.promote_claim(
        claim_id=claim["id"],
        confidence=adjusted["confidence"],
        source_weights=adjusted["source_weights"],
        threshold=snapshot["threshold_at_promotion"],
        evidence=[
            f"Re-promoted: {independently_confirmed} predictions confirmed "
            f"independently of {source_name}"
        ],
        predictions=snapshot["falsification_predictions"],
        session_id=sid,
    )

    audit.log_event(
        session_id=sid,
        event_type="cascade_survived",
        actor="cascade",
        action=(
            f"Claim {claim['id']} survived cascade: "
            f"{independently_confirmed} predictions independently confirmed"
        ),
        data_accessed={
            "claim_id":                claim["id"],
            "source_id":               source_id,
            "adjusted_confidence":     adjusted["confidence"],
            "independent_confirmations": independently_confirmed,
        },
        trust_level="PROMOTED",
    )

    report["survived"].append({
        "claim_id":               claim["id"],
        "adjusted_confidence":    adjusted["confidence"],
        "independent_confirmations": independently_confirmed,
    })

    log.info(
        f"[CASCADE] Claim {claim['id']} survived: "
        f"re-promoted at {adjusted['confidence']:.3f}"
    )


def _handle_sole_corroborator(claim, source_id, source_name, source_load, sid, report):
    """Source bore >80% of promotion weight. Immediate return, no analyst wait."""
    retcon_ledger.return_to_staged(
        claim_id=claim["id"],
        reason=(
            f"sole_corroborating_source_compromised: {source_name} "
            f"(load={source_load:.2f})"
        ),
        immediate=True,
        session_id=sid,
    )

    report["immediate_return"].append({
        "claim_id":    claim["id"],
        "source_load": round(source_load, 4),
    })

    log.info(
        f"[CASCADE] Claim {claim['id']} → RETURNED_TO_STAGED "
        f"(sole corroborator {source_name}, load={source_load:.2f})"
    )


def _handle_decisive(claim, source_id, source_name, source_load, sid, report):
    """Source bore 50–80% of promotion weight. Urgent flag — operator decides."""
    audit.log_event(
        session_id=sid,
        event_type="cascade_urgent_flag",
        actor="cascade",
        action=(
            f"Claim {claim['id']} URGENT: decisive corroborator {source_name} "
            f"compromised (load={source_load:.2f})"
        ),
        data_accessed={
            "claim_id":    claim["id"],
            "source_id":   source_id,
            "source_load": source_load,
        },
        trust_level="PROMOTED",
    )

    report["urgent_flag"].append({
        "claim_id":    claim["id"],
        "source_load": round(source_load, 4),
    })

    log.info(
        f"[CASCADE] Claim {claim['id']} URGENT FLAG "
        f"(decisive {source_name}, load={source_load:.2f})"
    )


def _handle_partial(claim, source_id, source_name, source_load,
                    original_trust, sid, report):
    """Source bore <50% of promotion weight. Confidence haircut + review flag."""
    delta = -(source_load * original_trust)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE claims
                SET staging_confidence = GREATEST(0.0, staging_confidence + %s)
                WHERE id = %s
                """,
                (delta, claim["id"]),
            )

    audit.log_event(
        session_id=sid,
        event_type="cascade_confidence_haircut",
        actor="cascade",
        action=(
            f"Claim {claim['id']} confidence haircut {delta:.3f} "
            f"(partial corroborator {source_name} compromised, load={source_load:.2f})"
        ),
        data_accessed={
            "claim_id":         claim["id"],
            "source_id":        source_id,
            "source_load":      source_load,
            "confidence_delta": delta,
        },
        trust_level="PROMOTED",
    )

    report["review_flag"].append({
        "claim_id":         claim["id"],
        "source_load":      round(source_load, 4),
        "confidence_delta": round(delta, 4),
    })

    log.info(
        f"[CASCADE] Claim {claim['id']} haircut {delta:.3f} "
        f"(partial {source_name})"
    )


# ---------------------------------------------------------------------------
# Independence verification
# ---------------------------------------------------------------------------

def _verify_independence(confirming_source_id: int, compromised_source_id: int) -> bool:
    """
    Returns True only if the confirming source is genuinely independent
    of the compromised source.

    Checks:
      1. Not the same source
      2. No direct amplification edge (either direction)
      3. Not in the same cluster

    Conservative: returns False if source IDs are equal or any check fails.
    SWARMFISH topology cross-validation: Phase 4 integration point.
    """
    if confirming_source_id == compromised_source_id:
        return False

    if source_intel.sources_are_connected(confirming_source_id, compromised_source_id):
        return False

    if source_intel.sources_in_same_cluster(confirming_source_id, compromised_source_id):
        return False

    return True


def _count_independent_confirmations(predictions: list, compromised_source_id: int) -> int:
    """
    Count how many falsification predictions were confirmed by sources
    genuinely independent of the compromised source.
    """
    count = 0
    for pred in predictions:
        confirmed_by = pred.get("confirmed_by")
        if not confirmed_by:
            continue
        confirming_id = _parse_source_id(confirmed_by)
        if confirming_id is None:
            # Can't verify — conservative: skip
            continue
        if _verify_independence(confirming_id, compromised_source_id):
            count += 1
    return count


def _parse_source_id(confirmed_by) -> Optional[int]:
    """
    Extract a source ID integer from a confirmed_by value.
    Accepts int directly or a string that parses as int.
    Returns None if unparseable (conservative: treat as not independent).
    """
    if isinstance(confirmed_by, int):
        return confirmed_by
    try:
        return int(str(confirmed_by).strip())
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Confidence adjustment
# ---------------------------------------------------------------------------

def _adjusted_confidence_without_source(
    snapshot: dict, compromised_source_id: int, independently_confirmed: int
) -> dict:
    """
    Recalculate promotion confidence after removing the compromised source.

    1. Strip the compromised source from source_weights.
    2. Renormalize remaining weights to sum to 1.0.
    3. Scale base confidence by the remaining fraction of the original load.
    4. Add a boost for independently confirmed predictions (0.05 per, capped at 0.15).

    Returns:
        { "confidence": float, "source_weights": dict }
    """
    weights = dict(snapshot["source_weights"])
    compromised_load = float(weights.pop(str(compromised_source_id), 0.0))

    # Renormalize
    total = sum(weights.values())
    if total > 0:
        weights = {k: round(v / total, 6) for k, v in weights.items()}

    # Base confidence scaled to remaining evidence weight
    remaining_fraction = 1.0 - compromised_load
    base = snapshot["promotion_confidence"] * remaining_fraction

    # Prediction confirmation boost
    boost = min(independently_confirmed * PREDICTION_CONFIRMATION_BOOST,
                PREDICTION_CONFIRMATION_BOOST_CAP)

    adjusted = min(0.99, base + boost)

    return {
        "confidence":    round(adjusted, 4),
        "source_weights": weights,
    }


# ---------------------------------------------------------------------------
# DB query: find claims where source appears in source_weights
# ---------------------------------------------------------------------------

def _get_claims_with_source_contribution(source_id: int) -> list:
    """
    Find all PROMOTED claims where source_id is a key in source_weights JSONB.
    Returns claims with their most recent promotion snapshot attached.

    Uses PostgreSQL JSON key existence operator (?).
    In psycopg2, ? is a literal character (not a placeholder), so this
    combines ? (JSON operator) with %s (psycopg2 parameter).
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.id, c.claim_text, c.trust_level,
                    ps.id AS snapshot_id,
                    ps.source_weights,
                    ps.promotion_confidence,
                    ps.threshold_at_promotion,
                    ps.falsification_predictions,
                    ps.promoting_evidence
                FROM claims c
                JOIN promotion_snapshots ps ON ps.claim_id = c.id
                WHERE c.trust_level = 'PROMOTED'
                  AND ps.source_weights ? %s
                ORDER BY ps.promoted_at DESC
                """,
                (str(source_id),),
            )
            rows = cur.fetchall()

    result = []
    seen_claim_ids = set()
    for row in rows:
        # Take only the most recent snapshot per claim (ORDER BY promoted_at DESC)
        if row["id"] in seen_claim_ids:
            continue
        seen_claim_ids.add(row["id"])
        result.append({
            "id":         row["id"],
            "claim_text": row["claim_text"],
            "trust_level": row["trust_level"],
            "snapshot": {
                "id":                     row["snapshot_id"],
                "source_weights":         dict(row["source_weights"]),
                "promotion_confidence":   row["promotion_confidence"],
                "threshold_at_promotion": row["threshold_at_promotion"],
                "falsification_predictions": list(
                    row["falsification_predictions"] or []
                ),
                "promoting_evidence": list(row["promoting_evidence"] or []),
            },
        })

    return result
