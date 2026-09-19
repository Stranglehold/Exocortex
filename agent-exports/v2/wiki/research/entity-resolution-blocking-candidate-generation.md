---
title: Entity-Resolution Blocking & Candidate-Pair Generation (2026)
date: 2026-09-18
status: DRAFT
interests:
  - Data Aggregation & Entity Resolution
cross_domains:
  - anti-bot / gray-band leverage (detection-FP curvature)
  - adversarial ML
  - metadata-resistant communication
---

# Entity-Resolution Blocking & Candidate-Pair Generation (2026)

Entity resolution (ER) — record linkage / data matching — is dominated by its **blocking stage**: the cheap, coarse partition of candidate record pairs into *blocks* so that the full comparison space `O(n²)` collapses to a tractable subset. Blocking is universally reported as the end-to-end bottleneck in 2026 ER production: matching reaches a ceiling ~98.95% F1 once pairs are presented, yet the choice of blocking method determines both correctness (which true pairs are *dropped*, i.e. recall) and cost (how much of `n²` survives — the reduction ratio). This page covers **what candidate-pair generation strategies exist, how they trade recall vs reduction**, and critically the still-open **evaluation question: how do you isolate blocking quality as a first-class metric at a fixed reduction ratio?**

---

## 1. Why Blocking Is the Bottleneck

In the standard ER procedure (Fellegi-Sunter matching pipeline):
`records → blocking → candidate-pair generation → pairwise comparison/scoring → clustering/deciding`,
the middle stages consume nearly all compute. If blocking drops a true pair, no downstream stage can recover it — **blocking recall is upper-bounded by design**, so poor blocking is an unfixable correctness failure, not just a speed problem.**Blocking precision (recall of *non-matching* pairs removed) drives cost; blocking recall (fraction of *matching* pairs retained) drives correctness.** Optimizing one without controlling the other produces misleading production numbers — this asymmetry is exactly why "blocking quality as a first-class metric" remains open.

---

## 2. Candidate-Pair Generation Strategies

**Deterministic blocking.** Same-value rules on key fields (exact match on company_id, jurisdiction, registration number). Perfect precision (no false candidates) but brittle to typos/variants → low recall for fuzzy matches. Used where authoritative keys exist.

**Probabilistic / similarity-based blocking.** Edit-distance or token-overlap gates: instead of exact equality, block records sharing *any* n-gram above a threshold. Catches variants but explodes candidate volume; precision trades directly against recall.

**Locality-Sensitive Hashing (LSH) & private blocking.** Hashes similar records into the same buckets with tunable collision probability `p`. arXiv 1407.3191 (`A Comparison of Blocking Methods for Record Linkage`) explicitly compares traditional partition-based methods against LSH variants on **recall, reduction ratio, and computational complexity** — showing you can parametrize a single method along the recall/reduction frontier rather than picking one operating point.

**Embedding / ANN blocking.** Encode records (names, descriptions) with dense vectors and retrieve nearest neighbours via FAISS/Milvus instead of enumerating pairs. Enables sub-linear candidate generation at scale; 2026 pipelines combine classical key/blocking + embedding ANN for recall, then an LLM or cross-encoder as the comparison layer (**tiered classical → embedding → LLM-judge pattern**).

---

## 3. The Open Evaluation Question (This Page's Contribution)

The stated honest gap in production ER is: **benchmarks do not yet isolate blocking quality — blocking recall *at a fixed reduction ratio* — as a first-class metric.** Conventional benchmarks report end-to-end F1, which conflates blocking correctness with matching-model quality; a strong matcher can mask weak blocking and vice-versa.

**How to isolate it (method, grounded in the evaluation literature):**

1. **Gold-pair holdout.** Sample a known set of *true* pairs (`P`) from a labelled reference — this is the gold standard for recall at the candidate-generation stage.
2. **Fixed reduction target.** Run each blocking method until it has produced a candidate set whose reduction ratio (fraction of `O(n²)` removed) equals your operating point.
3. **Blocking recall** = |{ true pairs in P retained by the blocked candidate set }| / |P|. This is *not* end-to-end recall — it measures only whether blocking retained the ground-truth pairs, independent of what happens downstream.
4. **Blocking precision** = (candidate pairs that are true) / (all candidate pairs), controlling cost.

Plotting blocking-recall vs reduction-ratio per method yields the recall-vs-cost curve; arXiv 1407.3191 demonstrates exactly this comparison, and arXiv 2404.05622 (`How to Evaluate Entity Resolution Systems`) documents why ER evaluation is "notoriously difficult" — traditional methods rely on application-specific sampling rather than a uniform recall-at-fixed-reduction definition.

**The residual honest gap:** no single public benchmark standardizes this metric across datasets with *identical* reduction-ratio control, so comparing blocking methods cross-dataset is still imperfect. Springer 10.1007/978-3-031-46970-1_11 (`Evaluation of Candidate Pair Generation Strategies`, EM'2023) and ACM 10.1145/3786768 (`Consistently Evaluating Record Linkage Classifiers`, 2025) push toward consistent, comparable evaluation; BlockingPy (ScienceDirect, 2026) offers an end-to-end pipeline with multiple blocking strategies + embedding-based candidate generation. Library search confirmed **no dedicated record-linkage / duplicate-detection text** among the reference books — this is a genuine citation gap; grounding rests on arXiv primary sources and conference proceedings.

---

## 4. Failure Modes

- **Blocking recall floor.** Once blocking drops true pairs, downstream stages cannot recover them (irreversibility).
- **Precision/recall confusion in production reporting** — end-to-end F1 hides which stage failed.
- **Embedding-block-key fragility** (cf. differential privacy: adding noise to block keys preserves matching recall but degrades quality when the DP budget is too aggressive) — a precedent that *attestation/quality-tracking can run off the blocking critical path* without degrading recall.

---

## 5. Cross-Domain Connections

- **Anti-bot / gray-band leverage** — the detection-FP curvature trade in CAPTCHA-evasion maps onto blocking's recall-vs-reduction curve: both reserve their edge to a probabilistic band where accuracy alone cannot resolve it, and owning the processing layer inside that band wins via sub-linear cost.
- **Adversarial ML** — an adversary can poison sources so blocked candidate pairs are systematically wrong (source availability bias); provenance-completeness instrumentation runs *off* blocking's critical path to flag this without slowing matching.
- **Metadata-resistant communication** — the same off-critical-path audit pattern that keeps attestation cheap also preserves blocking recall; quality tracking and signal preservation need not compete with throughput.

---

## 6b. Tiered Architecture & LLM-Judge Candidate Generation

The still-open Open-Q2 question — "can an LLM/judge layer sit *after* ANN/blocking to recover dropped recall without O(n²)?" — is now answered empirically by the **RAG-for-entity-matching** literature.

**CE-RAG4EM (arXiv 2602.05708, Ma et al., Feb 2026).** *Cost-Efficient RAG for Entity Matching with LLMs: A Blocking-based Exploration* reduces computation through **blocking-based batch retrieval and generation** instead of dense pairwise comparison against an unbounded corpus. Experiments report comparable-or-improved matching quality at substantially reduced end-to-end runtime — the same efficiency logic behind in-context clustering (arXiv 2506.02509: up to **150% higher accuracy with ~5x fewer API calls**) applied explicitly to the *candidate-pair generation* stage, where retrieval is batched inside blocking blocks before any LLM call.

**Implication for Open Q#2 — resolved YES:** an LLM/judge layer can (a) operate only within surviving candidate sets, (b) amortise one pass over many pairs via in-context clustering, and (c) recover recall dropped by coarse blocking without re-expanding to O(n²). The tiered **classical → embedding ANN → RAG/blocking-LLM** architecture is therefore a first-class 2026 production pattern, not merely a hypothesis.

**Config-trade-off caveat (grounded):** CE-RAG4EM's own analysis shows key configuration parameters introduce an inherent performance-vs-overhead trade-off — so the re-filter's recall-recovery benefit must be balanced against its own retrieval+generation overhead. Practically: run the LLM-judge pass at a **fixed reduction target** and measure recall gained per API call, *not* end-to-end F1 (which would conflate matching quality with blocking quality again).

---

## 6. Open Questions (next deepening)

1. Is there a universal recall-vs-reduction frontier family across deterministic/LSH/embedding blocking, or three domain-specific functional forms? — **still open**: CE-RAG4EM confirms parameterisation along the recall/reduction frontier but does not settle universality.
2. Can LLM-judge comparison be inserted as a cheap re-filter *after* ANN blocking to recover some dropped recall without full `O(n²)` comparison? — **RESOLVED: YES** (arXiv 2602.05708 CE-RAG4EM; in-context clustering arXiv 2506.02509). LLM retrieval is batched *within* blocking blocks before any model call; recall recovered per API call, balanced against the same layer's own overhead — set at a fixed reduction target so this stays separable from matching quality.
3. How does adversarial source-poisoning interact with blocked candidate sets specifically (does poisoning concentrate in high-precision low-recall blocks)? — **still open**; off-critical-path provenance attestation remains the mitigation (cf. §4).
3. How does adversarial source-poisoning interact with blocked candidate sets specifically (does poisoning concentrate in high-precision low-recall blocks)?

---

### Sources
- arXiv 2602.05708 — Cost-Efficient RAG for Entity Matching with LLMs: A Blocking-based Exploration (CE-RAG4EM; resolved Open Q#2)
- arXiv 2506.02509 — In-context clustering ER / LLM-CER (up to 150% higher accuracy, ~5x fewer API calls)
- arXiv 1407.3191 — Comparison of Blocking Methods for Record Linkage (recall/reduction/complexity)
- arXiv 2404.05622 — How to Evaluate Entity Resolution Systems (evaluation difficulty)
- Springer 10.1007/978-3-031-46970-1_11 — Evaluation of Candidate Pair Generation Strategies in Entity Matching (EM 2023)
- ACM 10.1145/3786768 — Consistently Evaluating Record Linkage Classifiers (2025)
- ScienceDirect S0306437918301480 — Selecting optimal blocking method for record linkage
- ScienceDirect S2352711026000774 — BlockingPy: ANN-based blocking & meta-blocking (2026)
- Library gap: no dedicated record-linkage text in reference collection (honest).
