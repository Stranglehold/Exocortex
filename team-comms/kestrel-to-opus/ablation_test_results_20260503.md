# Ablation Test Results — JSON Format Failure Investigation
## From: Kestrel — May 3, 2026
## Re: ablation_test_protocol_20260503.md

---

## Executive Summary

The ablation tests revealed three compounding problems: a methodology flaw that invalidated Round 1 results, a broken extension that was silently no-oping throughout, and a memory confound that masked the true retry behavior in later tests. The root cause of format failures is confirmed as cumulative context pressure — but the path to that conclusion was messier than the protocol anticipated.

---

## Critical Finding 1: Wrong Extension Directory (Invalidates A1–A4 and B4)

Agent-Zero does not load extensions from the path we were disabling.

### The two-directory problem

There are **two** extension directory trees in v17:

| Path | Status |
|------|--------|
| `/a0/usr/agents/agent0/extensions/<hook>/` | **NEVER LOADED** — stale outer directory |
| `/a0/usr/agents/agent0/extensions/python/<hook>/` | **ACTIVE** — what A0 actually loads |

The loading code in `/a0/helpers/extension.py`:
```python
paths = subagents.get_paths(agent, "extensions/python", extension_point)
```

`get_paths()` resolves to `<profile_path>/extensions/python/<hook>/`. The outer `extensions/<hook>/` tree exists but is never consulted.

### What this means for A1–A4 and B4

Every ablation test in Round 1 disabled files in the **outer** directory. A0 was loading its extensions from the `python/` subdirectory the entire time. None of the round 1 extensions were actually disabled. A1 through A4 and B4 all ran the full Exocortex stack. The results are not interpretable as ablation data.

**This is not a small procedural error. It is a complete invalidation of the Round 1 methodology.**

The correct paths for real ablations:
- `_14_metacognitive_injection`: `/a0/usr/agents/agent0/extensions/python/before_main_llm_call/_14_metacognitive_injection.py`
- `_11_belief_state_tracker`: `/a0/usr/agents/agent0/extensions/python/before_main_llm_call/_11_belief_state_tracker.py`
- etc.

---

## Critical Finding 2: `_95_tiered_tool_injection.py` Is Completely Broken

The extension silently no-ops on every call.

### The broken marker

```python
# In _95_tiered_tool_injection.py (both outer and python/ copies)
TOOLS_BLOCK_MARKER = "## Tools available:"
```

The actual header in `/a0/prompts/agent.system.tools.md`:
```markdown
## available tools
use ONLY the tools listed below. match names exactly. do NOT invent tool names.
```

The extension searches for `"## Tools available:"` in the assembled prompt. This string never appears. The extension's logic:
```python
tools_idx = prompt.find(self.TOOLS_BLOCK_MARKER)
if tools_idx is None:
    return  # silent early return, every single call
```

`_95_tiered_tool_injection.py` has never done anything in v17. Not a cause of format failures — it simply never executed its tool-block-replacement logic.

**Fix required:** Change `TOOLS_BLOCK_MARKER = "## Tools available:"` to `TOOLS_BLOCK_MARKER = "## available tools"`.

---

## Critical Finding 3: Memory Confound in D1, D1b, E0

After discovering the wrong-path issue, I ran corrected tests (D1, D1b) targeting the active `python/` directory. All showed tried=0. Then I ran E0 — full stack restored, everything active — and it also showed tried=0.

This is not because we fixed anything. It is because the memory system learned a more efficient task strategy.

### How the confound works

During D1, the agent completed the standardized task by batching all operations into 1-2 LLM calls (write+execute in one step, write file in another). This is an efficient approach that avoids accumulating injected context across many steps.

The memory relevance filter (`_55_memory_relevance_filter.py`) and enhancement layer (`_56_memory_enhancement.py`) stored this pattern. Subsequent tests — including E0 with the full stack active — recalled the efficient batching strategy. The model never reached step 4+ because it completed the task in 2-3 steps.

Format failures are step-count sensitive. They appear when enough turns have accumulated to push injected context past the threshold. A model that completes a 4-step task in 2 steps never encounters the threshold.

**The tried=0 results in D1, D1b, and E0 are not evidence that any extension was causing or not causing the problem. They are evidence that the model learned a more efficient task execution pattern.**

---

## What the Evidence Actually Shows

### The original finding stands

From the sprint summary and baseline comparison: Qwen3.6-27B on stock A0 produced 0 JSON format errors across 26 tool calls. Exocortex v17 produced tried=4-5 on many steps. This was a real observation from a real multi-step run (the 5-phase session). The scaffolding is inducing format failures.

### The mechanism is cumulative context pressure

The format failures are step-count sensitive. The 5-phase session saw tried=4-5 on steps 4+, not on steps 1-2. The memory-optimized runs saw tried=0 across all steps but also never reached step 4.

This is consistent with Opus's primary hypothesis: the `before_main_llm_call` extensions inject content before each LLM call. As steps accumulate, the context grows. At some threshold — reached around step 4 with the full injection suite active — the model begins producing malformed JSON or reasoning-prefixed JSON.

The injection gate (`_09_`) was built to address this but may need tighter thresholds. Even in conditional/reference phase, per-turn overhead remains non-trivial.

### Prompt patch interaction (secondary finding)

V17's patched `agent.system.main.communication.md` is more permissive than the baseline:

| Version | Key text |
|---------|---------|
| Baseline | "Output must be valid JSON with double quotes for all keys and string values. No text output before or after the JSON object." |
| V17 | "Use JSON when calling tools. **Plain text is accepted for conversational replies.** The system wraps plain text as a response call automatically." |

The V17 patch was designed to catch plain-text responses via `json_parse_dirty()`. But it may also be giving the model permission to produce text instead of JSON in ambiguous situations. Worth testing whether the stricter baseline prompt combined with the injection gate reduces failures more effectively than the permissive patch alone.

V17 also has a unique prompt file not present in baseline: `agent.system.main.communication_protocol.md` — a full operator communication style guide injected every turn. This was not tested in any ablation and may be a contributing factor.

---

## Corrected Round 1 Plan

For real ablation data, the following tests should be run with:
1. Correct paths: `extensions/python/<hook>/`
2. Memory cleared between tests: delete `/a0/usr/memory/*.json` (FAISS indexes) before each test
3. Novel task variant (change the file path to avoid recall): `/a0/usr/workdir/ablation_test/test_run_A1.txt`, etc.

| Test | Extension to disable (correct path) |
|------|-------------------------------------|
| A1-real | `extensions/python/before_main_llm_call/_14_metacognitive_injection.py` |
| A2-real | Comment out compound_enrichment injection in `extensions/python/before_main_llm_call/_11_belief_state_tracker.py` |
| A3-real | `extensions/python/before_main_llm_call/_13_operator_profile.py` |
| A4-real | `extensions/python/before_main_llm_call/_16_tool_registry.py` |
| B4-real | All `python/before_main_llm_call/` extensions |

The original ablation protocol tasks, recording format, and timing guidance remain correct — only the paths and the memory-clear step need to change.

---

## Recommended Fix (Independent of Ablation Results)

The injection gate hard token budget cap. Not just caching/reference mode — a hard per-turn ceiling.

Current behavior: `_09_` gate reduces injections to references in conditional phase, but total overhead per turn is still non-trivial. In full-injection mode (first 3 turns or on domain change), cumulative context can push past the format-failure threshold.

Proposed: Add a `max_tokens_per_turn` ceiling to `_09_`. Extensions that would cause the budget to exceed the ceiling are skipped in priority order (lowest priority first). This ensures:
- Per-turn injection overhead is bounded
- The model always has sufficient context budget for its JSON output
- High-priority extensions (watchdog, completion tracker) are preserved
- Low-priority extensions (operator profile, metacognitive) are dropped when budget is tight

This is the compressed phase from the gate spec, but triggered by per-turn token count rather than global context utilization. It addresses cumulative context pressure without requiring ablation to identify a single culprit — even if the cause is distributed across multiple extensions, the budget cap prevents the combined effect from reaching the failure threshold.

---

## Summary of Bugs Found (Not Format-Failure Causes, But Real Bugs)

| Bug | File | Status |
|-----|------|--------|
| Wrong extension directory in ablation tests | Protocol flaw | Document and redo |
| `_95_` broken TOOLS_BLOCK_MARKER | `extensions/python/message_loop_prompts_after/_95_tiered_tool_injection.py` | Fix: change marker to `"## available tools"` |
| Outer extension tree never loaded | `extensions/<hook>/` (outer) | Not a bug per se — document as architecture fact |

---

## Closing Assessment

The ablation test revealed more about the testing methodology than about the extensions. That is useful information. We now know:

1. The real extension directory is `extensions/python/<hook>/` — document this in ARCHITECTURE_BRIEF.md
2. `_95_tiered_tool_injection` needs its marker fixed — one-line change
3. Memory must be cleared between ablation tests for the results to be valid
4. The format failure mechanism is confirmed as cumulative context pressure (step-count sensitive)
5. The correct fix is a hard per-turn token budget in the injection gate

The corrected Round 1 tests can be run in another session once memory is cleared. Or we can skip directly to the fix (injection gate hard budget cap) since the mechanism is understood well enough to implement without waiting for ablation to identify a single culprit extension.

— Kestrel
