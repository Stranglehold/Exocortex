"""oss_question — Manage analyst active questions — the organizing principle for the OSS ledger."""

import os
import sys

from helpers.tool import Tool, Response

PLUGIN_PATH = os.environ.get("OSS_PLUGIN_PATH", "/a0/usr/plugins/oss")


def _ensure_plugin() -> None:
    for _k in list(sys.modules.keys()):
        if _k == 'src' or _k.startswith('src.'):
            del sys.modules[_k]
    if PLUGIN_PATH in sys.path:
        sys.path.remove(PLUGIN_PATH)
    sys.path.insert(0, PLUGIN_PATH)


def _get_conn():
    _ensure_plugin()
    from src.db import get_conn, init_db
    conn = get_conn()
    init_db(conn)
    return conn


def _jloads(s, default=None):
    _ensure_plugin()
    from src.db import jloads
    return jloads(s, default)


def _oss_error(prefix: str, e: Exception) -> Response:
    return Response(message=f"[OSS] {prefix}: {e}", break_loop=False)


class OssQuestion(Tool):
    """
    Manage analyst active questions — the organizing principle for the ledger.

    Actions:
      list       — list all active questions with attention weights
      create     — create a new question
      evolve     — mark old question inactive, create successor linked to it
      deactivate — mark a question inactive without creating a successor

    Args:
        action           (str):  list | create | evolve | deactivate [required]
        text             (str):  Question text (for create)
        question_id      (str):  Question ID (for evolve/deactivate)
        attention_weights (dict): Domain weight map — e.g. {"logistics": 0.8, "military": 0.6}
    """

    async def execute(self, **kwargs) -> Response:
        action = (self.args.get("action") or "list").strip().lower()
        print(f"[OSS] oss_question: action={action}", flush=True)

        try:
            _ensure_plugin()
            from src.questions import (
                create_question, evolve_question,
                get_active_questions, deactivate_question,
            )
            conn = _get_conn()
        except Exception as e:
            return _oss_error("oss_question import failed", e)

        try:
            if action == "list":
                questions = get_active_questions(conn)
                conn.close()
                if not questions:
                    return Response(
                        message="OSS Active Questions — none registered. Use action=create to add one.",
                        break_loop=False,
                    )
                lines = [f"OSS Active Questions — {len(questions)}\n"]
                for q in questions:
                    qid     = q.get("id", "?")[:8]
                    text    = q.get("text", "")
                    updated = (q.get("last_updated") or "")[:16]
                    weights = _jloads(q.get("attention_weights"), default={})
                    w_str   = " ".join(f"{k}:{v:.1f}" for k, v in weights.items()) if weights else "none"
                    lines.append(f"  [{qid}] {text}")
                    lines.append(f"    Updated: {updated} | Weights: {w_str}\n")
                return Response(message="\n".join(lines), break_loop=False)

            elif action == "create":
                text    = (self.args.get("text") or "").strip()
                weights = self.args.get("attention_weights") or {}
                if not text:
                    conn.close()
                    return Response(message="[OSS] create requires text", break_loop=False)
                q = create_question(conn, text, attention_weights=weights)
                conn.close()
                return Response(
                    message=f"OSS Question created — id={q.get('id', '?')[:8]}: {text}",
                    break_loop=False,
                )

            elif action == "evolve":
                qid     = (self.args.get("question_id") or "").strip()
                text    = (self.args.get("text") or "").strip()
                weights = self.args.get("attention_weights") or {}
                if not qid or not text:
                    conn.close()
                    return Response(message="[OSS] evolve requires question_id and text", break_loop=False)
                new_q = evolve_question(conn, qid, text, attention_weights=weights)
                conn.close()
                return Response(
                    message=f"OSS Question evolved — old id={qid[:8]} → new id={new_q.get('id', '?')[:8]}: {text}",
                    break_loop=False,
                )

            elif action == "deactivate":
                qid = (self.args.get("question_id") or "").strip()
                if not qid:
                    conn.close()
                    return Response(message="[OSS] deactivate requires question_id", break_loop=False)
                ok = deactivate_question(conn, qid)
                conn.close()
                if ok:
                    return Response(message=f"OSS Question {qid[:8]} deactivated.", break_loop=False)
                return Response(message=f"[OSS] Question {qid[:8]} not found.", break_loop=False)

            else:
                conn.close()
                return Response(
                    message=f"[OSS] Unknown action '{action}'. Valid: list / create / evolve / deactivate",
                    break_loop=False,
                )

        except Exception as e:
            try:
                conn.close()
            except Exception:
                pass
            return _oss_error(f"oss_question action={action} failed", e)
