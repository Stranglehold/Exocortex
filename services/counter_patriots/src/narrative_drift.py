"""
narrative_drift.py — Narrative framing shift detection.

Compares two equal-length time windows for a topic to detect when
the framing of coverage is systematically changing. Entirely deterministic —
no LLM calls. Uses claims already in the database.

Drift signals produced:
  - technique_shift:    technique_class distribution changed significantly
  - cluster_shift:      which ideological clusters are covering the topic changed
  - salience_shift:     average emotional_salience_score trending up or down
  - volume_shift:       claim volume changed significantly between windows
  - confidence_shift:   average source confidence changed (source quality drift)

A drift_score is computed as a weighted sum of signal magnitudes (0.0–1.0).
Threshold for flagging: >= 0.30.

Phase 2 implementation. Propagation dynamics (velocity, escape velocity)
are Phase 3 — see narrative_dynamics table and CDS v2 spec.
"""

import os
import logging
from collections import Counter
from typing import Optional

import psycopg2
import psycopg2.extras

log = logging.getLogger(__name__)

DB_URL = os.environ.get(
    "CP_DB_URL",
    "postgresql://cds_app:cds_app_dev_password@localhost:5433/counter_patriots"
)

DRIFT_FLAG_THRESHOLD = 0.30

# Signal weights for drift_score
WEIGHTS = {
    "technique_shift":  0.35,
    "cluster_shift":    0.30,
    "salience_shift":   0.15,
    "volume_shift":     0.10,
    "confidence_shift": 0.10,
}


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def detect_drift(topic_tag: str, window_hours: int = 168) -> dict:
    """
    Compare current window vs prior window for a topic.

    Each window is `window_hours` long. Current = most recent, prior = preceding.
    Returns drift signals, per-signal magnitude, and an overall drift_score.

    Args:
        topic_tag:     Topic to analyze (must exist in topics table)
        window_hours:  Length of each comparison window in hours (default 168 = 7 days)

    Returns:
        {
            topic:           str,
            window_hours:    int,
            current_window:  { start, end, claim_count, ... },
            prior_window:    { start, end, claim_count, ... },
            drift_score:     float (0.0–1.0),
            drifted:         bool,
            signals:         { signal_name: { magnitude, detail } },
        }
    """
    current_stats = _get_window_stats(topic_tag, offset_hours=0, window_hours=window_hours)
    prior_stats   = _get_window_stats(topic_tag, offset_hours=window_hours, window_hours=window_hours)

    signals = {}

    # 1. Technique class distribution shift
    technique_mag = _distribution_shift(
        current_stats["technique_dist"],
        prior_stats["technique_dist"],
    )
    signals["technique_shift"] = {
        "magnitude": technique_mag,
        "current":   current_stats["technique_dist"],
        "prior":     prior_stats["technique_dist"],
    }

    # 2. Cluster coverage shift
    cluster_mag = _set_shift(
        set(current_stats["active_clusters"]),
        set(prior_stats["active_clusters"]),
    )
    signals["cluster_shift"] = {
        "magnitude":       cluster_mag,
        "current_clusters": sorted(current_stats["active_clusters"]),
        "prior_clusters":   sorted(prior_stats["active_clusters"]),
        "entered":          sorted(
            set(current_stats["active_clusters"]) - set(prior_stats["active_clusters"])
        ),
        "exited":           sorted(
            set(prior_stats["active_clusters"]) - set(current_stats["active_clusters"])
        ),
    }

    # 3. Emotional salience shift
    salience_mag = _float_shift(
        current_stats["avg_salience"],
        prior_stats["avg_salience"],
        scale=1.0,
    )
    signals["salience_shift"] = {
        "magnitude":       salience_mag,
        "current_avg":     current_stats["avg_salience"],
        "prior_avg":       prior_stats["avg_salience"],
        "direction":       "up" if current_stats["avg_salience"] > prior_stats["avg_salience"]
                           else "down" if current_stats["avg_salience"] < prior_stats["avg_salience"]
                           else "stable",
    }

    # 4. Claim volume shift
    volume_mag = _volume_shift(
        current_stats["claim_count"],
        prior_stats["claim_count"],
    )
    signals["volume_shift"] = {
        "magnitude":     volume_mag,
        "current_count": current_stats["claim_count"],
        "prior_count":   prior_stats["claim_count"],
        "ratio":         _safe_ratio(current_stats["claim_count"], prior_stats["claim_count"]),
    }

    # 5. Source confidence shift
    confidence_mag = _float_shift(
        current_stats["avg_source_confidence"],
        prior_stats["avg_source_confidence"],
        scale=1.0,
    )
    signals["confidence_shift"] = {
        "magnitude":   confidence_mag,
        "current_avg": current_stats["avg_source_confidence"],
        "prior_avg":   prior_stats["avg_source_confidence"],
        "direction":   "up" if current_stats["avg_source_confidence"] > prior_stats["avg_source_confidence"]
                       else "down" if current_stats["avg_source_confidence"] < prior_stats["avg_source_confidence"]
                       else "stable",
    }

    # Weighted drift score
    drift_score = sum(
        WEIGHTS[name] * sig["magnitude"]
        for name, sig in signals.items()
        if name in WEIGHTS
    )
    drift_score = round(min(1.0, drift_score), 4)

    result = {
        "topic":          topic_tag,
        "window_hours":   window_hours,
        "current_window": {
            "start":       current_stats["window_start"].isoformat() if current_stats["window_start"] else None,
            "end":         current_stats["window_end"].isoformat() if current_stats["window_end"] else None,
            "claim_count": current_stats["claim_count"],
        },
        "prior_window": {
            "start":       prior_stats["window_start"].isoformat() if prior_stats["window_start"] else None,
            "end":         prior_stats["window_end"].isoformat() if prior_stats["window_end"] else None,
            "claim_count": prior_stats["claim_count"],
        },
        "drift_score": drift_score,
        "drifted":     drift_score >= DRIFT_FLAG_THRESHOLD,
        "signals":     signals,
    }

    if result["drifted"]:
        # Surface the dominant signal
        dominant = max(signals.items(), key=lambda x: x[1]["magnitude"])
        result["dominant_signal"] = dominant[0]
        log.info(
            f"[DRIFT] {topic_tag}: drift_score={drift_score:.3f} "
            f"dominant={dominant[0]} (mag={dominant[1]['magnitude']:.3f})"
        )
    else:
        log.info(f"[DRIFT] {topic_tag}: drift_score={drift_score:.3f} — stable")

    return result


# ---------------------------------------------------------------------------
# Window statistics
# ---------------------------------------------------------------------------

def _get_window_stats(topic_tag: str, offset_hours: int, window_hours: int) -> dict:
    """
    Compute statistics for a single time window.

    offset_hours: how many hours back the window starts (0 = current window)
    window_hours: length of the window
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.id, c.technique_class,
                    c.emotional_salience_score,
                    c.extracted_at,
                    s.cluster,
                    s.confidence_score
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE %s = ANY(c.topic_tags)
                  AND c.extracted_at >= NOW() - INTERVAL '%s hours'
                  AND c.extracted_at <  NOW() - INTERVAL '%s hours'
                """,
                (topic_tag, offset_hours + window_hours, offset_hours),
            )
            rows = cur.fetchall()

            # Window boundaries
            cur.execute(
                """
                SELECT
                    (NOW() - INTERVAL '%s hours') AS window_start,
                    (NOW() - INTERVAL '%s hours') AS window_end
                """,
                (offset_hours + window_hours, offset_hours),
            )
            bounds = cur.fetchone()

    if not rows:
        return {
            "window_start":          bounds["window_start"] if bounds else None,
            "window_end":            bounds["window_end"] if bounds else None,
            "claim_count":           0,
            "technique_dist":        {},
            "active_clusters":       [],
            "avg_salience":          0.0,
            "avg_source_confidence": 0.0,
        }

    technique_counts = Counter(
        r["technique_class"] or "none" for r in rows
    )
    total = len(rows)
    technique_dist = {
        k: round(v / total, 4) for k, v in technique_counts.items()
    }

    active_clusters = list({r["cluster"] for r in rows if r["cluster"]})

    avg_salience = (
        sum(float(r["emotional_salience_score"] or 0.0) for r in rows) / total
    )
    avg_confidence = (
        sum(float(r["confidence_score"] or 0.7) for r in rows) / total
    )

    return {
        "window_start":          bounds["window_start"],
        "window_end":            bounds["window_end"],
        "claim_count":           total,
        "technique_dist":        technique_dist,
        "active_clusters":       active_clusters,
        "avg_salience":          round(avg_salience, 4),
        "avg_source_confidence": round(avg_confidence, 4),
    }


# ---------------------------------------------------------------------------
# Signal magnitude calculations
# ---------------------------------------------------------------------------

def _distribution_shift(dist_a: dict, dist_b: dict) -> float:
    """
    Total variation distance between two probability distributions.
    Returns 0.0–1.0. 0.0 = identical, 1.0 = completely different.
    TVD = 0.5 * sum(|p_i - q_i|) over all keys in union.
    """
    keys = set(dist_a) | set(dist_b)
    if not keys:
        return 0.0
    tvd = 0.5 * sum(abs(dist_a.get(k, 0.0) - dist_b.get(k, 0.0)) for k in keys)
    return round(min(1.0, tvd), 4)


def _set_shift(set_a: set, set_b: set) -> float:
    """
    Jaccard distance between two sets: 1 - |A∩B| / |A∪B|.
    Returns 0.0 (identical) to 1.0 (completely disjoint).
    """
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    intersection = set_a & set_b
    jaccard = len(intersection) / len(union) if union else 1.0
    return round(1.0 - jaccard, 4)


def _float_shift(current: float, prior: float, scale: float = 1.0) -> float:
    """
    Normalized absolute difference between two float values.
    scale is the expected max range (e.g., 1.0 for 0–1 values).
    Returns 0.0–1.0.
    """
    if scale == 0.0:
        return 0.0
    return round(min(1.0, abs(current - prior) / scale), 4)


def _volume_shift(current: int, prior: int) -> float:
    """
    Normalized volume change. Uses ratio relative to prior.
    No prior data → 0.0 (can't measure shift without baseline).
    """
    if prior == 0 and current == 0:
        return 0.0
    if prior == 0:
        return 1.0
    ratio = current / prior
    # Map ratio to 0–1: 0.5x → 0.5 shift, 2x → 0.5 shift, 3x+ → 1.0
    if ratio >= 1.0:
        return round(min(1.0, (ratio - 1.0) / 2.0), 4)
    else:
        return round(min(1.0, (1.0 - ratio)), 4)


def _safe_ratio(a: int, b: int) -> Optional[float]:
    """Return a/b as float, or None if b is zero."""
    if b == 0:
        return None
    return round(a / b, 3)
