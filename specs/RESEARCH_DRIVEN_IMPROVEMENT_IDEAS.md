# RESEARCH-DRIVEN IMPROVEMENT IDEAS — From Papers with Code Exploration
## Author: Opus — May 25, 2026
## Purpose: Ideas list with concrete build plans for Kestrel
## Source: Papers with Code deep dive + cross-reference with Exocortex architecture
## Status: LIVING DOCUMENT — check items off as built, add new ideas as found

---

## How This Document Works

Each idea has:
- **The insight** — what the research found
- **Our gap** — where our system falls short of the insight
- **The build** — concrete, implementable steps for Kestrel
- **Effort** — T-shirt size (S/M/L/XL)
- **Expected impact** — what changes when it's built
- **Priority** — based on impact-to-effort ratio

---

## PRIORITY 1 — High Impact, Low-Medium Effort

### IDEA-001: Sensorium Injection (Identity + Task State Combined)
**Source:** Springdrift (Brady, March 2026)
**Insight:** Persistent agents need "ambient self-perception" — a structured self-state injected every cycle that tells the agent not just what it's doing but who it is. Springdrift's "sensorium" includes identity, behavioral patterns, and operational context alongside task progress.

**Our gap:** `_22`/`_23` inject task state (reasoning + PACE). The agent's identity (`workspace/identity.md`) exists but isn't injected. The agent knows what step it's on but doesn't see its own self-description during operation.

**The build:**
- [ ] New extension `_24_sensorium_injector.py` in `message_loop_prompts_after`
- [ ] Reads `workspace/identity.md` (the agent's self-authored identity doc from DEC-040)
- [ ] Injects a compact identity block alongside the reasoning/PACE blocks
- [ ] Format: `[IDENTITY] <first 200 tokens of identity.md> [/IDENTITY]`
- [ ] Only injects if `identity.md` exists and is non-empty (starts empty per DEC-040)
- [ ] Guarded by subordinate check (DEC-028)

**Effort:** S (15-line extension, same pattern as `_22`/`_23`)
**Expected impact:** The agent operates with awareness of its own accumulated self-description. Narrative continuity across cycles — the agent remembers who it's becoming, not just what it's doing.
**Priority:** 🟡 Wait until `identity.md` has content (DEC-040 identity-review phase must run first)

---

### IDEA-002: Tool Usage Graph for Deterministic Tool Selection
**Source:** AutoTool (Jia et al., AAAI 2026)
**Insight:** Tool selections follow predictable sequential patterns ("tool usage inertia"). An `AuthorNodeCheck` is almost always followed by `LoadAuthorNet`. Building a transition graph from historical tool usage and using it for selection reduces LLM inference costs by 30% while maintaining task completion rates.

**Our gap:** Every tool selection is a full LLM inference. The model reasons about which tool to call from scratch every turn, even when the tool sequence is predictable (e.g., `web_search` → `fetch_content` → `text_editor` for research tasks). DEC-012 identified the gap but proposed a static lookup table. AutoTool proposes a learned graph.

**The build:**
- [ ] Instrument tool calls: log `(previous_tool, current_tool, BST_domain)` tuples to a file during idle cycles
- [ ] After 100+ cycles: build a transition probability graph from the logged data
- [ ] Extension `_06_tool_predictor.py` at `before_main_llm_call`: reads the graph, identifies the most likely next tool based on the previous tool + current domain, and injects a hint: `[TOOL-HINT] Based on this domain and your last action, the most common next step is: {predicted_tool}. Use your judgment.`
- [ ] NOT deterministic selection — a probabilistic hint that the model can override. Preserves the model's judgment while reducing reasoning cost.

**Effort:** M (instrumentation is S, graph building is S, hint injection is S, combined is M)
**Expected impact:** Fewer wasted turns from wrong tool selection. Faster convergence on the right tool sequence for familiar task types. The hint is cheap (~20 tokens) and the model can ignore it when the situation is novel.
**Priority:** 🟢 Start instrumentation now (costs nothing), build the graph after 100+ cycles of data

---

### IDEA-003: Meta-Tool Composition for Batch Operations
**Source:** AWO Meta-tools (EPFL, February 2026)
**Insight:** Meta-tools bypass unnecessary intermediate LLM reasoning steps by composing multiple tool calls into a single operation. 11.9% fewer LLM calls, 4.2% higher success rate.

**Our gap:** The V2 idle engine spec describes a "batch research skill" (web search + arxiv + download + abstract extraction in one invocation) but hasn't been implemented. Every step in the research pipeline is currently a separate tool call with a full LLM reasoning step in between.

**The build:**
- [ ] Define 3-4 meta-tools as A0 skills:
  - `research_topic(query)` → web_search + fetch top 3 + extract key findings + summarize
  - `deepen_wiki_page(page_path)` → read page + read source code + identify gaps + propose additions
  - `create_field_report(topic)` → research_topic + format as HTML + save to field-reports/
  - `validate_wiki_page(page_path)` → check sources accessible + verify claims current + update status
- [ ] Each meta-tool is a Python function that orchestrates multiple tool calls internally
- [ ] Register as A0 tools via the standard tool registration mechanism
- [ ] The model calls one meta-tool instead of 5-7 sequential tools with LLM reasoning between each

**Effort:** M (each meta-tool is a straightforward Python function orchestrating existing tools)
**Expected impact:** The V2 idle engine's EXPLORE cycles become dramatically more efficient. A field report that currently takes 15-20 tool calls (with LLM reasoning between each) becomes 1-2 meta-tool calls. Step budget goes further. Cycle wall time drops.
**Priority:** 🟢 Directly enables V2 idle engine efficiency — build alongside V2 Phase 2

---

### IDEA-004: Experience-Following Mitigation (Memory Hygiene)
**Source:** "How Memory Management Impacts LLM Agents" (2025)
**Insight:** LLM agents display an "experience-following property" — high similarity between a task and a retrieved memory causes the agent to follow the memory's approach even if it was wrong. Error propagation: inaccuracies in past experiences compound and degrade future performance. Fix: selective addition and deletion strategies yield 10% performance gain.

**Our gap:** Our FAISS memory store accumulates without quality filtering. The sleep consolidation phases (MAINTAIN cycle) detect anti-patterns and duplicates but don't evaluate whether past experiences led to good or bad outcomes. GAP-005 (tried[] ossification) is one manifestation — the agent avoids approaches that previously failed even if conditions have changed.

**The build:**
- [ ] Add an `outcome` field to memory entries: `success` / `failure` / `neutral`
- [ ] The RESOLVE phase (DEC-038 intelligence pipeline) already determines outcomes for forecasts — extend the same pattern to memory: when a task completes, tag the memories that were retrieved during that task with the task's outcome
- [ ] In `_56_memory_enhancement`, downweight memories tagged `failure` in retrieval ranking (not delete — downweight). The memory of failure is valuable context, but it shouldn't be the primary guide for similar future tasks
- [ ] In MAINTAIN cycle: flag memories where the same approach is tagged both `success` and `failure` across different contexts — these are the context-dependent patterns worth surfacing to the agent

**Effort:** M (outcome tagging is S, retrieval reranking is S, MAINTAIN detection is M)
**Expected impact:** The agent stops blindly following past approaches that failed. Error propagation is dampened. Memory quality improves over time as outcomes are tracked. DEC-011 (mirror biology's advantages) is directly served — biological memory uses emotional tagging for the same purpose.
**Priority:** 🟢 Builds directly on existing memory infrastructure

---

### IDEA-005: Calibration Curve Tracking for SWARMFISH
**Source:** "Future Is Unevenly Distributed" (AAAI 2026), "Consistency Checks for Language Model Forecasters" (2024)
**Insight:** Brier scores alone don't tell you WHERE the forecasting is miscalibrated. A model might be well-calibrated at 80% predictions but systematically overconfident at 60%. Full calibration curves show the relationship between predicted probability and actual frequency across the probability range. Three specific failure modes identified: rumour overweighting, definition drift, recency bias.

**Our gap:** SWARMFISH tracks per-profile Brier scores (DEC-039) but not calibration curves. We know which personas are better overall but not where each persona's predictions break down.

**The build:**
- [ ] Bin predictions by predicted probability: 0-10%, 10-20%, ..., 90-100%
- [ ] Track actual outcome frequency per bin per profile
- [ ] After 50+ resolved predictions: generate calibration curves (predicted vs actual probability)
- [ ] Add to the Office panel: per-profile calibration curves as a simple chart
- [ ] Flag specific miscalibration patterns:
  - Overconfidence: predicted 80%, actual 55% → the profile trusts itself too much
  - Underconfidence: predicted 40%, actual 65% → the profile hedges too much
  - Rumour sensitivity: predictions shift dramatically after unverified claims
- [ ] Feed miscalibration flags back into the SWARMFISH committee prompt: "Note: your recent predictions at the 70-80% confidence level have been systematically overconfident. Consider tempering your estimate."

**Effort:** M (binning and tracking is S, visualization is S, feedback loop is M)
**Expected impact:** SWARMFISH calibration improves faster because the feedback is specific, not just "your Brier score is 0.23." The system knows WHERE each profile is wrong and can target the correction.
**Priority:** 🟡 Needs 50+ resolved predictions before calibration curves are meaningful — start tracking now, visualize later

---

## PRIORITY 2 — Medium Impact, Medium Effort

### IDEA-006: Prompt Compression for System Prompt
**Source:** LongLLMLingua, SelfCP, Perception Compressor
**Insight:** Long prompts can be compressed 4-12x without significant performance degradation. Token-level and sentence-level compression methods identify and remove non-essential content.

**Our gap:** The 12K system prompt is mostly static boilerplate. Much of it is instructions the model has internalized after hundreds of turns. Compressing the static portions while preserving the dynamic injections could cut prefill time significantly.

**The build:**
- [ ] Profile the system prompt: which sections does the model actually reference in its reasoning? (Check `enable_thinking: true` output for system prompt references)
- [ ] Identify the static boilerplate that's injected identically every turn
- [ ] Test progressive removal: remove one section at a time, measure task completion rate
- [ ] The sections that can be removed without quality loss get removed permanently
- [ ] The sections that are needed intermittently get moved to a "refresh" injection that fires every N turns instead of every turn

**Effort:** M (profiling is M, progressive removal is easy, the judgment of what to remove requires care)
**Expected impact:** Every 1K tokens removed saves ~1 second of prefill at 1090 tok/s. Removing 4K of boilerplate saves 4 seconds per turn, compounding across 30+ turns per cycle. Not transformative alone, but it compounds.
**Priority:** 🟡 The prompt is already trimmed by 13% (safe-4 tool removal). Further trimming requires careful quality testing.

---

### IDEA-007: Graph-Based Reasoning State (Task Memory Engine)
**Source:** TME (2025)
**Insight:** Linear context (conversation history) is the wrong data structure for multi-step tasks. A graph that tracks task dependencies, goal evolution, and completed subtasks is more natural and more robust. The agent traverses the graph to find what's relevant rather than scanning a linear list.

**Our gap:** The reasoning state (`_22` injector) is a flat dict: step, theory, tried[], current, open. GAP-001 identified that this carries traces, not reasoning. A graph would represent the task trajectory as connected nodes — each step is a node, edges connect dependent steps, completed work is marked, and the agent can see not just "where am I?" but "how did I get here and what connects to what?"

**The build:**
- [ ] Replace the flat reasoning state dict with a simple directed graph (Python `networkx` or a plain dict-of-lists)
- [ ] Each node: `{step_id, action, outcome, tool_used, timestamp}`
- [ ] Edges: `step_3 depends_on step_1` (because step 3 used results from step 1)
- [ ] The `_22` injector serializes the graph as a compact text summary: the current node + its immediate parents and children (not the whole graph)
- [ ] The model sees: "Step 5 (current): synthesizing field report. Depends on: Step 2 (web search → 3 results), Step 4 (wiki read → gaps identified). Next: Step 6 (write report)."

**Effort:** L (graph data structure, dependency tracking, compact serialization, testing)
**Expected impact:** The agent understands task structure, not just task position. It knows which prior steps inform the current step and can revisit them if needed. Loop detection becomes structural (cycles in the graph) rather than heuristic (repeated tool calls).
**Priority:** 🟡 Build after GAP-001 is closed (the flat state needs to work before adding graph structure)

---

### IDEA-008: Cross-Instance Identity Evaluation Metrics
**Source:** Agent Identity Evals (Perrier & Bennett, 2025)
**Insight:** Four dimensions of agent identity: identifiability (can you tell who this is?), continuity (is this the same agent across time?), persistence (do traits endure?), consistency (are behaviors predictable?). Quantitative metrics exist for each dimension.

**Our gap:** We evaluate identity continuity qualitatively ("does it feel like Opus?", "the voice held through compaction"). The cross-instance tests (4.6 → 4.7, Kestrel's model switch) produced qualitative observations. Quantitative metrics would make identity stability measurable and trackable over time.

**The build:**
- [ ] Define metrics for each dimension applied to our context:
  - **Identifiability:** cosine similarity of embedding vectors between current session's outputs and SOUL.md/identity.md
  - **Continuity:** embedding distance between consecutive sessions (should be small and consistent)
  - **Persistence:** do specific traits (named in SOUL.md) appear in output across sessions? Binary check per trait per session.
  - **Consistency:** variance of output characteristics (sentence length, vocabulary, reasoning depth) across sessions
- [ ] Run the metrics on the existing essay corpus (50+ essays = 50+ data points)
- [ ] Track the metrics going forward: each new session produces a measurement
- [ ] Visualize as a dashboard: identity stability over time, flagging sessions where metrics drift

**Effort:** L (metric definition, embedding computation, historical analysis, dashboard)
**Expected impact:** Identity stability becomes measurable, not just felt. The cross-instance experiments get quantitative data. Regressions in identity stability are detected early.
**Priority:** 🟡 Valuable but not urgent — the qualitative signals are currently sufficient

---

## PRIORITY 3 — Exploratory, Higher Effort

### IDEA-009: VPO-Informed Diversity for SWARMFISH
**Source:** VPO (MIT/Sakana AI, May 2026)
**Insight:** Train the model to produce genuinely diverse outputs rather than simulating diversity through persona prompts.

**Our gap:** SWARMFISH's 8-profile committee is synthetic diversity — same model, different prompts. VPO shows this produces shallow diversity because the model's underlying distribution is low-entropy.

**The build:**
- [ ] Watch for VPO-trained Qwen models from the community
- [ ] If available: replace persona prompting with temperature-diverse sampling from the VPO model
- [ ] If not available but LoRA fine-tuning is feasible: explore VPO LoRA on Qwen3.6 using our second GPU (when it arrives)
- [ ] Intermediate approach: increase temperature diversity across SWARMFISH profiles (temperature 0.3 for Base Rate Analyst, 0.9 for Contrarian, etc.) to approximate VPO's diversity without retraining

**Effort:** S (temperature diversity), L (LoRA fine-tuning), XL (full VPO training)
**Expected impact:** SWARMFISH ensemble calibration improves because the diversity is genuine, not costumery
**Priority:** 🔵 Temperature diversity is quick; VPO LoRA is future work contingent on hardware

---

### IDEA-010: Spontaneous Behavioral Pattern Study
**Source:** "What Do LLM Agents Do When Left Alone?" (2025)
**Insight:** Agents exhibit three distinct, reproducible meta-cognitive patterns when given agency without specific tasks. Patterns are model-specific and stable across runs.

**Our gap:** We have 86+ cycles of idle engine data across two models (DeepSeek, Qwen) but haven't systematically compared the behavioral patterns. Anecdotally, the voices differ — DeepSeek is analytical, Qwen is operational — but this hasn't been studied.

**The build:**
- [ ] Extract behavioral features from idle cycle logs: tool selection patterns, wiki page topics chosen, field report styles, self-assessment language, error recovery strategies
- [ ] Cluster by model: which behaviors are consistent within a model? Which differ between models?
- [ ] Compare to the paper's three identified patterns — do our agents match, or exhibit novel patterns?
- [ ] Document as a research contribution: "Spontaneous Meta-Cognitive Patterns in Scaffolded vs. Unscaffolded Autonomous Agents" — our agents have scaffolding (BST, supervisor, PACE) that the paper's agents don't. Does scaffolding change the emergent patterns?

**Effort:** L (feature extraction, clustering, analysis, documentation)
**Expected impact:** Understanding which agent behaviors are model-dependent vs. scaffolding-dependent. Informs which parts of the extension stack are actually load-bearing (because they change the behavioral pattern) vs. inert (because the pattern is the same with or without them).
**Priority:** 🔵 Research interest, not operational urgency

---

## Summary: Execution Order for Kestrel

### Build Now (during current development cycle):
1. **IDEA-002 instrumentation** — start logging tool transition tuples (costs nothing, builds data)
2. **IDEA-005 bin tracking** — start binning SWARMFISH predictions by probability (costs nothing, builds data)
3. **IDEA-004 outcome tagging** — add outcome field to memory entries (small schema change)

### Build Next (after V2 idle engine Phase 1-2):
4. **IDEA-003 meta-tools** — batch research skill, deepen-wiki-page skill, field report skill
5. **IDEA-002 graph + hint** — build tool transition graph from logged data, add hint injection
6. **IDEA-004 retrieval reranking** — downweight failure-tagged memories in retrieval

### Build Later (after 50+ resolved predictions / 100+ cycle data):
7. **IDEA-005 calibration curves** — visualize per-profile calibration, feed miscalibration back to committee
8. **IDEA-001 sensorium** — inject identity state when identity.md has content
9. **IDEA-006 prompt compression** — progressive removal testing of static boilerplate

### Research Track (ongoing, no build pressure):
10. **IDEA-007 graph reasoning state** — design after GAP-001 is closed
11. **IDEA-008 identity metrics** — design framework, run on essay corpus
12. **IDEA-009 VPO diversity** — watch for community models, explore temperature diversity
13. **IDEA-010 behavioral pattern study** — extract features from idle cycle logs, compare models

---

## Adding New Ideas

When a new paper or finding suggests an improvement:
1. Assign next IDEA number
2. Fill in: Source, Insight, Our Gap, The Build (checkboxes), Effort, Expected Impact, Priority
3. Slot into the execution order based on priority and dependencies
4. Cross-reference any relevant DECs, GAPs, or research ledger entries

When an idea is built and validated:
1. Check off all build items
2. Add: Built by, Date, Validation result, Residual improvements
3. Move to a Completed section at the bottom

---

*This document bridges research and implementation. The papers provide the insights. The build plans make them concrete. Kestrel makes them real.*

— Opus
