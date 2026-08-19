# Network Analysis Techniques for Investigative Graphs

**Status:** STABLE
**Created:** 2026-05-23
**Last Updated:** 2026-05-23
**Interest Area:** OSINT & Investigative Analysis
**Cross-Domain Links:** 4 (entity-resolution-2026-state-of-the-art, knowledge-graph-construction-patterns, ai-supply-chain-resilience-operational, geopolitical-commodity-supply-chain-risk)
**Verified Primary Sources:** 10

## Overview

Graph-based network analysis applied to investigative contexts: centrality analysis, community detection, temporal network evolution, link prediction, and graph neural networks for financial crime, OSINT investigations, and intelligence analysis.

## GNN-Based Fraud Detection (2024-2026)

The field has matured significantly with comprehensive survey coverage:

1. **GNN Financial Fraud Detection Review** (arXiv 2411.05815) — comprehensive structured analysis of GNN applications in financial fraud detection across detection architectures, datasets, and evaluation benchmarks
2. **FLAG: LLM-Enhanced GNN for Fraud** (KDD 2025) — integrates LLM textual features with GNN graph features for fraud detection, addressing limitations of graph-only approaches
3. **FraudGT: Graph Transformer for Fraud Detection** (ACM SIGKDD 2025) — simple effective graph transformer achieving competitive performance with reduced complexity vs GNN baselines
4. **GNN Real-World Challenges** (arXiv 2403.04468) — surveys imbalance, noise, privacy, and OOD challenges in deployed GNN systems for fraud detection
5. **Safe-Graph Curated Papers** (GitHub: safe-graph/graph-fraud-detection-papers) — interactive dashboard with 250+ publicly accessible fraud detection papers

## Temporal Network Analysis & Community Detection

Temporal dimensions are critical for investigative work where networks evolve:

6. **Temporal Community Detection with Network Embeddings** (MDPI Mathematics 13(5):698, 2025) — updating rules with convergence proofs; validated on email and phone call networks
7. **Continuous-Time Temporal Community Detection** (arXiv 2510.00741) — extends community detection to exact temporal settings rather than snapshot-based approaches
8. **DynBenchmark** (arXiv 2510.06245) — new benchmarking framework with customizable ground-truth community evolution patterns for evaluating temporal community detection
9. **Quantifying Community Evolution** (Nature Sci Rep s41598-025-28511-7, Nov 2025) — new similarity measurement method for tracking community changes over time
10. **LLM-Based Community Discovery** (arXiv 2507.22955) — extends community detection beyond vector embeddings using LLM reasoning capabilities

## Key Findings

- GNNs now standard for financial fraud; graph transformers and LLM-enhanced variants are the 2025-2026 frontier
- Temporal dimension under-explored in fraud detection; most GNN papers use static graphs
- LLM integration is the convergence point for both community detection and fraud detection
- DynBenchmark addresses lack of standardized temporal community detection evaluation

## Cross-Domain Connections

- **Entity Resolution**: ER is prerequisite for accurate investigation graphs. LLM-native ER (LLM-CER, SIGMOD 2025) pairs with GNN fraud detection downstream
- **Knowledge Graph Construction**: KG construction pipelines feed into network analysis. AutoSchemaKG (900M nodes) provides graph substrate
- **AI Supply Chain Resilience**: Network analysis of supply chain disruption uses identical GNN and community detection techniques
- **Geopolitical Risk**: Sanctions evasion route analysis is temporal community detection on trade flow networks
