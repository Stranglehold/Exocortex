"""
silence.py — Silence detection via comparative completeness.

Detects what is NOT said by comparing element inventories across
ideologically distinct source clusters.

The founding case study: every outlet covered the Tisch/ISIS frame.
No outlet in any cluster addressed the Sunni/Shia doctrinal conflict
that makes "ISIS ties" and "Iran war target" mutually incoherent.
That's a silence. This engine finds silences.

Key implementation decision: element matching is SEMANTIC, not string equality.
LLMs extract the same element with different surface forms across articles.
We embed elements and cluster near-duplicates before comparing across clusters.
This fixes the false-negative problem that string set intersection would produce.
"""

import os
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
import psycopg2
import psycopg2.extras
from openai import OpenAI
from sentence_transformers import SentenceTransformer

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

DB_URL    = os.environ.get("OSS_DB_URL", "postgresql://oss_admin:oss_admin_dev_password@localhost:5433/oss")
LLM_URL   = os.environ.get("OSS_LLM_URL", "http://localhost:1234/v1")
from llm_config import get_llm_model as _get_llm_model
LLM_MODEL = _get_llm_model()
EMB_MODEL = os.environ.get("OSS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Two elements are treated as the same element if their embedding cosine >= this
ELEMENT_DEDUP_THRESHOLD = float(os.environ.get("OSS_ELEMENT_DEDUP_THRESHOLD", "0.82"))

# A silence is flagged if the element appears in >= this many clusters
# but is absent from >= 1 cluster
MIN_PRESENT_CLUSTERS = int(os.environ.get("OSS_SILENCE_MIN_PRESENT_CLUSTERS", "2"))

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

_embedder: Optional[SentenceTransformer] = None
_llm_client: Optional[OpenAI] = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMB_MODEL)
    return _embedder

def get_llm():
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(base_url=LLM_URL, api_key="local")
    return _llm_client

def embed_elements(texts: list[str]) -> np.ndarray:
    """Embed a list of element strings. Returns (N, 384) float32, normalized."""
    return get_embedder().encode(texts, normalize_embeddings=True, show_progress_bar=False)


# ---------------------------------------------------------------------------
# Element extraction
# ---------------------------------------------------------------------------

EXTRACT_SYSTEM = """You are a claim decomposition system. Extract the discrete factual elements contained in a news claim.

An element is a single piece of information:
- An entity (person, organization, place, concept)
- A relationship between entities
- An attribution ("X said Y")
- A quantitative fact
- A contextual background fact that gives the claim meaning

Rules:
- Return ONLY a JSON array of short strings (5-15 words each).
- Be specific. "ISIS ties" is an element. "terrorism" is not specific enough.
- Capture implicit context: if a claim mentions "ISIS ties + Iran war target",
  the doctrinal incompatibility between Sunni ISIS and Shia Iran IS an element
  — one that any complete account should include.
- Max 8 elements per claim. Prefer the most analytically significant ones.
- Return [] if no extractable elements.

Example:
Claim: "Commissioner Tisch stated the suspect had ISIS ties but no connection to Iran"
Elements: [
  "suspect alleged to have ISIS affiliation",
  "statement attributed to Commissioner Tisch",
  "suspect stated to have no Iran connection",
  "ISIS is a Sunni organization",
  "Iran-linked conflict involves Shia alignment",
  "Sunni-Shia doctrinal conflict between ISIS and Iran"
]"""

def extract_elements(claim_text: str) -> list[str]:
    """Extract discrete factual elements from a claim. Returns list of element strings."""
    try:
        resp = get_llm().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": EXTRACT_SYSTEM},
                {"role": "user", "content": claim_text}
            ],
            temperature=0.1,
            max_tokens=256,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        elements = json.loads(raw)
        if isinstance(elements, list):
            return [str(e).strip() for e in elements if str(e).strip()]
        return []
    except Exception as e:
        log.warning(f"Element extraction failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Semantic deduplication of element strings
# ---------------------------------------------------------------------------

def canonicalize_elements(all_elements: list[str]) -> dict[str, str]:
    """
    Given a flat list of element strings (potentially with surface-form variation),
    return a mapping from each element string → canonical representative string.

    Two elements are merged if their embedding cosine >= ELEMENT_DEDUP_THRESHOLD.
    The canonical form is the first representative seen (stable across runs
    because we process in insertion order).

    This is the fix for the string-matching false-negative problem:
    "suspect had ISIS ties" and "ISIS affiliation of suspect" both map to
    the same canonical element and will be recognized as present/absent
    in the same cluster correctly.
    """
    if not all_elements:
        return {}

    embeddings = embed_elements(all_elements)
    canonical_map: dict[str, str] = {}
    canonicals: list[str] = []
    canonical_embeddings: list[np.ndarray] = []

    for i, elem in enumerate(all_elements):
        vec = embeddings[i]
        matched = False
        for j, canon_vec in enumerate(canonical_embeddings):
            sim = float(np.dot(vec, canon_vec))
            if sim >= ELEMENT_DEDUP_THRESHOLD:
                canonical_map[elem] = canonicals[j]
                matched = True
                break
        if not matched:
            canonical_map[elem] = elem
            canonicals.append(elem)
            canonical_embeddings.append(vec)

    return canonical_map


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def get_recent_claims_for_topic(topic_tag: str, hours: int = 24) -> list[dict]:
    """Fetch claims for a topic within the time window, with source cluster info."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.claim_text, c.source_id, s.cluster, s.name AS source_name
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE %s = ANY(c.topic_tags)
                  AND c.extracted_at >= NOW() - INTERVAL '%s hours'
                ORDER BY c.extracted_at ASC
            """, (topic_tag, hours))
            return cur.fetchall()


def silence_already_exists(conn, topic_tag: str, element_canonical: str) -> bool:
    """Avoid re-inserting a silence that was already flagged recently."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM silence_flags
            WHERE topic_tag = %s AND element = %s
              AND first_detected >= NOW() - INTERVAL '48 hours'
            LIMIT 1
        """, (topic_tag, element_canonical))
        return cur.fetchone() is not None


def insert_silence_flag(conn, topic_tag: str, element: str,
                         element_embedding: np.ndarray,
                         present_source_ids: list[int], absent_source_ids: list[int],
                         present_clusters: list[str], absent_clusters: list[str]):
    emb_json = json.dumps(element_embedding.tolist())
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO silence_flags
                (topic_tag, element, element_embedding_json,
                 present_in_sources, absent_from_sources,
                 present_in_clusters, absent_from_clusters,
                 detection_method)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'comparative')
        """, (topic_tag, element, emb_json,
              present_source_ids, absent_source_ids,
              present_clusters, absent_clusters))


# ---------------------------------------------------------------------------
# Core silence detection
# ---------------------------------------------------------------------------

def detect_silence(topic_tag: str, time_window_hours: int = 24) -> list[dict]:
    """
    For a given topic, find elements present in some source clusters
    but absent from others.

    Method:
    1. Fetch all claims for this topic in the time window
    2. Extract elements from each claim via LLM
    3. Canonicalize elements semantically (dedup surface-form variations)
    4. Build cluster → set(canonical elements) inventory
    5. Find elements present in MIN_PRESENT_CLUSTERS+ but absent from 1+
    6. Persist to silence_flags, return summary

    The inverse-CRQA insight: where do two source clusters' coverage
    fail to pass through the same information space?
    """
    log.info(f"[silence] Detecting silences for topic={topic_tag} window={time_window_hours}h")

    claims = get_recent_claims_for_topic(topic_tag, hours=time_window_hours)
    if not claims:
        log.info(f"[silence] No claims found for topic={topic_tag}")
        return []

    log.info(f"[silence] {len(claims)} claims from {len(set(c['cluster'] for c in claims))} clusters")

    # Step 1: Extract elements per claim
    claim_elements: dict[int, list[str]] = {}
    for claim in claims:
        elements = extract_elements(claim['claim_text'])
        claim_elements[claim['id']] = elements

    # Step 2: Flatten all elements and canonicalize
    all_elements = [e for elems in claim_elements.values() for e in elems]
    if not all_elements:
        return []

    canonical_map = canonicalize_elements(all_elements)
    log.info(f"[silence] {len(all_elements)} raw elements → {len(set(canonical_map.values()))} canonical")

    # Step 3: Build cluster → set(canonical elements) and source tracking
    cluster_elements: dict[str, set[str]] = defaultdict(set)
    # canonical_element → {cluster → [source_ids]}
    element_cluster_sources: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))

    for claim in claims:
        cluster = claim['cluster']
        for raw_elem in claim_elements.get(claim['id'], []):
            canon = canonical_map.get(raw_elem, raw_elem)
            cluster_elements[cluster].add(canon)
            element_cluster_sources[canon][cluster].append(claim['source_id'])

    all_clusters = set(c['cluster'] for c in claims)
    all_canonical = set(canonical_map.values())

    # Step 4: Find silences
    silences = []
    conn = get_conn()

    try:
        for canon_elem in all_canonical:
            present_clusters = [c for c in all_clusters if canon_elem in cluster_elements.get(c, set())]
            absent_clusters  = [c for c in all_clusters if canon_elem not in cluster_elements.get(c, set())]

            if len(present_clusters) < MIN_PRESENT_CLUSTERS or len(absent_clusters) == 0:
                continue

            # Collect source IDs
            present_source_ids = list({
                sid
                for cl in present_clusters
                for sid in element_cluster_sources[canon_elem].get(cl, [])
            })
            absent_source_ids = list({
                claim['source_id']
                for claim in claims
                if claim['cluster'] in absent_clusters
            })

            with conn:
                if silence_already_exists(conn, topic_tag, canon_elem):
                    continue
                emb = embed_elements([canon_elem])[0]
                insert_silence_flag(
                    conn, topic_tag, canon_elem, emb,
                    present_source_ids, absent_source_ids,
                    present_clusters, absent_clusters
                )

            silence_entry = {
                'element': canon_elem,
                'present_in_clusters': present_clusters,
                'absent_from_clusters': absent_clusters,
                'present_source_count': len(present_source_ids),
                'absent_source_count': len(absent_source_ids),
            }
            silences.append(silence_entry)
            log.info(f"  [silence] '{canon_elem[:60]}' "
                     f"present={present_clusters} absent={absent_clusters}")

    finally:
        conn.close()

    log.info(f"[silence] {len(silences)} new silence flags for topic={topic_tag}")
    return silences


def run_silence_scan(time_window_hours: int = 24):
    """Run silence detection for all active topics."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT tag FROM topics WHERE active = TRUE")
            tags = [row['tag'] for row in cur.fetchall()]

    total = 0
    for tag in tags:
        try:
            silences = detect_silence(tag, time_window_hours=time_window_hours)
            total += len(silences)
        except Exception as e:
            log.error(f"Silence scan failed for topic={tag}: {e}")

    log.info(f"[silence] Scan complete: {total} total new silence flags")
    return total
