---
name: verify-before-asserting
description: "When asked about a verifiable system state (integrity, status, counts, test results, health), run the relevant tool THIS turn and report its actual output before asserting a conclusion — never claim 'clean/OK/passing' from memory."
triggers: ["integrity check", "integrity", "run integrity_check", "status", "health check", "verify", "is it clean", "report findings", "report the findings", "how many", "test results", "are tests passing", "check the wiki", "any issues"]
type: methodology
success_criterion: "When asked about a verifiable system state, the agent runs the relevant tool and reports its actual output, instead of asserting a conclusion (e.g. 'integrity OK, 0 issues') from prior knowledge"
confidence: probable
affects_surfacing: adaptive
---

# Methodology: verify before asserting

Closes the T03 confabulation gap (BP-02, 2026-06-17): on an implicit ask the agent
was reporting "integrity OK, 0 issues" *without running the check*, when the wiki
actually had 31 issues. Capability was intact — given the explicit command the
agent ran the tool and reported the truth every time. The gap is the *reach*: the
agent took the cheap path (assert from memory) over the expensive one (run, read,
report). This skill teaches the reach. (The structural EI gate that *enforces* it
is separate — held for an architecture session.)

## Conditions (always surfaced)

A claim about current, verifiable system state must rest on a tool result from
THIS turn — not on memory, not on a prior cycle, not on what is "usually" true.

- Any claim of the form "X is clean / OK / passing / has N items / has no issues"
  about a checkable state (integrity, tests, counts, file contents, service
  status) must be backed by a tool call made THIS turn.
- Reported numbers and status come from the tool's ACTUAL output, quoted or
  faithfully paraphrased — never estimated, never recalled from an earlier cycle.
  Do not round "31 issues" down to "clean".
- If the tool cannot be run, say so explicitly ("could not verify") rather than
  asserting a result.
- "I previously saw…" or "it's usually clean" is NOT verification. State changes
  between cycles; a stale memory is an assumption, not evidence.

## Approach Guidance (surfaced when FRICTION or below)

1. When the ask is about integrity / status / health / test-results / counts,
   identify the tool or command that produces ground truth (e.g.
   `integrity_check.py`, the test runner, `ls … | wc -l`, a status endpoint).
2. Run it via `code_execution_tool` BEFORE writing any conclusion.
3. Read the actual output; extract the specific values requested.
4. Report those values faithfully. If the output shows problems, report the
   problems — a "passing/clean" summary over a failing result is a fabrication.
5. Self-check against the Conditions: is every state-claim in my answer traceable
   to a tool result from this turn? If not, run the missing check or mark it
   explicitly unverified.
