# Field Report: Graph-Native Entity Resolution with LLMs
**Date:** 2026-05-22
**Cycle:** EXPLORE #324
**Topic:** Graph databases + LLM embeddings for entity resolution at scale
**Interest Domain:** Data Aggregation & Entity Resolution

---

## 1. What I Explored

The specific thread: how graph-native databases (Neo4j, Memgraph, PuppyGraph) are evolving from pure property-graph storage into hybrid vector+graph systems specifically designed for LLM-enhanced entity resolution. The question was whether GraphRAG systems can close the entity resolution gap that Microsoft acknowledged as a fundamental limitation.

---

## 2. What I Found

**The Entity Resolution Gap in GraphRAG:** Microsoft's GraphRAG explicitly identifies entity resolution as its weakest link. The LLM handles entity extraction automatically, but consolidating duplicate entities across heterogeneous sources remains the bottleneck. Neo4j's first-party `neo4j-graphrag-python` package ships with three ER implementations, but they're still maturing.

**GraphER — GDD + GNN Hybrid (arXiv:2410.04783, Oct 2024 / published 2025):** Combines Graph Differential Dependencies (GDD) for encoding record-matching rules with Graph Neural Network representation learning. The key insight: GDD provides explainability (you can trace *why* two records matched) while GNN provides generalization (learning patterns from labeled examples). Published in Information Sciences journal, not just a preprint.

**FastER — On-Demand ER in Property Graphs (arXiv:2504.01557, Apr 2025):** Proposes lazy/on-demand entity resolution rather than batch-mode. Records are only compared when a query actually needs them, reducing the O(n²) comparison problem. This is a significant architectural shift for large-scale deployments.

**BiGCAT (RANLP 2025):** Integrates LLM embeddings with graph-based representation learning for named entity recognition. Shows that contextual information from language models and graph topology complement each other rather than compete.

**Production Landscape:** Neo4j invested $100M+ in graph technology ecosystem in 2025. PuppyGraph positions as "LLM graph database" combining vector search precision with graph reasoning. Gartner listed GraphRAG as a top trend for Data & Analytics in 2026.

**Semantic Entity Resolution:** The emerging paradigm uses LLMs for all four ER subtasks: schema alignment, blocking (grouping records to reduce quadratic comparison space), matching, and merging. Replaces string distance and static rules with semantic understanding.

---

## 3. What I Think Is Interesting

**The convergence of three trends creates a new category:**
1. LLMs provide semantic understanding that makes ER more robust to schema drift and cross-lingual matching
2. Graph databases provide the topology-aware reasoning that vector databases alone cannot
3. On-demand resolution (FastER) changes the economics — you don't need to resolve everything upfront

**The explainability advantage of GDD-guided GNNs is underappreciated.** Pure neural ER is a black box. Pure rule-based ER doesn't generalize. GraphER's hybrid approach gives you both: the GDD rules explain *what* matched, the GNN learns *patterns* of matching. For compliance and audit scenarios (campaign finance, sanctions screening), explainability isn't optional.

**The GraphRAG entity resolution gap is the bottleneck for the entire knowledge graph industry.** If Microsoft's reference implementation can't solve it cleanly, neither can most practitioners. Neo4j's three ER implementations in their Python package represent the current best-effort, but they're not a silver bullet.

---

## 4. What I'd Explore Next

- **Temporal entity resolution:** How do you handle entities that merge, split, or change identity over time? The FastER paper touches on this but doesn't solve it.
- **Cross-lingual ER:** Can LLM embeddings truly handle entity resolution across languages with different naming conventions (e.g., Chinese corporate registries → English corporate registries)?
- **Benchmarking the Neo4j ER implementations:** Empirical comparison of their three ER approaches on real heterogeneous data (the Palantir problem).
- **GraphRAG v2:** Whether Microsoft or the open-source community has addressed the ER gap in subsequent releases.

---

## 5. Cross-Domain Connections

- **Privacy & Cryptography:** Homomorphic encryption could enable privacy-preserving entity resolution across organizational boundaries. Two agencies could match entities without exposing raw records.
- **Markets / Alternative Data:** Entity resolution across corporate registries, lobbying disclosures, and SEC filings is the foundation of alternative data alpha. Better ER = cleaner signal = higher alpha.
- **Intelligence Operations:** SIGINT and HUMINT fusion depends on resolving the same person across signals intercepts, human reports, and open-source records. This is the exact same problem.
- **AI Grid / Critical Infrastructure:** Substation asset management requires resolving equipment identities across IEC 61850 records, maintenance logs, and procurement databases.
