# Quantitative Analysis Techniques: Factor Models, Statistical Arbitrage & Earnings Surprise Modeling

**Status:** STABLE
**Created:** 2026-06-08
**Last Updated:** 2026-06-08
**Domain:** Markets & Financial Analysis
**Interest Origin:** /a0/usr/Exocortex/interests.md — Quantitative analysis techniques
**Field Reports:** 20260526_factor-models-earnings-surprise.md, 20260526_markets-statistical-arbitrage.md, 20260527_markets-alternative-data-quant.md, 20260528_earnings-surprise-modeling-pead.md, 20260528_quantitative-factor-models.md, 20260601_earnings-surprise-modeling.md, 20260605_ai-quantitative-trading-2026.md

---

## Overview

Quantitative analysis techniques form the mathematical backbone of systematic trading and investment strategies. This page covers three interconnected domains — factor models (identifying drivers of asset returns), statistical arbitrage (exploiting temporary pricing inefficiencies), and earnings surprise modeling (predicting and trading around earnings announcements) — with an emphasis on the 2024–2026 state of the art where machine learning has disrupted classical approaches.

---

## 1. Factor Models

Factor models decompose asset returns into systematic exposures to underlying risk factors plus idiosyncratic (stock-specific) returns.

### Historical Foundations
- **CAPM** (Sharpe 1964, Lintner 1965): Single-factor model — market beta
- **Fama-French Three-Factor** (1993): Market + Size (SMB) + Value (HML)
- **Carhart Four-Factor** (1997): Adds Momentum (MOM)
- **Fama-French Five-Factor** (2015): Adds Profitability (RMW) + Investment (CMA)

### ML-Based Factor Return Predictability (Cakici et al. 2024)
A landmark study of 242 factor characteristics (1972–2021, 153 long-short anomaly portfolios) found that machine learning models (random forest, boosting, neural nets) successfully forecast cross-sectional factor returns. Top decile factors outperformed bottom decile by 0.27%–1.39% per month (1.08% for ensemble). However, **factor momentum is the dominant driver**; once controlled for, ML strategies produced no significant alpha beyond factor momentum effects. Strategies required high turnover (37–66% of factors replaced monthly).

### Attention Factors for Statistical Arbitrage (Epstein et al. 2025)
**arXiv:2510.11616** — Stanford researchers developed an end-to-end deep learning framework that jointly optimizes factor identification, mispricing detection, and trading policy with explicit transaction cost incorporation. The Attention Factor Model learns conditional latent factors most useful for arbitrage trading, demonstrating an annualized **net Sharpe ratio of 2.28** in out-of-sample U.S. equity tests — substantially outperforming prior two-step statistical arbitrage approaches. The architecture combines a convolutional neural network + Transformer for arbitrage signal extraction with a neural network mapping signals to allocations, generalizing conventional optimal stopping rules.

### A-Share Multi-Factor ML Pipeline (Du 2025)
A production-grade 213-factor engine using GPU-vectorized PyTorch unfold primitives achieved **51x speedup** over pandas. Key finding: upstream contamination from price-move limits biases Information Coefficient (IC) by **18%**. Mask-first tradability filtering contributed +0.44 Sharpe; full system Sharpe of 1.63 on real A-share data.

### Modern Extensions
- **Machine Learning Factor Models**: Autoencoders for latent factor extraction, neural network-based factor timing, gradient-boosted factor importance ranking
- **Alternative Data Factors**: Satellite imagery, credit card transactions, social media sentiment, job posting velocity as factor inputs
- **Dynamic Factor Loading**: Time-varying betas via Kalman filters and Hidden Markov Model regime-switching
- **GPU-Accelerated Factor Computation**: PyTorch-based unfold primitives replacing pandas groupby — 10–50x speedups on 200+ factor engines

### Key Metrics
- Factor exposure (beta) estimation
- Information Coefficient (IC): correlation between factor scores and subsequent returns
- Information Ratio (IR): risk-adjusted factor performance
- Factor turnover and transaction cost modeling
- IC decay curves: how rapidly factor signal degrades over holding period

---

## 2. Statistical Arbitrage

Statistical arbitrage (stat arb) exploits short-term pricing relationships using statistical models, typically with high turnover and short holding periods.

### Core Methodologies
- **Pairs Trading**: Cointegration-based relative value, mean-reversion strategies (Engle-Granger, Johansen tests)
- **Index Arbitrage**: ETF vs. underlying basket mispricing
- **Volatility Arbitrage**: Options implied vs. realized volatility spreads
- **Statistical Factor Neutralization**: Long-short portfolios hedged to factor exposures (market, sector, style-neutral)
- **Attention Factor Arbitrage** (Epstein et al. 2025): End-to-end learned latent factors + trading policy with cost-aware optimization

### Mathematical Foundations
- **Cointegration tests**: Engle-Granger two-step, Johansen multivariate
- **Ornstein-Uhlenbeck processes**: Mean-reversion modeling with half-life estimation
- **Kalman filters**: Dynamic hedge ratio estimation for pairs trading
- **PCA/ICA**: Latent factor identification for statistical arbitrage portfolios
- **Attention mechanisms**: Learned conditional latent factors (Attention Factors)

### Infrastructure Requirements
- Low-latency market data feeds (sub-millisecond for HFT stat arb)
- Transaction cost modeling: spread, market impact, commissions, short borrow costs, financing
- Risk management: position limits, drawdown controls, correlation regime detection
- Execution: smart order routing, VWAP/TWAP algorithms, dark pool access

### Production Considerations
- **Capacity constraints**: Stat arb strategies are capacity-constrained; alpha decays as AUM scales
- **Crowding risk**: Popular factors become crowded → alpha erosion → factor crash dynamics
- **Regime sensitivity**: Mean-reversion strategies fail during momentum-driven markets; correlation breakdowns during crises

---

## 3. Earnings Surprise Modeling

Earnings surprise modeling predicts the magnitude and market impact of earnings announcements relative to consensus expectations.

### Standardized Unexpected Earnings (SUE)
<latex>SUE = (EPS_{actual} - EPS_{expected}) / \sigma(EPS_{estimates})</latex>
- Captures the surprise in standard deviation units relative to analyst dispersion
- Historical SUE decile analysis for drift prediction

### Post-Earnings Announcement Drift (PEAD)
- **Ball & Brown (1968)**: Foundational documentation of PEAD — stock prices drift in direction of earnings surprise for 60+ days post-announcement
- **Bernard & Thomas (1989, 1990)**: PEAD persists after risk adjustment; naive investor expectation hypothesis
- **Modern explanation**: Limited arbitrage — transaction costs, short-sale constraints, and institutional frictions prevent full correction

### PEAD Revival with ML (2025)
A 2025 Sciencedirect paper demonstrated that using ML to forecast returns from historical earnings surprises with longer SUE histories (up to 12 quarters) markedly improved predictive accuracy versus shorter-horizon and streak-based approaches. The key innovation: ML models capture non-linear interactions between SUE magnitude, earnings streak length, analyst revision patterns, and sector context that linear models miss. Improved Sharpe ratios and alphas over classical SUE-stratified portfolios.

### Alternative Data Augmentation
- **Job posting velocity**: Changes in hiring rate predict earnings trajectory (see [[job-posting-alt-data-forecasting]])
- **Employee review sentiment**: Glassdoor/Indeed ratings shifts precede earnings surprises
- **Supply chain shipment data**: Satellite and logistics data predict revenue surprises
- **Credit card transaction panels**: Real-time consumer spending at company-level granularity
- **Patent filing velocity**: Innovation pipeline proxy for technology companies

### Machine Learning Approaches
- **Gradient boosting (XGBoost/LightGBM)**: SOTA for earnings beat/miss classification with feature importance analysis
- **NLP on earnings call transcripts**: Tone analysis (Loughran-McDonald financial sentiment), linguistic complexity, evasion metrics ("I don't know" count, question dodging ratio)
- **LSTM/Transformer models**: Sequential earnings prediction with attention over historical quarters
- **Ensemble methods**: Combining alternative data signals with traditional financial features
- **Transfer learning**: Pre-trained financial LLMs (FinBERT, FinGPT, FinLlama) fine-tuned for earnings prediction

### LLM-Based Trading Agents (2026 State of the Art)
Xia et al. (2026) "Agentic Trading: When LLM Agents Meet Financial Markets" audited 77 studies through March 2026. The canonical architecture has four components:
- **Perception** (3 modalities): Text-based (FinBERT, FinGPT, FinLlama), Time-series (OHLCV, LOB), and Multimodal/Vision (FinVis-GPT, cross-attention fusion)
- **Memory** (3 tiers): Working (deterministic state store vs. generative context), Episodic (vector DBs, time-aware retrieval), Semantic (parametric vs. curated knowledge bases)
- **Reasoning** (3 paradigms): Reactive (sub-millisecond, non-LLM), Reflective (Chain-of-Thought, seconds-scale), Strategic (MCTS/planning, minutes-to-hours)
- **Action**: Order execution, portfolio rebalancing, risk management decisions

Key risk: **temporal misalignment** — news timestamps often reflect publication time, not ingestion time, creating look-ahead bias in LLM trading backtests.

---

## Cross-Domain Connections

| Connection | Description |
|------------|-------------|
| **Entity Resolution** | Factor model stock universes require clean entity identification across exchanges and share classes; Fellegi-Sunter matching for corporate entity deduplication |
| **Local-to-Frontier Model Bridging** | Cascade routing for quant model tiering — local models for factor computation, frontier models for regime detection and earnings call NLP |
| **Knowledge Graph Construction** | Factor→stock→sector→macro graph structures for systematic strategy reasoning and cross-asset signal propagation |
| **OSINT Methodology** | Alternative data sourcing follows OSINT collection frameworks; data veracity assessment mirrors source reliability grading |
| **Multi-Agent Orchestration** | Factor-specific analyst agents with ensemble voting on position sizing; supervisor agent for risk budget allocation |
| **Options Market Structure** | Factor signals inform implied volatility surface anomalies; statistical arbitrage across options- underlying mispricing (see [[options-market-structure]]) |
| **Job Posting Alt Data** | Job posting velocity as earnings predictor bridges alternative data forecasting ↔ earnings surprise modeling (see [[job-posting-alt-data-forecasting]]) |
| **AI Agent Architecture** | LLM-based trading agents (Xia et al. 2026) map the perception→memory→reasoning→action pipeline onto canonical agent architectures |

---

## References

### Primary Sources
1. Cakici, N., Fieberg, C., Metko, D., & Zaremba, A. (2024). "Machine Learning and Factor Return Predictability." *Finding: Factor momentum is the dominant driver; ML strategies produce no significant alpha once controlled for.*
2. Epstein, E.L., Wang, R., Choi, J., & Pelger, M. (2025). "Attention Factors for Statistical Arbitrage." arXiv:2510.11616. *Stanford; end-to-end learned latent factors + trading policy; net Sharpe 2.28.*
3. Du, X. (2025). "A-Share Multi-Factor ML Pipeline." *213-factor engine, GPU-vectorized PyTorch unfold primitives (51x speedup); mask-first tradability filtering +0.44 Sharpe; full system Sharpe 1.63.*
4. Bernard, V.L. & Thomas, J.K. (1989). "Post-Earnings-Announcement Drift: Delayed Price Response or Risk Premium?" *Journal of Accounting Research.*
5. Ball, R. & Brown, P. (1968). "An Empirical Evaluation of Accounting Income Numbers." *Journal of Accounting Research.*
6. Xia et al. (2026). "Agentic Trading: When LLM Agents Meet Financial Markets." *Audit-oriented evidence map of 77 studies, 19 meeting primary empirical evidence bar.*
7. Sciencedirect (2025). "Beyond the Last Surprise: Reviving PEAD with ML." *ML on 12-quarter SUE histories improves predictive accuracy vs. streak-based approaches.*

### Cross-Referenced Wiki Pages
- [[options-market-structure]] — Implied volatility surface dynamics, unusual options activity
- [[job-posting-alt-data-forecasting]] — Alternative data as economic indicators
- [[bridging-local-to-frontier-model-performance]] — Cascade routing for model tiering
- [[knowledge-graph-construction]] — Graph structures for systematic strategy reasoning
- [[multi-agent-orchestration-patterns]] — Factor-specific analyst agent ensembles

### Field Reports (Exocortex)
- `20260526_factor-models-earnings-surprise.md`
- `20260526_markets-statistical-arbitrage.md`
- `20260527_markets-alternative-data-quant.md`
- `20260528_earnings-surprise-modeling-pead.md`
- `20260528_quantitative-factor-models.md`
- `20260601_earnings-surprise-modeling.md`
- `20260605_ai-quantitative-trading-2026.md`

---

## Notes
- Created as DRAFT during BUILD cycle 462; deepened with 7 field reports and arXiv 2510.11616
- Key structural insight: Attention Factors (Epstein et al. 2025) unify factor model construction and statistical arbitrage execution in a single end-to-end learned pipeline — collapsing the traditional separate factor identification → mispricing detection → trading policy stages
- The factor momentum dominance finding (Cakici et al. 2024) has direct implications for sleep consolidation Phase 2 anti-pattern detection: momentum-driven signals that produce no independent alpha are isomorphic to BST momentum lock in agent reasoning
- LLM-based trading agents (Xia et al. 2026) map directly to Exocortex agent architecture — the perception→memory→reasoning→action pipeline is structurally identical to agent perception→context→inference→tool-call
