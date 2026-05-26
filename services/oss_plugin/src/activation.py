"""
activation.py — Narrative activation (coordinated spike) detection.

Detects when the same claim pattern appears across ideologically distinct
source clusters within a short time window — a signature of coordinated
narrative injection.

Threshold: ≥3 distinct clusters, within 4 hours, embedding cosine ≥ 0.85.
"""
import logging
from datetime import datetime, timezone, timedelta

from .db import jloads, jdumps

log = logging.getLogger("[ACTIVATION]")

_ACTIVATION_THRESHOLD   = 0.85   # cosine similarity to treat as "same pattern"
_CLUSTER_MINIMUM        = 3      # distinct clusters required
_WINDOW_HOURS           = 4      # time window in hours
_DISTINCT_CLUSTERS      = {"left", "right", "center", "international", "independent", "wire"}


# ---------------------------------------------------------------------------
# Embedding helper (standalone)
# ---------------------------------------------------------------------------

def _embed(texts: list):
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        m = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        return m.encode(texts, normalize_embeddings=True)
    except Exception as e:
        log.warning(f"_embed failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Activation scan
# ---------------------------------------------------------------------------

def run_activation_scan(conn, topic_tag: str) -> int:
    """
    Look at claims in the last 24 hours on topic_tag.
    If the same claim pattern (cosine ≥ 0.85) appears in 3+ distinct clusters
    within a 4-hour window, insert an activation_pattern record.
    Returns count of new patterns inserted.
    """
    inserted = 0
    try:
        cur = conn.cursor()
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

        cur.execute("""
            SELECT c.id, c.claim_text, c.extracted_at, s.cluster, s.id AS source_id
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            WHERE EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value=?)
              AND c.trust_level IN ('STAGED','PROMOTED')
              AND c.extracted_at >= ?
              AND s.cluster IN ('left','right','center','international','independent','wire')
            ORDER BY c.extracted_at
        """, (topic_tag, cutoff))
        rows = [dict(r) for r in cur.fetchall()]

        if len(rows) < _CLUSTER_MINIMUM:
            return 0

        # Embed all claim texts once
        texts = [r["claim_text"] for r in rows]
        vecs = _embed(texts)
        if vecs is None:
            return 0

        import numpy as np  # noqa: PLC0415

        processed_seeds = set()

        for i, seed in enumerate(rows):
            if i in processed_seeds:
                continue

            seed_time = _parse_time(seed["extracted_at"])
            if seed_time is None:
                continue

            window_end = seed_time + timedelta(hours=_WINDOW_HOURS)

            matching_claims = [seed]
            clusters_seen   = {seed["cluster"]}
            source_ids_seen  = {seed["source_id"]}

            for j, candidate in enumerate(rows):
                if j == i or j in processed_seeds:
                    continue

                cand_time = _parse_time(candidate["extracted_at"])
                if cand_time is None or cand_time > window_end:
                    continue

                # Already same cluster — adds breadth but not cluster count
                if candidate["cluster"] in clusters_seen:
                    # Still include in matching_claims for count, but don't re-flag cluster
                    cosine = float(np.dot(vecs[i], vecs[j]))
                    if cosine >= _ACTIVATION_THRESHOLD:
                        matching_claims.append(candidate)
                        source_ids_seen.add(candidate["source_id"])
                    continue

                cosine = float(np.dot(vecs[i], vecs[j]))
                if cosine >= _ACTIVATION_THRESHOLD:
                    matching_claims.append(candidate)
                    clusters_seen.add(candidate["cluster"])
                    source_ids_seen.add(candidate["source_id"])

            if len(clusters_seen) < _CLUSTER_MINIMUM:
                continue

            # Check if this pattern already recorded for this window
            cur.execute("""
                SELECT id FROM activation_patterns
                WHERE topic_tag=?
                  AND claim_pattern=?
                  AND flagged_at >= datetime('now', '-24 hours')
            """, (topic_tag, seed["claim_text"][:500]))
            if cur.fetchone():
                processed_seeds.add(i)
                continue

            times = [m["extracted_at"] for m in matching_claims]
            try:
                window_minutes = int(
                    (
                        _parse_time(max(times)) - _parse_time(min(times))
                    ).total_seconds() / 60
                ) if len(times) > 1 else 0
            except Exception:
                window_minutes = 0

            try:
                conn.execute("""
                    INSERT INTO activation_patterns
                        (topic_tag, claim_pattern, source_ids, cluster_spread,
                         clusters_present, first_seen, last_seen,
                         window_minutes, claim_count, technique_class)
                    VALUES (?,?,?,?,?,?,?,?,?,'emergent')
                """, (
                    topic_tag,
                    seed["claim_text"][:500],
                    jdumps(list(source_ids_seen)),
                    len(clusters_seen),
                    jdumps(list(clusters_seen)),
                    min(times),
                    max(times),
                    window_minutes,
                    len(matching_claims),
                ))
                conn.commit()
                inserted += 1
                log.info(
                    f"Activation pattern detected: topic={topic_tag}, "
                    f"clusters={len(clusters_seen)}, claims={len(matching_claims)}, "
                    f"window={window_minutes}m"
                )
            except Exception as e:
                log.warning(f"Insert activation_pattern failed: {e}")

            # Mark participating claims so we don't re-seed from them.
            # matching_claims (incl. the seed) holds the participating claim rows;
            # key off claim id, NOT the source-id set (different namespaces).
            matching_ids = {c["id"] for c in matching_claims}
            for k, m in enumerate(rows):
                if m["id"] in matching_ids:
                    processed_seeds.add(k)

    except Exception as e:
        log.warning(f"run_activation_scan failed for topic={topic_tag}: {e}")

    return inserted


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def get_activation_patterns(conn, topic_tag: str, since: str = None) -> list:
    """Return activation patterns for a topic, newest first."""
    try:
        cur = conn.cursor()
        params: list = [topic_tag]
        since_clause = ""
        if since:
            since_clause = "AND flagged_at >= ?"
            params.append(since)
        cur.execute(
            f"SELECT * FROM activation_patterns WHERE topic_tag=? {since_clause} "
            f"ORDER BY id DESC",
            params,
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_activation_patterns failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_time(ts: str):
    """Parse an ISO timestamp string, return datetime or None."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None
