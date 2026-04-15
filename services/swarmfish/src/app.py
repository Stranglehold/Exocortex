"""
app.py — SWARMFISH Flask service entry point

Endpoints:
  GET  /                      — web UI
  POST /acp/predict           — run question through profile ensemble, return operator brief
  POST /acp/predict/stream    — same, but streams per-profile SSE events in real time
  POST /acp/outcome           — log outcome for a prediction/session, score, update calibration
  GET  /acp/status            — prediction history + calibration summary
  GET  /acp/profiles          — list profiles with current weights
  GET  /acp/session/<id>      — full session detail
  GET  /health                — healthcheck
"""

import json
import re
import uuid
import os
from datetime import datetime, timezone
from functools import wraps

import psycopg2
from flask import Flask, request, jsonify, g, render_template, Response, stream_with_context

import config
from acp.profiles import seed_profiles
from acp.predictor import run_profile, load_profiles_from_db
from acp.aggregator import finalize_session
from acp.tracker import record_outcome, record_session_outcome, get_calibration_summary
from acp.resolver import resolve_session
from oss_bridge import get_oss_context

app = Flask(__name__)


# ============================================================
# CORS — allow browser fetch() from any origin (analyst panel)
# ============================================================

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Analyst-Token'
    return response

@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path=''):
    return '', 204


# ============================================================
# DB connection
# ============================================================

def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(config.DB_URL)
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ============================================================
# Auth
# ============================================================

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Analyst-Token", "")
        if token != config.ANALYST_TOKEN:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ============================================================
# Session creation helper (shared by predict and predict/stream)
# ============================================================

def _create_session(db, question, domain, context=None):
    """Insert a new session row and return session_id.

    Stores up to 16KB of input context (was 200 chars) so post-hoc audit can
    reconstruct what the committee actually saw — fixes the truncation bug
    discovered in ST-007 where only the first claim line was archived.
    """
    session_id = str(uuid.uuid4())
    context_summary = context[:16000] if context else None
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO acp_sessions (id, question, domain, context_summary)
        VALUES (%s, %s, %s, %s)
    """, (session_id, question, domain, context_summary))
    db.commit()
    cursor.close()
    return session_id, context_summary


# ============================================================
# Input quality gate — defense against contaminated inputs
# ============================================================
#
# Background: ST-007 (eval/STRESS_TEST_007_OSS_SWARMFISH_IRAN_BLINDNESS.md)
# documented a catastrophic failure where the committee predicted "Strait
# of Hormuz remains open" with HIGH meta-confidence during an active
# blockade. Root cause: 80% of the input claims were off-topic noise from
# OSS topic-tagging contamination, and no profile flagged the input quality
# problem. The committee reasoned confidently from garbage.
#
# This gate runs BEFORE the profiles loop. It computes a relevance ratio of
# input claims against keywords extracted from the question, and if the
# ratio is below a threshold, it prepends an explicit warning to the context
# that all profiles will see. The warning gives the profiles a chance to
# react — and gives the analyst an unambiguous signal that the prediction
# was generated from low-quality input.
#
# This is a SOFT gate: it does not refuse to predict. It surfaces the
# warning so the analyst can grade the output appropriately.

_GATE_STOPWORDS = frozenset({
    'for', 'the', 'a', 'an', 'of', 'and', 'or', 'in', 'on', 'at', 'to',
    'is', 'are', 'was', 'were', 'be', 'will', 'what', 'when', 'how', 'why',
    'who', 'where', 'which', 'this', 'that', 'these', 'those', 'with',
    'from', 'by', 'as', 'situation', 'current', 'assess', 'about',
})

# Map common topic words to their concept families so a question containing
# "Iran / Strait of Hormuz" gates against any of {iran, strait, hormuz, irgc,
# tehran, persian, gulf} appearing in claims.
_KEYWORD_FAMILIES = {
    'iran':    {'iran', 'iranian', 'tehran', 'irgc', 'khamenei', 'pezeshkian', 'mojtaba'},
    'hormuz':  {'hormuz', 'strait', 'persian gulf', 'arabian sea', 'centcom', 'tanker'},
    'israel':  {'israel', 'israeli', 'idf', 'tel aviv', 'jerusalem', 'netanyahu', 'mossad'},
    'russia':  {'russia', 'russian', 'kremlin', 'putin', 'moscow'},
    'china':   {'china', 'chinese', 'beijing', 'xi jinping', 'pla'},
    'ukraine': {'ukraine', 'ukrainian', 'kyiv', 'zelensky'},
    'gaza':    {'gaza', 'hamas', 'palestinian', 'palestine', 'rafah'},
    'lebanon': {'lebanon', 'lebanese', 'hezbollah', 'beirut'},
    'yemen':   {'yemen', 'houthi', 'houthis', 'sanaa', 'aden'},
    'taiwan':  {'taiwan', 'taipei', 'taiwanese', 'cross-strait'},
    'korea':   {'korea', 'korean', 'pyongyang', 'kim jong'},
    'oil':     {'oil', 'crude', 'brent', 'wti', 'opec', 'barrel'},
    'nuclear': {'nuclear', 'enrichment', 'uranium', 'iaea', 'jcpoa'},
}


def _extract_topic_keywords(question: str) -> set[str]:
    """Extract the topic keyword set from a question.

    Looks for an explicit 'for: TOPIC.' clause first (the autonomous monitor
    uses this format); falls back to scanning the whole question. Expands
    each keyword via the KEYWORD_FAMILIES map so synonyms count as on-topic.
    """
    topic_text = question
    m = re.search(r'\bfor:\s*([^.?\n]+)', question, re.IGNORECASE)
    if m:
        topic_text = m.group(1)

    raw_words = re.split(r'[\s/\-,()]+', topic_text.lower())
    seeds = {w.strip('.,;:!?') for w in raw_words}
    seeds = {w for w in seeds if w and w not in _GATE_STOPWORDS and len(w) > 2}

    expanded = set(seeds)
    for seed in seeds:
        for family_key, family_set in _KEYWORD_FAMILIES.items():
            if seed in family_set or seed == family_key:
                expanded |= family_set
    return expanded


def _compute_input_relevance(context: str, keywords: set[str]) -> dict:
    """Compute the relevance ratio of claims in context against keywords.

    Returns a dict with: total_claims, on_topic, off_topic, ratio,
    and sample_off_topic (up to 3 example off-topic lines for the warning).
    """
    if not context or not keywords:
        return {'total_claims': 0, 'on_topic': 0, 'off_topic': 0,
                'ratio': 1.0, 'sample_off_topic': []}

    lines = [l.strip() for l in context.split('\n')
             if l.strip().startswith('•') or l.strip().startswith('-')]

    if not lines:
        return {'total_claims': 0, 'on_topic': 0, 'off_topic': 0,
                'ratio': 1.0, 'sample_off_topic': []}

    on, off, samples = 0, 0, []
    for line in lines:
        ll = line.lower()
        if any(k in ll for k in keywords):
            on += 1
        else:
            off += 1
            if len(samples) < 3:
                samples.append(line[:140])

    return {
        'total_claims': len(lines),
        'on_topic': on,
        'off_topic': off,
        'ratio': on / len(lines),
        'sample_off_topic': samples,
    }


def _apply_quality_gate(question: str, context: str | None,
                         session_id: str) -> tuple[str | None, dict | None]:
    """Run the input quality gate.

    Returns (effective_context, gate_report). gate_report is None if the
    gate did not fire. effective_context is context with a warning header
    prepended if the gate fired, or original context otherwise.
    """
    if not context:
        return context, None

    keywords = _extract_topic_keywords(question)
    if not keywords:
        return context, None

    rel = _compute_input_relevance(context, keywords)

    # Gate threshold: at least 5 claims AND less than 50% on-topic
    if rel['total_claims'] < 5 or rel['ratio'] >= 0.5:
        return context, None

    pct = int(rel['ratio'] * 100)
    sample_block = "\n".join(f"   {s}" for s in rel['sample_off_topic'])
    warning = (
        f"⚠ INPUT QUALITY GATE TRIPPED [session={session_id[:8]}]\n"
        f"Of {rel['total_claims']} provided claims, only {rel['on_topic']} ({pct}%) "
        f"directly engage with the question's topic keywords ({', '.join(sorted(keywords))[:200]}).\n"
        f"The remaining {rel['off_topic']} claims appear off-topic. Examples:\n"
        f"{sample_block}\n"
        f"This prediction is reasoning from contaminated or sparse input. "
        f"Profiles SHOULD acknowledge this and either (a) report INSUFFICIENT_DATA "
        f"or (b) explicitly identify what context is missing that would be needed "
        f"to assess the question. Treat any high-confidence output as suspect.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    print(f"[QUALITY-GATE] session={session_id[:8]} ratio={pct}% "
          f"({rel['on_topic']}/{rel['total_claims']}) — warning prepended", flush=True)

    return warning + context, {
        'tripped': True,
        'ratio': rel['ratio'],
        'on_topic': rel['on_topic'],
        'total_claims': rel['total_claims'],
        'keywords': sorted(keywords),
    }


# ============================================================
# GET /  — web UI
# ============================================================

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# ============================================================
# POST /acp/predict
# ============================================================

@app.route("/acp/predict", methods=["POST"])
@require_auth
def predict():
    """
    Run a prediction question through the profile ensemble.

    Body (JSON):
      question      str  required
      domain        str  optional, default "general"
      context       str  optional — operator-supplied data/analysis
      profile_names list optional — subset of profiles to use (default: all)

    Returns operator brief + per-profile predictions + session_id.
    """
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    domain         = data.get("domain", "general")
    context        = data.get("context")
    profile_names  = data.get("profile_names")  # None = all profiles

    db = get_db()

    # Auto-inject OSS context if bridge returns claims for this domain
    oss_ctx = get_oss_context(question, domain)
    if oss_ctx:
        context = f"{oss_ctx}\n\n{context}" if context else oss_ctx

    profiles_list = load_profiles_from_db(db, profile_names)
    if not profiles_list:
        return jsonify({"error": "No profiles found. Run seed first."}), 500

    profiles_dict = {p["name"]: p for p in profiles_list}
    session_id, context_summary = _create_session(db, question, domain, context)

    # Input quality gate — surfaces contaminated input so profiles see the
    # warning and the analyst gets an explicit signal. Soft gate only.
    effective_context, gate_report = _apply_quality_gate(question, context, session_id)

    # SFA-001 follow-up (2026-04-14) — cascade abort.
    # If 2 profiles fail back-to-back, abort the remaining profiles instead
    # of running them into the same broken pipe. Previous cycle observation:
    # LM Studio entered a degraded state, profile 5 timed out, then profiles
    # 6/7/8/9 each timed out, wasting ~20 minutes of GPU time. Fails fast
    # and leaves the session with whatever completed before the cascade.
    consecutive_failures = 0
    cascade_aborted = False
    predictions = []
    for profile in profiles_list:
        if cascade_aborted:
            # Record skipped profiles as errors so the Live Agent view shows them
            predictions.append({
                "prediction_id": None,
                "profile_name": profile["name"],
                "prediction": None,
                "confidence": None,
                "error": "skipped — cascade abort after 2 consecutive failures",
                "domain": domain,
            })
            continue

        result = run_profile(
            db, profile, question, domain,
            context=effective_context,
            session_id=session_id,
            context_summary=context_summary,
        )
        result["domain"] = domain
        predictions.append(result)

        if result.get("error"):
            consecutive_failures += 1
            if consecutive_failures >= 2:
                print(
                    f"[CASCADE] 2 consecutive profile failures — "
                    f"aborting remaining profiles for session {session_id[:8]}. "
                    f"Session will finalize with partial results.",
                    flush=True,
                )
                cascade_aborted = True
        else:
            consecutive_failures = 0

    result = finalize_session(
        db, session_id, question, domain, context_summary,
        predictions, profiles_dict
    )
    if gate_report:
        result['quality_gate'] = gate_report
    if cascade_aborted:
        result['cascade_aborted'] = True
    return jsonify(result), 200


# ============================================================
# POST /acp/predict/stream  — SSE streaming variant
# ============================================================

@app.route("/acp/predict/stream", methods=["POST"])
@require_auth
def predict_stream():
    """
    Same as /acp/predict but streams Server-Sent Events as each profile completes.

    Event types:
      session_created  { session_id }
      profiles_loaded  { profiles: [name, ...] }
      profile_start    { profile: name }
      profile_done     { result: { ...full profile result... } }
      done             { session: { ...finalized session... } }
      error            { message }
    """
    data = request.get_json(force=True) or {}
    question      = data.get("question", "").strip()
    domain        = data.get("domain", "general")
    context       = data.get("context")
    profile_names = data.get("profile_names")

    if not question:
        return jsonify({"error": "question is required"}), 400

    def generate():
        db = None
        # Resolve context outside the try block so the variable is always defined
        effective_context = context
        try:
            # Auto-inject OSS context if bridge returns claims for this domain
            oss_ctx = get_oss_context(question, domain)
            if oss_ctx:
                effective_context = f"{oss_ctx}\n\n{effective_context}" if effective_context else oss_ctx
        except Exception as e:
            print(f"[OSS BRIDGE] Error fetching context: {e}", flush=True)

        try:
            db = psycopg2.connect(config.DB_URL)

            session_id, context_summary = _create_session(db, question, domain, effective_context)
            yield f"data: {json.dumps({'type': 'session_created', 'session_id': session_id})}\n\n"

            # Input quality gate — soft warning prepended to context if input
            # is contaminated. See ST-007 for motivating failure.
            effective_context, gate_report = _apply_quality_gate(
                question, effective_context, session_id
            )
            if gate_report:
                yield f"data: {json.dumps({'type': 'quality_gate', 'report': gate_report})}\n\n"

            profiles_list = load_profiles_from_db(db, profile_names)
            if not profiles_list:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No profiles found'})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'profiles_loaded', 'profiles': [p['name'] for p in profiles_list]})}\n\n"

            predictions = []
            for profile in profiles_list:
                yield f"data: {json.dumps({'type': 'profile_start', 'profile': profile['name']})}\n\n"
                result = run_profile(
                    db, profile, question, domain,
                    context=effective_context,
                    session_id=session_id,
                    context_summary=context_summary,
                )
                result["domain"] = domain
                predictions.append(result)
                yield f"data: {json.dumps({'type': 'profile_done', 'result': result})}\n\n"

            profiles_dict = {p["name"]: p for p in profiles_list}
            final = finalize_session(
                db, session_id, question, domain, context_summary,
                predictions, profiles_dict
            )
            if gate_report:
                final['quality_gate'] = gate_report
            yield f"data: {json.dumps({'type': 'done', 'session': final})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            if db:
                db.close()

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ============================================================
# POST /acp/outcome
# ============================================================

@app.route("/acp/outcome", methods=["POST"])
@require_auth
def outcome():
    """
    Log an outcome and score predictions.

    Body (JSON):
      outcome             str  required — what actually happened
      was_correct         bool required
      prediction_id       str  optional — score a single prediction
      session_id          str  optional — score all predictions in a session
      conditions_held     list optional
      conditions_failed   list optional
      post_mortem_note    str  optional

    Provide exactly one of prediction_id or session_id.
    """
    data = request.get_json(force=True)
    outcome_text  = data.get("outcome", "").strip()
    was_correct   = data.get("was_correct")
    prediction_id = data.get("prediction_id")
    session_id    = data.get("session_id")

    if not outcome_text:
        return jsonify({"error": "outcome text is required"}), 400
    if was_correct is None:
        return jsonify({"error": "was_correct (bool) is required"}), 400
    if not prediction_id and not session_id:
        return jsonify({"error": "provide prediction_id or session_id"}), 400

    db = get_db()

    conditions_held   = data.get("conditions_held", [])
    conditions_failed = data.get("conditions_failed", [])
    post_mortem       = data.get("post_mortem_note")

    try:
        if session_id:
            results = record_session_outcome(
                db, session_id, outcome_text, bool(was_correct),
                conditions_held, conditions_failed, post_mortem
            )
            # If there's a pending proposed resolution for this session, mark it
            # as accepted (operator's verdict matches the proposed verdict) or
            # overridden (operator disagreed). This drives concordance tracking.
            _mark_proposal_reviewed(db, session_id, bool(was_correct))
            return jsonify({"scored": results}), 200
        else:
            result = record_outcome(
                db, prediction_id, outcome_text, bool(was_correct),
                conditions_held, conditions_failed, post_mortem
            )
            return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


def _mark_proposal_reviewed(db_conn, session_id: str, operator_was_correct: bool) -> None:
    """
    If there's a pending proposal for this session, flip its operator_action to
    'accepted' or 'overridden' based on whether the operator agreed with the
    proposed verdict.

    confirmed verdict → matches operator_was_correct=True
    falsified verdict → matches operator_was_correct=False
    still_pending verdict → always treated as overridden (operator resolved a
                            prediction the resolver wouldn't commit on)
    """
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT id, verdict FROM acp_proposed_resolutions
        WHERE session_id = %s AND operator_action IS NULL
        ORDER BY created_at DESC
        LIMIT 1
    """, (session_id,))
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        return
    proposal_id, verdict = row

    if verdict == "confirmed" and operator_was_correct:
        action = "accepted"
    elif verdict == "falsified" and not operator_was_correct:
        action = "accepted"
    else:
        action = "overridden"

    cursor.execute("""
        UPDATE acp_proposed_resolutions
        SET operator_action = %s,
            operator_action_at = NOW(),
            operator_was_correct = %s
        WHERE id = %s
    """, (action, operator_was_correct, proposal_id))
    db_conn.commit()
    cursor.close()
    print(f"[RESOLVER] Proposal {str(proposal_id)[:8]} marked {action} by operator", flush=True)


# ============================================================
# GET /acp/status
# ============================================================

@app.route("/acp/status", methods=["GET"])
@require_auth
def status():
    """Prediction history and calibration summary. Optional ?profile=Name filter."""
    profile_filter = request.args.get("profile")
    db = get_db()

    calib = get_calibration_summary(db, profile_filter)

    cursor = db.cursor()
    cursor.execute("""
        SELECT id, question, domain, meta_confidence, consensus_confidence,
               monitoring_active, created_at
        FROM acp_sessions
        ORDER BY created_at DESC
        LIMIT 20
    """)
    cols = [d[0] for d in cursor.description]
    sessions = [dict(zip(cols, row)) for row in cursor.fetchall()]

    # Serialize datetimes
    for s in sessions:
        if s.get("created_at"):
            s["created_at"] = s["created_at"].isoformat()

    cursor.close()

    return jsonify({
        "calibration": calib,
        "recent_sessions": sessions,
    }), 200


# ============================================================
# GET /acp/profiles
# ============================================================

@app.route("/acp/profiles", methods=["GET"])
@require_auth
def profiles():
    """List all profiles with current calibration weights."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT name, domain_affinities, update_sensitivity,
               confidence_calibration, consensus_weight, updated_at
        FROM acp_profiles
        ORDER BY id
    """)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    result = []
    for row in rows:
        p = dict(zip(cols, row))
        if p.get("updated_at"):
            p["updated_at"] = p["updated_at"].isoformat()
        result.append(p)

    return jsonify(result), 200


# ============================================================
# GET /acp/session/<id>
# ============================================================

# ============================================================
# GET /acp/archive  — historical sessions with full chain
# ============================================================
#
# Powers the "Archive" panel view. Returns a list of past sessions joined
# with their per-profile predictions, any resolver proposals, and any
# finalized outcomes. This is the canonical "what they thought vs how it
# actually played out" surface — the analyst reviews past predictions to
# see how they held up against subsequent evidence.
#
# Query params:
#   topic         — filter by topic substring in question (e.g. 'Hormuz')
#   outcome       — 'all' | 'scored' | 'unscored' | 'falsified' | 'confirmed'
#   limit         — max sessions to return (default 30)
#   include_live  — if 'true', include the current live session at the top
#
# Each session in the response includes:
#   - session core (id, question, domain, created_at, consensus, meta, brief)
#   - profiles: list of per-profile predictions with profile_extra_data
#   - resolutions: list of resolver proposals for this session
#   - outcomes: list of scored outcomes from resolved predictions
#   - analyst_note: operator commentary on the session

@app.route("/acp/archive", methods=["GET"])
@require_auth
def archive():
    topic_filter  = (request.args.get("topic") or "").strip()
    outcome_filter = (request.args.get("outcome") or "all").strip().lower()
    try:
        limit = int(request.args.get("limit", "30"))
    except ValueError:
        limit = 30
    limit = max(1, min(limit, 200))

    db = get_db()
    cursor = db.cursor()

    # Build session filter clauses
    where_clauses = []
    params: list = []
    if topic_filter:
        where_clauses.append("s.question ILIKE %s")
        params.append(f"%{topic_filter}%")
    if outcome_filter == "unscored":
        # Sessions that have at least one unscored prediction
        where_clauses.append(
            "EXISTS (SELECT 1 FROM acp_session_predictions sp "
            "JOIN acp_predictions p ON p.id = sp.prediction_id "
            "WHERE sp.session_id = s.id AND p.scored = FALSE)"
        )
    elif outcome_filter == "scored":
        where_clauses.append(
            "NOT EXISTS (SELECT 1 FROM acp_session_predictions sp "
            "JOIN acp_predictions p ON p.id = sp.prediction_id "
            "WHERE sp.session_id = s.id AND p.scored = FALSE)"
        )
    elif outcome_filter in ("falsified", "confirmed"):
        where_clauses.append(
            "EXISTS (SELECT 1 FROM acp_proposed_resolutions r "
            "WHERE r.session_id = s.id AND r.verdict = %s)"
        )
        params.append(outcome_filter)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    params.append(limit)

    cursor.execute(f"""
        SELECT s.id, s.question, s.domain, s.created_at, s.closed_at,
               s.consensus_confidence, s.consensus_range_low, s.consensus_range_high,
               s.meta_confidence, s.disagreement_level, s.operator_brief,
               s.falsification_checklist, s.profiles_used, s.context_summary,
               s.analyst_note, s.analyst_note_updated_at
        FROM acp_sessions s
        {where_sql}
        ORDER BY s.created_at DESC
        LIMIT %s
    """, tuple(params))
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()

    sessions_out = []
    session_ids: list = []
    for row in rows:
        d = dict(zip(cols, row))
        d["id"] = str(d["id"])
        session_ids.append(d["id"])
        if d.get("created_at"):
            d["created_at"] = d["created_at"].isoformat()
        if d.get("closed_at"):
            d["closed_at"] = d["closed_at"].isoformat()
        if d.get("analyst_note_updated_at"):
            d["analyst_note_updated_at"] = d["analyst_note_updated_at"].isoformat()
        d["profiles"] = []
        d["resolutions"] = []
        d["outcomes"] = []
        sessions_out.append(d)

    if not sessions_out:
        cursor.close()
        return jsonify({"sessions": [], "count": 0}), 200

    # Batch-load per-profile predictions for these sessions
    cursor.execute("""
        SELECT sp.session_id, p.id, p.profile_name, p.confidence, p.prediction,
               p.reasoning_summary, p.key_assumptions, p.falsification_conditions,
               p.confidence_capped, p.confidence_cap_reason, p.error,
               p.profile_extra_data, p.analogue_reference,
               p.overall_similarity_score, p.relevant_similarity_score,
               p.scored, p.created_at
        FROM acp_predictions p
        JOIN acp_session_predictions sp ON sp.prediction_id = p.id
        WHERE sp.session_id = ANY(%s::uuid[])
        ORDER BY sp.session_id, p.created_at
    """, (session_ids,))
    pcols = [d[0] for d in cursor.description]
    preds_by_session: dict = {}
    for prow in cursor.fetchall():
        pp = dict(zip(pcols, prow))
        sid = str(pp.pop("session_id"))
        pp["id"] = str(pp["id"])
        if pp.get("created_at"):
            pp["created_at"] = pp["created_at"].isoformat()
        preds_by_session.setdefault(sid, []).append(pp)

    # Batch-load resolver proposals
    cursor.execute("""
        SELECT id, session_id, verdict, resolver_confidence, outcome_text,
               reasoning, cited_claims, claims_considered_count, claims_since,
               operator_action, operator_action_at, operator_was_correct,
               final_outcome_id, created_at
        FROM acp_proposed_resolutions
        WHERE session_id = ANY(%s::uuid[])
        ORDER BY session_id, created_at DESC
    """, (session_ids,))
    rcols = [d[0] for d in cursor.description]
    resolutions_by_session: dict = {}
    for rrow in cursor.fetchall():
        rp = dict(zip(rcols, rrow))
        sid = str(rp.pop("session_id"))
        rp["id"] = str(rp["id"])
        if rp.get("created_at"):
            rp["created_at"] = rp["created_at"].isoformat()
        if rp.get("operator_action_at"):
            rp["operator_action_at"] = rp["operator_action_at"].isoformat()
        if rp.get("claims_since") and hasattr(rp["claims_since"], "isoformat"):
            rp["claims_since"] = rp["claims_since"].isoformat()
        if rp.get("final_outcome_id"):
            rp["final_outcome_id"] = str(rp["final_outcome_id"])
        resolutions_by_session.setdefault(sid, []).append(rp)

    # Batch-load finalized outcomes — linked via prediction_id
    prediction_ids = [
        pred["id"] for preds in preds_by_session.values() for pred in preds
    ]
    outcomes_by_prediction: dict = {}
    if prediction_ids:
        cursor.execute("""
            SELECT id, prediction_id, outcome, was_correct, brier_score,
                   conditions_that_held, conditions_that_failed,
                   post_mortem_note, scored_at
            FROM acp_outcomes
            WHERE prediction_id = ANY(%s::uuid[])
            ORDER BY scored_at DESC
        """, (prediction_ids,))
        ocols = [d[0] for d in cursor.description]
        for orow in cursor.fetchall():
            op = dict(zip(ocols, orow))
            op["id"] = str(op["id"])
            pid = str(op["prediction_id"])
            op["prediction_id"] = pid
            if op.get("scored_at"):
                op["scored_at"] = op["scored_at"].isoformat()
            outcomes_by_prediction.setdefault(pid, []).append(op)

    # Stitch everything back together
    for s in sessions_out:
        sid = s["id"]
        s["profiles"] = preds_by_session.get(sid, [])
        s["resolutions"] = resolutions_by_session.get(sid, [])
        # Flatten outcomes from each prediction up to the session level
        session_outcomes = []
        for pred in s["profiles"]:
            for o in outcomes_by_prediction.get(pred["id"], []):
                session_outcomes.append(o)
        s["outcomes"] = session_outcomes

    cursor.close()
    return jsonify({"sessions": sessions_out, "count": len(sessions_out)}), 200


# ============================================================
# POST /acp/session/<id>/note  — analyst commentary
# ============================================================

@app.route("/acp/session/<session_id>/note", methods=["POST"])
@require_auth
def set_session_note(session_id):
    """Save or update the analyst's note on a session.

    Notes let the operator record their judgment at review time — e.g.
    'I disagree with the committee's read because X' or 'The consensus
    missed Y that I think is load-bearing.' The note is persisted so it
    surfaces alongside the resolver verdict in the Archive view.
    """
    data = request.get_json(force=True) or {}
    note = (data.get("note") or "").strip()
    if len(note) > 4000:
        note = note[:4000]

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE acp_sessions
        SET analyst_note = %s, analyst_note_updated_at = NOW()
        WHERE id = %s
        RETURNING id
    """, (note or None, session_id))
    row = cursor.fetchone()
    db.commit()
    cursor.close()
    if row is None:
        return jsonify({"error": "session not found"}), 404
    return jsonify({"status": "saved", "session_id": session_id}), 200


# ============================================================
# GET /acp/topic_trajectory/<topic>  — recent consensus over time
# ============================================================
#
# Returns the last N sessions for a given topic with their consensus
# confidence and meta_confidence, ordered chronologically. Powers the
# trajectory mini-chart in the Archive view so the analyst can see
# how the committee's view of a topic has drifted across cycles.

@app.route("/acp/topic_trajectory", methods=["GET"])
@require_auth
def topic_trajectory():
    topic = (request.args.get("topic") or "").strip()
    try:
        limit = int(request.args.get("limit", "15"))
    except ValueError:
        limit = 15
    limit = max(2, min(limit, 50))

    if not topic:
        return jsonify({"topic": "", "points": []}), 200

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, created_at, consensus_confidence, consensus_range_low,
               consensus_range_high, meta_confidence, disagreement_level,
               question
        FROM acp_sessions
        WHERE question ILIKE %s
          AND consensus_confidence IS NOT NULL
        ORDER BY created_at DESC
        LIMIT %s
    """, (f"%{topic}%", limit))
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    # Reverse so oldest-first for line-chart rendering
    points = []
    for row in reversed(rows):
        p = dict(zip(cols, row))
        p["id"] = str(p["id"])
        if p.get("created_at"):
            p["created_at"] = p["created_at"].isoformat()
        points.append(p)

    return jsonify({"topic": topic, "points": points, "count": len(points)}), 200


# ============================================================
# GET /acp/live  — most-recent session with live profile state
# ============================================================
#
# Powers the "Live Agent" panel view. Returns the most recent session
# (by created_at) AND the per-profile predictions that have been written
# so far. The UI polls this endpoint at ~1-2s granularity during an
# in-flight cycle and renders each profile's state (waiting / running
# / complete / failed) as rows land in acp_predictions.
#
# This works for BOTH the manual /acp/predict path and the autonomous
# monitor path, because both write rows to the same table as profiles
# complete. No SSE required for the first version; polling is cheap
# against Postgres and gives real-time-enough updates for a 15-minute
# cycle where each profile takes ~90s.
#
# "Live" = the newest session regardless of whether it's finalized. If
# the session has consensus_confidence set, it's complete. If not, it's
# still running.

@app.route("/acp/live", methods=["GET"])
@require_auth
def live_session():
    """
    Return the most recent prediction session with per-profile state for
    the Live Agent panel. Includes completed profiles, in-progress estimate
    (based on creation time), and the full expected profile roster so the
    UI can render placeholder cards for profiles that haven't started.
    """
    db = get_db()
    cursor = db.cursor()

    # Most recent session — the one to show as "live"
    cursor.execute("""
        SELECT id, question, domain, created_at, closed_at,
               consensus_confidence, consensus_range_low, consensus_range_high,
               meta_confidence, disagreement_level, operator_brief,
               falsification_checklist, profiles_used, monitoring_active,
               context_summary
        FROM acp_sessions
        ORDER BY created_at DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        return jsonify({"session": None, "profiles": []}), 200

    cols = [d[0] for d in cursor.description]
    session = dict(zip(cols, row))
    session["id"] = str(session["id"])
    if session.get("created_at"):
        session["created_at"] = session["created_at"].isoformat()
    if session.get("closed_at"):
        session["closed_at"] = session["closed_at"].isoformat()

    # Full expected roster — so the UI can render placeholder cards for
    # profiles that haven't started yet
    cursor.execute("SELECT name FROM acp_profiles ORDER BY id")
    roster = [r[0] for r in cursor.fetchall()]

    # Per-profile predictions already written for this session
    cursor.execute("""
        SELECT p.id, p.profile_name, p.confidence, p.prediction, p.reasoning_summary,
               p.confidence_capped, p.confidence_cap_reason, p.error, p.created_at,
               p.profile_extra_data, p.key_assumptions, p.falsification_conditions,
               p.analogue_reference, p.overall_similarity_score, p.relevant_similarity_score
        FROM acp_predictions p
        JOIN acp_session_predictions sp ON sp.prediction_id = p.id
        WHERE sp.session_id = %s
        ORDER BY p.created_at
    """, (session["id"],))
    pcols = [d[0] for d in cursor.description]
    prows = cursor.fetchall()
    predictions_by_name = {}
    for prow in prows:
        p = dict(zip(pcols, prow))
        p["id"] = str(p["id"])
        if p.get("created_at"):
            p["created_at"] = p["created_at"].isoformat()
        predictions_by_name[p["profile_name"]] = p

    # Compose the profile list — one entry per roster member, status reflects
    # whether a row has been written yet and if so what state it's in.
    #
    # SFA-001 follow-up (2026-04-14) — "running" state inference:
    # The DB doesn't store mid-generation state. A profile is running if
    # it has no row yet AND the session is still live AND at least one
    # profile has already completed (meaning this profile is the next
    # one the monitor is working on). The first profile of a live session
    # is also "running" immediately after session creation.
    session_is_live = session.get("consensus_confidence") is None
    has_any_completion = any(
        (p.get("error") is None and p.get("confidence") is not None) or p.get("error")
        for p in predictions_by_name.values()
    )
    running_found = False  # only mark the first-unfilled profile as running
    profiles_out = []
    for name in roster:
        pred = predictions_by_name.get(name)
        if pred is None:
            # Hasn't started yet. If the session is still live and this is
            # the first un-filled slot, treat it as actively running. The
            # monitor processes profiles sequentially so only one can be
            # running at a time.
            if session_is_live and not running_found:
                # If this is the very first profile and nothing has completed,
                # OR the prior profile has a row, we're running right now.
                status = "running"
                running_found = True
            else:
                status = "waiting"
            profiles_out.append({
                "profile_name": name,
                "status": status,
                "confidence": None,
                "prediction": None,
                "reasoning_summary": None,
                "started_at": None,
                "completed_at": None,
                "error": None,
                "confidence_capped": False,
                "confidence_cap_reason": None,
                "profile_extra_data": None,
            })
        elif pred.get("error"):
            profiles_out.append({
                "profile_name": name,
                "status": "failed",
                "confidence": None,
                "prediction": None,
                "reasoning_summary": None,
                "started_at": None,
                "completed_at": pred.get("created_at"),
                "error": pred.get("error"),
                "confidence_capped": False,
                "confidence_cap_reason": None,
                "profile_extra_data": None,
            })
        else:
            profiles_out.append({
                "profile_name": name,
                "status": "complete",
                "confidence": pred.get("confidence"),
                "prediction": pred.get("prediction"),
                "reasoning_summary": pred.get("reasoning_summary"),
                "started_at": None,
                "completed_at": pred.get("created_at"),
                "error": None,
                "confidence_capped": pred.get("confidence_capped", False),
                "confidence_cap_reason": pred.get("confidence_cap_reason"),
                "profile_extra_data": pred.get("profile_extra_data"),
                "analogue_reference": pred.get("analogue_reference"),
                "key_assumptions": pred.get("key_assumptions"),
                "falsification_conditions": pred.get("falsification_conditions"),
            })

    # Aggregate state — session is "live" if consensus_confidence is still null
    session_status = "live" if session.get("consensus_confidence") is None else "complete"
    completed_count = sum(1 for p in profiles_out if p["status"] in ("complete", "failed"))

    cursor.close()
    return jsonify({
        "session": session,
        "status": session_status,
        "profiles": profiles_out,
        "profile_count": len(roster),
        "completed_count": completed_count,
    }), 200


# ============================================================
# GET /acp/pending  — resolution queue for unscored sessions
# ============================================================

@app.route("/acp/pending", methods=["GET"])
@require_auth
def pending_resolutions():
    """
    Return completed sessions that still have unscored predictions.
    These are the sessions the operator should resolve to close the calibration loop.
    Sorted oldest-first (longest-waiting resolves first).

    Also attaches the most recent *pending* proposed resolution (from the autonomous
    resolver) to each session, if one exists. The UI uses this to pre-fill the
    scoring form with the resolver's suggested verdict and outcome text.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.id, s.question, s.domain, s.created_at,
               s.consensus_confidence, s.consensus_range_low, s.consensus_range_high,
               s.meta_confidence, s.disagreement_level, s.operator_brief,
               s.monitoring_active,
               COUNT(p.id) FILTER (WHERE p.scored = FALSE) AS unscored_count,
               COUNT(p.id) AS total_count
        FROM acp_sessions s
        JOIN acp_session_predictions sp ON sp.session_id = s.id
        JOIN acp_predictions p ON p.id = sp.prediction_id
        WHERE s.consensus_confidence IS NOT NULL
        GROUP BY s.id, s.question, s.domain, s.created_at,
                 s.consensus_confidence, s.consensus_range_low, s.consensus_range_high,
                 s.meta_confidence, s.disagreement_level, s.operator_brief,
                 s.monitoring_active
        HAVING COUNT(p.id) FILTER (WHERE p.scored = FALSE) > 0
        ORDER BY s.created_at ASC
    """)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    pending = []
    for row in rows:
        d = dict(zip(cols, row))
        # Stringify UUID and timestamp so the frontend and downstream JSON work
        d["id"] = str(d["id"])
        if d.get("created_at"):
            d["created_at"] = d["created_at"].isoformat()
        pending.append(d)

    # Attach the most recent pending proposed resolution per session, if any.
    # "Pending" = operator_action IS NULL (not yet accepted/overridden/deferred).
    if pending:
        session_ids = [p["id"] for p in pending]
        cursor.execute("""
            SELECT DISTINCT ON (session_id)
                   id, session_id, verdict, resolver_confidence,
                   outcome_text, reasoning, cited_claims,
                   claims_considered_count, claims_since, created_at
            FROM acp_proposed_resolutions
            WHERE session_id = ANY(%s::uuid[]) AND operator_action IS NULL
            ORDER BY session_id, created_at DESC
        """, (session_ids,))
        pcols = [d[0] for d in cursor.description]
        by_session = {}
        for row in cursor.fetchall():
            prop = dict(zip(pcols, row))
            if prop.get("created_at"):
                prop["created_at"] = prop["created_at"].isoformat()
            if prop.get("claims_since") and hasattr(prop["claims_since"], "isoformat"):
                prop["claims_since"] = prop["claims_since"].isoformat()
            prop["id"] = str(prop["id"])
            by_session[str(prop["session_id"])] = prop
        for p in pending:
            p["proposal"] = by_session.get(p["id"])

    cursor.close()
    return jsonify({"pending": pending, "count": len(pending)}), 200


# ============================================================
# POST /acp/resolve/<session_id>  — run the autonomous resolver
# ============================================================

@app.route("/acp/resolve/<session_id>", methods=["POST"])
@require_auth
def resolve_endpoint(session_id):
    """
    Run the autonomous resolver on a session. Writes an advisory proposal to
    acp_proposed_resolutions; does NOT modify calibration. The operator must
    accept the proposal via the Pending UI to flow it into acp_outcomes.
    """
    db = get_db()
    try:
        result = resolve_session(db, session_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"resolver failed: {e}"}), 500


@app.route("/acp/session/<session_id>", methods=["GET"])
@require_auth
def get_session(session_id):
    """Return full session including operator brief and per-profile predictions."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM acp_sessions WHERE id = %s", (session_id,))
    cols = [d[0] for d in cursor.description]
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        return jsonify({"error": "session not found"}), 404
    session = dict(zip(cols, row))
    if session.get("created_at"):
        session["created_at"] = session["created_at"].isoformat()
    if session.get("closed_at"):
        session["closed_at"] = session["closed_at"].isoformat()

    # Fetch individual predictions
    cursor.execute("""
        SELECT p.* FROM acp_predictions p
        JOIN acp_session_predictions sp ON sp.prediction_id = p.id
        WHERE sp.session_id = %s
        ORDER BY p.created_at
    """, (session_id,))
    pcols = [d[0] for d in cursor.description]
    preds = [dict(zip(pcols, r)) for r in cursor.fetchall()]
    for p in preds:
        if p.get("created_at"):
            p["created_at"] = p["created_at"].isoformat()

    cursor.close()
    session["predictions"] = preds
    return jsonify(session), 200


# ============================================================
# GET /health
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM acp_profiles")
        n = cursor.fetchone()[0]
        cursor.close()
        return jsonify({"status": "ok", "profiles": n}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


# ============================================================
# Startup: seed profiles
# ============================================================

def startup():
    import time
    for attempt in range(10):
        try:
            conn = psycopg2.connect(config.DB_URL)
            seed_profiles(conn)
            conn.close()
            print("[SWARMFISH] Profiles seeded. Service ready.", flush=True)
            return
        except Exception as e:
            print(f"[SWARMFISH] DB not ready ({e}), retrying in 3s... ({attempt+1}/10)", flush=True)
            time.sleep(3)
    print("[SWARMFISH] WARNING: could not seed profiles at startup.", flush=True)


# ============================================================
# GET /monitor/status  /  POST /monitor/toggle
# ============================================================

@app.route("/monitor/status", methods=["GET"])
@require_auth
def monitor_status():
    from monitor import get_status
    return jsonify(get_status()), 200


@app.route("/monitor/toggle", methods=["POST"])
@require_auth
def monitor_toggle():
    from monitor import get_status, set_active
    current = get_status()["active"]
    set_active(not current)
    return jsonify(get_status()), 200


@app.route("/monitor/run_now", methods=["POST"])
@require_auth
def monitor_run_now():
    """Trigger one monitoring cycle immediately in a background thread."""
    import threading
    from monitor import get_status, run_monitoring_cycle, _load_state, _save_state
    if get_status()["running"]:
        return jsonify({"status": "already_running"}), 200

    def _run():
        state = _load_state()
        state = run_monitoring_cycle(state)
        _save_state(state)

    threading.Thread(target=_run, daemon=True, name="monitor-run-now").start()
    return jsonify({"status": "started"}), 202


if __name__ == "__main__":
    startup()
    from monitor import SwarmfishMonitor
    SwarmfishMonitor().start()  # thread always runs; _ACTIVE flag gates each cycle
    app.run(host="0.0.0.0", port=7732, debug=False)
