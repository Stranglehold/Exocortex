"""
api_oss_drift.py — Narrative drift detection

URL: POST /api/plugins/oss/api_oss_drift

Input:
  topic   str   required — topic tag to analyse
  source  str   optional — filter claims to this source name
  since   str   optional — ISO datetime, filter claims after this timestamp

Returns drift analysis, matching claims, and contradiction/retcon counts.
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.narrative_drift import detect_drift


class OssDrift(ApiHandler):
    """Narrative drift detection for a topic.

    URL: POST /api/plugins/oss/api_oss_drift
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

        source = (input.get("source") or "").strip() or None
        since  = (input.get("since") or "").strip() or None

        try:
            conn = get_conn()
            init_db(conn)
            cur = conn.cursor()

            # Fetch matching claims
            clauses = [
                "EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value = ?)",
                "c.trust_level != 'IRRELEVANT'",
            ]
            params = [topic]

            if source:
                clauses.append("s.name = ?")
                params.append(source)
            if since:
                clauses.append("c.extracted_at >= ?")
                params.append(since)

            where = "WHERE " + " AND ".join(clauses)
            cur.execute(f"""
                SELECT c.id, c.claim_text, c.article_url, c.article_title,
                       c.technique_class, c.extracted_at, c.published_at,
                       c.trust_level, c.staging_confidence, c.topic_tags,
                       s.name AS source_name, s.cluster
                FROM claims c
                JOIN sources s ON s.id = c.source_id
                {where}
                ORDER BY COALESCE(c.published_at, c.extracted_at) DESC
                LIMIT 200
            """, params)
            claims = [dict(r) for r in cur.fetchall()]
            claim_ids = [c["id"] for c in claims]

            # Contradiction and silent retcon counts for these claims
            contradiction_count = 0
            silent_retcon_count = 0
            if claim_ids:
                placeholders = ",".join("?" * len(claim_ids))
                cur.execute(f"""
                    SELECT relationship, COUNT(*) AS n
                    FROM contradictions
                    WHERE claim_a_id IN ({placeholders})
                       OR claim_b_id IN ({placeholders})
                    GROUP BY relationship
                """, claim_ids + claim_ids)
                for row in cur.fetchall():
                    if row["relationship"] == "contradiction":
                        contradiction_count += row["n"]
                    elif row["relationship"] == "retcon_silent":
                        silent_retcon_count += row["n"]

            # Run drift analysis
            drift_analysis = detect_drift(conn, topic)

            conn.close()

            return {
                "ok": True,
                "topic": topic,
                "source": source,
                "since": since,
                "claims": claims,
                "contradiction_count": contradiction_count,
                "silent_retcon_count": silent_retcon_count,
                "drift_analysis": drift_analysis,
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
