"""oss_list_topics — List all topics the OSS ingestion pipeline is monitoring."""

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


class OssListTopics(Tool):
    """
    List all topics the OSS ingestion pipeline is currently monitoring.

    Shows each topic's tag, display name, claim count, and last activity.

    Args:
        active_only (str): "false" to include inactive topics (default: true)
    """

    async def execute(self, **kwargs) -> Response:
        active_only = (self.args.get("active_only") or "true").lower().strip()
        print(f"[OSS] oss_list_topics: active_only={active_only}", flush=True)

        try:
            conn = _get_conn()
            cur  = conn.cursor()
            if active_only != "false":
                cur.execute("SELECT * FROM topics WHERE active=1 ORDER BY claim_count DESC")
            else:
                cur.execute("SELECT * FROM topics ORDER BY active DESC, claim_count DESC")
            topics = [dict(r) for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            return _oss_error("oss_list_topics failed", e)

        if not topics:
            return Response(
                message="[OSS] No monitored topics registered yet. Use oss_add_topic to add one.",
                break_loop=False,
            )

        lines = [f"OSS Monitored Topics — {len(topics)} registered\n"]
        for t in topics:
            tag    = t.get("tag", "?")
            name   = t.get("display_name", tag)
            count  = t.get("claim_count", 0)
            active = t.get("active", 1)
            last   = (t.get("last_active") or "")[:10]
            desc   = t.get("description") or ""
            status = "" if active else " [inactive]"
            detail = f" — {desc}" if desc else ""
            lines.append(f"  · {tag} ({name}){status}: {count} claims | last active {last}{detail}")

        return Response(message="\n".join(lines), break_loop=False)
