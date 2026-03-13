"""
contradict.py — Contradiction detection engine for OSS.

Compares new claims against existing claims from the same source
to detect contradictions, silent retcons, and acknowledged retcons.
Distinguishes these explicitly — Reuters issuing a correction is journalism;
a source silently editing its story is what this system is designed to detect.

Runs after each ingestion pass or on-demand.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import psycopg2
import psycopg2.extras
import faiss
from openai import OpenAI

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

DB_URL      = os.environ.get("OSS_DB_URL", "postgresql://oss_admin:oss_admin_dev_password@localhost:5433/oss")
LLM_URL     = os.environ.get("OSS_LLM_URL", "http://localhost:1234/v1")
LLM_MODEL   = os.environ.get("OSS_LLM_MODEL", "qwen2.5-14b-instruct")
FAISS_PATH  = os.environ.get("OSS_FAISS_PATH", "/app/data/faiss/claims.index")

# Cosine similarity threshold: above this, two claims are semantically close
# enough to warrant contradiction analysis
SIMILARITY_THRESHOLD = float(os.environ.get("OSS_CONTRADICTION_SIMILARITY", "0.72"))

# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

_llm_client: Optional[OpenAI] = None

def get_llm():
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(base_url=LLM_URL, api_key="local")
    return _llm_client


CONTRADICTION_SYSTEM = """You are a fact-checking assistant analyzing pairs of news claims from the same source.

Classify the relationship between claim A and claim B:

- contradiction: The claims assert mutually exclusive facts (e.g., A says suspect had ISIS ties; B says suspect had no ISIS ties).
- retcon_silent: B supersedes A on the same topic but no correction is stated. The story changed without acknowledgment.
- retcon_acknowledged: B explicitly corrects or updates A. The source acknowledged the change.
- elaboration: B adds detail to A without contradiction. Both can be simultaneously true.
- unrelated: The claims do not address the same facts.

Return ONLY a JSON object with exactly these fields:
{
  "relationship": "<one of the five categories>",
  "confidence": <float 0.0-1.0>,
  "source_acknowledged": <true if the source explicitly noted a correction, false otherwise>,
  "reasoning": "<one sentence>"
}"""

def classify_contradiction(claim_a: str, claim_b: str) -> dict:
    """
    Classify the relationship between two claims from the same source.
    Returns dict with relationship, confidence, source_acknowledged, reasoning.
    """
    try:
        resp = get_llm().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": CONTRADICTION_SYSTEM},
                {"role": "user", "content": f"Claim A: {claim_a}\n\nClaim B: {claim_b}"}
            ],
            temperature=0.1,
            max_tokens=200,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        valid_relationships = {'contradiction', 'retcon_silent', 'retcon_acknowledged', 'elaboration', 'unrelated'}
        if result.get('relationship') not in valid_relationships:
            result['relationship'] = 'unrelated'
        result['confidence'] = max(0.0, min(1.0, float(result.get('confidence', 0.5))))
        result['source_acknowledged'] = bool(result.get('source_acknowledged', False))
        return result
    except Exception as e:
        log.warning(f"Contradiction classification failed: {e}")
        return {'relationship': 'unrelated', 'confidence': 0.0,
                'source_acknowledged': False, 'reasoning': 'classification error'}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def get_recent_claims_for_source(source_id: int, since_id: int, limit: int = 200) -> list[dict]:
    """Claims from a source older than since_id, for comparison."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, claim_text, faiss_id, topic_tags, article_url
                FROM claims
                WHERE source_id = %s AND id < %s AND faiss_id IS NOT NULL
                ORDER BY id DESC
                LIMIT %s
            """, (source_id, since_id, limit))
            return cur.fetchall()


def contradiction_already_exists(conn, claim_a_id: int, claim_b_id: int) -> bool:
    """Avoid duplicate contradiction entries for the same pair."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM contradictions
            WHERE (claim_a_id = %s AND claim_b_id = %s)
               OR (claim_a_id = %s AND claim_b_id = %s)
            LIMIT 1
        """, (claim_a_id, claim_b_id, claim_b_id, claim_a_id))
        return cur.fetchone() is not None


def insert_contradiction(conn, claim_a_id: int, claim_b_id: int,
                         relationship: str, confidence: float,
                         source_acknowledged: bool, technique_class: Optional[str],
                         reasoning: str):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO contradictions
                (claim_a_id, claim_b_id, relationship, confidence,
                 source_acknowledged, technique_class, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (claim_a_id, claim_b_id, relationship, confidence,
              source_acknowledged, technique_class, reasoning))


def update_source_retcon_stats(conn, source_id: int, relationship: str):
    """Update source confidence tracking counters."""
    if relationship == 'retcon_silent':
        col = 'silent_retcon_count'
    elif relationship == 'retcon_acknowledged':
        col = 'acknowledged_retcon_count'
    else:
        return
    with conn.cursor() as cur:
        cur.execute(f"UPDATE sources SET {col} = {col} + 1 WHERE id = %s", (source_id,))


def update_source_confidence(conn, source_id: int, window_days: int = 30):
    """
    Recalculate source confidence based on observed retcon behavior.

    Silent retcons damage confidence. Acknowledged retcons are neutral
    or slightly positive (indicates editorial accountability).
    A clean record slowly pulls confidence up.

    This is the core distinction the spec requires: Reuters issuing
    a correction is different from a source silently changing its story.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                s.confidence_score,
                s.total_claims,
                COUNT(CASE WHEN c.relationship = 'retcon_silent' THEN 1 END) AS silent_count,
                COUNT(CASE WHEN c.relationship = 'retcon_acknowledged' THEN 1 END) AS ack_count
            FROM sources s
            LEFT JOIN claims cl ON cl.source_id = s.id
                AND cl.extracted_at >= NOW() - INTERVAL '%s days'
            LEFT JOIN contradictions c ON (c.claim_a_id = cl.id OR c.claim_b_id = cl.id)
                AND c.relationship IN ('retcon_silent', 'retcon_acknowledged')
            WHERE s.id = %s
            GROUP BY s.confidence_score, s.total_claims
        """, (window_days, source_id))
        row = cur.fetchone()
        if not row:
            return

        total        = max(row['total_claims'], 1)
        silent_rate  = row['silent_count'] / total
        ack_rate     = row['ack_count'] / total
        current      = row['confidence_score']

        # Silent retcons pull confidence down significantly
        # Acknowledged retcons are slightly positive (editorial accountability)
        # Clean record slowly recovers
        adjustment = -silent_rate * 0.3 + (1.0 - silent_rate) * 0.02 + ack_rate * 0.01
        new_confidence = max(0.1, min(0.99, current + adjustment))

        cur.execute(
            "UPDATE sources SET confidence_score = %s WHERE id = %s",
            (new_confidence, source_id)
        )


# ---------------------------------------------------------------------------
# FAISS similarity search
# ---------------------------------------------------------------------------

_faiss_index = None

def get_faiss():
    global _faiss_index
    if _faiss_index is not None:
        return _faiss_index
    if os.path.exists(FAISS_PATH):
        _faiss_index = faiss.read_index(FAISS_PATH)
    return _faiss_index


def get_embedding_for_faiss_id(faiss_id: int) -> Optional[np.ndarray]:
    """Reconstruct embedding vector from FAISS index by internal ID."""
    index = get_faiss()
    if index is None or faiss_id >= index.ntotal:
        return None
    vec = np.zeros((1, index.d), dtype=np.float32)
    index.reconstruct(faiss_id, vec[0])
    return vec[0]


def find_similar_claims(faiss_id: int, candidate_faiss_ids: list[int],
                        top_k: int = 5) -> list[tuple[int, float]]:
    """
    Find which candidate claims are most similar to the query claim.
    Returns list of (faiss_id, cosine_similarity) sorted by similarity desc.
    """
    query_vec = get_embedding_for_faiss_id(faiss_id)
    if query_vec is None:
        return []

    results = []
    for cand_id in candidate_faiss_ids:
        cand_vec = get_embedding_for_faiss_id(cand_id)
        if cand_vec is None:
            continue
        sim = float(np.dot(query_vec, cand_vec))
        if sim >= SIMILARITY_THRESHOLD:
            results.append((cand_id, sim))

    return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]


# ---------------------------------------------------------------------------
# Main contradiction scan
# ---------------------------------------------------------------------------

def scan_new_claims(since_claim_id: int = 0, source_id: Optional[int] = None):
    """
    Scan claims newer than since_claim_id for contradictions with older claims
    from the same source. If source_id is given, only scan that source.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id, source_id, claim_text, faiss_id, topic_tags
                FROM claims
                WHERE id > %s AND faiss_id IS NOT NULL
            """
            params = [since_claim_id]
            if source_id is not None:
                query += " AND source_id = %s"
                params.append(source_id)
            query += " ORDER BY id ASC"
            cur.execute(query, params)
            new_claims = cur.fetchall()

    log.info(f"[contradict] Scanning {len(new_claims)} new claims for contradictions")
    flagged = 0

    for claim in new_claims:
        older = get_recent_claims_for_source(claim['source_id'], claim['id'])
        if not older:
            continue

        # Build faiss_id → claim mapping for older claims
        faiss_id_to_claim = {c['faiss_id']: c for c in older if c['faiss_id'] is not None}
        candidate_faiss_ids = list(faiss_id_to_claim.keys())

        # Find semantically similar older claims from same source
        similar = find_similar_claims(claim['faiss_id'], candidate_faiss_ids)

        conn = get_conn()
        try:
            for old_faiss_id, similarity in similar:
                old_claim = faiss_id_to_claim[old_faiss_id]
                with conn:
                    if contradiction_already_exists(conn, claim['id'], old_claim['id']):
                        continue

                result = classify_contradiction(old_claim['claim_text'], claim['claim_text'])
                relationship = result['relationship']

                # Only persist meaningful relationships
                if relationship in ('contradiction', 'retcon_silent', 'retcon_acknowledged'):
                    with conn:
                        insert_contradiction(
                            conn,
                            old_claim['id'], claim['id'],
                            relationship, result['confidence'],
                            result['source_acknowledged'],
                            claim.get('technique_class'),
                            result.get('reasoning', '')
                        )
                        update_source_retcon_stats(conn, claim['source_id'], relationship)
                    flagged += 1
                    log.info(f"  [{relationship}] source={claim['source_id']} "
                             f"claims={old_claim['id']}→{claim['id']} "
                             f"conf={result['confidence']:.2f}")
        finally:
            conn.close()

        # Refresh source confidence after processing each source's claims
        conn2 = get_conn()
        try:
            with conn2:
                update_source_confidence(conn2, claim['source_id'])
        finally:
            conn2.close()

    log.info(f"[contradict] Scan complete: {flagged} contradictions/retcons flagged")
    return flagged
