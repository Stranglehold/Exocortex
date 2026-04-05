"""
api_oss_network.py — Source network topology dispatcher

URL: POST /api/plugins/oss/api_oss_network

Input: {action: str, ...}

Actions:
  get                 {source_id}
  register_edge       {source_id, connected_id, relationship_type, weight?}
  detect_coordination {topic_tag, since?}
  cascade             {source_id}
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.source_intel import get_network, register_edge, detect_coordination
from src.contamination_cascade import run_cascade


class OssNetwork(ApiHandler):
    """Source network topology — get, register_edge, detect_coordination, cascade.

    URL: POST /api/plugins/oss/api_oss_network
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

            if action == "get":
                source_id = input.get("source_id")
                if source_id is None:
                    conn.close()
                    return {"ok": False, "error": "source_id is required for get"}
                result = get_network(conn, int(source_id))

            elif action == "register_edge":
                source_id = input.get("source_id")
                connected_id = input.get("connected_id")
                relationship_type = (input.get("relationship_type") or "").strip()
                if source_id is None or connected_id is None or not relationship_type:
                    conn.close()
                    return {
                        "ok": False,
                        "error": "source_id, connected_id, and relationship_type are required",
                    }
                try:
                    weight = float(input.get("weight") or 1.0)
                except (TypeError, ValueError):
                    weight = 1.0
                result = register_edge(
                    conn,
                    source_id=int(source_id),
                    connected_id=int(connected_id),
                    relationship_type=relationship_type,
                    weight=weight,
                )

            elif action == "detect_coordination":
                topic_tag = (input.get("topic_tag") or "").strip()
                if not topic_tag:
                    conn.close()
                    return {"ok": False, "error": "topic_tag is required for detect_coordination"}
                since = (input.get("since") or "").strip() or None
                result = detect_coordination(conn, topic_tag, since=since)

            elif action == "cascade":
                source_id = input.get("source_id")
                if source_id is None:
                    conn.close()
                    return {"ok": False, "error": "source_id is required for cascade"}
                result = run_cascade(conn, int(source_id))

            else:
                conn.close()
                return {"ok": False, "error": f"Unknown action: {action!r}"}

            conn.close()
            return {"ok": True, "action": action, "result": result}

        except Exception as e:
            return {"ok": False, "error": str(e)}
