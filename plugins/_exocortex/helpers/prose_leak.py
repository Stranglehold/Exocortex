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
Detects the case and nudges specifically: *your tool call was valid, it was preceded by
prose, re-emit the JSON alone*. Nudge only — NOT extract-and-execute. Opus's call
(2026-08-22): v2.9 made the parser strict deliberately, to avoid firing a tool call the
model merely DESCRIBED inside an explanation, and that intent is respected until there is
nudge-acceptance data to justify changing it.

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


def find_leaked_call(msg: Any) -> dict | None:
    """Return {'root', 'surrounding', 'tool_name'} if msg is a prose-wrapped VALID call.

    None when: not a string, empty, already a valid whole-message call, a genuinely
    misformatted call (A0's own case — leave it the misformat nudge), no tool-shaped root
    present at all (genuine prose — leave it to _10), or too much surrounding prose.
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

    # Is there a tool-shaped root hiding inside?
    try:
        roots = extract_tools.extract_json_root_strings(content)
    except Exception:
        return None

    for root in roots:
        try:
            parsed = extract_tools._parse_json_root_object(root)
        except Exception:
            continue
        if parsed is None or not extract_tools._is_tool_request(parsed):
            continue

        surrounding = len(content) - len(root)
        if surrounding <= 0:
            # root == content would have parsed above; treat as nothing to do.
            return None
        if surrounding > MAX_SURROUNDING_CHARS:
            return None

        tool_name = ""
        try:
            tool_name, _ = extract_tools.normalize_tool_request(parsed)
        except Exception:
            pass

        return {"root": root, "surrounding": surrounding, "tool_name": tool_name}

    return None


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
