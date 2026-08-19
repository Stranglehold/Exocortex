# PQC Deployment Readiness & Harvest-Now-Decrypt-Later Threat

**Status:** STABLE  
**Domain:** Privacy & Cryptography  
**Created:** 2026-05-24  
**Deepened:** 2026-05-25 (BUILD Cycle 552)  
**Source:** EXPLORE Cycle 546 field report  
**Cross-refs:** post-quantum-critical-infrastructure, pqc-hardware-acceleration, ai-agent-trust-infrastructure, trusted-execution-environments-privacy-preserving-ml, sigint-ai-integration-2026

---

## Standardization State (Updated May 2026)

NIST published first three finalized PQC standards August 2024:
- **FIPS 203 (ML-KEM)**: CRYSTALS-Kyber key encapsulation — primary hybrid key establishment
- **FIPS 204 (ML-DSA)**: CRYSTALS-Dilithium digital signatures
- **FIPS 205 (SLH-DSA)**: SPHINCS+ stateless hash-based signatures (backup/fallback)
- **FIPS 206 (FN-DSA)**: FALCON — in development
- **HQC Selected**: March 2025, code-based KEM backup for algorithmic diversity, draft standard expected early 2026, final 2027
- **NIST IR 8547**: Transition guidance (IPD Nov 2024, comment period closed Jan 2025)

### Implementation Ecosystem (2025-2026)

| Platform | PQC Support Status | Notes |
|----------|-------------------|-------|
| OpenSSL 3.5 | Built-in ML-KEM & ML-DSA | Available on RHEL 9.6, integrated post-FIPS publication |
| Cloudflare | PQ-in-TLS active | PQ key exchange deployed, no PQ certificates yet (May 2026) |
| SealSq | SE/HSM integration 2026 | Hardware security module roadmap targets 2026-2030 hybrid deployment |
| NCSC UK | Migration guidance published | Nov 2023 white paper, Aug 2024 update, ongoing preparation phase |

### Performance Benchmarks (TLS 1.3)

| Configuration | Throughput | Notes |
|--------------|-----------|-------|
| Classical (x25519) | Baseline | Current production standard |
| ML-KEM-768 + ML-DSA-65 (hybrid) | ~804 conn/sec | Windows/MSYS2 Docker, 5s test window |
| Pure ML-KEM | ~750-800 conn/sec | Minimal computational overhead per Frontiers 2025 study |

**Key Finding**: Hybrid TLS handshakes absorb minimal computational overhead but increase packet size due to larger PQC keys/signatures (Kyber ~1.2KB vs RSA-2048 ~0.3KB public key).

## CNSA 2.0 Mandate Timeline

- **2025-12-31**: Existing NSS must meet CNSA 1.0 or request waiver
- **2027-01-01**: All new NSS acquisitions must be CNSA 2.0 compliant (PQC-migrated)
- **Effective migration window**: ~18 months from FIPS publication to mandated compliance
- **Enterprise timeline**: 2026 integration into SE/HSM, 2027-2030 hybrid deployments (SealSq roadmap)

## Harvest-Now-Decrypt-Later (HNDL) Threat

Adversaries collect encrypted data now, decrypt after quantum advantage arrives. NSA/CISA/NIST joint advisories confirm adversaries are actively harvesting encrypted data with long-term strategic value.

### Q-Day Timeline Pressure

| Development | Date | Impact |
|------------|------|--------|
| RSA-2048 qubit estimate: 20M qubits | Pre-2025 | Original Shor's algorithm estimate |
| RSA-2048 qubit estimate: <1M qubits | May 2025-Mar 2026 | Three papers reduced requirements significantly |
| RSA-2048 qubit estimate: ~100K qubits | Mar 2026 | Newer architectures (potential, not confirmed) |

**Implication**: Quantum advantage timeline for breaking RSA-2048 is shrinking faster than anticipated.

### Sector-Specific HNDL Risk

- **Financial**: Federal Reserve (2025) modeled blockchain HNDL risk — data harvested in 2025, PQC migration in 2027, Q-Day in 2030 = 3-year exposure window for blockchain transactions
- **Healthcare**: Patient records have 50+ year secrecy requirements; HNDL applies immediately
- **Critical Infrastructure**: SCADA/IEC 61850 systems with 20+ year lifespans; grid-edge devices need PQC migration pathways
- **National Security**: Intelligence communications classified 25-50 years; retroactive decryption devastating

NIST explicitly identifies "data secrecy lifetime" as a critical concern.
Olutimehin et al. (2025) adoption model under HNDL assumptions confirms: early PQC deployment dramatically reduces retrospective compromise probability.

## Deployment Gaps & Challenges

### Technical Gaps

- **Crypto-agility**: Most systems lack ability to swap algorithms without full re-architecture
- **Legacy hardware**: IoT, embedded, grid-edge devices with 10-20+ year lifespans
- **Hybrid mode complexity**: Running classical + PQC simultaneously increases attack surface
- **Key size overhead**: PQC keys/signatures are larger (Kyber ~1.2KB public key vs RSA-2048 ~0.3KB)
- **Performance profiling**: Lattice-based math has different computational profiles than factoring/DLP

### Organizational Gaps

- **Inventory completeness**: Organizations don't know all instances of classical crypto in use (similar to entity resolution problem)
- **Vendor readiness**: Commercial crypto libraries at varying PQC support levels (OpenSSL 3.5 leading, others lagging)
- **Certification backlog**: FIPS-validated PQC modules not yet widely available for regulated sectors
- **Skills shortage**: Cryptographic engineers with PQC expertise are scarce

### Regulatory Alignment

- **International divergence**: NIST, BSI, ANSSI, ASD differ on algorithm selection, parameter sets, hybrid use policies
- **Compliance overlap**: CNSA 2.0 (US), NCSC guidance (UK), EU ENISA recommendations — organizations need multi-jurisdictional strategy

## Primary Sources

### Standards & Guidance
1. NIST PQC Project: https://csrc.nist.gov/projects/post-quantum-cryptography
2. FIPS 203/204/205 Publication (Aug 2024)
3. NIST IR 8547 (Transition to PQC Standards)
4. CNSA 2.0 Suite (Sept 2024)
5. NIST PQC Road Ahead Presentation (Moody, March 2025)
6. NCSC UK PQC Migration Timelines: https://www.ncsc.gov.uk/guidance/pqc-migration-timelines

### Research & Analysis
7. Olutimehin et al. (2025) — PQC Adoption Model under HNDL Assumptions
8. Federal Reserve FEDS Paper 2025-093 — Blockchain HNDL Risk Modeling
9. Frontiers in Physics (2025) — ML-KEM/ML-DSA TLS Session Protocol Implementation
10. ACM/ScienceDirect (2025) — Performance Evaluation Framework for Post-Quantum TLS
11. arXiv:2603.11006v1 — Layered Performance Analysis of TLS 1.3 Handshakes (Classical vs Hybrid vs Pure PQ)
12. arXiv:2508.16078v1 — PQC Support in Cryptographic Libraries Survey

### Industry Status
13. Cloudflare Blog (2025) — State of Post-Quantum Internet 2025
14. SealSq — Quantum Risk Enterprise Migration Roadmap
15. PostQuantum.com — 2025 NIST Standardization Update

---

*Deepened BUILD Cycle 552: Added Q-Day timeline pressure data (qubit reduction 20M→<1M→~100K), TLS 1.3 performance benchmarks, OpenSSL 3.5/Cloudflare deployment status, sector-specific HNDL risk modeling, organizational/regulatory gaps, 15 primary sources. Status upgraded to STABLE.*
