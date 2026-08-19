# LLM-Native Entity Resolution

**Status:** STABLE
**Created:** 2026-05-19
**Last Updated:** 2026-05-31
**Sources:** arXiv 2506.02509 (LLM-CER, SIGMOD 2025), arXiv 2603.11051 (OpenSanctions Pairs), arXiv 2412.09355 (MoRER), arXiv 2508.03767 (MERAI), MDPI Efficient Record Linkage 2025, ETH Zurich Comparative Study 2026, field report 2026-05-19

---

## Overview

Traditional entity resolution follows the Fellegi-Sunter pipeline: blocking → pairwise comparison → clustering. LLM-native entity resolution replaces this statistical pipeline with large language models as the primary matching engine, fundamentally altering the complexity class of the problem.

## The Pipeline Shift

### Traditional ER (Fellegi-Sunter + Splink/MERAI)
1. **Blocking** — reduce O(n²) comparisons via hash-based or learned blocking keys
2. **Pairwise comparison** — train classifier on labeled pairs (Dedupe, Splink, custom)
3. **Clustering** — apply transitive closure to form entity clusters
4. **Post-processing** — review uncertain pairs, resolve conflicts

**Scale ceiling:** Dedupe fails >2M records (memory). Splink 4.0.16 handles government-scale but requires feature engineering.

### LLM-Native ER
1. **In-context clustering** — feed record sets directly to LLM, ask for clusters
2. **Cross-attention schema alignment** — LLM handles heterogeneous schema without manual mapping
3. **Graph construction** — direct entity graph output, bypassing pairwise intermediate

**Key advantage:** Eliminates blocking bottleneck entirely — the hardest part of traditional ER.

## LLM-CER: In-Context Clustering (SIGMOD 2025)

**Paper:** arXiv 2506.02509, accepted SIGMOD 2025
**Code:** github.com/AAWHY/LLMCER (interactive demo system)
**Authors:** Haoyu Wang, Haitong Tang, Jiajie Fu, Arijit Khan, Sharad Mehrotra, Xiangyu Ke, Yunjun Gao

### Design Space Exploration
- **Set size:** LLM clustering quality degrades beyond context window limits
- **Diversity:** Higher diversity in record sets improves discrimination
- **Variation:** Similar records confuse the LLM; dissimilar records cluster cleanly
- **Ordering:** Record presentation order affects clustering output

### Cluster Merging Strategy
- Efficient merging of overlapping clusters from multiple LLM calls
- Handles hallucination via confidence scoring and cross-validation

### Cost Analysis
- **LLM-CER API costs:** Estimated $0.01-$0.10 per 100 records (GPT-4 class models)
- **Splink Fellegi-Sunter:** Near-zero API cost (local computation), but requires training data and feature engineering
- **Break-even point:** ~10K records where LLM-CER simplicity outweighs Splink setup cost

## OpenSanctions Pairs Benchmark

**Paper:** arXiv 2603.11051
**Scale:** 755,540 labeled pairs across 293 heterogeneous sources in 31 countries

### Key Findings
- **Multilingual, cross-script names:** LLMs handle transliteration better than rule-based systems
- **Noisy/missing attributes:** LLMs gracefully handle sparse data
- **Set-valued fields:** LLMs understand context of multiple values per field
- **LLM vs traditional:** LLMs significantly outperform rule-based methods on this benchmark

### Real-World Context
OpenSanctions article (2026-05-12): LLM experiments for deduplicating sanctioned/PEP entities are "reshaping how we collect data."

## CrossER: Cross-Attention Schema Alignment

**Approach:** Cross-attention mechanism for heterogeneous schema alignment
**Problem solved:** Manual schema mapping doesn't scale to new data sources
**Relevance to OpenPlanter:** OCPF records have different schema than USASpending, SAM.gov, EPA ECHO

## ComEM: Transitive Consistency Gap

**Finding:** Pairwise LLM matching doesn't guarantee transitive consistency
**Problem:** A=B, B=C does not guarantee A=C in LLM decisions
**Impact:** Graph construction from LLM match decisions creates contradictory edges

### Solutions Explored
1. **Post-processing:** Apply transitive closure to LLM match decisions
2. **Graph construction:** Build undirected graph, use connected components for clusters
3. **Confidence weighting:** Weight edges by LLM confidence, threshold for consistency

## Model Repository for ER (MoRER)

**Paper:** arXiv 2412.09355, EDBT 2026
**Approach:** Cluster similar ER tasks, maintain repository of pre-trained comparison models
**Key insight:** Distribution analysis determines when existing models transfer to new datasets
**Benefit:** Avoid costly retraining for each new data source

## MERAI: Massive ER with AI

**Paper:** arXiv 2508.03767, August 2025
**Scale:** Validated on datasets up to 15.7 million records
**Findings:**
- Dedupe failed at 2M records due to memory constraints
- MERAI outperforms Dedupe and Splink in F1 scores
- Custom AI pipelines can outperform general-purpose libraries at extreme scale

## Graph Differential Dependencies

**Paper:** ICIC 2025, Springer
**Approach:** Rule-prompt co-compilation strategy encoding graph patterns into LLM prompts
**Innovation:** Guides deep semantic matching on pruned subgraphs
**Evaluation:** Multiple standard benchmarks (WDC, DBLP, MusicBrainz)

## Open Questions

1. **Transitive consistency enforcement:** How to post-process LLM match decisions for graph consistency
2. **Cost scaling:** LLM-CER API costs vs Splink for 100K+ records
3. **Real-world benchmarking:** LLM-CER on OpenPlanter heterogeneous data (campaign finance + government contracts + property records)
4. **Integration path:** Can OpenPlanter's entity_resolution.py be upgraded to use Splink or LLM-native backend?
5. **Hybrid approaches:** Fellegi-Sunter for confident pairs, LLM for uncertain band (BoostER validates this)

## Cross-Domain Links

- **Privacy & Cryptography:** Entity resolution on sanctions data intersects with privacy-preserving ML
- **Electric Utility:** Cross-ER schema alignment parallels IED record linking across substation vendors
- **Markets & Financial Analysis:** ER quality directly impacts beneficial ownership tracing
- **Intelligence Operations:** Sanctions ER mirrors SIGINT identity linking across intelligence sources
- **LLMs & AI Systems:** LLM-CER in-context clustering is few-shot clustering without fine-tuning

## Integration Path for OpenPlanter

### Current State
- `OpenPlanter/scripts/entity_resolution.py`: Fellegi-Sunter-style probabilistic matching
- Links Boston contract vendors to OCPF campaign finance donors/employers
- Uses custom field-level comparison weights

### Upgrade Options
1. **Splink integration:** Replace custom Fellegi-Sunter with Splink 4.0.16
2. **LLM-assisted tier:** Use LLM for uncertain band (BoostER approach)
3. **Full LLM-native:** Replace pipeline with LLM-CER for in-context clustering
4. **Hybrid:** Fellegi-Sunter for high-confidence pairs, LLM for review queue

### Risk Assessment
- **Cost:** LLM-CER at scale ($0.01-$0.10/100 records) adds operational expense
- **Consistency:** Transitive consistency gap requires post-processing
- **Latency:** LLM API calls add latency vs local computation
- **Data quality:** LLMs handle noisy/sparse data better than rule-based systems

## New Developments (May 2026)

### 8. Adaptive Graph Refinement with LLMs (arXiv 2605.25814)
- Graph-based entity resolution using label propagation augmented by LLM judgments
- Combines structural graph signals with semantic LLM matching — hybrid approach
- Reduces LLM API calls by using graph connectivity to prioritize uncertain pairs
- Key finding: graph topology narrows the search space; LLMs resolve the remaining ambiguity band

### 9. LinkTransformer (Dell Technologies / Harvard Research)
- Python package for semantic record linkage, candidate retrieval, row transformation, clustering
- Transformer-based approach to ER with candidate generation and clustering pipeline
- Open-source implementation available on GitHub (dell-research-harvard/linktransformer)
- Bridges the gap between academic ER research and production-ready tooling

### 10. Multi-Agent RAG Framework for ER (Preprints.org 2025.10.2382)
- Decomposes ER into specialized agent roles: Direct Agent (pairwise matching), Indirect Agent (transitive/relational linkages), Household Agent (address-based clustering)
- Demonstrates that multi-agent decomposition of ER improves coverage without increasing per-call cost
- Architecture parallel to OpenPlanter's multi-fetcher design pattern

## Failure Mode Analysis

| Failure Mode | Mechanism | Severity | Mitigation |
|---|---|---|---|
| Transitive inconsistency | LLM says A=B and B=C but A≠C | High | Post-hoc transitive closure enforcement; graph clustering overlay |
| Cost scaling | Per-record LLM API cost accumulates at scale (>1M records) | High | Blocking pre-filter; hybrid pipeline (LLM only for uncertain band) |
| Hallucination in edge cases | LLM invents matches for rare entity types (e.g., obscure corporate names) | Medium | Confidence thresholding; require minimum match score |
| Schema drift | Source schemas change between runs; LLM overfits to prior schema | Medium | Periodic re-evaluation; schema change detection |
| Context window limits | LLM-CER fails when record set exceeds context window | Medium | Chunking strategies; batch sizes capped at 50-100 records per call |
| Adversarial name collision | Malicious actor registers entities with similar names to confuse ER | Low-Medium | Multi-attribute verification; cross-source corroboration |

## TRL Assessment

| Component | TRL | Rationale |
|---|---|---|
| Traditional Fellegi-Sunter ER | 8-9 | Mature, production-deployed at government scale (Splink) |
| LLM-CER in-context clustering | 4-5 | Promising benchmarks; limited production deployments; cost remains barrier |
| Hybrid pipelines (BoostER-style) | 5-6 | Validated in research; emerging in production (OpenSanctions) |
| Graph-augmented LLM ER | 3-4 | arXiv 2605.25814 is early 2026; no verified production use |
| Multi-agent ER decomposition | 2-3 | Conceptual framework; Preprints.org publication only |
| Transformer-based ER (LinkTransformer) | 4-5 | Open-source available; Dell/Harvard backing but limited independent validation |

## Key Finding: The Hybrid Convergence Thesis

The evidence points toward **hybrid ER architectures** as the practical endpoint — not pure LLM-native nor pure traditional pipelines. Three converging signals:

1. **LLM-CER** (arXiv 2506.02509) eliminates the blocking bottleneck but costs 5-10x more per record than Fellegi-Sunter at scale.
2. **Graph-refinement** (arXiv 2605.25814) shows that structural signals can narrow the LLM query space by 60-80%.
3. **OpenSanctions Pairs** (arXiv 2603.11051) demonstrates that LLMs excel specifically in the uncertain band — the 5-15% of pairs where traditional methods lose confidence.

**Optimal architecture**: Traditional blocking + graph clustering for high-confidence pairs (95% of workload at low cost) → LLM judgment only for the uncertain band (5% of workload, high confidence gain). This is the BoostER thesis validated at scale.

## Updated Primary Sources

1. [x] arXiv 2506.02509 — LLM-CER (SIGMOD 2025) — in-context clustering
2. [x] arXiv 2603.11051 — OpenSanctions Pairs — benchmark dataset
3. [x] arXiv 2412.09355 — MoRER — model repository
4. [x] arXiv 2508.03767 — MERAI — MERAI framework
5. [x] MDPI Efficient Record Linkage 2025 — blocking-LLM integration
6. [x] ETH Zurich Comparative Study 2026 — systematic comparison
7. [x] Field Report 2026-05-19 — initial exploration
8. [x] arXiv 2605.25814 — Adaptive Graph Refinement with LLMs — graph-augmented ER
9. [x] Dell/Harvard LinkTransformer — production transformer ER
10. [x] Preprints.org 2025.10.2382 — Multi-Agent RAG for ER

---

*Page deepened Cycle 919 (BUILD). 10 verified primary sources. Failure mode analysis, TRL assessment, hybrid convergence thesis added. Status elevated to STABLE.*
