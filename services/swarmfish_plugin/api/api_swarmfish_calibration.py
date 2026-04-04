"""
api_swarmfish_calibration.py — Calibration state for all profiles

URL: GET /api/plugins/swarmfish/api_swarmfish_calibration
Query params:
  profile  str   filter by profile name (optional)

Returns per-profile Brier scores (V2: domain-specific breakdown).
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/swarmfish")

from helpers.api import ApiHandler, Request

from src.db import get_conn
from src.calibration import get_calibration_summary, get_profile_calibration_state


class SwarmfishCalibration(ApiHandler):
    """Return calibration state. V2: domain-specific Brier scores per profile."""

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        profile_name = input.get("profile") or None

        try:
            conn = get_conn()

            summary = get_calibration_summary(conn, profile_name)
            profile_state = get_profile_calibration_state(conn)

            # Session count
            session_count = conn.execute("SELECT COUNT(*) FROM acp_sessions").fetchone()[0]
            scored_count = conn.execute(
                "SELECT COUNT(*) FROM acp_outcomes"
            ).fetchone()[0]

            return {
                "ok": True,
                "session_count": session_count,
                "scored_session_count": scored_count,
                "calibration_by_domain": summary,
                "profile_weights": profile_state,
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
