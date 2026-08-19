# Data Quality as the Entity Resolution Bottleneck

**Status: STABLE**
**Topic Slug: data-quality-entity-resolution**
**Created: 2026-08-07**
**Interest Origin: interests.md → Data Aggregation & Entity Resolution (entity resolution algorithms, cross-jurisdictional data linking, data quality limitations)**
**Primary Sources:** shared corpus (memory_load 2026-05-20/26/29, 2026-07-06/14), [[entity-resolution-algorithms-2026]], [[entity-resolution-pipeline-performance]], [[data-lineage-provenance-entity-resolution]], [[llm-assisted-entity-resolution]], [[agentic-entity-resolution]], [[privacy-preserving-entity-resolution-osint]], web verification (arXiv 2506.02509, 2605.25814, 2607.27435; ACM Computing Surveys; MDPI Computers 14(12):525)

---

## Abstract

Data quality is the binding constraint on entity resolution (ER) in production: ER exists precisely because source data is dirty, and the character of the dirt — typographical error, structural heterogeneity, semantic ambiguity, staleness — determines which algorithm family will work. The 2026 lesson from the survey literature is sharp: **models that perform well on clean benchmark datasets systematically fail when exposed to noisy, heterogeneous real-world data**. The field has shifted from “better matchers” to *quality-aware pipelines*: standardization and error correction, LLM-based blocking/matching/clustering that tolerates dirt, and explicit audit of gold-standard quality. This page consolidates the data-quality layer that ER pages in this wiki treat piecemeal.

---

## 1. Why Data Quality Is the ER Bottleneck

- Entity resolution is “one of the most critical tasks for improving data quality” (ACM Computing Surveys, *An Overview of End-to-End Entity Resolution for Big Data*) — but it is also *itself* degraded by poor input quality. Dirty data is simultaneously the reason for ER and the main source of ER failure.
- The canonical dirty-data regimes align with the Deep-Learning ER survey taxonomy: **typographical errors**, **formatting variations**, and **semantic ambiguities**. Single-source/dirty ER (one messy dataset) is structurally different from multi-source heterogeneous ER (many clean-but-different schemas) and requires different designs (arXiv 2605.25814 works within the blocking-matching-clustering paradigm under dirty-record conditions).
- **Benchmark cleanliness gap:** heterogeneous-data evaluations find high-performing models trained on clean benchmarks fail to generalize to messy industrial data (*Heterogeneity in Entity Matching*, Information Systems, 2026). Any production ER evaluation that uses only clean benchmarks overstates deployable performance.

## 2. Error Taxonomy Relevant to ER

- **Syntactic:** typos, case/whitespace variants, transliteration differences, OCR noise. Handled by standardization/normalization plus edit-distance and embedding features.
- **Semantic:** aliases (“Bill” vs “William”), organization renames, abbreviation systems, and adversarial obfuscation — deliberately dirty records appear in OSINT datasets. LLMs are the 2026 tool of choice here.
- **Structural:** schema mismatch (same entity described by different column layouts), missing attributes, different ID formats, different filing standards — the cross-jurisdictional ER problem ([[cross-jurisdictional-entity-resolution]]).
- **Multiplicity/duplication:** the same entity repeated within one dataset; resolution must cluster, not just pair-match.
- **Temporal:** stale values (old address, former name). Requires time-aware matching and decay ([[temporal-entity-resolution]]).
- **Contradictory values:** two records, same entity, conflicting attributes; resolved by source-reliability weighting ([[data-lineage-provenance-entity-resolution]]).

## 3. Where Quality Gates Sit in the Pipeline

Standard production ER pipeline (corpus-grounded):
1. **Data profiling & source resolution** — decide which datasets cover the target; source discovery is structurally the same problem as ER (corpus memory 2026-05-29).
2. **Standardization / cleaning** — normalize names, addresses, dates; collapse format variants before matching.
3. **Blocking & candidate generation** — *the highest-leverage quality gate*: a bad blocking key is a recall ceiling no matcher can recover from ([[entity-resolution-pipeline-performance]]).
4. **Pairwise matching** — Fellegi-Sunter probabilistic scoring; the 2026 production standard is hybrid FS + LLM for semantic ambiguity (corpus memory 2026-07-14).
5. **Clustering / transitive closure** — propagate match decisions; threshold choice defines the precision-recall tradeoff.
6. **Verification / audit** — human-in-the-loop or LLM escalation (Agentic GraphRAG achieves 97.15% merge precision, arXiv 2605.18770).

## 4. Gold Standards, Benchmarks, and Evaluation Quality

- Accuracy claims are only as good as the gold standard: **benchmark label quality is itself a data-quality problem**; contaminated or synthetic labels propagate into inflated SOTA (ACL 2026 findings on error detection and quality control in benchmark construction).
- Dirty-ER evaluation stacks seen in the corpus/world: Magellan data, the 9 real-world entity-matching datasets used in the 2026 LLM clustering study (arXiv 2506.02509), and heterogeneous-data evaluations from the 2026 survey.
- Metrics: precision/recall/F-measure (pair-level and cluster-level), FP-measure, and — for LLM pipelines — API-cost metrics, since accuracy and spend are now jointly optimized.

## 5. LLM-Era Data-Quality Workflows (2026 SOTA)

- **In-context clustering-based ER with LLMs** (arXiv 2506.02509, 2025; nine real-world datasets): design-space exploration reports up to **150% higher accuracy**, **+10% F-measure**, and **up to 5× fewer API calls** than strong baselines at comparable monetary cost — accuracy and spend are now jointly optimized.
- **Agentic ER** (arXiv 2607.27435, vision 2026-07-29): proposes entity resolution as an agent task in which specialized agents collect evidence, correct data, match, and escalate; a multi-agent RAG instantiation reports 94.3% name-variation accuracy and 61% API-call reduction vs single-LLM baselines (MDPI Computers 14(12):525).
- **ChatMatcher** (2026): 7B-LLM end-to-end matching pipeline that treats ER as a data-cleaning/data-integration task (Information Systems, S0306437926000980).
- **Adaptive graph refinement + label propagation with LLMs** (arXiv 2605.25814): cost-effective dirty ER on single messy datasets — evidence the dirty-ER regime is an active research frontier, not a solved sidebar.
- **LLM error correction as preprocessing:** value normalization/correction before matching is standard, but each LLM-corrected value is a *synthetic fact* that needs provenance ([[data-lineage-provenance-entity-resolution]], [[entity-resolution-agent-safety]]).
- **Failure preservation:** summarize pipeline decisions and you smooth over false negatives; in Exocortex, observation masking beats summarization for ER failure preservation (corpus memory 2026-05-20).

## 6. OSINT Implications

- **Source resolution precedes entity resolution:** US public records span 50 states and 3,200+ counties with API-to-paper fragmentation; discovering the right source database is the same schema-mapping/confidence-scoring problem as resolving entities (corpus memory 2026-05-29; [[public-records-databases-osint]]).
- **Composite trust scoring is an open contribution gap:** no production system combines source reliability (Admiralty Code), provenance completeness (W3C PROV-O), match confidence (Fellegi-Sunter), and historical accuracy into one score (corpus memory 2026-07-06).
- **Adversarial dirt:** breach data, scanner logs, and AI-crawler-era scraped content introduce deliberately poisoned records (fake personas, planted aliases), so quality gates must assume malicious noise, not just accidental noise ([[data-breach-analysis-osint-identity-linkage]], [[web-scraping-data-acquisition-ai-era]]).

## 7. Cross-Domain Connections

1. **Knowledge-graph construction** — format-schema coupling mismatch causes catastrophic fact-coverage collapse (4/6 datasets below unconstrained baseline); retrieval can mask construction quality (direct-graph gap up to +47.6pp, p<0.0001) — the same masking trap applies to ER quality audits ([[knowledge-graph-construction-patterns]]).
2. **Privacy-preserving ER / PPRL** — DP requires “substantial perturbation → notable degradation of linkage quality”; Américas DataHub found data quality the PPRL2 bottleneck ([[privacy-preserving-entity-resolution-osint]]).
3. **Active learning** — gold-standard label quality is a data-quality problem; ALER/ALLabel cut ambiguous-match labeling cost ([[active-learning-entity-resolution]]).
4. **Agent safety** — 24-26% wrong-entity actions despite 0% wrong-tool show dirty entity indexes are an agent-risk issue ([[entity-resolution-agent-safety]]).
5. **Epistemic integrity** — ER errors as visible structural events vs buried probability scores maps to Exocortex error-comprehension architecture ([[epistemic-integrity]]).
6. **Temporal analytics** — stale-value detection gates time-varying ER ([[temporal-entity-resolution]]).
7. **LLM-assisted ER** — hybrid Fellegi-Sunter + LLM is the 2026 production standard ([[llm-assisted-entity-resolution]]).
8. **Agentic pipelines** — multi-agent RAG mirrors Exocortex subordinate-agent chains ([[agentic-entity-resolution]]).
9. **OSINT methodology** — ICIJ Panama Papers = manual Fellegi-Sunter at global scale with strict source-quality discipline ([[corporate-registry-investigation-osint]]).
10. **Self-improving agents** — memory dedup/consolidation is an ER problem inside the agent ([[memory-architecture-taxonomy]]).
11. **Financial intelligence** — data-quality limitations dominate EDGAR/revenue-concentration signals ([[revenue-concentration-analysis]]).
12. **Data lineage** — provenance completeness is one leg of composite trust scoring ([[data-lineage-provenance-entity-resolution]]).

## 8. Exocortex Integration

- Treat Exocortex memory consolidation (Phase 1 dedup) as a data-quality pipeline: blocking on stable keys, LLM verification of near-duplicates, and *preservation* of uncertain matches instead of silent merges.
- The composite confidence/trust-score gap (Section 6) is the clearest original contribution: extend the lineage-provenance page framework into a production trust score combining source reliability, provenance completeness, match confidence, and historical accuracy.
- Quality gates for vector/memory retrieval: retrieval masking of construction quality is analogous to LLM confabulation going undetected (Section 7.1); add explicit provenance checks to retrieval results.

---

## References

1. ACM Computing Surveys — *An Overview of End-to-End Entity Resolution for Big Data* (doi:10.1145/3418896).
2. *Heterogeneity in Entity Matching: A Survey and Experimental Analysis* (2026), Information Systems (S0169023X26000224).
3. *A Comprehensive Survey of Deep Learning for Entity Resolution*, ACM Computing Surveys (doi:10.1145/3828660).
4. *In-context Clustering-based Entity Resolution with Large Language Models: A Design Space Exploration*, arXiv:2506.02509 — up to 150% accuracy, +10% FP-measure, 5× API reduction.
5. *Agentic ER: The Next Frontier in Entity Resolution* [Vision], arXiv:2607.27435 (2026-07-29).
6. *Adaptive Graph Refinement and Label Propagation with LLMs for Cost-Effective Entity Resolution*, arXiv:2605.25814 (2026).
7. *ChatMatcher: End-to-end Entity Resolution with 7B LLM-based Matching*, Information Systems (2026) (S0306437926000980).
8. *Multi-Agent RAG Framework for Entity Resolution*, MDPI Computers 14(12):525 — 94.3% name-variation accuracy, 61% API-call reduction.
9. Qi et al., *Format-constraint coupling in knowledge-graph construction from CSV tables*, arXiv:2605.21974 (2026) — catastrophic mismatch; direct-graph gap +47.6pp.
10. Capozzi & Helbing, *Agentic GraphRAG production pipeline*, arXiv:2605.18770 (2026) — 97.15% merge precision.
11. Fellegi & Sunter (1969), *A Theory for Record Linkage* — foundational probabilistic model.
12. Splink (UK Ministry of Justice) — open-source Fellegi-Sunter implementation.
13. Corpus: memory_load 2026-05-20/26/29, 2026-07-06/14 — ICIJ methodology, PPRL tradeoffs, composite trust-score gap, source-resolution isomorphism.
