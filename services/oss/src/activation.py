"""
activation.py — Activation pattern detection for OSS.

Detects narrative spikes: the same claim pattern appearing simultaneously
across ideologically distinct source clusters within a narrow time window.

This is the emergent context management signature.
No coordinator required. Individual actors making locally reasonable
decisions produce a collectively managed information environment.
Detection signal: the same narrative frame appearing in left + center + right
+ wire within 72 minutes without any of them coordinating.

Algorithm:
1. Fetch recent claims grouped by topic and cluster
2. Embed all claims; cluster semantically similar ones into narrative patterns
3. For each pattern, compute cluster_spread (distinct clusters where it appeared)
4. Patterns with cluster_spread >= threshold within a time window = activation
5. Persist to activation_patterns table
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
from sentence_transformers import SentenceTransformer

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

DB_URL    = os.environ.get("OSS_DB_URL", "postgresql://oss_admin:oss_admin_dev_password@localhost:5433/oss")
EMB_MODEL = os.environ.get("OSS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Claims are considered the same narrative pattern if cosine >= this
PATTERN_CLUSTER_THRESHOLD = float(os.environ.get("OSS_ACTIVATION_CLUSTER_THRESHOLD", "0.75"))

# Minimum distinct clusters for an activation flag
MIN_CLUSTER_SPREAD = int(os.environ.get("OSS_ACTIVATION_MIN_CLUSTER_SPREAD", "3"))

# Time window in minutes for a spike to count
ACTIVATION_WINDOW_MINUTES = int(os.environ.get("OSS_ACTIVATION_WINDOW_MINUTES", "180"))


# ---------------------------------------------------------------------------
# Embedder
# ---------------------------------------------------------------------------

_embedder: Optional[SentenceTransformer] = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMB_MODEL)
    return _embedder

def embed(texts: list[str]) -> np.ndarray:
    return get_embedder().encode(texts, normalize_embeddings=True, show_progress_bar=False)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def get_recent_claims_with_timestamps(topic_tag: str,
                                       hours: int = 48) -> list[dict]:
    """Claims for a topic with source cluster and timestamp."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.claim_text, c.source_id, c.extracted_at,
                       c.published_at, c.technique_class,
                       s.cluster, s.name AS source_name
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE %s = ANY(c.topic_tags)
                  AND c.extracted_at >= NOW() - INTERVAL '%s hours'
                ORDER BY COALESCE(c.published_at, c.extracted_at) ASC
            """, (topic_tag, hours))
            return cur.fetchall()


def activation_already_exists(conn, topic_tag: str, pattern_canonical: str,
                               window_minutes: int) -> bool:
    """Avoid duplicating a recently-detected activation pattern."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM activation_patterns
            WHERE topic_tag = %s
              AND claim_pattern = %s
              AND flagged_at >= NOW() - INTERVAL '%s minutes'
            LIMIT 1
        """, (topic_tag, pattern_canonical, window_minutes * 2))
        return cur.fetchone() is not None


def insert_activation_pattern(conn, topic_tag: str, canonical_pattern: str,
                               source_ids: list[int], clusters: list[str],
                               first_seen: datetime, last_seen: datetime,
                               window_minutes: int, claim_count: int,
                               technique_class: str = 'emergent'):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO activation_patterns
                (topic_tag, claim_pattern, source_ids, cluster_spread,
                 clusters_present, first_seen, last_seen, window_minutes,
                 claim_count, technique_class)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (topic_tag, canonical_pattern, source_ids, len(clusters),
              clusters, first_seen, last_seen, window_minutes,
              claim_count, technique_class))


# ---------------------------------------------------------------------------
# Narrative pattern clustering
# ---------------------------------------------------------------------------

def cluster_claims_into_patterns(claims: list[dict]) -> list[dict]:
    """
    Group claims by semantic similarity into narrative patterns.

    Each pattern has:
    - canonical_text: representative claim string (highest centrality)
    - member_claims: list of claims in this cluster
    - centroid: mean embedding of members

    Returns list of pattern dicts.
    """
    if not claims:
        return []

    texts = [c['claim_text'] for c in claims]
    embeddings = embed(texts)

    # Greedy agglomerative clustering: build clusters in order
    # Each claim either joins an existing cluster (if cosine >= threshold)
    # or seeds a new one
    clusters: list[dict] = []  # list of {centroid, texts, claims, embedding_sum, count}

    for i, claim in enumerate(claims):
        vec = embeddings[i]
        best_cluster = None
        best_sim = -1.0

        for clust in clusters:
            sim = float(np.dot(vec, clust['centroid']))
            if sim > best_sim:
                best_sim = sim
                best_cluster = clust

        if best_cluster is not None and best_sim >= PATTERN_CLUSTER_THRESHOLD:
            best_cluster['claims'].append(claim)
            best_cluster['embedding_sum'] += vec
            best_cluster['count'] += 1
            # Recompute normalized centroid
            new_centroid = best_cluster['embedding_sum'] / best_cluster['count']
            norm = np.linalg.norm(new_centroid)
            best_cluster['centroid'] = new_centroid / max(norm, 1e-9)
        else:
            clusters.append({
                'centroid': vec.copy(),
                'embedding_sum': vec.copy(),
                'count': 1,
                'claims': [claim],
            })

    # Convert to output format
    patterns = []
    for clust in clusters:
        member_claims = clust['claims']
        # Pick canonical text: the claim whose embedding is closest to centroid
        member_vecs = embed([c['claim_text'] for c in member_claims])
        sims_to_centroid = [float(np.dot(member_vecs[i], clust['centroid']))
                            for i in range(len(member_claims))]
        canonical_idx = int(np.argmax(sims_to_centroid))
        patterns.append({
            'canonical_text': member_claims[canonical_idx]['claim_text'],
            'claims': member_claims,
            'centroid': clust['centroid'],
            'count': clust['count'],
        })

    return patterns


# ---------------------------------------------------------------------------
# Core activation detection
# ---------------------------------------------------------------------------

def detect_activation(topic_tag: str, time_window_hours: int = 48) -> list[dict]:
    """
    Detect narrative spikes for a topic.

    A spike is a narrative pattern that appears in MIN_CLUSTER_SPREAD+ distinct
    ideological clusters within ACTIVATION_WINDOW_MINUTES minutes.
    """
    log.info(f"[activation] Scanning topic={topic_tag} window={time_window_hours}h")

    claims = get_recent_claims_with_timestamps(topic_tag, hours=time_window_hours)
    if len(claims) < MIN_CLUSTER_SPREAD:
        return []

    patterns = cluster_claims_into_patterns(claims)
    log.info(f"[activation] {len(claims)} claims → {len(patterns)} narrative patterns")

    flagged = []
    conn = get_conn()

    try:
        for pattern in patterns:
            member_claims = pattern['claims']

            # Get time range for this pattern's members
            timestamps = []
            for c in member_claims:
                ts = c.get('published_at') or c.get('extracted_at')
                if ts:
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts)
                    timestamps.append(ts)

            if not timestamps:
                continue

            first_seen = min(timestamps)
            last_seen  = max(timestamps)
            span_minutes = (last_seen - first_seen).total_seconds() / 60.0

            if span_minutes > ACTIVATION_WINDOW_MINUTES:
                continue  # Pattern spans too wide a window — gradual spread, not a spike

            # Measure cluster spread within the time window
            clusters_in_window = list({c['cluster'] for c in member_claims})
            source_ids_in_window = list({c['source_id'] for c in member_claims})

            if len(clusters_in_window) < MIN_CLUSTER_SPREAD:
                continue

            canonical = pattern['canonical_text']

            with conn:
                if activation_already_exists(conn, topic_tag, canonical, ACTIVATION_WINDOW_MINUTES):
                    continue
                insert_activation_pattern(
                    conn, topic_tag, canonical,
                    source_ids_in_window, clusters_in_window,
                    first_seen, last_seen,
                    int(span_minutes), len(member_claims),
                    technique_class='emergent'
                )

            entry = {
                'canonical_pattern': canonical,
                'cluster_spread': len(clusters_in_window),
                'clusters': clusters_in_window,
                'claim_count': len(member_claims),
                'window_minutes': int(span_minutes),
                'first_seen': first_seen.isoformat(),
            }
            flagged.append(entry)
            log.info(f"  [activation] '{canonical[:70]}' "
                     f"spread={len(clusters_in_window)} clusters={clusters_in_window} "
                     f"window={int(span_minutes)}m claims={len(member_claims)}")

    finally:
        conn.close()

    log.info(f"[activation] {len(flagged)} activation patterns flagged for topic={topic_tag}")
    return flagged


def run_activation_scan(time_window_hours: int = 48):
    """Run activation detection for all active topics."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT tag FROM topics WHERE active = TRUE")
            tags = [row['tag'] for row in cur.fetchall()]

    total = 0
    for tag in tags:
        try:
            results = detect_activation(tag, time_window_hours=time_window_hours)
            total += len(results)
        except Exception as e:
            log.error(f"Activation scan failed for topic={tag}: {e}")

    log.info(f"[activation] Scan complete: {total} total patterns flagged")
    return total
