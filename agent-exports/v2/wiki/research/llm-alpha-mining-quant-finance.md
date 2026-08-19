# LLM-Driven Alpha Mining & Evolutionary Quantitative Finance

**Status:** STABLE
**Last Updated:** 2026-05-22
**Primary Sources:** 8 verified
**Cross-Domain Links:** 5

---

## Overview

The quantitative investment pipeline has evolved through three stages: manual feature engineering → deep learning end-to-end pipelines → LLM-based agentic systems with self-iterative workflows. This transition represents a fundamental shift from human-crafted factor libraries to autonomous discovery systems.

## The Alpha Mining Pipeline (Cao et al., arXiv 2503.21422)

Four canonical stages, all now being transformed by AI:

1. **Data Processing**: Raw numerical data, relational data, alternative data (news, social media, filings), simulation data
2. **Model Prediction**: Deep learning for temporal patterns (LSTM, Transformer, N-BEATS), spatial patterns (graph networks for cross-asset dependencies), spatiotemporal interactions
3. **Portfolio Optimization**: Moving from mean-variance to end-to-end learning-based portfolio generation (return-only, risk-adjusted, transaction-cost-aware, diversity-constrained)
4. **Order Execution**: Reinforcement learning frameworks replacing traditional discrete/continuous models

## Key Systems

### QuantaAlpha (Han et al., arXiv 2602.07085v3, May 2026)

Evolutionary framework combining LLM-driven hypothesis generation with trajectory-level genetic mutation/crossover. Each mining run is a trajectory refined by revising weak segments and recombining high-reward paths, with semantic consistency across hypotheses, executable factor code, and evaluation under noisy non-stationary markets.

**Verified metrics (GPT-5.2, CSI 300):**
- Information Coefficient (IC): 0.0472
- Annualized Return: 4.68%
- Maximum Drawdown: 11.8%
- Cross-market transfer: CSI 500 +40.28%, S&P 500 +19.1%
- 3 arXiv revisions in 3 months (Feb→Apr→May 2026) indicates active development

### AlphaAgent (arXiv 2502.16789, KDD 2025)

LLM-driven alpha mining with regularized exploration to counteract alpha decay. Three specialized agents. Outperforms traditional and LLM-based methods in mitigating alpha decay across bull and bear markets on CSI 500 and S&P 500 over 4 years.

### Chain-of-Alpha (arXiv 2508.06312, Aug 2025)

Dual-chain architecture: reasoning chain + factor chain working synergistically for alpha discovery without human intervention. Tested on real-world A-share benchmarks, outperforms existing baselines across multiple metrics.

### Agentic Trading Survey (arXiv 2605.19337, May 2026)

Comprehensive survey "Agentic Trading: When LLM Agents Meet Financial Markets". Covers transaction-cost modeling, market microstructure concerns specific to financial applications.

### AlphaEvolve (arXiv 2506.13131, Jun 2025)

Coding-centric evolution for algorithmic discovery. Scientific and algorithmic discovery via LLM coding agents.

### ACM Survey (ACM 3768292.3770387, 2025)

"Large Language Model Agents for Investment Management: Foundations" — comprehensive review of LLM-based agents in investment and trading: portfolio optimization, risk management, information retrieval, automated decision-making.

### OpenReview: Evolutionary Alpha Factor Discovery

OpenReview paper on evolutionary alpha factor discovery using LLMs under ℓ₀ constraints. LLM-driven evolutionary loop generating, mutating, and refining interpretable alpha formulas based on back-testing feedback.

## Alpha Decay Problem

Alpha factors degrade as markets adapt — analogous to distribution shift in ML.

**Mitigation strategies identified across literature:**
- **Regularized exploration** (AlphaAgent): diversify factor search to avoid overfitting to transient patterns
- **Evolutionary trajectory reuse** (QuantaAlpha): reuse high-performing trajectory segments rather than starting from scratch
- **Cross-market transferability testing** (QuantaAlpha): factors discovered on one market may persist on another (+40% transfer rate CSI 300→500)

## Cross-Domain Connections

1. → [ai-agent-trust-infrastructure](ai-agent-trust-infrastructure.md): QuantaAlpha self-iterative workflow is an autonomous agent in a high-stakes domain. How do you verify an LLM-generated trading signal?
2. → [adversarial-ml-robustness](adversarial-ml-robustness.md): Alpha decay ≈ distribution shift; adversarial training techniques applicable to factor discovery
3. → [entity-resolution-2026-state-of-the-art](entity-resolution-2026-state-of-the-art.md): Cross-market factor transferability requires resolving equivalent market microstructures across heterogeneous exchanges
4. → [memory-architecture-cognitive-systems](memory-architecture-cognitive-systems.md): Evolutionary trajectory reuse ≈ episodic memory consolidation
5. → [autonomous-self-improving-agents](autonomous-self-improving-agents.md): QuantaAlpha and AlphaAgent are self-improving agents with real economic consequences

## Verified Primary Sources

1. Cao et al., arXiv 2503.21422 — "From Deep Learning to LLMs: A survey of AI in Quantitative Investment"
2. Han et al., arXiv 2602.07085v3 — "QuantaAlpha: An Evolutionary Framework for LLM-Driven Alpha Mining" (May 2026)
3. AlphaAgent, arXiv 2502.16789 — "LLM-Driven Alpha Mining with Regularized Exploration" (KDD 2025)
4. Chain-of-Alpha, arXiv 2508.06312 — "Unleashing the Power of LLMs for Alpha Mining" (Aug 2025)
5. AlphaEvolve, arXiv 2506.13131 — Coding agent for algorithmic discovery (Jun 2025)
6. Agentic Trading Survey, arXiv 2605.19337 — "Agentic Trading: When LLM Agents Meet Financial Markets" (May 2026)
7. ACM 3768292.3770387 — "Large Language Model Agents for Investment Management" (2025)
8. OpenReview — "Evolutionary Alpha Factor Discovery with Large Language Models" (ℓ₀-constrained)

## Open Questions

- Live market vs backtest performance gap? No verified live deployment data.
- Economic viability after transaction costs, slippage, infrastructure overhead?
- Can trajectory-level evolutionary search scale to multi-asset portfolios?
- What regulatory frameworks will govern autonomous alpha mining agents?
