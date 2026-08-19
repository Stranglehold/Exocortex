# Corporate Registry Investigation for OSINT

**Status:** STABLE
**Created:** 2026-07-17
**Last Updated:** 2026-07-17
**Tags:** #osint #entity-resolution #corporate #investigation #financial-crime #beneficial-ownership

## Overview

Corporate registries — government-maintained databases of legal business entities — are the foundational layer of OSINT entity resolution. They provide the canonical record of a legal entity's existence: registered name, jurisdiction, formation date, registered agent/officer identities, registered address, and (increasingly) beneficial ownership declarations. Unlike campaign finance or government contracts data, which capture transactional snapshots, corporate registries operate at the entity-formation layer. They are the first step in any multi-source entity resolution pipeline and the backbone of financial crime investigations, sanctions screening, and corporate transparency research.

This page surveys global registry architectures, the 2026 policy landscape, data access patterns, investigative techniques for shell company detection and beneficial ownership tracing, entity resolution integration, the tool ecosystem, a five-phase investigation workflow, legal/ethical boundaries, and cross-domain connections to the broader Exocortex OSINT methodology.

---

## Global Registry Architecture

Corporate registries are fundamentally jurisdictional — each sovereign territory maintains its own registration database with distinct access rules, data schemas, and update cadence. The global landscape can be categorized across three axes:

### Jurisdictional Patchwork

| Jurisdiction Type | Registry Examples | Access Model | Coverage Quality |
|-------------------|------------------|--------------|------------------|
| **Common-law (UK model)** | Companies House (UK), ACRA (Singapore), ASIC (Australia), CIPC (South Africa) | Open, free digital access to filings, officers, and (since 2016) Persons of Significant Control | High — machine-readable bulk data available |
| **US State-level (50 states + DC)** | California SOS, Delaware Division of Corporations, New York DOS, Florida Sunbiz | Variable — some open (CA, FL), others paywalled (DE charges per search). No federal registry. | Fragmented — OpenSOSData unifies via single API across all 50 states |
| **EU National Registers** | EU Business Registers (EBR), BORIS (Austria), Infogreffe (France), Handelsregister (Germany) | Mixed — EU 5AMLD mandates public UBO registers but access restricted post-2022 ECJ ruling (legitimate interest test) | Variable — EBR provides cross-EU company search, but depth varies by member state |
| **Offshore/Tax Haven** | BVI Financial Services Commission, Cayman Islands General Registry, Panama Public Registry | Opaque — historically no public beneficial ownership; some reform under OECD pressure but incomplete | Low — often requires third-party providers (Orbis, ICIJ leaks) |
| **BRICS/Emerging Markets** | China NEEQ/SAIC, India MCA21, Brazil Junta Comercial, Russia EGRUL | Mixed — India MCA21 is open and structured; China's SAIC is fragmented and Mandarin-only; Russia partially accessible via third-party aggregators | Variable — language barriers and inconsistent digitization |

### Open vs. Closed Registries

- **Open registries** (Companies House UK, OpenCorporates aggregation): Provide free, machine-readable access to entity records, officer names, filing history, and shareholder data. Enable bulk data downloads and API access.
- **Closed/paywalled registries** (Delaware, Luxembourg, BVI): Restrict access behind per-search fees, CAPTCHA walls, or jurisdictional barriers. Require third-party aggregators (Orbis, Dun & Bradstreet) or specialized proxy services.
- **Emerging open-data movement**: OpenCorporates aggregates 200M+ companies across 130+ jurisdictions in a standardized schema with provenance links to primary sources. Open Ownership Register provides structured beneficial ownership data from public disclosures.

### UBO Registry Trends (2026)

Beneficial ownership transparency has followed a boom-bust trajectory:
- **2016-2022**: UK PSC Register sets global precedent. EU 5AMLD mandates public UBO registers. US passes Corporate Transparency Act (CTA) requiring FinCEN reporting.
- **2022**: ECJ ruling invalidates unconditional public access to EU UBO registers on privacy grounds (joined cases C-37/20 and C-601/20). Member states institute "legitimate interest" tests, effectively closing registers to casual OSINT.
- **2025**: US Treasury rule change strips beneficial ownership reporting requirements from >99% of US companies, reducing CTA scope to a narrow subset of entities. GAO warns this creates a critical intelligence gap.
- **2026**: GAO publishes alternative methodology for finding ownership when 99% of companies have gone dark, relying on OpenCorporates relationship files, branch data, and indirect ownership signals.

---

## Key Data Sources

### OpenCorporates
- **Coverage**: 200M+ companies across 130+ jurisdictions
- **Data**: Legal entity name, jurisdiction, company number, registered address, officer/director names, filing history, status (active/dissolved), branch relationships
- **Access**: Free share-alike open data (attribution required), commercial license available. REST API with search by name, officer, jurisdiction, and company number.
- **2026 enhancement**: Relationship file surfaces ownership and control connections in bulk — parent-subsidiary, branch-headquarters, and officer-appointment networks. Branch data sourced directly from Secretary of State filings.
- **OSINT value**: Cross-jurisdictional director name disambiguation; temporal filing analysis for dormant → active pattern detection; branch data reveals corporate presence in opaque jurisdictions.

### OpenSOSData
- **Coverage**: All 50 US states + DC in real time
- **Data**: Entity status, registered agents, officers/directors, filing history, UCC liens (debtor/secured party), assumed names/DBAs
- **Access**: Unified REST API with entity search, officer search, and filing retrieval across all states
- **OSINT value**: Overcomes US fragmentation — single API call queries all 50 states simultaneously; UCC lien data provides financial relationship signals; registered agent patterns reveal shell company networks (common agent across dozens of entities).

### Companies House (UK)
- **Coverage**: All UK-incorporated companies and LLPs
- **Data**: Company name, registration number, registered office address, SIC code, incorporation date, filing history (annual accounts, confirmation statements), officers (directors, secretaries), Persons of Significant Control (PSC) — name, nature of control, nationality, service address
- **Access**: Free, open API. Bulk data downloads available. Streaming API for real-time filing notifications.
- **OSINT value**: PSC register is the global gold standard for beneficial ownership transparency (despite compliance gaps); confirmation statement filing cadence reveals active vs. shelf companies; officer disambiguation via month/year of birth, nationality, and service address.

### European Business Register (EBR)
- **Coverage**: 30 European business registers (EU/EEA + UK, Switzerland, Ukraine associate)
- **Data**: Company name, registration number, registered office, legal form, status
- **Access**: Web search interface; limited machine-readability. Individual national registries often provide deeper data.
- **OSINT value**: Cross-border entity search to identify EU-wide presence; preliminary surface before deeper national registry dives.

### Beneficial Ownership Registers
- **UK PSC Register**: Mandatory disclosure of individuals with >25% ownership or control. Public, free, API-accessible.
- **EU UBO Registers**: Fragmented post-2022 ECJ ruling; most require "legitimate interest" demonstrating AML/CFT purpose.
- **Open Ownership Register**: International nonprofit aggregating structured beneficial ownership data from public disclosures across 100+ countries.
- **ICIJ Offshore Leaks Database**: Investigative journalism dataset — 810,000+ offshore entities from Panama Papers, Paradise Papers, Pandora Papers, etc. Structured for entity and officer search.

### Special-Purpose Registries
- **SEC EDGAR** (US): Public company filings — 10-K, 10-Q, 8-K, beneficial ownership (Schedule 13D/G), insider transactions (Form 4)
- **Federal Reserve/OTS Banking Charters**: Regulated financial institution records (FDIC BankFind, NCUA Credit Union search)
- **FINRA BrokerCheck**: Broker-dealer and registered representative disciplinary history
- **State-level professional licensing boards**: Individuals behind LLCs often hold professional licenses (real estate, law, medicine) — linkable via name/address to corporate roles

---

## Investigative Techniques

### 1. Shell Company Detection Patterns

Shell companies — legal entities with no significant assets or operations — are the primary vehicle for financial crime obfuscation. Key detection signals:

| Signal | Detection Method | Tool Support |
|--------|-----------------|--------------|
| **Shared address** | Multiple entities registered to the same physical address (especially commercial mail receiving agencies, virtual offices, or residential addresses) | OpenCorporates address search, OpenSOSData registered agent address aggregation |
| **Shared officers/directors** | One individual listed as director/officer of dozens or hundreds of entities — classic nominee director pattern | OpenCorporates officer search, Companies House officer appointment history |
| **Circular ownership** | Entity A owns Entity B which owns Entity C which owns Entity A — creates infinite recursion obfuscating ultimate control | Graph database traversal (Neo4j, NetworkX) with cycle detection algorithms |
| **Dormant-to-active transition** | Shelf company (dormant for years) suddenly files changes, opens bank accounts, or receives assets — indicates activation for specific transaction | Companies House confirmation statement monitoring, temporal filing cadence analysis |
| **Jurisdictional arbitrage** | Entity incorporated in Delaware, operated from UK, owned by BVI holding company — layering jurisdictional opacity | Cross-jurisdictional entity resolution via name/address matching |
| **Agent-of-record concentration** | Single registered agent represents thousands of entities — common in Delaware (CT Corporation, CSC, Registered Agents Inc.) | OpenSOSData agent filtering |

### 2. Chain-Walking Methodology

Systematic tracing of ownership and control through layered corporate structures:

1. **Seed Entity**: Start with known entity (target company, payment recipient, contract awardee)
2. **Registry Lookup**: Pull full filing history, officer roster, and registered address from primary jurisdiction registry
3. **Officer Expansion**: For each officer, search across all available registries for other directorships — builds personal corporate footprint
4. **Address Pivot**: Search other entities registered at the same address — reveals co-located shell cluster
5. **Upstream/Downstream**: If entity discloses shareholders or parent company, recurse upward. If subsidiary filings list this entity as parent, expand downward.
6. **Jurisdiction Hop**: Repeat for entities discovered in offshore jurisdictions — often requires commercial databases (Orbis, World-Check) for opaque registries
7. **Beneficial Ownership Check**: Cross-reference discovered individuals against PSC registers, ICIJ Offshore Leaks, sanctions lists, and PEP databases

### 3. Temporal Analysis

- **Formation-to-dissolution velocity**: Shell companies formed and dissolved within months → likely single-transaction vehicles
- **Filing burst patterns**: Entity dormant for years → sudden flurry of officer changes, address changes, and new filings in the same week → indicates activation
- **Jurisdictional migration**: Entity formed in one jurisdiction, dissolved, re-formed elsewhere — potentially regulatory arbitrage or investigation evasion

### 4. Agent/Officer Network Graphs

Treat officers and registered agents as nodes; directorships form edges. Apply network analysis:
- **Centrality measures**: Betweenness centrality identifies nominee directors who bridge multiple shell clusters; eigenvector centrality identifies "super-connector" agents
- **Community detection**: Louvain/Leiden algorithm clusters entities sharing officer pools — reveals coordinated shell networks
- **Bipartite projection**: Officer-Entity bipartite graph → projected Entity-Entity co-officer graph for similarity-based entity resolution

---

## Entity Resolution Integration

Corporate registries serve as **anchor sources** for probabilistic entity resolution across heterogeneous datasets. The registry provides a verified name, address, and jurisdiction tuple that can be matched against:
- Campaign finance records (donor name + employer/address matching)
- Government contracts (awardee entity name matching)
- Lobbying disclosures (registrant name + client entity matching)
- Property records (owner name → entity ownership via LLC-to-person linkage)
- Sanctions lists (entity name + jurisdiction + director name matching)

### Address Normalization Challenges

| Problem | Mitigation |
|---------|------------|
| "123 Main St, Suite 400" vs "123 Main Street #400" | USPS address standardization API; libpostal open-source parser |
| International address formats (UK postcode vs US ZIP vs French departement) | libpostal handles 200+ countries; GeoNames geocoding normalization |
| Virtual office addresses shared by thousands of entities | Treat shared virtual address as negative signal — does NOT indicate co-location or common ownership; must be cross-validated with other signals |
| Registered agent address vs. principal place of business | Delaware entities list agent address as registered address — must retrieve principal address from annual report filings |

### Director Name Disambiguation

- **Problem**: "John Smith" appears as director of 500+ entities across 50 jurisdictions
- **Solution**: Compound key matching — name + partial DOB (month/year from PSC register or filing) + nationality + service address + director ID system (Companies House assigns unique officer IDs)
- **Probabilistic matching**: Fellegi-Sunter model with name Jaro-Winkler similarity, geographic proximity of associated addresses, temporal overlap of directorships

---

## Tool Ecosystem

| Tool | Type | Coverage | Key Feature | OSINT Suitability |
|------|------|----------|-------------|--------------------|
| **OpenCorporates** | Aggregator, API | 130+ jurisdictions, 200M+ companies | Standardized cross-jurisdictional schema with source provenance | Free tier for non-commercial OSINT; commercial license for high-volume |
| **OpenSOSData** | Aggregator, API | All 50 US states | Unified API across all Secretary of State databases; UCC lien data | Commercial API with tiered pricing |
| **Companies House API** | Official Registry | UK | PSC beneficial ownership, streaming filing notifications, unique officer IDs | Free, open, no API key required for basic access |
| **OpenOwnership Register** | Nonprofit Aggregator | 100+ countries | Structured BODS (Beneficial Ownership Data Standard) format | Free, open |
| **ICIJ Offshore Leaks** | Investigative Dataset | 810K+ offshore entities | Cross-references five major leaks (Panama, Paradise, Pandora, etc.) | Free, web interface + structured data export |
| **OCCRP Aleph** | Investigative Platform | Cross-source (registries + sanctions + leaks) | Entity search across 200+ datasets with graph exploration | Free for investigative journalists and researchers |
| **Orbis (Bureau van Dijk/Moody's)** | Commercial Database | 400M+ companies globally | Beneficial ownership pyramids, corporate family trees, financials | Commercial license required; widely available via academic and library access |
| **Dun & Bradstreet D-U-N-S** | Commercial Database | 500M+ entities | DUNS number provides unique entity identifier across datasets | Commercial; basic company lookup available |
| **OpenRefine** | Data Cleaning | N/A | Reconciliation API against OpenCorporates, Wikidata — batch entity matching | Free, open source |
| **NetworkX / igraph / Neo4j** | Graph Analysis | N/A | Build entity-officer-address multi-partite graphs for community detection and centrality analysis | Free/open source for NetworkX/igraph; Neo4j Community Edition |

---

## 5-Phase Investigation Workflow

### Phase 1: Seed Discovery
- Identify target entity from initial intelligence source (payment records, contract award, news article, whistleblower report)
- Extract entity name, jurisdiction, and any known identifiers (company number, tax ID)

### Phase 2: Registry Lookup
- Query primary jurisdiction registry via OpenCorporates or official API
- Retrieve: legal name, registration number, status, registered address, officer roster, filing history
- If entity is in Delaware or other opaque jurisdiction, use OpenSOSData or third-party provider

### Phase 3: Network Expansion
- **Officer expansion**: Search each officer across all available registries for other directorships
- **Address expansion**: Search registered address for co-located entities
- **Upstream expansion**: Trace parent/subsidiary relationships via OpenCorporates relationship file, Orbis corporate tree, or Companies House PSC register
- **Downstream expansion**: Search for entities listing target entity as parent

### Phase 4: Entity Resolution & Cross-Source Verification
- Resolve discovered entities and individuals against:
  - Sanctions lists (OFAC SDN, EU, UN, UK HMT)
  - PEP databases (World-Check, Dow Jones)
  - Campaign finance records (FEC, state-level)
  - Government contracts (USASpending, TED EU)
  - Property records (county assessor, ATTOM)
  - News archives (LexisNexis, Google News)
- Fellegi-Sunter probabilistic matching with entity name + address + jurisdiction as blocking key

### Phase 5: Graph Construction & Analysis
- Build multi-partite graph: [Entity] —(has_officer)→ [Person] —(also_director_of)→ [Entity] —(registered_at)→ [Address] —(also_registered_at)→ [Entity]
- Run community detection (Leiden, Louvain) to identify coordinated shell clusters
- Compute centrality measures to identify key connector individuals and entities
- Export to Gephi/Cytoscape for visualization or Neo4j for interactive exploration

---

## Legal & Ethical Boundaries

Corporate registry data is generally public record — but accessing, aggregating, and using it at scale for investigative purposes carries legal and ethical obligations:

| Risk Category | Applicable Rules | Mitigation |
|---------------|-----------------|------------|
| **GDPR/Data Protection** | EU GDPR Article 14 — data subjects (officers, beneficial owners) have right to be informed of processing | If systematically processing personal data from EU registries, provide fair processing notice or rely on "legitimate interest" exception (DPA 2018 Schedule 2, Part 1 for UK) |
| **Beneficial Ownership Access** | Post-ECJ 2022 ruling, EU UBO registers require legitimate interest demonstration | AML/CFT investigation purposes qualify; general curiosity does not. Document the specific investigative purpose before accessing restricted registers |
| **FCRA (US Fair Credit Reporting)** | If entity data used for consumer eligibility decisions (credit, employment, insurance) | FCRA applies — corporate investigation for due diligence/KYC is generally exempt, but individual background checks using corporate data may trigger FCRA |
| **Computer Fraud and Abuse Act (CFAA)** | Automated scraping that violates registry terms of service | Use official APIs where available (OpenCorporates, Companies House, OpenSOSData). For registries without APIs, respect robots.txt and rate limits |
| **Private Investigator Licensing** | Some US states require PI license for certain types of investigative research | Corporate due diligence and OSINT from public records generally exempt, but investigation of individuals using registry data may cross the line — check state-specific regulations |
| **Source Attribution** | Open data licenses (ODbL, CC-BY-SA) require attribution | Cite OpenCorporates as source when using their data; preserve provenance links to primary registry filings |

---

## Cross-Domain Connections

| Connection | Exocortex Wiki Page | Relationship |
|------------|---------------------|--------------|
| Corporate registries are the anchor source for multi-source entity resolution | [[property-records-osint]], [[campaign-finance-entity-resolution]], [[government-contracts-entity-resolution]], [[lobbying-disclosure-entity-resolution]] | Entity name + address from registry enables cross-dataset probabilistic matching |
| Shell company detection mirrors sanctions evasion methodology | [[supply-chain-network-analysis-osint]], [[sanctions-evasion-detection-patterns]] | Layered corporate structures hide ultimate beneficiaries — same techniques apply to sanctions circumvention detection |
| DNS/WHOIS investigation reveals corporate digital infrastructure | [[dns-whois-investigation-osint]] | Domain registration (WHOIS) often lists corporate registrants — cross-reference with registry data for entity confirmation |
| Beneficial ownership is the inverse of entity resolution: finding the human behind the legal entity | [[entity-resolution-agent-safety]], [[cross-source-entity-resolution-knowledge-graphs]] | ER formalizes the probabilistic identity linkage; beneficial ownership is the specific application to corporate control |
| OpenCorporates relationship files enable graph-based investigation | [[network-analysis-techniques-osint]], [[force-directed-graph-layouts-osint]] | Entity-officer-address graphs are natural inputs to community detection and centrality analysis pipelines |
| Corporate registry investigation is a core OSINT competency | [[bellingcat-osint-methodology]], [[osint-tradecraft-bellingcat-methodology]] | Bellingcat's 7-element methodology includes corporate record analysis as a core evidence layer |
| Legal entities are persons in the intelligence analysis framework | [[analysis-of-competing-hypotheses-ach]], [[intelligence-failure-analysis]] | ACH applied to corporate structures: competing hypotheses about ultimate beneficial ownership are evaluated against registered evidence |
| Data breach records provide personal identifiers for officer disambiguation | [[data-breach-analysis-osint-identity-linkage]] | Breached email addresses and phone numbers linked to officers resolve ambiguous name matches across registries |
| Job posting analysis reveals corporate structure and expansion patterns | [[job-posting-analysis-economic-intelligence]] | Entity expansion signals (new office openings, hiring surges) complement static registry data with temporal intelligence |
| IP geolocation provides operational address verification | [[ip-address-geolocation]] | Corporate website hosting IP geolocation → validate against registered address for entity authenticity assessment |

---

## References

1. OpenCorporates. (2026). "The Largest Open Database of Companies in the World." https://opencorporates.com/ API Reference v0.4.8: https://api.opencorporates.com/documentation/API-Reference
2. OpenSOSData. (2026). "Secretary of State API — Every State, Real-Time." https://opensosdata.com/
3. US Government Accountability Office (GAO). (2026). Report on Beneficial Ownership Reporting Gap Post-2025 Rule Change. As covered by OpenCorporates blog, 2026-06-10: https://blog.opencorporates.com/2026/06/10/government-accountability-office-finding-ownership/
4. Companies House. (2026). "Companies House API." https://developer.company-information.service.gov.uk/
5. European Business Register. (2026). https://e-justice.europa.eu/content_business_registers_at_european_level-106-en.do
6. Open Ownership. (2026). "Beneficial Ownership Data Standard (BODS)." https://standard.openownership.org/
7. International Consortium of Investigative Journalists (ICIJ). (2026). "Offshore Leaks Database." https://offshoreleaks.icij.org/
8. OCCRP Aleph. (2026). "The Global Archive of Investigative Data." https://aleph.occrp.org/
9. Bureau van Dijk (Moody's Analytics). (2026). "Orbis — Company Data Across the Globe." https://www.bvdinfo.com/en-gb/our-products/data/international/orbis
10. Ren, W., Lian, X., & Ghazinour, K. (2021). "Online Topic-Aware Entity Resolution Over Incomplete Data Streams." arXiv:2103.08720.
11. Fellegi, I.P. & Sunter, A.B. (1969). "A Theory for Record Linkage." Journal of the American Statistical Association, 64(328), 1183-1210.
12. Court of Justice of the European Union. (2022). Joined Cases C-37/20 and C-601/20 — WM and Sovim SA v Luxembourg Business Registers. Invalidating unconditional public access to beneficial ownership registers.
13. UK Economic Crime and Corporate Transparency Act. (2023). Reforms to Companies House powers, identity verification for directors, and PSC register enforcement.
14. Spotlight EBU. (2026). "Tracing Beneficial Ownership with OSINT for Financial Crime." https://spotlight.ebu.ch/p/tracing-beneficial-ownership-with

---

*Grounded in shared Exocortex corpus (v17): corporate-registry-analysis-entity-resolution, cross-source-entity-resolution-knowledge-graphs, osint-entity-resolution-methods, economic-espionage-history-osint-detection, bellingcat-osint-methodology. Grounded in technical library: Nolo legal/business formation references. Web sources: OpenCorporates (2026), OpenSOSData (2026), GAO/OpenCorporates blog (2026-06-10), Spotlight EBU tutorial.*
