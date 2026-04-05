"""
api_oss_rejections.py — Rejection ledger transparency dispatcher

URL: POST /api/plugins/oss/api_oss_rejections

Input: {action: str, ...}

Actions:
  list    {reason?, source_id?, since?, limit?}
  summary {since?}
  override {rejection_id, analyst_note?}
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.rejection import get_rejections, get_rejection_summary, override_rejection


class OssRejections(ApiHandler):
    """Rejection ledger transparency — list, summary, override.

    URL: POST /api/plugins/oss/api_oss_rejections
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
                reason = (input.get("reason") or "").strip() or None
                source_id_raw = input.get("source_id")
                source_id = int(source_id_raw) if source_id_raw is not None else None
                since = (input.get("since") or "").strip() or None
                try:
                    limit = int(input.get("limit") or 100)
                except (TypeError, ValueError):
                    limit = 100
                result = get_rejections(
                    conn,
                    reason=reason,
                    source_id=source_id,
                    since=since,
                    limit=limit,
                )

            elif action == "summary":
                since = (input.get("since") or "").strip() or None
                result = get_rejection_summary(conn, since=since)

            elif action == "override":
                rejection_id = input.get("rejection_id")
                if rejection_id is None:
                    conn.close()
                    return {"ok": False, "error": "rejection_id is required for override"}
                analyst_note = (input.get("analyst_note") or "").strip() or ""
                result = override_rejection(conn, int(rejection_id), analyst_note)

            else:
                conn.close()
                return {"ok": False, "error": f"Unknown action: {action!r}"}

            conn.close()
            return {"ok": True, "action": action, "result": result}

        except Exception as e:
            return {"ok": False, "error": str(e)}
