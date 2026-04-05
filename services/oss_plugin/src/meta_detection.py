"""
meta_detection.py — CDS operational health monitoring.

Port of V1 meta_detection.py from PostgreSQL to SQLite.
Detects degradation in CDS performance that may indicate the system itself
is under targeted attack. All metrics computed deterministically from
audit_log, claims, and sources tables — no LLM calls.

Metrics:
  false_positive_rate:  RETURNED_TO_STAGED / (PROMOTED + RETURNED_TO_STAGED) over last 7 days
  source_trust_skew:    std dev of confidence_scores across sources (high = uneven trust)
  resolution_time_hours: avg time from STAGED to PROMOTED for promoted claims in last 7 days
  volume_anomaly:       today's claim count vs 7-day average (flag if >2x or <0.3x)

Overall status:
  NOMINAL:    All metrics within normal bounds
  DEGRADED:   1–2 metrics outside bounds
  COMPROMISED: 3+ metrics simultaneously degraded — coordinated attack signature
"""
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Optional

log = logging.getLogger("[META]")

# Thresholds
FALSE_POSITIVE_RATE_THRESHOLD   = 0.30   # >30% of promoted claims returned = degraded
SOURCE_TRUST_SKEW_STD_THRESHOLD = 0.20   # std dev of confidence_score > 0.20 = degraded
RESOLUTION_TIME_BASELINE_HOURS  = 72.0   # >72h avg resolution = degraded
VOLUME_ANOMALY_HIGH_RATIO       = 2.0    # today > 2x average = degraded
VOLUME_ANOMALY_LOW_RATIO        = 0.3    # today < 0.3x average = degraded (sudden drop)


def run_health_check(conn) -> dict:
    """
    Compute operational health report.

    Returns:
        {
          overall_status,
          false_positive_rate,
          source_trust_skew,
          resolution_time_hours,
          volume_anomaly,
          degraded_metrics: [...]
        }
    """
    try:
        fp   = _false_positive_rate(conn)
        skew = _source_trust_skew(conn)
        res  = _resolution_time(conn)
        vol  = _volume_anomaly(conn)

        metrics = {
            "false_positive_rate":   fp,
            "source_trust_skew":     skew,
            "resolution_time_hours": res,
            "volume_anomaly":        vol,
        }

        degraded = [name for name, m in metrics.items() if m.get("status") == "DEGRADED"]

        if len(degraded) >= 3:
            overall_status = "COMPROMISED"
        elif len(degraded) >= 1:
            overall_status = "DEGRADED"
        else:
            overall_status = "NOMINAL"

        if overall_status != "NOMINAL":
            log.warning(f"System health: {overall_status} — degraded: {degraded}")
        else:
            log.info("System health: NOMINAL")

        return {
            "overall_status":        overall_status,
            "degraded_metrics":      degraded,
            "false_positive_rate":   fp,
            "source_trust_skew":     skew,
            "resolution_time_hours": res,
            "volume_anomaly":        vol,
        }
    except Exception as e:
        log.warning(f"run_health_check failed: {e}")
        return {"overall_status": "NOMINAL", "error": str(e), "degraded_metrics": []}


# ---------------------------------------------------------------------------
# Metric computations
# ---------------------------------------------------------------------------

def _false_positive_rate(conn) -> dict:
    """
    RETURNED_TO_STAGED / (PROMOTED + RETURNED_TO_STAGED) over last 7 days.
    Counts trust_level values in the claims table directly — no audit_log dependency.
    """
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        cur = conn.cursor()
        cur.execute("""
            SELECT trust_level, COUNT(*) AS cnt
            FROM claims
            WHERE extracted_at >= ?
              AND trust_level IN ('PROMOTED','RETURNED_TO_STAGED')
            GROUP BY trust_level
        """, (since,))
        counts = {r["trust_level"]: r["cnt"] for r in cur.fetchall()}
        promoted = int(counts.get("PROMOTED", 0))
        returned = int(counts.get("RETURNED_TO_STAGED", 0))
        total = promoted + returned
        rate = round(returned / total, 4) if total > 0 else 0.0
        return {
            "rate":     rate,
            "promoted": promoted,
            "returned": returned,
            "status":   "DEGRADED" if rate > FALSE_POSITIVE_RATE_THRESHOLD else "OK",
        }
    except Exception as e:
        log.warning(f"_false_positive_rate failed: {e}")
        return {"rate": 0.0, "promoted": 0, "returned": 0, "status": "OK"}


def _source_trust_skew(conn) -> dict:
    """
    Standard deviation of confidence_score across all sources.
    High std dev = uneven trust distribution = coordinated source degradation signal.
    """
    try:
        cur = conn.cursor()
        cur.execute("SELECT confidence_score FROM sources WHERE confidence_score IS NOT NULL")
        scores = [float(r["confidence_score"]) for r in cur.fetchall()]
        if len(scores) < 2:
            return {"std_dev": 0.0, "source_count": len(scores), "status": "OK"}
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = round(math.sqrt(variance), 4)
        return {
            "std_dev":      std_dev,
            "mean_trust":   round(mean, 4),
            "source_count": len(scores),
            "status":       "DEGRADED" if std_dev > SOURCE_TRUST_SKEW_STD_THRESHOLD else "OK",
        }
    except Exception as e:
        log.warning(f"_source_trust_skew failed: {e}")
        return {"std_dev": 0.0, "source_count": 0, "status": "OK"}


def _resolution_time(conn) -> dict:
    """
    Average time from claim extraction to promotion, for claims promoted in the last 7 days.
    Uses promotion_snapshots.promoted_at vs claims.extracted_at.
    """
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.extracted_at, ps.promoted_at
            FROM promotion_snapshots ps
            JOIN claims c ON c.id = ps.claim_id
            WHERE ps.promoted_at >= ?
              AND c.extracted_at IS NOT NULL
        """, (since,))
        rows = cur.fetchall()
        if not rows:
            return {"avg_hours": None, "sample_count": 0, "status": "OK"}
        durations = []
        for row in rows:
            try:
                ea = datetime.fromisoformat(row["extracted_at"].replace("Z", "+00:00"))
                pa = datetime.fromisoformat(row["promoted_at"].replace("Z", "+00:00"))
                diff = (pa - ea).total_seconds() / 3600.0
                if diff >= 0:
                    durations.append(diff)
            except Exception:
                continue
        if not durations:
            return {"avg_hours": None, "sample_count": 0, "status": "OK"}
        avg_hours = round(sum(durations) / len(durations), 2)
        return {
            "avg_hours":      avg_hours,
            "sample_count":   len(durations),
            "baseline_hours": RESOLUTION_TIME_BASELINE_HOURS,
            "status": "DEGRADED" if avg_hours > RESOLUTION_TIME_BASELINE_HOURS else "OK",
        }
    except Exception as e:
        log.warning(f"_resolution_time failed: {e}")
        return {"avg_hours": None, "sample_count": 0, "status": "OK"}


def _volume_anomaly(conn) -> dict:
    """
    Today's claim count vs 7-day average.
    Flag DEGRADED if today > 2x average (flood) or < 0.3x average (sudden drop).
    """
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        week_start  = (now - timedelta(days=7)).isoformat()

        cur = conn.cursor()
        # Today's count
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM claims WHERE extracted_at >= ?",
            (today_start,),
        )
        today_count = int(cur.fetchone()["cnt"] or 0)

        # Per-day counts over the last 7 days (excluding today)
        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM claims
            WHERE extracted_at >= ? AND extracted_at < ?
        """, (week_start, today_start))
        week_total = int(cur.fetchone()["cnt"] or 0)
        week_avg = round(week_total / 7.0, 2)

        status = "OK"
        if week_avg > 0:
            ratio = today_count / week_avg
            if ratio > VOLUME_ANOMALY_HIGH_RATIO or ratio < VOLUME_ANOMALY_LOW_RATIO:
                status = "DEGRADED"

        return {
            "today_count": today_count,
            "week_avg":    week_avg,
            "ratio":       round(today_count / week_avg, 4) if week_avg > 0 else None,
            "status":      status,
        }
    except Exception as e:
        log.warning(f"_volume_anomaly failed: {e}")
        return {"today_count": 0, "week_avg": 0.0, "ratio": None, "status": "OK"}
