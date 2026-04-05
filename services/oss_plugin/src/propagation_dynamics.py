"""
propagation_dynamics.py — Narrative propagation dynamics engine.

Port of V1 propagation_dynamics.py from PostgreSQL to SQLite.
Computes velocity, acceleration, escape velocity, and time-to-escape-velocity
for tracked topics. Alert level escalates automatically based on trajectory.
Entirely deterministic — no LLM calls.

Definitions:
  velocity:                  claims/hour in current window (unique source count proxy)
  acceleration:              velocity change rate vs prior window
  escape_velocity_estimate:  threshold above which correction becomes impractical
  time_to_escape_velocity:   hours until current trajectory reaches escape velocity
  half_life_hours:           avg detection time for FALSIFIED claims on topic

Alert levels:
  INFORMATIONAL:  baseline monitoring
  WARNING:        velocity > WARNING_VELOCITY_THRESHOLD
  URGENT:         time_to_escape_velocity < OPERATOR_RESPONSE_BASELINE_HOURS

narrative_id is a stable 31-bit hash of topic_tag.
"""
import hashlib
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Optional

from .db import jloads, jdumps

log = logging.getLogger("[DYNAMICS]")

# Thresholds — configurable via module-level constants
VELOCITY_WINDOW_HOURS        = 24
ESCAPE_VELOCITY              = 5.0    # sources/hour
WARNING_VELOCITY_THRESHOLD   = 2.0    # sources/hour
WARNING_CLUSTER_COVERAGE_PCT = 0.30   # fraction of known clusters
OPERATOR_RESPONSE_BASELINE   = 24.0   # hours — URGENT when time_to_escape < this


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def compute_dynamics(conn, topic_tag: str, window_hours: int = VELOCITY_WINDOW_HOURS) -> dict:
    """
    Compute propagation dynamics for a topic and persist to narrative_dynamics.

    Returns a dict with:
      topic, narrative_id, propagation_velocity, acceleration,
      escape_velocity_estimate, time_to_escape_velocity_hours,
      half_life_hours, alert_level, current_window, prior_window
    """
    try:
        now = datetime.now(timezone.utc)
        current_start = (now - timedelta(hours=window_hours)).isoformat()
        prior_start   = (now - timedelta(hours=window_hours * 2)).isoformat()

        current = _window_stats(conn, topic_tag, current_start, now.isoformat())
        prior   = _window_stats(conn, topic_tag, prior_start, current_start)

        velocity       = round(current["claim_count"] / window_hours, 6)
        prior_velocity = round(prior["claim_count"] / window_hours, 6)
        acceleration   = round((velocity - prior_velocity) / window_hours, 8)

        total_clusters = _total_cluster_count(conn)
        cluster_coverage_pct = (
            round(current["cluster_count"] / total_clusters, 4)
            if total_clusters > 0 else 0.0
        )

        time_to_escape = _time_to_escape(velocity, acceleration)
        half_life      = _half_life_hours(conn, topic_tag)
        alert          = _alert_level(velocity, cluster_coverage_pct, time_to_escape)
        narrative_id   = _narrative_id(topic_tag)

        result = {
            "topic":                          topic_tag,
            "narrative_id":                   narrative_id,
            "velocity_window_hours":          window_hours,
            "current_window":                 current,
            "prior_window":                   prior,
            "propagation_velocity":           velocity,
            "acceleration":                   acceleration,
            "cluster_coverage_pct":           cluster_coverage_pct,
            "escape_velocity_estimate":       ESCAPE_VELOCITY,
            "time_to_escape_velocity_hours":  time_to_escape,
            "half_life_hours":                half_life,
            "alert_level":                    alert,
        }

        _persist(conn, result, topic_tag, narrative_id)

        if alert in ("WARNING", "URGENT"):
            log.warning(
                f"{topic_tag}: {alert} — velocity={velocity:.3f}/h, "
                f"clusters={cluster_coverage_pct:.0%}, "
                f"time_to_escape={time_to_escape}"
            )
        else:
            log.info(f"{topic_tag}: {alert} — velocity={velocity:.3f}/h")

        return result

    except Exception as e:
        log.warning(f"compute_dynamics failed for topic={topic_tag}: {e}")
        return {
            "topic": topic_tag, "alert_level": "INFORMATIONAL",
            "error": str(e),
        }


def get_dynamics(conn, topic_tag: str, limit: int = 10) -> list:
    """
    Return the most recent dynamics records for a topic, newest first.
    """
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM narrative_dynamics
            WHERE topic_tag=?
            ORDER BY computed_at DESC LIMIT ?
        """, (topic_tag, limit))
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_dynamics failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Window statistics
# ---------------------------------------------------------------------------

def _window_stats(conn, topic_tag: str, since: str, until: str) -> dict:
    """
    Return claim count, unique source count, and cluster count for a time window.
    Uses JSON array search for topic_tags column.
    """
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(c.id)              AS claim_count,
                COUNT(DISTINCT c.source_id) AS source_count,
                COUNT(DISTINCT s.cluster)   AS cluster_count
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            WHERE EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value=?)
              AND c.extracted_at >= ?
              AND c.extracted_at <  ?
              AND c.trust_level IN ('STAGED','PROMOTED')
        """, (topic_tag, since, until))
        row = cur.fetchone()
        if not row:
            return {"claim_count": 0, "source_count": 0, "cluster_count": 0}
        return {
            "claim_count":   int(row["claim_count"] or 0),
            "source_count":  int(row["source_count"] or 0),
            "cluster_count": int(row["cluster_count"] or 0),
        }
    except Exception as e:
        log.warning(f"_window_stats failed: {e}")
        return {"claim_count": 0, "source_count": 0, "cluster_count": 0}


def _total_cluster_count(conn) -> int:
    """Distinct cluster values currently in sources table."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT cluster) AS cnt FROM sources WHERE cluster IS NOT NULL")
        row = cur.fetchone()
        return int(row["cnt"] or 1)
    except Exception:
        return 1


def _half_life_hours(conn, topic_tag: str) -> Optional[float]:
    """
    Average detection time for FALSIFIED claims on this topic.
    Proxy: avg(falsified_at - extracted_at) in hours via hypothesis_registry.
    Returns None if no falsified claims exist.
    """
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT h.falsified_at, c.extracted_at
            FROM claims c
            JOIN hypothesis_registry h ON h.observation_id = c.id
            WHERE EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value=?)
              AND h.status = 'FALSIFIED'
              AND h.falsified_at IS NOT NULL
              AND c.extracted_at IS NOT NULL
        """, (topic_tag,))
        rows = cur.fetchall()
        if not rows:
            return None
        total_hours = 0.0
        count = 0
        for row in rows:
            try:
                fa = datetime.fromisoformat(row["falsified_at"].replace("Z", "+00:00"))
                ea = datetime.fromisoformat(row["extracted_at"].replace("Z", "+00:00"))
                diff = (fa - ea).total_seconds() / 3600.0
                if diff >= 0:
                    total_hours += diff
                    count += 1
            except Exception:
                continue
        return round(total_hours / count, 2) if count > 0 else None
    except Exception as e:
        log.warning(f"_half_life_hours failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Signal computation
# ---------------------------------------------------------------------------

def _time_to_escape(velocity: float, acceleration: float) -> Optional[float]:
    """
    Hours until current trajectory reaches escape velocity.
    Returns 0.0 if already at or above. Returns None if decelerating.
    """
    if velocity >= ESCAPE_VELOCITY:
        return 0.0
    if acceleration <= 0:
        return None
    return round((ESCAPE_VELOCITY - velocity) / acceleration, 2)


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

def _persist(conn, result: dict, topic_tag: str, narrative_id: int) -> None:
    try:
        conn.execute("""
            INSERT INTO narrative_dynamics
                (narrative_id, topic_tag, propagation_velocity, acceleration,
                 escape_velocity_estimate, time_to_escape_velocity_hours,
                 half_life_hours, alert_level)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            narrative_id,
            topic_tag,
            result.get("propagation_velocity"),
            result.get("acceleration"),
            result.get("escape_velocity_estimate"),
            result.get("time_to_escape_velocity_hours"),
            result.get("half_life_hours"),
            result.get("alert_level", "INFORMATIONAL"),
        ))
        conn.commit()
    except Exception as e:
        log.warning(f"_persist dynamics failed: {e}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _narrative_id(topic_tag: str) -> int:
    """Stable 31-bit integer hash of topic_tag."""
    digest = hashlib.sha256(topic_tag.encode()).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF
