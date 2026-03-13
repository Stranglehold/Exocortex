"""
app.py — Counter-Patriots A2A query interface.

Six endpoints. Returns records, not assessments.
The analyst holds the conclusions.

The Curtis Rule is enforced here by the absence of certain endpoints:
  - No /api/suggest_framing
  - No /api/truth_score
  - No /api/counter_narrative
These endpoints do not exist. They cannot be called.

The Festinger Boundary is enforced here by analyst authentication:
  - /api/contradictions requires CP_ANALYST_TOKEN header
  - No public bulk export of contradiction data

Agent Zero integration:
  POST endpoints accept JSON, return JSON.
  Service announces itself on /api/health for A2A discovery.
  Port 7731.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Optional

import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify, abort, g

from ingest import run_once as run_ingestion
from contradict import scan_new_claims
from silence import run_silence_scan
from activation import run_activation_scan
import audit
import retcon_ledger
import source_intel

logging.basicConfig(level=logging.INFO, format='[APP] %(message)s', force=True)
log = logging.getLogger(__name__)

app = Flask(__name__)

DB_URL         = os.environ.get("CP_DB_URL", "postgresql://cds_app:cds_app_dev_password@localhost:5433/counter_patriots")
ANALYST_TOKEN  = os.environ.get("CP_ANALYST_TOKEN", "dev_analyst_token")
SERVICE_PORT   = int(os.environ.get("CP_PORT", "7731"))


# ---------------------------------------------------------------------------
# Per-request session ID for audit trail
# ---------------------------------------------------------------------------

@app.before_request
def assign_session_id():
    g.session_id = uuid.uuid4()


# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Auth decorator (Festinger Boundary)
# ---------------------------------------------------------------------------

def require_analyst_auth(f):
    """Restrict endpoint to analyst-authenticated callers.
    Contradiction ledger has no public access — Festinger Boundary enforcement."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Analyst-Token') or request.json.get('analyst_token', '')
        if token != ANALYST_TOKEN:
            abort(403, description="Analyst authentication required. Festinger Boundary.")
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------

def parse_since(data: dict) -> Optional[datetime]:
    since_str = data.get('since')
    if not since_str:
        return None
    try:
        dt = datetime.fromisoformat(since_str.replace('Z', '+00:00'))
        return dt
    except Exception:
        return None


def require_field(data: dict, field: str):
    if not data.get(field):
        abort(400, description=f"Missing required field: {field}")


# ---------------------------------------------------------------------------
# Endpoint: /api/health
# ---------------------------------------------------------------------------

@app.route('/api/health', methods=['GET'])
def health():
    """
    Service health for A2A discovery.
    Agent Zero uses this to verify the service is alive before querying.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE trust_level = 'STAGED')          AS staged_count,
                        COUNT(*) FILTER (WHERE trust_level = 'PROMOTED')         AS promoted_count,
                        COUNT(*) FILTER (WHERE trust_level = 'RETURNED_TO_STAGED') AS returned_count,
                        COUNT(*)                                                 AS total_count,
                        MAX(extracted_at)                                        AS last_ingestion
                    FROM claims
                """)
                counts = cur.fetchone()
                cur.execute("SELECT COUNT(*) AS n FROM sources")
                sources_count = cur.fetchone()['n']
                cur.execute("SELECT COUNT(*) AS n FROM source_network_edges")
                edge_count = cur.fetchone()['n']

        return jsonify({
            'status': 'operational',
            'service': 'counter-patriots',
            'claims': {
                'total':    counts['total_count'],
                'staged':   counts['staged_count'],
                'promoted': counts['promoted_count'],
                'returned': counts['returned_count'],
            },
            'sources_count': sources_count,
            'network_edges': edge_count,
            'last_ingestion': counts['last_ingestion'].isoformat() if counts['last_ingestion'] else None,
            'capabilities': ['drift', 'contradictions', 'silence', 'activation', 'record',
                             'staging', 'network'],
            'version': '2.0.0',
        })
    except Exception as e:
        return jsonify({'status': 'degraded', 'error': str(e)}), 503


# ---------------------------------------------------------------------------
# Endpoint: /api/drift
# ---------------------------------------------------------------------------

@app.route('/api/drift', methods=['POST'])
def drift_query():
    """
    Claims from a source on a topic over time, with contradiction flags.

    Input:  { source: str, topic: str, since: ISO datetime }
    Output: { claims: [...], contradiction_count: int, silent_retcon_count: int }

    Use this to see how a source's coverage of a topic has changed.
    """
    data = request.get_json(force=True)
    require_field(data, 'topic')

    source_name = data.get('source')
    topic_tag   = data['topic']
    since       = parse_since(data)

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Build query
            params = [topic_tag]
            query = """
                SELECT c.id, c.claim_text, c.article_url, c.article_title,
                       c.technique_class, c.extracted_at, c.published_at,
                       c.trust_level, c.staging_confidence,
                       s.name AS source_name, s.cluster, s.confidence_score
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE %s = ANY(c.topic_tags)
            """
            if source_name:
                query += " AND s.name ILIKE %s"
                params.append(f"%{source_name}%")
            if since:
                query += " AND c.extracted_at >= %s"
                params.append(since)
            query += " ORDER BY COALESCE(c.published_at, c.extracted_at) ASC"

            cur.execute(query, params)
            claims = cur.fetchall()

            # Count contradictions for these claims
            claim_ids = [c["id"] for c in claims]
            silent_count = 0
            contradiction_count = 0
            if claim_ids:
                cur.execute("""
                    SELECT relationship, COUNT(*) AS n
                    FROM contradictions
                    WHERE claim_a_id = ANY(%s) OR claim_b_id = ANY(%s)
                    GROUP BY relationship
                """, (claim_ids, claim_ids))
                for row in cur.fetchall():
                    if row['relationship'] == 'retcon_silent':
                        silent_count += row['n']
                    elif row['relationship'] == 'contradiction':
                        contradiction_count += row['n']

    return jsonify({
        'topic': topic_tag,
        'source': source_name,
        'since': since.isoformat() if since else None,
        'claims': [dict(c) for c in claims],
        'contradiction_count': contradiction_count,
        'silent_retcon_count': silent_count,
    })


# ---------------------------------------------------------------------------
# Endpoint: /api/contradictions  (Festinger Boundary — analyst auth required)
# ---------------------------------------------------------------------------

@app.route('/api/contradictions', methods=['POST'])
@require_analyst_auth
def contradiction_query():
    """
    Contradiction ledger for a source or topic.
    ANALYST AUTH REQUIRED — Festinger Boundary.

    Input:  { source?: str, topic?: str, since: ISO datetime, analyst_token: str }
    Output: { pairs: [...], by_type: { contradiction: N, retcon_silent: N, retcon_acknowledged: N } }
    """
    data = request.get_json(force=True)
    source_name = data.get('source')
    topic_tag   = data.get('topic')
    since       = parse_since(data)

    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT
                    cont.id, cont.relationship, cont.confidence,
                    cont.source_acknowledged, cont.flagged_at, cont.notes,
                    ca.claim_text AS claim_a_text, ca.article_url AS claim_a_url,
                    ca.extracted_at AS claim_a_date,
                    cb.claim_text AS claim_b_text, cb.article_url AS claim_b_url,
                    cb.extracted_at AS claim_b_date,
                    sa.name AS source_name
                FROM contradictions cont
                JOIN claims ca ON ca.id = cont.claim_a_id
                JOIN claims cb ON cb.id = cont.claim_b_id
                JOIN sources sa ON sa.id = ca.source_id
                WHERE 1=1
            """
            params = []
            if source_name:
                query += " AND sa.name ILIKE %s"
                params.append(f"%{source_name}%")
            if topic_tag:
                query += " AND (%s = ANY(ca.topic_tags) OR %s = ANY(cb.topic_tags))"
                params.extend([topic_tag, topic_tag])
            if since:
                query += " AND cont.flagged_at >= %s"
                params.append(since)
            query += " ORDER BY cont.flagged_at DESC LIMIT 200"

            cur.execute(query, params)
            pairs = cur.fetchall()

    by_type = {'contradiction': 0, 'retcon_silent': 0, 'retcon_acknowledged': 0, 'elaboration': 0}
    for p in pairs:
        rel = p['relationship']
        if rel in by_type:
            by_type[rel] += 1

    audit.log_event(
        session_id=g.session_id,
        event_type='analyst_query',
        actor='analyst',
        action=f"Contradiction query: source={source_name!r} topic={topic_tag!r}",
        data_accessed={'source': source_name, 'topic': topic_tag, 'result_count': len(pairs)},
    )

    return jsonify({
        'pairs': [dict(p) for p in pairs],
        'by_type': by_type,
        'total': len(pairs),
    })


# ---------------------------------------------------------------------------
# Endpoint: /api/silence
# ---------------------------------------------------------------------------

@app.route('/api/silence', methods=['POST'])
def silence_query():
    """
    Silence flags — what's missing from coverage.

    Input:  { topic: str, since: ISO datetime }
    Output: { flags: [...], by_cluster: { cluster_name: [elements], ... } }
    """
    data = request.get_json(force=True)
    require_field(data, 'topic')
    topic_tag = data['topic']
    since     = parse_since(data)

    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id, element, present_in_clusters, absent_from_clusters,
                       present_in_sources, absent_from_sources,
                       first_detected, detection_method, analyst_reviewed
                FROM silence_flags
                WHERE topic_tag = %s
            """
            params = [topic_tag]
            if since:
                query += " AND first_detected >= %s"
                params.append(since)
            query += " ORDER BY first_detected DESC"
            cur.execute(query, params)
            flags = cur.fetchall()

    # Group by absent cluster for easy inspection
    by_cluster: dict[str, list[str]] = {}
    for flag in flags:
        for cluster in (flag['absent_from_clusters'] or []):
            by_cluster.setdefault(cluster, []).append(flag['element'])

    return jsonify({
        'topic': topic_tag,
        'flags': [dict(f) for f in flags],
        'by_cluster': by_cluster,
        'total': len(flags),
    })


# ---------------------------------------------------------------------------
# Endpoint: /api/activation
# ---------------------------------------------------------------------------

@app.route('/api/activation', methods=['POST'])
def activation_query():
    """
    Narrative spikes — same frame appearing across ideologically distinct clusters.

    Input:  { topic?: str, since: ISO datetime, min_cluster_spread?: int }
    Output: { patterns: [...], by_topic: { topic: [...] } }
    """
    data = request.get_json(force=True)
    topic_tag         = data.get('topic')
    since             = parse_since(data)
    min_spread        = int(data.get('min_cluster_spread', 3))

    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id, topic_tag, claim_pattern, cluster_spread,
                       clusters_present, source_ids, first_seen, last_seen,
                       window_minutes, claim_count, technique_class, flagged_at
                FROM activation_patterns
                WHERE cluster_spread >= %s
            """
            params = [min_spread]
            if topic_tag:
                query += " AND topic_tag = %s"
                params.append(topic_tag)
            if since:
                query += " AND flagged_at >= %s"
                params.append(since)
            query += " ORDER BY cluster_spread DESC, flagged_at DESC"
            cur.execute(query, params)
            patterns = cur.fetchall()

    by_topic: dict[str, list] = {}
    for p in patterns:
        by_topic.setdefault(p['topic_tag'], []).append(dict(p))

    return jsonify({
        'patterns': [dict(p) for p in patterns],
        'by_topic': by_topic,
        'total': len(patterns),
    })


# ---------------------------------------------------------------------------
# Endpoint: /api/record
# ---------------------------------------------------------------------------

@app.route('/api/record', methods=['POST'])
def full_record():
    """
    Complete timestamped record for an event — the founding case study output.

    Input:  { topic: str, since: ISO datetime }
    Output: {
        claims: [...],
        contradictions: [...],   # requires analyst_token, else omitted
        silences: [...],
        activations: [...]
    }

    This is the full picture: what was said, what changed,
    what was missing, and what spiked simultaneously.
    The analyst draws conclusions. The system provides the record.
    """
    data = request.get_json(force=True)
    require_field(data, 'topic')
    topic_tag = data['topic']
    since     = parse_since(data)

    # Claims
    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT c.id, c.claim_text, c.article_url, c.article_title,
                       c.technique_class, c.extracted_at, c.published_at,
                       c.topic_tags,
                       s.name AS source_name, s.cluster, s.confidence_score
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                WHERE %s = ANY(c.topic_tags)
            """
            params = [topic_tag]
            if since:
                query += " AND c.extracted_at >= %s"
                params.append(since)
            query += " ORDER BY COALESCE(c.published_at, c.extracted_at) ASC"
            cur.execute(query, params)
            claims = cur.fetchall()

            # Silences
            silence_query = "SELECT element, present_in_clusters, absent_from_clusters, first_detected FROM silence_flags WHERE topic_tag = %s"
            silence_params = [topic_tag]
            if since:
                silence_query += " AND first_detected >= %s"
                silence_params.append(since)
            cur.execute(silence_query, silence_params)
            silences = cur.fetchall()

            # Activations
            activation_query = "SELECT claim_pattern, cluster_spread, clusters_present, window_minutes, claim_count, first_seen FROM activation_patterns WHERE topic_tag = %s"
            activation_params = [topic_tag]
            if since:
                activation_query += " AND flagged_at >= %s"
                activation_params.append(since)
            cur.execute(activation_query, activation_params)
            activations = cur.fetchall()

    result = {
        'topic': topic_tag,
        'since': since.isoformat() if since else None,
        'claims': [dict(c) for c in claims],
        'silences': [dict(s) for s in silences],
        'activations': [dict(a) for a in activations],
    }

    # Contradictions: only include if analyst auth provided
    analyst_token = (request.headers.get('X-Analyst-Token') or
                     data.get('analyst_token', ''))
    if analyst_token == ANALYST_TOKEN:
        claim_ids = [c['id'] for c in claims]
        if claim_ids:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT cont.relationship, cont.confidence, cont.source_acknowledged,
                               cont.flagged_at, ca.claim_text AS claim_a, cb.claim_text AS claim_b
                        FROM contradictions cont
                        JOIN claims ca ON ca.id = cont.claim_a_id
                        JOIN claims cb ON cb.id = cont.claim_b_id
                        WHERE cont.claim_a_id = ANY(%s) OR cont.claim_b_id = ANY(%s)
                        ORDER BY cont.flagged_at DESC
                    """, (claim_ids, claim_ids))
                    result['contradictions'] = [dict(r) for r in cur.fetchall()]
    else:
        result['contradictions'] = None
        result['contradictions_note'] = 'Analyst auth required. Pass X-Analyst-Token header.'

    return jsonify(result)


# ---------------------------------------------------------------------------
# Endpoint: /api/staging  — claims awaiting analyst review
# ---------------------------------------------------------------------------

@app.route('/api/staging', methods=['POST'])
@require_analyst_auth
def staging_queue():
    """
    Claims in STAGED or RETURNED_TO_STAGED state awaiting analyst review.

    Input:  { topic?: str, limit?: int, analyst_token: str }
    Output: { claims: [...], total: int }
    """
    data = request.get_json(force=True)
    topic = data.get('topic')
    limit = min(int(data.get('limit', 100)), 500)

    claims = retcon_ledger.get_staged_claims(topic=topic, limit=limit)

    audit.log_event(
        session_id=g.session_id,
        event_type='analyst_query',
        actor='analyst',
        action=f"Staging queue query: topic={topic!r}, returned {len(claims)} claims",
        data_accessed={'topic': topic, 'result_count': len(claims)},
    )

    return jsonify({'claims': claims, 'total': len(claims)})


# ---------------------------------------------------------------------------
# Endpoint: /api/network  — source network topology
# ---------------------------------------------------------------------------

@app.route('/api/network', methods=['GET', 'POST'])
def network_topology():
    """
    Source network topology — amplification, coordination, and cluster edges.

    Input (POST): { source_id?: int }
    Output: { edges: [...], total: int }

    This is the map the contamination cascade uses for independence verification.
    """
    data = request.get_json(force=True, silent=True) or {}
    source_id = data.get('source_id')

    edges = source_intel.get_network_topology(source_id=source_id)
    return jsonify({'edges': edges, 'total': len(edges)})


# ---------------------------------------------------------------------------
# Admin endpoint: promote a claim
# ---------------------------------------------------------------------------

@app.route('/admin/promote_claim', methods=['POST'])
@require_analyst_auth
def admin_promote_claim():
    """
    Promote a STAGED claim to PROMOTED. Creates a frozen promotion snapshot.

    Input: {
        claim_id:       int,
        confidence:     float (0.0-1.0),
        source_weights: { "source_id": weight, ... },  -- must sum ~1.0
        threshold?:     float,
        evidence?:      [str, ...],
        predictions?:   [{"prediction": str, "confirmed_by": null, ...}, ...],
        analyst_token:  str
    }
    """
    data = request.get_json(force=True)
    require_field(data, 'claim_id')
    require_field(data, 'confidence')
    require_field(data, 'source_weights')

    try:
        result = retcon_ledger.promote_claim(
            claim_id=int(data['claim_id']),
            confidence=float(data['confidence']),
            source_weights=data['source_weights'],
            threshold=float(data['threshold']) if data.get('threshold') else None,
            evidence=data.get('evidence'),
            predictions=data.get('predictions'),
            session_id=g.session_id,
        )
        return jsonify({'status': 'promoted', **result})
    except ValueError as e:
        abort(400, description=str(e))


# ---------------------------------------------------------------------------
# Admin endpoint: return a claim to staging
# ---------------------------------------------------------------------------

@app.route('/admin/return_to_staged', methods=['POST'])
@require_analyst_auth
def admin_return_to_staged():
    """
    Return a PROMOTED claim to RETURNED_TO_STAGED for re-review.

    Input: { claim_id: int, reason: str, analyst_token: str }
    """
    data = request.get_json(force=True)
    require_field(data, 'claim_id')
    require_field(data, 'reason')

    try:
        result = retcon_ledger.return_to_staged(
            claim_id=int(data['claim_id']),
            reason=data['reason'],
            immediate=False,
            session_id=g.session_id,
        )
        return jsonify({'status': 'returned', **result})
    except ValueError as e:
        abort(400, description=str(e))


# ---------------------------------------------------------------------------
# Admin endpoint: register source network edge
# ---------------------------------------------------------------------------

@app.route('/admin/register_edge', methods=['POST'])
@require_analyst_auth
def admin_register_edge():
    """
    Register an observed network edge between two sources.

    Input: {
        source_id:            int,
        connected_source_id:  int,
        relationship_type:    amplifies | is_amplified_by | mutual_engagement | cluster_member,
        weight?:              float (default 1.0),
        analyst_token:        str
    }
    """
    data = request.get_json(force=True)
    require_field(data, 'source_id')
    require_field(data, 'connected_source_id')
    require_field(data, 'relationship_type')

    try:
        result = source_intel.register_edge(
            source_id=int(data['source_id']),
            connected_source_id=int(data['connected_source_id']),
            relationship_type=data['relationship_type'],
            weight=float(data.get('weight', 1.0)),
            session_id=g.session_id,
        )
        return jsonify({'status': 'registered', **result})
    except ValueError as e:
        abort(400, description=str(e))


# ---------------------------------------------------------------------------
# Admin endpoint: trigger ingestion pass (for testing / manual ingest)
# ---------------------------------------------------------------------------

@app.route('/admin/ingest', methods=['POST'])
@require_analyst_auth
def admin_ingest():
    """Trigger a manual ingestion pass and run all analysis engines."""
    try:
        claims_inserted = run_ingestion()
        contradictions  = scan_new_claims()
        silences        = run_silence_scan()
        activations     = run_activation_scan()
        return jsonify({
            'status': 'ok',
            'claims_inserted': claims_inserted,
            'contradictions_flagged': contradictions,
            'silences_flagged': silences,
            'activations_flagged': activations,
        })
    except Exception as e:
        log.error(f"Manual ingest failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info(f"Counter-Patriots starting on port {SERVICE_PORT}")
    app.run(host="0.0.0.0", port=SERVICE_PORT, debug=False)
