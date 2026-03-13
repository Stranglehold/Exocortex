"""
meta_detection.py — Operational health monitoring.

Detects degradation in CDS performance that may indicate the system itself
is under targeted attack. All metrics computed deterministically from
audit_log, claims, and sources tables — no LLM calls.

Metrics:
  false_positive_rate:    RETURNED_TO_STAGED / PROMOTED in rolling window
                          Rising trend = claims being promoted too eagerly
                          or cascade being triggered as manipulation vector

  source_trust_skew:      Fraction of sources below trust threshold (< 0.5)
                          Sudden increase = coordinated source degradation campaign

  resolution_time:        Avg hours from claim extraction → final state
                          Rising = system under load or analyst overload

  volume_anomaly:         Current window claim volume vs rolling baseline (z-score)
                          Spike > 2σ = flooding attack; sustained elevation = campaign

Health signals:
  NOMINAL:     All metrics within normal bounds
  DEGRADED:    1-2 metrics outside bounds
  COMPROMISED: 3+ metrics simultaneously degraded — coordinated attack signature

Phase 3 implementation.
"""

import logging
import os
from typing import Optional

import psycopg2
import psycopg2.extras

log = logging.getLogger(__name__)

DB_URL = os.environ.get(
    "CP_DB_URL",
    "postgresql://cds_app:cds_app_dev_password@localhost:5433/counter_patriots"
)

# Thresholds for metric degradation
FALSE_POSITIVE_RATE_THRESHOLD   = 0.30    # >30% of promoted claims returned = degraded
SOURCE_TRUST_SKEW_THRESHOLD     = 0.25    # >25% of sources below trust floor = degraded
RESOLUTION_TIME_BASELINE_HOURS  = 72.0   # >72h avg resolution = degraded
VOLUME_ANOMALY_ZSCORE_THRESHOLD = 2.0    # >2σ above baseline = degraded

SOURCE_TRUST_FLOOR = 0.50   # sources below this are "low-trust"


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def get_health_report(window_hours: int = 168) -> dict:
    """
    Compute operational health report.

    Args:
        window_hours: Rolling window for trend metrics (default 168 = 7 days)

    Returns:
        {
            health_signal:       "NOMINAL" | "DEGRADED" | "COMPROMISED",
            degraded_metrics:    [metric names outside bounds],
            window_hours:        int,
            metrics: {
                false_positive_rate: { rate, promoted, returned, status },
                source_trust_skew:   { skew_pct, low_trust_count, total, status },
                resolution_time:     { avg_hours, sample_count, status },
                volume_anomaly:      { current_count, baseline_avg, z_score, status },
            }
        }
    """
    with get_conn() as conn:
        fp   = _false_positive_rate(conn, window_hours)
        skew = _source_trust_skew(conn)
        res  = _resolution_time(conn, window_hours)
        vol  = _volume_anomaly(conn, window_hours)

    metrics = {
        "false_positive_rate": fp,
        "source_trust_skew":   skew,
        "resolution_time":     res,
        "volume_anomaly":      vol,
    }

    degraded = [name for name, m in metrics.items() if m.get("status") == "DEGRADED"]

    if len(degraded) >= 3:
        health_signal = "COMPROMISED"
    elif len(degraded) >= 1:
        health_signal = "DEGRADED"
    else:
        health_signal = "NOMINAL"

    if health_signal != "NOMINAL":
        log.warning(
            f"[META] System health: {health_signal} — "
            f"degraded metrics: {degraded}"
        )
    else:
        log.info("[META] System health: NOMINAL")

    return {
        "health_signal":    health_signal,
        "degraded_metrics": degraded,
        "window_hours":     window_hours,
        "metrics":          metrics,
    }


# ---------------------------------------------------------------------------
# Metric computations
# ---------------------------------------------------------------------------

def _false_positive_rate(conn, window_hours: int) -> dict:
    """
    Ratio of claims that were promoted then returned vs total promoted.

    Uses audit_log events: claim_promoted (promotions) and
    cascade_complete / retcon_return (returns). Conservative — only
    counts automated returns, not manual analyst reversals.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE event_type = 'claim_promoted') AS promoted,
                COUNT(*) FILTER (WHERE event_type IN ('cascade_complete', 'retcon_return',
                                                       'claim_returned_to_staged'))
                                                         AS returned
            FROM audit_log
            WHERE timestamp >= NOW() - INTERVAL '%s hours'
            """,
            (window_hours,),
        )
        row = cur.fetchone()

    promoted = int(row["promoted"] or 0)
    returned = int(row["returned"] or 0)
    rate     = round(returned / promoted, 4) if promoted > 0 else 0.0

    return {
        "rate":     rate,
        "promoted": promoted,
        "returned": returned,
        "status":   "DEGRADED" if rate > FALSE_POSITIVE_RATE_THRESHOLD else "OK",
    }


def _source_trust_skew(conn) -> dict:
    """
    Fraction of tracked sources currently below trust floor (0.50).
    Sudden increase = coordinated source degradation campaign.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*)                                         AS total,
                COUNT(*) FILTER (WHERE confidence_score < %s)   AS low_trust
            FROM sources
            """,
            (SOURCE_TRUST_FLOOR,),
        )
        row = cur.fetchone()

    total     = int(row["total"] or 0)
    low_trust = int(row["low_trust"] or 0)
    skew_pct  = round(low_trust / total, 4) if total > 0 else 0.0

    return {
        "skew_pct":       skew_pct,
        "low_trust_count": low_trust,
        "total":          total,
        "trust_floor":    SOURCE_TRUST_FLOOR,
        "status":         "DEGRADED" if skew_pct > SOURCE_TRUST_SKEW_THRESHOLD else "OK",
    }


def _resolution_time(conn, window_hours: int) -> dict:
    """
    Average hours from claim extraction to final state (PROMOTED or FALSIFIED).

    Rising trend = analyst overload or deliberate slowing (adversary flooding).
    Uses hypothesis_registry for FALSIFIED timestamps as proxy for resolution.
    Claims that haven't reached a final state are excluded.
    """
    with conn.cursor() as cur:
        # FALSIFIED claims: extracted_at → falsified_at
        cur.execute(
            """
            SELECT AVG(
                EXTRACT(EPOCH FROM (h.falsified_at - c.extracted_at)) / 3600
            ) AS avg_hours,
            COUNT(*) AS sample_count
            FROM claims c
            JOIN hypothesis_registry h ON h.observation_id = c.id
            WHERE h.status = 'FALSIFIED'
              AND h.falsified_at IS NOT NULL
              AND c.extracted_at IS NOT NULL
              AND h.falsified_at >= NOW() - INTERVAL '%s hours'
            """,
            (window_hours,),
        )
        row = cur.fetchone()

    avg_hours    = float(row["avg_hours"]) if row["avg_hours"] else None
    sample_count = int(row["sample_count"] or 0)

    return {
        "avg_hours":    round(avg_hours, 2) if avg_hours is not None else None,
        "sample_count": sample_count,
        "baseline_hours": RESOLUTION_TIME_BASELINE_HOURS,
        "status": (
            "DEGRADED"
            if avg_hours is not None and avg_hours > RESOLUTION_TIME_BASELINE_HOURS
            else "OK"
        ),
    }


def _volume_anomaly(conn, window_hours: int) -> dict:
    """
    Current window claim volume vs rolling baseline.

    z-score = (current - baseline_avg) / baseline_std
    > 2σ above baseline = volume anomaly (flooding or organic surge).

    Baseline: average claims per equivalent window over the prior 4 windows.
    """
    with conn.cursor() as cur:
        # Current window
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM claims WHERE extracted_at >= NOW() - INTERVAL '%s hours'",
            (window_hours,),
        )
        current_count = int(cur.fetchone()["cnt"] or 0)

        # Baseline: count per window for prior 4 windows, compute avg + std
        cur.execute(
            """
            WITH buckets AS (
                SELECT
                    floor(
                        EXTRACT(EPOCH FROM (NOW() - extracted_at)) / (%s * 3600)
                    )::int AS bucket,
                    COUNT(*) AS cnt
                FROM claims
                WHERE extracted_at >= NOW() - INTERVAL '%s hours'
                  AND extracted_at <  NOW() - INTERVAL '%s hours'
                GROUP BY bucket
            )
            SELECT
                AVG(cnt)    AS avg_cnt,
                STDDEV(cnt) AS std_cnt
            FROM buckets
            """,
            (window_hours, window_hours * 5, window_hours),
        )
        row = cur.fetchone()

    baseline_avg = float(row["avg_cnt"]) if row["avg_cnt"] else 0.0
    baseline_std = float(row["std_cnt"]) if row["std_cnt"] else 1.0

    # Avoid division by zero
    if baseline_std < 0.01:
        baseline_std = max(1.0, baseline_avg * 0.10)

    z_score = round((current_count - baseline_avg) / baseline_std, 4)

    return {
        "current_count":  current_count,
        "baseline_avg":   round(baseline_avg, 2),
        "baseline_std":   round(baseline_std, 2),
        "z_score":        z_score,
        "status":         "DEGRADED" if z_score > VOLUME_ANOMALY_ZSCORE_THRESHOLD else "OK",
    }
