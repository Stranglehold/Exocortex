"""
swarmfish_sessions — List recent SWARMFISH prediction sessions.

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


class SwarmfishSessions(Tool):
    """
    List recent SWARMFISH prediction sessions.

    Args:
        limit  (int): Number of sessions to return (default: 10, max: 100)
        domain (str): Filter by domain (optional)
    """

    async def execute(self, **kwargs) -> Response:
        _activate()
        limit  = min(int(self.args.get("limit") or 10), 100)
        domain = self.args.get("domain") or None

        try:
            from src.db import get_conn

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
