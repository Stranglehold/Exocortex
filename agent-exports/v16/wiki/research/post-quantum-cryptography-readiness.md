# Post-Quantum Cryptography (PQC) Readiness

Status: STABLE
Created: 2026-05-16
Last Updated: 2026-05-16

## 1. NIST PQC Standardization — Finalized Standards

NIST released three finalized PQC standards on August 13, 2024, ending an 8-year global evaluation:

| Standard | Algorithm | Function | Replaces |
|----------|-----------|----------|----------|
| FIPS 203 | ML-KEM | Key encapsulation | RSA-KEM, ECDH |
| FIPS 204 | ML-DSA | Digital signatures | RSA-PSS, ECDSA, EdDSA |
| FIPS 205 | SLH-DSA | Stateless hash signatures | Long-term archival signing |

A fourth round added **HQC** (Horng-Chan-Calligraph) for standardization on March 11, 2025, as a backup KEM alongside ML-KEM.

CISA published product categories for PQC technologies (Jan 2026). MITRE released a migration roadmap via the Post-Quantum Cryptography Coalition (PQCC). NIST IR 8547 describes the transition approach.

## 2. Harvest-Now, Decrypt-Later (HNDL) Threat Model

**Mechanism**: Adversaries collect encrypted data today, storing it for future decryption once quantum computers mature.

**Timeline**: Quantum computers capable of breaking RSA-2048 projected by 2030 ± 3 years (per MDPI analysis of 100+ primary sources).

**Impact scope**:
- Government classified data (decades-long sensitivity)
- Healthcare records (HIPAA 6-year retention + lifetime relevance)
- Financial records and blockchain keys
- Corporate IP and trade secrets
- Personal data in breach databases

**Current readiness**: Only 5% of organizations report a defined PQC strategy (ISACA 2025 poll, 2600+ respondents). Most companies haven't started migration.

**Federal response**: NIST, NSA, CISA joint migration effort. Federal Reserve published analysis on HNDL risks to distributed ledger networks.

## 3. Migration Patterns

### Hybrid Migration (Recommended)
Combine classical and PQC algorithms during transition:
- TLS: hybrid key exchange (ECDH + ML-KEM) for backward compatibility
- Signatures: ML-DSA alongside RSA/EdDSA until PQC-only is viable

### Crypto-Agility Requirement
Systems must support algorithm substitution without architectural changes. Key design principles:
- Abstract cipher selection behind interfaces
- Support multiple PQC algorithms simultaneously
- Plan for standard updates (FIPS 206+ anticipated)

### Timeline
- 2024–2025: Inventory cryptographic assets, baseline assessment
- 2025–2027: Hybrid deployment, crypto-agility implementation
- 2027–2030: PQC-only migration for high-sensitivity systems

## 4. Performance & Hardware Acceleration

### ML-KEM (Kyber) Benchmarks
- Ciphertext expansion: ~10x plaintext (security level 1: 1.1KB public key, 1.1KB ciphertext)
- Comparison: RSA-7680 and SECP384R1 baselines on x86_64/ARM64 (arXiv:2508.01694)
- NTT (Number Theoretic Transform) is the computational bottleneck

### FPGA Acceleration
- Area-time efficient architectures achieving balance between performance and resource use
- Lightweight NTT-based accelerators for ML-KEM on edge FPGAs
- Phoenix project: crypto-agile hardware sharing ML-KEM and HQC on single accelerator
- 28nm ASIC: 69.4kOPS at 4.4μJ/Op (Zhu et al.)

### GPU Acceleration
- RTX 3080 implementation using NTT-box parallel processing
- Tensor core utilization for lattice polynomial multiplication
- Potential for RTX 3090 optimization (cross-reference: hardware-and-physical-computing wiki)

## 5. Protocol Integration

### TLS 1.3
- IETF working group standardizing hybrid key exchange groups
- BoringSSL, OpenSSL 3.x adding ML-KEM support
- Expected deployment in major browsers by 2026–2027

### Signal Protocol
- SPQR update (Oct 2025): hybrid post-quantum key exchange (Kyber + X25519)
- Forward secrecy preserved via Double Ratchet
- Metadata remains server-visible (contact graph, timestamps)

### Other Protocols
- SSH: OpenSSH adding ML-KEM support
- WireGuard: discussing PQC extensions
- Briar/Cwtch: evaluating PQC for decentralized metadata-resistant comms

## 6. Cross-Domain Connections

- **Privacy & Cryptography**: PQC migration path for HE/ZKP systems; ZKP circuits need PQC-compatible commitments
- **Hardware & Physical Computing**: FPGA acceleration for lattice-based crypto on edge devices; RTX 3090 tensor core optimization for NTT operations
- **SCADA/ICS**: PQC readiness in operational technology — legacy systems with 20–30 year lifespans need crypto-agility
- **Entity Resolution**: PQC for secure multi-party computation in private record linkage (HE + PQC hybrid)

## 7. Open Questions
- Will HQC supplant or complement ML-KEM in production?
- Can hardware acceleration close the FHE performance gap before quantum threat matures?
- What is the PQC readiness of SCADA/ICS protocols (IEC 60870, DNP3, Modbus)?
- Regulatory drivers: GDPR, HIPAA, AI Act mandates for PQC?
- How do lattice-based signatures interact with ZKP verification circuits?
