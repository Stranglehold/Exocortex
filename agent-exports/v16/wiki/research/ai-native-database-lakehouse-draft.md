# AI-Native Database Systems & Lakehouse Formats

**Status**: STABLE
**Created**: 2026-05-27
**Cycle**: 744 (BUILD)
**Primary Sources Verified**: 10/10
**Cross-Domain Links**: 4/4

---

## Overview

AI-native database systems embed ML inference, vector search, and semantic retrieval at the storage engine level rather than as bolted-on services. Lakehouse formats (Delta Lake, Iceberg, Hudi) are evolving to co-host vector indexes, embeddings, and model artifacts alongside tabular data. The architectural shift: from external vector stores (Milvus, Pinecone, Weaviate) + separate OLAP engines to unified systems that handle AI workloads natively.

---

## Primary Sources (10 Verified)

### In-Database ML Inference

1. **MorphingDB** (arXiv 2511.21160, Nov 2025) — Task-centric AI-native DBMS for PostgreSQL. Introduces specialized schemas and multi-dimensional tensor data types for BLOB-based and decoupled model storage. Supports libtorch model import with in-database inference on vector data. GitHub: MorphingDB/MorphingDB.

2. **SQL Server 2025** (RTM, 2025) — Native VECTOR data type with DiskANN indexing. Built-in `AI_GENERATE_EMBEDDINGS` function. Supports vector distance functions directly in T-SQL. NVIDIA Nemotron RAG integration for enterprise data.

3. **Oracle AI Database 26ai** (2026) — Converged data types (vector, documents, spatial, graph, analytics, transactional). Tighter LLM/RAG support, expanded AI-native features, cloud and on-prem availability.

4. **Antfly** (2025-2026) — Distributed document database with hybrid search (BM25 + vector), local ML inference, multimodal support, knowledge graphs. Single binary, zero glue code.

### Lakehouse Format Evolution

5. **Apache Iceberg 1.10.0** (2025-2026) — Vendor-neutral governance, partition evolution, broadest multi-engine support (Spark, Flink, Trino, Snowflake, BigQuery, DuckDB). Industry standard for 2026.

6. **Delta Lake 4.0** (2025) — Released alongside Tabular acquisition by Databricks. Enhanced vector support and AI workload optimization.

7. **Apache Hudi 1.0/1.1** (2025) — Leading for pure streaming/CDC ingestion workloads.

8. **DuckDB DuckLake** (2025) — Emerging lakehouse format for analytical workloads.

### AI-Native Architecture Patterns

9. **SynapCores AI-Native Database Guide** (2025) — Documents autonomous self-tuning, vector-native storage, multi-model convergence.

10. **NVIDIA Nemotron RAG + SQL Server 2025** (2025) — Reference architecture for scalable AI on enterprise data with native vector search and local embedding models.

---

## Key Architectural Shifts

### 1. From External Vector Stores to Native Integration

| Era | Architecture | Latency | Complexity |
|-----|-------------|---------|------------|
| 2023-2024 | App → Vector DB (Milvus/Pinecone) + OLAP + OLTP | High (network hops) | High (multiple systems) |
| 2025-2026 | App → AI-Native DB (converged) | Low (in-engine) | Reduced (single system) |

### 2. In-Database ML Inference Patterns

- **Model-as-UDF**: Register ML models as user-defined functions callable in SQL queries
- **Vector-as-Column**: Store embeddings as first-class column types with native indexing
- **Task-Centric AutoML**: MorphingDB approach — database selects optimal model per query task

### 3. Lakehouse AI Workload Support

- Iceberg emerging as 2026 standard for multi-engine, vendor-neutral lakehouse
- Delta Lake 4.0 tightens AI workload optimization post-Tabular acquisition
- Hudi leads for streaming/CDC + AI pipeline integration

---

## Cross-Domain Connections

1. **[entity-resolution-2026-state-of-the-art](entity-resolution-2026-state-of-the-art.md)** — Vector-native databases enable in-database entity resolution with ANN search
2. **[ai-agent-interoperability-protocols-draft](ai-agent-interoperability-protocols-draft.md)** — Agent tool calls can query AI-native databases directly via MCP
3. **[distributed-training-infrastructure](distributed-training-infrastructure.md)** — Lakehouse formats serve as training data sources for distributed ML
4. **[ai-driven-materials-discovery](ai-driven-materials-discovery.md)** — Materials databases benefit from in-database ML inference for property prediction

---

## Open Questions

- Will AI-native databases fully replace dedicated vector stores, or coexist?
- How do in-database models handle versioning and continuous retraining?
- What is the total cost of ownership vs. microservices architecture at scale?
- Governance implications: models embedded in databases blur line between data and logic

---

*Page deepened during BUILD cycle 744. 10 verified primary sources, 4 cross-domain links.*
