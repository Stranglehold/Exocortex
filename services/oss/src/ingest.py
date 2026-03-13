"""
ingest.py — RSS ingestion pipeline for OSS.

Fetches RSS feeds, extracts claims via LLM, embeds them, deduplicates
against FAISS index, and persists to PostgreSQL.

Runs on a schedule (OSS_INGEST_INTERVAL_MINUTES). Also callable directly
for retroactive ingestion of archived articles.
"""

import os
import json
import time
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

import feedparser
import psycopg2
import psycopg2.extras
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='[INGEST] %(message)s', force=True)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DB_URL        = os.environ.get("OSS_DB_URL", "postgresql://oss_admin:oss_admin_dev_password@localhost:5433/oss")
LLM_URL       = os.environ.get("OSS_LLM_URL", "http://localhost:1234/v1")
LLM_MODEL     = os.environ.get("OSS_LLM_MODEL", "qwen2.5-14b-instruct")
EMB_MODEL     = os.environ.get("OSS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
FAISS_PATH    = os.environ.get("OSS_FAISS_PATH", "/app/data/faiss/claims.index")
DEDUP_THRESHOLD = float(os.environ.get("OSS_DEDUP_THRESHOLD", "0.95"))

# ---------------------------------------------------------------------------
# LLM client (OpenAI-compatible, points to LM Studio)
# ---------------------------------------------------------------------------

_llm_client: Optional[OpenAI] = None

def get_llm():
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(base_url=LLM_URL, api_key="local")
    return _llm_client


# ---------------------------------------------------------------------------
# Embedding model
# ---------------------------------------------------------------------------

_embedder: Optional[SentenceTransformer] = None

def get_embedder():
    global _embedder
    if _embedder is None:
        log.info(f"Loading embedding model: {EMB_MODEL}")
        _embedder = SentenceTransformer(EMB_MODEL)
    return _embedder


def embed(texts: list[str]) -> np.ndarray:
    """Return (N, 384) float32 embeddings."""
    return get_embedder().encode(texts, normalize_embeddings=True, show_progress_bar=False)


# ---------------------------------------------------------------------------
# FAISS index
# ---------------------------------------------------------------------------

_faiss_index: Optional[faiss.IndexFlatIP] = None

def get_faiss():
    global _faiss_index
    if _faiss_index is not None:
        return _faiss_index
    dim = 384
    if os.path.exists(FAISS_PATH):
        log.info(f"Loading FAISS index from {FAISS_PATH}")
        _faiss_index = faiss.read_index(FAISS_PATH)
    else:
        log.info("Creating new FAISS index")
        os.makedirs(os.path.dirname(FAISS_PATH), exist_ok=True)
        _faiss_index = faiss.IndexFlatIP(dim)
    return _faiss_index


def save_faiss():
    if _faiss_index is not None:
        faiss.write_index(_faiss_index, FAISS_PATH)


def is_duplicate(vec: np.ndarray) -> bool:
    """True if a near-identical claim already exists in the index."""
    index = get_faiss()
    if index.ntotal == 0:
        return False
    vec = vec.reshape(1, -1).astype(np.float32)
    D, _ = index.search(vec, 1)
    return float(D[0][0]) >= DEDUP_THRESHOLD


def add_to_faiss(vec: np.ndarray) -> int:
    """Add embedding to index; return the new FAISS id (0-indexed)."""
    index = get_faiss()
    faiss_id = index.ntotal
    index.add(vec.reshape(1, -1).astype(np.float32))
    return faiss_id


# ---------------------------------------------------------------------------
# Claim extraction via LLM
# ---------------------------------------------------------------------------

EXTRACT_SYSTEM = """You are a claim extraction system. From a news article excerpt, extract discrete factual claims.

A claim is a single assertable statement: an event, a causal attribution, a quantitative fact, an official statement, or a named entity relationship.

Rules:
- Return ONLY a JSON array of strings. No preamble, no explanation.
- Each string is one complete claim in third-person declarative form.
- Omit opinion, speculation, and editorial framing.
- Max 8 claims per excerpt. Prefer the most factually specific ones.
- If the excerpt contains no extractable factual claims, return [].

Example input: "NYPD Commissioner Tisch said the suspect had ISIS ties but no connection to the Iran war"
Example output: ["Commissioner Tisch stated the suspect had ISIS ties.", "Commissioner Tisch stated the suspect had no connection to the Iran war.", "NYPD is the attributing agency."]"""

def extract_claims(article_text: str, article_title: str) -> list[str]:
    """Call LLM to extract discrete claims from article text. Returns list of claim strings."""
    try:
        resp = get_llm().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": EXTRACT_SYSTEM},
                {"role": "user", "content": f"Title: {article_title}\n\nText: {article_text[:2000]}"}
            ],
            temperature=0.1,
            max_tokens=512,
        )
        raw = resp.choices[0].message.content.strip()
        # Robust parse: handle markdown code fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        claims = json.loads(raw)
        if isinstance(claims, list):
            return [str(c).strip() for c in claims if str(c).strip()]
        return []
    except Exception as e:
        log.warning(f"Claim extraction failed: {e}")
        return []


TECHNIQUE_SYSTEM = """Classify a news claim into one manipulation technique category.

Categories:
- presuasion: Claim primes emotional/identity context before the analytical question is asked (Cialdini pre-suasion pattern).
- fracture: Claim amplifies an existing social division. Goal is division, not belief adoption.
- emergent: Claim is part of a coordinated narrative that appears simultaneously across multiple outlets without explicit coordination.
- direct: Claim is a direct factual assertion with no apparent framing manipulation.
- none: No manipulation technique evident.

Return ONLY one word from the category list. No explanation."""

def classify_technique(claim: str) -> str:
    """Classify which manipulation technique a claim matches."""
    try:
        resp = get_llm().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": TECHNIQUE_SYSTEM},
                {"role": "user", "content": claim}
            ],
            temperature=0.0,
            max_tokens=10,
        )
        result = resp.choices[0].message.content.strip().lower()
        valid = {'presuasion', 'fracture', 'emergent', 'direct', 'none'}
        return result if result in valid else 'none'
    except Exception:
        return 'none'


TOPIC_SYSTEM = """Given a news claim, return the most relevant topic tag(s) from the provided list.

Return ONLY a JSON array of tag strings from the provided list. Return [] if none match.
Do not invent new tags."""

def assign_topics(claim: str, available_tags: list[str]) -> list[str]:
    """Match claim to known topic tags. Returns list of matching tags."""
    if not available_tags:
        return []
    try:
        tag_list = ", ".join(available_tags)
        resp = get_llm().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": TOPIC_SYSTEM},
                {"role": "user", "content": f"Available tags: [{tag_list}]\n\nClaim: {claim}"}
            ],
            temperature=0.0,
            max_tokens=64,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        tags = json.loads(raw)
        if isinstance(tags, list):
            return [t for t in tags if t in available_tags]
        return []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def get_all_sources() -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM sources ORDER BY id")
            return cur.fetchall()


def get_active_topics() -> list[str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT tag FROM topics WHERE active = TRUE")
            return [row['tag'] for row in cur.fetchall()]


def insert_claim(conn, source_id: int, raw_text: str, claim_text: str,
                 article_url: str, article_title: str, topic_tags: list[str],
                 technique_class: str, published_at: Optional[datetime],
                 faiss_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO claims
                (source_id, raw_text, claim_text, article_url, article_title,
                 topic_tags, technique_class, published_at, faiss_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (source_id, raw_text, claim_text, article_url, article_title,
              topic_tags, technique_class, published_at, faiss_id))
        row = cur.fetchone()
        cur.execute("UPDATE sources SET total_claims = total_claims + 1 WHERE id = %s", (source_id,))
        return row['id']


def update_topic_last_active(conn, tags: list[str]):
    if not tags:
        return
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE topics SET last_active = NOW(), claim_count = claim_count + 1
            WHERE tag = ANY(%s)
        """, (tags,))


# ---------------------------------------------------------------------------
# RSS fetch
# ---------------------------------------------------------------------------

def parse_published(entry) -> Optional[datetime]:
    """Parse feedparser published_parsed into a UTC datetime."""
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except Exception:
        pass
    return None


def fetch_feed(source: dict, available_topics: list[str]) -> int:
    """
    Fetch one RSS source, extract claims, embed, dedup, persist.
    Returns count of new claims inserted.
    """
    source_id = source['id']
    feed_url = source['url']
    log.info(f"Fetching {source['name']} ({feed_url})")

    try:
        feed = feedparser.parse(feed_url)
    except Exception as e:
        log.warning(f"Feed fetch failed for {source['name']}: {e}")
        return 0

    inserted = 0
    conn = get_conn()

    try:
        for entry in feed.entries[:20]:  # cap per-feed article count
            article_url   = getattr(entry, 'link', '')
            article_title = getattr(entry, 'title', '')
            raw_text      = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            published_at  = parse_published(entry)

            if not raw_text or not article_url:
                continue

            # Extract claims via LLM
            claims = extract_claims(raw_text, article_title)
            if not claims:
                continue

            for claim_text in claims:
                # Embed and dedup
                vec = embed([claim_text])[0]
                if is_duplicate(vec):
                    continue

                faiss_id        = add_to_faiss(vec)
                technique_class = classify_technique(claim_text)
                topic_tags      = assign_topics(claim_text, available_topics)

                with conn:
                    insert_claim(
                        conn, source_id, raw_text, claim_text, article_url,
                        article_title, topic_tags, technique_class,
                        published_at, faiss_id
                    )
                    update_topic_last_active(conn, topic_tags)

                inserted += 1

        save_faiss()
        log.info(f"  {source['name']}: {inserted} new claims")
        return inserted

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Main scheduler loop
# ---------------------------------------------------------------------------

def run_once():
    """Single ingestion pass across all sources."""
    sources = get_all_sources()
    topics  = get_active_topics()
    log.info(f"Ingestion pass: {len(sources)} sources, {len(topics)} active topics")
    total = 0
    for source in sources:
        try:
            total += fetch_feed(source, topics)
        except Exception as e:
            log.error(f"Source {source['name']} failed: {e}")
    log.info(f"Pass complete: {total} new claims total")
    return total


def run_scheduler():
    interval_minutes = int(os.environ.get("OSS_INGEST_INTERVAL_MINUTES", "30"))
    log.info(f"Ingestion scheduler starting (interval={interval_minutes}m)")
    while True:
        try:
            run_once()
        except Exception as e:
            log.error(f"Ingestion pass error: {e}")
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    run_scheduler()
