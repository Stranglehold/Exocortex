# Network Chokepoint & Routing Analysis

**Status:** STABLE
**Topic Slug:** network-chokepoint-routing-analysis
**Created:** 2026-08-02 (BUILD cycle, idle-time) | **Last deepened:** 2026-08-02
**Domain:** Internet infrastructure / Geopolitics / OSINT / Critical Infrastructure

## Summary

Internet traffic concentrates through a small set of physical and logical chokepoints: transit autonomous systems (ASes), Internet eXchange Points (IXPs), long-haul submarine cables, and cloud/edge peering layers. This page analyzes that concentration as a structural property, a measurement problem, and a resilience/interdiction surface. The core pattern — a handful of actors controlling the pipes that everyone depends on — is isomorphic to the chokepoint concentration already documented for semiconductors (TSMC/ASML/EDA), rare earths (Chinese midstream), and maritime straits (Hormuz/GIUK).

## 1. Logical chokepoints: BGP and transit ASes

- BGP (Border Gateway Protocol, RFC 4271) is the exterior gateway protocol connecting ~75,000 Autonomous Systems on the Internet. The Internet's route propagation and path selection are policy- and economics-driven (interconnection agreements between ISPs), not metric-driven — unlike interior protocols such as OSPF. This makes routing topology a map of commercial and political relationships, not just engineering.
- Transit concentration: the bulk of global traffic traverses a small set of large transit networks (historically ~13-20 "Tier 1" ASes with free-peering, no transit purchase). Measurement studies consistently show a heavy-tailed AS graph: a tiny fraction of ASes carries a dominant share of originated prefixes and routed traffic.
- Cloud/edge concentration adds a second logical layer: hyperscaler and CDN backbone networks (which now self-build global backbones and bypass classic Tier 1s for their own traffic) and zero-trust/bot-fronting layers (Cloudflare, Akamai, DataDome) act as application-layer chokepoints for specific kinds of traffic.
- OSINT implications (grounded in ip-geolocation-network-attribution): BGP data answers attribution questions — which AS announces an IP block, who are the upstream providers, has a prefix been hijacked or leaked, what other prefixes does an organization control.

## 2. Physical chokepoints: submarine cables and IXPs

- Submarine cable map / TeleGeography data: transoceanic traffic depends on a finite set of cable systems, with landing points concentrated in a few geographic corridors. The GIUK Gap carries transatlantic data cables and is a recorded vulnerable seam for undersea-cable sabotage (Nord Stream precedent; Russia's mapping/probing of cables is a first-order NATO concern).
- Ownership concentration: recent political-economy research (SPIR 2026) finds the global cable network owned by a diverse group but increasingly dominated by American tech giants investing in infrastructure, displacing legacy national telecom operators. This shifts control from public carriers to private platform operators.
- IXPs: more than 300 operational IXPs worldwide (since 1994's NAP decommissioning); the largest IXPs carry daily volumes comparable to Tier-1 ISPs, but regional concentration is uneven — Europe has dense IXP ecosystems (DE-CIX, AMS-IX, LINX), while many regions rely on a single dominant exchange or none. IXP-topology models (arXiv:1706.07323) capture the real inter-domain graph better than AS-only models because peering at IXPs is invisible in classic BGP adjacency data.
- IXP concentration creates a dual role: efficiency (local peering offloads transit cost and latency) and vulnerability (an IXP outage or control seizure can isolate a region's internal traffic).

## 3. Resilience and interdiction analysis

- Failure modes: cable cuts (fishing anchors, seismic activity, sabotage), BGP hijacks/leaks, IXP switch/router failures, state-level internet shutdowns (national kill switches), and electromagnetic threats.
- Solar-storm counterpoint: monitoring of transoceanic cable power systems during high solar activity (arXiv:2211.07850) finds century-scale CME events (even a Carrington-class 1859 event) will NOT damage long-haul submarine cables — geoelectric threats to cables are far smaller than to terrestrial power grids. Cable-interdiction risk is thus primarily physical/kinetic and regulatory, not solar-geophysical.
- State interdiction levers: cable-landing licensing, IXP control, BGP route filtering (withdrawal or selective announcement), national firewall layers, and physical sabotage by submarine assets. The Baltic Sea cable damage events and GIUK Gap concerns establish kinetic sabotage as the live threat vector.
- Offline-mesh resilience (grounded in metadata-resistant-messaging and SCADA/ICS availability patterns): delay-tolerant and mesh protocols (Briar-style) provide fallbacks during internet disruption; critical infrastructure systems must remain available during network degradation — the same principle that governs substation/SCADA continuity.

## 4. Measurement and data sources

- BGP data: RouteViews, RIPE RIS, BGPMon, Cloudflare/Kentik public dashboards for AS/prefix/hijack visibility; origin-AS and AS-path analysis for entity attribution.
- IXP data: PeeringDB, Euro-IX / IXP databases, IXP-Country-JSON, and passive BGP peering-link discovery (IEEE 6567146) to detect fabric membership not visible in public BGP.
- Cable data: TeleGeography Submarine Cable Map, telegeography.com, cable landing-station registries, + infrastructure OSINT tools (OpenInfrastructureMap, OpenGridWorks, FiberLocator) for physical-layer mapping.
- Topology models: IXP-based graph models (arXiv:1706.07323) plus classical AS-graph studies for degree distribution and centrality (power-law concentration).

## 5. Five-phase investigation workflow (OSINT use)

1. **Prefix-to-AS attribution** — map target IP/prefix to origin AS and upstream providers (whois, RPKI, BGP-looking-glass, RIPEstat).
2. **Path and policy mapping** — trace AS paths, identify Tier-1/transit dependence, detect route filtering, hijacks/leaks, and prepending.
3. **Physical-layer overlay** — map AS/IXP membership to cable routes and landing points using PeeringDB + submarinecablemap; find geographic concentration.
4. **Ownership resolution** — resolve AS registrants, cable consortium members, and IXP operators through corporate registries (corporate-registry-investigation); entity-resolution patterns apply.
5. **Resilience/interdiction assessment** — evaluate single-point-of-failure exposure (for critical-infrastructure operators) or adversary interdiction options (for adversary modeling) using the chokepoint concentration index.

## 6. Chokepoint concentration index (concept)

Analogous to supply-chain concentration metrics (HHI-style), a routing chokepoint index can be computed for any region/critical function: number of transit ASes carrying >80% of its traffic; number of IXPs on which it depends; cable systems and landing points serving it; and diversity of cloud/CDN providers in front. Low values indicate monoculture exposure; the same measurement logic already applied to semiconductors (manufacturing/equipment/EDA) and rare earths (oxide separation/magnet production) transfers directly.

## 7. Cross-domain connections

| Domain | Connection |
|--------|------------|
| OSINT / Network Attribution | BGP AS-path analysis is the backbone of IP attribution; dns-whois and ip-geolocation pages provide adjacent tooling |
| Maritime Logistics & Gray Zone | Hormuz/GIUK/NSR chokepoint logic applies identically to cable corridors; maritime sabotage (Baltic/Nord Stream) sets the kinetic precedent |
| Energy Commodities | Energy infrastructure and telecom corridors co-locate in rights-of-way; grid and data dependency overlap in critical-infrastructure planning |
| Semiconductor / Rare Earths | Chokepoint concentration pattern (single-supplier dependency) is structurally identical across all three domains |
| Critical Infrastructure / SCADA-ICS | Internet dependency of OT environments creates a chokepoint exposure; offline-mesh and SCADA availability are the resilience mirror |
| AI Agent Architecture | DNS/BGP/CDN chokepoints gate autonomous agents' data access; network resilience informs agent fallback/offline strategies (Briar delay-tolerant patterns) |
| Privacy & Censorship Evasion | CDN/IP-layer chokepoints are where censorship and bot-detection concentrate; Privacy Pass and metadata-resistant protocols respond to them |
| Finance / Market Structure | Routing and payment networks are both concentrative infrastructure; market-maker/microstructure concentration has the same HHI-style analysis shape |

## 8. References

1. RFC 4271 — Border Gateway Protocol 4 (BGP-4)
2. IP Geolocation & Network Attribution wiki (Exocortex, 2026-05-20) — ~75k ASes, attribution questions
3. Chatzis, N., et al. — "On the importance of Internet eXchange Points for today's Internet ecosystem" (arXiv:1307.5264)
4. Moura, G., et al. — "Re-mapping the Internet: Bring the IXPs into Play" (arXiv:1706.07323)
5. "Improving the discovery of IXP peering links through passive BGP measurements" (IEEE 6567146)
6. Solar Storms and Submarine Internet Cables (arXiv:2211.07850) — century-CME resilience study
7. "Beneath the Waves: Ownership and Control in the Submarine Cable Infrastructure" (SPIR, 2026)
8. CCNA Routing & Switching Complete Study Guide (Lammle) — BGP/EGP, AS concept, BGP-vs-OSPF economics distinction
9. AWS Certified Advanced Networking Study Guide — BGP dynamic routing, transit VPC hub pattern
10. Arctic Geopolitics & GIUK Gap wiki (Exocortex, 2026-06-06) — cable chokepoints, cable sabotage threat
11. Submarine Cable Map (TeleGeography) / OpenInfrastructureMap / OpenGridWorks / FiberLocator — physical-layer tools
12. Rare Earth Supply Chains wiki (2026) — chokepoint concentration pattern
13. Semiconductor Capital Expenditure Trends wiki — TSMC/ASML/EDA concentration
14. Maritime Logistics & Gray Zone wiki (2026) — chokepoint taxonomy, Hormuz/GIUK
15. Metadata-Resistant Messaging wiki (2026) — offline mesh resilience, Briar delay-tolerant protocols
16. SCADA/ICS Security wiki — OT availability requirements under network degradation
