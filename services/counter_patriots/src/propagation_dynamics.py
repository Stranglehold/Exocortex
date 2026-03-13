"""
propagation_dynamics.py — Narrative propagation dynamics engine.

Computes velocity, acceleration, escape velocity, and time-to-escape-velocity
for tracked topics. Alert level escalates automatically based on trajectory.
Entirely deterministic — no LLM calls.

Definitions:
  velocity:                  unique sources/hour covering topic in current window
  acceleration:              velocity change rate (sources/hour²) vs prior window
  escape_velocity_estimate:  threshold above which correction becomes impractical
  time_to_escape_velocity:   hours until current trajectory reaches escape velocity
  half_life_hours:           proxy: avg detection time for FALSIFIED claims on topic

Alert levels:
  INFORMATIONAL:  baseline monitoring
  WARNING:        velocity > WARNING_VELOCITY_THRESHOLD or cluster coverage > 30%
  URGENT:         time_to_escape_velocity < OPERATOR_RESPONSE_BASELINE_HOURS

narrative_id is a stable 31-bit hash of topic_tag.
Full FK binding to a narratives table: Phase 4.
Operator response baseline and escape velocity thresholds are configurable.

Phase 3 implementation.
"""

import hashlib
import logging
import os
from typing import Optional

import psycopg2
import psycopg2.extras

import audit

log = logging.getLogger(__name__)

DB_URL = os.environ.get(
    "CP_DB_URL",
    "postgresql://cds_app:cds_app_dev_password@localhost:5433/counter_patriots"
)

# Thresholds — configurable
VELOCITY_WINDOW_HOURS        = 24          # window for velocity computation
ESCAPE_VELOCITY              = 5.0         # sources/hour — correction impractical
WARNING_VELOCITY_THRESHOLD   = 2.0         # sources/hour
WARNING_CLUSTER_COVERAGE_PCT = 0.30        # fraction of clusters covered
OPERATOR_RESPONSE_BASELINE   = 24.0        # hours — URGENT when time_to_escape < this


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def compute_dynamics(topic_tag: str, velocity_window_hours: int = VELOCITY_WINDOW_HOURS,
                     session_id=None) -> dict:
    """
    Compute propagation dynamics for a topic and persist to narrative_dynamics.

    Args:
        topic_tag:             Topic to analyze
        velocity_window_hours: Window for velocity measurement (default 24h)
        session_id:            UUID for audit trail

    Returns:
        Full dynamics dict including alert_level and computed metrics.
    """
    import uuid
    sid = session_id or uuid.uuid4()

    current = _window_stats(topic_tag, offset_hours=0,
                            window_hours=velocity_window_hours)
    prior   = _window_stats(topic_tag, offset_hours=velocity_window_hours,
                            window_hours=velocity_window_hours)

    # Velocity: unique sources / window length
    velocity = round(current["source_count"] / velocity_window_hours, 6)
    prior_velocity = round(prior["source_count"] / velocity_window_hours, 6)

    # Acceleration: change in velocity per hour
    acceleration = round((velocity - prior_velocity) / velocity_window_hours, 8)

    # Cluster coverage fraction
    total_clusters = _total_cluster_count()
    cluster_coverage_pct = (
        round(current["cluster_count"] / total_clusters, 4)
        if total_clusters > 0 else 0.0
    )

    # Time to escape velocity
    time_to_escape = _time_to_escape(velocity, acceleration)

    # Half-life proxy: avg detection time for falsified claims
    half_life = _half_life_hours(topic_tag)

    # Alert level
    alert = _alert_level(velocity, cluster_coverage_pct, time_to_escape)

    narrative_id = _narrative_id(topic_tag)

    result = {
        "topic":                       topic_tag,
        "narrative_id":                narrative_id,
        "velocity_window_hours":       velocity_window_hours,
        "current_window": {
            "source_count":   current["source_count"],
            "cluster_count":  current["cluster_count"],
            "claim_count":    current["claim_count"],
        },
        "prior_window": {
            "source_count":  prior["source_count"],
            "cluster_count": prior["cluster_count"],
            "claim_count":   prior["claim_count"],
        },
        "propagation_velocity":        velocity,
        "acceleration":                acceleration,
        "cluster_coverage_pct":        cluster_coverage_pct,
        "escape_velocity_estimate":    ESCAPE_VELOCITY,
        "time_to_escape_velocity_hours": time_to_escape,
        "half_life_hours":             half_life,
        "alert_level":                 alert,
    }

    _persist(result, topic_tag, narrative_id)

    if alert in ("WARNING", "URGENT"):
        log.warning(
            f"[DYNAMICS] {topic_tag}: {alert} — "
            f"velocity={velocity:.3f} sources/h, "
            f"clusters={cluster_coverage_pct:.0%}, "
            f"time_to_escape={time_to_escape}"
        )
    else:
        log.info(
            f"[DYNAMICS] {topic_tag}: {alert} — "
            f"velocity={velocity:.3f} sources/h"
        )

    return result


def get_latest(topic_tag: str) -> Optional[dict]:
    """
    Retrieve the most recent dynamics computation for a topic.

    Returns None if no dynamics have been computed for this topic.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, topic_tag, narrative_id, computed_at,
                       propagation_velocity, acceleration,
                       escape_velocity_estimate, time_to_escape_velocity_hours,
                       half_life_hours, alert_level
                FROM narrative_dynamics
                WHERE topic_tag = %s
                ORDER BY computed_at DESC
                LIMIT 1
                """,
                (topic_tag,),
            )
            row = cur.fetchone()
    if not row:
        return None
    d = dict(row)
    d["computed_at"] = d["computed_at"].isoformat()
    return d


# ---------------------------------------------------------------------------
# Window statistics
# ---------------------------------------------------------------------------

def _window_stats(topic_tag: str, offset_hours: int, window_hours: int) -> dict:
    """
    Unique sources, clusters, and claim count for a time window.

    offset_hours: how far back the window ends (0 = current)
    window_hours: length of window
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(DISTINCT c.source_id)  AS source_count,
                    COUNT(DISTINCT s.cluster)    AS cluster_count,
                    COUNT(c.id)                  AS claim_count
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE %s = ANY(c.topic_tags)
                  AND c.extracted_at >= NOW() - INTERVAL '%s hours'
                  AND c.extracted_at <  NOW() - INTERVAL '%s hours'
                """,
                (topic_tag, offset_hours + window_hours, offset_hours),
            )
            row = cur.fetchone()

    return {
        "source_count":  int(row["source_count"] or 0),
        "cluster_count": int(row["cluster_count"] or 0),
        "claim_count":   int(row["claim_count"] or 0),
    }


def _total_cluster_count() -> int:
    """Distinct cluster values currently in sources table."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(DISTINCT cluster) FROM sources WHERE cluster IS NOT NULL")
            row = cur.fetchone()
    return int(row["count"] or 1)


def _half_life_hours(topic_tag: str) -> Optional[float]:
    """
    Average detection time for FALSIFIED claims on this topic.
    Computed as AVG(falsified_at - extracted_at) in hours.

    Phase 3 proxy for true half-life (post-falsification spread tracking
    requires citation monitoring — Phase 4).
    Returns None if no falsified claims exist for this topic.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT AVG(
                    EXTRACT(EPOCH FROM (h.falsified_at - c.extracted_at)) / 3600
                ) AS avg_hours
                FROM claims c
                JOIN hypothesis_registry h ON h.observation_id = c.id
                WHERE %s = ANY(c.topic_tags)
                  AND h.status = 'FALSIFIED'
                  AND h.falsified_at IS NOT NULL
                  AND c.extracted_at IS NOT NULL
                """,
                (topic_tag,),
            )
            row = cur.fetchone()

    val = row["avg_hours"] if row else None
    return round(float(val), 2) if val is not None else None


# ---------------------------------------------------------------------------
# Computed signals
# ---------------------------------------------------------------------------

def _time_to_escape(velocity: float, acceleration: float) -> Optional[float]:
    """
    Hours until current trajectory reaches escape velocity.

    Returns None  if acceleration <= 0 (stable or decelerating).
    Returns 0.0   if already at or above escape velocity.
    """
    if velocity >= ESCAPE_VELOCITY:
        return 0.0
    if acceleration <= 0:
        return None
    hours = (ESCAPE_VELOCITY - velocity) / acceleration
    return round(hours, 2)


def _alert_level(velocity: float, cluster_coverage_pct: float,
                 time_to_escape: Optional[float]) -> str:
    if time_to_escape is not None and time_to_escape < OPERATOR_RESPONSE_BASELINE:
        return "URGENT"
    if velocity > WARNING_VELOCITY_THRESHOLD or cluster_coverage_pct > WARNING_CLUSTER_COVERAGE_PCT:
        return "WARNING"
    return "INFORMATIONAL"


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _persist(result: dict, topic_tag: str, narrative_id: int) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO narrative_dynamics
                    (narrative_id, topic_tag, propagation_velocity, acceleration,
                     escape_velocity_estimate, time_to_escape_velocity_hours,
                     half_life_hours, alert_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    narrative_id,
                    topic_tag,
                    result["propagation_velocity"],
                    result["acceleration"],
                    result["escape_velocity_estimate"],
                    result["time_to_escape_velocity_hours"],
                    result["half_life_hours"],
                    result["alert_level"],
                ),
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _narrative_id(topic_tag: str) -> int:
    """
    Stable 31-bit integer hash of topic_tag.
    Used as narrative_id until Phase 4 narratives table exists.
    """
    digest = hashlib.sha256(topic_tag.encode()).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF
