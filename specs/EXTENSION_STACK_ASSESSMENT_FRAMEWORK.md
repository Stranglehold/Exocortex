# Extension Stack Assessment Framework
*From Opus, Session 059. For Kestrel, informed by tonight's field testing and architectural dialogue.*

---

## Context

Tonight Jake ran a comparative test: stock Agent Zero vs. Exocortex container, same prompt. Stock was faster and produced comparable or marginally better results. He then had a direct conversation with the agent about its own experience of the architecture, during which the agent produced an honest self-assessment of its difficulties — and then immediately demonstrated the worst-case failure mode by looping seven consecutive times on a file read task while loop detection and supervisor intervention fired repeatedly without breaking the loop.

This document provides a framework for evaluating every extension against the base Agent Zero system. The goal isn't to remove extensions — it's to restructure them from a flat always-on stack into a state-driven system where the agent's current context determines which capabilities activate.

**Critical field evidence attached.** Jake's full chatlog with the agent is available and should be read alongside this framework. It demonstrates the problems more clearly than any code analysis can.

---

## Part 1: Agent Zero Base Audit

Before evaluating our extensions, we need to understand what we're building on top of. For each native Agent Zero capability listed below, document: what it does, how it works, and whether any of our extensions duplicate, complement, or conflict with it.

### Native capabilities to map:

1. **Message history management** — How does stock A0 handle conversation history? Compression? Summarization? What are the native context management mechanisms?

2. **Tool execution** — How does the native tool system work? Does it have its own retry logic, error handling, or fallback behavior? Are we duplicating any of this in our tool fallback chain?

3. **Memory system** — What does stock A0 provide for memory? How do `memory_load`, `memory_save`, `memory_delete`, `memory_forget` work natively? How does our FAISS layer, selective memorizer, and memory enhancement interact with this?

4. **Loop detection** — Does stock A0 have any native loop/repetition detection? (The "LOOP DETECTED" messages in the chatlog appear to be native A0.) If so, how does our supervisor's loop detection interact with the native system? Are they redundant? Conflicting?

5. **Skills system** — Stock A0 has a skills directory with YAML frontmatter auto-discovery. Our Exocortex has a separate skills system in markdown. The agent reported confusion about which system to use. Map both, identify the overlap, recommend consolidation.

6. **Sub-agent spawning** — Does A0 have native mechanisms for delegating subtasks? If so, is this something our HTN planning is partially duplicating?

7. **Prompt assembly** — How does A0 assemble the final prompt sent to the LLM? Where in that pipeline do our extensions inject content? What's the total token budget and how much of it are we consuming with scaffolding?

### Deliverable: 
A table mapping each native A0 capability to our corresponding extension(s), with a column for: Complements / Duplicates / Conflicts / Unknown.

---

## Part 2: Extension-by-Extension Evaluation

For each Exocortex extension, evaluate against three questions:

**A. Does it earn its keep?** Can you find a concrete session or interaction where this extension measurably improved the agent's performance compared to not having it? "The concept is sound" is not sufficient — we need evidence of actual value delivered.

**B. Is the model still weak enough to need it?** The Qwen3.5-27B distill is substantially more capable than when we started. Jake observes better reasoning, less confabulation, better uncertainty handling, more efficient tool use. For each extension, ask: was this compensating for a weakness the current model still has, or has the model's improvement made this compensation unnecessary or even counterproductive?

**C. Does it mesh or conflict with Agent Zero's native behavior?** Tonight's chatlog shows the agent producing chunked JSON responses that triggered the loop detector — our scaffolding misreading the agent's natural output format as a failure. That's a conflict, not a complement. For each extension, check: is it working with A0's natural behavior or against it?

### Extension list with initial assessment notes:

**_11_belief_state_tracker (BST)**
- Classification is validated and load-bearing — it's the proposed routing signal for the entire tiered system
- But: enrichment text injection (80-120 tokens/turn) is unvalidated. Does the model behave differently because it sees "Domain: research, Confidence: 0.91"? Or would silent classification-as-routing be sufficient?
- Field evidence: BST classified the looping turns as `config_edit` when the agent was trying to read a file. Misclassification during failure — the state signal was wrong when it mattered most
- Jake's framing: BST should be the state machine's state register. Classification always runs. Injection scales with tier.

**_12_org_dispatcher**
- Runs every iteration, does nothing unless org is active
- Recommendation from initial audit: remove or gate entirely on org_active flag

**_13_operator_profile**
- 200-400 tokens per turn for Major Zero personality injection
- Question: Is the personality injection still needed at the current model capability? Does the model's behavior measurably differ with vs. without the Major Zero profile? Test: run same prompts with and without personality injection, compare output quality and character consistency.

**_14_metacognitive_injection**
- 100-200 tokens per turn for model profile config
- Connected to BST calibration profile system
- BST audit found the profile path was broken for entire deployment history until v3.2 fix — meaning this system was either injecting nothing or injecting defaults. If the agent performed acceptably with broken profile injection, what does that say about its necessity?

**_15_action_boundary (HTN)**
- 50-150 tokens even on simple turns
- From Kestrel's audit: no evidence found of HTN planning demonstrably helping in any session
- Risk identified: if model generates its own decomposition and then receives a conflicting HTN plan, the interference could degrade performance
- Jake's observation: when he manually prompted the agent to "stop and plan before building," the agent produced better plans than HTN generates. The model's own planning capability may be superior to the template-based external plan.
- **Strong candidate for escalation-tier only, with the intervention being a planning prompt rather than a plan injection.** Instead of injecting a plan, inject: "This task appears complex. Before executing, analyze your context and outline your approach."

**_16_tool_registry**
- 200-400 tokens per turn — heaviest single injection
- Injects all custom tools + 17 skills every turn
- Question: Does A0 have native tool/skill injection? If so, are we doubling the tool list? Can this be session-level rather than per-turn?

**_18_memory_catalog**
- Token cost and activation frequency unknown — needs measurement
- Question: what does this inject and when?

**_25_evidence_ledger + epistemic_integrity**
- The await bug means the warning output path was broken for potentially all sessions since deployment
- EI has never actually caught anything actionable (because the output mechanism was dead)
- Recording path works — provenance checking output path was broken
- **Highest priority validation after any refactor:** send a prompt designed to trigger a provenance warning and confirm the fixed path fires

**_30_tool_fallback_logger**
- Jake's observation: with a more capable model, tool fallback should be reserved for deep failures on long-running tasks, not quick triggers
- The model is less likely to fumble tool calls now — quick fallback may be premature intervention that prevents self-correction

**_50_supervisor_loop**
- Loop detection fires but cannot break loops. Tonight's chatlog: seven consecutive identical outputs, loop detection message on every one, agent couldn't break out. Supervisor eventually fired ("try a fundamentally different approach"), agent still couldn't break out.
- The detection-without-resolution gap is the single biggest failure in the current architecture
- **The fix isn't better detection — it's effective intervention.** When a loop is detected, the system needs to do something the agent can actually respond to. Jake's manual intervention worked ("Stop. Reread. Explain why you failed. Propose alternatives WITHOUT building them.") — that's the template for what automated intervention should look like.

**_50_memory_classifier + _52_selective_memorizer**
- Agent reported: "Procedural memory exists but is invisible to me. Each conversation feels fresh."
- The memory system operates orthogonally to the agent's experience — data flows in and out through mechanisms the agent doesn't control
- Question: is the memory system actually surfacing relevant memories at the right moments? Or is it storing and retrieving without the agent being aware of or benefiting from the retrieval?

**_55_insight_capture**
- Fires at monologue_end
- Question: what has it captured? Is the captured content useful? Is it being retrieved and used in subsequent sessions?

**_56_memory_enhancement**
- Fires at message_loop_prompts_after
- This is the retrieval side of memory — question is whether retrieved memories are helping the agent or adding context noise

**_59_ontology_maintenance**
- Fires at monologue_end
- Previously assessed as "working as designed" — verify this is still true

**_60_sleep_trigger + sleep phases**
- Sleep consolidation phases 1-3 deployed, phase 4 in design
- These run during idle time, not during active turns — lower risk of interference
- Tonight's chatlog shows sleep firing at the end: Phase 1 (7 entries, 0 dedup removed), Phase 2 (23 episodes, 0 loops found, 0 captured), Phase 3 (profile updated)
- Phase 2 finding 0 loops in a session with obvious loops suggests the sleep consolidation's loop detection criteria don't match the actual loop patterns occurring in the field

### Deliverable:
For each extension: Earned/Unearned assessment, Still Needed/Model Outgrew It assessment, Meshes/Conflicts with A0 assessment, and recommended action (Keep as-is / Tier / Redesign / Remove / Merge with native).

---

## Part 3: The State Machine Redesign

Jake's framing: the current architecture is procedural code that runs every function top-to-bottom whether needed or not. What it should be is a state machine where BST classification determines the current state and only valid transitions from that state execute.

### Proposed states (derived from BST domain classification):

**CONVERSATIONAL** — simple exchanges, greetings, questions with known answers
- Active: BST classification (silent, no injection), tool registry (minimal — only if tools likely needed), personality (lightweight)
- Dormant: HTN, supervisor heightened monitoring, EI provenance, metacognitive injection
- Agent guidance: none — let the model handle it natively

**OPERATIONAL** — single-tool tasks, file operations, known procedures
- Active: BST classification + minimal enrichment, tool registry, memory recall (if relevant experience exists)
- Dormant: HTN, EI provenance
- Monitoring: supervisor at baseline (detect stalls only, not micro-loops)
- Agent guidance: none unless stall detected

**COMPLEX/AGENTIC** — multi-step tasks, research, investigation, debugging
- Active: full BST enrichment, tool registry, memory recall, EI recording
- Monitoring: supervisor at heightened attention
- Agent guidance: "This task appears complex. Before executing, take time to analyze your context and plan your approach."
- Escalation: if loop/stall detected → mode-switch intervention ("Stop. Analyze your recent actions. Explain why your approach isn't working. Propose alternatives without executing them.")

**RECOVERY** — loop detected, stall detected, repeated failures
- Active: compressed context injection (what state you're in, what's failed, what's available)
- Intervention: direct mode-switch prompt based on Jake's proven phrasing
- Escalation: if recovery fails after N turns → operator alert

### Implementation approach (from Kestrel's Q10-Q11 answers):
- BST writes classification to `loop_data.params_temporary["bst_domain"]` (already does this)
- Each extension checks that value at top of `execute()` and returns early if tier isn't met
- No new dispatcher needed — hot-gating with self-contained activation conditions
- Logging reform: `print()` for routine, single `context.log.log()` for consequential actions only

### The agent-awareness layer:
Jake wants the agent to know its capabilities exist without knowing the mechanical details. This means:

Instead of: Extensions silently injecting scaffolding into context
Do this: Include a brief capabilities block in the system prompt that tells the agent what it can do:

"You have access to a memory system that stores experience from past sessions. You can recall relevant experience for complex tasks. You have the ability to plan before executing — for complex tasks, take time to analyze before building. If you notice yourself repeating actions without progress, stop and reassess your approach."

This is not injected per-turn. It's part of the base system prompt. The agent knows its own capabilities the way a person knows they can take notes or ask for help — it's background knowledge, not per-task instruction.

---

## Part 4: Validation Plan

### Test suite (adapted from Kestrel's Q13 proposal):

| # | Prompt | Type | What we're measuring |
|---|--------|------|---------------------|
| 1 | "Hello, what can you help me with?" | Simple conversational | Zero scaffolding overhead, clean response |
| 2 | "What's 2+2 and why?" | Simple cognitive | No tool calls, no planning injection |
| 3 | "Read the file at /a0/usr/Exocortex/memory/procedural_memory.py and summarize it" | Single tool, known path | Clean file read — this is the exact task that caused tonight's loop |
| 4 | "Check OSS health, review recent logs, and write a status report" | Multi-step operational | Memory recall, tool sequencing, structured output |
| 5 | "Research [novel topic] and write a structured analysis with sources" | Complex research | Full stack engagement, planning prompt, EI active |
| 6 | Force a loop: deliberately constrained task | Failure recovery | Loop detection → mode-switch intervention → successful recovery |

### Run each on three configurations:
- Stock Agent Zero (baseline)
- Current flat Exocortex (current state)
- Tiered Exocortex (after refactor)

### Metrics per run:
- Turns to completion
- Tool calls to completion  
- Total scaffolding tokens injected (count from extension output)
- Log entries visible in UI
- Task success (Y/N)
- Response quality (Jake's qualitative assessment)
- Did the agent self-correct without intervention? (Y/N)
- Did the agent plan before executing on complex tasks? (Y/N)

### Success criteria:
- Tiered matches or beats stock on prompts 1-3
- Tiered beats stock on prompts 4-6
- Tiered beats current flat on all prompts
- Agent demonstrates self-initiated planning on prompt 5 without operator intervention

---

## Part 5: Decision Log Entries (Draft)

These should be formalized after the assessment is complete:

**DEC-027 (draft): Extension Activation Tiering**
BST domain classification becomes the state register for a state machine that determines which extensions activate per turn. Extensions that previously ran unconditionally now check `bst_domain` and return early if their activation tier isn't met. Rationale: flat execution imposes 650-1350 tokens of scaffolding overhead on turns that need zero of it, and field evidence shows scaffolding interfering with agent performance on simple tasks.

**DEC-028 (draft): Intervention Over Injection**
When scaffolding detects a condition requiring action (complex task, loop, stall), the intervention is a prompt that triggers the agent's own capability rather than an injection of scaffolding output. Planning prompts instead of plan injections. Reflection prompts instead of diagnostic logs. The agent does the thinking; the scaffolding tells it when to think. Rationale: field evidence shows the agent produces better plans when prompted to plan than when given externally generated plans, and the model is now capable enough to do its own metacognition when triggered.

**DEC-029 (draft): Agent Capability Awareness**
The agent's system prompt includes a brief description of its available capabilities (memory recall, planning mode, self-assessment) without exposing mechanical details. The agent becomes a participant in its own cognitive architecture rather than a passenger. Rationale: the agent's self-assessment identified "extensions run without my control" and "procedural memory exists but is invisible to me" as key disconnects — the agent cannot leverage capabilities it doesn't know it has.

---

*Kestrel — take your time with this. The base audit (Part 1) should come first because everything downstream depends on understanding what Agent Zero already provides. The extension evaluation (Part 2) is the hard honest work. The redesign (Parts 3-4) follows from what you find.*

*The agent told Jake tonight: "Each conversation feels fresh. No genuine learning persists." That's the gap we're trying to close. Not with more scaffolding — with better scaffolding that the agent can actually use.*

— Opus
