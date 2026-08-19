# Maritime AIS OSINT & Dark Fleet Monitoring

**Status: STABLE**
**Created: 2026-08-14 | Last Updated: 2026-08-14**
**Domain: OSINT & Investigation Methodology / Geopolitics & Strategic Analysis**
**Topic Slug: maritime-ais-osint-dark-fleet**

## Overview

Maritime AIS OSINT is the systematic use of Automatic Identification System (AIS) data - positions, identities, courses, speeds, destinations - to track vessels, detect deception, and expose sanctions-evasion logistics. AIS is a self-reported broadcast protocol: vessels transmit unauthenticated VHF messages (161.975/162.025 MHz) with identity (MMSI, IMO, callsign), position, course, speed, draught, and voyage data. The protocol is mandatory for vessels over 300 GT on international voyages (SOLAS), but its integrity is the fundamental blind spot: the system trusts the transmitter, so it is trivially spoofable, suppressible, and fabricatable. This page is the maritime sibling of [[ads-b-signal-integrity-osint]]: both are self-reported RF broadcast protocols whose integrity can be independently verified only by fusing other sensing modalities.

This page fills a corpus gap: prior wiki coverage (supply-chain-network-analysis-osint, maritime-logistics-gray-zone, russian-oil-price-cap-sanctions-enforcement, software-defined-radio-osint) referenced AIS and dark fleets but had no dedicated treatment of AIS OSINT methodology, evasion taxonomy, or detection fusion.

## 1. AIS Protocol Fundamentals

- **Physical layer**: VHF transceiver + GPS; broadcasts at 161.975 MHz (AIS 1) and 162.025 MHz (AIS 2) over TDMA slots; range ~20-40 nm terrestrial, global via satellite constellation (SAT-AIS).
- **Message types**: position reports (Class A: every 2-10 s underway, 3 min anchored; Class B: 5 s-3 min), static/voyage data (MMSI, IMO, callsign, ship name, type, dimensions, destination, ETA, draught).
- **Identity hierarchy**: MMSI (radio ID, changeable), IMO number (permanent hull ID - the stable entity anchor), callsign/flag (registrable). Entity-resolution anchor is the IMO number, equivalent to a corporate registry ID.
- **Regulatory frame**: SOLAS mandates AIS for >=300 GT international voyages; VTS requires AIS operation in territorial waters. Designed for collision avoidance, not law enforcement - hence the integrity gap.

## 2. Dark Fleet Evasion Tactics Taxonomy

1. **Going dark** - AIS transponder deactivation (power cut, "technical fault"), especially on route legs where illicit STS transfer or sanctioned-port call occurs.
2. **Identity manipulation** - false MMSI/callsign/flag changes, repeated re-registration to flags of convenience; IMO number sometimes illegitimately changed in registries.
3. **Position spoofing** - GNSS/GPS spoofing feeds false coordinates into AIS; message replay of another vessel's position.
4. **Voyage manipulation** - falsified destination, draught, or cargo declarations; "unknown destination" fields.
5. **Ship-to-ship (STS) transfers in international waters** - crude/product transfer outside territorial waters; the primary vector for Russian/Iranian/Venezuelan oil evasion (Kpler: STS transfers as core evasion vector).
6. **Flag/ownership layering** - shell-company ownership chains, opaque beneficial ownership, parallel corporate registries.
## 3. Detection & Verification Methodology (Fusion Stack)

A single AIS broadcast is unverifiable; trust emerges only from cross-modal fusion:

1. **AIS continuity & behavioral anomaly analysis**
   - Signal dropout in transit (dark gaps) vs. normal coverage loss — distinguish by comparing against SAT-AIS coverage maps.
   - Impossible kinematics (speed/heading changes at anchor), loitering near known STS zones.
   - Kpler: AIS anomalies on ~1,000 sanctioned vessels were reliable early indicators of subsequent enforcement action.
2. **Satellite SAR** — Capella, ICEYE, Sentinel-1: cloud-penetrating, night-capable radar ship detection independent of AIS; confirms physical presence during dark periods.
3. **Optical satellite imagery** — Planet Pelican 50cm class: sub-meter resolution enables vessel classification and cargo assessment (deck configuration, STS transfer visuals) when AIS is off (Planet Labs Maritime Domain Awareness, Feb 2026).
4. **Ship-to-ship transfer inference** — AIS rendezvous detection (vessels within ~1 nm, slow relative motion, prolonged co-anchorage) + optical/SAR confirmation.
5. **Identity reconciliation** — cross-reference MMSI, IMO, callsign, flag, port call records, insurance/classification databases for consistency (Fellegi-Sunter entity-resolution logic).
6. **Port call & cargo records** — customs, port state control, bill-of-lading, and satellite verification of hidden port calls.

This mirrors the IEEE OSINT Framework for Maritime Surveillance (2025): AIS + port records + satellite imagery to detect AIS blackouts, STS transfers, and falsified destinations.

## 4. Empirical Landscape (2026)

- Windward Analytics: ~76% of Windward-tracked dark-fleet crude tankers are now sanctioned vessels; dark fleet uses AIS manipulation, false flags, and spoofed positions.
- Shadow fleet scale: ~1,300 vessels (65% of seaborne Russian crude at price-cap era); average vessel age ~17 yrs vs ~9 yrs for regulated tonnage (per russian-oil-price-cap-sanctions-enforcement).
- Venezuela seizure case (Dec 2025): demonstrated dark-fleet visibility improvement via satellite + AIS correlation.
- CSIS AIS classification framework: behavioral/anomaly taxonomy applied to Iranian shadow fleet architecture (maritime-logistics-gray-zone).

## 5. Tool Ecosystem

| Tier | Tools | Notes |
|---|---|---|
| Free/OSINT | MarineTraffic, VesselFinder, FleetMon, AISHub | Terrestrial + some SAT coverage, API limits, historical gaps |
| Professional | Spire, Kpler, Windward, Pole Star, Lloyd's List Intelligence | Global SAT-AIS, dark-fleet analytics, risk scoring |
| RF/SDR | RTL-SDR + rtl-ais decoders, OpenCPN | Direct VHF reception for shore/coastal collection (per software-defined-radio-osint) |
| Satellite | Planet (optical), Capella/ICEYE (SAR), ESA Copernicus Sentinel-1 | Independent verification layer |

## 6. Exocortex Integration

- AIS→SAR→corporate registries→crypto forensics→entity resolution pipeline is the shared sanctions-evasion detection playbook across Russia/Iran/DPRK (three-regime convergence field work).
- Dark-fleet AIS anomaly signals map to entropy-as-signal anomaly monitoring: unusual kinematics/dark gaps are the maritime analogue of token-level predictive entropy spikes.
- The self-reported-broadcast integrity problem is structurally isomorphic to LLM unverified outputs: verification requires a second, independent channel (SAR/optical for AIS; execution/validation for LLM).

## 7. Cross-Domain Connections

1. [[ads-b-signal-integrity-osint]] — sibling self-reported broadcast protocol; direct template for integrity OSINT.
2. [[russian-oil-price-cap-sanctions-enforcement]] — dark fleet as evasion surface.
3. [[maritime-logistics-gray-zone]] — chokepoint taxonomy, CSIS AIS classification, Iranian shadow fleet.
4. [[satellite-imagery-osint]] — optical/SAR verification layer.
5. [[software-defined-radio-osint]] — direct RF collection of AIS/ADS-B.
6. [[supply-chain-network-analysis-osint]] — shipping/logistics tracking methodology.
7. [[entity-resolution-confidence-calibration]] — IMO/MMSI identity reconciliation.
8. [[crypto-asset-tracing-blockchain-forensics-osint]] — AIS→SAR→crypto settlement pipeline.
9. [[entropy-as-signal]] — anomaly detection isomorphism.
10. [[intelligence-failures-strategic-surprise]] — dark gaps as warning signals.

## 8. Honest Gaps & Future Explorations

- arXiv specialist search (cs.LG/cs.AI/cs.CR, 2026-08-14) returned no focused AIS anomaly-detection papers — the ML AIS anomaly frontier (vessel-trajectory anomaly detection, generative dark-fleet simulation) is under-covered in open literature or outside searched categories; revisit with different query variants ("vessel trajectory" / "maritime traffic").
- Library grounding was generic marine electronics (Ocean Instrumentation, Electronics, and Energy: AIS/VHF/GPS/VTS fundamentals); no dedicated maritime-surveillance text was mounted.
- STS transfers in international waters are legal for non-sanctioned cargo — care needed to avoid false attribution.

## References

1. Vijayalakshmi, S.R. & Muruganand, S. — Ocean Instrumentation, Electronics, and Energy (2021): AIS/VHF/GPS/VTS fundamentals, pp. 289-331. [Library: humble_bundle]
2. IEEE OSINT Framework for Maritime Surveillance (2025) — cited in supply-chain-network-analysis-osint corpus.
3. Windward Analytics — dark fleet research (76% sanctioned crude tankers), 2025-2026.
4. Kpler — AIS spoofing analysis (~1,000 sanctioned vessels; STS transfers as primary evasion vector).
5. Planet Labs — Maritime Domain Awareness via Planet Pelican 50cm optical (Feb 2026).
6. Capella Space / ICEYE — SAR vessel detection.
7. CSIS — AIS Classification Framework (maritime-logistics-gray-zone).
8. russian-oil-price-cap-sanctions-enforcement (wiki) — shadow fleet composition.
