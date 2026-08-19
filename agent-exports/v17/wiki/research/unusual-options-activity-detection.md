# Unusual Options Activity Detection

Status: STABLE

---

## Overview

Unusual Options Activity (UOA) detection identifies abnormally large or anomalous options trades that deviate from historical norms. These trades may precede material corporate events — earnings surprises, M&A announcements, regulatory actions — and serve as early signals of informed trading, sentiment shifts, or volatility regime changes. UOA detection combines statistical thresholding, anomaly detection ML, and options market microstructure analysis to surface actionable signals from the options tape.

---

## Key Concepts

- **Unusual Options Activity (UOA):** Options trades that deviate significantly from historical norms in volume, size, timing, or strike/expiration characteristics.
- **Information leakage hypothesis:** Informed traders may prefer options markets due to embedded leverage, limited downside (long positions), and lower capital requirements compared to equity positions.
- **Sweep orders:** Large orders split across exchanges to minimize market impact — often a signature of institutional or informed flow.
- **Gamma Exposure (GEX):** Dealer positioning metric derived from net options open interest; shifts in GEX can predict intraday volatility and directional pressure.

---

## Detection Methodology

### 1. Traditional Statistical Thresholding

First-generation UOA detection relies on deviation-from-norm metrics:

- **Volume / Open Interest ratio:** A contract with 100 average daily volume suddenly trading 5,000+ contracts — typically >5σ above 20-day moving average.
- **Premium dollar thresholds:** Aggregate premium spent on a single strike/expiration exceeding a threshold (e.g., $500K+ in notional value).
- **Out-of-the-money (OTM) option surges:** Large OTM call buying suggests asymmetric upside bets; large OTM put buying suggests hedging or directional bearishness.
- **Call/Put ratio skew:** Sudden imbalance in bullish vs. bearish contract flow, especially when concentrated in near-term expirations.
- **Block trades outside the bid/ask spread:** Trades executed at a premium to the prevailing spread suggest urgency or conviction.

### 2. Machine Learning Anomaly Detection

Modern approaches move beyond static thresholds to learned normality:

- **Autoencoders:** Train on historical option flow features (volume, OI, Greeks, moneyness, time-to-expiry); flag trades with high reconstruction error as anomalous.
- **Isolation Forests:** Ensemble-based anomaly scoring on multi-dimensional option trade features — effective for detecting outlier combinations of size, timing, and strike placement.
- **Graph Neural Networks (GNNs):** Model option chains as graphs (nodes = strikes/expirations, edges = spread relationships); detect anomalous subgraph patterns indicating coordinated positioning.
- **LLM-based gamma exposure inference:** arXiv:2512.17923 demonstrates LLM reasoning over option flow data to infer dealer positioning and predict gamma-driven price pressure.
- **Time-series anomaly detection:** Foundation models for zero-shot TS anomaly detection (Lan et al. 2025) and LLM-guided knowledge distillation (Liu et al. 2024, IJCAI) applicable to streaming option flow.

### 3. Signature-Based Detection

Pattern recognition approaches for known informed-trading signatures:

- **Pre-earnings call accumulation:** Unusual call buying in the 1-2 weeks before earnings announcements.
- **Pre-M&A positioning:** Concentrated option activity in small/mid-cap names preceding takeover announcements (detection-controlled estimation: only ~30% of M&A insider trading detected by regulators; Aspris et al. 2025).
- **Sector rotation signals:** Cross-sector UOA monitoring to detect capital rotation before it appears in equity flows.
- **Sweep order detection:** Multi-exchange fragmentation patterns indicative of institutional algorithms executing large orders.

---

## Tool Landscape

| Tool | Type | Key Features |
|------|------|-------------|
| **Intrinio UOA Feed** | Data API | Real-time UOA without OPRA licensing; filtered by volume/strike/expiration; Greeks + sentiment indicators |
| **FlowAlgo** | Desktop/Web | Real-time options flow screener; dark pool prints; institutional order-flow detection |
| **Cheddar Flow** | Web | Visual options flow platform; unusual activity alerts; backtesting |
| **Unusual Whales** | Web/API | Retail-focused UOA alerts; politician trade tracking; sentiment aggregation |
| **TradeAlgo** | Web/Mobile | AI-powered options flow; dark pool data; DMA analytics |
| **BlackBoxStocks** | Web | Real-time options flow + social sentiment integration |

---

## Regulatory Context

- **SEC Market Abuse Unit:** Uses ARTEMIS (Advanced Relational Trading Enforcement and Market Investigation System) for pattern-based surveillance of options and equity markets.
- **FINRA:** Cross-market surveillance integrating options (OPRA) and equity (SIP/UTP) data; 2026 Annual Regulatory Oversight Report emphasizes AI-driven anomaly detection for market manipulation and insider trading.
- **OPRA (Options Price Reporting Authority):** Consolidated tape for U.S. listed options; UOA detection typically requires OPRA data or a licensed alternative (Intrinio offers OPRA-free UOA via derived feeds).
- **Insider trading detection gap:** Academic research (Aspris et al. 2025) finds only ~30% of M&A-related insider trading detected by regulators, motivating private-sector UOA monitoring.

---

## Cross-Domain Connections

- **[[financial-intelligence-entity-resolution]]** — Linking option trader identities across brokers/exchanges for SAR filing triggers.
- **[[alternative-data-sources]]** — Options flow as alternative data for earnings prediction and sentiment analysis.
- **[[quantitative-factor-models]]** — Incorporating options-implied signals (VIX term structure, put/call skew, GEX) into factor models.
- **[[options-market-structure]]** — Foundational understanding of exchange architecture, PFOF dynamics, and 0DTE trading growth required for UOA interpretation.
- **[[earnings-surprise-modeling]]** — UOA as a leading indicator for PEAD strategies.
- **[[network-analysis-graph-theory]]** — GNN-based anomaly detection on option-chain graphs; community detection for coordinated trader identification.
- **[[entity-resolution-algorithms]]** — Fellegi-Sunter probabilistic linkage for cross-broker trader identity resolution from fragmented options tape data.
- **[[intelligence-failure-analysis]]** — Structural isomorphism: the undetected-insider-trading blind spot mirrors the “zero-loss fantasy” pattern in private credit.

---

## References

### Academic
1. Aspris, A., et al. (2025). “Insider trading footprints: An empirical look at detected cases in Australia.” *International Review of Financial Analysis*. DCE model finds 17.79% M&A insider trading rate, 29.59% detection rate.
2. arXiv:2512.17923 — LLM-based gamma exposure inference from options flow data.
3. Lan et al. (2025). “Towards Foundation Models for Zero-Shot Time Series Anomaly Detection.” arXiv.
4. Liu et al. (2024). “Large Language Model Guided Knowledge Distillation for Time Series Anomaly Detection.” IJCAI 2024.
5. arXiv:2503.13195 — “Deep Learning Advancements in Anomaly Detection: A Comprehensive Survey.”

### Industry & Regulatory
6. Intrinio. (2025, June 24). “How Institutional Investors Use Intrinio’s Unusual Options Activity to Detect Market Trends.”
7. FINRA. (2025, December). “2026 Annual Regulatory Oversight Report.”
8. SEC. ARTEMIS surveillance system documentation.

---

*Last updated: 2026-07-04*
