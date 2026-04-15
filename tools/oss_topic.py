"""oss_topic — Query claims about a topic from the OSS intelligence ledger."""

import json
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


class OssTopic(Tool):
    """
    Query claims about a topic from the OSS intelligence ledger.

    Args:
        topic      (str):  Topic tag to query (e.g. 'iran-hormuz', 'taiwan-strait') [required]
        limit      (int):  Max claims to return (default 50)
        trust_level (str): Filter to STAGED / PROMOTED / FALSIFIED / RETURNED_TO_STAGED / IRRELEVANT
    """

    async def execute(self, **kwargs) -> Response:
        topic       = (self.args.get("topic") or "").strip()
        limit       = int(self.args.get("limit") or 50)
        trust_level = (self.args.get("trust_level") or "").strip().upper() or None
        print(f"[OSS] oss_topic: topic={topic!r} limit={limit} trust_level={trust_level}", flush=True)

        if not topic:
            return Response(message="[OSS] Error: topic argument required", break_loop=False)

        try:
            conn = _get_conn()
            cur  = conn.cursor()

            if trust_level:
                sql    = "SELECT c.*, s.name AS source_name FROM claims c JOIN sources s ON s.id=c.source_id WHERE c.topic_tags LIKE ? AND c.trust_level=? ORDER BY c.extracted_at DESC LIMIT ?"
                params = [f"%{topic}%", trust_level, limit]
            else:
                sql    = "SELECT c.*, s.name AS source_name FROM claims c JOIN sources s ON s.id=c.source_id WHERE c.topic_tags LIKE ? ORDER BY c.extracted_at DESC LIMIT ?"
                params = [f"%{topic}%", limit]

            cur.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            return _oss_error("oss_topic query failed", e)

        if not rows:
            return Response(
                message=f"OSS Intelligence Ledger — no claims found for topic '{topic}'",
                break_loop=False,
            )

        trust_order = {"PROMOTED": 0, "STAGED": 1, "RETURNED_TO_STAGED": 2, "IRRELEVANT": 3, "FALSIFIED": 4}
        rows.sort(key=lambda c: trust_order.get(c.get("trust_level", ""), 9))

        lines = [f"OSS Intelligence Ledger — {len(rows)} claim(s) for '{topic}'\n"]
        for c in rows[:15]:
            trust  = c.get("trust_level", "?")
            text   = (c.get("claim_text") or "")[:160]
            source = c.get("source_name", "?")
            tech   = c.get("technique_class") or "none"
            conf   = c.get("staging_confidence")
            conf_s = f", conf={conf:.2f}" if conf is not None else ""
            lines.append(f"[{trust}] {text}")
            lines.append(f"  Source: {source} | technique: {tech}{conf_s}\n")

        if len(rows) > 15:
            lines.append(f"… and {len(rows) - 15} additional claims (use trust_level filter to narrow).")

        return Response(message="\n".join(lines), break_loop=False)
