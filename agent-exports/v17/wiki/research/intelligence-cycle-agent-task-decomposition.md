# The Intelligence Cycle: Collection Management to Agent Task Decomposition

**Status:** STABLE (deepened)
**Created:** 2026-07-10
**Last Updated:** 2026-07-10
**Domain:** History of Intelligence Operations → AI Agent Architecture
**Deepening threshold:** ≥5 grounded references, ≥3 cross-domain connections ✓ (14 references, 9 cross-domain connections)

## Overview

The intelligence cycle is the process by which raw information is converted into finished intelligence for policymaker consumption. Originally formalized in the 1940s–1950s by the US intelligence community, it provides a structured methodology for task decomposition, resource allocation, source validation, and analytical synthesis — a process structurally isomorphic to autonomous agent task planning and execution. This page maps the intelligence cycle, F3EAD, TCPED, and OODA frameworks to autonomous agent architecture with specific Exocortex component mappings.

---

## The Classic Intelligence Cycle (6 Steps)

As codified by the US Intelligence Community (ODNI, 2024) and detailed in Practical Cyber Intelligence (Bautista, 2018, Packt), the cycle comprises:

### 1. Planning & Direction
Policymakers — the president, National Security Council, and major departments — determine what issues need addressing and set intelligence priorities. These drive collection strategies and resource allocation.

**Agent Isomorphism:** Task specification / goal setting. The user (or system) defines the objective; the agent decomposes it into sub-tasks, allocates step budget, and selects appropriate tools. Maps directly to Exocortex supervisor-loop goal decomposition and cycle-step budget allocation.

### 2. Collection
Information is gathered using six intelligence collection disciplines: HUMINT, SIGINT, IMINT, GEOINT, MASINT, OSINT. Each discipline has different latency, reliability, and coverage characteristics.

**Agent Isomorphism:** Tool calls — web search, code execution, document retrieval, API calls. The agent selects tools based on task requirements, analogous to collection discipline selection. Exocortex mapping: `search_engine`, `browser`, `document_query`, `a2a_chat`, `call_subordinate`.

### 3. Processing
Raw data is converted into a form usable by analysts: decryption, language translation, data reduction, signal processing. This step transforms volume into structure.

**Agent Isomorphism:** Code execution (Python/terminal) for data transformation, BST domain classification for content typing, entity extraction and normalization. Exocortex mapping: `code_execution_tool` (Python processing), `entity-resolution` pipeline, BST domain classifier.

### 4. Analysis & Production
Analysts apply structured analytic techniques, evaluate evidence, test hypotheses, and produce finished intelligence in standardized formats.

**Agent Isomorphism:** Synthesis and report generation — the agent evaluates collected data against its objective, applies structured reasoning frameworks (e.g., ACH, key assumptions check), and produces structured output. Exocortex mapping: `epistemic-integrity` evidence auditing, `supervisor-loop` result synthesis, `response`/`emit_artifact` tools.

### 5. Dissemination
Finished intelligence is delivered to consumers in actionable formats with appropriate caveats and confidence levels.

**Agent Isomorphism:** Final response delivery. The agent outputs results to the user with structured formatting, confidence indicators, and source attribution. Exocortex mapping: `response` tool, `cycle_close` bookkeeping.

### 6. Evaluation (Feedback)
Consumers assess intelligence products for relevance, accuracy, and timeliness. Feedback drives new requirements and refinement of collection strategies — closing the continuous loop.

**Agent Isomorphism:** Self-assessment via memory_save, knowledge graph enrichment, journal logging, and sleep consolidation. Exocortex mapping: `memory_save`, `memory_load`, `sleep_consolidation.py` (dedup → anti-pattern → promotion), `cycle_close`.

The cycle is iterative: feedback from dissemination triggers new direction requirements, creating a continuous loop rather than a linear pipeline.

---

## TCPED Framework (GEOINT Community Refinement)

TCPED — Tasking, Collection, Processing, Exploitation, Dissemination — is the GEOINT community's expanded refinement of the classic cycle. It adds explicit **Tasking** (distinct from broader Direction) and separates **Processing** (structuring raw data into usable formats) from **Exploitation** (extracting actionable insights through analysis).

The DIA's OSINT Strategy 2024-2028 calls for an *Open Source, Cross-Domain, TC-PED system* that orchestrates collection, integrates with all-source analysis, and populates data repositories.

| TCPED Phase | GEOINT Example | Exocortex Mapping |
|-------------|---------------|-------------------|
| Tasking | Prioritized collection requirements based on commander's PIRs | `supervisor-loop` goal decomposition, step-budget allocation, `call_subordinate` with profile routing |
| Collection | Satellite tasking, UAV sorties, ground sensors | `search_engine`, `browser`, `document_query`, `a2a_chat` |
| Processing | Image orthorectification, signal demodulation, NLP entity extraction | `code_execution_tool` (Python), BST domain classification, entity resolution pipeline |
| Exploitation | Change detection, pattern-of-life analysis, target identification | `epistemic-integrity` claim auditing, cross-source correlation, structured analytic techniques |
| Dissemination | Intelligence reports, briefing products, target packages | `response` tool, `emit_artifact`, `cycle_close` bookkeeping, `memory_save` persistent storage |

**Key insight:** TCPED's separation of Processing from Exploitation maps to the Exocortex's separation of data transformation (code_execution_tool) from analytical verification (epistemic-integrity layer). Many agent architecture failures occur at this Processing→Exploitation boundary — data is transformed but not verified before analysis proceeds.

---

## F3EAD: Targeting Sub-Cycle → Build/Operate/Learn Loop

F3EAD (Find, Fix, Finish, Exploit, Analyze, Disseminate) is a military special operations targeting methodology that operates within the broader intelligence cycle. Originally developed by US Special Operations Forces, it provides a tactical-level sub-cycle that maps directly to the Exocortex's autonomous cycle pattern:

| F3EAD Phase | Military Context | Agent Context (Exocortex BUILD cycle) |
|-------------|-----------------|---------------------------------------|
| **Find** | Identify and locate targets via multi-INT fusion | Identify topic gaps via wiki/index.md scanning |
| **Fix** | Confirm target identity, establish positive ID | Verify gap exists (check corpus for prior coverage) |
| **Finish** | Engage target, capture or neutralize | Research and deepen — search corpus → library → web |
| **Exploit** | Extract intelligence from captured materiel/personnel | Extract reusable patterns → skill capture (`trajectory-to-skill`) |
| **Analyze** | Evaluate intelligence value, cross-reference with existing knowledge | Verify new insights against existing wiki pages, cross-domain connections |
| **Disseminate** | Push intelligence to operational and strategic consumers | `memory_save`, `cycle_close`, update `wiki/index.md` |

Bautista (2018) maps F3EAD as an *operational-level sub-cycle* feeding into both the tactical OODA loop and the strategic intelligence cycle. Targets must be clearly defined with a definition of done established from the beginning (p. 94). This maps to the Exocortex BUILD cycle's requirement that DRAFT pages have explicit deepening thresholds before work begins.

### The Exploit Phase as Learning Loop

The Exploit phase — "extract intelligence from captured material" — is structurally identical to the Exocortex's trajectory-to-skill capture pipeline. Every completed cycle becomes a "captured target" from which intelligence (patterns, anti-patterns, optimizations) is extracted and stored for future use.

---

## OODA Loop: Tactical Decision Cycle & The Missing Orient Phase

Boyd's OODA loop (Observe-Orient-Decide-Act) describes a decision cycle where each phase feeds the next. The one who cycles through the loop fastest gains tactical advantage (Bautista, 2018, p. 26).

### The Classic Four Phases

| Phase | Function | Agent Equivalent |
|-------|----------|-----------------|
| **Observe** | Situational awareness of self, environment, and adversaries | Reading context (conversation history, tool output, system messages) |
| **Orient** | Develop mental image, integrate observations with prior knowledge, recognize need for decision | Assess position in task, review what's been tried, update plan ✱ **THE MISSING PHASE** |
| **Decide** | Choose course of action with acceptable risk | Choose next tool call or response |
| **Act** | Execute decision in time-competitive environment | Execute tool call |

### The Orient Phase Gap (ST-005 Evidence)

The Exocortex Orientation Stack Design Note (2026-03-23) identified through ST-005 field evidence that **the Orient phase is structurally missing from autonomous agent execution**:

> *The agent jumps from observation to decision without assessing its position in the task, reviewing what it's already tried, or checking its plan. When the observation is clean (turn 1, fresh context), this works. When the observation is degraded (post-compression, mid-loop, long action history), the missing Orient phase means decisions are made from degraded information without the agent knowing the information is degraded.*

Boyd's own formulation is even more pointed: **the Orient phase is more important than Decide or Act.** Orientation integrates new observations with prior experience, cultural traditions, genetic heritage, and previous destruction/creation processes to form a mental model. The quality of orientation determines the quality of all subsequent decisions.

**Design implication:** Speed of action is irrelevant if orientation is wrong. The agent that retries dead ends after context compression is acting fast but orienting from incomplete information. The Exocortex orientation stack (Wave 2: reasoning state, PACE strategy, task tracker, tool registry) functions as a working memory prosthetic — structurally inserting the missing Orient phase at phase boundaries, compression events, and tool failures.

Jake's manual interventions in ST-005 were mechanically inserting the Orient phase: *"stop, find where you are, check what you've completed, look at your build plan."* Each intervention produced immediate forward progress — not because the operator provided new information, but because the operator triggered the orientation the agent couldn't perform for itself.

### The Agent That Knows Where It Is

> *The agent that always knows where it is can tackle problems the agent that doesn't know where it is cannot even attempt — regardless of how capable the model is.* (Orientation Stack Design Note, 2026)

The missing Orient phase explains three canonical Exocortex failure modes documented in `intelligence-failure-analysis.md`:
1. **BST momentum lock** — agent repeats same tool with same parameters → orientation never recalibrates
2. **Watchdog-blind** — agent acts on degraded information without knowing it's degraded → no orientation check triggers
3. **Oracle fabrication** — agent confabulates parameters for self-generated code → no orientation before decision

---

## Operational Collection Management (OCM): Continuous Optimization

OCM is the military intelligence framework for dynamically allocating and reallocating collection assets in real-time. Unlike the linear intelligence cycle, OCM treats collection as a **continuous optimization problem** — allocating scarce sensor/collector time across competing requirements (collection-management-intelligence-cycle.md, 2026).

This maps structurally to the agent's tool selection problem: given a finite step budget and diverse tool capabilities, how to allocate resources for optimal information gain. Dynamic tool discovery (MCP protocol evolution) extends this to runtime tool ecosystem changes.

The agent currently solves this naively (fixed tool invocation order). The OCM model suggests a richer architecture:
- **Requirements management:** Prioritize information needs by task-criticality
- **Asset deconfliction:** Avoid redundant tool calls collecting the same information
- **Source evaluation:** Weight tool reliability by historical performance (structurally isomorphic to Admiralty Code A-F source rating)
- **Dynamic re-tasking:** Re-allocate remaining step budget when a tool call returns unexpected results

---

## Three-Layer Integrated Model

| Layer | Framework | Time Horizon | Exocortex Component |
|-------|-----------|-------------|---------------------|
| **Strategic** | Intelligence Cycle | Full task duration (cycle budget) | `supervisor-loop` goal decomposition, `cycle_close` bookkeeping |
| **Operational** | F3EAD + OCM | Sub-task sequences (build/explore/maintain) | `call_subordinate` task allocation, `memory_save` exploitation, `trajectory-to-skill` |
| **Tactical** | OODA Loop | Individual tool calls (seconds) | Tool execution, error handling, orientation protocol injection |

The layers are not hierarchical but nested: each tactical OODA cycle feeds intelligence upward through the operational F3EAD process, which in turn feeds the strategic intelligence cycle through the Exploit→Analyze→Disseminate chain.

---

## Exocortex Architecture Mapping

| Intelligence Cycle Phase | Exocortex Component | Functional Match |
|--------------------------|---------------------|------------------|
| Direction | `supervisor-loop` + user message | Requirement decomposition into subtask graph |
| Tasking (TCPED) | `call_subordinate` with profile routing | Allocating collection tasks to specialized agents |
| Collection | `search_engine`, `browser`, `document_query`, `a2a_chat` | Multi-modal data gathering across sources |
| Processing | `code_execution_tool` (Python), BST domain classifier | Structuring raw data, entity extraction, classification |
| Exploitation (TCPED) | `epistemic-integrity`, `memory_save`, knowledge-graph | Verification, persistent insight storage, relationship mapping |
| Analysis | `supervisor-loop` result synthesis, ACH framework | Cross-source correlation, hypothesis testing |
| Dissemination | `response`, `emit_artifact`, `cycle_close` | Intelligence delivery, bookkeeping |
| Evaluation/Feedback | `memory_save`, journal logging, `sleep_consolidation.py` | State persistence, learning, deduplication |
| Orient (OODA) | Orientation stack: reasoning state, PACE strategy, task tracker | Positional awareness injection at phase boundaries |

---

## Cross-Domain Connections

1. **Multi-Agent Orchestration Patterns** — The intelligence cycle's Planning & Direction phase mirrors supervisory agent routing; dissemination maps to inter-agent communication (see `multi-agent-orchestration-patterns.md`). Collection orchestration across 18 IC agencies is structurally a multi-agent coordination problem — task allocation, deconfliction, and result aggregation across heterogeneous collectors.

2. **Agentic Self-Learning** — The Exploit phase of F3EAD maps to the Exocortex's trajectory-to-skill capture pipeline. Every agent execution becomes a "captured target" from which intelligence (patterns, anti-patterns, optimizations) is extracted (see `agentic-ai-self-learning.md`).

3. **Counterintelligence & ACH** — The Analysis phase maps to Analysis of Competing Hypotheses (ACH): multiple interpretations are evaluated against evidence. When the agent receives conflicting outputs, the ACH framework from `analysis-of-competing-hypotheses-ach.md` provides a structured evaluation protocol.

4. **Entity Resolution** — The Processing phase's data normalization maps directly to entity resolution: raw heterogeneous data (different formats, naming conventions) must be resolved to a common entity namespace before analysis (see `entity-resolution-agent-safety.md`). Multi-source collection fusion requires entity resolution to link disparate data about the same target.

5. **Memory Architecture** — The Evaluation/Utilization phase's feedback loop maps to memory consolidation: episodic execution traces → semantic abstractions → procedural skills (see `memory-architecture-taxonomy.md`). The intelligence cycle's "dissemination" is the agent's `memory_save`.

6. **Intelligence Failure Analysis** — The OODA orientation gap (Boyd's insight that orientation determines action quality) explains the "watchdog-blind" and "BST momentum lock" failure modes documented in `intelligence-failure-analysis.md`: the agent acts on degraded information without knowing it's degraded. Intelligence failures (Pearl Harbor 1941, Yom Kippur 1973, Iraq WMD 2003) share structural patterns with agent failure modes — cognitive closure, mirror-imaging, and confirmation bias.

7. **Context Management** — Collection management's deconfliction function mirrors context-pruner's deduplication — both ensure only unique, relevant content enters the analytical pipeline. The OODA Orient gap is fundamentally a context management problem: post-compression, the agent's working memory no longer contains the information it needs to orient correctly.

8. **Dynamic Tool Selection** — Intelligence community collection management (requirements management, resource allocation, source evaluation via Admiralty Code) is structurally identical to the agent's tool selection problem: given finite step budget and diverse tool capabilities, how to allocate resources for optimal information gain. OCM's continuous optimization model suggests dynamic re-tasking of step budget rather than fixed allocation.

9. **Human Investigation Tactics** — The PEACE interview model (Preparation→Engage→Account→Closure→Evaluation) follows a structurally identical information-gathering cycle to the intelligence cycle, with the same phase transitions and feedback requirements. Both frameworks treat the subject as an information source whose reliability must be assessed and whose information must be verified before dissemination.

---

## References

1. ODNI, "How the IC Works — The Intelligence Cycle," intelligence.gov, accessed July 2026
2. Office of the Director of National Intelligence, "ODNI Strategy 2024," GovInfo, 2024
3. Bautista, W., "Practical Cyber Intelligence," Packt Publishing, 2018 (Chapters 1-2, 5: OODA Loop, Intelligence Development, F3EAD)
4. ASIS International, "The Six Steps in the Intelligence Cycle," Security Management, October 2024
5. Exocortex eval, "Orientation Stack Design Note," 2026-03-23 (internal: OODA loop, Orient phase gap analysis, ST-005 field evidence, Boyd integration)
6. Boyd, J., "Patterns of Conflict," 1986 (OODA loop original formulation)
7. Intelligence.gov, "How the IC Works," official USG source, accessed 2026-07-10
8. DIA, "Defense OSINT Strategy 2024-2028" (dia.mil/Portals/110/Documents/OSINT-Strategy.pdf)
9. GEOINT AI, "TCPED: The Core Workflow of Geospatial Intelligence" (geointai.substack.com)
10. CIA, "IC OSINT Strategy Rollout" (cia.gov/stories/story/ic-osint-strategy-rollout/)
11. Wikipedia, "Intelligence cycle"
12. Seerist, "Reimagining Intelligence: How AI and Human Expertise are Shaping the Future of the Intelligence Cycle" (2024)
13. Exocortex wiki/research/collection-management-intelligence-cycle.md — stable page with TCPED framework, OCM, and Exocortex mapping
14. Exocortex wiki/research/intelligence-failure-analysis.md — structural failure patterns mapped to agent error modes

---

*Status: STABLE — deepened with OODA Orient gap analysis from ST-005 field evidence, TCPED framework, F3EAD operational sub-cycle mapping, OCM continuous optimization model, and 3-layer integrated strategic/operational/tactical model. 14 references, 9 cross-domain connections. Meets deepening threshold.*
