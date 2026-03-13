"""
retcon_ledger.py — Claim trust lifecycle management.

Claims begin STAGED. When sufficient corroborating evidence accumulates,
an analyst promotes them to PROMOTED — creating a frozen snapshot of the
decision at that moment.

The snapshot is the defense against the patient adversary: when a source
is later compromised, the snapshot lets the contamination cascade reconstruct
exactly what the decision looked like when it was made — not a current
approximation of it.

Phase 2 implements the contamination cascade on top of these snapshots.
Phase 1: promotion mechanism, frozen snapshots, trust level transitions.
"""

import os
import uuid
import logging
from typing import Optional

import psycopg2
import psycopg2.extras

import audit

log = logging.getLogger(__name__)

DB_URL = os.environ.get(
    "OSS_DB_URL",
    "postgresql://oss_app:oss_app_dev_password@localhost:5433/oss"
)

DEFAULT_PROMOTION_THRESHOLD = float(os.environ.get("OSS_PROMOTION_THRESHOLD", "0.75"))


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def promote_claim(
    claim_id: int,
    confidence: float,
    source_weights: dict,
    threshold: float = None,
    evidence: list = None,
    predictions: list = None,
    session_id=None,
) -> dict:
    """
    Promote a STAGED claim to PROMOTED status. Creates a frozen snapshot.

    The snapshot records everything about this promotion decision so the
    contamination cascade can reconstruct it precisely if a source is later
    compromised.

    Args:
        claim_id:       ID of the claim to promote
        confidence:     Analyst-assessed confidence (0.0–1.0)
        source_weights: Dict mapping str(source_id) → weight (float), sum ~1.0
                        e.g. {"12": 0.60, "7": 0.25, "3": 0.15}
        threshold:      Confidence threshold applied at this promotion
        evidence:       List of evidence strings supporting the promotion
        predictions:    List of falsification prediction dicts:
                          [{"prediction": "oil above $95 within 72hrs",
                            "confirmed_by": null,
                            "confirmed_at": null,
                            "independent_of_source": null}]
        session_id:     UUID for audit trail (generated if not provided)

    Returns:
        dict with snapshot_id, claim_id, promoted_at, confidence

    Raises:
        ValueError: if claim not found or not in a promotable state
    """
    sid = session_id or uuid.uuid4()
    threshold = threshold if threshold is not None else DEFAULT_PROMOTION_THRESHOLD
    predictions = predictions or []
    evidence = evidence or []

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, trust_level, claim_text FROM claims WHERE id = %s",
                (claim_id,),
            )
            claim = cur.fetchone()
            if not claim:
                raise ValueError(f"Claim {claim_id} not found")
            if claim["trust_level"] not in ("STAGED", "RETURNED_TO_STAGED"):
                raise ValueError(
                    f"Claim {claim_id} is {claim['trust_level']}, cannot promote. "
                    "Only STAGED or RETURNED_TO_STAGED claims can be promoted."
                )

            # Freeze the snapshot — never update this row
            cur.execute(
                """
                INSERT INTO promotion_snapshots
                    (claim_id, promotion_confidence, source_weights,
                     threshold_at_promotion, promoting_evidence,
                     falsification_predictions)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, promoted_at
                """,
                (
                    claim_id,
                    confidence,
                    psycopg2.extras.Json(source_weights),
                    threshold,
                    evidence if evidence else None,
                    psycopg2.extras.Json(predictions),
                ),
            )
            snapshot = cur.fetchone()

            cur.execute(
                "UPDATE claims SET trust_level = 'PROMOTED', staging_confidence = %s "
                "WHERE id = %s",
                (confidence, claim_id),
            )

    audit.log_event(
        session_id=sid,
        event_type="claim_promoted",
        actor="analyst",
        action=f"Promoted claim {claim_id} with confidence {confidence:.2f}",
        data_accessed={
            "claim_id": claim_id,
            "snapshot_id": snapshot["id"],
            "source_weights": source_weights,
            "threshold": threshold,
            "predictions_count": len(predictions),
        },
        trust_level="PROMOTED",
    )

    log.info(
        f"[RETCON] Promoted claim {claim_id} → snapshot {snapshot['id']} "
        f"(confidence={confidence:.2f}, sources={list(source_weights.keys())})"
    )

    return {
        "snapshot_id": snapshot["id"],
        "claim_id": claim_id,
        "promoted_at": snapshot["promoted_at"].isoformat(),
        "confidence": confidence,
    }


def return_to_staged(
    claim_id: int,
    reason: str,
    immediate: bool = False,
    session_id=None,
) -> dict:
    """
    Return a PROMOTED claim to RETURNED_TO_STAGED status.

    Called by the contamination cascade (Phase 2) when a corroborating source
    is compromised, or manually by an analyst when new evidence warrants review.

    Args:
        claim_id:   ID of the claim to demote
        reason:     Why the claim is being returned to staging
        immediate:  If True, sole-corroborator case — no analyst review needed
        session_id: UUID for audit trail

    Returns:
        dict with claim_id, previous_trust_level, new_trust_level, reason
    """
    sid = session_id or uuid.uuid4()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, trust_level FROM claims WHERE id = %s", (claim_id,)
            )
            claim = cur.fetchone()
            if not claim:
                raise ValueError(f"Claim {claim_id} not found")

            previous = claim["trust_level"]
            cur.execute(
                "UPDATE claims SET trust_level = 'RETURNED_TO_STAGED' WHERE id = %s",
                (claim_id,),
            )

    audit.log_event(
        session_id=sid,
        event_type="claim_returned_to_staged",
        actor="cascade" if immediate else "analyst",
        action=f"Returned claim {claim_id} to staged: {reason}",
        data_accessed={
            "claim_id": claim_id,
            "previous_trust_level": previous,
            "reason": reason,
            "immediate": immediate,
        },
        trust_level="RETURNED_TO_STAGED",
    )

    log.info(f"[RETCON] Claim {claim_id}: {previous} → RETURNED_TO_STAGED ({reason})")

    return {
        "claim_id": claim_id,
        "previous_trust_level": previous,
        "new_trust_level": "RETURNED_TO_STAGED",
        "reason": reason,
    }


def get_staged_claims(topic: str = None, limit: int = 100) -> list:
    """
    List claims in STAGED or RETURNED_TO_STAGED state awaiting analyst review.
    Ordered newest-first.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT
                    c.id, c.claim_text, c.article_url, c.article_title,
                    c.topic_tags, c.technique_class, c.extracted_at,
                    c.staging_confidence, c.trust_level,
                    s.name AS source_name, s.cluster, s.confidence_score
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE c.trust_level IN ('STAGED', 'RETURNED_TO_STAGED')
            """
            params: list = []
            if topic:
                query += " AND %s = ANY(c.topic_tags)"
                params.append(topic)
            query += " ORDER BY c.extracted_at DESC LIMIT %s"
            params.append(limit)
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]


def get_promoted_claims(topic: str = None, limit: int = 100) -> list:
    """
    List claims in PROMOTED state with their promotion snapshots.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT
                    c.id, c.claim_text, c.article_url, c.article_title,
                    c.topic_tags, c.technique_class, c.extracted_at,
                    c.staging_confidence, c.trust_level,
                    s.name AS source_name, s.cluster, s.confidence_score,
                    ps.id AS snapshot_id, ps.promoted_at,
                    ps.promotion_confidence, ps.source_weights,
                    ps.predictions_confirmed_independently
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                LEFT JOIN promotion_snapshots ps ON ps.claim_id = c.id
                WHERE c.trust_level = 'PROMOTED'
            """
            params: list = []
            if topic:
                query += " AND %s = ANY(c.topic_tags)"
                params.append(topic)
            query += " ORDER BY ps.promoted_at DESC NULLS LAST LIMIT %s"
            params.append(limit)
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]


def get_promotion_snapshot(claim_id: int) -> Optional[dict]:
    """
    Retrieve the frozen promotion snapshot for a claim.
    Returns None if the claim has never been promoted.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM promotion_snapshots
                WHERE claim_id = %s
                ORDER BY promoted_at DESC
                LIMIT 1
                """,
                (claim_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
