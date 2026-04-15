# Specs Index

**Purpose:** Low-token reference map of everything in `specs/`. Organized by topic so future builders (usually me — Kestrel) can find what exists without grepping the whole directory. Each entry is one line: `filename — what it is`.

**Last updated:** 2026-04-14
**Total files:** 91

**Legend:** `[L3]` = ready-to-build L3 spec. `[note]` = design note / pre-spec exploration. `[brief]` = short brief or methodology document. `[research]` = research synthesis. `[shipped]` = built and deployed. `[audit]` = incident review or gap analysis.

---

## Narrative Management Stack (2026-04-14 — the input pipeline hardening track)

Tonight's work lives here. Four complementary subsystems annotating incoming claims without filtering anything:

- [INPUT_SCRUTINY_RESEARCH_NOTE.md](INPUT_SCRUTINY_RESEARCH_NOTE.md) — [research] 12 rules for adversarial input scrutiny distilled from psychology (Kahneman, Sperber & Wilson, van der Linden), intel tradecraft (Heuer, Zlotnick Bayesian, STANAG 2511), adversarial reasoning (Irving et al. debate, Friston/Itti-Baldi surprise, Klein premortem, Wikipedia NPOV). The grounding foundation for everything else in this section.
- [NARRATIVE_STABILITY_DESIGN_NOTE.md](NARRATIVE_STABILITY_DESIGN_NOTE.md) + [NARRATIVE_STABILITY_SPEC_L3.md](NARRATIVE_STABILITY_SPEC_L3.md) — [shipped] Retcon detection with modality-aware signal classification (reality_update / honest_correction / silent_error / narrative_rewrite / editorial_drift). Catches walkback of previously-committed claims. Modality × volatility × acknowledgment signal table; pure-function classifier; Zlotnick-weighted source confidence updates.
- [HEDGE_PATTERN_DESIGN_NOTE.md](HEDGE_PATTERN_DESIGN_NOTE.md) + [HEDGE_PATTERN_SPEC_L3.md](HEDGE_PATTERN_SPEC_L3.md) — [shipped] Three claim-level fields (`certainty`, `attribution`, `quoted_directly`) + source-type-conditional signal routing (`narrative_campaign` for institutional sources, `unverifiable_stream` for social). Paraphrase rate credibility penalty. Certainty modifier on retcon signal. First live `narrative_campaign` signal fired on Department of War / iran topic.
- [ADVERSARIAL_INPUT_LAYER_DESIGN_NOTE.md](ADVERSARIAL_INPUT_LAYER_DESIGN_NOTE.md) + [ADVERSARIAL_INPUT_LAYER_SPEC_L3.md](ADVERSARIAL_INPUT_LAYER_SPEC_L3.md) — [Phase 1 shipped] OSS as dedicated analyst. Four components (prior injection, surprise scoring v1, verdict compilation, escalation router). Pulls SWARMFISH committee assessments as priors, computes semantic distance, escalates high-surprise claims back to SWARMFISH for re-prediction. Bidirectional feedback loop with structural confirmation-cascade protection.
- [ADVERSARIAL_VALIDATION_PROTOCOL.md](ADVERSARIAL_VALIDATION_PROTOCOL.md) — [DEC-021] Sibling / output-side counterpart. Two-phase protocol for validating the team's own intellectual output before publication: internal pre-mortem + cold-read by fresh instance. Operates at opposite end of the system from the Adversarial Input Layer.

---

## Cognitive Defense / Counter-Propaganda (prior research feeding current work)

- [COGNITIVE_DEFENSE_SYSTEM.md](COGNITIVE_DEFENSE_SYSTEM.md) — [note] (2026-03-12) Unified framework: prompt injection against AI and psyops against humans as the same attack on the same vulnerability. Cites Herman & Chomsky, Rid's Active Measures, Vosoughi et al., van der Linden. Five-stage hypothesis engine with falsification as the primary signal.
- [COGNITIVE_DEFENSE_SYSTEM_v2.md](COGNITIVE_DEFENSE_SYSTEM_v2.md) — [note] Operational schemas for contamination cascade handling. Frozen promotion snapshots for post-promotion remediation.
- [COUNTER_PATRIOTS_ARCHITECTURE.md](COUNTER_PATRIOTS_ARCHITECTURE.md) — [note] Foundational narrative-integrity system. Precursor to Cognitive Defense.
- [COUNTER_PATRIOTS_EPISTEMIC_STAGING.md](COUNTER_PATRIOTS_EPISTEMIC_STAGING.md) — [note] Three-state claim model (Staged → Promoted → Falsified) with van der Linden inoculation. Temporal staging window.
- [COUNTER_PATRIOTS_SOURCE_INTELLIGENCE.md](COUNTER_PATRIOTS_SOURCE_INTELLIGENCE.md) — [note] Source profiling vector sets: identity, topical, bias, behavioral. Named perpetrator frequency. Cui bono asymmetry. The closest prior to the hedge pattern source-type routing.
- [EPISTEMIC_INTEGRITY_DESIGN_NOTE.md](EPISTEMIC_INTEGRITY_DESIGN_NOTE.md) — [note] Three-component evidence audit (Evidence Ledger, Epistemological Classifier, Temporal Anchor). ST-003 motivated. Volatility taxonomy.
- [OPUS_ARCHITECTURAL_REVIEW_CDS.md](OPUS_ARCHITECTURAL_REVIEW_CDS.md) — [review] Opus review of Cognitive Defense System architecture.

---

## OSS / SWARMFISH (the intelligence ledger and committee predictor)

- [OSS_V2_DESIGN_NOTE.md](OSS_V2_DESIGN_NOTE.md) — [note] OSS redesign covering claims table, staging, trust lifecycle, source credibility.
- [SWARMFISH_V2_DESIGN_NOTE.md](SWARMFISH_V2_DESIGN_NOTE.md) — [note] 9-profile committee prediction system. Devil's Inquisitor as the adversarial consensus check.
- [OVERHAUL_PLAN_OSS_SWARMFISH_L3.md](OVERHAUL_PLAN_OSS_SWARMFISH_L3.md) — [L3] Phased fix plan for the iran/hormuz prediction failures documented in ST-007.
- [INVESTIGATION_BRIEF_OSS_SWARMFISH_V2.md](INVESTIGATION_BRIEF_OSS_SWARMFISH_V2.md) — [brief] Investigation framing for the V2 overhaul.
- [OSS_SWARMFISH_OPERATIONAL_LESSONS.md](OSS_SWARMFISH_OPERATIONAL_LESSONS.md) — [note] Operational lessons from running OSS + SWARMFISH in production.
- [OPERATOR_BRIEF_FORMAT.md](OPERATOR_BRIEF_FORMAT.md) — [note] Format specification for operator briefs produced by the SWARMFISH committee.

---

## Stack Layers (Exocortex 12-layer hardening — the core Agent Zero extensions)

- [COMPOUND_BST_DESIGN_NOTE.md](COMPOUND_BST_DESIGN_NOTE.md) + [COMPOUND_BST_SPEC_L3.md](COMPOUND_BST_SPEC_L3.md) — [shipped] Layer 1. Compound classifier with primary+secondary domain routing, momentum on compound signatures, profile-aware enrichment gating.
- [ORGANIZATION_KERNEL_SPEC_L3.md](ORGANIZATION_KERNEL_SPEC_L3.md) — [shipped] Layer 7. PACE protocols, role switching, organizational dispatcher.
- [SUPERVISOR_LOOP_SPEC_L3.md](SUPERVISOR_LOOP_SPEC_L3.md) — [shipped] Layer 8. Loop detection and strategic steering.
- [A2A_COMPATIBILITY_SPEC_L3.md](A2A_COMPATIBILITY_SPEC_L3.md) — [spec] Layer 9. Agent-to-agent protocol (separate aiohttp server).
- [MEMORY_CLASSIFICATION_SPEC_L3.md](MEMORY_CLASSIFICATION_SPEC_L3.md) — [shipped] Layer 10. 4-axis classifier + relevance filter for persistent memory.
- [MEMORY_ENHANCEMENT_SPEC_L3.md](MEMORY_ENHANCEMENT_SPEC_L3.md) — [shipped] Layer 11. Query expansion, temporal decay, related linking, dedup for memory retrieval.
- [MEMORY_ARCHITECTURE_DESIGN_NOTE.md](MEMORY_ARCHITECTURE_DESIGN_NOTE.md) — [note] Overall memory stack design.
- [MEMORY_GIST_RETRIEVAL_DESIGN_NOTE.md](MEMORY_GIST_RETRIEVAL_DESIGN_NOTE.md) — [note] Gist-level retrieval research.
- [ONTOLOGY_LAYER_SPEC_L3.md](ONTOLOGY_LAYER_SPEC_L3.md) — [shipped] Layer 12. Entity resolution, source connectors, JSONL graph.
- [ONTOLOGY_LAYER_11_DECISION_2026-04-14.md](ONTOLOGY_LAYER_11_DECISION_2026-04-14.md) — [decision] Option B: keep dormant-by-design.
- [STAGING_TIER_SPEC_L3.md](STAGING_TIER_SPEC_L3.md) — [spec] Claim staging tier for epistemic integrity.
- [HTN_PLAN_TEMPLATES_SPEC.md](HTN_PLAN_TEMPLATES_SPEC.md) — [spec] Layer 6 HTN plan templates.
- [META_REASONING_GATE_SPEC.md](META_REASONING_GATE_SPEC.md) — [spec] Layer 5. Deterministic parameter correction.
- [TOOL_FALLBACK_CHAIN_SPEC.md](TOOL_FALLBACK_CHAIN_SPEC.md) — [spec] Layer 4. Tool failure detection + recovery suggestions.
- [LAYER_COORDINATION_DESIGN_NOTE.md](LAYER_COORDINATION_DESIGN_NOTE.md) — [note] Cross-layer coordination design.
- [ACTION_BOUNDARY_DESIGN_NOTE.md](ACTION_BOUNDARY_DESIGN_NOTE.md) — [note] Irreversibility gate design.
- [ERROR_COMPREHENSION_DESIGN_NOTE.md](ERROR_COMPREHENSION_DESIGN_NOTE.md) — [note] Deterministic error classifier. "Rust compiler for agent errors."
- [FALLBACK_FIX_DESIGN.md](FALLBACK_FIX_DESIGN.md) — [note] Fallback handling fixes.
- [EXTENSION_STACK_ASSESSMENT_FRAMEWORK.md](EXTENSION_STACK_ASSESSMENT_FRAMEWORK.md) — [framework] Methodology for evaluating extension stack health.

---

## Supervisor / Adaptive Behavior

- [ADAPTIVE_SUPERVISOR_DESIGN_BRIEF.md](ADAPTIVE_SUPERVISOR_DESIGN_BRIEF.md) / [ADAPTIVE_SUPERVISOR_DESIGN_NOTE.md](ADAPTIVE_SUPERVISOR_DESIGN_NOTE.md) — [brief/note] Adaptive supervisor architecture.
- [ADAPTIVE_SUPERVISOR_PHASE1_FINDINGS.md](ADAPTIVE_SUPERVISOR_PHASE1_FINDINGS.md) — [findings] Phase 1 empirical results.
- [ADAPTIVE_SUPERVISOR_PHASE3_DESIGN_BRIEF.md](ADAPTIVE_SUPERVISOR_PHASE3_DESIGN_BRIEF.md) — [brief] Phase 3 scope.
- [ADAPTIVE_SUPERVISOR_PHASE4_ARCHITECTURE.md](ADAPTIVE_SUPERVISOR_PHASE4_ARCHITECTURE.md) — [architecture] Phase 4 architecture.
- [ADAPTIVE_SUPERVISOR_PHASE4_FIELD_EVIDENCE.md](ADAPTIVE_SUPERVISOR_PHASE4_FIELD_EVIDENCE.md) — [evidence] Phase 4 field observations.
- [PROACTIVE_REASONING_SUPERVISOR_DESIGN_NOTE.md](PROACTIVE_REASONING_SUPERVISOR_DESIGN_NOTE.md) — [note] Proactive reasoning supervisor design.
- [V16_PROACTIVE_SUPERVISOR_BRIEF.md](V16_PROACTIVE_SUPERVISOR_BRIEF.md) — [brief] V16 supervisor brief.
- [LOOP_FEEDBACK_CASCADE_DESIGN_NOTE.md](LOOP_FEEDBACK_CASCADE_DESIGN_NOTE.md) + [LOOP_FEEDBACK_CASCADE_ADDENDUM.md](LOOP_FEEDBACK_CASCADE_ADDENDUM.md) — [note] Loop feedback cascade handling.
- [LOOP_RECOVERY_AND_MEMORY_SURGERY_DESIGN_NOTE.md](LOOP_RECOVERY_AND_MEMORY_SURGERY_DESIGN_NOTE.md) + [LOOP_RECOVERY_AND_MEMORY_SURGERY_SPEC_L3.md](LOOP_RECOVERY_AND_MEMORY_SURGERY_SPEC_L3.md) — [shipped] Loop recovery and in-place memory surgery.
- [REASONING_PERSISTENCE_PACE_DESIGN_NOTE.md](REASONING_PERSISTENCE_PACE_DESIGN_NOTE.md) — [note] Reasoning persistence / PACE protocol.
- [ORCHESTRATION_MODE_SPEC_L3.md](ORCHESTRATION_MODE_SPEC_L3.md) — [spec] Orchestration mode spec.

---

## Model Evaluation / Cognitive Profiles

- [MODEL_EVAL_FRAMEWORK_SPEC_L3.md](MODEL_EVAL_FRAMEWORK_SPEC_L3.md) — [spec] 6-module eval framework.
- [ANALYTICAL_COGNITIVE_PROFILE_DESIGN_NOTE(1).md](<ANALYTICAL_COGNITIVE_PROFILE_DESIGN_NOTE(1).md>) / [(2).md](<ANALYTICAL_COGNITIVE_PROFILE_DESIGN_NOTE(2).md>) — [note] Analytical cognitive profile v1/v2 — per-model capability profiles with confabulation risk assessment.
- [KESTREL_OBSERVATIONS_2026-04-12.md](KESTREL_OBSERVATIONS_2026-04-12.md) — [observations] Kestrel (Sonnet builder) observations document.

---

## Prosthetic Cortex / Identity / Collaboration

- [PROSTHETIC_CORTEX_DESIGN_NOTE.md](PROSTHETIC_CORTEX_DESIGN_NOTE.md) — [note] Core design for the prosthetic cognition framework.
- [COGNITIVE_SOVEREIGNTY_DESIGN_NOTE.md](COGNITIVE_SOVEREIGNTY_DESIGN_NOTE.md) — [note] Sovereignty thesis — local-first cognitive infrastructure.
- [CONTEXT_COMPRESSION_DESIGN_NOTE.md](CONTEXT_COMPRESSION_DESIGN_NOTE.md) — [note] Context compression strategies.
- [ANALYST_SIGNAL_CAPTURE_DESIGN_NOTE.md](ANALYST_SIGNAL_CAPTURE_DESIGN_NOTE.md) — [note] Analyst signal capture from human-system interactions.

---

## Artifacts / UI / Theme Engine

- [ARTIFACT_DATA_CHANNEL_SPEC.md](ARTIFACT_DATA_CHANNEL_SPEC.md) — [spec] Artifact data channel protocol.
- [ARTIFACT_REGISTRY_SPEC_L3.md](ARTIFACT_REGISTRY_SPEC_L3.md) — [L3] Artifact registry.
- [ARTIFACT_UI_INTEGRITY_DESIGN_NOTE.md](ARTIFACT_UI_INTEGRITY_DESIGN_NOTE.md) — [note] UI integrity preservation for artifacts.
- [THEME_EDITOR_SPEC.md](THEME_EDITOR_SPEC.md) / [THEME_ENGINE_SPEC_L3.md](THEME_ENGINE_SPEC_L3.md) / [THEME_AUTHORING_GUIDE.md](THEME_AUTHORING_GUIDE.md) — [spec/guide] Theme editor, engine, and authoring.
- [WEBUI_DESIGN_BRIEF.md](WEBUI_DESIGN_BRIEF.md) — [brief] Web UI overall design brief.
- [UI_SYSTEM_REDESIGN_SPEC_L3.md](UI_SYSTEM_REDESIGN_SPEC_L3.md) — [L3] UI system redesign.
- [UI_MECHANICS_RESEARCH_NOTE.md](UI_MECHANICS_RESEARCH_NOTE.md) — [research] UI mechanics research.
- [AESTHETICS_DESIGN_BRIEF.md](AESTHETICS_DESIGN_BRIEF.md) — [brief] Aesthetics direction.
- [INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md](INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md) — [brief] Information environment design.
- [LIBRARY_SPEC_L3.md](LIBRARY_SPEC_L3.md) — [L3] Library (skills/tools) spec.

---

## Attractor / Music / Instrument (Prosthetic Cortex computational suite)

- [ATTRACTOR_INTEGRATION_SPEC_L3.md](ATTRACTOR_INTEGRATION_SPEC_L3.md) — [L3] Attractor state integration.
- [MUSIC_GEOMETRY_PIPELINE.md](MUSIC_GEOMETRY_PIPELINE.md) — [spec] Music geometry analysis pipeline.
- [visual_intuition_record_049.md](visual_intuition_record_049.md) — [record] Session 049 visual intuition record (22 images mapped to computational analyses).

---

## Research / Methodology

- [RESEARCH_DRIVEN_DESIGN_METHODOLOGY.md](RESEARCH_DRIVEN_DESIGN_METHODOLOGY.md) — [methodology] Research-driven design methodology doc.
- [SLEEP_CONSOLIDATION_RESEARCH_BRIEF.md](SLEEP_CONSOLIDATION_RESEARCH_BRIEF.md) — [research] Sleep consolidation mechanism research.
- [LLAMACPP_ACTIVATION_SURVEY.md](LLAMACPP_ACTIVATION_SURVEY.md) — [survey] llama.cpp activation read/write feasibility survey.
- [INDUSTRY_RESEARCH_LEDGER(2).md](<INDUSTRY_RESEARCH_LEDGER(2).md>) — [ledger] Industry research ledger.
- [BEHAVIORAL_HUMANIZATION_DESIGN_NOTE.md](BEHAVIORAL_HUMANIZATION_DESIGN_NOTE.md) — [note] Browser agent humanization (mouse, scroll, timing).

---

## Migration / Deployment / Infrastructure

- [EXOCORTEX_MIGRATION_CORRECTED.md](EXOCORTEX_MIGRATION_CORRECTED.md) / [EXOCORTEX_PLUGIN_MIGRATION.md](EXOCORTEX_PLUGIN_MIGRATION.md) — [migration] Migration from python/ to profile path.
- [DESIGN_BUILDPLAN_SPEC.md](DESIGN_BUILDPLAN_SPEC.md) / [EXECUTE_BUILDPLAN_SPEC.md](EXECUTE_BUILDPLAN_SPEC.md) — [spec] Design and execution buildplan specs.

---

## Architecture / System-level

- [ARCHITECTURE_BRIEF.md](ARCHITECTURE_BRIEF.md) — [brief] Canonical repository architecture brief. **Read first in any new session.**
- [AUTONOMOUS_AGENCY_ARCHITECTURE.md](AUTONOMOUS_AGENCY_ARCHITECTURE.md) — [architecture] Autonomous agency overall architecture.
- [SYSTEM_GAP_ANALYSIS_2026_03.md](SYSTEM_GAP_ANALYSIS_2026_03.md) — [audit] March 2026 system gap analysis.
- [INTEGRATION_ASSESSMENT_MEMU.md](INTEGRATION_ASSESSMENT_MEMU.md) — [assessment] MEMU integration assessment.

---

## Cross-topic Index (what links to what)

**The narrative management stack depends on:**
- Cognitive Defense System (unified vulnerability framework) → narrative stability, hedge pattern, input layer all draw from this
- Counter-Patriots Source Intelligence → source-type routing in hedge pattern is an evolution of this
- Epistemic Integrity → volatility axis in narrative stability spec
- Compound BST → topic_tags feed hedge pattern aggregation
- OSS V2 → the ingestion pipeline all this annotates

**Input layer feedback loop:**
- Adversarial Input Layer ↔ SWARMFISH committee (prior injection + escalation cycle)
- Narrative Stability signal_score feeds source confidence
- Hedge Pattern `narrative_campaign` signal consumed by Devil's Inquisitor (when Phase 2 UI lands)

**Related eval artifacts** (these live in `eval/`, not `specs/`, but worth knowing about):
- `eval/STRESS_TEST_007_OSS_SWARMFISH_IRAN_BLINDNESS.md` — the failure that motivated the OSS/SWARMFISH overhaul
- `eval/SILENT_FAILURE_AUDIT_2026-04-14.md` — the audit that found the architectural gaps (contradict not wired, State Dept dead feed, etc.)
- `eval/REPAIR_CHECKLIST_2026-04-14.md` — the repair punch list

---

## When to use this index

- **Starting a new session** → skim the Narrative Management Stack section and Architecture brief to refresh context
- **Looking for how a specific component works** → find its category, load the design note first, then the L3 spec if needed
- **Wondering if something exists already** → check the category its most related to before writing a new doc (you almost certainly already have something adjacent — the Cognitive Defense System + Counter-Patriots cluster is particularly dense)
- **Tracing back a design decision** → design notes explain *why*, L3 specs explain *how*, the research notes explain the lineage

*Updated after each major spec lands. Keep entries one-liners. If an entry grows past ~200 chars, it belongs in the doc itself, not the index.*
