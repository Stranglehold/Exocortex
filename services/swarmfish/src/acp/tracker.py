"""
tracker.py — Outcome logging, Brier scoring, calibration update

Called by the operator after a prediction's time horizon has elapsed.
Records what actually happened, computes Brier score, updates the
profile's confidence_calibration and consensus_weight for the relevant domain.

Calibration mechanics from the design note:
  - Brier score: (confidence - outcome)^2
    Perfect calibration: 0.0. Random: 0.25. Worse than random: >0.25.
  - consensus_weight: max(0.5, min(2.0, 0.25 / max(avg_brier, 0.05)))
    Brier 0.25 (random)       → weight 1.0
    Brier 0.10 (good)         → weight 1.5  (approx)
    Brier 0.02 (superforecaster) → weight 2.0 (capped)
  - confidence_calibration per domain: avg_accuracy - avg_confidence (last 50)
    Positive = underconfident → increase expressed confidence
    Negative = overconfident  → decrease expressed confidence
  - Notable episodes: overconfident miss (confidence > 0.8, wrong)
                      underconfident hit  (confidence < 0.3, correct)
"""

import json
import uuid
from statistics import mean
from typing import Optional

import config


# ============================================================
# Brier score
# ============================================================

def brier_score(confidence: float, was_correct: bool) -> float:
    """(confidence - outcome)^2. outcome is 1.0 if correct, 0.0 if wrong."""
    outcome = 1.0 if was_correct else 0.0
    return (confidence - outcome) ** 2


# ============================================================
# Record outcome for a single prediction
# ============================================================

def record_outcome(db_conn, prediction_id: str, outcome: str,
                   was_correct: bool,
                   conditions_that_held: Optional[list] = None,
                   conditions_that_failed: Optional[list] = None,
                   post_mortem_note: Optional[str] = None) -> dict:
    """
    Log an outcome for a specific prediction. Computes Brier score.
    Updates calibration data for the prediction's profile + domain.
    Returns the scored outcome dict.
    """
    cursor = db_conn.cursor()

    # Fetch the prediction
    cursor.execute("""
        SELECT id, profile_name, domain, confidence
        FROM acp_predictions
        WHERE id = %s
    """, (prediction_id,))
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        raise ValueError(f"Prediction {prediction_id} not found")

    pred_id, profile_name, domain, confidence = row

    score = brier_score(confidence, was_correct)
    outcome_id = str(uuid.uuid4())

    # Write outcome
    cursor.execute("""
        INSERT INTO acp_outcomes (
            id, prediction_id, outcome, was_correct, brier_score,
            conditions_that_held, conditions_that_failed, post_mortem_note
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        outcome_id, prediction_id, outcome, was_correct, score,
        json.dumps(conditions_that_held or []),
        json.dumps(conditions_that_failed or []),
        post_mortem_note,
    ))

    # Mark prediction as scored
    cursor.execute("""
        UPDATE acp_predictions SET scored = TRUE WHERE id = %s
    """, (prediction_id,))

    # Write calibration row
    cursor.execute("""
        INSERT INTO acp_calibration (profile_name, domain, brier_score, confidence, was_correct)
        VALUES (%s, %s, %s, %s, %s)
    """, (profile_name, domain, score, confidence, was_correct))

    db_conn.commit()

    # Update profile calibration weights if we have enough data
    updated = _maybe_update_profile_calibration(db_conn, profile_name, domain)

    # Flag notable episodes
    notable = _flag_notable_episode(confidence, was_correct, prediction_id, domain)

    cursor.close()
    return {
        "outcome_id": outcome_id,
        "prediction_id": prediction_id,
        "profile_name": profile_name,
        "domain": domain,
        "confidence": confidence,
        "was_correct": was_correct,
        "brier_score": round(score, 4),
        "calibration_updated": updated,
        "notable_episode": notable,
    }


# ============================================================
# Calibration update
# ============================================================

def _maybe_update_profile_calibration(db_conn, profile_name: str, domain: str) -> bool:
    """
    Recompute confidence_calibration and consensus_weight for this profile+domain
    if we have at least MIN_CALIBRATION_PREDICTIONS scored predictions.
    Returns True if weights were updated.
    """
    cursor = db_conn.cursor()

    cursor.execute("""
        SELECT brier_score, confidence, was_correct
        FROM acp_calibration
        WHERE profile_name = %s AND domain = %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (profile_name, domain, config.CALIBRATION_WINDOW))

    rows = cursor.fetchall()
    if len(rows) < config.MIN_CALIBRATION_PREDICTIONS:
        cursor.close()
        return False

    brier_scores   = [r[0] for r in rows]
    confidences    = [r[1] for r in rows]
    correct_flags  = [r[2] for r in rows]

    avg_brier      = mean(brier_scores)
    avg_confidence = mean(confidences)
    avg_accuracy   = mean(1.0 if c else 0.0 for c in correct_flags)

    # Calibration bias: positive = underconfident, negative = overconfident
    calibration_bias = avg_accuracy - avg_confidence

    # Consensus weight: inversely proportional to Brier score
    consensus_weight = max(0.5, min(2.0, 0.25 / max(avg_brier, 0.05)))

    # Read current profile calibration/weight JSON
    cursor.execute("""
        SELECT confidence_calibration, consensus_weight
        FROM acp_profiles
        WHERE name = %s
    """, (profile_name,))
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        return False

    calib_json  = row[0] if row[0] else {"default": 0.0}
    weight_json = row[1] if row[1] else {"default": 1.0}

    calib_json[domain]  = round(calibration_bias, 4)
    weight_json[domain] = round(consensus_weight, 4)

    cursor.execute("""
        UPDATE acp_profiles
        SET confidence_calibration = %s, consensus_weight = %s
        WHERE name = %s
    """, (json.dumps(calib_json), json.dumps(weight_json), profile_name))

    db_conn.commit()
    cursor.close()

    print(f"[ACP] Calibration updated — {profile_name}/{domain}: "
          f"bias={calibration_bias:+.3f} weight={consensus_weight:.3f} "
          f"(n={len(rows)} predictions)", flush=True)
    return True


# ============================================================
# Notable episode detection
# ============================================================

def _flag_notable_episode(confidence: float, was_correct: bool,
                           prediction_id: str, domain: str) -> Optional[dict]:
    """
    Returns episode dict if this is a notable miss or hit.
    Overconfident miss: confidence > 0.80 and wrong.
    Underconfident hit: confidence < 0.30 and correct.
    """
    if confidence > 0.80 and not was_correct:
        return {
            "type": "overconfident_miss",
            "prediction_id": prediction_id,
            "domain": domain,
            "confidence": confidence,
            "lesson": f"High confidence ({confidence:.0%}) was wrong in {domain}. "
                       "Review reasoning for systematic bias."
        }
    if confidence < 0.30 and was_correct:
        return {
            "type": "underconfident_hit",
            "prediction_id": prediction_id,
            "domain": domain,
            "confidence": confidence,
            "lesson": f"Low confidence ({confidence:.0%}) was right in {domain}. "
                       "This profile's analytical frame may be stronger here than it believes."
        }
    return None


# ============================================================
# Session outcome: score an entire prediction session at once
# ============================================================

def record_session_outcome(db_conn, session_id: str, outcome: str, was_correct: bool,
                            conditions_held: Optional[list] = None,
                            conditions_failed: Optional[list] = None,
                            post_mortem: Optional[str] = None) -> list:
    """
    Score all predictions in a session. Returns list of per-prediction outcome dicts.
    """
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT p.id FROM acp_predictions p
        JOIN acp_session_predictions sp ON sp.prediction_id = p.id
        WHERE sp.session_id = %s AND p.scored = FALSE
    """, (session_id,))
    pred_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()

    results = []
    for pred_id in pred_ids:
        result = record_outcome(
            db_conn, str(pred_id), outcome, was_correct,
            conditions_held, conditions_failed, post_mortem
        )
        results.append(result)

    # Close the session
    cursor = db_conn.cursor()
    from datetime import datetime, timezone
    cursor.execute("""
        UPDATE acp_sessions SET monitoring_active = FALSE, closed_at = %s WHERE id = %s
    """, (datetime.now(timezone.utc), session_id))
    db_conn.commit()
    cursor.close()

    return results


# ============================================================
# Calibration summary (for status reporting)
# ============================================================

def get_calibration_summary(db_conn, profile_name: Optional[str] = None) -> list:
    """Return current calibration data per profile/domain for operator review."""
    cursor = db_conn.cursor()
    if profile_name:
        cursor.execute("""
            SELECT profile_name, domain,
                   COUNT(*) as n_predictions,
                   AVG(brier_score) as avg_brier,
                   AVG(confidence) as avg_confidence,
                   AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) as avg_accuracy
            FROM acp_calibration
            WHERE profile_name = %s
            GROUP BY profile_name, domain
            ORDER BY profile_name, domain
        """, (profile_name,))
    else:
        cursor.execute("""
            SELECT profile_name, domain,
                   COUNT(*) as n_predictions,
                   AVG(brier_score) as avg_brier,
                   AVG(confidence) as avg_confidence,
                   AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) as avg_accuracy
            FROM acp_calibration
            GROUP BY profile_name, domain
            ORDER BY profile_name, domain
        """)
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return [dict(zip(cols, row)) for row in rows]
