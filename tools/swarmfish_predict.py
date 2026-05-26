"""
swarmfish_predict — Run a prediction question through the SWARMFISH analytical committee.

V2: SWARMFISH runs as an A0 plugin (no external Docker service).
Data: /a0/usr/swarmfish/swarmfish.db (SQLite, auto-created on first predict).
"""

import json
import sys

PLUGIN_PATH = "/a0/usr/plugins/swarmfish"


def _activate() -> None:
    for _k in list(sys.modules.keys()):
        if _k == 'src' or _k.startswith('src.'):
            del sys.modules[_k]
    if PLUGIN_PATH in sys.path:
        sys.path.remove(PLUGIN_PATH)
    sys.path.insert(0, PLUGIN_PATH)


from helpers.tool import Tool, Response


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
        _activate()
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
