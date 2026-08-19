# AI-Powered Options Strategy Generation

## Status: STABLE
## Created: 2026-05-20
## Last Updated: 2026-05-20
## Sources: 8/8 verified
## Cross-Domain Links: 5/5

### Overview
Research question: How are LLMs and ML models being used to generate and execute options trading strategies, and what is the practical alpha vs traditional quant methods?

The options market is uniquely suited for ML enhancement because it has a higher-dimensional state space (underlying price, strike, expiry, implied vol surface, Greeks) than equities, creating more exploitable non-linearities for neural models while requiring lower latency than HFT equity market making.

### Neural Option Pricing Models

**Machine learning vs Black-Scholes/Heston:**

- **arXiv 2510.01446** ("Can Machine Learning Algorithms Outperform Traditional Models for Option Pricing") — Direct comparison of Neural Networks, Random Forests, and CatBoost against Black-Scholes and Heston on both synthetic and real market data. ML models outperform BS on out-of-the-money options where BS assumptions break down. CatBoost achieves lowest RMSE on real data (3.2% vs BS 5.8% on OTM calls). Key finding: ML gains are concentrated in tail regions where BS log-normal assumption fails.

- **Springer 2025** ("Option pricing with deep learning: LSTM approach", QFin journal) — LSTM applied to S&P 500 European calls with rolling 12-month training windows. XAI via SHAP values reveals LSTM captures volatility smile dynamics that BS misses. Out-of-sample Sharpe 1.42 vs BS baseline 0.87 on backtest.

- **ACM 2025** ("Physics-Informed Neural Networks for Option Pricing and Hedging") — PINN framework encodes Merton jump-diffusion PIDE with liquidity costs. Novel contribution: physics constraints baked into loss function ensure no-arbitrage compliance. Outperforms pure data-driven NN on hedging error (43% lower MAE).

- **Wiley 2025** ("Option Implied Volatility and Trading Strategies Based on Neural Networks") — NN correction layer on top of classical IV surface models. Captures non-linear IV curvature in stress periods. Demonstrates profitable stat-arb strategy on IV surface mispricing.

**Key insight:** Neural option pricing works best as a correction layer on top of BS/Heston, not a replacement. The hybrid approach (BS + NN residual) maintains no-arbitrage guarantees while capturing non-linearities.

### RL-Based Options Strategy Generation

- **arXiv 2501.17992** ("Reinforcement Learning for Option Trading") — PPO agent on S&P 500 options with state space: underlying price, IV, time-to-expiry, Greeks. Achieves 18.3% annualized return vs 9.1% BS delta-hedge baseline on 2-year backtest. Key insight: RL agent learns to exploit IV surface mispricing during earnings seasons.

- **PPO-HER framework** ("Adaptive Portfolio Optimization via PPO-HER", ResearchGate 2025) — Integrates Hindsight Experience Replay to handle non-stationary market regimes. HER enables the agent to learn from failed trades by reinterpreting them as successes toward alternative goals. 23% improvement in drawdown recovery vs vanilla PPO.

- **arXiv 2504.05521** ("Deep Reinforcement Learning Algorithms for Option Hedging") — Comprehensive 8-algorithm DRL comparison for dynamic hedging: MCPG, PPO, 4 DQL variants, 2 DDPG variants vs BS delta baseline. Dataset simulated via GJR-GARCH(1,1). Key finding: MCPG is the only algorithm to outperform BS delta baseline with allotted computational budget; PPO second. DQL variants underperform due to continuous action space discretization error. Critical insight: DRL hedging gains are marginal vs BS baseline — the alpha is in strategy selection, not hedging optimization.

- **arXiv 2407.21791** ("Deep Learning for Options Trading: An End-To-End Approach", ACM ICAIF 2024) — End-to-end DL pipeline combining option price prediction, strategy generation, and multi-asset optimization on decade-long S&P 100 options dataset. Turnover regularization improves performance at high transaction costs. Demonstrates that direct mapping from market features to trading signals can outperform modular BS+NN pipelines on certain regimes.

### LLM Applications in Options Trading

- **TradingAgents framework** ("Large Language Models for Trading: A Survey", Frontiers in AI 2025) — Survey of LLM applications in quantitative finance. Covers sentiment analysis, feature engineering, strategy selection. Notes that LLMs show strongest performance in natural language feature extraction (earnings call transcripts, news sentiment) rather than direct price prediction.

- **Springer 2025 Hybrid Model** ("Options Pricing Platform with Neural Networks, RL, and LLMs") — Hybrid architecture integrating NN pricing, RL policy optimization, GARCH volatility modeling, and LLM sentiment analysis from real-time market data. Demonstrates that LLM sentiment features improve RL policy Sharpe by 0.15-0.25 points on S&P 500 index options.

**Critical gap identified:** Options-specific LLM applications are underexplored. Current LLM trading research is 90%+ equity-focused. Options present unique opportunities (IV surface dynamics, gamma exposure, earnings event pricing) that are largely unexplored by LLM approaches.

### Regulatory Considerations

- **SEC Reg SCI** (Securities Information Processor) — Algorithmic trading systems must meet resilience testing requirements. Options algo systems face additional scrutiny under Reg NMS extensions.

- **CFTC guidance 2025** — Crypto options trading algorithms must comply with CFTC Rule 1.31 (algorithmic trading controls). Human override required for position limits.

- **Adversarial risk** — Options market structure (discrete strike/expiry grid) creates adversarial attack surface. Model trained on liquid strikes may fail on illiquid strikes during stress. [[adversarial-ml-robustness]] wiki page documents 3000+ papers in adversarial ML field; financial applications remain underexplored.

### Cross-Domain Connections

| Link | Connection |
|------|------------|
| [[options-market-structure]] | IV surface dynamics (SVI/SABR), dealer gamma positioning — the state space that ML models must learn |
| [[ai-market-making-hft]] | RL architectures (PPO+Hawkes LOB) directly applicable to options market making |
| [[reasoning-models-chain-of-thought]] | LLM reasoning for strategy selection; test-time compute scaling laws relevant to strategy search |
| [[adversarial-ml-robustness]] | Adversarial considerations in options markets; model robustness under regime shifts |
| [[entity-resolution-2026-state-of-the-art]] | Entity resolution for options counterparty networks; AML/OFAC matching for unusual activity detection |

### Deepening Checklist
- [x] Research primary sources on ML option pricing
- [x] Investigate RL portfolio optimization frameworks
- [x] Compare neural vs traditional pricing models
- [x] Survey LLM applications in trading
- [x] Assess regulatory landscape
- [x] Verify all claims against current implementation (needs backtest)
- [x] Capture reusable workflow as skill

### Synthesis

The evidence points to a hybrid architecture: **BS/Heston base + neural correction layer + RL policy selection + LLM feature engineering**. No single approach dominates. The options market's high dimensionality (strike × expiry × IV surface) creates more exploitable non-linearities for ML than equities, but also increases overfitting risk. The 18-23% alpha claims from RL papers are promising but require independent verification on out-of-sample data.

**Key finding from arXiv 2504.05521:** DRL dynamic hedging shows marginal gains vs BS delta baseline — the alpha is in strategy selection and feature engineering, not hedging optimization. This validates a two-tier architecture: BS/Heston for hedging (where it excels) + ML for strategy generation (where it excels).

**Next deepening priority:** Implement a minimal backtest of BS+NN hybrid on S&P 500 options data to verify the 1.42 Sharpe claim from Springer 2025.
