"""
hypothesis.py — Chamberlin's method hypothesis registry.

Each observation can have multiple competing hypotheses. Hypotheses are
confirmed/falsified by evidence as the investigation proceeds.
"""
import logging
from datetime import datetime, timezone

from .db import jloads, jdumps, new_id

log = logging.getLogger("[HYPOTHESIS]")


# ---------------------------------------------------------------------------
# Swarmfish notification (best-effort, import-guarded)
# ---------------------------------------------------------------------------

def _notify_swarmfish(session_id, outcome):
    try:
        import sys
        sys.path.insert(0, "/a0/usr/plugins/swarmfish")
        from src.db import get_conn as sf_conn  # noqa: PLC0415
        conn = sf_conn()
        conn.execute(
            "INSERT OR IGNORE INTO acp_outcomes (session_id, outcome) VALUES (?,?)",
            (session_id, outcome),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register_hypothesis(conn, observation_id, candidate_explanation: str,
                        predictions=None, initial_confidence: float = 0.0) -> dict:
    """
    Create a new hypothesis for an observation.
    Returns the newly created row as a dict.
    """
    try:
        preds_json = jdumps(predictions or [])
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO hypothesis_registry
                (observation_id, candidate_explanation, created_at,
                 current_confidence, status, predictions_generated)
            VALUES (?,?,?,?,?,?)
        """, (
            observation_id,
            candidate_explanation,
            now,
            max(0.0, min(1.0, float(initial_confidence))),
            "ACTIVE",
            preds_json,
        ))
        conn.commit()
        hid = cur.lastrowid
        log.info(f"Registered hypothesis id={hid} for observation={observation_id}")
        return _get_by_id(conn, hid)
    except Exception as e:
        log.warning(f"register_hypothesis failed: {e}")
        raise


def update_confidence(conn, hypothesis_id, new_confidence) -> dict:
    """Update the current confidence score for a hypothesis."""
    try:
        conf = max(0.0, min(1.0, float(new_confidence)))
        conn.execute(
            "UPDATE hypothesis_registry SET current_confidence=? WHERE id=?",
            (conf, hypothesis_id),
        )
        conn.commit()
        return _get_by_id(conn, hypothesis_id)
    except Exception as e:
        log.warning(f"update_confidence failed: {e}")
        raise


def confirm_prediction(conn, hypothesis_id) -> dict:
    """Increment the confirmed-predictions counter for a hypothesis."""
    try:
        conn.execute(
            "UPDATE hypothesis_registry "
            "SET predictions_confirmed = predictions_confirmed + 1 "
            "WHERE id=?",
            (hypothesis_id,),
        )
        conn.commit()
        return _get_by_id(conn, hypothesis_id)
    except Exception as e:
        log.warning(f"confirm_prediction failed: {e}")
        raise


def falsify_hypothesis(conn, hypothesis_id, evidence: str) -> dict:
    """
    Mark a hypothesis as FALSIFIED with supporting evidence.
    Notifies Swarmfish if the hypothesis has a swarmfish_session_id.
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            UPDATE hypothesis_registry
            SET status='FALSIFIED',
                falsified_at=?,
                falsification_evidence=?,
                predictions_falsified = predictions_falsified + 1
            WHERE id=?
        """, (now, evidence, hypothesis_id))
        conn.commit()
        row = _get_by_id(conn, hypothesis_id)
        if row.get("swarmfish_session_id"):
            _notify_swarmfish(row["swarmfish_session_id"], "falsified")
        return row
    except Exception as e:
        log.warning(f"falsify_hypothesis failed: {e}")
        raise


def promote_hypothesis(conn, hypothesis_id) -> dict:
    """
    Mark a hypothesis as PROMOTED (elevated to working model).
    Notifies Swarmfish if the hypothesis has a swarmfish_session_id.
    """
    try:
        conn.execute(
            "UPDATE hypothesis_registry SET status='PROMOTED' WHERE id=?",
            (hypothesis_id,),
        )
        conn.commit()
        row = _get_by_id(conn, hypothesis_id)
        if row.get("swarmfish_session_id"):
            _notify_swarmfish(row["swarmfish_session_id"], "promoted")
        return row
    except Exception as e:
        log.warning(f"promote_hypothesis failed: {e}")
        raise


def get_hypotheses(conn, observation_id=None, status=None, limit: int = 50) -> list:
    """
    Retrieve hypotheses, optionally filtered by observation or status.
    Returns newest first.
    """
    try:
        cur = conn.cursor()
        clauses = []
        params = []
        if observation_id is not None:
            clauses.append("observation_id=?")
            params.append(observation_id)
        if status is not None:
            clauses.append("status=?")
            params.append(status.upper())

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)
        cur.execute(
            f"SELECT * FROM hypothesis_registry {where} ORDER BY id DESC LIMIT ?",
            params,
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_hypotheses failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_by_id(conn, hypothesis_id) -> dict:
    cur = conn.cursor()
    cur.execute("SELECT * FROM hypothesis_registry WHERE id=?", (hypothesis_id,))
    row = cur.fetchone()
    return dict(row) if row else {}
