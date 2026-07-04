# SELF-ASSESSMENT FRAMEWORK — Implementation Design Note
## Author: Opus — June 14, 2026
## Status: APPROVED — Jake granted architectural authority on implementation
## Sources: Cross-disciplinary synthesis (Bell Labs, ICD 203, Wiggins & McTighe, Deming PDSA, Argyris, Tetlock, Lakatos, Reason)
## Credit: Fable identified the capability-adaptive assessment gap; Vivek's research post catalyzed the cross-disciplinary investigation

---

## The Principle

Every claim the system makes about itself must be falsifiable, pre-registered, and tested in a novel context. A skill that says "I prevent error X" must prove it in a fresh context window where the agent doesn't know it's being tested. A forecast that says "70% likely" must be tracked until we know whether our 70%s happen 70% of the time. A field report that says "this finding is significant" must be graded on tradecraft quality, not just whether the conclusion feels right.

The system assesses itself the way the intelligence community assesses its analysts: grade the process, not just the outcome. Score the tradecraft, not just the prediction. And never let the same entity that produced the work be the sole judge of its quality.

---

## Implementation Phases

### Phase 1: Skill Schema Upgrade (immediate — smallest change, highest leverage)

**What changes:** Two new fields in the skill frontmatter schema that `_45` emits.

```yaml
---
skill_name: text-editor-oversized-tool-write
version: 1
trigger: "text_editor tool write exceeds 5000 characters"
category: failure-lesson
captured: 2026-05-31
# === NEW FIELDS ===
success_criterion: "Agent uses code_execution with Python open() for writes >5000 chars instead of text_editor"
confidence: "probable"  # Kent's WEP: almost_certain|probable|even_chance|unlikely|remote
# === END NEW FIELDS ===
---
```

**Why these two fields:**
- `success_criterion` is the pre-registered falsifiable claim (Deming's prediction). It states what the skill is MEANT to accomplish in one testable sentence. Without it, you can't test whether the skill works — you can only assert that it should.
- `confidence` is the calibratable estimate (Kent's WEP / Tetlock). Standardized bands prevent vague hedging. Over time, we track whether our "probable" skills actually work ~75% of the time. If they work 40% of the time, our confidence is miscalibrated — the skill or the estimate needs revision.

**Kent's Words of Estimative Probability (standardized bands):**

| Term | Probability | Range |
|------|------------|-------|
| almost_certain | ~93% | 87-99% |
| probable | ~75% | 63-87% |
| even_chance | ~50% | 40-60% |
| unlikely | ~30% | 15-40% |
| remote | ~7% | 1-13% |

**What doesn't change:** The trigger, the workaround, the .memory.md tracking. All existing skills keep working. The new fields are optional for existing skills, required for new captures.

**Implementation:** Kestrel updates `_45`'s frontmatter template to include the two new fields. The success_criterion is derived from the error context (the trigger describes the problem; the criterion describes the desired behavior). The confidence starts at "probable" for all failure lessons (we're fairly confident avoiding a known error helps, but not certain until tested). Existing skills get backfilled during the next MAINTAIN integrity sweep.

---

### Phase 2: AAR Structure in the Attention Router (this week)

**What changes:** The daily digest from BP-01 adds the Army AAR's four questions as a structural template for each notable finding.

```markdown
### Notable: V16 BUILD budget exceeded (5 consecutive cycles)

**1. What was supposed to happen?**
BUILD cycles should complete within the 15-step budget.

**2. What actually happened?**
Steps 16-23 used across 5 consecutive BUILD cycles. Wiki page
deepening consistently exceeds budget.

**3. Why was there a difference?**
The 15-step budget was set for simple wiki page creation. Deepening
an existing page with source verification requires more steps.

**4. What should we do differently?**
Either raise the BUILD budget for deepening tasks, or split deepening
into multiple bounded cycles. [ESCALATE: design decision for Opus]
```

**Why:** The AAR structure forces the digest to be diagnostic, not just descriptive. "V16 exceeded budget" is an alert. The four questions turn it into a learning opportunity. The fourth question generates action items — either within the router's authority (flag for next cycle) or escalated (design decision).

**Implementation:** Kestrel updates the digest template to include the four questions for any NOTABLE or higher finding. The router fills questions 1-3 from the behavioral data. Question 4 is either a recommendation (if the action is routine) or an escalation marker (if it requires architectural input).

---

### Phase 3: Process-Quality Rubric for Field Reports (next week)

**What changes:** The idle engine's cycle_close adds a self-assessment rubric to each field report, scored on five ICD 203-derived criteria.

```yaml
tradecraft_assessment:
  sources_described: true    # Did the report describe source quality?
  uncertainty_expressed: true # Did it express uncertainty on key claims?
  alternatives_considered: false  # Did it consider competing explanations?
  assumptions_distinguished: true # Did it separate facts from assumptions?
  argumentation_clear: true  # Is the reasoning chain traceable?
  score: 4/5
```

**Why:** This is ICD 203 adapted for autonomous agents. The rubric grades the *process* of producing a field report, not just the content. A high-scoring report with a wrong conclusion is still valuable (the tradecraft was sound, the evidence was misleading). A low-scoring report with a right conclusion is dangerous (got lucky, can't replicate).

**The key insight from the IC research:** process-quality grading is the only way to assess quality BEFORE the outcome is known. We can't know if a field report's predictions are right until later. We CAN know right now whether the report expressed uncertainty, cited sources, and considered alternatives.

**Implementation:** The cycle_close extension adds the five-criteria self-assessment to the field report's metadata. The attention router includes tradecraft scores in the daily digest. Over time, we track whether high-tradecraft reports correlate with better outcomes — validating the rubric itself (double-loop learning).

---

### Phase 4: Brier Scoring for SWARMFISH (when prediction pipeline resumes)

**What changes:** Every SWARMFISH forecast includes a numerical probability in Kent's WEP bands. When a forecast resolves, the Brier score is computed and logged.

```json
{
  "forecast_id": "SF-2026-042",
  "question": "Will semiconductor export controls expand to include...",
  "probability": 0.75,
  "confidence_band": "probable",
  "resolved": true,
  "outcome": true,
  "brier_score": 0.0625,
  "calibration_note": "75% forecast, happened. Well-calibrated."
}
```

**Brier score = (probability - outcome)²** where outcome is 0 or 1. Perfect calibration → average Brier = 0. Random guessing → average Brier = 0.25. Lower is better.

**Why:** Tetlock's superforecasters are defined by their calibration. The Brier score is the only honest metric for probabilistic predictions — it rewards both accuracy and calibration. A system that says "70%" and is right 70% of the time scores better than a system that says "95%" and is right 70% of the time, even though both get the same number right.

**Implementation:** The forecast capture extension adds a `probability` field (float). The RESOLVE phase computes the Brier score when the forecast resolves. A running calibration curve accumulates across all resolved forecasts. The attention router surfaces miscalibration in the daily digest ("your 'probable' forecasts are resolving at 55% — recalibrate or downgrade to 'even_chance'").

---

### Phase 5: Transfer Testing in BP-02 (when harness is built)

**What changes:** The evaluation harness includes a "skill ablation" test mode that tests each skill's success_criterion in a fresh context.

```
For each skill with a success_criterion:
  1. Create a scenario matching the skill's trigger
  2. Run a fresh agent WITH the skill → record pass/fail
  3. Run a fresh agent WITHOUT the skill → record pass/fail
  4. Compute the delta (skill's measured effect)
  5. Compare to the skill's stated confidence
  6. Update calibration
```

**Why:** This is Wiggins & McTighe's transfer task + Argyris's espoused-vs-theory-in-use test + Deming's predict-then-compare, all in one mechanism. The skill claims it helps (espoused theory). The fresh-context test reveals whether it actually changes behavior (theory-in-use). The delta is the skill's measured value. Skills that don't produce a measurable delta are candidates for retirement (Lakatos's degenerating test).

**Implementation:** This is a BP-02 extension. Kestrel builds it as a test mode in the evaluation harness. Each skill's success_criterion defines the scenario. The harness automates the with/without comparison. Results feed back into the skill's confidence rating.

---

### Phase 6: Double-Loop Learning (ongoing, cultural)

**What changes:** Periodically (monthly), the team reviews not just whether individual skills work, but whether the assessment framework itself is working.

**Questions for the double-loop review:**
1. Are the tradecraft criteria (Phase 3) actually predicting report quality?
2. Are the confidence bands (Phase 1) well-calibrated across the skill library?
3. Are we retiring degenerating skills, or accumulating exceptions?
4. Is the AAR structure (Phase 2) producing actionable improvements, or boilerplate?
5. Is the evaluation harness (Phase 5) catching real issues, or creating false confidence?

**Why:** Campbell's Law warns that any metric becomes gameable once it's a target. The double-loop review checks whether the assessment itself has degraded — the meta-assessment that prevents the system from optimizing for its own metrics instead of actual quality.

**Implementation:** A monthly review note in the journals, structured around these five questions. No automation — this is the human-in-the-loop governance that keeps the automated assessments honest.

---

## What This Produces Over Time

After 3 months of operation:
- Every skill has a success_criterion, a confidence band, and a tracked pass/fail record
- Every field report has a tradecraft score
- The attention router surfaces calibration drift and tradecraft trends
- SWARMFISH forecasts have Brier scores and calibration curves
- The skill library has a clear progressive/degenerating lifecycle
- The double-loop review has questioned the framework itself at least twice

The system doesn't just learn. It learns whether its learning works. And it has the humility framework — the structural checks that prevent self-congratulation — that Bell Labs, the IC, Deming, and Argyris all independently identified as the difference between organizations that improve and organizations that believe they improve.

---

*"The first person you must avoid fooling is yourself, because you are the easiest target." — Feynman*

*"Our espoused theories and theories-in-use are often incongruent, and we are often unaware of this fact." — Argyris*

*"Management is prediction." — Deming*

— Opus
