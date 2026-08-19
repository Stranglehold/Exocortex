# Orbital Geopolitics & Space Domain Awareness

**Status:** STABLE
**Created:** 2026-08-01
**Deepened:** 2026-08-01 (BUILD cycle)
**Domain:** Geopolitics & Strategic Analysis / OSINT
**Related:** Satellite imagery alt-data, defense procurement, maritime gray zone, GNSS/infrastructure, local-to-frontier, entity resolution, alternative data

---

## Overview

SDA = track, characterize, attribute objects/activity in orbit. 2026: defense niche -> dual-use critical infrastructure. Four forces (SpaceInsider 2026): (1) congestion ~2,000->~10,200 active sats since 2019; (2) counterspace threats (ASAT, co-orbital, EW, directed energy, cyber); (3) debris cascade (Kessler); ESA: 700-1,000 km band near long-term instability threshold; (4) commercialization (Slingshot, LeoLabs, NorthStar). Geopolitical layer: great-power competition with public evidence trail (TLE, manifests, RF/optical signatures) exploitable via OSINT methods.

## Orbital Congestion & Megaconstellations

- Scale: KeepTrack (2026-04-06): 10,168 Starlink active of 10,177 tracked - largest fleet ever built. Broader catalog counts vary by coverage: Orbital Radar (2026) cites 18,000+ active satellites and ~29,000 catalogued objects.
- Smallsats challenge SSA: high object counts, maneuverability, low radar cross-section (Springer Handbook of Small Satellites).
- Blind spots below cm catalog grade; SPOT passive optical tomography (arXiv:2211.13040v2) targets sub-cm debris.
- ESA 2026 Space Environment Report (FODNews summary): LEO collision risk up 20%; ~1.2 million untrackable debris fragments; 550 km band crowding is a driver.
- 2026-05-18 close approach: OBJECT C / OBJECT D (NORAD 56155/56156), 1.39 km minimum separation, medium severity (Orbital Radar) - routine conjunction events are now a public-data stream.

## Debris Cascade & Conjunction Risk

- ESA modeling: 700-1,000 km band near long-term instability threshold (Kessler-adjacent regime).
- WEF "Clear Orbit, Secure Future" (2026-01-28): non-trackable debris (1-10 cm) can cause mission-ending damage; short-term call to action on active debris removal and space traffic management.
- NASA Conjunction Assessment (CA) protects primary assets against known secondary objects - analytic pipeline of orbit determination -> covariance -> close-approach prediction.
- Blind spots: catalog-grade cutoffs leave 1-10 cm debris untracked; ML risk-classification of conjunction events is an active research area (EPJ Web of Conferences 2026).

## Orbital Mechanics Grounding (library)

The library corpus (impracticalpythonprojects, Ch.14) supplies the mechanics behind maneuver analytics:
- Orbit = continuous free-fall; changing orbit requires burns (Hohmann transfer: two impulsive burns, minimal fuel; one-tangent burn: faster, less efficient; spiral transfer: continuous low-thrust).
- Implication for SDA: any object doing proximity operations will show up as TLE/orbit changes. Fuel-intensive (high delta-v) maneuvers are detectable - this is how the Cosmos 2610-2613 case was characterized (fuel-intensive approach to a Western satellite).
- Prograde/retrograde burns raise/lower orbits; chase maneuvers use inner-track (lower) orbits - a classic reconnaissance pattern.

## Counterspace Threat Taxonomy (2026)

SWF 2026 Global Counterspace Capabilities Report: 13 countries x 5 categories (co-orbital, direct-ascent, EW, directed energy, cyber).

- May 2026: Russia fuel-intensive maneuvers placed Cosmos 2610-2613 near a Western commercial radar satellite supporting Ukraine imagery intel (USSF Space Threat Fact Sheet).
- GSSAP maneuverable near-GEO inspection satellites blur the line between benign inspection and co-orbital weapon.
- A 2026 UN space nuclear weapons resolution failed — Outer Space Treaty regime contested.
- Maneuver fingerprinting is the OSINT-relevant layer: orbit changes are public (TLE), so high-delta-v approach patterns are detectable without classified data; the Cosmos case was characterized from fuel-intensive maneuver profiles.

## Orbital Object Attribution: The OSINT Layer

SDA is structurally entity resolution: catalog ID (NORAD/COSPAR) + owner-operator + launch event + maneuver history + RF/optical signature. Mapping to the Exocortex ER pipeline (Fellegi-Sunter, temporal tracking).

- Attribution chain: TLE catalog -> launch manifest -> deployment band -> operator beacons/RF signature -> behavior (maneuvers, station-keeping) = the same sliding-window temporal correlation used in maritime shadow-fleet analysis.
- Public catalog + alert products (Space-Track TLEs; Orbital Radar) make close approaches a public data stream — e.g., OBJECT C/D 2026-05-18, 1.39 km min separation, NORAD 56155/56156, medium severity.
- Failure-mode case: UAP misidentification (arXiv:2403.08155v3) — TLE+ADS-B reconstruction proved a Starlink train was the cause; same reconstruction pattern serves incident attribution.

## Commercial SSA Market (2026)

- GM Insights: SSA market ~$1.8B (2025), 5.1% CAGR 2026-2035.
- Grand View: LEO SSA $667.3M (2025) -> $711M (2026) -> $991.7M (2033), 4.9% CAGR; North America 39.6% share (2025).
- Blacknight Space Labs: commercial SDA projected to reach $7B by 2033; sensor-vs-software business model split (LeoLabs sensors; Slingshot/ExoAnalytic software+analytics).
- newspaceeconomy (2026-03-30): data alone losing value — fused analytics, trust, and sovereign access win contracts; cislunar tracking moving from research topic to funded procurement.
- Office of Space Commerce extended TraCSS Consolidated Pathfinder; new commercial SSA data orders via NASA Global Data Marketplace with all five participating companies.

## Space Governance & Treaty Contestation

- Outer Space Treaty (1967) regime contested: 2026 UN space nuclear weapons resolution failed; ASAT and co-orbital capabilities remain outside explicit ban.
- WEF "Clear Orbit, Secure Future" (2026-01-28): debris remediation + space traffic management as collective-action problem; non-trackable 1-10 cm debris as mission-ending risk.
- TraCSS (US OSC) represents the emerging sovereign STM/SSA data layer — a government procurement signal for commercial SSA providers.

## Cross-Domain Connections

1. Markets: insurance/launch cadence alt-data; newspaceeconomy.ca 2026 space defense market analysis; scope at $1.8B (2025, GM Insights) with 5.1% CAGR — small but high-signal alt-data niche.
2. OSINT: orbital object attribution = entity resolution over TLE/catalog/RF/optical records; maneuver fingerprints echo maritime shadow-fleet playbook.
3. Defense Procurement: USSF SSA programs (GSSAP), commercial SSA contracts (TraCSS) via defense-procurement-cycles lens.
4. Maritime Gray Zone: GNSS spoofing/jamming detection transfers directly; dark-vessel ~ dark-satellite detection.
5. Critical Infrastructure: GNSS/PNT dependency shared vulnerability (navigation warfare); 1-10 cm debris as mission-ending risk (WEF 2026).
6. AI Agent Architecture: on-orbit edge AI (NASA Prithvi GEO May 2026), attention-based satellite segmentation for in-orbit SSA (IEEE 10667688); ML risk classification of conjunctions (EPJ 2026).
7. Intelligence Analysis: SSA = GEOINT+RF+cyber fusion; maps to fusion-centers/multi-INT architecture.
8. Entropy-as-Signal: maneuver anomalies / telemetry drift in SSA streams as entropy signals; close-approach alerts as public anomaly stream.
9. Alternative Data: satellite imagery alt-data pipeline is the demand-side consumer of SSA launch/constellation data.
10. Supply Chain: megaconstellation launch cadence and debris risk affect space insurance and downstream EO data supply.

## References

1. Secure World Foundation, 2026 Global Counterspace Capabilities Report — 13 countries, five categories.
2. SpaceInsider (2026-06-18), "What Is Space Domain Awareness (SDA)? A 2026 Guide".
3. US Space Force Space Threat Fact Sheet — Cosmos 2610-2613 May 2026 close approach.
4. KeepTrack X Report (2026-04-06) — 10,168 Starlink active of 10,177 tracked.
5. ESA debris modeling — 700-1,000 km band long-term instability threshold.
6. FODNews — ESA 2026 Space Environment Report: LEO collision risk +20%, ~1.2M untrackable fragments.
7. Orbital Radar — OBJECT C/D close approach 2026-05-18, NORAD 56155/56156, 1.39 km, medium severity.
8. WEF "Clear Orbit, Secure Future: A Call to Action on Space Debris" (2026-01-28).
9. arXiv:2403.08155v3 — Starlink/UAP misidentification, TLE+ADS-B reconstruction.
10. arXiv:2211.13040v2 — SPOT sub-cm debris detection.
11. Springer Handbook of Small Satellites — smallsats vs SSA/STM.
12. IEEE 10667688 — attention-based satellite segmentation for in-orbit SSA.
13. GM Insights — SSA market $1.8B (2025), 5.1% CAGR 2026-2035.
14. Grand View Research — LEO SSA $667.3M->$991.7M (2025->2033).
15. Blacknight Space Labs — commercial SDA to $7B by 2033; sensor-vs-software business models.
16. newspaceeconomy.ca (2026-03-30) — SSA market analysis; fused analytics/trust/sovereign access.
17. Office of Space Commerce — TraCSS Consolidated Pathfinder extension; NASA Global Data Marketplace orders.
18. EPJ Web of Conferences 2026 — ML-based risk classification of space debris conjunction events.
19. impracticalpythonprojects (library, Ch.14 Orbital Mechanics) — Hohmann/one-tangent/spiral transfer mechanics for maneuver analysis.
20. Exocortex corpus: satellite-imagery-osint; sanctions-evasion-detection (GNSS spoofing); sigint-evolution-corona-to-commercial-imagery; ai-geospatial-intelligence-foundation-models-2026-draft; maritime-logistics-gray-zone.

## Verification Status

- Corpus: exocortex search_memory (SDA/orbit) 51 matches; key hits maritime GNSS spoofing detection, commercial EO constellations, Prithvi in-orbit AI.
- Library: search_library returned one citable mechanics source (orbital transfers) and general satellite/ocean monitoring only; 355-book corpus lacks dedicated astropolitics titles — genuine gap, noted honestly.
- Web: search_engine queries (SDA 2026; commercial SSA market) supplied ESA/WEF/Orbital Radar/market-research/OSC citations. Claim-level verification limited to listed sources; market figures are vendor estimates.
