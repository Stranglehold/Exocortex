# Markets & Financial Analysis

**Status:** STABLE
**Last updated:** 2026-05-16
**Related:** [entity-resolution-at-scale](research/entity-resolution-at-scale.md), [osint-pipeline-architecture](research/osint-pipeline-architecture.md), [semiconductor-supply-chain](research/semiconductor-supply-chain.md)

## Overview

Financial analysis as an investigative and strategic capability. Covers market data pipelines, financial statement analysis, SEC/EDGAR data extraction, campaign finance analysis, and connections to entity resolution.

## Entity Resolution in Financial Contexts

### OpenPlanter Implementation

OpenPlanter's `entity_resolution.py` demonstrates a production-grade financial entity resolution pipeline:

1. **Multi-source data ingestion**: SEC EDGAR filings, FEC campaign finance, SAM.gov contracts, USAspending.gov, OCPF Boston campaign finance
2. **Entity normalization**: CPF ID mapping, vendor name normalization, fuzzy matching (fuzzymatch)
3. **Cross-linking**: Vendor-to-donor matching via `cross_link_analysis.py`, identifying political connections to government contractors
4. **Pattern matching**: Sole-source contract detection, recurring vendor identification, donation pattern analysis

Key insight: Financial entity resolution is fundamentally a **graph construction problem**. Entities (people, companies, contracts, donations) form a heterogeneous graph where edges represent relationships. Entity resolution quality determines graph accuracy — poor ER creates false connections or misses real ones.

### SEC EDGAR Patterns

- **CIK as canonical identifier**: SEC CIK numbers provide unique entity identifiers across all filings
- **Entity resolution challenges**: Parent/subsidiary relationships, name changes, ticker symbol changes require CIK-based resolution
- **XBRL data**: Structured financial statements enable automated extraction but require taxonomy mapping
- **Rate limiting**: 10 requests/second, bulk archives for large-scale analysis

### Campaign Finance Entity Resolution

- **FEC data**: Donor names, amounts, committees require fuzzy matching to resolve entities
- **Massachusetts OCPF**: Local campaign finance with vendor/donor overlap detection
- **Cross-linking vendors to donors**: Identifying companies that receive government contracts while donating to politicians who approve those contracts

## Financial NLP & AI Capabilities

### Earnings Call Analysis

- **FinBERT**: Fine-tuned BERT for financial text classification (sentiment, entity extraction)
- **Recent research (2025-2026)**: AI-driven earnings call analysis for sentiment, guidance extraction, management tone analysis
- **Limitations**: Financial language is domain-specific; general LLMs perform poorly without fine-tuning

### SEC Filing Analysis

- **FinSightAI (2026)**: RAG platform for SEC filing analysis, turning hundreds of filings into searchable knowledge
- **Document structure**: 10-K/10-Q, 8-K, proxy statements have semi-structured formats requiring parsing
- **Entity extraction**: Executive compensation, related-party transactions, risk factor analysis

### Fraud Detection

- **Pattern analysis**: Unusual trading patterns, related-party transaction detection
- **Network analysis**: Corporate ownership structures, beneficial ownership chains
- **AI limitations**: False positive rates remain high; domain expertise required for interpretation

## Market Data & Prediction

### Current Capabilities

- **Real-time data**: Alpaca, Polygon, IEX Cloud APIs
- **Alternative data**: Satellite imagery (parking lots, shipping), web scraping, social sentiment
- **Supply chain signals**: Semiconductor export controls, commodity pricing, logistics data

### Prediction Limitations

- **Efficient market hypothesis**: Public information is rapidly priced in
- **AI prediction SOTA**: No reliable edge in stock price prediction; AI excels at pattern recognition but not at predicting novel events
- **Risk management**: AI better suited for risk analysis, portfolio optimization, and scenario modeling than pure prediction

## Regulatory & Compliance Landscape

### SEC Regulation

- **Rate limiting**: 10 requests/second for EDGAR API
- **User-Agent requirements**: All requests must include identifiable User-Agent header
- **Bulk data**: Nightly archives preferred for large-scale analysis

### Campaign Finance Regulation

- **FEC reporting**: Quarterly/annual donor reporting with contribution limits
- **State-level variations**: Massachusetts OCPF, California, New York have distinct reporting requirements
- **Data quality**: Inconsistent name formatting, missing addresses, committee mergers

## Cross-Domain Connections

1. **Entity resolution → Intelligence operations**: HUMINT source reliability grading maps to financial source evaluation; both require assessing data quality and potential biases
2. **OSINT methodologies → Corporate intelligence**: Public data collection, normalization, and analysis patterns transfer directly to financial investigation
3. **Privacy/Cryptography → Financial data protection**: Homomorphic encryption enables computation on encrypted financial data; ZKPs prove compliance without revealing underlying transactions
4. **Semiconductor supply chain → Market analysis**: Export controls, pricing, and logistics data feed directly into market analysis and prediction models
5. **SCADA/ICS → Financial infrastructure**: Banking systems use similar SCADA/ICS patterns for operational technology; security principles transfer

## Research Gaps

- **Real-time financial entity resolution**: Current OpenPlanter implementation is batch-oriented; streaming ER would enable real-time connection detection
- **Cross-jurisdictional entity resolution**: Linking US SEC filings with international corporate registries remains unsolved at scale
- **AI-driven financial network analysis**: Graph neural networks for financial relationship discovery are emerging but not production-ready
- **Automated regulatory compliance**: AI for monitoring compliance with SEC, FEC, and state-level regulations is nascent

## Implementation Notes

- OpenPlanter's `sec_edgar_collector.py` handles SEC data ingestion
- `cross_link_analysis.py` demonstrates vendor-donor connection detection
- `entity_resolution.py` provides the core resolution pipeline
- Future work: Extend to real-time data feeds, international registries, AI-assisted entity resolution

## References

- SEC EDGAR API documentation
- FEC campaign finance data
- OpenPlanter financial collectors (phase2/phase3)
- FinBERT and financial NLP research
- Medium article: "How We Built a Financial Intelligence Engine That Thinks in Relationships" (Apr 2026)
- FinSightAI RAG platform (Mar 2026)
