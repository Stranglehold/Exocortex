# Entity Resolution Algorithms: Deterministic vs Probabilistic Matching, Fellegi-Sunter Model, Active Learning Approaches

**Status: STABLE**
**Created: 2026-06-08**
**Deepened: 2026-06-08**
**Domain: Data Aggregation & Entity Resolution**

Core algorithmic foundations for entity resolution (ER) — deterministic rule-based matching, the probabilistic Fellegi-Sunter (FS) model, active learning for scaling ER pipelines, and modern extensions including LLM-assisted matching.

---

## 1. Overview

Entity resolution (ER) is the task of determining when two records refer to the same real-world entity despite inconsistencies, missing data, and format variations. This is the algorithmic backbone of everything from cross-jurisdictional corporate registry linking to memory deduplication in AI agent systems. The three canonical approaches — deterministic matching, probabilistic FS, and active learning — are typically layered: deterministic blocking first reduces the comparison space, probabilistic scoring classifies pairs, and active learning targets ambiguous cases for human or LLM annotation.

## 2. Deterministic Matching

Deterministic techniques use explicit rules rather than statistical inference. The core operations:

- **Exact matching**: Records agree on all key fields (e.g., SSN + DOB). Fast but brittle.
- **Normalized matching**: Fields are standardized before comparison — collapsing "ACME Corp.", "Acme Corporation", "ACME CORP INC" into a canonical form via uppercase, punctuation stripping, abbreviation expansion.
- **Token-overlap matching**: Records are compared by Jaccard similarity or token-set overlap after splitting into word tokens — handles transpositions and partial abbreviations.
- **Phonetic matching**: Soundex, Double Metaphone, NYSIIS for name fields where spelling variation is expected but pronunciation is stable.
- **Blocking rules**: Records are partitioned into mutually exclusive blocks (by ZIP code, phonetic encoding, first-letter surname) and compared only within blocks, reducing O(N²) to O(BN²/B²) ≈ O(N²/B). Blocking error — cases where matches fall into different blocks and are lost — is the primary failure mode.

The OpenPlanter pipeline uses three cascaded deterministic indexes: exact normalized match → token-overlap match → aggressive normalized match (handles transpositions and extreme abbreviations). Deterministic methods are always the heavy lift before probabilistic or LLM scoring.

## 3. Probabilistic Matching: Fellegi-Sunter Model

The canonical probabilistic framework, proposed by Ivan Fellegi and Alan Sunter in 1969, treats record linkage as a statistical decision problem.

### Core Mathematics

For each candidate record pair, a **comparison vector** γ captures agreement/disagreement across fields (name, DOB, address, etc.). Two conditional probabilities define the model:

- **m-probability**: m(γ) = Pr(γ | match) — likelihood of this comparison pattern for true matches
- **u-probability**: u(γ) = Pr(γ | non-match) — likelihood for random non-matches

The **match weight** for a field is log₂(m/u). Fields that rarely agree by chance (e.g., date of birth) get high positive weights when they match; fields that often agree by chance (e.g., common first name) provide less evidence. The composite match score is the sum of field-level weights: Σ log₂(mᵢ/uᵢ).

### Decision Rule

A threshold classifies pairs:
- Score > upper threshold → match (auto-accept)
- Score < lower threshold → non-match (auto-reject)
- Between thresholds → clerical review (ambiguous)

Parameters (m, u, thresholds) are typically estimated via Expectation-Maximization (EM) on unlabeled data.

### Key Strengths

- **Explainability**: Every decision decomposes into per-field contributions — critical for auditable, high-stakes OSINT workflows
- **No labeled data required**: EM estimation works on unlabeled comparison vectors
- **Calibrated uncertainty**: Match scores are interpretable weights of evidence, not black-box probabilities

### Exocortex Mapping

The injection gate could maintain per-assertion m/u probabilities for confabulation likelihood; the supervisor loop could apply FS-like decision thresholds (WARN/SUMMARIZE/RESET tiers). Memory deduplication (sleep consolidation Phase 1) is entity resolution on memory entries — merging near-duplicate insights with FS scoring.


## 4. Active Learning Approaches

When labeled data is scarce, active learning selects which candidate pairs to label for maximum model improvement per annotation.

### Classical Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| Uncertainty Sampling | Select pairs with match probability closest to 0.5 — the model is most confused | Bootstrapping |
| Query by Committee | Select pairs with highest disagreement among an ensemble of matchers | Heterogeneous data |
| Expected Error Reduction | Select pairs whose labeling would most reduce model error on the entire dataset | Efficient budgets |
| Representative Sampling | Cluster unlabeled pairs, pick representatives from each cluster | Coverage |

### Modern Extensions

- **ALER (2026)**: Hybrid system using lightweight proxy models for candidate selection and deep models for final matching
- **ALLabel (2025)**: Three-stage active learning for in-context LLM-based entity recognition
- **dedupe**: Python library with interactive active learning UI, widely used in investigative journalism (e.g., BuzzFeed, ICIJ)
- **Zingg**: ML-based active learning for enterprise-scale ER, handles blocking and matching jointly

## 5. Modern Extensions

### Bayesian Fellegi-Sunter
Extends FS with prior distributions over m/u parameters and blocking configurations. Propagates uncertainty through the full linkage pipeline rather than making hard decisions at each stage. The BRL (Bayesian Record Linkage) R package implements this, with scaling limitations.

### LLM-Assisted Entity Resolution
Uses LLMs (GPT-4o, Claude, etc.) for the ambiguous band — pairs that fall between the FS auto-accept and auto-reject thresholds. The LLM can reason about semantic similarity, cross-language name equivalence, and contextual clues that statistical methods miss. SELECTIVE callout (only for uncertain pairs) controls cost: 95% of pairs handled by FS at near-zero latency, 5% flagged for LLM at ~$0.001/pair. This mirrors the Exocortex injection gate: probabilistic triage before engaging expensive reasoning.

### Embedding-Based Blocking
Replaces rigid field-based blocking rules with dense vector representations (sentence transformers) for semantic blocking. Two records with different ZIP codes but semantically similar addresses can still fall into the same block, reducing blocking error. Cost: generating embeddings for all records.

## 6. Scaling & Blocking Strategies

Naïve all-pairs comparison is O(N²) — intractable beyond ~100K records. Strategies:

- **Standard blocking**: Partition by one or more perfect-match rules (e.g., ZIP code)
- **Sorted neighborhood**: Sort records by a key, slide a window — O(N log N) complexity but window size determines false negatives
- **Canopy clustering**: Cheap approximate distance metric creates overlapping canopies, then expensive comparison within canopies
- **LSH (Locality-Sensitive Hashing)**: Hash records so similar records collide with high probability — popular for minhash-based deduplication
- **Embedding-based**: Pre-compute sentence embeddings, use approximate nearest neighbor (ANN) indexes (Faiss, Annoy) for candidate retrieval

Blocking error — matches lost because they fall into different blocks — is the permanent, unrecoverable error. No current method fully propagates blocking uncertainty into the linkage stage.

## 7. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| Epistemic Integrity | FS provides a mathematical framework for calibrated uncertainty — m/u probabilities replace binary confidence in agent assertions |
| Memory Architecture (Sleep Consolidation) | Phase 1 deduplication is entity resolution on memory entries; active learning selects which insight pairs to merge |
| OSINT & Entity Resolution | Cross-jurisdictional data linking (corporate registries, campaign finance, property records) is the hardest case of FS |
| Knowledge Graph Construction | Resolved entities become nodes with source provenance; FS weights become edge confidence scores |
| Intelligence Failure Analysis | Entity resolution failures (false positives/negatives) map to intelligence failure patterns (mirror-imaging, anchoring) |
| SWARMFISH | Multi-agent committee deliberation for match consensus — each committee member applies a different ER strategy |
| Injection Gate | Selective LLM-assist for uncertain pairs mirrors probabilistic triage: cheap FS for most, expensive LLM for ambiguous |
| Context Pruner | Observation masking preserves FS evidence weights — failure modes remain traceable after pruning |

## 8. Key References

- Fellegi, I.P. & Sunter, A.B. (1969). A Theory for Record Linkage. *Journal of the American Statistical Association*
- Splink — UK government open-source FS implementation (SQL-backed, Python)
- (Almost) All of Entity Resolution (Science Advances, 2024) — comprehensive survey
- LLM-assisted record linkage for official statistics (Sage, 2026)
- MERAI enterprise deduplication pipeline (arXiv 2508.03767)
- ALER: Active Learning for Entity Resolution (2026)
- ALLabel: Active Learning for LLM-based Entity Recognition (2025)
- dedupe Python library — active learning ER for investigative journalism
- Zingg — ML-based entity resolution at enterprise scale
