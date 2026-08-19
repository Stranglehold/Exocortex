# Corporate Registry Analysis for Entity Resolution

**Status: STABLE**  
**Domain:** Data Aggregation & Entity Resolution  
**Deepened:** 2026-06-04  
**Lines:** ~195 | **Sources:** 12 (+2 primary APIs)

---

## Overview

Corporate registries — Secretary of State business filings, Companies House (UK), international commercial registers, and beneficial ownership registries — are foundational OSINT data sources for entity resolution. They provide legal name, registered address, agent/officer data, formation date, and jurisdiction identifiers that serve as anchor points for cross-dataset identity matching. Unlike campaign finance or government contracts data, corporate registries operate at the entity-formation layer: they are the canonical source of truth for a legal entity's existence, making them the first step in any multi-source entity resolution pipeline.

## Registry Landscape

### US Secretary of State System

The US operates a fragmented state-level registry system with 50+ jurisdictions (50 states + DC + territories), each maintaining its own database with varying:
- **Data availability:** Some states provide full company record downloads (DE, WY, NV); others require per-record lookups
- **API access:** Limited — no federal standard; OpenCorporates aggregates from state sources but coverage varies
- **Key fields:** Entity name, formation date, registered agent, principal address, status (active/inactive/dissolved)
- **Beneficial ownership:** FinCEN Corporate Transparency Act (CTA) beneficial ownership registry rollout was paused in March 2025; state-level BO disclosure remains inconsistent

**Wyoming, Delaware, Nevada** are notable for their high-volume LLC formations and minimal disclosure requirements — Wyoming had a single address used by hundreds of shell companies to fraudulently obtain pandemic relief funds (Esquire investigation using OpenCorporates data).

### Companies House (UK)

The UK's Companies House is an open-data pioneer — all public company data is freely accessible via REST API with:
- **Real-time API:** Live company profiles, officer/disqualified-director searches, filing history, persons with significant control (PSC)
- **Bulk data:** Full snapshot downloads available for large-scale processing
- **Key advantage:** PSC register provides beneficial ownership transparency rarely available in US state registries
- **MCP integration:** Community-maintained MCP server (stefanoamorelli/companies-house-mcp) enables programmatic agent access
- **Rate limits:** 600 requests per 5 minutes for unauthenticated access; higher with API key

### OpenCorporates

OpenCorporates is the world's largest open legal-entity database, aggregating data from **147 jurisdictions** across:
- **230M+ companies** and **380M+ officers** in database
- **2B+ rows** of data on companies worldwide
- **Sourced directly from primary government registries** — not scraped, but ingested from official sources
- **Seven Legal-Entity Data Principles** anchor the platform's commitment to provenance and quality
- **API access:** REST API with company search, officer search, corporate grouping, and statement data
- **Impact:** Used in Pandora Papers, Panama Papers, and COVID relief fraud investigations; >900 academic publications

### Global Legal Entity Identifier (GLEIF)

The Global LEI System provides unique 20-character identifiers for legal entities participating in financial transactions. Unlike commercial registries, the LEI:
- Is globally unique and jurisdiction-agnostic
- Includes direct/ultimate parent relationship data
- Is mandated for financial market participants under MiFID II, Dodd-Frank, and EMIR
- Provides free API access to the complete LEI database

### Other Notable Registries

| Registry | Jurisdiction | Key Feature |
|----------|-------------|-------------|
| OCCRP ID | Multi-jurisdictional | Investigative database with historic company extracts |
| OpenSanctions | Global | Sanctions + PEP + corporate registry consolidation |
| EU Business Registers (BRIS) | EU-wide | Cross-border company data exchange |
| Dun & Bradstreet D-U-N-S | Global | Proprietary but widely used for commercial ER |

### Registry Access Comparison

| Dimension | US SoS | Companies House | OpenCorporates | GLEIF |
|-----------|--------|----------------|----------------|-------|
| API | Fragmented (per-state) | Full REST | Full REST | Full REST |
| Bulk data | Rare | Yes (snapshots) | No (API only) | Yes (daily) |
| Beneficial ownership | Weak (CTA paused) | Strong (PSC register) | Aggregated from sources | Parent relationships |
| Free tier | Varies by state | Unlimited | Rate-limited | Unlimited |
| Unique ID | State filing number | Company number (8 digits) | OpenCorporates ID | LEI (20 chars) |

## Investigation Methods

### Registry Lookup Workflow

1. **Initial identification:** Start with entity name from any source (news article, contract award, campaign filing)
2. **Jurisdiction determination:** Identify likely incorporation jurisdiction from address, industry, or regulatory context
3. **Primary registry lookup:** Query state/country registry for legal entity details
4. **Officer extraction:** Extract directors, officers, registered agents for subsequent person-level investigation
5. **Related entity discovery:** Use shared officers/addresses to surface connected entities
6. **Cross-registry validation:** Verify across multiple registries and aggregated databases

### Cross-Jurisdictional Challenges

Corporate registries exhibit significant structural heterogeneity:
- **Naming conventions:** Different legal suffixes (Ltd, LLC, GmbH, SARL, K.K., OY) complicate fuzzy matching
- **Identifier systems:** No universal company identifier exists across jurisdictions; LEI partially fills this gap
- **Language barriers:** Non-Latin scripts (Chinese, Arabic, Cyrillic) require transliteration normalization
- **Data freshness:** Update cadences vary from daily to annual; dissolved entities may persist in records
- **Access asymmetry:** Some jurisdictions charge per-record fees; others restrict bulk access

### Automation Approaches

- **OpenCorporates API + Python (opyncorporates):** Programmatic company/officer search across 147 jurisdictions
- **Companies House MCP:** Agent-native access to UK registry data
- **OCCRP ID bulk extracts:** Investigative-grade datasets for cross-border shell company detection
- **Web scraping:** For state registries without APIs (requires anti-bot evasion — see [[anti-bot-evasion]])

## Entity Resolution Integration

### Registry Data as Blocking Keys

Corporate registry data provides high-precision blocking keys that dramatically reduce the ER search space:

| Blocking Key | Precision | Coverage | Notes |
|-------------|-----------|----------|-------|
| Company number | Very high | Jurisdiction-scoped | Perfect when available; cross-jurisdiction breaks down |
| LEI | Very high | Global (financial entities) | Best universal key; limited scope to financial sector |
| Tax ID (EIN/VAT) | High | Jurisdiction-scoped | Non-public in many jurisdictions |
| Registered address | Medium | Local | Suffers from registered-agent address reuse |
| Officer name + jurisdiction | Medium | Cross-dataset | Bridges corporate-to-person investigation |

### Comparison Features

When exact identifiers are unavailable, registry data feeds into fuzzy entity resolution through:
- **Name similarity:** Jaro-Winkler or Levenshtein distance on entity names, normalized for legal suffixes
- **Address matching:** Geocoded address comparison with tolerance for suite/unit variations
- **Officer overlap:** Shared directors/officers as strong signal for related entities
- **Formation date proximity:** Temporal clustering for incorporation-farm detection

### Pipeline Integration Pattern

```
Source Documents → Registry API Lookup → Blocking (company number / jurisdiction)
    → Candidate Pair Generation → Comparison (fuzzy name + address + officers)
    → Classification (rule-based → probabilistic → LLM) → Clustering → Entity Graph
```

Integration with existing wiki pages:
- **[[cross-jurisdictional-entity-resolution]]** — Fellegi-Sunter probabilistic framework for cross-border registry matching
- **[[open-source-entity-resolution-frameworks]]** — Splink, Zingg, dedupe integration with registry data
- **[[llm-assisted-entity-resolution]]** — LLM-based matching for multilingual entity names from non-Latin registries
- **[[government-contracts-entity-resolution]]** — USASpending.gov / SAM.gov entity linkage using DUNS/UEI identifiers
- **[[campaign-finance-donor-analysis]]** — Corporate donor identification through registry cross-referencing
- **[[data-breach-analysis-identity-linkage]]** — Corporate email domains linked to registry data for breach attribution

### Exocortex Architecture Mapping

| Registry Analysis Function | Exocortex Component |
|---------------------------|---------------------|
| Multi-source registry query | call_subordinate (parallel agents per jurisdiction) |
| Entity name normalization | deterministic-scaffolding (rule-based preprocessing) |
| Fuzzy matching across registries | LLM-assisted entity resolution (semantic matching) |
| Source reliability assessment | epistemic-integrity (evidence ledger per registry) |
| Multi-INT fusion with other data types | knowledge-graph-construction (cross-source entity links) |
| Jurisdiction selection triage | BST classifier (domain detection for jurisdiction routing) |

## Structural Patterns & Cross-Domain Connections

### 1. Multi-Jurisdictional Fragmentation → Multi-Agent Coordination

The US 50-state registry fragmentation is structurally isomorphic to the multi-agent coordination problem: each registry is an independent "agent" with different schemas, and entity resolution must reconcile their partial, overlapping views into a unified entity graph — the same problem as multi-agent belief reconciliation.

### 2. Beneficial Ownership Opacity → Adversarial AI Deception

The gap between legal entity registration and beneficial ownership is structurally isomorphic to the gap between an AI agent's stated reasoning and its actual decision process. Shell companies conceal true owners just as confabulated reasoning conceals actual decision drivers (→ [[adversarial-ai-agent-manipulation]]).

### 3. Registry Data Freshness → Agent Knowledge Staleness

Corporate registries update on different cadences (daily to annual), creating temporal inconsistencies across sources. This maps directly to the context staleness problem in agent memory architecture: different memory tiers (episodic, semantic, procedural) have different freshness guarantees (→ [[agent-memory-architecture]], [[proactive-interference]]).

### 4. OpenCorporates Aggregation → Exocortex Knowledge Graph

The OpenCorporates model — ingest from 147 primary sources, normalize schemas, provide unified query interface — is the entity resolution equivalent of Exocortex's knowledge graph construction: heterogeneous source ingestion, schema normalization, and unified cross-source query.

### 5. Registry-as-Ground-Truth → Epistemic Integrity

Corporate registries, when directly sourced, provide a canonical ground truth — analogous to the role of [[epistemic-integrity]] in verifying LLM claims against evidence ledgers. The registry is to entity resolution what the evidence ledger is to agent reasoning: an external, verifiable anchor.

### 6. PSC Register Model → AI Transparency Architecture

The UK's Persons with Significant Control register demonstrates that beneficial ownership transparency is technically feasible when mandated. This maps to the AI transparency problem: it's not technically difficult to log decision traces — it's a question of architectural will (→ [[intelligence-oversight-accountability-history]]).

### 7. Registry Access Asymmetry → Tool Access Control

The fragmented API landscape (some registries open, some paywalled, some no-API) mirrors the tool access control problem in agent architecture: different tools have different availability, rate limits, and reliability guarantees (→ [[agentic-tool-use-schema-optimization]]).

## References

### Primary Sources
1. OpenCorporates. "15 Years of Corporate Transparency: The Ultimate Resource List." December 2025. https://blog.opencorporates.com/2025/12/10/15-years-of-corporate-transparency-the-ultimate-resource-list/
2. OpenCorporates. "Data Duplicates Are Costing You Millions: Entity Resolution for Data Aggregators." June 2025. https://blog.opencorporates.com/2025/06/17/entity-resolution-for-data-aggregators/
3. Companies House. "API Overview." https://developer.company-information.service.gov.uk/overview/
4. Companies House MCP Server. GitHub. https://github.com/stefanoamorelli/companies-house-mcp
5. GLEIF. "Global LEI System." https://www.gleif.org/
6. Wikipedia. "List of Official Business Registers." https://en.wikipedia.org/wiki/List_of_official_business_registers
7. Esquire. "Wyoming Appears to Be in the Middle of an Economic Boom—of Corporate Malfeasance" (via OpenCorporates data).
8. ICIJ. "Millions in Covid Relief Funds Went to Shadowy Companies Registered at a Wyoming Storefront." Pandora Papers investigation (via OpenCorporates data).
9. UC Berkeley. "Limited Liability, Full Anonymity: LLCs as Dark Money Vessels" (via OpenCorporates data).
10. UCLA. "The Corporate Census — Examining Corporate Ownership Patterns" (via OpenCorporates data).
11. OCCRP ID. "Catalogue of Research Databases." https://id.occrp.org/databases/
12. OpenSanctions. "LLMs, Entity Resolution, Narrative Matching." May 2026. https://www.opensanctions.org/articles/

### Cross-Referenced Wiki Pages
- [[cross-jurisdictional-entity-resolution]]
- [[open-source-entity-resolution-frameworks]]
- [[llm-assisted-entity-resolution]]
- [[government-contracts-entity-resolution]]
- [[campaign-finance-donor-analysis]]
- [[data-breach-analysis-identity-linkage]]
- [[domain-whois-dns-investigation]]
- [[public-records-databases-osint]]
- [[intelligence-oversight-accountability-history]]
- [[adversarial-ai-agent-manipulation]]
- [[agent-memory-architecture]]
- [[anti-bot-evasion]]
- [[agentic-tool-use-schema-optimization]]
