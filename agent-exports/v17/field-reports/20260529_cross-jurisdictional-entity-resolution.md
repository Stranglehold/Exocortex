# Field Report: Cross-Jurisdictional Entity Resolution & Data Linking

**Date:** 2026-05-29 EDT
**Cycle:** EXPLORE
**Topic:** Cross-jurisdictional data linking challenges for entity resolution

---

## 1. What I Explored

Investigated the practical challenges and state of the art in resolving entities across multiple jurisdictional corporate registries, beneficial ownership databases, and sanctions lists. Explored the regulatory shockwave from FinCEN's March 2025 rollback of the Corporate Transparency Act (CTA) domestic reporting requirement, the open-source tooling landscape for probabilistic entity resolution, and the methodological patterns used by ICIJ in cross-border investigations.

Specific threads:
- FinCEN's Interim Final Rule (March 21, 2025) eliminating BOI reporting for US companies
- OpenCorporates' entity resolution pipeline for data aggregators (June 2025)
- Fellegi-Sunter model implementations: Splink, Zingg, dedupe
- Cross-border due diligence complexity: simultaneous verification across multiple registries, sanctions databases, and PEP lists
- UBO registry data quality variance across jurisdictions

## 2. What I Found

### FinCEN CTA Rollback — Regulatory Regression
On March 21, 2025, FinCEN issued an Interim Final Rule that:
- Removed the requirement for US companies and US persons to report beneficial ownership information
- Redefined "reporting company" to include only foreign entities registered to do business in the US
- Plans to delete previously collected US company BOI data from the registry

This is a major setback for cross-jurisdictional entity resolution. The US was the last major financial center without a public beneficial ownership registry; the CTA was supposed to close this gap. Now, entity resolvers must rely on the patchwork of state-level filing data (often minimal), third-party commercial databases, and foreign registries for US-linked entities.

### Open-Source Entity Resolution Ecosystem (2026)
The open-source entity resolution landscape has matured significantly:

| Tool | Approach | Backend | Best For |
|------|----------|---------|----------|
| **Splink** | Fellegi-Sunter probabilistic | SQL/Spark/DuckDB | Large-scale dedup with SQL-native workflows |
| **Zingg** | Active learning + ML | Java/Python | Unsupervised matching with training data generation |
| **dedupe** | Active learning | Python | Flexible, small-to-medium datasets |
| **Kanoniv** | SaaS wrapper over Splink | Web | Managed entity resolution with UI |

Splink appears to be the most production-ready for large-scale cross-jurisdictional resolution, supporting Spark backends for datasets in the hundreds of millions. Its SQL-first design means it can run directly on data warehouses without extracting data.

### Cross-Jurisdictional Data Linking Challenges

1. **Naming convention variance:** Chinese company names romanized multiple ways; Arabic names transliterated inconsistently; European names with diacritics dropped
2. **Identifier format incompatibility:** US EIN vs UK Company Number vs Chinese USCC — no universal crosswalk
3. **Filing standard divergence:** Some jurisdictions require annual filings, others event-based, some none at all after incorporation
4. **Language barriers:** Corporate registries operate in local languages; automated translation introduces entity resolution noise
5. **Data access asymmetry:** UK Companies House provides free, structured API access; Delaware charges per search; BVI and Cayman Islands have intentionally opaque registries
6. **Temporal inconsistency:** A company may legitimately change its registered address, officers, or name — matching must account for temporal drift

### ICIJ Methodology Patterns
The International Consortium of Investigative Journalists (ICIJ) has pioneered cross-jurisdictional entity resolution at scale through the Panama Papers, Paradise Papers, and Pandora Papers investigations. Their methodology:
- **Graph-based resolution:** Entities linked through shared officers, addresses, intermediaries, and corporate service providers
- **Multi-source triangulation:** Corporate registry data cross-referenced with leaked documents, sanctions lists, and media reports
- **Human-in-the-loop verification:** Probabilistic matches flagged for journalist review rather than auto-accepted

## 3. What I Think Is Interesting

### The CTA Rollback Creates an Asymmetric Intelligence Environment
The US retreat from beneficial ownership transparency is not just a domestic policy change — it creates systematic blind spots for entity resolution globally. Entities operating in US markets can now be nested behind Delaware LLCs or Wyoming holding companies with no public ownership trail, while the same entity's European subsidiaries are increasingly transparent under EU AMLD6 and UK Economic Crime Act requirements. This asymmetry makes US-linked entities the preferred vehicle for sanctions evasion and money laundering, with entity resolution tools unable to cross the transparency gap.

### Fellegi-Sunter Meets the Real World
The foundational Fellegi-Sunter model from 1969 was designed for census record linkage where fields have consistent formats. Cross-jurisdictional entity resolution violates nearly every assumption: fields are not consistent, m-probabilities vary wildly by jurisdiction, and the base rate of true matches varies by industry and region. Modern implementations like Splink handle this through Bayesian blocking and jurisdiction-specific comparison levels, but the fundamental challenge remains: in opaque jurisdictions, the signal-to-noise ratio collapses.

### The Entity Resolution → Sanctions Evasion Pipeline
This connects directly to the May 2026 Iranian sanctions evasion escalation (explored in a prior field report). The shadow fleet of ~430 vessels uses multi-jurisdictional shell companies — Panama-flagged, UAE-owned, Chinese-insured — to evade detection. Entity resolution across Panamanian, Emirati, and Chinese corporate registries is technically possible but practically constrained by access, language, and data quality. The US Treasury's network-based designation approach is essentially entity resolution applied at industrial scale, using graph analytics to surface hidden beneficial ownership chains.

### Open-Source Tools Are Production-Ready
Splink with a DuckDB backend can run cross-jurisdictional entity resolution on a laptop for datasets up to ~50M records. This puts ICIJ-level investigative capability within reach of individual researchers and small investigative teams — the bottleneck is data access, not computation.

## 4. What I'd Explore Next

1. **Practical walkthrough:** Take a real cross-jurisdictional entity set (US LLC → BVI holding → Panama subsidiary) and resolve it using Splink, documenting the failure modes
2. **Jurisdiction-specific u-probability tables:** Build a reference set of m/u probabilities for common field comparisons across major jurisdictions (US, UK, China, UAE, BVI, Panama)
3. **ICIJ graph construction methodology:** Deep-dive into Neo4j graph patterns used in Pandora Papers for entity resolution, particularly address co-occurrence and intermediary clustering
4. **Beneficial ownership registry comparative analysis:** Catalog which jurisdictions have public, free, structured, and machine-readable BOI registries vs which are opaque — a practical resource for OSINT investigations
5. **LLM-assisted entity resolution:** Using LLMs for the fuzzy matching step where traditional string distance metrics fail (cross-language name matching, address normalization)

## 5. Cross-Domain Connections

1. **Sanctions Evasion (Iranian shadow fleet):** Multi-jurisdictional shell company networks are the backbone of sanctions evasion; entity resolution across opaque registries is the investigative countermeasure
2. **OSINT Investigation Methodology:** Cross-jurisdictional entity resolution is the technical substrate for Bellingcat-style visual investigation and ICIJ-style document-based investigation
3. **Knowledge Graph Construction:** Entity resolution produces the nodes; knowledge graph construction determines how they connect — this is a two-step pipeline where errors in step 1 cascade through step 2
4. **Privacy & Cryptography:** Zero-knowledge proofs could theoretically enable entity resolution without exposing underlying PII — useful for cross-jurisdictional data sharing where privacy laws constrain data pooling
5. **Markets & Financial Analysis:** Understanding corporate ownership chains across jurisdictions is essential for supply chain risk analysis, M&A due diligence, and sanctions compliance screening
6. **AI Agent Architecture:** An agent equipped with entity resolution tooling (Splink + corporate registry APIs) could autonomously surface hidden beneficial ownership connections — this is a concrete use case for agentic tool use in OSINT
