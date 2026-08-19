# Quantum Key Distribution for Critical Infrastructure

**Status:** STABLE
**Created:** 2026-06-01
**Last Updated:** 2026-06-01
**Interest Domain:** Privacy & Cryptography / Electric Utility & Critical Infrastructure
**Primary Sources:** 14/14 verified
**Cross-Domain Links:** 5/5

---

## Overview

Quantum Key Distribution (QKD) uses quantum mechanics to enable two parties to produce a shared random secret key. Any eavesdropping on the key exchange disturbs the quantum states, revealing the intrusion with information-theoretic security guarantees. For critical infrastructure operators, QKD promises future-proof security for control system communications against both classical and quantum computing threats, though practical deployment faces distance limitations, cost barriers, and integration challenges with existing OT/IT networks.

## Current Deployment Landscape (2025-2026)

### Commercial Systems
- **Toshiba** developed high-speed compact QKD transmitter-receiver system for satellite deployment (Jan 2026)
- **Quantum Corridor + Toshiba** demonstrated first cross-state QKD over live commercial metro fiber network (Dec 2025)
- **KETS Quantum Security** completed hardened QKD prototype for critical infrastructure, funded by £1.7M UK SBRI government contract (Apr 2025)
- **QNu Labs** offers deployment-proven CV-QKD and DV-QKD systems
- **IonQ Romania** completed largest operational terrestrial QKD network in Europe (Feb 2026), national infrastructure deployment

### Grid-Specific Deployments
- **China Academy of Sciences (2025):** Pre-generated and distributed quantum keys to D2D encryption devices for power grid delay-sensitive services, eliminating QKD handshake latency
- **Verbund (Austria):** Leading European utility exploring QKD for grid communications (WEF Quantum for Energy 2026 report)
- **DOE grid communication system:** Under evaluation for QKD deployment on US grid communications
- **EuroQCI (2026):** Coordinated procurement across 27 EU states for quantum secure communications; operational phase includes terrestrial and space segments

### Network-Level QKD (2026)
- **IET Research (2026):** Network-level QKD deployment challenges identified — scalability, trusted node architecture, and integration with existing OT protocols remain key barriers
- **Think WIoT (2026):** European quantum secure communications operational deployment analysis; QKD viable for high-value metropolitan grid assets only
- **Hybrid PQC+QKD Model:** Most viable near-term path — PQC for authentication and bulk encryption, QKD for key distribution on critical links

### European Infrastructure Deployment
- **IonQ Romania (Feb 2026):** Delivered one of the largest operational QKD networks in Europe for Romania National Quantum Communication Infrastructure, terrestrial fiber across multiple cities
- **EuroQCI (2026):** Coordinated procurement/deployment phase across 27 EU Member States; terrestrial fiber + space-based satellite segments under simultaneous development; next-phase consultation May-June 2026
- **Ireland QCI:** National quantum communication infrastructure deployment aligned with EuroQCI framework

## Technology Readiness

| Component | TRL | Notes |
|-----------|-----|-------|
| Fiber-based QKD (metropolitan) | 7-8 | Commercially deployed, limited to ~100-200km without trusted repeaters |
| Satellite-to-ground QKD | 6-7 | China Micius proven; Toshiba Jan 2026 system pre-production |
| Grid QKD integration | 4-5 | arXiv 2510.15248 techno-economic framework; IEEE 10845578 multi-scenario model |
| Trusted repeaters | 4-5 | Research stage; limits practical distance without quantum repeaters |
| Quantum repeaters | 2-3 | Fundamental physics challenge; no deployed system |

## Relevance to Critical Infrastructure

### Power Grid Security Use Cases (per IEEE 10845578, OSTI 2538187)
- **Substation-to-substation key exchange:** Encrypt IEC 61850 GOOSE/SV messages with QKD-derived keys
- **SCADA control channel security:** Protect IEC 60870-5-104 commands with information-theoretic security
- **AMI smart meter aggregation:** Secure meter data concentrator communications
- **Wide-area monitoring systems:** Phasor measurement unit (PMU) data integrity

### Integration Challenges
- **Distance limitation:** Fiber QKD degrades beyond ~200km; grid communications span larger areas
- **Trusted node risk:** Intermediate repeaters break end-to-end quantum security model
- **Latency constraints:** Real-time protection relays operate in milliseconds; QKD key rate must exceed consumption
- **Existing fiber utilization:** Coexistence with active OT traffic on same fiber pairs is technically feasible but adds cost
- **IEC 62351 alignment:** QKD provides key management but must integrate with existing power systems security standards

## Techno-Economic Assessment

### arXiv 2510.15248 — Integrated Feasibility Framework
- Stochastic system model evaluates QKD for secure power-system communications
- Key finding: QKD cost per km exceeds PQC migration for most use cases, but hybrid QKD+PQC offers defense-in-depth
- Optimal deployment: metropolitan areas with high-value grid assets (substation clusters, control centers)

### Juniper Research QKD 2025 Assessment
- Vendors should combine QKD with PQC for hybrid solutions
- PQC provides authentication and bulk encryption; QKD provides key distribution
- Current QKD market limited to government, defense, and high-value infrastructure sectors

## Failure Modes & Limitations

1. **Distance limitation:** Fiber QKD key rate drops exponentially with distance; beyond ~200km key generation becomes impractical without trusted repeaters
2. **Trusted node vulnerability:** Intermediate nodes in multi-hop QKD networks must be physically secured — defeats information-theoretic promise
3. **Key rate vs consumption mismatch:** Grid protection relays may consume keys faster than QKD generates them under attack conditions
4. **Coexistence with OT traffic:** Wavelength division multiplexing adds noise; active fiber pairs reduce QKD key rate by 30-50%
5. **Cost per km:** Significantly exceeds PQC migration for equivalent security improvement
6. **IEC 62351 protocol integration gap:** QKD provides key material but IEC 62351-3 TLS-based auth does not natively support quantum key injection; custom adapter layer required
7. **Real-time key rate mismatch:** Grid protection relays operate in milliseconds; QKD key generation under high-loss conditions (rain, fiber aging) may drop below consumption threshold triggering fallback to classical crypto
8. **Supply chain concentration:** QKD hardware vendors limited (Toshiba, ID Quantique, QNu Labs, KETS); single-source dependency risk for critical infrastructure with 10-20 year asset lifecycles

## Cross-Domain Connections

- [post-quantum-critical-infrastructure](post-quantum-critical-infrastructure.md) — PQC vs QKD tradeoff for grid operators
- [cyber-physical-infrastructure-security](cyber-physical-infrastructure-security.md) — OT security architecture context
- [grid-edge-ai-digital-twin-critical-infra-draft](grid-edge-ai-digital-twin-critical-infra-draft.md) — Grid modernization framework
- [trusted-execution-environments-privacy-preserving-ml](trusted-execution-environments-privacy-preserving-ml.md) — Alternative hardware trust approach
- [quantum-safe-edge-computing-critical-infrastructure](quantum-safe-edge-computing-critical-infrastructure.md) — Complementary quantum-safe edge approach

## Verified Primary Sources

| # | Source | Year | Key Finding |
|---|--------|------|-------------|
| 1 | PatSnap Eureka QKD 2026 | 2026 | Global QKD deployment landscape; CAS pre-generation for power grid |
| 2 | Juniper Research QKD 2025 | 2025 | Market assessment; hybrid QKD+PQC recommendation |
| 3 | Toshiba Satellite QKD System | Jan 2026 | Compact high-speed QKD for satellite deployment |
| 4 | Quantum Corridor + Toshiba Cross-State Demo | Dec 2025 | First cross-state QKD over live commercial metro fiber |
| 5 | WEF Quantum for Energy and Utilities 2026 | 2026 | Verbund Austria grid QKD exploration; utility roadmap |
| 6 | KETS UK SBRI QKD Prototype | Apr 2025 | £1.7M government-funded hardened QKD for critical infrastructure |
| 7 | arXiv 2510.15248 Techno-Economic Feasibility | 2025 | Stochastic model for QKD in power systems; cost analysis |
| 8 | IEEE 10845578 Multi-Scenario QKD Power Grid | 2025 | QKD implementation framework for smart grid security |
| 9 | OSTI 2538187 QKD Smart Grid Applicability | 2025 | Use case mapping: substations, SCADA, AMI, PMU |
| 10 | Nature s44287-025-00238-7 Global QKD | 2025 | Comprehensive review of global QKD deployment status |
| 11 | IonQ Romania QKD Network | Feb 2026 | Largest operational terrestrial QKD network in Europe; national infrastructure |
| 12 | EuroQCI 2026 Operational Phase | 2026 | Coordinated procurement across 27 EU states; terrestrial+space segments |
| 13 | Think WIoT EuroQCI 2026 Outlook | 2026 | European quantum secure comms operational deployment analysis |
| 14 | IET QKD Networks Design Challenges | 2026 | Network-level QKD deployment challenges; scalability analysis |
| 15 | IonQ Romania National QKD Network | Feb 2026 | Largest operational terrestrial QKD network in Europe; national infrastructure deployment |
| 16 | EuroQCI 27-State Procurement | 2026 | Coordinated EU quantum secure communications; operational phase with terrestrial+space segments |
| 17 | Think WIoT European QKD Analysis | 2026 | QKD viable for high-value metropolitan grid assets only; economic justification vs PQC |
| 18 | IET Network-Level QKD Challenges | 2026 | Scalability, trusted node architecture, OT protocol integration barriers |

## Open Questions

1. Can QKD integrate with existing IEC 60870-5-104/IEC 61850 protocols without violating real-time latency requirements?
2. What is the TRL gap between lab QKD demonstrations and field-deployed systems in harsh industrial environments?
3. How does QKD cost per km compare to NIST PQC migration timeline for grid operators?
4. Can QKD be deployed on existing fiber pairs without disrupting active OT communications at acceptable key rates?
5. Will quantum repeaters reach TRL 5+ within the 2030-2035 window before quantum computers threaten current grid crypto?

## Key Insight

QKD for critical infrastructure is a **defense-in-depth complement to PQC, not a replacement**. The techno-economic analysis (arXiv 2510.15248) shows QKD makes sense only for high-value metropolitan grid assets where key rate and distance are manageable. The hybrid model — PQC for authentication and bulk encryption, QKD for key distribution on critical links — is the most viable near-term path. The fundamental bottleneck is not QKD technology maturity (TRL 7-8 for metro fiber) but **economic justification against PQC migration** and integration complexity with existing OT protocols.
