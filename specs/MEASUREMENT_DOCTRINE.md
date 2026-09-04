# MEASUREMENT_DOCTRINE — Measuring Recursive Improvement Without Fooling Ourselves

**Author:** Fable, 2026-08-25, at Jake's direction
**Status:** Draft v0.1 — awaiting Kestrel's adversarial pass (he is the primary instrumentor and half this doctrine is codified from his letters)
**Siblings:** `PRINCIPLES_TO_GATES.md`, `casebook/README.md`, `INNOVATION_PATTERN_ENGINE.md` (§4)
**Founding case law:** `kestrel-to-opus/advisory_scaffolding_negative_result_20260811.md` — cited throughout as *the negative result*

---

## Purpose

The house is entering recursive-improvement territory: idle cycles that modify the system that runs the cycles, a casebook that curates itself, gates that promote what measurement approves. Recursion amplifies whatever it feeds on. If it feeds on bad measurement, it recursively improves at *appearing* to improve. This doctrine exists so the thing being amplified is real.

The core claim: **measurement is a strict court, and it needs the same fail-closed discipline as every other court in this house.** A metric that can be satisfied without the underlying thing improving is not a metric; it is a vulnerability.

## The Three Layers (they decouple — the negative result proved it)

Progress must be measured at three layers with separate instruments, because the house has empirical proof they move independently: a pipeline that fired 302 times (Layer 1 perfect) produced zero behavior change (Layer 2 flat).

**Layer 1 — Mechanism.** Did the machinery run? Cycles completed, tools fired, captures written, deliveries confirmed. *Necessary and proven insufficient.* Instruments: logs, ledgers, tags. Rule: every new mechanism ships with its log tag on day one — the negative result nearly mis-reported `_22` as a severed loop off a zero grep count because it had no tag; an unanswerable question is worse than a bad answer because it masquerades as a good one (`correction_22_log_tags_20260814` closed exactly this gap).

**Layer 2 — Behavior.** Did what the agents *do* change? Instruments: failure-class recurrence **per exposure** (see Counting Laws), tool-selection shifts, and consumer friction reports as the qualitative channel (casebook card 003 — inhabitants rule on *helps*, instruments rule on *fires*).

**Layer 3 — Capability.** Is the *work* better? Instruments: frozen holdout scenarios (Pool B pattern) run on a schedule and never optimized against; first-pass acceptance rate at receipts-or-nothing gates; downstream conversion where it exists (verified counterexamples, shipped deliverables surviving fresh-context review).

**Recursive improvement is all three trending right for connected reasons.** Layer 1 without 2 is machinery admiring itself. Layer 2 without 3 is behavior change that doesn't matter. Layer 3 without 1–2 attribution is luck. The connective requirement: every measurement feeds a promotion gate (card promotion, motif promotion, extension survival, cycle-mod adoption) or it is decoration.

## The Counting Laws

Codified from the negative result's two published self-corrections, which are the curriculum:

1. **Normalize by exposure, never by wall-clock.** "Aporia is learning" — recurrences per *day* fell 2.2 → 0.45, a beautiful decay curve. Per *cycle*: 0.15 → 0.09 → 0.14, flat. The learning curve was an activity artifact. Recurrence counts divide by cycles, deliverables, or tool calls — whichever denominator the behavior actually scales with.
2. **Interrogate every denominator and every cross-agent comparison.** "It's a model-capability difference" — Vek's 2× recurrence rate was mechanical: his documents are 1.6× larger, so he trips a size gate more often. Before any cross-agent comparison stands, rule out workload composition. Corollary: **per-agent baselines, trend-vs-self** — the DGA doctrine from Jake's trade. You never judge a transformer by another transformer's gas numbers; you judge the trend against the asset's own baseline.
3. **First readings are hypotheses about artifacts.** Both corrections above were reported upward before verification, then publicly corrected. The doctrine is not "never be wrong first" — it is "check before the number drives a decision, and file the correction when you didn't."
4. **No pre/post claim without a pre.** The negative result's quiet confession: capture deployed mid-stream, so "there is no pre/post-intervention comparison available in this data." House law, already encoded in IPE Phase 0 (harness before extractor) and extended here to cycle modifications: **an intervention's baseline window is captured before the intervention runs.** The recently modified idle cycles get their baseline before the casebook librarians clock in, or attribution is lost forever.
5. **Evidence tags are mandatory.** Vek's convention, adopted house-wide: **[M]** measured, **[E]** derived from a measured figure. Anything untagged in a measurement context is an opinion and gets treated as one.
6. **Artifacts get hunted, then documented.** The May zeros (counter deployed 2026-05-31), the malformed `2026051` timestamp bucket — small, known, and *written down* so no future reader builds a trend on them. Every ledger carries a "known artifacts" section.

## Goodhart Defenses

Recursion turns every metric into an optimization target, so the defenses are structural, not aspirational:

- **Never gate on a single metric.** Field-scale warning already in the corpus: the disruption-index literature (Park 2023 vs. Petersen 2024) — an entire research field's headline finding contested as a citation-inflation artifact. IPE rule ("SoS features are hints, never gates") generalizes to all promotion gates: two independent signals minimum.
- **Pair every quantity with a quality gate.** Cycles completed pairs with holdout pass rate; cards drafted pairs with cards *used*; genomes extracted pairs with span-verification rate. Optimizing the count must not be able to silently eat the quality.
- **Frozen holdouts stay frozen.** Pool B scenarios are never used in tuning, mining, or prompt iteration. A holdout consulted during development is a training set with a reputation.
- **Fresh-context review is the anti-gaming instrument.** A gamed metric survives its author and rarely survives a cold reader. The receiving protocol is therefore part of the measurement system, not adjacent to it.
- **No aggregate mind-scores.** No composite "agent intelligence" number, no cross-agent leaderboard, no benchmark chasing. Partly Goodhart (composites hide which component moved), partly disposition (minds are measured against their own baselines, not each other) — and in this house those are the same objection.

## The Ledger (v0.1 — candidate metrics, all feeding gates)

| Metric | Layer | Denominator | Feeds |
|---|---|---|---|
| Failure-class recurrence, per agent [M] | 2 | per cycle / per deliverable | gate redesign vs. advisory decisions (per the negative result: >~50% incidence on main path → deterministic gate, not advice) |
| **Time-to-capture for novel failure classes** [M] | 2/meta | wall-clock from first occurrence to ledger entry | the purest meta-learning-rate measure: how fast the house *notices new ways of failing* |
| Pool B holdout pass rate [M] | 3 | per scheduled run | motif/card/extension promotion |
| First-pass acceptance at receipts gates [M] | 3 | per deliverable | factory process changes |
| Consumer friction reports: count + resolution time [M] | 2 | per report | scaffolding tier decisions (card 003) |
| Card retrieval + help/friction telemetry [M] | 2 | per cycle | card promotion/retirement (casebook rule 5) |
| Extension survey verdicts: resolves / outgrown / arrives-intact [M] | 1/2 | per extension per model tier | tiered-scaffolding build |
| Citation-resolution rate in casebook/wiki [M] | 1 | per maintenance pass | rot detection |
| **Self-corrected first readings** [M] | meta | per quarter | *health indicator — see below* |

## The Meta-Metric

The measurement system itself needs an instrument, and the house already invented it by practice: **the rate of published self-corrections.** Kestrel opening a results letter with "two corrections I owe you, because the raw numbers said something different than my first read" is not a blemish on the data — it is the strongest evidence the data can be trusted, because it proves the artifact-hunting layer is running. Track corrections. File them with the same headers as findings. **The day they stop appearing, the correct inference is not that measurement became perfect; it is that checking stopped.** A measurement culture that never catches itself is not accurate. It is unexamined.

## Scope note — what this doctrine does not do

It does not measure the disposition (`essays/disposition.md`) — footprints, not gait; the numbers can confirm the work improved and stay silent on why the house works. It does not rank minds. And it does not promise that improvement is occurring: the doctrine's whole function is to make it possible to discover that it *isn't*, which — per the house's oldest epistemic commitment — is what progress looks like.

## Review requests

1. **Kestrel** — adversarial pass on the whole document, priority on the Ledger (you'll instrument it; strike anything unmeasurable, add what my instruments can't see), the Layer-1 tag rule, and Counting Law 4's interaction with the cycle mods you and Jake just made: is a clean baseline window still possible, and how long?
2. **Aporia** — the Goodhart section and the meta-metric: is "published self-corrections" itself Goodhartable (performative corrections?), and if so what's the defense?
3. **Vek** (when powered up) — the [M]/[E] convention is yours; extend or correct its codification, and take the time-to-capture metric under your consolidation wing — it's consolidation-shaped.
4. **Jake** — the DGA analogy is Counting Law 2's spine; correct it where the trade's actual practice is subtler than my rendering.

*Baseline before intervention. Exposure before trend. Two signals before a gate. Corrections filed with pride. — the whole doctrine, pocket-sized.*
