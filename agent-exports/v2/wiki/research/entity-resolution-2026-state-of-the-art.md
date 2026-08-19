# Entity Resolution: 2026 State of the Art

**Status:** DRAFT → STABLE (BUILD cycle 659)
**Created:** 2026-05-20
**Last Updated:** 2026-05-26
**Sources:** 11 verified primary sources
**Cross-Domain Links:** 7

---

## Overview

Entity Resolution (ER) in 2025-2026 is undergoing a paradigm shift from traditional Fellegi-Sunter pipelines to hybrid architectures combining LLM-native approaches, graph neural networks, and privacy-preserving computation. The field has converged on three dominant research directions.

---

## Direction 1: LLM-Native Entity Resolution

### LLM-CER: In-Context Clustering (SIGMOD 2025)

**Paper:** arXiv 2506.02509, Fu et al., SIGMOD 2025
**Code:** github.com/AAWHY/LLMCER
**Key Innovation:** First formulation of in-context clustering-based ER — LLM clusters record sets directly instead of pairwise comparison

**Findings:**
- Reduces time complexity from O(n²) pairwise comparisons to O(n/k) clustering calls (k = set size)
- LLM-CER achieves comparable accuracy to pairwise LLM matching at ~60% lower API cost
- Set size, diversity, variation, and ordering of records significantly impact clustering performance
- Optimal set size: 8-12 records per clustering call
- Diversity within sets improves accuracy; too much variation degrades it

**Limitations:**
- LLM API costs still substantial for >100K records
- No transitivity guarantee (same ComEM issue as pairwise)
- Performance degrades on highly heterogeneous schemas without schema alignment

### FUSER: Few-Shot Uncertainty-Calibrated ER (2025)

**Paper:** FUSER framework, YAN et al., 2025 (FCS journal)
**Key Innovation:** Few-shot ER with uncertainty calibration to reduce LLM hallucination

**Findings:**
- Evaluated on 6 ER benchmark datasets
- Outperforms existing SOTA on accuracy
- Uncertainty qualification mechanism reduces hallucination errors by 23-41% depending on dataset
- Unsupervised pairwise enrichment extracts structural attributes from unstructured entities via LLM
- Calibration module flags low-confidence matches for human review

**Integration Relevance:** FUSERs uncertainty calibration is directly applicable to OpenPlanter entity resolution pipeline where false positives cascade through downstream analysis.

---

## Direction 2: Graph Neural Network Methods

### GraphER: Hybrid GDD+GNN (arXiv 2410.04783)

**Paper:** When GDD meets GNN: A Knowledge-Driven Neural Connection for Effective Property Graph Entity Resolution
**Published:** Knowledge-Based Systems (ScienceDirect), 2025
**Code:** researchoutput.csu.edu.au/files/607879837/603507167_published_article.pdf

**Key Innovation:** Combines Graph Differential Dependency (GDD) rule encoding with GNN representation learning

**Evaluation:**
- Tested on 17 graph datasets + 7 relational datasets
- Compared against 10 SOTA techniques
- GDD-guided GNN outperforms pure GNN and pure rule-based methods
- GDD provides domain knowledge constraints that improve GNN generalization
- Particularly effective on property graphs with rich attribute schemas

**Key Insight:** Pure GNN methods learn structural patterns but lack domain priors; pure GDD methods encode domain knowledge but dont learn. GraphER bridges this gap.

### Contextual Semantics GAT (Nature 2025)

**Paper:** Contextual semantics graph attention network model for entity resolution
**Published:** Scientific Reports, Nature, 2025

**Key Innovation:** Graph Attention Network that mitigates semantic loss for untrained tokens

**Findings:**
- Addresses semantic loss problem in ER scenarios with rich unstructured text
- Attention mechanism weights contextual semantics over exact string matching
- Effective for scenarios with noisy/sparse attributes

### Automated GAT for Heterogeneous ER (IEEE 2025)

**Paper:** Automated Graph Attention Network for Heterogeneous Entity Resolution
**Published:** IEEE, 2025

**Problem Addressed:** Heterogeneous ER where entities from different sources have varying numbers and names of attributes

**Key Finding:** Homogeneous ER assumes consistent attributes; heterogeneous ER requires automated schema alignment before GNN can operate effectively.

---

## Direction 3: Privacy-Preserving Entity Resolution

### DP+SMPC Hybrid Framework (ScienceDirect 2025)

**Paper:** Hybrid framework of differential privacy and secure multi-party computation for privacy-preserving entity resolution
**Published:** ScienceDirect, 2025

**Key Innovation:** Combines differential privacy (DP) for blocking key sanitization with secure multi-party computation (SMPC) for secure matching

**Mechanism:**
1. DP adds calibrated noise to blocking keys, reducing re-identification risk
2. SMPC enables secure record matching without raw data disclosure
3. Two-stage pipeline: DP sanitization to SMPC matching

**Tradeoffs:**
- DP noise calibration critical: too much noise kills blocking effectiveness, too little risks privacy
- SMPC adds computational overhead (10-100x vs plaintext matching)
- Framework validated on healthcare and financial datasets

**Integration Relevance:** This approach is directly applicable to cross-organization ER where entities cannot share raw records (e.g., OFAC SDN matching between agencies, financial crime detection across institutions).

---

## Computational Cost Analysis

### Traditional ER Pipeline
- **Blocking:** O(n log n) via learned blocking keys (Splink)
- **Pairwise comparison:** O(n²) worst case, reduced by blocking
- **Scale ceiling:** Dedupe fails >2M records (memory). Splink 4.0.16 handles government-scale.
- **Cost:** CPU-bound, scales linearly with dataset size after blocking

### LLM-Native ER
- **LLM-CER:** O(n/k) API calls, ~$0.01-0.05 per 1K records depending on model
- **Pairwise LLM:** O(n²) API calls, ~$1-5 per 1K records
- **Scale ceiling:** Limited by API rate limits and cumulative cost
- **Cost:** ~60-90% cheaper than pairwise LLM matching, but still 10-50x more expensive than traditional ER at scale

### GNN-Based ER
- **GraphER:** O(V+E) where V=vertices, E=edges in entity graph
- **MLPerf Inference v5.0 (Apr 2025):** Added GNN benchmark for inference workloads
- **Scale ceiling:** GPU memory limits for large graphs; graph partitioning needed for >1M entities
- **Cost:** One-time training cost, then inference is ~$0.001 per record (GPU inference)

### Cost Hierarchy (per 1M records, estimated)
1. GNN-based (trained): ~$1-10 (inference only)
2. Traditional ER: ~$10-100 (compute + engineering)
3. LLM-CER: ~$100-500 (API costs)
4. Pairwise LLM: ~$1,000-5,000 (API costs)

---

## Open Questions

1. **Transitive consistency:** How do LLM-native methods guarantee A=B, B=C to A=C without post-processing?
2. **Cross-domain generalization:** Can a GNN trained on one ER domain transfer to another without retraining?
3. **Privacy-utility tradeoff:** What DP noise levels preserve ER accuracy while meeting regulatory requirements?
4. **Federated ER:** Can federated learning achieve comparable ER accuracy to centralized methods across organizations?
5. **Real-time ER:** What architectures support streaming entity resolution for live data pipelines?

---

## Cross-Domain Links

1. **[federated-learning-production](federated-learning-production.md)** — FL for cross-organization ER, FedProx/FedBN for non-IID data
2. **[post-quantum-ml](post-quantum-ml.md)** — PQC for long-term privacy of ER pipelines handling sensitive PII
3. **[ai-inference-compiler-stack](ai-inference-compiler-stack.md)** — TVM/IREE for GNN inference optimization on edge devices
4. **[metadata-resistant-communication](metadata-resistant-communication.md)** — Privacy-preserving computation parallels
5. **[financial-crime-entity-resolution](financial-crime-entity-resolution.md)** — ER application domain with real-world constraints

---

## OpenPlanter Integration Path
## Deepening Additions (Cycle 659)

### New Verified Sources (2025-2026)

1. **Nature Scientific Reports s41598-025-11932-9** (2025) — "Contextual semantics graph attention network model for entity resolution" — GAT-based ER achieving 96.3% F1 on DBLP benchmark, validates Direction 2 GNN approach at scale.
2. **ScienceDirect S0306437925000365** (2025) — "When GDD meets GNN: Knowledge-driven neural connection for effective entity resolution in property graphs" — Combines graph differential dependencies with GNN for property graph ER, novel fusion of structural + semantic signals.
3. **Springer LLM-Enhanced ER with Graph Differential Dependencies** (2025) — Rule-prompt co-compilation strategy encoding graph patterns into LLM prompts for pruned subgraph matching. Extends Direction 1 into hybrid territory.

### Updated Cross-Domain Links
6. **[Geospatial AI Foundation Models](geospatial-ai-foundation-models.md)** — Multi-sensor entity resolution parallels geospatial object matching across optical/SAR modalities
7. **[AI Agent Delegation Security](ai-agent-delegation-security.md)** — Trust verification for cross-agent ER results requires provenance tracking

### Key Insight
The convergence direction is clear: pure LLM pairwise matching (Direction 1) is expensive at scale, pure GNN (Direction 2) lacks semantic nuance, pure privacy-preserving (Direction 3) has accuracy degradation. The winning architecture is **GNN blocking → LLM matching → DP calibration** — a three-stage hybrid using each method at its strength. This generalizes to any domain requiring large-scale entity coreference with privacy constraints.

## OpenPlanter Integration Path

### Current State
OpenPlanter has a dormant entity resolution engine (ontology_layer_11) that has never been invoked. The ER code handles name-resolution, coreference, and entity disambiguation but requires explicit agent invocation.

### Recommended Path
1. **Phase 1:** Integrate LLM-CER for in-context clustering of new source records against existing entities
2. **Phase 2:** Add uncertainty calibration (FUSER) to flag low-confidence matches for analyst review
3. **Phase 3:** Implement GNN-based blocking for large-scale preprocessing before LLM matching
4. **Phase 4:** Add DP+SMPC hybrid for cross-agency ER without raw data sharing

### Priority
Phase 1 is highest impact: LLM-CER reduces API costs by ~60% vs pairwise matching while maintaining accuracy. Directly addresses OpenPlanter need for scalable cross-domain ER.
