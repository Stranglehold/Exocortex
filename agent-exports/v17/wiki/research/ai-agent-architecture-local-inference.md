# AI Agent Architecture & Local Inference

**Status:** STABLE | **Created:** 2026-05-20 | **Last deepened:** 2026-05-20

## Overview

AI agent architecture and local inference — the technical frontier of autonomous agent design. Research here directly informs Exocortex design decisions. Six subdomains explored with primary-source arXiv papers and Exocortex cross-references.

1. Context management innovations
2. Self-improving agent patterns
3. Local inference optimization
4. Autonomous coding agents (ATLAS-style)
5. Memory architecture (episodic/semantic/procedural)
6. Agentic tool use (MCP, tool discovery)

---

## 1. Context Management Innovations

### PolyKV: Shared Asymmetrically-Compressed KV Cache Pool (Patel & Joshi, arXiv:2604.24971)

**Problem:** Multi-agent inference systems require N independent KV caches — one per agent — for the same shared document context. This is O(N) memory, prohibitive for concurrent agent operations.

**Solution:** PolyKV writes a single compressed KV state once and injects it into N independent agent contexts via HuggingFace DynamicCache objects. Compression is asymmetric: Keys at int8 (q8_0) to preserve softmax stability, Values at TurboQuant MSE 3-bit (FWHT + Lloyd-Max quantization).

**Key findings:**
- Stable 2.91× compression ratio across all configurations
- On Llama-3-8B with 15 agents sharing 4K tokens: KV cache memory reduced from 19.8 GB to 0.45 GB (97.7% reduction)
- PPL delta invariant to agent count; quality *improves* as context length increases
- PPL inversion finding: at 1,851 coherent tokens, compressed cache surpasses full-precision baseline (-0.26% PPL delta)
- Hypothesis: FWHT quantization noise acts as implicit regularization on redundant coherent tokens

**Exocortex relevance:** If Exocortex ever runs multiple concurrent analysis agents on the same source material, PolyKV's shared-pool model eliminates redundant KV cache computation. The asymmetric compression principle (higher precision for Keys, aggressive compression for Values) mirrors Exocortex's own tiered injection system where critical metadata (domain, confidence) gets priority representation.

## 2. Self-Improving Agent Patterns

### Experiential Reflective Learning (ERL) — Allard et al., arXiv:2603.24639

**Idea:** Agents reflect on task trajectories to generate heuristics that transfer across tasks. At test time, relevant heuristics are retrieved and injected into context.

**Results:** +7.8% on Gaia2 over ReAct baseline, outperforming prior experiential learning methods. Selective retrieval is essential; heuristics provide more transferable abstractions than few-shot trajectory prompting.

**Exocortex connection:** The heuristic extraction loop mirrors Exocortex's own autoresearch concept — reflecting on outcomes to surface reusable patterns. ERL's selective retrieval matches Exocortex's context pruner philosophy of injecting only task-relevant knowledge.

### Adaptive Data Flywheel (Shukla et al., arXiv:2510.27051)

**Production validation:** NVIDIA's NVInfo AI deployed a MAPE-driven (Monitor-Analyze-Plan-Execute) data flywheel for an enterprise MoE knowledge assistant serving 30K employees. Over 3 months, 495 negative samples identified routing errors (5.25%) and query rephrasal errors (3.2%). Fine-tuning a Llama 3.1 8B replacement for Llama 3.1 70B achieved 96% routing accuracy — 10× model size reduction with 70% latency improvement.

**Exocortex connection:** The MAPE control loop (monitor failures → analyze patterns → plan improvements → execute fine-tunes) validates Exocortex's supervisor loop architecture. Both systems close the feedback loop between production errors and system improvement.

### GEPA: Self-Modifying Prompt Evolution (see [[gepa]])

Already documented in wiki research. GEPA's iterative reflection cycles for prompt optimization achieve self-improvement without fine-tuning — directly applicable to Exocortex's prompt management.

### SRGen: Self-Reflective Generation at Test Time (arXiv:2510.02919)

LLMs generate multiple candidate outputs, then critically evaluate their own outputs in a structured reflection format. Present in local papers directory.

**Exocortex connection:** SRGen's generate-then-criticize pattern matches Exocortex's epistemic integrity layer, which audits claims against evidence ledgers.

## 3. Local Inference Optimization

### Quantization Advances

**TurboQuant (Google Research, ICLR 2026):** FWHT rotation followed by Lloyd-Max quantization enables 3-bit Value compression with distortion bound D_mse ≤ (√3π/2)·(1/4^b) ≈ 0.03 at b=3. Used in PolyKV for asymmetric K/V compression.

**SQuat (arXiv:2508.08256):** Constructs a subspace spanned by query tensors to capture critical task-related information. Enforces that quantization error remains orthogonal to this subspace. No model fine-tuning required. 2.17–2.82× peak memory reduction, 2.45–3.60× throughput improvement.

**MixKVQ:** Query-aware mixed-precision KV cache quantization — identifies critical key channels needing higher precision while applying per-token quantization for values. Matches full-precision baseline on complex reasoning tasks.

**NQKV (arXiv:2505.16210):** Elements within each KV cache block follow a normal distribution, enabling per-block quantile quantization achieving information-theoretically optimal error. 9.3× throughput improvement vs. no KV cache.

**FIER (Fine-Grained KV Retrieval):** Uses 1-bit quantized keys to estimate token importance for retrieval. Matches full KV performance using only 11% cache budget, reducing decoding latency by 1.2–1.5×.

### Exocortex Connection

Local inference optimization directly impacts Exocortex's ability to run on consumer hardware. The asymmetric K/V quantization pattern (higher precision for Keys, aggressive for Values) aligns with Exocortex's tiered information representation. TurboQuant's FWHT rotation for outlier redistribution mirrors the context pruner's approach of redistributing attention rather than truncating.

## 4. Autonomous Coding Agents (ATLAS-style)

**Concept from interests.md:** ATLAS represents autonomous coding agents that use temperature escalation retry, nightly LoRA fine-tuning, and self-hosted evaluation. No primary-source paper was retrieved for ATLAS in this deepening cycle, but the pattern is well-established.

**Exocortex connection:** The AUTONOMOUS_AGENCY_ARCHITECTURE.md spec (Feb 2026) proposes the reactive-to-autonomous shift: an agency that manages standing tasks, monitors domains, and escalates only when necessary. ATLAS-style coding agents that refine their own code map to Exocortex's self-improvement design goals.

**Cross-reference:** The Adaptive Data Flywheel (Shukla et al., §2) demonstrates production viability of closed-loop improvement for AI agents, validating the MAPE control loop that could drive autonomous coding cycles.

## 5. Memory Architecture (Episodic/Semantic/Procedural)

### Transformers Remember First, Forget Last (arXiv:2603.00270)

**Finding:** LLMs exhibit dual-process interference analogous to human memory. Primacy effect (better recall of early information) and recency degradation when context fills. This informs memory architecture design for agents operating over long sessions.

**Exocortex connection:** This directly validates Exocortex's stateful injection system, which preserves critical early-session context while allowing mid-session content to be compressed. The injection gate's three-phase transition (full context → masked → summarized) is a direct architectural response to the primacy/recency asymmetry documented in this paper.

### Sleep-Inspired Memory Consolidation for Resolving Proactive Interference (arXiv:2603.14517)

**Finding:** Sleep-inspired consolidation cycles can resolve proactive interference in LLMs by reorganizing memory representations during offline periods.

**Exocortex connection:** Exocortex's sleep consolidation subsystem (phases 0-3: staging, deduplication, chunking/anti-pattern capture, operator modeling) operationalizes this principle. The existing [[sleepgate]] and [[proactive-interference]] wiki pages document the theoretical grounding.

### Memory Types and Exocortex Mapping

- **Episodic memory:** Session-level conversation history. Exocortex uses context pruner and injection gate to manage.
- **Semantic memory:** Long-term knowledge via memory_save/memory_load (FAISS vector store). Exocortex's memory tools provide persistent cross-session recall.
- **Procedural memory:** Reusable workflows captured as skills ([[skill capture principle]]). Exocortex's skill system at /a0/usr/skills/ stores procedural knowledge.

### Existing Exocortex Memory Concepts

- [[context-pruner]]: Compresses resolved results before context fills
- [[injection-gate]]: Three-phase context management
- [[stateful-injection]]: Persistent state across turns
- [[catastrophic-forgetting]]: How overwriting early context degrades performance
- [[proactive-interference]]: Old information interfering with new processing
- [[sleepgate]]: Offline consolidation cycles


## 6. Agentic Tool Use (MCP, Tool Discovery)

### MCP-Zero: Active Tool Discovery (Fei et al., arXiv:2506.01056)

**Problem:** Current LLM agents inject pre-defined tool schemas into prompts, reducing models to passive selectors. For large tool ecosystems (2,797 tools across 308 MCP servers, 248.1K tokens), this is infeasible.

**Solution:** MCP-Zero restores tool discovery autonomy to LLMs themselves through three mechanisms:
1. **Active Tool Request:** Agents autonomously generate structured requests specifying exact tool requirements
2. **Hierarchical Semantic Routing:** Two-stage algorithm matching requests to relevant servers and tools via semantic alignment
3. **Iterative Capability Extension:** Agents progressively build cross-domain toolchains while maintaining minimal context footprint

**Results:** 98% reduction in token consumption on APIBank while maintaining accuracy. Consistent multi-turn performance that scales with tool ecosystem growth.

**Exocortex connection:** MCP-Zero's active discovery pattern mirrors Exocortex's dynamic-tool-selection system, which filters available tools per turn based on BST domain classification. Both systems replace passive full-schema injection with context-aware filtering. The hierarchical semantic routing matches Exocortex's injection gate tiered structure.

### Agent-First Tool API Paradigm (Production SaaS, 85 registered tools across 6 domains)

**Five architectural mismatches identified between conventional CRUD APIs and autonomous agents:**
1. Exact-identifier dependence
2. Rendering-oriented responses
3. Single-shot interaction assumptions
4. User-equivalent authorization
5. Opaque error semantics

**Solution — Six-Verb Semantic Protocol:** Search, Resolve, Preview, Execute, Verify, Recover — decomposing tool interactions into phases with structured decision-support metadata (confidence scores, evidence chains, suggested next actions).

**Results:** 88% end-to-end task success rate vs. 64% for optimized CRUD baselines (+37.5%), 72.7% reduction in human interventions, 5.8× improvement in autonomous error recovery.

**Exocortex connection:** The Six-Verb protocol's Recover phase aligns with Exocortex's error comprehension layer, which parses error context for autonomous recovery. The Normalized Tool Contract (confidence scores, evidence chains) mirrors the epistemic integrity layer's audit trail requirements.

### Existing Exocortex Tool Architecture

- **[[dynamic-tool-selection]]:** BST-domain-based per-turn tool filtering
- **[[error-comprehension]]:** Autonomous error parsing and recovery
- **[[epistemic-integrity]]:** Audit trails and evidence chains for every claim


---

## Exocortex Cross-Domain Connections

This page connects to 7 existing Exocortex concepts and 1 research page:

1. **Context Pruner ↔ PolyKV shared-pool model:** Both reduce redundant token storage. Context pruner removes stale intermediate steps; PolyKV eliminates redundant KV cache copies. The shared-pool abstraction could inspire Exocortex to cache shared context once across multiple analysis threads.

2. **Dynamic Tool Selection ↔ MCP-Zero active discovery:** BST-domain-based tool filtering mirrors MCP-Zero's hierarchical semantic routing. Both replace full-schema injection with context-aware selection, achieving token efficiency.

3. **Epistemic Integrity ↔ Agent-First Tool API Normalized Tool Contract:** Both require structured decision-support metadata (confidence scores, evidence chains, audit trails). Claims made by tools should be verifiable.

4. **Deterministic Scaffolding ↔ Self-Improving MAPE Control Loops:** The MAPE loop (Monitor→Analyze→Plan→Execute) provides deterministic structure for agent improvement — directly analogous to Exocortex's supervisor loop that monitors tool calls, analyzes domain, and executes interventions.

5. **Error Comprehension ↔ Six-Verb Protocol Recover Phase:** Both parse error context for autonomous recovery rather than requiring human intervention. Error comprehension provides the recovery logic; the Six-Verb protocol provides the architectural phase for it.

6. **Proactive Interference ↔ Dual-Process Memory Interference (Transformers Remember First, Forget Last):** The primacy/recency asymmetry documented in arXiv:2603.00270 validates Exocortex's tiered injection system, which preserves early critical context while compressing mid-session content.

7. **Autoresearch ↔ ERL Heuristic Extraction:** ERL reflects on task trajectories to generate transferable heuristics — identical in principle to autoresearch's gap-identification and knowledge-synthesis loop.

8. **[[Hermes Agent]] ↔ Autonomous Agency Architecture:** The reactive-to-autonomous shift proposed in AUTONOMOUS_AGENCY_ARCHITECTURE.md is the architectural complement to Hermes's tool-use reliability and recursive self-correction mechanisms.

---

## References

### Primary-Source Papers (Downloaded & Read)
- Patel, I. & Joshi, I. (2026). *PolyKV: A Shared Asymmetrically-Compressed KV Cache Pool for Multi-Agent LLM Inference.* arXiv:2604.24971.
- Fei, X., Zheng, X., & Feng, H. (2025). *MCP-Zero: Active Tool Discovery for Autonomous LLM Agents.* arXiv:2506.01056v4.
- Allard, M.-A., Teinturier, A., Xing, V., & Viaud, G. (2026). *Experiential Reflective Learning for Self-Improving LLM Agents.* arXiv:2603.24639v2.
- Shukla, A., Knowles, S., Madugula, M., Farris, D., Angilly, R., & Pombo, S. (2025). *Adaptive Data Flywheel: Applying MAPE Control Loops to AI Agent Improvement.* arXiv:2510.27051v1.

### ArXiv Searches (Abstracts Reviewed)
- Li, J., et al. (2025). *CommVQ: Commutative Vector Quantization for KV Cache Compression.* arXiv:2506.18879v1.
- *SQuat: Subspace-orthogonal KV cache quantization.* arXiv:2508.08256v2.
- *MixKVQ: Query-aware mixed-precision KV cache quantization.* (via arXiv search).
- Cai, Z., et al. (2025). *NQKV: A KV Cache Quantization Scheme Based on Normal Distribution Characteristics.* arXiv:2505.16210v1.
- *FIER: Fine-Grained and Efficient KV Cache Retrieval.* (via arXiv search).
- *Agent-First Tool API: A Paradigm for Autonomous Agent-Consumable APIs.* (via arXiv search, production SaaS).

### Exocortex Specs
- *AUTONOMOUS_AGENCY_ARCHITECTURE.md* — Operational design for persistent Agent-Zero operations.
- *CONTEXT_COMPRESSION_DESIGN_NOTE.md* — Observation masking and L1/L2 compression strategy.

### Existing Papers in /a0/usr/workdir/papers/
- *Self-Reflective Generation at Test Time* (arXiv:2510.02919) — SRGen generate-then-criticize pattern.
- *Transformers Remember First, Forget Last* (arXiv:2603.00270) — Dual-process interference in LLMs.
- *Learning to Forget: Sleep-Inspired Memory Consolidation* (arXiv:2603.14517) — Proactive interference resolution.
- *Can LLMs Perceive Time?* (arXiv:2604.00010) — Temporal awareness investigation.
- *Entropy and Attention Dynamics in Small Language Models* (arXiv:2604.03589) — TruthfulQA trace-level analysis.

### Related Wiki Pages
- [[context-pruner]] | [[injection-gate]] | [[stateful-injection]] | [[dynamic-tool-selection]]
- [[epistemic-integrity]] | [[error-comprehension]] | [[deterministic-scaffolding]]
- [[autoresearch]] | [[gepa]] | [[hermes-agent]] | [[sleepgate]]
- [[cognitive-bottleneck]] | [[proactive-interference]] | [[catastrophic-forgetting]]
