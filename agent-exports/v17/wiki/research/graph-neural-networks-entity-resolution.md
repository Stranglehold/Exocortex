# Graph Neural Networks for Entity Resolution

**Status:** DRAFT  
**Created:** 2026-07-08  
**Domain:** Data Aggregation & Entity Resolution  
**Interests:** Data Aggregation & Entity Resolution, AI Agent Architecture & Local Inference

## Overview

Graph Neural Networks (GNNs) applied to entity resolution (ER) form one of three dominant research directions in 2025-2026, alongside LLM-native ER and privacy-preserving ER. GNNs encode entity relationships as graph structures where nodes represent entities and edges represent similarity or co-occurrence, enabling learned representations that capture structural patterns beyond pairwise feature comparison.

## Key Papers & Methods

### GraphER: GDD + GNN Hybrid (arXiv:2410.04783, published 2025)
- **Venue:** Knowledge-Based Systems (ScienceDirect)
- **Method:** Combines Graph Differential Dependencies (GDD) for rule encoding with GNN representation learning
- **Results:** Evaluated on 17 graph + 7 relational datasets, outperforms 10 SOTA techniques
- **Key insight:** GDD provides explainability (trace *why* two records matched); GNN provides generalization (learning patterns from labeled examples). Resolves the explainability-vs-generalization tradeoff critical for compliance/audit scenarios.
- **Repository:** Zaiwen/Entity_Resolution_Junwei_HU

### Contextual Semantics Graph Attention Network (Nature Scientific Reports, 2025)
- **Paper:** Nature s41598-025-11932-9
- **Method:** GAT architecture mitigating semantic loss for untrained tokens in ER scenarios with rich unstructured text
- **Results:** 96.3% F1 on DBLP benchmark
- **Key insight:** Attention mechanism weights contextual semantics over exact string matching, addressing the semantic loss problem in noisy/sparse attribute scenarios

### Automated GAT for Heterogeneous ER (IEEE, 2025)
- **Problem:** Entities from different sources have varying numbers and names of attributes — homogeneous GNNs fail without schema alignment
- **Method:** Automated schema alignment layer before GAT processing
- **Significance:** Enables cross-source ER without manual attribute mapping

### FlexER: Flexible Entity Resolution for Multiple Intents (arXiv:2209.07569)
- **Method:** Formulates multi-intent ER as multi-label classification using multiplex graph representations as GNN input
- **Key insight:** Different downstream applications have varying interpretations of what constitutes "same entity" — FlexER learns intent-specific representations from a single model
- **Benchmark:** New MIER benchmark + validation on two standard benchmarks, outperforms universal ER SOTA

### GNNs for Inconsistent Cluster Detection (arXiv:2105.05957)
- **Application:** Incremental ER — detecting when existing entity clusters contain records that don't belong together
- **Method:** Supervised graph classification on weighted product similarity graphs using Message Passing Neural Networks with a novel aggregation scheme
- **Significance:** Shifts ER from pure matching to cluster quality assurance, addressing the maintenance problem in mature knowledge bases

## GNN-LLM Hybrid Architectures

### Multi-Source KG Construction via LLM-Assisted ER (ScienceDirect, 2026)
- **Pattern:** GNN encoding of graph structure → LLM semantic matching of ambiguous attributes → combined scoring
- **Application:** Cross-jurisdictional entity resolution where legal entity names and identifiers differ by jurisdiction

### Rule-Prompt Co-Compilation (Springer, 2025)
- **Method:** Encodes graph differential dependency patterns into LLM prompts for pruned subgraph matching
- **Key insight:** GDD rules constrain the LLM search space, reducing token consumption while maintaining accuracy

### BiGCAT (RANLP, 2025)
- **Method:** Integrates LLM embeddings with graph-based representation learning for named entity recognition
- **Finding:** Contextual information from language models and graph topology complement rather than compete

## Production & Benchmark Landscape

### MLPerf Inference v5.0 (April 2025)
- Added GNN benchmark for inference workloads, signaling industry recognition of GNN-ER as production-critical

### Neo4j GraphRAG Ecosystem
- Neo4j invested $100M+ in graph technology (2025)
- First-party `neo4j-graphrag-python` ships with three ER implementations
- Microsoft GraphRAG explicitly identifies entity resolution as its weakest link — GNN-based consolidation is the key gap

### FastER: On-Demand ER in Property Graphs (arXiv:2504.01557, April 2025)
- Proposes lazy/on-demand ER rather than batch — records compared only when a query needs them
- Architectural shift for large-scale deployments, reducing O(n²) comparison problem

### Scaling
- **Complexity:** O(V+E) where V=vertices, E=edges
- **Memory bottleneck:** GPU memory limits for >1M entity graphs; graph partitioning required at scale
- **Cost (per 1M records, estimated):** $1-10 inference-only after training — cheapest of all methods

## Cost Hierarchy for ER Methods (per 1M records, estimated)

| Method | Cost | Notes |
|--------|------|-------|
| GNN-based (trained) | $1-10 | Inference only; training is one-time |
| Traditional ER (Splink) | $10-100 | Compute + engineering time |
| LLM-CER (in-context clustering) | $100-500 | API costs, O(n/k) calls |
| Pairwise LLM | $1,000-5,000 | O(n²) API calls, prohibitive at scale |

## Open Research Questions

1. **Cross-domain transfer:** Can a GNN trained on one ER domain (e.g., product matching) transfer to another (e.g., corporate entity matching) without retraining?
2. **Temporal entity evolution:** How do GNNs handle entities that change identity over time (mergers, rebranding, shell company churn)? Current temporal GNNs are nascent for this use case.
3. **Transitive consistency:** GNN pairwise matching doesn't guarantee A=B ∧ B=C ⇒ A=C without post-processing
4. **Federated GNN-ER:** Can federated learning achieve comparable accuracy to centralized GNN-ER across organizations?
5. **Streaming ER:** What architectures support real-time GNN-based entity resolution for live data pipelines?

## Three-Stage Hybrid Architecture (Emerging Consensus)

The winning architecture combines methods at their strengths:

```
GNN blocking → LLM matching → DP calibration
```

1. **GNN blocking:** Use trained GNN to generate candidate pairs (cheap, fast, captures structural patterns)
2. **LLM matching:** Apply LLM semantic matching only to candidate pairs (expensive but precise, only on reduced set)
3. **DP calibration:** Add differential privacy noise to blocking keys for cross-organization ER without raw data sharing

This generalizes to any domain requiring large-scale entity coreference with privacy constraints.

## Exocortex Integration Pathways

1. **Knowledge graph enrichment:** GNN-ER as preprocessing step before entity ingestion into Exocortex knowledge graph
2. **Entity resolution flywheel:** GNN blocking → LLM matching → graph-native entities → new training data → improved GNN
3. **Cross-source OSINT:** GNN-ER for correlating entities across campaign finance, lobbying, government contracts, and corporate registries
4. **Temporal entity tracking:** GNN-based change detection for shadow fleet rotation, shell company churn, sanctions evasion
5. **Epistemic integrity:** GDD explainability layer (from GraphER) maps directly to Exocortex source reliability scoring and confidence propagation

## Cross-Domain Connections

1. **[[knowledge-graph-construction-patterns]]** — GNN-ER feeds entity nodes into property graph and RDF knowledge graphs
2. **[[entity-resolution-algorithms]]** — Traditional Fellegi-Sunter foundational methods that GNN-ER extends
3. **[[temporal-entity-resolution]]** — Temporal GNNs for dynamic entity identity tracking
4. **[[cross-jurisdictional-entity-resolution]]** — Heterogeneous GAT for multi-jurisdiction entity matching
5. **[[cross-source-entity-resolution-knowledge-graphs]]** — OpenPlanter framework, cross-source ER with KGs
6. **[[bridging-local-frontier-model-performance]]** — Distilled GNN models for local inference within Exocortex
7. **[[agentic-ai-self-learning]]** — GNN-ER as a learning substrate: improved entity resolution → better knowledge graph → improved agent reasoning
8. **[[data-lineage-provenance-entity-resolution]]** — GDD explainability maps to provenance tracking and confidence scoring
9. **[[osint-entity-resolution-methods]]** — GNN methods applied to OSINT entity correlation
10. **[[ai-agent-architecture-local-inference]]** — GPU-accelerated GNN inference for local Exocortex deployment

## References

1. Hu et al., "When GDD meets GNN: Knowledge-driven neural connection for effective entity resolution in property graphs," Knowledge-Based Systems (ScienceDirect), 2025. arXiv:2410.04783.
2. "Contextual semantics graph attention network model for entity resolution," Scientific Reports, Nature, 2025. s41598-025-11932-9.
3. Fu et al., "LLM-CER: In-Context Clustering for Entity Resolution," SIGMOD 2025. arXiv:2506.02509.
4. Barton, Neiman, Yuan. "Graph Neural Networks for Inconsistent Cluster Detection in Incremental Entity Resolution," arXiv:2105.05957.
5. Genossar, Shraga, Gal. "FlexER: Flexible Entity Resolution for Multiple Intents," arXiv:2209.07569.
6. "FastER: On-Demand Entity Resolution in Property Graphs," arXiv:2504.01557, April 2025.
7. "Multi-source knowledge graph construction via LLM-assisted ER," ScienceDirect, 2026.
8. "Hybrid framework of differential privacy and secure multi-party computation for privacy-preserving entity resolution," ScienceDirect, 2025.
9. MLPerf Inference v5.0 results, April 2025. mlcommons.org.
10. Neo4j GraphRAG ecosystem, neo4j.com/docs/neo4j-graphrag-python, 2025-2026.
11. Gartner, "Top Trends in Data & Analytics 2026," listing GraphRAG as a top trend.
