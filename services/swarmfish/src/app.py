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
from oss_bridge import get_oss_context

app = Flask(__name__)


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
    """Insert a new session row and return session_id."""
    session_id = str(uuid.uuid4())
    context_summary = context[:200] if context else None
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO acp_sessions (id, question, domain, context_summary)
        VALUES (%s, %s, %s, %s)
    """, (session_id, question, domain, context_summary))
    db.commit()
    cursor.close()
    return session_id, context_summary


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

    predictions = []
    for profile in profiles_list:
        result = run_profile(
            db, profile, question, domain,
            context=context,
            session_id=session_id,
            context_summary=context_summary,
        )
        result["domain"] = domain
        predictions.append(result)

    result = finalize_session(
        db, session_id, question, domain, context_summary,
        predictions, profiles_dict
    )
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
            return jsonify({"scored": results}), 200
        else:
            result = record_outcome(
                db, prediction_id, outcome_text, bool(was_correct),
                conditions_held, conditions_failed, post_mortem
            )
            return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


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
