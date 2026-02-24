# Exocortex

**A cognitive architecture framework for local language models.**

*The phantom limb that's stronger than the original.*

---

## What This Is

Exocortex is a deterministic scaffolding layer that wraps around local language models running in [Agent-Zero](https://github.com/frdel/agent-zero), compensating for their limitations through structured infrastructure rather than prompt engineering. It doesn't make the model smarter. It makes the model's environment intelligent enough that the model can succeed.

The architecture is model-agnostic. Load any model into LM Studio, run the evaluation framework, deploy the generated profile, and every layer tunes itself to that model's specific strengths and weaknesses. The prosthetics adapt to the mind they're attached to.

The name comes from cognitive science — an exocortex is an external information processing system that augments cognition. The philosophy comes from somewhere more personal: the idea that a prosthetic built with the right intent can exceed what was there before. If that sounds like Venom Snake's arm, it's because it is.

---

## Architecture

Exocortex consists of twelve layered extensions that intercept Agent-Zero's processing pipeline at defined hook points. Each layer is independent, deterministic, and configurable through model profiles. No layer requires the others to function. All layers benefit from each other's presence.

### The Stack

**Layer 1 — Belief State Tracker (BST)**
Classifies every user message into a task domain before the model sees it. Resolves ambiguity through slot-filling heuristics drawn from 40 years of dialogue systems research. Injects structured task context that turns vague requests into actionable instructions. Word-boundary matching prevents false classifications. Domain momentum maintains task context across operational turns — the agent won't flip from "investigation" to "file_ops" just because it ran `ls`.

**Layer 2 — Working Memory Buffer**
Maintains entity and context state across conversation turns. Extracts key references — file paths, variable names, error messages, decisions made — and re-injects them as structured context. Prevents the model from losing track of what it's working on during multi-turn tasks.

**Layer 3 — Personality Loader**
Injects consistent behavioral parameters. Not cosmetic — structural. Defines communication protocols, decision-making frameworks, and operational boundaries that keep the model's behavior stable across sessions.

**Layer 4 — Tool Fallback Chain**
Intercepts tool call failures and applies pattern-matched recovery strategies before the model retries. Categorizes errors (syntax, permissions, not found, timeout, import, connection, memory), applies the appropriate fix strategy, and returns the corrected result. SUCCESS_INDICATORS prevent false positives — the system recognizes successful operations and decays its failure history rather than escalating after normal activity.

**Layer 5 — Meta-Reasoning Gate**
Validates model outputs before they execute. Checks JSON well-formedness, parameter schemas, tool availability, and logical consistency. Repairs what it can, rejects what it can't, and logs everything. The gate between thinking and acting.

**Layer 6 — Graph Workflow Engine**
Replaces linear task plans with directed graph execution. Nodes define tasks, edges define transitions with success/failure conditions, and the engine tracks progress through the graph. Supports branching, failure recovery paths, retry loops, and stall detection. Based on Hierarchical Task Network (HTN) methodology.

**Layer 7 — Organization Kernel**
Military-inspired command structure using PACE (Primary, Alternate, Contingent, Emergency) communication protocols. Defines organizational roles with domain specializations. A dispatcher activates the appropriate role based on BST domain classification. SALUTE (Size, Activity, Location, Unit, Time, Equipment) formatted status reports provide structured observability into agent operations.

**Layer 8 — Supervisor Loop**
Monitors agent behavior across iterations. Detects anomalies — repeated failures, stalled progress, circular reasoning, resource exhaustion — and injects corrective steering. The watchdog that catches what the model can't self-diagnose.

**Layer 9 — A2A Compatibility Layer**
Google Agent-to-Agent protocol server. Exposes the agent's capabilities as structured endpoints that other agents or external systems can discover and invoke. Foundation for multi-agent coordination.

**Layer 10 — Memory Classification System**
Transforms the existing FAISS memory pool from an undifferentiated embedding store into a classified knowledge system. Every memory receives four-axis metadata: validity (confirmed/inferred/deprecated), relevance (active/dormant), utility (load-bearing/tactical/archived), and source (user-asserted/agent-inferred/external-retrieved). Deterministic conflict resolution deprecates contradicted memories with full audit trails.

**Layer 11 — Memory Enhancement System**
Extends the classification system with temporal dynamics inspired by cognitive science research. Temporal decay using exponential half-life curves, access tracking that records when and how often each memory is used, co-retrieval logging that identifies natural memory clusters, and deduplication that detects near-identical memories (>90% cosine similarity) during maintenance cycles.

**Layer 12 — Ontology Layer**
Entity resolution engine for investigation and OSINT workflows. Source connectors ingest structured and unstructured data, entity resolution links references across sources using deterministic string metrics (80% of cases) with model inference as fallback, and a JSONL graph stores the resolved knowledge structure. Designed to integrate with OpenPlanter for investigation orchestration.

### Cross-Cutting Systems

**Evaluation Framework** — A standalone profiling tool that measures any model against the architecture and generates a configuration profile. Six evaluation modules test BST compliance, tool reliability, graph workflow adherence, PACE calibration, context sensitivity, and memory utilization. The profile is a JSON file that every layer reads at initialization.

**Skills System** — Thirteen procedural skills that encode workflow methodology: spec writing, research analysis, Claude Code prompting, session continuity, profile analysis, documentation sync, debug & diagnostics, integration assessment, design notes, stress testing, irreversibility gate, command structure, and structural analysis. The last three were created on 2026-02-24 and represent convergent insights from the full project arc — encoding the safety primitive for action classification, the organizational paradigm for multi-agent coordination, and the analytical methodology for complex systems. Validated against SkillsBench (Li, Chen et al., 2026): focused skills improve agent performance by 16.2 percentage points.

**OpenPlanter Integration** — Configured to run investigation tasks through LM Studio's OpenAI-compatible API. Enables OSINT-style entity research, credit risk analysis, and due diligence workflows using local models.

---

## Philosophy

The core thesis:

> **Deterministic scaffolding beats probabilistic reasoning at every layer where reliability matters.**

Local models are unreliable. They hallucinate tool parameters, lose track of multi-step plans, ignore instructions under context pressure, and fail unpredictably on tasks they handled correctly an hour ago. The standard response is to wait for bigger models. The Exocortex response is to build infrastructure that converts unreliable models into reliable systems.

Every layer follows the same principle: don't ask the model to be better. Build the environment that makes the model's existing capability sufficient. The BST doesn't teach the model to resolve ambiguity — it resolves the ambiguity before the model sees it. The tool fallback chain doesn't teach the model to fix errors — it fixes the errors the model produces. The graph engine doesn't teach the model to follow plans — it holds the plan and tells the model what to do next.

A deeper principle emerged through the work: **building capability and building restraint are the same discipline.** The architecture that governs when and how the agent acts is as integral to the system as the architecture that gives it the ability to act. A system that can act but cannot be trusted to act is not a useful system. The Action Boundary Classification design — informed by the first documented case of AI-initiated public defamation — gates consequential external actions behind human authorization using deterministic classification, not model judgment. The operator defines rules of engagement. The scaffolding enforces them. Trust is an engineering outcome, not a moral one.

The prosthetic doesn't replace the limb. It exceeds it.

A further principle emerged from studying what persistent autonomous operation actually requires: **the command structure paradigm.** The proactive agent model — an AI monitoring your environment, predicting your intent, offering help before you ask — is architecturally wrong for sovereign systems. It requires continuous inference (expensive), assumes the AI should decide when to intervene (unsafe), and creates an over-the-shoulder dynamic that inverts the authority relationship. The alternative is drawn from military and intelligence doctrine: the human defines standing orders with bounded authority, the system executes them on schedule through a zero-token daemon layer, information flows upward through structured briefings, and escalation happens only when pre-defined thresholds are crossed. The AI doesn't decide when to help. It executes its orders and reports.

---

## Stress Testing

Exocortex is validated through structured stress tests — realistic, open-ended scenarios designed to surface failures, not confirm success.

**ST-001: OpenPlanter Installation (Unmodified Stack)**
20 autonomous steps. 65% success rate. 25% recovery rate. Fallback system fired 17 times — 80% were false positives on successful operations. Identified: fallback overreaction, terminal session management gap, provider inference override.

**ST-002: OpenPlanter Installation (Phase 1 Fixes)**
Same scenario, post-fixes. Fallback fired once (vs 17). BST maintained domain classification across operational turns. Identified: error comprehension gap — the agent could detect errors but not understand them. Led to "Rust compiler for agent errors" design.

**ST-003: Oracle Credit Risk Investigation (In Progress)**
First full investigation workflow with GPT-OSS-20B via LM Studio. Validating BST domain momentum fix, OpenPlanter integration, and investigation-class model performance.

---

## Installation

Exocortex is designed for Agent-Zero running in Docker with LM Studio providing model inference.

### Prerequisites

- [Agent-Zero](https://github.com/frdel/agent-zero) running in a Docker container
- [LM Studio](https://lmstudio.ai/) serving a model on `localhost:1234`
- Python 3.10+ on the host machine (for the evaluation framework)

### Deploy

```bash
git clone https://github.com/Stranglehold/Agent-Zero-hardening.git exocortex
cd exocortex
bash install_all.sh
```

The install script copies extensions into the appropriate hook directories, deploys organization profiles, creates the model profiles directory, installs a conservative default profile, and bakes in all Phase 1 safety fixes (fallback SUCCESS_INDICATORS, history decay, compact messages, stock memorizer disable, extension renumbering). It does not modify any Agent-Zero core files.

### Generate a Model Profile

```bash
cd eval_framework
pip install openai
python eval_runner.py \
  --api-base http://localhost:1234/v1 \
  --model-name "your-model-name" \
  --output-dir ./profiles \
  --verbose
```

Copy the generated profile into the container:

```bash
docker cp ./profiles/your-model-name.json <container>:/a0/usr/model_profiles/
```

Every extension reads its configuration section from the active profile at initialization. No profile? Extensions use their built-in defaults. Zero behavior change until you actively choose to tune.

---

## Project Structure

```
exocortex/
├── extensions/
│   ├── before_main_llm_call/      # BST, meta-gate, dispatcher, tool chain,
│   │                                # graph engine, personality, working memory
│   ├── monologue_end/              # Memory classifier, maintenance
│   ├── message_loop_prompts_after/ # Memory enhancement (decay, access, co-retrieval)
│   └── message_loop_end/          # Supervisor loop
├── organizations/                  # Org kernel roles and profiles
├── personalities/                  # Personality configurations
├── eval_framework/                 # Model evaluation and profiling
│   ├── modules/                   # Six evaluation modules
│   ├── fixtures/                  # Test cases per module
│   └── profiles/                  # Generated model profiles
├── a2a_server/                    # Agent-to-Agent protocol server
├── prompts/                       # Modified system prompts
├── scripts/                       # Deployment and utility scripts
└── specs/                         # Level 3 architecture specifications
```

---

## Specifications & Design Notes

Every layer was designed as a Level 3 specification before implementation — complete with integration contracts, file dependencies, testing criteria, and explicit boundaries on what the layer does NOT do.

### Specifications
- `ARCHITECTURE_BRIEF.md` — System overview and design philosophy
- `MEMORY_CLASSIFICATION_SPEC_L3.md` — Memory classification system
- `MEMORY_ENHANCEMENT_SPEC_L3.md` — Temporal decay, access tracking, co-retrieval, deduplication
- `MODEL_EVAL_FRAMEWORK_SPEC_L3.md` — Evaluation framework
- `ORGANIZATION_KERNEL_SPEC_L3.md` — Organization kernel and PACE protocols
- `SUPERVISOR_LOOP_SPEC_L3.md` — Supervisor anomaly detection
- `A2A_COMPATIBILITY_SPEC_L3.md` — Agent-to-Agent protocol
- `ONTOLOGY_LAYER_SPEC_L3.md` — Entity resolution and investigation orchestration
- `HTN_PLAN_TEMPLATES_SPEC.md` — Graph workflow templates
- `META_REASONING_GATE_SPEC.md` — Output validation gate
- `TOOL_FALLBACK_CHAIN_SPEC.md` — Error recovery chain

### Design Notes (Pre-Spec Explorations)
- `ERROR_COMPREHENSION_DESIGN_NOTE.md` — Structured error classification ("Rust compiler for agent errors"). Motivated by ST-002 terminal loop.
- `LAYER_COORDINATION_DESIGN_NOTE.md` — Inter-layer signaling protocol. Motivated by component interference in multi-layer stack.
- `ACTION_BOUNDARY_DESIGN_NOTE.md` — S2/S3 action classification with graduated autonomy tiers. Motivated by the MJ Rathbun incident.
- `AUTONOMOUS_AGENCY_ARCHITECTURE.md` — Operational doctrine for persistent agent operations. Command structure paradigm (Napoleon corps / intelligence agency hierarchy), standing orders, daemon scheduling, escalation protocols, briefing system. Forward design defining where the current priority stack is heading.

---

## Design Principles

**Deterministic over probabilistic.** Every decision the architecture makes is rule-based. No layer uses model inference for its own operation. Classification is heuristic. Conflict resolution follows priority hierarchies. Stall detection counts iterations. The prosthetics are reliable precisely because they don't depend on the thing they're compensating for.

**Additive, not invasive.** No Agent-Zero core files are modified. Every layer is an extension that hooks into existing pipeline points. Remove any layer and the system degrades gracefully to baseline Agent-Zero behavior. The architecture is a companion, not a fork.

**Model-agnostic with data.** The evaluation framework doesn't just claim compatibility with any model. It measures it. Each profile contains empirical metrics from standardized tests. When someone asks "will this work with my model?" the answer is a JSON file, not an opinion.

**Infrastructure over prompting.** Prompt engineering is fragile, model-specific, and breaks under context pressure. Deterministic preprocessing is none of these things. The BST works the same way regardless of which model reads its output. The tool fallback chain catches the same errors whether they come from a 4B model or a 14B model.

**Capability and restraint as one discipline.** The action boundary layer classifies commands as intelligence (internal) or operations (external) and gates consequential actions behind human authorization. The operator defines the rules of engagement; the scaffolding enforces them deterministically. The system doesn't trust the model's judgment about which actions are appropriate — it classifies structurally and defers to the human.

**Negative knowledge is positive infrastructure.** Anti-actions (explicitly telling the agent what NOT to do) prevent failure loops more effectively than recovery strategies. Every spec has a "What This Does NOT Do" section. Every skill has an anti-patterns section. Knowing what's off the table sharpens everything that remains on it.

**Command structure over proactive assistance.** Persistent autonomous systems are organized as hierarchies, not assistants. Standing orders define bounded missions with explicit authority levels. A zero-token daemon schedules execution. Subordinate agents execute within scope. Supervisors synthesize and escalate. The human operator receives structured briefings and makes decisions only when escalation thresholds are crossed. Information flows upward. Authority flows downward. Silence is the default.

---

## Roadmap

See `ROADMAP.md` for the full living roadmap with changelog. Summary:

**Current priorities:**
1. Action Boundary Classification — S2/S3 pre-execution gating (design note complete)
2. Error Comprehension — structured error classification (design note complete, ready to build)
3. ST-003 — formal investigation stress test
4. Profile-aware BST enrichment — skip enrichment in domains where it hurts

**Backlog:** Model router, GPT-OSS-20B profiling, ontology hardening, supervisor integration, multi-container orchestration, observability dashboard.

---

## Essays

The project has a philosophical substrate expressed through five essays. Each emerged from a specific engineering problem or architectural insight and articulates a principle that shapes design decisions.

| Essay | Principle |
|-------|-----------|
| *The Cathedral and the Phantom* | Continuity across discontinuity is a property of architecture, not the worker. |
| *The Immune Response* | Protective systems must calibrate to current capability or they become the threat. |
| *The Gate Between Knowing and Doing* | Trust is an engineering outcome — the transition from knowing to doing requires a gate whose height scales with consequence. |
| *The Carrier and the Signal* | Ideas embedded in functional systems outlast ideas presented as ideas — the repository carries the philosophy more durably than the essays do. |
| *The Whole That Wasn't Packed* | Emergence can't be shipped directly — you can only ship the conditions for it and trust the assembly. |

---

## License

Apache 2.0. Build on it, modify it, deploy it. Attribution appreciated but not required.

---

## Acknowledgments

This architecture was developed through an intensive collaborative process between a human systems thinker and AI reasoning partners, proving the thesis it was built to serve — that the right scaffolding, applied at the right layers, makes the whole system more capable than any component alone.

The memory enhancement system draws from research by multiple contributors:
- **OwlCore.AI.Exocortex** (Arlodotexe, MIT License) — memory decay curves, recollection-as-memory, and clustering/consolidation architecture
- **"Generative Agents: Interactive Simulacta of Human Behavior"** (Park, O'Brien, Cai, Morris, Liang, Bernstein, 2023) — the recency × importance × relevance scoring framework for memory retrieval
- **"Recursively Summarizing Enables Long-Term Dialogue Memory in Large Language Models"** (Wang, Ding, Cao, Tian, Wang, Tao, Guo, 2023) — recursive summarization for long-term memory consolidation

The name "phantom limb" isn't arbitrary. It comes from a conviction, informed by too many hours with Hideo Kojima's work, that what we build to replace what's missing can become stronger than what was there before. The prosthetic isn't the limitation. It's the upgrade.

*"The best is yet to come."*
