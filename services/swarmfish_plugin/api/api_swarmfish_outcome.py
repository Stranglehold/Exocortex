"""
api_swarmfish_outcome.py — Log prediction outcome and update calibration

URL: POST /api/plugins/swarmfish/api_swarmfish_outcome

Body:
  session_id    str    required — the session to score
  outcome       float  required — 0.0 = prediction wrong, 1.0 = prediction correct,
                                  0.5 = partially correct
  outcome_date  str    optional — ISO date when outcome was observed
  notes         str    optional — analyst notes on what happened
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/swarmfish")

from helpers.api import ApiHandler, Request

from src.db import get_conn
from src.calibration import record_session_outcome


class SwarmfishOutcome(ApiHandler):
    """Log outcome for a prediction session and update Brier calibration."""

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        session_id   = (input.get("session_id") or "").strip()
        outcome_raw  = input.get("outcome")
        outcome_date = input.get("outcome_date") or None
        notes        = input.get("notes") or None

        if not session_id:
            return {"ok": False, "error": "session_id is required"}

        if outcome_raw is None:
            return {"ok": False, "error": "outcome is required (0.0=wrong, 1.0=correct, 0.5=partial)"}

        try:
            outcome = float(outcome_raw)
        except (TypeError, ValueError):
            return {"ok": False, "error": f"outcome must be a number 0.0–1.0, got: {outcome_raw}"}

        if not (0.0 <= outcome <= 1.0):
            return {"ok": False, "error": f"outcome must be between 0.0 and 1.0, got: {outcome}"}

        try:
            conn = get_conn()

            # Verify session exists
            session = conn.execute(
                "SELECT id, question FROM acp_sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if not session:
                return {"ok": False, "error": f"Session {session_id} not found"}

            result = record_session_outcome(conn, session_id, outcome, outcome_date, notes)

            if "error" in result:
                return {"ok": False, "error": result["error"]}

            return {"ok": True, **result}

        except Exception as e:
            import traceback
            print(f"[SWARM] outcome error: {traceback.format_exc()}", flush=True)
            return {"ok": False, "error": str(e)}
