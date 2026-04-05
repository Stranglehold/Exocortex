"""
api_oss_submit.py — Analyst claim dictation path

URL: POST /api/plugins/oss/api_oss_submit

Input:
  claim_text      str   required — the claim to submit
  topic_tags      list  optional — topic tag strings
  source_name     str   optional — defaults to "Analyst Manual Entry"
  technique_class str   optional

Embeds claim, checks for duplicate via FAISS, inserts as STAGED,
then auto-promotes (analyst source = high confidence).
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

import json
import os

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db, jdumps

_ANALYST_SOURCE_NAME = "Analyst Manual Entry"
_ANALYST_SOURCE_URL  = "analyst://manual"
_FAISS_PATH = os.environ.get("OSS_FAISS_PATH", "/a0/usr/oss/claims.index")
_DEDUP_THRESHOLD = float(os.environ.get("OSS_DEDUP_THRESHOLD", "0.95"))


def _get_or_create_analyst_source(conn, source_name: str) -> int:
    """Return id for the analyst source, creating it if needed."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM sources WHERE name = ?", (source_name,))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute("""
        INSERT OR IGNORE INTO sources
            (name, url, source_type, cluster, confidence_score)
        VALUES (?, ?, 'official', 'official', 1.0)
    """, (source_name, f"analyst://{source_name.lower().replace(' ', '-')}"))
    conn.commit()
    cur.execute("SELECT id FROM sources WHERE name = ?", (source_name,))
    return cur.fetchone()["id"]


def _embed(text: str):
    """Embed text using the OSS embedding model. Returns numpy float32 array."""
    from sentence_transformers import SentenceTransformer
    import numpy as np
    model_name = os.environ.get("OSS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    m = SentenceTransformer(model_name)
    vec = m.encode([text], normalize_embeddings=True).astype("float32")
    return vec


def _check_duplicate(vec) -> bool:
    """Return True if a near-identical claim already exists in FAISS."""
    if not os.path.exists(_FAISS_PATH):
        return False
    try:
        import faiss
        import numpy as np
        idx = faiss.read_index(_FAISS_PATH)
        if idx.ntotal == 0:
            return False
        distances, _ = idx.search(vec, 1)
        return float(distances[0][0]) >= _DEDUP_THRESHOLD
    except Exception:
        return False


def _add_to_faiss(vec, claim_id: int) -> None:
    """Add a new vector to FAISS index and persist."""
    try:
        import faiss
        import numpy as np
        if os.path.exists(_FAISS_PATH):
            idx = faiss.read_index(_FAISS_PATH)
        else:
            os.makedirs(os.path.dirname(_FAISS_PATH), exist_ok=True)
            idx = faiss.IndexFlatIP(vec.shape[1])
        idx.add(vec)
        faiss.write_index(idx, _FAISS_PATH)
    except Exception:
        pass


class OssSubmit(ApiHandler):
    """Analyst claim dictation — embed, deduplicate, insert, auto-promote.

    URL: POST /api/plugins/oss/api_oss_submit
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        claim_text = (input.get("claim_text") or "").strip()
        if not claim_text:
            return {"ok": False, "error": "claim_text is required"}

        source_name     = (input.get("source_name") or _ANALYST_SOURCE_NAME).strip()
        topic_tags      = input.get("topic_tags") or []
        technique_class = (input.get("technique_class") or "").strip() or None

        if not isinstance(topic_tags, list):
            topic_tags = [str(topic_tags)]

        try:
            conn = get_conn()
            init_db(conn)

            source_id = _get_or_create_analyst_source(conn, source_name)

            # Embed and check for duplicate
            vec = _embed(claim_text)
            if _check_duplicate(vec):
                conn.close()
                return {
                    "ok": True,
                    "duplicate": True,
                    "message": "Claim already in ledger",
                }

            # Insert as STAGED with high staging_confidence (analyst source)
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO claims
                    (source_id, raw_text, claim_text, article_url,
                     topic_tags, technique_class, extracted_at,
                     trust_level, staging_confidence)
                VALUES (?,?,?,?,?,?,?,'STAGED', 0.9)
            """, (
                source_id,
                claim_text,
                claim_text,
                f"analyst://manual/{now}",
                jdumps(topic_tags),
                technique_class,
                now,
            ))
            conn.commit()
            claim_id = cur.lastrowid

            # Add to FAISS
            _add_to_faiss(vec, claim_id)

            # Auto-promote: analyst source = high confidence
            conn.execute("""
                INSERT INTO promotion_snapshots
                    (claim_id, promoted_at, promotion_confidence,
                     source_weights, threshold_at_promotion,
                     promoting_evidence, falsification_predictions)
                VALUES (?,?,?,?,?,?,?)
            """, (
                claim_id, now, 0.9,
                jdumps({source_name: 1.0}),
                0.5,
                jdumps(["Analyst manual entry"]),
                jdumps([]),
            ))
            conn.execute(
                "UPDATE claims SET trust_level='PROMOTED' WHERE id=?",
                (claim_id,),
            )
            conn.commit()
            conn.close()

            return {
                "ok": True,
                "claim_id": claim_id,
                "duplicate": False,
                "promoted": True,
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
