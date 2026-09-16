"""
Parse-Recovery Gate
===================
Hook: _functions/agent/Agent/process_tools/start  (at _07, between _05 and _10)

WHY THIS EXISTS
---------------
`_10`'s sibling problem. `_10` covers the case where recovery FAILED and the call
was discarded. This covers the case where recovery SUCCEEDED and should not have
been trusted.

At 05:07 UTC on 2026-09-10 the same unclosed-string defect that killed the 05:14
turn instead *recovered*: DirtyJson closed the open `code` string by absorbing the
trailing brace lines into it, marked the parse complete, and the shell executed
the command with five stray brace lines appended. Harmless there — trailing braces
in an `ls` pipeline. The same dice with a truncated `rm` path is the same dice.

In a driven turn someone is watching. In an idle cycle nobody is.

DETECTION — a differential, not a heuristic
-------------------------------------------
    strict  json.loads(msg.strip())   fails
    extract_tools.extract_tool_request()  succeeds
                                      => DirtyJson invented something

No threshold, no vocabulary, no judgement about the agent's language. Either the
two parsers agree or they do not. Clean by construction: `extract_tool_request`
strips, requires `root == content`, and does NO fence stripping (that lives only
in `is_misformatted_tool_request`), so the strict half runs on exactly the string
DirtyJson received.

THE FAIL-CLOSED RULE
--------------------
If attendedness cannot be positively determined, the turn is treated as
UNATTENDED. Reading a state key to decide whether to guard means that if the key
is absent, renamed, or reshaped, the gate silently does nothing in exactly the
case it exists for — the severed-consumer defect, applied to the guard against it.
That defect has been found five times in this system; `skills_captured: 0` ran for
878 cycles on it.

The asymmetry justifies the default. A driven turn misread as idle costs one nudge
and one extra turn, visible and recoverable. An idle cycle misread as driven
executes recovered garbage unattended.

    The file can only ever confirm UNATTENDED. It can never confirm ATTENDED.

"Present and wrong" is why. `idle_watch.py` fires first and writes second, so a
failed write — or a daemon dying between the two — leaves the previous cycle's id
in `engine_state.json`. Verified live 2026-09-10: the file held
`cycle_context_id: "TrPI3dyd"` while that chat was already gone from disk. A gate
keyed on that file alone would have failed open on every turn that day. The
primary signal is therefore the in-process marker set by `api/idle_cycle.py`,
which has no file, no daemon and no window.

The marker is a DICT, never a boolean, and this reads PRESENCE of the key — never
`is True`. Step 0 needs that key to carry the minted cycle id; a boolean now would
force either a rename (severed consumer) or a dict tested against a boolean.

NOT is_directed()
-----------------
`helpers/scope_expansion.py: is_directed()` is the only other consumer of
`cycle_context_id` and has the right name, but its polarity is inverted for a
gate: file absent -> directed, id present but different -> directed, empty current
id -> directed. Three of the six cases in `scripts/test_scope_expansion.py` are
fail-OPEN for this purpose. That polarity is correct for an observe-only detector
and wrong here, so this carries its own reader.

THE VETO
--------
`helpers/extension.py` initialises `data["result"]` to an internal `_UNSET`
sentinel and calls the wrapped function only while it is still `_UNSET`. Setting
it to None means the tool is never constructed, `process_tools` never runs, the
decorator returns None, the monologue continues on the falsy result, and the next
completion sees the nudge. A nudge-only version of this file would be `_05` with a
ledger, not a gate — `_05`'s own docstring says it "does NOT modify the message."

LEDGER — observe raw, derive later
----------------------------------
Every recovery is logged whether or not it is vetoed, so the attended path is
observable and the parse-recovery rate becomes measurable for the first time.
`delta` is deliberately NOT computed here: it cannot be a diff of two parses
because the strict one failed. The raw root is saved by content hash and the
recovered request stored alongside; derive the delta offline. A delta-computer
inside a guard is a bug in the guard waiting to happen.

Deterministic. No LLM call. Passthrough on any failure.

Reads:  data["args"] / data["kwargs"] (the `msg` argument)
Writes: data["result"] = None, on the unattended-recovery path only
Log tag: [RECOVERY-GATE]
"""

import hashlib
import json
import os
import sys
import time
from typing import Any

_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _HELPERS not in sys.path:
    sys.path.insert(0, _HELPERS)

from helpers.extension import Extension

# The attendedness rule lives in ONE place and this file is no longer it. The logic below was
# lifted verbatim into helpers/attendedness.py on 2026-09-15 so _10_plaintext_response_fallback
# could ask the same question; both import from there now. If this import fails the gate reports
# UNDETERMINED, which vetoes -- a guard that cannot read its own rule must not guess.
try:
    import attendedness as att
except Exception:  # pragma: no cover - helper missing
    att = None  # type: ignore[assignment]

try:
    from helpers import extract_tools
except Exception:  # pragma: no cover - core layout changed
    extract_tools = None  # type: ignore[assignment]

try:
    import prose_leak as pl
except Exception:  # pragma: no cover - helper missing
    pl = None  # type: ignore[assignment]

LOG_PREFIX = "[RECOVERY-GATE]"

# The in-process marker set by api/idle_cycle.py's fire handler. Presence means
# unattended. Never compared against True.
IDLE_MARKER_KEY = "idle_cycle"

# helpers/parallel_tools.py:445 — `worker_context.set_data(...)`. A `parallel`
# child gets its OWN AgentContext, so the marker does not reach it by sharing, and
# its id differs from the one in engine_state.json. Without this walk a child's
# recovered call reads as ATTENDED and executes — fail-open inside an idle cycle,
# which is the exact failure this file exists to prevent. The design assumed
# children need no marker because "the veto happens in the parent before dispatch";
# true of the dispatching call, not of calls the child itself makes.
PARENT_CONTEXT_KEY = "_parallel_parent_context_id"
MAX_PARENT_HOPS = 4

ENGINE_STATE = "/a0/usr/workdir/workspace/office/engine_state.json"
STATE_DIR = "/a0/usr/plugins/_exocortex/state"
LEDGER = os.path.join(STATE_DIR, "parse_recovery.jsonl")
ROOTS_DIR = os.path.join(STATE_DIR, "parse_recovery_roots")

# Bound what goes inline in a ledger row. The raw root is saved in full beside it,
# so nothing is lost by truncating the copy.
_MAX_INLINE = 4000

ATTENDED = "attended"
UNATTENDED = "unattended"
UNDETERMINED = "undetermined"

NUDGE = (
    "Your last tool call did not parse as valid JSON. It was repaired "
    "automatically, and because this turn is unattended the repaired call was NOT "
    "executed — a repaired call can differ from what you meant in ways nobody is "
    "here to catch.\n\n"
    "Strict parser error: {err}\n\n"
    "Re-send the call as strictly valid JSON. The usual cause is a raw newline or "
    "an unescaped quote inside a string value: put \\n in the string rather than "
    "an actual line break, and do not place XML-style tags inside JSON values."
)


class RecoveryGate(Extension):
    """process_tools/start: refuse to execute a call the parser had to invent."""

    def _log(self, message: str) -> None:
        print(f"{LOG_PREFIX} {message}", flush=True)

    # -- attendedness ------------------------------------------------------
    # Set by _marker() when the parent walk ends abnormally. Cleared at the top of
    # every execute(); a stale value from a previous turn would misattribute a fault.
    _walk_fault = None

    def _marker(self):
        """The idle marker, or None. Presence is the signal, not the value.

        Delegates to helpers/attendedness.py, which holds this logic verbatim as of
        2026-09-15. Kept as a method with the same name and return shape because the ledger
        and execute() both depend on the `self._walk_fault` side effect.
        """
        if att is None:
            self._walk_fault = "attendedness helper unavailable"
            return None
        marker, fault = att.marker(self.agent)
        if fault:
            self._walk_fault = fault
        return marker

    def _marker_inline_RETIRED(self):
        """RETIRED 2026-09-15 — superseded by helpers/attendedness.py:marker().

        Kept unreferenced for one release so the migration is auditable against the original
        rather than against a memory of it. Delete once _07 and _10 have run a full rotation
        on the shared rule.
        """
        try:
            ctx = self.agent.context
        except Exception:
            return None

        try:
            from agent import AgentContext
        except Exception:
            AgentContext = None  # type: ignore[assignment]

        for _hop in range(MAX_PARENT_HOPS):
            try:
                marker = ctx.get_data(IDLE_MARKER_KEY)
            except Exception as exc:
                self._walk_fault = "read failed at hop %d: %s" % (_hop, type(exc).__name__)
                return None
            if marker is not None:
                return marker
            if AgentContext is None:
                self._walk_fault = "AgentContext unavailable at hop %d" % _hop
                return None
            try:
                parent_id = ctx.get_data(PARENT_CONTEXT_KEY)
                if not parent_id:
                    return None          # top of the chain. Not a fault.
                parent = AgentContext.get(parent_id)
            except Exception as exc:
                self._walk_fault = "parent lookup failed at hop %d: %s" % (_hop, type(exc).__name__)
                return None
            if parent is None:
                self._walk_fault = "parent %s not resolvable at hop %d" % (parent_id, _hop)
                return None
            if parent is ctx:
                self._walk_fault = "parent chain cycles at hop %d" % _hop
                return None
            ctx = parent

        # Depth bound exceeded. Falling through to the file is SAFE — the file can
        # only ever confirm unattended — but it is not the same as "no marker", and
        # Opus's ruling of 2026-09-11 is the reason this is distinguished:
        # *"silent safety and observed safety are different categories."* This log
        # line is the only instrument that would tell us the bound was too shallow.
        self._walk_fault = "depth bound %d exceeded" % MAX_PARENT_HOPS
        return None

    def _attendedness(self) -> tuple[str, Any]:
        """Return (observation, marker). Fails closed to UNDETERMINED.

        Delegates to helpers/attendedness.py. The rule is unchanged; it simply lives in one
        file now, shared with _10_plaintext_response_fallback, which needs the same answer
        before it ends a turn by wrapping prose as a `response`.
        """
        if att is None:
            self._walk_fault = "attendedness helper unavailable"
            self._log("attendedness helper unavailable — reporting UNDETERMINED, which vetoes")
            return UNDETERMINED, None
        observation, marker, fault = att.attendedness(self.agent)
        if fault:
            self._walk_fault = fault
            self._log("parent walk fault: %s — falling through to the file, which "
                      "can only confirm unattended" % fault)
        return observation, marker

    # -- ledger ------------------------------------------------------------
    def _record(self, row: dict, root: str) -> None:
        try:
            os.makedirs(ROOTS_DIR, exist_ok=True)
            digest = hashlib.sha256(root.encode("utf-8", "replace")).hexdigest()
            row["root_sha256"] = digest
            row["root_chars"] = len(root)
            path = os.path.join(ROOTS_DIR, digest + ".txt")
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(root)
            row["root_path"] = path
            with open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception as exc:
            self._log(f"ledger write failed: {type(exc).__name__}: {exc}")

    # -- main --------------------------------------------------------------
    async def execute(self, data: dict | None = None, **kwargs) -> None:
        try:
            if not isinstance(data, dict) or extract_tools is None:
                return

            self._walk_fault = None
            msg = _read_msg(data)
            if not isinstance(msg, str):
                return
            stripped = msg.strip()
            if not stripped:
                return

            request = extract_tools.extract_tool_request(msg)
            if request is None:
                # Nothing was recovered. Either a clean non-call, or the failure
                # case `_10` owns. Not this gate's business.
                return

            try:
                json.loads(stripped)
                return  # both parsers agree — the overwhelmingly common path
            except Exception as exc:
                strict_error = f"{type(exc).__name__}: {exc}"

            observation, marker = self._attendedness()
            may_execute = observation == ATTENDED

            tool_name = ""
            try:
                tool_name = str(request.get("tool_name") or "")
            except Exception:
                pass

            try:
                context_id = self.agent.context.id
            except Exception:
                context_id = None

            cycle_id = None
            if isinstance(marker, dict):
                cycle_id = marker.get("cycle_id")

            try:
                recovered_json = json.dumps(request, ensure_ascii=False, default=str)
            except Exception:
                recovered_json = repr(request)

            row = {
                "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "context_id": context_id,
                "cycle_id": cycle_id,
                "attended": observation,
                "walk_fault": self._walk_fault,
                "tool_name": tool_name,
                "recovered": True,
                "action": "executed" if may_execute else "skipped",
                "strict_error": strict_error,
                "recovered_request": recovered_json[:_MAX_INLINE],
                "recovered_request_truncated": len(recovered_json) > _MAX_INLINE,
            }
            self._record(row, stripped)

            if may_execute:
                self._log(
                    f"recovered {tool_name or 'tool'} call, {observation} — "
                    f"executing and logging ({strict_error})"
                )
                return

            self._log(
                f"recovered {tool_name or 'tool'} call, {observation} — "
                f"NOT executing ({strict_error})"
            )
            try:
                self.agent.hist_add_warning(NUDGE.format(err=strict_error))
            except Exception as exc:
                self._log(f"warning injection failed: {type(exc).__name__}: {exc}")

            # The veto. helpers/extension.py calls the wrapped function only while
            # data["result"] is still its _UNSET sentinel.
            data["result"] = None

        except Exception as exc:  # never break the turn
            self._log(f"passthrough after error: {type(exc).__name__}: {exc}")


def _read_msg(data: dict):
    """Locate the `msg` argument. Signature: process_tools(self, msg)."""
    if pl is not None:
        try:
            return pl.read_msg(data)[0]
        except Exception:
            pass
    kwargs = data.get("kwargs")
    if isinstance(kwargs, dict) and "msg" in kwargs:
        return kwargs["msg"]
    args = data.get("args")
    if isinstance(args, (list, tuple)):
        for i in range(len(args) - 1, -1, -1):
            if isinstance(args[i], str):
                return args[i]
    return None
