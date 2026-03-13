"""
hypothesis.py — Multi-hypothesis registry.

Implements Chamberlin's method of multiple competing hypotheses:
register several candidate explanations for an observation, each
generating falsifiable predictions. The survivor is the hypothesis
whose predictions matched reality, not the analyst's prior.

The survivor advances to PROMOTED. Defeated explanations are FALSIFIED
with their falsification evidence preserved — the loss is part of the record.

Phase 2 implementation. observation_id is an opaque integer reference.
Full FK binding to a narrative_id comes in Phase 2+.
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

VALID_STATUSES = frozenset(("ACTIVE", "PROMOTED", "FALSIFIED", "SUSPENDED"))


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_hypothesis(
    observation_id: int,
    explanation: str,
    initial_confidence: float = 0.0,
    predictions: list = None,
    session_id=None,
) -> dict:
    """
    Register a candidate hypothesis for an observation.

    Multiple hypotheses can exist for the same observation_id.
    Each begins ACTIVE and generates its own prediction set.

    Args:
        observation_id:     Opaque event reference (FK to narrative_id in Phase 2+)
        explanation:        Candidate explanation text
        initial_confidence: Starting confidence (0.0–1.0)
        predictions:        List of prediction dicts:
                              [{"prediction": str, "falsifiable_by": str|null}]
        session_id:         UUID for audit trail

    Returns:
        dict with hypothesis_id, observation_id, status, created_at
    """
    sid = session_id or uuid.uuid4()
    predictions = predictions or []
    initial_confidence = max(0.0, min(1.0, float(initial_confidence)))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO hypothesis_registry
                    (observation_id, candidate_explanation,
                     current_confidence, predictions_generated)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    observation_id,
                    explanation,
                    initial_confidence,
                    psycopg2.extras.Json(predictions),
                ),
            )
            row = cur.fetchone()

    audit.log_event(
        session_id=sid,
        event_type="hypothesis_registered",
        actor="analyst",
        action=(
            f"Registered hypothesis {row['id']} for observation "
            f"{observation_id}: {explanation[:80]}"
        ),
        data_accessed={
            "hypothesis_id":  row["id"],
            "observation_id": observation_id,
            "predictions_count": len(predictions),
        },
    )

    log.info(
        f"[HYPOTHESIS] Registered #{row['id']} for observation {observation_id} "
        f"(confidence={initial_confidence:.2f}, predictions={len(predictions)})"
    )

    return {
        "hypothesis_id":  row["id"],
        "observation_id": observation_id,
        "status":         "ACTIVE",
        "created_at":     row["created_at"].isoformat(),
    }


# ---------------------------------------------------------------------------
# Confidence update
# ---------------------------------------------------------------------------

def update_confidence(
    hypothesis_id: int, confidence: float, session_id=None
) -> dict:
    """
    Update the current_confidence for an ACTIVE hypothesis.

    Args:
        hypothesis_id:  ID of the hypothesis to update
        confidence:     New confidence value (0.0–1.0)

    Returns:
        dict with hypothesis_id, confidence, status

    Raises:
        ValueError: if hypothesis not found or not ACTIVE
    """
    sid = session_id or uuid.uuid4()
    confidence = max(0.0, min(1.0, float(confidence)))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, status FROM hypothesis_registry WHERE id = %s",
                (hypothesis_id,),
            )
            hyp = cur.fetchone()
            if not hyp:
                raise ValueError(f"Hypothesis {hypothesis_id} not found")
            if hyp["status"] != "ACTIVE":
                raise ValueError(
                    f"Hypothesis {hypothesis_id} is {hyp['status']}, "
                    "only ACTIVE hypotheses can be updated"
                )
            cur.execute(
                "UPDATE hypothesis_registry SET current_confidence = %s WHERE id = %s",
                (confidence, hypothesis_id),
            )

    return {"hypothesis_id": hypothesis_id, "confidence": confidence, "status": "ACTIVE"}


# ---------------------------------------------------------------------------
# Prediction confirmation
# ---------------------------------------------------------------------------

def confirm_prediction(
    hypothesis_id: int, prediction_idx: int, session_id=None
) -> dict:
    """
    Record that a specific prediction for this hypothesis came true.

    Increments predictions_confirmed. Does not require the hypothesis to
    be ACTIVE — confirmed predictions on FALSIFIED hypotheses are still
    informative (the hypothesis made the right prediction but was killed
    on other grounds).

    Args:
        hypothesis_id:  ID of the hypothesis
        prediction_idx: 0-based index into predictions_generated list

    Returns:
        dict with hypothesis_id, predictions_confirmed, prediction_idx

    Raises:
        ValueError: if hypothesis not found or prediction_idx out of range
    """
    sid = session_id or uuid.uuid4()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, predictions_generated, predictions_confirmed "
                "FROM hypothesis_registry WHERE id = %s",
                (hypothesis_id,),
            )
            hyp = cur.fetchone()
            if not hyp:
                raise ValueError(f"Hypothesis {hypothesis_id} not found")

            preds = list(hyp["predictions_generated"] or [])
            if prediction_idx < 0 or prediction_idx >= len(preds):
                raise ValueError(
                    f"prediction_idx {prediction_idx} out of range "
                    f"(hypothesis has {len(preds)} predictions)"
                )

            cur.execute(
                "UPDATE hypothesis_registry "
                "SET predictions_confirmed = predictions_confirmed + 1 "
                "WHERE id = %s",
                (hypothesis_id,),
            )
            new_count = hyp["predictions_confirmed"] + 1

    audit.log_event(
        session_id=sid,
        event_type="hypothesis_prediction_confirmed",
        actor="analyst",
        action=(
            f"Prediction {prediction_idx} confirmed for hypothesis {hypothesis_id}"
        ),
        data_accessed={
            "hypothesis_id":         hypothesis_id,
            "prediction_idx":        prediction_idx,
            "predictions_confirmed": new_count,
        },
    )

    log.info(
        f"[HYPOTHESIS] #{hypothesis_id} prediction {prediction_idx} confirmed "
        f"(total confirmed: {new_count})"
    )

    return {
        "hypothesis_id":         hypothesis_id,
        "prediction_idx":        prediction_idx,
        "predictions_confirmed": new_count,
    }


# ---------------------------------------------------------------------------
# Falsification
# ---------------------------------------------------------------------------

def falsify_hypothesis(
    hypothesis_id: int, evidence: str, session_id=None
) -> dict:
    """
    Mark a hypothesis as FALSIFIED.

    Records the falsification evidence — defeated explanations are preserved,
    not deleted. The loss is part of the record.

    Args:
        hypothesis_id:  ID of the hypothesis
        evidence:       Text description of why the hypothesis was falsified

    Returns:
        dict with hypothesis_id, status, falsified_at

    Raises:
        ValueError: if hypothesis not found or already in terminal state
    """
    sid = session_id or uuid.uuid4()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, status FROM hypothesis_registry WHERE id = %s",
                (hypothesis_id,),
            )
            hyp = cur.fetchone()
            if not hyp:
                raise ValueError(f"Hypothesis {hypothesis_id} not found")
            if hyp["status"] in ("FALSIFIED", "PROMOTED"):
                raise ValueError(
                    f"Hypothesis {hypothesis_id} is already {hyp['status']}"
                )

            cur.execute(
                """
                UPDATE hypothesis_registry
                SET status = 'FALSIFIED',
                    falsified_at = NOW(),
                    falsification_evidence = %s
                WHERE id = %s
                RETURNING falsified_at
                """,
                (evidence, hypothesis_id),
            )
            row = cur.fetchone()

    audit.log_event(
        session_id=sid,
        event_type="hypothesis_falsified",
        actor="analyst",
        action=f"Hypothesis {hypothesis_id} FALSIFIED: {evidence[:120]}",
        data_accessed={
            "hypothesis_id": hypothesis_id,
            "evidence":      evidence,
        },
    )

    log.info(f"[HYPOTHESIS] #{hypothesis_id} FALSIFIED")

    return {
        "hypothesis_id": hypothesis_id,
        "status":        "FALSIFIED",
        "falsified_at":  row["falsified_at"].isoformat(),
    }


# ---------------------------------------------------------------------------
# Promotion
# ---------------------------------------------------------------------------

def promote_hypothesis(hypothesis_id: int, session_id=None) -> dict:
    """
    Promote the winning hypothesis — the one whose predictions matched reality.

    Args:
        hypothesis_id:  ID of the hypothesis to promote

    Returns:
        dict with hypothesis_id, status

    Raises:
        ValueError: if hypothesis not found or not ACTIVE
    """
    sid = session_id or uuid.uuid4()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, status, observation_id FROM hypothesis_registry WHERE id = %s",
                (hypothesis_id,),
            )
            hyp = cur.fetchone()
            if not hyp:
                raise ValueError(f"Hypothesis {hypothesis_id} not found")
            if hyp["status"] != "ACTIVE":
                raise ValueError(
                    f"Hypothesis {hypothesis_id} is {hyp['status']}, "
                    "only ACTIVE hypotheses can be promoted"
                )

            cur.execute(
                "UPDATE hypothesis_registry SET status = 'PROMOTED' WHERE id = %s",
                (hypothesis_id,),
            )

    audit.log_event(
        session_id=sid,
        event_type="hypothesis_promoted",
        actor="analyst",
        action=(
            f"Hypothesis {hypothesis_id} PROMOTED "
            f"(observation {hyp['observation_id']})"
        ),
        data_accessed={
            "hypothesis_id":  hypothesis_id,
            "observation_id": hyp["observation_id"],
        },
    )

    log.info(f"[HYPOTHESIS] #{hypothesis_id} PROMOTED")

    return {"hypothesis_id": hypothesis_id, "status": "PROMOTED"}


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_hypotheses(
    observation_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> list:
    """
    List hypotheses with optional filters.

    Args:
        observation_id: Filter by observation
        status:         Filter by status (ACTIVE, PROMOTED, FALSIFIED, SUSPENDED)
        limit:          Max results (default 50)

    Returns:
        List of hypothesis dicts ordered by created_at DESC
    """
    if status and status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status!r}. Must be one of {sorted(VALID_STATUSES)}")

    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id, observation_id, candidate_explanation,
                       created_at, current_confidence, status,
                       predictions_generated, predictions_confirmed,
                       predictions_falsified, falsified_at,
                       falsification_evidence
                FROM hypothesis_registry
                WHERE 1=1
            """
            params: list = []
            if observation_id is not None:
                query += " AND observation_id = %s"
                params.append(observation_id)
            if status:
                query += " AND status = %s"
                params.append(status)
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
