"""
Office Feed API Handler
=======================
Serves idle-time engine activity data for the Office panel.

Route (auto-registered by A0's dispatch): GET /api/office_feed

Feed source:   /a0/usr/Exocortex/office/feed.jsonl
Status source: /a0/usr/Exocortex/office/status.json

Returns:
  {
    "entries":      list[dict],   # last 50 feed entries, newest first
    "total_cycles": int,
    "status":       dict          # current engine state
  }
"""

import json
import os

from helpers.api import ApiHandler, Request, Response

_FEED_PATH = "/a0/usr/Exocortex/office/feed.jsonl"
_STATUS_PATH = "/a0/usr/Exocortex/office/status.json"
_MAX_ENTRIES = 50


class OfficeFeed(ApiHandler):
    """GET /api/office_feed — returns activity feed and current engine status."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        entries = _read_feed()
        status = _read_status()
        return {
            "entries": entries,
            "total_cycles": len(entries),
            "status": status,
        }


def _read_feed() -> list[dict]:
    """Read feed.jsonl, return last _MAX_ENTRIES entries newest-first."""
    entries: list[dict] = []
    try:
        if os.path.exists(_FEED_PATH):
            with open(_FEED_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
    except Exception:
        pass
    entries.reverse()
    return entries[:_MAX_ENTRIES]


def _read_status() -> dict:
    """Read status.json, return default if missing."""
    try:
        if os.path.exists(_STATUS_PATH):
            with open(_STATUS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"state": "idle", "label": "Available"}
