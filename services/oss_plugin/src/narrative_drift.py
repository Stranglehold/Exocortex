"""
narrative_drift.py — Framing shift detection.

Compares claims from the current window against the prior window on the
same topic. Detects shifts in technique distribution, cluster spread,
emotional salience, claim volume, and promotion confidence.
"""
import logging
from datetime import datetime, timezone, timedelta

from .db import jloads

log = logging.getLogger("[NARRATIVE_DRIFT]")

_NO_SHIFT = {"detected": False, "delta": 0.0, "description": "insufficient data"}


# ---------------------------------------------------------------------------
# Core drift detector
# ---------------------------------------------------------------------------

def detect_drift(conn, topic_tag: str, window_hours: int = 24) -> dict:
    """
    Compare claims from the last `window_hours` vs the previous `window_hours`
    on topic_tag. Returns a dict with five shift assessments:
      technique_shift, cluster_shift, salience_shift, volume_shift, confidence_shift
    Each is {detected: bool, delta: float, description: str}.
    """
    try:
        cur = conn.cursor()
        now = datetime.now(timezone.utc)
        current_start = (now - timedelta(hours=window_hours)).isoformat()
        prev_start    = (now - timedelta(hours=window_hours * 2)).isoformat()

        # Fetch current window
        cur.execute("""
            SELECT c.technique_class, s.cluster, c.emotional_salience_score,
                   c.staging_confidence, c.trust_level, c.extracted_at
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            WHERE EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value=?)
              AND c.extracted_at >= ?
              AND c.trust_level IN ('STAGED','PROMOTED')
        """, (topic_tag, current_start))
        current_rows = [dict(r) for r in cur.fetchall()]

        # Fetch previous window
        cur.execute("""
            SELECT c.technique_class, s.cluster, c.emotional_salience_score,
                   c.staging_confidence, c.trust_level, c.extracted_at
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            WHERE EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value=?)
              AND c.extracted_at >= ?
              AND c.extracted_at < ?
              AND c.trust_level IN ('STAGED','PROMOTED')
        """, (topic_tag, prev_start, current_start))
        prev_rows = [dict(r) for r in cur.fetchall()]

        if not prev_rows:
            return {
                "technique_shift":  _NO_SHIFT.copy(),
                "cluster_shift":    _NO_SHIFT.copy(),
                "salience_shift":   _NO_SHIFT.copy(),
                "volume_shift":     _NO_SHIFT.copy(),
                "confidence_shift": _NO_SHIFT.copy(),
            }

        return {
            "technique_shift":  _technique_shift(current_rows, prev_rows),
            "cluster_shift":    _cluster_shift(current_rows, prev_rows),
            "salience_shift":   _salience_shift(current_rows, prev_rows),
            "volume_shift":     _volume_shift(current_rows, prev_rows),
            "confidence_shift": _confidence_shift(current_rows, prev_rows),
        }
    except Exception as e:
        log.warning(f"detect_drift failed for topic={topic_tag}: {e}")
        return {
            "technique_shift":  _NO_SHIFT.copy(),
            "cluster_shift":    _NO_SHIFT.copy(),
            "salience_shift":   _NO_SHIFT.copy(),
            "volume_shift":     _NO_SHIFT.copy(),
            "confidence_shift": _NO_SHIFT.copy(),
        }


# ---------------------------------------------------------------------------
# get_topic_drift — wrapper that stores / returns last drift
# ---------------------------------------------------------------------------

def get_topic_drift(conn, topic_tag: str, since: str = None) -> dict:
    """
    Run detect_drift and return result. Optionally accept `since` to use as
    a relative start boundary (not currently used — detect_drift uses now-based
    windows). Exposed for API consistency with V1.
    """
    return detect_drift(conn, topic_tag)


# ---------------------------------------------------------------------------
# Shift sub-detectors
# ---------------------------------------------------------------------------

def _technique_shift(current: list, prev: list) -> dict:
    """Detect change in dominant technique class."""
    def dominant(rows):
        counts: dict = {}
        for r in rows:
            t = r.get("technique_class") or "none"
            counts[t] = counts.get(t, 0) + 1
        return max(counts, key=counts.get) if counts else "none"

    dom_curr = dominant(current)
    dom_prev = dominant(prev)

    if dom_curr == dom_prev:
        return {"detected": False, "delta": 0.0, "description": f"technique stable ({dom_curr})"}

    # Fraction shift
    def frac(rows, tech):
        n = len(rows) or 1
        return sum(1 for r in rows if (r.get("technique_class") or "none") == tech) / n

    delta = round(frac(current, dom_curr) - frac(prev, dom_curr), 4)
    return {
        "detected": True,
        "delta": delta,
        "description": f"technique shifted from '{dom_prev}' to '{dom_curr}' (Δ={delta:+.2%})",
    }


def _cluster_shift(current: list, prev: list) -> dict:
    """Detect change in cluster spread (number of distinct clusters represented)."""
    clusters_curr = {r.get("cluster") for r in current if r.get("cluster")}
    clusters_prev = {r.get("cluster") for r in prev if r.get("cluster")}

    delta = len(clusters_curr) - len(clusters_prev)
    if delta == 0:
        return {
            "detected": False,
            "delta": 0.0,
            "description": f"cluster spread stable ({len(clusters_curr)} clusters)",
        }

    direction = "broadened" if delta > 0 else "narrowed"
    return {
        "detected": True,
        "delta": float(delta),
        "description": (
            f"cluster spread {direction}: {len(clusters_prev)} → {len(clusters_curr)} "
            f"(added: {clusters_curr - clusters_prev}, dropped: {clusters_prev - clusters_curr})"
        ),
    }


def _salience_shift(current: list, prev: list) -> dict:
    """Detect change in mean emotional salience score."""
    def mean_sal(rows):
        vals = [r.get("emotional_salience_score") or 0.0 for r in rows]
        return sum(vals) / len(vals) if vals else 0.0

    curr_sal = mean_sal(current)
    prev_sal = mean_sal(prev)
    delta = round(curr_sal - prev_sal, 4)

    if abs(delta) < 0.05:
        return {
            "detected": False,
            "delta": delta,
            "description": f"salience stable (mean={curr_sal:.2f})",
        }

    direction = "increased" if delta > 0 else "decreased"
    return {
        "detected": True,
        "delta": delta,
        "description": f"emotional salience {direction}: {prev_sal:.2f} → {curr_sal:.2f} (Δ={delta:+.2f})",
    }


def _volume_shift(current: list, prev: list) -> dict:
    """Detect significant change in claim volume."""
    curr_n = len(current)
    prev_n = len(prev)

    if prev_n == 0:
        return _NO_SHIFT.copy()

    ratio = curr_n / prev_n
    delta = round(ratio - 1.0, 4)

    if abs(delta) < 0.25:
        return {
            "detected": False,
            "delta": delta,
            "description": f"volume stable ({prev_n} → {curr_n})",
        }

    direction = "surge" if delta > 0 else "drop"
    return {
        "detected": True,
        "delta": delta,
        "description": f"volume {direction}: {prev_n} → {curr_n} claims ({delta:+.0%})",
    }


def _confidence_shift(current: list, prev: list) -> dict:
    """Detect change in mean staging confidence."""
    def mean_conf(rows):
        vals = [r.get("staging_confidence") or 0.0 for r in rows]
        return sum(vals) / len(vals) if vals else 0.0

    curr_c = mean_conf(current)
    prev_c = mean_conf(prev)
    delta = round(curr_c - prev_c, 4)

    if abs(delta) < 0.05:
        return {
            "detected": False,
            "delta": delta,
            "description": f"confidence stable (mean={curr_c:.2f})",
        }

    direction = "increased" if delta > 0 else "decreased"
    return {
        "detected": True,
        "delta": delta,
        "description": f"staging confidence {direction}: {prev_c:.2f} → {curr_c:.2f} (Δ={delta:+.2f})",
    }
