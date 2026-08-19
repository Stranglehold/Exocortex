# Alternative Data Sources for Quantitative Analysis (2026)

**Status:** DRAFT
**Created:** 2026-07-15
**Primary Sources:** 0
**Cross-Domain Links:** 0

## Overview

Alternative data encompasses raw data as well as data that is aggregated or processed to add value for quantitative analysis. The market has matured from simple parking-lot counting to multi-modal fusion with edge-AI processing pipelines. Key finding: alternative data alpha has a ~3-6 month half-life (faster than consumer transaction data), making continuous discovery cycles the competitive moat rather than data access alone.

Three trends have revolutionized the use of data in algorithmic trading:
1. The exponential increase in the amount of digital data
2. The increase in computing power and data storage capacity at lower cost
3. The advances in ML methods for analyzing complex datasets

## Data Categories (by provider count)

Based on AlternativeData.org taxonomy:

| Category | Providers | Signal Type | Half-life |
|----------|-----------|-------------|-----------|
| Social sentiment | 48 | Raw/processed social media, short-term trends | 1-3 months |
| Satellite | 26 | Aerial monitoring of medium-term economic activity | 3-6 months |
| Geolocation | 22 | Track retail/commercial real estate/event foot traffic | 2-4 months |
| Web data & traffic | 22 | Monitor search interest, brand popularity, events | 1-2 months |
| Credit/debit card | 14 | Track near-term consumer spend and business revenues | 6-12 months |
| App usage | 7 | Monitor app sales or collect secondary data | 3-6 months |
| Email & receipts | 6 | Track consumer spend by chain, brand, sector, geography | 6-12 months |
| Weather | 4 | Crop and commodity-related longer-term trends | 6-12 months |
| Other | 87 | Various specialized sources | Varies |

## Key Providers

### Social Sentiment
- **Dataminr**: Founded 2009, $569M total funding, $1.6B valuation. Real-time signals from social media using ML. Serves buy/sell-side investment firms, news organizations, public sector.
- **RavenPack**: Analyzes 19,000+ web publications, premium newswires, regulatory info. Produces structured sentiment indicators.
- **StockTwits**: Social network where hundreds of thousands of investment professionals share trading ideas.

### Satellite Imagery
- Parking lot counting for retail earnings prediction
- Oil tanker tracking for energy supply chain analysis
- Shadow analysis of oil well activity
- Agricultural monitoring for commodity forecasting

### Web Traffic & Search
- Google Trends for debt/economic sentiment
- Brand popularity monitoring
- Job posting velocity as leading indicator
- Patent filing analysis for innovation tracking

## Signal Characteristics

- **Social media**: Competitive supply, lower prices, <5 years history typically
- **Search history**: Available from 2004, more stable long-term signal
- **Credit card data**: ~10 years history, near real-time availability, highly predictive
- **Corporate earnings**: Quarterly with 2.5-week lag — alternative data provides earlier signal

## Integration with Quantitative Analysis

- Options flow as alternative data: Unusual options activity predicts corporate events, earnings surprises, M&A activity
- Cross-referencing UOA signals with satellite imagery, web traffic, or patent filings creates multi-signal intelligence
- Mask-first data pipeline pattern generalizes to any quant system where data quality gates model performance

## Primary Sources

1. Machine Learning for Trading (Ch. 1, 3) — Humble Bundle collection
2. AlternativeData.org provider taxonomy
3. Dataminr funding/valuation data (2018)
4. RavenPack methodology documentation
5. Satellite imagery alpha half-life research

## Cross-Domain Connections

- [quantitative-analysis-techniques](quantitative-analysis-techniques.md) — factor models, statistical arbitrage
- [options-market-structure](options-market-structure.md) — unusual options activity as alt-data
- [ai-financial-markets](ai-financial-markets.md) — market microstructure, alpha decay
- [geopolitical-risk-analytics-modeling](geopolitical-risk-analytics-modeling.md) — supply chain indicators

## 2026 Developments

### Provider Landscape (2026)

The alternative data market reached $5.2B in 2026 (FMI), projected to hit $22.9B by 2036 (34% CAGR). Key providers:

| Provider | Focus | Coverage |
|----------|-------|----------|
| Techsalerator | Global B2B/B2C data hub | 195 countries |
| Preqin | Alternative assets (PE, hedge funds, real estate, infrastructure) | Global |
| Quandl/Nasdaq Data Link | Financial/economic datasets, commodity flows, macro signals | Global |
| Similarweb | Digital intelligence, web traffic, app engagement metrics | Global |
| Bombora | B2B intent data (online research behavior) | US/EU |
| Earnest Analytics | Consumer credit/debit card transaction data | US |
| SpaceKnow | Satellite imagery + ML for economic activity indicators | Global |

### Key Trends (2026)

1. **Real-time data adoption**: Satellite imagery, social media, web scraping, app usage, and geolocation signals now supplement or replace quarterly reports
2. **AI/ML processing**: Advanced ML enables processing of massive non-traditional data volumes
3. **New categories**: B2B intent data, digital intelligence/web traffic metrics, granular consumer transactions, satellite-derived economic indicators
4. **Compliance focus**: GDPR/CCPA compliance now prioritized alongside data breadth

### QuantMedia Nowcasting Framework (2026)

QuantMedia published a nowcasting framework for alternative data features:
- Machine learning pipeline for alternative data features
- Data governance checklist addressing timestamp integrity, survivorship bias, legal rights
- Point-in-time (PIT) data management to avoid look-ahead bias

## Deepening Notes

- Deepened 2026-07-15 with 2026 provider landscape, market size ($5.2B), and key trends.
- Grounded in ML for Trading textbook (Ch. 1, 3) + Techsalerator 2026 report + QuantMedia framework.
- Key insight: Alternative data alpha half-life is 3-6 months, making continuous discovery the moat.
- Credit card data has ~10 years history and near real-time availability — most reliable dataset.
- Social sentiment is commoditized (48 providers) but satellite/geolocation still differentiated.
- Multi-signal cross-referencing creates superior alpha vs single-source approaches.
- 2026 shift: from niche tool to mainstream strategic resource across finance, retail, logistics, tech.

## Key Areas to Explore

- Satellite imagery (parking lots, oil storage, shipping traffic)
- Web traffic analytics (retail foot traffic, app usage)
- Patent filing velocity
- Job posting analysis
- Social media sentiment
- Credit card transaction data
- Utility consumption patterns
- Supply chain indicators

## Primary Sources

[To be populated after research]

## Cross-Domain Connections

[To be populated after research]
