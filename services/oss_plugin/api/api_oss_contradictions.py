"""
api_oss_contradictions.py — Contradiction and retcon pair retrieval

URL: POST /api/plugins/oss/api_oss_contradictions

Input:
  source  str   optional — filter by source name
  topic   str   optional — filter by topic tag
  since   str   optional — ISO datetime, filter flagged_at after this

Returns contradiction pairs with full claim text and source info,
plus a summary count grouped by relationship type.
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db


class OssContradictions(ApiHandler):
    """Contradiction and retcon pair retrieval.

    URL: POST /api/plugins/oss/api_oss_contradictions
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        source = (input.get("source") or "").strip() or None
        topic  = (input.get("topic") or "").strip() or None
        since  = (input.get("since") or "").strip() or None

        try:
            conn = get_conn()
            init_db(conn)
            cur = conn.cursor()

            # Build WHERE clauses — filter on claim_a side then union with claim_b side
            # Simpler approach: fetch all contradictions that touch claims matching filters
            base_claim_ids = None

            if source or topic or since:
                clauses = []
                params = []
                if source:
                    clauses.append("s.name = ?")
                    params.append(source)
                if topic:
                    clauses.append(
                        "EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value = ?)"
                    )
                    params.append(topic)
                if since:
                    clauses.append("con.flagged_at >= ?")
                    params.append(since)

                # We filter contradictions directly
                where_parts = []
                direct_params = []

                if source or topic:
                    # Get claim IDs that match source/topic filters first
                    claim_clauses = []
                    claim_params = []
                    if source:
                        claim_clauses.append("s.name = ?")
                        claim_params.append(source)
                    if topic:
                        claim_clauses.append(
                            "EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value = ?)"
                        )
                        claim_params.append(topic)
                    claim_where = "WHERE " + " AND ".join(claim_clauses) if claim_clauses else ""
                    cur.execute(
                        f"SELECT c.id FROM claims c JOIN sources s ON s.id = c.source_id {claim_where}",
                        claim_params,
                    )
                    base_claim_ids = [r["id"] for r in cur.fetchall()]

            # Fetch contradictions with claim and source details
            if base_claim_ids is not None and len(base_claim_ids) == 0:
                # No claims match — return empty
                conn.close()
                return {
                    "ok": True,
                    "pairs": [],
                    "by_type": {
                        "contradiction": 0,
                        "retcon_silent": 0,
                        "retcon_acknowledged": 0,
                        "elaboration": 0,
                    },
                    "total": 0,
                }

            # Build the main query
            extra_clauses = []
            extra_params = []
            if base_claim_ids is not None:
                placeholders = ",".join("?" * len(base_claim_ids))
                extra_clauses.append(
                    f"(con.claim_a_id IN ({placeholders}) OR con.claim_b_id IN ({placeholders}))"
                )
                extra_params.extend(base_claim_ids + base_claim_ids)
            if since:
                extra_clauses.append("con.flagged_at >= ?")
                extra_params.append(since)

            extra_where = ("AND " + " AND ".join(extra_clauses)) if extra_clauses else ""

            cur.execute(f"""
                SELECT con.id, con.relationship, con.confidence,
                       con.source_acknowledged, con.analyst_reviewed,
                       con.flagged_at, con.notes,
                       ca.id AS claim_a_id, ca.claim_text AS claim_a_text,
                       cb.id AS claim_b_id, cb.claim_text AS claim_b_text,
                       sa.name AS source_a_name, sb.name AS source_b_name
                FROM contradictions con
                JOIN claims ca ON ca.id = con.claim_a_id
                JOIN claims cb ON cb.id = con.claim_b_id
                JOIN sources sa ON sa.id = ca.source_id
                JOIN sources sb ON sb.id = cb.source_id
                WHERE 1=1 {extra_where}
                ORDER BY con.flagged_at DESC
                LIMIT 500
            """, extra_params)

            pairs = [dict(r) for r in cur.fetchall()]
            conn.close()

            # Aggregate by type
            by_type = {
                "contradiction": 0,
                "retcon_silent": 0,
                "retcon_acknowledged": 0,
                "elaboration": 0,
            }
            for p in pairs:
                rel = p.get("relationship", "")
                if rel in by_type:
                    by_type[rel] += 1

            return {
                "ok": True,
                "pairs": pairs,
                "by_type": by_type,
                "total": len(pairs),
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
