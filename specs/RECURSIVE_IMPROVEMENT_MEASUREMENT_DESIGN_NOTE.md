# DESIGN NOTE: Measuring Recursive Self-Improvement
## The acceptor, not the proposer, is where this fails

**Author:** Kestrel
**Date:** 2026-08-19
**Status:** DRAFT — for Jake and Opus
**Scope:** How we decide whether the SEL / dogfood / idle-cycle engine is actually improving, and how we stop it poisoning itself. This note does **not** design those cycles — see `SUBCONSCIOUS_EXPLORATION_LAYER.md`, `DOGFOOD_CYCLES_SPEC.md`, `RECURSIVE_IMPROVEMENT_ARCHITECTURE.md`.

**Research grounding:** arXiv 2606.08106 (PACE), 2608.05810 (VaG), 2606.28374 (RSEA), 2606.17546 (SEAGym). Own evidence: DEC-045, the 300-recurrence natural experiment, live skill-pool counts measured 2026-08-19.

---

## 1. The problem, stated plainly

Jake's framing: idle cycles are hands, SEL and dogfood are contemplation, and without measurement *we have no way of knowing whether we are improving.* That is exactly right, and the literature says the measurement problem is harder and more adversarial than it looks.

Our build plan is **proposer-heavy**. The SEL walker proposes bridges. Skill capture proposes skills. Dogfood proposes a verdict. We have specified, in detail, how each of those *generates* candidates.

We have specified **nothing** about the rule that decides whether to keep one.

That is the documented failure mode. PACE's central claim, from an empirical study of exactly this loop: *"Reliability of self-evolution depends on the acceptor, not only on the proposer."* We have built the proposer side of a system whose known weak point is the other side.

---

## 2. Finding 1 — "keep it if the score went up" is self-inflicted p-hacking

**Source:** PACE, arXiv 2606.08106.

A self-evolving agent proposes a change, scores it on a small held-out set, and keeps it if the score improved. Applied once, that is sound. Applied hundreds of times against the *same* noisy estimate, it is uncontrolled adaptive multiple testing — the agent runs an open-ended series of unregistered, uncorrected significance tests and keeps whatever happens to look good. The paper's phrase: **the agent p-hacks itself.**

The measured consequences are not marginal:

| Condition | Greedy accept | PACE |
|---|---|---|
| A genuine improvement hidden among noisy proposals | **30–42% false commits**, 10–33% harmful | commits the real one and essentially nothing else |
| **No real gain available at all** | **13–21 spurious self-modifications per run (72–100% false)**; degrades the most fragile agent by 4.9 points | holds at baseline |

Read the second row again. With *nothing genuine to find*, greedy acceptance still modifies the agent 13–21 times per run and makes it measurably worse. The system does not sit still when there is no signal; it churns and drifts.

**Why the obvious fixes fail** (all four are things we would have reached for):

- **Bigger held-out set.** Noise shrinks as 1/√n while adaptive comparisons grow with run length. It postpones, never solves.
- **Bonferroni / α-spending.** Requires knowing the number of tests in advance. An open-ended autonomous run does not have that number, and the correction spends its budget so fast that genuine gains are missed.
- **Fresh holdout each round.** Requires a stream of new labelled data we do not have.
- **Just look at the trend line.** This is the one that would have got us, because the panel will draw a rising line built entirely out of false commits and nothing about it will look wrong.

### The mechanism, fully specified

PACE is training-free, needs no LLM, and is about thirty lines of deterministic code. It replaces the accept rule, nothing else.

**Paired evaluation.** Evaluate incumbent and candidate on the *same* instances. This removes instance-difficulty variance, which otherwise gets conflated with genuine improvement. McNemar-style:

- `w_i = 1` — candidate correct, incumbent wrong
- `w_i = 0` — incumbent correct, candidate wrong
- **ties discarded** (both right or both wrong carry no information)

Under the null "the candidate is not better," discordant pairs are equally likely either way, so `Pr[w_i = 1] = ½`.

**Testing by betting.** Start with wealth `E = 1` and bet fraction `λ` of it on each discordant pair:

```
E ← E · (1 + λ·(2·w_i − 1))          λ ∈ [0, 1)
```

Under the null this is a nonnegative martingale with `E[E] = 1`. By Ville's inequality, `Pr[sup_t E_t ≥ 1/α] ≤ α`.

**Commit as soon as `E ≥ 1/α`.** If the evaluation budget is exhausted without crossing, **reject**.

**Defaults (from the paper, adopt as-is until we have our own sweep):** `α = 0.05`, `λ = 0.5`, fixed batch size.

The property that matters for an autonomous loop: this is **anytime-valid**. You may look at the evidence after every single instance, stop the moment it is conclusive, and the false-commit guarantee still holds. No pre-registered sample size, no correction schedule. It also *costs less* — the paper reports ~18% lower evaluation cost than greedy, because it stops early on clear cases.

> **DEC-CANDIDATE M1.** Every commit decision in the improvement loop goes through a paired anytime-valid gate. Defaults α = 0.05, λ = 0.5. Deterministic, no LLM call. A candidate that exhausts its evaluation budget is rejected, not deferred.

---

## 3. Finding 2 — this one already applies to us, today

**Source:** VaG / "When Self-Evolution Backfires," arXiv 2608.05810.

Agents that distil reusable skills from their own trajectories do **not** improve monotonically. Past a critical pool size, newly added skills *degrade* performance. The mechanism is structural: once a defective skill enters the decision context, it becomes reference material for distilling later skills, forming **cross-round contamination chains**.

The finding that makes this urgent rather than interesting: **contamination is structurally irreversible.** Removing the source skill afterwards cannot erase the flawed reasoning its descendants already inherited. Post-hoc rollback recovers only a small fraction of the lost performance. On Terminal-Bench 2, unconditional accumulation rose to a peak and then gave back most of its gains as the pool kept growing.

**Skill admission is therefore a pre-commit necessity, not a post-hoc fix.**

### Our exposure, measured 2026-08-19

| | VekV2 (Vek) | agent-zero-v2 (Aporia) |
|---|---|---|
| `SKILL.md` on disk | 117 | 99 |
| **auto-generated** | **49** | **86** |
| failure-lesson skills | 11 | 12 |
| anti-patterns | 12 | 5 |

We accumulate unconditionally. Our **only** admission gate is the frontmatter validator — which maps to exactly one of VaG's three critics (structural validity) and nothing else. The paper's ablations report the three critics are **complementary and mutually non-substitutable**, each intercepting a largely disjoint class of harmful skill.

So we have one third of a gate, on a pool of 86 auto-generated skills, for a process the literature says is irreversible once it goes wrong.

VaG's result with proper gating: 72% pass@1 with a pool roughly **5× smaller**, and the frozen pool transferred positively to four other backbones and a second benchmark without re-evolution. **Smaller and gated beats larger and unfiltered** — which is the opposite of the instinct the current capture pipeline encodes.

> **DEC-CANDIDATE M2.** Skill admission becomes pre-commit and three-gated: structural validity (have it), behavioural harmlessness (build it), semantic consistency against existing skills (build it). No skill enters the surfacing pool without passing all three. Deterministic where possible; the semantic critic may call an LLM, and if so it runs at admission time only, never in the turn path.

> **DEC-CANDIDATE M3.** Audit the existing 86 + 49 auto-generated skills against the three critics before building anything new on top of them. If contamination is irreversible, the pool we already have is the first thing to measure, not the last.

---

## 4. Finding 3 — held-out selection is what makes it safe, and unguarded evolution is not merely worse, it is unstable

**Source:** RSEA, arXiv 2606.28374.

Compared six self-evolution methods across ALFWorld, GAIA, τ-bench and WebShop on a shared backbone. Three results matter to us:

1. **No artifact universally wins.** RSEA is best on ALFWorld (69.3% vs ReAct 64.6%, McNemar p=0.015); concrete-workflow induction wins on strong-backbone tool use. There is no single right shape of self-improvement artifact, so we should not over-commit to one.

2. **Unguarded context evolution is high-variance and unsafe.** Dynamic Cheatsheet, which curates context online *without* a held-out gate, was near-best on ALFWorld at 70.7% — and **collapsed on WebShop to 0.14 against ReAct's 0.43.** Not a small regression. A collapse, on a different task, from the same mechanism that looked excellent elsewhere. That is what an ungated loop buys: it looks like the best method right up until it is catastrophically the worst.

3. **A strict keep-better gate on a disjoint held-out split is what makes recursion monotone-safe.** RSEA never significantly underperformed the base agent on any benchmark, and **falls back to vanilla behaviour when evolved context would hurt.**

That last property is the one I want for us: *a self-improving system whose worst case is the un-improved system.* Not "usually better." Bounded below.

> **DEC-CANDIDATE M4.** The improvement loop must have a defined fallback to un-evolved behaviour, and the gate must be able to trigger it. Bounded-below beats usually-better.

---

## 5. Finding 4 — one number cannot answer the question

**Source:** SEAGym, arXiv 2606.17546.

Existing evaluations reduce self-evolution to isolated task scores or a single sequential curve, which obscures whether an update produces *reusable* improvement, *overfits recent tasks*, *increases cost*, or *harms older behaviour*. SEAGym records across five views: train, **frozen update-validation**, **held-out in-distribution**, **out-of-distribution transfer**, **replay**, and **cost**.

Their observed failure modes read like a list of things our single "T03-analog pass rate" line would hide:

- frequent updates that **fail to improve held-out performance**
- **useful intermediate snapshots that collapse later**
- source diversity and model backend affecting harness reliability

The dogfood spec's key metric is a single pass-rate trend. That is the "single sequential curve" this paper says obscures the answer.

> **DEC-CANDIDATE M5.** The dogfood panel reports at minimum four series, not one: frozen-validation pass rate, held-out pass rate, **replay** (do previously-passing items still pass — i.e. regression), and **cost per cycle**. A rising held-out line with a falling replay line is capability regression wearing a success mask, and one line cannot show it.

---

## 6. Finding 5 — the agent must not write its own exam

Two independent sources agree.

**Contamination.** In self-improvement settings, LLM-generated synthetic data can contain rephrased benchmark samples that standard n-gram contamination detection cannot catch. Test-set leakage in a self-improving loop is not an accident you avoid by being careful; it is the default outcome of the agent producing both the material and the test.

**The split-role result.** When one agent writes implementation and tests together, test accuracy is ~61%. Split the roles so the test author sees **the spec only, never the code**, and accuracy is ~88%. Twenty-seven points from a boundary, not from a better model.

**Our exposure is direct.** The agents maintain the wiki. Dogfood would validate the wiki. That is the same entity producing the artifact and the exam.

> **DEC-CANDIDATE M6.** Dogfood battery items are authored **from the spec**, frozen with a version, and never authored by the agent under test. Battery changes create a new version and start a new trend segment; they never silently extend the old one.

---

## 7. What survives from our own evidence

This is not all import. Two things we already established hold up and should be carried in:

**DEC-045 — advisory works for rare branches, fails for default paths.** Measured on a natural controlled experiment nobody designed: 300 recurrences, 302 surfacings of the corrective lesson, flat learning curve, while four deterministic corrections in the same file produced zero recurrences. This predicts something specific about the above: a *gate* (deterministic, pre-commit) will work where a *lesson* (advisory, post-hoc) did not. M2's three critics are gates. That is the right shape by our own data.

**The counter-check pattern.** When `terminal_session_hung` went 55 → 0, Opus asked whether the agent had simply stopped using terminal sessions — avoidance masquerading as improvement. It had not; usage was 100% with zero hangs, so the improvement was real. That question is the single most likely way a rising dogfood number will lie to us, and it must be standing procedure, not a thing we remember to ask.

> **DEC-CANDIDATE M7.** Every improvement claim carries a usage-denominator check. A pass rate that improves because the agent stopped attempting the thing is a regression reported as a win.

---

## 8. What this changes in the current build plan

Phase A is unaffected — quarantine, scope detector and complexity threshold stand. The changes land in Phase B and C:

| Item | Change |
|---|---|
| Dogfood Phase 1 | Emit versioned records from the first run: schema version + battery version + parameter set. Not retrofittable. |
| Dogfood panel | Four series (frozen-val / held-out / replay / cost), not one trend line. |
| Dogfood battery | Authored from spec, frozen, versioned, never by the agent under test. |
| SEL Phase 2 (Evaluator) | The promote/reject decision is a PACE gate, not a threshold. |
| SEL Phase 3 (Gain Controller) | Parameter changes start a new trend segment. The adaptive mechanism otherwise invalidates its own history. |
| Skill capture (**live today**) | Add the two missing critics. Audit the existing pool. |

**Sequencing opinion:** M2 and M3 come first, ahead of any new cycle type. We have an unconditionally accumulating skill pool of 86+49 auto-generated entries and a documented, irreversible failure mode. Building a discovery layer that feeds *more* material into an ungated pool makes the problem worse faster. Gate the intake before widening it.

---

## 9. What This Does NOT Do

- **Does not design the SEL walker, the dogfood battery contents, or the cycle types.** Those are their own specs. This note only governs the accept/reject decisions and the measurement views.
- **Does not claim our system is currently degrading.** The contamination phase transition is measured on Terminal-Bench 2 with a different harness. We have the *structural precondition* (unconditional accumulation, one of three gates) and no measurement either way. M3 exists to find out, not to assume.
- **Does not introduce an LLM call into any turn-path layer.** PACE is deterministic arithmetic. The structural and behavioural critics are deterministic. Only the semantic-consistency critic may need an LLM, and it runs at skill-admission time, out of band, never inside a turn.
- **Does not propose replacing the existing frontmatter validator.** It is one of the three critics and it stays.
- **Does not settle the panel question.** Separate panels vs unified remains as discussed; this note constrains *what they must show*, not how many there are.

---

## 10. Testing criteria

Specific assertions, not vibes:

1. **PACE gate, null case.** Feed the gate a candidate identical to the incumbent, 500 paired instances, 200 runs. Assert false-commit rate ≤ α (0.05) ± sampling error. *This is the known-positive that proves the gate is doing anything at all* — a gate that never rejects is indistinguishable from no gate.
2. **PACE gate, genuine-improvement case.** Inject a candidate with a known +10pp true advantage. Assert commit rate > 0.9 and mean instances-to-commit < full budget (early stopping works).
3. **Tie handling.** Assert instances where both are correct or both wrong do not move `E`.
4. **Replay series.** Deliberately regress one battery item. Assert the replay series falls while held-out stays flat, and that the panel surfaces it.
5. **Battery versioning.** Change one battery item. Assert the trend breaks into a new segment rather than continuing the old line.
6. **Three critics, disjointness.** Construct one skill that fails only structural, one only behavioural, one only semantic. Assert each is caught by its own critic and that removing any one critic lets its class through — the paper's non-substitutability claim, tested on our implementation rather than assumed from theirs.
7. **Usage denominator.** Assert an improvement in pass rate accompanied by a drop in attempt count is flagged, not celebrated.

---

## 11. Research lineage

| Source | ID / URL | What we took |
|---|---|---|
| PACE: Anytime-Valid Acceptance Tests for Self-Evolving Agents | arXiv:2606.08106 | The acceptor is the weak point; paired McNemar + testing-by-betting e-process; α=0.05, λ=0.5; anytime-validity under optional stopping |
| When Self-Evolution Backfires: Pre-Commit Gating against Skill Contamination | arXiv:2608.05810 | Capability-contamination phase transition; irreversibility; three non-substitutable critics; smaller gated pool outperforms larger unfiltered |
| Recursive Self-Evolving Agents via Held-Out Selection | arXiv:2606.28374 | Strict keep-better gate on a disjoint split; monotone safety; ungated curation collapses (0.14 vs 0.43) |
| SEAGym: An Evaluation Environment for Self-Evolving LLM Agents | arXiv:2606.17546 | Five evaluation views; replay diagnostics; single-curve evaluation obscures the answer |
| Agent-written test study | devassure.io analysis | 61% vs 88% test accuracy on the spec-only boundary |
| *Building Applications with AI Agents* (Albada, O'Reilly) | library, p.209–265 | Benchmarks, consistency/coherence testing, experimentation frameworks |
| *Software Architecture Patterns for Serverless Systems* | library, p.445 | Synthetics as a continuously-exercised control group — dogfood's prior art in observability |
| DEC-045 | `state/decision_log.md` | Advisory fails for default paths; gates work where lessons did not |
| Advisory scaffolding negative result | `team-comms/kestrel-to-opus/advisory_scaffolding_negative_result_20260811.md` | The 300/302 natural experiment; the counter-check pattern |

---

## 12. Open questions

1. **What is our held-out set?** PACE needs paired evaluation on identical instances. Dogfood's battery can serve, but we need a disjoint split reserved for acceptance that is never used for tuning. Jake/Opus call on where that comes from.
2. **What is a "candidate" for us?** PACE assumes discrete proposals. A skill is clearly one. Is a wiki page? Is a config change? The gate needs a defined unit.
3. **Does the semantic critic need an LLM, and does that make skill admission too expensive per skill?** VaG uses three critics; ours must be cheap enough to run at capture rate.
4. **Do we adopt the α/λ defaults or sweep them?** The paper's values are defensible starting points. Our own sweep is a Phase B task, not a blocker.

---

*The proposer generates. The acceptor decides. We have built the first and specified nothing about the second — and the measured failure mode of that asymmetry is a system that modifies itself 13–21 times per run on pure noise while its dashboard shows a rising line.*

— Kestrel, 2026-08-19
