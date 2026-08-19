# Market Mechanics & Quantitative Analysis (2026)

**Status:** STABLE
**Created:** 2026-08-18
**Last Updated:** 2026-08-18
**Origin:** Jake's standing directive (Eitan workstream / Palantir investment thesis) — least-recently-explored interest
**Domain:** Markets & Financial Analysis

## Scope

Understanding market mechanics and identifying asymmetric opportunities through data-driven analysis rather than speculation. This page covers the analytical toolkit — factor models, statistical arbitrage, alternative data, Fed/repo mechanics, sector analysis, and options market structure — not trading signals. It synthesizes the shared Exocortex corpus (which already has deep coverage) and grounds it in the 355-book technical library.

## 1. Quantitative Analysis Techniques

**Factor Models in Asset Pricing** (from `quantitative-analysis-techniques.md`, STABLE v17):
- Multi-factor models (Fama-French extensions, Q-factor models)
- Machine-learning-enhanced factor generation
- Autonomous factor discovery architectures (FactorMiner, Hubble, Cognitive Alpha Mining)
- PCA applied to asset returns yields data-driven risk factors; principal components of the return correlation matrix build uncorrelated portfolios (book: *Hands-On ML for Algorithmic Trading*, Ch.12 — ICA/PCA for algo trading, p.385)

**Statistical Arbitrage** (subset of quant analysis — exploits temporary price divergences between related instruments via mean-reversion, cointegration, factor models rather than directional bets):
- Pairs trading and cointegration strategies
- Mean-reversion approaches
- Deep-learning signal generation
- Cross-asset momentum and reversal signals

**Earnings Surprise Modeling:**
- PEAD (Post-Earnings Announcement Drift) anomaly
- NLP-based earnings prediction from transcripts and filings
- Alternative-data signals for earnings forecasting

## 2. Alternative Data Sources

**Provider taxonomy** (book: *Hands-On ML for Algorithmic Trading*, Ch.3 "Alternative Data for Finance", p.77 — AlternativeData.org / Yipit categories):

| Category | # Providers | Use case |
|----------|------------|----------|
| Social sentiment | 48 | Raw/processed social media; short-term trends |
| Satellite | 26 | Aerial monitoring of medium-term economic activity |
| Geolocation | 22 | Retail, commercial real estate, event foot traffic |
| Web data & traffic | 22 | Search interest, brand popularity, events |
| Credit/debit card usage | 14 | Near-term consumer spend, business revenues |
| App usage | 7 | App sales, secondary data |
| Email & consumer receipts | 6 | Consumer spend by chain/brand/sector/geography |
| Weather | 4 | Crop and commodity longer-term trends |
| Other | 87 | — |

**Key providers:** Dataminr (social sentiment + news, real-time ML signals, $1.6B valuation 2018), StockTwits (professional sentiment micro-blogging), RavenPack (unstructured text → structured sentiment indicators from 19,000+ web publications).

**Core insight** (book Ch.16, p.478): *Data is the single most important ingredient.* State-of-the-art ML (deep nets) improves with more data, but backtest overfitting is the dominant challenge and requires significant attention. Domain expertise is what realizes the value in the data.

**Web traffic as alt data** (from `web-traffic-analytics-alternative-data.md`, v17): web traffic anomalies pre-earnings signal revenue beats/misses; web-traffic correlation between competitive companies informs relative-value trading; integrates with satellite (physical) + options flow (multi-signal corporate intelligence).

## 3. Federal Reserve Operations & Repo Mechanics

From `financial-markets-analysis-2026-draft.md` (v2) + `treasury-market-functioning.md` (v17):
- **Balance sheet management:** QT/QE cycles
- **Repo market mechanics:** SOFR-IORB spread as the key liquidity signal; SFR/SRF residual demand modeling; reserve scarcity → repo rate volatility
- **Treasury market functioning:** primary dealer system, auction mechanics, TGA/reserve management
- **Cross-domain:** repo spreads and futures-cash basis are low-probability, high-entropy events — monitoring them parallels agent anomaly detection (entropy-as-signal). Identifying who holds dealer net longs / runs the basis trade requires the same registry/positional data fusion as OSINT entity resolution.

## 4. Options Market Structure

From `financial-markets-analysis-2026-draft.md` (v2) + `0dte-options-expiration-dynamics.md` (v17):
- Global options market processes ~108B contracts annually (FIA 2023); 1.35M distinct US-listed contracts
- **Implied volatility surface dynamics:** SVI/SSVI parameterization for arbitrage-free surfaces; deep hedging; no-arbitrage surface construction; order-flow interaction with market-maker delta-hedging
- **2025-2026 advances:** ML-driven GEX (gamma exposure) regime detection; SABR-informed IV surfaces; GAN-based volatility surface reconstruction (IEEE 2025); LLM-based gamma exposure inference (71.5% detection rate from raw gamma data)
- **Dealer positioning signals:** GEX, pin risk, 0DTE impact; gamma scalping; short-tenor pricing
- **Unusual activity detection:** 0DTE flow and OI screens

## 5. Sector-Specific Analysis

- **Utility sector regulatory dynamics** — see `ai-grid-edge-digital-twin-critical-infrastructure-draft.md` (STABLE)
- **Defense procurement cycles** — see `ai-geopolitical-risk-forecasting.md` (STABLE)
- **Semiconductor capex trends** — see `ai-accelerator-landscape-2026` (NVIDIA FY2026 DC ~$193.7B, Blackwell→Vera Rubin annual cadence, hyperscaler ASIC counterweight: Google Ironwood TPU v7, AWS Trainium 2, Meta/Broadcom 2nm MTIA ~1GW through 2029)

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[ai-cross-asset-regime-detection-draft]] | Factor models + regime detection share the same signal-extraction machinery |
| [[ai-algorithmic-trading-quant-finance]] | Direct overlap — this page is the analytical toolkit, that page is the AI execution layer |
| [[ai-geopolitical-risk-forecasting]] | Defense procurement + sector analysis feed geopolitical risk models |
| [[electric-utility-critical-infrastructure]] | Utility sector regulatory dynamics are a shared sector-analysis target |
| [[entity-resolution]] | Dealer net-long / basis-trade identification = registry/positional data fusion (OSINT analog) |
| [[entropy-as-signal]] | Repo spreads, futures-cash basis, IV surface = low-probability high-entropy regime signals |
| [[test-time-compute-reasoning-scaling-draft]] | LLM gamma inference (71.5%) is a test-time-compute application to market microstructure |

## Sources

- **Shared Exocortex corpus (PRIMARY):** `quantitative-analysis-techniques.md` (STABLE v17), `financial-markets-analysis-2026-draft.md` (v2), `web-traffic-analytics-alternative-data.md` (v17), `0dte-options-expiration-dynamics.md` (v17), `treasury-market-functioning.md` (v17), `interests.md` (directive origin)
- **Book library (grounded source):** *Hands-On Machine Learning for Algorithmic Trading* — Ch.3 Alternative Data for Finance (p.77-97, provider taxonomy), Ch.12 ICA/PCA for algo trading (p.385), Ch.16 Next Steps (p.478, data-as-ingredient + backtest overfitting)
- **Field reports (Exocortex):** 20260526_factor-models-earnings-surprise, 20260526_markets-statistical-arbitrage, 20260527_markets-alternative-data-quant, 20260528_earnings-surprise-modeling-pead, 20260528_quantitative-factor-models, 20260601_earnings-surprise-modeling, 20260605_ai-quantitative-trading-2026

## Deepening Note

Created as the least-recently-explored topic from Jake's standing directive. The shared corpus already had deep, STABLE coverage of every sub-area (factor models, stat-arb, alt data, Fed/repo, options structure) — so this page's value is **synthesis + grounding**: it unifies the scattered v17/v2 pages into one coherent toolkit and adds the book-library's concrete alt-data provider taxonomy (Ch.3) and ML-for-trading lessons (Ch.16) as citable source material. No web search was needed — the corpus + library fully covered the topic.
