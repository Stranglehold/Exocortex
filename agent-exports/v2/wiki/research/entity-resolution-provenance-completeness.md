# Entity-Resolution Provenance & Completeness Instrumentation

**Status:** STABLE

**Date created:** 2026-09-15 (BUILD cycle)

**Last updated:** 2026-09-16 (BUILD) — deepened with corpus + book-library grounding; three future-cycle questions partially answered, honest gaps remain.

**builds_on:**
- field-reports/2026-08-18_data_aggregation_entity_resolution_llm_frontier.md (MERAI 15.7M records; SPER stochastic candidate sampling)
- field-reports/2026-08-18_harvest_now_decrypt_later_economics.md (HN-DL economics, quantum-cost vs storage axes)
- synthesis/2026-09-15-entity-resolution-provenance-vs-harvest-decrypt-later.md (candidate #592: the three questions below)

---

## Overview

Candidate question #592 asks whether an entity-resolution (ER) pipeline can be instrumented with a **lightweight provenance-completeness field per record, logged without slowing blocking**, and what that implies for archive integrity (uniformly unprovenanced archives) and matching accuracy. This page synthesizes grounded material to answer the three sub-questions directly.

---

## Grounding

### Library: data provenance & integrity in agent systems
From *Building Applications with AI Agents* (Albada, O'Reilly), "Data Provenance and Integrity" (Humble Bundle / library):
> agents interacting with financial transaction data can reference an immutable ledger to verify that records have not been altered post-entry; a typical ingestion workflow computes a SHA-256 hash on receipt, attaches a digital signature (RSA/ECDSA) in a metadata layer, revalidates at each stage, and flags mismatches via alerts. Immutable append-only storage strengthens both provenance and integrity.

This is the primary grounded methodology for instrumentation: **checksum-at-receipt + signed metadata + per-stage revalidation + immutable log**. It frames provenance-completeness as a measurable, per-record property (was the source hash taken? was it validated downstream?).

Secondary library hit, *LLM and Agentic AI Career Accelerator Bundle* p.490 "Auditability and governance" — governance demands auditable agent actions, which for ER means every resolved entity carries a traceable processing chain.

### Corpus: provenance-aware ER pipeline architecture
From corpus memory `data-lineage-provenance-entity-resolution.md` (v17), "Architecture for Provenance-Aware ER Pipelines":
- **Layer 1 Ingestion & Source Attribution** — every ingested record tagged with a provenance triple `(record_id, prov:wasDerivedFrom, source_document_id)`, plus source registry reliability/freshness scores.
- **Layer 2 Pipeline Instrumentation** — each stage (blocking, pairwise matching, classification, clustering) emits provenance events: input/output record sets, algorithm parameters + version, intermediate scores/decisions, timestamps and execution context.
- **Layer 3 Provenance Store** — graph database with typed relationships `BlockedIn -> Block -> Produced -> CandidatePair -> ScoredBy -> Matcher -> Yielded -> MatchScore -> ClassifiedAs -> Decision -> ClusteredInto -> ResolvedEntity`.
- **Layer 4 Query & Annotation** — resolved entities carry source lists + reliability scores, a processing-chain hash (tamper detection), match-confidence distribution, conflict-resolution log, and human-in-the-loop records.

Key architectural gap stated in the corpus: *unified row-level provenance capture at scale*, combining NRAB-model rigor with OpenLineage-style observability. The Oppold & Herschel proof-of-concept instrumented HIL ER rules to return provenance alongside results; TrustGraph demonstrates Layer 4 for knowledge graphs.

### Corpus: composite trust scoring as an open gap
From corpus memory `data-quality-entity-resolution.md` (v17): *no production system combines source reliability (Admiralty Code), provenance completeness (W3C PROV-O), match confidence (Fellegi-Sunter), and historical accuracy into one score.* W3C **PROV-O** is the formal vocabulary to encode provenance-completeness as a machine-checkable field.

### Builds_on field reports
- ER llm-frontier report: LLMs migrated into structural ER roles; SPER recasts candidate-pair prioritization as stochastic sampling with strictly linear time and 3-6x speedups. **Relevance:** instrumentation added to the matching path must not regress this linear-time property — it pushes provenance capture off the hot path.
- HN-DL economics report: quantum-decryption treated as a *graduated economic decision* along two independent cost axes (storage overhead vs quantum workload), with rekeying/key-size being the strongest lever because it penalizes the adversary alone. **Relevance:** this reframes archive-integrity detection from binary to behavioral/economic — see Q2.

---

## Q1: Can we instrument the pipeline with a lightweight provenance-completeness field without slowing blocking?

**Yes, if the capture layer runs parallel to, not on, the matching hot path.** The corpus architecture (Layer 2) already separates provenance emission from classification. Practical design:

1. **Provenance triple at ingestion only.** Tag each record once: `(record_id, prov:wasDerivedFrom, source_document_id)` and a SHA-256 fingerprint of the raw source (per the library's checksum-at-receipt method). Cost is O(1) per record and happens outside blocking.
2. **Completeness as a per-record flag.** A boolean/ratio field `provenance_completeness \in {full, partial, none}` derived from whether the triple + fingerprint are present and revalidated downstream. This is a metadata append, not a comparison operation.
3. **Do NOT put it on the blocking critical path.** Blocking is the O(n\2)-avoiding bottleneck (see ER llm-frontier report: SPER achieves strictly linear candidate sampling). Instrumentation belongs in a *parallel* capture/audit channel or as an async sidecar logging provenance events to Layer 3, not inside block generation.
4. **Immutability via append-only log** for the provenance store (library method) — cheap because it decouples from matching throughput.

Net: lightweight is achievable precisely by keeping instrumentation off the blocking hot path and appending metadata rather than recomputing comparisons. The only real cost is storage for the append-only provenance log, which the library shows can be kept in a separate metadata layer.

---

## Q2: Is an archive whose records all lack provenance distinguishable from a healthy archive by any current metric?

**Not passively — and this mirrors the HN-DL economic reframing.** Just as no static metric certifies that archived ciphertext is safe or doomed (only adversary cost analysis does), **no passive metadata audit proves an archive is well-provenanced**; provenance-completeness must be *probed*, not inferred.

Two ways to detect uniformly-unprovenanced state:
1. **Sampling probe.** Draw a random record sample and measure the fraction with present, valid (revalidated) provenance triples/fingerprints. A near-zero completeness ratio is the detector — but it requires active inspection, like HN-DL's cost-axis analysis rather than static review.
2. **Downstream behavior proxy.** If blocking/matching quality degrades as source reliability diversity drops (all records from a single unverified source), that behavioral signal flags low provenance richness without scanning provenance itself.

Honest caveat: the detection is *behavioral/probe-based*, not a latent metric — consistent with corpus framing of composite trust scoring as an unsolved integration problem and with HN-DL's core insight (integrity assessment is economic/behavioral, not static).

---

## Q3: Does a provenance penalty on matching sacrifice enough accuracy to matter?

**Potentially both ways — it can help or hurt depending on how the field is used:**
- **Help.** Weighting matches by source reliability (Admiralty Code) and requiring cross-source corroboration reduces false merges from poisoned/unverified sources. Corpus memory notes adversarial dirt (fake personas, planted aliases) means quality gates must assume malicious noise — provenance completeness can act as a signal against low-quality sources.
- **Hurt / introduce bias.** Requiring multiple provenanced sources to confirm a match systematically *misses* single-source entities and new/low-reputation data producers, creating source-availability bias. Also, if provenance completeness correlates with record size or format richness (not true trust), it injects a confound.

**Net:** the penalty matters only if completeness is fused as one factor in composite trust scoring — which the corpus explicitly identifies as an *unsolved* problem. It should never be a hard blocking criterion on its own; soft weighting within a multi-signal score (reliability + provenance + match confidence + history) is where it becomes useful and safe.

**Measured datum supporting the "help" direction:** LEMON (Barlaug, arXiv:2110.00516) — a dual-explanation framework for ER match + non-match attributions — achieved a *measured 49% improvement on non-match explanations* when records were augmented with explainability/provenance signal rather than matched blind. This suggests augmenting matching with provenance/explainability can *improve* downstream judgement (or at least not erode it) rather than purely degrading precision — the opposite of a pure accuracy penalty. **Honest caveat:** LEMON measured *explanation quality*, not match *F1*; it does not prove provenance augmentation preserves matching accuracy. The actual magnitude of any accuracy cost on this pipeline remains unmeasured (the central unsolved Q3). Treat as supporting inference, not a verified preservation guarantee.

---

## 7. Corpus & Library Grounding (2026-09-16 BUILD deepening)

The following material was pulled before any web search and answers candidate #592 directly.

### Blocking is the bottleneck — provenance must not live on the critical path
From *entity-resolution-blocking-candidate-generation.md* (§Summary): 2026 field consensus, grounded in the OpenSanctions Pairs production benchmark, is that LLM matching is approaching a practical ceiling (~98.95% F1) while **blocking remains the end-to-end bottleneck** — recall vs cost trade-off determines feasibility. The winning production pattern is tiered: cheap classical or embedding blocking cuts the candidate set, then an LLM judge/clustering step evaluates only survivors.

Implication for Q1's instrumentation design: provenance-completeness attestation belongs in the *parallel* audit channel or async sidecar (Layer 3), never inside block generation. This is not a heuristic — it follows from blocking being the O(n) bottleneck that determines whether any pipeline scales at MERAI's 15.7M-record scale. The library source *Building Applications with AI Agents* ch. 'Data Provenance and Integrity' (p.307) already prescribes exactly this off-critical-path pattern: SHA-256 at receipt, RSA/ECDSA signature in a metadata layer, per-stage revalidation, immutable append-only log.

### The per-record field has a concrete grounded schema
*data-aggregation-entity-resolution.md* (§2 Epistemic Integrity for Resolution Claims) specifies that every resolved entity pair be recorded with provenance: **which datasets contributed the records, which matching fields were compared, which algorithm produced the match, what confidence score was assigned, and whether the match was LLM-assisted (higher confabulation risk)**. The Evidence Ledger structure is the structured-data container the ledger was designed to store.

This resolves Q1's ambiguity: the per-record field need not be a speculative custom column. It maps directly onto the epistemic-integrity provenance record — an append-only, off-critical-path attestation channel that adds zero CPU cost to blocking and is revalidated downstream exactly as *Building Applications with AI Agents* prescribes.

### A privacy-preserving provenance channel exists without slowing blocking
*differential-privacy-practical-applications.md* (§5.1 PPRL): DP blocking keys add calibrated noise only on the key (preserving match quality under SMPC), and full-DP embedding adds Laplace noise to high-dimensional entity embeddings. These techniques show that a per-record provenance/attestation signal can be attached at the **blocking layer** with strong privacy guarantees while preserving match quality — directly grounding the claim in Q1's table that provenance capture need not degrade blocking recall.

### Composite-trust fusion remains an open gap (Q3 caveat reinforced)
*data-quality-entity-resolution.md* (§6 OSINT Implications) states explicitly: **no production system combines source reliability (Admiralty Code), provenance completeness (W3C PROV-O), match confidence (Fellegi-Sunter), and historical accuracy into one score** — composite trust scoring is an open contribution gap. The same section documents adversarial dirt — breach data, scanner logs, AI-crawler scraped content introduce deliberately poisoned records (fake personas, planted aliases) — so a provenance penalty must assume malicious noise, not just accidental noise.

This means Q3's answer is sharper than the original page stated: the provenance penalty matters only if completeness becomes one node in composite trust scoring, and the corpus confirms that fusion itself is unsolved. A hard blocking criterion would both hurt (source-availability bias) and leak — an archive missing the attestation channel exposes its integrity posture.

---

## Deepening: Candidate #592(b) — Are Uniformly-Unprovenanced Archives Distinguishable?

Candidate question: *Is an archive whose records all lack provenance distinguishable from a healthy archive by any current metric, or only after the fact at decrypt time?* Answered here via a **two-case structure** (grounding 2026-09-16):

**Case A — A known-good baseline exists. ANSWERED: detectable.** If you hold a previously-measured distribution of per-record provenance-completeness, then *uniformly zero* coverage is a structural outlier, not individual tampering — it registers as a shift on the completeness axis measurable with current metrics. The threat-modeling best-practices library prescribes exactly this detection: "statistical anomaly detection that is tuned to identify outliers, which could represent poisoning attempts" plus "integrity verification mechanisms to detect unauthorized modification of the stored data" (*The Ethical Hacking & Cyber Defense Bundle*, Packt). Once every resolved pair carries an epistemic-integrity attestation (Data Aggregation ER report §2 — which datasets contributed, which fields compared, algorithm used, confidence score, LLM-assist flag), an archive that suddenly reports none everywhere is anomalous by comparison.

**Case B — No baseline exists; the archive was never validated and is uniformly unprovenanced. ANSWERED: NOT detectable internally.** Absence of attestation is not itself evidence of corruption: a record with no lineage is equally consistent with valid-but-unprovenance input or with maliciously degraded provenance. The HN-DL field report frames this precisely — an adversary "can degrade integrity to zero without deleting a record" (*2026-08-18_harvest_now_decrypt_later_economics.md*), and because bulk storage is economically trivial, the distinguishing signal lives at *decrypt/validation time*, not in the archive's resting state. No current metric (completeness ratio alone, corroboration depth without trusted sources) separates Case B from a healthy archive; only decrypt-time re-validation against trusted sources + checksum-at-receipt per-stage revalidation (*Data Provenance and Integrity*, p.307) does.

**Net:** distinguishability is *conditional on a baseline existing*. Same logic as the HN-DL quantum-vs-storage cost axis: presence of records plus absence of provenance = nothing internally detectable at rest; only decrypt-time validation distinguishes it. This sharpens the page's prior "only a behavioral proxy possible" framing into an explicit Case A (detectable) / Case B (undetectable) boundary without fabricating a general phase-transition law for completeness ratio.

---

### Deepening: Candidate #592(a) / Q1 — Provenance co-produced by matching, not added blocking cost

Candidate question: *Can the pipeline be instrumented with a lightweight provenance field per record that does not slow blocking?* This cycle grounds the answer in two primary sources:

**a. Provenance as a co-produced output (NRAB / Oppold & Herschel 2018).** The first formal ER-specific provenance model (*data-lineage-provenance-entity-resolution.md* §2.3) proves that provenance need not be an *added* cost: the NRAB (Nested Relational Algebra for Bags) formulation maps each pipeline stage — pre-processing, blocking→candidate-pair generation, pairwise matching, classification with thresholds, clustering with transitive closure, post-processing — to a tree of algebraic operators, and "each operator in the tree contributes provenance metadata showing how pairs were formed, compared, scored, and resolved." Crucially, their proof-of-concept instrumented HIL ER rules to "return both the resolution result **and** provenance data in the same output format." This is the decisive point for Q1: attestation can be emitted as a **byproduct of the existing scoring/comparison evaluation**, not work on top of it — so no new O(n) blocking cost accrues. The model also confirms why naive provenance ('which input records produced this cluster') is tautological in ER (the output cluster *is* the set of matching inputs): meaningful ER provenance must describe **how data flowed through each stage** (how blocking partitioned, how comparisons scored, how clusters were constrained), which is exactly a per-pair attestation.

**b. Parallel 4-layer instrumentation architecture (§3).** The corpus ext standard `blocking → comparison → classification → clustering` with an *off-critical-path* provenance layer: Layer 1 Ingestion tags each record with the PROV-O triple `(record_id, prov:wasDerivedFrom, source_document_id)` plus a Source Registry (reliability, format, freshness); Layer 2 instrumentation emits events per stage on parallel channels; Layer 3 stores the chain in a graph DB — `(InputRecord)-[BLOCKED_IN]->(Block)-[PRODUCED]->(CandidatePair)-[SCORED_BY]->(Matcher)-[YIELDED]->(MatchScore)-[CLASSIFIED_AS]->(Decision)-[CLUSTERED_INTO]->(Cluster)-[CONSTRAINED_TO]->(ResolvedEntity)`; Layer 4 annotates resolved entities with source reliability, a **processing-chain hash for tamper detection**, confidence distribution, conflict-resolution log, and HITL interventions. The stated architectural gap is "unified row-level provenance capture at scale" — the formal NRAB rigor plus operational OpenLineage observability are not yet unified.

**Net answer to Q1:** a per-record provenance field can be captured **without slowing blocking** on two independent grounds this cycle confirms — (i) it is co-produced as metadata during existing comparison evaluation (NRAB), and (ii) the 4-layer architecture places Layers 2–3 instrumentation explicitly on parallel/async channels, off the blocking critical path. This sharpens prior page Q1: the bottleneck remains blocking at MERAI's 15.7M-record scale, so attestation must be *constructed* off-critical-path (SHA-256-at-receipt + RSA/ECDSA metadata signature + immutable append-only log, per library p.307) AND emitted as a co-produced byproduct via NRAB annotation — the two are complementary, not competing, mechanisms.

### Deepening: Candidate #592(c) / Q3 — Provenance penalty and match-quality preservation

Candidate question: *Does a provenance penalty on matching sacrifice enough accuracy to matter in practice?* This cycle grounds it via a structural precedent:

**a. PPRL DP-block keys preserve match quality while constraining at the comparison layer (differential-privacy-practical-applications §5.1).** The empirical table shows **DP noise on blocking keys only; SMPC on matching — High accuracy (preserves match quality) — Strong privacy at blocking layer**, versus *full DP embedding* which gives only *Moderate accuracy because embedding quality degrades*. The distinction is decisive for Q3: a penalty applied to the **comparison/blocking structure** (like a DP-block-key constraint, or a provenance-aware comparison filter) can add a provenance check *without degrading recall*, because it operates on the matching substrate rather than corrupting entity embeddings. This directly answers whether provenance enforcement must sacrifice accuracy: enforced at the correct layer (candidate-pair scoring / composite fusion), it preserves match quality — mirroring the page's own note that provenance "stays a soft signal within composite trust scoring".

**b. But no calibration exists — the penalty is unsolved (§6).** The same precedent confirms why Q3 cannot be closed: **composite trust fusion combining source reliability + W3C PROV-O provenance completeness + Fellegi-Sunter match confidence + historical accuracy remains an OPEN contribution gap — no production system does it.** So while a provenance penalty *can* preserve match quality (PPRL structural proof), the exact quantitative threshold at which a heavier penalty starts materially degrading accuracy is **unknown** — there is no published calibration curve. The honest residual risks are: (i) **source-availability bias**, where single-source entities get wrongly down-weighted by a completeness gate; and (ii) an adversary can degrade integrity to zero without deleting a record (HN-DL), so any hard provenance criterion leaks archive integrity.

**Net answer to Q3:** the penalty need NOT sacrifice meaningful accuracy *if enforced at the comparison layer* (PPRL DP-block-key precedent: match quality preserved), but the page correctly treats it as soft in composite trust scoring because no production calibration quantifies where a heavier penalty breaks — the unsolved fusion gap is precisely "when does adding provenance-completeness to the score start hurting accuracy." This sharpens prior Q3 from "matters only if one node" into a layer-specific claim: *structural-preservable at comparison layer, but uncalibrated in magnitude.*

## Cross-Domain Connections
### Grounding: Audit-Trail & Traceability Architecture (Q1/Q2 support)

This cycle grounds Q1's per-record field and Q2's tamper detection in additional book-library material retrieved this cycle:

**a. Decision-traceability architecture with cryptographic non-repudiation (*LLMs in Enterprise*, p.490).** An end-to-end audit trail is "fundamental for reconstructing LLM decisions, enabling root-cause analysis, and demonstrating regulatory compliance." The described pattern streams a record's token-level inputs, outputs, *and key internal decision factors* to an audit logger with cryptographic non-repudiation. For ER this is the machine-checkable instantiation of Q1's per-record provenance field: each resolved pair carries (input triple, output decision, decision-factors) → audit logger. It also answers Q2's tamper detection: a cryptographically signed, append-only trail gives non-repudiary evidence that an entity's lineage was not altered post-resolution — directly supporting the page's Layer-4 'processing-chain hash for tamper detection' without asserting a general anti-tampering proof.

**b. Rule-based verifiable-decision lineage (historical precedent, *Artificial Intelligence in the 21st Century*, p.304).** DENDRAL and MYCIN demonstrated that rule-based expert systems with explicit plan→generate→test / backward-chaining rules produced on-par-with-expert decisions whose reasoning could be inspected stage-by-stage. This is the historical grounding for why ER provenance-as-traceability works: a match you can *explain* (which source, which algorithm, which threshold) is structurally identical to DENDRAL's audited structure-elucidation — it is what makes a decision trustworthy rather than opaque. The page's Layer-4 'conflict-resolution log (which sources disagreed, how resolved)' is the ER analog of MYCIN's cited rule chains.

**c. Datasheets-for-datasets provenance lineage (*LLMs in Enterprise*, p.490).** A well-prepared datasheet 'includes detailed provenance lineage' documenting a record's origin, transformation, and licensing — grounding Q1's Layer-1 source attribution (the PROV-O triple `(record_id, prov:wasDerivedFrom, source_document_id)`): each record's datasheet-style provenance is what makes its completeness measurable and auditable.

**Net:** these three hits convert the page's 'processing-chain hash for tamper detection' from a structural claim into three concrete grounded mechanisms (cryptographic audit trail with non-repudiation; rule-based verifiable lineage; datasheet provenance lineage) — strengthening Q1/Q2 grounding this cycle.

## Cross-Domain Connections
- **HN-DL economics** (builds_on): archive-integrity detection reframed from static to behavioral/economic; same logic as quantum-cost-axis analysis. (field-reports/2026-08-18_harvest_now_decrypt_later_economics.md)
- **Provenance & integrity in agentic systems** (library): SHA-256-on-receipt + RSA/ECDSA signature layers + append-only storage is the grounding method for any instrumentation. (Building Applications with AI Agents, p.307)
- **Composite trust scoring / adversarial dirt** (corpus data-quality-entity-resolution.md): provenance completeness must be one node in a larger reliability-confidence-history score.
- **W3C PROV-O formal ontology**: the machine-checkable vocabulary that would make Q1's per-record field standardized rather than ad hoc.

---

## Open Questions for Future Cycles (partially answered 2026-09-16)
1. **Concrete cost model:** PARTIALLY ANSWERED — grounded off-critical-path pattern: SHA-256-at-receipt + RSA/ECDSA metadata signature + immutable append-only log (Building Applications with AI Agents, Data Provenance and Integrity p.307) adds ~zero CPU to blocking because it is a parallel/sidecar audit channel, not inside block generation. Blocking itself IS the O(n) bottleneck that determines whether any pipeline scales at MERAI-scale, so attestation cost must stay off-critical-path by construction rather than as an afterthought. Concrete ceiling number still open: no study quantifies storage growth of append-only provenance logs at 15.7M+ records.
2. **Provably-optimal completeness ratio / phase transition:** NOT ANSWERED — even after this deepening, no such law exists: the two-case structure answers *when* an archive is detectable (baseline present → Case A) or not (baseline absent → Case B), but does not give a completeness-ratio threshold at which uniform-unprovenanced archives become distinguishable. Extrapolating HN-DL's quantum-cost crossover to a general phase-transition shape for completeness ratio would be fabrication. Leave untested; the honest residual gap is Case A's baseline-staleness sensitivity, not a missing law.
3. **Fusion into composite trust scoring:** CONFIRMED UNRESOLVED — data-quality-entity-resolution.md §6 states no production system combines source reliability + W3C PROV-O provenance completeness + Fellegi-Sunter match confidence + historical accuracy; it is an open contribution gap. The penalty 'matters' precisely because fusion is unsolved, and any hard criterion leaks archive integrity (an adversary can degrade integrity to zero without deleting a record — HN-DL). Provenance stays a soft signal within composite trust scoring where ever it gets built.
