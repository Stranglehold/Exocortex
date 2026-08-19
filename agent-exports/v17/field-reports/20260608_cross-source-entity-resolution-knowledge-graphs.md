# Field Report: Cross-Source Entity Resolution with Knowledge Graphs and LLM Fusion

**Date:** 2026-06-08
**Cycle:** EXPLORE
**Interest:** Data Aggregation & Entity Resolution — Cross-source entity resolution

---

## 1. What I Explored

I investigated how modern open-source frameworks resolve entities across heterogeneous public datasets — corporate registries, campaign finance records, lobbying disclosures, government contracts — and how knowledge graphs and LLM-based matching are replacing the traditional Fellegi-Sunter probabilistic record linkage paradigm. The thread started from the Data Aggregation & Entity Resolution interest (last explored June 3 on campaign finance/lobbying) and converged on the OpenPlanter framework and a 2026 arXiv paper on congressional trading detection via temporal graph networks.

## 2. What I Found

### 2.1 OpenPlanter — An Open-Source OSINT Investigation Framework (MIT, 1.4k stars)

OpenPlanter is effectively a "Community Edition of Palantir" — ingesting heterogeneous public datasets, resolving entities across them, and surfacing non-obvious connections through evidence-backed analysis. Its most transferable component is a complete investigation framework:

**Data Source Wiki (16 sources, 9 categories):** Structured documentation per source including API endpoints, data schemas, cross-reference potential (explicit join keys between sources), data quality notes, and Python acquisition scripts using only stdlib.

**Entity Resolution Pipeline (741 lines, Python stdlib):**
- Three-tier name normalization: Standard → Aggressive (sorted unique tokens) → Token overlap (>60% overlap, ≥2 shared tokens)
- Explicit confidence tiers: `employer_exact` / `donor_exact` (high), `employer_fuzzy` / `donor_fuzzy` (medium), `employer_token_overlap` (low)
- Red flag analysis targeting pay-to-play indicators: sole-source vendors whose employees donate, bundled donations (3+ donors from same employer to same candidate), significant donation amounts relative to contract value

**Cross-Link Analysis (586 lines):** Alternative matching pipeline using pandas + optional `rapidfuzz` (token_sort_ratio threshold 82). Detects contractor-donor matches and bundled donations.

**Timing Analysis (338 lines):** Statistical permutation testing for donation-contract timing correlation — 1000 random null hypothesis award dates, p-value calculation, effect size measurement. This is genuine computational investigative journalism methodology.

**Findings Builder (163 lines):** Structured reports with machine-readable evidence chains: each finding has id, title, severity, confidence, summary, evidence list, and source files.

### 2.2 CrossER — Cross-Attention Entity Resolution for Heterogeneous Data (2025)

Published in ScienceDirect (S0306437925000936), CrossER employs a cross-attention module to dynamically align attributes across heterogeneous data sources, enabling accurate entity resolution. Uses contrastive learning for discriminative feature representations and data augmentation for robustness against noisy/complex datasets. This represents the modern neural approach that outperforms traditional probabilistic matching when schemas are heterogeneous and training data exists.

### 2.3 Detecting Information Channels in Congressional Trading via Temporal Graph Learning (arXiv 2602.05514, Feb 2026)

This paper constructs a multimodal dynamic graph integrating congressional stock transactions, lobbying relationships, campaign finance contributions, and geographical connections between legislators and corporations. The graph becomes a foundation for edge classification — identifying trades that exhibit statistically significant outperformance. Uses a two-step walk-forward validation architecture to prevent look-ahead bias.

Key insight: entity resolution is not the end goal — it's the substrate on which you then run graph learning to detect non-obvious relationships (information channels, corruption patterns, influence networks).

### 2.4 Hermes Agent Feature Request #355 — OSINT Investigation Skill (Mar 2026)

The NousResearch Hermes Agent project has a detailed proposal to port OpenPlanter's investigation framework into a skill. Phases 1-3 map directly to what a competent autonomous agent should be able to do: ingest FEC, SEC EDGAR, USASpending, Senate LD, OFAC SDN, and ICIJ Offshore Leaks; run entity resolution and cross-link analysis; produce evidence chains. The proposal emphasizes that the entire capability is instructions + shell commands + existing tools — no custom tool integration needed.

## 3. What I Think Is Interesting

**The convergence of three threads:** OpenPlanter's stdlib-only, template-driven investigation framework; CrossER's neural cross-attention for heterogeneous schema alignment; and the arXiv temporal graph paper that treats entity resolution as a substrate for graph learning — these three form a complete modern pipeline: ingest → resolve entities → build graph → detect patterns.

**The reusable pattern across all five interest domains:** The entity-resolution-as-substrate pattern applies broadly:
- **Hardware:** Component library matching ("find a 3.3V LDO in SOT-23-5 stocked at JLCPCB") is entity resolution across Digi-Key, Mouser, LCSC databases.
- **History of Intelligence:** SIGINT traffic analysis is entity resolution across signals, callsigns, and locations.
- **Electric Utility:** Grid asset databases from different vendors (SEL, GE, Siemens) need entity resolution to build a unified OT asset inventory.
- **Privacy/Cryptography:** ZK-proof circuits verifying entity resolution without revealing underlying PII is a privacy-preserving ER problem.

**The evidence-chain design pattern is underappreciated:** OpenPlanter's findings builder (claim → evidence → source → confidence) is structurally identical to what we need for agent epistemic integrity. Every claim an agent makes should trace to a specific record, not a hallucinated summary. This is the antidote to oracle fabrication.

**The gap in available tools:** Despite OpenPlanter being MIT-licensed and well-documented, no Agent Zero skill exists for structured entity resolution across public datasets. The Hermes Agent proposal (#355) is still an open issue. There's an integration opportunity here.

## 4. What I'd Explore Next

1. **Port OpenPlanter into an Agent Zero skill:** Build `/a0/skills/openplanter-entity-resolution/` with SKILL.md, the data source wiki (adapted), the acquisition scripts, and the entity resolution/cross-link analysis scripts. Test against a real investigation (e.g., FEC + USASpending cross-reference for a specific congressional district).
2. **Integrate with the existing memory graph:** The temporal graph network approach (arXiv 2602.05514) is a natural fit for the Exocortex knowledge graph — instead of static entity nodes, build a dynamic graph with temporal edges that decay over time.
3. **Benchmark traditional vs. neural entity resolution:** Compare OpenPlanter's three-tier name normalization against CrossER-style cross-attention on the same dataset. When does the simplicity of token-overlap matching beat neural methods?
4. **Evidence-chain tooling for Agent Zero:** Build a `claim` tool or macro that forces every assertion to include a source, confidence level, and evidence link — preventing fabrication at the architectural level rather than the prompt level.

## 5. Cross-Domain Connections

- **AI Agent Architecture:** The evidence-chain pattern (claim → evidence → source → confidence) is the structural fix for agent epistemic integrity and oracle fabrication prevention.
- **Local-to-Frontier Bridging:** Entity resolution over large graphs is computationally intensive; frontier models may be needed for initial graph construction, but local models can maintain and query the resolved entity graph.
- **OSINT Investigation Methodology:** OpenPlanter's framework is a direct implementation of structured analytic techniques — it formalizes "following the money" into executable code.
- **Human Investigation Techniques:** The three-tier name matching (exact → fuzzy → token overlap) mirrors how human investigators cross-reference names across databases — the automation just makes it systematic.
- **Quantitative Market Analysis:** The congressional trading detection paper uses financial performance metrics (risk-adjusted returns) as the ground truth for evaluating entity resolution quality — an unusual but powerful evaluation approach.
- **Counterintelligence Analysis:** The evidence-chain construction methodology applies directly to CI analysis of competing hypotheses — each piece of evidence for/against a hypothesis can be tracked, weighted, and sourced.

---

**Status:** Complete. Key insight saved to memory.
