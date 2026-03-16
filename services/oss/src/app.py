"""
app.py — OSS A2A query interface.

Six endpoints. Returns records, not assessments.
The analyst holds the conclusions.

The Curtis Rule is enforced here by the absence of certain endpoints:
  - No /api/suggest_framing
  - No /api/truth_score
  - No /api/counter_narrative
These endpoints do not exist. They cannot be called.

The Festinger Boundary is enforced here by analyst authentication:
  - /api/contradictions requires OSS_ANALYST_TOKEN header
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
import urllib.request
import urllib.error
from datetime import datetime, timezone
from functools import wraps
from typing import Optional

import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify, abort, g, render_template

from ingest import run_once as run_ingestion, embed, is_duplicate, add_to_faiss, save_faiss, is_paused, set_paused
from contradict import scan_new_claims
from silence import run_silence_scan
from activation import run_activation_scan
import audit
import retcon_ledger
import source_intel
import contamination_cascade
import hypothesis
import narrative_drift
import propagation_dynamics
import meta_detection
import threat_model
import operator_state

logging.basicConfig(level=logging.INFO, format='[APP] %(message)s', force=True)
log = logging.getLogger(__name__)

app = Flask(__name__)

DB_URL                  = os.environ.get("OSS_DB_URL", "postgresql://oss_app:oss_app_dev_password@localhost:5433/oss")
ANALYST_TOKEN           = os.environ.get("OSS_ANALYST_TOKEN", "dev_analyst_token")
SERVICE_PORT            = int(os.environ.get("OSS_PORT", "7731"))
SWARMFISH_BASE_URL      = os.environ.get("SWARMFISH_BASE_URL", "http://host.docker.internal:7732")
SWARMFISH_ANALYST_TOKEN = os.environ.get("SWARMFISH_ANALYST_TOKEN", "dev_analyst_token")


# ---------------------------------------------------------------------------
# Web UI
# ---------------------------------------------------------------------------

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


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
            'service': 'oss',
            'claims': {
                'total':    counts['total_count'],
                'staged':   counts['staged_count'],
                'promoted': counts['promoted_count'],
                'returned': counts['returned_count'],
            },
            'sources_count': sources_count,
            'network_edges': edge_count,
            'last_ingestion': counts['last_ingestion'].isoformat() if counts['last_ingestion'] else None,
            'ingest_paused': is_paused(),
            'capabilities': [
                'drift', 'contradictions', 'silence', 'activation', 'record',
                'staging', 'network', 'cascade', 'hypotheses', 'topic_drift',
                'propagation_dynamics', 'meta_detection', 'threat_model', 'operator_state',
                'submit_claim',
            ],
            'version': '3.0.0',
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
# Endpoint: /api/feed  — recent claims, optionally filtered by topic
# ---------------------------------------------------------------------------

@app.route('/api/feed', methods=['GET'])
def feed_query():
    """
    Recent claims, newest first, optionally filtered by topic tag.

    Query params:
        topic   — filter to claims tagged with this topic (optional)
        limit   — max rows to return (default 50, max 200)

    Returns all trust levels so the analyst can see the full incoming stream.
    """
    topic = request.args.get('topic', '').strip()
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
    except (ValueError, TypeError):
        limit = 50

    with get_conn() as conn:
        with conn.cursor() as cur:
            if topic:
                cur.execute(
                    """
                    SELECT c.id, c.claim_text, c.article_url, c.article_title,
                           c.technique_class, c.extracted_at, c.published_at,
                           c.trust_level, c.staging_confidence, c.topic_tags,
                           s.name AS source_name, s.cluster, s.confidence_score
                    FROM claims c
                    JOIN sources s ON s.id = c.source_id
                    WHERE %s = ANY(c.topic_tags)
                      AND c.trust_level != 'IRRELEVANT'
                    ORDER BY COALESCE(c.published_at, c.extracted_at) DESC
                    LIMIT %s
                    """,
                    (topic, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT c.id, c.claim_text, c.article_url, c.article_title,
                           c.technique_class, c.extracted_at, c.published_at,
                           c.trust_level, c.staging_confidence, c.topic_tags,
                           s.name AS source_name, s.cluster, s.confidence_score
                    FROM claims c
                    JOIN sources s ON s.id = c.source_id
                    WHERE c.trust_level != 'IRRELEVANT'
                    ORDER BY COALESCE(c.published_at, c.extracted_at) DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            claims = cur.fetchall()

    return jsonify({
        'topic': topic or None,
        'claims': [dict(c) for c in claims],
        'total': len(claims),
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
# Admin endpoint: run contamination cascade
# ---------------------------------------------------------------------------

@app.route('/admin/run_cascade', methods=['POST'])
@require_analyst_auth
def admin_run_cascade():
    """
    Trigger the contamination cascade for a source whose trust score has dropped.

    Traces all PROMOTED claims where the source contributed, applies tier logic:
      - Survived (>= 2 predictions confirmed independently): re-promoted
      - Immediate return (>= 80% load): returned to staged without review
      - Urgent flag (>= 50% load): flagged for operator decision
      - Review flag (< 50% load): confidence haircut, flag for review

    Input: {
        source_id:       int,
        new_trust_score: float (0.0–1.0),
        analyst_token:   str
    }
    Output: contamination report
    """
    data = request.get_json(force=True)
    require_field(data, 'source_id')
    require_field(data, 'new_trust_score')

    new_trust = float(data['new_trust_score'])
    if not (0.0 <= new_trust <= 1.0):
        abort(400, description="new_trust_score must be between 0.0 and 1.0")

    try:
        report = contamination_cascade.run_cascade(
            source_id=int(data['source_id']),
            new_trust_score=new_trust,
            session_id=g.session_id,
        )
        return jsonify({'status': 'cascade_complete', **report})
    except ValueError as e:
        abort(400, description=str(e))


# ---------------------------------------------------------------------------
# Endpoint: /api/promoted — promoted claims with snapshots
# ---------------------------------------------------------------------------

@app.route('/api/promoted', methods=['POST'])
@require_analyst_auth
def promoted_claims():
    """
    List PROMOTED claims with their frozen promotion snapshots.

    Input:  { topic?: str, limit?: int, analyst_token: str }
    Output: { claims: [...], total: int }
    """
    data = request.get_json(force=True)
    topic = data.get('topic')
    limit = min(int(data.get('limit', 100)), 500)

    claims = retcon_ledger.get_promoted_claims(topic=topic, limit=limit)

    audit.log_event(
        session_id=g.session_id,
        event_type='analyst_query',
        actor='analyst',
        action=f"Promoted claims query: topic={topic!r}, returned {len(claims)}",
        data_accessed={'topic': topic, 'result_count': len(claims)},
    )

    return jsonify({'claims': claims, 'total': len(claims)})


# ---------------------------------------------------------------------------
# Endpoint: /api/topic_drift — narrative framing shift detection
# ---------------------------------------------------------------------------

@app.route('/api/topic_drift', methods=['POST'])
def topic_drift():
    """
    Detect narrative framing drift for a topic.

    Compares current window vs prior window. Returns drift signals
    (technique_shift, cluster_shift, salience_shift, volume_shift,
    confidence_shift), a drift_score (0.0–1.0), and a drifted flag.

    Input:  { topic: str, window_hours?: int (default 168 = 7 days) }
    Output: drift analysis dict
    """
    data = request.get_json(force=True)
    require_field(data, 'topic')

    topic_tag    = data['topic']
    window_hours = int(data.get('window_hours', 168))
    if window_hours < 1:
        abort(400, description="window_hours must be >= 1")

    result = narrative_drift.detect_drift(topic_tag=topic_tag, window_hours=window_hours)
    return jsonify(result)


# ---------------------------------------------------------------------------
# Endpoints: hypothesis registry
# ---------------------------------------------------------------------------

@app.route('/api/hypotheses', methods=['GET', 'POST'])
def hypotheses_list():
    """
    List hypotheses with optional filters.

    GET /api/hypotheses?observation_id=N&status=ACTIVE
    POST /api/hypotheses  { observation_id?: int, status?: str, limit?: int }
    Output: { hypotheses: [...], total: int }
    """
    if request.method == 'GET':
        data = request.args
    else:
        data = request.get_json(force=True, silent=True) or {}

    observation_id = data.get('observation_id')
    status_filter  = data.get('status')
    limit          = min(int(data.get('limit', 50)), 200)

    try:
        raw = hypothesis.get_hypotheses(
            observation_id=int(observation_id) if observation_id else None,
            status=status_filter,
            limit=limit,
        )
    except ValueError as e:
        abort(400, description=str(e))

    # Normalize field names for the frontend
    hyps = []
    for h in raw:
        hyps.append({
            **h,
            'explanation':  h.get('candidate_explanation', ''),
            'predictions':  h.get('predictions_generated') or [],
        })

    return jsonify({'hypotheses': hyps, 'total': len(hyps)})


@app.route('/api/hypothesis', methods=['POST'])
@require_analyst_auth
def hypothesis_register():
    """
    Register a new hypothesis for an observation.

    Multiple hypotheses can be registered per observation_id (Chamberlin's method).

    Input: {
        observation_id:      int,
        explanation:         str,
        initial_confidence?: float (default 0.0),
        predictions?:        [{"prediction": str, "falsifiable_by": str|null}, ...],
        analyst_token:       str
    }
    """
    data = request.get_json(force=True)
    require_field(data, 'observation_id')
    require_field(data, 'explanation')

    try:
        result = hypothesis.register_hypothesis(
            observation_id=int(data['observation_id']),
            explanation=data['explanation'],
            initial_confidence=float(data.get('initial_confidence', 0.0)),
            predictions=data.get('predictions'),
            session_id=g.session_id,
        )
        return jsonify({'status': 'registered', **result}), 201
    except ValueError as e:
        abort(400, description=str(e))


@app.route('/api/hypothesis/<int:hypothesis_id>/confirm_prediction', methods=['POST'])
@require_analyst_auth
def hypothesis_confirm_prediction(hypothesis_id: int):
    """
    Record that a prediction came true.

    Input: { prediction_idx: int, analyst_token: str }
    """
    data = request.get_json(force=True)
    if data.get('prediction_idx') is None:
        abort(400, description="Missing required field: prediction_idx")

    try:
        result = hypothesis.confirm_prediction(
            hypothesis_id=hypothesis_id,
            prediction_idx=int(data['prediction_idx']),
            session_id=g.session_id,
        )
        return jsonify({'status': 'confirmed', **result})
    except ValueError as e:
        abort(400, description=str(e))


@app.route('/api/hypothesis/<int:hypothesis_id>/falsify', methods=['POST'])
@require_analyst_auth
def hypothesis_falsify(hypothesis_id: int):
    """
    Mark a hypothesis as falsified.

    Input: { evidence: str, analyst_token: str }
    """
    data = request.get_json(force=True)
    require_field(data, 'evidence')

    try:
        result = hypothesis.falsify_hypothesis(
            hypothesis_id=hypothesis_id,
            evidence=data['evidence'],
            session_id=g.session_id,
        )
        # Notify SWARMFISH so profiles calibrate from this outcome
        sf_sid = result.get('swarmfish_session_id')
        if sf_sid:
            try:
                _swarmfish_request('/acp/outcome', method='POST', body={
                    'session_id':  sf_sid,
                    'outcome':     data['evidence'][:500],
                    'was_correct': False,
                })
                log.info(f"[HYPOTHESIS] SWARMFISH outcome posted (falsified, session={sf_sid})")
            except Exception as e:
                log.warning(f"[HYPOTHESIS] SWARMFISH outcome callout failed: {e}")
        return jsonify({'status': 'falsified', **result})
    except ValueError as e:
        abort(400, description=str(e))


@app.route('/api/hypothesis/<int:hypothesis_id>/promote', methods=['POST'])
@require_analyst_auth
def hypothesis_promote(hypothesis_id: int):
    """
    Promote the winning hypothesis.

    Input: { analyst_token: str }
    """
    data = request.get_json(force=True, silent=True) or {}

    try:
        result = hypothesis.promote_hypothesis(
            hypothesis_id=hypothesis_id,
            session_id=g.session_id,
        )
        # Notify SWARMFISH so profiles calibrate from this outcome
        sf_sid = result.get('swarmfish_session_id')
        if sf_sid:
            try:
                _swarmfish_request('/acp/outcome', method='POST', body={
                    'session_id':  sf_sid,
                    'outcome':     'Hypothesis promoted by analyst — predictions matched observed reality.',
                    'was_correct': True,
                })
                log.info(f"[HYPOTHESIS] SWARMFISH outcome posted (promoted, session={sf_sid})")
            except Exception as e:
                log.warning(f"[HYPOTHESIS] SWARMFISH outcome callout failed: {e}")
        return jsonify({'status': 'promoted', **result})
    except ValueError as e:
        abort(400, description=str(e))


# ---------------------------------------------------------------------------
# Endpoint: /api/hypothesis/from_swarmfish — receive SWARMFISH-generated hypothesis
# ---------------------------------------------------------------------------

@app.route('/api/hypothesis/from_swarmfish', methods=['POST'])
@require_analyst_auth
def hypothesis_from_swarmfish():
    """
    Register a hypothesis produced by the SWARMFISH monitoring loop.

    Input:
        topic:               str — OSS topic tag this relates to
        observation_label:   str — human-readable label for the observation thread
        swarmfish_session_id: str — SWARMFISH session UUID
        explanation:         str — operator_brief from the SWARMFISH session
        initial_confidence:  float — consensus_confidence from SWARMFISH
        predictions:         list[{prediction, falsifiable_by?}]
        source_profiles:     list[{profile_name, confidence, was_dissenter}]

    Returns: {status, hypothesis_id, observation_id}
    """
    data = request.get_json(force=True)
    require_field(data, 'explanation')
    require_field(data, 'swarmfish_session_id')

    topic             = data.get('topic', '')
    observation_label = data.get('observation_label', topic)
    session_id_sw     = data['swarmfish_session_id']
    explanation       = data['explanation']
    initial_conf      = float(data.get('initial_confidence', 0.0))
    predictions       = data.get('predictions') or []
    source_profiles   = data.get('source_profiles') or []

    # Derive a stable observation_id from topic + label
    import hashlib
    obs_hash = hashlib.sha256(f"{topic}:{observation_label}".encode()).hexdigest()
    observation_id = int(obs_hash[:8], 16) % (2**31 - 1)  # fit in SERIAL range

    try:
        result = hypothesis.register_hypothesis(
            observation_id=observation_id,
            explanation=explanation,
            initial_confidence=initial_conf,
            predictions=predictions,
            session_id=g.session_id,
        )
    except ValueError as e:
        abort(400, description=str(e))

    # Write attribution columns
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE hypothesis_registry
                SET swarmfish_session_id = %s,
                    source_profiles      = %s,
                    auto_generated       = TRUE,
                    observation_label    = %s
                WHERE id = %s
                """,
                (
                    session_id_sw,
                    psycopg2.extras.Json(source_profiles),
                    observation_label,
                    result['hypothesis_id'],
                ),
            )

    log.info(
        f"[HYPO] SWARMFISH hypothesis #{result['hypothesis_id']} registered "
        f"(session={session_id_sw}, topic={topic!r}, conf={initial_conf:.2f})"
    )
    return jsonify({'status': 'registered', **result}), 201


# ---------------------------------------------------------------------------
# Endpoints: propagation dynamics
# ---------------------------------------------------------------------------

@app.route('/api/propagation_dynamics', methods=['POST'])
def propagation_dynamics_compute():
    """
    Compute and persist propagation dynamics for a topic.

    Input:  { topic: str, window_hours?: int (default 24) }
    Output: velocity, acceleration, escape_velocity, time_to_escape, alert_level
    """
    data = request.get_json(force=True)
    require_field(data, 'topic')

    topic_tag    = data['topic']
    window_hours = int(data.get('window_hours', 24))
    if window_hours < 1:
        abort(400, description="window_hours must be >= 1")

    result = propagation_dynamics.compute_dynamics(
        topic_tag=topic_tag,
        velocity_window_hours=window_hours,
        session_id=g.session_id,
    )
    return jsonify(result)


@app.route('/api/propagation_dynamics/<topic>', methods=['GET'])
def propagation_dynamics_latest(topic: str):
    """
    Retrieve most recent computed dynamics for a topic.

    Output: most recent narrative_dynamics row, or 404 if none computed yet.
    """
    result = propagation_dynamics.get_latest(topic_tag=topic)
    if not result:
        abort(404, description=f"No dynamics computed yet for topic: {topic!r}")
    return jsonify(result)


# ---------------------------------------------------------------------------
# Endpoint: meta-detection / operational health
# ---------------------------------------------------------------------------

@app.route('/api/health/meta', methods=['GET', 'POST'])
def health_meta():
    """
    Operational health report. Detects system degradation / attack.

    GET  /api/health/meta
    POST /api/health/meta  { window_hours?: int (default 168) }

    Output: health_signal (NOMINAL|DEGRADED|COMPROMISED), per-metric status.
    """
    if request.method == 'POST':
        data = request.get_json(force=True, silent=True) or {}
        window_hours = int(data.get('window_hours', 168))
    else:
        window_hours = int(request.args.get('window_hours', 168))

    result = meta_detection.get_health_report(window_hours=window_hours)
    return jsonify(result)


# ---------------------------------------------------------------------------
# Endpoints: threat model (living adversary model)
# ---------------------------------------------------------------------------

@app.route('/api/threat_model', methods=['GET', 'POST'])
def threat_model_list():
    """
    List tracked adversarial techniques with optional filters.

    GET  /api/threat_model?technique_class=fracture&abandoned=false
    POST /api/threat_model  { technique_class?: str, abandoned?: bool, limit?: int }

    Output: { techniques: [...], total: int }
    """
    if request.method == 'GET':
        data = request.args
        abandoned_raw = data.get('abandoned')
        abandoned = None if abandoned_raw is None else abandoned_raw.lower() == 'true'
    else:
        data = request.get_json(force=True, silent=True) or {}
        abandoned = data.get('abandoned')

    technique_class = data.get('technique_class') or None
    limit           = min(int(data.get('limit', 50)), 200)

    try:
        techniques = threat_model.get_threat_model(
            technique_class=technique_class,
            abandoned=abandoned,
            limit=limit,
        )
    except ValueError as e:
        abort(400, description=str(e))

    return jsonify({'techniques': techniques, 'total': len(techniques)})


@app.route('/api/threat_model/technique', methods=['POST'])
@require_analyst_auth
def threat_model_record():
    """
    Record or update a technique observation.

    Idempotent: calling again for the same technique_name increments observed_count.

    Input: {
        technique_name:       str,
        technique_class:      str (presuasion|fracture|emergent|direct|none),
        detected_by_system?:  bool (default false),
        notes?:               str,
        analyst_token:        str
    }
    Output: { technique_id, technique_name, status (created|updated) }, 201
    """
    data = request.get_json(force=True)
    require_field(data, 'technique_name')
    require_field(data, 'technique_class')

    try:
        result = threat_model.record_technique(
            technique_name=data['technique_name'],
            technique_class=data['technique_class'],
            detected_by_system=bool(data.get('detected_by_system', False)),
            notes=data.get('notes'),
            session_id=g.session_id,
        )
        return jsonify({'status': 'recorded', **result}), 201
    except ValueError as e:
        abort(400, description=str(e))


@app.route('/api/threat_model/<int:technique_id>/abandon', methods=['POST'])
@require_analyst_auth
def threat_model_abandon(technique_id: int):
    """
    Mark a technique as abandoned by the adversary.

    Abandonment = adversary knows it's detected. Triggers feedback loop
    signal if multiple techniques abandoned in same window.

    Input: { predicted_adaptation?: str, analyst_token: str }
    Output: { technique_id, abandoned_at, feedback_loop_signal, recent_abandonments }
    """
    data = request.get_json(force=True, silent=True) or {}

    try:
        result = threat_model.flag_abandoned(
            technique_id=technique_id,
            predicted_adaptation=data.get('predicted_adaptation'),
            session_id=g.session_id,
        )
        return jsonify({'status': 'abandoned', **result})
    except ValueError as e:
        abort(400, description=str(e))


@app.route('/api/threat_model/trend', methods=['GET', 'POST'])
def threat_model_trend():
    """
    Technique observation trend and abandonment cluster analysis.

    GET  /api/threat_model/trend?window_days=30
    POST /api/threat_model/trend  { window_days?: int }

    Output: per-day observations by technique_class, abandonment cluster signal.
    """
    if request.method == 'GET':
        window_days = int(request.args.get('window_days', 30))
    else:
        data        = request.get_json(force=True, silent=True) or {}
        window_days = int(data.get('window_days', 30))

    result = threat_model.get_technique_trend(window_days=window_days)
    return jsonify(result)


# ---------------------------------------------------------------------------
# Endpoints: operator state monitoring
# ---------------------------------------------------------------------------

@app.route('/api/operator_state', methods=['GET'])
def operator_state_get():
    """
    Current operator state and active threshold multiplier.

    Output: { alert_level, threshold_multiplier, reason, set_by, set_at, override_active }
    """
    return jsonify(operator_state.get_current_state())


@app.route('/admin/operator_state', methods=['POST'])
@require_analyst_auth
def operator_state_set():
    """
    Set operator alert level. Threshold elevation is applied mechanically.

    NOMINAL:  1.0x — baseline threshold
    DEGRADED: 1.25x — elevated (fatigue, distraction)
    IMPAIRED: 1.50x — maximum elevation (significant impairment)

    Behavioral signal integration: Phase 4 (requires operator interface).
    Until then, state is set manually or by external monitor process.

    Input: {
        alert_level:            str (NOMINAL|DEGRADED|IMPAIRED),
        reason:                 str,
        override?:              bool (true = analyst overriding auto-detection),
        analyst_token:          str
    }
    Output: new state dict
    """
    data = request.get_json(force=True)
    require_field(data, 'alert_level')
    require_field(data, 'reason')

    try:
        result = operator_state.set_state(
            alert_level=data['alert_level'],
            reason=data['reason'],
            set_by='analyst',
            override=bool(data.get('override', False)),
            session_id=g.session_id,
        )
        return jsonify({'status': 'state_updated', **result})
    except ValueError as e:
        abort(400, description=str(e))


@app.route('/api/operator_state/history', methods=['GET'])
def operator_state_history():
    """
    Recent operator state history.

    GET /api/operator_state/history?limit=20
    Output: { history: [...], total: int }
    """
    limit  = min(int(request.args.get('limit', 20)), 100)
    result = operator_state.get_state_history(limit=limit)
    return jsonify({'history': result, 'total': len(result)})


# ---------------------------------------------------------------------------
# Admin endpoint: submit a claim directly (analyst dictation path)
# ---------------------------------------------------------------------------

@app.route('/admin/submit_claim', methods=['POST'])
@require_analyst_auth
def admin_submit_claim():
    """
    Submit a claim directly to the ledger without RSS ingestion.

    Use when the analyst observes something worth recording that isn't
    coming through monitored feeds — e.g. a live press briefing, a
    firsthand observation, or a source outside the ingestion pipeline.

    Claim is embedded, deduplicated, and inserted as STAGED with
    staging_confidence=1.0 (analyst-asserted). Promotion requires
    the standard /admin/promote_claim workflow.

    Input: {
        claim_text:      str,
        topic_tags?:     [str, ...],
        technique_class?: str (presuasion|fracture|emergent|direct|none, default: direct),
        source_name?:    str (looked up in sources; default: 'Analyst Manual Entry'),
        article_url?:    str,
        article_title?:  str,
        analyst_token:   str
    }
    Output: { claim_id, status, duplicate, topics_matched, topics_unrecognized }
    """
    data = request.get_json(force=True)
    require_field(data, 'claim_text')

    claim_text      = data['claim_text'].strip()
    topic_tags      = data.get('topic_tags') or []
    if isinstance(topic_tags, str):
        topic_tags = [t.strip() for t in topic_tags.split(',') if t.strip()]
    technique_class = data.get('technique_class', 'direct')
    source_name     = data.get('source_name', 'Analyst Manual Entry')
    article_url     = data.get('article_url', 'manual://analyst-entry')
    article_title   = data.get('article_title') or f'Manual entry — {claim_text[:80]}'

    valid_techniques = {'presuasion', 'fracture', 'emergent', 'direct', 'none'}
    if technique_class not in valid_techniques:
        abort(400, description=f"technique_class must be one of: {', '.join(sorted(valid_techniques))}")

    # Embed and deduplicate
    vec = embed([claim_text])[0]
    if is_duplicate(vec):
        return jsonify({
            'status': 'duplicate',
            'duplicate': True,
            'claim_id': None,
            'message': 'Near-identical claim already in ledger. Not added.',
        })

    faiss_id = add_to_faiss(vec)
    save_faiss()

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Resolve source: match by name, else use/create manual entry source
            cur.execute("SELECT id FROM sources WHERE name ILIKE %s LIMIT 1", (source_name,))
            row = cur.fetchone()
            if row:
                source_id = row['id']
            else:
                cur.execute("""
                    INSERT INTO sources (name, url, source_type, cluster, confidence_score)
                    VALUES ('Analyst Manual Entry', 'manual://analyst-entry', 'official', 'official', 1.0)
                    ON CONFLICT (url) DO NOTHING
                """)
                cur.execute("SELECT id FROM sources WHERE url = 'manual://analyst-entry'")
                source_id = cur.fetchone()['id']

            # Validate topic_tags against known topics
            if topic_tags:
                cur.execute("SELECT tag FROM topics WHERE tag = ANY(%s)", (topic_tags,))
                valid_tags = [r['tag'] for r in cur.fetchall()]
            else:
                valid_tags = []

            # Insert claim
            cur.execute("""
                INSERT INTO claims
                    (source_id, raw_text, claim_text, article_url, article_title,
                     topic_tags, technique_class, faiss_id, staging_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1.0)
                RETURNING id
            """, (source_id, claim_text, claim_text, article_url, article_title,
                  valid_tags, technique_class, faiss_id))
            claim_id = cur.fetchone()['id']

            if valid_tags:
                cur.execute("""
                    UPDATE topics SET last_active = NOW(), claim_count = claim_count + 1
                    WHERE tag = ANY(%s)
                """, (valid_tags,))

    audit.log_event(
        session_id=g.session_id,
        event_type='manual_claim_entry',
        actor='analyst',
        action=f"Manual claim submitted: {claim_text[:120]!r}",
        data_accessed={'claim_id': claim_id, 'topic_tags': valid_tags, 'technique_class': technique_class},
    )

    return jsonify({
        'status': 'staged',
        'claim_id': claim_id,
        'duplicate': False,
        'topics_matched': valid_tags,
        'topics_unrecognized': [t for t in topic_tags if t not in valid_tags],
        'message': f"Claim staged as ID {claim_id}. Review with /api/staging or promote with /admin/promote_claim.",
    }), 201


# ---------------------------------------------------------------------------
# Admin endpoints: pause / resume ingestion scheduler
# ---------------------------------------------------------------------------

@app.route('/admin/ingest/pause', methods=['POST'])
@require_analyst_auth
def admin_ingest_pause():
    """Pause the ingestion scheduler. Query endpoints and oss_submit remain active."""
    set_paused(True)
    return jsonify({'status': 'paused', 'ingest_paused': True})


@app.route('/admin/ingest/resume', methods=['POST'])
@require_analyst_auth
def admin_ingest_resume():
    """Resume the ingestion scheduler."""
    set_paused(False)
    return jsonify({'status': 'resumed', 'ingest_paused': False})


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
# Admin endpoints: SWARMFISH monitor toggle proxy
# ---------------------------------------------------------------------------

def _swarmfish_request(path: str, method: str = "GET", body: dict = None) -> dict:
    """Make an authenticated request to SWARMFISH and return parsed JSON."""
    url = f"{SWARMFISH_BASE_URL}{path}"
    encoded = json.dumps(body).encode() if body is not None else None
    headers = {"X-Analyst-Token": SWARMFISH_ANALYST_TOKEN}
    if encoded is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=encoded, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        try:
            return json.loads(body_text)
        except Exception:
            raise RuntimeError(f"HTTP {e.code}: {body_text[:200]}")


@app.route('/admin/swarmfish/status', methods=['GET'])
@require_analyst_auth
def admin_swarmfish_status():
    """Return current SWARMFISH monitor status."""
    try:
        data = _swarmfish_request("/monitor/status")
        return jsonify(data)
    except Exception as e:
        return jsonify({'active': False, 'error': str(e), 'unavailable': True})


@app.route('/admin/swarmfish/monitor/toggle', methods=['POST'])
@require_analyst_auth
def admin_swarmfish_monitor_toggle():
    """Toggle the SWARMFISH autonomous monitor on or off."""
    try:
        data = _swarmfish_request("/monitor/toggle", method="POST")
        state = 'enabled' if data.get('active') else 'disabled'
        log.info(f"[ADMIN] SWARMFISH monitor {state} via UI")
        return jsonify(data)
    except Exception as e:
        log.warning(f"[ADMIN] SWARMFISH toggle failed: {e}")
        return jsonify({'error': str(e)}), 502


@app.route('/admin/swarmfish/monitor/run_now', methods=['POST'])
@require_analyst_auth
def admin_swarmfish_monitor_run_now():
    """Trigger an immediate SWARMFISH monitoring cycle."""
    try:
        data = _swarmfish_request("/monitor/run_now", method="POST")
        return jsonify(data)
    except Exception as e:
        log.warning(f"[ADMIN] SWARMFISH run_now failed: {e}")
        return jsonify({'error': str(e)}), 502


# ---------------------------------------------------------------------------
# API endpoint: list monitored topics
# ---------------------------------------------------------------------------

@app.route('/api/topics', methods=['GET'])
def list_topics():
    """
    List all registered topics with claim counts and activity.

    Query params:
        active_only: bool (default true) — omit inactive topics
    Output: { topics: [...], total: int }
    """
    active_only = request.args.get('active_only', 'true').lower() != 'false'

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT tag, display_name, description, parent_tag,
                           claim_count, last_active, active
                    FROM topics
                """
                if active_only:
                    query += " WHERE active = TRUE"
                query += " ORDER BY claim_count DESC, tag ASC"
                cur.execute(query)
                rows = [dict(r) for r in cur.fetchall()]

        # Serialize timestamps
        for r in rows:
            if r.get('last_active'):
                r['last_active'] = r['last_active'].isoformat()

        return jsonify({'topics': rows, 'total': len(rows)})

    except Exception as e:
        log.error(f"list_topics failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Admin endpoint: add a new monitoring topic
# ---------------------------------------------------------------------------

@app.route('/admin/add_topic', methods=['POST'])
@require_analyst_auth
def admin_add_topic():
    """
    Register a new topic tag for the ingestion pipeline to monitor.

    Once added and active=true, the ingestion pipeline will tag incoming
    claims with this topic when the content matches.

    Input:  {
        tag:          str  (required) — slug identifier, e.g. 'taiwan-strait'
        display_name: str  (optional) — human label, defaults to tag
        description:  str  (optional) — what this topic covers
        parent_tag:   str  (optional) — parent topic tag for hierarchical grouping
        analyst_token: str (required)
    }
    Output: { status: 'created'|'exists', tag, display_name, active }
    """
    data = request.get_json(force=True)
    require_field(data, 'tag')

    tag          = data['tag'].strip().lower()
    display_name = (data.get('display_name') or tag.replace('-', ' ').title()).strip()
    description  = (data.get('description') or '').strip() or None
    parent_tag   = (data.get('parent_tag') or '').strip() or None

    if not tag:
        abort(400, description="tag cannot be empty")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Validate parent exists if provided
                if parent_tag:
                    cur.execute("SELECT tag FROM topics WHERE tag = %s", (parent_tag,))
                    if not cur.fetchone():
                        abort(400, description=f"parent_tag '{parent_tag}' does not exist")

                # Check if already exists
                cur.execute("SELECT tag, display_name, active FROM topics WHERE tag = %s", (tag,))
                existing = cur.fetchone()
                if existing:
                    return jsonify({
                        'status': 'exists',
                        'tag': existing['tag'],
                        'display_name': existing['display_name'],
                        'active': existing['active'],
                        'message': f"Topic '{tag}' already registered.",
                    })

                cur.execute(
                    """
                    INSERT INTO topics (tag, display_name, description, parent_tag)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (tag, display_name, description, parent_tag),
                )
                conn.commit()

        log.info(f"Topic added: {tag} ({display_name})")
        return jsonify({
            'status': 'created',
            'tag': tag,
            'display_name': display_name,
            'active': True,
            'message': f"Topic '{tag}' added. Ingestion pipeline will tag matching claims going forward.",
        }), 201

    except Exception as e:
        log.error(f"add_topic failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Endpoint: /api/sources  — list all registered sources
# ---------------------------------------------------------------------------

@app.route('/api/sources', methods=['GET'])
def list_sources():
    """
    Return all registered sources with ingestion stats.
    Used by the Sources UI tab.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, url, source_type, cluster,
                           confidence_score, total_claims, created_at
                    FROM sources
                    ORDER BY name
                """)
                rows = [dict(r) for r in cur.fetchall()]
                for r in rows:
                    if r.get('created_at'):
                        r['created_at'] = r['created_at'].isoformat()
        return jsonify({'sources': rows, 'total': len(rows)})
    except Exception as e:
        log.error(f"list_sources failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Admin endpoint: add a new source
# ---------------------------------------------------------------------------

@app.route('/admin/add_source', methods=['POST'])
@require_analyst_auth
def admin_add_source():
    """
    Register a new RSS feed source for the ingestion pipeline.

    Input: {
        name:             str  (required)
        url:              str  (required) — RSS feed URL
        source_type:      str  (required) — official|wire|outlet|social
        cluster:          str  (required) — left|center|right|wire|official|independent|international
        confidence_score: float (optional, default 0.7)
        analyst_token:    str  (required)
    }
    Output: { status: 'created'|'exists', source }
    """
    data = request.get_json(force=True)
    require_field(data, 'name')
    require_field(data, 'url')
    require_field(data, 'source_type')
    require_field(data, 'cluster')

    name         = data['name'].strip()
    url          = data['url'].strip()
    source_type  = data['source_type'].strip()
    cluster      = data['cluster'].strip()
    confidence   = float(data.get('confidence_score', 0.7))

    valid_types    = {'official', 'wire', 'outlet', 'social'}
    valid_clusters = {'left', 'center', 'right', 'wire', 'official', 'independent', 'international'}

    if source_type not in valid_types:
        abort(400, description=f"source_type must be one of: {', '.join(sorted(valid_types))}")
    if cluster not in valid_clusters:
        abort(400, description=f"cluster must be one of: {', '.join(sorted(valid_clusters))}")
    if not (0.0 <= confidence <= 1.0):
        abort(400, description="confidence_score must be between 0.0 and 1.0")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name FROM sources WHERE url = %s", (url,))
                existing = cur.fetchone()
                if existing:
                    return jsonify({
                        'status': 'exists',
                        'message': f"Source with this URL already registered as '{existing['name']}'.",
                        'source_id': existing['id'],
                    })

                cur.execute(
                    """
                    INSERT INTO sources (name, url, source_type, cluster, confidence_score)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, name, url, source_type, cluster, confidence_score
                    """,
                    (name, url, source_type, cluster, confidence),
                )
                source = dict(cur.fetchone())

                # Auto-seed cluster_member edge for non-official/non-independent sources
                if cluster not in ('official', 'independent'):
                    # Find another source in same cluster to link to
                    cur.execute(
                        """
                        SELECT id FROM sources
                        WHERE cluster = %s AND id != %s
                        LIMIT 1
                        """,
                        (cluster, source['id']),
                    )
                    peer = cur.fetchone()
                    if peer:
                        cur.execute(
                            """
                            INSERT INTO source_network_edges
                                (source_id, connected_source_id, relationship_type, weight)
                            VALUES (%s, %s, 'cluster_member', 0.5)
                            ON CONFLICT DO NOTHING
                            """,
                            (source['id'], peer['id']),
                        )

                conn.commit()

        log.info(f"Source added: {name} ({source_type}/{cluster}) — {url}")
        return jsonify({'status': 'created', 'source': source}), 201

    except Exception as e:
        log.error(f"add_source failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Admin endpoint: mark a claim as irrelevant
# ---------------------------------------------------------------------------

def _recompute_scrape_weight(cur, tag: str):
    """Recompute scrape_weight for a topic after irrelevance_count changes."""
    cur.execute(
        "SELECT irrelevance_count, total_staged_count FROM topics WHERE tag = %s",
        (tag,),
    )
    row = cur.fetchone()
    if not row or row['total_staged_count'] < 10:
        return  # not enough data yet
    rate = row['irrelevance_count'] / row['total_staged_count']
    weight = max(0.05, 1.0 - (rate * 0.8))
    cur.execute(
        "UPDATE topics SET scrape_weight = %s WHERE tag = %s",
        (weight, tag),
    )


@app.route('/admin/mark_irrelevant', methods=['POST'])
@require_analyst_auth
def admin_mark_irrelevant():
    """
    Mark a STAGED claim as IRRELEVANT. Increments irrelevance_count on
    each associated topic and recomputes scrape_weight.

    Input: { claim_id: int, reason?: str, analyst_token: str }
    Output: { status: 'ok', claim_id, topic_tags }
    """
    data = request.get_json(force=True)
    require_field(data, 'claim_id')
    claim_id = int(data['claim_id'])
    reason   = data.get('reason', '')

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT trust_level, topic_tags FROM claims WHERE id = %s",
                    (claim_id,),
                )
                claim = cur.fetchone()
                if not claim:
                    abort(404, description=f"Claim {claim_id} not found")
                if claim['trust_level'] not in ('STAGED', 'RETURNED_TO_STAGED'):
                    abort(400, description=f"Cannot mark {claim['trust_level']} claim as irrelevant. Only STAGED or RETURNED_TO_STAGED claims can be dismissed.")

                cur.execute(
                    "UPDATE claims SET trust_level = 'IRRELEVANT' WHERE id = %s",
                    (claim_id,),
                )

                tags = claim['topic_tags'] or []
                for tag in tags:
                    cur.execute(
                        "UPDATE topics SET irrelevance_count = irrelevance_count + 1 WHERE tag = %s",
                        (tag,),
                    )
                    _recompute_scrape_weight(cur, tag)

                audit.log_event(
                    session_id=g.session_id,
                    event_type='claim_marked_irrelevant',
                    actor='analyst',
                    action=f"Claim {claim_id} marked IRRELEVANT",
                    data_accessed={'claim_id': claim_id, 'reason': reason, 'topic_tags': tags},
                )
                conn.commit()

        log.info(f"Claim {claim_id} marked IRRELEVANT (tags={tags})")
        return jsonify({'status': 'ok', 'claim_id': claim_id, 'topic_tags': tags})

    except Exception as e:
        log.error(f"mark_irrelevant failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Endpoint: /api/social_monitors — list social monitor configurations
# ---------------------------------------------------------------------------

@app.route('/api/social_monitors', methods=['GET'])
def list_social_monitors():
    """List all social media monitor configurations."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM social_monitors ORDER BY created_at DESC"
                )
                rows = [dict(r) for r in cur.fetchall()]
                for r in rows:
                    if r.get('created_at'):
                        r['created_at'] = r['created_at'].isoformat()
                    if r.get('last_run_at'):
                        r['last_run_at'] = r['last_run_at'].isoformat()
        return jsonify({'monitors': rows, 'total': len(rows)})
    except Exception as e:
        log.error(f"list_social_monitors failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Admin endpoint: add a social monitor
# ---------------------------------------------------------------------------

@app.route('/admin/add_social_monitor', methods=['POST'])
@require_analyst_auth
def admin_add_social_monitor():
    """
    Add a new social media monitor.

    Input: {
        display_name:     str  (required)
        query:            str  (required) — search terms or handle
        monitor_type:     str  (optional, default 'search') — search|hashtag|user
        topic_tags:       list (optional)
        interval_minutes: int  (optional, default 60)
        analyst_token:    str  (required)
    }
    """
    data = request.get_json(force=True)
    require_field(data, 'display_name')
    require_field(data, 'query')

    display_name     = data['display_name'].strip()
    query            = data['query'].strip()
    monitor_type     = data.get('monitor_type', 'search')
    topic_tags       = data.get('topic_tags', [])
    interval_minutes = int(data.get('interval_minutes', 60))

    if monitor_type not in ('search', 'hashtag', 'user'):
        abort(400, description="monitor_type must be search, hashtag, or user")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO social_monitors
                        (display_name, query, monitor_type, topic_tags, interval_minutes)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (display_name, query, monitor_type, topic_tags, interval_minutes),
                )
                monitor = dict(cur.fetchone())
                if monitor.get('created_at'):
                    monitor['created_at'] = monitor['created_at'].isoformat()
                conn.commit()

        log.info(f"Social monitor added: {display_name} (query={query!r})")
        return jsonify({'status': 'created', 'monitor': monitor}), 201

    except Exception as e:
        log.error(f"add_social_monitor failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Admin endpoint: update/toggle a social monitor
# ---------------------------------------------------------------------------

@app.route('/admin/social_monitor/<int:monitor_id>', methods=['PATCH'])
@require_analyst_auth
def admin_update_social_monitor(monitor_id):
    """Toggle active state or update query/tags/interval for a social monitor."""
    data = request.get_json(force=True)

    fields = {}
    if 'active' in data:
        fields['active'] = bool(data['active'])
    if 'query' in data:
        fields['query'] = data['query'].strip()
    if 'topic_tags' in data:
        fields['topic_tags'] = data['topic_tags']
    if 'interval_minutes' in data:
        fields['interval_minutes'] = int(data['interval_minutes'])
    if 'display_name' in data:
        fields['display_name'] = data['display_name'].strip()

    if not fields:
        abort(400, description="No updatable fields provided")

    set_clause = ', '.join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [monitor_id]

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE social_monitors SET {set_clause} WHERE id = %s RETURNING id",
                    values,
                )
                if not cur.fetchone():
                    abort(404, description=f"Social monitor {monitor_id} not found")
                conn.commit()
        return jsonify({'status': 'ok', 'monitor_id': monitor_id})
    except Exception as e:
        log.error(f"update_social_monitor failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Admin endpoint: delete a social monitor
# ---------------------------------------------------------------------------

@app.route('/admin/social_monitor/<int:monitor_id>', methods=['DELETE'])
@require_analyst_auth
def admin_delete_social_monitor(monitor_id):
    """Remove a social media monitor configuration."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM social_monitors WHERE id = %s RETURNING id",
                    (monitor_id,),
                )
                if not cur.fetchone():
                    abort(404, description=f"Social monitor {monitor_id} not found")
                conn.commit()
        log.info(f"Social monitor {monitor_id} deleted")
        return jsonify({'status': 'ok', 'monitor_id': monitor_id})
    except Exception as e:
        log.error(f"delete_social_monitor failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Admin endpoint: on-demand X search
# ---------------------------------------------------------------------------

@app.route('/admin/x_search', methods=['POST'])
@require_analyst_auth
def admin_x_search():
    """
    On-demand X/Twitter search — scrape and ingest immediately.

    Input: { query: str, topic_tags?: list, count?: int (default 10), analyst_token: str }
    Output: { status: 'ok', staged: int, skipped: int, query: str }
    """
    data = request.get_json(force=True)
    require_field(data, 'query')
    query      = data['query'].strip()
    topic_tags = data.get('topic_tags', [])
    count      = int(data.get('count', 10))

    try:
        import social_ingest
        with get_conn() as conn:
            staged, skipped = social_ingest.run_query_sync(conn, query, topic_tags, count)
        log.info(f"On-demand X search '{query}': staged={staged}, skipped={skipped}")
        return jsonify({'status': 'ok', 'staged': staged, 'skipped': skipped, 'query': query})
    except Exception as e:
        log.error(f"x_search failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info(f"OSS starting on port {SERVICE_PORT}")
    app.run(host="0.0.0.0", port=SERVICE_PORT, debug=False)
