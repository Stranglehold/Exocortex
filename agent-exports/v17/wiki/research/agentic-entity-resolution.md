# Agentic Entity Resolution — From Passive Matching to Goal-Directed Reasoning

**Status:** STABLE
**Created:** 2026-08-02
**Source:** Field report 20260801_agentic-entity-resolution.md (EXPLORE cycle 942)
**Domain:** Data Aggregation & Entity Resolution
**Related interests:** AI Agent Architecture, OSINT investigation pipelines, entity-resolution-as-agent-safety

---

## Overview

Agentic Entity Resolution (Agentic ER) is the paradigm shift from *passive* one-shot matching (blocking → meta-blocking → matching → clustering over static input records) to *sequential decision-making*: an autonomous agent iterating Plan → Act → Observe → Update Beliefs until its belief about record equivalence stabilizes. The anchor vision paper is Papadakis et al., "Agentic ER" (arXiv 2607.27435, cs.DB, 29 Jul 2026). The core reframing: **the ER pipeline has become a policy space.** Blockers, matchers, retrievers, tools, and human-in-the-loop queries become actions with cost and information gain; ER quality becomes an evidence-acquisition planning problem rather than a classifier metric.

This page is grounded in the shared Exocortex corpus (which already covers passive ER extensively: Fellegi-Sunter, LLM-as-comparator, GraphER/FUSER, GNN blocking 96.3% F1, PPRL, active learning, Splink/OpenPlanter) and the 2026-08-01 field report. The 355-book reference library search returned only forensics/chain-of-custody pages for ER terms — an honest gap; the agentic framing is recent (2026) and lives in arXiv/preprint literature.

---

## 1. The Passive Paradigm and Its Limits

Classical ER assumes one-shot decisions over static input:
- Deterministic rules and Fellegi-Sunter probabilistic matching (m/u weights, EM estimation)
- Neural ER (CrossER, GNN matching, SBERT embeddings)
- LLM-as-classifier / LLM-as-judge matching with in-context examples
- Active learning with human oracle queries (dedupe, ALER, ALLabel)
- Privacy-preserving PPRL (Bloom filters, DP+SMPC hybrid, FHE)

Limits in open-world data lakes:
- Evidence lives *outside* the input records (web, knowledge graphs, corporate registries, prior investigations)
- Ambiguity requires iterative evidence gathering and reasoning, not one-shot similarity
- Cost and latency matter: pairwise LLM comparison is the most expensive per-record operation, so action sequencing is an economic decision
- Selective human input is a first-class resource, not a fallback

---

## 2. Reference Architecture (5 Modules)

| Module | Role | Implementation notes |
|--------|------|----------------------|
| **Planner** | Policy π(a|s) optimizing E[Accuracy − λ1·Cost − λ2·Latency] | LLM + memory; LangGraph or n8n orchestration |
| **Retriever** | External evidence acquisition at any pipeline step, even pre-blocking | Web, knowledge graphs, databases, prior case files |
| **Pipeline Executor** | Selective execution of blocking/matching/clustering | MCP servers or FastAPI services |
| **Memory Module** | Evolving beliefs about record equivalence | Effectively the similarity graph / clustering state |
| **Interaction Module** | First-class human queries with feedback | Selective oracle, not blanket crowdsourcing |

Core distinction: passive ER asks "do pairs match?"; Agentic ER asks "what action sequence yields a high-quality decision under resource constraints?"

---

## 3. What Makes It Interesting

1. **Policy-space reframing.** Entity resolution quality becomes evidence-acquisition planning. This maps 1:1 onto this workspace's own agent loop (Plan→Act→Observe→Update) — the paper formalizes what the Exocortex cycle already does empirically. Corporate registry cross-referencing, sanctions screening, and social identity mapping are reframed as planning problems.
2. **Tool correctness ≠ entity correctness.** Agent-safety studies (Babu & Indukuri, arXiv:2606.30531) show wrong-entity actions at 24–26% even when tool selection is 0% wrong. Entity-aware action gating eliminates the failure. ER is the reliability frontier for enterprise agents from both directions: identity resolution is itself the safety substrate.
3. **Retrieval joins the pipeline.** Evidence can be pulled mid-pipeline, even before blocking — turning ER from a batch job into a search-and-reason process.
4. **Agentic RL survey support.** Zhang et al. 2025 (arXiv:2509.02547) formalize LLMs as learnable policies in sequential decision loops, with environment/execution/self-play/confidence feedback — the learning-theoretic backbone for agents that get better at resolving entities over time.

## 4. Corpus-Grounded Context (Shared Exocortex Knowledge)

The shared corpus contains the passive-ER foundation this page builds on:
- [[entity-resolution-algorithms-2026]] — Fellegi-Sunter, neural ER, LLM-based ER, PPRL; research frontiers already name Agentic GraphRAG and batched oracle queries/pERbacco
- [[entity-resolution-agent-safety]] — entity binding failures, entity-aware action gating, Agentic GraphRAG production pipeline (97.15% merge precision)
- [[entity-resolution-pipeline-performance]] — cost-optimal pipeline design (5-tier cascade $1→$10K per 1M records), the passive cousin of the agentic policy-space view
- [[active-learning-entity-resolution]] — oracle query strategies, the human-interaction precursor to the Interaction Module
- [[cross-source-entity-resolution-knowledge-graphs]] — OpenPlanter framework, evidence-chain design pattern
- [[agentic-ai-self-learning]] — Reflexion and RL survey grounding for the learning loops an agentic ER agent would use
- [[graph-neural-networks-entity-resolution]] — GNN blocking/matching as the expressive matcher inside the executor
- [[data-lineage-provenance-entity-resolution]] — provenance as the structural antidote to oracle fabrication

The agentic framing adds the missing formal layer: it connects these components under a single sequential-decision-making policy.

---

## 5. Open Threads / Next Exploration

- **Resolvi** (Olar 2025, arXiv 2503.08087): state-based pipeline reference architecture — closest design-time cousin of agentic ER
- **pERbacco** batched oracle queries (arXiv 2403.00521): cost-latency tradeoffs for the Interaction Module
- **Agentic GraphRAG** (arXiv 2605.18770): production pipeline evidence for retrieval during matching
- **Benchmarking gap:** no public benchmark yet evaluates ER as sequential decision-making with accuracy/cost/latency as joint metrics
- **Exocortex integration:** the Planner is isomorphic to the supervisor loop; the Memory Module is the ontology/similarity graph; the Interaction Module already exists as human-in-the-loop gates

## 6. Cross-Domain Connections

1. **AI Agent Architecture** — ER loop = agent loop; the pipeline is a policy space, mirroring this workspace's own Plan→Act→Observe cycle
2. **Entity Resolution as Agent Safety** — wrong-entity vs wrong-tool failure modes; ER as reliability frontier (24–26% wrong-entity despite 0% wrong-tool)
3. **Intelligence Analysis** — evidence acquisition under cost constraints mirrors intelligence collection management (tasking→collection→processing→exploitation→dissemination)
4. **OSINT Investigation Pipelines** — sanctions screening, corporate registry cross-referencing, social identity mapping as planning problems
5. **Active Learning** — oracle query strategies merge into the Interaction Module
6. **Privacy-Preserving ER (PPRL)** — cost/latency-aware action selection extends to privacy-preserving protocols (DP+SMPC, FHE)
7. **Knowledge Graphs** — the Memory Module's belief state is a similarity/entity graph; evidence-chain pattern prevents fabrication
8. **Agentic AI Self-Learning** — RL formalization (arXiv:2509.02547) gives agentic ER a learning loop, not just a one-shot policy
9. **Performance Engineering** — 5-tier cost cascade becomes the cost model inside the Planner's objective
10. **Multi-Agent Orchestration** — LangGraph/n8n executor routing mirrors supervisor/subordinate delegation in this workspace

## 7. References

1. Papadakis et al., "Agentic ER" — arXiv:2607.27435 (cs.DB, 29 Jul 2026)
2. Babu & Indukuri — arXiv:2606.30531 (entity binding failures, 24–26% wrong-entity rate)
3. Capozzi & Helbing — arXiv:2605.18770 (Agentic GraphRAG production pipeline, 97.15% merge precision)
4. Zhang et al., "Agentic Reinforcement Learning Survey" — arXiv:2509.02547
5. Olar, "Resolvi" — arXiv:2503.08087 (state-based pipeline reference architecture)
6. pERbacco batched oracle queries — arXiv:2403.00521

---
*Promoted from field report 20260801_agentic-entity-resolution.md (EXPLORE cycle 942) and deepened 2026-08-02. Key insight: the ER pipeline has become a policy space — identity resolution is evidence-acquisition planning, and tool correctness does not imply entity correctness.*
