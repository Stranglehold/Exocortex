"""oss_add_topic — Register a new topic tag for the OSS ingestion pipeline."""

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


class OssAddTopic(Tool):
    """
    Register a new topic tag for the OSS ingestion pipeline.

    Tagging applies on the next ingestion pass — no restart required.

    Args:
        tag          (str): Topic tag slug, e.g. 'taiwan-strait' [required]
        display_name (str): Human-readable label (defaults to tag)
        description  (str): What this topic covers (optional)
    """

    async def execute(self, **kwargs) -> Response:
        tag          = (self.args.get("tag") or "").strip()
        display_name = (self.args.get("display_name") or "").strip() or tag
        description  = (self.args.get("description") or "").strip()
        print(f"[OSS] oss_add_topic: tag={tag!r}", flush=True)

        if not tag:
            return Response(message="[OSS] Error: tag argument required", break_loop=False)

        try:
            conn = _get_conn()
            cur  = conn.cursor()
            cur.execute("SELECT tag, active FROM topics WHERE tag=?", (tag,))
            existing = cur.fetchone()

            if existing:
                conn.close()
                active = existing["active"]
                return Response(
                    message=f"[OSS] Topic '{tag}' already registered (active={bool(active)}).",
                    break_loop=False,
                )

            cur.execute(
                "INSERT INTO topics (tag, display_name, description) VALUES (?,?,?)",
                (tag, display_name, description or None),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            return _oss_error("oss_add_topic failed", e)

        return Response(
            message=f"[OSS] Topic '{tag}' ({display_name}) added. Claims will be tagged on the next ingestion pass.",
            break_loop=False,
        )
