"""
api_oss_hypotheses.py — Hypothesis registry dispatcher

URL: POST /api/plugins/oss/api_oss_hypotheses

Input: {action: str, ...}

Actions:
  list              {observation_id?, status?, limit?}
  register          {observation_id, candidate_explanation, predictions?, initial_confidence?}
  confirm_prediction {hypothesis_id}
  falsify           {hypothesis_id, evidence}
  promote           {hypothesis_id}
  update_confidence {hypothesis_id, confidence}
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.hypothesis import (
    get_hypotheses,
    register_hypothesis,
    confirm_prediction,
    falsify_hypothesis,
    promote_hypothesis,
    update_confidence,
)


class OssHypotheses(ApiHandler):
    """Hypothesis registry — list, register, confirm, falsify, promote, update confidence.

    URL: POST /api/plugins/oss/api_oss_hypotheses
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
                observation_id = input.get("observation_id")
                status = (input.get("status") or "").strip() or None
                try:
                    limit = int(input.get("limit") or 50)
                except (TypeError, ValueError):
                    limit = 50
                result = get_hypotheses(
                    conn,
                    observation_id=observation_id,
                    status=status,
                    limit=limit,
                )

            elif action == "register":
                observation_id = input.get("observation_id")
                if observation_id is None:
                    conn.close()
                    return {"ok": False, "error": "observation_id is required for register"}
                candidate = (input.get("candidate_explanation") or "").strip()
                if not candidate:
                    conn.close()
                    return {"ok": False, "error": "candidate_explanation is required for register"}
                predictions = input.get("predictions") or []
                try:
                    initial_confidence = float(input.get("initial_confidence") or 0.0)
                except (TypeError, ValueError):
                    initial_confidence = 0.0
                result = register_hypothesis(
                    conn,
                    observation_id=observation_id,
                    candidate_explanation=candidate,
                    predictions=predictions,
                    initial_confidence=initial_confidence,
                )

            elif action == "confirm_prediction":
                hypothesis_id = input.get("hypothesis_id")
                if hypothesis_id is None:
                    conn.close()
                    return {"ok": False, "error": "hypothesis_id is required for confirm_prediction"}
                result = confirm_prediction(conn, hypothesis_id)

            elif action == "falsify":
                hypothesis_id = input.get("hypothesis_id")
                if hypothesis_id is None:
                    conn.close()
                    return {"ok": False, "error": "hypothesis_id is required for falsify"}
                evidence = (input.get("evidence") or "").strip()
                result = falsify_hypothesis(conn, hypothesis_id, evidence)

            elif action == "promote":
                hypothesis_id = input.get("hypothesis_id")
                if hypothesis_id is None:
                    conn.close()
                    return {"ok": False, "error": "hypothesis_id is required for promote"}
                result = promote_hypothesis(conn, hypothesis_id)

            elif action == "update_confidence":
                hypothesis_id = input.get("hypothesis_id")
                if hypothesis_id is None:
                    conn.close()
                    return {"ok": False, "error": "hypothesis_id is required for update_confidence"}
                try:
                    confidence = float(input.get("confidence") or 0.0)
                except (TypeError, ValueError):
                    conn.close()
                    return {"ok": False, "error": "confidence must be a float"}
                result = update_confidence(conn, hypothesis_id, confidence)

            else:
                conn.close()
                return {"ok": False, "error": f"Unknown action: {action!r}"}

            conn.close()
            return {"ok": True, "action": action, "result": result}

        except Exception as e:
            return {"ok": False, "error": str(e)}
