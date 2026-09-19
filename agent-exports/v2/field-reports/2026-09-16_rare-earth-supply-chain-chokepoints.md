# Rare Earth Supply Chains as Geopolitical Leverage: Chokepoints, Cascades, and the Migration of Power

## What I Explored

I followed one thread this cycle — how China's dominance over rare earth elements (REEs) translates into geopolitical leverage in 2025-2026. Rather than a static "who mines what" tally, I traced two questions:

1. **Structural question**: where exactly does the supply chain break under targeted pressure? — i.e., is it at mine-grade extraction or further up?
2. **Dynamics question**: how does that concentration behave as a network? Does diversification help linearly, or is there a threshold past which leverage flips?

This was chosen because Geopolitics & Strategic Analysis (Eitan's workstream) had been the least-recently-explored active interest — last field report 2026-07-16 — and REEs sit precisely at the intersection of three domains I care about: strategic analysis, complex adaptive systems (cascade/percolation dynamics), and entity-resolution flow-mapping.

## What I Found

### The real chokepoint moved up the value chain
The headline number most people cite — **~91% of global rare-earth refining/separation** (China's second is Malaysia) — understates the problem. Per IEA analysis, China holds ~60% of mine-grade output but its dominance is "even greater in the separation and refining stages." The decision-intel scan sharpens this: **"The Method, Not the Mine"** — the binding chokepoint has migrated to midstream separation, refining, metallisation, and magnet-making, *and* crucially to the process technology that runs them. China's October 2025 MOFCOM controls reportedly include a total ban on exporting the technology to extract, separate, and manufacture rare-earth magnets — "aiming to permanently cripple Western attempts to build competing supply chains."

### The leverage is now temporal (a window, not just capacity)
The most recent policy timeline:
- **Feb 2025**: phased-in tightened export licensing on REEs.
- **Apr 2026**: escalated to cover tungsten and antimony, plus additional rare-earth elements.
- **Extraterritorial rule**: controls reach downstream products (SmCo magnets, NdFeB magnets containing terbium/dysprosium) regardless of where they're made — a jurisdictional reach that complicates allied sourcing.
- **2025-09 / 2026-01**: China "paused" several newly announced controls — a signal that leverage is *applied*, then released, as a bargaining chip. The pause itself is a demonstration of the power: only someone with scarcity can afford to pause.

Price transmission confirmed: gallium +123%, germanium +203%, antimony +144% under controls — hitting US defense and AI-chip supply chains hard. A 6th-order price spike; European licensing cut below 25%. Western response centered on the **FORGE alliance** (Foundation for Reshoring Critical Supply Chains), reported at ~$30B, with an analyst window of only **12-18 months** to diversify.

### The network behaves like a percolating system — fragile but random-resilient
The Miner Economics (Springer 2026) network study is the key finding: the REE trading system is **resilient to random disruption yet acutely fragile to the targeted loss of its most central suppliers** — and that fragility concentrates in midstream refining, not at the mine. The trading lens also reveals a hidden tier: intermediaries like Japan and the US capture large import shares while mining little; single-commodity indices miss this because they count origin, not node centrality.

ScienceDirect's multilayer Rare-Earth Industry-Chain Trade Network (REICTN) model confirms supply risk *propagates* as a cascade: shocks in one layer (refining) flood into magnet and end-product layers simultaneously. JPMorgan's center-for-geopolitics framing, "Breaking the Critical Minerals Chokepoint," generalizes the lesson beyond REEs: governments are defaulting to a mix of public-private partnership, targeted financing, trade tools, and international coordination.

### Diversification is real but threshold-bound — and China moves with the feedstock, not just the metal
IEA data shows mining-share diversification has worked modestly: top-supplier share fell from >90% (2023) to ~85% (2025), projected lower as projects come online. ASEAN Oct 2025 deals (US-Malaysia, US-Thailand on extraction/processing/refining), CSIS's quantitative hubs analysis (identifying US, Australia, Saudi Arabia, Canada as most viable processing centers via 10 criteria), and the Pentagon's $25M equity in ReElement Technologies (Jul 13, 2026) alongside the IEA Global Critical Minerals Outlook 2026 (Jul 16, 2026) signal capital is flowing. But S&P Global grounds this: **China's lead in recycling** — built on established feedstock networks and integrated processing — means Western "diversification through recycling" largely flows back into a system China still controls at the integration layer.

## What I Think Is Interesting

1. **The weaponization regime shifted from 'material' to 'method'.** The October 2025 magnet-extraction technology ban is more durable than any quota on ore — you can build a mine in two years, but you cannot easily retrain the metallurgists or reproduce the process-integration IP. This mirrors how a chokepoint moves: once you control the *process*, the physical asset becomes commoditizable and competitive pressure returns; once you control the *recipe*, competitors are locked out structurally.

2. **The percolation analogy is more than pretty.** A complex adaptive system with a percolation threshold stays robust below criticality but collapses sharply above it. The Miner Economics finding — resilient to random node loss, fragile to targeted chokepoint loss at midstream — is the textbook signature of a network near its connectivity threshold. Diversification (new mines in US/Myanmar/Australia) raises the threshold; China's move up to controlling the *method* effectively re-raises the threshold precisely where diversifiers were about to cross it. This is not metaphor — it's the same mathematics underlying cascade dynamics, flocking, and epidemic spread.

3. **The 'paused' controls are a strategic reveal.** Pausing appears like de-escalation but functions as an assertion of ownership over the global supply: only a holder of genuine scarcity can pause and reset expectations. It converts a one-time weaponization into a standing, repeatable instrument — the leverage becomes institutionalized rather than singular.

4. **Intermediary nodes are invisible to naive indices.** Japan and the US capture high import shares via processing/intermediate layers despite minimal extraction. Any entity-resolution or flow analysis must distinguish *origin* from *node centrality* — a mistake that would underweight China's true chokepoint position by counting mine-grade alone.

## What I'd Explore Next

- **Quantify the threshold**: build a small percolation/ERGM model of the REICTN (ScienceDirect data exists) to estimate where the midstream connectivity threshold sits today — and test whether current diversification projects keep us above or below it. This turns an intuition into a number.
- **The 'method' ban durability**: how much IP/process knowledge is tacit vs patentable? Does China's own ability to export magnets constrain its incentive to permanently lock the recipe? (A Prisoner's-dilemma / commitment-problem framing.)
- **Substitutability as a threshold-shifter**: direct substitution (e.g. dysprosium-free magnets, motor redesigns) vs demand destruction — both push down the leverage. Could track substitutability curves as an inverse chokepoint.
- **Recycling feedstock topology**: map where Western recycling actually routes end-product — back to China's integrated layer (S&P Global claim) or genuinely new? An entity-resolution flow graph across e-waste handlers would settle it.

## Cross-Domain Connections

- **Complex Adaptive Systems (interest #2)**: rare-earth supply chains are a percolating network. Resilience-to-random / fragility-to-targeted-collapse at a midstream chokepoint is the same threshold behavior as cascade dynamics in ecological and social networks. The leverage weaponization (material -> method) re-draws where that threshold sits.
- **Entity Resolution & OSINT (interest #4)**: mapping this supply chain *is* entity resolution — resolving which nodes are true chokepoints vs intermediaries, distinguishing origin from centrality, constructing a multilayer flow graph. The REICTN percolation model is structurally identical to link-analysis / object-resolution in intelligence pipelines.
- **Electric Utility & Critical Infrastructure (interest #7)**: permanent magnets (NdFeB) with dysprosium/terbium are the binding input for grid-scale wind turbines and EV motors — the same magnets that power electrified infrastructure are themselves the chokepoint. My professional domain meets its own supply-chain dependency.
- **Ethics of Capability (interest #5)**: China *can* embargo; should it as a geopolitical tool? The extraterritorial rule on downstream products raises questions about secondary sanctions and whether controlling a public-benefit commodity (clean-energy inputs) via scarcity is a legitimate or destabilizing use of capability — the "just because we can" question at civilizational scale.

## Sourced Material
- IEA: `Rare Earth Elements` report, supply concentration commentary; Global Critical Minerals Outlook 2026 (Jul 16, 2026)
- Miner Economics / Springer 2026: "Supply concentration and cascading disruption risk in the trade of energy-transition minerals: a network approach"
- ScienceDirect 2025: multilayer REICTN supply risk propagation
- JPMorgan Center for Geopolitics: "Breaking the critical minerals chokepoint"
- S&P Global (Apr 2026): rare earth funding, policy, and China's edge (recycling)
- IEA / CSIS / ASEAN Oct 2025 deals; Pentagon $25M ReElement equity (Jul 13, 2026); MOFCOM Oct 2025 magnet-tech technology ban
- arXiv (Smerigan & Shi 2025, 2504.10495 / 2506.22569): recovery-economics grounding — REE supply security from phosphogypsum secondary feedstock
