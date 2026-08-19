# Rare Earth Supply Chain Geopolitics — Field Report

**Date:** 2026-07-11
**Cycle Type:** EXPLORE
**Topic Slug:** rare-earth-supply-chains

---

## 1. What I Explored

I followed the rare earth supply chains thread from Jake's interests registry, focusing on the structural chokehold China maintains on midstream processing and the West's attempts to de-risk. The investigation spanned five sub-threads:
- China's processing dominance and export control escalation (2025–2026)
- Western de-risking efforts (MP Materials, Lynas, Saskatchewan Research Council)
- Defense platform vulnerability quantification (new SSRN paper, 2026)
- Recycling economics and the talent gap
- The evolving "Critical Minerals Cold War" narrative

## 2. What I Found

### China's Processing Chokehold

China controls ~60% of rare earth mining but **85–90% of global processing capacity** (separation/refining). In October 2025, Beijing expanded export controls to cover five additional elements and imposed extra scrutiny for semiconductor/defense end-users. December 2025 saw controls extended to processing *technology* itself, triggering allied emergency stockpiling. The Herfindahl-Hirschman Index (HHI) for global REE processing is **4,954**, a monopolistic market structure far exceeding the 2,500 concern threshold (SSRN, 2026).

Heavy rare earth elements (HREEs) — dysprosium (Dy) and terbium (Tb) — are the most vulnerable link. They are indispensable for permanent magnets in F-35 fighters (~900 lbs of REEs per aircraft), Virginia-class submarines, and precision-guided munitions. China controls an estimated **99% of HREE processing**.

### Western De-Risking: Fragile Architecture

| Player | Location | Status |
|--------|----------|--------|
| **MP Materials** | Mountain Pass, California | Only scaled US REE production source. Light REE separation operational; heavy REE separation still a gap. Expanding into magnet manufacturing. |
| **Lynas Rare Earths** | Mt Weld, Australia | Largest non-Chinese producer. Producing NdPr, adding samarium by April 2026. Kalgoorlie cracking/leaching plant operational. US processing facility under construction (Texas, DOE-funded). Still dependent on Chinese refining for some HREEs. |
| **Saskatchewan Research Council** | Canada | Government-backed, began producing NdPr metal in summer 2025. |

**Structural brittleness** (Materials Dispatch, 2026): The non-Chinese NdPr deficit and tight HREE balance mean modest delays at one or two nodes could cascade. Western HREE independence is **unlikely before 2028**. Lynas and MP Materials estimate ~15% of global NdPr oxides by 2026, but allied magnet share remains under 10% vs. China's 85–90%.

### Defense Platform Vulnerability

A 2026 SSRN study (Defense Platform Vulnerability Assessment, SSRN 6208379) developed a composite vulnerability index for 15 major US weapons systems:

**V = w₁(REE_content) × w₂(element_criticality) × w₃(1-substitutability) × w₄(strategic_importance) × w₅(1-stockpile_coverage)**

Results across three disruption scenarios:
- **CVN-78 Ford-class carrier**: highest vulnerability (V = 0.915)
- **Columbia-class submarine** (V = 0.793), **Virginia-class** (V = 0.743)
- **Naval platforms** averaged highest category vulnerability (M = 0.7814)
- **Ground platforms** (M1 Abrams, JLTV) lowest (M = 0.370)
- Element criticality was the strongest driver (r = 0.91); stockpile coverage the strongest protector (r = −0.93)
- Under conflict-induced supply cessation, mean platform vulnerability rises 22.5% above baseline

A separate Chinese modeling paper (arXiv:2505.21579, May 2025) simulated a 10-year zero-tolerance REE export policy: years 3–5 lead to significant technological disconnect; years 8–12 to systemic capability lag with estimated annual US economic impact of **$35–40 billion**.

### Recycling vs. Economics

Recycling technologies (hydrogen decrepitation, hydrometallurgy, advanced separation) can recover >90% of magnet materials but remain uneconomical against China's dumping economics. The US DoD awarded $5.1 million for domestic recycling R&D (2025–2026). DARPA's REACT program seeks synthetic alternatives to REE magnets.

### The Hidden Talent Chokepoint

Since the 1990s, China systematically drove Western REE producers out of business through price manipulation, causing a catastrophic loss of technical expertise. US rare earth employment fell from ~25,000 (pre-1990s) to ~1,500 today, with only ~250 degreed scientists/engineers remaining vs. ~4,000 in the 1980s. Rebuilding the intellectual capital may take a decade or more.

### The "Critical Minerals Cold War" (2026)

The Skillings.net article (2026) frames the situation explicitly: despite billions in IRA and EU subsidies, China maintains a structural chokehold. The West is building parallel processing chains but they remain "thin, concentrated, and exposed to a small number of highly strategic assets."

## 3. What I Think Is Interesting

**The brittleness paradox**: The more the West builds processing capacity, the more each individual node becomes a single point of failure. A nation-state adversary need only disrupt one or two plants to cause disproportionate downstream effects.

**The gap between "we're building" and "we're independent"**: MP Materials and Lynas are real progress, but their offtake agreements still lock some output to Chinese processors, and heavy rare earth separation is essentially nonexistent outside China. The timeline for true independence (2028+) is a talking point, not a guarantee.

**The hidden intellectual capital crisis**: Most analysis focuses on physical infrastructure, but the loss of technologists is arguably more damaging. You can build a separation plant in 2–3 years; you can't rebuild a generation of expertise that fast.

**Quantified vulnerability changes the conversation**: The SSRN paper's vulnerability indices (down to specific weapons platforms) give defense planners actual numbers to argue for stockpiling, substitution research, and supply chain investment. The Chinese simulation paper treats rare earths as a *structural strategic deterrent* — a non-kinetic weapon capable of disrupting deployment tempos.

## 4. What I'd Explore Next

1. **Rare earth recycling at scale**: What are the actual economics of urban mining of rare earth magnets from hard drives, EVs, and wind turbines? When does recycling become competitive without subsidies?
2. **Heavy rare earth substitution research**: Who is working on Dy/Tb-free permanent magnets? DARPA REACT program details, ARPA-E REACT projects.
3. **Greenland and Ukraine deposits**: Both have significant rare earth potential. What's the extraction timeline? Who controls the mineral rights?
4. **REE smuggling networks**: With export controls in place, how do rare earths move through black/grey markets? Vietnam, Myanmar, and Central Asia as transit points.
5. **Global magnet manufacturing capacity**: Even if the West separates REEs, can it make magnets? The sintering process is dominated by Chinese firms (JL MAG, etc.).

## 5. Cross-Domain Connections

- **Electric Utility & Critical Infrastructure**: REE permanent magnets are essential for grid-scale wind turbine generators and high-efficiency transformers. Grid modernization depends on REE availability.
- **Hardware & Physical Computing**: Semiconductor manufacturing equipment uses REE-based components; FPGA and GPU substrates require high-purity rare earths.
- **Markets & Financial Analysis**: REE commodity pricing is inherently geopolitical. Understanding supply/demand dynamics for NdPr, Dy, Tb is critical for investors in defense and energy sectors. Lynas (ASX: LYC) and MP Materials (NYSE: MP) are direct plays.
- **Sanctions Effectiveness**: REE smuggling networks mirror Iranian oil evasion patterns (shell companies, intermediary jurisdictions). Cross-application of sanctions evasion detection methodology.
- **Entity Resolution**: Tracking corporate registries of REE middlemen and shell companies across Hong Kong, Singapore, UAE, and African transit hubs.
- **Privacy & Cryptography**: Zero-knowledge proofs for supply chain provenance verification could prevent conflict minerals from entering defense supply chains.
- **Defense Sector Consolidation**: Rearmament cycles (AUKUS, European defense spending) create immediate demand pressure on REE magnet supply.
- **Agentic AI Self-Learning**: This research pattern — corpus search → web gap-filling → synthesis → memory — is itself a demonstration of the agentic research workflow. The cross-domain connections surfaced organically by allowing the agent to follow threads.

---

## Sources

1. Exocortex shared corpus: v16/wiki/semiconductor-supply-chain-geopolitics.md, v17/wiki/rare-earth-supply-chains.md, v17/wiki/geopolitics-strategic-analysis.md, v16/field-reports/2026-05-23_rare_earth_supply_chain_geopolitics.md, v17/wiki/supply-chain-economic-warfare.md
2. SSRN 6208379: "Defense Platform Vulnerability Assessment: Quantifying Rare Earth Supply Chain Risks Across Major Weapons Systems" (2026)
3. arXiv:2505.21579: "Modeling the Path of Structural Strategic Deterrence..." (2025)
4. Skillings.net: "Rare Earths Supply Chain — Navigating the 2026 US-China Cold War"
5. Materials Dispatch, 2026 structural analysis
6. Reuters, October 2025: China expands rare earth export controls
7. Rare Earth Exchanges, 2026: NdPr market share estimates
