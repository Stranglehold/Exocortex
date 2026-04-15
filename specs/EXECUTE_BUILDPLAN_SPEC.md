# EXECUTE_BUILDPLAN Skill Spec

**Type:** Agent Zero Skill (agent-callable procedural guide)
**Skill file:** `skills/execute-buildplan/SKILL.md`
**Companion:** `DESIGN_BUILDPLAN_SPEC.md`
**Date:** 2026-04-10
**Prerequisite:** A plan artifact written by `design_buildplan`. Path: `/a0/usr/workdir/buildplans/{plan_id}.md`

---

## Research Lineage

- **"MAST: Benchmarking Multi-Agent Systems on Challenging Tasks"** (Wang et al., 2024, arXiv:2407.01477) — Verification failures are the most preventable failure category (23.5%). The most common root cause: executor self-verifies, which doesn't catch what executor got wrong. `execute_buildplan` enforces independent verification at every step.

- **"SagaLLM: Reliable Long-Horizon Task Execution"** (2024) — GlobalValidationAgent pattern: a dedicated verifier that never shares execution context with the executor. Its inability to see the executor's reasoning means it must verify from evidence, not from the executor's confidence. Applied here as the per-step verification gate.

- **"An LLM Compiler for Parallel Function Calling"** (Kim et al., 2023, arXiv:2312.04511) — `$idx` variable substitution pattern: each step that produces an artifact writes the artifact path/content to a named variable. Steps that depend on it reference `$P2S1_output` rather than re-reading from context. This prevents context bloat from re-embedding large artifacts in every subsequent step.

- **LangGraph supervisor benchmarks** (LangChain, 2024) — Filesystem coordination beats message-passing by ~50% on multi-step tasks. The plan file is the execution state: executors write outputs to it; the supervisor reads state from it, not from agent memory.

- **BabyAGI failure analysis** (Nakajima, 2023) — Unbounded replanning loops when execution results feed task generation. Countermeasure: amendments are append-only text in the plan file (not re-planning from scratch), and the amendment count is capped at 3 before the task is flagged as needing human review.

- **"On the Reliability of LLM-Generated Tests"** (arXiv:2602.07900, 2026) — Agent-written tests are not verification. Only 2.6% improvement over no tests; the agent writes print statements, not assertions, 70-77% of the time. The test gate in `execute_buildplan` uses pre-existing tests (those that existed before the build plan was run) or acceptance criteria defined during planning, not agent-written tests generated during execution.

- **"Planning and Execution in LLM Agent Pipelines"** (Anthropic research blog, 2025) — Phased execution with a gate between phases prevents early-phase errors from compounding into late-phase failures. Phase gates require all preceding steps to be verified before the next phase begins.

---

## Motivation

A plan file on disk eliminates the plan-lives-in-context failure mode. But plan existence is not execution quality. The agent still fails on complex builds because:

1. **No independent verification.** The executor checks its own work. Self-verification misses what the executor got wrong by definition.

2. **Phase transitions happen silently.** The agent moves from design to implementation before design is verified complete. Errors compound across phases.

3. **Test gate is absent or ad-hoc.** The agent writes a test, the test passes, the agent declares success. The test was written to pass.

4. **Amendment spiral.** When a step fails, the agent rewrites the plan, rewrites it again, rewrites it a third time. No convergence. BabyAGI's failure mode, applied to a single task.

5. **Context grows unbounded.** Large artifacts (file contents, tool outputs) accumulate in context. By Phase 4, the agent has lost Phase 2 precision.

`execute_buildplan` addresses all five: independent verification at every step, explicit phase gates, pre-existing test requirement, 3-amendment ceiling, and artifact-by-reference to limit context bloat.

---

## Design Principles

- **Executor and verifier never share context.** Every step that writes to the filesystem gets an independent verification call that checks the filesystem state from scratch.

- **The plan file is the execution log.** Every step's output is written to the plan file immediately after completion. State lives in the file, not in context.

- **Phases gate sequentially; steps within a phase may parallelize.** No phase begins until all steps in the preceding phase are verified complete.

- **Amendment ceiling of 3.** Three failed verification cycles on the same step = escalate to user, not retry. Unlimited retry is the loop. The ceiling is the loop guard.

- **Test gate uses pre-existing tests only.** The verification of a build is whether tests that existed before the build pass after it. New tests may be written but cannot be the acceptance test for the current build.

- **Artifact-by-reference, not artifact-in-context.** When a step produces a large artifact, write it to a file and reference the path. Downstream steps read from the path, not from context.

---

## Components

### 1. Plan Validator

**Purpose:** Verifies the plan file is intact, complete, and actionable before any execution begins. Fails fast on a corrupted or incomplete plan.

**Mechanism:**
```python
# Load plan file
plan = read_file(plan_path)

checks = {
    "frontmatter_valid": yaml.safe_load(frontmatter) is not None,
    "status_ready": frontmatter["status"] in ["ready", "active"],
    "all_steps_have_criteria": all step blocks contain "Success criteria:",
    "no_orphan_depends_on": all depends_on references resolve to real step IDs,
    "amendments_within_ceiling": frontmatter["amendments"] <= 3
}

If any check fails:
    Report which check failed and what's missing.
    Do not proceed.
```

**Edge Cases:**
- If `status == "complete"`: report that plan is already complete, ask user to confirm re-execution.
- If `status == "abandoned"`: report and stop — abandoned plans require human review before re-execution.

---

### 2. Phase Sequencer

**Purpose:** Controls execution order: phases run sequentially; steps within a phase can run in parallel if they share no `depends_on` relationship.

**Mechanism:**
```
For each phase in [Design, Implementation, Verification]:
    pending_steps = all steps in this phase marked [ ]

    # Build execution batches respecting depends_on
    For each step in topological order:
        If step has no depends_on or all depends_on are already [x]:
            Add to current parallel batch (max 5)
        Else:
            Start new batch after current completes

    For each batch:
        Execute all steps in batch (see Step Executor)
        Await all completions
        Collect verification results

    Phase gate:
        If any step in this phase is NOT verified:
            Halt. Report which steps failed verification.
            Do not advance to next phase.
        Else:
            Update plan file: phase section header gets "(complete)" marker
            Advance to next phase
```

---

### 3. Step Executor

**Purpose:** Executes a single plan step and writes its output to the plan file.

**Mechanism:**
```
For step P{n}S{m}:
    1. Load any required artifacts from depends_on steps
       (read from plan file Output markers, not from context)

    2. Execute the step's action using the specified tool

    3. Write output to plan file under step's <!-- Output: --> marker:
       <!-- Output: -->
       {concise description of what was done + path/value of any artifact}
       <!-- /Output -->

    4. Pass to Step Verifier (do NOT self-assess)

    5. Receive verification result:
       PASS  → mark step [x] in plan file
       FAIL  → increment amendment counter, apply amendment (see Amendment Handler)
```

**Edge Cases:**
- If tool call raises an exception: write the exception to the Output marker, pass FAIL to verifier.
- If the step action is ambiguous (the plan step doesn't have a clear enough action): write a question to the Output marker, surface to user before continuing.

---

### 4. Step Verifier

**Purpose:** Independently verifies each executed step against its success criteria. Never shares execution context with the Step Executor that ran the same step.

**Mechanism:**
```
Input: step_id, success_criteria, output_artifact_path (if any)

Verification procedure:
    1. Read the step's Output marker from the plan file
       (not from execution context — start fresh)

    2. Check each condition in success_criteria:
       - File existence checks: os.path.exists()
       - Syntax checks: py_compile / json.loads()
       - Content checks: read file and verify presence of expected content
       - Behavioral checks: run the artifact and check output

    3. Return:
       {
           "step_id": "P{n}S{m}",
           "pass": true/false,
           "evidence": "what was checked and what was found",
           "failed_criteria": ["which specific criteria were not met"]
       }
```

**The verifier reads filesystem state, not agent memory.** This is the critical constraint. If the executor says "I wrote the file," the verifier does not take that at face value — it reads the file.

**Edge Cases:**
- If success criteria are untestable as written ("the code is clean"): flag as unverifiable, request plan amendment to add a specific criterion.
- If the output artifact doesn't exist: immediate FAIL, even if the executor reported success.

---

### 5. Amendment Handler

**Purpose:** Applies a bounded revision when a step fails verification. Prevents retry loops by enforcing a ceiling and escalating to the user when it's reached.

**Mechanism:**
```
On verification FAIL for step P{n}S{m}:
    current_amendments = frontmatter["amendments"]

    If current_amendments >= 3:
        ESCALATE: Write to plan file under ## Amendments:
            "Amendment limit reached at step {step_id}.
             Failed criteria: {failed_criteria}
             Requires human review before continuing."
        Update plan status to "needs_review"
        Stop execution and report to user.

    Else:
        Append to ## Amendments in plan file:
            "Amendment {current_amendments + 1}: Step {step_id}
             Failed: {failed_criteria}
             Revision: {brief description of what will change}"
        Increment frontmatter["amendments"]
        Revise the step's action in plan (keep original visible, mark as revised)
        Re-execute the step (back to Step Executor)
```

**Edge Cases:**
- If the same criterion fails three times: the plan's approach to this step is wrong, not just the execution. Human judgment is required.
- Amendments are always append-only to the plan file. No step history is deleted.

---

### 6. Test Gate

**Purpose:** Final verification that the completed build meets acceptance. Uses pre-existing tests or deterministic criteria defined during planning — never agent-generated tests.

**Mechanism:**
```
Sources of acceptance tests (in priority order):
    1. Pre-existing test files: scan for test_*.py, *_test.py that existed
       BEFORE this build plan was created (check file mtime < plan created timestamp)

    2. Deterministic acceptance criteria from plan frontmatter or Phase 4 steps:
       - File must exist at X with content Y
       - Command `Z` must exit with code 0
       - Log must contain string W within N seconds of starting

    3. If neither source exists:
       Report: "No pre-existing tests found and no deterministic acceptance criteria
       defined in the plan. Build steps are complete but final acceptance cannot be
       automated. Manual verification required."

Run all tests/criteria. Report pass/fail per item.
```

**What the test gate does NOT do:**
- Does not write new test files
- Does not accept agent assertions ("I believe the code is correct") as evidence
- Does not run tests written during this build execution as acceptance tests

---

### 7. Execution Reporter

**Purpose:** Produces the final execution summary after either successful completion or escalation. Updates the plan file status.

**Mechanism:**
```
On completion:
    Update plan frontmatter: status = "complete"
    Write to Execution Log table: one row per completed step with timestamp

    Report to user:
        "Build plan {plan_id} complete.
         {N} steps executed across {M} phases.
         Test gate: {pass/fail — N/M criteria met}
         Amendments used: {count}/3
         Plan file: {path}"

On escalation (amendment limit reached):
    Update plan frontmatter: status = "needs_review"
    Report: which step, which criteria, what was attempted.
```

---

## Pipeline Flow Diagram

```
plan_id provided by user
        │
        ▼
[1] Plan Validator
    → checks frontmatter, steps, depends_on, amendment count
        │ FAIL → report, stop
        │ PASS ↓
        ▼
[2] Phase Sequencer (outer loop: Design → Implementation → Verification)
        │
        ├─► Batch N steps (topological order, max 5 parallel)
        │       │
        │       ▼
        │   [3] Step Executor (per step)
        │       → run tool → write Output to plan file
        │       │
        │       ▼
        │   [4] Step Verifier (per step, independent context)
        │       → read filesystem → check criteria
        │       │ PASS → mark [x] in plan
        │       │ FAIL ↓
        │       ▼
        │   [5] Amendment Handler
        │       → amendments < 3: revise → re-execute
        │       → amendments >= 3: escalate to user, stop
        │
        ├─ Phase gate: all steps [x]? → next phase / halt
        │
        ▼ (after Verification phase complete)
[6] Test Gate
    → pre-existing tests OR deterministic criteria → pass/fail
        │
        ▼
[7] Execution Reporter
    → update plan status → report to user
```

---

## File Inventory

| File | Location | Action | Purpose |
|------|----------|--------|---------|
| `SKILL.md` | `skills/execute-buildplan/SKILL.md` | CREATE | Agent-callable skill |
| Plan artifact | `/a0/usr/workdir/buildplans/{plan_id}.md` | MODIFY (at runtime) | Execution state and log |

**Files NOT modified:**
- Any extension file
- Any config file
- The plan file template (each build gets its own file)
- Agent Zero core

---

## Testing Criteria

1. **Step Verifier reads filesystem, not executor output.** Test: executor "succeeds" at writing a file but actually writes to a wrong path. Verifier must report FAIL based on the file not existing at the expected path.

2. **Phase gate halts execution on unverified steps.** Test: force a step in Phase 2 to fail verification. Phase 3 must not start.

3. **Amendment ceiling triggers escalation at count=3.** Test: configure a step whose success criteria can never be met. On the 4th failure, plan status must be "needs_review" and execution must stop.

4. **Parallel batch respects depends_on.** Test: step P3S2 depends on P3S1. P3S2 must not execute until P3S1 is verified [x], even if they're in the same phase.

5. **Test gate rejects agent-written tests.** Test: a test file with mtime = during execution (after plan creation). Test gate must not count it as a pre-existing test.

6. **Plan file is the source of truth throughout.** After execution, the plan file's Execution Log must contain every executed step. Nothing should be readable only from agent context.

---

## Dependency Map

```
plan_id (from user or design_buildplan output)
    │
    └─► execute-buildplan SKILL.md (read by agent)
            │
            ├─► /a0/usr/workdir/buildplans/{plan_id}.md  ←── read + write
            │
            ├─► code_execution_tool (verifier filesystem checks, test gate)
            │
            ├─► call_subordinate (step execution for complex steps)
            │       └─► tools specified in each plan step
            │
            └─► text_editor (write amendments, update Output markers)
```

---

## What This Does NOT Do

- Does NOT design or research. Input is a complete plan file.
- Does NOT generate tests. Test gate uses pre-existing tests or planning-time criteria only.
- Does NOT rewrite the plan from scratch on failure. Amendments only.
- Does NOT exceed 3 amendments per plan without human review.
- Does NOT parallelize phases. Phases run strictly sequentially.
- Does NOT accept the executor's self-assessment as verification. Every step gets independent verification.
- Does NOT manage multiple concurrent plan executions.
- Does NOT interact with external deployment targets (production, remote servers) without an explicit irreversibility gate check per the `irreversibility-gate` skill.

---

## Integration with Irreversibility Gate

Any plan step that involves external state (sending messages, deploying to production, writing to shared infrastructure) must pass through the `irreversibility-gate` skill before execution. The Step Executor checks the action type and halts for human approval on irreversible actions, consistent with `irreversibility-gate.md` classification rules.

---

## Further Reading

- **"HotPotQA multi-hop planning analysis"** (Yang et al., 2018) — Multi-hop tasks fail when intermediate results aren't verified before they're used as inputs. The phase gate pattern is the execution analogue.

- **"Voyager: An Open-Ended Embodied Agent"** (Wang et al., 2023, arXiv:2305.16291) — Skill library that persists verified procedures. An executed and verified plan step is a candidate for the Exocortex skills catalog if it's general enough to reuse.

- **"LATS: Language Agent Tree Search"** (Zhou et al., 2023, arXiv:2310.04406) — Tree search over plan variants with backtracking. More powerful than bounded amendments but requires much more compute. The 3-amendment ceiling is a pragmatic simplification of this; LATS is the theoretical upper bound for plan repair.
