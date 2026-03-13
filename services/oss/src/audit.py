"""
audit.py — Append-only audit log for OSS.

Records decision events, analyst access, trust level transitions,
and injection detection flags.

Enforcement is two-layer:
  DB level:   oss_app role has UPDATE and DELETE revoked on audit_log
  Code level: this module exposes only insert functions — no update, no delete

Never call UPDATE or DELETE on audit_log anywhere in the codebase.
The append-only invariant is architectural, not just convention.
"""

import os
import logging

import psycopg2
import psycopg2.extras

log = logging.getLogger(__name__)

DB_URL = os.environ.get(
    "OSS_DB_URL",
    "postgresql://oss_app:oss_app_dev_password@localhost:5433/oss"
)


def log_event(
    session_id,
    event_type: str,
    actor: str,
    action: str,
    data_accessed=None,
    trust_level: str = None,
    injection_flag: bool = False,
):
    """
    Append one record to the audit_log. The only write operation in this module.

    Args:
        session_id:     UUID identifying the request or session
        event_type:     Categorical event type, e.g.:
                          'claim_promoted'        — trust level transition
                          'claim_returned'        — contamination cascade action
                          'analyst_query'         — authenticated endpoint access
                          'source_edge_registered' — network topology update
                          'injection_suspected'   — potential injection in input
        actor:          Who performed the action: 'system' | 'analyst' | 'cascade'
        action:         Human-readable description of what happened
        data_accessed:  JSONB payload — what data was read or modified
        trust_level:    Claim trust level at time of event, if relevant
        injection_flag: True if prompt injection was suspected in input
    """
    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_log
                        (session_id, event_type, actor, action,
                         data_accessed, trust_level, injection_flag)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(session_id),
                        event_type,
                        actor,
                        action,
                        psycopg2.extras.Json(data_accessed)
                        if data_accessed is not None
                        else None,
                        trust_level,
                        injection_flag,
                    ),
                )
    except Exception as e:
        # Audit failure must never crash the application path.
        # Log locally but do not propagate the exception.
        log.warning(f"[AUDIT] log_event failed ({event_type}): {e}")
