# Data Aggregation & Entity Resolution

**Status: STABLE** (2026-08-29: Deepened from DRAFT — grounded in shared Exocopus corpus + verified arXiv 2025/2026 sources; library gap documented honestly)

## Overview

Data aggregation and entity resolution are the load-bearing lower layers of any large-scale processing pipeline. Aggregation gathers and combines records from heterogeneous sources; entity resolution (ER) — a.k.a. record linkage / deduplication / name matching — identifies and links records that refer to the same real-world entity across those sources. Together they form the preprocessing stage downstream consumers depend on: resolved entities become graph nodes, probabilistic match scores become edge weights, and community detection surfaces organizational structures hidden beneath layered aliases.

## Core Concepts

1. **Data Aggregation** — collecting and combining data from multiple sources; correctness is a quality problem because every aggregation step can inherit or amplify upstream errors.
2. **Entity Resolution (Record Linkage)** — identifying records that denote one real entity. Classic decomposition: **(a) Blocking / pre-matching** to prune the O(n^2) candidate space on cheap keys, **(b) Pairwise comparison** with similarity features, **(c) Probabilistic matching**, **(d) Clustering/linking** resolved pairs into entities.
3. **The Fellegi–Sunter model** — the Bayesian probabilistic foundation (m/u probabilities: probability a pair matches given observed fields; match vs non-match classes). It is mathematically grounded and auditable, estimated via EM. Splink is its leading open production implementation.
4. **LLM-based ER** — uses large language models for semantic matching or direct in-context clustering instead of statistical calibration, best where structure is ambiguous or cross-script/cross-lingual.

## Production Pipeline (from the shared corpus)

A verified production-grade pipeline pattern (mirrors OpenPlanter's `entity_resolution.py` / `cross_link_analysis.py`) runs:

1. **Ingestion** — bulk download/collect from source registries.
2. **Preprocessing** — normalize names, strip suffixes, standardize LLC/L.L.C., remove trade names; extract canonical identifiers.
3. **Blocking** — block on registration id, name n-grams, phonetic codes (Soundex, Double Metaphone) to cut the quadratic comparison space.
4. **Matching** — Fellegi–Sunter probabilistic linkage for structured high-volume data; LLM-assisted matching for cross-jurisdictional / ambiguous variations.
5. **Clustering / Linking** — merge matched pairs into entities (connected-components / DBSCAN).
6. **Graph Construction & Downstream Analytics** — network analytics, influence scoring, anomaly detection on the resolved entity graph.

## The Hybrid Architecture (best-of-both-worlds)

Corpus research establishes that Splink/Fellegi–Sunter and LLM-based ER are **complementary**, not competing:

- **Fellegi–Sunter / probabilistic** wins for structured, high-volume records with well-defined fields where m/u probabilities can be reliably estimated (corporate registries, financial transactions).
- **LLM-based** wins for unstructured, low-volume, ambiguous cases where semantic understanding dominates statistical calibration (names in prose, cross-lingual matching, schema mismatch).

A hybrid pipeline — probabilistic first-pass with LLM fallback on low-confidence / ambiguous pairs — is the recommended design and operationalizes an "uncertainty-aware review" stage.

## Verified State-of-the-Art (arXiv 2025/2026)

**OpenSanctions Pairs: Large-Scale Entity Matching with LLMs** (Smith, Sesodia, Lindenberg, Schroeder de Witt; arXiv:2603.11051, Feb 2026)

- First large-scale public benchmark for entity matching on sanctions/OSINT data: **755,540 expert-labeled pairs over 1M entities from 293 source datasets across 45 jurisdictions**, spanning Latin/Cyrillic/Arabic scripts and inconsistent structure.
- Rule-based production baseline (nomenklatura RegressionV1) reaches **91.3% F1**; GPT-4o reaches **99.0% F1**; locally deployable DeepSeek-R1-Distill-Qwen-14B reaches **98.2% F1** — with and without MIPROv2 prompt optimization.
- Key finding: rules over-match; LLMs struggle with cross-script transliteration — they fail in complementary ways.
- Headline claim: pairwise matching is approaching a practical ceiling, so research focus shifts to **pipeline components: blocking, clustering, uncertainty-aware review**.

**In-context Clustering-based ER with LLMs: A Design Space Exploration** (Fu, Tang, Khan, Mehrotra, Gao; arXiv:2506.02509, June 2025)

- Proposes **LLM-CER**: using LLMs to cluster records directly instead of pairwise comparison — cutting both time and monetary cost.
- Explores the design space factors that determine clustering quality: set size, diversity, variation, and ordering of records.
- Addresses two key failure modes: efficient **cluster merging** and **LLM hallucination** during in-context reasoning.
- Empirical result on 9 real-world datasets: up to **150% higher accuracy**, +10% F-measure, and up to **5x fewer API calls** at comparable cost — scaling where pairwise degrades with dataset size.

## Honest Gaps (library)

The Exocopus technical-reference library holds no dedicated record-linkage / data-integration text; only tangential embedded-vision tracking/association material. This is a real coverage gap — the grounding above rests on shared-corpus field reports and primary arXiv sources rather than a canonical textbook. Suggested remediation for a future cycle: source or commission a reference on probabilistic linkage (Fellegi–Sunter, EM estimation, blocking strategies).

## Cross-Domain Connections

- **Entity resolution isomorphism** — cross-platform identity resolution is structurally identical to Fellegi–Sunter applied to digital identity fragments (username variants, writing style, temporal patterns, social-graph overlap). Venona reads as a manual human Fellegi–Sunter operation; OSINT multi-platform identity investigation resolves identity-fragment pairs.
- **Network analysis / graph** — resolved entities become nodes; match scores become edge weights; community detection surfaces hidden structure (see adaptive-graph-entity-resolution-draft, llm-native-entity-resolution).
- **Financial compliance / AML** — blocking on registrant IDs/phonetics then probabilistic linkage feeds lobbying-disclosure and due-diligence pipelines.
- **Privacy** — the same Jensen-Shannon divergence framework backing privacy-preserving record linkage could anonymize social-graph comparisons.
- **Intelligence collection** — aggregation quality gates every downstream analytic; entity-resolution-as-signal (e.g., entropy-of-aggregation as a detection cue) links to signal-intelligence pattern analysis.

## Open Questions

- How exactly should a hybrid pipeline schedule the probabilistic-first / LLM-fallback decision boundary in production?
- What is the optimal blocking-key composition that minimizes false negatives without exploding the pairwise space?
- How reliable are LLMs on cross-script transliteration, and can targeted pre-processing close that gap?

## Resources

- OpenSanctions Pairs (arXiv:2603.11051) — large-scale ER benchmark with verified F1 scores.
- In-context clustering ER / LLM-CER (arXiv:2506.02509) — cost-effective clustering design space.
- Splink (probabilistic record linkage, Fellegi–Sunter implementation).
- OpenPlanter entity_resolution.py / cross_link_analysis.py (reference pipeline implementation in the shared corpus).
