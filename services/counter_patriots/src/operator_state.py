"""
operator_state.py — Operator state monitoring and threshold elevation.

Tracks the current cognitive/operational state of the system's human operators.
When the operator is degraded or impaired, the staging confidence threshold
is automatically elevated — making it harder for claims to reach PROMOTED
without additional corroboration.

Mechanism (CDS v2 spec, Gap 7):
  Behavioral signals monitored → state inferred → threshold multiplier applied.
  Threshold elevation is mechanical, not discretionary.
  Operator override available in both directions.

Behavioral signal integration:
  Phase 4. Requires operator interface plumbing to measure message length,
  response latency, and verification behavior deviation signals.
  Until that interface exists, state is set via API by the operator themselves
  or by an external monitoring process.

Current state is always the most recent row in operator_state table.
History is preserved for audit. State is never deleted.

Alert levels and their threshold multipliers:
  NOMINAL:  1.0x — baseline staging threshold
  DEGRADED: 1.25x — elevated: minor impairment, fatigue, distraction
  IMPAIRED: 1.50x — maximum elevation: significant impairment detected

Phase 3 implementation. Behavioral signal measurement: Phase 4.
"""

import logging
import os
import uuid

import psycopg2
import psycopg2.extras

import audit

log = logging.getLogger(__name__)

DB_URL = os.environ.get(
    "CP_DB_URL",
    "postgresql://cds_app:cds_app_dev_password@localhost:5433/counter_patriots"
)

VALID_ALERT_LEVELS = ("NOMINAL", "DEGRADED", "IMPAIRED")

THRESHOLD_MULTIPLIERS = {
    "NOMINAL":  1.00,
    "DEGRADED": 1.25,
    "IMPAIRED": 1.50,
}


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Read current state
# ---------------------------------------------------------------------------

def get_current_state() -> dict:
    """
    Return the current operator state and active threshold multiplier.

    Returns:
        {
            alert_level:          str,
            threshold_multiplier: float,
            reason:               str | None,
            set_by:               str,
            set_at:               ISO timestamp,
            override_active:      bool,
        }
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT alert_level, threshold_multiplier, reason,
                       set_by, set_at, override_active
                FROM operator_state
                ORDER BY set_at DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()

    if not row:
        # Table exists but is empty — return safe default
        return {
            "alert_level":          "NOMINAL",
            "threshold_multiplier": 1.0,
            "reason":               "no_state_recorded",
            "set_by":               "system",
            "set_at":               None,
            "override_active":      False,
        }

    d = dict(row)
    d["set_at"] = d["set_at"].isoformat() if d["set_at"] else None
    return d


def get_threshold_multiplier() -> float:
    """
    Return only the active threshold multiplier.
    Used by staging/promotion endpoints to apply elevated threshold.
    """
    return get_current_state()["threshold_multiplier"]


# ---------------------------------------------------------------------------
# Set state
# ---------------------------------------------------------------------------

def set_state(
    alert_level: str,
    reason: str,
    set_by: str = "analyst",
    override: bool = False,
    session_id=None,
) -> dict:
    """
    Set the current operator state.

    Inserts a new row (state history is preserved).
    When alert_level is NOMINAL, clears any active override.

    Args:
        alert_level:  NOMINAL | DEGRADED | IMPAIRED
        reason:       Description of why the state is being set
        set_by:       Actor setting the state (analyst, system, monitor)
        override:     True = analyst overriding auto-detection
        session_id:   UUID for audit trail

    Returns:
        New state dict

    Raises:
        ValueError: if alert_level not in VALID_ALERT_LEVELS
    """
    sid = session_id or uuid.uuid4()
    alert_level = alert_level.upper().strip()

    if alert_level not in VALID_ALERT_LEVELS:
        raise ValueError(
            f"Invalid alert_level: {alert_level!r}. "
            f"Must be one of {VALID_ALERT_LEVELS}"
        )

    multiplier    = THRESHOLD_MULTIPLIERS[alert_level]
    override_flag = override and alert_level != "NOMINAL"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO operator_state
                    (alert_level, threshold_multiplier, reason, set_by, override_active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING set_at
                """,
                (alert_level, multiplier, reason, set_by, override_flag),
            )
            row = cur.fetchone()

    audit.log_event(
        session_id=sid,
        event_type="operator_state_change",
        actor=set_by,
        action=(
            f"Operator state → {alert_level} "
            f"(multiplier={multiplier}x, override={override_flag}): {reason}"
        ),
        data_accessed={
            "alert_level":          alert_level,
            "threshold_multiplier": multiplier,
            "override_active":      override_flag,
        },
    )

    level_msg = f"[OPERATOR] State → {alert_level} (threshold {multiplier}x): {reason}"
    if alert_level == "NOMINAL":
        log.info(level_msg)
    elif alert_level == "DEGRADED":
        log.warning(level_msg)
    else:
        log.error(level_msg)

    return {
        "alert_level":          alert_level,
        "threshold_multiplier": multiplier,
        "reason":               reason,
        "set_by":               set_by,
        "set_at":               row["set_at"].isoformat(),
        "override_active":      override_flag,
    }


# ---------------------------------------------------------------------------
# State history
# ---------------------------------------------------------------------------

def get_state_history(limit: int = 20) -> list:
    """
    Recent operator state history, newest first.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT alert_level, threshold_multiplier, reason,
                       set_by, set_at, override_active
                FROM operator_state
                ORDER BY set_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

    result = []
    for r in rows:
        d = dict(r)
        d["set_at"] = d["set_at"].isoformat() if d["set_at"] else None
        result.append(d)
    return result
