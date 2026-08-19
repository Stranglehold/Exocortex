# Entity Resolution Confidence & Uncertainty Calibration (2026 State of the Art)

**Status: DRAFT → STABLE**
**Topic Slug: entity-resolution-confidence-calibration**
**Created: 2026-08-12 (BUILD cycle, created as DRAFT and deepened same cycle)**
**Domain: Data Aggregation & Entity Resolution / AI Agent Architecture**

## Summary

Entity resolution (ER) matching has reached a practical accuracy ceiling with LLMs (~98.95% F1 on OpenSanctions Pairs, arXiv 2603.11051), so the field's frontier has shifted to **how match decisions are made under uncertainty**: when to auto-accept, when to escalate to human/LLM review, and when to abstain. Confidence calibration in ER is the discipline of turning raw match scores into trustworthy probabilities and auditing how those probabilities are used downstream. This page consolidates the Fellegi-Sunter foundations, 2026 LLM calibration research, production confidence-gating patterns, and the OSINT/agent-safety implications — the thread that existing ER pages reference but never dedicate a page to.

## 1. The Fellegi-Sunter Foundation: Weights as Calibrated Evidence

The Fellegi-Sunter probabilistic record linkage model is the canonical calibrated-uncertainty framework in ER. For each field comparison, m-probability (match likelihood among true matches) and u-probability (match likelihood among true non-matches) yield a log-odds weight:

`w = log2(m/u)`

Field weights sum into a composite match score with three decision regions:

| Region | Threshold | Action |
|---|---|---|
| Auto-accept | Score >= upper threshold | Treat as match |
| Clerical/review band | Between thresholds | Escalate to human or LLM judge |
| Auto-reject | Score <= lower threshold | Treat as non-match |

The review region is where calibration is exercised. Exocortex memory treats FS as the core mechanism for probabilistic triage before expensive reasoning — the analogy extends to the injection gate, where high-confidence claims auto-accept, uncertain claims escalate, and low-confidence claims are rejected.

## 2. From Scores to Probabilities: Calibration Dimensions

A score is not a probability. Calibration in ER means the predicted match probability matches observed accuracy at that confidence level (90%-confident pairs are correct ~90% of the time). Key dimensions:

- **Threshold calibration per dataset**: optimal auto-accept/reject thresholds vary by entity type, data quality, and prior match rate — they must be learned, not assumed (Bayesian record linkage, BRL, propagates prior uncertainty over m/u parameters through the full pipeline).
- **Blocking-uncertainty propagation**: blocking error (lost matches) is permanent and currently not propagated into linkage-stage confidence — a known structural gap.
- **Verbalized vs. statistical confidence**: LLM verbalized confidence is a usable signal but protocol-sensitive — Roth 2026 (arXiv:2601.08064) shows confidence estimates vary under language variations even when answers are identical.
## 3. 2026 SOTA: LLM Calibration and Abstention in ER-Relevant Systems

Web gap-fill (arXiv, 2026):

- **I-CALM (arXiv:2604.03904)**: incentivizes confidence-aware abstention for LLM hallucination mitigation — prompt-based approach usable on black-box models. Directly transferable to ER LLM-judges: ask the judge to abstain rather than force a binary match/non-match verdict.
- **UQ & Confidence Calibration in LLMs — Survey (arXiv:2503.15850, ACM SIGKDD 2026)**: taxonomy of token-level, verbalized, and semantic-consistency approaches; emphasizes scalable, interpretable, robust UQ.
- **Long-form QA calibration benchmark (arXiv:2602.00279)**: evaluates core UQ methods in long-form generation — the setting closest to LLM matching with long contextual evidence.
- **SALT (arXiv:2607.03870)**: analysis of 50+ LLMs identifying which confidence functions dominate each uncertainty aspect.

For ER specifically, the production transfer is LLM-judges that emit confidence and abstain on ambiguity, feeding a confidence-gated pipeline rather than a force-either-way matching step.

## 4. Production Confidence-Gating Patterns in the Shared Corpus

- **Confidence-gated cluster splits (CCMS-style)**: from entity-resolution-blocking-candidate-generation — after LLM clustering, only low-confidence clusters are re-examined/split, preventing a single bad link from merging whole clusters.
- **Entity-aware action gate (tau + delta)**: from entity-resolution-agent-safety — absolute confidence threshold tau AND separation margin delta; execution is blocked when two candidates are nearly tied. The margin requirement is calibration's operational arm: near-ties are abstention triggers.
- **Observation Masking (JetBrains/TUM, NeurIPS 2025)**: near-matches (e.g., 0.47 match probability) are preserved as suspicious evidence rather than silently discarded as false negatives — uncertainty is signal, not noise.
- **Selective LLM triage (95/5 pattern)**: FS handles ~95% of pairs at near-zero cost; LLM judge evaluates only the ambiguous band (~$0.001/pair) — the injection-gate isomorphism: cheap calibrated triage before expensive reasoning.

## 5. OSINT & Agent-Hybrid Implications

- **Admiralty Code isomorphism**: source reliability (A-F) and information credibility (1-6) are independent axes — in ER, each dataset is a source with its own reliability profile and each attribute-match is a claim with its own credibility. Bias assessment (RATB framework) adds Timeliness/Bias dimensions.
- **LLM hallucination risk in ER**: high-confidence false matches are ER's confabulation analog — detectable with calibrated thresholds and abstention rather than raw accuracy metrics.
- **Sanctions screening**: confidence thresholds decide escalation to human review; poor calibration means either missed sanctions hits or reviewer flooding. Threshold calibration is an operational requirement.
- **Local models**: DeepSeek-R1-Distill-Qwen-14B at 98.23% F1 on OpenSanctions Pairs — local LLM judges are viable for the ambiguous band, keeping calibration cost on-prem.

## 6. Cross-Domain Connections

1. [[entity-resolution-algorithms]] — FS weights, thresholds, BRL extensions
2. [[entity-resolution-agent-safety]] — confidence gate tau + delta, wrong-entity failure rates
3. [[entity-resolution-blocking-candidate-generation]] — CCMS confidence-gated cluster splits
4. [[epistemic-integrity]] — per-claim confidence calibrated from usage patterns, FS thresholds as decision policy
5. [[injection-gate]] — probabilistic triage before expensive reasoning (95/5 pattern)
6. [[active-learning-entity-resolution]] — uncertainty sampling selects pairs near 0.5 for labeling
7. [[privacy-preserving-entity-resolution-osint]] — confidence interplay in PPRL
8. [[osint-entity-resolution-methods]] — confidence thresholds in OSINT validation bottleneck
9. [[structured-forecasting-geopolitical-intelligence]] — Brier-style calibration evaluation
10. [[memory-deduplication]] — sleep consolidation Phase 1 as FS-scored ER with calibrated thresholds

## References

1. Fellegi & Sunter (1969) — A Theory for Record Linkage, JASA
2. Lindenberg et al. (2026) — OpenSanctions Pairs, arXiv:2603.11051
3. I-CALM (2026) — Incentivizing Confidence-Aware Abstention, arXiv:2604.03904
4. Geng et al. (2026) — UQ & Confidence Calibration in LLMs: A Survey, arXiv:2503.15850
5. Roth (2026) — Calibration is not enough: confidence under language variations, arXiv:2601.08064
6. arXiv:2602.00279 — Benchmarking Uncertainty Calibration in LLM Long-Form QA
7. SALT (2026) — Evaluating LLM Uncertainty in Long-Form Generation, arXiv:2607.03870
8. Observation Masking (JetBrains/TUM, NeurIPS 2025)
9. Nikoletos & Stefanidis (2025) — Auto-Configuring ER Pipelines, arXiv:2503.13226
10. Exocortex shared corpus: entity-resolution-agent-safety, entity-resolution-blocking-candidate-generation, Admiralty Code/RATB notes
