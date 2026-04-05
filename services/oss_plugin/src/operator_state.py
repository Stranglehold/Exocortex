"""
operator_state.py — Tracks operator cognitive state.

Threshold multipliers:
  NOMINAL  = 1.0   (baseline vigilance)
  DEGRADED = 1.25  (raised thresholds — fatigue or distraction)
  IMPAIRED = 1.50  (significantly raised thresholds — high cognitive load)
"""
import logging
from datetime import datetime, timezone

log = logging.getLogger("[OPERATOR_STATE]")

MULTIPLIERS = {
    "NOMINAL":  1.0,
    "DEGRADED": 1.25,
    "IMPAIRED": 1.50,
}

_VALID_LEVELS = set(MULTIPLIERS.keys())


def get_current_state(conn) -> dict:
    """Return the most-recent operator state row as a dict."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT alert_level, threshold_multiplier, reason, set_at, set_by "
            "FROM operator_state ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            return dict(row)
        # Fallback if table is somehow empty
        return {
            "alert_level": "NOMINAL",
            "threshold_multiplier": 1.0,
            "reason": None,
            "set_at": None,
            "set_by": "default",
        }
    except Exception as e:
        log.warning(f"get_current_state failed: {e}")
        return {
            "alert_level": "NOMINAL",
            "threshold_multiplier": 1.0,
            "reason": None,
            "set_at": None,
            "set_by": "error",
        }


def get_threshold_multiplier(conn) -> float:
    """Return only the numeric threshold multiplier for the current state."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT threshold_multiplier FROM operator_state ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            return float(row["threshold_multiplier"])
        return 1.0
    except Exception as e:
        log.warning(f"get_threshold_multiplier failed: {e}")
        return 1.0


def set_state(conn, alert_level: str, reason: str = None,
              set_by: str = "analyst") -> dict:
    """
    Insert a new operator state row. Does NOT update the previous row —
    the table is an append-only history. Returns the new current state dict.
    """
    level = alert_level.upper()
    if level not in _VALID_LEVELS:
        raise ValueError(f"Invalid alert_level '{alert_level}'. Must be one of {sorted(_VALID_LEVELS)}")

    multiplier = MULTIPLIERS[level]
    now = datetime.now(timezone.utc).isoformat()

    try:
        conn.execute(
            """INSERT INTO operator_state
                   (alert_level, threshold_multiplier, reason, set_at, set_by)
               VALUES (?,?,?,?,?)""",
            (level, multiplier, reason, now, set_by),
        )
        conn.commit()
        log.info(f"Operator state set to {level} (×{multiplier}) by {set_by}")
        return get_current_state(conn)
    except Exception as e:
        log.warning(f"set_state failed: {e}")
        raise


def get_state_history(conn, limit: int = 20) -> list:
    """Return recent operator state history, newest first."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM operator_state ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_state_history failed: {e}")
        return []
