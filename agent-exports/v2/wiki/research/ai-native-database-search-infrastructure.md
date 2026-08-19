# AI-Native Database & Search Infrastructure

**Status:** STABLE
**Created:** 2026-05-20
**Last Deepened:** 2026-05-20
**Primary Sources:** 8 verified
**Cross-Domain Links:** 6 mapped

---

## Overview

AI-native database systems and search infrastructure underpin modern LLM applications, agent memory systems, and RAG pipelines. The field has matured from research prototypes to production infrastructure with measurable benchmarks, clear tradeoff curves, and emerging standardization around hybrid architectures.

## Architecture Landscape

### 1. Purpose-Built Vector Databases

**Players:** Pinecone, Weaviate, Qdrant, Milvus/Zilliz, Chroma

**Indexing algorithms:**
- **HNSW (Hierarchical Navigable Small World)** — dominant algorithm, 98% recall at 5ms latency for 1B+ embeddings (TechBytes 2026 benchmark). Best for read-heavy workloads where latency matters more than memory.
- **IVF-Flat** — reduces memory by 40% vs HNSW but at recall cost. Preferred when memory budget is constrained.
- **IVF-PQ (Product Quantization)** — alternative for very large datasets (>10M vectors), trades recall for storage efficiency.

**Key benchmark finding (2026):** At single-digit million scale, pgvector's HNSW index matches or beats dedicated databases at 99% accuracy (Supabase benchmarks, tianpan.co Apr 2026). The 60-80% cost savings over managed vector DBs are real at this scale.

### 2. Traditional DBs with Vector Extensions

**pgvector** has become the default for small-to-medium deployments due to PostgreSQL ubiquity. Keeps vector and relational data in one ACID-consistent store, eliminating a category of consistency bugs.

**MongoDB Atlas Vector Search** and **Elasticsearch dense_vector** offer vector capabilities within existing search/NoSQL stacks.

### 3. Hybrid Search: The Production Standard

**Finding:** Hybrid search (dense vector + sparse BM25/lexical) is now the production standard for RAG systems.

- Dense-only retrieval: ~62% accuracy
- Hybrid (dense + BM25): **91% retrieval accuracy** — a 48% improvement (Medium/@pbronck, verified via multiple 2025-2026 sources)
- TREC RAG 2025 Track: UTokyo-HitU achieved top results combining sparse retrievers (BM25, SPLADE) with dense retrievers (BGE-small, Qwen3-Embedding-0.6B) plus HyDE query augmentation and LLM-based reranking (arXiv 2604.01733)

**Why hybrid works:** BM25's IDF weighting catches exact keyword matches that embeddings miss (proper nouns, rare terms, exact product codes). Dense vectors catch semantic similarity that lexical search misses. Together they cover complementary failure modes.

### 4. Multi-Modal Vector Indexing

**State (mid-2026):**
- **Google Gemini Embedding 2** — first natively multimodal embedding model mapping text, images, video, audio, and PDFs into single vector space (Google Blog, 2026)
- **VLM2Vec-V2** (arXiv 2507.04590) — unified framework for learning embeddings across diverse visual forms (images with any resolution, text with any length)
- **Voyage AI multimodal embeddings** — text and content-rich images (figures, slide decks, document screenshots) in shared space
- Netflix trained combined video+text embedding space for video search

### 5. Agent Memory Backends

**Finding (mem0.ai State of AI Agent Memory 2026):** Agent memory is a production engineering discipline with 21 frameworks, 20 vector stores, and 3 hosting models (managed cloud, open-source self-hosted, local MCP).

**Memory taxonomy (arXiv 2512.13564):**
- **Short-term/working memory** — current conversation context, active reasoning scratchpad. Typically in-context buffers or ephemeral KV stores.
- **Long-term memory** — durable knowledge stores backed by vector databases. Semantic recall via similarity search.
- **Episodic memory** — session-specific event logs. Often graph-backed for relationship traversal.

**Cost impact:** Vector-backed long-term memory reduces context costs from $2.4K to $960/month (60% reduction) with frameworks like Mem0 and AgentCore (Iterathon 2026).

**Redis architecture pattern:** LLMs are stateless by default. Agent memory systems add short-term, long-term, and episodic memory layers so agents maintain context across sessions. Vector databases handle semantic recall; graph databases handle relationship traversal.

## Primary Sources (Verified)

1. **VectorDBBench (Zilliz/GitHub)** — open-source benchmark tool for vector database performance and cost-effectiveness comparison
2. **arXiv 2604.01733** — "From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text" — systematic comparison of 10 retrieval strategies on heterogeneous documents
3. **arXiv 2512.13564** — "Memory in the Age of AI Agents" — comprehensive agent memory landscape survey
4. **arXiv 2507.04590** — VLM2Vec-V2: Advancing Multimodal Embedding for Videos
5. **Supabase benchmarks (tianpan.co Apr 2026)** — pgvector HNSW matching dedicated DBs at 99% accuracy, single-digit million scale
6. **Google Gemini Embedding 2 announcement (2026)** — first natively multimodal embedding model
7. **mem0.ai State of AI Agent Memory 2026** — 21 frameworks, 20 vector stores, 3 hosting models
8. **TREC RAG 2025 Track results (UTokyo-HitU)** — hybrid sparse+dense+reranking approach

## Cross-Domain Connections

1. **Entity Resolution** — vector similarity for record matching (cosine similarity on embeddings as fuzzy matching layer). pgvector-backed ER pipelines replace pairwise string comparison.
2. **AI Agent Infrastructure** — memory backends for autonomous agents. Vector DBs provide the long-term memory layer; working memory is in-context.
3. **Data Aggregation** — unified hybrid search across heterogeneous data sources (corporate registries, filings, property records). BM25 catches exact entity names; dense vectors catch semantic relationships.
4. **Privacy & Cryptography** — vector search with homomorphic encryption (research stage). Post-quantum metadata risks for embedding stores.
5. **Adversarial ML** — adversarial examples in vector space (adversarial embeddings that manipulate retrieval). Robustness of ANN indexes against poisoning.
6. **Autonomous Self-Improving Agents** — agent memory is the substrate for self-improvement loops. Without durable memory, reflective agents cannot accumulate experience.

## Integration Path for OpenPlanter

- **Immediate:** pgvector for entity resolution similarity matching — replace pairwise string comparison with embedding-based similarity
- **Near-term:** Hybrid search (BM25 + dense) for cross-source correlation queries
- **Future:** Multi-modal indexing if OpenPlanter ingests scanned documents, images, or PDFs
- **Agent memory:** Vector-backed durable memory for investigation context persistence across sessions

## Key Metrics Summary

| Metric | Dense-only | Hybrid (Dense+BM25) | Improvement |
|--------|-----------|---------------------|-------------|
| RAG recall@10 | ~62% | 91% | +48% |
| Context cost (monthly) | $2,400 | $960 | -60% |
| pgvector vs managed DB accuracy | 99% | 99% | parity at <10M vectors |
| HNSW recall@5ms | 98% | — | 1B+ embeddings |
| IVF-Flat memory savings | — | 40% | vs HNSW |

## Open Questions
- Post-quantum vector search (PQC-protected embedding stores)
- Real-time vector index updates at scale (streaming ingestion vs batch)
- Multi-agent shared memory (how do agents coordinate when sharing vector-backed memory)
- Embedding drift over time (do embeddings need re-indexing as models update)
