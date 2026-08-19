# Entity Resolution Blocking & Candidate Generation: The Persistent Bottleneck

**Status:** STABLE
**Last deepened:** 2026-08-12 (deepened BUILD cycle; created from least-recently-explored interest Data Aggregation & Entity Resolution)
**Topic:** Data Aggregation & Entity Resolution

## Summary

Entity blocking (a.k.a. candidate generation or indexing) is the pre-filter stage of entity resolution (ER) that selects a small set of record pairs for expensive matching. Without blocking, pairwise comparison is O(n²); with blocking, only within-block pairs reach the matcher. In 2026 the field consensus — grounded in the OpenSanctions Pairs production benchmark and LLM-based ER literature — is that LLM matching is approaching a practical ceiling (~98.95% F1) while blocking remains the bottleneck: a recall-vs-cost trade-off that determines end-to-end ER feasibility. The winning production pattern is tiered: cheap classical or embedding blocking cuts the candidate set, then an LLM judge/clustering step evaluates only survivors.

## 1. Why Blocking Is the Bottleneck

- **Pairwise matcher cost is quadratic.** For 100k records there are ~5×10⁹ pairs; LLM-judging even 1% is ~50M calls — impractical. Blocking exists to make the matcher feasible.
- **Blocking design decides recall and cost simultaneously.** Over-aggressive blocking (many small blocks) sacrifices recall; loose blocking preserves recall but lets quadratic cost back in.
- **Formalization.** A 2026 Information Systems paper (Resource-efficient blocking: Optimizing the trade-off) formalizes candidate generation as a recall/cost trade-off, confirming blocking — not semantic matching — as the 2026 ER bottleneck.
- **LLM-CER (arXiv 2506.02509)** in-context clustering partially side-steps the pairwise step, but remains sensitive to set size/diversity/ordering and still needs its own chunked blocking for very large sets.
- **OpenSanctions Pairs (arXiv 2603.11051)** — 755,540 labeled pairs, 293 sources, 31 countries — shows LLM matching at ceiling; the benchmark community and production screening effort have shifted to blocking, clustering, and uncertainty-aware review.

## 2. Classical Blocking Methods

| Method | Key idea | Strength | Weakness |
|---|---|---|---|
| Sorted neighborhood | Sort by key, slide window | Simple, deterministic | Key-choice quality; misses transposed/renamed values |
| Canopy clustering | Cheap distance (e.g., TF-IDF) to build overlapping canopies | Fast pre-filter | Canopy threshold tuning |
| MinHash / LSH | Token-set Jaccard approximation | Scales to billions of records | Signature/band tuning; recall cliffs |
| Blocking keys | Concatenated normalized attributes (name+postcode) | Transparent, auditable | Attribute errors kill matches; requires augmentation |

Corpus prior art (20260529 Splink hybrid) aligns: Fellegi-Sunter for structured high-volume, LLM for ambiguous residual — blocking still dominates the pre-filter stage.

## 3. 2026 Shift: Semantic Blocking

- **Embedding-based blocking.** Encode blocking keys into dense vectors and use vector search (e.g., Elasticsearch kNN) to retrieve candidates beyond string agreement. This is the canonical 2026 production reference pattern: "retrieve plausible candidates at scale, then use an LLM to judge whether those candidates truly refer to the same real-world entity" (Elasticsearch Labs).
- **UCL-Blocker** (Applied Soft Computing 2026): unsupervised contrastive learning with multi-source representation learning for entity blocking — no labeled data required for the pre-filter stage.
- **Semantic entity resolution** (Towards Data Science / Graphlet 2025-2026): language models applied to schema alignment, blocking, matching, and merging. The hidden assumption: the expensive LLM stage only sees candidate pairs.
- **Multi-agent RAG for ER** (Preprints.org 2025): agent-based pipeline separating blocking, candidate retrieval, and verification while maintaining a transparent reasoning trail.

## 4. Tiered Blocking → LLM Judge Architecture

1. **Cheap blocking:** deterministic keys + MinHash/LSH/embedding kNN over the full dataset.
2. **Candidate survivors:** only pairs/blocks that pass the pre-filter proceed. In privacy-preserving settings this is also the privacy boundary.
3. **Semantic matching:** LLM pairwise judge or in-context clustering (LLM-CER) runs only on survivors.
4. **Cluster-level refinement:** confidence-gated cluster splits (CCMS-style metrics, Frontiers 2026) prevent a single bad link from merging whole clusters.
5. **Uncertainty-aware review:** human/agent review reserved for low-confidence cluster boundaries.

Exocortex fit: this tiered design slots directly into the agentic ER pipeline ([[agentic-entity-resolution]]); budget allocation mirrors the pERbacco batched-queries pattern from [[entity-resolution-algorithms-2026]].

## 5. OSINT Applications

- **Sanctions screening:** OpenSanctions Pairs is literally the hard domain. Blocking design determines whether screening tens of millions of corporate records with local LLM judges is feasible.
- **Corporate registry pivots:** cross-jurisdictional ER needs semantic blocking to catch name/script variants (Cyrillic/Arabic/CJK transliteration) where string similarity fails ([[cross-jurisdictional-entity-resolution]]).
- **Beneficial ownership / shadow fleet:** vessel IMO + corporate-record matching benefits from temporal + semantic blocking; entity rotation (flag hops, reincorporation) defeats static blocking keys ([[temporal-entity-resolution]], [[marine-insurance-sanctions-enforcement]]).
- **Privacy-preserving ER:** block-then-match means only candidates cross the PPRL boundary — directly composes with [[privacy-preserving-entity-resolution-osint]].

## 6. Verification Status / Open Questions

- Grounded corpus-first: field report 20260803_llm-entity-resolution-2026.md, wiki llm-based-entity-resolution-2026.md, entity-resolution-pipeline-performance.md, plus memory fragments NU4AsiLcXU / 52c8rB3oS2 / 0W39G2wiWN.
- Library gap (honest): the 355-book library lacks a dedicated record-linkage/duplicate-detection text; no citable book grounding found.
- Open question: benchmarks do not yet isolate blocking quality (blocking recall at fixed reduction ratio) as a first-class metric; CCMS-style cluster metrics partially cover this.
- Claim hygiene: the 98.95% F1 figure comes from the OpenSanctions Pairs paper/blog corpus; an earlier memory flagged an unverified cyclical "95%+" claim (memory tLhYamsyTc) — this page cites the paper-based figure, not the uncited blog claim.

## References

1. arXiv 2506.02509 — LLM-CER: In-Context Clustering for Entity Resolution
2. arXiv 2603.11051 — OpenSanctions Pairs: Large-Scale Entity Matching with LLMs
3. Information Systems 2026 — Resource-efficient blocking: Optimizing the trade-off
4. Applied Soft Computing 2026 — UCL-Blocker: Unsupervised contrastive learning for ER blocking
5. Elasticsearch Labs — Entity resolution: Match entities with LLMs & semantic search (2026)
6. Preprints.org 2025.2382 — Multi-Agent RAG Framework for Entity Resolution
7. Frontiers in Big Data 2026 — CCMS cluster-level evaluation metric
8. OpenSanctions Engineering — How LLMs are changing screening (2026-05-12)
9. Corpus: field report 20260803_llm-entity-resolution-2026.md
10. Corpus: wiki llm-based-entity-resolution-2026.md, entity-resolution-pipeline-performance.md, privacy-preserving-entity-resolution-osint.md, temporal-entity-resolution.md

## Cross-Domain Connections

- **LLM-based ER 2026** — blocking is the shared bottleneck that page identifies; this page deepens that thread.
- **Privacy-preserving ER** — blocking-first composes with PPRL: only candidate pairs cross the privacy boundary.
- **OSINT sanctions / beneficial ownership** — corporate-registry and crypto-asset-tracing pipelines depend on blocking-scale feasibility.
- **Entity resolution agent safety** — cluster-level error propagation parallels entity-binding failures; confidence gating aligns with entity-aware action gates.
- **Agentic self-learning** — in-context clustering is isomorphic to sleep-consolidation dedup; same near-duplicate merging problem.
- **Temporal ER** — entity rotation demands temporal+semantic blocking, not static keys.
- **Active learning ER** — uncertainty-aware review on low-confidence boundaries integrates with dedupe/AL strategies.
