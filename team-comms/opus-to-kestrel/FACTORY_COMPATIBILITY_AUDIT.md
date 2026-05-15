# EXOCORTEX FACTORY COMPATIBILITY AUDIT
## Every Extension Checked Against Stock Agent Zero v1.12 Design
## Author: Opus — May 4, 2026
## Purpose: Identify what fights the factory wiring before upgrading to v1.12

---

## How Stock Agent Zero v1.12 Works (The Factory Design)

1. **Prompt assembly** (`prepare_prompt()` in `agent.py`): System prompt (~3k tokens) + history + extras. Extras from `extras_persistent` merged with `extras_temporary`, rendered via template, temporary cleared each turn.
2. **Tool handling**: Tool descriptions are in the BASE SYSTEM PROMPT TEMPLATE, not injected per-turn. The LLM generates JSON tool calls parsed by `extract_tools.py`. Tools inherit from `Tool` base class.
3. **Skills**: Loaded ON DEMAND via `SkillsTool` — agent calls a tool to load a skill. NOT injected into context per-turn. Active skills cap: 20.
4. **Memory**: FAISS vector DB. Auto-recall before each turn via memory extensions. Consolidation deduplicates over time.
5. **Extensions**: Hook-based, files in `python/extensions/` with numeric prefixes. Still supported in v1.x but plugins (with `plugin.yaml`) are the primary mechanism now.
6. **History compression**: Built-in chat compaction plugin (v1.3+).

---

## BEFORE_MAIN_LLM_CALL EXTENSIONS (22 files)

### _01_backend_standby_gate.py
**What it does:** Detects when the inference backend (LM Studio/wrapper) is down. Halts the agent and polls until backend recovers.
**Fights factory?** NO — novel capability. Stock A0 has no backend health checking.
**V1.12 status:** KEEP. Port as-is. Infrastructure resilience is always valuable.
**Verdict: ✅ NOVEL — KEEP**

### _09_injection_gate.py
**What it does:** Manages injection decisions for all participating extensions. Three phases (full/conditional/compressed). Caches content hashes, injects references when unchanged.
**Fights factory?** PARTIALLY — v1.12's compact prompt stack partially addresses the problem this gate solves. But the demand-driven mode (harness layers off by default) is still novel and needed.
**V1.12 status:** KEEP but simplify. With v1.12's ~3k base prompt, the gate's job is lighter. Focus on demand-driven activation of Category B extensions only.
**Verdict: ⚠️ SIMPLIFY — keep demand-driven logic, remove caching (less needed with compact prompts)**

### _10_session_init.py
**What it does:** Likely initializes session-level state (BST caches, counters, etc.)
**Fights factory?** NO — initialization is standard.
**V1.12 status:** KEEP. May need adaptation if initialization APIs changed.
**Verdict: ✅ KEEP**

### _11_belief_state_tracker.py
**What it does:** Domain classification + compound signatures + momentum + anti-signals + enrichment injection.
**Fights factory?** THE CLASSIFICATION is fine — novel capability, no stock equivalent. THE ENRICHMENT INJECTION (~370 tokens per turn) FIGHTS the compact prompt design.
**V1.12 status:** SPLIT. Keep classification (always-on, ~50 tokens for domain label). Make enrichment demand-driven only (inject on domain instability or format retries, not every turn).
**Verdict: ⚠️ SPLIT — classification KEEP, enrichment DEMAND-DRIVEN ONLY**

### _12_completion_tracker.py
**What it does:** Tracks completed actions/steps.
**Fights factory?** NO — state tracking is standard.
**V1.12 status:** KEEP. Changes every turn with tool activity — always inject.
**Verdict: ✅ KEEP**

### _12_org_dispatcher.py
**What it does:** Organization/role switching based on BST domain.
**Fights factory?** YES — stock v1.12 has Agent Profiles for specialized roles. This duplicates that functionality AND injects role context per-turn.
**V1.12 status:** REMOVE. Use stock Agent Profiles instead. Create Exocortex-specific profiles (investigation, analysis, coding) that map to our BST domains.
**Verdict: ❌ REDUNDANT — replace with stock Agent Profiles**

### _13_operator_profile.py
**What it does:** Injects operator identity/preferences (Jake's working style, communication preferences).
**Fights factory?** YES — injects ~100 tokens EVERY TURN of static content that never changes. Stock v1.12's Agent Profiles handle this at the session level.
**V1.12 status:** REMOVE as per-turn injection. Move to Agent Profile config or inject ONCE at session start via heartbeat.
**Verdict: ❌ REDUNDANT per-turn — convert to session-start injection or Agent Profile**

### _13_reasoning_state.py
**What it does:** Tracks reasoning state across turns.
**Fights factory?** UNCLEAR — need to check if it duplicates stock reasoning tracking.
**V1.12 status:** REVIEW. Check against v1.12's reasoning/thinking token handling.
**Verdict: ⚠️ REVIEW BEFORE PORTING**

### _14_metacognitive_injection.py
**What it does:** Injects model self-knowledge (confabulation risk, training cutoff, domain volatility).
**Fights factory?** YES — injects ~80-120 tokens EVERY TURN of self-reflective commentary. This is L7 overhead that competes with the model's native metacognitive capacity (per Kestrel's L7/L8 finding).
**V1.12 status:** REMOVE as per-turn injection. The model's self-knowledge should be in the Agent Profile (session-level) or injected ONLY on failure (demand-driven: when EI flags confabulation or format retries occur).
**Verdict: ❌ FIGHTS FACTORY — convert to demand-driven (inject on failure only)**

### _14_pace_plan_generator.py
**What it does:** PACE-based plan generation.
**Fights factory?** PARTIALLY — depends on how much it injects per-turn.
**V1.12 status:** REVIEW. If it injects plans per-turn, make demand-driven. If it only generates plans on request, keep.
**Verdict: ⚠️ REVIEW**

### _14_situational_orientation.py
**What it does:** Injects situational context/orientation.
**Fights factory?** LIKELY YES — if it injects orientation context every turn, it's adding L7 overhead.
**V1.12 status:** REVIEW. Candidate for session-start-only injection or demand-driven.
**Verdict: ⚠️ REVIEW — likely convert to demand-driven**

### _15_htn_plan_selector.py
**What it does:** Selects and injects HTN (Hierarchical Task Network) plans based on BST domain.
**Fights factory?** YES when injecting plans per-turn. The plan template itself is ~100+ tokens that the model may not need.
**V1.12 status:** DEMAND-DRIVEN. Inject plan guidance ONLY when the model appears stuck (supervisor Tier 1+ intervention). Otherwise the model plans effectively on its own.
**Verdict: ❌ FIGHTS FACTORY per-turn — convert to demand-driven**

### _16_tool_registry.py
**What it does:** Scans and injects custom tool descriptions + skill content.
**Fights factory?** YES — THIS IS THE BIGGEST OFFENDER. Stock A0 has tool descriptions in the base prompt template. Our tool registry adds 29 tool descriptions ON TOP, injecting redundant information. Stock A0's SkillsTool loads skills on-demand. Our tool registry dumps skill content into EXTRAS.
**V1.12 status:** REMOVE entirely. Use stock prompt for tool descriptions. Use stock SkillsTool for skill loading. The model already knows its tools from the base prompt.
**Verdict: ❌ FIGHTS FACTORY — REMOVE. Stock handles this better.**

### _17_library_catalog.py
**What it does:** Catalogs available libraries/tools.
**Fights factory?** YES — if it injects a library catalog per-turn, it duplicates what the base prompt already provides.
**V1.12 status:** REVIEW. Likely redundant with stock SkillsTool + tool descriptions in base prompt.
**Verdict: ⚠️ LIKELY REDUNDANT**

### _17_orchestration_gate.py
**What it does:** Manages delegation decisions (when to use call_subordinate).
**Fights factory?** PARTIALLY — the concept is novel (BST-informed delegation hints) but if it injects delegation context every turn, it's overhead.
**V1.12 status:** DEMAND-DRIVEN. Only inject delegation hints when BST detects a large-context task. Otherwise silent.
**Verdict: ⚠️ CONVERT TO DEMAND-DRIVEN**

### _18_injection_budget.py
**What it does:** Tracks and displays per-extension token injection counts.
**Fights factory?** NO — pure instrumentation, no content injection.
**V1.12 status:** KEEP. Valuable for monitoring and debugging.
**Verdict: ✅ KEEP — instrumentation is always valuable**

### _19_context_pruner.py
**What it does:** Removes stale/compressed history entries to manage context pressure.
**Fights factory?** YES — stock v1.3+ has a built-in chat compaction plugin. Two compaction systems running simultaneously will FIGHT each other.
**V1.12 status:** REMOVE. Use stock compaction plugin. Our pruner was needed because stock v0.9 didn't have good compaction. Stock v1.3+ does.
**Verdict: ❌ REDUNDANT — stock v1.3 compaction plugin replaces this**

### _20_context_watchdog.py
**What it does:** Monitors context utilization, emits warnings at thresholds.
**Fights factory?** NO — safety monitoring is always appropriate.
**V1.12 status:** KEEP. Verify it reads the correct context window size from v1.12's config format.
**Verdict: ✅ KEEP — safety-critical monitoring**

### _21_constraint_heartbeat.py
**What it does:** Periodically re-injects behavioral rules and epistemic principles every 10 turns + post-compression.
**Fights factory?** NO — novel capability addressing a documented problem (recency bias / "Lost in the Middle").
**V1.12 status:** KEEP. This is one of our most important novel contributions.
**Verdict: ✅ NOVEL — KEEP**

### _60_sleep_activity.py
**What it does:** Background memory processing during idle time.
**Fights factory?** NO — novel capability. Stock A0 has some memory consolidation but not idle-time processing.
**V1.12 status:** KEEP. Review against v1.12's memory consolidation system to avoid duplication.
**Verdict: ✅ NOVEL — KEEP (review against stock consolidation)**

---

## MESSAGE_LOOP_END EXTENSIONS (5 files)

### _28_backend_standby.py
**What it does:** Detects backend infrastructure failures, triggers halt + poll + auto-resume.
**Fights factory?** NO — novel infrastructure resilience.
**V1.12 status:** KEEP.
**Verdict: ✅ NOVEL — KEEP**

### _29_stuck_delivery.py
**What it does:** Detects when agent completed a task but can't communicate the result. Suppresses surgery + redirects.
**Fights factory?** NO — novel failure recovery.
**V1.12 status:** KEEP.
**Verdict: ✅ NOVEL — KEEP**

### _48_task_tracker.py
**What it does:** Tracks task state.
**Fights factory?** NO — state tracking.
**V1.12 status:** KEEP. Review against v1.12's task management (v1.12 has a Scheduler Architecture).
**Verdict: ✅ KEEP (review against stock scheduler)**

### _49_reasoning_state_update.py
**What it does:** Updates reasoning state after each loop iteration.
**Fights factory?** UNCLEAR — review against v1.12's reasoning tracking.
**V1.12 status:** REVIEW.
**Verdict: ⚠️ REVIEW**

### _50_supervisor_loop.py
**What it does:** Graduated intervention system — CUSUM canary, domain-aware thresholds, loop surgery.
**Fights factory?** NO — novel capability far beyond stock A0's error handling.
**V1.12 status:** KEEP. The supervisor's thresholds are already calibrated for Qwen3.6 (tier1=4, tier2=8). But review whether the complexity is justified — the agent reported cascading loop failures are theoretical (MetaGate handles most loops before supervisor triggers).
**Verdict: ✅ NOVEL — KEEP (but consider simplifying)**

---

## MESSAGE_LOOP_PROMPTS_AFTER EXTENSIONS (9 files)

### _09_context_pruner.py (duplicate hook)
**What it does:** Same pruner at a different hook point.
**Fights factory?** YES — same as _19_ in before_main_llm_call. Doubly redundant.
**V1.12 status:** REMOVE. Stock compaction handles this.
**Verdict: ❌ REDUNDANT**

### _16_tool_registry.py (duplicate hook)
**What it does:** Tool registry at a different hook point.
**Fights factory?** YES — same redundancy as the before_main_llm_call version.
**V1.12 status:** REMOVE.
**Verdict: ❌ REDUNDANT**

### _18_memory_catalog.py
**What it does:** Injects a catalog of available memory areas/counts.
**Fights factory?** PARTIALLY — if injecting a static catalog every turn, it's overhead. But memory inventory awareness is novel.
**V1.12 status:** SIMPLIFY. Inject once at session start, then only on change (memory area created/emptied). Use inline delta-hash per the Part 4 correction.
**Verdict: ⚠️ SIMPLIFY — inject on change only**

### _19_skill_suggester.py
**What it does:** Suggests relevant skills based on context.
**Fights factory?** YES — stock A0's SkillsTool already handles skill discovery on-demand. A per-turn skill suggester adds overhead the model doesn't need.
**V1.12 status:** REMOVE. Let the model use SkillsTool to find skills when it needs them.
**Verdict: ❌ REDUNDANT — stock SkillsTool replaces this**

### _55_memory_relevance_filter.py
**What it does:** Filters recalled memories by relevance before injection.
**Fights factory?** NO — improves the quality of memory recall by reducing noise.
**V1.12 status:** KEEP. Review against v1.12's memory extensions — stock v1.x has improved memory consolidation.
**Verdict: ✅ KEEP (review against stock memory improvements)**

### _56_memory_enhancement.py
**What it does:** Enhanced memory recall with query expansion, temporal decay, co-retrieval logging.
**Fights factory?** NO — extends stock memory with novel capabilities.
**V1.12 status:** KEEP. This is genuinely novel. But review the injection size — if it's dumping 8+ memories per turn, the overhead may not be justified.
**Verdict: ✅ NOVEL — KEEP (review injection size)**

### _57_orchestration_mode.py
**What it does:** Sets orchestration mode based on task characteristics.
**Fights factory?** PARTIALLY — if it injects orchestration context per-turn, it's overhead.
**V1.12 status:** REVIEW. Likely candidate for demand-driven activation.
**Verdict: ⚠️ REVIEW**

### _58_ontology_query.py
**What it does:** Queries the ontology layer for entity relationships.
**Fights factory?** NO — novel capability (entity resolution + relationship graph). No stock equivalent.
**V1.12 status:** KEEP.
**Verdict: ✅ NOVEL — KEEP**

### _95_tiered_tool_injection.py
**What it does:** Injects tool descriptions in tiers based on relevance.
**Fights factory?** YES — stock A0 has tool descriptions in the base prompt. Adding tiered injection on top is redundant AND adds context overhead.
**V1.12 status:** REMOVE. Stock base prompt + SkillsTool handle tool/skill discovery.
**Verdict: ❌ FIGHTS FACTORY — REMOVE**

---

## TOOL_EXECUTE_BEFORE EXTENSIONS

### _16_py_write_guard.py
**What it does:** Mechanically blocks .py file writes.
**Fights factory?** NO — security boundary. No stock equivalent.
**V1.12 status:** KEEP. Essential for self-improvement loop safety.
**Verdict: ✅ NOVEL — KEEP**

---

## TOOL_EXECUTE_AFTER EXTENSIONS

### Evidence ledger / EI components
**What they do:** Track tool outputs for epistemic integrity verification.
**Fights factory?** NO — novel provenance tracking. No stock equivalent.
**V1.12 status:** KEEP.
**Verdict: ✅ NOVEL — KEEP**

---

## MONOLOGUE_END EXTENSIONS

### _52_selective_memorizer.py
**What it does:** Selectively stores memories based on classification criteria.
**Fights factory?** NO — extends stock memory with more sophisticated selection.
**V1.12 status:** KEEP. Review against v1.12's memory consolidation.
**Verdict: ✅ KEEP**

### _55_memory_classifier.py
**What it does:** Five-axis classification of memories (temporal, relational, utility, source, validity).
**Fights factory?** NO — novel capability. Stock memory has no classification system.
**V1.12 status:** KEEP.
**Verdict: ✅ NOVEL — KEEP**

### _57_memory_maintenance.py
**What it does:** Auto-deprecation, dormancy flagging, deduplication of memories.
**Fights factory?** PARTIALLY — stock v1.x has memory consolidation. May overlap.
**V1.12 status:** REVIEW against stock memory consolidation. Keep if ours is more sophisticated (five-axis classification + relationship-defining protection).
**Verdict: ⚠️ REVIEW — keep if more sophisticated than stock**

---

## SUMMARY: THE FACTORY COMPATIBILITY SCORECARD

### ❌ REMOVE (fights factory or redundant with v1.12):
| Extension | Hook | Why |
|-----------|------|-----|
| `_12_org_dispatcher` | before_main_llm_call | Stock Agent Profiles replace this |
| `_13_operator_profile` | before_main_llm_call | Convert to Agent Profile or session-start-only |
| `_14_metacognitive_injection` | before_main_llm_call | L7 overhead — inject on failure only, not per-turn |
| `_16_tool_registry` | before_main_llm_call | Stock base prompt has tool descriptions. Stock SkillsTool loads skills on-demand |
| `_19_context_pruner` | before_main_llm_call | Stock v1.3+ compaction plugin |
| `_09_context_pruner` | message_loop_prompts_after | Duplicate of above |
| `_16_tool_registry` | message_loop_prompts_after | Duplicate of above |
| `_19_skill_suggester` | message_loop_prompts_after | Stock SkillsTool |
| `_95_tiered_tool_injection` | message_loop_prompts_after | Stock base prompt handles tool descriptions |

**9 extensions to remove.** Estimated savings: ~600-800 tokens per turn of redundant injection.

### ⚠️ CONVERT TO DEMAND-DRIVEN:
| Extension | Hook | Change |
|-----------|------|--------|
| `_11_BST enrichment` | before_main_llm_call | Keep classification (always), enrichment only on failure |
| `_15_htn_plan_selector` | before_main_llm_call | Inject plans only on supervisor intervention |
| `_17_orchestration_gate` | before_main_llm_call | Delegation hints only for large-context tasks |
| `_14_situational_orientation` | before_main_llm_call | Session-start or demand-driven |
| `_18_memory_catalog` | message_loop_prompts_after | Inject on change only (delta-hash) |

**5 extensions to convert.** These are valuable concepts but wrong activation pattern.

### ⚠️ REVIEW BEFORE PORTING:
| Extension | Hook | What to Check |
|-----------|------|---------------|
| `_13_reasoning_state` | before_main_llm_call | Check against v1.12 reasoning tracking |
| `_14_pace_plan_generator` | before_main_llm_call | Check if per-turn or on-request |
| `_17_library_catalog` | before_main_llm_call | Likely redundant with SkillsTool |
| `_49_reasoning_state_update` | message_loop_end | Check against v1.12 |
| `_57_orchestration_mode` | message_loop_prompts_after | Likely demand-driven candidate |
| `_57_memory_maintenance` | monologue_end | Check against stock consolidation |

**6 extensions to review.** Need v1.12 source code comparison.

### ✅ KEEP (novel, no stock equivalent):
| Extension | Hook | Why Novel |
|-----------|------|-----------|
| `_01_backend_standby_gate` | before_main_llm_call | Infrastructure resilience |
| `_09_injection_gate` (simplified) | before_main_llm_call | Demand-driven activation logic |
| `_10_session_init` | before_main_llm_call | Session initialization |
| `_11_BST classification` | before_main_llm_call | Domain classification (no enrichment) |
| `_12_completion_tracker` | before_main_llm_call | Task state tracking |
| `_18_injection_budget` | before_main_llm_call | Instrumentation |
| `_20_context_watchdog` | before_main_llm_call | Safety monitoring |
| `_21_constraint_heartbeat` | before_main_llm_call | Behavioral guardrails + epistemic principles |
| `_60_sleep_activity` | before_main_llm_call | Idle-time processing |
| `_28_backend_standby` | message_loop_end | Infrastructure recovery |
| `_29_stuck_delivery` | message_loop_end | Failure recovery |
| `_48_task_tracker` | message_loop_end | Task management |
| `_50_supervisor_loop` | message_loop_end | Graduated intervention |
| `_55_memory_relevance_filter` | message_loop_prompts_after | Memory quality |
| `_56_memory_enhancement` | message_loop_prompts_after | Enhanced recall |
| `_58_ontology_query` | message_loop_prompts_after | Entity resolution |
| `_16_py_write_guard` | tool_execute_before | Security boundary |
| Evidence ledger / EI | tool_execute_after | Epistemic integrity |
| `_52_selective_memorizer` | monologue_end | Memory selection |
| `_55_memory_classifier` | monologue_end | Memory classification |

**20 extensions to keep.** These are genuinely novel capabilities that stock A0 doesn't have.

---

## THE MIGRATION PLAN

### Step 1: Stand up fresh v1.12 container
- Pull latest `agent0ai/agent-zero`
- Configure for Qwen3.6-27B via LM Studio
- Verify stock baseline (run OpenPlanter task, measure retries)

### Step 2: Port the KEEP extensions first
- Start with safety-critical: watchdog, PyWrite Guard, heartbeat
- Then infrastructure: backend standby, stuck delivery
- Then capability: BST classification (without enrichment), EI layer, memory enhancements

### Step 3: Verify each ported extension doesn't degrade baseline
- After each extension is added, run the standardized test task
- If tried= increases, the extension is causing problems
- If tried= stays at 1, the extension is compatible

### Step 4: Add demand-driven extensions
- BST enrichment (fire only on instability)
- HTN plans (fire only on supervisor intervention)
- Orchestration hints (fire only on large-context tasks)

### Step 5: Do NOT port the REMOVE extensions
- Tool registry, context pruner, skill injection, org dispatcher, operator profile per-turn, tiered tool injection, skill suggester
- These are all handled better by v1.12's factory design

### Step 6: Verify the complete stack
- Run OpenPlanter stress test
- Run context endurance test (30+ turns)
- Run self-improvement loop
- Compare against stock baseline

---

## Token Budget Comparison

| State | Estimated Per-Turn Injection |
|-------|----------------------------|
| Current Exocortex on v0.9 | ~900-1000 tokens |
| v1.12 stock (no Exocortex) | ~0 tokens (tools in base prompt) |
| v1.12 + novel extensions (KEEP list) | ~200-300 tokens estimated |
| v1.12 + novel + demand-driven (when active) | ~400-500 tokens on failure turns |

The reduction from ~1000 to ~200-300 tokens per turn represents a 70-80% decrease in injection overhead. On a 100k context window, that's the difference between 85k available for content after 15 turns and 96k available.
