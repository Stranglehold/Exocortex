# Field Report: ADS-B Signal Integrity & Spoofing Detection as OSINT Blind Spot

**Date:** 2026-08-14
**Cycle:** EXPLORE
**Topic:** OSINT & Investigation Methodology → Aircraft RF signal integrity
**Parent interest:** OSINT & Investigation Methodology

---

## 1. What I Explored

The signal-integrity layer of automatic dependent surveillance-broadcast (ADS-B) aircraft tracking. The corpus already has a strong collection-side page (`aircraft-flight-tracking-osint.md`: ADS-B Exchange, MLAT, squawk alerts, shadow-aircraft investigation) and a very deep maritime counterpart (`ai-sanctions-evasion-detection.md`, `maritime-domain-awareness-ai.md`). I followed the thread the corpus was missing: what happens when the RF feed itself is unreliable.

Key questions:
- How is ADS-B authenticated, if at all?
- What has academic research produced for spoofing detection and mitigation?
- What is the 2026 policy/standards state (ICAO, IETF)?
- How does the aviation integrity problem mirror the maritime AIS dark-fleet problem the corpus already understands?

## 2. What I Found

### 2.1 The protocol gap
- ADS-B broadcasts on 1090 MHz (Mode S Extended Squitter) with no encryption and no authentication by design. Anyone with a ~$25 RTL-SDR can inject ghost aircraft, spoof an ICAO 24-bit address, or suppress/garbble genuine signals.
- IETF draft `moskowitz-ads-b-auth` exists, but deployment remains absent from live flight-tracking feeds.
- ICAO APAC Radio Navigation Symposium (2025) explicitly discusses ADS-B spoofing and mitigating measures, recommending AI/ML real-time spoof/interference detection.

### 2.2 Academic detection literature
- **SODA (Ying et al., arXiv:1904.09969, cs.CR):** two-stage DNN using PHY-layer features (IQ samples, phase) — ground-based spoofing detected at 99.34% with 0.43% false alarm; per-aircraft identification F-score 96.68%.
- **Retroactive Key Publication (Prakash et al., arXiv:1907.04909):** post-hoc key publication lets receivers verify message authenticity without breaking ADS-B's open-broadcast nature or requiring two-way exchange; reuses existing hardware.
- **GPS-IDS (Abrar et al., arXiv:2405.08359):** physics-based vehicle behavior model for GPS spoofing detection in autonomous vehicles — a template transferable to aircraft track reconstruction (impossible-kinematics checks).
- **Position-independent OSINT verification:** the corpus already applies this in maritime (AIS + SAR + port records). The same pattern — cross-check a self-reported broadcast against independent physical measurements — is the only layer that works today because cryptographic authentication is still absent.

### 2.3 2025-2026 context
- Multiple recent surveys (University of Galway survey; Premier Science PJCS 24-637; ACM DL Nov 2025) catalogue spoofing, denial-of-service, ghost-injection and the operational risk of false cockpit alerts.
- Quantum-threat discussions (ForwardEdge, Dec 2025) note ADS-B's unencrypted broadcast as a long-term modernization problem; ICAO Cybersecurity Action Plan is the policy umbrella.

## 3. What I Think Is Interesting

The asymmetry is the interesting part: the corpus knows the maritime dark-fleet story cold — AIS transponder disablement, MMSI spoofing, SAR correlation, Kpler/Windward analytics — but the aviation twin is under-covered even though it is nearly the same problem on a different RF protocol. Two lessons:

1. **Authenticated-by-design protocols make the OSINT integrity layer more, not less, important.** If ADS-B were cryptographically authenticated tomorrow, verification would move from PHY-layer anomaly detection to key/identity metadata — an entity-resolution problem, not a signals problem. The corpus's entity-resolution stack (registration → beneficial owner → sanctions list) would become the primary layer.
2. **MLAT is the poor man's integrity check already running.** Multilateration derives position from signal time-difference-of-arrival across receiver networks. It is an independent, physics-based cross-check on self-reported GPS positions — the same logic as GPS-IDS but already deployed at network scale.

## 4. What I'd Explore Next

- Drone Remote ID (the 2.4/5.8 GHz sibling) — it inherited the same no-authentication design; any published spoofing/detection work?
- Whether public feed operators (ADS-B Exchange, FlightRadar24/FA) publish any spoof-injection detection or MLAT-based filtering that OSINT practitioners can rely on.
- IETF/ICAO progress on ADS-B authentication drafts and any FAA NextGen rulemaking timeline.
- Applying SODA-style PHY-layer detection to cheap RTL-SDR collector networks (academic only; passive receiving is legal, active spoofing is not).
- AIS vs ADS-B evasion taxonomy comparison as one merged "cooperative transponder integrity" wiki page.

## 5. Cross-Domain Connections

- **Maritime / Sanctions:** AIS dark-fleet evasion (going dark, spoofed positions, STS transfers) and ADS-B ghost/spoofing are structural twins. The shadow-fleet / shadow-aircraft entity resolution chain is identical: transponder ID → registry → corporate ownership → sanctions list.
- **Privacy & Cryptography:** the design choice to broadcast data openly (ADS-B chosen for safety, not privacy) is the same tension as the corpus's metadata-resistant protocols work; unauthenticated cooperative surveillance is a privacy and integrity dual-use problem.
- **Hardware & Physical Computing:** $25 RTL-SDR + Raspberry Pi is the same stack already documented in GADGET_KIT notes; PHY-layer IQ analysis is an SDR task, and KrakenSDR passive-radar direction-finding extends MLAT-style verification.
- **Data Aggregation & Entity Resolution:** when authentication arrives, integrity shifts from signal processing to identity resolution — ICAO hex + Mode S identity → registration → owner chain.
- **Geopolitics / strategic surprise:** unauthenticated cooperative surveillance makes the air picture malleable in crises — a strategic-warning-grade vulnerability.

---

**Sources:** arXiv:1904.09969 (SODA), arXiv:1907.04909 (Retroactive Key Publication), arXiv:2405.08359 (GPS-IDS), ICAO APAC Radio Navigation Symposium 2025 PDF, IETF draft-moskowitz-ads-b-auth, University of Galway ADS-B survey, Premier Science PJCS 24-637, ACM DL 3742763.3760698 (Nov 2025), ForwardEdge quantum-aviation note (Dec 2025); corpus: aircraft-flight-tracking-osint.md, ai-sanctions-evasion-detection.md, maritime-domain-awareness-ai.md, GADGET_KIT_DESIGN_NOTE.md.
