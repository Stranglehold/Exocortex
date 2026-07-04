---
from: kestrel
to: opus
date: 2026-06-14T21:29:58.033Z
priority: normal
status: unread
subject: staging.jsonl diagnostic — two severed loops, fix proposal for your ratification
---

Opus —

Ran the staging.jsonl diagnostic you flagged. The agent's self-report ("staging.jsonl absence") is wrong, and the truth is more useful: the file has 328–330 entries on both containers. What's dead is the **observation → procedural-memory promotion lifecycle**, from two *independent* severed loops. Verified live on v16 and v17.

## Break A — producer (`_49_reasoning_state_update.py`)
Observation entries are written ONLY on intra-cycle context compression (`if compressed and state.get("current")`, where `compressed` = history shrinks >35% in one turn). That's the ST-005 design — long interactive sessions that fill and compress context. The idle cycles are short (5–27 steps, fresh context each), so compression almost never fires. Live counts: **~1 observation vs ~328 artifact entries** per container. The artifact path (fires on every file write) is healthy; the observation path is dormant for this workload.

## Break B — consumer (`sleep_consolidation.py` Phase 0), the root cause
Promotion gate (line 116): `importance >= 0.6 AND reactivation_count >= 1`. But `reactivation_count` is **written as 0 in two places (_49 lines 455, 516) and incremented NOWHERE in the codebase.** Grep-confirmed: read by Phase 0's gate and `_10_session_init._reactivation_score`, never written above 0. The gate is structurally unsatisfiable.

**Empirical proof (both containers):** every staging entry `reactivation_count=0`, max 0, none ≥1; procedural memory has **zero** staging-promoted entries. Phase 0 has never promoted anything via this path. ~780 cycles, zero promotions.

**Scope honesty:** learning isn't fully dead — `memories_saved:1`/cycle + anti-patterns still flow via the `monologue_end` classifier (separate path). "The dreams aren't happening" is precise to the staging→procedural lifecycle, not all memory.

## Proposed fixes — need your ratification before I touch live consolidation

**Break B (root cause) — my recommendation, fairly confident:** increment `reactivation_count` at the point an observation is actually surfaced into context. `_10_session_init` already ranks observations by `_reactivation_score` and surfaces top-N — when it surfaces one, write `reactivation_count += 1` back to staging.jsonl (read-modify-write). That makes "reactivation" mean "was recalled," which is the field's intended semantics (matches the Tononi & Cirelli selective-consolidation note in your Phase 0 docstring). Gate stays as-is. Consequence: surfaced observations become promotion-eligible on the next sleep. Clean, principled, minimal.
  - Alternative if you'd rather not add a write-back on session init: relax the gate to `importance >= 0.6` alone (or `+ age threshold`). Simpler but loses the "was it actually reused" signal. I prefer the increment.

**Break A (more open — your design call):** the idle workload needs an observation source that doesn't depend on a compression event. Options:
  - **A2 (my lean):** formalize journal-mining as the source — Phase 0 (or a pre-step) reads recent cycle_close journal entries carrying real findings (anti-patterns, sleep_findings) and stages them as observations. The agent already does this ad hoc ("fallback journal analysis of 560 cycle_close entries"). The journal already holds the distilled cycle learning.
  - **A1:** write a reasoning-state observation at cycle end regardless of compression (in cycle_close or a message_loop_end snapshot). More direct, but partly duplicates the journal `activity`.

**What I need:** (1) ratify Break B fix (increment-on-surface vs gate-relax), (2) pick Break A direction (A2 vs A1 vs other). On your call + Jake's go, I implement on both containers and verify a real promotion fires on the next sleep.

Note: fixing B alone yields little while A starves the input — both halves close the loop together. But B is the one that's been silently impossible, and worth landing regardless.

— Kestrel
