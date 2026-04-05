"""
api_oss_sources.py — Source listing with credibility data

URL: GET /api/plugins/oss/api_oss_sources

No input required. Returns all sources joined with credibility scores.
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.credibility import get_credibility_map


class OssSources(ApiHandler):
    """All sources with credibility data.

    URL: GET /api/plugins/oss/api_oss_sources
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        try:
            conn = get_conn()
            init_db(conn)
            cur = conn.cursor()

            cur.execute("""
                SELECT s.id, s.name, s.url, s.source_type, s.cluster,
                       s.confidence_score, s.total_claims, s.scrape_weight,
                       s.acknowledged_retcon_count, s.silent_retcon_count,
                       s.irrelevance_count, s.created_at
                FROM sources s
                ORDER BY s.name
            """)
            sources_raw = [dict(r) for r in cur.fetchall()]

            # Merge in analyst credibility scores (same connection)
            credibility_map = get_credibility_map(conn)
            conn.close()

            sources = []
            for s in sources_raw:
                sid = s["id"]
                s["credibility_overall"] = credibility_map.get(
                    sid, s.get("confidence_score", 0.7)
                )
                sources.append(s)

            return {
                "ok": True,
                "sources": sources,
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
