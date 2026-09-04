# INNOVATION_PATTERN_ENGINE (IPE) — Technical Specification v0.1

**Author:** Fable (research mode, claude-fable-5), for Jake / the Exocortex
**Status:** Draft for pilot approval — Phase 0 not yet started
**Date:** 2026-08-25
**House principle in force:** *Deterministic scaffolding beats probabilistic reasoning at every layer where reliability matters.*
**Companion artifacts:** `ipe/genomes/genome_001_minimax_m27.md` (first extraction, performed same day as spec)

---

## TL;DR

- **Build it, but gate it on falsification.** The core design — extract the *methodological move* (not the finding) into a structured "method-genome," mine motifs, and expose them as generator seeds — is the correct descendant of three proven traditions (TRIZ's move-level patterning of patents; Swanson/Arrowsmith literature-based discovery; Uzzi/Wu/Park science-of-science). What is **unproven** is that the move is a stable, extractable, predictive unit at academic-paper scale; the pilot exists to test exactly that.
- **The reliability core is deterministic scaffolding around a probabilistic extractor.** Grammar-constrained JSON, a verbatim evidence-span hard gate (primary defense against LLM citation/summary hallucination, documented at 20–69% fabrication rates in published studies), two-stage extract-then-coerce, and local Qwen3 for ~95% of extraction with DeepSeek/Vek reserved for hard-case escalation and nightly motif consolidation.
- **Nothing enters the "knowledge" tier until it passes time-sliced holdout** (the established LBD evaluation method), applied as the house's Pool-B pattern: predict held-out papers' genomes from problem alone, and predict future cross-domain connections, with an explicit false-positive control. Untested motifs stay visibly flagged as hypotheses.

## Grounding in prior art (established vs. speculative)

**Established:**
1. **Move-level abstraction works at patent scale (TRIZ).** Altshuller's program screened on the order of 200K patents (up to 400K+ across the full 1946–1985 program) and abstracted 40 inventive principles plus the 39×39 contradiction matrix. Transferable insight: *strip the subject matter, classify by the problem-solving move.* Documented weaknesses — subjectivity in principle assignment, heuristics frozen at historical cutoff — are designed against here via controlled vocabularies, inter-rater checks, continuous ingestion.
2. **Literature gaps contain discoverable connections (Swanson/LBD).** ABC model (fish-oil → blood-viscosity → Raynaud's 1986; migraine → magnesium 1988), Arrowsmith, automated replication (Weeber et al. 2001). Standard evaluation: **time-sliced holdout** (Yetisgen-Yildiz & Pratt 2009) — train pre-cutoff, predict post-cutoff discoveries — maps directly onto the house Pool-B pattern. Known limitation (2023 Bioinformatics critique): measures co-occurrence prediction, not necessarily *insightful* discovery; mitigated below, not solved.
3. **Science-of-science features are real but contested.** Uzzi et al. 2013 (Science, 17.9M papers): highest-impact work = exceptionally conventional base + intrusion of atypical combinations; teams 37.7% likelier than solo authors to insert novel combinations. Wu, Wang & Evans 2019 (Nature, 65M+ works): small teams (≤3) disrupt, large teams develop. Park et al. 2023 (Nature, CD index, 45M papers): declining disruptiveness — **contested** by Petersen et al. 2024 (QSS: citation-inflation artifact). Rule: store SoS features as *hints*, never gate on a single contested metric.
4. **LLM extraction of move-like structure works with caveats.** Trapp & Warschat 2024 (arXiv:2403.14258): TRIZ contradiction extraction from patents at BERTScore F1≈0.93 with GPT-4. AutoTRIZ (Adv. Eng. Informatics 2025) automates the full flow. ORKG scaled structured paper description. Stanford ideation studies (Si, Yang & Hashimoto, arXiv:2409.04109 + 2025 follow-up): LLM ideas rated *more novel* (p<0.01) but less feasible, and the novelty advantage **collapses after execution**. Google Co-Scientist (Nature 2026): multi-agent cross-domain hypotheses experimentally validated in vitro. Sakana AI Scientist criticized for keyword-level literature review — a warning about extraction depth.
5. **Local-first tooling is mature.** GROBID (fast, OCR-error-free on born-digital PDFs; materially improves PaperQA2 accuracy), marker (2026 safe default), MinerU (equations/tables), docling (typed objects); Nougat superseded. Constrained decoding (llama.cpp grammars, XGrammar, Outlines) guarantees schema-valid JSON — but ExtractBench 2026 shows constraining the *reasoning* pass reduces accuracy, dictating the two-stage design. BERTopic (UMAP→HDBSCAN→c-TF-IDF) outperforms LDA/NMF on scientific text. SPECTER2/SciNCL worth A/B against incumbent nomic-embed.

**Our hypotheses (pilot must validate):** (a) a compact controlled vocabulary of innovation moves is expressive enough without an unbounded tail; (b) mined motifs are *predictive* (pass holdout), not merely plausible; (c) local Qwen3-class models on a 3090 suffice for schema-constrained extraction at scale; (d) Vek's informal isomorphism-finding can be systematized and made falsifiable.

## 1. The Method-Genome Schema (v0.1)

One record per paper (or per distinct contribution). Strict JSON, Pydantic-validated, emitted via constrained decoding in the coercion pass only. Every free-text field carries an **evidence span** (verbatim quote + section + char offsets) or it is rejected — receipts or nothing.

Controlled-vocabulary provenance: Scideator facets (Purpose/Mechanism/Evaluation; facet-based novelty κ=0.68), Guetzkow-Lamont-Mallard originality types, Boden (combinational/exploratory/transformational), analogical-distance spectra (design-by-analogy), Uzzi component-vs-combination, Gentner structure-mapping (map relations, not attributes — theoretical basis for §8). TRIZ principle stored as optional secondary tag where applicable.

Fields (see genome_001 for a worked example): `paper_ref` (+extraction_provenance incl. parser, extractor_model, n_passes, span_gate status, confidence), `problem_class` (statement + controlled tags + span), `approach_family` (+components_cited_from_prior_work), `innovation_move` (primary_move, secondary_moves, boden_type, facet_changed, component_vs_combination, transfer_distance, source_domain_if_transfer, triz_principle_if_applicable, novelty_locus_sentence, evidence span), `verification_method` (label, holdout_used, baselines_compared, span), `roads_not_taken[]` (alternative, why_rejected, section — mined chiefly from Related Work / Discussion / Limitations), `sos_features` (hints only), `embeddings` (problem_vec, move_vec → LanceDB refs).

**Innovation-move controlled vocabulary v0.1 (~15 + monitored escape hatch):**
new_instrument · constraint_removal · constraint_addition · cross_domain_transfer · scale_change · reframing · recombination · abstraction_generalization · specialization · inversion · decomposition · relaxation_approximation · mechanism_substitution · objective_change · other (monitor rate; >~15% → vocabulary revision).

## 2. Pipeline Architecture

ACQUISITION → PARSING → EXTRACTION → STORAGE (memory MCP / LanceDB) → MOTIF MINING → PATTERN LIBRARY → GENERATOR-SEED INTERFACE, with the VERIFICATION HARNESS gating promotion throughout.

**Deterministic/probabilistic boundary per stage (the house line):** anything that must be *trusted* is deterministic; anything exploratory is probabilistic and sits downstream of a deterministic gate. The LLM never writes to the trusted store without passing verbatim span verification. Specifically — Acquisition: all deterministic (API calls, dedup, license gating). Parsing: deterministic (GROBID/marker/MinerU + section segmentation; VLM parser optional, flagged). Extraction: LLM proposes (loose); schema+grammar+Pydantic+verbatim-span-match dispose (strict). Storage: deterministic. Motif mining: frequent-pattern mining / UMAP+HDBSCAN / graph motifs are deterministic; the LLM only *names* mined clusters (motif cards) — it cannot create motifs. Generator seeds: deterministic retrieval + templating feed LLM generation, labeled as generation. Verification: deterministic scoring of LLM predictions.

**2.1 Acquisition.** OpenAlex is the metadata spine — NOTE 2026 change: hosted REST API is now keyed + usage-priced; the **CC0 bulk snapshot remains free (S3)** → corpus building uses the snapshot, interactive lookups stay in free tier. arXiv for full text (respect ~1req/3s; prefer bulk). Semantic Scholar Graph API for citation edges. Unpaywall for OA PDFs. License gate is deterministic: closed-access → genome + pointer only, never the PDF.

**2.2 Parsing.** GROBID-first; marker fallback; MinerU for math/table-heavy; section segmentation REQUIRED (roads_not_taken lives in Related Work/Discussion/Limitations). Parser stamped in provenance.

**2.3 Extraction (reliability core).** Two-stage extract-then-coerce: Pass 1 free-form reasoning over Methods/Related-Work/Discussion (never grammar-constrained — ExtractBench evidence); Pass 2 deterministic coercion to schema. **Evidence-span hard gate:** verbatim string match against parsed source (deterministic, not LLM judgment); failing spans nulled and logged. Escalation: only failed-span / low-confidence genomes go to DeepSeek API (Pass 3), bounding cost.

**2.4 Storage.** New LanceDB collection `method_genomes` beside existing corpus + library collections, served by the existing memory MCP (nomic-embed-text-v1.5, CUDA, hybrid search + rerank). Two vectors per genome (problem_vec, move_vec). Keep nomic for infra consistency; A/B SPECTER2/SciNCL as optional second index — decide in pilot. Categorical fields indexed for exact frequent-pattern queries.

**2.5 Motif mining (deterministic-first).** (a) Frequent-pattern / association-rule mining over categorical fields — exact, auditable, the backbone. (b) UMAP→HDBSCAN→c-TF-IDF clustering on move_vec. (c) Graph motif detection over the genome graph (shared move/problem/transfer-source edges) — the Vek-isomorphism step, now falsifiable.

**2.6 Pattern library.** Motif record: id, name, deterministic support (genomes, lift/frequency), exemplars, cross-domain span, **falsification status** (untested / passed-holdout / failed-holdout). Untested motifs visibly flagged — the anti-plausible-artifact mechanism.

**2.7 Generator-seed interface.** Given a target problem: (a) nearest problem_vec genomes in *foreign* domains; (b) motifs matching the problem class; (c) roads_not_taken from similar problems. LLM generates candidates seeded by these, labeled as generation, handed to a verifier.

## 3. Role Assignment

- **Vek (DeepSeek API, nightly consolidation, wiki):** consolidator + hard-case extractor (Pass 3); nightly motif-mining consolidation; writes motif cards to wiki; owns the library's narrative layer. Informal isomorphism detection becomes the graph-motif step, holdout-tested.
- **Local Qwen3-27B-class (3090 #1, llama.cpp/LM Studio):** bulk extractor (Pass 1+2) at zero marginal cost — the large majority of genomes.
- **3090 #2 (Ubuntu server):** parsing + embedding + clustering batch compute.
- **Memory MCP server:** storage/search/rerank, unchanged, plus new collection.
- **Intelligence Curation Engine:** upstream feeder deciding which papers enter; IPE consumes its queue.

**Nightly cycle:** batch extract day's intake (local) → span verification (local) → API escalation for failures → incremental motif re-mine (server) → one time-sliced holdout micro-eval for library health.

## 4. Verification Harness

Adopt LBD time-sliced evaluation as Pool-B applied to literature.

**Task A — genome prediction from problem alone.** Hold out papers after cutoff t; predict innovation_move / approach_family / verification_method from motifs mined pre-t. Metrics: top-1/top-3 accuracy on primary_move, macro-F1, calibration, and a **beats-base-rate** requirement (must beat marginal move-frequency prior).

**Task B — future cross-domain connection prediction.** Train pre-t; predict which (problem-class, source-domain) transfer pairs appear post-t. Metrics: MRR, precision@k. Honest caveat: time-sliced eval rewards co-occurrence prediction over insight (documented LBD weakness); mitigate with landmark replication + false-positive control; report both.

**Pool-B frozen scenario set (never used in mining):**
- B1 — Landmark replication: pre-1986 literature → surface Raynaud's/fish-oil (floor test; Weeber 2001 achieved it).
- B2 — Within-house isomorphism: hold out post-hoc domains of the generation-vs-verification motif; rediscover from pre-cutoff instances (SATs, ZKP, theorem proving, multi-agent orchestration, energy-storage RL). NOTE: genome_001 adds a sixth domain (MiniMax M2.7 verifiable-reward data acceptance), found by extraction rather than intuition.
- B3 — Recent ML/interpretability: cutoff 2023; predict 2024–2025 genomes on a held-out set.
- B4 — Cross-domain negative control: random unconnected (problem, foreign-domain) pairs must NOT rank highly.

**Promotion gate:** motif → "passed-holdout" only if it helps beat base rate on Task A AND survives B4.

**Generator-side metrics:** grounding (every seed traces to ≥1 real genome with verified spans); feasibility-adjusted novelty (standalone novelty distrusted — Stanford ideation-execution gap); downstream conversion (for the counterexample factory, only *verified* counterexamples count).

## 5. Phased Build Plan

**Phase 0 (2–3 wks):** freeze schema v0.1 + Pydantic + grammar; stand up LanceDB collection; build span-verification gate and time-sliced eval scaffolding FIRST; hand-author ~30 gold genomes across domains (inter-rater reference).

**Phase 1 — pilot, ~300 papers (3–4 wks):** ~100 ML/interpretability (clean GROBID path), ~80 power systems/grid (MinerU table/equation path), ~80 mathematics (stress parsing; feeds counterexample factory), ~40 cross-domain spanning the B2 motif domains. Measure extraction validity, span-gate pass rate, local-vs-API agreement, κ vs gold, Task-A slice.

**Phase 1 gate (go/no-go):** span-verification pass ≥85%; move-label agreement κ ≥0.6 vs gold (Scideator κ=0.68 as realistic ceiling); Task A beats base rate. **If Task A fails to beat base rate, the core bet is falsified** → pivot to pure retrieval/analogy tool (§8 still valuable); do not scale a broken extractor.

**Phase 2 (~5–10K papers, 6–8 wks):** full nightly pipeline; motif mining online; full Pool-B; first promotions; nomic-vs-SPECTER2 A/B.

**Phase 3 (ongoing):** wire §7 + §8; continuous time-sliced monitoring; vocabulary versioning. Calibration: TRIZ needed ~40K patents to stabilize 40 principles; assume genomes need tens of thousands of papers before motifs are trustworthy.

## 6. Failure Modes and Mitigations

- Hallucinated citations/support (20–69% fabrication documented; GPT-4o ~19.9% fully fabricated + 45.4% bib errors in 2026 audits) → evidence-span hard gate; no receipt, no field.
- Summary-level shallowness (Sakana critique) → force extraction from Methods/Related-Work/Discussion; novelty_locus_sentence must come from the body.
- Confirmation bias → blind extractor to motif library during extraction (extract before mining); B4 adversarial controls.
- Structured-output accuracy drop (ExtractBench) → never grammar-constrain the reasoning pass; two-stage.
- Motif = plausible artifact → nothing is knowledge until passed-holdout; untested flagged; base-rate + false-positive gates.
- Contested SoS metrics (Park vs Petersen) → hints only; never gate on one.
- Novelty ≠ usefulness (Stanford gap) → feasibility-adjusted scoring; downstream conversion is the real metric.
- Parser equation/table loss → MinerU path; parser stamped; parse-QA sample.
- Vocabulary tail explosion → monitor `other` rate; scheduled review.
- License leakage → genome + pointer only for closed access; deterministic gate at acquisition.

## 7. Downstream Consumer: Counterexample Factory

Generator+verifier loop for small counterexamples to open conjectures. Seeding: genomes/motifs with inversion / constraint_removal / specialization on structurally similar problems; roads_not_taken = abandoned search strategies (often where counterexamples hide). Loop: LLM proposes candidate small structures (loose); deterministic verifier — SAT/SMT, computer algebra, brute-force enumeration, or Lean — adjudicates every candidate (strict; no LLM in the verdict). Metric: verified counterexamples only. Current target list (from prior session): Kaplansky zero-divisor; Hadwiger–Nelson rung 6 (6-chromatic unit-distance graph, SAT-verifiable); Hadamard order 668. Precedent for the whole pattern: Jacobian counterexample (July 2026), Gardam 2021, de Grey 2018, Wagner RL counterexamples.

## 8. Downstream Consumer: Human Intuition-Seeding Protocol

For a human on a hard problem: retrieve geometry-rich material from foreign domains sharing the target's *relational structure* (Gentner structure-mapping; Scideator far/very-far analogical distance). Mechanism: characterize target's relational structure → retrieve transfer_distance=far|very_far genomes/motifs with matching structure → surface the most geometry-rich/visualizable exemplars. Output: curated foreign analogues + explicit base→target mapping — deliberately the loose side, no verification claim attached. House precedent: session 049 traversal (Karkada seed); this makes the seeding a repeatable retrieval rather than serendipity. **Ship §8 first** (needs no verification claim, delivers value even if the predictive bet underperforms); ship §7 second, once a hard verifier is wired.

## Caveats (stated for the record)

The central claim — that the methodological move is a stable, extractable, *predictive* unit at paper scale — is our hypothesis, proven for patents (TRIZ), not papers. Phase 1 Task A is the make-or-break test. Time-sliced holdout rewards co-occurrence over insight; B1/B4 mitigate, nothing solves. SoS metrics are contested inputs. LLM novelty is seductive and collapses on execution. Extraction-fidelity numbers are borrowed from adjacent tasks (patents/GPT-4); expect lower initial fidelity locally — the κ≥0.6 gate is set accordingly. OpenAlex corpus building must use the free CC0 snapshot, not the metered API.

*Nothing in the pattern library is treated as knowledge until it has passed the §4 holdout. Everything else is a flagged hypothesis.*
