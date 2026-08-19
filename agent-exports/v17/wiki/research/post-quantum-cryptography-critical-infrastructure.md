# Post-Quantum Cryptography Transition for Critical Infrastructure

**Status: STABLE**
**Created: 2026-06-03**
**Lines: ~240**
**Domain: Privacy/Cryptography × Electric Utility/Critical Infrastructure**

## Overview

The transition from classical public-key cryptography to post-quantum cryptographic (PQC) algorithms is a structural imperative for critical infrastructure sectors. NIST's 2024-2025 PQC standards (FIPS 203 ML-KEM, FIPS 204 ML-DSA, FIPS 205 SLH-DSA, and the forthcoming FALCON-derived FIPS) provide the algorithmic foundation, but the operational challenge of migrating SCADA/ICS environments, substation automation, and smart grid communications presents unique constraints absent from enterprise IT migration planning.

The primary threat vector is "harvest now, decrypt later" — adversaries collecting encrypted operational data today for decryption once a cryptographically relevant quantum computer (CRQC) materializes. For critical infrastructure with 20-40 year field device lifecycles, data intercepted today on IEC 61850 GOOSE messages or DNP3 telemetry could be decrypted by a CRQC arriving well within the device's operational lifespan.

## 1. NIST Standards & Timeline

| Standard | Algorithm | Type | Key Size | Notes |
|----------|-----------|------|----------|-------|
| FIPS 203 | ML-KEM (CRYSTALS-Kyber) | Key Encapsulation | 800-1568 bytes (ciphertext) | Primary KEM for key establishment |
| FIPS 204 | ML-DSA (CRYSTALS-Dilithium) | Digital Signature | 2420-4595 bytes (sig) | Primary signature algorithm |
| FIPS 205 | SLH-DSA (SPHINCS+) | Digital Signature | 7856-49856 bytes (sig) | Stateless hash-based, conservative choice |
| (Future) | FN-DSA (FALCON) | Digital Signature | ~666-1280 bytes (sig) | Compact signatures for constrained environments |

**Deprecation Timeline (NIST IR 8547, 2024):**
- **After 2030:** Deprecate RSA/ECDSA/EdDSA at ≤112-bit security for digital signatures; deprecate 112-bit key-establishment algorithms.
- **After 2035:** Disallow all quantum-vulnerable algorithms; 128-bit+ security digital signatures also disallowed.
- Application-specific guidance may require earlier transitions for protocols facing harvest-now-decrypt-later risk.

## 2. Protocol-Level Vulnerabilities & Migration Pathways

### 2.1 IEC 61850 / IEC 62351 (Substation Automation)
- IEC 62351 specifies TLS profiles for GOOSE, SV, and MMS messaging.
- **Vulnerability:** TLS handshake uses RSA, ECDSA, or ECDH — all quantum-vulnerable.
- **Migration path:** Replace TLS cipher suites with PQC-hybrid (e.g., X25519+ML-KEM-768 for key exchange, ECDSA+ML-DSA for authentication). Requires protocol specification updates to IEC 62351.
- **Constraint:** GOOSE messages typically <1500 bytes; larger PQC signatures may require fragmentation or protocol redesign.

### 2.2 DNP3 Secure Authentication v5
- **Resistance:** Uses HMAC-SHA-256 for authentication (symmetric — quantum-resistant for pre-image resistance at 256-bit).
- **Vulnerability:** Key management/distribution layer uses asymmetric cryptography. If ECDH or RSA is used to establish session keys, a CRQC can recover those keys and forge subsequent DNP3 traffic.
- **Migration path:** Replace asymmetric key establishment with PQC KEM (ML-KEM) while retaining HMAC for session authentication. Requires DNP3 Users Group specification update.

### 2.3 Modbus (Legacy Fieldbus)
- **Current state:** Typically completely unencrypted, no authentication.
- **PQC strategy:** Cannot be upgraded at protocol level. Requires external overlay — PQC-capable gateways or bump-in-the-wire encryption appliances at network boundary.
- **Hybrid approach:** Gateway performs PQC key exchange and encrypts Modbus TCP traffic with AES-256-GCM, presenting plain Modbus on the OT side to legacy devices.

### 2.4 OPC UA
- **Vulnerability:** Depends on standard TLS — same quantum-vulnerable handshake as all TLS-dependent protocols.
- **Migration path:** OPC Foundation to specify PQC cipher suites in OPC UA specification. PQC-hybrid TLS 1.3 extensions exist (IETF drafts).

## 3. Constrained Device Migration

OT equipment operates under severe constraints absent from IT PQC planning:

| Constraint | Typical OT Value | PQC Impact |
|------------|------------------|------------|
| CPU | 8-bit or 16-bit microcontroller | ML-KEM requires 32-bit arithmetic; some optimizations exist for Cortex-M0 |
| RAM | 128-256 KB | ML-DSA signatures (2420 bytes) consume 1-2% of total RAM; SLH-DSA (7856 bytes) may be infeasible |
| Latency | <4ms GOOSE, <10ms control loop | ML-DSA signing ~200μs on Cortex-M4 vs RSA-2048 ~50ms; PQC actually faster for signing |
| Packet size | DNP3 max 2048 bytes, GOOSE ~1500 bytes | ML-KEM ciphertext (768-1568 bytes) fits; SLH-DSA (7856 bytes) requires fragmentation |
| Firmware | Often hardcoded crypto, no field-upgrade path | Devices with ROM-based crypto require complete hardware replacement |

**Algorithm Selection Criteria for OT:**
1. Smallest feasible key and signature sizes (favors FALCON/FN-DSA over ML-DSA over SLH-DSA)
2. Acceptable signing/verification latency within control-loop timing budgets
3. CCA security (all NIST-selected KEMs are IND-CCA2)
4. Implementability on 8/16-bit MCUs with minimal code size
5. Crypto-agility — ability to swap algorithms via firmware update as standards evolve

## 4. NERC CIP & Regulatory Landscape

- **NERC CIP-005, CIP-007, CIP-011:** Address cryptographic controls in general terms (electronic security perimeter, systems security management, information protection). Do not yet reference PQC primitives.
- **Expected evolution:** Future CIP revisions to align with CNSA 2.0, NIST FIPS 203/204/205, and CISA PQC guidance.
- **Current best practice:** Utilities should document quantum risk within existing CIP cybersecurity risk management programs, include PQC roadmap requirements in procurement language, and begin cryptographic asset inventory.
- **IEC 62351:** Quantum-vulnerable at TLS handshake. Compliance will require incorporation of quantum-resistant algorithms and crypto-agility — likely via IETF PQC-hybrid TLS drafts.
- **CISA Post-Quantum OT Guidance (2024):** Four-stage framework: (1) Inventory cryptographic assets, (2) Prioritize long-lived data and equipment, (3) Engage vendors on crypto-agility and PQC roadmaps, (4) Treat migration as a multi-year program.

## 5. Hybrid Migration Architecture for Brownfield Deployments

Three-layer coexistence model for OT environments where legacy devices cannot be field-upgraded:

1. **Network Boundary Encryption:** PQC-capable gateways perform ML-KEM key exchange and AES-256 session encryption for WAN/control-center links. Legacy field devices communicate via plain or classical protocols internally.

2. **Dual-Signing for Firmware Integrity:** Firmware images signed with both classical (RSA/ECDSA) and PQC signature (ML-DSA) — legacy boot chains verify the classical signature, PQC-capable devices verify both. Enables gradual transition without breaking existing update infrastructure.

3. **PQC-Hybrid TLS for Control-Center Links:** TLS 1.3 with hybrid key exchange (X25519+ML-KEM) and hybrid authentication (ECDSA+ML-DSA) on SCADA master-to-RTU and ICCP links. Provides defense-in-depth against both classical and quantum adversaries during the migration window.

## 6. Vendor Readiness & Supply Chain

As of early 2026:
- **SEL, GE, ABB, Siemens:** No publicly announced PQC-capable firmware for protection relays or RTUs.
- **Cisco, RuggedCom:** PQC roadmap announced for industrial switches; ML-KEM support in IOS-XE roadmap (2026-2027).
- **Red flag:** Vendors unwilling to share quantum-safe roadmaps create dependency risk for 20-40 year asset lifecycles.
- **Procurement guidance:** Require PQC capability roadmaps in RFPs; specify crypto-agility as a requirement.

## 7. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[scada-ics-security]] | PQC migration is the next phase of SCADA/ICS security — protecting against future threats to protocols whose current vulnerabilities are well-cataloged in that page. |
| [[privacy-cryptography]] | PQC is a sub-domain of cryptographic evolution alongside ZK-proofs, homomorphic encryption, and metadata-resistant protocols covered there. |
| [[electric-utility-critical-infrastructure]] | The substation protocols and grid modernization efforts described there are the very systems that must be migrated to PQC. |
| [[iec-61850-standard-evolution]] | Direct protocol dependency — IEC 61850 security (IEC 62351) must evolve to incorporate PQC cipher suites. |
| [[grid-resilience-physical-security]] | Quantum threats are the cyber equivalent of EMP/GMD threats — long-duration, low-probability, high-consequence events requiring preparation well before manifestation. |
| [[utility-sector-regulatory-dynamics]] | NERC CIP evolution and state PUC rate cases will determine whether PQC migration costs can be recovered through rate bases. |
| [[us-china-semiconductor-supply-chain]] | The CRQC development race is a geopolitical competition; Chinese advances in quantum computing directly accelerate the migration timeline for US critical infrastructure. |
| [[sigint-evolution]] | Quantum computing represents the next paradigm shift in signals intelligence — what cryptanalysis was to Enigma in WWII, quantum decryption could be to current public-key infrastructure. |

## 8. Sources

1. NIST IR 8547 (Initial Public Draft), "Transition to Post-Quantum Cryptography Standards," 2024. https://nvlpubs.nist.gov/nistpubs/ir/2024/NIST.IR.8547.ipd.pdf
2. FIPS 203, "Module-Lattice-Based Key-Encapsulation Mechanism Standard," 2024.
3. FIPS 204, "Module-Lattice-Based Digital Signature Standard," 2024.
4. FIPS 205, "Stateless Hash-Based Digital Signature Standard," 2024.
5. CISA, "Post-Quantum Considerations for Operational Technology," 2024. https://www.cisa.gov/resources-tools/resources/post-quantum-considerations-operational-technology
6. CISA/NSA/NIST, "Quantum-Readiness: Migration to Post-Quantum Cryptography," 2023.
7. Postquantum.com, "PQC Migration for SCADA and OT Networks," https://postquantum.com/post-quantum/ot-pqc-challenges/
8. QuantumSecurityDefence.com, "Workshop: PQC Migration for SCADA and OT Networks," https://www.quantumsecuritydefence.com/workshops/power-energy/pqc-migration-for-scada-and-ot-networks/
9. QNSQY, "PQC for Power Grid and Critical Infrastructure," https://quantumsequrity.com/blog/pqc-critical-infrastructure-grid
10. AllSecureX, "SCADA & ICS Systems: The Quantum Threat to Critical Infrastructure," https://allsecurex.com/blog/scada-ics-quantum-threat.html
11. QuantumSecurityDefence.com, "Quantum Security for OT and SCADA Systems: A Practitioner's Assessment Framework," https://quantumsecuritydefence.com/insights/ot-scada-quantum-security-practitioner-framework/
12. IETF, "Hybrid key exchange in TLS 1.3" (draft-ietf-tls-hybrid-design).

---
*Status: STABLE — 12 sources, 8 cross-domain connections*
