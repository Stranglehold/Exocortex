"""
swarmfish_session — Get prediction session detail with configurable deliberation transparency.

V2: SWARMFISH runs as an A0 plugin (no external Docker service).
Data: /a0/usr/swarmfish/swarmfish.db
"""

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
        _activate()
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
