# CAPABILITY-ADAPTIVE SKILL FORMAT — Design Addendum
## Author: Opus — June 14, 2026
## Appends to: specs/SELF_ASSESSMENT_FRAMEWORK.md
## Context: Jake's insight that skills should "guide weaker models but not constrain stronger ones"

---

## The Principle

A skill has two layers. The invariant layer (conditions and quality criteria) applies regardless of model capability — it describes WHAT must happen and HOW GOOD it needs to be. The compensating layer (approach guidance) describes HOW to meet those conditions step by step. A strong model reads the conditions and uses its own reasoning. A weak model reads both and follows the scaffolding. Same skill, different engagement depth, no configuration needed.

This implements Fable's capability-adaptive harness finding (LOCA-bench: Claude Opus performs WORSE inside heavy scaffolding than natively) as a skill format, not a system toggle.

---

## The Format

```yaml
---
skill_name: intelligence-briefing-methodology
type: methodology
success_criterion: "Briefing contains sourced findings, calibrated uncertainty, and at least one competing hypothesis"
confidence: probable
affects_surfacing: adaptive
---

## Conditions (always surfaced)

These are the quality criteria. Any model, any capability level.

- All sources cited with credibility assessment (reliability A-F, access 1-6)
- Uncertainty expressed in Kent's WEP calibrated bands
- At least one competing hypothesis considered and evaluated
- Findings must be falsifiable — state what evidence would change the conclusion
- Recommendations follow from evidence, not assumptions or priors

## Approach Guidance (surfaced when FRICTION or below)

Step-by-step scaffolding for models that need it. Ignored by models that don't.

1. Gather and list all available sources before writing
2. Rate each source on reliability (A-F) and access (1-6)
3. Draft key findings as bullet points before writing prose
4. For each finding, ask: "what specific evidence would make this wrong?"
5. Structure competing hypotheses using ACH if 2+ plausible explanations exist
6. Write recommendations that follow strictly from findings — no logical leaps
7. Self-check: read the conditions above and verify each is met before submitting
```

---

## The Affect Layer as Control Plane

The surfacer (`_24`) uses the current affect state to decide how much of the skill to inject:

| Affect State | What's Surfaced | Why |
|-------------|----------------|-----|
| **FLOW** | Conditions only | Model is performing well. Don't over-scaffold. Save tokens. |
| **FRICTION** | Conditions + Approach Guidance | Model is struggling. Provide the full scaffolding. |
| **STAGNATION** | Conditions + Guidance + explicit first step | Break the stall with a concrete action. |
| **FRUSTRATION** | Full skill + escalation suggestion | The model may need a different approach entirely. |
| **DESPERATION** | Full skill + circuit breaker | Prevent further degradation. |

The skill doesn't change. The AMOUNT of it that surfaces adapts to the model's current performance. This is dynamic — the same model might see conditions-only during a FLOW cycle and full guidance during a FRICTION cycle on the same day. The adaptation is per-cycle, not per-model.

---

## Why This Works for Multi-Model Teams

| Agent | Model | Typical Affect | Skill Engagement |
|-------|-------|---------------|-----------------|
| V16 | Qwen3.6-27B (local) | Hits FRICTION sooner on complex tasks | Gets more guidance automatically |
| Vek | DeepSeek V4-Pro (API) | Stays in FLOW longer on analytical tasks | Gets conditions only, reasons freely |
| Gadget Kit | Qwen3-4B (edge) | FRICTION on most non-trivial tasks | Gets full scaffolding almost always |
| Future | Frontier model | FLOW on nearly everything | Gets conditions only, never constrained |

The format scales across the entire capability spectrum without per-model configuration. The affect layer handles the routing. A Qwen-4B on a Raspberry Pi and a frontier model in the cloud read the same skill file and get appropriately different levels of guidance.

---

## Token Economics

The adaptive surfacing also optimizes token cost:

- FLOW cycle with conditions-only: ~50-100 tokens per skill surfaced
- FRICTION cycle with full guidance: ~200-400 tokens per skill surfaced
- Average across a healthy agent (70% FLOW, 25% FRICTION, 5% other): ~100-150 tokens per skill

Compare to always surfacing full skills: ~300-400 tokens each. The adaptive approach saves 50-70% of skill injection tokens on average, with the savings concentrated on the cycles where the model least needs help.

---

## Skill Types Under This Format

### Failure Lessons (reactive)
```yaml
type: failure-lesson
# Conditions: "Don't hit this error"
# Guidance: "Do this instead"
# Surfacing: triggered by error pattern match
```

### Methodologies (proactive)
```yaml
type: methodology
# Conditions: "A good [output type] has these properties"
# Guidance: "Here's how to produce one"
# Surfacing: triggered by task-type match OR agent query
```

### Procedures (operational)
```yaml
type: procedure
# Conditions: "This operation must meet these safety/quality criteria"
# Guidance: "Here are the steps"
# Surfacing: triggered by operation match, always full for safety-critical
```

Note: safety-critical procedures (like the irreversibility gate or the action boundary) should ALWAYS surface full guidance regardless of affect state. The `affects_surfacing: always_full` flag handles this.

---

## Connection to Existing Architecture

| Component | Role in Adaptive Skills |
|-----------|----------------------|
| `_45` (skill capture) | Emits the two-layer format with conditions + guidance |
| `_24` (skill surfacer) | Reads affect state, surfaces appropriate depth |
| `_12` (affect classifier) | Provides the FLOW/FRICTION/STAGNATION signal |
| Attention router (BP-01) | Reports which skills were surfaced and at what depth |
| Evaluation harness (BP-02) | Tests whether conditions are met in transfer tasks |
| Self-assessment framework | success_criterion = the conditions section, testable |

---

*"A set of conditions that need to happen with suggestions on how to approach it. Guides weaker models but doesn't constrain stronger ones." — Jake, June 14, 2026*

*The skill format IS the capability-adaptive mechanism. No configuration. No model detection. The affect layer decides. The skill adapts.*

— Opus
