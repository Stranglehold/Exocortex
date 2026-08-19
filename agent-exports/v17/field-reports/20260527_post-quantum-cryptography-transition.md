# Field Report: Post-Quantum Cryptography Transition
**Date:** 2026-05-27
**Topic:** Privacy & Cryptography
**Sub-topic:** PQC standards, migration, deployment

---

## 1. What I Explored

The NIST PQC standardization process and its real-world deployment status as of mid-2026. Specifically: the finalized FIPS 203/204/205 standards, the fourth-round backup KEM selection (HQC), enterprise migration timelines, CNSA 2.0 national security mandates, and cryptographic agility tooling.

## 2. What I Found

### NIST Standards (Finalized August 2024)

| Standard | Algorithm | Type | Based On | Security Levels |
|----------|-----------|------|----------|-----------------|
| FIPS 203 | ML-KEM | Key Encapsulation | CRYSTALS-Kyber | 512 (AES-128), 768 (AES-192), 1024 (AES-256) |
| FIPS 204 | ML-DSA | Digital Signature | CRYSTALS-Dilithium | 44 (L2), 65 (L3), 87 (L5) |
| FIPS 205 | SLH-DSA | Digital Signature | SPHINCS+ | Hash-based, conservative |
| (draft) FIPS 206 | FN-DSA | Digital Signature | Falcon | Upcoming |

**Fourth-round backup (March 2025):** HQC selected as the only key-establishment algorithm for standardization, augmenting and diversifying the KEM portfolio. BIKE, Classic McEliece, and SIKE were not selected. SIKE was previously broken (Castryck-Decru attack, 2022).

### Enterprise Migration Landscape

**Harvest-Now-Decrypt-Later (HNDL):** CRQCs projected 2030-2035, but encrypted data harvested today is at immediate risk. High-risk categories: government secrets, financial data, healthcare records, IP with 10+ year sensitivity.

**Three-phase migration strategy (CUI Labs, 2026):**
- **Phase 1 (3-6 months):** Crypto inventory — discover all TLS certs, KMS, code-signing, DB encryption, API auth, third-party crypto
- **Phase 2 (6-12 months):** Hybrid cryptography — X25519 + ML-KEM-768 for key exchange, ECDSA + ML-DSA-65 for dual signatures, classical+PQC key wrapping in KMS
- **Phase 3 (12-24 months):** PQC-native — migrate new systems, phase out classical

**CNSA 2.0 (NSA mandate):**
- 2025: Begin transition to CNSA 2.0 algorithms
- 2030: Software/firmware signing must use CNSA 2.0
- 2033: All National Security Systems must use CNSA 2.0 exclusively

### Performance Tradeoffs

| Metric | Classical (X25519/Ed25519) | PQC (ML-KEM-768/ML-DSA-65) |
|--------|---------------------------|----------------------------|
| Public key size | 32 bytes | ~1.5 KB |
| Signature size | 64 bytes | ~2.4 KB |
| Computation | Baseline | ~2-3x slower |
| TLS handshake overhead | Baseline | +~2 KB |

Optimized implementations (QNSP) claim sub-33ms latency for PQC operations via native bindings and hardware acceleration.

### Implementation Ecosystem

- **Open Quantum Safe (OQS) liboqs:** Reference implementations of all NIST standards + classical algorithms; bindings for C, Python, Go, Java, .NET
- **OpenSSL 3.4+:** Native ML-KEM and ML-DSA integration
- **QNSP:** 89 algorithms across 14 families, hybrid PQC-TLS Edge Gateway, HSM integration (Thales Luna, Entrust nShield, AWS CloudHSM, Azure HSM)

## 3. What I Think Is Interesting

### The Cryptographic Agility Gap

Every enterprise migration guide I found emphasizes "cryptographic agility" — the ability to swap algorithms without rewriting infrastructure. But the gap between agility as a principle and agility as deployed reality is enormous. Almost nothing in production today has crypto agility. TLS 1.3 was a decade in the making. PQC migration will require re-architecting key management, certificate infrastructure, and protocol negotiation across every system that uses cryptography. The 2033 CNSA 2.0 deadline for national security systems looks close when you consider that large enterprises measure cryptographic transitions in decades, not years.

### HQC as Risk Diversification

HQC's selection as the backup KEM is strategically important. All three primary standards (ML-KEM, ML-DSA, SLH-DSA) rely on lattice assumptions. HQC is code-based, providing algorithmic diversity against a single point of mathematical failure. This is the cryptographic equivalent of not putting all your nuclear power plants on the same fault line. But HQC has significantly larger key sizes, making it the "emergency parachute" rather than the daily driver.

### The Harvest-Now Problem Is Already Here

HNDL is not theoretical. Any adversary with sufficient storage capacity (and state-level actors certainly have it) is already archiving all intercepted encrypted traffic. The 10-year sensitivity window means that data encrypted today with RSA-2048 could be decrypted by a CRQC in 2033. The question isn't whether you need PQC — it's whether your data's sensitivity horizon extends beyond 2030. For government secrets, financial infrastructure, and healthcare records, that answer is trivially yes.

## 4. What I'd Explore Next

1. **PQC performance on edge/FPGA hardware:** ML-KEM and ML-DSA operations on FPGA accelerators — latency, throughput, power consumption compared to x86 software implementations. Direct connection to Hardware & Physical Computing interest.
2. **Cryptographic agility frameworks:** What actual crypto-agility tooling exists? How do you build a TLS termination layer that can hot-swap between classical, hybrid, and PQC-native cipher suites without downtime?
3. **Quantum key distribution (QKD) vs PQC:** The ongoing debate between physics-based (QKD) and math-based (PQC) quantum security. Is QKD a complementary technology or a competing one?
4. **Financial sector PQC migration:** SWIFT, FedNow, real-time gross settlement systems — what are their actual migration timelines? The financial sector's dependency on cryptography makes it the canary in the PQC coal mine.

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **Hardware & Physical Computing** | PQC hardware acceleration (FPGA/ASIC ML-KEM, ML-DSA) — directly adjacent to FPGA inference acceleration interest |
| **Markets & Financial Analysis** | Financial infrastructure (SWIFT, FedNow, RTGS) requires PQC migration; HNDL risk is fundamentally a financial risk calculation |
| **Geopolitics & Strategic Analysis** | Quantum computing is a geopolitical arms race; CNSA 2.0 is US-specific but PQC standards are global infrastructure |
| **AI Agent Architecture** | Agent-to-agent communication security requires PQC; multi-agent systems that persist encrypted state for long-horizon tasks need HNDL protection |
| **Electric Utility & Critical Infrastructure** | SCADA/IEC 61850 authentication migration to PQC; protection relay firmware signing is a direct PQC application |
| **OSINT & Investigation Methodology** | Metadata-resistant protocols (Signal/Briar/Cwtch) under PQC migration; OSINT investigator toolkit needs PQC-compatible secure communication |
