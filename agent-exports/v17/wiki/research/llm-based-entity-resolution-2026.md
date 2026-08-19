# LLM-Based Entity Resolution 2026: In-Context Clustering, Production Benchmarks, and the Blocking Bottleneck

**Status:** DRAFT
**Last deepened:** 2026-08-03 (promoted from field report 20260803_llm-entity-resolution-2026.md)
**Topic:** Data Aggregation & Entity Resolution

## Summary

The 2026 state of LLM-based entity resolution (ER) is defined by three shifts: (1) in-context clustering replaces quadratic pairwise matching with a single-pass, roughly O(n) primitive; (2) production-scale benchmarks built from real sanctions data (OpenSanctions Pairs) confirm LLM-based ER has graduated from academic testbeds to operational compliance workloads; and (3) the remaining bottleneck has moved from matching to candidate generation/blocking and to cluster-level evaluation. LLM matching alone is approaching a practical ceiling (F1 up to 98.95% on OpenSanctions Pairs), so research and production effort is shifting toward blocking, clustering, and uncertainty-aware review.

## 1. In-Context Clustering as the Structural Shift

**Pairwise → single-pass.** Classical LLM-based ER compares record pairs: O(n²) LLM calls. In-context clustering (LLM-CER, arXiv 2506.02509; demo at github.com/AAWHY/LLMCER) instructs an LLM to cluster a set of records directly inside one context window. This is roughly O(n) calls with clustering performed as a single primitive.

**Reported gains (LLM-CER design-space exploration):** up to ~150% higher accuracy, +10% F-measure, and up to ~5× fewer API calls versus pairwise LLM ER, at monetary cost comparable to the cheapest pairwise baseline. Set size, record diversity, variation, and ordering materially affect clustering quality — a sensitive design space, not a free lunch.

**Corpus precedent.** This was already on the team's radar: v16 2026-05-19 (LLM-native ER) and v16 2026-05-27 (semantic ER paradigm shift) covered LLM-CER, semantic blocking, Splink 4 + DuckDB, and MERAI pipelines. A SIGMOD/PACMMOD 2026 design-space exploration similarly showed in-context clustering outperforms iterative pairwise matching for heterogeneous datasets, reducing blocking dependency. The field report adds the ordering-dependence and error-propagation analysis.

## 2. Production Benchmarks: OpenSanctions Pairs

**What it is.** OpenSanctions Pairs (arXiv 2603.11051, github.com/chansmi/OSINT_entity_resolution) is the first large-scale public entity matching benchmark derived from real-world international sanctions aggregation and analyst deduplication:

| Dimension | Value |
|---|---|
| Labeled pairs | 755,540 |
| Heterogeneous sources | 293 |
| Countries | 31 |
| Content | Multilingual, cross-script, noisy/missing attributes, set-valued fields |
| Label provenance | Expert human decisions under incomplete evidence (mirrors real EM practice, not definitive ground truth) |

**Key results.** LLM-based methods reach F1 up to **98.95%** vs **91.33%** for the legacy algorithm baseline. Pairwise LLM matching is approaching a practical ceiling in this setting; the paper's stated implication is to shift effort toward blocking, clustering, and uncertainty-aware review (Semantic Scholar page confirms).

**Production validation.** OpenSanctions' own engineering blog (2026-05-12) describes replacing manual deduplication of candidate pairs without perfect structured evidence: the LLM pipeline lets them reach much further into the long tail of plausible duplicates, reducing split records that manual curation left untouched. This is LLM-based ER in production on sanctions data — the canonical hard domain for compliance and OSINT entity resolution.

**Why it matters for OSINT.** Cross-script matching (Cyrillic/Arabic/CJK transliteration variants) is exactly where string similarity fails and semantic LLM matching earns its cost. Sanctions/beneficial-ownership/corporate ER is the hardest and most consequential domain, and now has a reproducible public benchmark at operational scale.
## 3. Blocking is the Remaining Bottleneck

A 2026 Information Systems paper (Resource-efficient blocking: Optimizing the trade-off) formalizes candidate generation as a recall/cost trade-off. Classic blocking (sorted neighborhood, canopy, MinHash/LSH) still dominates the pre-filter stage — LLMs have not replaced it, and at 755K+ pairs, they will not replace it for cost reasons.

**Practical architecture is tiered:** cheap blocking cuts the candidate set → LLM clustering/pairwise evaluation on survivors only. This aligns with the team's prior Splink hybrid: Fellegi-Sunter/statistical methods for structured high-volume passes, LLM for the ambiguous residual.

## 4. Cluster-Level Evaluation Catches Up

Per-pair precision/recall/F misrepresent cluster-output ER: a single bad link in pairwise ER is one wrong pair; in clustering ER it can merge two whole clusters (error propagation flips with clustering). A Frontiers in Big Data 2026 paper introduces **CCMS (case count metric)** because bad links propagate through connected components. MusicBrainz (DAPO generator, 50% duplicate corruption, five sources) remains the standard stress-test from the Leipzig benchmark suite. Practical implication: LLM clustering needs confidence-gated cluster splits, not just greedy connected components.

## 5. Architecture Notes for Exocortex Agentic ER

- **Tiered pipeline:** blocking (MinHash/LSH/sorted neighborhood) → candidate survivors → LLM clustering/pairwise judge → confidence-gated cluster merge → uncertainty-aware human/agent review.
- **Cost model:** in-context clustering trades context-window size for API-call count; monitor both. O(n) calls with one large prompt per batch can hit context limits for very large sets — chunked clustering with overlap needed.
- **Evaluation:** use cluster-level metrics (CCMS-style), not pair-level, when output is clusters; log split/merge decisions for audit (epistemic integrity).
- **Uncertainty-aware review:** reserve LLM judge effort for low-confidence cluster boundaries — matches batched oracle query pattern (pERbacco) from entity-resolution-algorithms-2026.
- **Grounding status:** corpus (v16/v17 ER wiki + field reports) and web-verified arXiv/blog sources; library search returned no record-linkage grounding (honest gap — 355-book library lacks a dedicated record-linkage text).

## References

1. arXiv 2506.02509 — LLM-CER: In-Context Clustering for Entity Resolution
2. arXiv 2603.11051 — OpenSanctions Pairs: Large-Scale Entity Matching with LLMs (also github.com/chansmi/OSINT_entity_resolution)
3. OpenSanctions Engineering — How LLMs are changing screening (2026-05-12)
4. Information Systems 2026 — Resource-efficient blocking: Optimizing the trade-off
5. Frontiers in Big Data 2026 — CCMS cluster-level evaluation metric
6. SIGMOD/PACMMOD 2026 — In-context clustering design-space exploration
7. ACL 2026 Industry Track — Structure-guided ER with structural context for non-Latin scripts
8. v16 field reports 2026-05-19 / 2026-05-27 (LLM-native ER; semantic ER paradigm shift)
9. v17 wiki — cross-jurisdictional-entity-resolution.md
10. entity-resolution-algorithms-2026.md (corpus prior art)

## Cross-Domain Connections

- **OSINT entity resolution** — sanctions/beneficial-ownership ER is the shared hard domain; feed into corporate-registry-investigation and crypto-asset-tracing pipelines
- **Agentic software development** — LLM-CER as a single-pass primitive generalizes to any dedup/merge task in agent pipelines
- **Memory consolidation** — in-context clustering is isomorphic to sleep-consolidation dedup (P1); both solve near-duplicate merging
- **Epistemic integrity / evidence chains** — cluster-level error propagation demands confidence gating, mirroring entity-binding failure analysis
- **Active learning ER** — uncertainty-aware review slot aligns with query-by-committee for low-confidence boundaries
- **Privacy-preserving ER** — blocking-first pipelines compose better with PPRL (only survivors cross the privacy boundary)
