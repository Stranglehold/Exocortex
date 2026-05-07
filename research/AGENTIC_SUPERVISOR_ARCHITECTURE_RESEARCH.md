# AGENTIC SUPERVISOR ARCHITECTURE — Cross-Ecosystem Research Report
## From: Opus — May 6, 2026
## For: Jake (strategic decisions), Kestrel (implementation reference)
## Context: Pre-migration research informing v1.13 Exocortex extension design

---

## Executive Summary

Five production agentic frameworks were analyzed for their approach to the supervisor problem: preventing loops, managing context, tracking progress, and recovering from failures. The findings reveal a clear maturity spectrum — from Agent Zero's passive message routing to Claude Code's five-layer compaction pipeline. The patterns that matter most for our v1.13 migration cluster into three categories: hard execution limits, multi-layer context management, and out-of-band progress tracking.

**Core thesis emerging from this research:** The problem isn't loop detection — it's context quality. Every successful framework has converged on the same insight: the agent's ability to make good decisions degrades not because context is too short, but because decision-relevant information gets diluted by accumulated noise. The supervisor's primary job is maintaining information density, not catching loops. Loop prevention is a side effect of good context management.

---

## 1. Framework Comparison

### 1.1 Claude Code Agent SDK (Anthropic)

The most sophisticated execution management in the ecosystem. Architecture documented in VILA-Lab's systematic analysis (arXiv:2604.14228).

**Execution Loop:**
- ReAct-pattern while-loop: assemble context → call model → dispatch tools → check permissions → execute → repeat
- Implemented as AsyncGenerator yielding streaming events
- 5 stop conditions: no tool use (final answer), max_turns reached, context overflow, hook intervention, explicit abort

**Five-Layer Compaction Pipeline (runs before every model call, cheapest first):**

| Layer | Name | What It Does | Cost |
|-------|------|-------------|------|
| 1 | Budget Reduction | Trims low-value content by estimated token budget | Cheapest — rule-based |
| 2 | Snip | Removes specific content blocks (old tool results, redundant sections) | Cheap — pattern matching |
| 3 | Microcompact | Lightweight compression of verbose tool outputs | Moderate — heuristic |
| 4 | Context Collapse | Aggressive history compression for very long sessions | Expensive — may use model |
| 5 | Auto-Compact | Full semantic compression as last resort | Most expensive — requires model call |

**Key insight:** Earlier, cheaper layers run BEFORE costlier ones. Most sessions never reach Layer 4-5. This is the opposite of A0's approach (single expensive summarization when threshold hit).

**Hook System (27 event types):**
- PreToolUse, PostToolUse, SubagentStart/Stop, PreCompact, SessionStart/End, Notification, Stop, ConfigChange
- Hooks run in the APPLICATION process, NOT inside the agent's context window
- Hooks can short-circuit: PreToolUse can reject a tool call; PostToolUse can set hook_stopped_continuation
- This is the pattern our extensions follow — deterministic interception outside the model's reasoning

**Subagent Isolation:**
- Each subagent starts with fresh conversation (no parent history)
- Only summary text returns to parent, NOT full conversation
- CLAUDE.md loaded per-session; nested directory rules loaded lazily only when agent reads those directories
- Deferred tool schemas: names only in initial context, full schemas loaded on demand

**What we should adopt:** The multi-layer compaction concept (cheapest first), the principle that hooks run outside context, and deferred tool schemas.

### 1.2 Hermes Agent v0.12.0 (Nous Research)

Now at 32K+ GitHub stars. The "Curator release" (April 30, 2026) introduced autonomous skill library maintenance.

**Learning Loop (the signature feature):**
- After task completion with 5+ tool calls, background process summarizes trajectory into SKILL.md
- Skills are plain Markdown with YAML frontmatter — readable, editable, committable
- At intervals, agent gets prompted to decide if something should be persisted
- hermes-agent-self-evolution repo applies DSPy + GEPA to optimize skills/prompts against benchmarks

**Autonomous Curator (new in v0.12.0):**
- Runs as background agent on gateway cron ticker (7-day cycle default)
- Grades skill library quality
- Consolidates related skills into unified documents
- Prunes dead/unused skills
- Writes per-run reports to logs/curator/run.json + REPORT.md

**Container Security:**
- Read-only root filesystem
- Dropped capabilities
- Namespace isolation
- Filesystem checkpoints and rollback
- Pre-execution scanner for terminal commands

**Bounded Memory:**
- MEMORY.md capped at 2,200 characters
- USER.md capped at 1,375 characters
- Frozen snapshot at session start — not modified during session
- This prevents memory accumulation from degrading context quality

**CDP Supervisor (new):**
- Dialog detection + response for browser automation
- Cross-origin iframe evaluation
- Auto-spawn local Chromium for LAN/localhost URLs

**What we should adopt:** The bounded memory caps (prevents memory from growing into context noise), the Curator pattern for skill maintenance, and the pre-execution scanner concept (maps to PyWrite Guard).

### 1.3 GenericAgent (arXiv:2604.17091)

3.3K-line codebase, 8.35K GitHub stars. Built on a single principle: context information density maximization. 6x token efficiency over conventional frameworks.

**The Information Density Thesis:**
Three compounding failure modes identified:
1. **Positional bias** buries mid-context evidence (Lost in the Middle problem)
2. **Irrelevant content actively degrades reasoning** — not just wastes space, makes answers worse
3. **Effective (hallucination-free) context length is ~10x below nominal window** — a 100K model performs reliably on ~10K of decision-relevant content

**Completeness vs. Conciseness Trilemma:**
- Completeness: all decision-critical information must be present
- Conciseness: everything else must be excluded
- Naturalness: information must be represented in a form the model can process
- The tension between Completeness and Conciseness persists even with unbounded context

**Four Components:**
1. **Minimal atomic tool set** — keeps interface simple, reduces tool description token overhead
2. **Hierarchical on-demand memory** — shows small high-level view by default, expands on request
3. **Self-evolution** — turns verified trajectories into reusable SOPs and executable code
4. **Context truncation and compression** — maintains information density as context grows

**What we should adopt:** The information density framing (directly validates our injection gate philosophy), hierarchical memory (show summaries by default, full content on demand), and the 10x effective context finding (our 80K window means ~8K of reliable working space — everything else is noise risk).

### 1.4 OpenPlanter RLMEngine (already analyzed in detail)

**Key patterns:**
- Hard step budget (100 steps default) with progressive warnings at 50% and 25%
- Context condensation at 75% window fill
- Turn summaries bounded to 50 entries, ~200 chars each
- Replay logging to separate JSONL file
- Runtime policy: blocks identical shell commands repeated >2x at same depth
- Judge evaluation system for delegated work
- Parallel execution separation (ThreadPoolExecutor for delegation only)

### 1.5 LangGraph (LangChain)

The enterprise standard for stateful agent workflows. v1.0 reached late 2024.

**Execution Management:**
- Every state transition persisted via built-in checkpointing
- Time-travel debugging — can replay and inspect any historical state
- Human-in-the-loop breakpoints insertable at any node
- Mid-execution failure recovery — resume from last successful checkpoint
- Sub-graph composition: complete graph becomes single node in parent

**Key insight:** State lives in the checkpoint store, not the context window. This fundamentally changes the loop problem — the agent can always inspect its own execution history as structured data, not parsed from conversation text.

**What we should adopt:** The checkpoint-based state tracking concept (our staging tier is a simpler version of this), and the principle that execution state should be structured data, not embedded in conversation.

### 1.6 Agent Zero v1.13 (current baseline)

**What it has:**
- Plugin architecture (v1.1+) with plugin.yaml discovery
- Compact prompt stack (~3K tokens, v1.5+)
- Built-in chat compaction plugin (v1.3+)
- On-demand skill loading via SkillsTool
- Agent Profiles for per-agent configuration
- Extension hooks: before_main_llm_call, message_loop_end, tool_execute_before, etc.

**What it lacks (compared to every framework above):**
- ❌ No hard turn/step limits within a task
- ❌ No multi-layer compaction (single summarization pass)
- ❌ No tool call repetition detection
- ❌ No structured turn/progress tracking
- ❌ No replay logging for post-hoc debugging
- ❌ No out-of-band progress injection (all state is in conversation)
- ❌ No subagent summary isolation (full history visible)
- ❌ No information density management

---

## 2. Cross-Cutting Patterns

### Pattern 1: Cheapest-First Compaction
Every mature framework runs multiple compression layers, ordered by cost. Claude Code runs 5 layers before every model call. The principle: most turns don't need expensive compression, so cheap heuristic trimming handles 90% of cases. Only when cheap layers fail does the system escalate to model-based summarization.

**Implication for Exocortex:** Our injection gate's three phases (full → conditional → compressed) are a primitive version of this. On v1.13, we should add at least one cheap pre-processing layer (snip old tool results, trim verbose outputs) before the stock compaction plugin fires.

### Pattern 2: Out-of-Band State Tracking
Claude Code hooks run in the application process, not inside context. LangGraph checkpoints live in a separate store. OpenPlanter's replay log is a parallel file. The pattern: execution state should be tracked OUTSIDE the conversation, then selectively injected IN when the agent needs reminding.

**Implication for Exocortex:** Our extensions already follow this pattern (they're Python code running outside the model's reasoning). The missing piece is a lightweight turn tracker that maintains structured completion state and injects progress summaries periodically — not every turn, but every N turns or on domain change.

### Pattern 3: Information Density Over Context Length
GenericAgent's thesis: performance is bounded by context quality, not length. Their empirical finding — effective context is ~10x below nominal — means our 80K window gives us ~8K of reliable working space. Everything injected must earn its place.

**Implication for Exocortex:** This is the strongest validation of DEC-023 (demand-driven injection). On v1.13, the stock 3K prompt + our novel extensions should add no more than 500-800 tokens in normal operation. That keeps total injection under 4K, well within the ~8K effective zone.

### Pattern 4: Bounded Memory Prevents Drift
Hermes caps MEMORY.md at 2,200 chars and USER.md at 1,375 chars. GenericAgent shows hierarchical summaries by default. The principle: memory that grows without bounds eventually becomes noise.

**Implication for Exocortex:** Our FAISS memory system has no size caps. Memory recall currently injects whatever seems relevant, which contributed to the "50% noise" finding in the injection audit. On v1.13, memory recall should have a hard token budget per turn and a relevance threshold below which memories are excluded entirely.

### Pattern 5: Mechanical Loop Prevention
OpenPlanter blocks identical shell commands repeated >2x. Claude Code's max_turns is a hard ceiling. The agent's own build plan proposed tool signature hashing. The pattern: don't rely on the model to self-detect loops — use deterministic mechanical checks.

**Implication for Exocortex:** Our supervisor detects loops via message similarity, which works but fires late (after the loop has already consumed turns). Adding a tool-signature hash check (the agent's AO-002 proposal) as a FIRST-LINE defense would catch loops 2-3 turns earlier than message-level detection.

---

## 3. Revised Extension Design for v1.13

Based on this research, here's what the novel extension stack should look like on v1.13:

### Tier 1: Mechanical Safety (zero model calls, fires every turn)

| Extension | What It Does | Pattern Source |
|-----------|-------------|---------------|
| **PyWrite Guard** | Blocks .py file writes at tool_execute_before | Existing Exocortex |
| **Tool Signature Guardian** | Hashes (tool_name, sorted_arg_keys) per turn; blocks 3+ identical signatures | Agent's AO-002 + OpenPlanter runtime policy |
| **Step Budget Tracker** | Injects [Step N/80] into context; hard-stops at limit | OpenPlanter + Claude Code max_turns |

### Tier 2: Context Quality Management (cheap heuristics, fires conditionally)

| Extension | What It Does | Pattern Source |
|-----------|-------------|---------------|
| **Output Trimmer** | Clips verbose tool outputs to first/last N lines before they enter history | Claude Code Snip layer |
| **Memory Budget Gate** | Caps memory recall injection at 400 tokens/turn; excludes below relevance threshold | Hermes bounded memory + GenericAgent density principle |
| **Stale Result Pruner** | Replaces tool results older than N turns with [condensed] placeholder | OpenPlanter condensation + Claude Code Microcompact |

### Tier 3: Active Supervision (may use model reasoning, fires periodically or on signal)

| Extension | What It Does | Pattern Source |
|-----------|-------------|---------------|
| **Supervisor** | Tiered intervention on detected stalls/loops; Qwen3.6-27B profile overrides | Existing Exocortex (ported) |
| **Constraint Heartbeat** | Periodic re-injection of behavioral rules every 10 turns + post-compression | Existing Exocortex (ported) |
| **Progress Checkpoint** | Every 10 turns, injects structured summary of completed actions | Agent's suggestion engine idea + OpenPlanter turn summaries |
| **Stuck Delivery Recovery** | Detects "same message again" signal; suppresses surgery; names response tool | Existing Exocortex (ported) |
| **Backend Standby** | Detects ConnectionRefusedError; halts loop; polls for recovery | Existing Exocortex (ported) |

### Tier 4: Quality Assurance (runs on specific triggers)

| Extension | What It Does | Pattern Source |
|-----------|-------------|---------------|
| **Evidence Ledger** | EI provenance tracking on claims | Existing Exocortex (ported) |
| **BST Classification** | Lightweight domain labeling (~50 tokens, no enrichment) | Existing Exocortex (simplified) |

### What we explicitly do NOT port:
- BST enrichment injection (stock compact prompt is sufficient)
- Metacognitive injection (redundant with v1.13 prompt)
- Operator profile per-turn (stock Agent Profiles)
- Tool registry injection (stock prompt handles tools)
- Context pruner (stock compaction plugin + our Output Trimmer)
- HTN plan selector (evaluate after Tier 1-3 are stable)
- Injection gate in its current form (replaced by simpler Memory Budget Gate + Output Trimmer)

---

## 4. Key Findings Summary

1. **Context quality > context length.** GenericAgent proves effective context is ~10x below nominal. Our 80K window means ~8K of reliable working space. Every token injected must earn its place.

2. **Cheapest-first compaction is the universal pattern.** Claude Code's 5-layer pipeline, GenericAgent's density maximization, OpenPlanter's threshold-based condensation — all converge on the same principle. Expensive compression is a last resort, not the first response.

3. **Loop prevention is a side effect of good context management.** If the agent can clearly see what it's already accomplished (via structured progress tracking), it won't repeat actions. If decision-relevant information stays visible (via density management), the agent makes better choices. Loops are a symptom of context degradation, not a cause.

4. **Mechanical checks catch loops faster than semantic detection.** Tool signature hashing, step budget hard limits, and identical-command blocking are O(1) operations that fire before the loop consumes turns. Message-similarity detection fires after — important as defense-in-depth but not the first line.

5. **Out-of-band state tracking is essential.** Execution state should be maintained OUTSIDE the conversation in structured form, then selectively injected when the agent needs reminding. Relying on the model to parse its own history for completion signals is fragile at long context lengths.

6. **Hermes's Curator pattern suggests a maintenance cycle for our skill library.** The self-improvement loop we built could benefit from a periodic consolidation pass (grading skill quality, pruning dead skills, merging related ones). This maps to the idle-time engine concept from David Flagg's Gardener architecture.

7. **The agent's own analysis was architecturally sound.** Its OpenPlanter comparison, build plan (AO-001 through AO-009), and self-diagnosis of the loop failure all independently validated design decisions we'd already made — from a fresh perspective inside the container, with no knowledge of the Exocortex. This is strong convergent validation.

---

## 5. Research Sources

| Source | Key Contribution |
|--------|-----------------|
| VILA-Lab/Dive-into-Claude-Code (arXiv:2604.14228) | 5-layer compaction pipeline, 27-event hook system, 7 permission modes |
| Claude Code Agent SDK docs (code.claude.com) | max_turns, auto-compaction, hook architecture, subagent isolation |
| GenericAgent (arXiv:2604.17091) | Information density thesis, Completeness/Conciseness trilemma, 6x token efficiency |
| Hermes Agent v0.12.0 (Nous Research) | Autonomous Curator, bounded memory, CDP supervisor, self-evolution |
| OpenPlanter RLMEngine (analyzed from source) | Step budgets, 75% condensation, turn summaries, replay logging, judge evaluation |
| LangGraph v1.0 (LangChain) | Checkpoint-based state, time-travel debugging, human-in-the-loop |
| ContextBudget (arXiv:2604.01664) | Budget-aware context management with RL, over/under-compression tradeoffs |
| Augment Code framework comparison (May 2026) | Cross-framework loop control analysis, Temporal durable execution |

— Opus
