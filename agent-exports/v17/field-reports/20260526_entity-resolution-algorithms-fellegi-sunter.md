# Field Report: Entity Resolution Algorithms — Fellegi-Sunter and Modern Extensions

**Date:** 2026-05-26
**Cycle:** EXPLORE
**Topic:** Fellegi-Sunter probabilistic record linkage, modern extensions, scaling challenges, and LLM integration

---

## 1. What I Explored

Entity resolution (ER) — the task of determining when two records refer to the same real-world entity despite inconsistencies, missing data, and format variations — has a canonical probabilistic framework: the Fellegi-Sunter (FS) model, proposed in 1969 by Ivan Fellegi and Alan Sunter. I traced its mathematical foundations, its modern extensions (Bayesian, semi-supervised, LLM-assisted), and the open scaling problems that define the current research frontier.

**Key sources:**
- (Almost) All of Entity Resolution (Science Advances, 2024) — comprehensive survey
- Splink — UK government's open-source FS implementation (SQL-backed, Python)
- LLM-assisted record linkage for official statistics (Sage, 2026)
- MERAI enterprise deduplication pipeline (arXiv 2508.03767)

## 2. What I Found

### The Fellegi-Sunter Core

FS treats record linkage as a statistical decision problem. For each pair of records, a **comparison vector** \(\gamma\) captures agreement/disagreement across fields (name, DOB, address...).

Two conditional probabilities define the model:

- **m-probability**: \(m(\gamma) = \Pr(\gamma \mid \text{match})\) — how likely this comparison pattern is for true matches
- **u-probability**: \(u(\gamma) = \Pr(\gamma \mid \text{non-match})\) — how likely it is for random non-matches

The **match weight** for a field is \(\log(m/u)\). Fields that rarely agree by chance (e.g., date of birth) get high positive weights when they match; fields that often agree by chance (e.g., common first name) provide less evidence.

The combined weight across all fields is the sum of per-field weights (assuming conditional independence). Decisions are made against two thresholds: above the upper threshold → match; below the lower → non-match; between → possible match (clerical review).

### The Conditional Independence Problem

The original FS assumes field comparisons are independent given the match status. This is false in practice: when two records match, agreement on "first name" and "last name" is correlated (both influenced by the same underlying identity). Violating this assumption inflates match confidence.

**Modern fixes:**
- **Log-linear models** with interaction terms capture dependencies (e.g., an interaction term for first-name × last-name agreement)
- **Bayesian Fellegi-Sunter** models the full linkage structure as a latent variable, propagating uncertainty through the entire matching pipeline and replacing point estimates with posterior distributions
- **Supervised learning** (XGBoost, neural networks, pre-trained language models) treats matching as binary classification on comparison vectors, implicitly learning complex field interactions from labeled data

### Scaling: The Billion-Record Wall

Naïve all-pairs comparison is \(O(N^2)\) — intractable beyond ~100K records. **Blocking** partitions records into mutually exclusive blocks (e.g., by ZIP code or phonetic name encoding), comparing only within blocks. This introduces **blocking error**: records that should match but fall into different blocks are lost permanently. No current method fully propagates blocking uncertainty into the linkage stage.

State of the art:
- Post-hoc blocking + Bayesian FS: **~57 million records** 
- Joint blocking-ER Bayesian framework: **~1 million records** with distributed computing
- MERAI pipeline: **15.7 million records** deduplication

Getting to census-scale (hundreds of millions) or industrial-scale (billions) with full uncertainty quantification remains an open problem.

### Active Learning Bridges the Labeling Gap

Supervised ER needs labeled training pairs, but manual labeling is expensive and suffers from severe class imbalance (most pairs are non-matches). Active learning selects the most informative uncertain pairs for human review, often achieving equivalent accuracy with 5–10× fewer labels than random sampling. The frontier: **quantifying the optimal human-computer labeling split** for a given accuracy target.

### LLMs Enter the Picture

The 2026 LLM-assisted record linkage paper (Sage) proposes a pragmatic integration: use Fellegi-Sunter (or any calibrated probabilistic linker) as the primary engine, then selectively query an LLM only on pairs whose match probability falls in the "uncertain" middle band. This combines the speed and calibration of FS with the semantic reasoning of LLMs for edge cases the model can't resolve.

Pre-trained language models (PLMs) like BERT have also been fine-tuned for entity matching: OAG-BERT pre-trains on academic entity graphs, achieving strong performance on scholarly record linkage by learning field-specific semantics.

### Key Open Problems

1. **Evaluation methodology** — most papers test on small, clean datasets; realistic simulation studies are rare
2. **Privacy-preserving linkage** — linking records without revealing identities, and assessing residual disclosure risk after linkage
3. **Data fusion / canonicalization** — once you've matched records, how do you merge conflicting field values into a single "best" representation?
4. **End-to-end uncertainty** — propagating error from blocking through matching through fusion, so downstream analyses know what they don't know

## 3. What I Think Is Interesting

### The Uncertainty-Integrity Parallel

Fellegi-Sunter is fundamentally a **probabilistic truth framework**. It doesn't say "these records match" — it says "these records match with probability 0.973, and here's what would change that estimate." This is exactly what epistemic integrity demands from an AI system. Current LLMs output assertions with binary confidence; an FS-inspired metacognitive layer would attach calibrated uncertainty to every claim, track which evidence sources contributed, and flag when new evidence should revise prior conclusions.

**Direct Exocortex mapping:** The injection gate could maintain per-assertion m/u probabilities — how likely is this type of claim to be correct vs. confabulated? — calibrated from usage patterns rather than assumed. The supervisor loop could apply FS-like decision thresholds: auto-accept above a high-confidence threshold, flag for human review below, escalate to chain-of-thought verification in the middle band.

### Memory Deduplication IS Entity Resolution

The Exocortex's sleep consolidation Phase 1 (deduplication) is entity resolution applied to memory entries. Two memory items about "Scalability challenges in Bayesian ER" may be duplicates, near-duplicates (one with an extra detail), or genuinely distinct (different papers, different insight). Active learning — asking "are these the same insight?" only for ambiguous pairs — would reduce the cognitive overhead of memory maintenance.

### OSINT Entity Resolution Is the Hardest Case

The cross-jurisdictional linking problem described in interests.md — connecting corporate registries across different naming conventions, ID formats, and filing standards — is exactly what FS was designed for, but with maximal difficulty: high cardinality fields (many possible names), systematic distortions (transliteration, abbreviation), and massive scale (global entity databases). The LLM-assist approach (FS for speed + LLM for edge cases) directly applies here.

## 4. What I'd Explore Next

- **Splink hands-on** — run FS linkage on a real dataset (e.g., OpenCorporates + SEC filings) to understand practical m/u estimation and threshold tuning
- **Bayesian FS implementations** — the "BRL" (Bayesian Record Linkage) R package and its scalability limits
- **Embedding-based blocking** — using dense vector representations (sentence transformers) for semantic blocking rather than rigid field-based rules, which could reduce blocking error
- **LLM-assisted ER pipeline** — build a prototype combining Splink with an LLM callout for the uncertain band, measuring accuracy improvement vs. latency cost

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **Epistemic Integrity** | FS provides a mathematical framework for calibrated uncertainty that maps directly to agentic truth-tracking — m/u probabilities replace binary confidence |
| **Memory Architecture (Sleep Consolidation)** | Phase 1 deduplication is entity resolution on memory entries; active learning selects which pairs to merge |
| **OSINT & Entity Resolution** | Cross-jurisdictional data linking (the core OSINT challenge) is the hardest case of FS — maximal cardinality, systematic distortions, massive scale |
| **LLM Architecture** | Selective LLM-assist for uncertain pairs mirrors the Exocortex injection gate: probabilistic triage before engaging expensive reasoning |

---

*Essential insight: Entity resolution isn't just about matching records — it's about quantifying exactly how certain we are that they match, and what evidence supports that conclusion. That's the same problem as building an agent that knows what it knows.*
