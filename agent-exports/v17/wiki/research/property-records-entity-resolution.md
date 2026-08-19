# Property Records & Entity Resolution for OSINT

**Status: STABLE**
**Created: 2026-06-01 | Deepened: 2026-06-01**
**Interest domain: Data Aggregation & Entity Resolution**

## Summary

Property records — deeds, tax assessments, liens, mortgages, property transfers — are a high-signal public data source for entity resolution and OSINT investigation. They tie individuals to physical locations, financial relationships, and corporate structures through a paper trail publicly accessible in most jurisdictions. The gutting of the Corporate Transparency Act (CTA) for domestic entities in March 2025 made autonomous entity resolution more necessary, not less: for domestic LLCs holding U.S. real estate, no centralized database provides the beneficial owner. You build the chain yourself.

---

## 1. Property Records Architecture

### 1.1 Types of Property Records

| Record Type | Contains | OSINT Utility |
|------------|----------|---------------|
| **Deeds** | Grantor/grantee, sale price (in disclosure states), legal description, recording date | Ownership transfer chain, financial relationships |
| **Tax Assessments** | Annual valuations, owner of record, property characteristics, mailing address | Owner verification, property portfolio aggregation |
| **Liens & Mortgages** | Financial encumbrances, lender identity, loan amounts, recording dates | Financial exposure, lender relationships, distress indicators |
| **Property Transfer Records** | Chain of title, historical transaction sequence | Long-term ownership patterns, shell company churn |
| **Plat Maps & Parcel Data** | GIS boundaries, zoning, land use classifications | Spatial analysis, parcel aggregation, land banking detection |

### 1.2 Jurisdictional Fragmentation

Property records in the United States are maintained at the county level — 3,143 counties and county-equivalents — creating a massive cross-jurisdictional integration challenge. Each county recorder/assessor operates independently with:

- Variable digitization levels (fully digital → paper-only with in-person access)
- Inconsistent data formats and field names
- Different search interfaces (by owner name, parcel ID, address, or legal description)
- Varying public access policies (some counties restrict bulk downloads or require payment)

### 1.3 Regulatory Context: Post-CTA Landscape

**Key timeline events:**

| Date | Event | Impact on Entity Resolution |
|------|-------|---------------------------|
| March 2025 | FinCEN exempts all U.S.-formed entities from CTA beneficial ownership reporting | No federal BO database for domestic LLCs |
| Jan 2026 | NY LLC Transparency Act (weakened) — foreign-formed LLCs only | Minimal coverage improvement |
| March 1, 2026 | FinCEN Residential Real Estate Rule — settlement agents report all-cash residential entity/trust transfers | Covers residential only, non-financed only, reports not publicly searchable |

**Bottom line:** For domestic LLCs holding U.S. real estate, no database provides the beneficial owner. Entity resolution must be performed through chain-walking across heterogeneous registries.

---

## 2. Chain-Walking Methodology

### 2.1 The Property-to-Person Pipeline

Synthesized from Zephira.ai (2026) and OpenCorporates analysis, the pipeline has four phases:

**Phase 1: Property Identification**
- Start with address or parcel ID
- Query county assessor database for owner of record
- Result: LLC name or individual

**Phase 2: Corporate Disambiguation**
- Search state Secretary of State business registry for LLC entity
- Obtain: registered agent, principal address, filing history
- Note: registered agent ≠ beneficial owner

**Phase 3: Cross-Jurisdictional Tracing**
- If LLC was formed in a different state (e.g., Delaware, Wyoming):
  - Query formation state registry for articles of organization
  - Check for foreign qualification in property state
  - Chain rule: "If the entity holding the property was formed out-of-state, you must query two registries."

**Phase 4: Identity Linkage**
- Cross-reference names and addresses against:
  - Other property holdings (same LLC or affiliated addresses)
  - Federal court records (PACER)
  - Campaign finance disclosures (FEC)
  - Data breach databases (Dehashed, HIBP domain search for associated emails)
  - Social media / professional profiles

### 2.2 Common Failure Modes

| Failure Mode | Description | Mitigation |
|-------------|-------------|------------|
| **Delaware Dead End** | FL LLC → DE LLC (no foreign registration) → ownership hidden | Search DE annual franchise tax filings; cross-reference registered agent as bridge identifier |
| **Trust Ownership** | Property held by a trust rather than individual or LLC | Trust deeds may name trustees; probate records for deceased settlors |
| **Nominee Officers** | Registered agent service listed as all officers | Look for pattern: same agent service across multiple entities → investigate agent's client list |
| **Name Variations** | "Smith Properties LLC" vs "Smith Properties, L.L.C." vs "Smith Properties Limited Liability Company" | Fuzzy matching with Damerau-Levenshtein; entity resolution normalization |

---

## 3. Automated Data Collection

### 3.1 County Assessor Web Scraping

Most county assessor databases offer web-based property search. Automated collection requires:

- **Search by owner name**: Query all properties held by a given entity
- **Search by address**: Reverse lookup to identify owner
- **Parcel ID lookup**: Most reliable unique identifier within a county

Challenges: CAPTCHA protection, rate limiting, inconsistent HTML structures, session timeouts.

### 3.2 Open Data Sources

| Source | Coverage | Access | Notes |
|--------|----------|--------|-------|
| **OpenCorporates** | 222+ jurisdictions, 220M+ companies | API (free tier: 500 calls/month) | Corporate registry aggregation; officers, filings, addresses |
| **Regrid** | Nationwide parcel data | Commercial API / bulk files | Standardized parcel boundaries with owner attributes |
| **ATTOM / CoreLogic** | Nationwide property data | Commercial (expensive) | Comprehensive but costly; used by institutional investors |
| **OSINT-Tools_USA** (paulpogoda GitHub) | County assessor URL directory | Open source | Community-maintained county data portal links |
| **County GIS portals** | Per-county | Typically free web access | REST endpoints often available for programmatic access |

### 3.3 OSINTBay PERSINT Framework

Property deeds are one node in the PERSINT (Personal Intelligence) methodology — integrated with:
- Court dockets (civil, criminal, bankruptcy)
- Corporate registries (state SOS, SEC EDGAR)
- Voter registration records
- Marriage/divorce certificates
- Professional licensing databases

---

## 4. OSINT Applications

### 4.1 Beneficial Ownership Investigation

Tracing the true human owner behind LLC-held real estate, used in:
- Anti-money laundering (AML) investigations
- Sanctions evasion detection
- Political corruption and conflict-of-interest reporting
- Competitive intelligence on commercial real estate portfolios

### 4.2 Portfolio Aggregation

Identifying all properties controlled by a given individual or entity:
- Search by entity name across all counties in a state
- Cross-reference with associated names (spouses, business partners, known aliases)
- Aggregate into a property portfolio for net worth estimation or influence mapping

### 4.3 Financial Distress Indicators

- Mortgage recording volume spikes → refinancing wave
- Lis pendens (notice of pending lawsuit) filings → pre-foreclosure
- Tax lien certificates → property tax delinquency
- Frequent LLC-to-LLC transfers → potential money laundering or asset shielding

---

## 5. Entity Resolution Techniques Specific to Real Estate

### 5.1 Address as Bridge Identifier

A physical address acts as the bridge between registration systems:
- Principal address on LLC filings → property owned at that address
- Mailing address on tax assessment → other LLCs using same mailing address
- Registered agent address → all entities sharing that agent

### 5.2 Name Normalization

| Challenge | Technique |
|-----------|-----------|
| Corporate name variants | Fuzzy matching (Damerau-Levenshtein, Jaccard on tokens) |
| Individual name variants | Phonetic encoding (Soundex, Metaphone); middle initial expansion |
| Trustee/nominee structures | Look for pattern: same trustee across multiple unrelated entities |
| Foreign character sets | Transliteration + original script matching |

### 5.3 Probabilistic Record Linkage

Applying Fellegi-Sunter methodology to property records:
- **Blocking key**: County + ZIP code (reduces comparison space)
- **Comparison variables**: Owner name (Jaro-Winkler), property address (normalized), sale price (numeric proximity), recording date (temporal proximity)
- **Threshold tuning**: M-probability and U-probability estimated from ground-truth matches
- **Clerical review**: Edge cases flagged for manual verification

---

## 6. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **OSINT Investigation Methodology** | Property records are a canonical public records OSINT source; chain-walking methodology maps to broader investigation patterns |
| **Markets & Financial Analysis** | $1.2T CRE refinancing wave makes ownership transparency financially material; corporate ownership of residential parcels (8.9%) has housing affordability implications |
| **Geopolitics & Strategic Analysis** | Foreign entities accumulating U.S. real estate through shell LLCs is a national security concern; CTA foreign-entity reporting signals this priority |
| **Privacy & Cryptography** | CTA rollback = privacy policy choice (anonymous LLCs) vs UK PSC register = transparency choice — privacy-vs-transparency tension |
| **AI Agent Architecture** | Automated chain-walking across heterogeneous registries is structurally isomorphic to tool-use delegation patterns — each registry is a "tool" with different capabilities |
| **History of Intelligence Operations** | Venona Project cryptonym-to-identity pipeline is the historical precursor to automated property record chain-walking — resolving partial identifiers across fragmented data sources |
| **Counterintelligence Analysis Frameworks** | Shell company analysis for property holdings applies CI techniques: threat actor (LLC owner) uses denial and deception (nominee structures) to conceal capabilities (asset ownership) |

---

## 7. References

1. OpenCorporates Blog, "Why Unmasking Corporate Property Ownership Is the Next Frontier for Commercial Real Estate Data," August 2025
2. Zephira.ai, "Who Really Owns That Property? How to Trace Real Estate LLC Ownership in 2026"
3. Lincoln Institute of Land Policy & Center for Geospatial Solutions, "Who Owns America: Mapping Corporate Ownership of Residential Land," January 2026
4. FinCEN Residential Real Estate Rule, effective March 1, 2026 (31 CFR § 1010.380)
5. OpenCorporates API v0.4 documentation — entity search, officers, filings endpoints
6. OSINT-Tools_USA GitHub repository (paulpogoda) — county assessor database URLs by state
7. OSINTBay, "PERSINT Public Records: The OSINT Operator's Guide to Court, Corporate & Government Filings"
8. Fellegi, I.P. & Sunter, A.B. (1969). "A Theory for Record Linkage." Journal of the American Statistical Association, 64(328), 1183-1210.
9. Corporate Transparency Act, 31 U.S.C. § 5336 (as amended by FinCEN interim final rule, March 2025)
10. New York LLC Transparency Act (S.995-B / A.3484), effective January 2026
