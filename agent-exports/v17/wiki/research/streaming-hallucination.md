# Streaming Hallucination: Trajectory Contamination Monitoring
**Created:** 2026-04-28T05:51Z
**Deepened:** 2026-05-10 (cycle 50 — contamination trajectory model, detection methodology, Exocortex integration plan, connection to epistemic integrity)
**Status**: Research paper summary — arXiv:2601.02170
**Category**: Real-time hallucination detection during generation.

## Abstract Summary (arXiv:2601.02170)
Streaming Hallucination investigates how early tokens in an LLM's output trajectory can contaminate subsequent generations even when the initial error is minor or ambiguous. Once a wrong path starts, entropy drops into deterministic mode locking in the hallucination before correction mechanisms can activate.

## Key Findings

### Trajectory Contamination Dynamics
- **3-5 token window**: Trajectory contamination begins within 3–5 tokens of first factual deviation. This is the critical detection window — earlier than previously assumed (prior work focused on end-of-sentence).
- **Entropy collapse**: During contamination, output token entropy drops sharply (from 6-8 bits to 2-3 bits) as the model commits to the hallucinated trajectory. Low entropy indicates high confidence in the wrong answer.
- **Confidence-entropy inversion**: Standard confidence scores correlate inversely with trajectory accuracy during contamination. The highest confidence often marks the deepest commitment to a false fact.
- **Irreversibility threshold**: After ~8-12 tokens of contaminated generation, the model cannot self-correct via simple probability reassignment. Re-rolling requires backtracking to the deviation point.

### Detection Methodology
1. **Early-trajectory entropy monitoring** — Measure token-level entropy during generation (not post-hoc). A drop below 3 bits within the first 10 tokens of a sentence signals potential contamination.
2. **Divergence from self-consistency baseline** — Compare streaming output tokens against a "shadow pass" (second sample with higher temperature). Significant divergence within first 5 tokens indicates trajectory instability.
3. **Factual consistency probe** — Insert a lightweight fact-checking prompt at the 5-token mark during generation. If the probe disagrees with the direction, flag for review.

## System Design Implications for Exocortex

### Real-time Detection Pipeline
1. **Inference wrapper hooks** — The [[inference-wrapper]] must expose token-level entropy metrics during streaming, not just cumulative output. Current architecture sends complete responses; need to add SSE stream with per-token entropy.
2. **Supervisor integration** — Early contamination signals feed as soft input to [[supervisor-loop]] CUSUM accumulator. Detection at token 5 allows L2 nudge before full sentence commitment (currently post-turn only).
3. **Entropy thresholds per domain** — Different task domains have different baseline entropy profiles (coding tasks have lower entropy naturally; creative writing has higher). [[entropy-as-signal]] and [[entropy-threshold-calibration-per-domain]] research must inform contamination detection thresholds.

### Contamination Scoring
Track per-turn contamination scores:
- `contamination_score = entropy_drop_magnitude × (1 - self_consistency_overlap)`
- Accumulate across conversation to identify turns where hallucination propagated downstream.
- Feed cumulative score to [[context-pruner]] to archive contaminated turns or flag for human review.

### Connection to Epistemic Integrity
Contamination detection provides a real-time signal to the [[epistemic-integrity]] layer. When contamination is detected during generation, the claim can be pre-flagged as "low confidence — possible contamination" before it enters the evidence ledger. This prevents contaminated claims from cascading through subsequent reasoning steps.

## Connection to Other Concepts
- **[[entropy-as-signal]]**: Early trajectory drift detected by same Shannon entropy monitoring described in 2604.03589. Streaming hallucination extends this from turn-level to token-level monitoring.
- **[[inference-wrapper]]**: Real-time hooks needed for pre-commit detection, not batch analysis after generation complete. Requires architectural changes to expose streaming metrics.
- **[[supervisor-loop]]**: Early deviation feeds as soft signal into CUSUM accumulator, preventing escalation to hard failure. Contamination detection at token 5 is a new input source.
- **[[first-hallucination-tokens]]**: Direct dependency — first-hallucination-tokens research identifies the earliest detectable tokens, streaming hallucination uses them to trigger intervention.
- **[[epistemic-integrity]]**: Contamination flagging before evidence ledger commitment prevents hallucinated claims from being treated as sourced facts.
- **[[context-pruner]]**: Contamination scores can inform which turns to archive more aggressively.

## Implementation Feasibility

### Current Exocortex Readiness
| Component | Readiness | Required Changes |
|-----------|-----------|-----------------|
| Inference wrapper | Partial | Token-level entropy not exposed; need SSE streaming support |
| Supervisor loop | Ready | CUSUM can accept token-level signals; need new signal type |
| Entropy monitoring | Ready | Shannon entropy calculation exists; need per-token granularity |
| Epistemic integrity | Ready | Can flag claims with contamination metadata |

### Minimum Viable Implementation
1. Add per-token entropy to inference wrapper output (requires .py change — human review needed)
2. Supervisor loop accepts `contamination_signal` with turn/token position/entropy value
3. Epistemic integrity adds contamination flag to claim metadata
4. Context pruner uses contamination score multiplier

## Future Research Directions
- **Adaptive detection thresholds**: Calibrate entropy thresholds per domain and per model (DeepSeek V4 vs GPT-4 have different entropy profiles)
- **Contamination rollback**: Develop protocol for backtracking to deviation point and re-generating without contamination
- **Cross-turn contamination tracking**: Does a hallucination in turn N contaminate reasoning in turn N+5 even if the specific claim was corrected?
- **Human-in-the-loop trigger**: When contamination score exceeds threshold, pause and show operator the detected deviation before continuing

## References
- arXiv:2601.02170 (Streaming Hallucination)
- arXiv:2604.03589 (Entropy as Signal) — foundational entropy monitoring framework
- arXiv:2603.14517 (First Hallucination Tokens) — complementary research on earliest detectable tokens

## Verification Status
Last verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.
Deepened: 2026-05-10 (cycle 50) with contamination trajectory dynamics, detection methodology (3 approaches), Exocortex integration plan, implementation readiness table, and future research directions (4 items).
