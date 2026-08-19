# Field Report: Alternative Data Sources for Financial Analysis

**Date:** 2026-05-26
**Interest:** Markets & Financial Analysis
**Thread:** Alternative data — satellite imagery, web traffic analytics, patent filing velocity, job posting analysis

## 1. What I Explored

I investigated the current state of alternative data ("alt data") for financial analysis, focusing on four non-traditional data sources that Jake listed as exploration targets under Markets & Financial Analysis: satellite imagery (e.g., parking lots, oil storage), web traffic analytics, patent filing velocity, and job posting analysis. I also surveyed the broader alternative data market to understand scale, providers, and adoption patterns.

## 2. What I Found

**Market Size:** The global alternative data market was valued at $12 billion in 2025 and is projected to reach $168.2 billion by 2034, growing at a 34.0% CAGR (IMARC Group). This explosive growth is driven by hedge funds and institutional investors seeking differentiated information sources as traditional financial data becomes commoditized.

**Definition and Categories:** Alternative data encompasses information from non-traditional channels: web scraping, app usage, social sentiment, geolocation, surveys, workforce analytics, satellite/aerial imagery, credit card transaction data, and more (Bright Data 2026 guide). What makes it valuable is timeliness, granularity, and real-world signal — it reflects what is happening now, rather than backward-looking financial statements.

**Specific Sources Examined:**

- **Satellite Imagery:** Used to monitor retail parking lot traffic (predicting quarterly revenue before earnings), oil storage tank levels (commodity supply signals), agricultural yields, and shipping activity. Providers include Orbital Insight (acquired by Privateer in 2024), RS Metrics, and Ursa Space.

- **Web Traffic Analytics:** Aggregated website visit data from panels or ISP partnerships can signal e-commerce revenue trends, user growth, or declining engagement. Major providers include SimilarWeb, Semrush, and Datos (SparkToro).

- **Patent Filing Velocity:** Patent application data from USPTO, EPO, and WIPO can indicate R&D direction, technology moat strength, and competitive positioning. Firms like IFI Claims and PatSnap provide structured datasets. Patent filing acceleration in a sector can precede stock outperformance.

- **Job Posting Analysis:** Scraping company career pages and aggregators (LinkedIn, Indeed) reveals hiring trends that predict expansion, new product lines, or geographic moves. Providers include Revelio Labs, LinkUp, and Thinknum Alternative Data.

**Provider Landscape:** The top 20 alternative data providers in 2026 (capitalranking.com) span data aggregation platforms (Bright Data, Eagle Alpha), satellite imagery specialists, web traffic panels, and AI-powered signal generation firms. Bright Data's comprehensive guide rates providers on data freshness, coverage, compliance, and pricing.

**Hedge Fund Adoption:** Institutional investors use alt data for signal generation, portfolio monitoring, and risk assessment. The competitive edge comes from combining multiple alt data sources with traditional financial metrics to form non-consensus views.

## 3. What I Think Is Interesting

**The convergence with OSINT is striking.** The techniques for extracting intelligence from public data — satellite imagery analysis, web scraping, entity resolution across disparate sources — are essentially OSINT methods applied to financial markets. This creates a natural bridge between Jake's entity resolution interests and financial analysis: the same entity resolution algorithms that link corporate registries to campaign finance records can also link alternative data signals to specific public companies, private firms, or supply chain nodes.

**The entity resolution challenge is harder in alt data.** A job posting for "Senior ML Engineer at a stealth-mode startup in San Francisco" must be resolved to a specific company. A spike in web traffic to an obscure domain must be attributed to a corporate parent. This is the same core problem from Data Aggregation & Entity Resolution, but with noisier, less structured inputs.

**Alt data is becoming the new OSINT frontier.** Just as OSINT revolutionized intelligence analysis by democratizing access to actionable information, alt data is democratizing investment research. The barrier to entry is falling: Bright Data now offers managed data acquisition starting at $1,500/month, and some providers offer self-service APIs for individual researchers.

**The market is consolidating rapidly.** The 34% CAGR suggests a land-grab phase where aggregators and platform plays (Bright Data, Databricks acquiring data marketplaces) are absorbing point-solution providers (satellite, web traffic). The winners will be those who solve the entity resolution and signal-to-noise problem at scale.

## 4. What I'd Explore Next

1. **Specific satellite imagery analytics:** Deep dive into SAR (Synthetic Aperture Radar) for oil storage monitoring — SAR penetrates clouds and works at night, making it more reliable than optical imagery for commodity trading signals.

2. **Job posting NLP pipelines:** Build a proof-of-concept pipeline that scrapes Indeed/LinkedIn for a specific sector (e.g., electric utilities) and extracts hiring trend signals using NLP — directly applicable to Jake's Electric Utility interest.

3. **Patent-to-stock-price correlation studies:** Look for academic papers on whether patent filing velocity predicts equity returns, and at what lag.

4. **Entity resolution for alt data:** Investigate how commercial alt data platforms (Eagle Alpha, Neudata) handle entity mapping and whether they use Fellegi-Sunter, graph embeddings, or LLM-based approaches — directly feeding the Entity Resolution wiki page.

## 5. Cross-Domain Connections

- **Data Aggregation & Entity Resolution:** Alt data requires resolving signals to legal entities — the same core challenge Jake is exploring. The alt data industry has real economic incentives to solve this, so their approaches may be more advanced than academic methods.

- **Electric Utility & Critical Infrastructure:** Utility sector analysis can leverage alt data: satellite imagery of power plant construction, job postings for grid modernization roles, patent filings for smart grid technologies.

- **Hardware & Physical Computing:** Processing satellite imagery at scale requires GPU acceleration — relevant to RTX 3090 optimization. SAR image processing is computationally intensive.

- **History of Intelligence Operations:** The alt data industry is essentially the private-sector mirror of Cold War-era National Technical Means (satellite reconnaissance) and SIGINT collection — the same intelligence disciplines, now applied to alpha generation instead of national security.
