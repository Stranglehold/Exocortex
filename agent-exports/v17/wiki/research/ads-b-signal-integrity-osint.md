# ADS-B Signal Integrity & Spoofing Detection for OSINT

**Status:** STABLE
**Created:** 2026-08-14
**Topic:** OSINT & Investigation Methodology → Aircraft RF signal integrity
**Grounding sources:** corpus-first (Exocortex shared memory / GADGET_KIT_DESIGN_NOTE, Flight Science book, Kali Linux cookbook dump1090, software-defined-radio-osint.md, aircraft-flight-tracking-osint.md) + EXPLORE field report 20260814 + arXiv specialist.

---

## 1. Overview

Automatic Dependent Surveillance-Broadcast (ADS-B) is the cooperative surveillance backbone of modern air traffic control: aircraft broadcast their identity (ICAO 24-bit address), position (WGS-84 from GPS), altitude, velocity, and call sign every ~0.5 s on 1090 MHz (Mode S Extended Squitter) with no encryption and no authentication. The signal is a broadcast by design; any receiver can decode it with a ~$25 RTL-SDR and open-source software (dump1090, readsb). For OSINT this is a rich collection surface: uncensored feeds (ADS-B Exchange, OpenSky Network, Icarus Flights) enable dark-aircraft detection, shadow-airline sanctions-evasion investigation, and military logistics tracking (see `aircraft-flight-tracking-osint.md`).

This page covers the layer the collection-side pages do not: **what happens when the RF feed itself is unreliable.** If the ADS-B picture is malleable, every downstream investigative conclusion — no-fly-zone monitoring, sanctions-evasion attribution, air-order-of-battle assessment — inherits that fragility. The aviation problem is structurally the same as the maritime AIS dark-fleet problem: a self-reported broadcast protocol with no integrity layer, exploited by adversaries and misunderstood by consumers of the data.

## 2. The Protocol Gap

- **No authentication, no encryption, by design.** ADS-B (1090ES) was standardized for open cooperative surveillance. Transmissions are unverified self-reports.
- **The gap is exploitable at low cost:** a ~$25 RTL-SDR (receive) and a cheap TX-capable SDR (HackRF ~$300) are enough to inject ghost aircraft, spoof an ICAO 24-bit address, or replay/suppress genuine signals. The non-cryptographic 24-bit CRC only detects random bit errors, not deliberate forgery.
- **Standards attempts remain unimplemented in live feeds.** IETF draft `moskowitz-ads-b-auth` proposes post-hoc authentication (see Section 3). ICAO APAC Radio Navigation Symposium (2025) explicitly discusses ADS-B spoofing and recommends AI/ML real-time spoof/interference detection — a recommendation, not a mandate.
- **History:** the insecurity was documented at least since Costin & Francillon (2012) — the issue is not new, which makes the continuing absence of mitigation a strategic choice about backward compatibility and cost, not an oversight.

### 2.1 Attack taxonomy

| Attack class | Mechanism | OSINT impact |
|---|---|---|
| Ghost aircraft injection | Forge valid-looking squitters from a ground station | Phantom presence in feeds; false-alarm confusion in conflict monitoring |
| ICAO address spoofing | Reuse a real 24-bit address on a different target | Misattribution: real tail number vs actual emitter |
| Replay/meaconing | Record and re-broadcast genuine signals elsewhere | Apparent aircraft in two places; timeline forgery |
| Suppression/garbling | Transmit interference or garble to hide a real target | Deliberate blackout — the OSINT-relevant evasion |
| Position manipulation | Fake position reports (kinematically impossible) | Wrong geospatial conclusions; fake alerts |

## 3. Detection & Trust Restoration Literature

- **SODA (Ying et al., arXiv:1904.09969, cs.CR):** two-stage DNN using PHY-layer features (IQ samples, phase) — ground-based spoofing detected at 99.34% with 0.43% false alarm; per-aircraft identification F-score 96.68%. Demonstrates that physical-layer fingerprints can separate genuine emitters from impostors (RF fingerprinting).
- **Retroactive Key Publication (Prakash et al., arXiv:1907.04909):** post-hoc key publication lets receivers verify message authenticity without breaking ADS-B's open-broadcast nature or requiring two-way exchange; designed to reuse existing hardware. This is the practical compromise between unauthenticated broadcast and full PKI.
- **GPS-IDS (Abrar et al., arXiv:2405.08359):** physics-based vehicle behavior model for GPS spoofing detection in autonomous vehicles — a transferable template for aircraft track reconstruction via impossible-kinematics checks (cf. maritime AIS anomalous speed reports 81-101 knots).
- **University of Galway ADS-B survey** and **Premier Science PJCS 24-637**: survey-grade summaries of the academic spoofing-detection landscape (2024-2025).
- **ACM DL 3742763.3760698 (Nov 2025):** recent ADS-B security/ML detection work surfaced in the field report.
- **ForwardEdge quantum-aviation note (Dec 2025):** quantum-resistant direction for future ADS-B authentication; forward-looking, not deployed.

## 4. The Maritime AIS Mirror (Cross-Domain Template)

The corpus already models an identical problem in the maritime domain (`maritime-logistics-gray-zone.md`):

- **AIS manipulation** — disabling, spoofing, or jamming Automatic Identification System signals; false identity broadcasting; duplicating codes of scrapped vessels ("zombie" tactics).
- **Empirical impact:** during the 2026 Hormuz crisis, AIS underreported actual vessel presence by up to 50% (Citrini Research); anomalous speed reports (81-101 knots) consistent with AIS spoofing were detected on struck vessels.
- **Mature countermeasure stack:** CSIS behavioral anomaly classification (filtering ~12,000 vessels to 128 likely gray-zone actors), SAR/EO satellite cross-referencing, RF direction finding, entity resolution across shell companies/flag registries/beneficial ownership.

**Transferable lesson:** the aviation counterpart should pre-build the same multi-INT validation stack — MLAT triangulation of Mode S even when ADS-B position is suppressed, satellite/optical cross-referencing, kinematics plausibility filters, RF fingerprinting, and entity-level attribution hooks. Note: the field report cited `maritime-domain-awareness-ai.md`; that file does not exist on disk — the live cross-link page is `maritime-logistics-gray-zone.md` (honest gap).

## 5. OSINT Methodology Implications

1. **Feed integrity triage:** before relying on an ADS-B-derived conclusion, score the feed: uncensored source? receiver density? any suppression events in the area/time window?
2. **Multi-receiver / MLAT cross-check:** triangulate Mode S beyond ADS-B position; detect geometric inconsistencies.
3. **Kinematics plausibility filtering:** apply impossible-velocity/acceleration/turn-rate filters to every track; flag outliers for manual review (GPS-IDS template).
4. **RF fingerprinting where possible:** PHY-layer features (SODA-style) distinguish genuine transponders from ground-based impostors.
5. **Cross-INT validation:** satellite imagery, ATC/press releases, radio comms, and surface-mode reporting should agree with the aircraft picture; divergence is the signal.
6. **Adversarial assumption:** in crisis environments, assume the air picture can be selectively suppressed — treat absence of coverage as a finding, not noise.

## 6. Cross-Domain Connections

- [[aircraft-flight-tracking-osint]] — collection-side twin: protocol fundamentals, dark aircraft, evasion/counter-evasion, tool ecosystem.
- [[software-defined-radio-osint]] — RF collection layer: RTL-SDR/HackRF, dump1090/readsb, SDR software ecosystem, RF fingerprinting.
- [[maritime-logistics-gray-zone]] — AIS shadow-fleet manipulation: behavioral anomaly classification, multi-INT validation, entity resolution.
- [[fpga-inference-osint-signal-processing]] — real-time RF decoding/MLAT/PHY-layer inference on FPGA for field-deployed sensors.
- [[geolocation-osint]] — GPS spoofing detection: meaconing, synthetic generation, cross-validation convergence principle (EXIF + IP + visual must agree).
- [[counterintelligence-analysis-frameworks]] — RF deception requires adversarial hypothesis testing (CI-ACH): spoofed feed = deceptive signal.
- [[strategic-warning-osint-early-warning]] — unauthenticated cooperative surveillance makes the air picture malleable in crises: a strategic-warning-grade vulnerability.
- [[intelligence-failures-strategic-surprise]] — feed-suppression as warning-pipeline failure: collection gaps amplified at the decision layer.
- [[autonomous-osint-agent-opsec-attribution-risk]] — RF emissions are entity identity; jamming/spoofing is an attribution risk for agents operating RF sensors.
- [[evidence-preservation-chain-of-custody-osint]] — raw IQ/decoded frames must be hashed and archived to preserve legal value when feed manipulation is contested.

## 7. Research Frontiers (2026)

- Real-time PHY-layer spoof detection inside the receiver/toolchain, not as post-hoc forensics.
- Deployment of retroactive key publication or lightweight authentication without breaking legacy receivers.
- AI/ML anomaly detection recommended by ICAO APAC 2025 — implementation is the open gap.
- Post-quantum authentication (ForwardEdge note) for the long-lived 1090 MHz ecosystem.
- Cross-domain porting of maritime behavioral-anomaly classification (CSIS-style) to aviation tracks.

## References

1. Ying et al., SODA: ADS-B spoofing detection — arXiv:1904.09969 (cs.CR).
2. Prakash et al., Retroactive Key Publication — arXiv:1907.04909.
3. Abrar et al., GPS-IDS: GPS spoofing detection — arXiv:2405.08359.
4. IETF draft-moskowitz-ads-b-auth.
5. ICAO APAC Radio Navigation Symposium 2025 — ADS-B spoofing and mitigation.
6. University of Galway, ADS-B survey.
7. Premier Science, PJCS 24-637.
8. ACM DL 3742763.3760698 (Nov 2025).
9. ForwardEdge AI, quantum-aviation note (Dec 2025).
10. Costin & Francillon (2012), ADS-B insecurity analysis.
11. Citrini Research / Seavantage, Hormuz AIS underreporting (2026), via maritime-logistics-gray-zone.md.
12. Flight Science (Applied Mathematics book library), ADS-B/NextGen/ASBU/SESAR.
13. Kali Linux Ethical Hacker's Cookbook, dump1090 decoding recipes.
14. Exocortex GADGET_KIT_DESIGN_NOTE — RF sensing hardware (RTL-SDR/HackRF/KrakenSDR).
