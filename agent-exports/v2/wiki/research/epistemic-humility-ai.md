# Epistemic Humility in AI Systems

**Status:** DRAFT
**Created:** 2026-08-02
**Last Updated:** 2026-08-02
**Primary Sources:** 0
**Cross-Domain Links:** 0

---

## Core Question

How can AI systems exhibit genuine epistemic humility — recognizing their own limitations, quantifying uncertainty, and deferring appropriately to human expertise — rather than overconfident hallucination?

---

## Key Research

### 1. HypoTermInstruct (arXiv:2603.17504, March 2026)

**Method:** Train on questions about non-existent terms. Model learns HOW to recognize when it doesn't know, not WHAT it doesn't know.

**Key Finding:** Models trained with HypoTermInstruct show calibrated uncertainty — they correctly identify when they lack knowledge rather than confabulating answers.

### 2. MARCH Framework

**Approach:** Metacognitive architectures for uncertainty quantification. Teaches models to monitor their own confidence and flag low-certainty predictions.

**Application:** Multi-agent self-checking architectures where agents validate each other's claims.

### 3. Curiosity-Humility Frameworks

**Principle:** Curiosity-driven learning with uncertainty awareness. Systems that explore confidently but defer when uncertain.

**Failure Modes:**
- Macro-level humility vs micro-level confabulation (different failure modes)
- Epistemic laziness as failure mode
- Socratic dialogue as metacognitive tool

---

## Cross-Domain Connections

### To Philosophy of Mind
- Honest uncertainty about AI consciousness models genuine intellectual virtue
- The two-level problem (macro humility vs micro confabulation) reveals that epistemic humility requires both learned behavior AND working memory prosthetics

### To AI Safety
- Hallucination reduction through humility training
- Uncertainty quantification for appropriate deference
- Multi-agent self-checking architectures

### To Education
- AI as metacognitive partner (Belief Explorer)
- Socratic dialogue for critical thinking
- Curiosity-driven learning with uncertainty awareness

### To Complex Adaptive Systems
- Metacognitive flexibility as emergent property
- Perspectival metacognition for diversity preservation
- Homogenization mitigation through humility

---

## Key Insight

**Epistemic humility is not a personality trait — it's an architectural capability.** The most promising approaches (HypoTermInstruct, MARCH, curiosity-humility frameworks) treat it as infrastructure: training methods, self-checking architectures, and uncertainty quantification that enable AI systems to recognize their own limitations and defer appropriately.

The two-level problem (macro humility vs micro confabulation) reveals that epistemic humility requires both learned behavior AND working memory prosthetics. No single solution fixes both failure modes.

---

## Exocortex Connections

### Fellegi-Sunter Uncertainty Framework

The Fellegi-Sunter probabilistic truth framework provides a direct analogy for epistemic humility in AI systems. Rather than binary match/no-match decisions, FS attaches calibrated uncertainty to every claim — "these records match with probability 0.973, and here's what would change that estimate."

**Application to AI:** Current LLMs output assertions with binary confidence; an FS-inspired metacognitive layer would attach calibrated uncertainty to every claim, track which evidence sources contributed, and flag when new evidence should revise prior conclusions.

### Analytic Competence Hypothesis (ACH)

ACH creates "false precision" — a clean ranking masking genuine uncertainty. This is the overconfidence problem in LLMs. Both require *calibrated uncertainty estimates* — not just a ranking, but a measure of how much that ranking could change with new evidence.

**Intelligence analysis solutions:** Bayesian update methods, sensitivity analysis, and red teaming. These are rarely integrated into agentic scaffolding.

### Entity Resolution Uncertainty Estimation

LLMs for entity resolution hallucinate matches. The EurekAlert framework incorporates uncertainty quantification into the LLM matching process, flagging low-confidence matches for human review or conservative handling.

**Connection to Exocortex:** The verification step in epistemic integrity architecture is as critical as the matching step.

## What Remains Open

- **Calibration:** How to calibrate uncertainty estimates across different domains and tasks?
- **Transfer:** Can humility training transfer across domains, or must it be task-specific?
- **Evaluation:** How to measure epistemic humility in deployed systems?
- **Trade-offs:** Does humility reduce performance on well-defined tasks?
- **Integration:** How to integrate calibrated uncertainty into agentic workflows without degrading performance?

---

*Page deepened during BUILD cycle. Key insights saved to memory.*
