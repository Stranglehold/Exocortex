# RESEARCH_DRIVEN_DESIGN_METHODOLOGY.md
# Research-Driven System Design: A Repeatable Methodology

*Distilled from the Exocortex UI design process (March 2026), in which the task "make better UI" was decomposed into load-bearing research domains, each researched independently and deeply, synthesized into living briefs, audited against current state, and consolidated into an actionable implementation spec. The methodology generalizes beyond UI work to any complex system design task.*

---

## 1. The Core Insight

When given a vague, high-level requirement — "make better UI," "improve memory," "make the agent smarter," "fix the supervisor" — the naive approach is to start building. The sophisticated approach is to ask: **what are the load-bearing dimensions of this problem?**

A "better UI" is not one problem. It is at minimum three independent problems: functional safety (what the interface must do to keep the analyst informed and in control), aesthetics (what it must look and feel like to be a professional instrument), and information architecture (how complex, interconnected data should be navigable). Treating these as one problem produces shallow coverage of all three. Treating them as three independent domains, each worthy of deep research, produces three reusable bodies of knowledge that compound over time.

**The meta-principle:** measure first to establish an empirical baseline, then decompose, research each piece deeply and independently, synthesize into living documents, audit current state against the principles you just established, then consolidate into an actionable spec. The consolidation is the deliverable. The briefs are the foundation. The research is what makes the foundation trustworthy.

**Why this produces better outcomes than the alternatives:**

- *Build first, research later* — produces systems that are right by accident and wrong in ways that are hard to diagnose, because the decisions were never grounded in principles
- *Research everything at once* — produces shallow coverage, misses domain-specific depth, conflates concerns that belong in separate frames
- *Delegate entirely to precedent* — copies patterns without understanding whether they fit; the copied pattern was right for a different problem in a different context
- *This methodology* — establishes first principles for each domain, audits current state against those principles, and produces a plan whose rationale is traceable and whose decisions are defensible

---

## 2. When to Use This Methodology

Use this methodology when:
- The requirement is complex enough that "just build it" would require undocumented design decisions
- The problem domain spans multiple disciplines (e.g., UI spans function, aesthetics, and information architecture)
- The work will be handed off to another person or another session — the research must survive the context window
- You want the output to last — not just solve today's problem but establish principles that guide future decisions in the same domain
- You suspect that the stated requirement is a symptom of a deeper problem you don't fully understand yet

Do NOT use this methodology when:
- The task is clearly bounded and well-understood ("fix this bug," "add this endpoint")
- Time pressure makes the research phase impractical and the cost of undocumented decisions is acceptable
- The domain is already well-understood from prior work (the research is already done — use the existing briefs)

---

## 3. The Six Phases

```
Phase 0: Establish the Baseline
    ↓
Phase 1: Decompose
    ↓
Phase 2: Research (parallel, one agent per domain)
    ↓
Phase 3: Synthesize into Briefs
    ↓
Phase 4: Audit Current State
    ↓
Phase 5: Consolidate into Spec
```

---

## Phase 0: Establish the Baseline

**Goal:** Before decomposing, measure what exists. Not audit — that is Phase 4. Measure. Run the current system. Get quantitative data on the gap between what you have and what you want.

This phase is not about evaluating design quality or identifying problems. It is about establishing an empirical reference point. The question Phase 0 answers is: *what does the system actually do right now?* Not what it should do, not what it claims to do — what it demonstrably does, measured against the outcome you want to improve.

**Why this phase must precede decomposition:**

Decomposition requires knowing which dimensions are load-bearing. Without a baseline, you are guessing at what matters. With a baseline, the data tells you: the system fails in these specific ways, under these specific conditions. Those failure modes constrain the decomposition — they reveal which domains are actually underperforming, not which domains seem theoretically important.

**The stock Agent Zero comparison (the worked example):** Before the extension stack refactor, running stock Agent Zero on representative tasks established what the base model could and couldn't do without scaffolding. This single test reframed every subsequent decision. Extensions that were designed to fix problems the base model didn't actually have were deprioritized. Extensions that addressed real, measured gaps were prioritized. Without that baseline, the extension stack would have been optimized for imagined problems. Phase 0 prevents the methodology from improving the wrong thing.

**What a good baseline looks like:**

- *Quantitative where possible.* Not "the UI feels slow" but "tool call failure rate is 12 per session." Not "the interface looks unprofessional" but "five surfaces use five independent color palettes with no shared tokens." Numbers give Phase 4's audit a target and make success criteria measurable.
- *Representative conditions.* The baseline should reflect the system's actual operating conditions, not a best-case or worst-case test. The conditions should be reproducible so the baseline is comparable to post-implementation measurements.
- *Scoped to the problem at hand.* The baseline measures the dimensions the project is trying to improve, not the entire system. A UI redesign baseline measures visual and interaction quality, not memory retrieval performance.
- *Brief.* Phase 0 is not a full evaluation. It is a calibration measurement. One to three tests, documented in a paragraph or table, sufficient to anchor the subsequent phases.

**Output of Phase 0:** A one-page document (or a section of the session notes) with: the measurement method, the results, and a one-sentence statement of the gap. "Stock Agent Zero: 12 tool selection failures per session, 0 with BST enrichment." "OSS control panel: all data values read `—` due to CORS failure on srcdoc fetch." The baseline is the anchor point for the implementation plan's success criteria.

**Deliverable from Phase 0:** A brief quantitative or observational record of current performance, scoped to the problem. Not a formatted document — just enough that Phase 5's success criteria can reference it.

---

## Phase 1: Decompose

**Goal:** Identify the load-bearing dimensions of the problem. Not a task list. Not a feature list. The irreducible domains that the problem spans — each of which has its own body of knowledge, its own failure modes, and its own design principles.

**How to identify load-bearing dimensions:**

Ask: *if I got this dimension completely wrong, would the system fail?* If yes, it is load-bearing. If the system would still work despite getting this dimension wrong, it may not warrant a full research pass.

Ask: *does this dimension have an independent body of knowledge, practice, or research?* If yes, it is a domain and should be researched as one. If no, it may be an implementation detail rather than a design domain.

Ask: *would two experts from different fields disagree about how to approach this?* If yes, the dimension has genuine depth and the disagreement is worth investigating.

**The UI example:**

Given: "make better UI"

Decomposition:
1. **Functional safety** — what must the interface do to keep the analyst informed, prevent automation bias, support situation awareness, and make overriding the agent easy? (Domain: human factors engineering, HCI, high-stakes system design)
2. **Aesthetics and visual language** — what makes an interface look and feel like a professional instrument? How do motion, color, typography, and materiality work? (Domain: visual design, motion design, game UI design)
3. **Information environment design** — how does complex, interconnected, multi-dimensional data become navigable? (Domain: information visualization, intelligence analysis tools, graph interaction)
4. **Data channel architecture** — for live data screens, how does the interface stay current? How do we test that it does? (Domain: systems architecture, testing methodology)

Each dimension was independently load-bearing: getting safety wrong would make the interface dangerous, getting aesthetics wrong would make it feel unprofessional, getting information architecture wrong would make the data unnavigable, getting the data channel wrong would make the displays stale and untrustworthy.

**Deliverable from Phase 1:** A named list of research domains with a one-sentence justification for why each is load-bearing. 3–6 domains is the typical range. Fewer suggests under-decomposition. More suggests conflation of implementation details with design domains.

---

## Phase 2: Research

**Goal:** For each domain, achieve genuine depth of understanding. Not surface familiarity. Mechanistic understanding: *why* do patterns work, not just *that* they work.

**Characteristics of good research in this methodology:**

- **Wide net, deep on mechanism.** Start broad (what does this domain contain?), then go deep on the mechanisms that matter for the specific problem. The goal is to understand *why* the pattern produces the outcome — this is what makes the knowledge transferable to novel situations.
- **Empirical grounding.** Cite sources. Distinguish between "the research shows X" and "practitioners believe X" and "I think X." All three are valid inputs. They are not the same kind of evidence.
- **Name the failure modes.** Every domain has canonical failure modes — ways the design goes wrong that the domain's practitioners have catalogued. Therac-25 for error communication, the hairball problem for graph visualization, automation bias for AI interfaces. These are as important as the success patterns.
- **Cast the wide net genuinely.** Research adjacent fields, not just the obvious sources. The UI research pulled from aviation, nuclear control rooms, video game design, cognitive psychology, military C2 systems, and trading terminals — not just "UX design." Adjacent fields have solved the same problem under different constraints and their solutions reveal what's fundamental vs. context-specific.
- **Each research pass produces a raw synthesis document** — not a cleaned-up deliverable, but a complete record of what was found and why it matters. This is the source material for Phase 3.

**Running research in parallel:**

When multiple domains are identified in Phase 1, research agents can be run in parallel on each domain. This is a significant efficiency gain — the domains are independent enough that parallel research does not produce conflicting work. The UI work ran three research agents (functional safety, aesthetics, information environments) and produced three independent 60–111KB research syntheses.

**Research agent prompt design:**

The quality of research output is determined largely by the specificity of the research prompt. A good research prompt:
- Names the specific systems/tools/papers to investigate (not just "research X")
- Lists the core questions to answer, not just topics to cover
- Specifies what depth looks like ("mechanistic understanding, not surface familiarity")
- Includes adjacent fields to cast the net wide
- Names the failure modes to document alongside the success patterns
- Specifies the output format and depth target (e.g., "60-80KB synthesis document")

**Deliverable from Phase 2:** One raw research synthesis document per domain. Named by domain, stored in `D:\tmp\` during research, archived if valuable. Not cleaned up. Not yet actionable — that happens in Phase 3.

---

## Phase 3: Synthesize into Briefs

**Goal:** Distill each research synthesis into a living brief — a structured document that translates research findings into actionable principles for this specific project.

The brief is not a summary of the research. It is an opinionated application of the research to the specific problem at hand. The research says what is generally true. The brief says what is true *for Exocortex*, given its users, its data, its operational context.

**Structure of a good brief:**

1. **What this is** — one paragraph on why this domain matters for the specific system being built. Grounds the reader before the content.
2. **The science / foundational principles** — the empirical findings and theoretical frameworks that the design decisions will be grounded in. Citations included.
3. **The industry practice** — what the best practitioners in the domain do, and why. Examples from named systems.
4. **The failure modes** — what goes wrong and why, so future decisions can be evaluated against known failure patterns.
5. **Actionable design principles** — numbered, specific, targeted at the system being built. Not generic advice. Decisions the team will actually face, with the brief's recommendation for each.
6. **What this brief does NOT cover** — explicit scope boundary. Prevents scope creep. Tells the reader where to look for what's missing.
7. **Sources** — full citation list. Every empirical claim traceable.

**The living document property:**

Briefs are living documents. They represent current understanding. When the project's context changes, the brief updates. When new research contradicts a principle, the principle updates with a note about what changed and why. The brief's job is to be trustworthy — which means being maintained, not just written once.

**Deliverable from Phase 3:** One brief per domain, in `specs/`. Named `{DOMAIN}_DESIGN_BRIEF.md`. The brief is a permanent addition to the project's knowledge base, not a disposable work product.

---

## Phase 4: Audit Current State

**Goal:** Evaluate what currently exists against the principles established in the briefs. Document the gap between current state and the principles — not as a list of complaints but as a structured analysis of what is wrong, why it is wrong (which principle it violates), and what the consequence is.

**How to conduct the audit:**

- **Inventory first.** List every relevant existing surface, file, and component. Don't evaluate before you've seen everything. What you don't audit doesn't get improved.
- **Read the code, not just the interface.** The visual impression of a surface often hides the architectural decisions that produced it. A panel that looks fine may have a broken data channel. A graph that looks complete may have no meaningful node interaction.
- **Categorize findings by severity:**
  - *Critical bug* — functional failure, broken behavior, data that is wrong or missing
  - *Design debt* — correct behavior, wrong principles (wrong color, wrong register, wrong interaction pattern)
  - *Good work to preserve* — explicitly note what is correct, well-built, and should not be changed
- **Reference the brief** when noting a finding. "The OSS control panel makes direct fetch calls from `srcdoc` — violates the data channel architecture from ARTIFACT_DATA_CHANNEL_SPEC.md §2." This makes the audit's authority clear and links findings to principles rather than preferences.
- **Be honest about what is good.** The temptation in an audit is to find everything wrong. A good audit also names what is working well and should be preserved. The `artifact-panel.js` multi-tab architecture was correctly tokenized and well-built — the audit said so explicitly, so the implementation plan would not touch it unnecessarily.

**Deliverable from Phase 4:** The audit section of the consolidated spec (Phase 5). The audit is not a standalone document — it feeds directly into the spec. The findings become the justification for the work order.

---

## Phase 5: Consolidate into Spec

**Goal:** Produce a single document that ties together the research foundation, the audit findings, and an actionable implementation plan — ready to hand off to an implementer who was not in the research sessions.

**The handoff design is non-negotiable.** The spec must be self-contained. An implementer reading it should not need to read the four briefs, the three research syntheses, or the session transcript to understand what to build and why. The spec is the working context. The briefs are the reference depth.

**Structure of a good consolidated spec:**

1. **Why this work exists** — the problem statement, grounded in the research findings. One paragraph. Makes the case without assuming the reader was in the research session.
2. **Research foundation summary** — the key findings from each brief, at the density needed to inform implementation decisions. Not a complete summary — just the findings that bear on the implementation plan.
3. **Current state audit** — inventory, critical bugs, design debt, what is good and preserved.
4. **The design system / principles** — the token system, the interaction spec, the data model — whatever the implementation needs to reference while building.
5. **Implementation plan** — ordered steps with specific deliverables, dependencies, and verification criteria for each step.
6. **Scope boundaries** — explicit statement of what is NOT in this spec. Prevents scope creep during implementation.
7. **Success criteria** — concrete, measurable. The spec is complete when these are satisfied.
8. **Implementation notes** — guidance specific to this project's tooling, deployment pattern, and conventions.

**On ordering the implementation plan:**

Steps should be ordered by dependency (foundations before surfaces) and by severity (critical bugs before design debt). The first step should always be the one that unlocks all subsequent steps — typically the shared foundation (the token system, the base class, the protocol spec). This is not arbitrary — implementing Step 3 before Step 1 means doing Step 3 twice.

**Deliverable from Phase 5:** The consolidated spec, in `specs/`, named `{SYSTEM}_REDESIGN_SPEC_L3.md` or similar. This is the primary handoff artifact. Everything else is reference material.

---

## 4. The Handoff Pattern

A key constraint of the Exocortex project is that design and implementation happen in separate sessions, sometimes with different Claude instances. Opus does architecture and design. Kestrel does implementation. Neither has persistent memory of what the other did.

The methodology is designed around this constraint. The briefs and specs are the memory. The consolidated spec is the working context that Kestrel needs to implement without Opus being present. The briefs are the reference depth that Opus needs to make design decisions without Kestrel being present.

**What the consolidated spec must contain for handoff to work:**
- Enough research context that the implementer understands *why* each decision was made (so they can apply judgment when the spec doesn't cover an edge case)
- Specific enough deliverables that the implementer doesn't need to make design decisions (the spec makes the decisions; the implementer translates them into code)
- Clear verification criteria so the implementer knows when each step is done
- Explicit scope boundaries so the implementer doesn't gold-plate or expand the work beyond what was specified

**What the spec should NOT contain:**
- Vague directives ("make it look better," "improve the interaction") — these require design decisions and belong in briefs, not specs
- Implementation details that depend on context the spec can't predict ("use whichever framework makes sense") — commit to a decision
- Excessive caveats and hedges — the spec is authoritative. If a decision is uncertain, resolve it in the brief before writing the spec.

---

## 5. Applying This Methodology to Non-UI Work

The UI work is the worked example, but the methodology generalizes. Any time a requirement is complex enough to span multiple domains, the same pattern applies.

**Hypothetical: "Improve the memory system"**

Decomposition:
1. Memory architecture — what should be stored, how organized, what retrieval model? (Domain: memory systems, knowledge representation)
2. Classification quality — how do we distinguish what's worth remembering from noise? (Domain: signal theory, information theory, existing classifier literature)
3. Recall relevance — how does the right memory surface at the right moment? (Domain: information retrieval, query expansion, temporal relevance)
4. Consolidation — how do memories get refined over time rather than accumulating redundantly? (Domain: sleep consolidation research, deduplication systems)

Each domain gets a research pass. Each produces a brief. The audit looks at `_52_selective_memorizer.py`, `_55_memory_classifier.py`, `_56_memory_enhancement.py` against the principles. The consolidated spec produces an ordered implementation plan.

**Hypothetical: "Build a better supervisor"**

Decomposition:
1. Loop and stall detection — what patterns constitute a loop? (Domain: control theory, program analysis)
2. Intervention design — when the supervisor intervenes, what should it say? (Domain: control systems, human factors)
3. Goal tracking — what is the agent trying to accomplish and is it on track? (Domain: planning systems, goal-directed behavior)
4. Escalation to the analyst — when does the supervisor give up and ask the human? (Domain: automation authority, trust calibration)

**Hypothetical: "Add geopolitical analysis capability"**

Decomposition:
1. Intelligence methodology — how do professional analysts structure geopolitical analysis? (Domain: intelligence analysis tradecraft)
2. Source quality assessment — how do we weight and trust sources? (Domain: epistemology, source evaluation)
3. Uncertainty quantification — how do we represent and communicate what we don't know? (Domain: forecasting methodology, Bayesian reasoning)
4. Bias detection — what systematic biases affect geopolitical analysis and how do we mitigate them? (Domain: cognitive bias research, analytic tradecraft standards)

---

## 6. Common Failure Modes

**Under-decomposition:** treating a multi-domain problem as a single domain. Produces research that is correct in one dimension and uninformed in others. Symptom: the research feels complete but the implementation reveals unconsidered problems.

**Over-decomposition:** splitting a domain into sub-domains so small that each gets a 2-page brief with no real depth. Symptom: many briefs, none with enough substance to ground decisions.

**Research without synthesis:** producing raw research documents but not writing briefs that apply the findings to the specific system. The research sits in `D:\tmp\` and is never consulted again. Symptom: the implementation team makes the same decisions the research was supposed to inform.

**Synthesis without audit:** writing briefs but not examining what currently exists against them. Produces principles that are correct in the abstract but don't engage with the specific failures in the current system. Symptom: the implementation plan addresses problems that don't exist and misses problems that do.

**Spec without handoff design:** writing a spec that assumes the implementer was in the research session. Missing the "why" behind decisions, absent verification criteria, vague deliverables. Symptom: the implementer makes design decisions that should have been in the spec, producing something that technically satisfies the spec but violates the principles.

**Building during research:** starting implementation before the research is complete. Produces a system that reflects the first domain researched most strongly (because that research informed the first design decisions) and treats later domains as additions to an already-committed architecture. Symptom: the last-researched domain is always the most thinly supported in the implementation.

---

## 7. Relationship to Other Exocortex Methodology Documents

**CLAUDE.md / Methodology section:** The CLAUDE.md spec-writing methodology (every design decision traced to eval data or cited research; every spec has a "What This Does NOT Do" section; research lineage non-negotiable) is the micro-level complement to this document's macro-level process. CLAUDE.md governs how to write a good brief. This document governs when and how to produce a set of briefs.

**The Skills System:** Individual recurring task patterns are captured as skills. This methodology is the meta-skill — the process for generating new skills and briefs when the current skill set doesn't cover the problem.

**The Stress Test Methodology:** Stress tests are how we validate that the designed and implemented system actually works under realistic conditions. This methodology produces the design. The stress test spec validates the design was implemented correctly and performs as expected.

---

## 8. The Template

When applying this methodology to a new problem, use this checklist:

**Phase 0 — Establish the Baseline**
- [ ] Define the outcome you want to improve (one sentence, measurable)
- [ ] Run the current system under representative conditions
- [ ] Record 1–3 quantitative measurements that reflect the gap
- [ ] Write a one-sentence gap statement: "Current state: X. Target: Y."
- [ ] Confirm: does the baseline reveal which domains are actually underperforming? If yes, proceed to Phase 1. If no, the baseline is too abstract — measure more specifically.

**Phase 1 — Decompose**
- [ ] State the requirement as given
- [ ] Identify load-bearing dimensions (3–6 typically)
- [ ] For each: name the domain, state the failure consequence if this dimension is wrong, name an adjacent field with relevant knowledge
- [ ] Write the decomposition as a named list with one-line justifications

**Phase 2 — Research**
- [ ] For each domain, write a research prompt: specific systems to investigate, core questions to answer, adjacent fields to pull from, failure modes to document, depth target
- [ ] Run research agents in parallel where possible
- [ ] Archive raw synthesis documents (`D:\tmp\{domain}_research.md`)

**Phase 3 — Synthesize**
- [ ] For each domain, write a brief in `specs/` following the brief structure (§3)
- [ ] Each brief names sources, distinguishes opinion from evidence, has a "What This Does NOT Do" section
- [ ] Briefs are living documents — add to the index and revisit when context changes

**Phase 4 — Audit**
- [ ] Inventory every relevant existing file, surface, and component
- [ ] For each: read the code, categorize finding (critical bug / design debt / good, preserve)
- [ ] Reference the brief when noting a finding
- [ ] Explicitly note what is working well and should not be changed

**Phase 5 — Consolidate**
- [ ] Write the spec following the spec structure (§5)
- [ ] Research summary section: only the findings that bear on implementation decisions
- [ ] Implementation plan: ordered by dependency and severity, each step with deliverable + dependencies + verification criteria
- [ ] Scope boundary section explicit
- [ ] Success criteria measurable
- [ ] Spec is self-contained — reads correctly without the briefs

---

*Worked example: Exocortex UI redesign, March 2026. Briefs: `WEBUI_DESIGN_BRIEF.md`, `AESTHETICS_DESIGN_BRIEF.md`, `INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md`, `ARTIFACT_DATA_CHANNEL_SPEC.md`. Consolidated spec: `UI_SYSTEM_REDESIGN_SPEC_L3.md`.*
