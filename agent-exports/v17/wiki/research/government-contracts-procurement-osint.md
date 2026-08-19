# Government Contracts & Procurement OSINT

**Status:** STABLE
**Created:** 2026-07-08
**Deepened:** 2026-07-08
**Domain:** OSINT → Financial Intelligence → Entity Resolution
**Lines:** ~310

## Overview

Government procurement data represents one of the world's largest and most detailed public datasets on corporate activity — the US federal government alone obligates ~$700B per year in contracts, each with transaction-level records including vendor identity, award value, period of performance, NAICS code, PSC code, competition type, and modification history. For OSINT investigators, this dataset enables corporate relationship mapping, beneficial ownership linkage, industrial base analysis, fraud detection, and competitive intelligence at a scale unmatched by any private commercial registry.

The key shift for 2026: the Federal Procurement Data System (FPDS.gov) was permanently decommissioned on February 24, 2026, along with the Electronic Subcontracting Reporting System (eSRS.gov) on February 20, 2026. All contract award data, subcontracting reports, and procurement records now reside exclusively on SAM.gov. The legacy ATOM data feed is scheduled to sunset later in FY2026, replaced by the new SAM.gov Contract Awards API. Public access to detailed contract award data now requires an authenticated SAM.gov login — a major change from the old FPDS ezSearch tool, which permitted anonymous searching.

## Data Infrastructure

### Primary US Federal Sources

| Source | Description | Access Method | Historical Coverage |
|--------|-------------|---------------|---------------------|
| **USAspending.gov** | Transaction-level federal award data — contracts, grants, loans, direct payments | Bulk CSV download, public API (filtering/aggregation/pagination) | FY2001–present (contracts) |
| **SAM.gov — Contract Data** | Post-Feb 2026: sole repository for all historical FPDS contract awards + subcontracting reports (eSRS) | Authenticated web search, SAM.gov Contract Awards API (replacing ATOM feed) | All historical FPDS records |
| **SAM.gov — Entity Information** | Legal business name, UEI, CAGE codes, NAICS, set-aside certifications, registration status | Entity API (1,000 requests/day free tier), bulk extract | Current registrations |
| **SAM.gov — Exclusions** | Debarred/suspended entities (FAR Subpart 9.4) | Exclusions API (free) | Current exclusions |
| **SBA Size Standards** | Industry-specific revenue/employee thresholds for small business classification | SBA Size Standards API | Current FY standards |
| **FPDS Legacy** | Pre-2026 contract award records (now on SAM.gov) | Redirected to SAM.gov; ezSearch and public FPDS dashboards permanently offline | FY2001–FY2025 |

### Key International Sources

| Source | Jurisdiction | Description |
|--------|-------------|-------------|
| **TED (Tenders Electronic Daily)** | EU | Public procurement notices ~$2T annual market, 15% EU GDP; FOPPA open database covers French award notices 2010–2020 |
| **Contracts Finder** | UK | Public-sector contracts >£10K; Crown Commercial Service |
| **AusTender** | Australia | Federal procurement data with contract details, supplier data |
| **Buyandsell.gc.ca** | Canada | Federal procurement and contracting data |
| **UNGM (UN Global Marketplace)** | UN System | ~$20B annual UN procurement notices |
| **MERX** | Canada private | ~$100B+ in public-private tenders |

### Post-2026 Changes (Critical OSINT Impact)

1. **Authenticated access required**: SAM.gov login is now required for all detailed contract award searches — anonymous search via ezSearch is permanently dead. OSINT investigators must register for a SAM.gov account (free, but traceable).
2. **ATOM feed sunset**: The legacy FPDS ATOM data feed (which powered many OSINT pipelines) is being replaced by a new SAM.gov Contract Awards API — pipeline migrations required.
3. **CPARS migration pending**: The Contractor Performance Assessment Reporting System (contractor past performance evaluations) is slated to migrate into SAM.gov later in FY2026 — will add a new qualitative layer to procurement OSINT.
4. **UEI replaces DUNS**: Since April 4, 2022, federal contractors are identified by the 12-character Unique Entity ID (UEI) rather than the Dun & Bradstreet 9-digit DUNS number. Cross-walking between legacy DUNS and current UEI is available via the FFATA-derived crosswalk (GovCon API, ~24,000 contractors indexed). CAGE codes remain in use as a 5-character alphanumeric identifier.

## Entity Resolution via Procurement Data

### UEI/DUNS/CAGE Cross-Walking

The transition from DUNS to UEI created a fragmentation challenge for entity resolution. Key crosswalk methods:
- **GovCon API free lookup**: Paste 9-digit DUNS → returns 12-character UEI + entity name from FFATA-derived crosswalk of ~24,000 federal contractors
- **SAM.gov Entity API**: With a UEI, retrieve full entity registration including legal name, NAICS codes, certifications, CAGE codes, physical address, and registration status
- **Exclusions API cross-check**: Free UEI screening against the federal debarment/suspension list
- **CAGE code triangulation**: 5-character CAGE codes provide an additional pivot point for entity identity confirmation

### Corporate Ownership Linkage

Procurement data supports corporate relationship mapping through:
- **Sub-award data**: Reveals prime-subcontractor relationships — tracking which firms subcontract to which entities and at what dollar concentration. A single subcontractor receiving >50% of prime award value is a pass-through indicator.
- **Joint venture tracking**: SAM.gov registration reflects JV entities; cross-reference with award data to identify teaming patterns
- **NAICS-based competitor mapping**: Firms receiving awards in the same NAICS codes form a de facto competitive set — analyze award volume, geographic footprint, and agency relationships
- **Parent-subsidiary resolution**: Dun & Bradstreet ownership data (commercial) can be cross-referenced with SAM.gov entity data for corporate family tree reconstruction

### Temporal Entity Resolution

Organizations change identity (name changes, M&A, entity restructuring). Procurement data provides a temporal trail:
- SAM.gov modification records show name changes and entity restructurings
- USASpending recipient profiles aggregate awards under both legacy and current identifiers
- CAGE code history reflects corporate evolution over decades

## Fraud Detection & Anomaly Analysis

### Detection Function Typology

Based on the RonanWrites US Federal Procurement Anomaly Detection pipeline (14 production runs on FY2024 USASpending data, 38,821 vendors scored, 542,094 sole-source rows processed):

| Detection Function | Signal Pattern | FAR References | OSINT Relevance |
|-------------------|----------------|----------------|-----------------|
| **Cumulative Award Concentration** | Same vendor, same NAICS, cumulative awards above simplified acquisition thresholds ($250K/$750K), minimal competition | FAR 6.301 (sole-source justification), FAR 13.003(c)(2) (prohibition on splitting) | Identify vendors with captured agency relationships — map to ownership, political contributions, lobbying disclosures |
| **Pass-Through Subcontracting** | Single subcontractor receives >50% of prime award value on set-aside contract; $1M signal floor; pricing >1.5x competitive P90 benchmark | FAR 52.219-14 (Limitations on Subcontracting) | Identify shell/front companies passing set-aside work to ineligible large businesses |
| **Price Benchmark Outlier** | Vendor pricing consistently 3-6x NAICS P90 competitive benchmark | FAR 15.404-1 (price reasonableness) | Surface overbilling patterns for investigative targeting; cross-reference with DOJ settlement databases |
| **Certification Fraud Screen** | SAM.gov small business certifications vs. SBA size standards by NAICS — revenue/employee counts from public filings exceed thresholds | 13 CFR 121 (size standards), FAR 19.301 | Identify fraudulent certification claims using OSINT corporate data |

### Academic Research on Procurement Fraud Detection

- **Automatic Procurement Fraud Detection with ML** (arXiv:2304.10105): SF Express database study; ML classifiers on procurement transaction attributes; limitation: strong reliance on whistleblower reporting for training labels
- **Pattern Mining for Anomaly Detection in Graphs** (arXiv:2306.10857): Graph-based red flag detection resilient to missing contract attributes — critical for jurisdictions with incomplete data
- **Structural Asymmetry as Fraud Signature** (arXiv:2511.10957): Heron's Information Coefficient (HIC) — geometric measure quantifying subgraph deviation from global network structure; applied to Brazilian Unified Health System (SUS) procurement
- **Learning from Sanctioned Government Suppliers** (arXiv:2512.19491): ML + network science for Mexican federal procurement; combines contract-level features with network topology for corruption risk indicators
- **FOPPA Database** (arXiv:2305.18317): Open database of French public procurement award notices 2010–2020 — 15% of EU GDP; critical for comparative European procurement OSINT

### Legal Constraints (US FCA Context)

**Baylor v. United States** (5th Cir., cert. denied 2021): Statistical analysis of public government data alone does NOT satisfy the False Claims Act "original source" / "materially adds" standard required for qui tam relator standing. The practical implication for OSINT practitioners: public procurement data analysis is an investigative lead tool, not a direct filing vehicle. Law firms must develop independent original-source knowledge before filing.

### LLM-Narrated Validation Pipeline

Advanced procurement fraud detection now pairs automated signal detection with LLM validation:
- Each flagged finding passes through an agentic validation loop (Claude + Tavily: 15-25 web searches per finding)
- Validation covers: vendor ownership/certifications, DOJ/IG/GAO prior investigation history, pricing context from comparable contracts, subcontracting plan filings
- Output: structured intelligence card with vendor profile, detection rationale, FAR citations, pricing analysis, and FCA exposure assessment
- Critical architectural separation: detection function decides WHAT to flag; LLM decides HOW to explain it — conflating these roles produces either missed flags or unfounded narratives

## Competitive Intelligence via Procurement OSINT

### Recompete Opportunity Tracking

Contracts have finite periods of performance — tracking expiration dates reveals upcoming recompete solicitations months before they appear on SAM.gov. A contract expiring in 18 months typically means the agency begins the acquisition process within 6-12 months. USAspending modification history reveals exercise of option years, funding expansions, and scope changes.

### Agency Spending Trend Analysis

- **Year-over-year comparison**: Compare agency spending in specific NAICS codes by fiscal year to identify growing/declining markets
- **Q4 surge pattern**: ~33% of annual obligations occur in Q4 (July-September) as agencies push awards before the September 30 fiscal year-end appropriation expiration
- **Agency NAICS heatmapping**: Map which agencies spend in which NAICS codes, year-over-year, to identify underserved niches with thinner competition

### IDIQ Obligation Tracking

For Indefinite Delivery/Indefinite Quantity (IDIQ) contracts, the parent IDV sets the ceiling, while individual task orders show actual utilization. Competitor analysis on an IDIQ requires task order history review to understand actual utilization rather than just the ceiling value. Tracking task order flow reveals which IDIQ holders are actually "in the money" vs. "shelf contracts."

### Teaming Relationship Mapping

Sub-award data reveals teaming patterns: which primes subcontract to which subs, at what dollar levels, and in which geographic areas. For competitive intelligence, this shows which primes have demonstrated relationships with small businesses in specific markets.

## Tool Ecosystem

| Tool | Type | Capability | Access Model |
|------|------|-----------|-------------|
| **USAspending.gov** | Government portal | Transaction-level award search, recipient profiles, bulk CSV/API | Free, public; API key recommended |
| **SAM.gov Contract Data** | Government portal | Post-2026 consolidated contract awards, subcontracting reports | Free, authenticated login required |
| **SAM.gov Entity API** | REST API | Full entity registration, certifications, exclusions screening | 1,000 req/day free tier |
| **GovCon API** | Commercial API | DUNS-to-UEI crosswalk, vendor risk screening, recompete watchlist, buyer intel | Paid tiers; free UEI/DUNS crosswalk |
| **USASpending Bulk Download** | Data export | Full award archive FY2001–present in CSV/Parquet | Free download; DuckDB/Parquet for large-scale processing |
| **AppointmentPlus** | Commercial | SAM.gov opportunity search, past performance, teaming | Paid subscription |
| **HigherGov** | Commercial | Procurement analytics, award forecasting, competitor tracking | Paid subscription |
| **Deltek GovWin IQ** | Commercial | Comprehensive government market intelligence, budget analysis | Enterprise paid |
| **Bloomberg Government** | Commercial | Policy + procurement data, legislative tracking, spending analysis | Enterprise paid |

## Methodology for OSINT Investigation

### Phase 1: Entity Identification
1. **UEI Lookup**: Search SAM.gov for known UEI or legal name → retrieve full entity registration, NAICS, certifications
2. **DUNS Crosswalk** (if only legacy DUNS available): Use GovCon API free lookup → UEI → full SAM record
3. **CAGE Code Triangulation**: If entity has CAGE code, cross-reference across contract awards to confirm identity

### Phase 2: Award History Reconstruction
1. **USAspending Recipient Profile**: Total awards by category, top awarding agencies, individual award list
2. **Award Detail Pages**: Base and exercised options, funding agency, place of performance, NAICS/PSC codes, competition type, set-aside status
3. **Modification Trail**: Track how each award grew — initial value vs. total obligations reveals true scope

### Phase 3: Network Mapping
1. **Sub-award Analysis**: Prime-sub relationships, subcontractor concentration
2. **Agency-Vendor Graph**: Which agencies spend on which vendors in which NAICS — identify dominant relationships
3. **Co-bidding/Teaming Detection**: JV partners, teaming arrangements, shared subcontractors

### Phase 4: Anomaly Flagging
1. **Concentration Analysis**: Cumulative awards same vendor-NAICS-agency above FAR thresholds
2. **Pricing Analysis**: Vendor pricing vs. NAICS P90 competitive benchmark
3. **Certification Verification**: SAM certifications vs. SBA size standards vs. public filings

## Cross-Domain Connections

| Wiki Page | Connection |
|-----------|------------|
| [[data-breach-analysis-osint]] | Breach data (email domains, credentials) can link individuals to procurement entities — a company email domain from a breach dataset maps to SAM.gov registration contact data |
| [[dns-whois-investigation-osint]] | Domain WHOIS registration dates and email addresses tied to procurement entity identities for corporate lineage reconstruction |
| [[entity-resolution-agent-safety]] | Same entity resolution techniques (Fellegi-Sunter, temporal consistency, network community detection) apply to both procurement identity linkage and agent tool safety |
| [[sanctions-evasion-detection]] | Procurement data is a primary detection layer for sanctions evasion — shell procurement entities, false certifications, and pass-through subcontracting mirror evasion network architectures |
| [[supply-chain-network-analysis-osint]] | Procurement data provides the ground-truth edges for supply chain network graphs — contract award data defines who supplies what to whom at what value |
| [[alternative-data-sources-financial-intelligence]] | Procurement data as FININT alternative data: trade-based money laundering detection, adversarial data quality calibration |
| [[data-lineage-provenance-entity-resolution]] | Procurement award modification trails as temporal provenance chains — analogous to W3C PROV-O influenced chains for entity identity over time |
| [[defense-procurement-cycles]] | Defense procurement specific methodology: PPBE reform, Nunn-McCurdy analysis, industrial base single-point-of-failure, contractor financial health |
| [[osint-legal-ethical-boundaries]] | Baylor v. United States FCA constraints, EU AI Act data scraping provisions, GDPR Article 6/9/17 for EU procurement data |
| [[network-analysis-techniques-osint]] | Graph-based anomaly detection in procurement networks: centrality measures for vendor influence, community detection for teaming clusters, link prediction for emerging relationships |
| [[counterintelligence-analysis-frameworks]] | CI-ACH methodology applied to procurement anomaly adjudication — competing hypotheses for flagged patterns (legitimate vs. fraudulent) |
| [[humint-tradecraft-osint]] | Admiralty Code source reliability scoring adapted to procurement data quality assessment (A-F reliability mapped to data source completeness/timeliness) |

## References

1. RonanWrites (2026). "US Federal Procurement Anomaly Detection — Case Study." ronanwrites.com. 14 production runs, FY2024 USASpending data, 38,821 vendors scored.
2. Bureauify (2026). "Understanding USAspending.gov Data — Federal Spending Intelligence." bureauify.com/guide/usaspending.
3. Ellsworth Solutions (Feb 2026). "FPDS is Gone — Here's How to Find Your Federal Contract Awards on SAM.gov." ellsworth.solutions. Detailed FPDS/SAM.gov migration guide.
4. Gorm Group (Feb 2026). "FPDS Contract Data Search Moves to SAM.gov February 24, 2026." gormgroup.com. GSA modernization transition documentation.
5. GovCon API (2026). "Free DUNS to UEI Lookup & SAM Identifier Crosswalk." govconapi.com. FFATA-derived crosswalk of ~24,000 federal contractors.
6. GAO-25-107469 (2025). "Federal Spending Transparency: Actions Needed to Help Ensure Quality Procurement Data." gao.gov.
7. arXiv:2304.10105 — Automatic Procurement Fraud Detection with Machine Learning (SF Express, 2023)
8. arXiv:2306.10857 — Pattern Mining for Anomaly Detection in Graphs: Application to Fraud in Public Procurement (2023)
9. arXiv:2511.10957 — Structural Asymmetry as a Fraud Signature: Detecting Collusion with Heron's Information Coefficient (2025)
10. arXiv:2512.19491 — Learning from Sanctioned Government Suppliers: ML + Network Science for Mexican Procurement Fraud Detection (2025)
11. arXiv:2305.18317 — FOPPA: An Open Database of French Public Procurement Award Notices 2010–2020 (2023)
12. Baylor v. United States, 5th Cir., cert. denied 2021 — FCA original-source requirement; public data statistical analysis insufficient for qui tam standing
13. GSA Open Technology. "SAM.gov Get Opportunities Public API." open.gsa.gov.
