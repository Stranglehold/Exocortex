"""
Response Finalizer — Display Correctness Fix
============================================
Hook: tool_execute_after (_22_)

Two fixes for the response tool's web UI display:

1. Complete text guarantee: live_response (_20_ in response_stream hook)
   updates the log item on every streaming chunk using DirtyJson.parse_string().
   If DirtyJson fails on the final complete chunk (e.g., markdown with **),
   the log item content freezes at the last successful partial parse.
   Fix: after the response tool executes, response.message has the complete text.
   Update log_item_response here to guarantee the full content is displayed.

2. Agent log item cleanup: _10_log_from_stream (response_stream hook) creates
   log_item_generating (type="agent") with content=raw_json on every stream
   chunk. For the response tool, this raw JSON is visible in the webUI alongside
   the response bubble. Fix: clear log_item_generating.content after the response
   tool executes — the response text is already in log_item_response.

No LLM calls. Read-only on response.message. Two log item writes.
"""

from agent import LoopData
from python.helpers.extension import Extension
from python.helpers.tool import Response


class ResponseFinalizer(Extension):
    """Finalize response display: complete text + hide raw JSON artifact."""

    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        response: Response | None = None,
        **kwargs,
    ) -> None:
        try:
            if kwargs.get("tool_name") != "response":
                return

            if not response or not response.message:
                return

            # Fix 1: ensure response bubble has complete text
            log_item = loop_data.params_temporary.get("log_item_response")
            if log_item:
                log_item.update(content=response.message)

            # Fix 2: clear raw JSON content from the agent activity item
            # log_item_generating.content holds the full JSON response stream,
            # which the webUI renders as visible text. Clear it — the response
            # is already shown in log_item_response.
            generating_item = loop_data.params_temporary.get("log_item_generating")
            if generating_item:
                generating_item.update(content="")

        except Exception:
            pass
