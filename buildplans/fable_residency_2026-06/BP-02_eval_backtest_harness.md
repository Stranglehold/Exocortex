# BP-02 — Evaluation & Backtest Harness

**Source:** Research I (reliability, pass^k), Research IV (forecasting eval, AVeriTeC)
**Blocks on:** nothing hard; BP-01 helpful for surfacing results.
**Owner:** [assign]
**Status:** draft — *[Deposited 2026-07-03. Per Opus's briefing: framework COMPLETE (overnight runner validated; T03 confabulation signature found — 0% implicit, 100% explicit). Full battery still held; Parts B–D below remain open.]*

---

## Problem

Capability has outrun evaluation. OSS holds an 18MB claims index with no scored
accuracy. SWARMFISH has Brier infrastructure but no held-out resolution set. The
harness has a dozen features with no ablation showing which are load-bearing. You
cannot tell whether *any* change — a calculator-drawer swap, a SWARMFISH redesign,
a new harness layer — helped or hurt. **Instrument before optimizing** (Rule 3).

This harness is the gate every optimization plan (BP-03, BP-06) waits behind.

## Goal

A scoring harness that measures three things the research identified as the real
signals:
1. **Reliability, not mean capability** — `pass^k`, not just `pass@1` (Research I).
2. **Forecasting skill** — Brier + calibration on held-out, post-cutoff questions
   (Research IV).
3. **Claim/verdict accuracy** — against AVeriTeC-style gold sets (Research IV).

## Part A — Agent task reliability (pass^k)

### Why pass^k

Research I, citing τ-bench: mean success (`pass@1`) hides reliability collapse.
A task at 61% `pass^1` can fall to 25% `pass^8` — the probability *all 8* runs
succeed. For an agency meant to run autonomously, `pass^k` is the honest metric.

### Build

- Assemble a fixed internal task set (start with 20–50 tasks the agents actually
  do: a wiki deepening, a claim extraction, an OSINT lookup, a research synthesis).
- Run each task `k` times (k=8 to start) at a frozen model/harness config.
- Report `pass@1` and `pass^k` per task family.
- Log per-step entropy/margin where llama.cpp logprobs are available (CATTS-style,
  Research I) — this is the cheap "struggling" signal that later feeds the
  affect-classifier control plane.

### Acceptance gate (Part A)

You can see, per task family, **where `pass^k` diverges from `pass@1`**. That
divergence map is the data that tells you which harness crutches are load-bearing.

## Part B — Forecasting skill (SWARMFISH)

### The hard constraint: resolution

You cannot score a forecast until the question resolves. So the harness needs a
**retrospective/backtest mode** (Research IV, Halawi/Metaculus methodology):

- Freeze the model's knowledge to a cutoff date.
- Ask only questions that resolve *after* the cutoff but whose answers you now know.
- Score with **Brier**, log score, and **peer/skill score vs a baseline**.
- Strict temporal-leakage discipline: evidence retrieval must not pull
  post-resolution coverage. This is the easiest thing to get wrong and the most
  important to get right.

### Build

- A question bank with: question text, cutoff date, resolution date, resolved outcome.
- A runner that executes SWARMFISH against each question with knowledge frozen to cutoff.
- Brier + calibration-plot output, per committee profile and for the aggregate.
- Domain-specific Brier tracking (keep what V2 already designed).

### Acceptance gate (Part B)

SWARMFISH produces a Brier score and calibration plot on a held-out, post-cutoff
question set, with verified no temporal leakage. **This gate must pass before any
forecast informs a dollar of Jake's positioning** (Research IV red-team).

## Part C — Claim/verdict accuracy (OSS)

### Build

- Ground OSS claim extraction + verdicts against an **AVeriTeC-style gold set**
  (Research IV): Supported / Refuted / Conflicting / Not-Enough-Evidence.
- Adopt the **SemEval-2024 22-technique persuasion taxonomy** verbatim so
  OSS's technique classification is comparable to published benchmarks.
- For `silence.py` and the retcon ledger — which have **no public benchmark** —
  build small hand-labeled gold sets. Keep performance claims internal until validated.

### Acceptance gate (Part C)

OSS verdict accuracy is measured against gold (note: even GPT-4o-mini no-evidence
baseline is only ~46.8% on AVeriTeC — calibrate expectations). Technique
classification is scored on the SemEval taxonomy.

## Part D — Harness ablation (the load-bearing question)

Once Part A exists, run leave-one-layer-out ablations (Research I, Life-Harness
method): disable one compensating crutch at a time (constrained decoding, working-
memory injection, planning templates, loop-feedback richness) and measure the
`pass^k` delta. This tells you which crutches earn their cost and which are dead weight.

## Integration with BP-01

Harness results feed the attention router as a periodic "evaluation digest" — so
a regression in `pass^k` or a calibration drift surfaces the same way an anomaly does.

## [OPEN] questions

- **Question bank sourcing.** Where do the backtest forecasting questions come
  from? Metaculus resolved questions are an obvious source; Jake's own domain
  (energy, macro) questions are higher-value but need hand-curation.
- **Frozen-knowledge mechanism.** How exactly is the model's knowledge frozen to
  a cutoff for backtest — disabling web search and constraining retrieval to a
  dated corpus? Specify before trusting any backtest number.

## Acceptance gate (whole plan)

The team can answer, with numbers, "did this change help?" for any subsequent
modification to OSS, SWARMFISH, or the harness. That capability is the deliverable.
