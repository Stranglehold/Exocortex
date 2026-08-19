# Field Report: LLM-Assisted Record Linkage & Active Learning Extensions to Fellegi-Sunter
**Date:** 2026-05-26 | **Cycle:** EXPLORE | **Topic:** Data Aggregation & Entity Resolution

---

## 1. What I Explored

After the ICIJ methodology deep-dive (May 20), the open question was: *how are modern approaches — LLM embeddings, active learning, and budget-aware sampling — extending or replacing the classic Fellegi-Sunter probabilistic framework?* This report explores three emerging threads:

1. **LLM-assisted record linkage** — using language model embeddings for entity matching, particularly for official statistics
2. **BEACON budget-aware entity matching** — distribution-aware active learning for cross-domain entity resolution
3. **Practical convergence** — how tools like Splink, Zingg, and Senzing are incorporating these advances

---

## 2. What I Found

### 2.1 LLM-Assisted Record Linkage (Statistical Journal, Jan 2026)

A 2026 paper in the *Journal of Official Statistics* proposes augmenting the Fellegi-Sunter framework with LLM-encoded similarity features. The key insight:

- Traditional FS requires manual feature engineering (e.g., Jaro-Winkler, Soundex, token overlap). For unstructured or multilingual fields, these fail.
- LLMs (even small ones like RoBERTa or TinyLlama) encode semantic similarity that FS can't capture — e.g., "ACME Corp LLC" vs "Acme Corporation Ltd" resolve to semantic equivalence that edit-distance metrics miss.

**Architecture pattern:**
```
Original Records
    ↓
LLM Embedding → cosine similarity feature
    ↓
FS model uses LLM-cosine as one comparison feature alongside traditional ones
    ↓
Match probability (FS output)
```

The LLM weight is treated as an `m-probability` within FS, where the model learns how predictive the semantic similarity is for true matches. This is a *hybrid*, not a replacement — FS still provides the probabilistic framework, but LLM features make it robust to linguistic variation.

### 2.2 BEACON: Budget-Aware Entity Matching Across Domains (EDBT 2025/arXiv 2603.11391)

BEACON tackles the *cold-start, low-resource* problem: you want to match entities in a new domain (e.g., shipping registries) but have no labeled training data for that domain. Classic active learning picks in-domain examples to label; BEACON picks *out-of-domain* examples that are distributionally close.

**Key mechanism:** Embedding-space candidate ranking. BEACON computes pairwise match candidate embeddings (e.g., using sentence-transformers), then clusters them. It selects labeling candidates from the cluster centroids of source domains, weighted by estimated relevance to the target domain. This achieves 85-90% of fully-supervised performance with only 50-100 labeled examples.

**Cross-domain connection:** This is the same transfer-learning pattern used in OSINT entity resolution — you train on one jurisdiction's corporate records and transfer to another with different naming conventions (e.g., Delaware LLCs → Singaporean Pte. Ltd.).

### 2.3 Splink's Active Learning Integration Roadmap

Splink (the open-source FS implementation used by UK Government) is adding active learning directly to its pipeline:

- **Train-from-labelled-data mode:** Accepts human-labeled match/non-match pairs to learn m- and u-probabilities instead of pure unsupervised EM estimation
- **Interactive labelling workflow:** Splink can propose uncertain pairs for human review, then refit the model — this is active learning inside the FS framework
- **Implementation note:** Splink's SQL-backend architecture makes this feasible at scale (Spark/Flink backend for 100M+ records)

### 2.4 Observation Masking for Failure Preservation (NeurIPS 2025)

The JetBrains/TUM NeurIPS 2025 paper introduces *Observation Masking*, a technique that preserves evidence of missed matches (false negatives) rather than silently discarding them. The core insight:

> In standard ER pipelines, when two records fail to match (e.g., due to insufficient evidence), the evidence of their near-match is lost. The system continues as if they are unrelated.

Observation Masking retains a *masked observation*: "Records A and B had a 0.47 match probability — not linked, but this is a suspicious near-match." This maps directly to Jake's core epistemic integrity principle: *errors must be visible and auditable, not silently smoothed over.*

---

## 3. What I Think Is Interesting

### The FS Framework Is Not Being Replaced — It's Being Augmented

Every thread examined — LLM features, active learning, BEACON — adds capabilities *on top* of the Fellegi-Sunter probabilistic structure. The FS model is 55 years old (1969) but remains the backbone because:

1. **Interpretability:** Match probabilities are explainable ("the name field contributed +3.2 log-likelihood to this match") — critical for audit and legal admissibility
2. **Statistical rigor:** m/u probabilities have formal interpretations that embedding similarity scores lack
3. **Composability:** External features (LLM, embeddings, active learning) plug into the FS comparison vector naturally

### The Real Innovation Is Sample Efficiency

BEACON's insight — that embedding space structure can guide sample selection across domains — is generalizable beyond entity matching. Any classification task with a cold-start domain problem (OSINT pivot attribution, sanctions evasion detection, supply chain mapping) could use the same distribution-aware sampling.

### Failure Preservation Is a Neglected Dimension

Observation Masking is the first paper I've seen that treats false negatives as *data to be preserved* rather than *errors to be minimized*. This aligns with the epistemic integrity pattern running through Jake's entire architecture: the injection gate, the BST enrichment plan, the conviction tracker — all of which treat uncertainty and failure as signals, not noise.

---

## 4. What I'd Explore Next

1. **Observation Masking implementation** — could we add a "near-match trail" to the OpenPlanter pipeline that the field report already described? This would be a lightweight addition: any match probability between 0.3 and 0.7 gets logged as a suspicious-near-match for later human review.

2. **BEACON-style cross-jurisdiction transfer** — test whether a Splink model trained on Delaware companies transfers to Singapore Pte. Ltd. entities using embedding-space candidate ranking

3. **LLM-feature pipeline** — build a minimal demo that adds a `llm_cosine_similarity` feature column to Splink's comparison model and measure whether it reduces false negatives on multilingual company names

4. **Senzing principle convergence** — investigate whether Senzing's principle-based approach ("entity with two active addresses is suspicious") and Observation Masking ("0.47 match preserved as evidence") are solving the same problem from different directions

---

## 5. Cross-Domain Connections

| Connection | Domains | Insight |
|---|---|---|
| **Transfer learning pattern** | Entity Resolution → OSINT Investigation | BEACON's cross-domain active learning is the same problem as applying a corporate-entity resolver trained on SEC filings to shell companies in the Offshore Leaks database |
| **Failure preservation** | Entity Resolution → Exocortex Epistemic Integrity | Observation Masking's "preserve near-matches" is structurally identical to the injection gate's "preserve low-confidence outputs for review" — both treat uncertainty as signal |
| **FS augmentation** | Entity Resolution → AI Agent Architecture | The hybrid FS+LLM pattern (keeping the rigorous scaffold, adding a flexible feature) mirrors the Exocortex architecture pattern (deterministic BST scaffold + flexible LLM reasoning) |

---

*Sources: Statistical Journal paper (Jan 2026), BEACON paper (arXiv 2603.11391), Splink documentation, NeurIPS 2025 Observation Masking, ICIJ Offshore Leaks Database documentation.*
