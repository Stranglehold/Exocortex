"""
swarmfish_calibration — Get SWARMFISH profile calibration state.

V2: domain-specific Brier scores show which profiles are most accurate
for which question types. Use to guide committee composition.
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


class SwarmfishCalibration(Tool):
    """
    Get SWARMFISH profile calibration state.

    V2: domain-specific Brier scores show which profiles are most accurate
    for which question types. Use to guide committee composition.

    No arguments required.
    """

    async def execute(self, **kwargs) -> Response:
        _activate()
        print("[SWARMFISH] calibration", flush=True)

        try:
            from src.db import get_conn
            from src.calibration import get_calibration_summary, get_profile_calibration_state

            conn = get_conn()

            session_count = conn.execute("SELECT COUNT(*) FROM acp_sessions").fetchone()[0]
            scored_count  = conn.execute("SELECT COUNT(*) FROM acp_outcomes").fetchone()[0]

            profile_state   = get_profile_calibration_state(conn)
            domain_summary  = get_calibration_summary(conn)

            lines = [
                f"**SWARMFISH calibration** — {session_count} sessions, {scored_count} scored",
                "",
            ]

            if not profile_state:
                lines.append("No profiles seeded yet — run swarmfish_predict first.")
                return Response(message="\n".join(lines), break_loop=False)

            lines.append("**Profile consensus weights** (default=1.0, calibration updates with outcomes):")
            for p in profile_state:
                wt  = p["consensus_weight"].get("default", 1.0)
                n   = p["n_scored"]
                lines.append(f"  · {p['name']}: weight={wt:.2f} ({n} scored predictions)")
            lines.append("")

            if domain_summary:
                lines.append("**Calibration by domain** (lower Brier = more accurate; random = 0.25):")
                current_profile = None
                for row in domain_summary:
                    if row["profile_name"] != current_profile:
                        current_profile = row["profile_name"]
                        lines.append(f"  *{current_profile}*")
                    brier = row.get("avg_brier")
                    n     = row.get("n_predictions", 0)
                    brier_str = f"{brier:.3f}" if brier is not None else "n/a"
                    lines.append(f"    {row['domain']}: Brier={brier_str} (n={n})")
            else:
                lines.append("No calibration data yet — score sessions with swarmfish_outcome.")

            return Response(message="\n".join(lines), break_loop=False)

        except Exception as e:
            import traceback
            print(f"[SWARMFISH] calibration error: {traceback.format_exc()}", flush=True)
            return Response(message=f"SWARMFISH calibration error: {e}", break_loop=False)
