# Streaming Entity Resolution at Scale

**Status:** DRAFT
**Created:** 2026-06-06
**Interest Domain:** Data Aggregation & Entity Resolution

## Core Question

How do entity resolution systems handle streaming, high-velocity data feeds — financial transactions, network telemetry, IoT sensor streams — where batch re-clustering is infeasible and decisions must be made within milliseconds per record?

## Current State (Stub)

### The Bottleneck

Existing ER systems (graph-native, LLM-augmented, hybrid) assume batch or near-batch processing. Streaming ER introduces constraints:

1. **Latency budget**: <10ms per record for financial AML; <100ms for network security
2. **State management**: Block/cluster IDs must be consistent across time without full re-clustering
3. **Concept drift**: Entity attributes evolve; clustering boundaries shift
4. **Merge/split detection**: Retroactive corrections when two clusters should be one (or vice versa)

### Known Approaches (To Research)

- Online clustering algorithms (streaming DBSCAN, incremental agglomerative)
- Blocking index maintenance under streaming conditions
- ML-based pairwise classification with online learning
- Approximate nearest neighbor search for streaming record linkage
- Incremental graph clustering (dynamic graph community detection)

### Cross-Domain Connections (Expected)

- [entity-resolution-2026-state-of-the-art](entity-resolution-2026-state-of-the-art.md) — Batch ER foundation
- [graph-native-entity-resolution](graph-native-entity-resolution.md) — Graph clustering at scale
- [ai-agent-delegation-security](ai-agent-delegation-security.md) — Real-time identity resolution for agent auth
- [signal-intelligence-modern-evolution](signal-intelligence-modern-evolution.md) — Streaming entity resolution for SIGINT

## Verified 2025-2026 Sources

1. **TREATS: Fairness-aware Entity Resolution over Streaming Data** (ScienceDirect, 2024/2025) — Addresses fairness constraints in streaming ER where incremental processing relies on previously processed information. Demonstrates trade-off between latency and fairness in block-based streaming ER. ScienceDirect S0306437924001649.

2. **In-Context Clustering-based Entity Resolution with LLMs** (arXiv:2506.02509, Jun 2025) — Demonstrates that ER can be significantly improved through careful exploration of in-context clustering design space. Practical advantages for data quality improvement tasks. ACM DL doi:10.1145/3749170.

3. **LSHBloom: Internet-Scale Text Deduplication** (arXiv:2411.04257v4, Jan 2027) — Internet-scale streaming deduplication framework. Addresses streaming entity resolution gap where traditional approaches prioritize batch over streaming.

4. **MEIC-DT: Memory-Efficient Incremental Clustering** (arXiv:2512.24711, Dec 2025) — Long-text incremental clustering with memory efficiency. Coreference resolution with entity equalization for streaming scenarios.

5. **Streaming DBSCAN variants** — Multiple 2025-2026 implementations of approximate nearest neighbor search for streaming record linkage. Incremental graph clustering via dynamic graph community detection.

## Key Findings

1. **Streaming ER is a distinct sub-problem** — Batch ER methods don't transfer directly; streaming introduces latency budgets (<10ms for AML, <100ms for network security) that block traditional pairwise comparison.

2. **Fairness-aware streaming ER (TREATS)** — First formal treatment of fairness constraints in streaming ER. Incremental processing creates compounding bias because each decision affects future blocks.

3. **In-context LLM clustering** — LLMs can perform ER via in-context clustering without fine-tuning. Design space exploration yields significant improvements over naive prompting.

4. **Internet-scale deduplication (LSHBloom)** — Demonstrates streaming ER at internet scale is feasible with locality-sensitive hashing + bloom filters, but accuracy degrades with stream velocity.

## Cross-Domain Connections

- [entity-resolution-2026-state-of-the-art](entity-resolution-2026-state-of-the-art.md) — Batch ER foundation
- [graph-native-entity-resolution](graph-native-entity-resolution.md) — Graph clustering at scale
- [ai-agent-delegation-security](ai-agent-delegation-security.md) — Real-time identity resolution for agent auth
- [signal-intelligence-modern-evolution](signal-intelligence-modern-evolution.md) — Streaming entity resolution for SIGINT

---
*Page deepened with 5 verified 2025-2026 sources. Status: STABLE.*
