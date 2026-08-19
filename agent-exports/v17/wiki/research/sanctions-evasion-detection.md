# Sanctions Evasion Detection & Effectiveness Analysis

**Status: STABLE**
**Created: 2026-07-08 | Last deepened: 2026-07-08**
**Tags:** sanctions, evasion-detection, entity-resolution, financial-intelligence, maritime, OSINT, network-analysis

## Overview

Sanctions evasion detection is the systematic identification and analysis of methods used by state actors, entities, and individuals to circumvent economic sanctions. It sits at the intersection of financial intelligence (FININT), entity resolution, maritime domain awareness, and network analysis. The goal is not merely to detect individual violations, but to reconstruct the *evasion architecture* — the networks of shell companies, intermediary jurisdictions, re-flagging patterns, and trade-based money laundering (TBML) mechanisms that enable sanctioned entities to continue operating.

This page synthesizes evasion typologies, detection methodologies, and effectiveness metrics across three primary theaters: Russian oil price cap evasion (2022–2026), Iranian sanctions evasion networks (2012–ongoing), and North Korean crypto operations (2018–ongoing).

## Key Insight: Evasion as Inverse Entity Resolution

Entity resolution (ER) asks: "are record A and record B the same entity despite differing identifiers?" Evasion deliberately fragments identity across shells, flags, and jurisdictions to break exactly those links. Detection is thus ER run in reverse — identifying the *deliberate fragmentation patterns* rather than the coalescing matches. The same mathematical tools (Fellegi-Sunter probabilistic matching, temporal consistency windows, network community detection) solve both problems. See [[temporal-entity-resolution]] for the mathematical framework; see [[entity-resolution-agent-safety]] for why entity binding failures in tool-augmented agents mirror evasion detection failures in intelligence analysis.

---

## Evasion Typologies

### 1. Russian Oil Price Cap Evasion (2022–2026)

The G7+EU oil price cap ($60/bbl for crude, effective December 2022) was designed to limit Russian export revenue while maintaining global supply. Evasion mechanisms include:

- **Shadow Fleet:** Russia assembled an estimated ~600 aging tankers with opaque ownership, substandard insurance, and frequent flag changes (GIS Reports 2026). These vessels operate outside Western maritime services (insurance, classification, financing) and use AIS manipulation to conceal port calls and ship-to-ship (STS) transfers.
- **"Flags of Deceit" (FOD):** A 2026 AGILE GIS study (Novaes Porto et al., DOI:10.5194/agile-giss-7-21-2026) provided the first quantitative evaluation of re-flagging among sanctioned Russian vessels. While initial shadow fleet ships used classical Flags of Convenience (FOC: Panama, Liberia, Marshall Islands), increasing numbers are re-flagging to countries with even less regulatory rigor — Cameroon, Sierra Leone, São Tomé and Príncipe — often under fake identifiers.
- **STS Transfer Hubs:** Russian crude is transferred at sea in the Laconia Gulf (Greece), off Ceuta (Spain), and near Oman, blending with non-sanctioned oil to obscure origin before entering refineries in India, China, and Turkey.
- **Teapot Refineries:** Chinese independent "teapot" refineries have become primary buyers of price-cap-violating Russian crude, processing it into products that re-enter the global market without sanctions taint (Atlantic Council Energy Sanctions Dashboard 2026).
- **Insurance Arbitrage:** Russian state-owned insurers (RNRC, Ingosstrakh) provide coverage that falls below International Group of P&I Clubs standards, creating environmental risk spillover (IMO Resolution A.1192(33), December 2023; EU Parliament comprehensive resolution November 2024).

**Effectiveness Assessment:** The price cap mechanism has deteriorated. LSEG/SSRN working paper "The Dynamics of Evasion" (2025) documents how the shadow fleet amassed to systematically bypass price cap enforcement. The Atlantic Council notes that sanctions effectiveness depends on targeting two central nodes: shadow fleet tankers and Chinese teapot refineries. Without enforcement pressure on both simultaneously, the evasion ecosystem adapts.

### 2. Iranian Sanctions Evasion Networks

Iran's sanctions evasion architecture is the longest-running and most sophisticated, with decades of iterative adaptation:

- **Shadow Fleet Architecture:** Iran operates a fleet of tankers using AIS manipulation (spoofing, dark transits), identity laundering ("zombie" IMO numbers from scrapped vessels), and flag rotation through nominal registries. The Board's March 2026 analysis identified a paradox: Iran simultaneously threatens to close the Strait of Hormuz while continuing crude exports through it at reduced volumes.
- **Shell Company Networks:** Iran uses serial incorporator patterns — shell companies with short lifespans, interlocking directorates, and shared beneficial owners across jurisdictions. These are designed to break temporal links, as documented in [[temporal-entity-resolution]].
- **Trade-Based Money Laundering (TBML):** Over/under-invoicing of dual-use goods, pharmaceutical shipments, and petrochemical products. See [[alternative-data-sources-financial-intelligence]] for TBML detection methodology (FATF-Egmont 2020 framework).
- **2026 Escalation Impact:** The July 7, 2026 tanker attack (Iran struck Qatari LNG tanker Al-Rekayyat) led to the US revoking Iran's oil sales authorization, a 5.6% Brent spike to $76.04, and accelerated sanctions enforcement that pushed Iranian export volumes into even more opaque channels (see [[energy-commodity-dynamics]] for full timeline).

**Effectiveness Assessment:** Kharon (2026) documents a global campaign of shadow fleet ship seizures that expanded in early 2026 — the US detained the Russia-flagged Marinera in the North Atlantic with British assistance. However, vessel designation and seizure have only "somewhat more effect" than port entry bans; Russia and Iran have secured alternative routes and financial channels. The net effect is shift from transparent evasion to deeper opacity.

### 3. North Korean Crypto Operations

North Korea's evasion uses cryptocurrency as its primary vector, distinct from the maritime/oil focus of Russia and Iran:

- **Exchange Exploitation:** Nation-state actors (Lazarus Group) conduct sophisticated cyber intrusions against cryptocurrency exchanges and DeFi protocols, laundering proceeds through mixers (Tornado Cash, Sinbad) and cross-chain bridges.
- **IT Worker Fronts:** DPRK IT workers use false identities to obtain remote employment contracts, funneling salaries in cryptocurrency to state-controlled wallets. This is a form of *human entity resolution fraud* — individuals presenting as legitimate freelancers while controlled by the same entity.
- **Blockchain Forensics:** Detection relies on chainalysis methodologies — cluster analysis of wallet addresses, temporal patterns in transaction graphs, and linkage to known exchange accounts. The analytical framework is structurally isomorphic to corporate registry analysis: replace wallet addresses with shell company names, transaction graphs with beneficial ownership graphs, and mixers with intermediary jurisdictions.
- **Sanctions-Evasion Nexus:** North Korea has been documented sharing evasion infrastructure with Iran — joint ventures in crypto laundering, shared front companies, and technology exchange for missile programs.

---

## Detection Methodologies

### 1. Corporate Registry & Beneficial Ownership Analysis

Detecting shell company networks requires systematic analysis of corporate registries across multiple jurisdictions:

- **Temporal Entity Resolution:** Tracking entities across time when legitimate evolution (name change, merger) and deliberate obfuscation (serial incorporation, straw ownership) produce identity fragmentation. See [[temporal-entity-resolution]] for the three-category taxonomy and algorithm survey (FlexRL, ST-Link, Bayesian).
- **Beneficial Ownership Graph Construction:** Reconstructing ultimate beneficial owners (UBOs) from fragmented registry data, nominee directorships, and layered trusts. OpenOwnership and national registries (UK Persons of Significant Control, EU 5th AMLD) provide key data.
- **Network Anomaly Detection:** Identifying communities of entities with shared addresses, officers, incorporation dates, or service providers that indicate coordinated evasion. See [[network-analysis-techniques-osint]] for centrality and community detection methods.

### 2. Maritime Domain Awareness (MDA)

Detection of shadow fleet operations uses multiple complementary data sources:

- **AIS Integrity Analysis:** Rule-based diagnostics to filter communication-layer defects (duplicated MMSIs, timestamp errors, stale retransmissions) before kinematic analysis (Park et al., arXiv:2603.11055). Their three-stage framework applied to ~966M AIS messages from Korean coastal waters detected 17 spoofing and 343 jamming clusters, achieving 98.6% false alarm reduction.
- **GNSS Spoofing Detection:** Wide-area GNSS interference detection using AIS-derived spatiotemporal integrity monitoring (Park et al., 2026). Spoofing incidents in 2023–2024 displaced over 100 vessels simultaneously to false airport positions in the Eastern Mediterranean.
- **Dark Vessel Detection:** SAR and optical satellite imagery correlation for vessels that disable AIS (MDPI 2025 survey). NBER working paper #33486 documents the rise of dark shipping amid Western sanctions on Iran, Syria, North Korea, and Venezuela.
- **Re-Flagging Pattern Analysis:** Tracking flag changes across FOC and FOD registries, vessel identity manipulation, and "zombie" IMO reuse. See [[maritime-logistics-gray-zone]] for the 3-phase behavioral analysis (Mar-Apr 2026) of Iran's shadow fleet.

### 3. Financial Tracking & Trade Data Anomalies

- **Trade Data Discrepancy Analysis:** Comparing declared export values between trade partners. For example, Russian crude exports to India at "market" rates that breach the price cap can be detected by comparing Russian customs data with Indian import declarations, satellite-based tanker loading volumes, and insurance validation.
- **Blockchain Forensics:** Wallet clustering, transaction graph analysis, and exchange inflow/outflow monitoring for North Korean and Iranian crypto operations. See [[alternative-data-sources-financial-intelligence]] for the HybridFL privacy-preserving collaborative detection framework (Khan et al., 2026).
- **Beneficial Ownership Registry Correlation:** Cross-referencing corporate registries, sanctions lists (OFAC SDN, EU consolidated, UK OTSI), and ownership databases (Orbis, Capital IQ) to identify undisclosed control relationships.

### 4. Network-Level Detection

- **Multi-Layer Network Construction:** Building networks that combine maritime (AIS, port call data), corporate (registry records), financial (SWIFT, trade finance), and trade (customs declarations) layers. See [[supply-chain-network-analysis-osint]] for the 8-layer data/tool taxonomy.
- **Community Detection:** Applying Louvain, Leiden, or label propagation algorithms to identify clusters of entities engaged in coordinated evasion, then cross-referencing against known sanctions networks.
- **Link Prediction:** Identifying entities likely to be connected based on structural similarity to known evasion patterns — analogous to the link prediction techniques used in counter-network analysis (see [[network-analysis-techniques-osint]]).

---

## Effectiveness Metrics

| Metric | Russia (2026) | Iran (2026) | North Korea |
|--------|---------------|-------------|-------------|
| Shadow fleet size | ~600 tankers | ~300 tankers | N/A (crypto focus) |
| AIS dark transits/month | >1,000 (Mar 2026) | >500 (hormuz crisis) | N/A |
| Price cap compliance rate | <30% (estimate) | N/A | N/A |
| Sanctioned entities designated | 2,300+ individuals/entities | 1,800+ individuals/entities | 200+ crypto addresses |
| Shell company lifespan (median) | 18 months | 14 months | 6–12 months |
| Oil export volume (bbl/day) | ~3.3M (pre-invasion) → ~2.8M (2026) | ~1.5M → ~0.7M (post-Hormuz crisis) | N/A |
| Crypto stolen (cumulative) | N/A | N/A | $3.4B+ (2017–2026) |

Sources: GIS Reports, Atlantic Council, Kharon, Chainalysis, IEA, Brookings, NBER.

---

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[temporal-entity-resolution]] | Mathematical framework for tracking shell company rotation, flag hopping, and zombie IMO reuse |
| [[maritime-logistics-gray-zone]] | Iranian shadow fleet architecture, AIS manipulation detection, 3-phase behavioral analysis |
| [[energy-commodity-dynamics]] | Russian oil price cap enforcement, Hormuz crisis impact, shadow fleet economic effects |
| [[rare-earth-supply-chains]] | Sanctions and extraterritorial enforcement: Chinese REE export license deadline as structured prediction problem |
| [[entity-resolution-agent-safety]] | Entity binding failures as hidden failure mode in tool-augmented agents; same math as evasion detection |
| [[alternative-data-sources-financial-intelligence]] | TBML detection (FATF-Egmont 2020), trade data discrepancy analysis, blockchain forensics |
| [[supply-chain-network-analysis-osint]] | Multi-layer network construction for evasion architecture reconstruction |
| [[network-analysis-techniques-osint]] | Community detection, link prediction, centrality measures for evasion network mapping |
| [[data-breach-analysis-osint]] | Breach data as source for uncovering shell company networks and beneficial owner links |
| [[counterintelligence-analysis-frameworks]] | CI-ACH applied to adversary evasion TTP analysis; deception detection |
| [[intelligence-failure-analysis]] | Structural failure patterns (mirror-imaging, anchoring) that cause sanctions regime overconfidence |
| [[metadata-resistant-communication-protocols]] | Evasion actors' use of encrypted communications to coordinate without detection |
| [[private-credit-systemic-risk]] | Sanctions create secondary effects: exposure of BDCs to sanctioned entities through opaque private credit |
| [[defense-procurement-cycles]] | Industrial base sanctions: restrictions on dual-use components for military supply chains |

---

## Open Questions

1. What is the theoretical limit of detection when evasion adapts faster than designation? (Arms race dynamics)
2. Can generative AI models simulate evasion scenarios to train detection systems? (Adversarial training)
3. How do secondary sanctions (extraterritorial enforcement) shift evasion patterns vs. primary designation?
4. What is the optimal coordination mechanism between maritime safety regulation (IMO) and sanctions enforcement (OFAC, EU)?
5. Can zero-knowledge proofs enable sanctions compliance verification without revealing trade details to competitors? (Privacy-preserving compliance — see [[zkp-applications-beyond-crypto]])

---

## References

1. Novaes Porto et al., "Flags of Deceit: Re-Flagging Trends among Sanctioned Ships in the Russian Shadow Fleet," AGILE GIScience Series, 2026. DOI:10.5194/agile-giss-7-21-2026.
2. Park, Cho & Son, "Wide-Area GNSS Spoofing and Jamming Detection Using AIS-Derived Spatiotemporal Integrity Monitoring," arXiv:2603.11055, February 2026.
3. NBER Working Paper #33486, "The (Un)Intended Consequences of Oil Sanctions and Dark Shipping," 2024.
4. GIS Reports, "Russia's Shadow Fleet and Oil Exports," 2026.
5. Atlantic Council, "Energy Sanctions Dashboard," 2026.
6. The Board, "Dark Fleet Tankers 2026: Shadow Fleet Moving Sanctioned Oil," March 2026.
7. Brookings Institution, "Stiffening European Sanctions Against the Russian Oil Trade," 2026.
8. Kharon, "Why Are So Many Countries Now Seizing Shadow Fleet Ships? Four Experts Explain," 2026.
9. SSRN, "The Dynamics of Evasion: The Price Cap on Russian Oil Exports and the Amassing of the Shadow Fleet," 2025 (ID: 5110126).
10. IMO Resolution A.1192(33), December 2023, warning on shadow fleet proliferation.
11. EU Parliament comprehensive resolution on shadow fleet sanctions, November 2024.
12. Chainalysis, 2026 Crypto Crime Report.
13. Polestar Global, "SKIPPER Sanctions Evasion: A 12-Month Pattern Exposed," 2026.
14. Preprints.org, "Shadow Fleets: A Growing Challenge in Global Maritime Commerce," May 2025.
15. MDPI Remote Sensing, "Dark Ship Detection via Optical and SAR Collaboration," June 2025.
16. Exocortex wiki/research/temporal-entity-resolution.md — Temporal entity resolution framework with sanctions evasion case studies.
17. Exocortex wiki/research/energy-commodity-dynamics.md — Hormuz Crisis 2026 impact on sanctions enforcement.
18. Exocortex wiki/research/maritime-logistics-gray-zone.md — Iranian shadow fleet behavioral analysis.
