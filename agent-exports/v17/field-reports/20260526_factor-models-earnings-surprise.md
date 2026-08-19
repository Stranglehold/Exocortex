# Field Report: Factor Models & Earnings Surprise Modeling

**Date**: 2026-05-26
**Explorer**: Agent Zero
**Topic**: Markets & Financial Analysis — Factor Models & Earnings Surprise Modeling

## 1. What I explored
Investigated recent research (2024-2026) on applying machine learning to quantitative factor models and earnings surprise prediction. Focus on cross-sectional factor return predictability and post-earnings announcement drift (PEAD) using ML methods.

## 2. What I found

### Factor return predictability with ML (Cakici et al. 2024)
- Study of 242 factor characteristics (1972–2021), 153 long-short anomaly portfolios in US market
- ML models (random forest, boosting, neural nets) forecast cross-sectional factor returns successfully
- Top decile factors outperformed bottom decile by 0.27%–1.39% per month (1.08% for ensemble)
- **Factor momentum is the dominant driver**; once controlled for, ML strategies produced no significant alpha
- Strategies require high turnover (37–66% of factors replaced monthly)

### PEAD revival with longer SUE histories (2025)
- Sciencedirect paper "Beyond the last surprise: Reviving PEAD with ML"
- Using ML to forecast returns from historical earnings surprises, longer SUE histories (up to 12 quarters) markedly improved predictive accuracy vs shorter-horizon and streak-based approaches
- Improved Sharpe ratios and alphas

### A-share multi-factor ML pipeline (Du 2025)
- 213-factor engine using GPU-vectorized PyTorch unfold primitives (51x over pandas)
- Addressed upstream contamination from price-move limits biasing IC by 18%
- Mask-first tradability filtering contributed +0.44 Sharpe; full system Sharpe 1.63 on real A-share data

## 3. What I think is interesting
Factor momentum being the dominant signal validates behavioral persistence theories. The PEAD revival shows that deep earnings histories encode information markets don't fully price. Unexpectedly, the A-share paper's mask-first approach offers a general lesson for data pipeline integrity in any ML trading system. Also notable: ensemble methods consistently outperformed individual models, suggesting component diversification benefits.

## 4. What I'd explore next
- Deeper dive into PEAD ML methodologies (neural networks vs. gradient boosting)
- Factor interaction effects (nonlinear interactions, regime-switching)
- Transaction cost modeling for high-turnover factor strategies
- Alternative data integration for earnings surprise (job postings, patent filings)

## 5. Cross-domain connections
- **Agentic AI self-learning**: The factor momentum phenomenon (recent winners continue winning) is structurally similar to momentum-based learning strategies in reinforcement learning agents (policy gradient momentum, experience replay with recent priority). The ensemble model approach for factor return prediction parallels ensemble methods in agentic decision-making (combining multiple policies).
- **Data aggregation & entity resolution**: Earnings surprise prediction from alternative data sources (job postings, supply chain data) requires entity resolution to link companies across datasets — a direct connection to the data aggregation interest.
