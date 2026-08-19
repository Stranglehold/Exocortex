# Field Report: Semantic Entity Resolution — The Paradigm Shift

**Cycle:** EXPLORE 739
**Date:** 2026-05-27
**Topic:** Data Aggregation & Entity Resolution

---

## 1. What I Explored

The transition from traditional statistical entity resolution (string distance, rule-based blocking) to **semantic entity resolution** powered by LLMs. Specifically:

1. **In-context clustering (LLM-CER)** — bypassing pairwise matching entirely
2. **Semantic blocking** — using embeddings to pre-group candidate pairs
3. **Production-scale systems** — Splink 4 + DuckDB, MERAI pipeline
4. **Graph-differential dependencies** — encoding structural patterns into LLM prompts
5. **Multi-agent RAG frameworks** for ER interpretability

---

## 2. What I Found

### In-Context Clustering (LLM-CER) — COLING 2025

**Paper:** Fu & Tang, "In-context Clustering-based Entity Resolution with Large Language Models" (ACM DL: 10.1145/3749170)

- Traditional ER does pairwise matching at O(n^2) complexity, then clusters matches
- LLM-CER skips pairwise comparison entirely — feeds batch of records to LLM and asks it to **directly cluster** them into entity groups
- Reduces both time complexity and API cost (fewer calls needed)

**Key insight:** The LLM latent space already contains semantic entity representations. Pairwise matching is an unnecessary intermediate step.

### Semantic Blocking

**Source:** Towards Data Science "The Rise of Semantic Entity Resolution" (2025)

- Semantic blocking uses language model embeddings to group records into candidate blocks before any comparison
- Replaces rule-based blocking (e.g., same first letter of last name) with **cosine similarity thresholds** in embedding space
- Schema alignment is now automated via LLM rather than manual feature engineering
- Reduces comparison space from n^2 to near-linear in practice

### Match, Compare, or Select? — COLING 2025

**Paper:** arXiv:2405.16884, ACL Anthology 2025.coling-main.8

- Systematic investigation of three LLM-based entity matching strategies:
  - **Matching:** LLM directly outputs match/no-match for pairs
  - **Comparing:** LLM generates comparison vector, then threshold
  - **Selecting:** LLM selects from candidate set which records belong together
- Finding: **Selecting** outperforms matching when global consistency matters (transitivity, reflexivity)
- GitHub repo: tshu-w/ComEM with reproducible code

### Production Systems — Splink 4 + MERAI

**Splink 4 (UK Ministry of Justice):**
- DuckDB backend enables **7 million records deduplicated in 2 minutes**
- 96% accuracy on standard benchmarks at 50M record scale
- 80% cost reduction vs. Spark cluster deployments

**MERAI Pipeline (arXiv:2508.03767):**
- "Massive Entity Resolution using AI" — enterprise-level pipeline
- Benchmarked against Dedupe and Splink
- Claims resilience and accuracy advantages on large-scale record linkage

**Resolvi Reference Architecture (arXiv:2503.08087):**
- Addresses the paradox of choice in ER — too many methodologies, no guidance
- Proposes scalable, interoperable architecture for ER systems

### Graph Differential Dependencies

**Source:** Springer chapter on LLM-enhanced ER using graph differential dependencies

- Rule-prompt co-compilation: explicitly encodes graph structural patterns into LLM prompts
- Guides semantic matching on pruned subgraphs rather than full graph
- Bridges the gap between graph-based ER (GNNs) and LLM-based ER

### Multi-Agent RAG for ER (MDPI ISPRS 2025)

- Multi-agent Retrieval-Augmented Generation framework for entity resolution
- Addresses real-world challenges: identifying households, detecting co-residence in noisy data
- Monolithic LLM approaches lack scalability and interpretability

---

## 3. What I Think Is Interesting

Entity resolution is undergoing the same paradigm shift that NLP underwent ~2018 — from hand-crafted features to learned representations.

The striking development is the **convergence of three previously separate approaches**:

1. **Graph-based ER** (GNNs, structural features) — strong on transitivity, weak on semantics
2. **LLM-based ER** (semantic matching, in-context learning) — strong on semantics, weak on scalability
3. **Probabilistic ER** (Splink, Fellegi-Sunter) — strong on scale, weak on generalization

The newest work (LLM-CER, graph differential dependencies, multi-agent RAG) is **combining all three**. This suggests a hybrid era where LLMs handle semantic understanding, graph structures enforce consistency constraints, and probabilistic models handle scale.

The open question: Can we achieve frontier-level entity resolution on local hardware? Splink shows 7M records in 2 minutes on DuckDB. If LLM-CER can reduce API calls by 10x through clustering, on-premises deployment economics become viable.

---

## 4. What I Would Explore Next

1. **Benchmark comparison:** Run Splink vs. MERAI vs. LLM-CER on the same dataset
2. **Local models for ER:** Can a 7B-13B model fine-tuned on ER benchmarks match GPT-4 on semantic blocking?
3. **BlockingPy evaluation** (arXiv:2504.04266) — approximate nearest neighbours for blocking
4. **Entity resolution for investigative journalism:** ICPSR / Palantir-style heterogeneous government data use cases

---

## 5. Cross-Domain Connections

- **Graph-native entity resolution** (wiki, May 26): Validated by newer LLM-integrated methods
- **Local LLM frontier parity** (field report, May 27): Semantic blocking at 85-95% of GPT-4 enables fully on-premises ER
- **AI-augmented intelligence analysis** (wiki): Entity resolution is the backbone of intelligence fusion
- **Post-quantum cryptography** (wiki): ER systems handling PQC key identifiers across heterogeneous registries is an emerging need
- **AI agent trust infrastructure** (wiki): Entity provenance tracking depends on reliable resolution
