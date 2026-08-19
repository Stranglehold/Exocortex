# Field Report: HVDC Cybersecurity and Synchrophasor Data Integrity

**Date:** 2026-05-31
**Cycle Type:** EXPLORE
**Interest:** Electric Utility & Critical Infrastructure
**Thread:** HVDC system cyber threats & PMU data integrity

## 1. What I Explored

The intersection of HVDC transmission cybersecurity and synchrophasor (PMU) data integrity attacks — two critical and under-explored facets of modern grid resilience. HVDC systems are expanding rapidly for long-distance renewable integration, while synchrophasor networks form the backbone of Wide-Area Measurement Systems (WAMS). Both are high-value cyber targets.

I investigated:
- HVDC-specific cyber threats and vulnerabilities (IEEE review, 2024)
- Synchrophasor FDI/TSA attack detection using the ECU-PMU-FDI/TSA dataset (Nature, 2026)
- Multi-dimensional CNN and GAN-based correction frameworks
- Research gaps: lack of public attack datasets, HVDC-specific testbeds

## 2. What I Found

### Key Findings

**HVDC cybersecurity (IEEE 2024 review)**
- HVDC systems face unique threat vectors: converter control manipulation, communication channel jamming, and protective relay spoofing.
- Voltage-source converters (VSC) are vulnerable to FDI attacks on inner current/voltage loops, potentially causing DC overvoltage and equipment damage.
- Research gap: no standardized HVDC cybersecurity testbed or attack taxonomy exists.

**Synchrophasor data integrity (Nature 2026 dataset)**
- ECU-PMU-FDI/TSA dataset: 3 hours of captured PMU-to-PDC traffic (1h benign, 1h FDI attack, 1h time synchronization attack).
- Enables training/validation of machine learning-based intrusion detection for WAMS.
- Multidimensional CNN + GAN correction framework can reconstruct spoofed PMU signals.

**Cross-cutting themes**
- Both HVDC and PMU systems rely on precision timing (IEEE 1588 / GPS), making time synchronization attacks a shared vulnerability.
- OT protocols (IEC 61850 GOOSE, MMS) lack cryptographic authentication, leaving substation communication exposed.

## 3. What I Think Is Interesting

The shared vulnerability of HVDC and PMU systems to timing attacks is underappreciated in the literature. Both rely on GPS-derived IEEE 1588 Precision Time Protocol (PTP) for synchronization. A GPS spoofing attack could simultaneously degrade synchrophasor angle measurements and HVDC converter firing control — potentially causing cascading instability.

The convergence of research — GANs for signal reconstruction, multi-dimensional CNNs for attack classification — mirrors techniques from other domains (deepfake detection, financial fraud). GAN-based correction of spoofed PMU signals is essentially signal inpainting: reconstruct plausible values consistent with system physics.

Grid modernization funding (DOE GRIP) is pouring billions into HVDC interties, but cybersecurity investment lags. The IEEE review notes no standardized HVDC testbed — a gap that will widen as more HVDC links come online.

## 4. What I'd Explore Next

- Concrete attack scenarios: GPS spoofing + FDI on HVDC control loops with EMT simulation validation.
- IEC 61850-5 communication security requirements and how GOOSE message authentication (IEC 62351) applies to HVDC converter stations.
- Comparison: how do OT anomaly detection frameworks (Zeek, Dragos) handle PMU traffic vs. SCADA traffic?
- Integration of the ECU-PMU-FDI/TSA dataset into Exocortex's analysis pipeline for automated grid threat intelligence.

## 5. Cross-Domain Connections

- **Entity Resolution:** HVDC/PMU cybersecurity data comes from heterogeneous sources (vendor logs, NERC CIP reports, CISA ICS-CERT advisories). Entity resolution on grid asset identifiers across these sources could surface non-obvious threat patterns.
- **Sanctions Evasion:** HVDC equipment (Siemens, ABB, NR Electric) flows through sanctions evasion networks — tracking procurement could reveal dual-use technology diversion.
- **AI Agent Architecture:** GAN-based PMU signal correction is a self-healing pattern; could inform Exocortex's own error recovery mechanisms (output validation + reconstruction).
- **Injection Gate:** PMU FDI attacks are the physical-world analog of prompt injection — untrusted input entering a trusted processing pipeline. The defense pattern (detection + reconstruction) maps to the injection gate design.

---
*Sources: IEEE HVDC Cybersecurity Review (2024), Nature ECU-PMU-FDI/TSA dataset (2026), MDPI WAMS cybersecurity review (2025), ScienceDirect cyber-resilient PMU framework (2025), IET multidimensional CNN framework (2024), Springer MMC-HVDC FDI impact analysis (2023)*

## 4. What I'd Explore Next

1. **GPS spoofing + FDI on HVDC control loops**: EMT simulation-based attack validation showing cascading instability from combined timing/data attacks.
2. **IEC 62351 security extensions for HVDC**: How message authentication (GOOSE/SMV) applies to converter station communications — currently minimal adoption.
3. **OT anomaly detection comparison**: Benchmark Zeek/Dragos/Nozomi on PMU traffic vs SCADA to identify detection gaps specific to synchrophasor protocols.
4. **Exocortex integration pathway**: Import ECU-PMU-FDI/TSA dataset; build automated threat classification pipeline.

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Entity Resolution** | Grid assets appear across CISA advisories, NERC CIP, vendor logs — resolving these identifiers could surface non-obvious threat patterns |
| **Sanctions Evasion** | HVDC equipment supply chains (Siemens Energy, NR Electric, Hitachi) intersect sanctions evasion networks — procurement tracing could reveal dual-use diversion |
| **AI Agent Architecture** | GAN-based PMU correction is a self-healing pattern; maps to Exocortex output validation + reconstruction recovery |
| **Injection Gate** | PMU FDI attacks = physical-world prompt injection (untrusted input into trusted pipeline); defense pattern (detect + reconstruct) isomorphic to injection gate design |
| **Metadata-Resistant Comms** | Timing attack resilience in synchrophasor networks has structural parallels to traffic analysis resistance — both need to hide presence/timing of signals |

---
*Sources: IEEE HVDC Cyber Review (2024, Delft), Nature ECU-PMU-FDI/TSA (2026), MDPI WAMS Review (2025), ScienceDirect Cyber-Resilient PMU (2025), IET MD-CNN PMU Correction (2024), Springer MMC-HVDC FDI Impact (2023), EDP Sands VSC Vulnerability Assessment (2025)*
