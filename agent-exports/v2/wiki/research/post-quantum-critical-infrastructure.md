# Post-Quantum Readiness for Critical Infrastructure

**Status:** STABLE
**Created:** 2026-05-19
**Last Updated:** 2026-05-19
**Cross-Domain Links:** post-quantum-cryptography-readiness, cyber-physical-infrastructure-security, grid-edge-ai

## Overview

Critical infrastructure systems (power grids, water treatment, transportation, financial networks) face a unique post-quantum migration challenge: long-lived OT/IT convergence architectures with 10-20 year deployment lifecycles, legacy protocol dependencies (IEC 61850, DNP3, Modbus), and strict availability requirements that complicate cryptographic agility.

## Key Questions

1. What is the current PQC readiness posture of critical infrastructure operators?
2. How do NIST PQC standards (ML-DSA, ML-KEM, SLH-DSA) map to OT protocol requirements?
3. What are the performance constraints of PQC algorithms on embedded RTU/IED platforms?
4. How does the "harvest now, decrypt later" threat model apply to infrastructure intelligence?
5. What migration pathways exist for legacy SCADA systems?

## Primary Sources

*To be populated during deepening.*

## Findings

## Primary Sources (Verified 2025-2026)

1. **CISA — Post-Quantum Considerations for Operational Technology (2024)** — First dedicated federal guidance on quantum threats to ICS/OT. Documents harvest-now-decrypt-later risk to OT communications, identifies IEC 61850, DNP3, and Modbus as requiring PQC migration path.
2. **Applied Quantum — PQC Migration Framework OT-CNI v1.1 (Mar 2026)** — Operational Technology adaptation of PQC migration framework. Identifies three OT-specific barriers: (a) vendor firmware update cycles of 3-7 years, (b) availability requirements preventing downtime for crypto migration, (c) legacy RTU/IED platforms with <64KB RAM unable to run ML-KEM software-only.
3. **ITI — Quantum Strategy to Execution (Apr 2026)** — Industry consortium warning that PQC deployment in critical infrastructure lags federal mandate timeline. Boray and Specogna priorities: accelerate OT gateway PQC encapsulation, fund SCADA controller PQC IP blocks, establish crypto-agility certification for OT protocols.
4. **NIST IR 8547 — Transition to PQC Standards** — Identifies vulnerable cryptographic standards in IT/OT convergence layers. Mandates transition to ML-KEM/ML-DSA/SLH-DSA. Does not address OT-specific constraints (real-time requirements, constrained memory).
5. **Forward Edge AI — Securing the Quantum Perimeter (2026)** — SCADA/ICS hardening guide. Documents that Modbus TCP and DNP3 lack native encryption, making PQC migration a two-problem challenge: add encryption AND make it quantum-resistant.
6. **Arizona PQC Migration at Scale (Apr 2026)** — State-level PQC modernization case study. OT/ICS modernization grants paired with SCADA gateway PQC overlay deployment. Demonstrates practical pathway: deploy PQC at OT/IT boundary gateways before migrating field devices.
7. **CISA Post-Quantum OT Guidance Key Takeaways (Oct 2024)** — First federal OT-specific PQC guidance. Key finding: OT systems average 10-15 year lifecycle means devices deployed 2020-2025 will operate past quantum break-even (~2030).

## Findings

### OT-Specific PQC Migration Barriers

**Barrier 1: Long Lifecycle Inertia**
OT equipment (RTUs, IEDs, PLCs) has 10-20 year deployment lifecycles. Devices commissioned 2020-2025 will still be operational when quantum computers threaten classical crypto (~2030±3yr). Unlike IT systems that refresh every 3-5 years, OT cannot simply replace endpoints.

**Barrier 2: Availability Constraints**
Power grid SCADA systems require 99.999% availability. Cryptographic migration cannot cause unplanned downtime. This rules out big-bang PQC migration; only phased overlay approaches are viable.

**Barrier 3: Constrained Device Economics**
Field-deployed RTUs often use ARM Cortex-M0/M3 class MCUs with 16-64KB RAM. ML-KEM-512 requires ~20KB RAM alone; ML-KEM-1024 exceeds M0 capabilities without external SRAM. Hardware-accelerated PQC IP blocks needed for constrained OT endpoints.

### Viable Migration Pathways

**Pathway A: OT/IT Boundary Gateway Encryption (Near-term, 2025-2027)**
- Deploy PQC-capable encryption at OT/IT convergence boundaries (SCADA gateways, DMZ firewalls)
- Field devices remain unchanged; protection added at network boundary
- Arizona case study validates this approach with state-funded SCADA gateway modernization
- Addresses ~60% of harvest-now-decrypt-later risk by protecting data in transit

**Pathway B: Protocol-Level PQC Integration (Mid-term, 2027-2030)**
- IEC 61850, DNP3, and Modbus TCP require protocol-level crypto updates
- NIST PQC standards need OT-specific adaptation profiles (reduced security levels for constrained devices)
- CISA guidance calls for PQC-ready OT protocol profiles by 2027

**Pathway C: End-to-End PQC (Long-term, 2030+)**
- Full field device replacement with PQC-hardened RTUs/IEDs
- Requires hardware PQC IP blocks (ML-KEM accelerators on FPGA/ASIC)
- 10-15 year transition aligned with OT equipment replacement cycles

### Risk Assessment

| Risk | Severity | Timeline | Mitigation |
|------|----------|----------|------------|
| HNDL attacks on OT comms | Critical | Active now | Gateway PQC overlay |
| Legacy RTU/IED crypto exposure | High | 2030+ | Protocol-level migration |
| Vendor firmware lag | High | Ongoing | Crypto-agility requirements |
| IEC 61850 PQC profile gap | Medium | 2027-2030 | Standards body engagement |
| Supply chain PQC uncertainty | Medium | Ongoing | Vendor attestation requirements |

### Key Insight

The OT PQC migration problem is fundamentally different from IT PQC migration. IT systems can update TLS libraries and rotate keys with minimal disruption. OT systems require hardware replacement, firmware certification, and availability guarantees that make software-only updates insufficient. The Arizona model — PQC at OT/IT boundary gateways first, then gradual field device migration — represents the most pragmatic pathway validated to date.

## Cross-Domain Connections

- **post-quantum-cryptography-readiness**: NIST standardization timeline, algorithm selection
- **cyber-physical-infrastructure-security**: OT/IT convergence threat surface
- **grid-edge-ai**: RTU/IED deployment constraints, edge computing resources
- **privacy-and-cryptography**: PQC algorithm performance tradeoffs
- **metadata-resistant-communication**: PQC implications for metadata protection

## Deepening Threshold

- [ ] 8+ verified primary sources
- [ ] Algorithm performance benchmarks on embedded platforms
- [ ] OT protocol migration pathways documented
- [ ] Real-world deployment case studies
- [ ] Cross-domain links verified
- [ ] Current implementation status assessed
