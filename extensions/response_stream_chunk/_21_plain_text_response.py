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
      starts with '{' or '{' appears in the first 200 chars (handles model
      separator tokens between </think> and {), treat as JSON — skip.

Late-detection cleanup: when a model outputs plain text THEN a JSON tool call,
earlier chunks create a "response" log item before "tool_name" appears. Once
"tool_name" is detected, that partial entry is demoted to "util" so it doesn't
show as a truncated response bubble in the chat. The demotion clears the content
first (while still "response" type) so the response bubble is properly removed
client-side, then changes type to "util" to hide the process step.

No LLM calls. Fully deterministic.
"""

import asyncio
from python.helpers.extension import Extension
from agent import LoopData

# Marker key to track whether this extension created the current log item
_OWN_LOG_KEY = "_plain_text_log_item"

# Characters to search ahead for { to detect JSON with separator-token preamble
_JSON_LOOKAHEAD = 200


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
            # After </think> closes, inspect what follows — if { appears within
            # the first _JSON_LOOKAHEAD chars (handles model separator tokens
            # like <|im_sep|> between </think> and {), treat as JSON tool call.
            if "<think>" in full:
                if "</think>" not in full:
                    # Still accumulating thinking content — don't create anything yet
                    return
                # Thinking block closed — check what follows
                after_think = full.split("</think>", 1)[1].lstrip()
                # Check for JSON: { at start, tool_name anywhere, or { within
                # first _JSON_LOOKAHEAD chars (catches separator-token preambles)
                first_brace = after_think.find("{")
                is_json = (
                    after_think.startswith("{")
                    or "tool_name" in full
                    or (first_brace != -1 and first_brace < _JSON_LOOKAHEAD)
                )
                if is_json:
                    await _demote_if_owned(loop_data)
                    return
                # After </think> and it's plain text — fall through to create log item.
                # Rewrite full to only the visible text after the thinking block.
                full = after_think
                if not full or len(full) < 10:
                    return  # Nothing visible yet after think block closed

            # ── Standard JSON gate ────────────────────────────────────────────
            # Catches non-thinking models: bare { at stream start, tool_name
            # appearing in text, or { appearing within first _JSON_LOOKAHEAD
            # chars (handles whitespace/token preamble before JSON).
            stripped = full.lstrip()
            first_brace = stripped.find("{")
            is_json = (
                stripped.startswith("{")
                or "tool_name" in full
                or (first_brace != -1 and first_brace < _JSON_LOOKAHEAD)
            )
            if is_json:
                await _demote_if_owned(loop_data)
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


async def _demote_if_owned(loop_data: LoopData) -> None:
    """
    Demote an extension-owned response log item to util (hides it from chat).

    Two-phase demotion:
      1. Clear content while still "response" type — this causes _drawMessage on
         the client to remove the content div from the response bubble, preventing
         the partial JSON from staying visible.
      2. Wait for the state-monitor debounce (25ms) to fire and send the clear
         update to the client before changing the type.
      3. Change type to "util" — the process step gets class message-util and is
         hidden by CSS (.process-step.message-util { display: none }).
      4. Remove log_item_response from params_temporary so that live_response
         can create a fresh, properly-typed "response" item for the actual text.
    """
    if loop_data.params_temporary.get(_OWN_LOG_KEY):
        try:
            log_item = loop_data.params_temporary.get("log_item_response")
            if log_item:
                # Phase 1: clear content while still "response" type so the
                # response bubble's content div is removed client-side
                log_item.update(content="")
                # Wait > debounce_seconds (0.025s) so the clear reaches the client
                # before the type change turns it into a util process step
                await asyncio.sleep(0.05)
                # Phase 2: change type to util — hides the now-empty process step
                log_item.update(type="util", heading="icon://code Agent output (tool call)")
            # Remove from params so _20_live_response can create a fresh response item
            loop_data.params_temporary.pop("log_item_response", None)
        except Exception:
            pass
        loop_data.params_temporary[_OWN_LOG_KEY] = False
