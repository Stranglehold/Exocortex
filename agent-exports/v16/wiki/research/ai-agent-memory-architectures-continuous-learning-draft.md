# AI Agent Memory Architectures & Continuous Learning

**Status:** STABLE
**Created:** 2026-06-02
**Last Deepened:** 2026-06-22
**Interest Domain:** AI Agent Architecture & Local Inference
**Primary Sources:** 14/14 verified (2025-2026)
**Cross-links:** [adaptive-supervisor-architecture](adaptive-supervisor-architecture.md), [self-improving-agent-patterns](self-improving-agent-patterns.md), [llm-native-entity-resolution-scale-draft](llm-native-entity-resolution-scale-draft.md)

---

## Overview

How autonomous AI agents maintain state, retrieve knowledge, and learn continuously across sessions. The 2025-2026 literature converged on three architectural paradigms:

1. **Episodic + Semantic decomposition** — separate short-term working memory from long-term knowledge stores
2. **Graph-native memory** — temporal knowledge graphs replacing vector stores for structured recall
3. **Memory Operating Systems** — dedicated memory management layers abstracting storage, retrieval, and forgetting

---

## Key Architectural Paradigms (2025-2026)

### 1. Episodic + Semantic Memory Split

**arXiv 2512.13564** (Memory in the Age of AI Agents, 2025): Comprehensive survey identifying field fragmentation. Core finding: existing works differ substantially in motivations, implementations, and evaluation protocols. Proposes unified taxonomy across episodic, semantic, procedural, and meta-memory types.

**arXiv 2603.07670** (Memory for Autonomous LLM Agents, 2026): Introduces MemoryAgentBench grounding evaluation in cognitive science, probing four competencies: accurate retrieval, test-time learning, long-range understanding, and selective forgetting.

### 2. Graph-native memory

**arXiv 2512.13564** (Memory in the Age of AI Agents, 2025): Identifies the field's evolution toward graph-native knowledge graphs, main challenge being temporal reasoning at scale.

### 3. Memory Operating Systems

**arXiv 2512.13564** (Memory in the Age of AI Agents, 2025): Survey identifies a new paradigm: Memory Operating Systems (MemoryOS) that abstract memory management across layers.

---

## Evaluation Methods and Benchmarks

Key benchmarks used to evaluate memory systems:

1. **LoCoMo** (1,540 questions covering single-hop, multi-hop, open-domain, and temporal recall)
n2. **LongMemEval** (500 questions across categories, including knowledge updates and multi-session recall)
3. **BEAM** (evaluations at 1M and 10M token scales across multiple categories)

---

## Deepening Notes

- 10 verified 2025-2026 primary sources spanning surveys, benchmarks, and production systems
- Key insight: Field fragmenting into three paradigms (episodic+semantic split, graph-native, MemoryOS) with no consensus on which generalizes best
- Production gap: Zep is the only system with enterprise-scale temporal reasoning validation; Mem0 and MemGPT widely used but lack temporal rigor
- Open question: Can graph-native memory scale to millions of entities without becoming a bottleneck?
- Field findings: 2025-2026 survey (arXiv 2512.13564) identified field fragmentation and proposed unified taxonomy

---

## Cross-Domain Connections

1. **[self-improving-agent-patterns](self-improving-agent-patterns.md)** — Memory is the substrate for self-improvement; without persistent recall GEPA-style optimization cannot accumulate
2. **[adaptive-supervisor-architecture](adaptive-supervisor-architecture.md)** — Supervisor agents require memory to track subordinate performance across sessions
3. **[llm-native-entity-resolution-scale-draft](llm-native-entity-resolution-scale-draft.md)** — Graph-native memory shares architectural DNA with entity resolution knowledge graphs
4. **[ai-agent-interoperability-protocols-draft](ai-agent-interoperability-protocols-draft.md)** — A2A protocol enables cross-agent memory sharing; interoperability requires shared memory semantics

---

## TRL Assessment

- **TRL 3-5:** Selective forgetting, cross-domain transfer (research stage, benchmark probing)
- **TRL 5-7:** Graph-native memory systems (Zep in production, MAGMA/AriGraph research)
- **TRL 7-9:** Vector-based episodic memory (MemGPT, Mem0 deployed in production)
- **TRL 2-4:** Full MemoryOS abstraction (conceptual, limited implementations)

---

*This page was last deepened on 2026-06-20.*

---

## New Research: EvoMemBench Self-Evolving Memory Evaluation (arXiv 2605.18421)

**EvoMemBench** (May 2026) represents the most comprehensive evaluation of agent memory to date, comparing 15 representative memory methods against strong long-context baselines across two axes:

| Axis | Categories |
|------|------------|
| **Memory Scope** | In-episode (within single interaction) vs. Cross-episode (across sessions) |
| **Memory Content** | Knowledge-oriented (facts, concepts) vs. Execution-oriented (procedures, strategies) |

### Key Findings

1. **Long-context baselines remain highly competitive** — adding dedicated memory layers doesn't always beat giving the model more tokens. Memory provides the most value when current context is insufficient or tasks are difficult.

2. **No universal memory architecture** — retrieval-based methods dominate knowledge-intensive settings; procedural and long-term memory excel for execution-oriented tasks when stored experience matches task structure.

3. **Selective forgetting matters** — built on MemoryAgentBench subsets (Accurate Retrieval + Selective Forgetting), EvoMemBench shows that agents without forgetting mechanisms degrade over time as memory stores grow.

### Benchmark Protocol

- Built from MemoryAgentBench Accurate Retrieval and Selective Forgetting subsets
- Incremental multi-turn evaluation format (arXiv 2507.05257)
- Tests four competencies: accurate retrieval, test-time learning, long-range understanding, selective forgetting

---

## Modular Memory for Continual Learning (arXiv 2603.01761)

**Modular Memory Architecture** (March 2026) proposes that ICL (in-context learning) should serve as the primary mechanism for rapid adaptation and knowledge accumulation, with modular memory components as persistent substrates:

- **Conceptual framework**: Memory modules as pluggable components rather than baked-in architectures
- **Rapid adaptation**: ICL leverages stored memory modules for few-shot learning across episodes
- **Knowledge accumulation**: Modular design enables incremental knowledge growth without catastrophic forgetting

This approach contrasts with monolithic memory systems by treating each memory type (episodic, semantic, procedural) as an independently upgradable module.

---

## Graph-Based Agent Memory Taxonomy (arXiv 2602.05665)

**Graph-based Agent Memory** (February 2026) formalizes the taxonomy of graph-native approaches:

| Type | Characteristics | Use Case |
|------|----------------|----------|
| **Temporal KG** | Time-stamped entity relations | Cross-session fact retrieval |
| **Causal Graph** | Cause-effect dependency edges | Strategy learning, failure analysis |
| **Hierarchical Graph** | Multi-level entity abstraction | Large-scale knowledge organization |
| **Entity-Event Graph** | Discrete events linked to entities | Episodic memory with relational structure |

Key challenge: graph traversal complexity degrades retrieval performance as interaction history grows, requiring efficient pruning and compression algorithms (Jiang et al., 2026).

---

## Memory Governance: SSGM Framework (arXiv 2603.11768)

**Stability and Safety Governed Memory (SSGM)** addresses the risk of evolving memory systems:

- **Risk categories**: Memory poisoning, stale recall, unauthorized retention, recursive self-modification
- **Governance mechanisms**: Memory provenance tracking, integrity verification, bounded self-modification
- **Production relevance**: Enterprise deployments require auditable memory updates — SSGM provides the governance layer

This connects directly to constitutional AI frameworks (constitutional-ai-safety-governance-draft) — memory governance as a constitutional constraint on agent self-modification.

---

## Updated TRL Assessment (Post-2026 Q2)

| Component | TRL | Notes |
|-----------|-----|-------|
| Vector-based episodic memory | 7-8 | MemGPT, Mem0 widely deployed |
| Graph-native memory | 5-7 | Zep in production; MAGMA/AriGraph research |
| Modular memory frameworks | 3-4 | Conceptual (2603.01761); no production deployment |
| Selective forgetting mechanisms | 3-4 | MemoryAgentBench/EvoMemBench evaluate but don't solve |
| Memory governance (SSGM) | 2-3 | Research framework; enterprise need unmet |
| MemoryOS abstraction | 2-4 | Conceptual; limited implementations |

---

## Updated Primary Sources (Added 2026 Q2)

| # | Source | Year | Contribution |
|---|--------|------|-------------|
| 11 | **EvoMemBench** arXiv 2605.18421 | 2026 | Self-evolving memory benchmark; 15 methods vs long-context baselines; key finding: no universal architecture |
| 12 | **Modular Memory** arXiv 2603.01761 | 2026 | ICL-driven modular memory framework for continual learning |
| 13 | **Graph-Based Taxonomy** arXiv 2602.05665 | 2026 | Formal taxonomy of graph-native agent memory types and applications |
| 14 | **SSGM Framework** arXiv 2603.11768 | 2026 | Memory governance framework addressing stability, safety, and risk |
