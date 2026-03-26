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
Three checks:
  (1) if the text starts with '{' it's a forming JSON response — skip.
  (2) if "tool_name" appears anywhere in the accumulated text — skip.
  (3) if the text starts with '<think>' (reasoning model thinking block)
      and the block hasn't closed yet — skip. Reasoning models stream
      <think>...</think> before the JSON tool call; without this check the
      extension treats the thinking content as plain text and creates a
      response log item that shows raw JSON in the chat once the tool call
      starts appending. After </think> closes, check what follows: if it
      starts with '{', it's a JSON tool call — skip.

Late-detection cleanup: when a model outputs plain text THEN a JSON tool call,
earlier chunks create a "response" log item before "tool_name" appears. Once
"tool_name" is detected, that partial entry is demoted to "util" so it doesn't
show as a truncated response bubble in the chat.

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

            # ── Thinking-block gate ───────────────────────────────────────────
            # Reasoning-distilled models stream <think>...</think> before the
            # JSON tool call. stream_data["full"] is raw (pre-strip), so the
            # accumulated text starts with <think> rather than {.
            # While inside the thinking block, hold off entirely.
            # After </think> closes, inspect what follows — if it's { or already
            # contains tool_name, treat the whole response as a JSON tool call.
            if "<think>" in full:
                if "</think>" not in full:
                    # Still accumulating thinking content — don't create anything yet
                    return
                # Thinking block closed — check what follows
                after_think = full.split("</think>", 1)[1].lstrip()
                if after_think.startswith("{") or "tool_name" in full:
                    _demote_if_owned(loop_data)
                    return
                # After </think> and it's plain text — fall through to create log item.
                # Rewrite full to only the visible text after the thinking block.
                full = after_think

            # ── Standard JSON gate ────────────────────────────────────────────
            # Catches non-thinking models: bare { at stream start, or tool_name
            # appearing before we've created a log item.
            if full.lstrip().startswith("{") or "tool_name" in full:
                _demote_if_owned(loop_data)
                return

            # ── Plain text response — create or update the browser log item ───
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


def _demote_if_owned(loop_data: LoopData) -> None:
    """Demote an extension-owned response log item to util (hides it from chat)."""
    if loop_data.params_temporary.get(_OWN_LOG_KEY):
        try:
            log_item = loop_data.params_temporary.get("log_item_response")
            if log_item:
                log_item.update(type="util", heading="icon://code Agent output (tool call)")
        except Exception:
            pass
        loop_data.params_temporary[_OWN_LOG_KEY] = False
