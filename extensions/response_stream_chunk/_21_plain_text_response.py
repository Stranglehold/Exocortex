"""
Plain Text Response Display
===========================
Hook: response_stream_chunk (_21_)

When a reasoning-distilled model responds in natural language (no JSON),
agent.py's handle_response_stream() only fires the `response_stream` hook
when DirtyJson successfully parses a dict — so plain text never reaches
live_response, no log item is created, and the response never appears in
the web UI.

This extension catches plain text in response_stream_chunk (which fires
for every chunk regardless of format) and creates the browser log item
directly, mirroring what live_response does for JSON responses.

Gate: only activates when the accumulated text contains no "tool_name"
key — i.e. it is not a structured JSON tool call. JSON responses are left
entirely to live_response.

No LLM calls. Fully deterministic.
"""

from python.helpers.extension import Extension
from agent import LoopData


class PlainTextResponse(Extension):

    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        stream_data: dict = {},
        **kwargs,
    ):
        try:
            full = stream_data.get("full", "")
            if not full or len(full) < 10:
                return

            # Gate: if "tool_name" appears in the text it's a JSON tool call —
            # leave it to live_response in the response_stream hook.
            if "tool_name" in full:
                return

            # Plain text response — create or update the browser log item.
            if "log_item_response" not in loop_data.params_temporary:
                loop_data.params_temporary["log_item_response"] = (
                    self.agent.context.log.log(
                        type="response",
                        heading=f"icon://chat {self.agent.agent_name}: Responding",
                    )
                )

            log_item = loop_data.params_temporary["log_item_response"]
            log_item.update(content=full)

        except Exception:
            pass
