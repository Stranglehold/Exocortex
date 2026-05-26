"""
rejection.py — Rejection ledger transparency layer.

Claims rejected during ingestion are stored here for analyst review.
Transparency at every stage — the analyst can see what was rejected and why.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from .db import jloads, jdumps

log = logging.getLogger("[REJECTION]")


def get_rejections(conn, reason: str = None, source_id: int = None,
                   since: str = None, limit: int = 100) -> list:
    """
    Return rejection records, optionally filtered by reason, source, and/or
    since timestamp. Results ordered newest first.
    """
    try:
        cur = conn.cursor()
        clauses = []
        params = []

        if reason is not None:
            clauses.append("rejection_reason=?")
            params.append(reason)
        if source_id is not None:
            clauses.append("source_id=?")
            params.append(source_id)
        if since is not None:
            clauses.append("rejected_at >= ?")
            params.append(since)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)

        cur.execute(
            f"SELECT rl.*, s.name AS source_name "
            f"FROM rejection_ledger rl "
            f"LEFT JOIN sources s ON s.id = rl.source_id "
            f"{where} "
            f"ORDER BY rl.id DESC LIMIT ?",
            params,
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_rejections failed: {e}")
        return []


def get_rejection_summary(conn, since: str = None) -> dict:
    """
    Return aggregate rejection statistics.

    Result:
        {
          total,
          by_reason: {duplicate: N, low_confidence: N, off_topic: N, source_rejected: N},
          recent_sources: [list of source names with highest rejection counts]
        }
    """
    try:
        cur = conn.cursor()
        since_clause = "WHERE rejected_at >= ?" if since else ""
        params = [since] if since else []

        # Total and by-reason counts
        cur.execute(
            f"SELECT rejection_reason, COUNT(*) AS cnt "
            f"FROM rejection_ledger {since_clause} "
            f"GROUP BY rejection_reason",
            params,
        )
        by_reason_raw = {r["rejection_reason"]: r["cnt"] for r in cur.fetchall()}
        by_reason = {
            "duplicate":        by_reason_raw.get("duplicate", 0),
            "low_confidence":   by_reason_raw.get("low_confidence", 0),
            "off_topic":        by_reason_raw.get("off_topic", 0),
            "source_rejected":  by_reason_raw.get("source_rejected", 0),
        }
        total = sum(by_reason.values())

        # Top sources by rejection volume
        cur.execute(
            f"SELECT s.name, COUNT(*) AS cnt "
            f"FROM rejection_ledger rl "
            f"LEFT JOIN sources s ON s.id = rl.source_id "
            f"{since_clause} "
            f"GROUP BY rl.source_id, s.name "
            f"ORDER BY cnt DESC LIMIT 10",
            params,
        )
        recent_sources = [
            {"source_name": r["name"] or "unknown", "count": r["cnt"]}
            for r in cur.fetchall()
        ]

        return {
            "total":          total,
            "by_reason":      by_reason,
            "recent_sources": recent_sources,
        }
    except Exception as e:
        log.warning(f"get_rejection_summary failed: {e}")
        return {"total": 0, "by_reason": {}, "recent_sources": []}


def override_rejection(conn, rejection_id: int, analyst_note: str) -> dict:
    """
    Manually override a rejection: re-ingest the rejected claim as STAGED
    with staging_confidence=0.8, then record the override in audit_log.

    Does NOT alter the rejection_ledger schema — override is tracked via
    audit_log (event_type='rejection_override').

    Returns the newly created claim row as dict, or {} on failure.
    """
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM rejection_ledger WHERE id=?",
            (rejection_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Rejection {rejection_id} not found")
        rej = dict(row)

        now = datetime.now(timezone.utc).isoformat()

        # Insert the claim as STAGED
        cur.execute("""
            INSERT INTO claims
                (source_id, raw_text, claim_text, article_url, article_title,
                 topic_tags, extracted_at, trust_level, staging_confidence)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            rej.get("source_id"),
            rej.get("claim_text", ""),
            rej.get("claim_text", ""),
            rej.get("article_url", ""),
            rej.get("article_title"),
            "[]",          # topic_tags — analyst can tag manually
            now,
            "STAGED",
            0.8,
        ))
        conn.commit()
        new_claim_id = cur.lastrowid

        # Embed + index the restored claim so it's visible to dedup and synthesis
        # FAISS retrieval — without faiss_id it would be a second-class claim that
        # re-duplicates and never surfaces in synthesis. Reuse ingest's shared embedder.
        try:
            from .ingest import embed as _embed, add_to_faiss as _add_to_faiss  # noqa: PLC0415
            vec = _embed([rej.get("claim_text", "")])
            fid = _add_to_faiss(vec)
            cur.execute("UPDATE claims SET faiss_id=? WHERE id=?", (fid, new_claim_id))
            conn.commit()
        except Exception as e:
            log.warning(f"override_rejection: FAISS index failed for claim {new_claim_id}: {e}")

        # Record override in audit_log
        session_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO audit_log
                (session_id, event_type, actor, action, data_accessed, trust_level)
            VALUES (?,?,?,?,?,?)
        """, (
            session_id,
            "rejection_override",
            "analyst",
            f"Override rejection id={rejection_id} → claim id={new_claim_id}. Note: {analyst_note}",
            jdumps({
                "rejection_id":   rejection_id,
                "new_claim_id":   new_claim_id,
                "analyst_note":   analyst_note,
                "original_reason": rej.get("rejection_reason"),
            }),
            "STAGED",
        ))
        conn.commit()

        log.info(f"Override rejection id={rejection_id} → new claim id={new_claim_id}")

        # Return the new claim row
        cur.execute("SELECT * FROM claims WHERE id=?", (new_claim_id,))
        claim_row = cur.fetchone()
        return dict(claim_row) if claim_row else {}

    except Exception as e:
        log.warning(f"override_rejection failed: {e}")
        raise
