# Supply Chain & Economic Warfare

**Status:** STABLE
**Created:** 2026-05-20 | **Last deepened:** 2026-05-20
**Interest:** Supply Chain & Economic Warfare
**Cross-domain:** Geopolitics, Markets, Entity Resolution, OSINT

Analysis of economic coercion as a strategic instrument — sanctions design, export controls enforcement, rare earth supply chain dependencies, and the financial infrastructure of economic warfare. Six subdomains populated with primary-source research and Exocortex cross-references.

---

## 1. Sanctions Design & Effectiveness

### 1.1 Theory of Economic Coercion

The theory of economic coercion rests on the premise that restricting a target state's access to global markets, technology, and financial infrastructure will alter its behavior. In practice, effectiveness is contested. A 2024 Chatham House conference on sanctions identified three critical fallacies: (1) lack of clear terminology for "effectiveness," (2) continued reliance on behavioral change as the primary measure of success, and (3) neglect of how sanctions accelerate economic fragmentation and alternative financial infrastructure (Sabatini & Isard, 2025).

**Key theoretical frameworks:**
- **Hufbauer-Schott-Elliott (1990, 3rd ed. 2007):** Foundational database of 204 sanctions episodes. Core finding: sanctions "succeed" in only 34% of cases. Success correlates with modest goals, strong multilateral cooperation, and economic asymmetry favoring the sender.
- **Pape (1997) critique:** Disputed HSE methodology — argued that sanctions almost never achieve major political goals alone.
- **Biersteker et al. (2016, *Targeted Sanctions*):** Shift from comprehensive to targeted/smart sanctions reduces humanitarian cost but creates new evasion dynamics.

### 1.2 The Russian Sanctions Regime (2022-2026)

The post-2022 sanctions regime against Russia is the most comprehensive in history — SWIFT disconnection of major banks, G7 oil price cap ($60/bbl), technology export controls, and ~1,900 individual/entity designations. Brookings (September 2024) analysis found measurable economic contraction but questioned whether the political objective — compelling withdrawal from Ukraine — was achieved.

**MIT CEEPR 2025 Price Cap Dynamic Equilibrium Model (Kilian, Rapson & Schipper):** The G7 Russian oil price cap revealed a perverse outcome: lowering the cap to $0 paradoxically *increases* Russian profits in certain scenarios because Russia can choose to sell the marginal barrel rather than shut in production. The model demonstrates that sanctions design must account for multi-parameter strategic response curves.

**Shadow fleet economics:** Approximately 600 aging tankers with opaque ownership structures, non-Western insurance, and flag-of-convenience registration transport 60-70% of Russian crude exports, effectively bypassing the G7 maritime services leverage.

### 1.3 Sanctions Evasion Vectors

| Vector | Mechanism | Detection Difficulty |
|--------|-----------|---------------------|
| Shell company nesting | Multi-jurisdictional corporate structures with nominee directors | High — requires entity resolution across registries |
| Trade-based money laundering | Misinvoicing, phantom shipments, over/under-shipment | High — requires mirror statistics analysis |
| Crypto obfuscation | Mixers, chain-hopping, privacy coins | Medium — blockchain transparent but attribution hard |
| Third-country transshipment | UAE, Turkey, Central Asian states relabel sanctioned goods | Medium — trade data anomalies detectable |
| Maritime deception | AIS spoofing, ship-to-ship transfers, flag hopping | Medium — satellite imagery + AIS gap analysis |

### 1.4 Sanctions Enforcement and Detection

- **OFAC SDN List:** CNAS "Sanctions by the Numbers 2024 Year in Review" reported over 3,000 new designations in 2024 alone.
- **Paul Weiss 2025 Year in Review:** Key trends: expansion of secondary sanctions, FinCEN beneficial ownership registry (Corporate Transparency Act), AML/CFT integration with sanctions enforcement.
- **Detection methodology:** Entity resolution across corporate registries (OpenCorporates, ICIJ Offshore Leaks), trade data (UN Comtrade mirror statistics), shipping data (AIS vessel tracking), and sanctions lists (OFAC, UN, EU, UK consolidated lists).

---

## 2. Export Controls & Semiconductor Supply Chain

### 2.1 US-China Technology Competition

The semiconductor supply chain represents the most strategically concentrated industrial ecosystem in modern history. Taiwan produces 90%+ of the world's most advanced semiconductors (<7nm). This "silicon shield" creates both a deterrent and a critical vulnerability.

**Export Control Architecture (2025-2026):**
- **MATCH Act (cleared committee April 2026):** Would *require* US allies (Japan, Netherlands) to align with US restrictions on advanced semiconductor equipment exports to China, specifically targeting ASML's DUV immersion lithography. Scaled back from broader drafts (Reuters, April 2026).
- **Commerce Department waiver revocation (September 2025, CNBC):** Waivers allowing TSMC, Samsung, SK Hynix to import US-made equipment into their China fabs being revoked.

### 2.2 Chip Fabrication Geography

| Entity | Location | Capability | Constraint |
|--------|----------|-----------|------------|
| TSMC | Taiwan (90%+ <7nm); Arizona | Monopoly on advanced logic | Political risk; Arizona higher cost |
| Samsung | South Korea; Texas | 3nm GAA in production | Smaller foundry market share |
| Intel | US, Ireland, Israel | 18A (2nm eq.) by 2025 | Struggling for external foundry customers |
| SMIC | China | 7nm via DUV multi-patterning | Blocked from EUV; expensive, low yield |

### 2.3 Equipment Restrictions

| Maker | Country | Specialty | Export Restriction |
|-------|---------|-----------|--------------------|
| ASML | Netherlands | EUV monopoly; DUV lithography | EUV banned since 2019; DUV under MATCH Act |
| Tokyo Electron | Japan | Etch and deposition | Japanese controls since July 2023 |
| Lam Research | US | Etch and deposition | US restrictions since Oct 2022 |
| Applied Materials | US | Deposition, CMP, inspection | US restrictions |

**SMIC 7nm via DUV multi-patterning:** Achieved using ASML DUV immersion with multi-patterning — requires 4x the lithography steps of EUV, dramatically increasing cost and defect density. Demonstrates limits of export controls: they raise costs and slow progress but cannot indefinitely prevent catch-up.

---

## 3. Rare Earth Supply Chains

### 3.1 Chinese Processing Dominance

China controls ~60% of global rare earth mining and **85-90% of processing** — the separation and refining step that converts raw ore into usable oxides and metals. Even rare earths mined outside China (Mountain Pass, CA; Mount Weld, Australia) typically travel to China for separation, creating a single-point chokepoint.

### 3.2 Alternative Sources

| Source | Status | Timeline |
|--------|--------|----------|
| Lynas Rare Earths | **April 2026 HRE expansion** — targeting dysprosium and terbium | HRE ramp-up through 2027 |
| MP Materials (Mountain Pass, CA) | Light rare earth concentrate operational; HRE separation DOD-funded | HRE facility 2027-2028 |
| Bloomberg Decadal Gap Analysis (April 2026) | US needs "another decade" for independent processing capacity | 2035+ |

### 3.3 Recycling Economics

Rare earth magnet recycling — recovering neodymium, praseodymium, dysprosium from end-of-life products — remains subeconomic at current commodity prices. Key barriers: collection infrastructure, separation technology, and competition with Chinese virgin material. Recycling is a strategic hedge against supply disruption, not a near-term commercial solution.

---

## 4. SWIFT, BRICS Settlement, and Dollar Weaponization

### 4.1 Financial Infrastructure as Strategic Terrain

- **SWIFT:** Belgium-based messaging system connecting 11,000+ financial institutions. Not a settlement system — it's the communication layer.
- **Correspondent banking:** Dollar transactions clear through US banks, giving US jurisdiction over dollar flows.
- **Trade invoicing:** ~40% of global trade invoiced in dollars, creating structural demand for dollar reserves.

### 4.2 Alternative Payment Systems

| System | Country/Bloc | Status |
|--------|-------------|--------|
| CIPS | China | Processed ~$17T (¥123T) in 2023; growing but SWIFT-interoperable in practice |
| SPFS | Russia | ~400 institutions; limited cross-border adoption |
| BRICS Pay | BRICS | Conceptual/demonstration phase |
| mBridge | BIS + China, UAE, Thailand, HK | CBDC-based cross-border settlement pilot |

Full decoupling into competing financial blocs would fragment global trade, increase transaction costs, and reduce efficiency — but gradual erosion creates structural vulnerabilities over decades.

---

## 5. Commodity Market Warfare

### 5.1 Oil Price Caps: Theory and Practice

| Mechanism | Description | Effectiveness |
|-----------|-------------|---------------|
| G7 Price Cap ($60/bbl) | Restricts Western maritime services for Russian crude above cap | Partial — shadow fleet diverts 60-70% of volumes |
| Shadow fleet | ~600 aging tankers, opaque ownership | Key evasion vector; safety/environmental risks |
| Secondary sanctions threat | OFAC can sanction non-US facilitation entities | Deters Western-aligned entities; limited for no-US-nexus entities |

**MIT CEEPR 2025 model** (see Section 1) demonstrates theoretical limits — sanctions design must account for the target's participation constraint. See [[geopolitics-strategic-analysis]] Section 5.1.1 for full treatment.

### 5.2 Strategic Petroleum Reserves

US SPR reached 40-year lows in 2023-2024 after Ukraine-war releases. SPR releases function as short-term supply interventions (30-60 days at max drawdown) but cannot address structural disruptions — as demonstrated by the Strait of Hormuz crisis in 2026 (IEA May 2026 assessment).

---

## 6. Detection & Attribution Methodologies

### 6.1 Trade Data Analysis for Sanctions Evasion

**Mirror statistics analysis:** Compare reported exports from Country A to reported imports of Country B. Persistent gaps exceeding typical measurement error (+/- 5-10%) warrant investigation. CIF/FOB valuation differences must be adjusted (+10% for freight and insurance).

### 6.2 Network Analysis for Shell Company Detection

Shell company networks exhibit distinctive topological signatures: high clustering with low average path length, nesting (shared addresses), director overlap across jurisdictions, and circular ownership structures. Centrality measures — **betweenness centrality** (gatekeeper identification) and **PageRank** (recursive influence) — surface controlling entities. See [[network-analysis-graph-theory]].

### 6.3 Entity Resolution for Supply Chain Mapping

| Data Source | Coverage |
|------------|----------|
| OpenCorporates | 140+ jurisdictions, corporate registries |
| UN Comtrade | Bilateral trade flows by HS code, global annual |
| Panjiva/ImportGenius | Bill of lading data (US imports) |
| AIS vessel tracking | Maritime positions, real-time |
| OFAC SDN / UN / EU / UK lists | Designated entities and individuals |
| ICIJ Offshore Leaks | Beneficial ownership data, 50+ jurisdictions |

Entity resolution must handle: name variations across languages, subsidiary-parent relationships, beneficial ownership opacity, and temporal changes. See [[data-aggregation-entity-resolution]] for algorithmic approaches (Fellegi-Sunter, neural ER).

---

## Cross-Domain Connections

- [[geopolitics-strategic-analysis]] — Semiconductor supply chain, rare earths, sanctions effectiveness — 7 direct references
- [[markets-financial-analysis]] — Commodity markets, SWIFT/BRIICS settlement erosion, Fed trilemma and sanctions interaction
- [[data-aggregation-entity-resolution]] — Shell company detection, trade data matching, entity resolution for supply chain mapping
- [[network-analysis-graph-theory]] — Centrality measures for chokepoint identification, community detection for evasion clusters
- [[human-investigation-osint]] — Sanctions evasion investigation techniques, corporate registry research
- [[domain-whois-dns-investigation]] — Attribution of shell company websites, domain registration patterns
- [[email-forensics-header-analysis]] — Tracing communications infrastructure of evasion networks

---

## References

1. **Sabatini & Isard (2025).** "Understanding and Improving Sanctions." Chatham House.
2. **Kilian, Rapson & Schipper (2025).** "The Price Cap on Russian Oil: A Quantitative Analysis." MIT CEEPR Working Paper.
3. **Paul Weiss (2025).** "Economic Sanctions and Anti-Money Laundering Developments: 2025 Year in Review."
4. **CNAS (2024).** "Sanctions by the Numbers: 2024 Year in Review."
5. **Brookings (2024).** "The Effectiveness of Economic Sanctions on Russia."
6. **Biersteker, Eckert & Tourinho (2016).** *Targeted Sanctions.* Cambridge University Press.
7. **Hufbauer, Schott, Elliott & Oegg (2007).** *Economic Sanctions Reconsidered*, 3rd Ed. PIIE.
8. **Lynas Rare Earths (April 2026).** HRE expansion announcement.
9. **Bloomberg (April 2026).** "US Needs Another Decade for Rare Earth Independence."
10. **Reuters (April 2026).** MATCH Act scaled back reporting.
11. **CNBC (September 2025).** Commerce Department revoking TSMC/Samsung/SK Hynix waivers.

---

## Verification Status

**Last verified:** 2026-05-20
**Source:** Cross-referenced with [[geopolitics-strategic-analysis]], [[markets-financial-analysis]], [[network-analysis-graph-theory]], [[data-aggregation-entity-resolution]]. Web search: Chatham House 2025, Paul Weiss 2025, CNAS 2024, Brookings 2024.
**Deepening added:** All 6 sections populated with primary/secondary sources, evasion vector taxonomy, entity resolution dataset table, oil price cap mechanism table, semiconductor geography table, equipment restrictions table, alternative payment systems table, 11 references, 7 cross-domain connections.
