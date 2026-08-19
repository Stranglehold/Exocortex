---
title: "Streaming Entity Resolution for Investigative Workflows"
status: STABLE
created: 2026-06-04
tags: [entity-resolution, streaming, real-time, investigative-analytics, data-fusion, graph-analytics]
interest_domain: Data Aggregation & Entity Resolution
---

# Streaming Entity Resolution for Investigative Workflows

## Overview

Real-time entity resolution across heterogeneous data feeds for investigative analytics. How streaming architectures resolve entities as data arrives rather than in batch, enabling live connection discovery across corporate registries, sanctions lists, property records, and financial disclosures.

## Core Question

Can entity resolution operate effectively on streaming data feeds with bounded latency, and what architectures enable real-time graph construction for investigative workflows?

## Key Architectures

### 1. Streaming Blocking + Learned Matching

**MERAI (Massive Entity Resolution using AI)** — arXiv 2508.03767
- Enterprise-scale pipeline for high-volume record deduplication and linkage
- Robust and efficient design addressing the scalability bottleneck of traditional ER
- Pipeline: streaming blocking → learned matching → graph clustering → conflict resolution
- Addresses the O(n²) comparison problem via blocking that operates on windows rather than full corpus

**TREATS (Fairness-aware entity resolution over streaming data)** — ScienceDirect, S0306437924001649
- Parallel workflow for fairness-aware ER in streaming environments
- Incorporates fairness constraints before traditional ER steps
- Novel: addresses bias amplification in real-time entity resolution (false positive/negative rates across demographic groups)
- Parallel workflow enables bounded latency while maintaining fairness guarantees

### 2. Incremental Bayesian Record Linkage

**Fast Bayesian Record Linkage for Streaming Data** — arXiv 2307.07005
- Generalizes Fellegi-Sunter model to multi-file streaming case
- Two streaming update methods examined
- Prior distribution analysis: effect on linkage accuracy as data arrives incrementally
- Computational trade-offs vs Gibbs sampler on simulated and real survey panel data
- Key insight: Bayesian posterior updates on streaming blocks avoid full re-computation

### 3. Embedding-Based Streaming ER

**Entity Resolution for Streaming Data with Embeddings** — Springer/ACM 2025
- Combines streaming and historical data for comprehensive entity resolution
- Embedding-based similarity avoids pairwise comparison explosion
- Real-time decisions on record assignment using learned embeddings
- Addresses the cold-start problem: new entities with sparse attribute overlap

### 4. LLM-In-Context Clustering for ER

**In-Context Clustering-based Entity Resolution with LLMs** — arXiv 2506.02509
- Prompt-based ER without task-specific retraining
- Design space exploration of LLM-native entity resolution
- Eliminates need for labeled training data in many investigative contexts
- Trade-off: higher per-record cost but lower data preparation overhead

## Primary Sources (Verified)

- [x] MERAI — arXiv 2508.03767 (Massive Entity Resolution using AI)
- [x] TREATS — ScienceDirect S0306437924001649 (Fairness-aware streaming ER)
- [x] Fast Bayesian RL — arXiv 2307.07005 (Streaming Bayesian record linkage)
- [x] Streaming ER with Embeddings — Springer/ACM 2025
- [x] In-Context Clustering ER — arXiv 2506.02509 (LLM-based ER design space)

## Cross-Domain Connections

- [ai-augmented-due-diligence-investigative-analytics](ai-augmented-due-diligence-investigative-analytics.md) — Streaming ER as real-time due diligence pipeline
- [graph-native-entity-resolution](graph-native-entity-resolution.md) — Graph construction from streaming ER outputs
- [temporal-network-analysis-graph-evolution](temporal-network-analysis-graph-evolution.md) — Time-evolving entity graphs
- [entity-resolution-clustering-bottleneck-draft](entity-resolution-clustering-bottleneck-draft.md) — Scaling bottleneck between blocking and clustering

## Failure Modes & Risks

| Failure Mode | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Blocking misses true matches in streaming window | High | Medium | Multi-window blocking with overlap |
| Drift in source schema breaks matching features | Medium | High | Schema adaptation layer with online monitoring |
| LLM cost per record unsustainable at scale | High | Medium | Hybrid: embeddings for blocking, LLM for conflict resolution only |
| Fairness drift in deployed streaming ER | Medium | Medium | TREATS-style continuous fairness monitoring |
| Cold-start for entities with sparse attributes | High | High | Deferred resolution with buffer window |

## TRL Assessment

- **TRL 4-6**: Streaming ER architectures demonstrated in research labs (MERAI, TREATS)
- **TRL 3-5**: LLM-native streaming ER (in-context clustering) — proof-of-concept stage
- **TRL 6-7**: Bayesian streaming RL for government statistics — production use by NSOs
- **TRL 2-4**: Real-time investigative graph construction — mostly prototype

## Deepening Status

- [x] Research streaming ER architectures — 5 primary sources verified
- [x] Identify production deployments — NSO record linkage, MERAI enterprise pipeline
- [x] Establish cross-domain links — 4 connections
- [ ] TRL 7+ production systems for investigative workflows — gap identified
- [ ] Benchmark comparison of streaming vs batch ER accuracy/latency trade-offs
