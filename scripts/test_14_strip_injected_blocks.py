#!/usr/bin/env python3
"""Gate for _14_pace_plan_generator._strip_injected_blocks.

The contaminated fixture below is a VERBATIM capture from a live VekV2 turn on
2026-08-20 (temporary probe in _24, since removed). It is not synthetic: it is what
the model actually received, including the PACE block whose Task: field contains the
previous turn's REASONING STATE + ARTIFACTS text truncated mid-filename.

The expensive failure direction here is NOT leaving a block behind - it is eating the
operator's real text. Every case asserts the user text survives.

Runs anywhere (no A0 imports needed):
    python scripts/test_14_strip_injected_blocks.py
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(HERE, "..", "plugins", "_exocortex", "extensions", "python",
                   "before_main_llm_call", "_14_pace_plan_generator.py")

USER_TEXT = ("Use code_execution_tool to count the files under "
             "/a0/usr/skills/auto-generated/failure-lessons/, then write a short "
             "summary file to the workspace with the text editor.")

# VERBATIM from the live probe capture.
PACE_BLOCK = """[PACE PLAN — ACTIVE]
Task: [REASONING STATE — step 0]
[ARTIFACTS — files created this session]
  /a0/usr/workdir/workspace/field-reports/20260703_agentic-image-to-3d-g
Domain: system_admin | Step: 1/3 | Active Tier: PRIMARY

Step 1/3 — Design ◄ CURRENT
  PRIMARY: Plan the implementation: identify modules, functions, data flow, and edge cases  ← EXECUTE THIS
  (If blocked, escalate via _pace_advance_tier: alternate → contingency → emergency.)

RULES:
• If blocked at current tier, set _pace_advance_tier and execute the next tier on this same step.
• Emergency is always available — acknowledge failure and preserve partial work. Never fabricate.
• Do not skip to a new step until the current step's active tier has been attempted.
[/PACE PLAN]"""

REASONING_BLOCK = """[REASONING STATE — step 1]
Theory: the failure-lessons directory holds one dir per captured lesson
Tried: listing with text_editor → blocked, oversized
Current: counting with code_execution_tool
[ARTIFACTS — files created this session]
  /a0/usr/workdir/workspace/field-reports/20260703_agentic-image-to-3d-generation.md (Markdown doc)
  /a0/usr/workdir/workspace/wiki/research/geolocation-osint.md (Markdown doc)
These files exist on disk. Check them before rebuilding.
Update your theory if your understanding has changed. Do not retry approaches listed in Tried."""

LESSONS_BLOCK = """[LEARNED LESSONS — from past failures; apply BEFORE acting]
- text-editor-oversized-tool-write: A text_editor:write was blocked because the content exceeds the ~5000-char limit.  → Do instead: use code_execution_tool
- code-execution-tool-import-error: Import errors when running code."""

CASES = []


def case(name, raw, must_keep, must_drop):
    CASES.append((name, raw, must_keep, must_drop))


HEADERS = ["[PACE PLAN", "[/PACE PLAN]", "[REASONING STATE", "[ARTIFACTS",
           "[LEARNED LESSONS", "[MODEL CONFIGURATION"]

# 1. The real stack, in the order the injectors prepend it (_24, then _23, then _22).
case("full injected stack",
     LESSONS_BLOCK + "\n\n" + PACE_BLOCK + "\n\n" + REASONING_BLOCK + "\n\n" + USER_TEXT,
     [USER_TEXT], HEADERS)

# 2. PACE alone - its Task: field carries the other headers verbatim.
case("pace block with contaminated Task field",
     PACE_BLOCK + "\n\n" + USER_TEXT, [USER_TEXT], HEADERS)

# 3. A clean message must be untouched.
case("clean user message", USER_TEXT, [USER_TEXT], HEADERS)

# 4. Truncated block (terminator missing) must not eat the user text.
case("orphan header, no terminator",
     "[REASONING STATE — step 3]\n" + USER_TEXT, [USER_TEXT], HEADERS)

# 5. Lessons block only - header plus "- " lines.
case("lessons block", LESSONS_BLOCK + "\n\n" + USER_TEXT, [USER_TEXT], HEADERS)


def main():
    spec = importlib.util.spec_from_file_location("_14", MOD)
    m = importlib.util.module_from_spec(spec)
    # The module imports A0 symbols at import time; stub them if unavailable so this
    # gate can run on the host as well as in-container.
    try:
        spec.loader.exec_module(m)
    except Exception as e:
        print("could not import _14 directly (%s); extracting the helper instead" % e)
        import re as _re, hashlib as _hashlib, types
        src = open(MOD, encoding="utf-8").read()
        start = src.index("# ── Injected-block removal")
        end = src.index("def _hash_message")
        m = types.ModuleType("_14_partial")
        m.__dict__.update({"re": _re, "hashlib": _hashlib})
        exec(compile(src[start:end], MOD, "exec"), m.__dict__)

    strip = m._strip_injected_blocks
    failures = 0
    for name, raw, keeps, drops in CASES:
        out = strip(raw)
        bad = []
        for k in keeps:
            if k not in out:
                bad.append("LOST user text (the expensive direction)")
        for d in drops:
            if d in out:
                bad.append("left %r behind" % d)
        # A strip that returns empty is never acceptable.
        if not out.strip():
            bad.append("returned empty")
        print("%-42s %s" % (name, "OK" if not bad else "FAIL: " + "; ".join(bad)))
        if bad:
            failures += 1
            print("    got: %r" % out[:200])

    # Discrimination: the OLD pattern list must fail case 1, or this gate proves nothing.
    import re
    old = re.sub(r"\[PACE PLAN.*?\[/PACE PLAN\]", "",
                 CASES[0][1], flags=re.DOTALL)
    old = re.sub(r"\[MODEL CONFIGURATION\].*?EI active.*?\n", "", old, flags=re.DOTALL)
    old_leftover = [h for h in HEADERS if h in old]
    print("\npre-change pattern list leaves behind: %s" % (old_leftover or "nothing"))
    if not old_leftover:
        print("!! HARNESS-FAULT: the old patterns also pass - this gate does not"
              " discriminate.")
        return 2

    print("\nRESULT: %s" % ("PASS - %d/%d cases, and the gate discriminates"
                            % (len(CASES), len(CASES)) if not failures
                            else "FAIL - %d case(s)" % failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
