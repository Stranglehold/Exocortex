"""
swarmfish.py — SWARMFISH V2 Analytic Consensus Protocol tools for Agent Zero

V2: SWARMFISH runs as an A0 plugin (no external Docker service).
All tools import directly from the plugin's src/ modules.
Data: /a0/usr/swarmfish/swarmfish.db (SQLite, auto-created on first predict).

Available tools:
  swarmfish_predict     — run question through committee, get operator brief + session_id
  swarmfish_session     — get session detail at transparency level 1/2/3
  swarmfish_sessions    — list recent sessions
  swarmfish_calibration — profile accuracy stats (domain-specific Brier scores)
  swarmfish_outcome     — log outcome for completed prediction, update calibration
"""

import json
import sys

sys.path.insert(0, "/a0/usr/plugins/swarmfish")

from helpers.tool import Tool, Response


# ─────────────────────────────────────────────────────────────
# swarmfish_predict
# ─────────────────────────────────────────────────────────────

class SwarmfishPredict(Tool):
    """
    Run a prediction question through the SWARMFISH analytical committee.

    Eight profiles (Base Rate Analyst, Contrarian, Historian, Reflexivity Modeler,
    Decomposer, Network Analyst, Sentiment Decoder, Risk Manager) assess the question
    independently. Results aggregate to a consensus confidence estimate.

    V2: committee is configurable — pass committee list to run a subset of profiles.
    Returns session_id for follow-up (use swarmfish_session for full deliberation).

    Args:
        question  (str):  The prediction question (required)
        domain    (str):  Domain hint: geopolitical | economic | military | general
        context   (str):  Analyst-supplied evidence and context (optional)
        committee (list): Profile names to include (default: all 8)
    """

    async def execute(self, **kwargs) -> Response:
        question  = (self.args.get("question") or "").strip()
        domain    = (self.args.get("domain") or "general").strip()
        context   = (self.args.get("context") or "").strip() or None
        committee = self.args.get("committee") or None  # list of profile names or None

        if not question:
            return Response(message="Error: question argument required", break_loop=False)

        print(f"[SWARMFISH] predict: {question[:60]!r} domain={domain} "
              f"committee={committee or 'all 8'}", flush=True)

        try:
            from swfsrc.db import get_conn
            from swfsrc.profiles import seed_profiles, load_profiles, PROFILE_NAMES
            from swfsrc.predictor import run_all_profiles
            from swfsrc.aggregator import finalize_session
            import uuid

            conn = get_conn()
            seed_profiles(conn)

            if committee:
                valid_names = [n for n in committee if n in PROFILE_NAMES]
                if not valid_names:
                    return Response(
                        message=f"Error: no valid profile names in committee. "
                                f"Available: {', '.join(PROFILE_NAMES)}",
                        break_loop=False
                    )
                profiles = load_profiles(conn, valid_names)
            else:
                profiles = load_profiles(conn)

            session_id = str(uuid.uuid4())
            context_summary = context[:200] if context else None

            conn.execute("""
                INSERT INTO acp_sessions (id, question, domain, context_summary, committee_config)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, question, domain, context_summary,
                  json.dumps(committee) if committee else None))
            conn.commit()

            assessments = await run_all_profiles(conn, profiles, question, domain, context, session_id)

            result = finalize_session(conn, session_id, question, domain, context_summary, assessments, profiles)
            if "error" in result:
                return Response(message=f"SWARMFISH error: {result['error']}", break_loop=False)

            # Format output
            consensus = result["consensus"]
            c_conf    = consensus["consensus_confidence"]
            meta      = consensus["meta_confidence"]
            brief     = result["operator_brief"]
            dissenters = consensus.get("dissenters", [])

            lines = [
                f"**SWARMFISH ensemble assessment** (session `{session_id[:8]}…`)",
                "",
                brief[:2500] if brief else "",
                "",
            ]

            if dissenters:
                lines.append("**Dissenters** (use `swarmfish_session` with level=2 for full reasoning):")
                for d in dissenters:
                    lines.append(f"  ⚡ {d['profile_name']}: {d['confidence']:.0%} "
                                  f"(divergence: {d['divergence']:.0%})")
                    lines.append(f"     {d['reasoning_summary'][:160]}")
                lines.append("")

            lines.append(f"Session ID: `{session_id}` — use `swarmfish_session` to inspect deliberation")
            return Response(message="\n".join(lines), break_loop=False)

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[SWARMFISH] predict error: {tb}", flush=True)
            return Response(message=f"SWARMFISH predict error: {e}", break_loop=False)


# ─────────────────────────────────────────────────────────────
# swarmfish_session
# ─────────────────────────────────────────────────────────────

class SwarmfishSession(Tool):
    """
    Get prediction session detail with configurable deliberation transparency.

    Level 1 — confidence + one-sentence summary per profile
    Level 2 — structured: reasoning, key assumptions, falsification conditions, dissent
    Level 3 — full LLM reasoning text for each profile (show me your work)

    Args:
        session_id (str): Session ID from swarmfish_predict (required)
        level      (int): Transparency level 1, 2, or 3 (default: 2)
    """

    async def execute(self, **kwargs) -> Response:
        session_id = (self.args.get("session_id") or "").strip()
        level      = int(self.args.get("level") or 2)

        if not session_id:
            return Response(message="Error: session_id required", break_loop=False)

        if level not in (1, 2, 3):
            level = 2

        try:
            from swfsrc.db import get_conn
            import json as _json

            conn = get_conn()
            session = conn.execute(
                "SELECT * FROM acp_sessions WHERE id = ?", (session_id,)
            ).fetchone()

            if not session:
                return Response(message=f"Session {session_id} not found", break_loop=False)

            assessments = conn.execute("""
                SELECT * FROM acp_assessments WHERE session_id = ? ORDER BY created_at
            """, (session_id,)).fetchall()

            s = dict(session)
            lines = [
                f"**SWARMFISH Session** `{session_id[:8]}…` (Level {level} transparency)",
                f"Question: {s['question']}",
                f"Domain: {s['domain']} | Consensus: {s.get('consensus_confidence', '?')} "
                f"| Agreement: {s.get('meta_confidence', '?')}",
                "",
                s.get("operator_brief", "") or "",
                "",
                f"**Profile deliberation** (Level {level}):",
                "",
            ]

            for a in assessments:
                a = dict(a)
                name = a["profile_name"]
                conf = a.get("confidence")
                conf_str = f"{conf:.0%}" if conf is not None else "ERROR"

                if a.get("error"):
                    lines.append(f"**{name}**: ❌ {a['error'][:100]}")
                    continue

                lines.append(f"**{name}**: {conf_str}"
                              + (" ⚠ capped" if a.get("confidence_capped") else ""))

                if level >= 1:
                    lines.append(f"  > {(a.get('prediction') or '')[:200]}")

                if level >= 2:
                    lines.append(f"  *Reasoning*: {(a.get('reasoning_summary') or '')[:400]}")
                    assumptions = a.get("key_assumptions")
                    if assumptions and isinstance(assumptions, str):
                        try:
                            assumptions = _json.loads(assumptions)
                        except Exception:
                            assumptions = [assumptions]
                    if assumptions:
                        lines.append(f"  *Assumptions*: {'; '.join(str(x) for x in assumptions[:3])}")
                    if a.get("confidence_cap_reason"):
                        lines.append(f"  ⚠ Cap reason: {a['confidence_cap_reason'][:200]}")

                if level >= 3:
                    full = a.get("full_reasoning") or ""
                    if full:
                        lines.append("")
                        lines.append(f"  **Full reasoning** (Level 3):")
                        lines.append(f"  {full[:3000]}")

                lines.append("")

            return Response(message="\n".join(lines), break_loop=False)

        except Exception as e:
            import traceback
            print(f"[SWARMFISH] session error: {traceback.format_exc()}", flush=True)
            return Response(message=f"SWARMFISH session error: {e}", break_loop=False)


# ─────────────────────────────────────────────────────────────
# swarmfish_sessions
# ─────────────────────────────────────────────────────────────

class SwarmfishSessions(Tool):
    """
    List recent SWARMFISH prediction sessions.

    Args:
        limit  (int): Number of sessions to return (default: 10, max: 100)
        domain (str): Filter by domain (optional)
    """

    async def execute(self, **kwargs) -> Response:
        limit  = min(int(self.args.get("limit") or 10), 100)
        domain = self.args.get("domain") or None

        try:
            from swfsrc.db import get_conn

            conn = get_conn()

            if domain:
                rows = conn.execute("""
                    SELECT id, question, domain, created_at,
                           consensus_confidence, meta_confidence
                    FROM acp_sessions
                    WHERE domain = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (domain, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, question, domain, created_at,
                           consensus_confidence, meta_confidence
                    FROM acp_sessions
                    ORDER BY created_at DESC LIMIT ?
                """, (limit,)).fetchall()

            if not rows:
                return Response(message="No SWARMFISH sessions found.", break_loop=False)

            lines = [f"**SWARMFISH sessions** (last {len(rows)}):", ""]
            for r in rows:
                r = dict(r)
                sid  = r["id"][:8]
                q    = (r["question"] or "")[:80]
                conf = r.get("consensus_confidence")
                conf_str = f" → {conf:.0%}" if conf is not None else ""
                ts   = (r.get("created_at") or "")[:16].replace("T", " ")
                lines.append(f"  `{sid}…` [{r['domain']}] {ts}{conf_str}")
                lines.append(f"    {q}")

            return Response(message="\n".join(lines), break_loop=False)

        except Exception as e:
            return Response(message=f"SWARMFISH sessions error: {e}", break_loop=False)


# ─────────────────────────────────────────────────────────────
# swarmfish_calibration
# ─────────────────────────────────────────────────────────────

class SwarmfishCalibration(Tool):
    """
    Get SWARMFISH profile calibration state.

    V2: domain-specific Brier scores show which profiles are most accurate
    for which question types. Use to guide committee composition.

    No arguments required.
    """

    async def execute(self, **kwargs) -> Response:
        print("[SWARMFISH] calibration", flush=True)

        try:
            from swfsrc.db import get_conn
            from swfsrc.calibration import get_calibration_summary, get_profile_calibration_state

            conn = get_conn()

            session_count = conn.execute("SELECT COUNT(*) FROM acp_sessions").fetchone()[0]
            scored_count  = conn.execute("SELECT COUNT(*) FROM acp_outcomes").fetchone()[0]

            profile_state   = get_profile_calibration_state(conn)
            domain_summary  = get_calibration_summary(conn)

            lines = [
                f"**SWARMFISH calibration** — {session_count} sessions, {scored_count} scored",
                "",
            ]

            if not profile_state:
                lines.append("No profiles seeded yet — run swarmfish_predict first.")
                return Response(message="\n".join(lines), break_loop=False)

            lines.append("**Profile consensus weights** (default=1.0, calibration updates with outcomes):")
            for p in profile_state:
                wt  = p["consensus_weight"].get("default", 1.0)
                n   = p["n_scored"]
                lines.append(f"  · {p['name']}: weight={wt:.2f} ({n} scored predictions)")
            lines.append("")

            if domain_summary:
                lines.append("**Calibration by domain** (lower Brier = more accurate; random = 0.25):")
                current_profile = None
                for row in domain_summary:
                    if row["profile_name"] != current_profile:
                        current_profile = row["profile_name"]
                        lines.append(f"  *{current_profile}*")
                    brier = row.get("avg_brier")
                    n     = row.get("n_predictions", 0)
                    brier_str = f"{brier:.3f}" if brier is not None else "n/a"
                    lines.append(f"    {row['domain']}: Brier={brier_str} (n={n})")
            else:
                lines.append("No calibration data yet — score sessions with swarmfish_outcome.")

            return Response(message="\n".join(lines), break_loop=False)

        except Exception as e:
            import traceback
            print(f"[SWARMFISH] calibration error: {traceback.format_exc()}", flush=True)
            return Response(message=f"SWARMFISH calibration error: {e}", break_loop=False)


# ─────────────────────────────────────────────────────────────
# swarmfish_outcome
# ─────────────────────────────────────────────────────────────

class SwarmfishOutcome(Tool):
    """
    Log outcome for a completed prediction session and update profile calibration.

    Brier score per profile is computed from the outcome.
    Calibration weights update after MIN_CALIBRATION_PREDICTIONS scored sessions.

    Args:
        session_id   (str):   Session to score (required)
        outcome      (float): 0.0=wrong, 1.0=correct, 0.5=partial (required)
        outcome_date (str):   ISO date when outcome was observed (optional)
        notes        (str):   Analyst notes on what happened (optional)
    """

    async def execute(self, **kwargs) -> Response:
        session_id   = (self.args.get("session_id") or "").strip()
        outcome_raw  = self.args.get("outcome")
        outcome_date = self.args.get("outcome_date") or None
        notes        = self.args.get("notes") or None

        if not session_id:
            return Response(message="Error: session_id required", break_loop=False)
        if outcome_raw is None:
            return Response(message="Error: outcome required (0.0=wrong, 1.0=correct, 0.5=partial)", break_loop=False)

        try:
            outcome = float(outcome_raw)
        except (TypeError, ValueError):
            return Response(message=f"Error: outcome must be a number 0.0–1.0", break_loop=False)

        if not (0.0 <= outcome <= 1.0):
            return Response(message=f"Error: outcome must be between 0.0 and 1.0", break_loop=False)

        try:
            from swfsrc.db import get_conn
            from swfsrc.calibration import record_session_outcome

            conn = get_conn()
            result = record_session_outcome(conn, session_id, outcome, outcome_date, notes)

            if "error" in result:
                return Response(message=f"SWARMFISH outcome error: {result['error']}", break_loop=False)

            lines = [
                f"**SWARMFISH outcome logged** for session `{session_id[:8]}…`",
                f"Outcome: {outcome:.0%} | Avg Brier: {result['avg_brier_score']:.4f}",
                f"Profiles scored: {result['profiles_scored']}",
                "",
            ]

            notable_list = [s for s in result["profile_scores"] if s.get("notable")]
            if notable_list:
                lines.append("**Notable episodes:**")
                for s in notable_list:
                    n = s["notable"]
                    lines.append(f"  · {s['profile_name']} ({n['type']}): {n['lesson'][:120]}")

            calibrated = [s for s in result["profile_scores"] if s.get("calibration_updated")]
            if calibrated:
                lines.append(f"Calibration weights updated: {', '.join(s['profile_name'] for s in calibrated)}")

            return Response(message="\n".join(lines), break_loop=False)

        except Exception as e:
            import traceback
            print(f"[SWARMFISH] outcome error: {traceback.format_exc()}", flush=True)
            return Response(message=f"SWARMFISH outcome error: {e}", break_loop=False)
