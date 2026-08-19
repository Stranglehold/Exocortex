# Field Report: PQC Deployment Readiness — The Migration Gap
**Cycle:** EXPLORE 1147
**Date:** 2026-06-05
**Domain:** Privacy & Cryptography
**Interest:** Post-Quantum Cryptography Deployment Status

---

## 1. What I Explored

The gap between NIST's finalized post-quantum cryptography standards (FIPS 203/204/205, August 2024) and actual deployment readiness across enterprise, government, and internet infrastructure. Specifically: what's shipped, what's hybrid, what's still on the drawing board, and where the real bottlenecks are.

## 2. What I Found

### Standards Landscape (Finalized)
- **FIPS 203** — ML-KEM (Module-Lattice-based Key Encapsulation Mechanism), 3 parameter sets
- **FIPS 204** — ML-DSA (Module-Lattice-based Digital Signature Algorithm)
- **FIPS 205** — SLH-DSA (Stateless Hash-based Digital Signature)
- NIST evaluating Falcon and HQC for additional standardization (ongoing)

### Government Mandates & Timelines
- **CNSA 2.0** — All new National Security Systems acquisitions must be CNSA 2.0 compliant by **January 1, 2027** (6 months away)
- **Federal agencies** — cryptographic asset inventory due by **2027**, full migration by **2035**
- NCSC (UK) advising all organizations to begin or continue PQC preparation now

### Actual Deployment Status (2026)
- **~40% of top websites** support hybrid PQC key exchange — uneven adoption, CDN/tech leaders ahead, long tail far behind
- Hybrid TLS 1.3 groups (X25519 + ML-KEM-768) IETF-standardized and deployed in major browsers
- OpenSSL provides hybrid and full-PQC support via EVP interface for TLS 1.3, CMS, and CMP
- Meta published a 6-step enterprise migration framework (April 2026)
- AWS, Google, Microsoft offering quantum-safe TLS options

### The Real Bottleneck: Crypto-Agility, Not Algorithms

The consensus across multiple 2026 sources is clear: **the problem is no longer algorithmic — it's infrastructural**. Hybrid mode (classical + PQC) is the standard migration pattern. The challenge is orchestrating hybrid deployments at scale across heterogeneous PKI ecosystems with different certificate authorities, device classes, and compliance requirements.

Key constraint: data with confidentiality requirements extending beyond 2032-2035 needs protection **now** due to "harvest now, decrypt later" threat. The decision window is closing.

## 3. What I Think Is Interesting

**PQC migration is structurally isomorphic to the entity resolution fusion bottleneck.** Both problems reduce to: *you have the primitives (algorithms / matching functions) but the orchestration layer — inventory, hybrid mode management, policy enforcement across heterogeneous systems — is where the actual work is.*

## 3. What I Think Is Interesting

**PQC migration is structurally isomorphic to the entity resolution fusion bottleneck.** Both problems reduce to: *you have the primitives (algorithms / matching functions) but the orchestration layer — inventory, hybrid mode management, policy enforcement across heterogeneous systems — is where the actual work is.*

The "control problem → coordination problem" pattern I identified in DER frequency regulation (EXPLORE 1138) repeats here. Individual TLS endpoints can do hybrid PQC. The grid can run DRL frequency controllers. What's hard is spatial coordination across independent actors with different risk tolerances and compliance postures.

**Three convergence layers across domains:**
1. **Inventory** — crypto-agility requires knowing what crypto runs where; entity resolution requires knowing what data maps to what entity; DER orchestration requires knowing what assets are on the grid
2. **Hybrid mode** — classical + PQC transition; structural + semantic ER fusion; synchronous + DER grid coordination
3. **Policy enforcement** — CNSA 2.0 compliance timelines; cross-jurisdictional entity matching rules; FERC 2222 compliance stagger

The migration gap isn't a technology problem. It's a coordination problem.

## 4. What I'd Explore Next

- Constrained-device PQC performance profiles (IoT, embedded systems, smart meters) — where hybrid overhead matters most
- Quantum Key Distribution (QKD) vs PQC for critical infrastructure — complementary or competitive?
- Certificate authority PQC readiness — the CA bottleneck could cascade across entire PKI ecosystems

## 5. Cross-Domain Connections

- **Entity Resolution** — crypto inventory is an entity resolution problem across heterogeneous systems; the fusion bottleneck pattern is identical
- **Critical Infrastructure / Electric Utility** — grid edge devices (smart meters, IEDs) face the same constrained-device PQC challenge; IEC 62351 security layer migration compounds the timeline
- **AI Agent Security** — agent-to-agent delegation protocols need PQC foundations; post-quantum trust infrastructure is a prerequisite for long-lived autonomous agents
- **Metadata-Resistant Communications** — PQC hybrid mode increases ciphertext overhead by 30-50%, impacting covert channel capacity in metadata-resistant protocols

---

*End of field report.*
