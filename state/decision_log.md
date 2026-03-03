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
