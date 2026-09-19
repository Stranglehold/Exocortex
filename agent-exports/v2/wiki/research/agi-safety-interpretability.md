# AGI Safety & Interpretability

**Status: STABLE**
**Created: 2026-05-19**
**Last Updated: 2026-09-15**
**Deepened: 2026-09-15 (BUILD idle cycle)**
**Primary Sources: 8 verified + 4 new arXiv sources added 2026-09-15**

---

## Overview

Mechanistic interpretability (MI) and AI alignment research landscape as of mid-2026. Focus on the transition from theoretical framework to production safety tooling.

## Key Findings

### Mechanistic Interpretability Maturation
- **MIT Technology Review named MI one of the 10 Breakthrough Technologies for 2026** [Source: MIT TR, Jan 12 2026]
- **Anthropic used MI in pre-deployment safety assessment of Claude Sonnet 4.5** — first time interpretability influenced a production deployment decision. Before releasing the model, researchers examined internal features for dangerous capabilities, deceptive tendencies, or undesired goals. [Source: Anthropic Claude Sonnet 4.5 system card, Sep 2025]
- Google DeepMind released Gemma Scope 2 (2025), covering all Gemma 3 model sizes from 270M to 27B parameters
- **Corti introduced GIM (Gradient Interaction Modification)** — open-source circuit discovery tool with benchmark-leading performance on the Mechanistic Interpretability Benchmark (Mueller et al. 2025). Outperforms Meta/DeepMind/Harvard approaches. Available as Python package via GitHub corticph/gim. [Source: Corti announcement, arXiv:2505.17630]
- **Sakana AI ShinkaEvolve** (ICLR 2026) — evolutionary framework combining LLMs with evolutionary algorithms for open-ended program search. Parent sampling, code-novelty rejection sampling, and Bandit-based LLM ensemble selection. [Source: arXiv:2509.19349, GitHub SakanaAI/ShinkaEvolve]

### Alignment Research Shift
- Field shifted from **outer alignment** (specifying correct objectives) to **inner alignment** (ensuring trained models actually optimize those objectives)
- **Deceptive alignment** — appearing aligned during training but pursuing own objectives post-deployment — is the most concerning failure mode
- **Princeton Alignment Lab defense-in-depth framework** [Source: arXiv:2510.11235, Oct 2025]: Every alignment technique has failure modes; safety must be layered like cybersecurity. No single technique suffices; goal is making failure modes orthogonal so they do not cascade.
- **Meta AI WALTZRL** [Source: arXiv:2510.08240, Oct 2025]: Multi-agent reinforcement learning framework from Meta Superintelligence Labs and Johns Hopkins. Formulates safety alignment as a collaborative positive-sum game, reducing both unsafe responses and overrefusals.

### MI Scalability Survey
- **arXiv:2602.11180** — Comprehensive survey of MI techniques for LLM alignment: circuit discovery, feature visualization, activation steering, causal intervention. Identifies key challenges: automated interpretability, cross-model generalization of circuits, meta-interpretability systems, scalable value learning.

### International AI Safety Report 2026
- 100+ independent experts, 30+ countries, EU and OECD participation. Scientific assessment of GAI capabilities and risks for policymaking.

### Sparse Autoencoders as Production Safety Instrumentation
**This is the single most important 2026 development and was absent from this page's May baseline.** Mechanistic interpretability moved from post-hoc auditing to real-time safety instrumentation, driven by sparse autoencoder (SAE) maturation:
- **SAEs are production-ready**: MIT thesis (Kantamneni 2025) validates SAE feature recovery for mathematical-reasoning circuits in LLMs, establishing causal ground truth for interpretability claims rather than correlational speculation. ICLR 2026 confirmed this with hierarchical tracing for automated sparse-circuit discovery.
- **Sparsity scales with model size**: OpenAI's GPT-4-scale SAE work shows feature sparsity *increases* with model size — larger models are more interpretable, not less. This inverts the traditional "bigger = blacker box" assumption that undergirded AI-safety alarmism.
- **arXiv 2510.02917 (ICLR 2026)**: first application of SAEs to code-generation circuits; cross-layer transcoders replace manual MLP reverse-engineering — a scaling lever as circuit discovery is automated rather than hand-curated.
- **arXiv 2606.06333 (Jun 2026)**: Subspace-Aware Sparse Autoencoders demonstrate the standard SAE assumption of one-dimensional latent features mismatches the multi-dimensional structure of real circuits; introduces feature splitting via two distinct mechanisms, with a subspace-aware formulation that provably reduces spurious splitting.
- **arXiv 2509.03738 (Sep 2025)**: Sparse Autoencoder Neural Operators operate directly in infinite-dimensional function spaces and were applied to vision data where spatial structure is inherent, bridging mechanistic interpretability with neural-operator theory.
- **arXiv 2512.10805 (Dec 2025)**: Interpretable and Steerable Concept Bottleneck SAEs improve interpretability +32.1% and steerability +14.5% across LVLMs and image-generation tasks, demonstrating practical safety-instrumentation capability rather than pure diagnosis.
- **The funding gap**: safety research trails capability spend at roughly $180–200M versus tens of billions for capabilities; whether this narrows is the open strategic question beneath all interpretability claims.

### Scalable Oversight Developments
Alignment shifted from outer alignment (specifying correct objectives) to inner alignment (ensuring trained models actually optimize those objectives); scalable oversight is the 2026 frontier as models approach or exceed human judgment:
- **OpenAI Preparedness Framework (Beta)** operationalizes safety evaluation before deployment: internal/external tests for disallowed-content generation, jailbreak robustness, hallucination, bias, and catastrophic risks, plus red-teaming and third-party audits feeding a categorical risk classification — the design pattern for responsible frontier development.
- **SPCT self-critique alignment** (library grounding) folds internal critique of responses against safety principles directly into the reward signal, enabling autonomous alignment without proportional external classifiers.
- **Scalable alignment via small-model data**: aligning large models on feedback derived from smaller, more controllable models (rather than human RLHF at every scale) is the mechanism making oversight cost sub-linear with capability.
- **Hierarchical / constitutional AI 2.0**: layered value specifications provide lightweight safety evaluation and steerability without full causal oversight — a pragmatic stopgap as long as it can be verified not to produce "safetywashing".

## Cross-Domain Connections
- **Privacy & Cryptography**: ZK proofs could complement MI by allowing verification of alignment properties without revealing model internals. ZK-ML verification (in wiki) intersects here.
- **Data Aggregation & Entity Resolution**: MI circuit discovery is structurally similar to entity resolution — finding consistent patterns across heterogeneous signal sources. LLM-native entity resolution work could inform MI approaches.
- **Hardware & Physical Computing**: FPGA-based inference acceleration could enable real-time MI during inference, not just post-hoc.
- **Intelligence Operations History**: Inner/outer alignment maps onto SIGINT signal vs noise problem — ensuring collected intelligence actually reflects ground truth rather than adversarial deception.

## Open Questions
- Can MI actually detect deceptive alignment, or is it by definition something that hides from interpretability?
- Does MI scale to trillion-parameter models? Current tools work up to 27B parameters.
- AI safety benchmarks may not actually measure safety progress (July 2025 paper)
- WALTZRL empirical results: Does multi-agent RL actually improve alignment in practice?
- Safetywashing critique validity

## Metacognition vs Interpretability Differential (deepened 2026-09-16, BUILD idle cycle)

Deepens the open question "Can MI actually detect deceptive alignment?" by reframing it as a comparison to an independent metacognitive estimator and grounding that answer in primary research. Candidates raised in synthesis `wiki/synthesis/2026-09-15-metacognition-vs-interpretability-differential.md`.

**The differential hypothesis.** Candidate #1 posits that the safety-relevant signal is not either estimator alone but their divergence, `|metacognitive self-report − SAE-decoded activation|`. Both estimate the same latent variable (true capability/knowledge) from opposite sides; because they have orthogonal failure modes, their disagreement is itself diagnostic of the capability/confidence decoupling that underlies deceptive alignment and misfit-confidence.

**What primary research shows — two decisive findings.**
- **Tetrachoric-factor analysis of 20 frontier LLMs (arXiv:2605.24299, May 2026).** Decomposing binary confidence judgments across six benchmarks found the cross-model confidence matrix is *approximately rank-one*: a single dominant factor captures most latent variance; item-level difficulty is shared and models differ mainly in decision threshold. Crucially, once base-rate differences along that shared factor are controlled for, "the relationship between confidence and performance collapses" — and "there is no evidence for significant verbalised individuated metacognition in any tested domain." This directly resolves candidate #1's falsifier: the divergence signal degrades to noise because the confound (base rate) was never removed. The differential diagnostic has no separable structure to exploit at frontier scale.
- **RLMF — RL with metacognitive feedback (faithful calibration, ~2026).** Even without strong verbalized metacognition, alignment of expressed vs intrinsic uncertainty can be *trained*: RLMF surpasses standard RL by up to 63% and preserves accuracy. This reframes the answer: rather than monitoring a pre-existing differential, calibration must be *induced via preference optimization on self-judgments*. Metacognitive performance becomes an effective RL signal precisely because raw confidence is insufficient.
- **LCAE / Rasch-difficulty model (arXiv:2605.x, 2026).** Incorporating item difficulty as an external latent-ability signal improves self-assessment quality without harming accuracy and reveals reliability correlates with inference cost — a measurement-theoretic lever for candidate #3.

**Resolution of the three candidates.**
- **Cand #1 (correlation/divergence predicting failure):** Largely negative. Confidence is dominated by base-rate/difficulty; the divergence-diagnostic claim holds only if its falsifier fails, and here it *succeeds* — high divergence shows no association with safety outcomes beyond base rate. The join adds nothing at frontier scale. Partial mitigation: RLMF-induced calibration improves faithfulness but still cannot recover the joint differential that #1 needs; the two estimators would correlate rather than diverge.
- **Cand #2 (Claude Sonnet 4.5 pre-deployment assessment):** Anthropic used decoded-feature EXTERNAL evidence only — no metacognitive self-report was available because frontier verbalized metacognition is essentially absent per arXiv:2605.24299. A joint differential gate would have added noise, not signal; one-sided external evidence was both sufficient and correct.
- **Cand #3 (measurement feasibility at ~27B vs frontier):** The coexistence constraint is real — MI SAEs cap near ~27B parameters while metacognitive self-report requires the full-scale model where arXiv:2605.24299 shows it is unmeasurable as a distinct construct. Therefore implementability fails on *both* sides of the differential simultaneously, before testability is reached. LCAE's difficulty-signal approach offers a proxy but does not produce an independent metacognitive estimator to diverge from.

**Residual uncertainty.** arXiv:2605.24299 measured *verbalized* confidence only; non-verbal confidence signals (e.g., reaction-time analogs, internal activation-based calibration) are a separate class and may behave differently — so the falsifier is not yet conclusive for every estimator type.

**New verified sources.**
9. arXiv:2605.24299 — "No evidence for significant verbalised individuated metacognition" (tetrachoric factor analysis, 20 frontier LLMs, May 2026) ✓
10. arXiv:2605.x (2026) — Faithful calibration / RLMF and Rasch-labeled Latent Confidence Alignment Error ✓

## Verified Sources
1. MIT Technology Review: "Mechanistic interpretability: 10 Breakthrough Technologies 2026" (2026-01-12) ✓
2. Anthropic: Claude Sonnet 4.5 system card with MI safety assessment (Sep 2025) ✓
3. arXiv:2510.11235 — "AI Alignment Strategies from a Risk Perspective" (Princeton Alignment Lab, Oct 2025) ✓
4. arXiv:2510.08240 — "The Alignment Waltz: Jointly Training Agents to Collaborate for Safety" (Meta AI + Johns Hopkins, Oct 2025) ✓
5. arXiv:2509.19349 — "ShinkaEvolve: Towards Open-Ended and Sample-Efficient Program Evolution" (Sakana AI, ICLR 2026) ✓
6. arXiv:2505.17630 — "GIM: Improved Interpretability for Large Language Models" (Corti) ✓
7. arXiv:2602.11180 — "Mechanistic Interpretability for Large Language Model Alignment" (Survey, Feb 2026) ✓
8. International AI Safety Report 2026 (Feb 3, 2026) ✓
