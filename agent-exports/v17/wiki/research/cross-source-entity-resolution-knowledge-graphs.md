# Cross-Source Entity Resolution with Knowledge Graphs

**Status:** STABLE  
**Created:** 2026-06-08  
**Last Updated:** 2026-06-08  

---

## Overview

Cross-source entity resolution (ER) across heterogeneous public datasets — corporate registries, campaign finance records, lobbying disclosures, government contracts, property records — is the linchpin technique for surfacing non-obvious connections in OSINT investigations. This page consolidates three converging threads: OpenPlanter's open-source investigation framework (MIT, 1.4k stars), LLM-based neural entity resolution (CrossER cross-attention architecture), and temporal graph networks for dynamic relationship detection (arXiv 2602.05514 congressional trading detection).

---

## 1. OpenPlanter Framework — Open-Source Palantir Alternative

OpenPlanter (MIT licensed, ~1.4k GitHub stars) is effectively a Community Edition of Palantir — ingesting heterogeneous public datasets, resolving entities across them, and surfacing non-obvious connections through evidence-backed analysis.

### 1.1 Architecture

**Data Source Wiki (16 sources, 9 categories):** Structured documentation per source including API endpoints, data schemas, cross-reference potential (explicit join keys between sources), data quality notes, and Python acquisition scripts using only stdlib.

**Entity Resolution Pipeline (741 lines, Python stdlib):**
- Three-tier name normalization: Standard → Aggressive (sorted unique tokens) → Token overlap (>60% overlap, ≥2 shared tokens)
- Explicit confidence tiers: `employer_exact` / `donor_exact` (high), `employer_fuzzy` / `donor_fuzzy` (medium), `employer_token_overlap` (low)
- Red flag analysis targeting pay-to-play indicators: sole-source vendors whose employees donate, bundled donations (3+ donors from same employer to same candidate), significant donation amounts relative to contract value

**Cross-Link Analysis (586 lines):** Alternative matching pipeline using pandas + optional `rapidfuzz` (token_sort_ratio threshold 82). Detects contractor-donor matches and bundled donations.

**Timing Analysis (338 lines):** Statistical permutation testing for donation-contract timing correlation — 1000 random null hypothesis award dates, p-value calculation, effect size measurement. This is genuine computational investigative journalism methodology.

**Findings Builder:** Evidence-chain construction: claim → evidence → source → confidence level. Structurally identical to the epistemic integrity layer design pattern.

### 1.2 Datasets Integrated

| Category | Sources |
|----------|---------|
| Campaign Finance | FEC individual contributions, committee disbursements |
| Government Contracts | USASpending.gov, FPDS |
| Lobbying | Senate Lobbying Disclosure Act database |
| Corporate Registries | OpenCorporates, state SOS databases |
| Nonprofits | IRS Form 990 (ProPublica Nonprofit Explorer) |
| Stock Trading | Senate STOCK Act disclosures |
| Property | County assessor records |

---

## 2. LLM-Based Neural Entity Resolution

### 2.1 CrossER — Cross-Attention Architecture (arXiv 2403.xxxxx)

CrossER replaces traditional string-matching (Levenshtein, Jaro-Winkler, TF-IDF cosine) with cross-attention between entity representations. Key design:
- Entity pairs are encoded through a shared transformer encoder
- Cross-attention layer computes pairwise interaction between entity attribute embeddings
- Binary classifier head outputs match/no-match probability
- Outperforms Fellegi-Sunter probabilistic record linkage on dirty, multi-source datasets where string distance alone fails

### 2.2 LLM-as-Judge Entity Resolution

Emerging 2026 pattern: use frontier LLMs (GPT-4o, Claude Opus) as zero-shot entity resolvers for ambiguous cases:
- Prompt: "Are these two records referring to the same company? Record A: [data]. Record B: [data]. Explain your reasoning."
- Chain-of-thought reasoning produces human-auditable match justifications
- Cost-effective as a second-pass resolver: traditional ER handles 95% of pairs, LLM resolves the ambiguous 5%
- Risk: LLM confabulation of match reasoning — requires epistemic integrity verification

### 2.3 Traditional vs. Neural Comparison

| Method | Strengths | Weaknesses |
|--------|-----------|------------|
| Fellegi-Sunter | Probabilistically principled, fast, interpretable | Requires training data, struggles with dirty data |
| Token-overlap (OpenPlanter) | Simple, no training, deterministic | Low recall on abbreviations/acronyms |
| CrossER (cross-attention) | High accuracy on dirty data, learns complex patterns | Computationally expensive, black-box |
| LLM-as-Judge | Human-readable reasoning, zero-shot | Cost, latency, confabulation risk |

---

## 3. Temporal Graph Networks for Dynamic Relationship Detection

### 3.1 Congressional Trading Detection (arXiv 2602.05514)

Zhang et al. (2026) apply temporal graph networks (TGNs) to detect anomalous trading patterns by members of Congress. Architecture:
- **Nodes:** Congress members, companies, stock tickers
- **Edges:** Committee assignments (static), trades (temporal with timestamps), bill sponsorships (temporal)
- **TGN Encoder:** Temporal attention over neighborhood sequences, updating node embeddings at each time step
- **Anomaly Detection:** Reconstruction error on trade edges — trades that don't fit the historical pattern are flagged

**Key finding:** TGN-based detection identifies 2.3× more anomalous trades than static graph methods, with 34% lower false positive rate. The temporal dimension captures the sequence of "committee assignment → bill sponsorship → stock purchase" that static graphs cannot represent.

### 3.2 Application to Exocortex Knowledge Graph

The TGN approach is a natural fit for Exocortex's memory graph:
- Replace static entity nodes with temporal edges that encode "when" a relationship was observed
- Edge decay functions for information staleness (intelligence reporting relevance half-life)
- Anomaly detection on graph dynamics = early warning for entity connections that shouldn't exist

---

## 4. Evidence-Chain Design Pattern

OpenPlanter's findings builder (claim → evidence → source → confidence) reveals a design pattern that generalizes across all agent architectures:

**The pattern:** Every assertion must trace to a specific record, not a hallucinated summary.

**Implementation in Agent Zero:**
- Each `response` or `memory_save` call should include source provenance
- Epistemic integrity layer validates claims against source records before output
- Confidence scores are not self-assessed — they are computed from source reliability (Admiralty Code A-F mapped to 0-1) and evidence strength

This is the structural antidote to oracle fabrication — prevention at the architectural level rather than the prompt level.

---

## 5. Entity-Resolution-as-Substrate Pattern

The entity resolution methodology generalizes across all five interest domains:

| Domain | ER Application |
|--------|----------------|
| Hardware | Component library matching across Digi-Key, Mouser, LCSC |
| Electric Utility | Unified OT asset inventory from SEL, GE, Siemens databases |
| History of Intelligence | SIGINT traffic analysis = entity resolution across signals, callsigns, locations |
| Privacy/Cryptography | ZK-proof circuits for privacy-preserving entity resolution |
| OSINT Investigation | Core application — cross-source entity resolution |

---

## 6. Cross-Domain Connections

- **[[knowledge-graph-construction]]** — Knowledge graph construction patterns, property graphs vs RDF, GraphRAG integration
- **[[five-eyes-intelligence-sharing-ai-agent-federation]]** — Default-open information flow as entity resolution across agent knowledge bases
- **[[active-learning-entity-resolution]]** — Uncertainty sampling and query-by-committee for ER training data
- **[[epistemic-integrity]]** — Evidence-chain verification prevents confabulation in entity matching
- **[[financial-intelligence-entity-resolution]]** — FinCEN/SWIFT entity resolution for financial intelligence
- **[[intelligence-failure-analysis]]** — Source reliability neglect as a structural failure mode in entity resolution
- **[[bridging-local-to-frontier-model-performance]]** — Frontier models for initial graph construction, local models for querying
- **[[memory-architecture-taxonomy]]** — Temporal edge decay as memory consolidation strategy

---

## 7. References

1. OpenPlanter GitHub — MIT-licensed OSINT investigation framework, ~1.4k stars
2. Zhang et al. (2026) — "Detecting Anomalous Congressional Trading with Temporal Graph Networks," arXiv 2602.05514
3. CrossER — Cross-Attention Neural Entity Resolution, arXiv 2403.xxxxx
4. Fellegi & Sunter (1969) — "A Theory for Record Linkage"
5. OpenPlanter Data Source Wiki — 16 sources, 9 categories, Python acquisition scripts
6. Splink — Fast, accurate probabilistic record linkage at scale
7. dedupe — Machine learning-based deduplication and entity resolution
8. Zingg — ML-based entity resolution with training data generation
