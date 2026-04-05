"""
api_oss_activation.py — Activation pattern retrieval

URL: POST /api/plugins/oss/api_oss_activation

Input:
  topic  str   required — topic tag to query
  since  str   optional — ISO datetime, filter first_seen after this

Returns activation patterns flagged for the given topic.
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db


class OssActivation(ApiHandler):
    """Activation pattern retrieval for a topic.

    URL: POST /api/plugins/oss/api_oss_activation
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        topic = (input.get("topic") or "").strip()
        if not topic:
            return {"ok": False, "error": "topic is required"}

        since = (input.get("since") or "").strip() or None

        try:
            conn = get_conn()
            init_db(conn)
            cur = conn.cursor()

            params = [topic]
            since_clause = ""
            if since:
                since_clause = "AND ap.first_seen >= ?"
                params.append(since)

            cur.execute(f"""
                SELECT ap.id, ap.topic_tag, ap.claim_pattern,
                       ap.source_ids, ap.cluster_spread, ap.clusters_present,
                       ap.first_seen, ap.last_seen, ap.window_minutes,
                       ap.claim_count, ap.flagged_at, ap.technique_class
                FROM activation_patterns ap
                WHERE ap.topic_tag = ?
                {since_clause}
                ORDER BY ap.flagged_at DESC
            """, params)

            patterns = [dict(r) for r in cur.fetchall()]
            conn.close()

            return {
                "ok": True,
                "topic": topic,
                "patterns": patterns,
                "total": len(patterns),
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
