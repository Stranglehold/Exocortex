"""
api_oss_synthesis.py — Evidence synthesis for analyst questions

URL: POST /api/plugins/oss/api_oss_synthesis

Input:
  question     str   required — the analyst question to synthesize against
  question_id  str   optional — link synthesis to an active question record
  limit        int   optional — max claims to retrieve (default 40)

Calls synthesize() which retrieves semantically relevant claims from FAISS,
weights by credibility and recency, and returns structured evidence.
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.synthesis import synthesize


class OssSynthesis(ApiHandler):
    """Evidence synthesis — ask the ledger a question.

    URL: POST /api/plugins/oss/api_oss_synthesis
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        question = (input.get("question") or "").strip()
        if not question:
            return {"ok": False, "error": "question is required"}

        question_id = (input.get("question_id") or "").strip() or None
        try:
            limit = int(input.get("limit") or 40)
        except (TypeError, ValueError):
            limit = 40

        try:
            conn = get_conn()
            init_db(conn)
            result = synthesize(conn, question, question_id=question_id, limit_claims=limit)
            conn.close()

            return {"ok": True, **result}

        except Exception as e:
            return {"ok": False, "error": str(e)}
