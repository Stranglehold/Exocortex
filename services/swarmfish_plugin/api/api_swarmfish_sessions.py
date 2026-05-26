"""
api_swarmfish_sessions.py — List prediction sessions

URL: GET /api/plugins/swarmfish/api_swarmfish_sessions
Query params:
  limit   int   number of sessions to return (default: 20, max: 100)
  domain  str   filter by domain (optional)
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/swarmfish")

import json

from helpers.api import ApiHandler, Request

from swfsrc.db import get_conn


class SwarmfishSessions(ApiHandler):
    """List recent prediction sessions."""

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        limit = min(int(input.get("limit") or 20), 100)
        domain = input.get("domain") or None

        try:
            conn = get_conn()

            if domain:
                rows = conn.execute("""
                    SELECT id, question, domain, created_at,
                           consensus_confidence, meta_confidence, disagreement_level,
                           profiles_used, committee_config
                    FROM acp_sessions
                    WHERE domain = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (domain, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, question, domain, created_at,
                           consensus_confidence, meta_confidence, disagreement_level,
                           profiles_used, committee_config
                    FROM acp_sessions
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,)).fetchall()

            sessions = []
            for r in rows:
                d = dict(r)
                for field in ("profiles_used", "committee_config"):
                    if d.get(field) and isinstance(d[field], str):
                        try:
                            d[field] = json.loads(d[field])
                        except json.JSONDecodeError:
                            pass
                sessions.append(d)

            return {"ok": True, "sessions": sessions, "count": len(sessions)}

        except Exception as e:
            return {"ok": False, "error": str(e)}
