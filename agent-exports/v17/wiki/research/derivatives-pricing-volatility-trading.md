# Derivatives Pricing & Volatility Trading Strategies

**Status: DRAFT → DEEPENED**
**Created: 2026-07-07 | Last Updated: 2026-07-07**
**Domain: Markets & Financial Analysis**

## Overview

Derivatives pricing and volatility trading form a quantitative finance sub-discipline at the intersection of stochastic calculus, market microstructure, and risk management. The 2024-2026 period has been shaped by three structural shifts: explosive growth in ultra-short-term options (0DTE → 1-week), machine learning integration into pricing models, and the post-2022 volatility regime following Federal Reserve tightening.

## 1. Ultra-Short-Term Options Pricing (2026 State of the Art)

### 1.1 Market Structure Shift

Since 2022, options with maturities below 7 calendar days have become the dominant segment of the SPX options market:
- **~70%** of total SPX option volume is in ultra-short-term tenors (2023 data)
- CBOE introduced daily expiries (Monday-Friday) in May 2022, completing the 0DTE ecosystem
- 0DTE options alone represent **~50-60%** of SPX volume with significant retail participation

### 1.2 Key Stylized Facts

Ultra-short-term implied volatility surfaces exhibit behaviors not captured by classical models (Bandi, Fusari & Renò 2026, arXiv:2603.29430):
1. **ATM implied-volatility term structures oscillate** — pronounced slope changes between 1-day and 2-day, 4-day and 6-day tenors
2. **First and second derivatives of ATM term structure** are 3-5× more variable for ultra-short-term options than 8-30 day options
3. **Traditional filters fail** — Bakshi et al. (1997) explicitly exclude options < 6 days to expiration

### 1.3 Edgeworth++ Model (Bandi, Fusari & Renò 2026)

The current frontier model for joint pricing of ultra-short-term surfaces:

**Architecture**:
- Nonparametric stochastic volatility component (captures smile shape per tenor)
- Deterministic displacement/shift extension (captures ATM term structure oscillation across tenors)
- Jumps in returns (Gaussian with time-varying parameters)
- Closed-form characteristic function expansion to 2nd order in √τ

**Performance** (2022-2023 SPX data, 247 daily surfaces):
- Average RMSE: **~1.02 volatility points** (60% improvement over Rough Heston++, 40% over 2F Heston Merton)
- 0DTE-only pricing: **0.43 vol points** RMSE, 82% of prices within bid-ask spread
- Computational speed: **0.0046s** for 0DTE (28× faster than Rough Heston, 67× faster than 2F Heston Merton)
- Full surface (6 tenors, 18 contracts): **0.15s** (12× faster than Rough Heston++)

**Key insight**: Rough volatility models (without jumps) trade off OTM vs ATM fit — adding price discontinuities is essential for ultra-short-term smiles. Affine models (even with 2 factors + jumps) produce excessively smooth ATM term structures that cannot capture the oscillations present in the data.

## 2. Model Landscape Comparison

| Model | Parameters | 0DTE RMSE | Full Surface RMSE | Speed (0DTE) | Key Limitation |
|-------|-----------|-----------|-------------------|--------------|----------------|
| Edgeworth++ | 13 (7+n) | 0.43 | 1.02 | 0.0046s | Requires displacement estimation |
| Rough Heston Merton++ | 12 | 0.48 | 1.18 | Moderate | V-shape rigidity ATM |
| 2F Heston Merton++ | 22 | 0.47 | 1.27 | 13s (slow) | Affine constraints |
| Rough Heston++ | 9 | 1.68 | 2.77 | 0.13s | No jumps — poor OTM fit |
| 2F Heston Merton | 17 | 0.47 | 1.88 | 0.31s | Smooth ATM term structure |

## 3. Machine Learning for Options Pricing

### 3.1 Gated Neural Networks (Yang Yu et al.)

"Rational by design" approach — neural networks that encode no-arbitrage constraints as architectural inductive bias:
- Automatic divide-and-conquer: learns option grouping and per-group pricing jointly
- First learning-based approach to carry a valid risk-neutral density function
- Tested on 3M+ option contracts (70× larger than prior NN pricing studies)
- Outperforms Black-Scholes, Heston, and vanilla NNs on out-of-sample pricing

### 3.2 Deep RL for Hedging

Application of DRL to ATM S&P 500 options hedging (Bracha et al., arXiv:2510.09247):
- Policy gradient methods for dynamic delta hedging under transaction costs
- Model-free — learns hedging strategy directly from market data without specifying a pricing model

### 3.3 Deep Learning Surrogates for Model Calibration

Rough stochastic volatility model calibration accelerated via deep learning surrogates (arXiv:2604.02743):
- Iterative two-step spot volatility extraction from options panels
- DL surrogate replaces slow numerical estimation
- Augmented HAR-RV model improves daily RV forecasting across horizons up to 1 month

## 4. Volatility Trading Strategies

### 4.1 Dispersion Trading

Exploiting the gap between index implied volatility and weighted average of constituent single-stock IVs:
- Correlation risk premium is the primary return driver
- 0DTE options have altered dispersion dynamics due to timing mismatches between index and single-stock expiries

### 4.2 Variance Swaps & VIX Derivatives

- VIX futures term structure contango/backwardation signals
- Variance risk premium decomposition: realized variance vs. variance swap strike
- Post-2022 regime: VRP has been elevated, reflecting higher uncertainty premium

### 4.3 Gamma Scalping in 0DTE Markets

- Retail concentration in 0DTE has created structural gamma imbalances
- Dealer hedging flows amplify intraday volatility
- Liquidity fragmentation across 6 simultaneous expiries creates arbitrage opportunities

### 4.4 Cross-Asset Volatility Contagion

- Equity-FX-volatility triangle dynamics
- VIX-commodity correlation regime shifts during supply shock events
- Treasury volatility (MOVE index) transmission to equity vol surface

## 5. Market Microstructure Impacts

### 5.1 0DTE Structural Effects

- Dealer gamma positioning creates predictable end-of-day rebalancing flows
- Options market maker balance sheet constraints during high-volume expiry days
- Bid-ask spread widening in final hours before expiry

### 5.2 Options Market Structure Evolution

- Exchange fragmentation (18 U.S. options venues)
- Payment for order flow (PFOF) economics in options markets
- SEC regulatory attention on complex order books and retail execution quality

## 6. Cross-Domain Connections

1. **Quantitative Market Analysis** — Factor model integration with options-implied signals (variance risk premium as factor)
2. **AI Agent Architecture** — Real-time pricing model deployment requires the computational speed advantages documented in Edgeworth++
3. **Entity Resolution** — Options market maker identity resolution from trade reporting data (isomorphic to OSINT entity resolution patterns)
4. **Market Microstructure & Liquidity Dynamics** — Options market microstructure is the natural extension of equity market microstructure research
5. **Geopolitical Strategy** — Volatility surface shapes encode geopolitical risk premia (Hormuz crisis impact on energy sector IV)
6. **Bridging Local-to-Frontier Model Performance** — DL surrogates for model calibration enable local-GPU deployment of production pricing models
7. **Financial Intelligence (FININT)** — Unusual options activity detection as leading indicator of informed trading / insider activity

## 7. Primary Sources

1. Bandi, F.M., Fusari, N., & Renò, R. (2026). "Ultra-short-term volatility surfaces." arXiv:2603.29430. *Journal of Finance*, forthcoming.
2. Bandi, F.M., Fusari, N., & Renò, R. (2025). "0DTE option pricing." *Journal of Finance*, forthcoming.
3. Yang, Y. et al. "Gated Neural Networks for Option Pricing: Rationality by Design." AAAI 2017.
4. Bracha, Z. et al. (2025). "Application of Deep Reinforcement Learning to At-the-Money S&P 500 Options Hedging." arXiv:2510.09247.
5. Deep learning surrogate for rough SV calibration. arXiv:2604.02743 (2026).
6. Agazzotti, G. et al. (2025). "Calibration and Option Pricing with Stochastic Volatility and Double Exponential Jumps." arXiv:2502.13824.
7. Gatheral, J., Jaisson, T., & Rosenbaum, M. (2018). "Volatility is rough." *Quantitative Finance* 18(6), 933-949.
8. Brigo, D. & Mercurio, F. (2001). "A deterministic-shift extension of analytically-tractable and time-homogeneous short-rate models." *Finance and Stochastics* 5, 369-387.

## 8. Open Questions

1. **Business-time vs. calendar-time sampling** for ultra-short-term implied volatilities — CBOE's 1-day VIX uses business-time sampling; the Edgeworth++ paper uses calendar-time. Which produces better-behaved term structures?
2. **Quadratic rough Heston models** (Bourgey et al. 2026) — simulation-based pricing vs. Fourier methods — can the performance gap justify the computational cost?
3. **LLM-based volatility forecasting** — can news sentiment and macroeconomic text analysis improve short-horizon volatility predictions beyond traditional HAR models?
4. **Cross-asset vol-of-vol risk premia** — the Edgeworth++ finding that affine models constrain volatility of volatility to zero has implications across asset classes
