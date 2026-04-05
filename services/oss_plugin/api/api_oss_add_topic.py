"""
api_oss_add_topic.py — Add a new topic tag

URL: POST /api/plugins/oss/api_oss_add_topic

Input:
  tag           str   required — short identifier slug (e.g. "iran-nuclear")
  display_name  str   required — human-readable label
  description   str   optional
  parent_tag    str   optional — parent topic tag for hierarchy

Returns {ok, tag, created} where created=True if the topic was newly inserted.
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db


class OssAddTopic(ApiHandler):
    """Add a new topic tag.

    URL: POST /api/plugins/oss/api_oss_add_topic
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        tag = (input.get("tag") or "").strip()
        if not tag:
            return {"ok": False, "error": "tag is required"}

        display_name = (input.get("display_name") or "").strip()
        if not display_name:
            return {"ok": False, "error": "display_name is required"}

        description = (input.get("description") or "").strip() or None
        parent_tag  = (input.get("parent_tag") or "").strip() or None

        try:
            conn = get_conn()
            init_db(conn)
            cur = conn.cursor()

            # Check if already exists before INSERT OR IGNORE
            cur.execute("SELECT tag FROM topics WHERE tag = ?", (tag,))
            existing = cur.fetchone()

            cur.execute("""
                INSERT OR IGNORE INTO topics (tag, display_name, description, parent_tag)
                VALUES (?, ?, ?, ?)
            """, (tag, display_name, description, parent_tag))
            conn.commit()

            created = existing is None
            conn.close()

            return {
                "ok": True,
                "tag": tag,
                "created": created,
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
