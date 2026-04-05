"""
social_ingest.py — Social monitor management and stub ingest interface.

The actual Playwright scraping requires an authenticated browser session
and is not suitable for headless container execution without additional
setup. The ingest function returns a clear error directing the analyst
to configure it via browser_agent.

CRUD operations on social_monitors are fully functional — monitors can be
created, listed, updated, and deleted. The monitor loop will run when
ingest is operational.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from .db import jloads, jdumps

log = logging.getLogger("[SOCIAL]")


# ---------------------------------------------------------------------------
# Stub ingest
# ---------------------------------------------------------------------------

def ingest_x_search(conn, query: str, topic_tags: list = None) -> dict:
    """
    Stub: social ingestion requires playwright and an authenticated X session.

    To configure:
    1. Use browser_agent to log into X/Twitter in a browser session.
    2. Extract the auth_token and ct0 cookies.
    3. Set X_AUTH_TOKEN and X_CT0_TOKEN environment variables.
    4. Rebuild/restart the OSS plugin container.

    Until configured, this function does nothing and returns an error descriptor.
    """
    return {
        "ok":    False,
        "error": (
            "Social ingestion requires playwright and authenticated session. "
            "Use browser_agent to configure. Set X_AUTH_TOKEN and X_CT0_TOKEN "
            "environment variables, then rebuild the container."
        ),
        "query":      query,
        "topic_tags": topic_tags or [],
    }


# ---------------------------------------------------------------------------
# Social monitor CRUD
# ---------------------------------------------------------------------------

def get_social_monitors(conn) -> list:
    """Return all social monitors, ordered by creation date."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM social_monitors ORDER BY created_at DESC"
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_social_monitors failed: {e}")
        return []


def add_social_monitor(conn, monitor_type: str, query: str,
                       topic_tags: list = None) -> dict:
    """
    Create a new social monitor.

    monitor_type: one of 'search', 'hashtag', 'user'
    query:        the search query, hashtag (without #), or username (without @)
    topic_tags:   list of topic tag strings to associate with ingested claims

    Returns the created monitor row as dict.
    """
    valid_types = {"search", "hashtag", "user"}
    if monitor_type not in valid_types:
        raise ValueError(f"monitor_type must be one of {valid_types}")
    try:
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO social_monitors
                (monitor_type, query, topic_tags, enabled, created_at)
            VALUES (?,?,?,1,?)
        """, (
            monitor_type,
            query.strip(),
            jdumps(topic_tags or []),
            now,
        ))
        conn.commit()
        monitor_id = cur.lastrowid
        log.info(f"Added social monitor id={monitor_id} type={monitor_type} query={query!r}")
        return _get_monitor(conn, monitor_id) or {}
    except Exception as e:
        log.warning(f"add_social_monitor failed: {e}")
        raise


def update_social_monitor(conn, monitor_id: int, enabled: bool = None,
                          query: str = None) -> dict:
    """
    Update a social monitor's enabled state and/or query string.
    Returns the updated row as dict.
    """
    try:
        sets = []
        params = []
        if enabled is not None:
            sets.append("enabled=?")
            params.append(1 if enabled else 0)
        if query is not None:
            sets.append("query=?")
            params.append(query.strip())
        if not sets:
            return _get_monitor(conn, monitor_id) or {}
        params.append(monitor_id)
        conn.execute(
            f"UPDATE social_monitors SET {', '.join(sets)} WHERE id=?",
            params,
        )
        conn.commit()
        log.info(f"Updated social monitor id={monitor_id}")
        return _get_monitor(conn, monitor_id) or {}
    except Exception as e:
        log.warning(f"update_social_monitor failed: {e}")
        raise


def delete_social_monitor(conn, monitor_id: int) -> bool:
    """
    Delete a social monitor. Returns True if a row was deleted.
    """
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM social_monitors WHERE id=?", (monitor_id,))
        conn.commit()
        deleted = cur.rowcount > 0
        if deleted:
            log.info(f"Deleted social monitor id={monitor_id}")
        return deleted
    except Exception as e:
        log.warning(f"delete_social_monitor failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_monitor(conn, monitor_id: int) -> Optional[dict]:
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM social_monitors WHERE id=?", (monitor_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception:
        return None
