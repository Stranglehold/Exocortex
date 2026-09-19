"""
_06_name_the_defect — say WHAT is wrong with a structurally invalid tool call.

A0 already computes the answer and throws it away.

    agent.py:1425   raw_tool_name, tool_args = extract_tools.normalize_tool_request(tool_request)
    agent.py:1428   except ValueError:
    agent.py:1429       tool_request = None   # treat structural validation errors as misformat

A bare `except` — the exception is not even bound. The ValueError it discards carries the exact
defect, verified 2026-09-18 against A0's own validator:

    flat args, no wrapper   -> "Tool request must have a tool_args (type dictionary) field"
    no tool_name            -> "Tool request must have a tool_name (type string) field"
    tool_args not a dict    -> "Tool request must have a tool_args (type dictionary) field"

What she receives instead is the whole of `prompts/fw.msg_misformat.md`:

    "You have misformatted your message. Follow system prompt instructions on JSON message
     formatting precisely."

**This extension adds no diagnosis. It surfaces the one A0 computes one line before discarding it.**

WHY THAT MATTERS, measured rather than assumed
----------------------------------------------
Cycle 593 ran 66 minutes, produced a 10 KB field report, and died at its own close: four attempts
at the journal append, every one flat-args, every one answered with the generic warning. Her own
reasoning shows the cost — she guessed "surrounding text" three times while the defect was the
missing `tool_args` wrapper. 595 guessed "literal newlines" while the defect was unescaped ones.
`_05`'s docstring already states the principle from its own case: *a generic misformat warning
sends the model to fix correct JSON.* We proved that once and built exactly one detector.

NARROW ON PURPOSE, and the exclusivity is structural rather than a flag
-----------------------------------------------------------------------
It speaks only when a JSON root PARSES, carries a `tool_name`, and fails `normalize_tool_request`:

    _05 extracted a valid call      -> normalize succeeds       -> silent
    _04's cases (bad string/escape) -> the root does not parse   -> silent
    prose with no call at all       -> no root                   -> silent
    trailing tags after a valid call-> `_05` owns it as ambiguous -> silent

So it cannot double-nudge with `_04` or `_05` without needing to know about them.

NUDGE-ONLY. It never rewrites the message. Whether a gate may ACT on a recovered payload is a
live question for Jake and Opus (`_05` extracts, `_07` refuses when unattended); this stays out of
it entirely, which is also why it can be deployed without touching that decision.

WHY THE READER IS IMPORTED AND NOT WRITTEN (v2, 2026-09-18 — the first version was INERT)
-----------------------------------------------------------------------------------------
v1 shipped its own `_read_msg` that accepted only dict holders, with a docstring claiming it
"mirrors `_04`/`_05`'s reader". It did not, and nobody checked the claim. A0 calls
`self.process_tools(message)` **positionally** (`agent.py:1136`), and `@extension.extensible`
packs the raw tuple straight through — `data = {"args": args, "kwargs": kwargs}`
(`helpers/extension.py`). So in production `data["args"]` is `(agent, msg)`, a TUPLE, and
`data["kwargs"]` is empty. v1's reader returned None on every real call and `execute()` exited on
its first branch. Deployed 2026-09-18 ~20:32, **zero firings** against 12 messages of exactly its
class in cycles 623 and 626 (Fable's count).

The control did not catch it because it fed `{"args": {"msg": msg}}` — a shape A0 never produces.
Measured, the two are exact complements: on the control's shape v1's reader returns a str and
`prose_leak.read_msg` returns None; on production's shape it is the other way round. A perfect
false positive, 14 PASS on a message the extension could never receive.

Hence: **import the house reader, never re-implement it.** `_04`, `_05` and `_10` all use
`prose_leak.read_msg`, which is why all three fire and this did not. The fallback below is a
byte-copy of it rather than a paraphrase, for the same reason.
"""

import json
import sys

from helpers.extension import Extension

_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _HELPERS not in sys.path:
    sys.path.insert(0, _HELPERS)

try:
    from helpers import extract_tools
except Exception:  # pragma: no cover
    extract_tools = None  # type: ignore[assignment]

try:  # the same reader `_04`, `_05` and `_10` use, so all four see the same message
    from prose_leak import read_msg as _read_msg
except Exception:  # pragma: no cover - fallback mirrors it exactly
    def _read_msg(data):
        kwargs = data.get("kwargs")
        if isinstance(kwargs, dict) and "msg" in kwargs:
            return kwargs["msg"], "kwargs", -1
        args = data.get("args")
        if isinstance(args, (list, tuple)):
            for i in range(len(args) - 1, -1, -1):
                if isinstance(args[i], str):
                    return args[i], "args", i
        return None, "", -1

#: Envelope keys that are never tool arguments. Used only to SHOW her which of her own top-level
#: keys belong inside the wrapper — never to move them. Naming the keys she actually used is what
#: makes the warning actionable rather than a restatement of the schema.
_ENVELOPE = {"thoughts", "headline", "tool_name", "tool", "type", "name", "tool_args", "args",
             "parameters"}


def _candidate_request(content: str):
    """A JSON object carrying a `tool_name` that A0 could not accept. None when nothing applies."""
    if extract_tools is None or not isinstance(content, str):
        return None
    text = content.strip()
    if not text:
        return None
    # Already acceptable -> nothing to say. This is what keeps us silent after `_05` extracts.
    if extract_tools.extract_tool_request(text) is not None:
        return None
    try:
        roots = extract_tools.extract_json_root_strings(text)
    except Exception:
        return None
    if not roots and text.startswith("{"):
        roots = [text]
    for root in roots:
        try:
            obj = json.loads(root)
        except Exception:
            continue          # does not parse -> `_04`'s territory, not ours
        if isinstance(obj, dict) and obj.get("tool_name"):
            return obj
    return None


def nudge_text(error: str, request: dict) -> str:
    """Name the defect, show the shape, and echo the keys SHE used.

    Deliberately does not say "follow the system prompt": that is the existing warning, and it is
    the one measured to send her looking in the wrong place.
    """
    flat = [k for k in request if k not in _ENVELOPE]
    tool = request.get("tool_name")
    lines = [f"Your last reply was not accepted as a tool call: {error}."]
    if flat:
        shown = ", ".join(repr(k) for k in flat[:6])
        lines.append(
            f"You put {shown} at the top level of the message. Tool arguments do not go there — "
            f"they belong inside a \"tool_args\" object."
        )
        example = {"thoughts": ["..."], "tool_name": tool or "code_execution_tool",
                   "tool_args": {k: "..." for k in flat[:3]}}
        lines.append("The shape is:\n" + json.dumps(example, indent=2))
    else:
        lines.append(
            "A tool call needs \"tool_name\" (a string) and \"tool_args\" (an object), both at the "
            "top level of the message."
        )
    lines.append("Send the same call again with that shape; nothing else about it was wrong.")
    return "\n\n".join(lines)


class NameTheDefect(Extension):

    def _log(self, message: str) -> None:
        print(f"[NAME-DEFECT] {message}", flush=True)

    async def execute(self, data: dict | None = None, **kwargs) -> None:
        if not isinstance(data, dict):
            return
        try:
            msg, _where, _index = _read_msg(data)
            if not isinstance(msg, str):
                return
            request = _candidate_request(msg)
            if request is None:
                return
            try:
                extract_tools.normalize_tool_request(request)
            except ValueError as exc:
                error = str(exc)
            except Exception:
                return
            else:
                return      # it validates after all; nothing to name

            self._log(f"structurally invalid {request.get('tool_name')!r} call — {error}; "
                      f"naming it instead of the generic misformat warning")
            try:
                self.agent.hist_add_warning(nudge_text(error, request))
            except Exception as exc:
                self._log(f"warning not added: {type(exc).__name__}: {exc}")
        except Exception as exc:  # never let a diagnostic break the turn
            self._log(f"error (passthrough): {type(exc).__name__}: {exc}")
