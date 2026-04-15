"""oss_drift — Detect narrative framing drift for a topic."""

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


class OssDrift(Tool):
    """
    Detect narrative framing drift for a topic.

    Compares current window vs prior window for technique shifts, cluster
    shifts, salience changes, and volume changes.

    Args:
        topic        (str): Topic tag to analyze [required]
        window_hours (int): Window length in hours (default 24)
    """

    async def execute(self, **kwargs) -> Response:
        topic        = (self.args.get("topic") or "").strip()
        window_hours = int(self.args.get("window_hours") or 24)
        print(f"[OSS] oss_drift: topic={topic!r} window={window_hours}h", flush=True)

        if not topic:
            return Response(message="[OSS] Error: topic argument required", break_loop=False)

        try:
            _ensure_plugin()
            from src.narrative_drift import detect_drift
            conn   = _get_conn()
            result = detect_drift(conn, topic, window_hours=window_hours)
            conn.close()
        except Exception as e:
            return _oss_error("oss_drift failed", e)

        signals        = result.get("signals", {})
        drift_detected = any(s.get("detected") for s in signals.values()) if signals else result.get("drifted", False)
        drift_score    = result.get("drift_score", 0.0)
        dominant       = result.get("dominant_signal", "none")

        status = "DRIFT DETECTED" if drift_detected else "Stable"
        lines  = [
            f"OSS Narrative Drift — '{topic}'",
            f"Status: {status} (score={drift_score:.3f}, dominant={dominant})",
        ]

        cur_window = result.get("current_window", {})
        pri_window = result.get("prior_window", {})
        if cur_window or pri_window:
            lines.append(
                f"Current window: {cur_window.get('claim_count', '?')} claims | "
                f"Prior window: {pri_window.get('claim_count', '?')} claims"
            )
        lines.append("")

        for name, sig in signals.items():
            mag = sig.get("delta", sig.get("magnitude", 0.0))
            if mag > 0.05:
                desc   = sig.get("description", "")
                detail = f"  {desc}" if desc else ""
                lines.append(f"  {name}: delta={mag:.3f}{detail}")

        if not any(s.get("delta", s.get("magnitude", 0)) > 0.05 for s in signals.values()):
            lines.append("  No significant shifts detected in this window.")

        return Response(message="\n".join(lines), break_loop=False)
