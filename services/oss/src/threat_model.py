"""
threat_model.py — Living adversary model.

Tracks adversarial technique observation, abandonment, and predicted adaptation.

Key principle: technique abandonment = the adversary knows it's been detected.
A cluster of abandonments in a short window = the adversary has a feedback loop
on our detection capability. That's a higher-order threat than any single technique.

Technique classes map to claims.technique_class:
  presuasion | fracture | emergent | direct | none

technique_name is sub-class (e.g., 'fracture_attrition' within 'fracture').
record_technique() is idempotent: calling it multiple times for the same
technique_name increments observed_count and refreshes last_observed.

Phase 3 implementation.
"""

import logging
import os
import uuid
from typing import Optional

import psycopg2
import psycopg2.extras

import audit

log = logging.getLogger(__name__)

DB_URL = os.environ.get(
    "OSS_DB_URL",
    "postgresql://oss_app:oss_app_dev_password@localhost:5433/oss"
)

VALID_TECHNIQUE_CLASSES = frozenset(
    ("presuasion", "fracture", "emergent", "direct", "none")
)

# Abandonment cluster: multiple techniques abandoned within this window = feedback loop
ABANDONMENT_CLUSTER_WINDOW_HOURS = 48


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Record technique
# ---------------------------------------------------------------------------

def record_technique(
    technique_name: str,
    technique_class: str,
    detected_by_system: bool = False,
    notes: Optional[str] = None,
    session_id=None,
) -> dict:
    """
    Record or update a technique observation.

    Idempotent: if technique_name already exists, increment observed_count
    and update last_observed. If new, INSERT with first_observed = NOW().

    Args:
        technique_name:      Human-readable technique identifier
        technique_class:     One of: presuasion | fracture | emergent | direct | none
        detected_by_system:  True if detected automatically vs analyst report
        notes:               Optional free-text analyst note
        session_id:          UUID for audit trail

    Returns:
        dict with technique_id, technique_name, status (created | updated)

    Raises:
        ValueError: if technique_class is not in VALID_TECHNIQUE_CLASSES
    """
    sid = session_id or uuid.uuid4()
    technique_name  = technique_name.strip()
    technique_class = technique_class.strip().lower()

    if technique_class not in VALID_TECHNIQUE_CLASSES:
        raise ValueError(
            f"Invalid technique_class: {technique_class!r}. "
            f"Must be one of {sorted(VALID_TECHNIQUE_CLASSES)}"
        )

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, observed_count FROM threat_model WHERE technique_name = %s",
                (technique_name,),
            )
            existing = cur.fetchone()

            if existing:
                cur.execute(
                    """
                    UPDATE threat_model
                    SET observed_count  = observed_count + 1,
                        last_observed   = NOW(),
                        detected_by_system = detected_by_system OR %s,
                        notes           = COALESCE(%s, notes)
                    WHERE id = %s
                    RETURNING id, observed_count
                    """,
                    (detected_by_system, notes, existing["id"]),
                )
                row    = cur.fetchone()
                status = "updated"
                log.info(
                    f"[THREAT] Updated technique '{technique_name}' "
                    f"(observed_count={row['observed_count']})"
                )
            else:
                cur.execute(
                    """
                    INSERT INTO threat_model
                        (technique_name, technique_class, first_observed, last_observed,
                         observed_count, detected_by_system, notes)
                    VALUES (%s, %s, NOW(), NOW(), 1, %s, %s)
                    RETURNING id, observed_count
                    """,
                    (technique_name, technique_class, detected_by_system, notes),
                )
                row    = cur.fetchone()
                status = "created"
                log.info(f"[THREAT] Recorded new technique '{technique_name}' ({technique_class})")

    audit.log_event(
        session_id=sid,
        event_type="threat_technique_recorded",
        actor="analyst",
        action=f"Technique '{technique_name}' ({technique_class}) {status}",
        data_accessed={
            "technique_id":    row["id"],
            "technique_name":  technique_name,
            "technique_class": technique_class,
            "status":          status,
        },
    )

    return {
        "technique_id":   row["id"],
        "technique_name": technique_name,
        "status":         status,
    }


# ---------------------------------------------------------------------------
# Flag abandoned
# ---------------------------------------------------------------------------

def flag_abandoned(
    technique_id: int,
    predicted_adaptation: Optional[str] = None,
    session_id=None,
) -> dict:
    """
    Mark a technique as abandoned by the adversary.

    Abandonment = adversary knows this technique is detected.
    Logs a feedback_loop_signal if multiple techniques were abandoned
    in the last ABANDONMENT_CLUSTER_WINDOW_HOURS.

    Args:
        technique_id:          ID of the technique to mark
        predicted_adaptation:  Analyst's prediction of the next technique
        session_id:            UUID for audit trail

    Returns:
        dict with technique_id, abandoned_at, feedback_loop_signal

    Raises:
        ValueError: if technique not found or already abandoned
    """
    sid = session_id or uuid.uuid4()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, technique_name, adversary_abandoned FROM threat_model WHERE id = %s",
                (technique_id,),
            )
            technique = cur.fetchone()
            if not technique:
                raise ValueError(f"Technique {technique_id} not found")
            if technique["adversary_abandoned"]:
                raise ValueError(
                    f"Technique {technique_id} ({technique['technique_name']}) "
                    "is already marked as abandoned"
                )

            cur.execute(
                """
                UPDATE threat_model
                SET adversary_abandoned  = TRUE,
                    abandoned_at         = NOW(),
                    predicted_adaptation = COALESCE(%s, predicted_adaptation)
                WHERE id = %s
                RETURNING abandoned_at
                """,
                (predicted_adaptation, technique_id),
            )
            row = cur.fetchone()

            # Abandonment cluster detection
            cur.execute(
                """
                SELECT COUNT(*) AS recent_abandonments
                FROM threat_model
                WHERE adversary_abandoned = TRUE
                  AND abandoned_at >= NOW() - INTERVAL '%s hours'
                """,
                (ABANDONMENT_CLUSTER_WINDOW_HOURS,),
            )
            cluster_row = cur.fetchone()

    recent = int(cluster_row["recent_abandonments"] or 0)
    feedback_loop = recent >= 2

    if feedback_loop:
        log.warning(
            f"[THREAT] FEEDBACK LOOP SIGNAL: {recent} techniques abandoned "
            f"in last {ABANDONMENT_CLUSTER_WINDOW_HOURS}h — "
            f"adversary has detection feedback"
        )

    audit.log_event(
        session_id=sid,
        event_type="threat_technique_abandoned",
        actor="analyst",
        action=(
            f"Technique {technique_id} ({technique['technique_name']}) "
            f"flagged as abandoned. "
            f"{'FEEDBACK LOOP SIGNAL — cluster of abandonments detected.' if feedback_loop else ''}"
        ),
        data_accessed={
            "technique_id":        technique_id,
            "predicted_adaptation": predicted_adaptation,
            "feedback_loop_signal": feedback_loop,
            "recent_abandonments":  recent,
        },
    )

    return {
        "technique_id":         technique_id,
        "technique_name":       technique["technique_name"],
        "abandoned_at":         row["abandoned_at"].isoformat(),
        "predicted_adaptation": predicted_adaptation,
        "feedback_loop_signal": feedback_loop,
        "recent_abandonments":  recent,
    }


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_threat_model(
    technique_class: Optional[str] = None,
    abandoned: Optional[bool] = None,
    limit: int = 50,
) -> list:
    """
    List techniques with optional filters.

    Args:
        technique_class: Filter by class
        abandoned:       Filter by abandoned status (True/False)
        limit:           Max results (default 50)

    Returns:
        List of technique dicts ordered by last_observed DESC
    """
    if technique_class and technique_class not in VALID_TECHNIQUE_CLASSES:
        raise ValueError(
            f"Invalid technique_class: {technique_class!r}. "
            f"Must be one of {sorted(VALID_TECHNIQUE_CLASSES)}"
        )

    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id, technique_name, technique_class,
                       first_observed, last_observed, observed_count,
                       detected_by_system, adversary_abandoned,
                       abandoned_at, predicted_adaptation, notes
                FROM threat_model
                WHERE 1=1
            """
            params: list = []
            if technique_class:
                query += " AND technique_class = %s"
                params.append(technique_class)
            if abandoned is not None:
                query += " AND adversary_abandoned = %s"
                params.append(abandoned)
            query += " ORDER BY last_observed DESC NULLS LAST LIMIT %s"
            params.append(limit)
            cur.execute(query, params)
            rows = cur.fetchall()

    result = []
    for r in rows:
        d = dict(r)
        if d.get("first_observed"):
            d["first_observed"] = d["first_observed"].isoformat()
        if d.get("last_observed"):
            d["last_observed"] = d["last_observed"].isoformat()
        if d.get("abandoned_at"):
            d["abandoned_at"] = d["abandoned_at"].isoformat()
        result.append(d)
    return result


def get_technique_trend(window_days: int = 30) -> dict:
    """
    Technique observation trend over recent history.

    Returns observations per day grouped by technique_class,
    plus abandonment cluster analysis.

    Abandonment cluster: if >= 2 techniques were abandoned within
    ABANDONMENT_CLUSTER_WINDOW_HOURS, the adversary likely has feedback
    on our detection capability.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Observations per day by class
            cur.execute(
                """
                SELECT
                    technique_class,
                    DATE_TRUNC('day', last_observed) AS day,
                    SUM(observed_count)              AS total_observations
                FROM threat_model
                WHERE last_observed >= NOW() - INTERVAL '%s days'
                  AND last_observed IS NOT NULL
                GROUP BY technique_class, day
                ORDER BY day DESC, technique_class
                """,
                (window_days,),
            )
            trend_rows = cur.fetchall()

            # Abandonment cluster: recent abandonments
            cur.execute(
                """
                SELECT
                    COUNT(*) AS count,
                    MAX(abandoned_at) AS most_recent
                FROM threat_model
                WHERE adversary_abandoned = TRUE
                  AND abandoned_at >= NOW() - INTERVAL '%s hours'
                """,
                (ABANDONMENT_CLUSTER_WINDOW_HOURS,),
            )
            cluster_row = cur.fetchone()

            # Total abandonment history
            cur.execute(
                "SELECT COUNT(*) AS total FROM threat_model WHERE adversary_abandoned = TRUE"
            )
            total_abandoned = int(cur.fetchone()["total"] or 0)

    recent_count = int(cluster_row["count"] or 0)
    trend = []
    for r in trend_rows:
        trend.append({
            "technique_class": r["technique_class"],
            "day":             r["day"].date().isoformat() if r["day"] else None,
            "total_observations": int(r["total_observations"] or 0),
        })

    return {
        "window_days":           window_days,
        "trend":                 trend,
        "abandonment_cluster": {
            "recent_count":              recent_count,
            "cluster_window_hours":      ABANDONMENT_CLUSTER_WINDOW_HOURS,
            "feedback_loop_signal":      recent_count >= 2,
            "most_recent_abandonment":   (
                cluster_row["most_recent"].isoformat()
                if cluster_row["most_recent"] else None
            ),
            "total_abandoned_all_time":  total_abandoned,
        },
    }
