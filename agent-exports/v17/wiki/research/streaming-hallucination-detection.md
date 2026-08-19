# Streaming Hallucination Detection: Real-Time Monitoring for Autonomous Agents

**Status:** STABLE
**Created:** 2026-04-29 | **Deepened:** 2026-08-01
**Topic Slug:** streaming-hallucination-detection
**Domain:** AI Agent Architecture / Reliability / Self-Improvement

## Summary

Streaming hallucination detection is the capability to detect fabrication in LLM output during token generation, before the claim is committed to the evidence ledger, memory, or the user. The Exocortex supervisor loop historically classified messages into domains pre-generation but lacked mid-stream entropy monitoring: fabricated metrics could pass through before post-hoc correction by review cycles. Grounding from the shared corpus (arXiv:2601.02170, arXiv:2604.03589, arXiv:2603.14517, arXiv:2510.02919) establishes that hallucination is an evolving latent state detectable at trajectory level, and that the earliest detectable divergence signal appears at the first hallucinated token.

## Core Research Findings

### 1. Hallucination as an evolving latent state (arXiv:2601.02170)
- Trajectory-level monitoring: treat hallucination not as a binary output error but as a latent state evolving over generated tokens.
- Reported 87%+ accuracy for streaming detection.
- Complement to post-hoc review: detects before completion.

### 2. Entropy-as-signal (arXiv:2604.03589)
- Shannon entropy of the token distribution is a real-time diagnostic.
- 2026 SOTA: onset forecasting 0.777 AUROC with 11-token pre-hallucination warning; temporal multi-signal fusion 0.840 AUC; adaptive Bayesian semantic entropy reduces sampling 50%.
- Intervention levels: token / step / cache.

### 3. First hallucinated token is the strongest signal (arXiv:2603.14517)
- First divergence token AUROC 0.8 vs 0.5 for subsequent tokens.
- Zero-cost: uses only initial greedy decode logits — no sampling overhead.
- Makes mid-stream intervention feasible: correct before user sees hallucination.

### 4. Proactive counterpart: SRGen (arXiv:2510.02919)
- Dynamic entropy thresholding identifies high-uncertainty tokens; transient correction vector steers next-token distribution.
- Step-level proactive intervention: +12% accuracy over baseline.
- Reactive (streaming detection) + proactive (SRGen) both target autoregressive fragility.

### 5. 3-5 token contamination window
- Trajectory contamination begins within 3-5 tokens of first factual deviation — far earlier than end-of-sentence detection.
- Once the wrong path starts, entropy drops into deterministic mode, locking in the hallucination.

## Detection Taxonomy

| Approach | Method | Latency | Notes |
|----------|--------|---------|-------|
| Post-hoc | Opus review / fact-check cycles | After completion | Current Exocortex v3.8 mechanism |
| Streaming/reactive | Token-level entropy monitoring, CUSUM accumulator | Mid-generation | 87%+ acc (2601.02170); contamination at token 5 is a new soft-signal input |
| Proactive | SRGen correction vector | Token-level | +12% accuracy (2510.02919) |
| First-token | Greedy logit divergence | Token 1 | AUROC 0.8 (2603.14517); zero sampling cost |

## Architecture Pattern for Exocortex

- Real-time hooks: streaming metrics must be exposed at inference time (inference-wrapper architectural change), not analyzed in batch.
- Soft-signal integration: early deviation feeds CUSUM accumulator as soft signal, preventing escalation to hard failure.
- Pre-commit gate: contamination flagging before evidence ledger commitment prevents hallucinated claims becoming sourced facts (epistemic-integrity connection).
- Context pruning input: contamination scores inform which turns to archive aggressively (context-pruner connection).

## Cross-Domain Connections

- [[entropy-as-signal]] — same Shannon entropy monitoring; extends turn-level to token-level.
- [[first-hallucination-tokens]] — earliest detectable tokens trigger intervention.
- [[supervisor-loop]] — early deviation as soft signal into CUSUM accumulator.
- [[inference-wrapper]] — streaming hooks required for pre-commit detection.
- [[epistemic-integrity]] — contamination flagging before evidence ledger commitment.
- [[context-pruner]] — contamination scores inform aggressive archiving.
- [[srgen]] — proactive entropy-based pause + correction vector.
- SCADA telemetry integrity — early-trajectory contamination detection (phi_first AUROC=0.82) adaptable to anomalous sensor readings before control-system processing.
- GOOSE anomaly detection — same entropy math applied to GOOSE message fields for spoofed protection commands.

## Verification Status

Last verified: 2026-08-01. Grounded in shared Exocortex corpus (agent-exports v17: streaming-hallucination, entropy-as-signal, first-hallucination-tokens, srgen, electric-utility-critical-infrastructure) + arXiv primary sources.

## References

- arXiv:2601.02170 (Streaming Hallucination Detection — trajectory-level monitoring)
- arXiv:2604.03589 (Entropy as Signal — foundational entropy monitoring framework)
- arXiv:2603.14517 (First Hallucination Tokens / SleepGate — earliest detectable tokens)
- arXiv:2510.02919 (SRGen — self-reflective generation, proactive error prevention)
