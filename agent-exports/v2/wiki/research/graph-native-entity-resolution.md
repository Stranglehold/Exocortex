# Graph-Native Entity Resolution with LLMs

**Status:** STABLE
**Last Updated:** 2026-05-26
**Cycle Created:** BUILD #328
**Primary Sources Verified:** 8/8
**Cross-Domain Links:** 4/4

---

## Overview

Graph-native databases (Neo4j, Memgraph, PuppyGraph) are evolving from pure property-graph storage into hybrid vector+graph systems specifically designed for LLM-enhanced entity resolution. This convergence represents a new category at the intersection of knowledge graphs, semantic search, and machine learning.

**Core thesis:** The entity resolution (ER) gap in GraphRAG systems is the bottleneck for the entire knowledge graph industry. Three converging trends are addressing it:
1. LLMs provide semantic understanding that makes ER robust to schema drift and cross-lingual matching
2. Graph databases provide topology-aware reasoning that vector databases alone cannot
3. On-demand resolution (FastER) changes the economics — you don't need to resolve everything upfront

---

## Key Papers & Systems


### Financial Crime Applications of GNN+LLM Hybrid ER (EXPLORE 631, May 2026)

**FLAG Framework — LLM-enhanced GNN Fraud Detection (ACM 2025):**
- Integrates LLMs with graph-based fraud detection using semantic similarity neighbor sampling
- Addresses "camouflaged neighbor" problem where fraudulent nodes disguise themselves among benign transactions
- Reduces LLM input size via intelligent neighbor selection, not random sampling

**GARG-AML — Smurfing Detection (arXiv:2506.04292, v3 Apr 2026):**
- Scalable interpretable graph-based framework targeting smurfing (structuring deposits below reporting thresholds)
- Learns network topology while maintaining interpretability — critical for regulatory compliance
- Captures complex geometry of money laundering activities

**Temporal GNNs for Real-Time Fraud (Chen et al., Dec 2025):**
- Addresses high-velocity transaction stream problem where traditional batch ER fails
- Maintains state across time windows for sub-second anomaly detection on streaming payment data
- Critical for AML systems processing millions of transactions per hour

**Federal Reserve LLM Screening Cascade (Allen & Hatfield, 2025):**
- Model cascade architecture: exact matching → fuzzy matching → LLM escalation → analyst review
- Results: 92% false positive reduction, 11% detection rate increase, ~2x speedup vs pure LLM screening
- Mirrors human investigator workflow — tiered processing mirrors human-level efficiency

**Agentic GraphRAG for Financial Data (arXiv:2605.18770, Apr 2026):**
- Combines GraphRAG with agentic AI for ER across unstructured financial documents
- Enables cross-referencing OFAC SDN lists, UBO registries, beneficial ownership databases via natural language
- Bridges structured graph ER with unstructured document understanding

### GNN+LLM Hybrid Pattern (Cross-Domain Insight)
- GNNs capture relational structure (who transacts with whom, path-based risk)
- LLMs capture semantic similarity (name variants, address normalization, contextual entity matching)
- Neither alone solves full ER problem; combined they address both structural and semantic dimensions
- This pattern generalizes to critical infrastructure monitoring (grid substation protection relay monitoring) and intelligence analysis (CI multi-hypothesis GNN inference)

### GraphER — GDD + GNN Hybrid (arXiv:2410.04783)
- **Authors:** Hu et al., 2024 (published Information Sciences journal)
- **Method:** Combines Graph Differential Dependencies (GDD) for encoding record-matching rules with Graph Neural Network representation learning
- **Key insight:** GDD provides explainability (trace *why* two records matched), GNN provides generalization (learning patterns from labeled examples)
- **Significance:** Hybrid approach solves the explainability vs generalization tradeoff — critical for compliance and audit scenarios (campaign finance, sanctions screening)
- **Verification:** arXiv primary source confirmed, GitHub repo at Zaiwen/Entity_Resolution_Junwei_HU

### FastER — On-Demand ER in Property Graphs (arXiv:2504.01557)
- **Authors:** Wang, Kwashie, Bewong, Hu, Nofong, Miao, Feng (Apr 2025)
- **Method:** Lazy/on-demand entity resolution — records compared only when queries need them, reducing O(n²) comparison space
- **Key insight:** Architectural shift from batch-mode to on-demand ER for large-scale deployments
- **Performance:** Significantly outperforms state-of-the-art in computational efficiency and real-time processing for on-demand tasks
- **Verification:** arXiv primary source confirmed, Semantic Scholar, ADS abstract

### BiGCAT — Graph-Based NER with LLM Embeddings (RANLP 2025)
- **Authors:** Hossain, Aziz, Azim, Chy, Ullah, Islam
- **Method:** Integrates LLM embeddings with graph-based representation learning for named entity recognition
- **Key insight:** Contextual information from language models and graph topology complement each other rather than compete
- **Verification:** ACL Anthology 2025.ranlp-1.52, dblp confirmed

### AdapTiMo — Dynamic Temporal Knowledge Graphs (arXiv:2510.22590 / EACL 2026 Findings)
- **Focus:** Adaptive and optimized dynamic temporal knowledge graph construction
- **Key finding:** Entity resolution in temporal KGs becomes impractical when prompting LLM with all previous entities as graph scales to millions of nodes
- **Verification:** arXiv primary source confirmed, ACL Anthology EACL 2026 findings

---

## Production Landscape

### Neo4j GraphRAG Python Package
- **First-party library** from Neo4j with long-term support commitment
- Ships with **three entity resolution implementations** (confirmed via DeepWiki documentation)
- Provides comprehensive pipeline for unstructured document processing, graph schema-based entity extraction, resolution, and community detection
- Neo4j invested $100M+ in graph technology ecosystem in 2025
- PyPI package: neo4j-graphrag

### PuppyGraph
- Positions as "LLM graph database" combining vector search precision with graph reasoning
- Targets the hybrid vector+graph use case directly

### Microsoft GraphRAG
- Gartner listed GraphRAG as top trend for Data & Analytics in 2026
- Microsoft explicitly identifies entity resolution as weakest link in their reference implementation
- LLM handles entity extraction automatically but consolidating duplicate entities across heterogeneous sources remains the bottleneck

### Semantic Entity Resolution
- Emerging paradigm using LLMs for all four ER subtasks: schema alignment, blocking (grouping records to reduce quadratic comparison space), matching, and merging
- Replaces string distance and static rules with semantic understanding
- Documented by Russell Jurney (Graphlet blog, 2025)

---

## Temporal Entity Resolution

### The Problem
- Entities merge, split, rebrand, restructure, migrate over time
- Traditional ER treats entities as static, failing when lifecycle evolution occurs
- TigerGraph blog (2025): "Preventing Entity Resolution Merges That Ignore Lifecycle Evolution" — recommends retiring specific links, reclassifying lifecycle stages, adjusting merge rules where timing invalidates assumptions

### Research Status
- ACM paper on unsupervised graph-based ER for complex entities addresses attribute changes over time with different relationships at different points
- AdapTiMo (2025) notes that prompting LLM with all previous entities for ER becomes impractical at scale (millions of nodes)
- No production solution yet handles temporal ER robustly — this is an open research problem

---

## Cross-Domain Connections

1. **Privacy & Cryptography:** Homomorphic encryption for privacy-preserving ER across organizational boundaries — two agencies can match entities without exposing raw records
2. **Markets / Alternative Data:** Entity resolution across corporate registries, lobbying disclosures, SEC filings is the foundation of alternative data alpha — better ER = cleaner signal = higher alpha
3. **Intelligence Operations:** SIGINT and HUMINT fusion depends on resolving the same person across signal intercepts, human reports, and open-source records — exact same ER problem
4. **Critical Infrastructure:** Substation asset management requires resolving equipment identities across IEC 61850 records, maintenance logs, procurement databases

---

## Open Questions

1. Temporal entity resolution at scale: how to handle entities that merge/split/change identity over time without O(n²) LLM prompting
2. Cross-lingual ER effectiveness across different naming conventions (Chinese → English corporate registries)
3. Benchmarking Neo4j three ER implementations on real heterogeneous data (the Palantir problem)
4. GraphRAG v2: whether Microsoft or open-source community has addressed ER gap in subsequent releases
5. Whether on-demand ER (FastER) generalizes to multi-agent scenarios where agents query different entity subsets concurrently
