"""
api_oss_questions.py — Active question management dispatcher

URL: POST /api/plugins/oss/api_oss_questions

Input: {action: str, ...}

Actions:
  list       — return all active questions
  create     {text, attention_weights?}
  update     {question_id, text?, attention_weights?}
  evolve     {question_id, new_text, attention_weights?}
  deactivate {question_id}
  get        {question_id}
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.questions import (
    get_active_questions,
    create_question,
    update_question,
    evolve_question,
    deactivate_question,
    get_question,
)


class OssQuestions(ApiHandler):
    """Active question management — list, create, update, evolve, deactivate, get.

    URL: POST /api/plugins/oss/api_oss_questions
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
                result = get_active_questions(conn)

            elif action == "create":
                text = (input.get("text") or "").strip()
                if not text:
                    conn.close()
                    return {"ok": False, "error": "text is required for create"}
                attention_weights = input.get("attention_weights") or {}
                result = create_question(conn, text, attention_weights=attention_weights)

            elif action == "update":
                question_id = (input.get("question_id") or "").strip()
                if not question_id:
                    conn.close()
                    return {"ok": False, "error": "question_id is required for update"}
                text = (input.get("text") or "").strip() or None
                attention_weights = input.get("attention_weights")
                result = update_question(
                    conn, question_id,
                    text=text,
                    attention_weights=attention_weights,
                )

            elif action == "evolve":
                question_id = (input.get("question_id") or "").strip()
                if not question_id:
                    conn.close()
                    return {"ok": False, "error": "question_id is required for evolve"}
                new_text = (input.get("new_text") or "").strip()
                if not new_text:
                    conn.close()
                    return {"ok": False, "error": "new_text is required for evolve"}
                attention_weights = input.get("attention_weights")
                result = evolve_question(
                    conn, question_id, new_text,
                    attention_weights=attention_weights,
                )

            elif action == "deactivate":
                question_id = (input.get("question_id") or "").strip()
                if not question_id:
                    conn.close()
                    return {"ok": False, "error": "question_id is required for deactivate"}
                result = deactivate_question(conn, question_id)

            elif action == "get":
                question_id = (input.get("question_id") or "").strip()
                if not question_id:
                    conn.close()
                    return {"ok": False, "error": "question_id is required for get"}
                result = get_question(conn, question_id)
                if result is None:
                    conn.close()
                    return {"ok": False, "error": f"Question {question_id!r} not found"}

            else:
                conn.close()
                return {"ok": False, "error": f"Unknown action: {action!r}"}

            conn.close()
            return {"ok": True, "action": action, "result": result}

        except Exception as e:
            return {"ok": False, "error": str(e)}
