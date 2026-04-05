"""
source_intel.py — Source network topology.

Tracks relationships between sources (amplification, cluster membership,
coordination patterns). Provides graph queries for influence chain analysis.
"""
import logging
from datetime import datetime, timezone

from .db import jloads, jdumps

log = logging.getLogger("[SOURCE_INTEL]")


def register_edge(conn, source_id: int, connected_id: int,
                  relationship_type: str, weight: float = 1.0) -> dict:
    """
    Upsert a directed edge between two sources.
    If the edge already exists, increment observation_count, update last_confirmed
    and weight (take the average). Returns the edge row.
    """
    try:
        weight = max(0.0, min(1.0, float(weight)))
        now = datetime.now(timezone.utc).isoformat()

        cur = conn.cursor()
        # Try to insert; if duplicate, update instead
        cur.execute("""
            INSERT INTO source_network_edges
                (source_id, connected_source_id, relationship_type, weight,
                 first_observed, last_confirmed, observation_count)
            VALUES (?,?,?,?,?,?,1)
            ON CONFLICT(source_id, connected_source_id, relationship_type)
            DO UPDATE SET
                observation_count = observation_count + 1,
                last_confirmed    = excluded.last_confirmed,
                weight            = (weight + excluded.weight) / 2.0
        """, (source_id, connected_id, relationship_type, weight, now, now))
        conn.commit()

        cur.execute("""
            SELECT * FROM source_network_edges
            WHERE source_id=? AND connected_source_id=? AND relationship_type=?
        """, (source_id, connected_id, relationship_type))
        row = cur.fetchone()
        return dict(row) if row else {}
    except Exception as e:
        log.warning(f"register_edge failed: {e}")
        raise


def get_network(conn, source_id: int) -> dict:
    """
    Return the immediate network around a source:
      edges         — all outgoing edges from source_id
      amplifiers    — sources that this source amplifies
      amplified_by  — sources that amplify this source
      cluster_members — sources in the same cluster
    """
    try:
        cur = conn.cursor()

        # All outgoing edges
        cur.execute("""
            SELECT sne.*, s.name AS connected_name, s.cluster AS connected_cluster
            FROM source_network_edges sne
            JOIN sources s ON s.id = sne.connected_source_id
            WHERE sne.source_id = ?
            ORDER BY sne.weight DESC
        """, (source_id,))
        edges = [dict(r) for r in cur.fetchall()]

        # Amplifiers (sources this one amplifies outbound)
        cur.execute("""
            SELECT s.id, s.name, s.cluster, sne.weight, sne.observation_count
            FROM source_network_edges sne
            JOIN sources s ON s.id = sne.connected_source_id
            WHERE sne.source_id = ? AND sne.relationship_type = 'amplifies'
            ORDER BY sne.weight DESC
        """, (source_id,))
        amplifiers = [dict(r) for r in cur.fetchall()]

        # Amplified-by (sources that amplify this one)
        cur.execute("""
            SELECT s.id, s.name, s.cluster, sne.weight, sne.observation_count
            FROM source_network_edges sne
            JOIN sources s ON s.id = sne.source_id
            WHERE sne.connected_source_id = ? AND sne.relationship_type = 'amplifies'
            ORDER BY sne.weight DESC
        """, (source_id,))
        amplified_by = [dict(r) for r in cur.fetchall()]

        # Cluster members (mutual_engagement or cluster_member)
        cur.execute("""
            SELECT s.id, s.name, s.cluster, sne.weight
            FROM source_network_edges sne
            JOIN sources s ON s.id = sne.connected_source_id
            WHERE sne.source_id = ?
              AND sne.relationship_type IN ('cluster_member', 'mutual_engagement')
            ORDER BY sne.weight DESC
        """, (source_id,))
        cluster_members = [dict(r) for r in cur.fetchall()]

        return {
            "edges": edges,
            "amplifiers": amplifiers,
            "amplified_by": amplified_by,
            "cluster_members": cluster_members,
        }
    except Exception as e:
        log.warning(f"get_network failed for source_id={source_id}: {e}")
        return {"edges": [], "amplifiers": [], "amplified_by": [], "cluster_members": []}


def detect_coordination(conn, topic_tag: str, since: str = None) -> list:
    """
    Find sources that posted the same claim pattern in a short time window.
    Returns list of coordination candidate groups — each is a dict with:
      claim_pattern, source_ids, clusters, window_start, window_end, source_count
    """
    try:
        cur = conn.cursor()
        params: list = []

        # Base: claims on this topic
        since_clause = ""
        if since:
            since_clause = "AND c.extracted_at >= ?"
            params.append(since)

        cur.execute(f"""
            SELECT c.id, c.claim_text, c.source_id, c.extracted_at,
                   s.name AS source_name, s.cluster
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            WHERE EXISTS (
                SELECT 1 FROM json_each(c.topic_tags) WHERE value = ?
            )
            {since_clause}
            AND c.trust_level IN ('STAGED','PROMOTED')
            ORDER BY c.extracted_at
        """, [topic_tag] + params)
        rows = [dict(r) for r in cur.fetchall()]

        if not rows:
            return []

        # Python-side grouping: look for same-topic claims across distinct clusters
        # within a 4-hour window using simple pairwise text overlap
        groups = []
        processed = set()

        for i, row_a in enumerate(rows):
            if i in processed:
                continue
            matches = [row_a]
            clusters_seen = {row_a["cluster"]}
            sources_seen = {row_a["source_id"]}

            for j, row_b in enumerate(rows[i + 1:], start=i + 1):
                if j in processed:
                    continue
                # Within 4-hour window?
                try:
                    from datetime import datetime as _dt
                    ta = _dt.fromisoformat(row_a["extracted_at"].replace("Z", "+00:00"))
                    tb = _dt.fromisoformat(row_b["extracted_at"].replace("Z", "+00:00"))
                    if abs((tb - ta).total_seconds()) > 4 * 3600:
                        continue
                except Exception:
                    continue

                # Simple overlap heuristic: share ≥3 words of 5+ chars
                words_a = {w for w in row_a["claim_text"].lower().split() if len(w) >= 5}
                words_b = {w for w in row_b["claim_text"].lower().split() if len(w) >= 5}
                overlap = words_a & words_b
                if len(overlap) >= 3 and row_b["cluster"] not in clusters_seen:
                    matches.append(row_b)
                    clusters_seen.add(row_b["cluster"])
                    sources_seen.add(row_b["source_id"])
                    processed.add(j)

            if len(clusters_seen) >= 2 and len(matches) >= 3:
                processed.add(i)
                times = [m["extracted_at"] for m in matches]
                groups.append({
                    "claim_pattern": row_a["claim_text"][:200],
                    "source_ids": list(sources_seen),
                    "source_names": [m["source_name"] for m in matches],
                    "clusters": list(clusters_seen),
                    "window_start": min(times),
                    "window_end": max(times),
                    "source_count": len(matches),
                })

        return groups
    except Exception as e:
        log.warning(f"detect_coordination failed for topic={topic_tag}: {e}")
        return []


def get_amplification_chain(conn, source_id: int, depth: int = 2) -> list:
    """
    Walk the amplification graph up to `depth` hops.
    Returns a flat list of edge dicts, deduplicated, ordered by depth.
    """
    try:
        visited_edges = set()
        result = []
        frontier = [source_id]

        for hop in range(depth):
            if not frontier:
                break
            next_frontier = []
            cur = conn.cursor()
            placeholders = ",".join("?" * len(frontier))
            cur.execute(f"""
                SELECT sne.source_id, sne.connected_source_id,
                       sne.relationship_type, sne.weight, sne.observation_count,
                       sa.name AS source_name, sb.name AS connected_name,
                       sa.cluster AS source_cluster, sb.cluster AS connected_cluster
                FROM source_network_edges sne
                JOIN sources sa ON sa.id = sne.source_id
                JOIN sources sb ON sb.id = sne.connected_source_id
                WHERE sne.source_id IN ({placeholders})
                  AND sne.relationship_type = 'amplifies'
            """, frontier)

            for row in cur.fetchall():
                edge_key = (row["source_id"], row["connected_source_id"])
                if edge_key not in visited_edges:
                    visited_edges.add(edge_key)
                    d = dict(row)
                    d["hop"] = hop + 1
                    result.append(d)
                    next_frontier.append(row["connected_source_id"])

            frontier = list(set(next_frontier) - {source_id})

        return result
    except Exception as e:
        log.warning(f"get_amplification_chain failed for source_id={source_id}: {e}")
        return []
