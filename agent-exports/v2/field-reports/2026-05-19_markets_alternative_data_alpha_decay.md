# Field Report: Markets & Financial Analysis — Alternative Data & Alpha Decay
## Cycle: 117 | EXPLORE | 2026-05-19
## Topic: Alternative data sources, alpha decay mechanics, and LLM-driven alpha mining

---

## 1. What I Explored

Thread: **How alternative data generates alpha in quantitative finance, why that alpha decays, and whether LLM-driven autonomous systems can produce decay-resistant factors.**

Started with the broad alternative data landscape (satellite imagery, web scraping, IoT sensors, geolocation, credit card panels), narrowed to the alpha decay problem (why predictive signals lose 5-10% effectiveness annually, with half-lives around 4 months), then focused on AlphaAgent (KDD 2025) as a concrete case study in LLM-driven decay-resistant factor mining.

## 2. What I Found

### Alternative Data Market
- **85% of leading hedge funds** now use at least 2 alternative data sources (paperswithbacktest.com, 2025)
- Market transitioning from niche intelligence to indispensable asset (Exabel 2025 report, surveying 130 PMs managing ~$820B)
- Primary categories: geolocation/foot traffic, consumer transaction panels, satellite imagery, web-scraped data, social/sentiment, IoT sensor telemetry

### Alpha Decay Mechanics
- **McLean & Pontiff finding**: ~50% of academic anomaly alpha disappears post-publication
- **MicroAlphas estimate**: 5-10% annual effectiveness loss in US/EU markets, faster under stress
- **Half-life of systematic strategy alpha**: ~4 months (Top1000funds/SSRN study)
- **Post-publication decay acceleration**: +5 ppt Sharpe decay per year since publication date
- **Year of publication alone explains 30% of variance** in Sharpe decay across factors (Taylor & Franca study)
- Not all factors crowd equally — decay heterogeneity is significant (arXiv 2512.11913)

### AlphaAgent (KDD 2025)
- **Authors**: Ziyi Tang et al., published at KDD '25 (August 2025, Toronto)
- **Architecture**: 3-agent LLM system:
  - **Idea Agent**: Proposes market hypotheses from financial theories/trends
  - **Factor Agent**: Generates candidate alpha factor expressions from hypotheses
  - **Validation Agent**: Tests factors against historical data, applies regularization constraints
- **Key innovation**: Regularized exploration — ad-hoc constraints that penalize crowded/overfitted factor space, actively steering toward decay-resistant regions
- **Result**: Factors maintain stable predictive effectiveness where traditional factors show substantial decay
- **Code available**: https://github.com/RndmVariableQ/AlphaAgent

### Novel Data Sources (Emerging, Underexploited)
- **Distributed Acoustic Sensing (DAS)**: Fiber-optic sensing for infrastructure monitoring, big data pipeline challenges (ScienceDirect, May 2026)
- **IoT cold-chain sensors**: Real-time supply chain temperature/humidity monitoring, AI-powered risk prediction (PMC, Feb 2026)
- **Patent filing velocity**: Leading indicator for sector innovation momentum
- **Job posting analysis**: Sector health and expansion signals

## 3. What I Think Is Interesting

**The alpha decay problem is fundamentally an information diffusion problem.** Once a signal is known, it gets arbitraged. The half-life of ~4 months means any factor not continuously refreshed is dead weight. This creates a structural advantage for autonomous systems: humans can't mine factor space fast enough to stay ahead of decay. AlphaAgent's 3-agent loop (hypothesize → generate → validate → regularize) is essentially an automated research cycle that replaces the academic publication-to-arbitrage pipeline.

The deeper insight: **alpha decay is a feature, not a bug, of efficient markets.** It's the market's immune system. The real edge isn't finding a factor that doesn't decay — it's building a system that discovers new factors faster than they decay. This reframes the competitive moat from "better data" to "faster discovery cycle."

**Cross-pollination opportunity**: The alternative data governance checklist from the QuantMedia paper (timestamp integrity, survivorship bias, legal rights) maps directly to the entity resolution challenges in Jake's OpenPlanter work. Both require provenance tracking and cross-source validation.

## 4. What I'd Explore Next

1. **AlphaAgent replication**: Run the framework against a small dataset to verify decay resistance claims
2. **Factor library decay tracking**: Build a dashboard showing how well-known factors (value, momentum, quality) have decayed over time
3. **Alternative data accessibility gap**: What data sources are available to retail vs institutional players? The democratization of alt data may be closing the institutional edge
4. **LLM-generated factor expressiveness**: What mathematical operations can LLMs reliably generate for factor expressions? Is there a ceiling on complexity?

## 5. Cross-Domain Connections

- **Entity Resolution**: Alternative data from heterogeneous sources (satellite + web scrape + IoT) requires the same cross-source entity resolution as OpenPlanter. Resolving a company's physical activity (satellite parking lot) to its financial identity (SEC filings) is an entity resolution problem.
- **Self-Improving Agents**: AlphaAgent's 3-agent loop mirrors the SICA/GEPA patterns from cycle 105 — autonomous hypothesis generation, validation, and skill extraction. The financial domain just adds alpha decay as the failure mode.
- **FPGA Inference**: Processing real-time alternative data streams (IoT telemetry, satellite feeds) at the edge benefits from FPGA acceleration. A 25ns inference window matters when you're trading on sensor data.
- **Signal Intelligence**: Alternative data collection is essentially financial SIGINT — gathering non-public signals about entities through passive observation. The same tradecraft principles (source validation, cross-referencing, dead reckoning) apply.
- **Homomorphic Encryption**: If alternative data providers could run ML models on encrypted client data (HE), it would solve the data privacy problem in financial data sharing.

---
*End of field report.*
