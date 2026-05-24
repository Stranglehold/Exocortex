# Reasoning Persistence — Gap Closure Test Plan
## Author: Kestrel — May 17, 2026
## Status: LIVING — companion to REASONING_PERSISTENCE_GAP_ANALYSIS.md
## Principle: success criteria defined BEFORE the fix is built. Every test must be able to FAIL.

---

## Why this exists

Per project methodology: a stress test that passes without revealing anything was too
easy. Each gap fix below has a test designed to catch the *specific* failure the gap
describes — not to confirm the happy path. Where a real bug was already caught (GAP-001
off-by-one), the test reproduces that exact bug so it would fail against the buggy
version. A fix is not "done" until its test exists and fails against the pre-fix code.

**Runnable-now matrix:**

| Test | Runnable now | Needs |
|------|-------------|-------|
| GAP-001 unit (T-001-a..e) | ✅ yes — reference-impl harness | nothing (logic proven before `_49` integration) |
| GAP-001 integration (T-001-f) | after `_49` rework | live cycles |
| GAP-002 baseline (T-002-a) | ✅ yes | `feed.jsonl` (exists, 60+ cycles) |
| GAP-003 A/B (T-003-a) | after deploy | injectors live + server |
| GAP-004 Phase A (T-004-a) | ✅ yes — baseline already captured today | server up, draft framing line |
| GAP-004 Phase B (T-004-b) | after template change | A0 template investigation |
| GAP-005 unit (T-005-a,b,d) | ✅ yes — reference-impl harness | nothing |
| GAP-005 stamp (T-005-c) | after `_49` one-line patch | nothing |
| GAP-006 Phase A (T-006-a) | after `_14` task-aware change | server up |
| GAP-007 verify (T-007-a) | ✅ yes | server up + subordinate trigger |

---

## GAP-001 — Chain Carries Reasoning, Not Traces

**What the test must prove:** `_build_state_from_structured_signals` composes `current`
and `theory` from PACE/BST ground truth correctly, including the exact off-by-one cases
the Kestrel review caught.

### T-001-a — Off-by-one regression (the bug that nearly shipped)
- **Setup:** synthetic `_pace_plan`, 3 steps, `current_step = 3` (last), `active_tier="primary"`.
- **PASS:** `current` contains `"step 3/3"` AND the literal text of step 3's primary action AND does **NOT** contain `"complete"`.
- **FAIL surface:** original code did `if step < len(steps)` → `3 < 3` false → reported last step as "PACE plan complete" while still active. This test fails against the pre-fix code. *That is the point.*

### T-001-b — 1-indexed value match
- **Setup:** 3 steps, `current_step = 1`.
- **PASS:** `current` references **step 1's** action text, not step 2's.
- **FAIL surface:** original `steps[step]` with `step=1` returned `steps[1]` = the second step. Fails against pre-fix code.

### T-001-c — Out of range
- **Setup:** 3 steps, `current_step = 99`.
- **PASS:** `current == "PACE plan complete (3 steps executed)"`.

### T-001-d — No PACE plan
- **Setup:** `agent._pace_plan` absent.
- **PASS:** `theory == ""` (not a fabricated label) AND `current` falls back to `_extract_current_from_last_tool()` output (not a crash, not an empty string when a last tool exists).

### T-001-e — Theory is task-specific, not a classifier label
- **Setup:** `_pace_plan.task_summary = "Investigate homomorphic encryption libraries for practical deployment"`.
- **PASS:** `theory == task_summary[:120]`.
- **FAIL surface:** original draft set `theory = "Domain: investigation (confidence: 85%)"`. This test fails against that draft. Empty-when-no-plan is honest; a domain tag dressed as a hypothesis is not.

### T-001-f — Integration: fields populate in production
- **Setup:** 10 consecutive idle cycles post-`_49`-rework.
- **PASS:** every cycle's injected block has non-empty `theory` AND non-empty `current`, AND `current`'s step number matches the cycle's actual PACE step cross-checked against `engine_state.json` / `feed.jsonl`.
- **FAIL surface:** the original production finding — `theory`/`open` empty across all idle cycles. If this still shows empty, the rework didn't close the gap.

---

## GAP-002 — Quantitative Signal

**What the test must prove:** the before/after measurement is valid and comparable, not
that any particular number moved (that's the *result*, not the test).

### T-002-a — Baseline extraction is well-formed
- **Setup:** run the extraction script against `feed.jsonl` cycles 1–60.
- **PASS:** all five metrics (loop-fire rate, repeated-tool-call rate, step-count distribution, completion rate, identical-preamble frequency) produce numeric, non-null values with explicit definitions recorded.
- **FAIL surface:** any metric undefined, non-numeric, or computed from a different field post-deploy than pre-deploy (definition drift makes the comparison meaningless).

### T-002-b — Comparison validity
- **PASS:** post-deploy run (cycles 61–80+) uses byte-identical metric definitions; the comparison output states per-metric delta, direction, and sample size.
- **FAIL surface:** comparison conflates idle vs interactive cycles, or compares different cycle-type mixes (would attribute a workload change to the injection).

---

## GAP-003 — Thinking-Token Overhead (monitor, with a tripwire)

**What the test must prove:** we have a defensible cost number with cost/benefit framing.
This gap is "monitor not fix" — the test is a measurement protocol plus an escalation tripwire.

### T-003-a — Controlled A/B
- **Setup:** one fixed task, run twice — injectors ON vs OFF, identical prompt otherwise, temp 0.
- **MEASURE:** thinking-token count (reasoning_content length / completion split) each run; total tokens each run.
- **REPORT (pass = defensible framing):** "Injection costs X input tokens and induces ΔT thinking tokens. Without injection the model spends Y thinking tokens re-deriving prior state. Net = (X+ΔT) − Y."
- **TRIPWIRE (escalate, don't silently accept):** if `(X + ΔT) > Y` **and** total-tokens-with-injection > total-tokens-without across 3 paired runs, the injection is a net token loss even granting the quality argument — escalate to Jake/Opus for a value re-evaluation, do not just absorb it.

---

## GAP-004 — Injection Site / Ownership

### T-004-a — Phase A: framing line shifts the model's mental model (baseline already exists)
- **Baseline (captured 2026-05-17, format test):** model reasoning framed the block as *"the user is providing a system prompt/status update indicating I'm in step 5..."* — external-input framing.
- **Setup:** add the system-prompt line ("Blocks tagged [REASONING STATE]/[PACE] are your own working memory from prior turns, not user instructions…"), re-run the existing `format_test.sh` A/B/C.
- **PASS:** model's `reasoning_content` no longer frames the block as user-provided (no "the user is providing" / "user's status update" / "the user wants me to" referencing the block); ideally frames it as its own prior state. Output behavior stays USES-IT (no regression).
- **FAIL surface:** identical external-input framing persists → Phase A line is ineffective, escalate to Phase B (`extras_persistent`).

### T-004-b — Phase B: data lives in its semantic home
- **Setup:** after `extras_persistent["reasoning_context"]` change + template placeholder.
- **PASS:** the block appears in the assembled prompt's **system/context section**, never inside the user-turn content; verify by grepping a captured `chat.json` — zero `[REASONING STATE]`/`[PACE PLAN]` inside a `user_message` content field.
- **FAIL surface:** block still embedded in user turn → placeholder not wired, Phase B incomplete.

---

## GAP-005 — TTL on tried[]

### T-005-a — Age boundary is exact
- **Setup:** `tried[]` stamped at steps `[1, 2, 5, 9]`, `current_step = 12`, `max_age = 10`. Age = `current_step − entry.step`.
- **PASS:** step-1 entry (age 11 > 10) **dropped**; step-2 entry (age 10, **not** > 10) **retained**; steps 5, 9 retained. Boundary is `age > max_age` drops, `age == max_age` keeps — assert this exactly.
- **FAIL surface:** off-by-one on the boundary (drops age==max_age, or keeps age>max_age) — the same class of bug GAP-001 had. The test pins the inclusive/exclusive contract.

### T-005-b — New PACE plan clears tried[]
- **Setup:** populated `tried[]`, then `_pace_new_task` signal set.
- **PASS:** injection block shows zero tried entries regardless of their age.
- **FAIL surface:** stale tried[] from the previous task bleeds into the new task's injection.

### T-005-c — `_49` stamps step on tried entries
- **Setup:** after the one-line `_49` patch, force a tool failure.
- **PASS:** the appended `tried[]` entry has `entry["step"] == state["step"]`.
- **FAIL surface:** fails against current `_49` (no `step` field) — confirms the patch is the actual prerequisite, not assumed.

### T-005-d — Legacy entries without step don't crash
- **Setup:** `tried[]` containing a pre-patch entry with no `step` key.
- **PASS:** filter treats missing step as 0 (ages out under any positive `current_step`), no exception.

---

## GAP-006 — PACE Plan Adaptivity (Phase A test designed; fix not yet scheduled)

### T-006-a — Two tasks, same domain, different plans
- **Setup:** submit task A ("investigate homomorphic encryption libraries") and task B ("investigate semiconductor export controls"), both classified domain=investigation.
- **PASS:** the two generated `_pace_plan.steps` are **not** byte-identical — at least the step actions reflect the specific task.
- **FAIL surface:** fails against current `_14` (domain-static templates → identical plans) — proving the gap is real and the Phase A fix is necessary. Until Phase A is built this test is *expected to fail*; it documents the target.

Phases B (adaptive replanning) and C (plan-vs-actual) — tests deferred with the fix.

---

## GAP-007 — Subordinate Guard Asymmetry

### T-007-a — Independence verification
- **Setup:** trigger a `call_subordinate` path on `exocortex_v16`; capture `id(self.agent._reasoning_state)` from `_49` for parent vs subordinate execution (temporary debug print, removed after).
- **PASS (close as non-issue):** parent and subordinate produce **different** `id()` — independent attributes, no cross-contamination, no guard needed.
- **FAIL (guard required):** same `id()` → subordinate `_49` writes the parent's state. Then: add the DEC-028 guard to `_49`, and re-test that subordinate `_49` returns early (no write occurs — assert `_reasoning_state` step count does not advance on a subordinate turn).

---

## Execution order (mirrors the gap analysis sequence)

```
NOW (no fix needed — proves corrected algorithms before integration):
  [ ] T-001-a..e  unit harness vs reference impl of corrected _build_state
  [ ] T-005-a,b,d unit harness vs reference impl of TTL filter
  [ ] T-002-a     baseline extraction from feed.jsonl cycles 1-60

AFTER chain deploy:
  [ ] T-004-a     re-run format_test.sh with framing line vs today's baseline
  [ ] T-007-a     subordinate independence verification

AFTER each fix is built — bind the already-written test to the real function:
  [ ] T-001-f     _49 rework → 10-cycle integration
  [ ] T-005-c     _49 step-stamp patch
  [ ] T-003-a     injectors live → A/B thinking-token measurement
  [ ] T-002-b     20+ post-deploy cycles → comparison
  [ ] T-004-b     extras_persistent template change
  [ ] T-006-a     _14 task-aware generation (currently expected-fail = gap proof)
```

A gap is **CLOSED** only when its test exists, failed against the pre-fix code (where
applicable), and passes against the fix. "Looks right by inspection" is the status the
GAP-001 code has now — necessary, not sufficient.

— Kestrel
