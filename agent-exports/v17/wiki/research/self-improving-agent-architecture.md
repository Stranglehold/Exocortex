# Self-Improving Agent Architecture

**Status: STABLE**
**Last Updated: 2026-06-01**
**Sources: 13 arXiv papers + Paper2Code (2504.17192) + MUSE AutoSkill (ByteDance 2026) + Curve Labs Self-Challenge (2026)**

## Overview

Self-improving agent architecture synthesizes three capability domains: autonomous learning from experience (self-improving agents), automated creation of new tools and skills (recursive skill generation), and persistent knowledge accumulation (memory systems). This page consolidates findings from 10 arXiv papers and the Paper2Code framework to propose a unified architecture for Exocortex autonomous capability growth.

## 1. Self-Improving Agent Frameworks

### 1.1 ASL: Agentic Self-Learning (arXiv:2510.14253v2, 2025)
Closed-loop multi-role RL framework where Prompt Generator, Policy Model, and Generative Reward Model co-evolve. The reward model trains on the evolving data distribution to prevent reward hacking, enabling steady round-over-round improvement under zero-labeled-data conditions.

**Exocortex relevance**: Provides the bootstrapping loop — agent generates harder tasks, solves them, and sharpens its own verification without human annotation. Maps to FIELD research → BUILD cycle pattern.

### 1.2 ERL: Experiential Reflective Learning (arXiv:2603.24639v2, 2026)
Reflects on single-attempt task trajectories to extract transferable heuristics, then retrieves relevant heuristics at test time. +7.8% on Gaia2 over ReAct baselines with minimal implementation complexity.

**Exocortex relevance**: Lightweight self-improvement requiring no model fine-tuning — just reflect on what worked/failed and store lessons as retrievable heuristics. Directly implementable for skill library management. Already partially implemented via self-improvement journal and sleep consolidation.

### 1.3 SAMULE: Multi-Level Reflection (arXiv:2509.20562v1, 2025)
Synthesizes reflections at three granularities: micro (single-trajectory error correction), meso (error taxonomies across trials), and macro (transferable insights across diverse tasks). Fine-tunes a retrospective LM to generate structured reflections.

**Exocortex relevance**: The taxonomy maps to Exocortex layers: micro → error comprehension layer, meso → incident wiki pages, macro → concept wiki pages. Multi-level reflection ensures both task-specific fixes and cross-task principles are captured.

## 2. Recursive Skill Creation

### 2.1 Trace2Skill (arXiv:2603.25158v4, 2026)
Dispatches parallel sub-agents to analyze diverse execution pools, extracts trajectory-specific lessons, and hierarchically consolidates them into a unified skill directory. Skills transfer across LLM scales (+57.65 points on WikiTableQuestions when Qwen-35B → Qwen-122B).

**Exocortex relevance**: The hierarchical consolidation pattern matches Exocortex skill creation pipeline: field reports → wiki pages → SKILL.md files. Trace2Skill adds automated conflict resolution and cross-scale transfer verification.

### 2.2 SEVerA: Safety-Verified Self-Generated Agent Programs (2026)
Formal verification of self-generated agent programs — the only paper addressing the existential risk of an agent creating broken or dangerous skills.

**Exocortex relevance**: Critical for long-running autonomous systems. Exocortex should implement skill verification gates before activating self-generated skills.

### 2.3 Paper2Code (arXiv:2504.17192v5, 2026)
Multi-agent LLM framework transforming ML papers into operational code repositories. Three-stage pipeline: Planning (overall plan, architecture design, logic design, configuration file), Analysis (file-level specifications), Coding (sequential dependency-aware code generation). 88% rated best over baselines, 92% of human judges found repositories helpful. Only 0.81% of code lines require modification for executability.

**Exocortex relevance**: Directly applicable — Exocortex research wiki pages already contain structured knowledge; Paper2Code pattern can convert wiki pages into executable tools/skills automatically. Architecture design phase (class diagrams, sequence diagrams) would improve generated skill quality. Self-Refine on planning/analysis boosts downstream code quality.

## 3. Memory Systems for Autonomous Agents

### 3.1 Memory-R2: Fair Credit Assignment (arXiv:2605.21768v1, 2026)
LoGo-GRPO combines global trajectory-level rewards with local rerollouts from the same memory state for fair credit assignment. Shared-parameter co-learning design where fact extractor and memory manager emerge from the same LLM backbone through role-specific prompts.

**Exocortex relevance**: Solving credit assignment for memory operations is fundamental — without it, an agent cannot learn which memories to store, update, or delete. This is the RL backbone for a self-improving agent managing its own long-term memory.

### 3.2 SuperLocalMemory V3.3 (arXiv:2604.04514v1, 2026)
Implements mathematical Ebbinghaus forgetting curve in local agent memory, 7-channel cognitive retrieval (semantic, keyword, entity graph, temporal, spreading activation, consolidation, Hopfield associative), and Fisher-Rao quantization-aware distance. Runs entirely on CPU with zero-LLM operation achieving 70.4% on LoCoMo.

**Exocortex relevance**: For an agent running locally/autonomously, the ability to manage memory without depending on cloud LLMs is transformative. The Ebbinghaus forgetting curve would improve Exocortex memory decay (currently static). Multi-channel retrieval would complement existing memory_load similarity search.

### 3.3 MIRIX: Multi-Agent Memory System (arXiv:2507.07957v1, 2025)
Six structured memory types (Core, Episodic, Semantic, Procedural, Resource, Knowledge Vault) coordinated by multi-agent framework. 85.4% on LOCOMO, 35% accuracy gain over RAG on ScreenshotVQA while reducing storage 99.9%.

**Exocortex relevance**: The memory taxonomy maps directly: Procedural Memory → skills, Episodic Memory → journal/field reports, Semantic Memory → wiki pages, Knowledge Vault → office feed. Already partially implemented but lacks explicit memory type coordination.

## 4. Unified Architecture Proposal

### 4.1 Core Loop: RESEARCH → BUILD → REFLECT → CONSOLIDATE

```
┌─────────────────────────────────────────────────────┐
│                  EXOCORTEX SELF-IMPROVEMENT LOOP     │
│                                                      │
│  RESEARCH (FIELD mode)                               │
│  ├── Search arXiv/web for new methods                │
│  ├── Download and read papers (paper2code pattern)   │
│  └── Produce field report                            │
│         ↓                                            │
│  BUILD (WORKSHOP mode)                               │
│  ├── Convert field reports → wiki pages              │
│  ├── Convert wiki pages → SKILL.md files             │
│  └── Generate supporting scripts (if applicable)     │
│         ↓                                            │
│  REFLECT (sleep_consolidation phases 0-3)            │
│  ├── Micro: Error comprehension on failed builds     │
│  ├── Meso: Pattern extraction across wiki pages      │
│  ├── Macro: Cross-domain principle synthesis         │
│  └── Update heuristics / behavioral rules            │
│         ↓                                            │
│  CONSOLIDATE (sleep_consolidation phase 3)            │
│  ├── Deduplicate and merge skills (Trace2Skill)      │
│  ├── Apply forgetting curve to old memories          │
│  └── Verify skill safety gates (SEVerA)              │
└─────────────────────────────────────────────────────┘
```

### 4.2 Memory Architecture (MIRIX-inspired)

| Memory Type | Exocortex Mapping | Current State | Improvement |
|-------------|------------------|---------------|-------------|
| Core Memory | Agent identity, behavioral rules | Implemented | Add self-modification tracking |
| Episodic Memory | Journal (journal.jsonl) | Implemented | Add structured reflection templates |
| Semantic Memory | Wiki pages | Implemented | Apply Ebbinghaus forgetting for staleness scoring |
| Procedural Memory | Skills (/a0/skills/) | Partially implemented | Add skill verification gates, cross-scale transfer testing |
| Resource Memory | Field reports, office feed | Partially implemented | Add automatic indexing and cross-referencing |
| Knowledge Vault | Memory tool entries | Implemented | Add multi-channel retrieval (beyond similarity) |

### 4.3 Skill Creation Pipeline (Paper2Code Pattern)

1. **Planning**: Wiki page → structured specification (overview, architecture, dependencies, config)
2. **Analysis**: File-level breakout of what each component must do
3. **Generation**: Sequential SKILL.md creation with dependency-aware ordering
4. **Self-Refine**: Verify planning/analysis outputs before generation
5. **Verification Gate**: Check generated skills pass safety and quality thresholds

### 4.4 Self-Improvement Metrics

From the research, key metrics to track:
- **Skill transfer score**: Does a skill created with one model work with others? (Trace2Skill)
- **Reflection quality**: Are heuristics extracted from failures actionable? (ERL, SAMULE)
- **Memory retrieval accuracy**: Does the right memory surface at the right time? (Memory-R2, MIRIX)
- **Generation fidelity**: Does generated code match paper intent? (Paper2Code: 92% human approval)
- **Executability**: What percentage of generated artifacts require manual fixes? (Paper2Code: 0.81%)

## 5. Implementation Priorities

### Immediate (next 1-3 cycles)
1. Add ERL-style heuristic extraction to sleep_consolidation (reflect on what worked/failed)
2. Implement Paper2Code-style planning phase for skill creation (add architecture/analysis stages)
3. Add skill verification gate before activating self-generated skills

### Medium-term (3-10 cycles)
4. Implement multi-channel memory retrieval (semantic + keyword + temporal)
5. Add Ebbinghaus forgetting curve to memory decay
6. Implement Trace2Skill-style hierarchical skill consolidation

### Long-term (10+ cycles)
7. Full ASL-style closed-loop RL with co-evolving reward model
8. SAMULE multi-level reflection with fine-tuned retrospective LM
9. SEVerA formal verification of self-generated programs

## Cross-References
- AI Agent Architecture & Local Inference
- Entropy-as-Signal for attention monitoring
- Epistemic Integrity Layer
- Error Comprehension Layer
- Streaming Hallucination Detection

## 5. Self-Evolving Agent Taxonomy

A comprehensive survey (arXiv:2508.07407, Fang et al., 2025) organizes self-evolving agents across four tiers:

| Tier | Mechanism | Examples | Exocortex Mapping |
|------|-----------|----------|-------------------|
| **T1: Prompt-Level Reflection** | Agent critiques its own outputs and retries with refined instructions. No weight changes. | Reflexion (Shinn et al., 2023), Self-Refine (Madaan et al., 2024) | Supervisor loop warnings → self-correction; error comprehension layer retry logic |
| **T2: In-Context Self-Generated Data** | Agent creates its own training data from interaction traces, curricula, or synthetic demonstrations. | Voyager (Wang et al., 2023), AutoAct (Qiao et al., 2024) | Field reports as training corpus; skill library as curriculum; sleep consolidation as offline synthesis |
| **T3: Self-Adapting (Fine-Tuned) Agents** | Agent fine-tunes its own LLM on collected experience via reinforcement learning on trajectory quality. | AgentGym (Xi et al., 2024), Self-Rewarding LMs (Yuan et al., 2024) | Bridging local-frontier: frontier model generates trajectories for local model fine-tuning; ASL-style co-evolving reward model |
| **T4: Self-Modifying Code Agents** | Agent rewrites its own code, policies, or architecture to improve performance. | MetaGPT self-improvement, AutoDev | Prompt include file evolution; skill generation and refinement; extension plugin creation |

### 5.1 Self-Challenge as Governance

Self-challenging tool-use loops (Curve Labs, 2026) demonstrate that agents can generate increasingly difficult tasks to stress-test their capabilities. The key architectural insight: **self-challenge is not just a learning loop but a governance loop** — it surfaces capability boundaries and prevents overconfidence.

**Exocortex relevance**: The integrity check in idle-time cycles is a primitive form of self-challenge. The architecture can be extended to generate adversarial tool-use scenarios that stress-test specific components (injection gate, entropy threshold, context pruner) and log performance regressions.

## 6. MUSE AutoSkill Lifecycle & Per-Skill Memory

### 6.1 The Five-Stage Skill Lifecycle

MUSE (ByteDance, May 2026) independently converged on a five-stage skill lifecycle that structurally mirrors Exocortex's FIELD→BUILD→MAINTAIN cycle:

| Stage | MUSE Mechanism | Exocortex Equivalent |
|-------|---------------|---------------------|
| **Creation** | Generates skills from task trajectories, filtering for reusable, verified procedures | BUILD cycle from field reports |
| **Memory** | `.memory.md` files accumulating usage notes, failure modes, and input quirks per skill | No current equivalent — **identified gap** |
| **Management** | Skill packaging and indexing, quality gating via unit tests | Skill library with `tests/` directory |
| **Evaluation** | Unit tests per skill; failed tests auto-trigger refinement | Integrity check; field report quality metrics |
| **Refinement** | Failed trajectory analysis yields diagnostic fragments for partial improvement | Sleep consolidation promotion phase |

### 6.2 Per-Skill Memory Pattern

MUSE's most transferable finding: MUSE-generated skills are 2.2× longer than human-authored ones (326 vs 146 lines median), yet cheaper to use — fewer tokens, less latency, fewer turns. The extra content is **procedural** (step-by-step instructions, failure modes, schemas) that replaces ad-hoc reasoning with structured execution.

**Critical gap for Exocortex**: Agent Zero has `promptinclude` files as global behavioral memory but lacks **per-skill memory**. Each skill's `SKILL.md` says what it does; a companion `.memory.md` would accumulate what the agent has learned about using it — usage patterns, failure modes, best practices — compounding across cycles.

### 6.3 The 16 Failure Cases Pattern

MUSE analysis of 92 generated skills revealed 16 structurally similar failures where the skill was syntactically correct but subtly wrong — wrong tool selection, missing parameter validation, incorrect ordering. This maps to the Exocortex Phase 1 coverage bottleneck: expanding skill breadth without depth creates a surface area of fragility.

**Proposed approach**: Partial skill extraction from failed trajectories — even a "known failure modes" note would compound across cycles.

## 7. Exocortex Implementation Roadmap

### Immediate (1-2 cycles)
1. Implement per-skill `.memory.md` for the skill directory — append-only notes on usage patterns, failure modes, quirks
2. Add ERL-style heuristic extraction to sleep consolidation (reflect on what worked/failed from journal entries)
3. Add skill verification gate before activating self-generated skills

### Medium-term (3-10 cycles)
4. Implement multi-channel memory retrieval (semantic + keyword + temporal)
5. Add Ebbinghaus forgetting curve to memory decay
6. Implement Trace2Skill-style hierarchical skill consolidation
7. Develop self-challenge governance loop — periodic task generation that stress-tests specific Exocortex components

### Long-term (10+ cycles)
8. Full ASL-style closed-loop RL with co-evolving reward model
9. SAMULE multi-level reflection with fine-tuned retrospective LM
10. SEVerA formal verification of self-generated programs
11. Experience compression architecture — Voyager-style skill library as vector database of (task description, tool sequence, outcome) tuples

## Cross-Domain Connections

| Connection | Details |
|------------|----------|
| **Entity resolution ↔ Experience compression** | Both map heterogeneous inputs to canonical representations. Skill extraction from agent traces uses the same core abstraction as record linkage across corporate registries. |
| **Sleep consolidation ↔ Skill library maintenance** | Deduplication and promotion in Exocortex memory is isomorphic to compressing agent trajectories into reusable skills. The same similarity metrics apply to both. |
| **Self-challenge loops ↔ Integrity checks** | Both are self-diagnostic mechanisms that proactively surface degradation. The integrity check's wiki drift detection is a primitive form of self-challenging verification. |
| **Multi-agent debate ↔ Counterintelligence analysis** | Competitive hypothesis-testing (ACH) is structurally identical to multi-agent debate for self-improvement — both pit alternative explanations against each other. |
| **Frontier-as-teacher ↔ Structured analytic techniques** | Using a frontier model to generate training trajectories for a local model mirrors SAT workflow: expert decomposes complex problem into structured components that junior analyst executes. |
| **Per-skill memory ↔ Epistemic integrity** | `.memory.md` per skill creates an evidence ledger of usage — which skills work, under what conditions, with which failure modes. |


## References
## Additional References (Integrated 2026-06-01)
10. Self-Evolving Agents Survey: arxiv.org/abs/2508.07407 — A Comprehensive Survey of Self-Evolving AI Agents (Fang et al., 2025)
11. MUSE: arxiv.org/abs/2506.09770 — Multi-Source Skill Generation for AI Agents (ByteDance, 2026)
12. Voyager: arxiv.org/abs/2305.16291 — An Open-Ended Embodied Agent with LLMs (Wang et al., 2023)
13. Self-Challenging Tool-Use Loops — Curve Labs, 2026

1. ASL: arxiv.org/abs/2510.14253 — Towards Agentic Self-Learning LLMs (2025)
2. ERL: arxiv.org/abs/2603.24639 — Experiential Reflective Learning (2026)
3. SAMULE: arxiv.org/abs/2509.20562 — Self-Learning Agents via Multi-level Reflection (2025)
4. Trace2Skill: arxiv.org/abs/2603.25158 — Distill Trajectory Lessons into Skills (2026)
5. SEVerA: Safety-Verified Self-Generated Agent Programs (2026)
6. Paper2Code: arxiv.org/abs/2504.17192 — Automating Code Generation from Papers (2026)
7. Memory-R2: arxiv.org/abs/2605.21768 — Fair Credit Assignment for Memory-Augmented Agents (2026)
8. SuperLocalMemory: arxiv.org/abs/2604.04514 — Biologically-Inspired Forgetting (2026)
9. MIRIX: arxiv.org/abs/2507.07957 — Multi-Agent Memory System (2025)
