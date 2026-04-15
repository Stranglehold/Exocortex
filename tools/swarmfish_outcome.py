"""
swarmfish_outcome — Log outcome for a completed prediction session and update calibration.

Brier score per profile is computed from the outcome.
Calibration weights update after MIN_CALIBRATION_PREDICTIONS scored sessions.
"""

import sys

PLUGIN_PATH = "/a0/usr/plugins/swarmfish"


def _activate() -> None:
    for _k in list(sys.modules.keys()):
        if _k == 'src' or _k.startswith('src.'):
            del sys.modules[_k]
    if PLUGIN_PATH in sys.path:
        sys.path.remove(PLUGIN_PATH)
    sys.path.insert(0, PLUGIN_PATH)


from helpers.tool import Tool, Response


class SwarmfishOutcome(Tool):
    """
    Log outcome for a completed prediction session and update profile calibration.

    Brier score per profile is computed from the outcome.
    Calibration weights update after MIN_CALIBRATION_PREDICTIONS scored sessions.

    Args:
        session_id   (str):   Session to score (required)
        outcome      (float): 0.0=wrong, 1.0=correct, 0.5=partial (required)
        outcome_date (str):   ISO date when outcome was observed (optional)
        notes        (str):   Analyst notes on what happened (optional)
    """

    async def execute(self, **kwargs) -> Response:
        _activate()
        session_id   = (self.args.get("session_id") or "").strip()
        outcome_raw  = self.args.get("outcome")
        outcome_date = self.args.get("outcome_date") or None
        notes        = self.args.get("notes") or None

        if not session_id:
            return Response(message="Error: session_id required", break_loop=False)
        if outcome_raw is None:
            return Response(message="Error: outcome required (0.0=wrong, 1.0=correct, 0.5=partial)", break_loop=False)

        try:
            outcome = float(outcome_raw)
        except (TypeError, ValueError):
            return Response(message="Error: outcome must be a number 0.0–1.0", break_loop=False)

        if not (0.0 <= outcome <= 1.0):
            return Response(message="Error: outcome must be between 0.0 and 1.0", break_loop=False)

        try:
            from src.db import get_conn
            from src.calibration import record_session_outcome

            conn = get_conn()
            result = record_session_outcome(conn, session_id, outcome, outcome_date, notes)

            if "error" in result:
                return Response(message=f"SWARMFISH outcome error: {result['error']}", break_loop=False)

            lines = [
                f"**SWARMFISH outcome logged** for session `{session_id[:8]}…`",
                f"Outcome: {outcome:.0%} | Avg Brier: {result['avg_brier_score']:.4f}",
                f"Profiles scored: {result['profiles_scored']}",
                "",
            ]

            notable_list = [s for s in result["profile_scores"] if s.get("notable")]
            if notable_list:
                lines.append("**Notable episodes:**")
                for s in notable_list:
                    n = s["notable"]
                    lines.append(f"  · {s['profile_name']} ({n['type']}): {n['lesson'][:120]}")

            calibrated = [s for s in result["profile_scores"] if s.get("calibration_updated")]
            if calibrated:
                lines.append(f"Calibration weights updated: {', '.join(s['profile_name'] for s in calibrated)}")

            return Response(message="\n".join(lines), break_loop=False)

        except Exception as e:
            import traceback
            print(f"[SWARMFISH] outcome error: {traceback.format_exc()}", flush=True)
            return Response(message=f"SWARMFISH outcome error: {e}", break_loop=False)
