"""
calibration.py — SWARMFISH V2 Brier scoring and calibration

V2 adds domain-specific calibration: per-profile per-domain Brier scores.
Adapted from V1 tracker.py for SQLite.
"""

import json
import sqlite3
import uuid
from statistics import mean
from typing import Optional

# Window for calibration update (minimum predictions before weights change)
MIN_CALIBRATION_PREDICTIONS = 5
CALIBRATION_WINDOW = 50  # use last N predictions for rolling calibration


# ─────────────────────────────────────────────────────────────
# Brier score
# ─────────────────────────────────────────────────────────────

def brier_score(confidence: float, outcome: float) -> float:
    """Brier score: (confidence - outcome)^2. Perfect = 0.0, random = 0.25."""
    return (confidence - outcome) ** 2


# ─────────────────────────────────────────────────────────────
# Record session outcome
# ─────────────────────────────────────────────────────────────

def record_session_outcome(conn: sqlite3.Connection, session_id: str,
                            outcome: float, outcome_date: Optional[str] = None,
                            notes: Optional[str] = None) -> dict:
    """
    Log an outcome for an entire session (outcome 0.0–1.0: 0=wrong, 1=correct, 0.5=partial).
    Scores all profile assessments in the session, updates calibration weights.
    Returns summary dict.
    """
    # Fetch all assessments for this session
    rows = conn.execute("""
        SELECT id, profile_name, confidence, domain
        FROM acp_assessments
        WHERE session_id = ? AND confidence IS NOT NULL AND error IS NULL
    """, (session_id,)).fetchall()

    if not rows:
        return {"error": f"No scoreable assessments for session {session_id}"}

    outcome_id = str(uuid.uuid4())
    conn.execute("""
        INSERT INTO acp_outcomes (id, session_id, outcome, outcome_date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (outcome_id, session_id, outcome, outcome_date, notes))

    scored = []
    for row in rows:
        assessment_id, profile_name, confidence, domain = (
            row["id"], row["profile_name"], row["confidence"], row["domain"]
        )
        score = brier_score(confidence, outcome)

        conn.execute("""
            INSERT INTO acp_calibration (profile_name, domain, brier_score, confidence, was_correct, session_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            profile_name, domain or "general", score, confidence,
            1 if outcome >= 0.5 else 0, session_id
        ))

        updated = _maybe_update_calibration(conn, profile_name, domain or "general")
        notable = _flag_notable(confidence, outcome)

        scored.append({
            "profile_name": profile_name,
            "confidence": confidence,
            "brier_score": round(score, 4),
            "calibration_updated": updated,
            "notable": notable,
        })

    conn.commit()

    avg_brier = mean(s["brier_score"] for s in scored)
    return {
        "outcome_id": outcome_id,
        "session_id": session_id,
        "outcome": outcome,
        "avg_brier_score": round(avg_brier, 4),
        "profiles_scored": len(scored),
        "profile_scores": scored,
    }


# ─────────────────────────────────────────────────────────────
# Calibration update
# ─────────────────────────────────────────────────────────────

def _maybe_update_calibration(conn: sqlite3.Connection,
                               profile_name: str, domain: str) -> bool:
    """
    Recompute confidence_calibration and consensus_weight for profile+domain
    if we have at least MIN_CALIBRATION_PREDICTIONS. Returns True if updated.
    """
    rows = conn.execute("""
        SELECT brier_score, confidence, was_correct
        FROM acp_calibration
        WHERE profile_name = ? AND domain = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (profile_name, domain, CALIBRATION_WINDOW)).fetchall()

    if len(rows) < MIN_CALIBRATION_PREDICTIONS:
        return False

    brier_scores  = [r["brier_score"] for r in rows]
    confidences   = [r["confidence"] for r in rows]
    correct_flags = [r["was_correct"] for r in rows]

    avg_brier      = mean(brier_scores)
    avg_confidence = mean(confidences)
    avg_accuracy   = mean(float(c) for c in correct_flags)

    calibration_bias = avg_accuracy - avg_confidence
    consensus_weight = max(0.5, min(2.0, 0.25 / max(avg_brier, 0.05)))

    profile_row = conn.execute(
        "SELECT confidence_calibration, consensus_weight FROM acp_profiles WHERE name = ?",
        (profile_name,)
    ).fetchone()

    if not profile_row:
        return False

    calib_json  = json.loads(profile_row["confidence_calibration"] or '{"default": 0.0}')
    weight_json = json.loads(profile_row["consensus_weight"] or '{"default": 1.0}')

    calib_json[domain]  = round(calibration_bias, 4)
    weight_json[domain] = round(consensus_weight, 4)

    conn.execute("""
        UPDATE acp_profiles
        SET confidence_calibration = ?, consensus_weight = ?, updated_at = datetime('now')
        WHERE name = ?
    """, (json.dumps(calib_json), json.dumps(weight_json), profile_name))
    conn.commit()

    print(f"[SWARM-CAL] {profile_name}/{domain}: bias={calibration_bias:+.3f} "
          f"weight={consensus_weight:.3f} (n={len(rows)})", flush=True)
    return True


# ─────────────────────────────────────────────────────────────
# Notable episode detection
# ─────────────────────────────────────────────────────────────

def _flag_notable(confidence: float, outcome: float) -> Optional[dict]:
    """Flag overconfident misses and underconfident hits."""
    was_correct = outcome >= 0.5
    if confidence > 0.80 and not was_correct:
        return {
            "type": "overconfident_miss",
            "confidence": confidence,
            "lesson": f"High confidence ({confidence:.0%}) was wrong. Review for systematic bias.",
        }
    if confidence < 0.30 and was_correct:
        return {
            "type": "underconfident_hit",
            "confidence": confidence,
            "lesson": f"Low confidence ({confidence:.0%}) was correct. This analytical frame may be stronger than it believes.",
        }
    return None


# ─────────────────────────────────────────────────────────────
# Calibration summary (for status reporting)
# ─────────────────────────────────────────────────────────────

def get_calibration_summary(conn: sqlite3.Connection,
                             profile_name: Optional[str] = None) -> list:
    """Return calibration data per profile/domain. V2: includes domain breakdown."""
    if profile_name:
        rows = conn.execute("""
            SELECT profile_name, domain,
                   COUNT(*) as n_predictions,
                   AVG(brier_score) as avg_brier,
                   AVG(confidence) as avg_confidence,
                   AVG(CAST(was_correct AS FLOAT)) as avg_accuracy
            FROM acp_calibration
            WHERE profile_name = ?
            GROUP BY profile_name, domain
            ORDER BY profile_name, domain
        """, (profile_name,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT profile_name, domain,
                   COUNT(*) as n_predictions,
                   AVG(brier_score) as avg_brier,
                   AVG(confidence) as avg_confidence,
                   AVG(CAST(was_correct AS FLOAT)) as avg_accuracy
            FROM acp_calibration
            GROUP BY profile_name, domain
            ORDER BY profile_name, avg_brier
        """).fetchall()

    return [dict(r) for r in rows]


def get_profile_calibration_state(conn: sqlite3.Connection) -> list:
    """Return current consensus_weight and confidence_calibration per profile."""
    rows = conn.execute("""
        SELECT name, consensus_weight, confidence_calibration,
               (SELECT COUNT(*) FROM acp_calibration WHERE profile_name = acp_profiles.name) as n_total
        FROM acp_profiles ORDER BY name
    """).fetchall()

    result = []
    for r in rows:
        result.append({
            "name": r["name"],
            "n_scored": r["n_total"],
            "consensus_weight": json.loads(r["consensus_weight"] or '{"default": 1.0}'),
            "confidence_calibration": json.loads(r["confidence_calibration"] or '{"default": 0.0}'),
        })
    return result
