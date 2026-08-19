# Property Records OSINT: Real Estate as Open-Source Intelligence Vector

**Status: STABLE**
**Created: 2026-07-09 | Deepened: 2026-07-09**
**Topic:** Property records as OSINT data source for entity resolution, financial intelligence, and investigation
**Parent interest:** Data Aggregation & Entity Resolution

---

## Overview

Property records — deeds, tax assessments, liens, mortgages, property transfers — are a high-signal public data source for OSINT investigation and entity resolution. They tie individuals to physical locations, financial relationships, and corporate structures through paper trails publicly accessible in most U.S. jurisdictions. The gutting of the Corporate Transparency Act (CTA) for domestic entities in March 2025 made automated entity resolution more necessary: for domestic LLCs holding U.S. real estate, no centralized database provides the beneficial owner. You build the chain yourself.

Property records function as a canonical example of the broader public records OSINT pattern: heterogeneous, jurisdiction-specific data that requires automated chain-walking and entity resolution to yield actionable intelligence.

---

## 1. Types of Property Records

| Record Type | Contains | OSINT Utility |
|------------|----------|---------------|
| **Deeds** | Grantor/grantee, sale price (in disclosure states), legal description, recording date | Ownership transfer chain, financial relationships |
| **Tax Assessments** | Annual valuations, owner of record, property characteristics, mailing address | Owner verification, property portfolio aggregation |
| **Liens & Mortgages** | Financial encumbrances, lender identity, loan amounts, recording dates | Financial exposure, lender relationships, distress indicators |
| **Property Transfer Records** | Chain of title, historical transaction sequence | Long-term ownership patterns, shell company churn |
| **Plat Maps & Parcel Data** | GIS boundaries, zoning, land use classifications | Spatial analysis, parcel aggregation, land banking detection |

---

## 2. Jurisdictional Architecture

### 2.1 Fragmentation Challenge

Property records in the United States are maintained at the county level — 3,143 counties and county-equivalents — creating a massive cross-jurisdictional integration challenge. Each county recorder/assessor operates independently with:

- Variable digitization levels (fully digital to paper-only with in-person access)
- Inconsistent data formats and field names
- Different search interfaces (by owner name, parcel ID, address, or legal description)
- Varying public access policies (some counties restrict bulk downloads or require payment)

### 2.2 Regulatory Context: Post-CTA Landscape

| Date | Event | Impact on Entity Resolution |
|------|-------|-----------------------------|
| March 2025 | FinCEN exempts all U.S.-formed entities from CTA beneficial ownership reporting | No federal BO database for domestic LLCs |
| January 2026 | NY LLC Transparency Act (weakened) — foreign-formed LLCs only | Minimal coverage improvement |
| March 1, 2026 | FinCEN Residential Real Estate Rule (31 CFR § 1010.380) — settlement agents report all-cash residential entity/trust transfers | Covers residential only, non-financed only, reports not publicly searchable |

**Bottom line:** For domestic LLCs holding U.S. real estate, no database provides the beneficial owner. Entity resolution must be performed through chain-walking across heterogeneous registries.

---

## 3. Data Access Landscape

### 3.1 County-Level Access

County assessor/recorder offices are the primary source for U.S. real property ownership.

- **County Assessor databases:** parcel numbers, assessed values, tax history, property characteristics
- **County Recorder/Register of Deeds:** deeds, mortgages, liens, easements, plat maps
- **Access pattern:** Most counties have free online portals; some require in-person visits for historical records
- **Key tool:** NETROnline (publicrecords.netronline.com) provides county assessor/recorder links by state

### 3.2 Aggregators & Commercial Sources

| Source | Coverage | Access | Notes |
|--------|----------|--------|-------|
| **OpenCorporates** | 222+ jurisdictions, 220M+ companies | API (free tier: 500 calls/month) | Corporate registry aggregation; officers, filings, addresses |
| **Regrid** | Nationwide parcel data | Commercial API / bulk files | Standardized parcel boundaries with owner attributes |
| **ATTOM / CoreLogic** | Nationwide property data | Commercial (expensive) | Comprehensive but costly; used by institutional investors |
| **Zillow, Redfin, Realtor.com** | Consumer-facing | Free web | Limited historical depth |
| **OSINT-Tools_USA** (paulpogoda GitHub) | County assessor URL directory | Open source | Community-maintained county data portal links |
| **County GIS portals** | Per-county | Typically free web access | REST endpoints often available for programmatic access |

### 3.3 Corporate Ownership Transparency

- **FinCEN Residential Real Estate Rule** (effective March 1, 2026, 31 CFR § 1010.380): Requires reporting of certain non-financed residential real estate purchases.
- **Corporate Transparency Act** (gutted for domestic entities March 2025): No centralized beneficial owner database for domestic LLCs holding U.S. real estate.
- **New York LLC Transparency Act** (effective January 2026): State-level beneficial ownership reporting.
- **Lincoln Institute/CGS, "Who Owns America" (January 2026):** Mapped corporate ownership of residential land — 8.9% of residential parcels are corporate-owned.

---

## 4. Chain-Walking Methodology

### 4.1 The Property-to-Person Pipeline

**Phase 1: Property Identification**
1. Start with property address or parcel ID
2. Query county assessor database for owner of record
3. Result: LLC name or individual name

**Phase 2: Corporate Disambiguation**
1. Search state Secretary of State business registry for LLC entity
2. Obtain: registered agent, principal address, filing history
3. Note: registered agent ≠ beneficial owner

**Phase 3: Cross-Jurisdictional Tracing**
1. If LLC was formed in a different state (e.g., Delaware, Wyoming):
   - Query formation state registry for articles of organization
   - Check for foreign qualification in property state
   - Chain rule: "If the entity holding the property was formed out-of-state, you must query two registries."
2. Cross-reference registered agent address with other corporate filings (same agent = common ownership)

**Phase 4: Identity Linkage**
1. Search for additional properties owned by the same LLC or individual
2. Cross-reference names and addresses against:
   - Other property holdings (same LLC or affiliated addresses)
   - Federal court records (PACER)
   - Campaign finance disclosures (FEC)
   - Data breach databases (Dehashed, HIBP domain search for associated emails)
   - Social media / professional profiles
3. Recurse: follow property-to-owner-to-other-properties chains

### 4.2 Common Failure Modes

| Failure Mode | Description | Mitigation |
|-------------|-------------|------------|
| **Delaware Dead End** | FL LLC → DE LLC (no foreign registration) → ownership hidden | Search DE annual franchise tax filings; cross-reference registered agent as bridge identifier |
| **Trust Ownership** | Property held by a trust rather than individual or LLC | Trust deeds may name trustees; probate records for deceased settlors |
| **Nominee Officers** | Registered agent service listed as all officers | Look for pattern: same agent service across multiple entities → investigate agent\'s client list |
| **Name Variations** | "Smith Properties LLC" vs "Smith Properties, L.L.C." vs "Smith Properties Limited Liability Company" | Fuzzy matching with Damerau-Levenshtein; entity resolution normalization |


---

## 5. Entity Resolution Techniques

### 5.1 Integration with Fellegi-Sunter

Property records serve as one dimension in a multi-source entity resolution pipeline:

- **Blocking key:** County + ZIP code (reduces comparison space)
- **Comparison variables:** Owner name (Jaro-Winkler), property address (normalized), sale price (numeric proximity), recording date (temporal proximity)
- **Agreement weights:** Property co-ownership is a strong positive weight for entity linkage; same mailing address across LLC registrations is a medium weight; same registered agent is a weak-but-diagnostic weight
- **Disagreement weights:** Name mismatch with matching address is weak evidence against match; different counties with same owner name is neutral
- **Threshold tuning:** M-probability and U-probability estimated from ground-truth matches
- **Clerical review:** Edge cases flagged for manual verification

### 5.2 Address as Bridge Identifier

A physical address acts as the bridge between registration systems:
- Principal address on LLC filings → property owned at that address
- Mailing address on tax assessment → other LLCs using same mailing address
- Registered agent address → all entities sharing that agent

### 5.3 Name Normalization

| Challenge | Technique |
|-----------|-----------|
| Corporate name variants | Fuzzy matching (Damerau-Levenshtein, Jaccard on tokens) |
| Individual name variants | Phonetic encoding (Soundex, Metaphone); middle initial expansion |
| Trustee/nominee structures | Pattern detection: same trustee across multiple unrelated entities |
| Foreign character sets | Transliteration + original script matching |

### 5.4 Shell Company Detection

- **Nominee registration patterns:** Same registered agent across dozens of unrelated LLCs
- **Circular ownership:** LLC A owns property, LLC B owns LLC A, same individuals behind both
- **Foreign ownership layering:** Delaware/Wyoming/Nevada LLCs holding real estate with foreign beneficial owners
- **Address concentration:** Multiple LLCs using the same UPS Store mailbox as principal address
- **Transfer velocity:** Frequent LLC-to-LLC transfers without economic rationale → potential money laundering or asset shielding

---

## 6. Automated Data Collection

### 6.1 County Assessor Web Scraping

Most county assessor databases offer web-based property search. Automated collection requires:

- **Search by owner name:** Query all properties held by a given entity
- **Search by address:** Reverse lookup to identify owner
- **Parcel ID lookup:** Most reliable unique identifier within a county

**Challenges:** CAPTCHA protection, rate limiting, inconsistent HTML structures, session timeouts. See also: [[anti-bot-evasion-fingerprinting]] for evasion engineering patterns.

### 6.2 OSINTBay PERSINT Framework

Property deeds are one node in the PERSINT (Personal Intelligence) methodology — integrated with:
- Court dockets (civil, criminal, bankruptcy)
- Corporate registries (state SOS, SEC EDGAR)
- Voter registration records
- Marriage/divorce certificates
- Professional licensing databases

---

## 7. OSINT Applications

### 7.1 Beneficial Ownership Investigation

Tracing the true human owner behind LLC-held real estate, used in:
- Anti-money laundering (AML) investigations
- Sanctions evasion detection
- Political corruption and conflict-of-interest reporting
- Competitive intelligence on commercial real estate portfolios

### 7.2 Portfolio Aggregation

Identifying all properties controlled by a given individual or entity:
- Search by entity name across all counties in a state
- Cross-reference with associated names (spouses, business partners, known aliases)
- Aggregate into a property portfolio for net worth estimation or influence mapping

### 7.3 Financial Distress Indicators

- Mortgage recording volume spikes → refinancing wave
- Lis pendens (notice of pending lawsuit) filings → pre-foreclosure
- Tax lien certificates → property tax delinquency
- Frequent LLC-to-LLC transfers → potential money laundering or asset shielding
- $1.2T CRE refinancing wave makes ownership transparency financially material

---

## 8. Tool Inventory

| Tool | Category | Access | Key Capability |
|------|----------|--------|---------------|
| NETROnline | County Assessor Directory | Free web | Links to 3,143 county assessor/recorder portals |
| OpenCorporates API | Corporate Registry Aggregator | Freemium API | 222+ jurisdictions, officers, filings, addresses |
| OSINT-Tools_USA (GitHub) | County Data Portal Links | Open source | Community-maintained URL directory by state |
| Regrid | Nationwide Parcel Data | Commercial | Standardized parcel boundaries with owner attributes |
| County GIS Portals | Per-County Parcel Search | Free web | REST endpoints often available programmatically |
| PACER | Federal Court Records | Per-search fee | Civil/criminal case filings with party names and addresses |
| FEC Individual Contributions | Campaign Finance | Free, bulk downloads | Donor name, address, employer, recipient |
| Dehashed | Breach Data Search | Subscription | Email-to-name, phone-to-address correlation |

---

## 9. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[entity-resolution-algorithms]] | Property records are a canonical ER data source; Fellegi-Sunter weight assignment for co-ownership linkage |
| [[data-breach-analysis-osint]] | Cross-reference breached PII with property records for identity verification |
| [[cross-jurisdictional-entity-resolution]] | Property ownership across county lines requires cross-jurisdictional ER |
| [[sanctions-evasion-detection]] | Shell LLCs holding real estate is a primary sanctions evasion technique |
| [[anti-bot-evasion-fingerprinting]] | Automated county assessor scraping requires anti-detection engineering |
| [[supply-chain-network-analysis-osint]] | Industrial property ownership maps to supply chain node identification |
| [[network-analysis-techniques-osint]] | Property co-ownership graphs for association network mapping |
| [[public-records-databases-osint]] | Property records as a core public records data source |
| [[financial-intelligence-entity-resolution]] | Property records integrated with FININT ER pipeline (FinCEN SAR/CTR, SWIFT, Fellegi-Sunter with Splink) |
| [[counterintelligence-analysis-frameworks]] | Shell company analysis for property holdings applies CI techniques: threat actor (LLC owner) uses denial and deception (nominee structures) to conceal capabilities (asset ownership) |
| [[intelligence-failure-analysis]] | Venona Project cryptonym-to-identity pipeline is the historical precursor to automated property record chain-walking — resolving partial identifiers across fragmented data sources |
| [[multi-agent-orchestration-patterns]] | Automated chain-walking across heterogeneous registries is structurally isomorphic to tool-use delegation patterns — each registry is a "tool" with different capabilities |
| [[geopolitical-strategy]] | Foreign entities accumulating U.S. real estate through shell LLCs is a national security concern; CTA foreign-entity reporting signals this priority |
| [[market-microstructure-liquidity-dynamics]] | $1.2T CRE refinancing wave means property ownership transparency is financially material; distress indicators (lis pendens, tax liens) serve as leading signals |

---

## 10. References

1. OpenCorporates Blog, "Why Unmasking Corporate Property Ownership Is the Next Frontier for Commercial Real Estate Data," August 2025
2. Zephira.ai, "Who Really Owns That Property? How to Trace Real Estate LLC Ownership in 2026"
3. Lincoln Institute of Land Policy & Center for Geospatial Solutions, "Who Owns America: Mapping Corporate Ownership of Residential Land," January 2026
4. FinCEN Residential Real Estate Rule, 31 CFR § 1010.380, effective March 1, 2026
5. OpenCorporates API v0.4 documentation — entity search, officers, filings endpoints
6. OSINT-Tools_USA GitHub repository (paulpogoda) — county assessor database URLs by state
7. OSINTBay, "PERSINT Public Records: The OSINT Operator's Guide to Court, Corporate & Government Filings"
8. Fellegi, I.P. & Sunter, A.B. (1969). "A Theory for Record Linkage." Journal of the American Statistical Association, 64(328), 1183-1210.
9. Corporate Transparency Act, 31 U.S.C. § 5336 (as amended by FinCEN interim final rule, March 2025)
10. New York LLC Transparency Act (S.995-B / A.3484), effective January 2026
