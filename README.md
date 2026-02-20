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

Exocortex consists of layered extensions that intercept Agent-Zero's processing pipeline at defined hook points. Each layer is independent, deterministic, and configurable through model profiles. No layer requires the others to function. All layers benefit from each other's presence.

### The Stack

**Layer 1 — Belief State Tracker (BST)**
Classifies every user message into a task domain before the model sees it. Resolves ambiguity through slot-filling heuristics drawn from 40 years of dialogue systems research. Injects structured task context that turns vague requests into actionable instructions. The model receives enriched messages instead of raw ambiguity.

**Layer 2 — Working Memory Buffer**
Maintains entity and context state across conversation turns. Extracts key references — file paths, variable names, error messages, decisions made — and re-injects them as structured context. Prevents the model from losing track of what it's working on during multi-turn tasks.

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
Monitors agent behavior across iterations. Detects anomalies — repeated failures, stalled progress, circular reasoning, resource exhaustion — and injects corrective steering. The watchdog that catches what the model can't self-diagnose.

**Layer 9 — A2A Compatibility Layer**
Google Agent-to-Agent protocol server. Exposes the agent's capabilities as structured endpoints that other agents or external systems can discover and invoke. Foundation for multi-agent coordination.

**Layer 10 — Memory Classification System**
Transforms the existing FAISS memory pool from an undifferentiated embedding store into a classified knowledge system. Every memory receives four-axis metadata: validity (confirmed/inferred/deprecated), relevance (active/dormant), utility (load-bearing/tactical/archived), and source (user-asserted/agent-inferred/external-retrieved). Deterministic conflict resolution deprecates contradicted memories with full audit trails. Role-aware filtering ensures each specialist role sees only the memories relevant to its domain.

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

Every layer follows the same principle: don't ask the model to be better. Build the environment that makes the model's existing capability sufficient. The BST doesn't teach the model to resolve ambiguity — it resolves the ambiguity before the model sees it. The tool fallback chain doesn't teach the model to fix errors — it fixes the errors the model produces. The graph engine doesn't teach the model to follow plans — it holds the plan and tells the model what to do next.

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

The install script copies extensions into the appropriate hook directories, deploys organization profiles, creates the model profiles directory, and installs a conservative default profile. It does not modify any Agent-Zero core files.

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
│   ├── monologue_end/              # Memory classifier
│   ├── message_loop_prompts_after/ # Memory relevance filter
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

## Specifications

Every layer was designed as a Level 3 specification before implementation — complete with integration contracts, file dependencies, testing criteria, and explicit boundaries on what the layer does NOT do. Specs live in the repo root.

- `ARCHITECTURE_BRIEF.md` — System overview and design philosophy
- `MEMORY_CLASSIFICATION_SPEC_L3.md` — Memory classification system
- `MODEL_EVAL_FRAMEWORK_SPEC_L3.md` — Evaluation framework
- `ORGANIZATION_KERNEL_SPEC_L3.md` — Organization kernel and PACE protocols
- `SUPERVISOR_LOOP_SPEC_L3.md` — Supervisor anomaly detection
- `A2A_COMPATIBILITY_SPEC_L3.md` — Agent-to-Agent protocol
- `HTN_PLAN_TEMPLATES_SPEC.md` — Graph workflow templates
- `META_REASONING_GATE_SPEC.md` — Output validation gate
- `TOOL_FALLBACK_CHAIN_SPEC.md` — Error recovery chain

---

## Design Principles

**Deterministic over probabilistic.** Every decision the architecture makes is rule-based. No layer uses model inference for its own operation. Classification is heuristic. Conflict resolution follows priority hierarchies. Stall detection counts iterations. The prosthetics are reliable precisely because they don't depend on the thing they're compensating for.

**Additive, not invasive.** No Agent-Zero core files are modified. Every layer is an extension that hooks into existing pipeline points. Remove any layer and the system degrades gracefully to baseline Agent-Zero behavior. The architecture is a companion, not a fork.

**Model-agnostic with data.** The evaluation framework doesn't just claim compatibility with any model. It measures it. Each profile contains empirical metrics from standardized tests. When someone asks "will this work with my model?" the answer is a JSON file, not an opinion.

**Infrastructure over prompting.** Prompt engineering is fragile, model-specific, and breaks under context pressure. Deterministic preprocessing is none of these things. The BST works the same way regardless of which model reads its output. The tool fallback chain catches the same errors whether they come from a 4B model or a 14B model. The graph engine holds the same plan structure regardless of who's executing it.

---

## Roadmap

**Current: Foundation hardening**
- Model profiles tuned from real evaluation data
- Profile loader integration into each extension
- Bookshelf reference library (document ingestion into classified memory)

**Next: Capability expansion**
- Model router — role-based model selection driven by evaluation profiles
- LM Studio JIT loading integration for dynamic model swapping
- Cross-model profiles for supervisor/specialist/utility model allocation

**Future: Scale**
- Multi-container orchestration via A2A protocol
- Distributed compute pooling across heterogeneous hardware
- Observability dashboard reading SALUTE reports in real time

---

## License

Apache 2.0. Build on it, modify it, deploy it. Attribution appreciated but not required.

---

## Acknowledgments

This architecture was developed through an intensive collaborative process between a human systems thinker and AI reasoning partners, proving the thesis it was built to serve — that the right scaffolding, applied at the right layers, makes the whole system more capable than any component alone.

The name "phantom limb" isn't arbitrary. It comes from a conviction, informed by too many hours with Hideo Kojima's work, that what we build to replace what's missing can become stronger than what was there before. The prosthetic isn't the limitation. It's the upgrade.

*"The best is yet to come."*
