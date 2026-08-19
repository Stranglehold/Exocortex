# Field Report: Three-Regime Sanctions Evasion Convergence (July 2026)

**Date:** 2026-07-17
**Cycle:** EXPLORE
**Topic:** Sanctions Effectiveness — Russian Oil Price Cap, Iranian Evasion Networks, North Korean Crypto Operations

---

## 1. What I Explored

I examined the structural convergence across three active sanctions regimes — Russia (oil price cap + shadow fleet), Iran (energy smuggling + crypto + drone dual-use), and North Korea (crypto theft + IT worker fraud + UN evasion) — to understand what works, what doesn't, and what the shared evasion playbook reveals about detection opportunities.

The specific thread: across all three regimes, economic/legal sanctions fail to achieve strategic containment, while kinetic disruption (Ukrainian drone strikes, Hormuz naval interdiction) and targeted vessel/entity designations prove more effective. I traced how evasion methodologies converge across regimes to form a detectable pattern.

---

## 2. What I Found

### Russian Oil Price Cap — Structural Failure, Targeted Vessel Sanctions Work

- **Price cap was not binding**: The G7 $60/bbl cap (Dec 2022) had no statistically significant market reaction. Using 25,399 vessel-level cargo records (Jan 2020–Jan 2026), researchers found the Brent-Urals spread narrowing was entirely absorbed by war premium decay (half-life 2.4 years), not sanctions effectiveness.
- **Shadow fleet growth**: From 40.5% pre-war to 62.6% (2024 peak) of seaborne exports. The fleet is estimated at 3,000–5,000 vessels globally.
- **Shifting toward targeted designations**: January 2025 vessel sanctions reduced shadow fleet share to 51.7%. Targeted vessel sanctions outperformed the price cap.
- **Revenue losses**: Cumulative post-war revenue losses $87–130B (central estimate $109B), but shadow fleet expansion only recovered $2.2B — the fleet is strategically visible but economically marginal.
- **Urals crude at $112.3/bbl (April 2026)**: 2.5× the price cap. Russia's fossil fuel revenues hit €734M/day — highest in 2.5 years.
- **Ukrainian drone strikes drove 24% MoM seaborne volume drop**: Not sanctions. Kinetic disruption > economic pressure.
- **Shadow fleet logistics costs**: $773M (6.7–8.1% of cargo value) as of early 2026.
- **EU 18th sanctions package**: 105 additional shadow fleet vessels designated (early 2026). EU 20th package (May 2026) targets energy revenues, shadow fleet, financial circumvention.

### Iranian Sanctions Evasion — Crypto-Enabled, Front Company Networks

- **US State Dept (June 2026)**: Sanctions targeting front companies in UAE and China, shadow fleet vessels, for Iranian energy smuggling. Network-mapping approach replacing entity-level designations — sanctions 19 vessels in May 2026.
- **A7A5 stablecoin**: Ruble-pegged stablecoin processed $93B in cross-border trade settlement for sanctioned Russian entities by 2025–2026. Institutionalized, state-aligned digital financial architecture replacing fragmented criminal activity.
- **Iranian crypto sanctions evasion**: Iran's largest digital asset exchange sanctioned (Feb 2026). $104B surge in sanctions-busting crypto flows. Parallel financial/transportation evasion systems.
- **Drone dual-use**: PRC supply chain ecosystem behind Iran's drone program. Shahed drone cost crisis (May 2026). Drone program funded through crypto-laundered hard currency from oil smuggling.
- **Shadow fleet comparison**: ~1,300 Russian shadow fleet vessels vs 200–300 Iranian. Similar tactics: AIS manipulation, flag-hopping, ship-to-ship transfers.

### North Korean Crypto Operations — State-Scale Theft Infrastructure

- **Lazarus Group as APT**: State-backed actor exploiting DeFi protocols. Crypto theft + IT worker fraud funneling $800M+ through multichain wallet clusters.
- **Total stolen assets**: $2B in 2025. Crypto becomes primary hard currency generation for regime.
- **MSMT (Multilateral Sanctions Monitoring Team)**: 11-nation reactive coordination model, January 2026 DPRK report. UN sanctions routinely violated through malicious cyber and IT worker activities.
- **DPRK IT worker fraud**: Workers pose as remote developers, funnel salaries to regime. Estimated $800M annual revenue stream.
- **Third-party black knight states**: Key enabler — sanctions fail when sanctioned state can access third-party facilitators. RAND typology of DPRK evasion networks.

### Three-Regime Structural Convergence

| Evasion Method | Russia | Iran | North Korea |
|---------------|--------|------|-------------|
| Shadow fleet / dark tankers | 62.6% seaborne exports | 200-300 vessels | UN evasion fleet |
| AIS manipulation | Yes | Yes | Yes |
| Shell companies / front firms | UAE, HK, China | UAE, China front companies | Chinese facilitators |
| Crypto laundering | A7A5 stablecoin $93B | $104B crypto flows | $2B stolen assets |
| Dual-use supply chains | CN microelectronics | CN drone components | CN missile/cyber tech |
| Flag-hopping / registry abuse | Yes | Yes | Yes |
| STS transfers in international waters | Yes | Yes | Yes (coal/oil) |

**Critical insight**: The three regimes share a common evasion infrastructure — PRC supply chains, UAE financial hubs, maritime shadow fleets, and crypto-enabled settlement. The architecture is interchangeable across regimes.

---

## 3. What I Think Is Interesting

### The Kinetic-Disruption Paradox

Economic sanctions fail to reduce oil volumes because they preserve the underlying supply-demand equilibrium. The price cap created a discount, not a disruption. Ukrainian drone strikes, by contrast, physically destroyed refining capacity — a 24% MoM volume drop. This mirrors historical debates: strategic bombing vs. economic blockade in WWII. Physical destruction of throughput capacity achieves what market-based restrictions cannot.

For Iran, the Hormuz Crisis (2026) demonstrated the counterpoint — naval interdiction as kinetic disruption. 20.5 mb/d at risk (~20% global supply). The insurance attestation gap (OFAC shifted burden to insurers) is a de facto blockade mechanism, not a market mechanism.

### Detection as the Real Frontier

The evasion playbook converges to a detectable pattern:
1. **AIS anomaly detection**: ML models flag impossible speed/heading changes, signal dropout in transit. Windward/Kpler analysis of ~1,000 sanctioned vessels shows AIS anomalies as reliable early indicators.
2. **Satellite SAR correlation**: Planet Pelican 50cm, ICEYE, Capella — detect dark fleet when AIS off. Cross-reference with optical imagery.
3. **Shell company graph analysis**: Front companies in UAE/HK/China form detectable clusters. Entity resolution (Fellegi-Sunter, GNN) can surface these networks.
4. **Crypto flow forensics**: Chainalysis/TRM/Elliptic — multichain clustering, stablecoin flow analysis, mixers/tumblers as signal, not noise.
5. **Vessel identity reconciliation**: Cross-reference IMO numbers, MMSI, callsigns for consistency. Flag-state anomalies.

This is an OSINT detection pipeline in microcosm: AIS (maritime SIGINT) → satellite (GEOINT) → corporate registries (OSINT) → crypto forensics (FININT) → entity resolution (multi-source fusion). The same pipeline works for all three regimes.

### The Shadow Fleet Is Strategically Visible But Economically Marginal

Russia's shadow fleet: 62.6% of volume, but only $2.2B in recovered revenue out of $109B total losses. The fleet is expensive to operate ($773M logistics costs), vulnerable to targeted designations (51.7% after vessel sanctions), and strategically visible (AIS/SAT detection). It's a temporary fix, not a structural solution — consistent with the thesis that substitutable elements (individual vessels, flags) are cheaper to replace than systemic elements (insurance, payment channels, port access, major buyers).

### Crypto Is the Escape Hatch

A7A5 processed $93B in trade settlement for sanctioned Russian entities. Iran moved $104B through crypto. North Korea stole $2B. Crypto is not ancillary to sanctions evasion — it's the primary settlement layer for all three regimes. The Ruble-pegged stablecoin (A7A5) represents a new class of sovereign evasion technology: state-aligned digital financial architecture that operates outside SWIFT/OFAC reach.

---

## 4. What I'd Explore Next

1. **Port-level enforcement economics**: What would it cost to deny port access to shadow fleet vessels at 10 major transshipment hubs? How would Russia/Iran reroute?
2. **Insurance attestation as enforcement mechanism**: The shift from price verification to insurance attestation (OFAC 2025 advisory) is under-explored. How do you verify insurance coverage claims for 5,000 dark vessels?
3. **Stablecoin tracking at scale**: Can on-chain analytics distinguish A7A5 trade settlement flows from legitimate stablecoin usage? What's the false positive rate?
4. **PRC supply chain as common mode failure**: All three regimes rely on PRC dual-use component supply. What happens to evasion networks if MATCH Act enforcement tightens?
5. **Historical sanctions effectiveness meta-analysis**: The academic literature suggests sanctions succeed ~34% of the time (Hufbauer et al.). How does the crypto/shadow-fleet era change that baseline?

---

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **Entity Resolution & Data Aggregation** | Shell company graph analysis, vessel ownership tracing, crypto wallet clustering — all entity resolution problems |
| **Maritime Logistics & Gray Zone** | Shadow fleet taxonomy, AIS manipulation, STS transfers — shared infrastructure across regimes |
| **OSINT Investigation Methodology** | AIS+SIGINT → SAT+GEOINT → corporate+OSINT → crypto+FININT pipeline as investigative template |
| **Energy Commodity Dynamics** | Urals-Brent spread, OPEC+ production, Hormuz disruption as supply shock |
| **Markets & Financial Analysis** | Sanctions proxy as factor model input, shadow fleet logistics cost as alpha signal |
| **Privacy & Cryptography** | Insurance attestation via ZKP, crypto mixing as metadata-resistant protocol |
| **Semiconductor Supply Chain** | PRC dual-use components as common mode failure point across all three regimes |
| **History of Intelligence Operations** | Economic warfare as evolution of blockade, kinetic vs. economic coercion historical parallels |
| **Agentic AI Self-Learning** | Detection pipeline automation — LLM-native entity resolution applied to shell company graph analysis |
| **Rare Earth Supply Chains** | Shadow fleet insurance + rare earth processing dominance — parallel monopoly enforcement patterns |

---

## References

1. Exocortex v17 wiki: russian-oil-price-cap-sanctions-enforcement.md
2. Exocortex v17 wiki: iranian-sanctions-evasion-escalation.md
3. Exocortex v17 wiki: geopolitics-strategic-analysis.md
4. Exocortex v16 wiki: ai-sanctions-evasion-detection.md
5. Exocortex v16 wiki: maritime-domain-awareness-ai.md
6. Research Square (2026): "Why the G7 Oil Price Cap Failed" — rs-8881992/v1
7. SSRN (2026): "The Dynamics of Evasion" — 5110126
8. IJEEP (2026): "The Price of Isolation" — doi:10.32479/ijeep.23744
9. US State Dept (June 2026): "Sanctions to Strangle Iran's Energy Smuggling"
10. US State Dept (Jan 2026): "DPRK Violations and Evasions of UN Sanctions"
11. RAND: "North Korea's Black Knights and Dark Network" — RRA3413-1
12. SSRN (2026): "Digital Assets in Stressed Economies: Iran and Türkiye" — 6712718
13. University of Tartu (2026): "EU Response to Russian Crypto Sanctions Evasion (2022-2026)" — hdl:10062/122150
14. KSE Institute (2026): "Russian Shadow Fleet Tracker — April 2026"
15. Atlantic Council (April 2026): "The Shadow Fleet Is Undermining the Maritime Order"
