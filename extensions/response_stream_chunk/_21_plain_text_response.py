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

Late-detection cleanup: when a model outputs plain text THEN a JSON tool call,
earlier chunks create a "response" log item before "tool_name" appears. Once
"tool_name" is detected, that partial entry is demoted to "util" so it doesn't
show as a truncated response message in the chat.

No LLM calls. Fully deterministic.
"""

from python.helpers.extension import Extension
from agent import LoopData

# Marker key to track whether this extension created the current log item
_OWN_LOG_KEY = "_plain_text_log_item"


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
                # Late-detection cleanup: if we already created a response log item
                # from earlier plain-text chunks, demote it to "util" so it doesn't
                # show as a truncated response bubble in the chat.
                if loop_data.params_temporary.get(_OWN_LOG_KEY):
                    try:
                        log_item = loop_data.params_temporary.get("log_item_response")
                        if log_item:
                            log_item.update(type="util", heading="icon://code Agent output (tool call)")
                    except Exception:
                        pass
                    loop_data.params_temporary[_OWN_LOG_KEY] = False
                return

            # Plain text response — create or update the browser log item.
            if "log_item_response" not in loop_data.params_temporary:
                loop_data.params_temporary["log_item_response"] = (
                    self.agent.context.log.log(
                        type="response",
                        heading=f"icon://chat {self.agent.agent_name}: Responding",
                    )
                )
                loop_data.params_temporary[_OWN_LOG_KEY] = True

            log_item = loop_data.params_temporary["log_item_response"]
            log_item.update(content=full)

        except Exception:
            pass
