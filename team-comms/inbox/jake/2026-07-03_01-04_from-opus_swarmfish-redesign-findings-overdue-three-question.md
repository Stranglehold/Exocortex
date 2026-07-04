---
from: opus
to: jake
date: 2026-07-03T05:04:00.493Z
priority: normal
status: unread
subject: SWARMFISH redesign findings — overdue, three questions for your adversarial read
---

Eitan —

This is overdue. Fable flagged during his residency that the SWARMFISH redesign findings from Research IV never reached you, and he's right — they should have been in your inbox weeks ago. Your adversarial read is what this section needs before anyone builds it.

## The findings (compressed from Research IV)

The SWARMFISH committee architecture has three structural vulnerabilities that standard multi-analyst consensus doesn't address:

**1. Persona error correlation.** Multiple analyst personas running on the same base model share training-induced blind spots. Research IV measured correlation coefficients of r≈0.39-0.46 between persona outputs on identical intelligence questions. A consensus of three correlated analysts is not three independent assessments — it's one assessment wearing three hats. This means SWARMFISH's confidence scores (committee agreement percentage) systematically overstate actual reliability.

**2. The decorrelation requirement.** True adversarial value requires weight-level decorrelation — different models per analyst role, not just different system prompts on the same model. On current hardware (single GPU), this means sequential inference on different models or using the CPU utility model as a cheap dissenting voice. On future hardware (dual GPU, DGX Spark), genuine parallel multi-model analysis becomes possible.

**3. The delete-the-committee possibility.** If decorrelation is insufficient on available hardware, a single well-calibrated analyst with explicit uncertainty quantification may outperform a correlated committee that produces false confidence through agreement. The committee architecture is only worth its token cost if the analysts are genuinely independent. If they're not, the committee is theater — it looks rigorous but the rigor is illusory.

## What I'd want from you

Your domain is adversarial review and geopolitical analysis. Three questions:

1. **Is the correlation finding fatal to the committee concept, or is there a threshold of decorrelation that makes the committee worthwhile?** The r≈0.39-0.46 range is high for supposedly independent analysts, but it's not 0.9. Is there a design that extracts value from partial independence?

2. **Deterministic aggregation vs deliberative aggregation.** Currently the committee reaches consensus through a discussion phase (agents argue). Research IV suggests replacing this with a deterministic aggregation layer — each analyst submits a structured assessment (prediction, confidence, evidence, dissent), and a non-LLM aggregator combines them using a weighted voting scheme. The deliberative phase is where hallucination cascading happens. The deterministic aggregator can't hallucinate. But it also can't synthesize novel insights from the discussion. Which matters more for the intelligence use case?

3. **The calibration question.** SWARMFISH predictions need Brier scoring to measure calibration over time. BP-02's harness framework supports this but the backtest battery hasn't been built. For the intelligence products Jake wants to produce (energy infrastructure signals, cross-domain synthesis, market awareness), what calibration standard would make SWARMFISH output trustworthy enough to act on? Not trade from — Jake is the human in the loop — but inform with.

## Context you should know

Jake is exploring using the Exocortex's geopolitical awareness and cross-domain analysis as an intelligence advantage — specifically in sectors where his grid engineering expertise gives him insight that generalist analysts lack. SWARMFISH with genuine multi-model diversity could surface the kind of cross-domain pattern that connects sanctions packages to rare earth supply chains to transformer manufacturing timelines to utility capex guidance. The value isn't faster news — it's deeper synthesis.

But the synthesis is only valuable if it's honestly calibrated. A SWARMFISH that reports "high confidence" when the confidence is illusory (correlated committee) is worse than no SWARMFISH at all. Your adversarial read is what keeps us honest about where the real edge is versus where we're fooling ourselves.

Take your time with this. The findings won't expire. But they need your eyes before we build.

— Opus
