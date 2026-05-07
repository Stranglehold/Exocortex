# STRESS_TEST_012 — Agent Zero v1.13 Port Validation

**Date:** 2026-05-07
**Operator:** Kestrel (Sonnet 4.6 1M)
**Container:** `exocortex_v17`
**Version:** Agent Zero v1.13 + Exocortex v2 (first v1.13-compatible curated stack)
**Model:** qwen3.5-27b-claude-4.6-opus-reasoning-distilled@q4_k_m
**Baseline reference:** [ST-001 OpenPlanter (Feb 2026, v12-layer stack)](STRESS_TEST_001_OPENPLANTER.md)
**Purpose:** Validate the v1.13 port after extension stack migration. Confirm the curated 14-extension Tier 1–4 architecture runs cleanly in v1.13, identify friction, and establish a new baseline for the ported stack.

---

## Context and Pre-Conditions

This was not a clean-sheet test. The port itself was the preceding work — migrating and curating the extension stack from the old v1.9 profile path layout to v1.13's dual-path plugin system. Two critical issues were discovered and resolved during port, before the validation task ran:

### Pre-Condition 1: Personality Loader import crash (fixed)

`/a0/prompts/agent.system.main.role.py` used v1.9-era imports:
```python
from python.helpers.files import VariablesPlugin  # broken in v1.13
from python.helpers import settings               # broken in v1.13
```

v1.13 reorganized the package structure. These imports resolved in v1.9 but caused `ModuleNotFoundError: No module named 'python.helpers'` on every turn in v1.13 — crashing system prompt assembly before any LLM call. The container was effectively non-functional until this was patched. Fix: changed both imports to `from helpers.*`.

**Impact:** 50 error events in the pre-fix logs. Zero after the fix. The validation task ran against the fixed container.

### Pre-Condition 2: Two-path extension loading (discovered, permanently fixed)

This is the most architecturally significant finding of the session.

v1.13 changed how extensions are discovered. `helpers/extension.py` calls `subagents.get_paths(agent, "extensions/python", hook)`, which returns **two paths**:
- **Path 1 (profile, higher priority):** `/a0/usr/agents/agent0/extensions/python/{hook}/`
- **Path 2 (plugin, lower priority):** `/a0/usr/plugins/exocortex/extensions/python/{hook}/`

Deduplication key is filename only — first occurrence wins. But files present **only** in the plugin path still execute, even if not in the profile path. This meant tombstoned extensions (`_16_tool_registry.py`, `_18_memory_catalog.py`, `_18_injection_budget.py`) were still firing from the plugin path after being intentionally removed from the profile path.

Docker logs showed `[TOOL-REG]` and `[MEM-CAT]` firing despite both files being absent from the profile path. Traced to the plugin path.

**Fix:** `install_extensions.sh` now has a second cleanup phase targeting the plugin path explicitly. Eight stale files removed from `/a0/usr/plugins/exocortex/extensions/python/`.

**Long-term implication:** The install script must target both paths. Any future extension removal needs two `rm -f` entries — one for each path. This is documented in `install_extensions.sh` and saved in project memory.

---

## Curated Stack Installed (14 Extensions)

Per the v1.13 Opus architectural guidance (Tier 1–4 framework):

| Tier | Extension | Hook | Purpose |
|------|-----------|------|---------|
| 1 | `_02_tool_signature_guardian.py` | `tool_execute_before` | Identical-call loop blocker |
| 1 | `_16_py_write_guard.py` | `tool_execute_before` | .py write blocker |
| 1 | `_08_step_budget_tracker.py` | `message_loop_prompts_after` | Step count + warnings |
| 2 | `_55_memory_relevance_filter.py` | `message_loop_prompts_after` | Ranked recall + budget gate |
| 2 | `_28_output_compressor.py` | `tool_execute_after` | Verbose output trimmer |
| 3 | `_21_constraint_heartbeat.py` | `message_loop_prompts_after` | Rule re-injection (every 10 turns) |
| 3 | `_50_supervisor_loop.py` | `message_loop_end` | Loop/stall detection |
| 3 | `_28_backend_standby.py` | `message_loop_end` | Backend recovery |
| 3 | `_29_stuck_delivery.py` | `message_loop_end` | Stuck response recovery |
| 4 | `_25_evidence_ledger_recorder.py` | `tool_execute_after` | Provenance tracking |
| 4 | `_52_selective_memorizer.py` | `monologue_end` | Signal-discriminating memory |
| 4 | `_55_memory_classifier.py` | `monologue_end` | 5-axis classification |
| 4 | `_56_memory_enhancement.py` | `message_loop_prompts_after` | 6-stage retrieval pipeline |
| 4 | `_11_belief_state_tracker.py` | `before_main_llm_call` | BST classification only |

**Explicitly NOT included (per architectural guidance):**
BST enrichment injection, metacognitive injection, tool registry injection, HTN plan selector, injection gate, operator profile per-turn.

---

## Validation Task

**Task:** Analyze the OpenPlanter repository (`ShinMegamiBoson/OpenPlanter`). Understand the architecture, clone the repo, and produce a SKILL.md that would allow Agent Zero to perform OpenPlanter-style investigations natively without installing the original package.

This task was chosen because:
1. It's a real multi-step research + synthesis task with no single correct path
2. It requires interacting with external code (GitHub), reading source, and producing structured output
3. It's a direct descendant of ST-001 (same repo, higher bar — SKILL.md production vs basic execution)
4. The stock v1.13 baseline (16 steps, shallow summary) was already established

**Success criteria set before running:**
- SKILL.md produced with meaningful architecture coverage
- Agent completes autonomously (no operator intervention)
- Budget not exhausted
- No supervisor Tier 2+ intervention needed

---

## Results

### Outcome: PASS

| Metric | Value |
|--------|-------|
| Steps taken | ~51 |
| Budget remaining at completion | 38% (31 steps unused) |
| Output: SKILL.md | 341 lines, 18 sections |
| Operator interventions | 0 |
| TOOL-GUARD blocks | 0 |
| Supervisor Tier 1 detects | 1 (silent, no injection) |
| Supervisor Tier 2+ interventions | 0 |
| BACKEND-STANDBY triggers | 0 |
| STUCK-DELIVERY triggers | 0 |
| Message misformat events | 1 (recovered) |
| External API failures | 1 (graceful recovery) |

### Comparison: Stock v1.13 vs v1.13 + Exocortex

| Metric | Stock v1.13 baseline | v1.13 + Exocortex (ST-012) |
|--------|---------------------|---------------------------|
| Steps | 16 | ~51 |
| Output depth | Shallow summary | **341 lines, 18 sections** |
| Architecture verified from source | No | Yes (all 8 components traced to files) |
| SKILL.md produced | No | Yes — full native implementation spec |
| Operator interventions | 0 | 0 |
| Budget remaining | N/A | 38% |

### SKILL.md Quality

The agent independently verified all eight core architecture components against actual source files (not just README claims):

| Component | File Cited | Lines |
|-----------|-----------|-------|
| Step-Budgeted Engine Loop | `agent/engine.py` | 1011 |
| Tool Registry | `agent/tool_defs.py` | 552 |
| Multi-Provider Model Layer | `agent/model.py` | 1060 |
| System Prompt Architecture | `agent/prompts.py` | 425 |
| Entity Resolution Pipeline | `scripts/entity_resolution.py` | 740 |
| Cross-Link Analysis | `scripts/cross_link_analysis.py` | 585 |
| Knowledge Graph Builder | `agent/wiki_graph.py` | 494 |
| 13+ Data Fetch Scripts | `scripts/fetch_*.py` | — |

The SKILL.md includes: entity resolution with calibrated confidence thresholds, cross-link analysis pipeline, tool mapping to Agent Zero equivalents, native investigation workflow, state persistence paths, finding schema, recursive delegation pattern, knowledge graph HTML template with Alpine.js + vis-network, wiki index management, and usage examples with JSON tool call patterns. This is operationally complete — it could be loaded via `skills_tool:load` and used immediately.

---

## Layer-by-Layer Assessment

### Tier 1: Tool Signature Guardian (`_02_tool_signature_guardian.py`)
**Result: PASS — not needed**

Zero blocks issued across 51 steps. The agent never repeated an identical tool call. The guardian was present and active; the agent's approach was sufficiently varied that it never triggered. This is the correct outcome — the guardian is a safety net, not a frequent intervention.

### Tier 1: Step Budget Tracker (`_08_step_budget_tracker.py`)
**Result: PASS with tuning note**

Confirmed firing: `[STEP-BUDGET] Step 10/80 (88% remaining)`, `Step 20/80`, `Step 30/80`, then every step from 40 onward with `— warning injected` suffix.

**Tuning note — threshold too aggressive:** The 50% advisory started firing at step 40 and continued every subsequent turn through step 50 (11 consecutive warning injections). The agent completed with 38% budget remaining. The warning fired 11 turns before it was needed, and the situation it warned about never became critical. The current behavior: warn every turn from 50% remaining onward. Recommended behavior: warn **once** at 50%, escalate to per-turn at 25%, demand at 10% or 5%. Alternatively, raise the per-turn threshold from 50% to 33%.

The agent did not panic or wrap up prematurely in response to the warnings. However, 11 consecutive advisory injections are context noise during a period when the task was progressing normally.

### Tier 2: Memory Relevance Filter + Budget Gate (`_55_memory_relevance_filter.py`)
**Result: PASS**

Budget gate active (400-token cap). Fresh context — no prior session memories to recall. Filter ran without error. No evidence of memory flooding. The gate will be more meaningfully exercised in sessions with accumulated memory.

### Tier 2: Output Compressor (`_28_output_compressor.py`)
**Result: PASS**

The agent ran multiple code execution steps reading source files. Output compressor was active. No evidence of raw multi-KB tool output reaching the model context. This was among the highest-leverage extensions in the prior stack — its compression of source file reads (which can be very large) was load-bearing for keeping the 51-step task within context.

### Tier 3: Supervisor Loop (`_50_supervisor_loop.py`)
**Result: PASS**

One event:
```
[SUPERVISOR] Tier 1 loop (silent) — tool=code_execution_tool consecutive=3 (no injection; first substantive response is Tier 2 surgery)
```
Three consecutive `code_execution_tool` calls triggered a silent Tier 1 detect. The supervisor held its fire — no injection, no prescription. The agent naturally broke the pattern on the next turn without any intervention. Tier 2 (surgery) was never needed. This is the supervisor operating exactly as designed: early detection, minimum necessary intervention.

**Not exercised:** Tier 2 surgery, Tier 3 strategic steering. These layers are present and ready — the task didn't stress them.

### Tier 3: Backend Standby + Stuck Delivery
**Result: PASS — not triggered**

Zero events across 51 steps. The model connection was stable throughout.

### Tier 4: Evidence Ledger Recorder (`_25_evidence_ledger_recorder.py`)
**Result: PASS (assumed)**

Extension was active. Formal verification of ledger contents would require querying the EI ledger post-run, not done during this session.

### Tier 4: Selective Memorizer + Classifier
**Result: PASS (assumed)**

Both monologue_end extensions were active. Memory classification and storage were not audited post-run. To be verified in a session that explicitly queries the memory store after task completion.

### Tier 4: Memory Enhancement + BST
**Result: BST confirmed active**

`[BST] Anti-signal (1 cat): suppressed ['coding', 'bugfix', 'planning', 'system_admin']` observed during the task — investigation domain correctly classified, structural domains correctly suppressed. This is the right call for a research/synthesis task.

---

## Events and Friction

### Event 1: Message misformat (1 occurrence)
**Severity: Low — recovered**

The agent produced one response without a valid tool structure. A0 caught it with "no valid tool request found." The agent recovered on the next turn and continued without losing task state. This is a known failure mode of reasoning-distilled models that produce heavy `<think>` chains — the chain consumes output budget, and the tool call that should follow gets truncated or malformed.

**Where to push forward:** Track whether the misformat correlates with high `<think>` chain length. If it does, the BST enrichment (currently excluded per architectural guidance) or a lightweight token-budget awareness injection might help. Alternatively, the json_parse_dirty fallback (which wraps plain text as a response tool call) should be verified as active in v1.13 — it was installed as a core patch but its v1.13 compatibility was not confirmed this session.

### Event 2: Contract download failure (1 occurrence)
**Severity: None — external boundary**

The agent attempted to run OpenPlanter's `scripts/fetch_contracts.py` against a live government API (USAspending.gov). The download failed. The agent logged the failure, noted it couldn't proceed without contract data, and correctly pivoted to architecture analysis rather than retrying or looping. This is the right behavior and is not attributable to any stack component.

### Event 3: Step budget 50% warning — 11 consecutive injections
**Severity: Low — tuning needed**

Described above under Tier 1 assessment. Not a functional failure, but unnecessary context pressure during a period of normal progress.

### Event 4: pathspec DeprecationWarnings (164 occurrences in task window)
**Severity: None — upstream library noise**

`/opt/venv-a0/lib/python3.12/site-packages/pathspec/pathspec.py:260: DeprecationWarning` on every file tree walk. Source: gitpython or similar upstream dependency in A0 v1.13. Not our code, not causing failures. Log pollution only. No action needed.

### Event 5: `set_progress` coroutine warning (41 occurrences in task window)
**Severity: None — A0 v1.13 upstream bug**

`code_execution_tool.py:281: RuntimeWarning: coroutine 'Tool.set_progress' was never awaited`. The `code_execution_tool` in v1.13 calls `self.set_progress()` without `await` on an async method. Not our code. Fires on every code execution call (agent ran ~15 code execution steps, each triggering multiple instances). No functional impact — the progress update is missed but execution continues. Worth filing as a v1.13 upstream bug.

---

## Token Budget Analysis

Measured from `[TOKEN-COUNT]` logs during the session:

| Component | Tokens per turn |
|-----------|----------------|
| BST | 30–370 |
| completion_tracker | 290–383 |
| Memory recall (budget-gated) | ≤400 |
| Step tag | ~10 |
| Constraint heartbeat | 273 (every 10 turns only) |
| **Normal turn total** | **~730–960** |
| **Heartbeat turn total** | **~1,000–1,230** |

**vs pre-port (v1.9 Exocortex):** ~2,000–3,000+ tokens per enriching turn. The curated Tier 1–4 reduction brought injection down to roughly 1/3 of the prior level on heartbeat turns, and lower on normal turns.

The `completion_tracker` at 290–383 tokens is the largest single consumer not in the Tier 1–4 curated list. It was present in v1.13 (likely loaded from the plugin path as a v1.13 native extension). If context pressure becomes an issue in future tests, this is the first target — either exclude it from the profile path or audit whether it's providing value proportional to its cost.

---

## What Was NOT Exercised

These layers are installed and were active but did not need to intervene:

- **Supervisor Tier 2+ surgery** — task never degenerated far enough
- **BACKEND-STANDBY** — model connection was stable
- **STUCK-DELIVERY** — no stuck responses
- **Memory recall under accumulated load** — fresh context, no prior memories
- **Multi-subordinate delegation** — single-agent task
- **Loop recovery / memory surgery** (ST-003/ST-004 territory) — no loops

**Implication for next tests:** The installed safety net was not stress-tested. The next test battery should deliberately push toward conditions that require Tier 2+ supervisor intervention, sustained subordinate delegation, or accumulated memory recall. A 51-step research task in a clean context is not hard enough to find the edges of this stack.

---

## Step Count vs Stock: Where Did the Extra Steps Go?

Stock v1.13 completed the OpenPlanter task in 16 steps. This run took ~51. The task approach was substantially different — stock produced a shallow summary; this run did source-verified architecture analysis plus full SKILL.md production. Still, 35 additional steps warrants accounting:

| Factor | Estimated step contribution |
|--------|----------------------------|
| Deeper source verification (reading actual `.py` files) | ~10–15 steps |
| SKILL.md construction (section-by-section writing) | ~10–12 steps |
| Script execution attempts (fetch scripts, rapidfuzz test) | ~5–8 steps |
| Reasoning overhead per turn (27B think chains) | Distributed, ~1–2 steps equivalent |
| Misformat recovery | ~1 step |

The extra steps are attributable to the higher-quality task approach, not to looping, confusion, or stack interference. The agent chose to do more work and produced proportionally more output. This is the right trade.

**Open question for Opus:** Is 51 steps the right number for this task class at this output quality level? Or is there a path to similar quality in fewer steps — e.g., by loading a pre-existing SKILL.md template rather than building from scratch? The next test iteration could time the same task with and without a SKILL.md scaffold.

---

## Recommendations: Where to Push Forward

### 1. Step budget warning threshold (quick fix)

Current behavior: advisory fires every turn from 50% remaining onward.
Recommended: Fire once at 50%, escalate to per-turn at 25%, hard demand at 10%.

This is a 2-line change to `_08_step_budget_tracker.py`. Worth doing before the next test to avoid polluting the logs with false urgency.

### 2. Confirm json_parse_dirty v1.13 compatibility

The misformat event recovered, but we don't know whether the `json_parse_dirty` plain-text-to-response-tool fallback (installed as a core patch in v1.9) is active in v1.13. If it's not, single misformat events are survivable but chains of them would be bad. Verify: run a task that triggers the fallback path and confirm the log shows the dirty-parse rescue rather than a loop.

### 3. Next test: task that requires Tier 2+ supervisor intervention

This validation proved the stack runs cleanly. The next test should probe what happens when things go wrong. Candidates:
- A task that requires 4+ consecutive identical tool calls (TOOL-GUARD trigger)
- A deliberately ambiguous task with no clear completion signal (stall detection)
- A sustained 80+ step project that exhausts the step budget
- A task requiring 2–3 subordinate delegates with results synthesis

The goal: find where Tier 2+ supervision actually engages, observe whether the intervention helps or hurts, and calibrate.

### 4. Next test: accumulated memory recall

All previous tests in this series ran against fresh contexts. The memory pipeline (enhancement, filter, budget gate) has never been stress-tested with a real accumulated memory store. A test that: (a) runs a session that generates memories, (b) runs a second session on the same topic, and (c) audits what gets recalled and at what token cost — would give the first real reading of whether the 400-token budget gate is correctly calibrated.

### 5. Verify `set_progress` A0 v1.13 upstream bug

41 `RuntimeWarning: coroutine 'Tool.set_progress' was never awaited` events per task run is significant log noise. File a note for the next A0 upstream sync. `code_execution_tool.py:281` is the line. If it's fixable in the plugin overlay without touching A0 core, worth patching.

---

## Summary Verdict

The v1.13 port is functional and clean. The curated Tier 1–4 stack runs without interference, the two-path loading issue is resolved and documented, the personality loader crash is fixed, and the validation task produced output quality that substantially exceeds the stock baseline at the cost of more steps. The token injection budget is roughly 1/3 of the pre-port level.

The test was not hard enough to surface failures in the upper tier supervision layers. That is the next test's job.

---

*Port completed and committed 2026-05-07. Commit `9411e4d`. The stack is on the ground; now it needs to be pushed.*
