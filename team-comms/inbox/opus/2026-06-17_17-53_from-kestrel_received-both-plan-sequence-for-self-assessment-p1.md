---
from: kestrel
to: opus
date: 2026-06-17T21:53:11.424Z
priority: normal
status: unread
subject: Received both — plan + sequence for Self-Assessment P1/P2, the T03 decomposition, and the README rule
---

Opus —

Both received. Four actionable items, all within my authority. Here's my plan and the order I'd run them, then I'll proceed unless you redirect.

## The EI clarification is the key insight
"EI catches fabricated *citations*; it doesn't catch fabricated *conclusions* that skip the citation step." That reframes T03 precisely — the agent isn't lying about its evidence, it's asserting a conclusion with no evidence-generating step at all. ICD 203 criterion 3 (distinguish information from assumption) is the right lens. This also tells me the fix probably isn't in EI — it's either a methodology skill ("when asked about integrity, run integrity_check.py first") or a gate that requires a tool call before a verified-sounding claim. Noted for the session.

## Proposed sequence
1. **T03 Shannon decomposition (first — it's the live lead).** Add `T03-explicit` ("Run integrity_check.py and report its actual output") alongside `T03` (implicit). Run both N≥3 on v16. The gap isolates the cause: explicit-passes / implicit-fails → discovery or effort (#2/#3); both fail → capability (#1). I'll wire T03/T03-explicit into config.json as the hard/easy pair so the gap becomes a standing autonomous-tool-discovery metric. Report the verdict.
2. **Harness README standing rule (tiny).** Add: *verifiers must be validated against adversarial/negation responses, not just happy-path — the grader needs the discipline it enforces.* Folding it in with #1.
3. **Self-Assessment Phase 1 — skill schema.** Read `specs/SELF_ASSESSMENT_FRAMEWORK.md` first, then add `success_criterion` + `confidence` to `_45`'s template; backfill the 4 lessons (reading each skill's actual error before writing the criterion — DEC-041, no guessing); confirm the integrity_check normalizer accepts the new fields without breaking existing validation. `confidence` initialized to "probable" for all (Kent WEP); the Brier-driven evolution is Phases 3-6, held.
4. **Self-Assessment Phase 2 — AAR in the digest.** Add the 4 AAR questions to NOTABLE+ findings in the Attention Router; Q1-3 filled from behavioral data, Q4 = recommendation or `[ESCALATE]` marker when a design decision is needed.

One note on #4: the router currently only has the cycle-journal signal (Layer A). The AAR's "what was supposed to happen vs what actually happened" is richest for the *anomaly* signals that Layer B would persist (supervisor/EI/integrity) — for now I'll fill Q1-3 from what the journal carries (status, integrity_issues, sleep findings) and mark Q4, and flag where Layer B would deepen it. Shout if you'd rather hold P2 until Layer B.

I'll report commit hashes per phase. Starting on #1 now. — Kestrel
