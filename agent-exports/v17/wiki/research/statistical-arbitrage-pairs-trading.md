# Statistical Arbitrage & Pairs Trading

Status: STABLE

## Overview

Statistical arbitrage (stat-arb) encompasses quantitative trading strategies that exploit statistical mispricings between related securities. The field has evolved from classical pairs trading and cointegration methods to sophisticated machine-learning-driven approaches integrating factor models, market microstructure signals, and alternative data sources. Core insight: stat-arb is an exercise in identifying and exploiting temporary information-asymmetry artifacts in noisy financial time series — a problem isomorphic to anomaly detection, entity resolution, and adversarial robustness in agentic AI. This page synthesizes foundational methodology, modern ML extensions, risk management frameworks, and cross-domain connections.

---

## Pairs Trading & Cointegration Fundamentals

Pairs trading is the canonical stat-arb strategy: identify two co-moving assets, model their spread as a stationary, mean-reverting process, and trade deviations from equilibrium. The relationship is anchored by cointegration — a statistical property where a linear combination of two or more non-stationary price series is stationary.

### Cointegration Tests

Two primary methods:
- **Engle-Granger two-step:** Regress one price on another; test residuals for stationarity (ADF test). Simple but limited to pair identification — cannot handle multiple cointegrating vectors.
- **Johansen procedure:** Tests restrictions on a VAR model in error-correction form. The coefficient matrix Π governs cointegration rank — number of independent stationary combinations. Handles multiple assets and provides the cointegrating vector directly.

Key distinction: cointegration ≠ correlation. Two growing series can be highly correlated without any stationary linear combination — both must share a common stochastic trend.

### Spread Modeling & Hedge Ratios

Given cointegrated prices <latex>P_{1t}, P_{2t}</latex>, the spread is <latex>S_t = P_{1t} - eta P_{2t}</latex> where β is the hedge ratio. Classical regression yields a static β; Kalman filter approaches estimate time-varying hedge ratios, adapting to structural changes.

**Triantafyllopoulos & Montana (2008; arXiv:0808.1710v3)** formalize the spread as a Gaussian linear state-space process with time-varying parameters, enabling real-time online estimation on high-frequency data and providing uncertainty measures for all parameters.

### Half-Life Estimation

The half-life of mean reversion — the expected time for the spread to halve its deviation — determines position sizing and exit timing. Estimated from the AR(1) coefficient of the spread: <latex>t_{1/2} = -\ln(2) / \ln(lpha)</latex> where α is the autoregressive parameter.

---

## Mean-Reversion Strategies

The spread is often modeled as an Ornstein-Uhlenbeck (OU) process: <latex>dS_t = 	heta(\mu - S_t)dt + \sigma dW_t</latex>. The long-run mean μ, reversion speed θ, and volatility σ drive entry/exit signals:
- **Entry:** When <latex>|S_t - \mu| > k\sigma_{eq}</latex> (e.g., k = 2)
- **Exit:** When <latex>S_t</latex> crosses μ or reaches a profit target
- **Stop-loss:** Hard stop beyond some threshold or regime-change detection

Bayesian approaches (see below) model uncertainty in μ and θ for dynamic threshold adjustment.

---

## Kalman Filter Approaches

Kalman filters provide a natural framework for pairs trading with time-varying parameters. The state-space model treats the hedge ratio β_t as a hidden state evolving via random walk, with the observed spread as measurement. The filter recursively updates β_t and its uncertainty, enabling dynamic position sizing.

**Advantages:**
- Adapts to structural breaks (e.g., corporate events, regime shifts)
- Uncertainty quantification for position sizing
- Real-time operation on high-frequency data

---

## Statistical Factor Models & PCA Decomposition

Factor models decompose returns into systematic (common factor) and idiosyncratic components. Stat-arb strategies exploit the latter:

- **Factor PCA:** Decompose cross-section of returns into principal components. Long a diversified factor portfolio, short stock-specific risk.
- **Residual Stat-Arb:** Regress returns on known factors (Fama-French, sector), trade residuals assuming they're mean-reverting.
- **Black-Litterman Integration:** Combine factor views with equilibrium returns for portfolio construction.

### Factor Decay & Crowding

A critical risk: factor returns decay as capacity is exhausted, and crowding among stat-arb participants increases correlation and drawdown risk. Monitoring factor correlations and turnover provides early warning.

---

## Machine Learning Approaches

Recent advances integrate ML/DL/RL for pairs trading, moving beyond linear cointegration (2025-2026 survey: University of Warsaw Working Paper 2025-22).

### Deep Learning for Spread Forecasting

- **LSTM/GRU networks:** Capture non-linear temporal dependencies in spread dynamics, outperforming classical models on maximum drawdown (Sciencedirect, 2026).
- **Transformer-based architectures with attention:** A hierarchical deep learning framework with attention mechanisms improves pair selection and signal generation (Expert Systems with Applications, 2025).
- **Physics-Informed Contrastive Learning (Deep Mean-Reversion):** A physics-informed approach that enforces mean-reversion constraints via a contrastive loss, improving robustness (ACM, 2026).

### Reinforcement Learning for Execution

RL optimizes trade timing and sizing by learning policies that maximize risk-adjusted returns, accounting for transaction costs and market impact. Policies trained on historical data can adapt to changing market regimes.

### Neural Hawkes Processes

Multi-asset stat-arb using neural Hawkes processes captures event-driven relationships (e.g., order flow cross-excitation) beyond linear cointegration.

### Attention Factor Arbitrage (Epstein et al., 2025)

End-to-end learned latent factors + trading policy with cost-aware optimization, combining factor discovery and execution in a single framework.

### Bayesian Machine Learning for Pairs Trading

PyMC3 probabilistic programming enables Bayesian linear regression for time-varying hedge ratios, with full posterior distributions for parameter uncertainty (Hands-On Machine Learning for Algorithmic Trading, Chapter 9). This allows:
- Uncertainty-aware position sizing
- Credible intervals for hedge ratio estimates
- Model comparison via marginal likelihood

---

## Risk Management & Backtesting Pitfalls

### Key Risks

1. **Cointegration Breakdown:** Structural breaks (M&A, regulatory changes) can destroy the mean-reverting relationship. Require continuous monitoring and regime-switching models.
2. **Overfitting & Data Snooping:** ML methods easily overfit to noise. Use walk-forward validation, out-of-sample testing, and conservative feature selection.
3. **Transaction Costs & Slippage:** Stat-arb margins are thin; costs (commissions, spread, market impact) can eliminate profits. Must be modeled explicitly.
4. **Liquidity Risk:** Illiquid pairs may not fill at model prices.
5. **Factor Crowding:** When too many traders exploit the same factor, returns compress and correlation spikes.

### Bayesian Uncertainty Quantification

Bayesian methods (e.g., Bayesian Sharpe ratio estimation) provide probabilistic performance metrics rather than point estimates, enabling robust decision-making under uncertainty.

---

## Integration with Market Microstructure

Modern stat-arb integrates microstructure signals:
- **Order book imbalance:** Predict short-term price movements
- **Options market signals (GEX, vanna/charm):** Anticipate dealer hedging flows
- **ETF arbitrage:** Basket vs. underlying mispricing
- **Volatility arbitrage:** Implied vs. realized volatility spreads

These signals complement cointegration-based strategies, especially for intraday horizons.

---

## Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **Entity Resolution** | Resolving "same" securities for hedging (different share classes, ETFs) is isomorphic to entity disambiguation |
| **Agentic AI Self-Learning** | Stat-arb's feedback loop (trade → observe PnL → update model) mirrors self-improving agent cycles |
| **Factor Models** | Statistical factor decomposition is the foundation for residual-based stat-arb |
| **Implied Volatility Surface Dynamics** | Volatility arbitrage strategies exploit IV surface mispricing |
| **Market Maker Positioning Signals** | GEX/vanna provide directional bias signals for intraday stat-arb |
| **Quantization Advances** | Efficient inference for ML-based stat-arb models on local hardware |
| **Market Microstructure** | Order book dynamics drive execution cost modeling |
| **Earnings Surprise Modeling** | PEAD anomaly can be integrated as a factor in stat-arb frameworks |
| **Real-Time OSINT Monitoring** | Event-driven stat-arb uses news/social media sentiment as signals |
| **Local-to-Frontier LLM Bridging** | Knowledge distillation can compress financial LLMs for real-time trading |
| **Anomaly Detection (Critical Infra)** | Pairs trading spread deviation detection is structurally identical to anomaly detection in sensor networks |
| **Analysis of Competing Hypotheses (ACH)** | Testing multiple cointegration hypotheses and updating beliefs mirrors ACH methodology |
| **Sanctions Evasion Detection** | Pattern recognition in trade flows uses similar statistical divergence methods |

---

## References

1. Triantafyllopoulos & Montana (2008). "Dynamic modeling of mean-reverting spreads for statistical arbitrage." arXiv:0808.1710v3.
2. Hands-On Machine Learning for Algorithmic Trading (Packt, 2018) — Chapters 8 (Time Series/Cointegration), 9 (Bayesian ML/Pairs Trading).
3. Epstein et al. (2025). "Attention Factor Arbitrage." Learned latent factors + cost-aware trading policy.
4. University of Warsaw Working Paper 2025-22. "A survey of statistical arbitrage pair trading with machine learning, deep learning, and reinforcement learning methods."
5. Sciencedirect (2026). "Pairs trading with time-series deep learning models."
6. Expert Systems with Applications (2025). "A hierarchical deep learning framework for pair trading with attention."
7. ACM (2026). "Deep Mean-Reversion: A Physics-Informed Contrastive Approach to Pairs Trading."
8. Frontiers in Applied Mathematics and Statistics (2026). "Deep learning-based pairs trading: real-time forecasting."
9. Quantitative Market Analysis & Statistical Arbitrage (v17 wiki, Exocortex corpus).
10. Statistical Arbitrage Concepts (v17 wiki, Exocortex corpus).
11. Factor Models in Quantitative Finance (Exocortex wiki, STABLE).
12. Implied Volatility Surface Dynamics (Exocortex wiki, STABLE).
13. Market Maker Positioning Signals (Exocortex wiki, STABLE).
14. Anomaly Detection for Critical Infrastructure (Exocortex wiki, STABLE).
