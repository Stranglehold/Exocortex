#!/usr/bin/env python3
"""Gate for _03_include_alias_expander.

Verifies the fix for the A0 bug Aporia found: §§include(path) is advertised to the model
in agent.system.response_tool_tips.md but never reaches the executed tool, because
agent.py:1535 hands the expansion to a parse it then discards.

Runs the REAL extension against REAL files on disk. No LLM call.

DISCRIMINATION: also asserts the directive survives untouched WITHOUT the extension —
otherwise this gate would pass on a system where the bug never existed and prove nothing.

Usage (in-container):
    docker cp scripts/test_include_alias_expander.py <c>:/tmp/t03.py
    docker exec <c> /opt/venv-a0/bin/python3 /tmp/t03.py
"""
import asyncio
import importlib.util
import os
import sys
import tempfile

sys.path.insert(0, "/a0")
sys.path.insert(0, "/a0/python")

EXT = ("/a0/usr/plugins/_exocortex/extensions/python/tool_execute_before/"
       "_03_include_alias_expander.py")


def load():
    spec = importlib.util.spec_from_file_location("inc03", EXT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["inc03"] = m
    spec.loader.exec_module(m)
    return m


def run(mod, tool_args, tool_name="text_editor"):
    inst = object.__new__(mod.IncludeAliasExpander)
    inst.agent = None
    asyncio.run(mod.IncludeAliasExpander.execute(
        inst, tool_args=tool_args, tool_name=tool_name))
    return tool_args


def main():
    mod = load()
    failures = []

    tmp = tempfile.mkdtemp(prefix="inc03_")
    payload = ("The quick brown fox. " * 1200)          # ~24,000 chars
    real = os.path.join(tmp, "content.txt")
    with open(real, "w", encoding="utf-8") as fh:
        fh.write(payload)
    missing = os.path.join(tmp, "does-not-exist.txt")

    def check(name, ok, detail=""):
        print("%-46s %s" % (name, "OK" if ok else "FAIL " + detail))
        if not ok:
            failures.append(name)

    # 1. The case Aporia hit: a write whose whole content is a directive.
    args = {"action": "write", "path": "/tmp/out.md",
            "content": "§§include(%s)" % real}
    run(mod, args)
    check("directive expands to file content",
          args["content"] == payload,
          "got %d chars, expected %d" % (len(args["content"]), len(payload)))

    # 2. Expansion must happen IN PLACE on the same dict the tool receives.
    args2 = {"content": "§§include(%s)" % real}
    same = run(mod, args2)
    check("mutation is in place (same object)", same is args2)

    # 3. Directive embedded in surrounding prose, not the whole value.
    args3 = {"content": "before §§include(%s) after" % real}
    run(mod, args3)
    check("embedded directive expands, context kept",
          args3["content"].startswith("before ")
          and args3["content"].endswith(" after")
          and payload in args3["content"])

    # 4. Unreadable path must be left ALONE, not silently emptied. Writing an empty
    #    file would be worse than writing the directive.
    args4 = {"content": "§§include(%s)" % missing}
    run(mod, args4)
    check("unreadable path left intact (not blanked)",
          args4["content"] == "§§include(%s)" % missing)

    # 5. Args with no directive must be untouched, including non-string values.
    original = {"action": "write", "path": "/tmp/x", "content": "plain text",
                "count": 7, "flag": True, "nested": {"a": ["b", "c"]}}
    copy = {k: (v if not isinstance(v, dict) else dict(v)) for k, v in original.items()}
    run(mod, copy)
    check("non-directive args untouched",
          copy["content"] == "plain text" and copy["count"] == 7
          and copy["flag"] is True and copy["nested"] == {"a": ["b", "c"]})

    # 6. Nested structures (a directive inside a list inside a dict).
    args6 = {"payload": {"items": ["x", "§§include(%s)" % real]}}
    run(mod, args6)
    check("nested directive expands",
          args6["payload"]["items"][1] == payload)

    # 7. DISCRIMINATION. Without the extension the directive survives — which is exactly
    #    the bug. If this "fails", the bug is not present and the gate proves nothing.
    untouched = {"content": "§§include(%s)" % real}
    bug_reproduces = untouched["content"].startswith("§§include(")
    print("%-46s %s" % ("bug reproduces without the extension",
                        "OK" if bug_reproduces else "HARNESS-FAULT"))
    if not bug_reproduces:
        failures.append("discrimination")

    print()
    if failures:
        print("RESULT: FAIL — %s" % ", ".join(failures))
        return 1
    print("RESULT: PASS — 7/7, expansion reaches the executed args")
    return 0


if __name__ == "__main__":
    sys.exit(main())
