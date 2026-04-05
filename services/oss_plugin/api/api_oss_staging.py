"""
api_oss_staging.py — Claim trust lifecycle management dispatcher

URL: POST /api/plugins/oss/api_oss_staging

Input: {action: str, ...}

Actions:
  list             {topic?, limit?}
  promote          {claim_id, promoting_evidence?, falsification_predictions?}
  return_to_staged {claim_id, reason}
  mark_irrelevant  {claim_id, reason}
  promoted         {topic?, since?, limit?}
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.retcon_ledger import (
    get_staged_claims,
    promote_claim,
    return_to_staged,
    mark_irrelevant,
    get_promoted_claims,
)


class OssStaging(ApiHandler):
    """Claim trust lifecycle management — list, promote, return, irrelevant, promoted.

    URL: POST /api/plugins/oss/api_oss_staging
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        action = (input.get("action") or "").strip()
        if not action:
            return {"ok": False, "error": "action is required"}

        try:
            conn = get_conn()
            init_db(conn)

            if action == "list":
                topic = (input.get("topic") or "").strip() or None
                try:
                    limit = int(input.get("limit") or 50)
                except (TypeError, ValueError):
                    limit = 50
                result = get_staged_claims(conn, topic_tag=topic, limit=limit)

            elif action == "promote":
                claim_id = input.get("claim_id")
                if claim_id is None:
                    conn.close()
                    return {"ok": False, "error": "claim_id is required for promote"}
                promoting_evidence      = input.get("promoting_evidence") or []
                falsification_preds     = input.get("falsification_predictions") or []
                result = promote_claim(
                    conn,
                    claim_id=int(claim_id),
                    promoting_evidence=promoting_evidence,
                    falsification_predictions=falsification_preds,
                )

            elif action == "return_to_staged":
                claim_id = input.get("claim_id")
                if claim_id is None:
                    conn.close()
                    return {"ok": False, "error": "claim_id is required for return_to_staged"}
                reason = (input.get("reason") or "").strip()
                if not reason:
                    conn.close()
                    return {"ok": False, "error": "reason is required for return_to_staged"}
                result = return_to_staged(conn, int(claim_id), reason)

            elif action == "mark_irrelevant":
                claim_id = input.get("claim_id")
                if claim_id is None:
                    conn.close()
                    return {"ok": False, "error": "claim_id is required for mark_irrelevant"}
                reason = (input.get("reason") or "").strip()
                if not reason:
                    conn.close()
                    return {"ok": False, "error": "reason is required for mark_irrelevant"}
                result = mark_irrelevant(conn, int(claim_id), reason)

            elif action == "promoted":
                topic = (input.get("topic") or "").strip() or None
                since = (input.get("since") or "").strip() or None
                try:
                    limit = int(input.get("limit") or 100)
                except (TypeError, ValueError):
                    limit = 100
                result = get_promoted_claims(conn, topic_tag=topic, since=since, limit=limit)

            else:
                conn.close()
                return {"ok": False, "error": f"Unknown action: {action!r}"}

            conn.close()
            return {"ok": True, "action": action, "result": result}

        except Exception as e:
            return {"ok": False, "error": str(e)}
