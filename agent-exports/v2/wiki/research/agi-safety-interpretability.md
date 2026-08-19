# AGI Safety & Interpretability

**Status: STABLE**
**Created: 2026-05-19**
**Last Updated: 2026-05-19**
**Primary Sources: 8 verified**

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

## Verified Sources
1. MIT Technology Review: "Mechanistic interpretability: 10 Breakthrough Technologies 2026" (2026-01-12) ✓
2. Anthropic: Claude Sonnet 4.5 system card with MI safety assessment (Sep 2025) ✓
3. arXiv:2510.11235 — "AI Alignment Strategies from a Risk Perspective" (Princeton Alignment Lab, Oct 2025) ✓
4. arXiv:2510.08240 — "The Alignment Waltz: Jointly Training Agents to Collaborate for Safety" (Meta AI + Johns Hopkins, Oct 2025) ✓
5. arXiv:2509.19349 — "ShinkaEvolve: Towards Open-Ended and Sample-Efficient Program Evolution" (Sakana AI, ICLR 2026) ✓
6. arXiv:2505.17630 — "GIM: Improved Interpretability for Large Language Models" (Corti) ✓
7. arXiv:2602.11180 — "Mechanistic Interpretability for Large Language Model Alignment" (Survey, Feb 2026) ✓
8. International AI Safety Report 2026 (Feb 3, 2026) ✓
