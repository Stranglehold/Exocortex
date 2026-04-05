"""
api_oss_silence.py — Silence flag retrieval

URL: POST /api/plugins/oss/api_oss_silence

Input:
  topic  str   required — topic tag to query
  since  str   optional — ISO datetime, filter first_detected after this

Returns silence flags for the topic, grouped by absent cluster.
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

import json

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db


class OssSilence(ApiHandler):
    """Silence flag retrieval for a topic.

    URL: POST /api/plugins/oss/api_oss_silence
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
                since_clause = "AND sf.first_detected >= ?"
                params.append(since)

            cur.execute(f"""
                SELECT sf.id, sf.topic_tag, sf.element,
                       sf.present_in_sources, sf.absent_from_sources,
                       sf.present_in_clusters, sf.absent_from_clusters,
                       sf.first_detected, sf.detection_method, sf.analyst_reviewed
                FROM silence_flags sf
                WHERE sf.topic_tag = ?
                {since_clause}
                ORDER BY sf.first_detected DESC
            """, params)

            flags = [dict(r) for r in cur.fetchall()]
            conn.close()

            # Group by absent_from_clusters (parse JSON array)
            by_cluster: dict = {}
            for flag in flags:
                absent_raw = flag.get("absent_from_clusters") or "[]"
                try:
                    absent_clusters = json.loads(absent_raw) if isinstance(absent_raw, str) else absent_raw
                except (json.JSONDecodeError, TypeError):
                    absent_clusters = []

                for cluster in (absent_clusters if absent_clusters else ["unknown"]):
                    by_cluster.setdefault(cluster, []).append(flag.get("element", ""))

            return {
                "ok": True,
                "topic": topic,
                "flags": flags,
                "by_cluster": by_cluster,
                "total": len(flags),
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
