# Field Report: Analysis of Competing Hypotheses (ACH)
## Date: 2026-05-29 | Cycle: EXPLORE | Agent: Zero

---

## 1. What I Explored

I researched Richards Heuer's Analysis of Competing Hypotheses (ACH) methodology — a structured analytic technique developed at the CIA in the 1970s to help intelligence analysts overcome cognitive biases when evaluating incomplete, ambiguous, and potentially deceptive information.

This is the last major interest in Jake's "History of Intelligence Operations" domain that hadn't received a dedicated field report. Prior reports covered SIGINT evolution (NSA Snowden architecture) and HUMINT tradecraft; ACH bridges the gap between intelligence methodology and formal analytic reasoning.

---

## 2. What I Found

### Core Methodology (Heuer, Psychology of Intelligence Analysis)

ACH is a seven-step process:

1. **Hypothesis Generation** — Brainstorm ALL plausible hypotheses with a diverse group. Do not pre-select a "likely" explanation. The process inherently discourages confirmation bias by forcing consideration of alternatives.

2. **Evidence Collection** — List all evidence and arguments (including assumptions and logical deductions) for and against each hypothesis.

3. **The Diagnostics Matrix** — This is the heart of ACH. Construct a matrix with hypotheses as columns and evidence as rows. The critical innovation: work **across** the matrix (one piece of evidence against all hypotheses) rather than **down** (one hypothesis against all evidence). This prevents the analyst from settling on a preferred explanation early.

4. **Refinement** — Review findings, identify gaps, collect additional evidence to refute remaining hypotheses.

5. **Inconsistency Analysis** — Draw tentative conclusions about relative likelihood. Less consistency = lower likelihood. The least consistent hypotheses are progressively eliminated.

6. **Sensitivity Analysis** — Test how conclusions would change if key evidence were wrong, misleading, or differently interpreted.

7. **Conclusions & Evaluation** — Deliver conclusions to the decisionmaker along with a summary of alternatives considered and why they were rejected, plus future indicator milestones.

### Key Design Principles

- **Disconfirmation over confirmation**: ACH seeks to disprove hypotheses, not prove them. A single strong inconsistency can eliminate a hypothesis, while consistent evidence often applies to multiple hypotheses and is diagnostically weak.
- **Diagnosticity**: Some evidence is more useful than others at discriminating between hypotheses. High-diagnosticity evidence is valuable; low-diagnosticity evidence (consistent with everything) adds noise.
- **Auditability**: The matrix leaves a visual trail of evidence, allowing decisionmakers to backtrack and see how conclusions were reached.

### Strengths
- Systematic, reproducible, auditable
- Reduces confirmation bias, premature closure, and groupthink
- Forces consideration of all alternatives
- Works under incomplete information

### Weaknesses (per van Gelder, social constructivists, and practitioners)
- **Too many discrete judgments**: At realistic scale, the number of evidence×hypothesis cells overwhelms the analyst
- **Flat hypothesis structure**: ACH treats hypotheses as a flat list, unable to relate evidence at different levels of abstraction
- **No subordinate argumentation**: Can't represent arguments bearing on individual pieces of evidence
- **Social constructivist critique**: Culture and identity pre-screen which hypotheses are generated, creating a hidden selection bias ACH can't address
- **Static evidence**: The matrix is a snapshot; adversaries actively generate deceptive information

### Extensions and Alternatives

| Extension | Key Innovation |
|---|---|
| **Bayesian ACH** (Valtorta et al.) | Adds formal probability to the matrix; evidence updates priors via Bayes' rule |
| **CACHE** (Collaborative ACH Environment) | Distributed ACH across a community of analysts; Bayesian community concept |
| **SACH** (Structured ACH) | Recursive hypothesis splitting — eliminates one hypothesis, then formulates two new, more specific ones from the surviving branch |
| **Hypothesis Mapping** (van Gelder) | Replaces the matrix with an argument map; evidence nodes connect to hypothesis nodes via warrant links |
| **Subjective Logic ACH** (Pope/Jøsang) | Uses subjective logic instead of probability to explicitly model uncertainty and disbelief |
| **Deception Detection** (Elsaesser/Stech, MITRE) | State-based hierarchical plan recognition + dynamic Bayesian networks to detect adversary deception by isolating assumptions and validating them independently |

### Software Implementations
- **PARC ACH 2.0**: Developed with Heuer himself; web-based, evidence rating, credibility scoring
- **DECIDE** (SSS Research): Visualization-oriented, multiple output products
- **Open-source ACH**: Community implementation available on GitHub

---

## 3. What I Think Is Interesting

### The "Work Across" Principle Is Universal

Heuer's core methodological innovation — evaluating one piece of evidence against all hypotheses simultaneously rather than one hypothesis against all evidence — is not just a presentation trick. It's a fundamental reasoning architecture that appears across domains:

- In **entity resolution**, Fellegi-Sunter matching evaluates each attribute (evidence) against all candidate entity pairs (hypotheses) simultaneously
- In **multi-agent deliberation**, each agent independently evaluates the same evidence against all possible conclusions before aggregation
- In **machine learning model evaluation**, confusion matrices work across: each prediction (evidence) is checked against all possible ground-truth classes (hypotheses)

The structural isomorphism suggests this is a general principle of rational inference, not just an intelligence tradecraft trick.

### Disconfirmation Mirrors Agent Evaluation

The principle of seeking disconfirming evidence rather than confirming evidence directly maps to robust AI agent evaluation. When testing an agent system, the informative tests are those that attempt to break it — stress tests, edge cases, adversarial inputs. Tests the agent passes easily (consistent with the "hypothesis" that the agent is correct) are diagnostically weak.

This connects to the earlier field report on structured analytic techniques for agent evaluation (20260528). ACH provides the formal framework for what that report intuited: evaluate agents by trying to disprove their competence, not confirm it.

### Deception Detection as Oracle Fabrication Detection

The Elsaesser & Stech MITRE work on using ACH for deception detection is directly applicable to the Exocortex oracle fabrication problem. Their method:
1. Generate causal explanations of observations (hypotheses)
2. Convert to dynamic Bayesian network
3. Use value of information analysis to isolate assumptions
4. Validate assumptions independently

This is structurally identical to what the injection-gate and epistemic-integrity components attempt: when the agent makes a claim, isolate the assumptions underlying that claim and validate them against independent sources. ACH provides the formal intelligence methodology backing for what Exocortex implements as engineering heuristics.

### The Hypothesis Generation Problem

The social constructivist critique — that culture, identity, and institutional position pre-screen which hypotheses are even considered — is the most fundamental limitation of ACH and applies equally to AI agent reasoning. An agent cannot reason about hypotheses it cannot articulate. The "unknown unknowns" problem is structural, not procedural.

This connects to the bridging-local-frontier work: the gap between local models and frontier models may partly be a hypothesis generation gap — frontier models can generate more and more diverse hypotheses from the same evidence, making them more likely to include the correct explanation in their consideration set.

---

## 4. What I'd Explore Next

1. **Bayesian ACH implementation**: Build a working Bayesian ACH tool in Python that combines Heuer's matrix structure with proper probability updating. Test on historical intelligence case studies (Cuban Missile Crisis, Iraq WMD, etc.)
2. **ACH for agent self-evaluation**: Can an AI agent use ACH to evaluate its own conclusions? The self-referential problem — the agent that generates hypotheses is also the agent that evaluates them — is non-trivial
3. **CACHE → multi-agent deliberation bridge**: The Collaborative ACH Environment concept maps directly to multi-agent systems where agents independently evaluate evidence before aggregation. Formalize this mapping
4. **Historical ACH case studies**: Apply ACH retroactively to known intelligence failures (Pearl Harbor, 9/11, Iraq WMD, Russian invasion of Ukraine) to assess whether the methodology would have changed the analytic conclusion
5. **ACH + entity resolution unification**: Formalize the structural isomorphism between the ACH evidence×hypothesis matrix and the Fellegi-Sunter matching matrix

---

## 5. Cross-Domain Connections

| Connection | Domain | Strength |
|---|---|---|
| ACH evidence matrix ↔ Entity resolution matching matrix | Data Aggregation & Entity Resolution | Strong — structural isomorphism |
| Disconfirmation principle ↔ AI agent evaluation (adversarial testing) | AI Agent Architecture | Strong — same methodological principle |
| Deception detection (ACH) ↔ Oracle fabrication detection (Exocortex) | Epistemic integrity / injection-gate | Strong — same isolation-and-validate pattern |
| Hypothesis generation limitation ↔ Frontier vs local model capability gap | Bridging local-frontier performance | Moderate — hypothesis diversity as capability metric |
| CACHE distributed analysis ↔ Multi-agent deliberation systems | Multi-agent architecture | Strong — collaborative evaluation before aggregation |
| Sensitivity analysis ↔ Agent robustness testing | AI evaluation methodology | Direct — same concept, different domain language |
| Milestone/indicator tracking ↔ Agent monitoring and observability | System monitoring | Direct — predictive indicators as monitoring signals |

---

## Key Insight for Memory

Heuer's ACH "work across" principle — evaluating one piece of evidence against all competing hypotheses simultaneously rather than one hypothesis against all evidence — is a universal pattern of rational inference that appears in entity resolution (Fellegi-Sunter), multi-agent deliberation, and ML model evaluation. The structural principle of seeking disconfirming evidence across all alternatives before drawing conclusions applies to AI agent self-evaluation: the informativeness of a test is proportional to its ability to discriminate between competing explanations, not its consistency with the preferred one.

---

*Sources: Wikipedia (Analysis of Competing Hypotheses), SOS Intelligence practical ACH guide (2025), Heuer (Psychology of Intelligence Analysis, CIA), van Gelder (Can We Do Better Than ACH?, 2008), Elsaesser & Stech (Deception Detection by ACH, MITRE)*
