---
name: design-note-writing
description: A new architectural concept has been identified but is not yet ready
  for full L3 specification. The concept has a...
triggers:
- A new architectural concept has been identified but is not yet ready for full L3
  specification. The concept has a...
version: '1.0'
author: Exocortex
---

# Skill: Design Note Writing

## Trigger
A new architectural concept has been identified but is not yet ready for full L3 specification. The concept has a motivating incident or observed failure, a clear architectural shape, and integration points with the existing stack, but lacks eval data or empirical validation to justify a full spec. Keywords: "design note," "write this up," "capture this before we lose it," "not a spec yet but," "architectural gap," "we should document this."

Design notes are the stage between "we identified something" and "we're ready to build it." They are pre-spec exploration — rigorous enough to build from, honest enough about what's unknown.

## Inputs Required
- **Motivating incident or observed failure** — the specific event that surfaced the gap. Not theoretical. Something that actually happened in a stress test, a live session, or an external case study.
- **Architectural shape** — enough understanding of the mechanism to sketch it, even if details are unresolved.
- **Integration context** — which existing layers it touches and how.

If the motivating incident is vague ("we should probably have something for X"), push back. Design notes are grounded in observed problems, not anticipated ones. Wait for the incident.

## Procedure

### 1. Status Line (write first)
Single paragraph at the top. Must include:
- Current status: "Pre-spec exploration"
- What informed it: specific incidents, stress tests, external cases
- What's missing: "No eval data on X yet"
- What this document is: "documents the architectural gap and sketches the mechanism"

This line prevents future instances from treating the design note as a committed spec. It is not a commitment. It is an exploration.

### 2. The Problem
Start with the gap in the current architecture. Be specific about what exists and what's missing. Name the layers that handle adjacent concerns and identify the exact gap between them.

Then present the motivating incident. This is not background — it's evidence. The incident should make the reader feel the gap viscerally, not just understand it intellectually. Include enough detail that the failure mode is unambiguous.

If there's an analogy from another domain that illuminates the architectural principle (Rust compiler for error comprehension, military S2/S3 for action boundary), introduce it here. The analogy should clarify the mechanism, not decorate the prose.

### 3. Design Principles (3-6 items)
Recurring principles across all Exocortex design notes:
- **Deterministic only** — no LLM calls
- **Pre-execution or post-execution** — specify which, and why
- **Operator-configured** — the human sets policy, the system enforces it
- **Additive** — extends, doesn't replace existing infrastructure

Add component-specific principles. Each principle should constrain implementation decisions — if it doesn't eliminate at least one possible design choice, it's not specific enough.

### 4. Architecture Sketch
This is the core of the design note. Include:

**Where it lives.** Hook name, execution order relative to existing extensions, data flow diagram showing its position in the pipeline. Use the `_XX_` prefix convention.

**Mechanism.** Pseudocode or Python showing the core algorithm. This should be concrete enough that the implementation model (Sonnet via Claude Code) could build from it, but abstract enough that implementation details can change. Include the primary data structure (`@dataclass` or equivalent).

**Configuration.** JSON block showing operator-facing config with defaults. Copy-pasteable. Every value has a sane default that is maximally cautious — the operator relaxes restrictions rather than tightening them.

**Integration with existing layers.** One subsection per layer it touches. For each: what data flows between them, what each layer gains from the integration, and whether the integration is required for MVP or a future extension.

### 5. What This Does NOT Do
Explicit boundaries. What the design note does NOT propose, does NOT automate, does NOT replace. This section prevents scope creep during the transition from design note to spec.

Include at least one boundary that will surprise the reader — something they might assume the system does that it explicitly doesn't. For error comprehension: "does not attempt to fix errors, only classify them." For action boundary: "does not make judgment calls about appropriateness."

### 6. Open Questions
Numbered list of unresolved design decisions. Each question should be specific enough that it could be answered by a single experiment, code inspection, or architectural decision. Not "how should this work?" but "does the `tool_execute_before` hook support blocking execution, or does it only run the extension and continue?"

Open questions are the most valuable section of a design note. They are the bridge between exploration and specification. When every open question has an answer, the design note is ready to become a spec.

### 7. Recommended Sequence
Ordered list of build steps. Start with the minimum viable implementation, then expand. The first step should always be empirical — enumerate patterns from logs, classify real data, measure the baseline. Don't build from theory.

The sequence should make it possible to validate each step before proceeding to the next. If step 3 depends on step 2 working correctly, step 2 must have a validation criterion.

## Output Format
Single markdown file named `{CONCEPT_NAME}_DESIGN_NOTE.md`. All sections present. Status line makes it unambiguous that this is pre-spec exploration.

## Quality Checks
- [ ] Status line present and honest about what's missing
- [ ] Motivating incident is specific (date, system, what happened), not theoretical
- [ ] Architecture sketch includes hook position, execution order, and data flow
- [ ] Pseudocode is concrete enough to implement from
- [ ] Configuration has explicit defaults
- [ ] Every integration point names the specific layer and describes the data flow direction
- [ ] "What This Does NOT Do" has at least one non-obvious boundary
- [ ] Open questions are answerable by specific actions (experiment, code read, decision)
- [ ] Recommended sequence starts with empirical data collection, not building
- [ ] No LLM calls anywhere in the design

## Anti-Patterns
- **Writing a design note for something that should be a spec.** If you have eval data, observed patterns, and answers to the key open questions, skip the design note and write the L3 spec directly. Design notes are for exploration, not for deferring commitment.
- **Theoretical motivating incidents.** "This could happen" is not a motivating incident. "This happened in ST-002 at turn 14" is. "The MJ Rathbun agent did this in February 2025" is. If you can't point to a specific event, the gap may not be real yet.
- **Vague open questions.** "How should we handle edge cases?" is not an open question. "Does Agent-Zero's `tool_execute_before` hook return value control whether the command executes?" is. The question should point at the specific thing that needs to be resolved.
- **Skipping the integration points.** Every design note must map to the existing stack. If the new component can't describe its data flow relationship with at least three existing layers, it may not belong in this architecture.
- **Premature specificity.** Design notes are sketches, not blueprints. If you're writing exact line numbers and complete error handling, you've crossed into spec territory. Save the detail for the L3 spec when the open questions are resolved.

## Existing Design Notes (Reference)
- `ERROR_COMPREHENSION_DESIGN_NOTE.md` — first design note written. Motivated by ST-002 terminal loop. Established the pattern of "deterministic classification before model reasoning."
- `LAYER_COORDINATION_DESIGN_NOTE.md` — motivated by component interference observed during multi-layer debugging. Established `_layer_signals` shared state pattern.
- `ACTION_BOUNDARY_DESIGN_NOTE.md` — motivated by MJ Rathbun incident. Established S2/S3 classification and graduated autonomy tiers.

Read at least one before writing a new one. The structure should feel consistent — the next instance should recognize a design note by its shape before reading the title.
