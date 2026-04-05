"""
api_oss_topics.py — Topic listing

URL: GET /api/plugins/oss/api_oss_topics

No input required. Returns all active topics with claim counts.
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db


class OssTopics(ApiHandler):
    """List all topics with claim counts.

    URL: GET /api/plugins/oss/api_oss_topics
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
                SELECT t.tag, t.display_name, t.description, t.parent_tag,
                       t.created_at, t.last_active, t.claim_count, t.active,
                       COUNT(c.id) AS live_claim_count
                FROM topics t
                LEFT JOIN claims c ON (
                    EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value = t.tag)
                    AND c.trust_level != 'IRRELEVANT'
                )
                GROUP BY t.tag
                ORDER BY t.active DESC, t.last_active DESC
            """)

            topics = [dict(r) for r in cur.fetchall()]
            conn.close()

            return {
                "ok": True,
                "topics": topics,
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
