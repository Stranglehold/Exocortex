"""
Idle Cycle lifecycle endpoint — POST /api/idle_cycle  (API-key auth)
====================================================================
Lets the idle_watch daemon manage autonomous cycle contexts using Agent Zero's
NATIVE context state instead of the tool-call heartbeat proxy.

Why this exists (2026-07-05): the idle engine used to infer "is the cycle still
generating?" from `cycle_heartbeat`, which the _70 sensor only updates on tool
calls. A cycle that makes ZERO tool calls (model timeout / degenerate one-line
output) never advanced the heartbeat, so the daemon declared it stale at the
20-min mark and fired a NEW cycle on top of it — the overlap / pile-up.

A0 already tracks this natively: `AgentContext.is_running()` == `task.is_alive()`
is True for the whole cycle, independent of whether it makes tool calls. This
endpoint exposes that (and cycle fire/reset) over API-key auth so the separate
daemon process can use it. Neither native endpoint fit: /api/api_message awaits
task.result() (blocks for minutes); /api/message_async returns the id
immediately but requires web/CSRF auth the daemon does not have.

Actions:
  fire   {message, lifetime_hours?}  -> create a fresh USER context, START the
                                        agent task (does NOT await), return
                                        {context_id, running}.
  status {context_id}                -> {found, running, last_message}. running
                                        is A0's own is_running(). Unknown id ->
                                        found False, running False (the context
                                        finished / was never here -> safe to fire).
  reset  {context_id}                -> kill the context's task (hung-cycle
                                        backstop). {found, reset}.
"""

from datetime import datetime, timezone

from agent import AgentContext, AgentContextType, UserMessage
from helpers.api import ApiHandler, Request, Response
from initialize import initialize_agent


class IdleCycle(ApiHandler):
    """POST /api/idle_cycle — fire | status | reset an autonomous cycle context."""

    @classmethod
    def requires_auth(cls) -> bool:
        return False  # no web session

    @classmethod
    def requires_api_key(cls) -> bool:
        return True  # daemon authenticates with X-API-KEY (same as /api/api_message)

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = (input.get("action") or "").strip().lower()

        if action == "fire":
            message = input.get("message", "")
            if not message:
                return {"error": "message required"}
            # Mirror /api/api_message context creation — but DO NOT await the task.
            config = initialize_agent()
            context = AgentContext(config=config, type=AgentContextType.USER)
            AgentContext.use(context.id)
            context.set_data("lifetime_hours", input.get("lifetime_hours", 24))
            context.last_message = datetime.now(timezone.utc)
            context.communicate(UserMessage(message=message))  # starts DeferredTask; returns now
            return {"context_id": context.id, "running": context.is_running()}

        elif action == "status":
            cid = input.get("context_id", "")
            ctx = AgentContext.get(cid) if cid else None
            if not ctx:
                return {"found": False, "running": False}
            lm = ctx.last_message
            return {
                "found": True,
                "running": ctx.is_running(),
                "last_message": lm.isoformat() if lm else None,
            }

        elif action == "reset":
            cid = input.get("context_id", "")
            ctx = AgentContext.get(cid) if cid else None
            if not ctx:
                return {"found": False, "reset": False}
            ctx.kill_process()  # DeferredTask.kill() — stop a hung cycle
            return {"found": True, "reset": True}

        return {"error": f"unknown action {action!r}. Use fire | status | reset."}
