"""
credibility.py — Analyst-driven source credibility model.

The analyst marks sources as reliable, unreliable, or conditional
("reliable on military topics, unreliable on economic data").
Credibility weights flow through to synthesis scoring.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from .db import jloads, jdumps

log = logging.getLogger("[CREDIBILITY]")

_DEFAULT_OVERALL = 0.7


def set_credibility(conn, source_id: int, overall: float,
                    domain_overrides: dict = None,
                    set_by: str = "analyst") -> dict:
    """
    Upsert a credibility record for a source.
    overall must be in [0.0, 1.0].
    domain_overrides is a dict mapping domain name → score, e.g.
      {"military": 0.9, "economic": 0.3}
    Returns the full record as dict.
    """
    try:
        overall = max(0.0, min(1.0, float(overall)))
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            INSERT INTO source_credibility
                (source_id, overall, domain_overrides, set_by, last_updated)
            VALUES (?,?,?,?,?)
            ON CONFLICT(source_id) DO UPDATE SET
                overall          = excluded.overall,
                domain_overrides = excluded.domain_overrides,
                set_by           = excluded.set_by,
                last_updated     = excluded.last_updated
        """, (
            source_id,
            overall,
            jdumps(domain_overrides or {}),
            set_by,
            now,
        ))
        conn.commit()
        log.info(f"Set credibility source_id={source_id} overall={overall:.2f} by={set_by}")
        return get_credibility(conn, source_id)
    except Exception as e:
        log.warning(f"set_credibility failed: {e}")
        raise


def get_credibility(conn, source_id: int) -> dict:
    """
    Return credibility record for a source.
    Returns default {overall: 0.7, domain_overrides: {}} if no record exists.
    """
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM source_credibility WHERE source_id=?",
            (source_id,),
        )
        row = cur.fetchone()
        if row:
            return dict(row)
        return {
            "source_id":       source_id,
            "overall":         _DEFAULT_OVERALL,
            "domain_overrides": {},
            "set_by":          "default",
            "last_updated":    None,
        }
    except Exception as e:
        log.warning(f"get_credibility failed: {e}")
        return {
            "source_id":       source_id,
            "overall":         _DEFAULT_OVERALL,
            "domain_overrides": {},
            "set_by":          "default",
            "last_updated":    None,
        }


def get_credibility_for_domain(conn, source_id: int, domain: str) -> float:
    """
    Return the domain-specific score if a domain_overrides entry exists for
    `domain`, else return the overall score, else return 0.7.
    """
    try:
        rec = get_credibility(conn, source_id)
        overrides = jloads(rec.get("domain_overrides"), {})
        if domain and domain in overrides:
            return max(0.0, min(1.0, float(overrides[domain])))
        return max(0.0, min(1.0, float(rec.get("overall", _DEFAULT_OVERALL))))
    except Exception as e:
        log.warning(f"get_credibility_for_domain failed: {e}")
        return _DEFAULT_OVERALL


def list_all(conn) -> list:
    """
    Return all credibility records joined with source name and url.
    Ordered by overall score descending.
    """
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT sc.*, s.name AS source_name, s.url AS source_url,
                   s.source_type, s.cluster
            FROM source_credibility sc
            JOIN sources s ON s.id = sc.source_id
            ORDER BY sc.overall DESC
        """)
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"list_all credibility failed: {e}")
        return []


def get_credibility_map(conn) -> dict:
    """
    Return {source_id: float} for all sources that have a credibility record.
    Uses the domain-neutral overall score.
    Sources without records are not included — callers should default to 0.7.
    """
    try:
        cur = conn.cursor()
        cur.execute("SELECT source_id, overall FROM source_credibility")
        return {int(r["source_id"]): float(r["overall"]) for r in cur.fetchall()}
    except Exception as e:
        log.warning(f"get_credibility_map failed: {e}")
        return {}
