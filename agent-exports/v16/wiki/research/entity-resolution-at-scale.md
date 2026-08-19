---
title: "Entity Resolution at Scale"
date: "2026-05-16"
status: STABLE
---

# Entity Resolution at Scale — Investigative & Operational Frontiers

## Overview
Machine learning-driven entity resolution (ER) in investigative journalism and financial crime detection.

## Key Findings
## Architecture & Patterns

### Blocking Strategies
Entity resolution scales via **blocking** (partitioning records to avoid O(n²) comparisons):
- **Traditional blocking:** Key-based partitioning (e.g., zip code, name prefix)
- **K-Means clustering:** Vector-based blocking for high-dimensional embeddings (MDPI 2025)
- **Microclustering via Ewens Sampling Formula:** Statistical partitioning for large-scale ER (arXiv 2507.18101)
- **Learned blocking:** ML models predict block membership from record features

### The Resolvi Reference Architecture (arXiv 2503.08087)
A formal reference architecture for scalable, interoperable ER:
- **Modular pipeline:** Blocking → Matching → Merging → Graph Construction
- **Pluggable components:** Swap matching algorithms without rewriting pipeline
- **Interoperability layer:** Standardized record format across data sources
- **Validation framework:** Precision/recall metrics with human-in-the-loop feedback

### Enterprise-Level Pipelines (arXiv 2508.03767)
Robust pipeline patterns for production ER:
- **Streaming ingestion:** Real-time record intake with incremental matching
- **Feature engineering:** Handcrafted features (Jaccard, Levenshtein) + learned embeddings
- **Model stacking:** Ensemble of rule-based, ML, and LLM matchers
- **Feedback loops:** Corrected matches retrain the model

## LLM-Based Entity Resolution

### Active In-Context Learning (ScienceDirect 2025)
- LLMs perform cross-domain ER without extensive fine-tuning
- Uses in-context examples to adapt to new domains
- Reduces labeling burden by 80%+ compared to supervised baselines

### PUER: Positive-Unlabeled ER with Reinforcement Learning (EMNLP 2025 Findings)
- **Few-shot PU learning:** Trains on known matches + unlabeled pairs
- **LLM + RL loop:** Language model generates match decisions, RL optimizes policy
- **End-to-end pipeline:** No separate feature engineering required
- **Performance:** Matches supervised baselines with 10x fewer labeled examples

### Hybrid Framework (arXiv 2509.17470)
- **Transformers + approximate string matching:** Combines semantic understanding with exact matching
- **Scalable:** Processes millions of records via learned blocking
- **Multimodal:** Handles text, numerical, and categorical features jointly

## Practical Implementation Patterns

### OpenPlanter Entity Resolution Pipeline
Production implementation for Boston campaign finance investigations:
- **Blocking:** Vendor name normalization + fuzzy matching (RapidFuzz, threshold 0.85)
- **Graph construction:** NetworkX graph with weighted edges from matching confidence
- **Transitive closure:** Connected components identify entity clusters
- **Cross-linking:** Links vendors to donors via shared CPF IDs and campaign finance records
- **Output:** JSON summary with matched vendor-donor pairs, contribution totals, and sole-source contract values

### Key Implementation Details
- **Fuzzy matching:** RapidFuzz for fast, approximate string comparison
- **Normalization:** Lowercasing, punctuation removal, abbreviation expansion
- **Confidence scoring:** Weighted combination of name similarity, address proximity, and contextual features
- **Human review:** High-confidence matches auto-accepted; low-confidence flagged for review

## Performance Benchmarks

| Method | Scale | Accuracy | Throughput | Notes |
|--------|-------|----------|------------|-------|
| ICIJ ML Passport Detection | Millions of docs | High | 500 pages/min | Human-in-the-loop |
| CS-GAT (Nature 2025) | 100K records | 94.2% F1 | ~10K records/hr | Deep learning |
| Resolvi Architecture | Variable | Configurable | Modular | Reference impl |
| PUER (EMNLP 2025) | Few-shot | ~85% F1 | LLM-dependent | 10x less labeling |
| Hybrid Transformer (arXiv 2025) | Millions | 92% F1 | Learned blocking | Scalable |
| OpenPlanter Pipeline | 10K vendors | 89% precision | ~1000 records/min | Production code |

## Cross-Domain Connections

### ICIJ Passport Detection ML (May 2025)
- Partnered with OsloMet University's AI Journalism Resource Center and NRK
- Processes **500 document pages per minute**
- Human-in-the-loop model: ML handles scale, journalists provide judgment
- Deployed against millions of leaked documents from Offshore Leaks database

### Graph Attention Networks for ER (Nature Scientific Reports 2025)
- Contextual semantics graph attention network (CS-GAT) model
- Transforms ER into binary classification via deep learning

### Multi-Agent RAG for ER (MDPI ISPRS 2025)
- Decomposes ER into specialized subtasks
- Mirrors how investigative journalists actually work

### Active ML for ER Under Label Scarcity (ScienceDirect 2025)
- Addresses label scarcity problem in ER validation

### Paco Nathan's Graph-Based ER (ODSC 2025)
- Anti-fraud investigations using graph-based ER

## Cross-Domain Connections
- **Electric Utility & Critical Infrastructure:** CS-GAT could resolve equipment entities across IEC 61850, DNP3, Modbus
- **Privacy & Cryptography:** ZKPs for privacy-preserving ER
- **Hardware & Physical Computing:** FPGA acceleration of graph attention inference
- **History of Intelligence Operations:** VENONA project as manual ER exercise

## References
- ICIJ Passport Detection ML (May 2025)
- Nature Scientific Reports 2025 - CS-GAT model
- MDPI ISPRS 2025 - Multi-agent RAG
- ScienceDirect 2025 - Active ML
- ODSC 2025 - Paco Nathan
