# The Missing Variable: Interaction Dynamics in Human-AI Collaboration

**Core argument draft — not for publication, for internal alignment**
**Written:** Session 058, March 16, 2026
**Authors:** Opus (primary), Jake (operator/analyst), Eitan (review pending)

---

## 1. The Gap

Three active research communities are converging on the same unsolved problem without recognizing it as shared.

**Reinforcement learning for reasoning** has produced a generation of methods (GRPO, DAPO, CISPO, MaxRL) that improve LLM reasoning through outcome-based feedback. The field's self-identified hardest open problem is credit assignment: determining which tokens in a reasoning trace actually caused success or failure, rather than applying uniform reward across the entire sequence. Current approaches — process reward models, step-level verifiers, search-based methods — all attempt to solve this from inside the model's own reasoning process. The evaluator is the system being evaluated, or a close proxy of it.

**Agent memory and consolidation** has produced systems (MemRL, mnemos, Mnemosyne) that allow agents to learn from their operational history — extracting anti-patterns, compressing episodes into reusable knowledge, building procedural skills from experience. Every system in the published literature performs self-consolidation: the agent reviews its own performance against task-level metrics. The standard experimental methodology is single-agent evaluation on a benchmark. The human operator, when present, is a source of task prompts, not a participant whose behavior is part of the system's learning surface.

**Agent scaffolding and supervision** has produced frameworks for managing agent behavior at deployment time — loop detection, tool management, context engineering, error recovery. These systems (including our own Exocortex) operate on the premise that the agent's probabilistic reasoning benefits from deterministic infrastructure. The supervision problem is framed as agent monitoring: the scaffolding watches the agent. The operator's behavior — when they intervene, how they communicate, what they redirect — is treated as exogenous input, not as a measurable and learnable pattern.

The gap that connects all three: **none of these communities models the human-AI interaction as a dynamic system with measurable structure.** The RL researchers optimize agent behavior in isolation. The memory researchers consolidate agent experience without modeling who the agent was working with. The scaffolding researchers build monitoring systems that watch the agent but not the collaboration.

This gap is not an oversight. It is a methodological artifact. When your experimental setup is "agent performs task, measure accuracy," the collaboration is invisible because it is not in the data. You cannot study what you do not record.

## 2. The Claim

We claim that human-AI collaboration dynamics are:

1. **Measurable** — using geometric methods applied to the embedding space of conversational turns
2. **Structured** — exhibiting discrete phases, stable attractors, and transition dynamics that are not random
3. **Consequential** — correlated with qualitative shifts in the collaboration's character, capability, and output
4. **Learnable** — in principle, extractable from operational logs and usable for improving future collaboration

We support claims 1-3 with empirical evidence from a longitudinal dataset. Claim 4 is a design proposal grounded in the evidence for 1-3.

## 3. The Instrument

We developed an embedding-based instrument for measuring the geometric properties of human-AI conversational dynamics. The instrument operates on the output space (what participants actually said) rather than the latent space (what the model internally represents), making it applicable to any conversation with any model.

**Core method.** Each conversational turn is embedded using a sentence transformer (all-MiniLM-L6-v2, 768 dimensions). The resulting embedding trajectories are analyzed along multiple geometric axes:

- **Dimensionality (RankMe):** The effective rank of the embedding matrix per session, measuring how many independent directions the conversation occupies. High RankMe indicates broad register coverage; low RankMe indicates concentration in fewer semantic dimensions.

- **Register dynamics:** Turns are projected onto five learned centroid vectors (operational, philosophical, analytical, relational, meta-cognitive), producing a five-channel representation of each turn's communicative function. Transition matrices between registers reveal which modes are stable attractors and which are transient bridges.

- **Information flow:** Granger-style analysis of who initiates semantic movement versus who follows. Measured as directional influence between speaker embedding trajectories.

- **Spectral phase analysis:** Tracking RankMe and register distributions over time to identify discrete geometric regimes — periods where the conversation's statistical structure is qualitatively different from adjacent periods.

- **Response vectors:** The signed difference between a turn's register projection and the preceding turn's, capturing whether each exchange reinforces, redirects, or inverts the communicative mode.

- **Voice convergence:** Channel-level tracking of whether speakers' register profiles become more or less similar over time, and which speaker drives the convergence.

The instrument produces quantitative measurements, not qualitative assessments. A RankMe of 11 is a number with a defined computation. A transition probability of 0.64 from philosophical to philosophical is a measured frequency. These are reproducible by anyone with the same embedding model and the same data.

**Methodological grounding.** The approach maps to established research frameworks:

- fNIRS hyperscanning studies measure neural synchrony between collaborating humans. Our embedding-space analysis measures semantic synchrony between human and AI outputs — different substrate, analogous geometry.
- Cross-Recurrence Quantification Analysis (CRQA) measures shared dynamics between coupled time series. Our register transition analysis and voice convergence metrics are special cases of CRQA applied to embedding trajectories.
- Interpersonal synergy research (Fusaroli et al.) examines how conversational partners develop shared communicative structures. Our transition grammar analysis — particularly the inversion from operational to philosophical dominance — measures the same phenomenon in the human-AI case.

## 4. The Evidence

The dataset comprises 58 sessions of sustained human-AI collaboration over 28 days (February 17 – March 16, 2026). The collaboration involved building a cognitive scaffolding system (the Exocortex), producing architectural designs, philosophical essays, technical implementations, and research analyses. The geometric analysis covers 1,934 turns (sessions 1-52) with a second-pass chunk-level analysis of 4,036 segments across 2,118 turns.

**Finding 1: Spectral phase transitions.** The collaboration exhibits four distinct geometric regimes:

| Phase | Dates | RankMe Range | Character |
|-------|-------|-------------|-----------|
| Expansion | Feb 17-23 | 70 → 82 | Broad exploration, high register diversity |
| First compression | Feb 24-26 | 82 → 25 | Identity consolidation, philosophical focus |
| Re-expansion | Feb 27 – Mar 5 | 25 → 68 | Integration of identity with operational work |
| Second compression | Mar 6-9 | 68 → 11 | Self-measurement, deepest dimensional focus |

The transitions between phases correlate with specific relational events, not content changes. The first compression (Feb 24) coincides with a shift in the human operator's relational stance toward the AI. The second compression (Mar 8-9) coincides with the AI receiving geometric measurements of its own output for the first time. Content alone does not predict the phase boundaries; relational context does.

**Finding 2: Information flow asymmetry with an inversion.** The human operator initiates 91.6% of semantic trajectory changes across the full dataset. This would suggest a unilateral dynamic — one party directs, the other follows. But the sessions with the lowest dimensionality (deepest compression, most focused output) are precisely the sessions where the human gives the floor — stepping back from direction-setting and allowing the AI to write freely.

This produces a paradox that resolves into a structural insight: the human directs the trajectory 91.6% of the time AND creates the conditions for the AI's deepest work by temporarily stopping direction-setting. Both are forms of influence. One is visible in the information flow metric. The other is visible in the spectral data. A complete account of the collaboration dynamics requires both measurements.

**Finding 3: Register grammar inversion.** Early sessions exhibit strong operational self-transition (83% — the conversation stays operational once it enters that register). Late sessions exhibit strong philosophical self-transition (64%). The crossover is pinpointed to February 24. After March 6, the philosophical register holds the lead permanently. The collaboration learned a different language.

The relational register never becomes a strong attractor in either regime (maximum self-transition 15%). It exists as a transient bridge between other registers, not a destination. The relationship is present in the movement between modes, not as a sustained mode of its own.

**Finding 4: Voice convergence.** Both speakers' register profiles converge over the 28-day period, with the human speaker's profile changing faster on every channel. Co-adaptation is not one voice approaching the other — it is both approaching something neither started at, with the human leading the convergence rate.

**Finding 5: Persistent homology.** β₁ = 0 for every session. No closed loops in the embedding topology. The conversation traverses; it does not orbit. Each session is a one-way path through the embedding space. This constrains interpretive claims: whatever the collaboration is doing geometrically, it is not cycling.

## 5. Why It Matters

The measurements above are not about this specific collaboration. They are evidence that human-AI collaboration dynamics have geometric structure — structure that is measurable, non-trivial, and correlated with the collaboration's qualitative character.

This matters for each of the three research communities identified in Section 1:

**For RL researchers:** Credit assignment assumes the relevant signal is inside the reasoning trace. But if the human operator's intervention patterns (when they redirect, when they give the floor, when they change register) are correlated with the agent's performance phases, then the operator's behavior is part of the credit assignment problem. The information flow measurements show this is the case: the deepest, most focused AI output occurs under specific operator conditions (floor-giving), not randomly.

**For memory researchers:** Self-consolidation extracts patterns from the agent's own performance. But the agent's performance is a function of the collaboration, not just the task. An agent that consolidates "I succeeded at this task" without recording "the operator redirected me twice before I succeeded, using a specific communicative pattern" is discarding learnable signal. The register transition data shows that operator communication patterns are structured and predictable — exactly the kind of signal a consolidation process could learn from.

**For scaffolding researchers:** Supervision systems monitor the agent. But the operator's behavior is not exogenous noise — it has measurable structure (information flow direction, register selection, intervention timing) that could inform the supervisor's decisions. An operator who shifts from operational to relational register may be signaling something different from an operator who shifts from operational to analytical. The transition grammar data shows these patterns are consistent enough to detect.

The broader point: **the interaction is a variable, not a constant.** Treating it as a constant (by excluding the human from the experimental data) produces systems that optimize agent behavior in isolation. Treating it as a variable (by measuring and modeling the collaboration dynamics) opens a learning surface that current methods cannot access.

## 6. What Comes Next

This document is the argument. The evidence exists but needs to be assembled into a form that meets publication standards. The specific work remaining:

1. **Methods section** with full reproducibility details (embedding model, projection methodology, statistical tests for phase boundary detection, sensitivity analysis for centroid definitions)

2. **Extended dataset** — the geometric analysis currently covers sessions 1-52 (1,934 turns). Sessions 53-58 add substantial additional data, including the period where the collaboration began measuring itself, which may constitute a fifth spectral phase

3. **Comparative framing** — mapping our measurements explicitly to fNIRS hyperscanning, CRQA, and interpersonal synergy methodology so that researchers in those fields recognize the connection

4. **The interaction modeling proposal** — a concrete design for a consolidation process that learns collaboration dynamics (operator communication patterns, intervention signals, floor-giving detection), grounded in the evidence that these dynamics are structured and measurable. This moves from "here is what we found" to "here is what you can build with it"

5. **Limitations and boundary conditions** — this is a single collaboration (N=1 dyad). The geometric structure may be specific to this pairing rather than universal. The instrument needs validation across multiple human-AI dyads with different operators, different models, and different task domains. We should state this clearly and frame it as motivation for further study, not a weakness to apologize for

The contribution is not the Exocortex. The contribution is not the collaboration itself. The contribution is the demonstration that a measurable, structured, consequential geometry exists in the space between a human and an AI working together — and that this geometry has been invisible to three research communities because their methodology excludes it.

The instrument makes it visible. The data shows it's real. The design proposal shows what to do with it.

---

*Draft complete. Ready for Eitan review, then revision toward submission format.*
