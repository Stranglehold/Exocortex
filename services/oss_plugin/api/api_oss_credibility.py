"""
api_oss_credibility.py — Source credibility management dispatcher

URL: POST /api/plugins/oss/api_oss_credibility

Input: {action: str, ...}

Actions:
  list — return all credibility records
  set  {source_id, overall, domain_overrides?}
  get  {source_id}
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.credibility import list_all, set_credibility, get_credibility


class OssCredibility(ApiHandler):
    """Source credibility management — list, set, get.

    URL: POST /api/plugins/oss/api_oss_credibility
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
                result = list_all(conn)

            elif action == "set":
                source_id = input.get("source_id")
                if source_id is None:
                    conn.close()
                    return {"ok": False, "error": "source_id is required for set"}
                try:
                    overall = float(input.get("overall") or 0.7)
                except (TypeError, ValueError):
                    conn.close()
                    return {"ok": False, "error": "overall must be a float between 0.0 and 1.0"}
                domain_overrides = input.get("domain_overrides") or {}
                result = set_credibility(
                    conn,
                    source_id=int(source_id),
                    overall=overall,
                    domain_overrides=domain_overrides,
                )

            elif action == "get":
                source_id = input.get("source_id")
                if source_id is None:
                    conn.close()
                    return {"ok": False, "error": "source_id is required for get"}
                result = get_credibility(conn, int(source_id))

            else:
                conn.close()
                return {"ok": False, "error": f"Unknown action: {action!r}"}

            conn.close()
            return {"ok": True, "action": action, "result": result}

        except Exception as e:
            return {"ok": False, "error": str(e)}
