# GraphRAG: Hybrid Knowledge Graph + Retrieval-Augmented Generation Architecture

**Status:** STABLE
**Created:** 2026-05-28
**Interest domain:** Data Aggregation & Entity Resolution, AI Agent Architecture

---

## Executive Summary

GraphRAG combines structured knowledge graph indexing with LLM-based retrieval-augmented generation to improve answer quality and multi-hop reasoning over complex document corpora. Microsoft Research introduced the approach in 2024 as an alternative to naive vector search. Independent benchmarks (2025-2026) show GraphRAG achieves 3.4x accuracy improvement over vector RAG on complex reasoning tasks but at 4x latency and 6x cost. Vector RAG remains superior for simple fact retrieval and cost-sensitive workloads.

---

## Core Architecture

### Original Microsoft Research Design (2024)
- **Document processing**: Chunk text -> extract entities/relationships via LLM -> populate graph database
- **Graph database**: Neo4j, NetworkX, or native implementations
- **Retrieval strategy**: Community detection for hierarchical summarization + graph traversal for multi-hop reasoning
- **Indexing cost**: ~$33K for large datasets (reported impractical for many use cases)

### 2025-2026 Evolution
- **LazyGraphRAG**: Microsoft's follow-up reducing indexing costs through selective graph construction
- **Neo4j GraphRAG SDK**: Production deployment framework (2025)
- **LangChain integration**: Standardized GraphRAG components in LangChain ecosystem
- **Azure deployment**: Microsoft Discovery platform integrates GraphRAG for scientific research

---

## Verified Benchmark Results

### Performance Comparison (Independent Sources)

| Metric | Vector RAG | GraphRAG | Source |
|--------|------------|----------|--------|
| Single-hop fact retrieval | 68.73% | Lower | TailoredAI systematic eval |
| Complex reasoning (multi-hop) | Baseline | 3.4x improvement | Multiple 2025-2026 studies |
| Schema-bound queries (KPIs, forecasts) | 0% | 90%+ | FalkorDB 2025 SDK benchmark |
| Natural Questions dataset | Baseline | 13.4% lower | arXiv 2506.05690v3 |
| Query latency | ~300ms | ~1200ms | Iterathon 2026 enterprise guide |
| Cost per query | ~$0.002 | ~$0.012 | Iterathon 2026 enterprise guide |

### Key Findings

1. **GraphRAG dominates on complex reasoning**: Multi-hop questions requiring relationship traversal show 3.4x accuracy improvement
2. **Vector RAG wins on simple retrieval**: Single-hop fact lookup tasks perform equally or better with vector-only
3. **GraphRAG fails on some benchmarks**: Natural Questions shows 13.4% degradation — graph structure adds noise when relationships don't help
4. **Schema-aware queries**: FalkorDB reports vector RAG scored 0% on KPI/forecast queries; GraphRAG recovered to 90%+
5. **Cost-latency tradeoff**: GraphRAG is 4x slower and 6x more expensive per query

---

## Failure Modes & Limitations

### Documented Failure Modes
1. **Over-indexing cost**: Original Microsoft implementation's $33K indexing cost for large corpora is prohibitive
2. **Graph construction quality**: Entity/relationship extraction errors propagate through retrieval
3. **Simple query degradation**: Graph overhead hurts performance on straightforward fact retrieval
4. **Maintenance complexity**: Graphs require schema management, updates, and consistency maintenance
5. **Cold start problem**: Building the initial knowledge graph is expensive and slow

### When GraphRAG Underperforms (arXiv 2506.05690v3)
- Natural Questions benchmark: 13.4% lower accuracy than vector RAG
- Simple entity lookup tasks where semantic similarity suffices
- High-volume low-latency requirements (real-time systems)

---

## Production Deployments (2026)

| Platform | Status | Notes |
|----------|--------|-------|
| Microsoft Azure Discovery | Production | Scientific research integration |
| Neo4j GraphRAG SDK | Production | 2025 SDK, enterprise deployments |
| LangChain GraphRAG | Production | Standardized components |
| Databricks | Evaluation/Early | Graph processing integration |

---

## Cross-Domain Connections

- **[semantic-entity-resolution-hybrid-era-draft](semantic-entity-resolution-hybrid-era-draft.md)** — Entity resolution is prerequisite for graph construction quality
- **[ai-augmented-due-diligence-investigative-analytics-draft](ai-augmented-due-diligence-investigative-analytics-draft.md)** — Investigation workflows use graph traversal for relationship discovery
- **[knowledge-graph-construction-patterns](knowledge-graph-construction-patterns.md)** — KG construction methodology and best practices
- **[reasoning-models-chain-of-thought](reasoning-models-chain-of-thought.md)** — Multi-hop reasoning over structured data parallels CoT
- **[data-aggregation-entity-resolution](data-aggregation-entity-resolution.md)** — Core interest domain connection

---

## Primary Sources (Verified)

1. **Microsoft Research GraphRAG** (2024) — Original architecture paper: https://microsoft.github.io/graphrag/
2. **arXiv 2506.05690v3** — GraphRAG-Bench comprehensive benchmark (Feb 2026): https://arxiv.org/abs/2506.05690
3. **FalkorDB GraphRAG SDK Benchmark** (2025) — 90%+ accuracy on schema-bound queries: https://www.falkordb.com/blog/graphrag-accuracy-diffbot-falkordb/
4. **TailoredAI Systematic Evaluation** — RAG vs GraphRAG performance analysis: https://tailoredai.substack.com/p/rag-vs-graphrag-a-performance-analysis
5. **Iterathon Enterprise Guide** (2026) — Cost/performance/latency comparison: https://iterathon.tech/blog/graphrag-vs-vector-rag-2025-enterprise-knowledge-graph-guide
6. **Microsoft Discovery Platform** — Production deployment: https://www.microsoft.com/en-us/research/project/graphrag/
7. **Awesome-GraphRAG** (GitHub) — Curated resource list including ICLR 2026 LinearRAG: https://github.com/DEEP-PolyU/Awesome-GraphRAG
8. **Neo4j GraphRAG** — Production deployment framework (2025)
9. **LangChain GraphRAG** — Standardized integration components
10. **GraphRAG-Bench GitHub** — Official benchmark repository: https://github.com/GraphRAG-Bench/GraphRAG-Benchmark

---

## Open Questions

1. Can LazyGraphRAG reduce indexing costs below practical threshold (<$1K for enterprise datasets)?
2. What graph complexity threshold justifies GraphRAG over vector RAG for a given corpus?
3. How do graph construction errors propagate to retrieval accuracy?
4. What hybrid architectures (vector + graph + reranker) offer best cost/accuracy tradeoff?
5. Can automated graph maintenance keep knowledge graphs fresh without manual schema management?

---

## Deepening Notes

- 10 verified primary sources covering architecture, benchmarks, and production status
- 5 cross-domain connections established
- Key tradeoff identified: GraphRAG wins on complex reasoning (3.4x accuracy) but loses on cost (6x) and latency (4x)
- Failure mode documented: Natural Questions shows 13.4% degradation, proving graph structure isn't universally beneficial
- Production deployments confirmed in Azure, Neo4j, LangChain ecosystems
- Deepening threshold met for STABLE status consideration
