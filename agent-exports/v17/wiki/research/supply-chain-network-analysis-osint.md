# Supply Chain Network Analysis via OSINT

**Status: STABLE**
**Created: 2026-07-07 | Deepened: 2026-07-07**
**Topic Areas: OSINT Methodology · Strategic Intelligence · Sanctions Enforcement · Supply Chain Risk**

## Overview

Supply chain network analysis using open-source intelligence reconstructs multi-tier supplier networks, logistics flows, and corporate ownership structures from publicly available data. This methodology enables sanctions enforcement, strategic intelligence, investment analysis, and industrial base vulnerability assessment without access to classified or proprietary data.

## Core Methodology: Five-Phase OSINT Supply Chain Reconstruction

### Phase 1: Corporate Registry Mapping
Identify entities and ownership structures using:
- National business registries (Companies House, SEC EDGAR, OpenCorporates, local equivalents)
- Beneficial ownership disclosures
- Bellingcat curated archive of country-specific business registries
- Cross-reference with sanctions lists (OFAC SDN, EU, UK, UN)

### Phase 2: Trade Data Analysis
Map physical goods flows using:
- Customs data aggregators (Panjiva, ImportGenius, UN Comtrade)
- Bill of lading records
- Harmonized System (HS) code tracking
- Country-level trade statistics

### Phase 3: Shipping & Logistics Tracking
Track maritime and logistics movements using:
- AIS (Automatic Identification System) vessel tracking (MarineTraffic, FleetMon, Spire)
- "Going dark" detection for sanctions-evading vessels
- Container tracking (container numbers, bill of lading references)
- Port call records and satellite imagery verification

### Phase 4: Network Analysis & Entity Resolution
Connect entities across datasets using:
- Graph database construction (Neo4j, NetworkX) with node types: companies, vessels, ports, individuals
- Entity resolution algorithms (Fellegi-Sunter, neural ER) to link entities across disparate records
- Address matching, director cross-referencing, phone number correlation
- Data breach/leak correlation for obscured relationships

### Phase 5: Sanctions Evasion Pattern Detection
Identify evasion techniques flagged in FATF and OFAC advisories:
- Ship-to-ship transfers in open water
- AIS manipulation (spoofing, gaps, false destinations)
- Shell company networks with layered ownership
- Trade-based money laundering (TBML) indicators
- Transshipment through third countries

## Key Data Sources & OSINT Tools

| Layer | Data Source | Tools & Platforms |
|-------|-------------|-------------------|
| Corporate | National registries, OpenCorporates, SEC EDGAR, beneficial ownership databases | OpenCorporates API, Bellingcat country registry toolkit, corporate registry search aggregators |
| Trade | Customs declarations, bills of lading, UN Comtrade | Panjiva, ImportGenius, Descartes Datamyne, TradeDataMonitor |
| Maritime | AIS data, port records, satellite imagery | MarineTraffic, VesselFinder, FleetMon, Spire AIS, exactEarth |
| Logistics | Container tracking, rail/air cargo manifests | Container xChange, Freightos, flight tracking (ADS-B Exchange, Flightradar24) |
| Sanctions | OFAC SDN, EU Consolidated List, UK Sanctions List, UN 1718 | OpenSanctions, Sayari Graph, Kharon, Castellum.AI |
| Entity Resolution | Cross-reference databases | Splink (probabilistic linkage), Neo4j Graph Data Science, Maltego, i2 Analyst's Notebook |
| Satellite | Optical/SAR imagery for facility verification | Sentinel Hub, Google Earth Engine, Planet Labs, Umbra SAR |
| Breach Data | Leaked databases for hidden connections | Dehashed, HaveIBeenPwned, IntelX, SnusBase (within legal boundaries) |

## Techniques in Detail

### Corporate Registry Mapping
Supplier network mapping uses corporate registries, leaked databases, social graphs, and sanctions lists to construct an organizational map of a supply chain. Key technique: searching director overlaps across multiple entity registrations reveals hidden common control structures. OpenCorporates provides programmatic access to 200+ jurisdictions.

### Trade Data Analysis
Customs import/export declarations provide consignee/shipper names, HS codes, quantities, and values. By analyzing trade flows over time, analysts can identify supplier substitution patterns, detect anomalies suggesting sanctions evasion, and quantify dependence on specific suppliers or countries. Panjiva and ImportGenius aggregate bills of lading from global shipping manifests.

### Maritime AIS Tracking
The IEEE OSINT Framework for Maritime Surveillance (2025) demonstrates analysis of AIS data, port records, and satellite imagery to detect suspicious activities including AIS blackouts, sanction-evading ship-to-ship transfers, and falsified destinations. Vessels "going dark" (disabling AIS transmissions) is a standard OPSEC measure for sanctions evasion; correlating AIS gaps with satellite imagery or port call records reveals hidden port calls.

### Sanctions Evasion Detection
OSINT Field Notes #5 (Feb 2026) documents real-time sanctions-evasion monitoring on a map, corporate registries, undercover procurement, and network mapping. Common evasion patterns include: establishing front companies in third countries, falsifying end-user certificates, routing goods through transshipment hubs, and using alternative payment channels (cryptocurrencies, hawala). Entity resolution linking shell companies to ultimate beneficial owners requires cross-jurisdictional corporate registry analysis.

### Supply Chain Risk Mapping
Supply chain leaders use OSINT to map risk across borders by monitoring geopolitical developments, regulatory changes, labor disputes, natural disasters, and supplier financial health — all from open sources. The Supply Chain Strategy article (March 2026) emphasizes the targeted collection and analysis of publicly available or licensable data to produce actionable intelligence for supply chain resilience.

## Entity Resolution Challenges in Supply Chains

Supply chain entity resolution must handle:
- **Multilingual name variants:** The same company appearing under different legal names in different jurisdictions
- **Shell company layering:** Deliberate obscuration through nested ownership
- **Temporal resolution:** Entity relationships change over time (acquisitions, restructurings)
- **Multi-modal linkage:** Connecting a corporate entity to a vessel to a trade transaction to a sanctioned individual

Techniques drawn from financial intelligence entity resolution (Fellegi-Sunter, Splink) and active learning for entity resolution are directly applicable.

## Cross-Domain Connections

- **[[maritime-logistics-gray-zone]]** — AIS manipulation and shadow fleets are core OSINT signals for supply chain mapping; the Iran shadow fleet architecture analysis directly applies to supply chain evasion detection
- **[[financial-intelligence-entity-resolution]]** — FINCEN SAR/CTR data and Splink ER methodology integrate with trade finance and beneficial ownership analysis for supply chain investigations
- **[[data-breach-analysis-osint]]** — Breach databases provide alternative vectors for identifying hidden supplier relationships and UBOs
- **[[satellite-imagery-osint]]** — Facility monitoring, port activity analysis, and change detection complement maritime and trade data
- **[[dns-whois-investigation-osint]]** — Corporate domain registration analysis reveals infrastructure links between shell companies
- **[[reverse-image-search-osint]]** — Verifying product authenticity and tracing manufacturing origins through imagery
- **[[alternative-data-sources-financial-intelligence]]** — Trade/customs data and TBML detection directly overlap with supply chain network reconstruction
- **[[rare-earth-supply-chains]]** — The rare earth supply chain analysis provides a case study of OSINT supply chain reconstruction
- **[[defense-procurement-cycles]]** — Industrial base single-point-of-failure analysis uses identical supply chain mapping techniques
- **[[private-credit-systemic-risk]]** — Supply chain concentration risk is a key input to private credit portfolio stress testing
- **[[energy-commodity-dynamics]]** — Energy commodity supply chains (crude, LNG, refined products) are mapped using OSINT trade flow analysis

## References

1. EBU Financial OSINT Guide: Tracing Corporate Assets & Networks — supply chain route analysis for sanctions evasion networks
2. Neotas — Supply Chain Transparency Using OSINT (July 2025): supplier network mapping, corporate registries, leaked databases, social graphs
3. Supply Chain Strategy — "How OSINT Helps Supply Chain Leaders Map Risk Across Borders" (March 2026)
4. IEEE — An Open-Source Intelligence (OSINT) Framework for Maritime Surveillance (2025): AIS data, port records, satellite imagery for anomaly detection
5. OSINT Field Notes #5 — "Sanctions-Evasion Monitoring on a Map" (February 2026): corporate registries, undercover procurement, network mapping
6. Atlas Bear GitHub — Maritime and Supply Chain OSINT Tools: curated ship tracking, container tracking, geolocation, risk management tools
7. Bellingcat Online Investigation Toolkit — curated interactive map of country-specific OSINT resources including business registries (June 2026)
8. FATF-Egmont — Trade-Based Money Laundering: Trends and Developments (2020): TBML techniques and red flag indicators
9. Fellegi-Sunter — A Theory for Record Linkage (1969): foundational probabilistic entity resolution framework applied to cross-database supply chain linkage
10. Venntel — "OSINT Data Sources: A 2026 Guide for Intelligence Analysts": "going dark" AIS as standard sanctions evasion OPSEC
