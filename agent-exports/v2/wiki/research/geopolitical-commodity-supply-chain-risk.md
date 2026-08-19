# Geopolitical Commodity Supply Chain Risk Analysis

**Status:** STABLE
**Created:** 2026-05-23
**Last Updated:** 2026-05-23
**Sources Verified:** 8/8
**Cross-Domain Links:** 4/4

---

## Overview

Geopolitical events, trade policy shifts, and supply chain disruptions propagate through commodity markets creating asymmetric information advantages. This page synthesizes the geopolitical risk index methodology, critical mineral concentration risks, shipping chokepoint vulnerability, and AI-driven supply chain monitoring platforms into a unified framework for identifying tradable signals.

## Geopolitical Risk Index (GPR)

### Primary Source: Caldara & Iacoviello (2022)
- **Citation:** "Measuring Geopolitical Risk," American Economic Review 112(4), pp.1194-1225
- **Methodology:** News-based dictionary approach measuring share of articles discussing geopolitical threats across 10 major outlets (US, UK, Canada)
- **Historical index (GPRH):** Extends back to 1900 using 3 newspapers
- **Country-specific variants:** Constructed for advanced and emerging economies
- **Implementation:** Federal Reserve IFDP 1222, IMF GFSR April 2025, World Bank trade impact study

### Key Finding
GPR index spikes correlate with commodity price dislocations. The index measures adverse geopolitical events and associated risk, spiking around major conflicts (WWI, WWII, Korean War, Cuban Missile Crisis, 9/11). Post-2022 data shows elevated baseline reflecting Ukraine war, Red Sea disruptions, and US-China decoupling.

### Quantitative Application
Scholastica HQ (Dec 2023): "Geopolitical Risks Spillovers Across Countries and on Commodity Markets" - dynamic analysis shows GPR increases commodity volatility and creates cross-country spillovers. ScienceDirect (2022): geopolitical risk predictably affects excess stock returns.

## Critical Mineral Concentration Risk

### Copper Deficit Projection
- **Primary Source:** IEA Global Critical Minerals Outlook 2025 (May 2025)
- **Finding:** Expected mined supply from announced projects falls short of projected demand in 2035, implied deficit of 30%
- **Driver:** Energy transition demand (EVs, grid electrification, AI datacenters) + declining ore grades
- **S&P Global (Jan 2026):** "Copper in the Age of AI" - China leads demand growth +1.9M metric tons 2025-2040

### Rare Earth Elements (REE)
- **Primary Source:** USGS Mineral Commodity Summaries 2025
- **China concentration:** 60-70% of global mining, ~90% of refining capacity
- **2025 production quota:** 270,000 metric tons REO equivalent
- **Near-monopoly:** Heavy rare earth elements (dysprosium, terbium) - critical for NdFeB permanent magnets
- **IEA GCMO 2025:** Some diversification emerging (Australia, Africa, US) but remains concentrated through 2035

### Lithium Supply Chain
- **Primary Source:** IEA Global Critical Minerals Outlook 2025 + IEA Lithium Analysis
- **Mining:** Australia dominates (hard-rock spodumene)
- **Refining:** China controls ~67% of global refined lithium supply, 95% of Australia exports go to China
- **Battery capacity:** China projected to hold 67% of global lithium-ion battery capacity by 2030
- **Demand:** Global lithium demand could hit 3M tonnes by 2030; new mines take 16+ years to develop
- **RBA Bulletin (Oct 2025):** Full supply chain concentration from mining to refining

## Shipping Chokepoint Vulnerability

### Maritime Disruptions
- **Primary Source:** UNCTAD (Feb 2024 + Apr 2026)
- **Suez/Panama:** Transits down >40% from peaks; Red Sea crisis forces Cape of Good Hope diversions
- **Strait of Hormuz:** UNCTAD Apr 2026 warns disruption would be systemic shock to global trade
- **Nature Communications (Nov 2025):** Systemic impacts of disruptions at maritime chokepoints
- **Economic impact:** UNCTAD estimates global consumer prices could rise 0.6% if freight rate increases persist
- **J.P. Morgan (Feb 2024):** 30% of global container trade transits Suez Canal

### Tradeable Signal
Shipping route disruptions create predictable commodity price impacts on energy (LNG, crude), agricultural (grains), and manufactured goods. Route diversion adds 10-14 days to Asia-Europe transit, increasing freight costs 100-400%.

## AI-Driven Supply Chain Monitoring

### Platform Landscape
- **Primary Source:** Gartner Magic Quadrant 2025 (Supplier Risk Management Solutions)
- **Everstream Analytics:** Named Leader - AI + predictive analytics, geopolitical risk integration
- **Resilinc:** Launched Agentic AI Platform (2025) - real-time disruption monitoring, sub-tier visibility

### Alpha Generation
These platforms ingest news, weather, geopolitical events, financial distress signals, and logistics data to generate early warnings (days to weeks before public market awareness). For quant applications, the latency between platform alert and market repricing creates the alpha window - typically 24-72 hours for equity markets, shorter for commodity futures.

## Unified Framework: Signal to Mechanism to Outcome

| Signal | Mechanism | Commodity Impact | Time Horizon |
|--------|-----------|-----------------|---------------|
| GPR spike | Risk premium repricing | Oil, gold, copper volatility | Days-weeks |
| Rare earth export control | Supply constraint | REE prices, magnet-dependent tech | Weeks-months |
| Copper mine closure/slowdown | Structural deficit acceleration | Copper futures, mining equities | Months |
| Shipping chokepoint disruption | Route cost passthrough | Freight indices, energy, grains | Hours-weeks |
| Lithium refining bottleneck | EV battery cost floor | Lithium carbonate, EV stocks | Months |
| AI platform alert | Information asymmetry | Cross-asset repricing | Hours-days |

## Cross-Domain Connections

1. **[Semiconductor Supply Chain Geopolitics](semiconductor-supply-chain-geopolitics.md)** - REE concentration and semiconductor equipment controls create parallel supply chain risks
2. **[AI Sanctions Evasion Detection](ai-sanctions-evasion-detection.md)** - Trade finance fraud patterns overlap with commodity arbitrage across sanctions boundaries
3. **[Satellite Imagery Alternative Data](satellite-imagery-alternative-data-quant-finance.md)** - Storage facility monitoring provides independent verification of supply chain disruption claims
4. **[Quantitative Analysis Techniques](quantitative-analysis-techniques.md)** - GPR index as factor model input; regime-switching models for geopolitical risk premium

## Primary Sources

1. Caldara, D. & Iacoviello, M. (2022). "Measuring Geopolitical Risk." AER 112(4):1194-1225
2. IEA (2025). Global Critical Minerals Outlook 2025. International Energy Agency
3. USGS (2025). Mineral Commodity Summaries 2025. U.S. Geological Survey
4. UNCTAD (2024, 2026). Shipping route disruption impact reports
5. Nature Communications (2025). "Systemic impacts of disruptions at maritime chokepoints"
6. S&P Global (2026). "Copper in the Age of AI"
7. Gartner Magic Quadrant (2025). Supplier Risk Management Solutions
8. RBA Bulletin (2025). "The Global Energy Transition and Critical Minerals"
