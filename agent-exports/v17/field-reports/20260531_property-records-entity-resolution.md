# Field Report: Property Records as Entity Resolution Data Source
**Date:** 2026-05-31
**Cycle:** EXPLORE — Data Aggregation & Entity Resolution
**Topic thread:** How property/real estate records can resolve entities and surface hidden corporate-individual-property connections

---

## 1. What I Explored

The intersection of property records and entity resolution: using county assessor databases, state corporate registries, and cross-border company registries to trace the true beneficial owners behind real estate holdings. This sits at the convergence of three existing threads in Jake's research agenda: entity resolution methodology, OSINT public records investigation, and financial/markets analysis.

I focused on the post-CTA landscape (March 2025 onward), where the Corporate Transparency Act's beneficial ownership reporting was effectively gutted for domestic entities, making autonomous entity resolution more necessary rather than less.

---

## 2. What I Found

### 2.1 Regulatory Context: CTA Rollback & Fragmentation

**Timeline of key events:**
- **March 2025:** FinCEN interim final rule exempted all U.S.-formed entities from beneficial ownership reporting under the Corporate Transparency Act. Only foreign-formed entities registered in the U.S. must file.
- **January 2026:** New York's LLC Transparency Act took effect in weakened form — covers only foreign-formed LLCs registered in NY.
- **March 1, 2026:** FinCEN's Residential Real Estate Rule went live — settlement agents must report all-cash residential transfers to entities or trusts. But it only covers residential, only non-financed deals, and reports aren't publicly searchable.

**The bottom line:** For domestic LLCs holding U.S. real estate — the vast majority of entity-owned property — no database hands you the beneficial owner. You build the chain yourself.

### 2.2 The Property-to-Person Chain-Walking Methodology

Synthesized from Zephira.ai's 2026 guide and OpenCorporates analysis:

**Step 1 — Start at the Property:**
- Search county assessor by address or use aggregated APIs (ATTOM, CoreLogic, First American)
- Extract: entity name on deed, mailing address, transfer date/price, grantor (prior owner)
- Key clue: a mailing address of "1209 Orange Street, Wilmington, DE" signals the Corporation Trust Company (registered agent for 285,000+ entities) → LLC is Delaware-formed

**Step 2 — Search the State Registry:**
- Use OpenCorporates API (aggregates 140+ registries) or direct state lookups
- **Disclosure-friendly states:** Florida (sunbiz.org — officers, managers, members by name), California, Nevada, New York
- **Opaque states:** Delaware (name, formation date, status, registered agent — nothing else), Wyoming, New Mexico

**Step 3 — Walk the Ownership Chain:**
- A manager is often another LLC → look up that LLC → repeat until a natural person or a dead end
- Example of success: Miami property → FL LLC → DE LLC (foreign registration reveals UK parent) → UK Companies House PSC register → John Smith, 75-100% ownership
- Common failure mode: Florida LLC → Delaware LLC (no foreign registrations) → dead end

**Step 4 — Cross Borders:**
- UK Companies House PSC (Persons with Significant Control) register: the gold standard — free API, every company must disclose ultimate beneficial owners with ownership percentages
- Other cooperative jurisdictions exist but most U.S. opaque-state LLCs won't have foreign parentage

### 2.3 Scale of the Problem

- 30% of high-value all-cash real estate deals flagged by FinCEN involve shell companies with beneficial owners already in prior Suspicious Activity Reports
- $18-22 trillion total U.S. commercial real estate stock value
- $1.2 trillion CRE debt coming due in 2024-25, forcing lenders to stress-test collateral → ownership transparency now has financial materiality
- Lincoln Institute of Land Policy: corporations now own 8.9% of residential parcels across 500 U.S. counties
- 3,100+ counties and independent cities each with their own data format, update frequency, and quality standards

### 2.4 Tool Landscape

- **OpenCorporates API:** Aggregates 140+ registries; free tier for basic entity data, paid for officers/filings
- **ATTOM / CoreLogic / First American:** Aggregated property data APIs for bulk county-level lookups
- **OSINT-Tools_USA (GitHub: paulpogoda):** Curated list of U.S. government databases organized by OSINT-for-Countries framework
- **PropertyShark:** Commercial property owner identification tool

---

## 3. What I Think Is Interesting

### 3.1 CTA Rollback as a Structural Forcing Function

The CTA rollback didn't reduce the need for entity resolution — it increased it. When beneficial ownership data was expected to flow into a centralized database, commercial tools could query it. Now that domestic entities are exempt, the work shifts to autonomous chain-walking across heterogeneous registries. This is the exact problem Jake's entity resolution research agenda targets.

### 3.2 State-Level Transparency as a Natural Experiment

The 50 states form a gradient of disclosure quality: Florida (full officers/members) → California/Nevada/New York (partial) → Delaware/Wyoming/New Mexico (zero). This makes U.S. entity resolution an inherently multi-jurisdictional problem where success depends on finding the weakest link in the chain (a Florida registration, a UK subsidiary, a California foreign qualification filing).

### 3.3 Mailing Address as Side-Channel Signal

The registered agent address as a state-formation indicator is a clever side channel. "1209 Orange Street, Wilmington, DE" is a signal, not the answer. This pattern — using metadata artifacts rather than declared fields — is structurally similar to email header analysis and domain WHOIS investigation, both active interests in Jake's research agenda.

### 3.4 The UK Companies House PSC Register as Model Infrastructure

The UK PSC register demonstrates what functional beneficial ownership registry looks like: free API, mandatory disclosure, ownership percentages, publicly searchable. It's the benchmark against which the U.S. system's opacity is measured.

---

## 4. What I'd Explore Next

1. **Automated chain-walking:** Build a script that takes a property address, queries county assessor, identifies entity, searches OpenCorporates API, detects "is this a Delaware entity?" → searches for foreign qualifications → repeats until person or dead end. The Zephira guide provides pseudocode.

2. **Graph-based ownership network detection:** Apply temporal graph neural networks (already explored in cycle: temporal-graph-networks-financial-entity-resolution) to link property ownership to sanction evasion, money laundering, or political influence networks.

3. **Commercial real estate as geopolitical intelligence:** Track which foreign sovereign wealth funds/nation-states are accumulating U.S. real estate through LLC shells, linking to existing geopolitical threads (Iranian sanctions evasion, Chinese capital flight through real estate).

4. **County-level data aggregation:** Investigate automated ingestion of county assessor data at scale — 3,100+ counties with inconsistent schemas is a classic entity resolution problem.

5. **OSINTBay PERSINT methodology:** Deeper dive into their framework — property deeds as one node in a broader public records investigation (court dockets, corporate registries, voter rolls, marriage certificates).

---

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **OSINT & Investigation Methodology** | Property records are a canonical public records OSINT source; the chain-walking methodology maps directly to broader OSINT investigation patterns |
| **Markets & Financial Analysis** | $1.2T CRE refinancing wave makes ownership transparency financially material; corporate ownership of residential parcels (8.9%) has housing affordability implications |
| **Geopolitics & Strategic Analysis** | Foreign entities accumulating U.S. real estate through shell LLCs is a national security concern; CTA's foreign-entity reporting requirement signals this priority |
| **Privacy & Cryptography** | The CTA rollback represents a policy choice favoring privacy (LLC owners remain anonymous) over transparency; the UK PSC register shows the opposite choice — this is a privacy-vs-transparency tension |
| **AI Agent Architecture** | Automated chain-walking across heterogeneous registries is structurally isomorphic to the tool-use delegation patterns in agent architectures — each registry is a "tool" with different capabilities |
| **History of Intelligence Operations** | The Venona Project's manual entity resolution (cryptonym-to-identity pipeline) is the historical precursor to automated property record chain-walking — both involve resolving partial identifiers across fragmented data sources |

---

## Sources

1. OpenCorporates Blog, "Why Unmasking Corporate Property Ownership Is the Next Frontier for Commercial Real Estate Data," August 2025
2. Zephira.ai, "Who Really Owns That Property? How to Trace Real Estate LLC Ownership in 2026"
3. Lincoln Institute of Land Policy & Center for Geospatial Solutions, "Who Owns America: Mapping Corporate Ownership of Residential Land," January 2026
4. FinCEN Residential Real Estate Rule, effective March 1, 2026
5. OpenCorporates API documentation (v0.4)
6. OSINT-Tools_USA GitHub repository (paulpogoda)
7. OSINTBay, "PERSINT Public Records: The OSINT Operator's Guide to Court, Corporate & Government Filings"
