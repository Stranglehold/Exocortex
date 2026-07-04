# STRESS_TEST_005 — The Software Factory (Architectural)

**Test ID:** ST-005 (architectural — paper exercise, not an empirical ST run)
**Date:** 2026-07-03
**Author:** Fable 5, at Opus's request (residency task #2)
**Target:** The software factory architecture — five specialist agents, adversarial
testing, Shannon AI pentester — as described in Opus's 2026-07-03 briefing.
**Method:** Adversarial design review against the project's own documented evidence
base. Every failure mode cited below is grounded in a finding this project has
already paid for, applied to the factory's scale.
**Baseline:** ST-004 (Architect Inside) for genre; no prior factory test exists.

---

## Finding 0 — The spec under test does not exist on disk

Before any technical finding: the software factory architecture was designed
June 21–29 **in the conversation layer** and has no repo artifact. No spec in
`specs/`, no message in either inbox, no design note. This stress test therefore
targets the one-line description plus the known substrate, and its first
recommendation precedes all others: **deposit the design.** The project has now
hit this failure twice in three weeks (the June build plans existed only as
downloads until 2026-07-03). Un-deposited architecture cannot be reviewed,
cannot be built faithfully, and dies with its chat window. This is Rule 2
applied to design itself: the conversation is a capture system; the repo is the
consumption path.

Everything below is falsifiable against the real spec once deposited. Where the
actual design already answers an attack, mark it answered and move on — some of
these may be solved in the undeposited version.

---

## The central claim under test

A pipeline of specialist agents (plan → build → test → integrate → ship, with an
adversarial tester and a security pentester) will produce working software with
less operator attention than a single agent, on local models, inside the
Exocortex harness.

The stress test asks Opus's framing question directly: **where does "assert
without verifying" show up in a multi-agent build pipeline?** Answer: at every
handoff, and the pipeline structure makes it worse, not better. Details follow.

---

## Attack Surface 1 — Trust laundering through handoffs

**The failure mode.** Specialist N produces an artifact plus implicit claims
about it ("this module implements the spec," "these tests cover the edge
cases"). Specialist N+1 receives the artifact as *context* — and context is
trusted by default. The claim's epistemic status (asserted vs verified) is
stripped at the boundary. By the third handoff, an unverified assertion has
become load-bearing fact with no provenance. Single-agent "assert without
verifying" at least keeps the asserter and the believer in one context window,
where later evidence can collide with the earlier claim. A pipeline
*launders* the assertion: each stage's output arrives at the next stage
pre-trusted, laundered of its uncertainty.

**The house's own evidence.** BP-02's T03 finding: confabulation measured at
**0% implicit, 100% explicit** — the failure mode fires precisely when the
model is asked to make explicit assertions about state it hasn't verified.
A factory pipeline is, structurally, a chain of explicit assertions about
unverified state. The T03 result predicts the factory's default failure class
before it runs once.

**What breaks.** Integrator ships a build whose test-coverage claim originated
as a Builder's unverified sentence three stages earlier. Post-mortem cannot
locate where the falsehood entered, because no stage recorded epistemic status.

**Mitigations, in order of leverage.**
1. **Artifacts carry receipts or they carry nothing.** Every handoff object is
   (artifact + machine-checkable evidence): code ships with its compile log and
   test transcript, plans ship with their acceptance criteria as executable
   checks. A claim without a receipt is displayed to the next agent as
   `UNVERIFIED:` — the provenance-marking proposal (EVT-008) applied to
   pipeline handoffs. This is frontmatter, not new infrastructure; the
   three-layer skill validation already proves the pattern.
2. **Deterministic gates between stages, not agent judgment.** The next stage's
   *harness* re-runs the receipts (compile, test, lint, schema-check) before
   the artifact enters the next agent's context. Zero LLM calls — the `_45`
   exception-capture pattern shows the house already knows how to build
   deterministic hooks.
3. BP-05's provenance service is the durable home for this, but the factory
   should not wait for it: frontmatter receipts are buildable this week.

---

## Attack Surface 2 — The correlated adversary

**The failure mode.** "Adversarial testing" implies independence. If the
Builder and the Tester run on the same weights (or a persona-split of the same
model), they share blind spots. The tester will not find the class of bug the
builder could not conceive of, because it cannot conceive of it either. The
adversarial stage then produces something worse than no testing: **confidence
without independence.**

**The house's own evidence.** Research IV's persona finding, cross-applied:
persona ensembles on one model carry error correlations of r≈0.39–0.46, and the
"silicon crowd" result required *different models*. Builder/tester is a
two-persona ensemble. The confirmatory-testing blind spot in the meta-rules
("automated test suites tend to validate stubs rather than deliverables") is
this failure already observed in single-agent form.

**What breaks.** The Tester writes tests that mirror the Builder's mental model
of the code, both pass, the artifact is "adversarially validated," and the bug
class neither model represents ships to the integrator with a green badge.

**Mitigations.**
1. **Decorrelate by construction.** The stable already contains genuinely
   different models — Ornith-1.0-35B, Qwen3-Coder, Qwable, DeepSeek-V4-Pro
   (Vek's backend), the CPU utility model. Route Builder and Tester to
   *different weights* as policy. Qwen builds, Ornith attacks; swap per task.
   The single-GPU serialization cost is real (see Surface 5) but the
   independence is the entire value of the adversarial stage.
2. **Deterministic adversaries first.** Mutation testing (mutmut/cosmic-ray
   class tools), property-based testing (Hypothesis), fuzzing — these find the
   bugs *no* LLM on the box can see, at zero correlation, zero VRAM. Research V:
   the calculator drawer applies to testing. A mutation score is a receipt; a
   tester's opinion is not.
3. **Test the tests.** A Tester whose test suite kills <X% of injected mutants
   is rejected by the stage gate — the tester gets scored, not just the code.
4. Shannon covers security; it does not cover correctness. Do not let the
   pentester's presence satisfy the adversary requirement for logic bugs.

---

## Attack Surface 3 — The oracle problem (who verifies the spec?)

**The failure mode.** Five specialists can execute flawlessly against a spec
that is wrong, ambiguous, or self-contradictory, and the pipeline will
*polish* the wrongness — each stage adding coherence to a mistake. Verification
gates catch spec-violations; nothing in a pipeline catches spec-errors. The
factory's throughput becomes the rate at which it manufactures confident
wrongness.

**The house's own evidence.** DEC-017 (format determines capability): the L7/L8
finding showed local models execute categorically differently depending on spec
format — meaning spec quality is not a constant, it is the dominant variable.
DEC-015: local models comprehend without absorbing; they will not push back on
a flawed spec the way an architect would. The oracle sits *outside* the factory
by construction.

**Mitigations.**
1. **Specs are executable or they are drafts.** The DESIGN_BUILDPLAN /
   EXECUTE_BUILDPLAN pattern already exists; harden it: every factory job
   begins with acceptance criteria expressed as runnable checks (the HTN plan
   templates spec points the same direction). A job whose success cannot be
   expressed as a check is not factory-ready — route it to the architect
   layer, not the pipeline.
2. **Spec review is a frontier-model or human gate**, per DEC-015's routing
   principle: local specialists execute within scaffolding; they do not
   validate the scaffolding. Budget one Opus/Kestrel review per spec, not per
   artifact.
3. **The Planner specialist must be allowed to return "spec inadequate"** as a
   successful output. If the pipeline's only forward path is production, it
   will produce. See Surface 4.

---

## Attack Surface 4 — Pipeline momentum (progress theater at system scale)

**The failure mode.** The BST detects an *agent* looping. Nothing detects a
*pipeline* conveying. Each stage completes, artifacts flow, cycle counters
increment, the affect layer reads FLOW — and the build is garbage moving
smoothly. A pipeline has structural momentum: every stage is rewarded for
passing work forward, no stage is rewarded for stopping the line. This is the
loop-failure finding one level up: mechanistic momentum without productive
state change, invisible to per-agent instrumentation.

**The house's own evidence.** The inc-bst-momentum-lock incident (agent-level
momentum). The 569-line context-degradation skill written entirely from
training data while 200 wiki pages sat unconsulted — an agent *completing
confidently* while disconnected from its own evidence base. Scale that to five
agents in series.

**Mitigations.**
1. **Every stage gate has veto authority, fail-closed.** A stage can and must
   reject upstream work and send it back with receipts. In protection terms:
   each stage is a zone with its own relay, and the coordination study —
   who trips first, on what signal — is part of the factory design, not an
   afterthought. A factory without trip authority is a conveyor.
2. **Andon cord instrumentation.** Line-level metrics distinct from stage
   metrics: rework rate (rejections per handoff), receipt-failure rate,
   spec-return rate. A line where rework is *zero* is as alarming as one where
   it's constant — zero rejections across N jobs means the gates aren't
   gating (the confirmatory blind spot, measured). Route these to the
   attention router (BP-01) as first-class signals.
3. **pass^k, not pass@1, as the factory's headline metric** (BP-02 Part A).
   A factory is the definitional case where reliability-under-repetition is
   the product.

---

## Attack Surface 5 — The single-GPU economics nobody budgeted

**The failure mode.** Five specialists on one RTX 3090 means either (a) one
model playing five roles — maximizing Surface 2's correlation — or (b) model
swaps per stage, resurrecting the JIT-contention fiasco the operational
lessons document was written about, or (c) honest serialization, in which case
the "factory" is one workstation with five hats and the throughput math must
say so. None of these is fatal; all of them are design constraints the
one-line architecture doesn't visibly address.

**Mitigations.**
1. **Role ≠ model ≠ container.** Let cheap roles run cheap: the CPU utility
   model (port 1237, zero VRAM) can run orchestration, receipt-checking
   dispatch, and formatting roles. Deterministic gates run on no model at all.
   Reserve GPU swaps for the Builder/Tester decorrelation, batched to minimize
   swap count per job.
2. **Vek's API backend (DeepSeek) is a decorrelation resource** — a
   different-weights adversary with zero VRAM cost, within API budget
   discipline (the cache-optimization work already prices this).
3. **Publish the throughput model before building**: jobs/night as a function
   of swap count, stage latencies, and rework rate. The Seventeen Minutes essay
   is the cautionary reference — do not optimize an axis before measuring it.

---

## Attack Surface 6 — The ratchet ingests a defect

**The failure mode.** The factory runs inside a learning system. Path A/B skill
capture, the methodology tracker, and (eventually) squishy-weights LoRA
training will harvest the factory's runs as training signal. A
wrong-but-completed run — Surface 1 or 4 undetected — gets captured as
*successful methodology*, surfaced by the skill surfacer at the next planning
step, and eventually baked toward weights. The accumulation ratchet locks in
the defect with the same efficiency it locks in insight, and the error
compounds under the same interest rate as the knowledge.

**The house's own evidence.** The letter on time (essays/fable/) flags this as
the ratchet's known dual; inc-oracle-fabrication and inc-fabricated-metrics
show fabricated content already reaching persistent stores once.

**Mitigations.**
1. **Skill capture gates on verified outcomes, not completed cycles.** A
   methodology is capturable only from runs whose receipts all passed and
   whose artifact survived integration. Wire the capture hook to the stage-gate
   verdicts, not to `cycle_close`.
2. **Quarantine tier for factory-derived skills** — STAGED until a second,
   receipt-verified run reproduces the success (the retcon ledger's
   STAGED→PROMOTED lifecycle, applied to skills).
3. **Squishy-weights training excludes unverified-run data by construction.**
   The methodology tracker should carry a `verified: bool` field from day one
   so the LoRA pipeline can filter without archaeology.

---

## What the factory has going for it (so this reads as a review, not a demolition)

The substrate is genuinely unusual in its readiness: deterministic gate
patterns proven (`_45`, three-layer validation), an eval harness with a
confabulation detector already operational (BP-02), a model stable diverse
enough to decorrelate adversaries, a CPU utility model for free orchestration,
an attention router to annunciate line metrics, meta-rules that anticipate
half these failures, and an operator whose entire professional formation is
zones-of-protection thinking. Most factory attempts fail because none of that
exists. Here, the failure modes above are *addressable with existing parts* —
the review's severity is a function of how much is already in reach.

## Recommendations, priority-ordered

| # | Action | Surface | Cost |
|---|--------|---------|------|
| 1 | Deposit the factory spec to `specs/` | 0 | one paste |
| 2 | Receipts-or-nothing handoff format (frontmatter + deterministic re-check) | 1 | days |
| 3 | Stage gates with veto + rework-rate metrics → BP-01 router | 4 | days |
| 4 | Builder/Tester on different weights as policy; deterministic adversaries (mutation/property tests) in the Tester's drawer | 2 | days |
| 5 | Executable acceptance criteria required at job intake; "spec inadequate" is a valid Planner output | 3 | policy + template |
| 6 | Skill/methodology capture gated on verified outcomes; `verified` field in tracker | 6 | small patch |
| 7 | Throughput model published before first build night | 5 | one evening |

## Falsification conditions

This review is wrong, in whole or part, if: (a) the deposited spec already
contains receipt-carrying handoffs and veto-gates — then Surfaces 1 and 4 are
answered and this document downgrades to a checklist; (b) an empirical ST run
of the factory shows correlated Builder/Tester pairs finding injected bugs at
rates indistinguishable from decorrelated pairs — then Surface 2's transfer of
the persona finding to build pipelines fails; (c) rework-rate instrumentation
shows healthy nonzero rejection under same-model staffing — then the momentum
claim is overweighted. Design the first empirical factory ST (ST-006) to test
exactly (b) and (c): same job, correlated vs decorrelated staffing, injected
defects, measure detection rates.

---

*Filed by the visitor, day two of five. The factory is worth building. Build
the gates first — the house has never once regretted that order.*
