# Exocortex

**A cognitive architecture framework for local language models.**

*The phantom limb that's stronger than the original.*

---

## What This Is

Exocortex is a deterministic scaffolding layer that wraps around local language models running in [Agent-Zero](https://github.com/frdel/agent-zero), compensating for their limitations through structured infrastructure rather than prompt engineering. It doesn't make the model smarter. It makes the model's environment intelligent enough that the model can succeed.

The architecture is model-agnostic. Load any model into LM Studio, run the evaluation framework, deploy the generated profile, and every layer tunes itself to that model's specific strengths and weaknesses. The prosthetics adapt to the mind they're attached to.

What started as hardening for local model reliability has grown into something closer to an intelligence apparatus — entity resolution, knowledge graphs, investigation orchestration, and classified memory, all running on a single RTX 3090 in a Docker container. A personal-scale Palantir that answers to its operator and no one else.

The name comes from cognitive science — an exocortex is an external information processing system that augments cognition. The philosophy comes from somewhere more personal: the idea that a prosthetic built with the right intent can exceed what was there before. If that sounds like Venom Snake's arm, it's because it is.

---

## Architecture

Exocortex consists of layered extensions that intercept Agent-Zero's processing pipeline at defined hook points. Each layer is independent, deterministic, and configurable through model profiles. No layer requires the others to function. All layers benefit from each other's presence.

### The Stack

**Layer 1 — Belief State Tracker (BST)**
Classifies every user message into a task domain before the model sees it. Resolves ambiguity through slot-filling heuristics drawn from 40 years of dialogue systems research. Injects structured task context that turns vague requests into actionable instructions. The model receives enriched messages instead of raw ambiguity.

**Layer 2 — Working Memory Buffer**
Maintains entity and context state across conversation turns. Extracts key references — file paths, variable names, error messages, decisions made — and re-injects them as structured context. Prevents the model from losing track of what it's working on during multi-turn tasks. Entities decay after 8 turns of disuse; entities mentioned 3+ times promote to persistent storage.

**Layer 3 — Personality Loader**
Injects consistent behavioral parameters. Not cosmetic — structural. Defines communication protocols, decision-making frameworks, and operational boundaries that keep the model's behavior stable across sessions.

**Layer 4 — Tool Fallback Chain**
Intercepts tool call failures and applies pattern-matched recovery strategies before the model retries. Categorizes errors (syntax, permissions, not found, timeout, import, connection, memory), applies the appropriate fix strategy, and returns the corrected result. The model sees fewer failures and learns nothing about the recovery — the infrastructure handles it silently.

**Layer 5 — Meta-Reasoning Gate**
Validates model outputs before they execute. Checks JSON well-formedness, parameter schemas, tool availability, and logical consistency. Repairs what it can, rejects what it can't, and logs everything. The gate between thinking and acting.

**Layer 6 — Graph Workflow Engine**
Replaces linear task plans with directed graph execution. Nodes define tasks, edges define transitions with success/failure conditions, and the engine tracks progress through the graph. Supports branching, failure recovery paths, retry loops, and stall detection. Based on Hierarchical Task Network (HTN) methodology.

**Layer 7 — Organization Kernel**
Military-inspired command structure using PACE (Primary, Alternate, Contingent, Emergency) communication protocols. Defines organizational roles with domain specializations. A dispatcher activates the appropriate role based on BST domain classification. SALUTE (Size, Activity, Location, Unit, Time, Equipment) formatted status reports provide structured observability into agent operations.

**Layer 8 — Supervisor Loop**
Monitors agent behavior across iterations. Detects anomalies — repeated failures, stalled progress, circular reasoning, resource exhaustion — and injects corrective steering. The XO watching the operation from higher ground.

**Layer 9 — A2A Compatibility Layer**
Google Agent-to-Agent protocol server. Exposes the agent's capabilities as structured endpoints that other agents or external systems can discover and invoke. Foundation for multi-agent coordination — when the operation needs more than one operative.

**Layer 10 — Memory Classification System**
Transforms the existing FAISS memory pool from an undifferentiated embedding store into a classified knowledge system. Every memory receives four-axis metadata: validity (confirmed/inferred/deprecated), relevance (active/dormant), utility (load-bearing/tactical/archived), and source (user-asserted/agent-inferred/external-retrieved). Deterministic conflict resolution deprecates contradicted memories with full audit trails. Role-aware filtering ensures each specialist role sees only the memories relevant to its domain.

**Layer 11 — Memory Enhancement Pipeline**
Six-component processing pipeline that makes memory retrieval intelligent rather than relying on raw embedding similarity. Query expansion generates three retrieval variants per user message. Temporal decay weights recent memories over stale ones. Related memory links surface co-occurring knowledge through graph traversal. Access tracking boosts frequently-referenced memories. Co-retrieval logging captures implicit relationships between memories retrieved together. Deduplication merges near-identical content with full audit trails. Informed by MemR³'s finding that query expansion alone improves recall by 23%, and A-MEM's associative linking architecture.

**Layer 12 — Ontology Layer**
Entity resolution, knowledge graph construction, and investigation orchestration running entirely on local infrastructure. A deterministic resolution engine handles entity matching through name normalization, Levenshtein distance, address canonicalization, and identifier exact-match — 80% of cases resolved without model inference. Source connectors ingest heterogeneous data (CSV, JSON, HTML) through a common pipeline. Entities land in FAISS as classified memories with ontology metadata; relationships persist in a JSONL graph. An investigation orchestrator decomposes complex queries into structured sub-tasks with evidence chains and confidence scoring. Informed by Palantir Foundry's ontology-as-operational-layer pattern and validated by Multi-Agent RAG research showing 94.3% accuracy with hybrid rule-based + LLM entity resolution.

### Evaluation Framework

A standalone profiling tool that measures any model against the architecture and generates a configuration profile. Six evaluation modules test BST compliance, tool reliability, graph workflow adherence, PACE calibration, context sensitivity, and memory utilization. The profile is a JSON file that every layer reads at initialization — swap the model, swap the profile, and the entire architecture recalibrates.

```
eval_runner.py → LM Studio API → 6 test modules → model profile JSON → deployed to container
```

This is what makes the architecture genuinely model-agnostic with empirical data to prove it.

---

## Philosophy

The core thesis:

> **Deterministic scaffolding beats probabilistic reasoning at every layer where reliability matters.**

Local models are unreliable. They hallucinate tool parameters, lose track of multi-step plans, ignore instructions under context pressure, and fail unpredictably on tasks they handled correctly an hour ago. The standard response is to wait for bigger models. The Exocortex response is to build infrastructure that converts unreliable models into reliable systems.

Every layer follows the same principle: don't ask the model to be better. Build the environment that makes the model's existing capability sufficient. The BST doesn't teach the model to resolve ambiguity — it resolves the ambiguity before the model sees it. The tool fallback chain doesn't teach the model to fix errors — it fixes the errors the model produces. The graph engine doesn't teach the model to follow plans — it holds the plan and tells the model what to do next. The ontology layer doesn't teach the model to do entity resolution — it resolves entities deterministically and hands the model structured knowledge.

This was validated independently by SkillsBench (Li, Chen et al., 2026), which found that curated procedural knowledge improves agent performance by 16.2 percentage points, while self-generated skills produce negative impacts. The finding confirmed what every layer of Exocortex was already built on: reliable scaffolding, not clever prompting.

The prosthetic doesn't replace the limb. It exceeds it.

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

The install script copies extensions into the appropriate hook directories, deploys organization profiles, creates the ontology directory structure, initializes runtime files, and installs a conservative default profile. It does not modify any Agent-Zero core files. The ontology layer creates persistent runtime files (`*.jsonl`) on first install that survive subsequent reinstalls.

Individual layers can be installed or reinstalled in isolation:

```bash
bash install_all.sh --layer=8     # Reinstall only the ontology layer
bash install_all.sh --check-only  # Check for upstream conflicts without installing
```

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
│   ├── before_main_llm_call/       # BST, meta-gate, dispatcher, graph engine,
│   │                                # personality, working memory
│   ├── monologue_end/               # Memory classifier, memory maintenance
│   ├── message_loop_prompts_after/  # Memory enhancement, ontology query, relevance filter
│   ├── message_loop_end/            # Supervisor loop
│   ├── tool_execute_before/         # Meta-reasoning gate, fallback advisor
│   ├── tool_execute_after/          # Failure counter reset, fallback logger
│   ├── error_format/                # Structured retry, failure tracker
│   └── hist_add_before/             # Working memory buffer
├── ontology/                        # Entity resolution and knowledge graph
│   ├── connectors/                  # Source ingestion (CSV, JSON, HTML)
│   ├── resolution_engine.py         # Deterministic entity matching pipeline
│   ├── relationship_extractor.py    # Relationship discovery (5 methods)
│   └── ontology_store.py            # FAISS + JSONL storage layer
├── organizations/                   # Org kernel roles and profiles
│   └── roles/                       # Specialist roles incl. intelligence analyst
├── tools/                           # Agent-Zero tool extensions
│   └── investigation_tools.py       # Investigation orchestration
├── personalities/                   # Personality configurations
├── eval_framework/                  # Model evaluation and profiling
│   ├── modules/                     # Six evaluation modules
│   ├── fixtures/                    # Test cases per module
│   └── profiles/                    # Generated model profiles
├── a2a_server/                      # Agent-to-Agent protocol server
├── translation-layer/               # BST canonical source + slot taxonomy
├── prompts/                         # Modified system prompts
├── fw-replacements/                 # Framework message overrides
├── scripts/                         # Layer install scripts
│   ├── install_ontology.sh          # Ontology layer deployment
│   ├── install_memory_classification.sh
│   ├── install_org_kernel.sh
│   ├── install_supervisor_loop.sh
│   └── ...                          # One script per layer
├── specs/                           # Level 3 architecture specifications
├── install_all.sh                   # Full deployment (idempotent, 8 install layers)
└── update.sh                        # Git pull + conflict check + reinstall
```

---

## Specifications

Every layer was designed as a Level 3 specification before implementation — complete with integration contracts, file dependencies, testing criteria, and explicit boundaries on what the layer does NOT do. Specs live in the repo root.

- `ARCHITECTURE_BRIEF.md` — System overview, design principles, and development rules
- `MEMORY_CLASSIFICATION_SPEC_L3.md` — Four-axis memory classification and conflict resolution
- `MEMORY_ENHANCEMENT_V2_SPEC_L3.md` — Memory enhancement pipeline (query expansion, temporal decay, related links, access tracking, co-retrieval, deduplication)
- `ONTOLOGY_LAYER_SPEC_L3.md` — Entity resolution, relationship extraction, investigation orchestration, and ontology-aware retrieval
- `MODEL_EVAL_FRAMEWORK_SPEC_L3.md` — Evaluation framework and profile generation
- `ORGANIZATION_KERNEL_SPEC_L3.md` — Organization kernel, PACE protocols, and SALUTE reporting
- `SUPERVISOR_LOOP_SPEC_L3.md` — Supervisor anomaly detection and corrective steering
- `A2A_COMPATIBILITY_SPEC_L3.md` — Agent-to-Agent protocol server
- `HTN_PLAN_TEMPLATES_SPEC.md` — Graph workflow templates and plan library
- `META_REASONING_GATE_SPEC.md` — Output validation and parameter checking
- `TOOL_FALLBACK_CHAIN_SPEC.md` — Error classification and recovery strategies

---

## Design Principles

**Deterministic over probabilistic.** Every decision the architecture makes is rule-based. No layer uses model inference for its own operation. Classification is heuristic. Conflict resolution follows priority hierarchies. Entity matching uses string metrics. Stall detection counts iterations. The prosthetics are reliable precisely because they don't depend on the thing they're compensating for.

**Additive, not invasive.** No Agent-Zero core files are modified. Every layer is an extension that hooks into existing pipeline points. Remove any layer and the system degrades gracefully to baseline Agent-Zero behavior. The architecture is a companion, not a fork.

**Model-agnostic with data.** The evaluation framework doesn't just claim compatibility with any model. It measures it. Each profile contains empirical metrics from standardized tests. When someone asks "will this work with my model?" the answer is a JSON file, not an opinion.

**Infrastructure over prompting.** Prompt engineering is fragile, model-specific, and breaks under context pressure. Deterministic preprocessing is none of these things. The BST works the same way regardless of which model reads its output. The tool fallback chain catches the same errors whether they come from a 4B model or a 14B model. The ontology resolves the same entities whether the downstream consumer is Qwen or GPT.

**Research-informed, not research-dependent.** Every design decision traces to empirical data — either from the evaluation framework or from published research. But papers propose mechanisms that require training, RL, or cloud APIs. Exocortex extracts the insight and builds the deterministic version. The question is always: "what's the local, rule-based alternative?"

---

## Roadmap

**Current: Ontology hardening**
- Resolution threshold tuning from real-world data (campaign finance, corporate filings, investigative datasets)
- OpenPlanter integration as investigation tool alongside ontology source connectors
- Memory enhancement + ontology cross-validation (entity memories flowing through full retrieval pipeline)
- Skills system refinement from session patterns

**Next: Model routing and multi-model orchestration**
- Model router — BST domain classification drives model selection (precision models for tool calls, reasoning models for analysis)
- LM Studio JIT loading integration for dynamic model swapping
- Cross-model profiles for supervisor/specialist/utility allocation

**Future: Scale and integration**
- Multi-container orchestration via A2A protocol (PentAGI as peer agent for security operations)
- Voice interaction via TTS sidecar (Voicebox or equivalent)
- Distributed compute pooling across heterogeneous hardware
- Observability dashboard reading SALUTE reports in real time

---

## License

Apache 2.0. Build on it, modify it, deploy it. Attribution appreciated but not required.

---

## Acknowledgments

This architecture was developed through an intensive collaborative process between a human systems thinker and AI reasoning partners, proving the thesis it was built to serve — that the right scaffolding, applied at the right layers, makes the whole system more capable than any component alone.

### Research That Informed Builds

- **SkillsBench** (Li, Chen et al., 2026) — Curated procedural knowledge improves agent performance by 16.2 percentage points; self-generated skills produce negative impacts. Validated the core design philosophy and informed the focused skills system.
- **MemR³** (Huang et al.) — Multi-path retrieval with query expansion improves recall by 23%. Directly informed the three-variant query expansion in the memory enhancement pipeline.
- **A-MEM** — Associative memory linking through co-occurrence graphs. Informed the related memory links and co-retrieval logging components.
- **Palantir Foundry Architecture** — Ontology as operational layer with fourfold integration (data, logic, action, security). Provided the architectural pattern for Layer 12's entity-centric design.
- **Multi-Agent RAG for Entity Resolution** (Aatif et al., Dec 2025) — 94.3% accuracy with 61% fewer API calls using hybrid rule-based + LLM reasoning. Validated the deterministic-first resolution strategy with model-assisted ambiguous case handling.
- **Resolvi Reference Architecture** (arXiv:2503.08087) — Formal ER pipeline stages (preprocessing, blocking, candidate generation, matching, clustering, canonicalization). Informed the five-stage resolution engine design.
- **OpenPlanter** (ShinMegamiBoson, Apache 2.0) — Recursive investigation agent with 19 tools and entity resolution across corporate registries, campaign finance, lobbying, and contracts. Integration target for investigation orchestration.

### The Name

The name "phantom limb" isn't arbitrary. It comes from a conviction, informed by too many hours with Hideo Kojima's work, that what we build to replace what's missing can become stronger than what was there before. The prosthetic isn't the limitation. It's the upgrade.

The layers have codenames that won't appear in any spec. The supervisor is the XO. The organization kernel runs PACE because that's how you communicate when the channel is unreliable. SALUTE reports because that's how you report what you see in the field. The BST is the intelligence officer who reads the message before the commander does and marks it up with everything the commander needs to know.

There's a Diamond Dogs unit patch in here somewhere. You just have to look for it.

*"Why are we still here? Just to suffer? Every night, I can feel my leg... and my arm..."*

No. We're here to build.

*"The best is yet to come."*
