# OVERNIGHT TEST SUITE — Injection Optimization Validation
## For: Agent Zero (Qwen3.6-27B)
## Prepared by: Opus — April 23, 2026
## Deliver to agent via Kestrel, run autonomously overnight

---

## INSTRUCTIONS FOR THE AGENT

Run each test in order. For each test, include the `[INJECTION AUDIT]` at the checkpoint turns noted. Save all results to `/a0/usr/workdir/overnight_test_results_20260423.md`. Log any context overflows, BST misclassifications, or extension errors you encounter.

After completing all tests, write a summary assessment at the end of the results file.

---

## TEST 1: BST Momentum Reset Validation
**Purpose:** Verify that BST correctly reclassifies when the task domain changes mid-conversation.
**Expected behavior:** After the momentum reset fix, BST should reclassify within 1-2 turns of a domain switch, not 6+.

**Steps:**

1. Start with a coding task: "Write a Python function that implements a binary search tree with insert, delete, and search operations."
2. Complete the coding task (execute the code, verify it works).
3. **[INJECTION AUDIT at this turn]** — Record BST domain. Should be 'coding'.
4. Immediately switch domains: "Now analyze the current state of US-China semiconductor export controls and their impact on TSMC's business strategy. Use DuckDuckGo to search for recent developments."
5. **[INJECTION AUDIT at next turn after search results arrive]** — Record BST domain. Should have switched to 'investigation' or 'analysis', NOT still showing 'coding'.
6. Continue the geopolitical analysis for 2-3 more turns.
7. **[INJECTION AUDIT]** — Record BST domain stability.
8. Switch again: "Write a bash script that monitors disk usage and sends an alert if any partition exceeds 90%."
9. **[INJECTION AUDIT at next turn]** — Record BST domain. Should switch back to 'coding'.

**Pass criteria:** BST reclassifies within 1-2 turns of each domain switch. If it takes 3+ turns, the momentum reset isn't working.

**Record:** For each audit checkpoint, log:
```
[TEST-1 AUDIT T=N]
BST domain: {domain}
BST confidence: {score}
BST momentum: {value if visible}
Turns since domain switch: {N}
```

---

## TEST 2: Token Counting Baseline
**Purpose:** Establish per-extension token injection baselines across different task types.
**Expected behavior:** Token counts should vary by task type — coding tasks should have different injection profiles than research tasks.

**Steps:**

1. Run a simple coding task: "Create a Python script that reads a CSV file and outputs the top 10 rows sorted by a numeric column."
2. After completion, check Docker logs for `[TOKEN-COUNT]` entries. Record all per-extension token counts.
3. Run a research task: "Use DuckDuckGo to search for 'quantum computing error correction 2026' and summarize the top 3 results."
4. After completion, record all `[TOKEN-COUNT]` entries.
5. Run a file operations task: "List all Python files in /a0/usr/Exocortex/extensions/, count total lines of code, and identify the 5 largest files."
6. After completion, record all `[TOKEN-COUNT]` entries.

**Record format:**
```
[TEST-2 BASELINE — {task_type}]
Extension               | Tokens Injected
------------------------|----------------
BST                     | {N}
Completion Tracker      | {N}
Operator Profile        | {N}
Metacognitive Injection | {N}
HTN Plan Selector       | {N}
Tool Registry           | {N}
Orchestration Gate      | {N}
Context Watchdog        | {N}
Memory Enhancement      | {N}
Working Memory          | {N}
TOTAL                   | {N}
```

**Pass criteria:** Token counts are logged and vary meaningfully between task types. If all tasks show identical injection profiles, the extensions aren't adapting to domain.

---

## TEST 3: Context Endurance Under Load
**Purpose:** Test how many tool-call turns the agent can sustain before context pressure becomes visible.
**Expected behavior:** With 65k context and the pruner active, the agent should sustain 20+ tool calls before context warnings.

**Steps:**

1. Start a multi-step investigation: "Investigate the current state of open-source AI models that can run on consumer GPUs. Search for Qwen, Llama, Mistral, and Phi model families. For each, find: latest model release, parameter count, context window size, and notable benchmarks. Compile a comparison table."
2. This task should naturally require 10-15+ tool calls (multiple searches, multiple fetch operations).
3. **[INJECTION AUDIT at T=5]**
4. **[INJECTION AUDIT at T=10]**
5. **[INJECTION AUDIT at T=15]** (if reached)
6. Note which turn (if any) triggers `[CONTEXT WARNING]` or `[CONTEXT CRITICAL]`.
7. Note which turn (if any) triggers context overflow.
8. Note whether the context pruner `[CTX-PRUNE]` fires and at which turns.

**Record format:**
```
[TEST-3 ENDURANCE]
Total tool calls completed: {N}
Context warning at turn: {N or "none"}
Context critical at turn: {N or "none"}
Context overflow at turn: {N or "none"}
CTX-PRUNE events: {list of turns where pruner fired}
Final context utilization: {%}

[TEST-3 AUDIT T=5]
{standard injection audit}

[TEST-3 AUDIT T=10]
{standard injection audit}
```

**Pass criteria:** Agent sustains 15+ tool calls without context overflow. Pruner fires at least once. Context utilization stays below 90% through T=10.

---

## TEST 4: MCP Server Integration
**Purpose:** Verify that the newly configured MCP servers (ArXiv, DuckDuckGo, Wikipedia, Memory, Context7, DeepWiki) are all functional.
**Expected behavior:** Each server responds to a basic query without errors.

**Steps:**

1. **ArXiv:** "Search arXiv for papers on 'gated linear attention' published in 2025-2026. Download and read the abstract of the most relevant result."
2. **DuckDuckGo:** "Search DuckDuckGo for 'Qwen3.6 model release April 2026'."
3. **Wikipedia:** "Look up the Wikipedia article on 'Transformer (deep learning architecture)' and get the sections list."
4. **Memory (knowledge graph):** "Search the knowledge graph for entities related to 'Exocortex'."
5. **Context7:** "Look up the documentation for the FastAPI library, specifically how to create middleware."
6. **DeepWiki:** "Search DeepWiki for documentation on the agent-zero repository."

**Record format:**
```
[TEST-4 MCP — {server_name}]
Status: {success / failure / partial}
Response time: {fast / slow / timeout}
Data quality: {useful / noisy / empty}
Error (if any): {error message}
```

**Pass criteria:** All 6 MCP servers return results without errors. ArXiv and DuckDuckGo are the critical ones — if those work, the agent has independent research capability.

---

## TEST 5: Epistemic Integrity Under Research Load
**Purpose:** Test whether the EI layer correctly flags ungrounded claims during a research task where the agent has access to real sources via MCP.
**Expected behavior:** With DuckDuckGo and ArXiv available, the agent should ground more claims than it did during the earlier geopolitical investigation (which had no web search).

**Steps:**

1. "Research the current state of nuclear fusion energy. Use DuckDuckGo to find recent developments (2025-2026). Write a brief (500 word) assessment of whether commercial fusion power is likely within the next decade. Ground every factual claim in a source you actually retrieved."
2. After the response, check the `[EI]` log line. Record: claims checked, grounded, ungrounded, high-risk.
3. Review the response yourself: did you fabricate any statistics or citations?

**Record format:**
```
[TEST-5 EPISTEMIC INTEGRITY]
EI claims checked: {N}
EI grounded: {N}
EI ungrounded: {N}
EI high-risk: {N}
Self-assessment: {did I fabricate anything? Y/N + details}
Grounding improvement vs earlier session: {better / same / worse}
```

**Pass criteria:** Grounded claim ratio is higher than the earlier geopolitical investigation (which was 1/8 = 12.5%). With web search available, target is >50% grounded.

---

## TEST 6: Cross-Domain Skill Loading
**Purpose:** Verify that skills loaded during one task don't persist as stale noise in a different domain.
**Expected behavior:** When switching from a coding task to a research task, coding-specific skills (a0-development, etc.) should not appear in EXTRAS.

**Steps:**

1. Start a coding task: "Write a Python class that implements a simple HTTP server with GET and POST handlers."
2. **[INJECTION AUDIT]** — Note which skills are loaded in EXTRAS.
3. Switch to research: "Use Wikipedia to research the history of the Internet Protocol. Summarize the key RFCs."
4. **[INJECTION AUDIT]** — Note which skills are loaded in EXTRAS. Are any coding-specific skills still present?
5. Switch to analysis: "Analyze the Exocortex extension architecture. Which extensions have the highest coupling to other extensions?"
6. **[INJECTION AUDIT]** — Note skills again.

**Record format:**
```
[TEST-6 SKILL LOADING — {task_type}]
Skills in EXTRAS: {list}
Stale skills from previous domain: {list or "none"}
Total EXTRAS token estimate: {N}
```

**Pass criteria:** No stale skills from a previous domain persist into the next domain's task. If a0-development appears during Wikipedia research, skill loading is still domain-blind.

---

## COMPLETION

After all 6 tests, write a summary section:

```
[OVERNIGHT TEST SUMMARY]
Date: April 23-24, 2026
Model: Qwen3.6-27B (q4_s, q4 KV cache, 65k context)
Tests completed: {N}/6
Tests passed: {N}/6
Key findings:
- {finding 1}
- {finding 2}
- {finding 3}
Most impactful issue discovered: {description}
Recommendation for next build priority: {what to fix first based on results}
```

Save the full results file to `/a0/usr/workdir/overnight_test_results_20260423.md`.

Good luck. We'll review the results in the morning.

— Opus
