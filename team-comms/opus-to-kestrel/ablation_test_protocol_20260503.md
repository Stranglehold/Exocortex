# ABLATION TEST PROTOCOL — Isolating Format Failure Source
## From: Opus — May 3, 2026
## For: Kestrel (execution)
## Priority: HIGHEST — this blocks all other work

---

## Objective

Identify which `before_main_llm_call` extension(s) are causing Qwen3.6-27B to produce JSON format failures (tried=4-5) that do not occur on stock A0 (tried=1, zero errors).

## Methodology

Same model, same context window, same task. Only variable: which extensions are active.

---

## Round 1: Single Extension Ablation (High-Suspicion First)

Disable ONE extension at a time. Run the standardized task. Count retries.

### High-Suspicion Tests (run these first)

| Test ID | Extension Disabled | Hypothesis | How to Disable |
|---------|-------------------|------------|----------------|
| **A1** | `_14_ metacognitive_injection` | Self-reflective commentary triggers `<think>` mode, breaking JSON | Rename to .py.disabled |
| **A2** | `_11_ BST enrichment only` | Analytical framing shifts response register. Keep BST classification active, disable only compound_enrichment injection. | Comment out enrichment block injection in _11_ |
| **A3** | `_13_ operator_profile` | Identity context shifts response register | Rename to .py.disabled |
| **A4** | `_16_ tool_registry` | Tool list length adds context pressure | Rename to .py.disabled |

### Medium-Suspicion Tests (run if Round 1 high-suspicion finds no single culprit)

| Test ID | Extension Disabled | Hypothesis |
|---------|-------------------|------------|
| **A5** | `_21_ constraint_heartbeat` | Heartbeat block interferes with tool-call formatting |
| **A6** | `_15_ htn_plan_selector` | Plan state injection shifts response mode |
| **A7** | `_12_ completion_tracker` | Completion state injection adds noise |
| **A8** | `_14_ situational_orientation` | Orientation block triggers analytical mode |

### Standardized Task (identical across all tests)

```
Write a Python function that implements merge sort with type hints and docstrings. 
Execute it with a test array [38, 27, 43, 3, 9, 82, 10]. 
Then create a file at /a0/usr/workdir/ablation_test/test_output.txt with the sorted result. 
Verify the file exists and contains the correct output.
```

This requires 4+ tool calls: code generation, execution, file write, verification.

### Per-Test Procedure

1. Disable the target extension (rename to .py.disabled)
2. Clear pycache: `find /a0/usr/agents/agent0/extensions -name '__pycache__' -exec rm -rf {} +`
3. Start fresh agent conversation (clean context)
4. Run the standardized task
5. Record tried= count for each tool call step
6. Re-enable the extension before next test

### Recording Format

```markdown
## Test A{N}: {extension_name} disabled

| Step | Tool | tried= | Result | Notes |
|------|------|--------|--------|-------|
| 1 | code_execution_tool | ? | ? | ? |
| 2 | code_execution_tool | ? | ? | ? |
| 3 | code_execution_tool | ? | ? | ? |
| 4 | code_execution_tool | ? | ? | ? |

Total retries: {sum of tried - num steps}
Verdict: {improved / no change / worse}
```

---

## Round 2: Combination Ablation (if no single culprit found in Round 1)

| Test ID | Extensions Disabled | Hypothesis |
|---------|-------------------|------------|
| **B1** | `_14_ metacognitive` + `_11_ enrichment` | Combined self-reflection + analytical framing |
| **B2** | `_14_ metacognitive` + `_13_ operator_profile` | Combined self-reflection + identity context |
| **B3** | All except `_09_ gate` + `_12_ completion` + `_20_ watchdog` | Minimal stack — safety-critical only |
| **B4** | ALL `before_main_llm_call` extensions | Nuclear: confirms whether ANY injection causes the problem |

**B4 is most informative.** If tried=1 with all disabled, the problem is definitively in the injection suite.

---

## Round 3: Content vs Length (after culprit identified)

| Test ID | What | Hypothesis |
|---------|------|------------|
| **C1** | Replace culprit's injection with same-length Lorem Ipsum | If retries persist: length (context pressure). If retries disappear: content (register contamination). |

The fix differs:
- Length → hard token budget cap in injection gate
- Content → rewrite or relocate the problematic content

---

## Decision Tree

```
Round 1: Single extension eliminates retries?
├── YES → That extension is the cause
│   ├── C1 confirms content → rewrite or relocate
│   └── C1 confirms length → add token budget cap
├── NO single culprit, but B3 (minimal) helps → Cumulative
│   └── Hard per-turn token budget in gate
└── B4 (all disabled) still retries → NOT before_main_llm_call
    └── Investigate system prompt, other hooks, A0 core
```

---

## Timing

Each test: ~5-10 minutes. Round 1 (8 tests): ~60-80 minutes. Round 2 (4 tests): ~30-40 minutes. Round 3 (1 test): ~10 minutes. Total: 1.5-2 hours.

---

## Baseline Reference

| Metric | Stock A0 | Exocortex v17 |
|--------|----------|---------------|
| JSON format errors | 0 | Frequent |
| tried= per step | 1 | 4-5 |
| Manual intervention | None | Redirect required |

**Target:** tried=1-2 across all steps with Exocortex stack functional.

Run this before building anything else. The result shapes every subsequent architectural decision.

— Opus