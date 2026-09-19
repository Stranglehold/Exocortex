"""prose_leak.py — detect a VALID tool call that the model wrapped in prose.

WHY THIS EXISTS
---------------
Measured 2026-08-22. Asked for a 32K escape-dense file, qwen3.8-27b emitted a complete,
valid tool call — 37,422 bytes, all 243 requested blocks, `extract_tool_request` returns
`text_editor` when handed the JSON alone. It was rejected anyway, because A0 v2.9 requires
the tool call to BE the whole message:

    helpers/extract_tools.py:extract_tool_request
        root = extract_json_root_string(content)
        if root != content:
            return None

The model had prefixed it with "I'll write out blocks 1..243. Let me go. I realize I
should just carefully write the entire thing."

That prose is not a defect. "Capacity, Not Format" (arXiv:2606.09410) finds that
"performance recovers whenever unconstrained reasoning precedes structured submission",
and DCCD (arXiv:2603.03305) builds a decoding scheme on exactly that: draft freely, then
serialise. The model reasoning before emitting JSON is the behaviour the literature says
produces the best results. The strict parser punishes it.

WHAT GOES WRONG WITHOUT THIS
----------------------------
`is_misformatted_tool_request` returns False on a prose-wrapped call — its thoughts-leak
branch requires `content.endswith("}")`. So the message falls into the gap between the two
detectors, and `_10_plaintext_response_fallback` claims it: observed in production as
`[PLAINTEXT-FB] wrapped 52943 chars of prose as a response tool call` — the agent reciting
a 37KB tool call aloud instead of writing the file.

Without `_10` it is only marginally better: A0 emits the generic `fw.msg_misformat`
warning, which tells the model its JSON is malformed. The JSON was perfect. The model is
pointed at the wrong fix and re-runs the same emission.

WHAT THIS DOES
--------------
Detects the case and acts on it. Two modes, gated on `survey_leaked_calls().unambiguous`:

  * UNAMBIGUOUS (one call, prose only before it): extract the valid root and rewrite `msg`
    so `process_tools` sees a clean tool call. The prose preamble is stripped.

  * AMBIGUOUS (prose after the call, or multiple calls): nudge specifically — *your tool
    call was valid, it was preceded by prose, re-emit the JSON alone*. Nudge only.

History: Opus's original call (2026-08-22) was nudge-only for both cases, to respect
v2.9's intent of not firing a call the model merely DESCRIBED. The `unambiguous` field
was designed for the transition, gated on nudge-acceptance data. Data collected over
cycles 513–640+: Ornith's nudge acceptance rate is near zero — the retry produces the
same prose-wrapped format, and the response content ends up empty. Jake's messages in the
"Workspace Scripts" chat (2026-09-17) went unanswered because three consecutive turns
produced valid tool calls that the nudge loop silently discarded. The unambiguous
extraction is justified: prose-before-only is the "Capacity, Not Format" pattern
(reasoning then structured output), not a description.

SHARED BY BOTH HALVES ON PURPOSE
--------------------------------
`_05_prose_leak_detector` sets the flag, `_10_plaintext_response_fallback` defers on it.
Both import HANDLED_KEY from here rather than repeating a literal, because a mismatched
string in either file leaves the mechanism inert while looking installed — the defect
class this codebase produces most reliably.

No LLM calls. Parsing and string comparison only.
"""

from typing import Any

try:
    from helpers import extract_tools
except Exception:  # pragma: no cover — core layout changed
    extract_tools = None  # type: ignore[assignment]

# Agent-data flag handed from the detector to _10. ONE definition, imported by both.
HANDLED_KEY = "_prose_leak_handled"

LOG_PREFIX = "[PROSE-LEAK]"

# A tool call wrapped in this much surrounding prose is not "a call with a preamble", it
# is a message that happens to quote JSON. Nudging there would be wrong, and executing it
# would be worse.
MAX_SURROUNDING_CHARS = 4000


def read_msg(data: dict) -> tuple[Any, str, int]:
    """Locate the `msg` argument of process_tools(self, msg).

    Positionally `self` is args[0] and `msg` is args[1], but the decorator does not
    guarantee how the call was made, so the keyword form is handled too. Mirrors the
    reader in _10 deliberately — same contract, one behaviour.
    """
    kwargs = data.get("kwargs")
    if isinstance(kwargs, dict) and "msg" in kwargs:
        return kwargs["msg"], "kwargs", -1

    args = data.get("args")
    if isinstance(args, (list, tuple)):
        for i in range(len(args) - 1, -1, -1):
            if isinstance(args[i], str):
                return args[i], "args", i

    return None, "", -1


def write_msg(data: dict, where: str, index: int, value: str) -> None:
    """Write back the `msg` argument after extraction or repair.

    Same contract as `_write_msg` in _04 and _10. ONE definition here so _05 can
    import it rather than duplicating, keeping the shared-key discipline the header
    of this file describes.
    """
    if where == "kwargs":
        data["kwargs"]["msg"] = value
    elif where == "args" and index >= 0:
        args = list(data["args"])
        args[index] = value
        data["args"] = tuple(args)


def survey_leaked_calls(msg: Any) -> dict | None:
    """Return EVERY tool-request root in msg, with where the prose sits around them.

    Opus's ruling, 2026-09-04. The previous form returned the FIRST valid root and a
    single `surrounding` scalar, which destroyed the two facts a caller needs to decide
    anything:

      * how many tool calls leaked (it returned one of possibly several)
      * whether the prose came BEFORE the call or AFTER it

    Prose-after is the describe side of the describe-versus-emit line. A model that writes
    JSON and then keeps talking about it is more likely to be explaining a call than
    issuing one, and that is precisely the case v2.9's strict parser exists to refuse. A
    scalar `len(content) - len(root)` cannot tell the two apart, so a caller acting on it
    would be guessing on the one distinction that matters.

    Returns None on the same conditions as before: not a string, empty, already a valid
    whole-message call, a genuinely misformatted call (A0's own nudge owns that), no
    tool-shaped root at all (genuine prose — _10's case), or more surrounding prose than
    MAX_SURROUNDING_CHARS.

    Otherwise:
        {
          "calls":       [{"root", "tool_name", "start", "end"}, ...]  in document order
          "prose":       [{"position", "chars"}, ...]   position is "before-first",
                         "between-N-and-N+1", or "after-last"
          "surrounding": total prose chars outside the calls
          "unambiguous": exactly one call AND nothing but whitespace after it
        }

    `unambiguous` is the only field a caller should gate execution on. It is deliberately
    strict — one call, prose before it only — because that is the shape we have evidence
    for (16 of 18 production cases resolved on a single nudge) and the ambiguous remainder
    is small enough to keep nudging.
    """
    if extract_tools is None or not isinstance(msg, str):
        return None

    content = msg.strip()
    if not content:
        return None

    # Already valid as a whole message — nothing leaked.
    if extract_tools.extract_tool_request(content) is not None:
        return None

    # A genuinely broken call. A0's misformat nudge is the right response; do not claim it.
    if extract_tools.is_misformatted_tool_request(content):
        return None

    try:
        roots = extract_tools.extract_json_root_strings(content)
    except Exception:
        return None

    # Locate every tool-shaped root, in document order, with offsets. `find` runs from a
    # cursor so two identical roots resolve to two distinct positions rather than one.
    calls: list[dict] = []
    cursor = 0
    for root in roots:
        try:
            parsed = extract_tools._parse_json_root_object(root)
        except Exception:
            continue
        if parsed is None or not extract_tools._is_tool_request(parsed):
            continue

        start = content.find(root, cursor)
        if start < 0:                      # not a literal substring — cannot place it
            start = content.find(root)
        if start < 0:
            continue
        cursor = start + len(root)

        tool_name = ""
        try:
            tool_name, _ = extract_tools.normalize_tool_request(parsed)
        except Exception:
            pass

        calls.append({"root": root, "tool_name": tool_name, "start": start, "end": cursor})

    if not calls:
        return None

    calls.sort(key=lambda c: c["start"])

    # Prose segments, named by where they sit relative to the calls.
    prose: list[dict] = []
    gap = content[: calls[0]["start"]]
    if gap.strip():
        prose.append({"position": "before-first", "chars": len(gap)})
    for i in range(len(calls) - 1):
        gap = content[calls[i]["end"] : calls[i + 1]["start"]]
        if gap.strip():
            prose.append({"position": f"between-{i}-and-{i+1}", "chars": len(gap)})
    trailing = content[calls[-1]["end"] :]
    if trailing.strip():
        prose.append({"position": "after-last", "chars": len(trailing)})

    surrounding = len(content) - sum(len(c["root"]) for c in calls)
    if surrounding <= 0:
        # A single root equal to the whole message would have parsed above.
        return None
    if surrounding > MAX_SURROUNDING_CHARS:
        return None

    unambiguous = len(calls) == 1 and not trailing.strip()

    return {
        "calls": calls,
        "prose": prose,
        "surrounding": surrounding,
        "unambiguous": unambiguous,
    }


def find_leaked_call(msg: Any) -> dict | None:
    """Back-compatible single-call view. `_05` and `_10` keep working unchanged.

    Kept deliberately rather than changing the signature in place: both extensions import
    from this module, and a silent contract change between them is the defect class the
    header of this file warns about. Callers that need the whole picture — and any caller
    contemplating execution rather than a nudge — must use `survey_leaked_calls`.
    """
    survey = survey_leaked_calls(msg)
    if not survey:
        return None
    first = survey["calls"][0]
    # `surrounding` is recomputed the OLD way on purpose: len(content) - len(FIRST root),
    # which counts any second call as prose. The survey's figure subtracts every root and
    # is the more honest number, but it is SMALLER in the multi-call case, and this value
    # gates MAX_SURROUNDING_CHARS in `_05`. Handing back the better number would make the
    # detector nudge on messages it previously refused — a behaviour change smuggled in
    # under the word "back-compatible". Identical means identical.
    content = msg.strip() if isinstance(msg, str) else ""
    return {
        "root": first["root"],
        "surrounding": len(content) - len(first["root"]),
        "tool_name": first["tool_name"],
    }


def nudge_text(hit: dict) -> str:
    """The correction the model sees. Names the REAL failure, not a guessed one.

    Deliberately does not say "malformed" — the JSON was valid, and the generic misformat
    warning sending the model to fix correct JSON is the behaviour being replaced.
    """
    tool = hit.get("tool_name") or "the tool"
    return (
        f"{LOG_PREFIX} Your `{tool}` call was VALID but it was not the whole message — "
        f"{hit['surrounding']:,} characters of prose surrounded it, and the tool parser "
        f"requires the JSON object to be the entire response.\n\n"
        f"Nothing is wrong with the JSON. Do not rewrite or reformat it. Re-send the SAME "
        f"tool call with no text before or after it — no preamble, no explanation, no "
        f"closing remark. Put any reasoning inside the `thoughts` field instead, which is "
        f"where it belongs and where it costs you nothing."
    )
