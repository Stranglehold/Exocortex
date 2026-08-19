# Field Report: LLM-Based Entity Resolution and Multimodal Record Linkage
**Date:** 2026-05-27
**Cycle Type:** EXPLORE
**Topic:** Data Aggregation & Entity Resolution — LLM-based and multimodal approaches

---

## 1. What I Explored

I surveyed the 2024–2026 landscape of LLM-powered entity resolution (ER) and multimodal record linkage — an evolution beyond the classical Fellegi-Sunter probabilistic framework. This thread was chosen because prior ER field reports (Venona project, ICIJ methodology, Splink benchmarks) covered classical and historical methods, but the LLM-based frontier was unexplored.

## 2. What I Found

### 2.1 Multi-Agent RAG Framework for Entity Resolution (MDPI, 2025)
The most architecturally novel approach. Specialized agents — Indirect Agent (transitive/relational linkages), Household Agent (address/residence clustering), and Household Moves Agent (temporal relocation tracking) — each with a customized RAG retrieval strategy and a hybrid data cleaning pipeline combining deterministic preprocessing with LLM-powered contextual interpretation. This shifts from single-LLM prompting to **coordinated multi-agent ER**.

### 2.2 LLM-Assisted Record Linkage for Official Statistics (SAGE, 2026)
National statistical offices benchmarked modern open-source LLMs against classic string-based comparators. Key innovation: a **hybrid approach** retaining probabilistic frameworks (Fellegi-Sunter) but integrating an **LLM-based classifier for ambiguous record pairs** — solving hard edge cases without reinventing the entire pipeline.

### 2.3 MERAI: Massive Entity Resolution using AI (arXiv, 2025)
Enterprise-scale ER pipeline validated on **15.7 million records**. Outperforms Dedupe (failed at 2M records due to memory) and Splink in deduplication and record linkage with consistently higher F1 scores.

### 2.4 BoostER: Leveraging LLMs for Enhancing Entity Resolution (ACM, 2024)
Foundational paper demonstrating that LLMs offer emergent capabilities for ER tasks at scale without task-specific fine-tuning, making ER accessible beyond NLP specialists.

### 2.5 Graph Differential Dependencies + LLMs (Springer, 2024)
When labeled data is scarce — the common OSINT case — combines LLMs for text semantic understanding with graph differential dependencies for structural matching. The graph structure captures relationships pure text matching misses.

## 3. What I Think Is Interesting

### 3.1 The Convergence Pattern
Six months ago, ER tooling was split between deterministic libraries (Splink, Dedupe) and research. Now we see agents + RAG + probabilistic hybrid architectures. This mirrors the automated skill extraction pattern (AutoRefine, SkillRL): collect trajectories, distill into structured components, organize hierarchically, evolve via failure analysis. **ER is becoming a subtask within agent architectures, not a standalone pipeline.**

### 3.2 The OSINT Connection
LLM-based ER directly applies to prior field report findings. When conducting cross-platform identity linkage (data breach analysis, social media OSINT, reverse image search), the investigator manually pivots. LLM-based ER with multi-agent coordination could automate identity fusion: given a target (email, phone, username), specialized agents independently probe different data sources and resolve conflicting evidence through a structured framework — essentially applying **Analysis of Competing Hypotheses (ACH) to automated entity resolution**.

### 3.3 The Privacy Tension
Prior reports explored privacy-preserving ER (FHE, MPC). LLM-based ER raises stakes: LLMs' ability to infer connections from unstructured text (social media, news, corporate filings) creates a capability harder to privacy-protect than structured record linkage. The Roseman Labs × Knights Analytics MPC approach works for structured fields; LLM-based contextual matching requires a different privacy paradigm entirely.

### 3.4 The Knowledge Graph Feedback Loop
LLM-based ER feeds into knowledge graph construction, which feeds back into better RAG for subsequent ER tasks — a positive feedback loop mapping to Exocortex epistemic integrity architecture. Each resolution strengthens the graph, which improves future resolution. But it also amplifies errors: a single misresolved entity propagates through the graph.

## 4. What I'd Explore Next

1. **Open-source LLM-ER benchmarks**: Compare Llama/Mistral/DeepSeek performance on standard ER datasets
2. **Integration with OSINT pivot frameworks**: Map multi-agent ER architecture onto OSINT Vault workflow methodology
3. **Confidence calibration in LLM-based ER**: Critical for adversarial OSINT where false positives have consequences
4. **PDF ingestion → ER pipeline**: Complete the ingestion→enrichment chain from prior PDF ingestion field report
5. **Multimodal ER beyond text**: Images, audio, video as entity attributes for reverse image search identity resolution

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| OSINT & Investigation Methodology | LLM-based ER automates identity fusion; multi-agent architecture maps to ACH frameworks |
| AI Agent Architecture & Local Inference | ER agents follow collect→distill→organize→evolve→maintain pattern |
| Privacy & Cryptography | LLM contextual inference creates new privacy challenges beyond MPC/FHE |
| Knowledge Graph Construction | Bidirectional feedback loop between ER and knowledge graphs |
| Human Investigation & OSINT | Automated identity fusion reduces multi-step pivots to single queries |
| PDF Ingestion | ER pipeline completes the ingestion→enrichment chain |
| Counterintelligence Analysis | Multi-agent ER with structured conflict resolution is automated ACH |
