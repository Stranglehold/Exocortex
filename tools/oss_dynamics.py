"""oss_dynamics — Compute propagation dynamics (velocity, acceleration, escape velocity) for a topic."""

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


def _oss_error(prefix: str, e: Exception) -> Response:
    return Response(message=f"[OSS] {prefix}: {e}", break_loop=False)


class OssDynamics(Tool):
    """
    Compute propagation dynamics for a topic.

    Returns velocity (unique sources/hour), acceleration, cluster coverage,
    time until correction becomes impractical, and alert level.

    Alert levels:
      INFORMATIONAL — baseline monitoring
      WARNING       — spreading faster than expected
      URGENT        — time to escape velocity < 24h

    Args:
        topic        (str): Topic tag to analyze [required]
        window_hours (int): Velocity measurement window (default 24)
    """

    async def execute(self, **kwargs) -> Response:
        topic        = (self.args.get("topic") or "").strip()
        window_hours = int(self.args.get("window_hours") or 24)
        print(f"[OSS] oss_dynamics: topic={topic!r}", flush=True)

        if not topic:
            return Response(message="[OSS] Error: topic argument required", break_loop=False)

        try:
            _ensure_plugin()
            from src.propagation_dynamics import compute_dynamics
            conn   = _get_conn()
            result = compute_dynamics(conn, topic, window_hours=window_hours)
            conn.close()
        except Exception as e:
            return _oss_error("oss_dynamics failed", e)

        alert    = result.get("alert_level", "?")
        velocity = result.get("propagation_velocity", 0.0)
        accel    = result.get("acceleration", 0.0)
        coverage = result.get("cluster_coverage_pct", 0.0)
        t_escape = result.get("time_to_escape_velocity_hours")
        half     = result.get("half_life_hours")

        t_escape_str = f"{t_escape:.1f}h" if t_escape is not None else "N/A (not accelerating)"
        half_str     = f"{half:.1f}h"     if half      is not None else "insufficient falsified claims"

        lines = [
            f"OSS Propagation Dynamics — '{topic}'",
            f"Alert:            {alert}",
            f"Velocity:         {velocity:.4f} sources/h",
            f"Acceleration:     {accel:.6f} sources/h²",
            f"Cluster coverage: {coverage:.0%}",
            f"Time to escape:   {t_escape_str}",
            f"Half-life proxy:  {half_str}",
        ]

        cur = result.get("current_window", {})
        pri = result.get("prior_window", {})
        if cur or pri:
            lines.append(
                f"Window: {cur.get('claim_count', '?')} claims (current) / "
                f"{pri.get('claim_count', '?')} claims (prior {window_hours}h)"
            )

        return Response(message="\n".join(lines), break_loop=False)
