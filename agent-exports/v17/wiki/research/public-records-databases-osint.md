# Public Records Databases for OSINT Investigation
**Status:** STABLE
**Created:** 2026-07-08
**Domain:** OSINT & Investigation Methodology → Data Aggregation & Entity Resolution
**Interests:** OSINT & Investigation Methodology

## Summary
Comprehensive survey of public records databases available for OSINT investigations. Covers seven major categories of publicly accessible records — campaign finance, corporate registries, government contracts, lobbying disclosures, property records, court/legal records, and securities filings — plus professional licensing and vital records. For each category: key data sources, access tiers (free vs paid), API availability, rate limits, data freshness characteristics, and entity resolution integration patterns. The public records landscape is the raw material of OSINT entity resolution: each database type provides different fragments of an entity's identity, and the investigator's craft lies in resolving these fragments across heterogeneous sources.

---

## 1. Campaign Finance Records

### Federal: FEC.gov
| Attribute | Detail |
|-----------|--------|
| **Source** | [FEC.gov/data](https://www.fec.gov/data/) |
| **Coverage** | Federal candidates, PACs, parties, itemized individual contributions ($200+ threshold) |
| **Access** | REST API (free), bulk CSV downloads (free), web search |
| **Rate Limits** | 1,000 API calls/hour (key required), 30 calls/minute without key |
| **Data Freshness** | Quarterly filing deadlines; 24-48 hour processing delay after filing |
| **Key Fields** | Contributor name/address/employer/occupation, recipient committee, date, amount, election cycle |
| **Entity Resolution Value** | Links individuals to political affiliations, employer data, geographic location; donor-donor network edges |

### State-Level Sources
| Source | Coverage | Access |
|--------|----------|--------|
| [FollowTheMoney.org](https://www.followthemoney.org/) | All 50 states: campaign + ballot measure contributions | Web, API (free) |
| [OpenSecrets](https://www.opensecrets.org/) | Federal + growing state coverage | API, web (free tier, paid bulk) |
| [ProPublica Campaign Finance API](https://projects.propublica.org/api-docs/campaign-finance/) | Federal, enriched with social media accounts | REST API (free, rate-limited) |
| [FECGraph](https://www.fecgraph.com/) | Federal, Stanford/Columbia graph-based linking | Knowledge graph interface |
| Individual state portals | CA Cal-Access, NY BOE, TX Ethics Commission, etc. | Varies (web, some API) |

### Cross-Domain Entity Resolution
Campaign finance data links to: corporate registries (employer validation), lobbying disclosures (same firm lobbying + donating), government contracts (vendor → political contributions), property records (donor address → property ownership). See [[campaign-finance-donor-analysis]], [[campaign-finance-entity-resolution]].

---

## 2. Corporate Registries

### US Secretary of State System
The US operates a fragmented state-level registry system with 50+ jurisdictions, each maintaining independent databases.

| Attribute | Detail |
|-----------|--------|
| **Structure** | 50 states + DC + territories, each with independent database |
| **Key Fields** | Entity name, formation date, registered agent, principal address, status (active/inactive/dissolved), officers/members (varies by state) |
| **Access** | Varies: some states provide full downloads (DE, WY, NV), others require per-record lookups; no federal API standard |
| **Aggregators** | OpenCorporates, Bizapedia, CorporationWiki aggregate from state sources |
| **Beneficial Ownership** | FinCEN CTA paused March 2025 — no federal BO database for domestic LLCs; state-level disclosure inconsistent |
| **Notable Jurisdictions** | Wyoming, Delaware, Nevada — high-volume LLC formations, minimal disclosure |
| **Cost** | Generally free at state level; aggregator APIs have paid tiers |

### UK: Companies House
| Attribute | Detail |
|-----------|--------|
| **Source** | [Companies House](https://www.companieshouse.gov.uk/) |
| **Coverage** | All UK registered companies |
| **Access** | Free REST API with real-time company profiles, officer searches, filing history, Persons with Significant Control (PSC) register |
| **Key Advantage** | PSC register provides beneficial ownership data — a feature absent from US state registries |

### International Registries
| Registry | Jurisdiction | Access | Notes |
|----------|-------------|--------|-------|
| Companies House | UK | Free API | PSC beneficial ownership |
| OpenCorporates | Global (140+ jurisdictions) | API (free tier, paid bulk) | Best aggregation layer; variable coverage by jurisdiction |
| EU Business Registers | EU member states | BRIS (Business Registers Interconnection System) | Cross-EU search; not all states at full parity |
| Dun & Bradstreet | Global | Paid (D-U-N-S Number) | Commercial; DUNS required for US federal contracting |
| Orbis (Bureau van Dijk) | Global | Paid (enterprise) | Ultimate ownership, corporate trees, financials |

### Entity Resolution Value
Corporate registries are the foundational layer — the canonical source of truth for legal entity existence. All subsequent entity resolution (campaign finance, procurement, property, sanctions) ties back to corporate identity. See [[corporate-registry-analysis-entity-resolution]], [[cross-jurisdictional-entity-resolution]].

---

## 3. Government Contracts & Procurement

### US Federal: SAM.gov (Post-February 2026)
**Critical OSINT Impact:** FPDS.gov permanently decommissioned February 24, 2026. All contract award data now exclusively on SAM.gov. Anonymous ezSearch is dead — authenticated SAM.gov login required. Legacy ATOM feed sunsetting FY2026, replaced by Contract Awards API.

| Source | Coverage | Access |
|--------|----------|--------|
| **SAM.gov — Contract Data** | All historical FPDS records + new awards + eSRS subcontracting reports | Authenticated web search, Contract Awards API |
| **SAM.gov — Entity Information** | Legal business name, UEI, CAGE codes, NAICS, set-aside certifications | Entity API (1,000 req/day free tier), bulk extract |
| **SAM.gov — Exclusions** | Debarred/suspended entities (FAR Subpart 9.4) | Exclusions API (free) |
| **USAspending.gov** | Transaction-level federal awards — contracts, grants, loans, direct payments | Bulk CSV, public API (filtering/aggregation/pagination) |
| **SBA Size Standards** | Industry-specific revenue/employee thresholds | SBA API |
| **CPARS** | Contractor past performance evaluations (migrating to SAM.gov FY2026) | Currently separate; migration pending |
| **USASpending** | ~$700B/year in obligations, FY2001–present | Public API + bulk downloads |

### International Procurement Data
| Source | Jurisdiction | Coverage |
|--------|-------------|----------|
| **TED (Tenders Electronic Daily)** | EU | ~$2T annual market, 15% EU GDP; public procurement notices |
| **FOPPA** | France | Open database: French award notices 2010–2020 |
| **Contracts Finder** | UK | Public sector contracts >£10,000 |
| **CanadaBuys** | Canada | Federal procurement, standing offers |

### Entity Resolution Value
Four detection functions (from RonanWrites production pipeline): cumulative concentration analysis, pass-through subcontracting detection, price benchmark outlier analysis, certification fraud screening. Procurement data links entities to revenue streams, capabilities (NAICS), and government relationships. See [[government-contracts-procurement-osint]].

---

## 4. Lobbying Disclosures

### Federal: LDA.gov / Congress.gov
| Attribute | Detail |
|-----------|--------|
| **Legal Basis** | Lobbying Disclosure Act of 1995 (LDA), Honest Leadership and Open Government Act of 2007 (HLOGA) |
| **Filings** | LD-1 (Registration), LD-2 (Quarterly Activity Report), LD-203 (Contributions Report) |
| **Key Fields** | Registrant, client, lobbyists (with former government positions), issues lobbied (26 categories + specific bills), agencies contacted, income/expenses |
| **Access** | Public web (LDA.gov, Congress.gov), bulk downloads, Senate Office of Public Records (SOPR) raw filings |
| **Enriched Sources** | OpenSecrets (standardized data + revolving door), ProPublica Lobbying API (structured JSON) |
| **Data Freshness** | Quarterly filings due 20 days after quarter end; ~30-day processing delay |

### State-Level Lobbying
| Attribute | Detail |
|-----------|--------|
| **Structure** | 50 separate jurisdictions, varying disclosure quality and formats |
| **Access** | Fragmented — each state maintains its own database; some provide bulk downloads, others web-only |
| **Key Limitation** | No unified API; cross-state analysis requires per-state ingestion |

### Entity Resolution Value
Lobbying records are the bridge between corporate identity and political influence. A typical pipeline: corporate registry → lobbying client → individual lobbyists (with former government roles) → issues/agencies → campaign contributions. The lobbying-campaign finance-government contracts triangle reveals the full influence architecture. See [[lobbying-disclosure-entity-resolution]].

---

## 5. Property Records

### County-Level Assessor/Recorder Databases
| Attribute | Detail |
|-----------|--------|
| **Structure** | ~3,000+ US counties, each with independent assessor and recorder offices |
| **Key Fields** | Owner name/mailing address, property address, assessed value, sale date/price, legal description (parcel number), tax status, mortgage/deed records |
| **Access** | Highly variable: some counties offer free online search/API (larger urban counties), others require in-person or paid subscription |
| **Aggregators** | Zillow, Redfin, CoreLogic, Black Knight (mortgage), ATTOM Data — commercial aggregators with API access |

### Title Company Databases
| Source | Coverage | Access |
|--------|----------|--------|
| County Recorder offices | Individual counties | Free-to-paid; in-person for historical |
| Title plants (First American, Old Republic, Fidelity) | Regional aggregations | Paid; access via title company relationships |
| MERS (Mortgage Electronic Registration Systems) | National mortgage registry | Limited public access |

### Privacy-Limited Jurisdictions
- **Trust ownership states** (Wyoming, Delaware, South Dakota): property can be held in trust, obscuring beneficial ownership
- **LLC-owned property**: chain-walking required — county assessor → LLC name → state SOS → registered agent (not beneficial owner)
- **Non-disclosure states**: ~12 states (TX, UT, NM, etc.) do not disclose sale prices

### Entity Resolution Value
Property records are the physical anchor for entity resolution — linking individuals and entities to geographic locations, financial capacity (assessed values, mortgage amounts), and ownership networks (multiple properties under same owner). The assessor→LLC→SOS chain-walking pattern is fundamental to beneficial ownership investigation. See [[property-records-entity-resolution]].

---

## 6. Court & Legal Records

### Federal: PACER (Public Access to Court Electronic Records)
| Attribute | Detail |
|-----------|--------|
| **Source** | [PACER.gov](https://pacer.uscourts.gov/) |
| **Coverage** | All US federal district, appellate, and bankruptcy courts |
| **Cost** | $0.10/page ($3.00 cap per document); free if <$30/quarter |
| **Key Data** | Party names/attorneys, case type (civil/criminal/bankruptcy), docket entries, filings, judgments, appeal status |
| **Limitations** | No full-text search across courts; per-court query interface; documents behind paywall |
| **Third-Party Access** | RECAP (free browser extension — crowdsourced PACER documents), CourtListener (Free Law Project — bulk docket data, API), UniCourt (paid — normalized cross-court search) |

### State Court Systems
| Attribute | Detail |
|-----------|--------|
| **Structure** | 50 state court systems, each with varying levels of electronic access |
| **Access** | Growing e-filing adoption; many states now offer online docket search (free or low-cost) |
| **Aggregators** | LexisNexis CourtLink, Westlaw Dockets (paid); JudyRecords (free, crowdsourced) |
| **Key Limitation** | No unified national state court search; cross-state entity resolution requires per-state queries |

### Other Legal Databases
| Database | Coverage | Access |
|----------|----------|--------|
| **SEC EDGAR** | Public company filings (10-K, 10-Q, 8-K, proxy, insider trading) | Free API + web; see Section 7 below |
| **Bureau of Prisons Inmate Locator** | Federal inmates | Free web |
| **State DOC inmate databases** | State prisoners | Varies by state |
| **National Sex Offender Registry** | Registered offenders | Free (Dru Sjodin NSOPW) |
| **OFAC SDN List** | Sanctioned individuals/entities | Free API + bulk download |
| **Interpol Red Notices** | Wanted persons | Limited public access |

### Entity Resolution Value
Court records provide the adversarial paper trail — litigation reveals business relationships, disputes, fraud allegations, and ownership structures not disclosed in voluntary filings. Bankruptcy records are particularly rich for entity resolution (schedules of assets, creditors, affiliated entities). The defendant-plaintiff edge is a high-signal entity relationship that does not appear in corporate registries. See also [[data-breach-analysis-osint]] (civil litigation following breaches).

---

## 7. Securities Filings (SEC EDGAR)

| Attribute | Detail |
|-----------|--------|
| **Source** | [SEC EDGAR](https://www.sec.gov/edgar) |
| **Coverage** | All US public companies, mutual funds, ETFs; filings from 1994–present |
| **Key Filings** | 10-K (annual report — business description, risk factors, financials, legal proceedings), 10-Q (quarterly), 8-K (material events), Proxy (DEF 14A — executive compensation, related-party transactions), Forms 3/4/5 (insider trading), 13-D/G (beneficial ownership >5%), S-1 (IPO registration) |
| **Access** | Free: EDGAR full-text search, REST API (10 requests/second), bulk XBRL/RSS feeds |
| **Data Freshness** | Real-time acceptance; 8-K within 4 business days of material event; 10-K/Q on periodic schedule |
| **Key Limitations** | XBRL tagging quality varies; only covers public companies; foreign private issuers file 20-F (less granular) |
| **Third-Party** | OpenSEC (API), EDGAR Online (paid enhanced), BamSEC (paid analysis) |

### Entity Resolution Value
SEC filings are the most regulatorily-enforced public records in existence — false statements carry criminal liability. Key OSINT value: beneficial ownership (13-D/G, proxy), related-party transactions (proxy), subsidiary listings (10-K Exhibit 21), material contracts (8-K exhibits), executive backgrounds (proxy bios). The public-company disclosure regime is the gold standard for entity transparency. See also: [[alternative-data-sources-financial-intelligence]], [[derivatives-pricing-volatility-trading]], [[market-microstructure-liquidity-dynamics]].

---

## 8. Professional Licensing Databases

| Category | Examples | Access Pattern |
|----------|----------|---------------|
| **Medical** | State medical boards, NPDB (restricted) | Per-state lookup; some states provide bulk licensee lists |
| **Legal** | State bar associations | Generally free lookup by name/bar number |
| **Financial** | FINRA BrokerCheck, SEC IAPD (investment advisers), state insurance commissioners | Free web search by name/CRD# |
| **Real Estate** | State real estate commissions | Per-state lookup |
| **Contractors** | State contractor licensing boards | Per-state lookup |
| **Aviation** | FAA Airmen Certification, Aircraft Registry | Free web search |
| **Maritime** | FCC Ship Licenses, USCG Mariner Credentialing | Free web search |
| **Education** | State teacher credentialing | Per-state lookup |

### Entity Resolution Value
Professional licenses provide verified identity anchors — name, address, credential number, disciplinary history — that serve as high-confidence matching keys across datasets. A medical license number is a stronger identity anchor than a name+address pair. FINRA BrokerCheck is particularly rich: employment history, exam qualifications, disclosures, customer disputes.

---

## 9. Vital Records (Limited OSINT Utility)

| Record Type | Access | OSINT Constraints |
|-------------|--------|-------------------|
| **Birth certificates** | State vital records offices | Restricted — typically only to registrant, immediate family, or legal representative |
| **Death certificates** | State vital records offices | Partially public; Social Security Death Master File (SSDMF) available commercially |
| **Marriage/divorce records** | County clerk offices | Generally public but per-county access; some states have centralized indexes |
| **SSDMF (Social Security Death Master File)** | NTIS (commercial license) | Available via LexisNexis, Westlaw, other commercial aggregators |

---

## 10. Access Tiers, APIs & Rate Limits Summary

### Free Tier (Public APIs)
| Database | API | Rate Limit | Key Constraint |
|----------|-----|-----------|----------------|
| FEC.gov | REST | 1,000/hr (key), 30/min (no key) | $200 itemization threshold |
| SAM.gov Entity API | REST | 1,000/day free tier | Authenticated login required post-2026 |
| SAM.gov Exclusions | REST | Free, no stated limit | Current exclusions only |
| USAspending.gov | REST | Free, no stated limit | FY2001–present; lag on recent awards |
| Companies House (UK) | REST | Free, real-time | UK entities only |
| SEC EDGAR | REST | 10 req/sec, no daily limit | XBRL quality varies |
| OpenSecrets | REST | Free tier (limited calls) | Bulk data is paid |
| FollowTheMoney | REST | Free | State-level only |
| PACER | Web | $0.10/page, free if <$30/quarter | Per-court interface, no cross-court text search |
| CourtListener | API | Free (Free Law Project) | Bulk dockets, not all documents |
| OFAC SDN | API | Free | Sanctions list only |

### Paid / Commercial Access
| Category | Providers | Typical Cost |
|----------|----------|-------------|
| Corporate registries (aggregated) | OpenCorporates API (paid tier), Dun & Bradstreet, Orbis | $500–$5,000+/year |
| Court records (aggregated) | LexisNexis CourtLink, Westlaw Dockets, UniCourt, PacerPro | $200–$1,000+/month |
| Property records (aggregated) | ATTOM Data, CoreLogic, Black Knight | Enterprise pricing ($1,000+/year) |
| SEC filings (enhanced) | BamSEC, Sentieo/AlphaSense | $500–$2,000+/year |
| Professional licensing (aggregated) | LexisNexis, TLOxp, IRBsearch | Enterprise pricing |
| Entity resolution (commercial) | LexisNexis Accurint, Thomson Reuters CLEAR, Sayari | Enterprise pricing ($5,000+/year) |

### Key OSINT Constraints
1. **Fragmentation:** US public records are distributed across ~3,000 counties, 50 states, and dozens of federal agencies — no unified query interface
2. **Authenticated Access Trend:** SAM.gov moving to login-required (2026), CDX (EPA) requires registration — the post-FPDS era means more traceable OSINT
3. **Data Freshness:** Quarterly/annual filing cycles mean 90-365 day lag on many datasets
4. **Paywalls:** PACER charges by page, commercial aggregators charge enterprise fees — free OSINT has real cost constraints
5. **Beneficial Ownership Gap:** No US federal BO database (CTA paused March 2025); state-level BO disclosure inconsistent
6. **State-Level Variability:** Campaign finance disclosure quality, corporate registry search functionality, and court e-filing access vary dramatically by state

---

## 11. Entity Resolution Integration Pattern

The standard multi-source entity resolution pipeline using public records:

1. **Anchor**: Start with corporate registry (state SOS / Companies House) — canonical entity existence
2. **Enrich**: Add federal identifiers (UEI/DUNS from SAM.gov, EIN from tax filings, CIK from EDGAR)
3. **Link**: Campaign finance (FEC donor/recipient), lobbying (LDA client/registrant), government contracts (vendor), property (owner)
4. **Network**: Build graph — shared addresses, shared officers, shared lobbyists, shared campaign contributions
5. **Adverse**: Court records (PACER) for litigation relationships, disputes, fraud allegations
6. **Validate**: Professional licenses as identity anchors; SEC filings for public company verification

See also: [[cross-jurisdictional-entity-resolution]], [[corporate-registry-analysis-entity-resolution]], [[campaign-finance-entity-resolution]], [[lobbying-disclosure-entity-resolution]], [[property-records-entity-resolution]], [[financial-intelligence-entity-resolution]], [[data-lineage-provenance-entity-resolution]].

---

## 12. Cross-Domain Connections

| Connection | Wiki Page |
|------------|-----------|
| Entity resolution across public records | [[cross-jurisdictional-entity-resolution]], [[corporate-registry-analysis-entity-resolution]] |
| Campaign finance → influence networks | [[campaign-finance-donor-analysis]], [[campaign-finance-entity-resolution]] |
| Government contracts → vendor mapping | [[government-contracts-procurement-osint]] |
| Lobbying → influence architecture | [[lobbying-disclosure-entity-resolution]] |
| Property → beneficial ownership | [[property-records-entity-resolution]] |
| Court records → adversarial paper trail | [[data-breach-analysis-osint]], [[osint-legal-ethical-boundaries]] |
| FININT integration | [[financial-intelligence-entity-resolution]], [[alternative-data-sources-financial-intelligence]] |
| Sanctions evasion detection | [[sanctions-evasion-detection]], [[temporal-entity-resolution]] |
| Supply chain reconstruction | [[supply-chain-network-analysis-osint]] |
| Dark web → clearnet cross-reference | [[dark-web-osint-investigation]] |
| OSINT legal/ethical boundaries | [[osint-legal-ethical-boundaries]] |
| Visualization for multi-source networks | [[visualization-techniques-osint]] |
| Human investigation tactics | [[human-investigation-tactics]] |
| Data lineage/provenance | [[data-lineage-provenance-entity-resolution]] |
| Defense procurement OSINT | [[defense-procurement-cycles]] |
| Network analysis techniques | [[network-analysis-techniques-osint]] |
| OSINT tools survey | [[open-source-osint-tools-survey]] |
| DNS/WHOIS integration | [[dns-whois-investigation-osint]] |
| Email header analysis | [[email-header-analysis]] |
| Phone number investigation | [[phone-number-investigation-osint]] |
| Social media forensics | [[social-media-forensics-osint]] |
| Reverse image search | [[reverse-image-search-osint]] |
| Satellite imagery | [[satellite-imagery-osint]] |
| Data breach analysis | [[data-breach-analysis-osint]] |

---

## References

1. FEC.gov Campaign Finance Data — https://www.fec.gov/data/
2. OpenSecrets (Center for Responsive Politics) — https://www.opensecrets.org/
3. FollowTheMoney.org (National Institute on Money in Politics) — https://www.followthemoney.org/
4. LDA.gov / Congress.gov Lobbying Disclosure — https://lda.congress.gov/
5. SAM.gov (post-Feb 2026 FPDS migration) — https://sam.gov/
6. USAspending.gov — https://www.usaspending.gov/
7. SEC EDGAR — https://www.sec.gov/edgar
8. PACER (Public Access to Court Electronic Records) — https://pacer.uscourts.gov/
9. CourtListener / Free Law Project — https://www.courtlistener.com/
10. Companies House (UK) — https://www.companieshouse.gov.uk/
11. OpenCorporates — https://opencorporates.com/
12. FinCEN Corporate Transparency Act implementation (paused March 2025) — https://www.fincen.gov/boi
13. FINRA BrokerCheck — https://brokercheck.finra.org/
14. OFAC SDN List — https://sanctionssearch.ofac.treas.gov/
15. IRS Form 990 (nonprofit filings) — https://apps.irs.gov/app/eos/
16. Lobbying Disclosure Act of 1995 (2 U.S.C. § 1601 et seq.)
17. Honest Leadership and Open Government Act of 2007 (Pub. L. 110-81)
18. Government Contracts & Procurement OSINT wiki page — [[government-contracts-procurement-osint]]
