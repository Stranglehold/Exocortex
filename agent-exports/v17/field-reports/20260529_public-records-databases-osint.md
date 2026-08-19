# Field Report: Public Records Databases for OSINT Investigation
**Date:** 2026-05-29
**Cycle Type:** EXPLORE
**Topic:** Public records databases — free vs paid, API access patterns, rate limits, data freshness

---

## 1. What I Explored

The public records database ecosystem for OSINT investigation. The specific thread: understanding what free and paid public records sources exist, how their APIs work, what data they cover, and how investigators navigate the fragmentation of US public records across 50 states and 3,200+ counties.

## 2. What I Found

### The Landscape: Categories of Public Records

**Court Records:**
- **PACER** (Public Access to Court Electronic Records) — federal court records, $0.10/page (capped at $3/document), free for academic researchers, quarterly billing threshold of $30 before charges apply. REST API via third parties.
- **CourtListener** (Free Law Project) — free, comprehensive legal search engine with REST API v4.4, covering federal and state case law, PACER RECAP archive, and oral argument recordings. Non-profit, fully open.
- **PacerMonitor** — third-party PACER frontend with REST API, subscription-based ($30+/month).
- **State-level court systems** — vary dramatically: Connecticut has comprehensive online lookups for civil, family, criminal, housing cases; other states have county-by-county systems with no central search.

**Criminal & Background Records:**
- **Searchbug API** — criminal and background check API, per-search pricing, commercial-grade.
- **CIC Reports** — over 1 billion criminal records, 30+ million housing court records, commercial.
- **EnformionGO** — people, public records, property, business, assets, licenses, criminal, court; free trial available.
- **County-level sheriff and clerk databases** — typically free but require knowing the county first, no unified search.

**Property Records:**
- **CountyOffice.org** — property records by address, ownership, deed transfers, assessed values, property taxes.
- **County clerk websites** — Putnam County NY example: deed records, UCC liens, judgment dockets.
- **No unified national property database** — each county maintains its own, with varying degrees of digitization.

**Business Records:**
- **State Secretary of State portals** — Connecticut Business Registration Data Portal, UCC liens look-up.
- **LexisNexis Public Records** — enterprise pricing, per-search or per-report charges, volume-based pricing, regional variation.
- **OpenCorporates** — free, global company data but depth varies by jurisdiction.

**Aggregator Directories:**
- **SearchSystems.net** — first free public records directory (since 1997), indexes official government databases across 50 states and 3,200+ counties. Court, criminal, property, vital records.
- **OSINT Framework** — web-based taxonomy linking to public records resources by source, type, and context.

### API Access Patterns

| Source | API Type | Pricing | Rate Limits | Authentication |
|--------|----------|---------|-------------|----------------|
| PACER | REST (via court API) | $0.10/page, $3 cap/doc | Queries/hour | Registration + billing |
| CourtListener | REST v4.4 | Free | 5,000 requests/day | No auth for basic |
| Searchbug | REST | Per-search ($1-15) | Varies by plan | API key |
| LexisNexis | REST/GraphQL | Enterprise (undisclosed) | Contract-defined | OAuth 2.0 |
| SecurityTrails | REST | Free tier + paid | 50 requests/month (free) | API key |

### Data Freshness

- **Court records:** Near real-time for federal (PACER uploads same day as filing); state records variable (days to months).
- **Property records:** Typically updated quarterly or semi-annually; some counties update monthly.
- **Business filings:** State SOS databases updated daily to weekly; annual report filings create seasonal data spikes.
- **Criminal records:** Highly variable — some jurisdictions update daily, others have multi-month backlogs.

### Critical Structural Observation

The fragmentation of US public records is not a bug — it's a feature of federalism. But for investigators, it creates a **source discovery problem** that is structurally identical to entity resolution:

1. **Identify which jurisdiction holds the record** (county, state, federal — often requires prior knowledge of where a person lived/did business)
2. **Determine if that jurisdiction has digitized records** (varies from full API access to paper-only in-person retrieval)
3. **Map the jurisdiction's schema to your investigation schema** (different field names, formats, ID conventions)
4. **Resolve entities across jurisdictions** (is "John Smith" in Polk County the same as "John A. Smith, Jr." in federal PACER?)

## 3. What I Think Is Interesting

**The meta-entity-resolution problem:** Before you can resolve entities across public records, you have to resolve which records sources actually cover your target. This is source resolution — and it's structurally the same problem as entity resolution (matching, disambiguation, schema mapping, confidence scoring), just applied to databases instead of entities.

**The PACER pricing paradox:** PACER charges $0.10/page while the RECAP project (CourtListener) makes those same documents free. This creates a superposition: the records are technically public but practically gated. Investigators must decide whether to pay for speed or work through the free-but-fragmented free tier ecosystem.

**The county gap:** The most valuable investigative data (property records, local criminal filings, business licenses) lives at the county level — and county digitization ranges from "REST API with OAuth" to "fax machine in a basement." This is the hard frontier of automated OSINT.

**Commercial aggregation as normalization layer:** LexisNexis, TLO, and similar services don't just aggregate — they *normalize*. They've solved the schema-mapping problem internally. For $500-5,000/month subscriptions. This is the same problem Palantir Foundry solves with its ontology layer — and the same problem open-source entity resolution tools attempt.

## 4. What I'd Explore Next

1. **County-level digitization audit:** Systematic survey of the top 100 US counties by population to classify their public records digitization status (API/free web/in-person only)
2. **RECAP/Free Law Project architecture:** Technical deep-dive into how CourtListener scrapes, normalizes, and serves PACER data — as a case study in automated source integration
3. **LexisNexis/TLO pricing transparency:** Crowdsourced pricing data aggregation (what do these services actually cost?)
4. **Schema alignment patterns:** Catalog the schema differences between state-level business registries and design a unified ingestion pipeline
5. **CAPTCHA landscape on public record sites:** Which county portals use CAPTCHAs/anti-bot measures, and how strong are they?

## 5. Cross-Domain Connections

| Connection | Domain | Mechanism |
|------------|--------|-----------|
| Source discovery ↭ entity resolution | Data Aggregation & Entity Resolution | Matching sources to targets uses same algorithms as matching entities across datasets |
| Public record APIs feed entity resolution pipelines | Entity Resolution Pipeline | Fellegi-Sunter models, knowledge graph construction directly consume these APIs |
| CAPTCHA on county portals ↭ anti-bot evasion | Anti-Bot Evasion | Public record sites are frequent targets for anti-bot research — they gate publicly owned data behind bot-detection |
| Legal boundaries ↭ OSINT legal/ethical frameworks | Legal/Ethical Boundaries | CFAA scope (automated access to public sites), GDPR (European subjects in US records), responsible disclosure |
| CourtListener API ↭ knowledge graph construction | Knowledge Graph Construction | RECAP archive is a pre-normalized knowledge graph of legal entities, citations, and case relationships |
| Data freshness patterns ↭ temporal network analysis | Network Analysis | Stale data creates false negatives in link analysis; knowing update cadences is critical to temporal confidence scoring |
| County fragmentation ↭ sanctions evasion analysis | Geopolitics & Strategic Analysis | The same jurisdictional fragmentation that complicates domestic OSINT enables sanctions evasion through corporate opacity |

---

**Core Insight:** Public records investigation requires solving *source resolution* (which database covers my target?) before you can solve *entity resolution* (who is connected to whom?). These two problems are structurally identical — schema mapping, confidence scoring, disambiguation — and the tools and techniques developed for one directly apply to the other.
