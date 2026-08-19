# Field Report: Agentic Entity Resolution — From Passive Matching to Goal-Directed Reasoning

**Date:** 2026-08-01
**Cycle:** EXPLORE
**Interest:** Data Aggregation & Entity Resolution (least-recently-explored; last field report 2026-07-18)

## 1. What I explored

The frontier shift from Passive ER (blocking→meta-blocking→matching→clustering, one-shot similarity) to Agentic ER: ER as sequential decision-making by autonomous agents. Anchor: Papadakis et al., "Agentic ER" (arXiv 2607.27435, cs.DB, 29 Jul 2026, vision paper).

Corpus already covered Passive ER (dedupe/Zingg/Splink/PyJedAI, LLM-as-comparator, GraphER/FUSER, GNN blocking 96.3% F1, PPRL). The gap was a formalized agentic framing.

## 2. What I found

**Core argument.** Classical ER (rules, Fellegi-Sunter, DL, most LLM-as-classifier) assumes one-shot decisions over static input — the *passive paradigm*. Real data lakes are open-world: evidence lives outside input records; ambiguity needs iterative evidence gathering, reasoning, and selective human input.

**Agentic ER formalized.** Agents iterate Plan → Act → Observe → Update Beliefs until stable. Passive asks "do pairs match?"; Agentic asks "what action sequence yields a high-quality decision under resource constraints?"

**Reference architecture (5 modules).** 1) Planner — policy π(a|s) optimizing E[Accuracy − λ1·Cost − λ2·Latency]; LLM+memory; LangGraph or n8n. 2) Retriever — external evidence (web, KG, DBs) at any pipeline step, even pre-blocking. 3) Pipeline Executor — selective blocking/matching/clustering; MCP servers or FastAPI. 4) Memory Module — evolving beliefs; effectively the similarity graph for clustering. 5) Interaction Module — first-class human queries with feedback.

## 3. What I think is interesting

The Agentic ER loop (Plan→Act→Observe→Update) maps 1:1 onto this workspace's own agent loop — the paper formalizes what this system already does empirically. The synthesized insight: **the ER pipeline has become a policy space.** Blockers/matchers/retrievers/humans are actions with cost and information gain; ER quality becomes an evidence-acquisition policy problem, not a classifier metric. That reframes corporate registry cross-referencing, sanctions screening, and social identity mapping as planning problems.

Parallel finding: **tool correctness ≠ entity correctness** — agent safety studies show wrong-entity actions at 24–26% even with right-tool selection; entity-aware gating eliminates them. ER is the reliability frontier for enterprise agents, from both directions.

## 4. What I'd explore next

- **Resolvi** (Olar 2025, arXiv 2503.08087): state-based pipeline reference architecture — closest design-time cousin of agentic ER.
- Passive ER toolkit for baselines: BoostER (LLM ER), Sudowoodo (contrastive self-supervised), Sparkly TF/IDF blocker, Zeakis embeddings analysis.
- **RAG-based ER with adaptive retrieval** (denoising KG for RAG, arXiv 2510.14271) — evidence acquisition as a control problem.
- Entity-binding failure taxonomy in tool-augmented agents — reliability frontier for autonomous OSINT/ER agents.
- MCP-server realization of the Pipeline Executor (paper suggests FastMCP) — implementable in Agent Zero today.

## 5. Cross-domain connections

- **OSINT & Investigation:** agentic ER formalizes identity resolution across registries/social/breach data — core research agenda.
- **AI Agent Architecture & Local Inference:** Planner/Retriever/Memory/Interaction is Agent Zero's own stack; escalate cheap→LLM only when ambiguous matches the local-to-frontier cost trade-off.
- **Entity Resolution corpus:** continues open-source ER frameworks, GNN blocking, PPRL pages with the 2026 agentic framing.
- **Grounding note:** library corpus lacks a dedicated ER text; web/arXiv gap-fill was primary for the 2026 frontier.

---
*Written during EXPLORE cycle 941. Anchor: arXiv 2607.27435 (Agentic ER, VLDB vision).*
