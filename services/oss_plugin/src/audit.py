"""
audit.py — Append-only audit log for OSS events.
"""
import logging
from .db import jdumps

log = logging.getLogger("[AUDIT]")


def log_event(conn, session_id, event_type: str, actor: str, action: str,
              data_accessed=None, trust_level: str = None, injection_flag: bool = False):
    """Append one audit record. Caller is responsible for connection lifecycle."""
    try:
        conn.execute("""
            INSERT INTO audit_log
                (session_id, event_type, actor, action, data_accessed, trust_level, injection_flag)
            VALUES (?,?,?,?,?,?,?)
        """, (
            str(session_id),
            event_type,
            actor,
            action,
            jdumps(data_accessed) if data_accessed is not None else None,
            trust_level,
            1 if injection_flag else 0,
        ))
        conn.commit()
    except Exception as e:
        log.warning(f"log_event failed: {e}")


def get_recent(conn, limit: int = 50) -> list:
    """Return the most-recent audit records, newest first."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_recent failed: {e}")
        return []
