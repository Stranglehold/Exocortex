"""
Chat Retention trigger (monologue_end, _80_)
============================================
After any conversation/cycle ends, enforce the chat retention policy so run_ui's
loaded chat set stays bounded and the UI stays responsive. Throttled so it runs
at most once per _THROTTLE seconds regardless of activity. Runs in-process (has
direct access to AgentContext._contexts + the filesystem — no HTTP/auth needed).

Config (config.json "chat_retention"): enabled (default true), keep_recent (25),
max_age_days (7), throttle_seconds (300).
"""

import json
import os
import sys
import time

from agent import LoopData
from helpers.extension import Extension

# Portable across containers: v2 uses the _exocortex plugin layout; v16/v17 use
# the older /a0/usr/Exocortex layout. Try both for the helper import and config.
_HELPER_PATHS = ("/a0/usr/plugins/_exocortex/helpers", "/a0/usr/Exocortex")
for _p in _HELPER_PATHS:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

_CONFIG_PATHS = (
    "/a0/usr/plugins/_exocortex/config/config.json",
    "/a0/usr/Exocortex/config.json",
)
_last_run = 0.0


def _load_cfg() -> dict:
    for path in _CONFIG_PATHS:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8-sig") as f:
                    return json.load(f).get("chat_retention", {})
        except Exception:
            continue
    return {}


class ChatRetention(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        global _last_run
        try:
            cfg = _load_cfg()
            if not cfg.get("enabled", True):
                return
            throttle = cfg.get("throttle_seconds", 300)
            now = time.time()
            if now - _last_run < throttle:
                return
            _last_run = now

            import chat_retention
            res = chat_retention.enforce_retention(
                keep_recent=cfg.get("keep_recent", 25),
                max_age_days=cfg.get("max_age_days", 0),
            )
            if res.get("archived"):
                print(f"[CHAT-RETENTION] archived {res['archived']} chats "
                      f"(kept {res['kept']}, pinned {res['pinned']}).", flush=True)
        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning", content=f"[CHAT-RETENTION] passthrough error: {e}"
                )
            except Exception:
                pass
