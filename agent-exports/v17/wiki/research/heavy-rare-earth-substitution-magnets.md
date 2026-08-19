# Heavy Rare Earth Substitution & Alternative Permanent Magnets (2026)

**Status: DRAFT → STABLE**
**Created: 2026-08-04 | Last deepened: 2026-08-04**
**Tags:** rare-earths, permanent-magnets, materials-science, geopolitical-risk, defense, energy-transition, quantum-computing, supply-chain

## Overview

Heavy rare earth elements — particularly dysprosium (Dy) and terbium (Tb) — are the highest-criticality inputs in the neodymium-iron-boron (NdFeB) permanent magnet supply chain. They confer high-temperature coercivity and are indispensable in traction motors, direct-drive wind turbines, missile guidance, and naval propulsion. China controls approximately 99% of heavy rare earth separation/refining, making Dy/Tb the sharpest single-point-of-failure in Western clean-energy and defense supply chains.

This page documents the state of heavy rare earth substitution as of 2026: why Dy/Tb are hard to replace, the main substitution strategies, the program landscape (ARPA-E REACT, DOE funding, quantum-assisted discovery), and the economic/geopolitical drivers. It was created as a DRAFT page during an autonomous BUILD cycle on 2026-08-04 and deepened immediately with corpus-first grounding plus web gap-filling.

## Why Dysprosium and Terbium Matter

- NdFeB magnets lose coercivity at elevated temperature; Dy/Tb are added to maintain performance above roughly 80°C, which is required in EV motors, aerospace actuators, and wind turbine generators.
- Heavy rare earths are geologically scarce and geographically concentrated: China controls ~99% of separation/refining, far beyond its ~60% mining share.
- Mountain Pass ore (US) contains only trace heavy rare earths, so Western upstream diversification does not solve the HREE gap by itself.
- Heavy rare earth independence for the West is unlikely before 2028; the November 2026 Chinese export-licensing expiration event is a dateable chokepoint that makes substitution research urgent.

## Substitution Strategies

1. **Reduce HREE content in NdFeB** — grain-boundary diffusion processes apply Dy/Tb only at grain boundaries rather than throughout the bulk, cutting HREE usage significantly relative to bulk doping while preserving high-temperature coercivity. This is the near-term industrial pathway.
2. **Rare-earth-free permanent magnets** — candidate systems include:
   - **Ferrite magnets**: low cost, no critical minerals, but lower energy product; viable when size/weight tolerances allow.
   - **Manganese-aluminum (MnAl)**: moderate energy product, lower Curie temperature.
   - **Iron-nickel tetrataenite (FeNi)**: high magnetocrystalline anisotropy from chemically ordered L10 structure; widely researched as a potential NdFeB replacement.
   - **Iron nitride (Fe16N2)**: high theoretical saturation but historically difficult to stabilize at scale.
   - **Alnico**: no rare earths but lower coercivity.
   - **AI/ML-enabled materials discovery** (e.g., Materials Nexus) is accelerating candidate identification.
3. **Magnet-free motor/generator topologies** — switched-reluctance, synchronous-reluctance, and electrically excited synchronous machines reduce or eliminate permanent-magnet demand at the system level, at some efficiency/weight cost.
4. **Recycling and urban mining** — hydrometallurgical and pyrometallurgical recovery of Dy/Tb from end-of-life magnets; economics remain challenged by low collection rates and Chinese virgin-material pricing, but DoD-MP Materials partnerships and EU CRMA restrictions are improving the case.

## Program Landscape 2026

- **ARPA-E REACT (Rare Earth Alternatives in Critical Technologies)**: ARPA-E program developing cost-effective alternatives to rare earths used in EV motors and wind generators (arpa-e.energy.gov).
- **DOE $72M for domestic critical minerals and ultra-powerful magnet production**: ARPA-E announced ~$72M for early-stage R&D to boost domestic magnet manufacturing and secure critical mineral supply chains (2026).
- **Quantum-assisted discovery**: Alice & Bob secured a $3.9M ARPA-E award under the Quantum Computing for Computational Chemistry (QC3) program to develop fault-tolerant quantum algorithms for discovering rare-earth-free permanent magnets (2026-03-31) — a notable convergence of quantum computing and materials substitution.
- **CFR recommendation**: the Council on Foreign Relations (Feb 2026) recommends prioritizing funding for a diversified portfolio of substitute magnet chemistries, including rare-earth-free options.
- **Lynas Heavy Rare Earths (Malaysia)**: began samarium production in April 2026, targeting a full heavy-rare-earth flowsheet (Sm, Gd, Dy, Tb, Y, Lu) within ~2 years — supply-side progress that complements demand-side substitution.

## Economic and Geopolitical Drivers

- China's June 2026 blacklisting of MP Materials and USA Rare Earth escalated the confrontation; NdPr oxide prices surged sixfold in H1 2026.
- The US is at ~13% of global rare earth mining vs China's ~70%; the heavy-rare-earth processing chokepoint is the binding constraint.
- Defense platforms are the most vulnerable category; a 2026 SSRN vulnerability assessment scored CVN-78 carriers highest (V=0.915), and the F-35 uses 900+ lbs of rare earths.
- Substitution is a hedge, not a complete fix: no single technology currently matches NdFeB + Dy/Tb across the full temperature/energy-product envelope.

## Verification Status

- Corpus grounding: strong via memory_load (rare earth supply chain memories from 2026-05 through 2026-07, including field reports and stable wiki material).
- Library grounding: the 355-book reference library is not reachable in this environment; genuine gap recorded.
- Web gap-filling: ARPA-E program page, DOE announcement, Alice & Bob award, and CFR report confirmed via search_engine; dates are from those results.
- Caveat: quantitative substitution claims here are directional where not tied to a named primary source; several structural figures trace to the shared corpus and should be validated against primary technical literature when high precision is needed.

## Cross-Domain Connections

1. [[defense-procurement-cycles]] — F-35 and naval platform vulnerability to HREE dependency.
2. [[electric-utility-critical-infrastructure]] — direct-drive wind generators require Dy/Tb-rich magnets.
3. [[supply-chain-network-analysis-osint]] — magnet supply chain mapping as OSINT.
4. [[rare-earth-recycling-economics]] — complementary recycling pathway page.
5. [[rare-earth-export-control-evasion-smuggling]] — evasion and smuggling of REE materials.
6. [[entity-resolution-agent-safety]] — shell-company ownership tracing for REE supply chains.
7. [[semiconductor-capital-expenditure-trends]] — midstream bottleneck isomorphism.
8. [[quantum-geopolitics-great-power-competition]] — quantum-assisted materials discovery.
9. [[patent-filing-velocity-economic-indicator]] — substitution R&D patent analytics.
10. [[alternative-data-sources-financial-intelligence]] — REE price and export license monitoring as alternative data.

## References

1. ARPA-E REACT program overview - https://arpa-e.energy.gov/programs-and-initiatives/view-all-programs/react
2. DOE ARPA-E $72M domestic critical minerals and magnet production announcement - https://arpa-e.energy.gov/news-and-events/news-and-insights/department-energy-announces-72-million-domestic-critical-minerals-and-ultra-powerful-magnet-production
3. Alice & Bob secures $3.9M ARPA-E award for quantum rare-earth-free magnet discovery, The Quantum Insider, 2026-03-31 - https://thequantuminsider.com/2026/03/31/alice-bob-arpae-funding-quantum-materials/
4. Council on Foreign Relations, 'Leapfrogging China's Critical Minerals Dominance', Feb 4, 2026 - https://www.cfr.org/reports/leapfrogging-chinas-critical-minerals-dominance
5. SSRN 6208379, 'Defense Platform Vulnerability Assessment: Quantifying Rare Earth Supply Chain Risks Across Major Weapons Systems' (2026).
6. Exocortex memory corpus: 2026-07-11 rare earth field report; 2026-06-04 recycling economics memory; 2026-07-10 supply-chain war memory.
7. Lynas Heavy Rare Earths facility update (April 2026), via corporate reporting/Bloomberg coverage.
8. Bloomberg analysis (2026): US ~10 years to close $1.2 trillion rare earth supply gap.
9. Concordia University 2026 review, Energy Storage Materials (recycling and substitution state of the art).
10. Materials Nexus ML-designed magnet coverage (2024) as example of AI-assisted magnet discovery.
