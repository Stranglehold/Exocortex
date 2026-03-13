"""
source_intel.py — Source network topology for OSS.

Maintains source_network_edges — the map of amplification, coordination,
and cluster relationships between sources.

Required by the contamination cascade for independent_of_source verification.
Cannot be descoped without breaking cascade precision.
See: COGNITIVE_DEFENSE_SYSTEM_v2.md — dependency graph.

Phase 1:  Manual edge registration. Cluster membership seeded from schema.
Phase 2+: Automated topology detection from RSS cross-citation patterns
          and social media amplification signals.
"""

import os
import logging
from typing import Optional

import psycopg2
import psycopg2.extras

import audit

log = logging.getLogger(__name__)

DB_URL = os.environ.get(
    "OSS_DB_URL",
    "postgresql://oss_app:oss_app_dev_password@localhost:5433/oss"
)

VALID_RELATIONSHIP_TYPES = frozenset(
    ("amplifies", "is_amplified_by", "mutual_engagement", "cluster_member")
)


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def register_edge(
    source_id: int,
    connected_source_id: int,
    relationship_type: str,
    weight: float = 1.0,
    session_id=None,
) -> dict:
    """
    Register an observed network edge between two sources.

    If the edge already exists, increments observation_count and updates
    last_confirmed — treating the new observation as additional evidence.

    Args:
        source_id:            Source initiating the relationship
        connected_source_id:  Source being related to
        relationship_type:    amplifies | is_amplified_by | mutual_engagement | cluster_member
        weight:               Relationship strength (0.0–1.0)
        session_id:           UUID for audit trail

    Returns:
        dict with edge_id, created (bool), observation_count

    Raises:
        ValueError: on invalid relationship_type or self-edge
    """
    if relationship_type not in VALID_RELATIONSHIP_TYPES:
        raise ValueError(
            f"Invalid relationship_type: {relationship_type!r}. "
            f"Must be one of: {sorted(VALID_RELATIONSHIP_TYPES)}"
        )
    if source_id == connected_source_id:
        raise ValueError("A source cannot have a network edge to itself")

    import uuid as _uuid
    sid = session_id or _uuid.uuid4()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO source_network_edges
                    (source_id, connected_source_id, relationship_type, weight)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source_id, connected_source_id, relationship_type)
                DO UPDATE SET
                    last_confirmed = NOW(),
                    observation_count = source_network_edges.observation_count + 1,
                    weight = EXCLUDED.weight
                RETURNING id, observation_count, (xmax = 0) AS created
                """,
                (source_id, connected_source_id, relationship_type, weight),
            )
            row = cur.fetchone()

    created = row["created"]
    audit.log_event(
        session_id=sid,
        event_type="source_edge_registered",
        actor="analyst",
        action=(
            f"{'Created' if created else 'Confirmed'} edge: "
            f"source {source_id} --{relationship_type}--> source {connected_source_id} "
            f"(weight={weight:.2f})"
        ),
        data_accessed={
            "source_id": source_id,
            "connected_source_id": connected_source_id,
            "relationship_type": relationship_type,
            "weight": weight,
            "observation_count": row["observation_count"],
        },
    )

    log.info(
        f"[SOURCE_INTEL] Edge {'created' if created else 'confirmed'}: "
        f"{source_id} --{relationship_type}--> {connected_source_id} "
        f"(weight={weight:.2f}, obs={row['observation_count']})"
    )

    return {
        "edge_id": row["id"],
        "source_id": source_id,
        "connected_source_id": connected_source_id,
        "relationship_type": relationship_type,
        "weight": weight,
        "created": created,
        "observation_count": row["observation_count"],
    }


def sources_are_connected(source_id: int, connected_source_id: int) -> bool:
    """
    True if the two sources have any direct edge relationship in either direction.
    Used by the contamination cascade for independence verification.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM source_network_edges
                WHERE (source_id = %s AND connected_source_id = %s)
                   OR (source_id = %s AND connected_source_id = %s)
                LIMIT 1
                """,
                (source_id, connected_source_id, connected_source_id, source_id),
            )
            return cur.fetchone() is not None


def sources_in_same_cluster(source_id: int, connected_source_id: int) -> bool:
    """
    True if the two sources share cluster membership via cluster_member edges.
    Used by the contamination cascade for independence verification.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM source_network_edges
                WHERE relationship_type = 'cluster_member'
                  AND (
                    (source_id = %s AND connected_source_id = %s)
                    OR (source_id = %s AND connected_source_id = %s)
                  )
                LIMIT 1
                """,
                (source_id, connected_source_id, connected_source_id, source_id),
            )
            return cur.fetchone() is not None


def get_network_topology(source_id: Optional[int] = None) -> list:
    """
    Return current network topology.

    Args:
        source_id: If provided, return only edges involving this source.

    Returns:
        List of edge dicts with source/connected names, cluster, relationship, weight.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT
                    sne.id, sne.relationship_type, sne.weight,
                    sne.first_observed, sne.last_confirmed, sne.observation_count,
                    sa.id AS source_id, sa.name AS source_name, sa.cluster AS source_cluster,
                    sb.id AS connected_source_id,
                    sb.name AS connected_source_name, sb.cluster AS connected_cluster
                FROM source_network_edges sne
                JOIN sources sa ON sa.id = sne.source_id
                JOIN sources sb ON sb.id = sne.connected_source_id
            """
            params: list = []
            if source_id is not None:
                query += " WHERE sne.source_id = %s OR sne.connected_source_id = %s"
                params.extend([source_id, source_id])
            query += " ORDER BY sne.observation_count DESC, sa.name, sne.relationship_type"
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
