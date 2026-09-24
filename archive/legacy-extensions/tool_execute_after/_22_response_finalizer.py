"""
Response Finalizer — Display Correctness Fix
============================================
Hook: tool_execute_after (_22_)

Ensures the web UI displays the complete response text by updating the log
item with response.message after the response tool finishes executing.

Problem: live_response (_20_ in response_stream hook) updates the log item on
every streaming chunk using DirtyJson.parse_string(). If DirtyJson fails on
the final complete chunk (e.g., due to markdown special characters like **),
the log item content freezes at the last successful partial parse — truncating
the display.

Fix: After the response tool executes, response.message contains the complete
text. Update the log item here to guarantee the full content is displayed.

Note: raw JSON clearing from log_item_generating is handled generically by
_20_clear_generating_content in response_stream_end (covers all tool calls).

No LLM calls. Read-only on response.message. One log item write.
"""

from agent import LoopData
from helpers.extension import Extension
from helpers.tool import Response


class ResponseFinalizer(Extension):
    """Update response log item with complete text after streaming ends."""

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

            log_item = loop_data.params_temporary.get("log_item_response")
            if not log_item:
                return

            log_item.update(content=response.message)

        except Exception:
            pass
