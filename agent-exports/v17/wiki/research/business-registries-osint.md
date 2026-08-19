# Business Registries OSINT: Corporate Registry Investigation & Entity Resolution

**Status:** STABLE
**Created:** 2026-07-10
**Deepened:** 2026-07-10
**Parent Interest:** Data Aggregation & Entity Resolution

## Overview

Business registries — government-maintained databases of company incorporations, filings, directors, and beneficial owners — are a foundational OSINT source for entity resolution. Every jurisdiction maintains at least one registry, but formats, accessibility, and data quality vary widely.

## Registry Types & Access Models

- **Centralized national registries:** e.g., Companies House (UK), SEC EDGAR (US), SEDAR+ (Canada)
- **Distributed/state-level:** e.g., US Secretaries of State (50+ jurisdictions)
- **International aggregators:** OpenCorporates, OpenOwnership, Dun & Bradstreet

## Key Data Fields for Entity Resolution

- Company name (legal and trading-as)
- Registration number / jurisdiction-specific identifier
- Registered address / principal place of business
- Directors and officers (names, dates of appointment, other directorships)
- Shareholders / beneficial owners (where disclosed)
- Filing history (annual returns, changes in control, financial statements)
- Dissolution/restoration dates

## OSINT Investigation Workflow

1. **Initial entity identification:** Name, jurisdiction hints, industry sector
2. **Registry search:** Primary national registry, then aggregator cross-check
3. **Network expansion:** Officer/director cross-walk to other entities
4. **Address triangulation:** Registered address matches across entities
5. **Beneficial ownership tracing:** Combine registry filings with leaked data (e.g., Panama Papers, Pandora Papers)

## Challenges

- Inconsistent naming conventions across jurisdictions (accents, transliterations, abbreviations)
- Shell company layers and nominee directors obscuring true beneficial ownership
- Paywalled/restricted access registries (e.g., some offshore jurisdictions)
- Data lags between filing and public availability

## Tool Ecosystem

| Tool | Type | Coverage | API | Notes |
|------|------|----------|-----|-------|
| OpenCorporates | Aggregator | 140+ registries worldwide | REST API (v0.4.8), OpenRefine reconciliation | Largest open legal-entity database; share-alike attribution or commercial licensing |
| OpenOwnership | Beneficial Ownership | Global BO registry aggregation | REST API, BODS data standard | Links company records to beneficial owners; Beneficial Ownership Data Standard (BODS) |
| Companies House (UK) | National Registry | United Kingdom | REST API, free | PSC (Persons of Significant Control) register; one of the most transparent registries globally |
| SEC EDGAR | National Registry | US public companies | REST API (xbrl), bulk FTP | 10-K, 10-Q, 8-K filings; SIC codes, subsidiary lists, executive compensation |
| SEDAR+ | National Registry | Canada | Web API | Canadian public company filings; successor to SEDAR, launched 2023 |
| OpenRefine + OpenCorporates Reconciliation | Entity Resolution | 140+ registries | OpenRefine plugin | Match company names to legal entities via reconciliation API |
| Dun & Bradstreet | Commercial | Global | Proprietary API | DUNS numbers; paid access; widely used for government contracting entity resolution |

## Beneficial Ownership Registries

Beneficial ownership transparency is the critical frontier for entity resolution. Key developments:

- **FinCEN BOI Registry (US):** Corporate Transparency Act (CTA) effective 2024; requires reporting companies to disclose beneficial owners (25%+ ownership or substantial control) to FinCEN. Access restricted to law enforcement and financial institutions with customer consent — not publicly searchable.
- **UK PSC Register:** Companies House Persons of Significant Control register; publicly searchable, free. 25%+ ownership or control threshold. Most transparent major-economy BO registry.
- **EU AMLD5/AMLD6:** Member states required to establish public BO registries; implementation varies. Luxembourg, Netherlands, and Denmark have robust public registries; others lag.
- **Offshore jurisdictions:** British Virgin Islands, Cayman Islands, Panama maintain private registries with limited access. ICIJ Offshore Leaks database (Panama Papers, Pandora Papers, Paradise Papers) provides alternative BO tracing for these jurisdictions.
- **OpenOwnership:** Aggregates BO data globally using BODS (Beneficial Ownership Data Standard); links corporate entities to ultimate beneficial owners across jurisdictions.

## Investigation Methodology

### Phase 1: Entity Identification
- Start with known identifiers: company name, jurisdiction, registration number
- Use OpenCorporates to verify legal name, status (active/dissolved), registered address
- Cross-check with national registry for filing history and director/officer data

### Phase 2: Network Expansion
- Extract all officers and directors from registry filings
- Cross-walk each person to other entities through officer search
- Map registered addresses; flag addresses shared across multiple entities as shell company indicators

### Phase 3: Beneficial Ownership Tracing
- For UK entities: search PSC register directly
- For US entities: CTA BOI not public; use state-level filings, SEC filings, and commercial databases
- For offshore: combine OpenCorporates with ICIJ Offshore Leaks data for BO hints
- Construct ownership chain: entity → intermediate holding company → natural person

### Phase 4: Cross-Dataset Resolution
- Link registry entities to FININT data (SAR/CTR filings, SWIFT data) via FinCEN Query system
- Cross-walk to government contracts (USAspending.gov, SAM.gov) for entity verification
- Match to sanctions lists (OFAC SDN, EU, UN) for compliance screening
- Integrate with lobbying disclosure databases (LDA, FARA) for influence mapping

### Phase 5: Visualization & Reporting
- Construct entity-relationship diagrams (Gephi, Cytoscape, Maltego)
- Map geographic footprint: registered addresses, branch offices, subsidiary locations
- Timeline visualization: incorporation dates, director changes, filing anomalies
- Flag anomalies: circular ownership, nominee director patterns, shelf company indicators

## Cross-Domain Connections

- [[entity-resolution-agent-safety]] — Entity binding failures when registry data is stale
- [[financial-intelligence-entity-resolution]] — FININT overlays with registry data
- [[sanctions-evasion-detection]] — Shell company networks identified via registries
- [[lobbying-disclosure-osint]] — Lobbying registrants cross-walked to corporate registries
- [[government-contracts-procurement-osint]] — Contractor entity resolution

## References

*To be populated during deepening*

## Deepening Log

- 2026-07-10: Created DRAFT stub
