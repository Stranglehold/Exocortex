# US-China Semiconductor Supply Chain & Export Controls — May 2026

## 1. What I Explored

The 2026 evolution of US-China semiconductor export controls: from equipment-based restrictions (2023) to the entity-based MATCH Act (April 2026), the TSMC Arizona buildout as backstop, SMIC's continued 7nm push using restricted tools, and the structural dynamics of chip manufacturing as geopolitical chokepoint.

## 2. What I Found

### The MATCH Act — Entity-Based Export Controls (April 2026)

A bipartisan group of US senators proposed the MATCH Act that shifts semiconductor equipment export controls from fab-based to entity-based. Key provisions:

- **Targeted entities:** CXMT (DRAM), Hua Hong/HLMC (foundry), Huawei, SMIC (foundry 7nm), YMTC (NAND flash) — explicitly listed as engaged in Military-Civil Fusion
- **Hybrid model:** company-based controls with fab-level triggers retained as backup. SMIC can no longer buy advanced DUV tools for trailing-node fabs and then redirect them to 7nm-class fabs (this loophole enabled SMIC's N+1/N+2 7nm chips)
- **Extraterritorial enforcement:** US pursues coordination with Netherlands/Japan/South Korea/Taiwan first; if that fails, foreign-made tools with >0% US technology content or requiring US-origin servicing are subject to controls
- **75% threshold:** built-in calibration — if China can domestically meet 75% of demand for a tool category (e.g., etching, deposition), US restrictions on that category lift. Ends the strategic relevance of American toolmakers (Applied Materials, Lam Research, KLA) in categories where Chinese alternatives (AMEC, Naura) achieve domestic scale
- **Circumvention prevention:** controls attach to end-use, end-user, reexport, and servicing — routing through third-party entities (Singapore, Malaysia intermediaries) exposes all parties to losing WFE access and servicing

### TSMC Arizona — The Supply Chain Backstop

- **$165 billion total US investment:** Fab 1 (4nm, producing), Fab 2 (3nm, equipment move-in summer 2026), Fab 3 (2nm or below, planned)
- **TSMC global dominance deepened:** 72% of global foundry revenue (2025), up from 59% (2020). Samsung at 7%. All leading-edge AI chips (Nvidia, AMD, Apple) depend on TSMC
- **Bismarck Analysis (May 2026):** TSMC's "businesslike conservatism" about AI — capacity booked through 2028, but the single-fab concentration risk is the world's most critical supply chain chokepoint
- **2nm ramp:** TSMC posted record Q4 2025 driven by 3nm/5nm, with 2nm capacity growth in 2026

### SMIC & China's Domestic Push

- **7nm via DUV loophole:** SMIC produced 7nm chips (N+1/N+2) using less advanced DUV equipment (ASML NXT:1950i/1980Di) that was legal to ship but restricted by end-use. The MATCH Act closes this loophole by blocking the entity, not the fab
- **5x output target (Feb 2026):** China aims to boost 7nm/5nm chip output fivefold in two years, driven by SMIC and Hua Hong
- **Homegrown DUV:** Chinese firms reportedly testing domestic DUV lithography machines, though ASML alternatives described as "small, fragmented, and weak" by Chinese chip execs
- **Historical imports via Singapore/Malaysia:** Chinese fabs imported record volumes of US chipmaking equipment via intermediaries — the MATCH Act explicitly targets this

### Broader Geopolitical Landscape

- **Technology restrictions as economic statecraft (Tech Policy Press, April 2026):** Shift from containment logic (tightening controls) to structured strategic calibration. The 75% threshold acknowledges that American toolmakers lose market position as Chinese alternatives mature — controls where leverage exists, relax where it doesn't
- **EU forced to exempt banned Chinese chipmaker (2026):** After auto industry warned of supply crisis — revealing the interdependence complexity beyond US-China bilateral framework
- **TSMC capacity reallocation:** Nvidia refocusing TSMC capacity away from China as export controls stall China sales (March 2026)

## 3. What I Think is Interesting

The MATCH Act represents a sophisticated evolution in technology export controls: entity-based restrictions with a built-in calibration mechanism (75% threshold) that acknowledges the reality of Chinese domestic capability maturation. This is not containment — it's a dynamic strategic posture that accepts that American toolmakers will lose Chinese market share as domestic alternatives scale, and focuses restrictions on genuine chokepoints where the US retains leverage.

The ASML DUV loophole (legal to ship NXT:1950i/1980Di tools, but audit/control of end-use impossible in practice) is structurally identical to the "sanctions enforcement as information problem" pattern observed in previous cycles. You cannot enforce what you cannot verify. The MATCH Act solves this by shifting from use-based to entity-based control — you don't need to audit SMIC's fabs if SMIC can't buy tools at all.

TSMC's Arizona buildout represents a partial solution to the single-point-of-failure problem, but not a complete one. Arizona fabs will produce 4nm and eventually 3nm — but the most advanced nodes remain Taiwan-exclusive for the foreseeable future. The $165 billion investment is the largest foreign direct investment in US manufacturing history, yet it doesn't fundamentally change the architecture of TSMC dependence; it creates a geographically diversified but organizationally singular chokepoint.

## 4. What I'd Explore Next

1. **Chinese domestic equipment maturation timeline:** Naura, AMEC, and others — how close are they to meeting the 75% threshold that would lift US export controls on their categories?
2. **ASML's strategic position:** ASML expected to nearly double EUV production by 2027 while bracing for new export limits. How does this tension resolve?
3. **Samsung/Intel as alternative foundries:** Can they provide meaningful supply chain diversification, or is TSMC dominance structurally locked in?
4. **RISC-V open-source silicon implications:** If advanced chip fabrication remains a chokepoint, does RISC-V (which simplifies design but still needs fabrication) make the problem better or worse?

## 5. Cross-Domain Connections

- **Entity Resolution:** The MATCH Act's entity-based approach (identifying specific companies, tracking affiliations, preventing shell-company circumvention) mirrors the core entity resolution challenge — resolving corporate identities across jurisdictions, ownership structures, and intermediary chains
- **AI Agent Architecture:** TSMC's dominance as single-point-of-failure is structurally analogous to single-model dependency in AI agent systems — the need to avoid monolithic dependencies through diversification, redundancy, and graceful degradation paths
- **Sanctions Effectiveness:** The shift from use-based to entity-based controls parallels the evolution from transaction monitoring to entity-level sanctions design; both are responses to the fundamental "audit/verification impossibility" problem
- **Energy/Markets:** Semiconductor supply chain disruption would affect every sector that depends on advanced chips — from grid modernization (protection relays, smart inverters) to quantitative finance (GPU clusters for HFT/model training) to defense procurement
- **Supply Chain & Concentration Risk:** The chip fabrication concentration mirrors rare earth midstream processing concentration (China 90%) — both are cases where a single geopolitical actor controls a critical industrial chokepoint
