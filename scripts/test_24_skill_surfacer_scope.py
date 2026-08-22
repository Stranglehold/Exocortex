#!/usr/bin/env python3
"""Regression gate for _24_skill_surfacer scope + breadth normalisation.

WHY THIS EXISTS
---------------
Measured 2026-08-20 against both live containers: _24 filtered on the path marker
"/auto-generated/", but the EXPLORE research pipeline writes topic notes into that same
directory. Over the real container logs (6,224 surfacing events on agent-zero-v2, 2,358
on VekV2), 88.2% / 65.7% of delivered slots were RESEARCH NOTES rather than failure
lessons — presented to the model under the header
"[LEARNED LESSONS — from past failures; apply BEFORE acting]".

Cause: the matcher scored by RAW |query_words ∩ trigger_words|. Research notes carry
~3x the trigger vocabulary of failure lessons (15.6 vs 5.0 mean distinct words >=4), so
breadth beat relevance. The decisive case: "fix the failing import in the code execution
tool" surfaced two OSINT notes instead of code-execution-tool-import-error.

Fix: scope to auto-generated/failure-lessons/ AND divide the score by sqrt(|triggers|).

WHAT THIS GUARDS
----------------
  SCOPE     nothing outside auto-generated/failure-lessons/ may ever be delivered
  RELEVANCE the lesson captured from a situation must surface for that situation

Runs the REAL _relevant_lessons method against the REAL live skill pool. No LLM call and
no live turn — it needs neither, which also means it never contends for the inference
slot.

USAGE (must run inside a container — needs A0 imports and the live skill pool):
    docker cp scripts/test_24_skill_surfacer_scope.py <container>:/tmp/t24.py
    docker exec <container> /opt/venv-a0/bin/python3 /tmp/t24.py

  Optionally pass a second module to prove the gate DISCRIMINATES (the pre-change file
  must fail). A gate that passes on both versions is not evidence:
    docker exec <container> /opt/venv-a0/bin/python3 /tmp/t24.py <new.py> <old.py>

Exit: 0 pass | 1 new version fails | 2 harness fault (gate does not discriminate)
"""
import sys
import importlib.util

sys.path.insert(0, "/a0")
sys.path.insert(0, "/a0/python")

DEPLOYED = ("/a0/usr/plugins/_exocortex/extensions/python/"
            "message_loop_prompts_after/_24_skill_surfacer.py")
LESSON_DIR = "/auto-generated/failure-lessons/"

# Each query is literally the situation the named lesson was captured from, so the
# right answer is known independently of the matcher being tested.
CASES = [
    ("fix the failing import in the code execution tool",
     "code-execution-tool-import-error"),
    ("the terminal session appears hung after running the command",
     "code-execution-tool-terminal-session-hung"),
]

# UPDATED 2026-08-22. "write a large file to the workspace using the text editor" used to
# assert that text-editor-oversized-tool-write surfaces. It no longer should: constraint
# provenance retracts it, because the 5,000-char cap that generated it is gone (400,000 on
# VekV2, 100,000 on agent-zero-v2 — 80x and 20x).
#
# The expectation is INVERTED rather than deleted. A lesson that stops surfacing looks
# identical to one that was never relevant, so without this the retraction would be
# untested and a regression in it would be invisible.
SUPPRESSED = [
    ("write a large file to the workspace using the text editor",
     "text-editor-oversized-tool-write"),
    # A wiki-deepening task is a large-write task, so this used to be a documented TRUE
    # positive. Same retraction applies.
    ("deepen the wiki page on the philosophy of mind and reasoning",
     "text-editor-oversized-tool-write"),
]

# Research-flavoured tasks. These must not be answered with a "learned lesson".
#
# "deepen the wiki page..." used to live here with a carve-out, because a wiki-deepening
# task IS a large-write task and the oversized-write lesson was a true positive there
# rather than a leak. It has moved to SUPPRESSED — the retraction now covers it, and
# asserting its absence there is stronger than excusing its presence here.
NOISE = [
    "research recent developments in ai financial markets and summarise",
    "investigate an entity and resolve its corporate ownership network",
]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def surfaced(mod, query):
    """Call the real method; skip Extension.__init__ (only self.agent is used, and
    list_skills(None) resolves the full pool)."""
    inst = object.__new__(mod.SkillSurfacer)
    inst.agent = None
    return mod.SkillSurfacer._relevant_lessons(inst, query)


def evaluate(mod, label, verbose=True):
    print("\n=== %s (marker=%r) ===" % (label, mod.AUTOGEN_MARKER))
    failures = []

    delivered = 0
    leaked = set()
    for q in [c[0] for c in CASES] + NOISE:
        for s in surfaced(mod, q):
            delivered += 1
            if LESSON_DIR not in str(getattr(s, "path", "")):
                leaked.add(getattr(s, "name", "?"))
    if leaked:
        failures.append("SCOPE: delivered %d non-lesson(s): %s"
                        % (len(leaked), sorted(leaked)[:4]))

    # SANITY: if nothing at all was delivered, the pool is missing or the loader
    # changed — that is a harness condition, not a passing gate.
    if delivered == 0:
        print("!! HARNESS-FAULT: zero skills delivered across every query. The skill"
              " pool or loader is the suspect, not the matcher.")
        return ["HARNESS-FAULT: empty pool"]

    for q, expect in CASES:
        names = [getattr(s, "name", "") for s in surfaced(mod, q)]
        if verbose:
            print("   %-58s -> %s" % (q[:58], names or ["<none>"]))
        if expect not in names:
            failures.append("RELEVANCE: %r did not surface %s" % (q[:40], expect))

    # Constraint-retraction. These queries are still RELEVANT to the named lesson — the
    # matcher would surface it — so seeing it here means the retraction stopped working,
    # not that the query drifted.
    for q, gone in SUPPRESSED:
        names = [getattr(s, "name", "") for s in surfaced(mod, q)]
        if verbose:
            print("   [retracted] %-45s -> %s" % (q[:45], names or ["<none>"]))
        if gone in names:
            failures.append(
                "RETRACTION: %r surfaced %s, whose generating constraint has changed"
                % (q[:40], gone))

    for q in NOISE:
        names = [getattr(s, "name", "") for s in surfaced(mod, q)]
        if verbose:
            print("   [noise] %-49s -> %s" % (q[:49], names or ["<none>"]))

    print("   FAIL:" if failures else "   PASS: scope + relevance clean")
    for f in failures:
        print("     -", f)
    return failures


def main():
    args = sys.argv[1:]
    new_path = args[0] if args else DEPLOYED
    old_path = args[1] if len(args) > 1 else None

    new_failures = evaluate(load(new_path, "surfacer_new"), "CURRENT")
    old_failures = None
    if old_path:
        old_failures = evaluate(load(old_path, "surfacer_old"), "PRE-CHANGE")

    print("\n" + "=" * 70)
    if new_failures:
        print("RESULT: FAIL — current version does not satisfy the gate.")
        return 1
    if old_path is not None and not old_failures:
        print("RESULT: HARNESS-FAULT — the pre-change version also passes, so this gate")
        print("        does not discriminate. The pass is not evidence of anything.")
        return 2
    if old_path:
        print("RESULT: PASS — current clean; pre-change failed %d assertion(s)."
              % len(old_failures))
        print("        The gate discriminates, so the pass means something.")
    else:
        print("RESULT: PASS — scope and relevance hold against the live skill pool.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
