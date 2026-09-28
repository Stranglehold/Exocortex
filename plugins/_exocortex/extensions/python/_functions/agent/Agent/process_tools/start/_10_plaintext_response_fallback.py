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
import sys
from typing import Any

_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _HELPERS not in sys.path:
    sys.path.insert(0, _HELPERS)

from helpers.extension import Extension

try:
    from helpers import extract_tools
except Exception:  # pragma: no cover - core layout changed
    extract_tools = None  # type: ignore[assignment]

try:
    import prose_leak as pl
except Exception:  # pragma: no cover - helper missing
    pl = None  # type: ignore[assignment]

# ONE implementation of "is anyone watching this turn", shared with _07_recovery_gate.
# If it cannot be imported the gate below fails CLOSED by refusing to wrap in any turn it
# cannot vouch for -- see _attendedness_veto().
try:
    import attendedness as att
except Exception:  # pragma: no cover - helper missing
    att = None  # type: ignore[assignment]

LOG_PREFIX = "[PLAINTEXT-FB]"

# Consecutive unattended refusals before the wrap is allowed through to end the turn. The
# refusal costs one step each; the budget is 15-30 depending on cycle type, so three leaves
# room to recover and still ends the turn far short of burning the cycle on nudges.
NUDGE_BOUND = 3
_NUDGE_COUNT_KEY = "_plaintext_fb_unattended_nudges"

# Keys that mark JSON-shaped text as an ATTEMPTED tool call rather than an answer.
_CALL_KEYS = ("tool_name", "tool_calls")


def _is_unrecoverable_call(stripped: str) -> bool:
    """JSON-shaped text that tried to be a tool call and could not be completed.

    THE GAP THIS CLOSES. A0 v2.9's `is_misformatted_tool_request` has three
    conditions: multiple roots with one valid, a fenced block, and content not
    ending in `}`. A SINGLE root that is unrecoverable and still ends in `}`
    matches none of them, so it returns False -- and `_10` then wrapped the whole
    broken call as a prose answer. Measured 2026-09-10 on chat P4NEl4t6: one
    missing closing quote in a 2,807-char call, three times, and the agent's
    adjudicated decision was destroyed at the gate each time while the memoriser's
    reflexive summaries landed normally.

    Deliberately structural, never lexical. Every lexical critic built in Aug 2026
    false-positived on first contact and always in the expensive direction; here
    that direction is a genuine final answer bounced into the misformat loop this
    file exists to prevent. Genuine prose does not start with `{`, and genuine
    JSON parses.

    Reading of the design (Kestrel, flagged for Opus): the key test is the BARE
    substring, not the quoted literal `"tool_name"`. Conditions 1 and 3 already do
    the narrowing, and requiring the closing quote would miss a call broken at
    exactly that key -- which is the failure shape being fixed.
    """
    if not stripped.startswith("{"):
        return False
    if not any(k in stripped for k in _CALL_KEYS):
        return False
    try:
        json.loads(stripped)
    except Exception:
        return True
    # Parses cleanly. Not our case -- a valid JSON document that merely mentions
    # the keys is an answer, and wrapping it is the correct existing behaviour.
    return False

# Guard: do not wrap enormous payloads. If a model emits something this large as
# prose, wrapping it silently hides a real problem we would rather see.
_MAX_WRAP_CHARS = 200_000


# ATTENDED + MID-TASK (Opus's v3, 2026-09-28; Opus/design-notes/empty-content-retry.md).
# In an attended turn this file wraps any non-tool message as `response`, which ends the turn. That is
# right for an answer, and wrong for an agent that stumbled mid-task. On 2026-09-28 it ended both turns of
# chat UAF8M7i2 while she was verifying a letter. So, ONCE per monologue, when this monologue has
# executed a tool, return without wrapping and let core's misformat nudge (which does not name
# `response`) ask for the call. A second stumble in the same monologue wraps as before.
_MIDTASK_KEY = "_10_midtask_vetoed"


def _is_working_mode(agent) -> bool:
    """True if a tool result is in the current history topic.

    A user message starts a new topic (agent.hist_add_user_message calls history.new_topic()), so the
    current topic IS this monologue. Tool results are stored as {"tool_name", "tool_result"}
    (agent.hist_add_tool_result). Structural and read-only. Anything unreadable reads as False, which
    keeps today's behaviour (wrap).
    """
    try:
        for m in agent.history.current.messages:
            c = getattr(m, "content", None)
            if not getattr(m, "ai", True) and isinstance(c, dict) and "tool_result" in c:
                return True
    except Exception:
        return False
    return False


class PlaintextResponseFallback(Extension):
    """Rewrite bare prose into an explicit `response` tool call."""

    def _log(self, message: str) -> None:
        print(f"{LOG_PREFIX} {message}", flush=True)

    def _attendedness_veto(self) -> tuple[bool, str]:
        """(veto, why). True means: do not end this turn by wrapping prose.

        Fails CLOSED in every direction. If the shared rule cannot be imported, if it raises,
        or if it cannot positively determine that a human is watching, the answer is veto. The
        cost of a false veto is one nudge on a driven turn; the cost of a false pass is a
        cycle's work discarded with every counter reading zero.
        """
        if att is None:
            return True, "attendedness helper unavailable"
        try:
            observation, _marker, fault = att.attendedness(self.agent)
        except Exception as exc:
            return True, f"attendedness raised {type(exc).__name__}"
        if fault:
            # Not a veto by itself -- the walk falling through to the file is safe, because the
            # file can only ever confirm unattended. Logged because silent safety and observed
            # safety are different categories (Opus, 2026-09-11).
            self._log(f"attendedness parent-walk fault: {fault}")
        return (observation in att.VETOES), observation

    def _midtask_veto(self, nchars: int) -> bool:
        """Attended, mid-task, first stumble this monologue: do not end the turn. The flag lives in
        loop_data.params_persistent, which is new at every monologue start (agent.py:398). Fails OPEN
        to today's wrap."""
        try:
            pp = self.agent.loop_data.params_persistent
            if pp.get(_MIDTASK_KEY) or not _is_working_mode(self.agent):
                return False
            pp[_MIDTASK_KEY] = True
            self._log(
                f"attended turn, mid-task (a tool ran this monologue) — NOT wrapping {nchars} chars "
                "once; leaving for the misformat nudge"
            )
            return True
        except Exception as exc:
            self._log(f"mid-task veto check failed ({type(exc).__name__}) — wrapping as before")
            return False

    def _bump_nudges(self) -> int:
        try:
            n = int(self.agent.get_data(_NUDGE_COUNT_KEY) or 0) + 1
        except Exception:
            n = 1
        try:
            self.agent.set_data(_NUDGE_COUNT_KEY, n)
        except Exception:
            pass
        return n

    def _reset_nudges(self) -> None:
        try:
            if self.agent.get_data(_NUDGE_COUNT_KEY):
                self.agent.set_data(_NUDGE_COUNT_KEY, 0)
        except Exception:
            pass

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

            # Already a valid tool call — nothing to do. This is also the ONLY evidence
            # available here that the model recovered, so the nudge counter resets on it: a
            # counter that only ever climbs turns a transient stumble into a permanent state.
            if extract_tools.extract_tool_request(msg) is not None:
                self._reset_nudges()
                return

            # A BROKEN tool call. Leave it alone so A0 emits fw.msg_misformat and
            # the model learns to fix its formatting. Swallowing these as prose is
            # exactly the bug in the patch this replaces.
            if extract_tools.is_misformatted_tool_request(msg):
                self._log("misformatted tool request — leaving for the misformat nudge")
                return

            # A VALID tool call that the model wrapped in prose. _05_prose_leak_detector
            # claims this case and nudges for a clean re-send.
            #
            # Without this check _10 wins it, because its condition — non-empty, not a
            # valid whole-message call, not misformatted — is a strict SUPERSET of the
            # leak signature. Measured 2026-08-22: "wrapped 52943 chars of prose as a
            # response tool call", i.e. the agent recited a valid 37KB text_editor call
            # aloud instead of writing the file. Strictly worse than any other outcome
            # available, which is why this file was held back from the live containers.
            #
            # HANDLED_KEY is imported, never retyped. Two literals here would be two
            # notions of the handoff, free to drift, and the failure would be silent.
            if pl is not None:
                try:
                    if self.agent.get_data(pl.HANDLED_KEY):
                        self._log("prose-wrapped valid tool call — deferring to _05")
                        return
                except Exception:
                    pass

            # An unrecoverable tool call that v2.9's misformat test does not
            # recognise. Return WITHOUT wrapping: `process_tools` then finds no
            # tool request and A0 emits fw.msg_misformat.md itself (agent.py:1511),
            # which is the same nudge the branch above relies on. Nothing new is
            # emitted here -- one code path, one nudge.
            if _is_unrecoverable_call(stripped):
                self._log(
                    f"unrecoverable tool call ({len(stripped)} chars) — "
                    "not wrapping; leaving for the misformat nudge"
                )
                return

            # LAST GATE. Wrapping prose as a `response` ENDS THE TASK. In a driven chat that
            # is right: a human reads the prose and replies. In an idle cycle there is nobody
            # to read it, and the turn dies mid-work -- which on 2026-09-15 discarded the first
            # synthesis this system ever produced, three steps from being registered.
            veto, why = self._attendedness_veto()
            if veto:
                n = self._bump_nudges()
                if n <= NUDGE_BOUND:
                    self._log(
                        f"unattended turn ({why}) — NOT wrapping {len(stripped)} chars; "
                        f"leaving for the misformat nudge ({n}/{NUDGE_BOUND})"
                    )
                    return
                # Bound reached: let the wrap through so the turn ENDS rather than spending the
                # rest of the budget on nudges nobody is reading. The distinct tag is the point
                # -- "died after N nudges" and "died on the first prose" must not arrive as the
                # same row.
                self._log(
                    f"unattended turn ({why}) — nudge bound {NUDGE_BOUND} exhausted after "
                    f"{n} refusals; wrapping to end the turn"
                )
            elif self._midtask_veto(len(stripped)):
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
