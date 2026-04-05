"""
contradict.py — Contradiction detection between claims.

Scans STAGED/PROMOTED claims from the same source on the same topic.
Uses embedding cosine similarity — claims from the same source on the same
topic with cosine < 0.4 within a 7-day window are flagged as potential
contradictions.
"""
import logging
from datetime import datetime, timezone, timedelta

from .db import jloads

log = logging.getLogger("[CONTRADICT]")


# ---------------------------------------------------------------------------
# Embedding helper (standalone — no import from ingest)
# ---------------------------------------------------------------------------

def _embed(texts: list):
    """Return normalized embeddings or None on failure."""
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        m = SentenceTransformer("all-MiniLM-L6-v2")
        return m.encode(texts, normalize_embeddings=True)
    except Exception as e:
        log.warning(f"_embed failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Contradiction scan
# ---------------------------------------------------------------------------

def scan_new_claims(conn) -> int:
    """
    Find pairs of recent STAGED/PROMOTED claims from the same source that may
    contradict each other. Criteria:
      - same source
      - share at least one topic tag
      - published/extracted within 7 days of each other
      - embedding cosine < 0.4

    Inserts into contradictions table (INSERT OR IGNORE equivalent via
    checking existence first). Returns count of new contradiction records.
    """
    inserted = 0
    try:
        cur = conn.cursor()
        # Fetch recent eligible claims (last 14 days to catch pairs)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
        cur.execute("""
            SELECT id, source_id, claim_text, topic_tags, extracted_at
            FROM claims
            WHERE trust_level IN ('STAGED','PROMOTED')
              AND extracted_at >= ?
            ORDER BY source_id, extracted_at
        """, (cutoff,))
        rows = [dict(r) for r in cur.fetchall()]

        if len(rows) < 2:
            return 0

        # Group by source_id for efficient pairwise comparison
        by_source: dict = {}
        for row in rows:
            sid = row["source_id"]
            by_source.setdefault(sid, []).append(row)

        for source_id, claims in by_source.items():
            if len(claims) < 2:
                continue

            for i in range(len(claims)):
                for j in range(i + 1, len(claims)):
                    ca = claims[i]
                    cb = claims[j]

                    # Check topic overlap
                    tags_a = set(jloads(ca["topic_tags"], []))
                    tags_b = set(jloads(cb["topic_tags"], []))
                    if not tags_a & tags_b:
                        continue

                    # Check time window (7 days)
                    try:
                        ta = datetime.fromisoformat(ca["extracted_at"].replace("Z", "+00:00"))
                        tb = datetime.fromisoformat(cb["extracted_at"].replace("Z", "+00:00"))
                        if abs((tb - ta).total_seconds()) > 7 * 86400:
                            continue
                    except Exception:
                        continue

                    # Check not already recorded
                    cur.execute("""
                        SELECT id FROM contradictions
                        WHERE (claim_a_id=? AND claim_b_id=?)
                           OR (claim_a_id=? AND claim_b_id=?)
                    """, (ca["id"], cb["id"], cb["id"], ca["id"]))
                    if cur.fetchone():
                        continue

                    # Embed and compute cosine
                    vecs = _embed([ca["claim_text"], cb["claim_text"]])
                    if vecs is None:
                        continue

                    import numpy as np  # noqa: PLC0415
                    cosine = float(np.dot(vecs[0], vecs[1]))

                    if cosine < 0.4:
                        confidence = round(max(0.0, min(1.0, 1.0 - cosine)), 4)
                        try:
                            conn.execute("""
                                INSERT INTO contradictions
                                    (claim_a_id, claim_b_id, relationship,
                                     confidence, source_acknowledged, analyst_reviewed)
                                VALUES (?,?,?,?,0,0)
                            """, (ca["id"], cb["id"], "contradiction", confidence))
                            conn.commit()
                            inserted += 1
                            log.info(
                                f"Contradiction flagged: claims {ca['id']} ↔ {cb['id']} "
                                f"(cosine={cosine:.3f}, confidence={confidence:.3f})"
                            )
                        except Exception as e:
                            log.warning(f"Insert contradiction failed: {e}")

    except Exception as e:
        log.warning(f"scan_new_claims failed: {e}")

    return inserted


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def get_contradictions(conn, source_name: str = None, topic_tag: str = None,
                       since: str = None, limit: int = 200) -> list:
    """
    Return contradiction records, optionally filtered by source name,
    topic tag, or flagged-at date. Returns newest first.
    """
    try:
        cur = conn.cursor()
        clauses = []
        params: list = []

        base_query = """
            SELECT ct.*,
                   ca.claim_text  AS claim_a_text,
                   cb.claim_text  AS claim_b_text,
                   ca.source_id   AS source_a_id,
                   cb.source_id   AS source_b_id,
                   sa.name        AS source_a_name,
                   sb.name        AS source_b_name
            FROM contradictions ct
            JOIN claims  ca ON ca.id = ct.claim_a_id
            JOIN claims  cb ON cb.id = ct.claim_b_id
            JOIN sources sa ON sa.id = ca.source_id
            JOIN sources sb ON sb.id = cb.source_id
        """

        if source_name:
            clauses.append("(sa.name LIKE ? OR sb.name LIKE ?)")
            params += [f"%{source_name}%", f"%{source_name}%"]

        if topic_tag:
            clauses.append("""
                (EXISTS (SELECT 1 FROM json_each(ca.topic_tags) WHERE value=?)
                 OR EXISTS (SELECT 1 FROM json_each(cb.topic_tags) WHERE value=?))
            """)
            params += [topic_tag, topic_tag]

        if since:
            clauses.append("ct.flagged_at >= ?")
            params.append(since)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)

        cur.execute(
            f"{base_query} {where} ORDER BY ct.id DESC LIMIT ?",
            params,
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_contradictions failed: {e}")
        return []
