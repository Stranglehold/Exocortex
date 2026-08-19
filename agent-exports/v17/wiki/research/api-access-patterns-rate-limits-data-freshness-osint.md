# API Access Patterns, Rate Limits & Data Freshness for OSINT Investigation

**Status:** DRAFT → STABLE
**Created:** 2026-08-04
**Updated:** 2026-08-04
**Domain:** OSINT & Investigation Methodology → Data Aggregation & Entity Resolution
**Interests:** OSINT & Investigation Methodology (public records, API access, rate limits, data freshness)

## Summary

The practical API layer separating an investigator from public-records data is often the real barrier: the underlying records (PACER, EDGAR, OpenFEC, state registries) are free, while access, aggregation, and freshness engineering carry the cost. This page systematizes API access patterns, rate-limit mechanics, and data-freshness windows for OSINT collection, grounded in the shared corpus (public-records survey, field reports, memory) and primary documentation (OpenFEC, CourtListener v4.4, data.gov, SAM.gov 2026).

## Why This Layer Matters

- Public records are fragmented across ~3,000 counties, 50 states, and dozens of federal agencies with no unified query interface.
- Source resolution (which database covers my target?) is structurally isomorphic to entity resolution (who connects to whom?): both require schema mapping, confidence scoring, disambiguation, and matching.
- Rate limits and freshness windows determine whether collection can be automated, how fast an investigation can pivot, and whether collection stays inside ToS/legal boundaries.
- The collection stack is a three-layer architecture: query layer (search APIs), transport layer (bulk mirrors, webhooks, CDC feeds), aggregation layer (commercial multi-jurisdictional aggregators).

## API Access Taxonomy

| Tier | Characteristics | Examples |
|------|-----------------|----------|
| Open REST (key optional) | Documented endpoints, free | OpenFEC, CourtListener, EDGAR |
| Key-required free tier | Registration gated, generous quotas | api.data.gov, FEC elevated tier |
| Authenticated/pay-per-use | Billing per query | PACER ($0.10/page), LexisNexis, Searchbug |
| Gated government APIs | Federal identity/auth required | SAM.gov post-2026 (ezSearch decommissioned) |
| Bulk/CSV mirrors | Full-dataset dumps | FEC bulk files, EDGAR full-text, open-data portals |
| Scraping-only | No API, HTML-only | Many county assessor/recorder portals |
| Commercial aggregators | Normalized multi-jurisdiction | ATTOM Data, CoreLogic, OpenCorporates paid tiers |

## Rate-Limit Mechanics

- Standard signals: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`; HTTP 429 on exhaustion.
- Algorithm families: token bucket, sliding window, per-key/per-IP quotas; align backoff with reset semantics, not fixed sleeps.
- Robust client pattern: exponential backoff with jitter on 429/5xx, honor `Retry-After`, cache with ETag/If-None-Match, batch pagination within quota.
- Pagination caps make logical queries expensive (OpenFEC 100 results/page); budget calls before scheduling.
- Bulk-over-API tradeoff: if a periodic full refresh suffices, bulk dumps are cheaper than page-by-page API enumeration.
- Distributed collectors must centralize quota state; per-IP limits still apply even when per-key quotas are separate.

## Data Freshness & Temporal Design

- Freshness windows define the staleness envelope: campaign finance quarterly filings + 24-48h lag; court dockets near real-time after filing; SEC EDGAR same-day; county assessors often paper-linked and delayed.
- Freshness tiering: real-time/streaming (webhooks), near-real-time (REST polling), batch (bulk mirrors), archival (web archives, government portals).
- Collection design should map each record type to its freshness tier; over-polling wastes quota, under-polling misses pivots.
- Timestamp normalization is an entity-resolution prerequisite: record `last_updated` as metadata and maintain as-of provenance for chain of custody.

## Public Records API Reference Points

| Source | Access | Rate Limits | Freshness |
|--------|--------|-------------|-----------|
| FEC/OpenFEC | REST + bulk | 1,000/hr default; elevated 7,200/hr (120/min) on request | Quarterly deadlines + 24-48h lag |
| CourtListener REST v4.4 | Free REST | 2026 default 5/min, 50/hr, 125/day; membership packages expand | Rolling window; webhook push |
| PACER | Paid API/web | Per-page cost | Near real-time after filing |
| data.gov API | api.data.gov proxy | 1,000/hour per key | Varies by dataset |
| SEC EDGAR | REST + full-text | ~10 req/s and 1,000/hr per IP (fair access) | Same-day filings |
| SAM.gov | Authenticated API | API key; legacy ATOM sunset FY2026 | FPDS consolidated; old ezSearch dead |
| County assessor/recorder | Web/API variable | Highly variable | Often delayed; aggregators lag |

*Rate-limit figures reflect 2026 documentation; always probe live endpoints before building a collector.*

## OSINT Workflow Integration

- **Pre-collection:** source discovery (registry → API → tier) resolves source before entity resolution.
- **Collection:** quota-conscious harvesting with retry/backoff and response caching; bulk mirroring for large refreshes.
- **Post-collection:** freshness metadata attached to each record for chain of custody and evidence preservation.
- **Monitoring:** real-time alerting on freshness-sensitive sources (court filings, SAM.gov awards); see [[real-time-osint-monitoring-alerting]].

## Cross-Domain Connections

- [[public-records-databases-osint]] — the source survey this page operationalizes
- [[entity-resolution]] — source-vs-entity resolution isomorphism from shared corpus
- [[anti-bot-evasion-fingerprinting]] — rate-limit evasion patterns overlap with scraping defenses
- [[data-breach-analysis-osint-identity-linkage]] — API automation patterns for breach lookup
- [[evidence-preservation-chain-of-custody-osint]] — freshness/provenance metadata
- [[web-archives-osint]] — archival freshness as bulk tier
- [[open-source-osint-tools-survey]] — tool ecosystem tiering
- [[real-time-osint-monitoring-alerting]] — freshness-driven alerting
- [[captcha-solving-2026-state-of-art]] — scraping-only access-tier friction
- [[corporate-registry-investigation-osint]] — multi-jurisdiction registry APIs

## References

1. OpenFEC API documentation — https://api.open.fec.gov/developers/
2. OpenFEC docs via Postman API Network (1,000/hr, 100/page, 7,200/hr elevated) — https://www.postman.com/api-evangelist/federal-election-commission-fec/documentation/
3. CourtListener REST API v4.4 overview — https://wiki.free.law/c/courtlistener/help/api/rest/v4/overview
4. Free Law Project — API included in memberships (2026-05-07) — https://free.law/2026/05/07/api-included-in-memberships/
5. data.gov API Developer Manual — https://api.data.gov/docs/developer-manual/
6. fecgov/openFEC GitHub — https://github.com/fecgov/openfec
7. Shared corpus: memory N9BsvHV5Xg (field report 20260527_osint-public-records-databases-apis.md)
8. Shared corpus: wiki page public-records-databases-osint.md (338 lines, 18 references)

## Verification Status

- Corpus-first grounding: strong — memory_load surfaced prior field reports and the public-records wiki page.
- 355-book library: not locatable at expected paths (/a0/usr/library, /a0/usr/workdir/library, etc.) — documented as a genuine environment gap.
- Web gap-fill: primary documentation consulted for OpenFEC/CourtListener/data.gov limits; claims to verify against live endpoints before production collectors.
