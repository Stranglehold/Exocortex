# ML-Driven Volatility Surface Modeling & Derivatives Pricing

**Status: STABLE**
**Created: 2026-05-22**
**Last Updated: 2026-05-22**
**Primary Sources: 8/8**
**Cross-Domain Links: 4/4**

---

## Overview

Machine learning approaches to modeling the volatility surface for options pricing, replacing or augmenting traditional local/stochastic volatility models (SVI, SABR, Heston) with neural network parameterizations that better capture term structure dynamics, skew evolution, and arbitrage-free constraints.

## Key Questions

1. Can ML models learn arbitrage-free volatility surfaces from market data?
2. How do neural stochastic volatility models compare to Heston/SABR in calibration speed and accuracy?
3. What are the failure modes of ML-based volatility modeling during stress periods?
4. Integration path: can these models plug into existing options strategy generation pipelines?

## Verified Primary Sources

### 1. HyperIV: Real-time IVS via Hypernetwork (ICML 2025)
**Method**: Hypernetwork generates parameters for compact NN that constructs full IV surfaces
**Key Innovation**: <2ms surface construction with SABR priors embedded
**Performance**: 40% RMSE reduction vs baseline when SABR prior included; 9+ market quotes sufficient
**Source**: ICML 2025 poster session

### 2. AT-PINN: Attention-Augmented Physics-Informed NN (arXiv 2605.06688)
**Method**: Encodes Black-Scholes PDE as soft constraint in loss function + attention mechanism for regime adaptation
**Key Innovation**: Zero labeled price data needed; learns from market quotes + PDE physics
**Performance**: European options MAE ~5e-2; American puts MAE ~1e-1; provides epistemic uncertainty bands
**Source**: arXiv 2605.06688

### 3. PINN for Jump-Diffusion Pricing (ACM DL 2025)
**Method**: Physics-informed NN encodes Merton-type jump-diffusion PIDE with liquidity cost adjustment
**Key Innovation**: Extends PINN beyond diffusion to jump processes; integrates liquidity frictions
**Significance**: Realistic market microstructure modeling within physics-informed framework
**Source**: ACM Digital Library, DOI:10.1145/3760678.3760691

### 4. Deep Learning Option Pricing with Market IV Surfaces (arXiv 2509.05911)
**Method**: Variational autoencoder for high-dimensional IV surface representation, single forward pass pricing
**Data**: S&P 500 index options 2018-2023, QuantLib-generated training data for American puts and arithmetic Asian options
**Key Innovation**: Bridges IV surface modeling and exotic option pricing in unified framework; no labeled prices needed when combined with physics constraints
**Performance**: MAE scales favorably with additional data volume
**Source**: arXiv 2509.05911

### 5. DL-Enhanced Heston Calibration (arXiv 2510.24074)
**Method**: Hybrid framework augments Heston model with two regression-based neural networks
**Problem Solved**: Heston calibration is computationally intensive, sensitive to local minima in 5D parameter space
**Key Innovation**: NNs provide intelligent initialization and residual correction, avoiding local minima traps
**Performance**: Substantially faster calibration than pure numerical methods while preserving stochastic volatility interpretability
**Source**: arXiv 2510.24074

### 6. Meta-Learning Neural Process for IVS (arXiv 2509.11928)
**Method**: Meta-learning view trains across trading days to learn procedure mapping sparse quotes to full IVS
**Key Innovation**: Learns to learn — generalizes to unseen market conditions without recalibration
**Source**: arXiv 2509.11928

### 7. ARTEMIS: Neuro-Symbolic Arbitrage-Free Framework (arXiv 2603.18107)
**Method**: Continuous-time Laplace Neural Operator encoder + neural SDE with physics-informed losses + differentiable symbolic bottleneck
**Key Innovation**: First framework to distill interpretable trading rules from learned dynamics while enforcing no-arbitrage constraints
**Significance**: Bridges black-box DL with white-box financial modeling — economically constrained by design, not post-hoc
**Source**: arXiv 2603.18107

### 8. Options-Driven Realized Volatility Forecasting (arXiv 2604.02743)
**Method**: Iterative two-step inference of spot volatility under rough stochastic volatility model
**Key Innovation**: Leverages options market data for forward-looking RV estimation
**Source**: arXiv 2604.02743

## Verified Quantitative Benchmarks

| Method | Task | MAE/RMSE | Speed | Data Efficiency |
|--------|------|----------|-------|----------------|
| PINN (2605.06688) | European options | MAE ~5e-2 | Single forward pass | No labeled prices |
| PINN (2605.06688) | American puts | MAE ~1e-1 | Single forward pass | No labeled prices |
| HyperIV (ICML 2025) | Full IVS reconstruction | 40% RMSE reduction w/ SABR prior | <2ms per surface | 9+ market quotes |
| VAE IVS (2509.05911) | Exotic option pricing | Scales with data volume | Single forward pass | S&P 500 2018-2023 |
| DL-Heston (2510.24074) | Heston calibration | Outperforms pure numerical | Faster than grid search | Market quotes |

## Production Deployment Constraints

1. **Calibration Latency**: HyperIV <2ms; PINN/VAE single forward pass; DL-Heston faster than grid search
2. **Arbitrage-Free Guarantee**: HyperIV explicit; PINN encodes PDE physics; ARTEMIS enforces via SDE constraints
3. **Data Efficiency**: PINN zero labeled prices; HyperIV needs 9+ observations; VAE benefits from extended history
4. **Uncertainty Quantification**: AT-PINN provides epistemic bands; ARTEMIS symbolic bottleneck enables rule extraction
5. **Stress Period Behavior**: ARTEMIS neuro-symbolic approach most promising for regime shifts — symbolic rules generalize beyond training distribution
6. **Interpretability Gap**: Pure NN models (HyperIV, VAE) remain black boxes; ARTEMIS and DL-Heston partially address this

## Integration Path

- **Options Strategy Generation**: ML volatility surfaces replace SVI/SABR calibration for real-time surface updates
- **Market Making**: <2ms surface construction (HyperIV) viable for HFT; PINN/VAE viable for mid-frequency
- **Risk Management**: Uncertainty quantification (AT-PINN, ARTEMIS) enables confidence-aware position sizing
- **Exotic Options**: VAE approach (2509.05911) extends beyond European to American puts and Asian options
- **Regulatory Compliance**: ARTEMIS symbolic bottleneck produces interpretable rules for audit trails

## Cross-Domain Connections

- [options-market-structure](research/options-market-structure.md) — IV surface dynamics, SVI/SABR baseline
- [ai-options-strategy-generation](research/ai-options-strategy-generation.md) — ML for options strategies, RL policy selection
- [ai-market-making-hft](research/ai-market-making-hft.md) — HFT infrastructure, RL market making
- [formal-verification-ai-systems](research/formal-verification-ai-systems.md) — PDE-constrained ML mirrors verified ML compilers

---

*This page is STABLE. Deepening complete.*
