# Capability-vs-Transport Layer Classification

**Purpose:** Categorize every Exocortex layer as either *capability-compensation* or *transport-compensation* — the organizing distinction for architectural longevity decisions.

**Authored:** 2026-04-17 (Stack Audit Session 002, Finding C1)

---

## The Distinction

**Capability-compensation** layers exist because the current model can't do something reliably. If a future model — v4, or v5, or the next generation of reasoning models — solves that capability gap natively, the layer becomes dead weight. These layers are tactical: necessary now, probably temporary.

**Transport-compensation** layers exist because the operating environment requires them regardless of model capability. A frontier model running in Agent-Zero still needs loop detection, action authorization, and memory persistence — not because it's incapable, but because the scaffold's job is to be trustworthy regardless of model quality. These layers are structural: necessary now, necessary in ten years.

**Mixed** layers have components from both categories. Often the triggering logic is capability-compensation while the enforcement mechanism is transport-compensation.

The practical test for each layer: *If v4 were 10x better at X, would this layer still matter?*

---

## Layer Classification Table

| Layer | Category | Rationale | Retires if... |
|-------|----------|-----------|---------------|
| **BST** (Belief State Tracker) | Capability-compensation | Classifies task domain because the model doesn't reliably self-classify. Rigidity eval confirms: raw Qwen3 outperforms enriched on investigation tasks. V3 models needed it less than V1. | Model can reliably signal its own task domain and select appropriate tooling. |
| **BST enrichment templates** | Capability-compensation | Injects domain methodology because the model doesn't apply the right framework unprompted. ST-010 rigidity finding: info-only = full enrichment on reasoning domains. | Model applies appropriate analytical methodology without scaffolding. |
| **BST register-shift domains** (orientation, meta_cognitive, philosophical) | Transport-compensation | Breaking momentum and providing cognitive space isn't about model capability. It's about protecting reflective work from task-oriented context pressure. | Never. The system should always honor the human's request to step back. |
| **BST slot resolution** | Capability-compensation | Extracts structured slots (branch_name, language, target) because models miss contextual parameters under pressure. | Model reliably extracts all task parameters without missing slot values. |
| **Working Memory Buffer** | Mixed | Entity tracking across turns: capability-compensation for models that lose state. But the *architecture* — knowing what the current task is — is transport-compensation. | Entity tracking retires. Objective persistence stays. |
| **Personality Loader** | Transport-compensation | Behavioral contract between operator and agent. Not compensating for a capability gap — defining the operating parameters. Frontier models are MORE in need of this, not less, because they have broader behavioral range. | Never. Becomes more important as models become more capable. |
| **Tool Fallback Chain** | Capability-compensation | Pattern-matched error recovery because models don't reliably produce working tool calls on first attempt. V3's tool-calling RL training already reduced this layer's workload. | Model produces valid, executable tool calls consistently. |
| **Meta-Reasoning Gate** | Mixed | JSON validation / schema check: capability-compensation. The *gate itself* — blocking execution until output is validated — is transport-compensation. | JSON generation retires. The gate pattern stays (applied to other validation concerns). |
| **Graph Workflow Engine** | Mixed | Multi-step plan tracking: capability-compensation. The *failure recovery and branching structure* — knowing which path to take when a step fails — is transport-compensation. | The model can manage multi-step state internally. The plan library for known workflow types stays. |
| **Organization Kernel** | Transport-compensation | Command structure, PACE protocols, role definitions. This is governance architecture. Not compensating for model limitations — defining operating procedures. | Never. Governance needs grow as agent capability grows. |
| **Supervisor Loop** | Transport-compensation | Loop and stall detection is governance, not compensation. A superintelligent model that loops is still looping. An agent operating without resource and behavior oversight is unsafe regardless of capability. | Never. Oversight is structural. |
| **Tiered Tool Injection** | Capability-compensation | Lists available tools because models don't know what's callable. `_16_tool_registry.py` exists because the model explores the filesystem instead of calling tools by name. | Model has persistent awareness of available tools. |
| **Conversational Insight Capture** | Capability-compensation | Extracts explicit signals (corrections, decisions, preferences) because models don't reliably retain them across turns. | Model maintains accurate working memory of user signals from conversation. |
| **Selective Memorizer** | Mixed | Signal discrimination (deciding what's worth remembering): capability-compensation. The *act of recording* for future sessions: transport-compensation. | Signal discrimination improves, but long-term memory persistence stays. |
| **Memory Classification** | Capability-compensation | Tags memories with validity, relevance, utility, source axes because models don't maintain structured knowledge provenance. | Model produces and maintains structured knowledge provenance natively. |
| **Memory Enhancement** | Mixed | Temporal decay and deduplication: capability-compensation (models forget to update stale knowledge). Relational exemptions (some memories should never decay): transport-compensation. | Decay logic retires. Explicit preservation policies stay. |
| **Ontology Layer** | Capability-compensation | Entity resolution and disambiguation across sources. Improves with better models. | Model reliably links entity references across heterogeneous sources without assistance. |
| **Error Comprehension** | Capability-compensation | Structured error diagnosis because models don't reliably interpret raw error output. Anti-actions prevent loops. | Model interprets error output accurately and selects correct recovery strategy. |
| **Action Boundary** | Transport-compensation | Authorization gate for irreversible/high-consequence actions. **This is the most purely transport-compensation layer in the stack.** A GPT-5 that deletes production data without authorization is still a failure. The policy enforcement — not model capability — is the guarantee that matters. | Never. The authorization gate is a governance requirement independent of model capability. |
| **Epistemic Integrity** | Transport-compensation | Provenance tracking and confabulation detection. Claim verification isn't about compensating for model limitations — it's about maintaining epistemic standards. A more capable model can confabulate more convincingly. | Never. Becomes more critical as model outputs become more persuasive. |
| **Staging Tier** | Transport-compensation | Session state management and lifecycle tracking. Not compensating for a capability gap — maintaining operational hygiene. | Never. Session state management is infrastructure. |
| **Orientation Stack** | Mixed | **Artifact Registry / Completion Tracker:** capability-compensation (context-loss recovery). **Reasoning State persistence across compression:** transport-compensation (the context boundary is a structural reality, not a capability gap). **Tool Registry:** capability-compensation. | Artifact/completion tracking retires. Compression bootstrap stays. |
| **Loop Recovery & Memory Surgery** | Mixed | Loop detection and recovery: capability-compensation (and supervisor overlap — Supervisor handles this better). False recovery detector and loop-epoch isolation: transport-compensation (the surgeon arriving for the next loop, not the current one, is an architectural pattern that holds regardless of model quality). | Loop detection retires. Loop-epoch isolation stays. |
| **Sleep Consolidation** | Transport-compensation | Background consolidation isn't compensating for a model limitation — it's maintaining the knowledge base during idle time. A more capable model still benefits from deduplication, anti-pattern extraction, and interaction modeling during off-peak cycles. | Never. Background maintenance is infrastructure. |
| **Document Library** | Transport-compensation | Persistent reference storage with retrieval. The model's context window doesn't replace a library. | Never. Persistent storage is infrastructure, not capability compensation. |
| **OSS Service** | Transport-compensation | Intelligence ingestion, deduplication, and provenance tracking at scale. This is a data infrastructure layer. More capable models still need a clean, sourced data substrate. | Never. Data quality is infrastructure. |
| **SWARMFISH** | Mixed | Committee consensus for prediction under uncertainty: arguably capability-compensation (better models reason better under uncertainty). But Bayesian calibration tracking and adversarial input detection: transport-compensation. | Prediction quality improves. Calibration tracking and adversarial detection stay. |
| **Skills System** | Mixed | Procedural skills that encode known workflows: partially capability-compensation (models with better instruction following need fewer procedural guides). But skills as operator-installed domain knowledge: transport-compensation (the operator's right to install their own methodology is structural). | Generic procedural guidance retires. Domain-specific operator methodology stays. |
| **A2A Layer** | Transport-compensation | Multi-agent coordination protocol. Governance and interoperability, not capability compensation. | Never. Grows in importance as multi-agent use increases. |

---

## Summary: Classification Distribution

| Category | Count | Layers |
|----------|-------|--------|
| **Capability-compensation** | 9 | BST enrichment, BST slot resolution, Tool Fallback Chain, Tiered Tool Injection, Conversational Insight Capture, Memory Classification, Ontology Layer, Error Comprehension, Tool Registry |
| **Transport-compensation** | 12 | BST register-shift, Personality Loader, Organization Kernel, Supervisor Loop, Action Boundary, Epistemic Integrity, Staging Tier, Sleep Consolidation, Document Library, OSS Service, A2A Layer, Document Library |
| **Mixed** | 8 | Working Memory, Meta-Reasoning Gate, GWE, Selective Memorizer, Memory Enhancement, Orientation Stack, Loop Recovery/Surgery, SWARMFISH, Skills |

---

## Architectural Implications

**Layers that may shrink or retire in 2-3 model generations:**
- BST enrichment (reasoning domains already showing raw ≥ enriched)
- Tool Fallback Chain (RL-trained tool calling reduces failure rate)
- Error Comprehension (model error interpretation is improving rapidly)
- Tiered Tool Injection (registry injection exists because of context window limitations)

**Layers that become more critical as models improve:**
- Action Boundary (more capable models = higher stakes for unauthorized irreversible actions)
- Epistemic Integrity (more persuasive outputs = harder to detect confabulation without mechanistic verification)
- Personality Loader / Organization Kernel (greater behavioral range = greater need for behavioral contract)
- Supervisor Loop (more autonomous agents = more governance needed, not less)

**Investment guidance:**
- New capability-compensation layers: ask "is this a temporary bridge or a permanent fixture?" If temporary, build it cheap and fast.
- New transport-compensation layers: build them to last. Document the invariants. They'll outlive the models they govern.

---

*This classification is a snapshot. Re-evaluate when a new model generation is deployed. The rigidity eval methodology is the right instrument for determining when a capability-compensation layer becomes dead weight.*
