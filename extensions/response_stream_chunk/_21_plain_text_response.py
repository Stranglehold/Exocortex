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

Gate: only activates when the text is NOT a JSON tool call.
Two checks: (1) if the text starts with '{' it's a forming JSON response —
leave it to live_response. (2) if "tool_name" already appears anywhere in
the accumulated text, it's definitely JSON — also leave it to live_response.
The '{' check catches early chunks before "tool_name" arrives and prevents
a spurious "response" log item from being created alongside the structured
"agent" log item, which broke the collapsible step display.

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

            # Gate: skip if this is a forming or complete JSON tool call.
            # Check for '{' first — catches early chunks before "tool_name" arrives
            # and prevents a spurious response log item that breaks the step tabs.
            if full.lstrip().startswith("{") or "tool_name" in full:
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
