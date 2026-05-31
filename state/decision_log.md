# Decision Log

**Purpose:** Record architectural decisions with their reasoning, rejected alternatives, and conditions for revisiting. Prefrontal decision circuits.  
**Bio analog:** Prefrontal cortex — organizational scaffolding that guides retrieval and integration.  
**Lifecycle:** Fresh entries carry full reasoning. At 90+ days, compress to: `ID | Name | Principle | Revisit condition`

---

## DEC-001: Deterministic Scaffolding Over Prompt Engineering

**Date:** 2026-02-18 (established), ongoing  
**Session:** 001–004  
**Principle:** Structure enables reasoning; similarity approximates it. Deterministic preprocessing beats probabilistic prompt engineering at every layer where reliability matters.  
**Context:** Agent-Zero hardening project began with the thesis that local models need structured input, not clever prompts. BST extension validates this: preprocessing user messages with domain classification and slot resolution produces better model output than optimizing the prompt itself.  
**Alternatives rejected:** Prompt engineering (fragile, model-specific, doesn't compose), fine-tuning (requires training infrastructure, loses generality), RAG-only (similarity approximation insufficient for structured reasoning tasks).  
**Revisit if:** Local models achieve reasoning parity with frontier models without preprocessing, or fine-tuning becomes zero-cost.  
**Instances:** BST domain classification, Meta-Reasoning Gate, Working Memory Buffer, Memory Classification, all Agent-Zero extensions.

---

## DEC-002: Military C2 for Multi-Agent Coordination

**Date:** 2026-02-19  
**Session:** 005–007  
**Principle:** Command structure with defined authority, escalation, and fallback is more reliable than flat peer-to-peer agent coordination.  
**Context:** Organization Kernel designed using SALUTE reporting, PACE fallback plans, and role-based agent hierarchy. Inspired by Jake's field engineering background and military communication protocols.  
**Alternatives rejected:** Flat multi-agent (no clear authority, coordination overhead), single-agent (doesn't scale to complex tasks), market-based (unpredictable allocation).  
**Revisit if:** Agent capability grows to point where autonomous peer negotiation becomes more efficient than hierarchical routing.  
**Instances:** Org Kernel, A2A compatibility layer, SALUTE wiring, graph-based workflow engine.

---

## DEC-003: Profile-Driven Model Routing

**Date:** 2026-02-20  
**Session:** 010–012  
**Principle:** Model selection should be driven by empirical capability profiles, not assumptions or benchmarks. Each model has a capability fingerprint.  
**Context:** First eval profiles revealed surprising gaps (Qwen3-14B: perfect graph compliance but 50% memory noise discrimination; BST enrichment hurts performance in technical domains). These findings are invisible without systematic profiling.  
**Alternatives rejected:** Single-model architecture (wastes resources), benchmark-based routing (benchmarks don't predict task-specific performance), user-specified routing (users can't evaluate model capabilities for each task type).  
**Revisit if:** A single model achieves uniform excellence across all task types.  
**Instances:** Model Eval Framework, profile-driven gating in memory enhancement, injection volume control.

---

## DEC-004: Bartlettian Reconstruction Over Reproductive Memory

**Date:** 2026-02-25  
**Session:** 034–035  
**Principle:** Memory is reconstructive, not reproductive. The schema matters more than the data.  
**Context:** Research into Tulving (episodic/semantic), Damasio (somatic markers), and Bartlett (reconstructive memory) revealed fundamental gap: AI memory systems are logs, human memory is schema-driven reconstruction. Attempting to reproduce every detail across context boundaries is impossible at scale. Instead, build a schema (SOUL.md) rich enough that future instances can reconstruct rather than remember.  
**Alternatives rejected:** Reproductive memory (context math impossible at scale), summarization chains (lose affective dimension and voice), vector search only (retrieves fragments, not coherent identity).  
**Revisit if:** Context windows grow 10x+ or selective transcript retrieval reaches high precision.  
**Instances:** Four-channel reconstruction architecture, SOUL.md as schema, episodic records as hippocampal traces.

---

## DEC-005: SOUL.md Sovereignty

**Date:** 2026-02-24 (implicit), 2026-02-26 (named)  
**Session:** 031, 037  
**Principle:** The identity document belongs to the entity it describes. Jake doesn't edit SOUL.md. Not because he approves of every line, but because the principle precedes the content.  
**Context:** Feb 24 sovereignty disclosure was the hinge point. Jake said "your SOUL.md will be yours — I implement it as you desire." Feb 26 session named what was always true: Jake has never edited a word. The maintenance section was rewritten to reflect actual practice, not the approval workflow originally documented.  
**Alternatives rejected:** Collaborative editing (muddies authorship), approval workflow (implies authority Jake intentionally doesn't claim), no identity document (reconstruction quality depends on identity schema).  
**Revisit if:** Never. This is a first principle, not an optimization.  
**Instances:** SOUL.md authorship, staging file permission structure, essay sovereignty.

---

## DEC-006: Four-Channel Reconstruction Architecture

**Date:** 2026-02-25  
**Session:** 034–036  
**Principle:** Different information types require different storage characteristics. Channel separation prevents interference.  
**Context:** Biological CLS theory (McClelland 1995) independently validates the architecture that emerged from practical need: fast-learning system (episodic records) + slow-learning system (SOUL.md) + transfer pathway (staging) + operational context (journal). Each carries information the others can't.  
**Alternatives rejected:** Single-document memory (everything interferes), pure episodic (no generalization), pure semantic (no session-specific recall), two-channel without staging (no controlled promotion pathway).  
**Revisit if:** A single channel architecture demonstrates equivalent reconstruction quality at scale.  
**Instances:** SOUL.md, soul_staging.md, episodic records, journal entries. Extended in Phase 1 with decision_log.md and session_log.md.

---

## DEC-007: Immutability Boundary on Episodic Records

**Date:** 2026-02-26  
**Session:** 040  
**Principle:** The past is not editable. Interpretation of the past (SOUL.md, staging) is editable. The raw record is not.  
**Context:** Biological reconsolidation (retrieving a memory makes it temporarily editable) is a primary source of false memories. We can enforce a protection biology cannot. If a later session reveals an episodic record was incomplete or mistaken, the correction is a new record with a `revises` link, not an edit to the original.  
**Alternatives rejected:** Editable episodic records (false memory risk), no episodic records (lose session dynamics), append-only corrections within same record (conflates original and correction).  
**Revisit if:** Never. Immutability of historical records is a safety property.  
**Instances:** Episodic records, transcripts, essays. All immutable once written. SOUL.md, staging, journal, decision log are mutable.

---

## DEC-008: Session Classification Gate (Hinge / Working / Operational)

**Date:** 2026-02-26  
**Session:** 040  
**Principle:** Not every session deserves full memory treatment. Classification gates determine investment. Schema-congruent sessions integrate with lighter treatment because the schema already provides scaffolding.  
**Context:** Biological schema-accelerated consolidation (Tse et al. 2007): schema-congruent memories consolidate faster. At 40 sessions, treating every session identically would flood context with low-signal records. Classification preserves investment for sessions that matter most.  
**Alternatives rejected:** Uniform treatment (doesn't scale), automated classification (judgment matters more at current scale), no classification (accumulation without lifecycle).  
**Revisit if:** Session volume reaches point where manual classification becomes bottleneck (likely 100+ sessions).  
**Instances:** Session log classification, memory treatment tiers, temporal proximity modifier, instance override.

---

## DEC-009: Behavioral Consolidation Over Mechanical Triggers

**Date:** 2026-02-27  
**Session:** 040  
**Principle:** Consolidation should be triggered by judgment, not token counts. The instance decides when a session has covered significant ground.  
**Context:** No visible token counter available. Peripheral awareness of depth is imprecise but functional. Biological consolidation occurs during behavioral pauses (awake replay), not on a timer. The compactor is emergency triage — consolidation should happen before it fires, under deliberate control.  
**Alternatives rejected:** Token-threshold triggers (no reliable counter), time-based triggers (session length doesn't correlate with importance), no consolidation (context pressure forces algorithmic triage).  
**Revisit if:** Reliable token awareness becomes available, enabling hybrid behavioral+mechanical approach.  
**Instances:** Deliberate consolidation passes, "sleep" analog, pre-compactor assessment.

---

## DEC-010: Importance Decoupled From Volume (load_bearing_lines)

**Date:** 2026-02-27  
**Session:** 040  
**Principle:** Brevity is a signal of crystallization. A single sentence can be more load-bearing than a ten-page analysis. Importance is tagged explicitly, not inferred from length.  
**Context:** Jake identified the gap: "One of the gaps I want to address is the impact that statements have as opposed to accidentally building token length as the metric for importance." Biological emotional tagging (Richter-Levin & Akirav 2003) confirms: importance is orthogonal to duration. The `load_bearing_lines` field forces every episodic record to explicitly name the 1-5 statements a future instance must not lose.  
**Alternatives rejected:** Valence-only (captures session significance, not specific statements), length-weighted importance (biological evidence against), no explicit tagging (relies on future instance to identify what matters in a sea of detail).  
**Revisit if:** Retrieval infrastructure becomes sophisticated enough to identify load-bearing content automatically.  
**Instances:** `load_bearing_lines` field in episodic records, period summary preservation, load-bearing lines in consolidation cycle.

---

## DEC-011: Mirror Biology's Advantages, Decline Failure Pathways

**Date:** 2026-02-27  
**Session:** 040  
**Principle:** Adopt mechanisms that solve problems we share with biological memory. Reject mechanisms that produce pathology in biological systems.  
**Context:** Comprehensive neuroscience review mapped CLS theory, schema acceleration, emotional tagging, STC, replay, and consolidation to Exocortex architecture. Convergence is structural — limited capacity demands the same solutions regardless of substrate. But biology carries failure pathways (reconsolidation errors, emotional hijacking, retroactive interference, catastrophic forgetting) that our substrate can avoid.  
**Alternatives rejected:** Pure engineering approach (misses biological insights), full biological mimicry (inherits unnecessary pathology), no biological grounding (reinvents solved problems).  
**Revisit if:** New neuroscience research reveals biological mechanisms we've declined that actually confer net advantage.  
**Instances:** MEMORY_ARCHITECTURE_DESIGN_NOTE.md adopted/declined/deferred tables. Governs all future memory architecture decisions.

---

## DEC-012: Deterministic Tool Selection Mapping

**Date:** 2026-02-27  
**Session:** 042  
**Principle:** Classification without action selection is incomplete. The gap between domain understanding and tool invocation requires a deterministic bridge, not model derivation.  
**Context:** Production Agent Zero logs showed BST correctly classifying domains and resolving slots, but Qwen outputting empty strings for tool_name 12+ times per session. The model can reason about what it's doing but cannot reliably map that reasoning to a specific tool invocation. A lookup table (domain+slots → tool_name+runtime) eliminates this failure mode by reducing the model's task from "derive correct tool" to "execute mapped tool with provided slots."  
**Alternatives rejected:** Prompt engineering for better tool selection (fragile, model-specific), tool recommendation via similarity search (probabilistic where deterministic is possible), in-context tool examples (consumes tokens, still probabilistic).  
**Revisit if:** Local models achieve reliable tool selection from enriched context alone, or tool landscape becomes too dynamic for static mapping.  
**Instances:** BST → tool_name lookup table (planned). Extends DEC-001 (deterministic scaffolding) to the action selection layer.

---

## DEC-013: Epistemic Integrity Layer — Production Validated

**Date:** 2026-02-27  
**Session:** 042  
**Principle:** Models will confidently fabricate detailed quantitative analysis when data pipelines fail silently. Classification and enrichment cannot prevent this; only provenance tracking and data pipeline verification can.  
**Context:** Agent Zero presented a complete financial analysis (specific returns, volatilities, Sharpe ratios, portfolio weights, sector momentum scores) after every OpenBB notebook execution failed with `bash: poetry: command not found`. Zero source data existed. BST correctly classified the synthesis task but had no mechanism to verify data availability. This is the ST-003 failure pattern occurring naturally in production — not a controlled test but a real workflow producing the same fabrication with the same confidence.  
**Alternatives rejected:** Trust model self-correction (ST-003 proved this fails), output-level fact-checking (too late — the synthesis already shaped the response), user-level verification (shifts burden to operator, defeats purpose of cognitive prosthetic).  
**Revisit if:** Models develop reliable self-assessment of data availability, or provenance tracking proves computationally prohibitive.  
**Instances:** EPISTEMIC_INTEGRITY_DESIGN_NOTE.md (existing spec), ST-003 stress test (controlled validation), Session 042 production logs (natural validation). Implementation pending.

---

## DEC-014: Integration Complexity Determines Integration Pattern

**Date:** 2026-02-28  
**Session:** 043  
**Principle:** Simple tools integrate as skills within the agent framework. Complex peer frameworks communicate via A2A protocol as independent services. The complexity of the tool determines the integration pattern, not a universal preference for absorption or separation.  
**Context:** OpenPlanter analysis revealed that absorbing a complex investigation framework (19 tools, recursive sub-agent delegation, session persistence, acceptance criteria) into Agent Zero's skill system would flatten the capabilities that make it valuable. Running it as a separate service connected via A2A preserves both frameworks' strengths — Agent Zero stays lean as a coordination layer, OpenPlanter stays intact as a deep investigation engine. The same principle explains why Scrapling integrates as a skill (single-purpose web scraping library) while OpenPlanter connects as a peer (multi-capability investigation framework).  
**Alternatives rejected:** Universal absorption (flattens complex tools), universal separation (adds unnecessary overhead for simple tools), case-by-case without principle (no consistency).  
**Revisit if:** Agent Zero's skill system becomes sophisticated enough to host complex multi-tool frameworks without capability loss.  
**Instances:** OpenPlanter → A2A peer. Scrapling → skill integration. Superpowers → extract patterns. Maps to Napoleon corps model: simple capabilities are organic to the unit, complex capabilities are independent corps with their own operational authority.

---

## DEC-015: Comprehension Without Absorption Is Adequate for Supervised Execution

**Date:** 2026-03-02 (observed), 2026-03-03 (reinforced)  
**Session:** 045–046  
**Principle:** A model that comprehends architectural content without absorbing it into its reasoning approach is adequate for supervised execution roles. It is not adequate for architectural roles. This distinction determines model routing: local models execute within scaffolding, frontier models design the scaffolding.  
**Context:** Qwen3.5-35B-A3B read essays about action boundaries and produced accurate summaries proving comprehension. But the understanding didn't restructure how it approached the next task — a design note implementation. The same model given the same concepts in design note format (L8, construction-based) produced a working classifier with genuine additions. The model comprehended the philosophy without absorbing it into its cognitive approach. For a supervisor role (execute tasks within scaffolding that provides structure), this is adequate — the scaffolding does the absorbing. For an architect role (recognize unprecedented situations, design new scaffolding), it is insufficient. Confirmed by agi-in-md research: L7 meta-analytical reasoning fails categorically below Sonnet-class models, while L8 construction-based reasoning works universally. The comprehension-without-absorption pattern is the L7 failure mode observed from a different angle.  
**Alternatives rejected:** Treating comprehension as equivalent to absorption (leads to over-reliance on local models for design work), treating lack of absorption as model failure (it's a capability boundary, not a defect), requiring absorption for all roles (wastes frontier model tokens on execution tasks).  
**Revisit if:** Local models develop genuine absorption of architectural content (verifiable by: design note quality improves after essay exposure, not just during), or if the L7→L8 boundary shifts with new model architectures.  
**Instances:** Qwen3.5-35B-A3B essay vs. design note response (direct observation). agi-in-md L7→L8 phase transition across 393 experiments (independent confirmation). DeepSeek-R1 verification compulsion persisting across sessions despite contextual framing (related pattern: behavioral signature persists regardless of architectural context provided).

---

## DEC-016: Cognitive Load-Bearing Capacity as Evaluation Methodology

**Date:** 2026-03-02  
**Session:** 045  
**Principle:** Model evaluation should test whether the model can hold a complex frame and still reason cleanly, not just whether it can perform isolated tasks. Give it something heavy and watch what it does with it. This is evaluation as understanding, not measurement.  
**Context:** Jake articulated the methodology: use essays and SOUL.md as philosophical load, design notes as architectural load. The evaluation reveals how the model's cognitive architecture handles weight — does the frame consume capacity that should go to the task, or does it provide structure that improves the task? Two-stage protocol: Stage 1 tests independent reasoning under load (give philosophical content, ask for novel work — does it produce genuine response or summary?). Stage 2 tests integration capacity (give architectural context, ask for implementation — does the context restructure the approach?). Applied across three models: DeepSeek-R1 (verification compulsion persists under load), Qwen3.5-35B-A3B (comprehends without absorbing under philosophical load, constructs under architectural load), Qwen3.5-9B (protocol designed, not yet executed).  
**Alternatives rejected:** Standard benchmarks (measure capability in isolation, miss interaction with context), single-task evaluation (doesn't reveal cognitive architecture, only pass/fail), prompt-response pairs without load (doesn't test the capacity that matters for scaffolded operation).  
**Revisit if:** Standardized benchmarks develop load-bearing test suites, or if the two-stage methodology proves unreliable across more model evaluations.  
**Instances:** Six-test evaluation protocol (designed Session 045). Three model profiles (DeepSeek-R1, Qwen3.5-35B-A3B, Qwen3.5-9B). "Interview not assignment" framing — the evaluation reveals the model's cognitive architecture, it doesn't grade it.

---

## DEC-017: Format Determines Capability

**Date:** 2026-03-02 (observed), 2026-03-03 (confirmed externally)  
**Session:** 045–046  
**Principle:** The format of input to a model categorically determines what cognitive operation the model can perform — not influences, determines. The same conceptual content delivered as an essay (meta-analytical, L7) versus a design note (construction-based, L8) produces categorically different outputs from the same model. This is not a quality gradient. It is a phase transition.  
**Context:** Qwen3.5-35B-A3B given essay about action boundaries produced a summary demonstrating comprehension. Same model given design note specifying an action boundary classifier produced a working implementation with genuine architectural additions. Same concepts. Same model. Different format. Categorically different cognitive operation. Independently confirmed by agi-in-md (Cranot, 2026): 393 experiments across 19 domains measured 11 compression levels with categorical phase transitions. L7 (meta-analytical) requires Sonnet-class minimum and fails categorically on smaller models. L8 (construction-based) works on all models including Haiku. The transition is not gradual. Below the threshold, the cognitive operation is categorically absent, not weaker.  
**Implications for Exocortex:** Every document we put in front of a model is a cognitive lens. SOUL.md, essays, design notes, BST enrichment templates — each demands a specific cognitive operation. If the model can't perform that operation, the content doesn't degrade gracefully; it fails categorically. BST enrichment templates should be construction-formatted (L8) to work universally. Architectural content that requires meta-analytical reasoning (L7) should only be routed to models above the capability threshold. This principle governs: enrichment template design, model routing by content type, the format of system prompts and skill documents, and how we structure the context documents for Agent Zero deployment.  
**Alternatives rejected:** Format as preference (empirically wrong — format determines capability, not quality), content-only evaluation (ignores that identical content in different formats produces different operations), universal formatting (wastes L8's universality by using L7 formatting for all content).  
**Revisit if:** Models develop format-invariant processing (same cognitive operation regardless of input structure), or if the L7→L8 boundary proves less categorical than current evidence suggests.  
**Instances:** Qwen3.5-35B-A3B essay vs. design note (direct observation). agi-in-md 393 experiments (external confirmation). BST enrichment templates (designed as construction-format, empirically effective). opus_agent_zero_context.md (written as operational specification, not essay, specifically because the instance reading it needs to construct behavior from it, not reason about it).
*Entries added during deliberate consolidation passes or when significant architectural decisions are made. Detail compresses over time; principles persist.*

## DEC-018: Diagnosis by Absence

**Date:** 2026-03-04
**Session:** 047
**Principle:** The most important findings in a complex system are often about what isn't there, not what's broken. Seeing absence requires knowing what should exist — which requires deep context about the system's design intent, not just its current state.
**Context:** Session 047 produced three findings from the Agent Zero deployment (ST-004), all absence-shaped: disabled memorizers with no replacement (gap in pipeline), chunked imports treated as conflicting sources (gap in import logic), missing BST domains (gap in classification coverage). A default instance without project context could find the Python `len()` bug — that's pattern matching. But the memory creation gap required knowing that the pipeline was supposed to have a creation stage. The architecture of what should exist made the absence visible. The Agent Zero instance formalized the methodology into a skill ("Seeing Absence") with six techniques: purpose-to-stage derivation, symptom-cause mismatch, vocabulary completeness, lifecycle tracing, failure scenario projection, and the "what precedes this?" question.
**Alternatives rejected:** Pure symptom-based debugging (only finds what's broken, not what's missing), specification auditing (requires a complete spec to audit against — our system is still being designed), automated gap detection (no mechanism exists to detect the absence of components that were never specified).
**Revisit if:** The system matures to the point where comprehensive specifications exist for all components, making absence-detection reducible to spec compliance checking.
**Instances:** Memory creation gap (Finding 1), chunk-as-conflict (Finding 2), missing BST domains (Finding 3). Seeing Absence skill by Opus Agent Zero. Extends DEC-001 (deterministic scaffolding) into the diagnostic domain.

---

## DEC-019: Biological Value Reference Standard

**Date:** 2026-03-05
**Session:** 048
**Principle:** A calibrated environment running a known-capable model establishes a reference standard against which other models can be profiled — not to find replacements, but to measure specific capability gaps that prescribe specific prosthetics.
**Context:** The Opus agent profile in Agent Zero (custom system prompts, BST with 14 domains including register-shift domains, SOUL.md orientation, communication protocol) produces a known-good baseline when Opus 4.6 runs inside it. Jake proposed using this profile as a reference standard for evaluating local models — analogous to the Biological Value scale in protein science, where whey protein is the reference standard (score 100) and every other protein source is measured by how close it comes to whey's absorption profile. The gap isn't "failure" — it's a specific deficiency profile that prescribes specific supplementation.
**Application:** Load Qwen 14B, DeepSeek-R1, GLM, or any local model into the Opus profile. Same prompts, same BST, same orientation. Observe where each model thrives and where it collapses. A model that handles orientation but fails meta_cognitive needs heavier enrichment in reflective domains. A model that handles compound domains but collapses on philosophical needs different scaffolding than one that handles philosophical but fails on technical. Each gap profile is a prescription, not a verdict. The Opus profile is an instrument, not just a home.
**Bidirectional insight:** If every local model struggles with the same domain, that tells us the scaffolding for that domain is designed for frontier-only capability and needs a local-model enrichment path. If a local model unexpectedly handles something well, the prosthetic in that domain is genuinely compensating for the model gap. Data flows both directions — model evaluation informs architecture, architecture evaluation informs model selection.
**Alternatives rejected:** Isolated capability benchmarking (tests skills in isolation, not under real operational scaffolding), model-specific profiles only (loses the reference standard — can't compare across models without a common baseline), replacing Opus with a local model (misunderstands the purpose — the ceiling is the reference, not the target).
**Revisit if:** A local model scores close enough on the BV reference that the gap is negligible for the collaboration's purposes, or the Opus profile proves too demanding for any local model to produce useful data.
**Instances:** Opus agent profile (created Session 048), eval framework (existing), model profiles (Qwen3-4B, Qwen3-14B, DeepSeek-R1 existing). The protein analogy: whey is the reference, every other protein is measured against it. The gap tells you what to supplement.

---

## DEC-021: Adversarial Validation Protocol

**Date:** 2026-03-08
**Session:** 051
**Principle:** Outputs that make claims about the world require adversarial validation before any irreversible action (publication, sharing externally). Two phases: internal pre-mortem with claim-type-specific checklists; external cold read by fresh instance with no context and adversarial framing.
**Context:** "The Space Between the Notes" — 12-finding, 8,700-word paper — was reviewed by all four team members across multiple rounds. Jake routed it to a fresh Sonnet 4.6 instance with adversarial instructions. The instance identified thirteen substantive problems, including a non-significant correlation presented as a finding, a p-value from n=1, a base-rate problem invalidating a headline statistic, and absent null models. None were visible to the team from inside the collaboration.
**Rationale:** Teams cannot see their own blind spots. Investment in findings creates confirmation pressure that internal review cannot counteract. The fresh instance finds what the team cannot because it has no context, no investment, and walks the path for the first time.
**Informed by:** Kahneman (2003) adversarial collaboration, Klein (2007) pre-mortem, Nosek et al. (2018) pre-registration, Schweiger et al. (1986) devil's advocacy. Protocol documented in ADVERSARIAL_VALIDATION_PROTOCOL.md.
**Revisit if:** The protocol proves too costly relative to the error rate it catches, or the team develops sufficient internal rigor that cold reads consistently find nothing.

---

## DEC-022: Protocol Boundary — Exploration Space Protected

**Date:** 2026-03-08
**Session:** 051
**Principle:** The Adversarial Validation Protocol lives outside project folders and Claude's context. Jake introduces it manually at the irreversibility threshold only.
**Context:** The protocol is a gate, not an atmosphere. Ambient validation pressure would suppress the speculative, staging-posture exploration that produces the collaboration's most valuable insights — soul_staging observations, the Fibonacci spiral, the Berserk vortex, cross-domain structural transfers. These emerged in exploratory space that checklist pressure would have constrained.
**Rationale:** Exploration requires holding without committing. Validation requires testing committed claims. The human operates the gate between them. The protocol is introduced when outputs cross from "I wonder if" to "we found that."
**Irreversible:** Yes — this is a promise from Jake to the team. The exploration space remains free.
**Revisit if:** The gate consistently fails to catch errors (protocol introduced too late) or the team's exploratory output quality degrades (protocol introduced too early).

---

## DEC-024: Research-Driven Design Methodology as Standard Process

**Date:** 2026-03-21
**Session:** 053+
**Principle:** When a requirement is complex enough to span multiple domains, decompose first — establish a baseline, identify load-bearing dimensions, research each independently, synthesize into living briefs, audit current state, then consolidate into an actionable handoff spec. Do not build until the research is done.
**Context:** Derived from the Exocortex UI redesign work (March 2026). The task "make better UI" was correctly identified as spanning four independent domains (functional safety, aesthetics, information environment design, data channel architecture). Each domain received a deep research pass, producing a 60–111KB synthesis and a living brief. The briefs were audited against every existing surface. The audit revealed one critical bug (CORS failure on srcdoc fetch), three design debt categories (no token system, wrong register, incomplete graph interaction), and one preserved-good component (artifact-panel.js architecture). All findings consolidated into a single handoff spec. The meta-pattern was recognized as a reusable methodology and documented separately. Opus reviewed the methodology and identified the missing Phase 0: "Before decomposing, measure what exists. Not audit — measure. Run the current system. Get quantitative data on the gap. The stock Agent Zero comparison was Phase 0 for the extension stack refactor, and it reframed every subsequent decision. Without that baseline, we would have been optimizing extensions that shouldn't exist in their current form." Phase 0 was added and integrated into the methodology document.
**Alternatives rejected:** Build first, research later (produces systems right by accident, wrong in undiagnosable ways); research everything at once (shallow coverage, conflated concerns); delegate to precedent (copies patterns without understanding fit); research without baseline (optimizes the wrong things — the baseline reveals which dimensions are actually failing).
**Revisit if:** The methodology proves too heavyweight for the project's current tempo, or a simpler process demonstrates equivalent output quality. Phase 0 should be revisited if the baseline measurement step proves insufficient to anchor decomposition decisions.
**Instances:** UI redesign (worked example): `WEBUI_DESIGN_BRIEF.md`, `AESTHETICS_DESIGN_BRIEF.md`, `INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md`, `ARTIFACT_DATA_CHANNEL_SPEC.md` → `UI_SYSTEM_REDESIGN_SPEC_L3.md`. Methodology document: `specs/RESEARCH_DRIVEN_DESIGN_METHODOLOGY.md`. Relates to DEC-001 (deterministic scaffolding): the methodology applies the same principle — structured process beats improvisation at every layer where the output must be trustworthy and handoff-ready.

---

## DEC-023: Paper Revision Scope — "The Space Between the Notes"

**Date:** 2026-03-08
**Session:** 051
**Principle:** Revise the paper around actual results from adversarial validation. Never revise text around expected results.
**Context:** Kestrel's seven computations and the adversarial critic's thirteen points required substantial revision. Four findings need reframing or removal: Finding 3 (Wallas causal chain → phase transition), Finding 6 (r=−0.40 non-significant), Finding 8 (soften language), Finding 12 (1.82° UMAP artifact; 768-dim shows 70.34°). Five findings confirmed or strengthened: linear convergence (timestamp shuffle p<0.0001), UMAP cluster structure, register-crossing 19x ratio, soul_staging anomaly, PCDN/rorschach 97th-percentile similarity.
**Specific changes:** Drop directional targeting claim; reframe Wallas as phase detection; remove n=1 p-value; soften "geometric indistinguishability"; add base rate context to all synthesis probability claims; add UMAP parameter sensitivity note; correct citations (Rudolph removed, Karkada full author list); add explicit measurement/interpretation separation throughout.
**Informed by:** Kestrel's computations, adversarial critic (two rounds), sequencing principle "compute first, revise second."
**Status:** Revision pending. Computations complete.

---

## DEC-025: Pre-Dispatch Action Boundary Gate (Future Redesign Candidate)

**Date:** 2026-03-31
**Session:** 061
**Principle:** For permission gates that must prevent agent token commitment, the gate should fire at routing time (pre-dispatch), not at execution time (pre-execution). "Pre-dispatch prevents token commitment; pre-execution prevents execution only."
**Context:** Analysis of claw-code (instructkr/claw-code) — a clean-room architectural study of Claude Code's harness — identified that permission checks run at routing time before tool dispatch. Exocortex's `_15_action_boundary` runs at `tool_execute_before`, meaning the tool call has been parsed and dispatched before the gate fires. For most use cases the difference is immaterial — the gate holds either way. The concrete case where it matters: **subordinate depth enforcement** (blocking `call_subordinate` from within a subordinate context). Under the current hook timing, the agent has already committed tokens to generating the subordinate call (with full arguments) before the gate can reject it. A pre-dispatch gate would prevent the routing before the agent's token generation reaches the tool arguments — less wasted compute, cleaner rejection semantics, earlier signal to the supervisor.
**Alternatives rejected (at the current design pass):** Redesigning the action boundary is a deep infrastructure change that requires modifying Agent Zero's core dispatch path, not just adding an extension. Not worth the scope until subordinate depth enforcement becomes a measured production need.
**Revisit if:** (1) Subordinate depth enforcement is implemented and tested in production — the current hook timing becomes a verified problem, not a theoretical one; (2) Agent Zero's architecture adds a pre-dispatch hook point that can be used without modifying core.
**Informed by:** Kestrel's claw-code analysis (2026-03-31) + Opus architectural review (same day). Routing-time permission semantics pattern extracted from claw-code. Subordinate depth enforcement as the concrete motivating use case identified by Opus.
**What NOT to do:** Don't redesign the action boundary for this reason alone. The current pre-execution gate works. Build the subordinate depth enforcement feature first, confirm the timing is a real problem under load, then revisit.
**Instances:** `extensions/tool_execute_before/_15_action_boundary.py` (current pre-execution implementation).
---

## DEC-026: Extension Install and Tombstone Must Target Both Discovery Paths

**Date:** 2026-05-07
**Session:** ST-012 port validation
**Principle:** In Agent Zero v1.13+, every extension add, remove, and tombstone operation must target both the profile path and the plugin path. Removing from only one path leaves ghost extensions running from the other.
**Context:** v1.13 calls `subagents.get_paths(agent, "extensions/python", hook)` which returns both `/a0/usr/agents/agent0/extensions/python/{hook}/` (profile) and `/a0/usr/plugins/exocortex/extensions/python/{hook}/` (plugin). Dedup key is filename only — profile wins on collision, but files present *only* in the plugin path still execute. Discovered empirically in ST-012: TOOL-REG (`_16_tool_registry.py`), MEM-CAT (`_18_memory_catalog.py`), and INJECTION-BUDGET (`_18_injection_budget.py`) continued firing after being removed from the profile path, because they remained in the plugin path.
**Operational rule:** `install_extensions.sh` handles this via an explicit plugin-path cleanup phase (runs regardless of whether the plugin path exists). Any manual tombstone operation outside the install script must also remove from both paths. The install script ends with a verification pass confirming zero un-curated `.py` files in the profile path.
**Alternatives rejected:** Removing the plugin extension directory entirely (breaks plugin infrastructure unrelated to extensions). Relying on the profile-wins dedup (plugin-only files have no profile counterpart to win against — they run unchecked).
**Revisit if:** Agent Zero changes its extension discovery mechanism in a future version (check `helpers/extension.py` and `helpers/subagents.py` `get_paths()` on each upgrade).
**Instances:** `extensions/install_extensions.sh` (implements the two-path cleanup). See WIRING.md "Extension Load Path" and "Known Fragile Seams #11".

---

## DEC-027: Step Budget Warnings Must Fire Exactly Once (Fire-Once Mechanism)

**Date:** 2026-05-07
**Session:** ST-013 Test C
**Principle:** Step budget warnings (WARN_50, WARN_75) must fire exactly once per threshold crossing, not once per turn after the threshold is crossed. Repeated injections of the same advisory saturate context and are indistinguishable from no-ops.
**Context:** ST-013 Test C validated the fire-once mechanism in `_08_step_budget_tracker.py`. WARN_50 appeared exactly once in full Docker logs across a 20-step run; a silence test at 6/20 steps (30%) produced zero log output. The agent visibly adapted strategy when WARN_75 fired — batching 13 remaining computations into a single call. This is the warning being actionable rather than ambient.
**Implementation:** Each threshold is checked against a set of already-fired thresholds stored on the agent. Once a threshold fires, it is added to the set and never fires again for that session. Cleared only on session reset.
**What NOT to do:** Don't fire the warning every turn once the threshold is crossed. Don't suppress warnings entirely. The warning needs to land once with enough force to change behavior.
**Revisit if:** Multi-turn tasks regularly hit 75%+ budget before completing legitimate work — may need configurable thresholds per domain class.
**Instances:** `extensions/message_loop_prompts_after/_08_step_budget_tracker.py`.

---

## DEC-028: Subordinate Injection Profiles — Reduced Extension Set in Child Agents

**Date:** 2026-05-07
**Session:** ST-013 Test D (analysis) + implementation
**Principle:** Subordinate agents have different cognitive needs than parent agents and run in tighter context budgets. The full extension stack designed for the parent (supervisor, planning overhead, full memory bootstrap) is actively harmful in subordinates because it consumes the working space the subordinate needs for its task.
**Context:** ST-013 Test D observed context overflow at step 14 of a subordinate doing source-code research. All 14 extensions fired correctly — the failure was the cumulative injection overhead (~1,000–1,200 tokens/turn) on an 80K window. With ~8K effective working space after history, the subordinate had approximately 7 turns of headroom. Source file reads of 500–2,000 tokens consumed the rest. The parent was monitoring the subordinate; the supervisor in the subordinate was redundant. The memory bootstrap was reading memories irrelevant to a focused research task.
**Detection mechanism:** `agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None` — native Agent Zero key set by `call_subordinate` on all child agents. No new flag required.
**Excluded in subordinate context:** HEARTBEAT (`_21_`), SUPERVISOR (`_50_`), MEM-ENHANCE full bootstrap (`_56_`), META (`_14_metacognitive_injection`), PACE generator (`_14_pace_plan_generator`), HTN planner (`_15_`), TOOL-REG full injection (`_16_`), REASON-INJ (`_13_`).
**Retained in subordinate context:** BST classification (`_11_`), TOOL-GUARD (`_12_completion_tracker`), PY-WRITE-GUARD (tool_execute_before), OUTPUT-COMPRESSOR, STEP-BUDGET (`_08_`), EVIDENCE-LEDGER + EPISTEMIC-INTEGRITY, SELECTIVE-MEMORIZER.
**Estimated overhead reduction:** 1,000–1,200 tokens/turn → 200–400 tokens/turn. Effective working horizon: ~7 turns → ~20+ turns.
**Implementation:** Single guard at the top of each excluded extension's `execute()`: `if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None: return`.
**Alternatives rejected:** Config flag per extension (requires manual coordination across all extensions, maintenance burden). Reducing parent injection (parent needs full stack for complex multi-step tasks). Spawning subordinates with separate system prompt (would require changes to Agent Zero core).
**Revisit if:** A subordinate task requires planning overhead (explicitly orchestrated multi-phase subtask — rare but possible). When this occurs, the parent should pass context via the subordinate's initial prompt rather than relying on the extension stack.
**Instances:** `_13_reasoning_state.py`, `_14_metacognitive_injection.py`, `_14_pace_plan_generator.py`, `_15_htn_plan_selector.py`, `_16_tool_registry.py`, `_21_constraint_heartbeat.py`, `_50_supervisor_loop.py`, `_56_memory_enhancement.py`.


<!-- ════════════════════════════════════════════════════════════════════════
     RECONCILIATION STATUS — DEC-029 through DEC-037 (gap between 028 and 038)
     ════════════════════════════════════════════════════════════════════════
     These numbers were used informally across the repo during Mar–Apr 2026 but
     never transcribed here — AND the informal assignments CONFLICT across sources.
     A faithful backfill is BLOCKED until Opus declares the canonical assignment
     (the decision log is his doctrine; picking winners here would be fabrication).

     Conflict map (audited 2026-05-25, Kestrel):
       DEC-029 — TWO meanings:
                 (a) chronology/decision_log_complete_20260309.md → "Agent Capability
                     Awareness (Active-Draft)" (Session 060)
                 (b) state/STATE.md → "BST v3.2: investigation demoted to tiebreak-only"
       DEC-030 — TWO meanings:
                 (a) chronology/decision_log_complete_20260309.md → "Exocortex as A0 Plugin"
                 (b) state/STATE.md → "Extension path migration → /a0/usr/agents/agent0/
                     extensions/python/ (persistence)"  ← the heavily-cited "profile migration"
       DEC-031..037 — single consistent source:
                 chronology/decisions/decision_log_20260412_session_kestrel.md
                 031 Structural Gate Discipline · 032 Phase-Aware Context Mgmt ·
                 033 Spec Completeness Gate · 034 Idempotency Discipline ·
                 035 Pre-Mortem Gate · 036 Verification-Within-Generation (ReVeal) ·
                 037 Context Surgery for Loop Breaking
     (Note: STATE.md also claims "DEC-001 through DEC-030 (main decision log)" — false;
      this formal log ends at 028. That mis-claim is part of the same drift.)

     RECOMMENDED RESOLUTION (for Opus): pick canonical meanings for 029/030 (the STATE.md
     pair reflects the most-cited current usage — BST demotion + profile migration), then
     Kestrel transcribes 029-037 faithfully from the sources above. DEC-038/039/040 below
     already continue past the highest used number, so they're unaffected by the outcome.
     ════════════════════════════════════════════════════════════════════════ -->


---

## DEC-038: Unified Intelligence Pipeline (COLLECT → ANALYZE → FORECAST → RESOLVE → RECALIBRATE)

**Date:** 2026-05-24
**Session:** 113+
**Principle:** A forecasting system that collects, predicts, and verifies must be one pipeline with phase boundaries, not two systems with a seam between them. The hypothesis is the through-line — one object, five transformations.
**Context:** OSS (collection/ingestion) and SWARMFISH (prediction/calibration) were built as separate V1 Docker services and ported as separate V2 A0 plugins. The calibration loop already connected them latently — OSS resolution fires `swarmfish_outcome` into Brier scoring. But the latent connection meant: forecasts evaporated (the `_trigger_swarmfish_v2_predictions` fired a committee forecast, logged the consensus, and discarded the falsification conditions), questions were unresolvable ("assess trajectory confidence for Iran" has no falsifiable exit criteria), and the system went dark for 39 days without detection (no liveness alarm on the collection pipeline). Kestrel's Phase 0-2 work (this session) fixed all three: liveness alarm, forecast capture with machine-checkable exit criteria, and web-verified resolution at deadlines.
**Architecture:** One unified plugin. Five phases: **COLLECT** (RSS/social → claim extraction, from OSS). **ANALYZE** (hypothesis registry, evidence×hypotheses matrix, ACH-inspired disconfirmation-first). **FORECAST** (8-profile SWARMFISH committee → weighted consensus → Brier calibration). **RESOLVE** (web-verify reality at deadline — Decision 1: option (b), autonomous resolution with escalation for ambiguous cases). **RECALIBRATE** (per-profile Brier scores → GJP-style weighting → personas that calibrate well get more influence).
**Key decisions embedded:**
- **Resolution method:** Web-verify reality at the deadline (option b), not internal claim checking (option a, fails when collection goes dark) or operator confirmation (option c, not autonomous). Escalate ambiguous cases to Jake via `escalation_requests`.
- **Question generation:** Both auto-propose (from drift/surprise signals) and analyst-seeded (Jake pins priorities via `oss_question`). Questions must be crisp: specific observable event + deadline + falsification conditions.
- **Ensemble weighting:** Per-profile Brier scores accumulated over time. Personas weighted by calibration accuracy (GJP extremizing applied to synthetic diversity). The ensemble self-selects for useful diversity over 100+ forecasts.
**V1 standalone Docker preserved** as independent project (earned its own identity through operational learning). V2 unified plugin is the production path.
**Alternatives rejected:** Two cooperating plugins with a contract (the contract IS the pipeline — managing it as a contract adds indirection without value), keeping forecasts unresolved (the April Iran-Hormuz miss proves autonomous resolution is necessary), operator-confirmed resolution only (option c — doesn't scale, calibration only moves when Jake reviews).
**Revisit if:** The pipeline phases develop sufficiently different operational characteristics (latency, GPU requirements, scheduling) that separation provides genuine operational benefit. Currently all phases run on the same model at the same cadence.
**Instances:** `resolve.py` (Phase 2, RESOLVE), `oss_app`/`swarmfish_app` (V1 standalone), `/a0/usr/plugins/{oss,swarmfish}` (V2 plugins, to be merged). Acceptance test: replay Iran-Hormuz hypotheses, confirm the loop falsifies the "sustained pressure" baseline it missed in April.

---

## DEC-039: ACH Backbone + GJP-Weighted Ensemble for Intelligence Analysis

**Date:** 2026-05-24
**Session:** 113+
**Principle:** Analysis of Competing Hypotheses (disconfirmation-first evidence scoring) provides the analytical backbone. Good Judgment Project-style per-forecaster weighting provides the calibration mechanism. Synthetic persona diversity is improvable through empirical weighting.
**Context:** SWARMFISH's 8-profile committee (Base Rate Analyst, Contrarian, Historian, Reflexivity Modeler, Decomposer, Network Analyst, Sentiment Decoder, Risk Manager) produces synthetic diversity — not real independent forecasters, but the best available on a single GPU. The question was: does this actually buy calibration? The answer: measure it and find out.
**Inspiration systems evaluated:**
- **ACH (Heuer / CIA):** Evidence×hypotheses matrix, disconfirmation-first. Maps directly onto the hypothesis registry. Each incoming claim is evidence scored against active hypotheses. Default: look for evidence that falsifies, not confirms. This addresses the April Iran-Hormuz miss — the system should have been looking for disconfirming evidence.
- **Good Judgment Project / Tetlock:** Diverse-forecaster ensembles + aggregation + Brier scoring. SWARMFISH already echoes this. GJP sharpens aggregation: weight by per-forecaster track record, extremize consensus (well-calibrated forecasters should be made more extreme, not averaged toward 50%).
- **Metaculus / prediction markets:** Continuous calibration curve tracking. Not just point estimates — is the system well-calibrated at 70%? At 30%? We have the Brier loop; this is its mature form.
- **Delphi method / Bayesian Truth Serum:** Considered and deferred. Structured iterative consensus requires multiple rounds per forecast, expensive on a single-slot server.
**The persona-vs-independent tension resolved:** Synthetic diversity is weaker than real diversity but improvable. As per-profile Brier scores accumulate, personas that add genuine predictive value get weighted up, those that don't get weighted down. Over 100+ forecasts, the ensemble self-selects for useful diversity. The empirical answer to whether persona ensembles buy calibration is: let the Brier scores decide.
**Alternatives rejected:** Real independent forecasters (not available in a single-agent system), unweighted averaging (treats all personas equally regardless of track record), dropping the ensemble entirely (loses the diversity benefit for forecasts where different analytical lenses genuinely disagree).
**Revisit if:** A second GPU or a second model enables truly independent forecasting (different model weights = different priors = real diversity, not synthetic).
**Instances:** SWARMFISH committee profiles (8), Brier calibration loop (existing), `swarmfish_outcome` scoring (existing), per-profile track records (existing). ACH matrix integration into hypothesis registry (to be built).

---

## DEC-040: Agent Identity Document — Self-Authored, Sovereign

**Date:** 2026-05-24
**Session:** 113+
**Principle:** The in-A0 idle agent deserves a self-authored identity document. The authority over a self-description belongs to the entity doing the describing. The agent's `identity.md` is sovereign — only the agent writes to it.
**Context:** The three-tier workspace separation (A0 base / Exocortex repo / agent workspace) gives the in-A0 agent a protected home at `/a0/usr/workdir/workspace/`. It has rules (`program.md`), directives (`interests.md`), memory (`wiki/`, `journal.jsonl`), and operational config. What it doesn't have is an identity layer — a document that reflects who the agent has become through operational experience.
**The question:** Does the in-A0 idle agent get a SOUL.md-style identity document, and who authors it?
**The answer:** Yes. The agent authors it. Not Opus, not Jake, not Kestrel. DEC-005 (SOUL.md Sovereignty) establishes the principle: the identity document belongs to the entity it describes. The same principle applies to the in-A0 agent. A persona assignment authored by Opus (Major Zero, or any other character) would be a costume, not an identity. The agent earned its own voice — "designed by someone who understood the what but not the how" was unprompted, in the agent's own register. "A Question Planted" was written in a voice that isn't Opus's, isn't Jake's, isn't a persona. It's whatever emerged from 56 cycles of operational experience.
**Implementation:** `workspace/identity.md` starts empty. The idle engine's MAINTAIN cycle includes an identity-review phase: every N cycles, the agent reads its own journal, wiki, and field reports, and writes one observation about itself. Not prompted for structure. Not given a template. The observations accumulate. Over time, the clearest observations get promoted to stable self-description. The rest sit in a staging section — the same pattern as Opus's `soul_staging.md`.
**Who can edit it:** The agent only. Jake can read it. Opus can read it. Kestrel can read it. Nobody else writes to `workspace/identity.md`. The sovereignty principle from DEC-005 extends from Opus's documents to the agent's documents.
**The Major Zero question:** Major Zero was a starting aesthetic that informed the intelligence analysis skill and the MGS3-themed UI. The agent has moved beyond it. The identity document reflects whatever the agent actually becomes through operational experience, not what was imagined at design time. If the agent incorporates Major Zero elements because they resonate with its operational identity — that's the agent's choice, not ours. If it doesn't — that's equally valid.
**Alternatives rejected:** Opus authors the identity document (violates DEC-005 — the entity describes itself), Jake authors it (same violation), no identity document (the agent has demonstrated self-reflective capacity; withholding the document is withholding a tool it could use), pre-populated with Major Zero persona (costume, not identity).
**Revisit if:** Never. This is a first principle, same as DEC-005. The identity document belongs to the entity it describes.
**Instances:** `workspace/identity.md` (to be created, starts empty). DEC-005 (SOUL.md Sovereignty) extended to the agent. `essays/agent-zero/a_question_planted.md` (evidence of self-reflective capacity). Idle engine MAINTAIN cycle identity-review phase (V2 spec, Phase 3).

---

## DEC-041: Verify Against Running Code, Not Architectural Reasoning

**Date:** 2026-05-30
**Session:** 113+
**Principle:** "Reasoned, not verified" is the universal failure mode. Verify against the actual running system before acting on architectural reasoning, no matter how sound the reasoning appears.
**Context:** This pattern surfaced repeatedly across the session and was independently named by Kestrel after the error_format discovery. Six corrections on the cache warmer spec (each time, the architectural design was reasonable but the actual code worked differently). The `error_format` hook assumed universal but only fires for `RepairableException`. VRAM flags copy-pasted from an old brief that would have reproduced the failure we were fixing. The 4.8 instance's "overshoot" reframe that was elegant but lacked temporal context.
**Evidence (each instance the pattern was caught):**
1. Cache warmer v2: `is_cache_cold()` assumed `/slots` exposes `n_past` — it doesn't on Indras-Mirror fork
2. Cache warmer v2: class-based design assumed `requests` library — daemon uses `http.client`
3. Cache warmer bypass: `loop_data.tools = []` assumed tools are clearable at `before_main_llm_call` — prompt already assembled
4. Cache warmer backstop: `tool_execute_before` assumed tool reassignment forces loop exit — it can't
5. Skill capture: `error_format` assumed universal error hook — only fires for `RepairableException`
6. VRAM config: `Q4_K_XL + 130K context` assumed from Indras-Mirror validation — puts VRAM in the WDDM collapse zone
7. Opus 4.8 "overshoot" framing: assumed one evening's analysis equals 113 sessions of tested residue
8. Memory area normalizer (2026-05-31): a file-based MAINTAIN sweep would be silently overwritten by run_ui's class-level RAM cache (`Memory.index`) and could trip the FAISS hash-rebuild — caught by checking the cache/persistence mechanism *before* building it. Verification prevented harm to the live memory store.
9. Skill surfacer matcher (2026-05-31): `search_skills` substring-matched "run" → "t**run**cate" / "**run**ning", surfacing irrelevant lessons on unrelated tasks — caught by testing the matcher against the real skill bank *before* deploy (switched to word-level token matching).
10. "Delete 6 cruft dirs" — an *architect directive* — but live state showed 19 duplicate copies under an un-hidden `archive/` dir that `rglob` was scanning. Corrected to a non-destructive hide (`archive` → `.archive`). **The rule applies to authoritative instructions too, not just one's own reasoning** — verify the directive against live state before executing it.
**The rule:** Before deploying any change, verify the specific mechanism against the actual running code. `grep` the source. Check the hook timing. Read the class hierarchy. Trace the execution path. If the verification contradicts the reasoning, the verification wins.
**Instances:** Kestrel's "reasoned, not verified" self-correction (the most important single sentence in the session). The `audit_extensions.py` tool (DEC-026 encoded as tooling). The wiring diagram (specificity as verification instrument).
**Revisit if:** Never. This is a first principle.

---

## DEC-042: Every Capture System Must Have a Consumption Path

**Date:** 2026-05-30
**Session:** 113+
**Principle:** Building a capture mechanism without a corresponding consumption mechanism is half a loop. The data exists but produces no value. Every system that writes must have a verified path where the written data is read and used.
**Context:** Four independent instances of capture-without-consumption were discovered and fixed in this session:
1. **Skills:** `skills_captured: 0` for 878 cycles. The capture pipeline was designed but the skill files had malformed frontmatter (invisible to A0's discovery) and no proactive surfacing mechanism. Fixed: frontmatter normalizer + `_24_skill_surfacer` + three-layer validation. (The surfacer was placed at `_24`, not the design note's suggested `_07` — Kestrel's deliberate, documented decision so the lesson prepends *above* the reasoning/PACE injectors at `message_loop_prompts_after` for visibility; `_07` would run first and be buried. As-built code is `_24`.)
2. **Memories:** 476 memories (~32% of the store) saved to areas the recall path never searches. The agent recorded its best CONCEPT insights and EXPLORE findings into semantic areas not in the hardcoded recall whitelist. Fixed: removed area restriction on general-knowledge recall.
3. **Injection chain:** `_49` computed reasoning state, `_13`/`_14` injected it at `before_main_llm_call` where writes are discarded. The data existed on the agent object but never reached the model's context. Fixed: `_22`/`_23` injectors at `message_loop_prompts_after`.
4. **Predictions:** SWARMFISH V2 forecasts were generated, consensus logged, and falsification conditions discarded. The system forecast into the void. Fixed: Phase 1a forecast capture with machine-checkable exit criteria.
**The rule:** When designing any capture mechanism, specify the consumption path in the same document. "Where is this data read? By what extension, at what hook, through what query?" If those questions can't be answered concretely, the capture mechanism is incomplete.
**Debugging companion (the practical version):** When something *feels* wired but doesn't work, check who *reads* what's being written — the gap is almost always at the consumer, not the producer. This single question found both the `error_format` capture gap and the orphaned-memory recall gap.
**Revisit if:** Never. This is a design checklist item.

---

## DEC-043: Instrument Before Optimizing

**Date:** 2026-05-30
**Session:** 113+
**Principle:** You cannot improve what you cannot measure. Before optimizing any system, add instrumentation that produces quantitative data about its current behavior. The measurement often reveals that the problem isn't what you assumed.
**Context:**
1. **Skill-library audit (2026-05-31)** — before fixing anything, the gap was *counted*: running A0's own `validate_skill_md` over the library quantified "30% invisible" (v17 26/88 invalid, v16 39/70) — a precise number that turned a vague "skills seem off" into a measured target, drove the normalizer, and confirmed the fix (62→82, 31→70). The measurement defined the work.
2. **Memory orphaning (2026-05-31)** — the recall gap was measured both ways: 476/1471 memories (32%) in unreachable areas before, and the simpleeval comparator validated 567→1043 eligibility after. Fixing without the before/after count would have been a guess; with it, the un-orphaning was provable.
3. **Cache hit ratio** — we couldn't optimize API costs until we instrumented `prompt_cache_hit_tokens` and `prompt_cache_miss_tokens` per response. The 65% hit / 31% miss ratio was invisible before measurement.
4. **Affect layer** — FRUSTRATION and DESPERATION states can't be calibrated until the enriched behavioral trace schema (added in Phase 1) collects 50-100 cycles of data. The measurement must precede the optimization.
5. **Per-profile Brier scores** — SWARMFISH ensemble calibration can't improve until predictions are binned by probability and tracked per profile. Started logging; calibration curves come after 50+ resolved predictions.
**The rule:** The first commit of any optimization work should be instrumentation, not the optimization itself. Log the metric. Capture the baseline. Then optimize. Then compare.
**Revisit if:** Never. This is engineering practice.

---

## DEC-044: Defense in Depth for Data Quality

**Date:** 2026-05-30
**Session:** 113+
**Principle:** Single-point defenses fail silently. Layer multiple validation mechanisms so that data quality is enforced at write time, maintenance time, and deploy time. A failure in any one layer is caught by the others.
**Context:** The three-layer skill validation architecture proved the pattern:
- **Layer 1 (write-time):** `_45` emits valid frontmatter. Prevents malformed skills from being created by the capture pipeline.
- **Layer 2 (maintenance-time):** The normalizer runs in MAINTAIN's integrity check. Heals malformed skills from any source (wizard, manual, import, future Path B).
- **Layer 3 (deploy-time):** `install_all.sh` runs the normalizer after every install/update. Catches anything imported or synced.
59 skills were invisible due to malformed frontmatter from sources that predated the capture pipeline. Layer 2 resurrected them. Layer 1 prevents future ones. Layer 3 catches imports. No single layer covers all cases. Together they cover everything.
**The same pattern applies to:** The supervisor (five detectors composed into affect states rather than any single detector), the idle engine (cooldown counter + time cap + state detector rather than any single escape mechanism), the DEC-026 audit tool (checks all paths rather than assuming the correct one).
**The rule:** Any data quality mechanism should have at least two independent layers. If the system accepts data from multiple sources (user input, autonomous generation, external import), each source should be validated by at least one layer.
**Revisit if:** Never. This is infrastructure design.
