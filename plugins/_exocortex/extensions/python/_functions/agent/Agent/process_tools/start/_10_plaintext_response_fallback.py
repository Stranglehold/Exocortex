"""
Plain-Text Response Fallback
============================
Hook: _functions/agent/Agent/process_tools/start

Replaces the Session 054 core patch to `helpers/extract_tools.py`, which was a
wholesale stale copy that dropped six symbols A0 v2.9 calls and broke every turn
on a fresh install. This does the same job with zero core modification, so there
is nothing to re-base on the next A0 bump. (Tier 1.1 step 2.)

The problem
-----------
Reasoning-distilled models sometimes answer in prose instead of emitting a JSON
tool call. A0 v2.9 already handles that — in `agent.py`:

    if (llm_result.mode == "responses"
        and extract_tools.extract_tool_request(message) is None
        and not extract_tools.is_misformatted_tool_request(message)):
        return await self._execute_tool_request(tool_name="response", ...)
    return await self.process_tools(message)

but it is gated on `mode == "responses"`. Our models run
`a0_api_mode: chat_completions`, so that branch never fires for us and plain
prose falls through to `process_tools`, finds no tool request, and triggers the
`fw.msg_misformat.md` warning — the misformat loop from Session 054.

What this does
--------------
At `process_tools/start`, if the message is non-empty, is NOT a valid tool
request, and is NOT a misformatted one, rewrite `msg` into an explicit
`response` tool call and let A0's own machinery execute it. Inputs are mutated,
not short-circuited: `process_tools` still runs, extracts, validates and
dispatches exactly as it would for a model that emitted the call itself.

Keeping v2.9's `is_misformatted_tool_request` guard is deliberate and is the
reason this is placed here rather than inside `json_parse_dirty` as the old
patch was. The old placement was one layer too low: it swallowed *malformed*
tool calls as prose, so a broken JSON tool call silently became a chat message
instead of getting the misformat nudge that teaches the model to fix it.

Deterministic. No LLM call. Passthrough on any failure.

Reads:  data["args"] / data["kwargs"] (the `msg` argument)
Writes: the same, only when the fallback applies
Log tag: [PLAINTEXT-FB]
"""

import json
from typing import Any

from helpers.extension import Extension

try:
    from helpers import extract_tools
except Exception:  # pragma: no cover - core layout changed
    extract_tools = None  # type: ignore[assignment]

LOG_PREFIX = "[PLAINTEXT-FB]"

# Guard: do not wrap enormous payloads. If a model emits something this large as
# prose, wrapping it silently hides a real problem we would rather see.
_MAX_WRAP_CHARS = 200_000


class PlaintextResponseFallback(Extension):
    """Rewrite bare prose into an explicit `response` tool call."""

    def _log(self, message: str) -> None:
        print(f"{LOG_PREFIX} {message}", flush=True)

    async def execute(self, data: dict | None = None, **kwargs) -> None:
        try:
            if not isinstance(data, dict) or extract_tools is None:
                return

            msg, where, index = _read_msg(data)
            if not isinstance(msg, str):
                return

            stripped = msg.strip()
            if not stripped:
                return

            if len(stripped) > _MAX_WRAP_CHARS:
                self._log(f"skip: {len(stripped)} chars exceeds wrap ceiling")
                return

            # Already a valid tool call — nothing to do.
            if extract_tools.extract_tool_request(msg) is not None:
                return

            # A BROKEN tool call. Leave it alone so A0 emits fw.msg_misformat and
            # the model learns to fix its formatting. Swallowing these as prose is
            # exactly the bug in the patch this replaces.
            if extract_tools.is_misformatted_tool_request(msg):
                self._log("misformatted tool request — leaving for the misformat nudge")
                return

            wrapped = json.dumps(
                {"tool_name": "response", "tool_args": {"text": stripped}},
                ensure_ascii=False,
            )
            _write_msg(data, where, index, wrapped)
            self._log(f"wrapped {len(stripped)} chars of prose as a response tool call")

        except Exception as exc:  # never break the turn
            self._log(f"passthrough after error: {type(exc).__name__}: {exc}")


def _read_msg(data: dict) -> tuple[Any, str, int]:
    """Locate the `msg` argument. Signature: process_tools(self, msg).

    Positionally `self` is args[0] and `msg` is args[1], but the decorator does
    not guarantee how the call was made, so handle the keyword form too.
    """
    kwargs = data.get("kwargs")
    if isinstance(kwargs, dict) and "msg" in kwargs:
        return kwargs["msg"], "kwargs", -1

    args = data.get("args")
    if isinstance(args, (list, tuple)):
        # Last positional string is the message; avoids depending on whether
        # `self` was passed positionally.
        for i in range(len(args) - 1, -1, -1):
            if isinstance(args[i], str):
                return args[i], "args", i

    return None, "", -1


def _write_msg(data: dict, where: str, index: int, value: str) -> None:
    if where == "kwargs":
        data["kwargs"]["msg"] = value
    elif where == "args":
        args = list(data["args"])
        args[index] = value
        data["args"] = tuple(args)
