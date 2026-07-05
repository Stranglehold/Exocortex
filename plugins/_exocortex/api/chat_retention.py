"""
Chat Retention control endpoint — POST /api/plugins/_exocortex/chat_retention
=============================================================================
API-key auth (daemon / tooling). Actions:
  status  {}                          -> {loaded, pinned, running}
  enforce {keep_recent?, max_age_days?, dry_run?} -> retention summary
  pin     {context_id}                -> set context.data["pinned"]=True
  unpin   {context_id}                -> set context.data["pinned"]=False

Note: pinning also works with NO endpoint / NO UI build via A0's existing rename
— prefix a chat name with 📌 and the policy keeps it (see helpers/chat_retention).
"""

import sys

_HELPER_PATH = "/a0/usr/plugins/_exocortex/helpers"
if _HELPER_PATH not in sys.path:
    sys.path.insert(0, _HELPER_PATH)

from agent import AgentContext, AgentContextType
from helpers.api import ApiHandler, Request, Response

import chat_retention


class ChatRetention(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = (input.get("action") or "").strip().lower()

        if action in ("pin", "unpin"):
            cid = input.get("context_id", "")
            ok = chat_retention.set_pinned(cid, action == "pin")
            return {"ok": ok, "pinned": action == "pin", "context_id": cid}

        if action == "enforce":
            return chat_retention.enforce_retention(
                keep_recent=int(input.get("keep_recent", 25)),
                max_age_days=int(input.get("max_age_days", 0)),  # 0 = age rule off (pure "last N")
                dry_run=bool(input.get("dry_run", False)),
            )

        if action == "status":
            ctxs = [c for c in AgentContext.all()
                    if getattr(c, "type", None) != AgentContextType.BACKGROUND]
            return {
                "loaded": len(ctxs),
                "pinned": len([c for c in ctxs if chat_retention.is_pinned(c)]),
                "running": len([c for c in ctxs if c.is_running()]),
            }

        return {"error": f"unknown action {action!r}. Use status | enforce | pin | unpin."}
