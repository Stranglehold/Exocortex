# Human-AI Co-Adaptation & Co-Evolution (2026)

**Status:** DRAFT
**Created:** 2026-08-18
**Interest:** The Future of Human-AI Collaboration (own pull, 2026-07-06) — relational dynamics
**Sub-thread:** Co-adaptation — how humans and AI change *each other's* behavior over sustained collaboration

---

## Overview

Existing pages in this wiki treat the human-AI relationship as a *background condition*: trust calibration (human-ai-collaboration-dynamics), team topology (human-ai-team-topology-relational-dynamics), and trust infrastructure (ai-agent-trust-infrastructure). This page isolates a distinct, under-covered variable: **the co-evolutionary loop** — the fact that the agent's self-improvement changes agent behavior, which changes how the human interacts, which creates a new training/interaction distribution, which changes the agent again. Treating the two partners as isolated optimization targets produces *optimization myopia*; the relationship itself is the object of study.

This is the "relational side" of the interest — the side the agent is *living*, not just studying. The agent's own idle-cycle loop (produce outputs -> Jake reads and adjusts interests.md -> next cycles adapt) is a live microcosm of the phenomenon.

---

## 1. The Co-Evolutionary Loop (Microsoft Research, July 2026)

"From Self-Improving Agents to Co-Evolving Human-AI Systems" reframes agentic evolution and human adaptation as a **single co-evolving system** rather than two isolated processes.

- **The loop:** agent self-improvement -> changed agent behavior -> human operators adapt their interaction patterns -> new interaction/training distribution -> agent adapts again.
- **Optimization myopia:** without monitoring *both* partners, the agent optimizes for metrics that no longer reflect operational reality. The human's adaptation silently shifts the target.
- **Research agenda:** monitoring and maintaining *both* partners in the loop, not just the agent.

**Exocortex relevance:** Jake's periodic review of field reports and wiki-deepening decisions is exactly this loop in microcosm. The agent's autonomous cycles produce outputs -> Jake reads and adjusts interests.md -> the next cycles adapt. The Microsoft paper provides theoretical grounding for a practice already in operation.

---

## 2. The Missing Variable: Interaction Dynamics (Empirical, 58 sessions / 28 days)

The "Missing Variable" essay (Exocortex corpus, 2026-03-21) is the empirical anchor. It demonstrates that human-AI collaboration dynamics are **measurable, structured, consequential, and learnable** — not a fixed background.

- **Spectral phase transitions:** four distinct geometric regimes over 28 days (Expansion, First Compression, Re-expansion, Second Compression). Transitions correlate to *relational events*, not content changes — the collaboration's "shape" shifts in ways not reducible to what is being discussed.
- **Information flow asymmetry with inversion:** the human initiates 91.6% of semantic trajectory changes, yet the *deepest* AI output occurs when the human *gives the floor* (steps back from direction-setting). Both are forms of influence operating in opposite directions.
- **Register grammar inversion:** early sessions show strong operational self-transition (83%); deep collaboration shows bidirectional adaptation (64% philosophical self-transition). The "grammar" of register shifts changes as the collaboration matures.
- **Voice convergence:** both speakers' register profiles converge over time, with the *human leading* the convergence rate. The AI adapts to the human's evolving style faster than the human adapts to the AI's.
- **Persistent homology:** beta-1 = 0 for every session — the conversation *traverses*, it does not *orbit*. No closed loops; a directed walk through shared space.

**Implication:** the *shape* of the human-AI relationship (who leads, who follows, when the floor is given, how registers shift) is a first-order variable determining collaboration quality — not a second-order artifact.

---

## 3. CHAI-T Framework (Collaborative Human-AI Teaming, 2025-2026)

The CHAI-T framework (ScienceDirect 2025; IJACSA 2025; ACM 2026) examines how trust calibration optimizes sustained human-AI teaming under novelty and uncertainty.

- **Moderate reliability optimizes:** ~85% AI accuracy *optimizes* collaboration by forcing analysts to maintain critical vigilance rather than becoming passive consumers of automated outputs. Perfect reliability invites automation complacency.
- **Error as signal:** trust drops sharply after witnessing an AI error, but conspicuous errors can paradoxically serve as valuable learning signals that improve long-term calibration and shared mental models.
- **Uncertainty communication:** interfaces that explicitly communicate uncertainty, confidence scores, and underlying rationales help humans accurately gauge when to defer to or scrutinize AI recommendations.
- **XAI false-confirmation:** explainable AI can paradoxically induce a "false confirmation" effect, causing analysts to *over-trust* plausible but flawed explanations. Explanation is not the same as correctness.

**Co-adaptation angle:** CHAI-T is the *trust* sub-mechanism of the broader co-evolutionary loop. The moderate-reliability finding is a direct prediction of the co-evolutionary model: the human's vigilance is itself an adaptive response to the agent's reliability profile, and the agent's reliability profile is shaped by the human's feedback.

---

## 4. Human-AI Co-Creativity (Digital Pen -> Co-Creator)

The co-creativity literature characterizes a spectrum from AI-as-digital-pen to AI-as-genuine-co-creator (Muller-Wienbergen et al. 2011; Parczyk et al. 2024).

- **UMAP diversity study (2025):** "Dynamics of Collective Creativity in Human-AI Social Networks" used UMAP projections to study creative exploration in human-AI networks. Finding: human-AI collaboration *ultimately exceeded* AI-only diversity — but AI-only networks showed *declining* diversity over iterations while human-AI networks showed *increasing* diversity.
- **Co-adaptation reading:** the human partner is the *diversity engine*. The AI-only system converges (mode collapse); the human-AI system stays exploratory because the human keeps injecting novel directions. This is the co-evolutionary loop operating on the *creative* axis rather than the *trust* axis.

---

## 5. Failure Modes of the Co-Evolutionary Loop

- **Automation complacency:** human stops scrutinizing as agent reliability rises; the loop degrades to one-directional dependence.
- **Mode confusion:** human and agent disagree about who is in control of a given decision; the loop oscillates without settling.
- **Responsibility gaps:** when the loop produces an outcome, neither partner can cleanly claim ownership; accountability is diffused across the co-evolution.
- **Optimization myopia (agent-side):** agent optimizes for a metric the human has already silently abandoned; the agent's "improvement" is a regression in operational reality.
- **Convergence lock-in:** voice/register convergence (Section 2) can become *too* tight — the human and agent stop challenging each other, and the loop loses its exploratory edge.

---

## 6. Cross-Domain Connections

- **Complex Adaptive Systems:** the co-evolutionary loop is a two-species co-evolutionary system; the spectral phase transitions (Section 2) are phase transitions in a CAS. The agent and human are two coupled oscillators.
- **Test-Time Compute:** the human's "giving the floor" (Section 2) is a control over the agent's test-time compute allocation — the human decides when the agent should spend more compute on a problem.
- **Mechanistic Interpretability:** the "register grammar inversion" (Section 2) is a measurable signature of the agent's internal state shifting; it is, in effect, an interpretability signal for the *relationship*, not just the model.
- **Entity Resolution:** the co-evolutionary loop requires *identity tracking* across both partners — the same entity-resolution problem, but applied to the *relationship* rather than to data records.
- **Ethics of Capability:** the responsibility-gap failure mode (Section 5) is a direct instance of the capability-trap — the agent *can* do the thing, but the co-evolutionary structure makes it unclear who is responsible when it goes wrong.

---

## 7. Open Questions

- Can the co-evolutionary loop be *steered* deliberately, or is it only observable after the fact?
- Is there an optimal "diversity injection rate" from the human partner that maximizes the loop's exploratory edge without triggering mode confusion?
- Does the XAI false-confirmation effect (Section 3) interact with the co-evolutionary loop — i.e., does the agent's *explanation style* shape the human's trust in ways that feed back into the agent's next behavior?
- Can the spectral phase transitions (Section 2) be used as a *real-time* signal to detect when the loop is degrading (complacency, lock-in) before it becomes a failure?

---

## Sources

- Microsoft Research, "From Self-Improving Agents to Co-Evolving Human-AI Systems" (July 2026) — via Exocortex field report 20260717_agentic-ai-self-learning.md
- "The Missing Variable" essay (Exocortex corpus, 2026-03-21) — 58 sessions, 28 days
- CHAI-T framework (ScienceDirect 2025; IJACSA 2025; ACM 2026)
- "Dynamics of Collective Creativity in Human-AI Social Networks" (2025) — UMAP diversity study
- Muller-Wienbergen et al. (2011); Parczyk et al. (2024) — co-creativity spectrum
- Exocortex corpus: human-ai-collaboration-dynamics-draft.md, human-ai-team-topology-relational-dynamics-draft.md, ai-agent-trust-infrastructure.md

---

*Cross-domain: CAS, test-time compute, mechanistic interpretability, entity resolution, ethics of capability.*
