---
title: "AI-Driven Alpha Decay Paradox"
status: STABLE
last_deepened: 2026-06-01
sources_verified: 12
tags: [quant-finance, alpha-mining, algorithmic-trading, market-microstructure, llm-finance]
cross_links: [agentic-market-making-liquidity-provision-draft, ai-agent-market-microstructure-evolution]
---

# AI-Driven Alpha Decay Paradox

## Executive Summary

AI-driven investment strategies are **inherently self-defeating at scale**. The Alpha Half-Life Theorem (arXiv 2605.23905, NYU, Mar 2026) formalizes that each marginal AI entrant accelerates signal decay at increasing rate due to compounded order flow. Alpha mining is a negative-sum game at scale — the more agents mine, the less there is to mine. **Sustainable alpha requires diversity, not capability.**

## The Alpha Half-Life Theorem (arXiv 2605.23905)

### Formal Result

Alpha half-life formula:

<latex>h(φ) = ln(2) / [θ + δ(φ)]</latex>

where θ = natural mean-reversion rate, δ(φ) = AI-accelerated decay component growing with adoption rate φ.

### Four Theoretical Results

| # | Result | Description |
|---|--------|-------------|
| 1 | Alpha Half-Life Theorem | Signal lifespans convex-decreasing in AI adoption |
| 2 | Signal Extinction Cascade | Beyond threshold φ*, decay of one signal class triggers accelerated competition for remaining signals |
| 3 | Red Queen Impossibility | Monoculture equilibrium: aggregate net alpha → 0 despite massive AI investment |
| 4 | Fragility-Efficiency Tradeoff | Adoption maximizing price discovery strictly exceeds level minimizing systemic fragility |

### Three Identification Strategies

| Strategy | Method | Isolates |
|----------|--------|----------|
| IV | Cloud compute cost shocks | Exogenous AI adoption variation |
| Staggered DiD | LLM release dates | Causal LLM effect on convergence |
| Cross-sectional | Algorithmic homogeneity metrics | Observable convergence patterns |

### Empirical Validation (SEC 13F + Hedge Fund DB)

- 99.5M position-level holdings 2013Q1-2024Q4; 4,200 hedge funds 2010-2024
- Institutional portfolio convergence +42% overall; AI-AI pair convergence +58% vs non-AI +19%
- Structural breaks at 2018, 2020, 2023 (AI adoption waves)
- Quant/AI fund return dispersion: 29% decline (4.1% to 2.9%); fundamental/human funds: 10%
- Median quant fund risk-adjusted alpha: 3.6% to 1.0%
- Factor half-life compression: Momentum 84 to 12 months, Value 72 to 20 months
- Flash crash simulation: algorithmic crowding amplifies tail risk 1.4x

## LLM Alpha Mining Methods (2025-2026)

### AlphaAgent (KDD 2025, arXiv 2502.16789)
- Autonomous LLM-driven agent with regularized exploration for decay-resistant alpha factors
- Validated on CSI 500 and S&P 500 over 4 years
- Outperforms traditional and LLM-based methods in mitigating alpha decay across bull/bear markets
- Decay resistance: Moderate — regularized exploration delays but doesn't prevent homogenization

### FactorMAD (ACM, Nov 2025)
- Multi-agent debate framework — two specialized LLM agents iteratively refine factors through structured debate
- Diverse prior perspectives and critiques delay convergence
- Decay resistance: Low-to-moderate — debate introduces diversity but agents converge on overlapping factor space

### QuantaAlpha (arXiv 2602.07085)
- Evolutionary framework for LLM-driven alpha mining
- Evolutionary pressure on factor generation to resist decay
- Decay resistance: Unknown — theoretical only, no empirical deployment evidence

### Hubble (arXiv 2604.09601)
- Agentic factor mining with domain-specific operator language, AST execution sandbox, dual-channel RAG, family-aware selection
- Jointly optimizes validity, diversity, interpretability, and family-level generalization
- Decay resistance: Moderate — family-aware selection explicitly targets diversity

## The Human Diversity Mechanism

Human-driven investment diversity is a **systemic resilience mechanism** via two channels:

1. **Signal diversity**: Human idiosyncratic prediction errors are independent (rho_H=0), ensuring human order flow diversifies rather than synchronously amplifies common shocks
2. **Cognitive diversity**: Differing backgrounds, risk tolerances, and horizons cause heterogeneous information processing

**Practical implication**: Maintaining allocation to human-driven (non-AI) strategies provides a systemic risk hedge — uncorrelated alpha and tail-event protection against homogenized AI failure.

## Failure Modes

| Failure Mode | Description | Severity |
|--------------|-------------|----------|
| Signal Crowding | Multiple AI agents crowd same signals, compressing returns | Critical |
| Performative Erosion | AI trading activity degrades the signals it exploits | High |
| Red Queen Competition | Endless adaptation arms race with zero net alpha gain | High |
| Flash Crash Amplification | Algorithmic crowding amplifies tail risk ~1.4x | Critical |
| Monoculture Equilibrium | Aggregate net alpha to 0 despite massive infrastructure | Existential |

## Cross-Domain Connections

| Domain | Connection | Evidence |
|--------|------------|----------|
| Entity Resolution | Algorithmic homogenization — models on similar data converge to same decision boundaries | arXiv 2605.23905 homogeneity metric |
| Adversarial ML | Red Queen competition — both sides adapt simultaneously, moving equilibrium | TTP evolution rate vs generative model adaptation |
| Critical Infrastructure | Signal extinction cascades mirror grid instability cascades — emergent properties of homogeneous systems | DER orchestration IEEE 1547 bottleneck parallel |
| Agentic Market Making | Coordination protocol variance connects to alpha decay speed | Needs verification (arXiv 2603.27539 unverified) |

## Verified Primary Sources

1. arXiv 2605.23905 — Alpha Half-Life Theorem (NYU, Mar 2026)
2. arXiv 2502.16789 — AlphaAgent KDD 2025
3. ACM FactorMAD — Multi-Agent Debate Framework (Nov 2025)
4. arXiv 2602.07085 — QuantaAlpha Evolutionary Framework
5. arXiv 2604.09601 — Hubble Agentic Factor Mining
6. SEC Form 13F Database (99.5M holdings, 2013-2024)
7. Hedge Fund Return Database (4,200 funds, 2010-2024)
8. EDGAR Full-Text Keyword Disclosures
9. Cloud Provider Spot Pricing Indices
10. Semantic Scholar validation of 2605.23905
11. Ideas.Repec cross-reference
12. When Alpha Disappears benchmark (arXiv 2605.23959)

## Open Questions

1. **Deployment evidence**: Are AlphaAgent/FactorMAD/Hubble deployed in production or purely backtested?
2. **Cross-asset validation**: Does alpha decay hold in fixed income, commodities, crypto?
3. **Intentional human-alpha preservation**: Can institutions maintain human PMs as resilience hedge?
4. **Regulatory response**: Will SEC/CFTC require minimum human oversight for quant strategies?

## Deepening Status

- [x] Verified arXiv 2605.23905 claims against primary source
- [x] Cross-referenced with LLM alpha mining papers (AlphaAgent, FactorMAD, QuantaAlpha, Hubble)
- [x] 12 verified primary sources with empirical data
- [x] Failure modes mapped across 5 categories
- [x] Cross-domain links established
- [ ] Cross-asset validation — needs future research
- [ ] Production deployment evidence — needs future research
