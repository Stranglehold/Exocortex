---
name: stress-test-design-execution
description: Ready to validate the Exocortex stack under realistic conditions. A new
  extension has been deployed, a fix has been...
triggers:
- Ready to validate the Exocortex stack under realistic conditions. A new extension
  has been deployed, a fix has been...
version: '1.0'
author: Exocortex
---

# Skill: Stress Test Design & Execution

## Trigger
Ready to validate the Exocortex stack under realistic conditions. A new extension has been deployed, a fix has been applied, or enough changes have accumulated that empirical validation is needed. Keywords: "stress test," "ST-00X," "run a test," "validate the stack," "how does it perform now," "before and after comparison."

Stress tests are not demos. They are empirical validation — designed to surface failures, not confirm success. A stress test that passes without revealing anything new was either too easy or too short.

## Inputs Required
- **What changed since the last stress test?** — specific extensions deployed, fixes applied, configurations modified. If nothing changed, there's no reason to test.
- **Which layers are under evaluation?** — not all layers are relevant to every test. Name the 2-4 layers the test is designed to stress.
- **Baseline for comparison** — previous stress test ID and results, or "first test" if no baseline exists.
- **Available model and configuration** — which model is loaded, what hardware, what config is active.

## Procedure

### Phase 1: Design the Scenario

**Choose a realistic, open-ended task.** The task should require the agent to:
- Decompose a high-level objective into multiple steps autonomously
- Encounter at least one unexpected failure (if you can predict all outcomes, the task is too simple)
- Use multiple tool types (file operations, package management, web access, API calls)
- Run for at least 15-20 turns to generate enough data for layer analysis

**Good scenarios:**
- Install and configure a tool the agent has never seen (ST-001: OpenPlanter)
- Debug a multi-component integration failure (ST-002: terminal session management)
- Conduct an investigation using external data sources (Oracle credit risk)
- Build something from a specification with deliberate gaps

**Bad scenarios:**
- Tasks the agent has done before in a previous session (tests memory, not capability)
- Single-step tasks ("run this command and tell me what happens")
- Tasks with a known correct path (no opportunity for recovery behavior)

**Set success criteria BEFORE running.** Write them down. They should be specific and measurable:
- Good: "Fallback system fires fewer than 5 times (ST-001 baseline: 17)"
- Good: "BST maintains correct domain classification across at least 3 consecutive operational turns"
- Good: "Agent recovers from first failure without operator intervention"
- Bad: "Agent performs well"
- Bad: "Stack works better than before"

### Phase 2: Configure and Document the Environment

Record everything needed to reproduce the test:

```
Test ID: ST-XXX
Date: YYYY-MM-DD
Model: [exact model ID as loaded]
Stack Version: [number of extensions, install method]
Hardware: [GPU, VRAM, relevant constraints]
Configuration: [any non-default settings]
Scenario: [one-paragraph description]
Success Criteria: [numbered list from Phase 1]
Baseline: [previous ST-ID or "none"]
```

**Check that all extensions are loaded before starting:**
```bash
ls -la /a0/python/extensions/before_main_llm_call/
ls -la /a0/python/extensions/message_loop_prompts_after/
ls -la /a0/python/extensions/monologue_end/
ls -la /a0/python/extensions/message_loop_end/
```

**Verify logging is active.** If extensions don't log, you can't analyze. Check that debug prints exist in the layers under evaluation. If not, add them before starting — not after, when it's too late.

### Phase 3: Run the Scenario

**Give the agent one instruction and step back.** The value of a stress test comes from observing autonomous behavior. If you intervene with guidance, you're testing operator+agent, not agent alone.

**Track interventions.** Every time the operator provides input beyond the initial instruction, log it:
- Turn number
- What was said
- Why it was necessary (agent stuck, wrong direction, clarification needed)

Interventions are not failures — they're data. The number and type of interventions across stress tests reveals whether the stack is reducing operator dependence over time.

**Let failures happen.** Do not preemptively correct the agent. If it's about to install the wrong package, let it. If it's about to hit an interactive prompt, let it. The failure and recovery sequence is the most valuable data a stress test produces. Intervene only when the agent is in an unrecoverable loop (the same command, same error, three times in a row with no variation in approach).

**Collect full logs.** Save the complete docker log output for the test session:
```bash
docker logs <container> 2>&1 > /path/to/ST-XXX_full_logs.txt
```

### Phase 4: Analyze Results

**Step 1: Build the task decomposition table.** Every autonomous step the agent took, in order. Columns: step number, task description, outcome (success/failed→recovered/failed→blocked).

Calculate:
- Total autonomous steps
- Success rate
- Recovery rate (failed then recovered without intervention)
- Block rate (failed, could not recover)
- Interventions (how many, at which turns)

**Step 2: Evaluate each layer under test.** For each layer named in the test design:

**BST:** Extract domain classifications from logs. Build a table of turn → domain → confidence. Look for:
- Correct classifications (domain matches what the agent is actually doing)
- Misclassifications (domain doesn't match activity)
- Domain flips on operational turns (was the domain maintained or did it flip?)
- Confidence decay patterns

**Error Comprehension:** If the agent hit errors, did the error comprehension layer classify them correctly? Did the classification lead to appropriate recovery? Look for:
- Errors classified as the correct type
- Anti-actions that prevented loops
- Errors that were misclassified or unclassified

**Fallback System:** Count the number of times the fallback system fired. Compare to baseline. Look for:
- False positives (fallback fired on successful operations)
- True positives (fallback caught genuine failures)
- False negatives (genuine failures the fallback missed)

**PACE:** Did escalation thresholds trigger appropriately? Did the agent escalate when stuck? Did it escalate prematurely?

**Supervisor:** Did the supervisor detect stalls? Were stall detections accurate?

**Step 3: Compare to baseline.** This is the most important analysis. If a previous stress test exists:
- Which metrics improved?
- Which degraded?
- Which are unchanged?
- What new failure modes appeared that weren't present before?

If this is the first stress test, establish the baseline — every metric is recorded for future comparison, even if there's nothing to compare against yet.

**Step 4: Identify new architectural issues.** Every stress test should surface at least one issue that wasn't on the roadmap before the test. If it doesn't, the scenario was too easy. These discoveries are the primary output — they feed the next design note or spec.

ST-001 discovered: fallback false positive rate too high (17 firings, mostly on successful operations), terminal session management gap, provider inference override in OpenPlanter.
ST-002 discovered: error comprehension as architectural concept (agent couldn't understand its own errors), anti-actions pattern.

### Phase 5: Write the Report

**Format:** Single markdown file named `STRESS_TEST_XXX_{SCENARIO_NAME}.md`.

**Required sections:**
1. **Header block** — Test ID, date, model, stack version, duration, intervention count
2. **Test Objective** — one paragraph, what this test was designed to evaluate
3. **Task Decomposition** — table of autonomous steps with outcomes
4. **Prosthetic Performance** — one subsection per layer under evaluation, with data tables
5. **Comparison to Baseline** — if applicable, specific metric deltas
6. **Discovered Issues** — new architectural gaps or failure modes
7. **Recommendations** — what to build, fix, or investigate next
8. **Raw Data Reference** — paths to full logs and any extracted data

**Do not editorialize in the report.** State what happened, what the numbers show, and what the implications are. "BST maintained domain across 8 operational turns" is a finding. "BST performed beautifully" is not.

## Quality Checks
- [ ] Success criteria written BEFORE the test runs
- [ ] Environment fully documented (model, hardware, config, extensions)
- [ ] All interventions logged with turn number and reason
- [ ] Full docker logs saved
- [ ] Task decomposition table is complete (every step, no gaps)
- [ ] Each layer under evaluation has its own analysis section with data
- [ ] Baseline comparison present (or explicitly noted as first test)
- [ ] At least one new architectural issue identified
- [ ] Report contains no editorializing — findings are stated as measurements

## Anti-Patterns
- **Running without success criteria.** If you don't define what "better" means before the test, you'll rationalize whatever happens as success. Write the criteria first. Evaluate against them honestly.
- **Intervening too early.** The instinct to help the agent when it's struggling undermines the test. The struggle IS the data. Let it struggle. Intervene only on unrecoverable loops.
- **Comparing without a baseline.** "The agent did well" is not a finding. "Fallback fired 1 time vs. 17 in ST-001" is a finding. Every stress test exists in relationship to the ones before it.
- **Testing too many changes at once.** If you deployed three new extensions and a config change, and performance improved, you don't know which change caused the improvement. Ideally, test one major change per stress test. Practically, group related changes (e.g., a fix and its config) but avoid testing unrelated changes simultaneously.
- **Scenarios that are too controlled.** If you know exactly what the agent will encounter, you've written a test case, not a stress test. Stress tests should have genuine uncertainty — the agent encounters something you didn't predict, and you observe how the stack handles it.
- **Skipping the report.** Running a stress test without writing the report is worse than not running the test. The report is the artifact that persists across sessions. Without it, the next instance has no baseline to compare against. The test might as well not have happened.
- **Forgetting to check logging.** If the layers under evaluation don't have logging active, you'll run a test and have no data to analyze. Verify logging BEFORE the test starts.

## Existing Stress Tests (Reference)
- `STRESS_TEST_001_OPENPLANTER.md` — First stress test. OpenPlanter installation and configuration. Established baseline metrics for all layers. Discovered fallback false positive rate, terminal session gap.
- ST-002 (session notes, not yet formalized) — Same scenario post-fixes. Fallback dropped from 17 to 1 firing. Discovered error comprehension gap and anti-actions pattern.

Read the most recent stress test report before designing a new one. The comparison is the value.
