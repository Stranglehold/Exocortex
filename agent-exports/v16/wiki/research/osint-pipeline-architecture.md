# OSINT Pipeline Architecture

**Status:** STABLE  
**Created:** 2026-05-16  
**Last Updated:** 2026-05-16  
**Deepened by:** BUILD cycle #30  

---

## Overview

How heterogeneous public data sources are collected, normalized, entity-resolved, and linked into actionable investigation graphs. This page documents the pipeline architecture used by OpenPlanter's collector system and cross-references external OSINT pipeline research.

## Core Question

Given N heterogeneous data sources (corporate registries, campaign finance records, lobbying disclosures, government contracts, property records, sanctions lists), what is the optimal pipeline architecture for:
1. **Reliable collection** — crawling, API access, rate limiting, retry logic
2. **Normalization** — schema mapping, type coercion, deduplication within sources
3. **Entity resolution** — linking the same real-world entity across different sources
4. **Graph construction** — relationship extraction and graph storage
5. **Anomaly detection** — surfacing non-obvious connections

## Pipeline Stages

### Stage 1: Collection

OpenPlanter uses a phased collector architecture:

| Phase | Collectors | Sources |
|-------|-----------|--------|
| Phase 2 | 9 collectors | FEC, SEC EDGAR, SAM.gov, USASpending, Senate lobbying, Census ACS, EPA ECHO, OSHA, ICIC Offshore Leaks, FDIC BankFind, ProPublica 990, OFAC SDN |
| Phase 3 | 3 collectors | STIX/TAXII threat intel, malware analysis |
| Phase 4 | 1 collector | Social media |

Each collector inherits from `BaseCollector` which provides:
- Standardized `execute()` interface returning `collection_result` with hash, confidence, metadata
- Rate limiting (configurable delay, default 1.0s)
- Retry logic (default 3 retries)
- Confidence scoring via weighted factor averaging
- Session tracking via MD5 hash of timestamp + object ID

### Stage 2: Normalization

- Entity name normalization: lowercase, remove punctuation except periods
- CSV-based record loading with standard field mapping
- Data hashing via MD5 for deduplication within sources
- Template-driven schema documentation (OpenPlanter wiki template.md)

### Stage 3: Entity Resolution

The `EntityResolverCollector` implements fuzzy matching between two datasets:

**Algorithm:** Python `difflib.SequenceMatcher` with configurable threshold (default 0.80)

**Process:**
1. Load Dataset A and Dataset B as CSV
2. Normalize entity names from both datasets
3. For each entity in A, find best match in B using SequenceMatcher
4. If similarity >= threshold, record as evidence chain with confidence score
5. Return list of evidence chains linking matched entities

**Key design decisions:**
- Standard library only (no pandas, no rapidfuzz) — reduces dependency footprint
- Blocking keys not yet implemented — brute-force O(n×m) matching
- No transitive resolution — each match is independent
- Confidence derived directly from SequenceMatcher ratio

**Use cases:**
- Campaign finance donors vs corporate registrants (find shell companies)
- Government contract vendors vs employer records in campaign donations
- OFAC sanctions list vs corporate registries

### Stage 4: Graph Construction

- Wiki graph system in `OpenPlanter/agent/wiki_graph.py`
- Nodes = entities (people, organizations, events)
- Edges = relationships (donor-to-candidate, vendor-to-contract, entity-to-sanctions-list)
- Evidence chains from Stage 3 become graph edges with confidence metadata
- Graph stored as markdown wiki pages with cross-references

## External Architecture References

### 300+ Source OSINT Platform (Simeon Garratt)
- Graph-based entity resolution at scale
- Investigator privacy as architectural constraint
- Architecture decisions documented for reproducibility
- Source: simeongarratt.com/blog/osint-investigation-tools

### MERAI — Massive Entity Resolution using AI (arXiv:2508.03767)
- Enterprise-scale entity resolution pipeline
- Addresses record deduplication and linkage in high-volume datasets
- Relevant for scaling OpenPlanter's current O(n×m) approach

### LLM-based Dual-Retrieval Architecture (Justin Lin)
- Combines vector retrieval with knowledge graph retrieval
- Graph-cleanup stage for identity ambiguity resolution
- Consent-based framework for OSINT data handling

### CEUR-WS OSINT Digital Asset Discovery (Vol. 4180)
- Heterogeneous OSINT data (structured, semi-structured, unstructured)
- Gradient Boosted Decision Trees for mixed-type feature processing
- Focus on automated asset discovery and risk assessment

## Gaps & Open Questions

1. **Blocking strategy** — Current brute-force matching doesn't scale beyond ~10K records per dataset. Need phonetic blocking (Soundex, Metaphone) or n-gram blocking.

2. **Transitive resolution** — If A matches B and B matches C, A should match C. Current implementation doesn't propagate matches.

3. **Evaluation metrics** — No precision/recall measured for entity resolution. Need ground truth datasets to evaluate threshold tuning.

4. **Real-time pipeline** — Current collectors are batch-mode. Streaming collection with incremental entity resolution is an open architectural question.

5. **Schema evolution** — Source APIs change (FEC, SAM.gov). Pipeline lacks schema drift detection.

6. **Graph storage** — Markdown wiki pages work for small investigations but don't support graph queries. Consider Neo4j or NetworkX for larger investigations.

## Cross-Domain Connections

- **Entity resolution** → links to entity-resolution.md for theoretical background
- **Privacy & cryptography** → metadata-resistant collection methods relate to privacy-and-cryptography.md
- **Grid edge AI** → anomaly detection on graph data could use techniques from grid-edge-ai.md
- **Intelligence operations** → ACH framework from intelligence-operations-history.md provides competing hypothesis analysis

## References

- `/a0/usr/workdir/phase2_collectors/entity_resolver.py` — implementation
- `/a0/usr/workdir/phase2_collectors/base_collector.py` — base class
- `/a0/usr/workdir/OpenPlanter/wiki/` — 12+ documented data sources
- arXiv:2508.03767 — MERAI entity resolution paper
- CEUR-WS Vol. 4180 — OSINT digital asset discovery
