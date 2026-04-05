"""
api_oss_feed.py — Recent claims feed

URL: GET /api/plugins/oss/api_oss_feed

Input (query params or JSON body):
  topic  str   filter by topic tag (optional)
  limit  int   max results, default 50, max 200

Returns claims newest-first, excluding IRRELEVANT trust level.
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db


class OssFeed(ApiHandler):
    """Recent claims feed, newest-first, excluding IRRELEVANT.

    URL: GET /api/plugins/oss/api_oss_feed
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        topic = (input.get("topic") or "").strip() or None
        try:
            limit = min(int(input.get("limit") or 50), 200)
        except (TypeError, ValueError):
            limit = 50

        try:
            conn = get_conn()
            init_db(conn)
            cur = conn.cursor()

            if topic:
                cur.execute("""
                    SELECT c.id, c.claim_text, c.article_url, c.article_title,
                           c.technique_class, c.extracted_at, c.published_at,
                           c.trust_level, c.staging_confidence, c.topic_tags,
                           s.name AS source_name, s.cluster, s.confidence_score
                    FROM claims c
                    JOIN sources s ON s.id = c.source_id
                    WHERE EXISTS (
                        SELECT 1 FROM json_each(c.topic_tags) WHERE value = ?
                    )
                      AND c.trust_level != 'IRRELEVANT'
                    ORDER BY COALESCE(c.published_at, c.extracted_at) DESC
                    LIMIT ?
                """, (topic, limit))
            else:
                cur.execute("""
                    SELECT c.id, c.claim_text, c.article_url, c.article_title,
                           c.technique_class, c.extracted_at, c.published_at,
                           c.trust_level, c.staging_confidence, c.topic_tags,
                           s.name AS source_name, s.cluster, s.confidence_score
                    FROM claims c
                    JOIN sources s ON s.id = c.source_id
                    WHERE c.trust_level != 'IRRELEVANT'
                    ORDER BY COALESCE(c.published_at, c.extracted_at) DESC
                    LIMIT ?
                """, (limit,))

            claims = [dict(r) for r in cur.fetchall()]
            conn.close()

            return {
                "ok": True,
                "topic": topic,
                "claims": claims,
                "total": len(claims),
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
