# Government Contracts Entity Resolution
**Status: STABLE**
**Created: 2026-06-03 | Last Updated: 2026-06-03**
**Domain: Data Aggregation & Entity Resolution | OSINT Investigation**

## Overview

Federal procurement data — over $600 billion annually in contracts — is a structured yet underexploited dataset for entity resolution and OSINT investigation. USASpending.gov and SAM.gov provide rich corporate linkage signals: Unique Entity Identifiers (UEI), parent-subsidiary relationships, NAICS codes, and ownership disclosures that can pierce corporate opacity when cross-referenced with other datasets (campaign finance, lobbying, property records).

## Key Data Sources

| Source | Description | API/Access |
|--------|-------------|------------|
| **USASpending.gov** | Federal procurement database tracking all contracts >$10,000; includes prime awards, subawards, grants | [REST API](https://api.usaspending.gov/docs/) with filtering, autocomplete |
| **SAM.gov** | System for Award Management — central vendor registration, UEI assignment, exclusion records | Entity Information API, ownership disclosure fields |
| **FPDS-NG** | Federal Procurement Data System Next Generation — raw transactional data | Accessible via USASpending.gov API |
| **State/local procurement databases** | Vary by jurisdiction; some expose open data APIs | Per-state portals |

## Entity Resolution Methods for Procurement Data

### 1. UEI-Based Deterministic Matching
- The Unique Entity Identifier (UEI), mandated by 2 CFR Part 25, supersedes DUNS numbers as of April 2022.
- SAM.gov records parent-subsidiary relationships via "Immediate Owner" and "Highest-Level Owner" fields.
- Multiple UEIs per corporate family: subsidiaries register separate UEIs, enabling hierarchical network reconstruction.

### 2. Name Normalization + Fuzzy Matching
- Award recipient names vary across agencies and fiscal years (LLC, Inc., Corp, abbreviations).
- USASpending ORM (`usaspending-orm` PyPI) provides Python object-relational mapping to standardize queries.
- Traditional pipeline: normalize → TF-IDF cosine similarity → Fellegi-Sunter probabilistic weighting.

### 3. SAM.gov Ownership Disclosure Analysis
- **Goodwin Law (Feb 2026)** details expanded SAM.gov ownership disclosure requirements: insight into federal spending patterns across affiliated entities, traceability of performance issues across corporate families, physical location of leadership, and corporate-wide supply chain integrity.
- Ownership data fields include: immediate owner CAGE/UEI, highest-level owner CAGE/UEI, total employee count, and physical addresses.

### 4. Agentic Pipelines
- **PlatypusVenom604/codex-contract-research** (GitHub, 2026): agentic federal contract research pipeline combining USASpending.gov data extraction, entity resolution, financial enrichment, and Excel/brief output.
- Pattern: crawl contract awards → resolve recipient entities across agencies → enrich with financial data → produce structured intelligence products.

### 5. LLM-Assisted Entity Resolution
- LLM-based string matching for company name normalization across procurement databases, with prompts that incorporate industry knowledge (NAICS codes, set-aside designations).
- Hybrid approach: deterministic UEI matching for known entities, LLM semantic matching for unknown/shell entities with fuzzy names.

## Investigation Workflow

1. **Collect**: Query USASpending.gov API for contracts matching agency/program/timeframe.
2. **Normalize**: Extract recipient names, UEIs, parent/highest-level owner fields.
3. **Resolve**: Cross-reference with SAM.gov entity information, OpenCorporates, state business registries.
4. **Link**: Connect to FEC campaign finance (donor employers), lobbying disclosures (LD-1/LD-2), and property records.
5. **Enrich**: Add financial data (Dun & Bradstreet, CAGE codes, NAICS), exclusion/debarment status.
6. **Visualize**: Graph networks of parent-subsidiary-contract-award relationships.

## Cross-Domain Connections

- **Campaign Finance Donor Analysis**: Government contractors are major political donors — USASpending-to-FEC linkage reveals "pay-to-play" patterns.
- **Lobbying Disclosure Cross-Referencing**: LD-1/LD-2 filings name the specific agencies and programs being lobbied; procurement data shows contract awards to lobbyists' clients.
- **Property Records Investigation**: Corporate real estate holdings often linked to government contract performance locations.
- **Data Aggregation & Entity Resolution**: The procurement-to-ownership pipeline is a variant of the general heterogeneous data integration problem.
- **LLM-Assisted Entity Resolution**: Fuzzy name matching across procurement systems benefits from LLM-based semantic matching where deterministic UEI matching fails.
- **Intelligence Failure Analysis**: Stovepiped procurement data without cross-agency entity resolution is structurally analogous to pre-9/11 intelligence sharing failures (agencies had data but couldn't connect entities).
- **Anti-Bot Evasion / OSINT Operations**: USASpending.gov API has rate limits; programmatic scraping requires respectful automation patterns.

## Limitations & Challenges

- **UEI rollout incomplete**: Legacy DUNS numbers persist in older data; migration ongoing.
- **Subsidiary opacity**: Ownership fields rely on self-reported SAM.gov data; shell layers require cross-referencing.
- **API rate limits**: USASpending.gov imposes request limits; bulk downloads recommended for large-scale ER.
- **Jurisdictional fragmentation**: State/local procurement data not unified; multi-jurisdiction ER requires separate integrations.

## References

1. USASpending.gov API Documentation — https://api.usaspending.gov/docs/
2. USASpending ORM — https://pypi.org/project/usaspending-orm/
3. SAM.gov Entity Information — https://sam.gov/entity-information
4. SAM.gov Ownership Disclosures — Goodwin Law, Feb 2026 — https://www.goodwinlaw.com/en/insights/publications/2026/02/alerts-practices-sam-gov-ownership-disclosures
5. 2 CFR Part 25 — Unique Entity Identifier and System for Award Management — https://www.ecfr.gov/current/title-2/subtitle-A/chapter-I/part-25
6. PlatypusVenom604/codex-contract-research — https://github.com/PlatypusVenom604/codex-contract-research
7. USASpending.gov Analytics — Loading Data into Dask and Pandas — https://lulstrup.medium.com/4-usaspending-gov-analytics-loading-data-into-dask-and-pandas-3e83af441901
