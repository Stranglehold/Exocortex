"""
questions.py — V2 active question management.

The active question is the analyst's organizing principle. Claims are
relevant relative to the question, not just keyword-matching a topic.
Multiple questions can coexist. Questions evolve — each evolution
is recorded as a new question linked to the previous.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from .db import get_conn, jloads, jdumps, new_id

log = logging.getLogger("[QUESTIONS]")


def create_question(conn, text: str, evolved_from_id: str = None,
                    attention_weights: dict = None) -> dict:
    """
    Create a new active_question row.
    If evolved_from_id is given, records it in evolved_from JSON array.
    Returns full row as dict.
    """
    try:
        qid = new_id()
        now = datetime.now(timezone.utc).isoformat()
        evolved_from = [evolved_from_id] if evolved_from_id else []
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO active_questions
                (id, text, evolved_from, attention_weights, created_at, last_updated, active)
            VALUES (?,?,?,?,?,?,1)
        """, (
            qid,
            text.strip(),
            jdumps(evolved_from),
            jdumps(attention_weights or {}),
            now,
            now,
        ))
        conn.commit()
        log.info(f"Created question id={qid}: {text[:80]!r}")
        return get_question(conn, qid) or {}
    except Exception as e:
        log.warning(f"create_question failed: {e}")
        raise


def update_question(conn, question_id: str, text: str = None,
                    attention_weights: dict = None) -> dict:
    """
    Update text and/or attention_weights. Sets last_updated = datetime('now').
    Returns the updated row as dict.
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.cursor()
        # Build SET clause dynamically based on what was provided
        sets = ["last_updated=?"]
        params = [now]
        if text is not None:
            sets.append("text=?")
            params.append(text.strip())
        if attention_weights is not None:
            sets.append("attention_weights=?")
            params.append(jdumps(attention_weights))
        params.append(question_id)
        cur.execute(
            f"UPDATE active_questions SET {', '.join(sets)} WHERE id=?",
            params,
        )
        conn.commit()
        log.info(f"Updated question id={question_id}")
        return get_question(conn, question_id) or {}
    except Exception as e:
        log.warning(f"update_question failed: {e}")
        raise


def evolve_question(conn, question_id: str, new_text: str,
                    attention_weights: dict = None) -> dict:
    """
    Marks old question inactive (active=0), creates new question with
    evolved_from=[question_id]. Returns new question dict.
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        # Deactivate the old question
        conn.execute(
            "UPDATE active_questions SET active=0, last_updated=? WHERE id=?",
            (now, question_id),
        )
        conn.commit()
        # Create successor
        new_q = create_question(conn, new_text, evolved_from_id=question_id,
                                attention_weights=attention_weights)
        log.info(f"Evolved question {question_id} → {new_q.get('id')}")
        return new_q
    except Exception as e:
        log.warning(f"evolve_question failed: {e}")
        raise


def get_active_questions(conn) -> list:
    """Return all questions where active=1, ordered by last_updated DESC."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM active_questions WHERE active=1 ORDER BY last_updated DESC"
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_active_questions failed: {e}")
        return []


def get_question(conn, question_id: str) -> Optional[dict]:
    """Return single question row by id, or None."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM active_questions WHERE id=?", (question_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        log.warning(f"get_question failed: {e}")
        return None


def deactivate_question(conn, question_id: str) -> bool:
    """
    Set active=0 on a question. Returns True if a row was updated.
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.cursor()
        cur.execute(
            "UPDATE active_questions SET active=0, last_updated=? WHERE id=?",
            (now, question_id),
        )
        conn.commit()
        updated = cur.rowcount > 0
        if updated:
            log.info(f"Deactivated question id={question_id}")
        return updated
    except Exception as e:
        log.warning(f"deactivate_question failed: {e}")
        return False
