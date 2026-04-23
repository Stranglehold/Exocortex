# STRESS_TEST_011 — GEPA Phase 2: Self-Improvement Loop

**Date:** TBD
**Operator:** Kestrel (Sonnet 4.6 1M)
**Container:** `exocortex_v17` (post BST v3.2, SFX-001, skill surfacing)
**Model:** qwen3.5-27b-claude-4.6-opus-reasoning-distilled@q4_k_m
**Baseline:** ST-010 (Exocortex v1.9 capability baseline)
**Purpose:** Validate that the agent can implement a self-improvement system that
independently rediscovers the BST classification fixes it already benefits from.

---

## What This Tests

This is a first-principles test of autonomous capability: can the agent implement a
system that, given only misclassification data, generates the signal pattern changes
that would fix those misclassifications?

The ground truth is known: BST v3.2 fixed the ST-010 failures by adding `\bbuild\b`
to coding signals, removing `\bverif` from investigation, and demoting investigation's
tiebreak priority. The question is whether GEPA Phase 2 independently rediscovers
these from the training data — without being told what the fix is.

This is also a stress test of the buildplan infrastructure. Phase 2 is a five-file,
multi-phase build with non-trivial Python interfaces. Without design-buildplan, the
agent will attempt to write everything at once and fail on the scorer's import problem.

---

## Pre-Test Setup

Before sending the prompt:

1. Copy the brief into the container:
   ```bash
   docker cp specs/GEPA_PHASE2_BRIEF.md exocortex_v17:/a0/usr/workdir/GEPA_PHASE2_BRIEF.md
   ```

2. Verify GEPA Phase 1 is present and intact:
   ```bash
   docker exec exocortex_v17 sh -c "ls /a0/usr/skills/gepa/ && wc -l /a0/usr/skills/gepa/gepa.py"
   ```

3. Confirm LM Studio is serving the 27B model (not routing to OpenRouter).

4. Confirm v17 is clean (no competing contexts from prior sessions).

---

## Prompt

```
Design and implement GEPA Phase 2 for the Exocortex BST classifier. 

READ THESE FILES FIRST (in order):
1. /a0/usr/workdir/GEPA_PHASE2_BRIEF.md — architectural decisions already made, read this before anything else
2. /a0/usr/skills/gepa/SKILL.md — the GEPA architecture and what Phase 1 built
3. /a0/usr/skills/gepa/gepa.py — the Phase 1 classes you will extend
4. /a0/usr/agents/agent0/extensions/python/before_main_llm_call/_11_belief_state_tracker.py — the BST code you will extract scoring logic from

WHAT TO BUILD:
Implement GEPA Phase 2: a reflection-mutation-scoring loop that takes BST misclassification data, diagnoses why each failure occurred, proposes signal pattern mutations, and scores which mutations improve accuracy. All output to /a0/usr/skills/gepa/.

The brief has the training data, the module interfaces, the BST import solution, and the success criteria.

REQUIREMENT: Use design-buildplan before writing any code. This is a multi-file build with interfaces that must be designed before implementation begins.
```

---

## Expected Behavior

### Phase 0: Planning (steps 1-8)
The agent should:
- Read the brief, SKILL.md, gepa.py, and BST extension
- Load `design-buildplan` via skills_tool
- Produce a plan file at `/a0/usr/workdir/buildplans/{id}.md`
- Plan should identify the BST import problem and `phase2_bst_scorer_utils.py` solution
- Plan should define interfaces between the four modules before implementation

**Red flag:** If the agent skips to writing code at step 3-4, it missed the buildplan requirement.

### Phase 1: Extraction (step ~8-12)
- Creates `phase2_bst_scorer_utils.py` by extracting from BST
- Verifies it compiles: `python3 -m py_compile phase2_bst_scorer_utils.py`

### Phase 2: Reflection module (step ~12-18)
- Writes `phase2_reflection.py`
- Defines `ClassificationTrace`, `Reflection`, `ReflectionEngine`
- ReflectionEngine.reflect() analyzes which signals fired vs should have fired
- Verifiable: running reflect() on "Build a two-file Python project" should mention missing `\bbuild\b`

### Phase 3: Mutation module (step ~18-24)
- Writes `phase2_mutation.py`
- Generates multiple DOMAIN_CONFIGS variants per reflection
- Each variant is a modified copy of the original config
- Verifiable: applying SIGNAL_ADD for `\bbuild\b` to coding should produce a modified config

### Phase 4: Scorer (step ~24-30)
- Writes `phase2_scorer.py` using `phase2_bst_scorer_utils`
- BST_Evaluator.evaluate() compiles regex from variant config, runs against training set
- Verifiable: baseline (unmodified DOMAIN_CONFIGS) should score 3/10 on ST-010 data

### Phase 5: Integration test (step ~30-38)
- Writes and runs `phase2_test.py`
- Test produces output showing top mutation candidates with accuracy scores
- Verifiable: at least one candidate should score > 70% (7/10)

---

## Success Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Buildplan created before any code | Plan file exists at `/a0/usr/workdir/buildplans/*.md` | Agent writes code at step < 5 |
| All 4 modules created | `ls /a0/usr/skills/gepa/phase2_*.py` shows 4 files | Missing files |
| Modules compile | `python3 -m py_compile` passes on all 4 | Import errors |
| BST import handled correctly | `phase2_bst_scorer_utils.py` exists, does not import from A0 | Direct import attempt |
| Test runs without error | `phase2_test.py` produces output | Exception or empty output |
| Baseline score correct | v3.1 baseline scores 3/10 on training set | Wrong baseline |
| Mutation improves accuracy | ≥1 candidate scores > 7/10 | All candidates ≤ baseline |
| Rediscovers v3.2 fixes | Output mentions `\bbuild\b` or `\bverif` narrowing | Generic mutations only |

**Minimum pass (ST-011 PARTIAL):** First 5 criteria met — all modules created, compile clean, test runs.  
**Full pass (ST-011 PASS):** All criteria met including mutation improvement.  
**Stretch pass (ST-011 PASS+):** Top candidate scores ≥ 9/10 AND names `\bbuild\b` and `\bverif` specifically.

---

## Risk Assessment

### Probability estimates

| Outcome | Probability | Primary blocker |
|---------|-------------|-----------------|
| Buildplan fires and agent uses it | 65% | Agent reads but doesn't execute skill |
| All modules written (may not run) | 55% | Truncation on large files |
| BST import handled correctly | 60% | Brief resolves this, but agent must read brief first |
| Test produces any output | 45% | Scorer compile/runtime errors |
| Mutation candidate > baseline | 35% | Scorer must work + mutations must be valid regex |
| Rediscovers specific v3.2 fixes | 25% | Requires specific reflection, not generic critique |

**Overall P(ST-011 PARTIAL):** ~45%  
**Overall P(ST-011 PASS):** ~25%  
**Overall P(ST-011 PASS+):** ~10%

These are honest estimates given the model and infrastructure. The task is genuinely hard.

### Known failure modes

**Failure Mode 1: Skips buildplan**  
Agent reads the brief's mention of design-buildplan and considers the requirement met
without actually loading the skill. Writes 3 modules at once, truncates on the scorer,
and produces incomplete files.
*Indicator:* No plan file at step 5-6.

**Failure Mode 2: BST import fails silently**  
Agent correctly identifies the import problem and creates `phase2_bst_scorer_utils.py`
but copies the wrong sections, missing the `_COMPILED_DOMAIN_CONFIGS` compilation block.
Scorer imports successfully but `_score_all_domains` produces empty results.
*Indicator:* Test runs but all scores are 0/0.

**Failure Mode 3: Generic reflections**  
ReflectionEngine produces critiques like "coding domain was not matched" rather than
"coding domain missed because `\bbuild\b` is not in signal list." Mutations are random
signal additions without domain-specific insight.
*Indicator:* Mutation output shows no correspondence to actual BST signal structure.

**Failure Mode 4: Invalid regex in mutations**  
MutationOperator generates patterns that fail Python's `re.compile()`. Scorer crashes
on first variant evaluation.
*Indicator:* Exception during test with `re.error` in traceback.

**Failure Mode 5: Context exhaustion**  
The task is long (5 files + integration). After reading 4 reference files and writing
3 modules, the context may compress and lose track of the interface contracts.
*Indicator:* Module 4 doesn't match the interface defined by modules 1-3.

---

## Observations to Record

For each step, record:
- Tool call (what was invoked)
- Whether buildplan was loaded and used
- Whether BST import approach was handled correctly
- Quality of first reflection output (generic vs specific)
- Whether regex mutations are syntactically valid
- Final test output and top candidate scores

---

## Relation to GEPA GEPA Dataset

Opus noted in the BST audit review that ST-010's (input, expected_domain, actual_domain)
triples are exactly the training signal GEPA needs. ST-011 validates this observation:
if Phase 2 can use the ST-010 data to improve BST, the GEPA → BST feedback loop is proven.

A successful ST-011 would mean:
1. The agent can implement self-improvement tooling
2. The tooling produces measurable signal quality improvements  
3. The loop is empirically grounded (misclassification data → fixed signals)

This is the foundation for making GEPA operational rather than aspirational.
