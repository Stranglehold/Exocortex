"""oss_health — System operational health report for the OSS intelligence ledger."""

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


class OssHealth(Tool):
    """
    System operational health report.

    Detects performance degradation that may indicate the OSS system itself
    is under targeted attack. All metrics computed deterministically.

    Health signals:
      NOMINAL     — all metrics within bounds
      DEGRADED    — 1-2 metrics outside bounds
      COMPROMISED — 3+ metrics simultaneously degraded (coordinated attack)

    No arguments required.
    """

    async def execute(self, **kwargs) -> Response:
        print("[OSS] oss_health", flush=True)

        try:
            _ensure_plugin()
            from src.meta_detection import run_health_check
            from src.ingest import is_paused, start_background_loop
            start_background_loop()  # idempotent — no-op if already running
            conn   = _get_conn()
            result = run_health_check(conn)

            cur = conn.cursor()
            cur.execute("SELECT trust_level, COUNT(*) AS n FROM claims GROUP BY trust_level")
            counts       = {row["trust_level"]: row["n"] for row in cur.fetchall()}
            total_claims = sum(counts.values())

            cur.execute("SELECT COUNT(*) AS n FROM sources")
            source_count = cur.fetchone()["n"]

            cur.execute(
                "SELECT MAX(extracted_at) AS last FROM claims WHERE trust_level != 'IRRELEVANT'"
            )
            last_claim = (cur.fetchone()["last"] or "")[:19]
            conn.close()
        except Exception as e:
            return _oss_error("oss_health failed", e)

        signal   = result.get("health_signal", "?")
        degraded = result.get("degraded_metrics", [])
        metrics  = result.get("metrics", {})

        paused_s = "paused" if is_paused() else "active"

        lines = [
            "OSS Intelligence Ledger — Health Report",
            f"Status: {signal}",
            f"Claims: {total_claims} total ({counts.get('PROMOTED', 0)} promoted, "
            f"{counts.get('STAGED', 0)} staged, {counts.get('IRRELEVANT', 0)} irrelevant)",
            f"Sources: {source_count} registered",
            f"Ingestion: {paused_s} (last claim: {last_claim or 'none'})",
        ]

        if degraded:
            lines.append(f"Degraded metrics: {', '.join(degraded)}")

        lines.append("")
        icon_map = {"OK": "✓", "WARN": "⚠", "DEGRADED": "⚠"}
        for name, m in metrics.items():
            status = m.get("status", "?")
            icon   = icon_map.get(status, "?")
            detail = ""
            if name == "false_positive_rate":
                detail = f"rate={m.get('rate', 0.0):.3f} ({m.get('promoted', '?')} promoted, {m.get('returned', '?')} returned)"
            elif name == "source_trust_skew":
                detail = f"{m.get('low_trust_count', '?')}/{m.get('total', '?')} sources below trust floor"
            elif name == "resolution_time":
                avg = m.get("avg_hours")
                detail = f"avg={avg:.1f}h" if avg is not None else "no data"
            elif name == "volume_anomaly":
                z = m.get("z_score")
                detail = f"z={z:.2f}" if z is not None else "no data"
            lines.append(f"  {icon} {name}: {status}" + (f" — {detail}" if detail else ""))

        return Response(message="\n".join(lines), break_loop=False)
