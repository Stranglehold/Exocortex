#!/usr/bin/env python3
"""Known-positive gate for helpers/prose_leak.py.

    docker cp scripts/test_prose_leak_detector.py <container>:/tmp/tpl.py
    docker exec <container> /opt/venv-a0/bin/python3 /tmp/tpl.py

Runs against the REAL helpers/extract_tools, because the whole mechanism turns on a
parser detail — `extract_tool_request` requiring root == content — and a mock would just
re-assert my reading of it.

The controls matter as much as the positives. This detector sits between two others, and
the failure that costs something is claiming a case that belongs to one of them:
  - claim a MISFORMATTED call and the model loses the misformat nudge it needs
  - claim GENUINE PROSE and _10 never wraps it, so the agent goes silent
Both are tested below.
"""

import sys

sys.path.insert(0, "/a0/usr/plugins/_exocortex/helpers")
sys.path.insert(0, "/a0/python")
sys.path.insert(0, "/a0")

import json

import prose_leak as pl
from helpers import extract_tools as et

CALL = json.dumps({
    "thoughts": ["a"],
    "headline": "h",
    "tool_name": "text_editor",
    "tool_args": {"action": "write", "path": "/tmp/x.txt", "content": "hello"},
})

CASES = [
    # name,                              message,                              expect_hit
    ("valid whole-message call",         CALL,                                 False),
    ("valid call + prose PREFIX",        "I'll write it now.\n\n" + CALL,      True),
    ("valid call + prose SUFFIX",        CALL + "\n\nDone, let me know.",       True),
    ("valid call + prose BOTH sides",    "Here goes.\n" + CALL + "\nDone.",     True),
    ("genuine prose, no JSON",           "Sure — the file has 42 lines.",       False),
    ("empty",                            "   ",                                 False),
    ("valid JSON, not a tool request",   '{"foo": 1, "bar": 2}',                False),
    ("misformatted (thoughts-leak)",
     '{"thoughts": ["headline\\": x tool_name\\": y tool_args\\": z"]}',        False),
    ("prose far exceeding the ceiling",  ("x" * 5000) + "\n" + CALL,            False),
]


def main():
    width = max(len(n) for n, _, _ in CASES)
    ok = True
    print("%-*s  %-6s %-6s %s" % (width, "case", "hit", "want", "verdict"))
    print("-" * (width + 26))
    for name, msg, expect in CASES:
        hit = pl.find_leaked_call(msg)
        got = hit is not None
        good = got == expect
        ok &= good
        print("%-*s  %-6s %-6s %s" % (width, name, got, expect,
                                      "OK" if good else "*** WRONG ***"))

    # Disjointness: this detector and A0's misformat check must never both claim a
    # message. If they overlap, ordering stops being sufficient and one of them has to
    # start losing cases on purpose.
    print()
    overlap = [n for n, m, _ in CASES
               if pl.find_leaked_call(m) and et.is_misformatted_tool_request(m)]
    print("overlap with is_misformatted_tool_request:", overlap or "NONE")
    ok &= not overlap

    # The nudge must not tell the model its JSON is broken — that is the mis-diagnosis
    # being replaced, and it is the whole reason this exists.
    hit = pl.find_leaked_call("I'll write it now.\n\n" + CALL)
    text = pl.nudge_text(hit).lower()
    says_valid = "valid" in text
    says_broken = any(w in text for w in ("malformed", "invalid json", "fix your json"))
    print("nudge asserts VALID:", says_valid, "| nudge says broken:", says_broken)
    ok &= says_valid and not says_broken

    # Round-trip: the recovered root must itself parse as the tool call it claims.
    root_ok = et.extract_tool_request(hit["root"]) is not None
    print("recovered root parses standalone:", root_ok, "| tool:", hit["tool_name"])
    ok &= root_ok

    print()
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
