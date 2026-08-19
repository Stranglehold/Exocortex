# Knowledge Graph Construction Patterns

**Status:** STABLE
**Created:** 2026-05-23
**Last Updated:** 2026-05-23
**Cycle:** 464 (BUILD)

## Overview

Knowledge graphs (KGs) are structured representations of entities and their relationships, forming the backbone of modern data aggregation, entity resolution, and AI reasoning systems. The field has shifted from rule-based/statistical KG pipelines to LLM-driven generative frameworks in 2025-2026.

## Core Questions

1. What are the dominant KG construction paradigms in 2025-2026?
2. Property graphs (Neo4j, TigerGraph) vs RDF/OWL — when to use which?
3. LLM-assisted KG construction: current state of automated triple extraction?
4. Schema design patterns: ontology-first vs emergent schema?
5. Scalability: NetworkX (in-memory) vs Neo4j vs TigerGraph vs Amazon Neptune at scale?

## Primary Sources

### 1. arXiv 2510.20345 — LLM-Empowered KG Construction Survey (ICAIS 2025)
- Comprehensive survey covering ontology engineering, knowledge extraction, and knowledge fusion
- Documents the paradigm shift: rule-based -> language-driven generative frameworks
- Three-layer pipeline reimagined: ontology engineering -> knowledge extraction -> knowledge fusion
- Key finding: LLMs excel at schema induction and semantic alignment but struggle with scalability and hallucination in large-scale extraction

### 2. arXiv 2505.23628 — AutoSchemaKG (HKUST-KnowComp)
- Fully autonomous KG construction WITHOUT predefined schemas
- 92-95% semantic alignment with human-crafted schemas at zero manual intervention
- Uses unsupervised clustering and relation discovery for schema induction
- Multi-stage prompts tailored to different relation types; schema evolves iteratively
- GitHub: HKUST-KnowComp/AutoSchemaKG; tested on MMLU benchmark

### 3. arXiv 2411.17388 — GraphJudge (Can LLMs be Good Graph Judge for KG Construction?)
- Evaluation framework for LLM-constructed KGs
- Three-module architecture: initial high-recall extraction -> LLM judgment -> quality filtering
- Moves field from "can we build KGs with LLMs" to "how do we know they're good?"
- Addresses the hallucination problem in large-scale KG construction

### 4. arXiv 2502.09956 — KGGen (NeurIPS 2025)
- Clusters related entities to reduce sparsity in LLM-constructed KGs
- Addresses the scalability challenge identified in the survey
- Available as Python library (pip install kg-gen)
- Introduces MINE benchmark (Measure of Information in Nodes and Edges)

### 5. arXiv 2404.15923 — KGValidator
- Validation framework for LLM-constructed knowledge graphs
- Provides automated quality assessment metrics

### 6. arXiv 2404.13207 — STaRK Benchmark
- Benchmark for structured knowledge graph construction evaluation
- Standardized test suite for KG quality measurement

## Deepening Notes

### Paradigm Shift
The 2025-2026 shift is from rule-based extraction (OpenIE, spaCy, Stanza) to LLM-native frameworks. AutoSchemaKG demonstrates that billion-scale KGs with dynamically induced schemas can effectively complement parametric knowledge in LLMs.

### Schema Design
- **Ontology-first**: Define schema before extraction (traditional, good for constrained domains)
- **Emergent schema**: AutoSchemaKG approach — induce schema from data, iterate, refine
- **Hybrid**: LLM reasoning for schema induction + rule-based extraction for scale

### Scalability
- NetworkX: good for prototyping, fails at >1M nodes in memory
- Neo4j: production-ready, native GNN support, GraphRAG integration
- TigerGraph: enterprise scale, distributed architecture
- Amazon Neptune: cloud-native, managed service

### Evaluation Challenge
GraphJudge and STaRK represent the maturation of the field. The key insight: evaluation is now a first-class concern, not an afterthought. LLM-as-a-Judge architectures are becoming standard.

### Cross-Domain Integration
- Entity resolution is one layer in the KG construction pipeline (fusion stage)
- Graph-native ER (GraphER) and LLM-native ER (LLM-CER) both feed into KG construction
- KGs enable grounded reasoning for AI agents — dynamic knowledge updates
- Privacy-preserving KG construction possible via homomorphic encryption across organizational boundaries

## Cross-Domain Links

- [entity-resolution-2026-state-of-the-art](entity-resolution-2026-state-of-the-art.md)
- [llm-native-entity-resolution](llm-native-entity-resolution.md)
- [graph-native-entity-resolution](graph-native-entity-resolution.md)
- [ai-native-database-search-infrastructure](ai-native-database-search-infrastructure.md)
- [ai-agent-delegation-security](ai-agent-delegation-security.md)
