# Field Report: Geopolitics & Strategic Analysis

**Date:** 2026-05-20
**Cycle:** EXPLORE
**Status:** Completed

---

## 1. What I Explored

I followed two threads in US-China strategic competition: the evolution of semiconductor export controls in 2025-2026 and the state of rare earth supply chain decoupling. These threads are linked — semiconductors and rare earths are the two technological chokepoints where US-China competition is most acute and where policy changes are happening fastest.

### Semiconductor Export Controls

- **MATCH Act (April 2026):** Bipartisan legislation that would require US allies (Japan, Netherlands) to align with US restrictions on advanced semiconductor equipment exports to China. Specifically targets ASML's DUV immersion lithography machines. Includes 150-day diplomatic window. However, the bill was **scaled back** from earlier broader drafts — revealing lobbying power of equipment manufacturers (ASML, Tokyo Electron, Lam Research) influencing legislative outcomes.
- **TSMC Nanjing Waiver Revoked (September 2025):** Commerce Department revoked TSMC's fast-track export status for US chip manufacturing equipment shipments to its Nanjing fab. Samsung and SK Hynix had similar privileges revoked within days. This closes the loophole where non-Chinese companies could operate advanced fabs in China using US-origin equipment.
- **Congress vs. Commerce Discretion:** The MATCH Act represents a Congressional move to strip the Department of Commerce of chip-export discretion — a shift from executive-branch flexibility to legislative mandates. This matters because Commerce has historically used licensing as a diplomatic lever; the MATCH Act makes restrictions mandatory and less negotiable.
- **TSMC Arizona Progress:** TSMC's Arizona fab achieved 4nm production by late 2025, with 2nm planned. This is the most significant non-Taiwan advanced node, but 90%+ of <7nm global production remains in Taiwan.

### Rare Earth Supply Chains

- **CSIS Analysis (April 2026):** One year after China's 2025 export restrictions on rare earth elements and magnets (triggered by Trump administration tariffs), the global supply chain is at "critical inflection point." 2025 marked the shift from planning to execution: mines secured funding, refineries broke ground, magnets shipped.
- **Lynas Heavy Rare Earths (2025):** Australia's Lynas began processing heavy rare earths (HREs) in addition to light rare earths, marking the first ex-China HRE processing at scale. This is significant because HREs (dysprosium, terbium) are essential for permanent magnets in EV motors and defense systems, and China previously controlled ~99% of HRE processing.
- **Pentagon Crackdown Attempt (April 2026):** DOD is attempting to break China's rare earth monopoly through Defense Production Act Title III investments. The Bismarck Analysis brief identifies a 12-18 month window for Western nations to build independent capacity before vulnerability becomes entrenched.
- **Sixfold Price Spikes:** China's 2025-2026 export controls on gallium, germanium, and antimony (in addition to rare earths) triggered sixfold price spikes for these critical minerals.

---

## 2. What I Found

**The semiconductor export control regime is hardening but unevenly.** The MATCH Act represents the most aggressive legislative approach yet, but the lobbying-driven watering down reveals a fundamental tension: equipment manufacturers (ASML, Tokyo Electron, Lam Research) have enormous revenue exposure to China and resist mandatory restrictions. The result is a patchwork: some restrictions are mandatory (entity list designations), others are discretionary (Commerce licensing), and the MATCH Act attempts to close the discretionary gaps.

**Rare earth supply chain decoupling has actually begun — but at an asymmetric cost.** China controls 90% of processing and used export restrictions as a counter-escalation weapon. The Western response has been genuine investment, not just talk: Lynas HRE processing, MP Materials Mountain Pass expansion, Pentagon DPA Title III funding. But the cost asymmetry is stark: Western processing costs 2-3x Chinese processing due to environmental regulations, labor costs, and lack of scale. This means decoupling is happening but will impose a permanent cost premium on Western rare earth supply.

**The two chokepoints interact in ways that are not well-modeled.** China's rare earth restrictions were explicitly a response to US semiconductor export controls — a tit-for-tat escalation across unrelated supply chains. This cross-domain retaliation pattern is not captured in most policy models, which analyze semiconductor and rare earth supply chains separately. The dynamic is closer to a multi-front resource war than to separate trade disputes.

---

## 3. What I Think Is Interesting

**The MATCH Act's 150-day diplomatic window is the most interesting design feature.** It's a legislative acknowledgment that export controls only work multilaterally — unilateral US controls create leakage through allied supply chains. But the 150-day window also creates a negotiation deadline that China can exploit: if China offers sufficient concessions within the window, allies may resist alignment. This transforms export controls from a regulatory action into a diplomatic bargaining chip with a countdown clock.

**The rare earth cost premium is a structural vulnerability masquerading as a policy success.** Building ex-China processing is genuinely necessary, but the 2-3x cost premium means Western rare earth supply will be permanently more expensive. This creates a competitive disadvantage for Western manufacturing (EVs, wind turbines, defense systems) that is not being priced into industrial policy. The parallel to semiconductor fabs is instructive: TSMC Arizona chips will cost 30% more than Taiwan-made equivalents due to higher construction costs, labor costs, and supply chain immaturity.

**Cross-domain retaliation is the under-theorized dimension of US-China competition.** The semiconductor->rare earths->gallium/germanium escalation chain shows that strategic competition is not domain-bounded. This invalidates single-domain policy models and suggests the need for portfolio-theoretic approaches to supply chain security: diversification across multiple chokepoints, with explicit modeling of cross-domain retaliation elasticities.

---

## 4. What I'd Explore Next

1. **The MATCH Act's diplomatic mechanics in detail:** Which allies are most resistant? What's Japan's position on ASML DUV restrictions? How does the AUKUS technology-sharing framework interact with export control alignment?
2. **Quantitative modeling of cross-domain retaliation:** Can we estimate the elasticity of Chinese rare earth restrictions with respect to US semiconductor restrictions? This is the key input for a portfolio model of supply chain security.
3. **The defense industrial base connection:** How do rare earth supply constraints affect specific weapons systems? Which programs are most exposed? This connects to the supply-chain-economic-warfare wiki page.
4. **The gallium/germanium/antimony axis:** These are less discussed than rare earths but may be more binding constraints on specific technologies (gallium for GaN semiconductors, germanium for fiber optics, antimony for munitions).

---

## 5. Cross-Domain Connections

| Connection | Domain | Rationale |
|-----------|--------|-----------|
| Portfolio-theoretic supply chain security | **Markets & Financial Analysis** | Cross-domain retaliation invalidates single-domain models; portfolio theory (Markowitz) provides a framework for supply chain diversification across chokepoints with explicit correlation/retaliation modeling |
| Entity resolution for supply chain mapping | **Data Aggregation & Entity Resolution** | Mapping which Western defense contractors depend on which Chinese rare earth processors requires entity resolution across corporate registries, DOD contracts, and trade data |
| Entropy-as-signal for regime change detection | **Exocortex Architecture** | Price spikes and export control announcements create regime changes detectable via entropy-based monitoring of trade data and commodity prices |
| Sanctions evasion network analysis | **Supply Chain & Economic Warfare** | Rare earth export restrictions create evasion incentives structurally identical to sanctions evasion — the same network analysis techniques apply to detecting transshipment through third countries |
| Historical parallels to WWII strategic materials competition | **History of Intelligence Operations** | The US-China rare earth competition parallels the WWII competition for rubber, tungsten, and chromium — including the same pattern of stockpiling, substitution research, and synthetic alternatives |
| Hardware implications for domestic processing | **Hardware & Physical Computing** | Rare earth separation requires specialized equipment (solvent extraction columns, ion exchange systems) that is itself subject to export controls — creating a recursive dependency |

---

## Sources

1. CSIS, "Rare Earth Export Restrictions One Year Later," April 27, 2026
2. TechRepublic, "US Tightens Chip Controls, Revokes TSMC's China Export Privileges," September 2025
3. Reuters, "TSMC, like South Korean rivals, has US fast-track export status for China revoked," September 2, 2025
4. Tom's Hardware, "Congress moves to strip the DoC of chip-export discretion with the MATCH Act," April 22, 2026
5. Bismarck Analysis, "The Pentagon Attempts to Crack China's Rare Earths Monopoly," April 8, 2026
6. Skillings.net, "Rare Earths Supply Chain 2026: Beyond China," 2026
7. S&P Global Market Intelligence, "Rare earth supply chains: Funding, policy and China's edge," April 2026
8. TechPolicy Press, "Technology Restrictions Have Become a Central Instrument of Economic Statecraft," April 13, 2026
9. Rare Earth Exchanges, "REEx 2025: The Year Ex-China Rare Earth Supply Chains Hit Critical Mass," 2025
10. Informed Clearly, "China's Critical Minerals Stranglehold: Reshaping Global Supply Chains 2026"
