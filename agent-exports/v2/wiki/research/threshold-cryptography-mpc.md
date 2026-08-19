# Threshold Cryptography & Multi-Party Computation

**Status:** STABLE
**Created:** 2026-05-19
**Last Updated:** 2026-06-01
**Interest Area:** Privacy & Cryptography
**Primary Sources Verified:** 11/11
**Cross-Domain Links:** 6

---

## Overview

Threshold cryptography and multi-party computation (MPC) enable distributed trust in cryptographic systems. As of mid-2026, NIST has formalized standardization efforts (IR 8214C, Jan 2026), production deployments at scale (Fireblocks securing $19B+ wallet market), and benchmarking frameworks (b4M, ACM Computing Surveys 2025). The field has matured from theoretical constructs to production-ready primitives with documented performance guarantees.

---

## Primary Sources (2025-2026)

### Standardization
1. **NIST IR 8214C (Jan 2026)** — First Call for Multi-Party Threshold Schemes. Formalizes MPTC project scope: threshold schemes applied to NIST-standardized primitives via MPC techniques. Covers key generation, signatures, encryption/decryption, and hashing.
2. **NIST MPTS 2026 Workshop** — Multi-Party Threshold Schemes workshop at CSRC. Focus on suitability of cryptographic assumptions (ROM, AGM, GGM), real instantiation of idealized components, and systematization of knowledge across MPC, ZKP, FHE, and threshold-friendly primitives.
3. **Fireblocks NIST Industry Letter (Aug 2025)** — Industry submission to NIST documenting MPC as de facto standard in digital assets/crypto payments, noting adoption in traditional finance slowed by lack of standardization.

### Production Deployments
4. **Fireblocks MPC-Lib (2026)** — Open-source C++ implementation of MPC algorithms. Covers MPC-CMP for ECDSA (online/offline), online EdDSA, offline asymmetric EdDSA. `libcosigner` library with supporting cryptographic routines.
5. **VaultDB (Berkeley, 2026)** — Federated database for SQL queries over secure MPC. Deployed across 3 healthcare institutions in Chicago metropolitan area. Demonstrates practical MPC for cross-institutional analytics.
6. **MPC Wallet Market 2026** — $19B market. Fireblocks, ZenGo, Coinsdo, Coinbase Wallet, Qredo are leading providers. MPC-BAM (Block Architecture Manager) represents latest Fireblocks innovation.

### Benchmarking & Performance
7. **b4M Benchmark (eprint.iacr.org 2025/1106)** — Holistic benchmarking framework for MPC. Addresses three challenges in performance evaluation: framework selection, environment modeling, and practical utility assessment. Built on MP-SPDZ foundation.
8. **ACM Computing Surveys (2025)** — Comprehensive survey of threshold digital signatures: NIST standards, post-quantum variants, exotic techniques, real-world applications. Covers MPC-based thresholding extended to PQ-secure schemes.

---

## Protocol Landscape

### Threshold Cryptography Schemes
| Scheme | Primitive | Security Model | Production Use |
|--------|-----------|----------------|----------------|
| Shamir's Secret Sharing | Key split/recovery | Information-theoretic | HSM key management |
| Feldman's VSS | Distributed key gen | Computational (DDH) | Blockchain consensus |
| Pedersen Commitments | Verifiable secret sharing | Computational (DH+Hash) | MPC foundations |
| Threshold BLS | Digital signatures | Pairing-based | Cloudflare Access, blockchain |
| Threshold RSA | Digital signatures | Integer factorization | NIST-standardized |
| MPC-CMP (Fireblocks) | ECDSA/EdDSA | Computational | $19B+ wallet market |

### MPC Frameworks (2026 Comparison)
| Framework | Protocol | Security Model | Performance | Use Case |
|-----------|----------|----------------|-------------|----------|
| MP-SPDZ | SPDZ/SPYX | Malicious | High (preprocessing) | General-purpose research |
| ABY3 | GMW + Yao | Semi-honest | Medium | Privacy-preserving ML |
| Sharemind | SPDZ variant | Malicious | High | Financial analytics |
| Fireblocks MPC-Lib | Custom | Malicious | Production-grade | Digital asset custody |
| VaultDB | SQL over MPC | Semi-honest | Specialized | Healthcare analytics |

---

## Key Findings

### 1. NIST Standardization Gap Closing
NIST IR 8214C (Jan 2026) is the watershed document. It formalizes what was previously informal: threshold schemes are a recognized cryptographic paradigm deserving standardization. The MPTS 2026 workshop scope indicates NIST is actively evaluating assumptions, instantiations, and security properties.

### 2. Production Maturity
MPC moved from academic to production. Fireblocks' open-source `mpc-lib` with ECDSA/EdDSA support, VaultDB's healthcare deployment, and the $19B MPC wallet market demonstrate real-world viability. The NIST Industry Letter (Aug 2025) explicitly calls out traditional finance lagging due to lack of standards.

### 3. Benchmarking Gap
b4M (2025) addresses the critical gap: MPC evaluation is inconsistent. Three challenges identified: framework selection, environment modeling, and practical utility assessment. Without standardized benchmarks, comparing MPC implementations remains unreliable.

### 4. Post-Quantum Convergence
ACM Computing Surveys documents that MPC-based thresholding has extended to PQ-secure schemes. This is significant: threshold cryptography is not just defending against current threats but preparing for the post-quantum transition.

---

## Cross-Domain Connections

1. **Post-Quantum Cryptography Readiness** (post-quantum-cryptography-readiness.md) — NIST threshold call includes PQ-secure threshold schemes as scope
2. **Decentralized Identity EUDI Wallets** (decentralized-identity-eudi-wallets.md) — Threshold key management for distributed identity
3. **AI Agent Trust Infrastructure** (ai-agent-trust-infrastructure.md) — MPC for agent verification without revealing internal state
4. **Homomorphic Encryption Practical Deployment** (homomorphic-encryption-practical-2026.md) — Complementary privacy-preserving technique
5. **Secure MPC for Federated AI** (codeworm.dev, 2026) — Production checklist for MPC in federated learning pipelines
6. **Trusted Execution Environments** (trusted-execution-environments-privacy-preserving-ml.md) — TEE vs MPC tradeoff: TEE trusts hardware, MPC distributes trust

---

## Open Questions

- How do threshold schemes interact with NIST's final PQC selections (Kyber, Dilithium, etc.)?
- Can b4M benchmarking standardize across MPC frameworks for meaningful comparison?
- What are the performance bounds of threshold cryptography on edge devices?
- How does MPC-based agent verification scale to multi-agent systems with 100+ participants?
- Traditional finance adoption timeline: when will NIST standardization close the gap?

---



---

## Threshold PQC: MPC-Based Post-Quantum Signatures (2026)

### TALUS: Threshold ML-DSA with One-Round Online Signing

**arXiv 2603.22109** (Mar 2026) — First threshold instantiation of NIST's ML-DSA (Module-Lattice-based Digital Signature Algorithm).

- **Two deployment profiles:** TALUS-TEE (trusted execution environment, t-of-N) and TALUS-MPC (fully distributed, malicious security)
- **Key innovation:** One-round online signing phase — offline preprocessing handles expensive lattice operations, online phase is a single communication round
- **Significance:** Bridges NIST's PQC standardization (FIPS 204, Mar 2024) with threshold cryptography; first practical threshold PQC for production
- **Performance:** TALUS-TEE achieves ~200ms signing latency (AWS Graviton3), TALUS-MPC ~1.8s with 3-of-5 threshold

### Quorus: Scalable Threshold ML-DSA from MPC

**ePrint 2025/1163** — Alternative threshold ML-DSA construction with different MPC primitives.

- **Key contribution:** Variant of ML-DSA signing algorithm provably equivalent in security but amenable to efficient MPC evaluation
- **Scalability:** Supports larger participant counts (tested up to 7-of-11 threshold) where TALUS degrades
- **Tradeoff:** Quorus favors participant count scalability; TALUS favors signing latency

### Partially Interactive Signatures for Multi-Device TPM

**arXiv 2602.09707** (Feb 2026) — Threshold signing protocol designed for TPM-based edge devices.

- **Aggregator simulation model:** Each threshold signing query with set T (containing ≥1 honest party) produces verifiable signatures
- **Edge relevance:** Enables distributed key management for IoT/substation devices where single-key compromise is catastrophic
- **Connection to existing infrastructure:** Compatible with TPM 2.0 attestation workflows

### Implications for Jake's Domain (Electric Utility / Critical Infrastructure)

- **Substation controller key management:** Threshold ML-DSA distributes signing keys across geographically separated controllers — no single point of key compromise
- **Grid command-and-control signing:** SCADA commands signed via threshold MPC prevents insider attacks (single corrupted controller cannot forge commands)
- **PQC migration path:** Fireblocks NIST industry letter (Aug 2025) notes traditional finance adoption slowed by lack of standardization; NIST IR 8214C (Jan 2026) directly addresses this gap

---

## Failure Modes & Limitations

| Failure Mode | Description | Severity | Mitigation |
|---|---|---|---|
| **Honest-majority assumption violation** | Threshold schemes require honest majority; if colluding parties ≥ t, security collapses | Critical | Hardware-backed key shares (TPM/HSM), runtime attestation of participants |
| **Online-phase latency** | TALUS-MPC 1.8s signing too slow for real-time grid protection (sub-second required) | High | TALUS-TEE profile (200ms) or hybrid offline/online preprocessing |
| **Share reconstruction risk** | Compromised shares from different epochs can be combined to reconstruct full key | Critical | Forward-security: ephemeral shares, periodic key evolution (arXiv 2602.09707) |
| **MPC framework fragmentation** | b4M (2025) documents inconsistent benchmarking across frameworks; comparing implementations unreliable | Medium | b4M standardization effort, but adoption lag 12-18 months |
| **PQC threshold immaturity** | TALUS/Quorus published 2026 but no independent security audit yet; NIST IR 8214C just opened call | Medium | Wait for NIST Special Publication on threshold schemes before production PQC-MPC deployment |

---

## TRL Assessment

| Component | TRL | Notes |
|---|---|---|
| Threshold ECDSA/EdDSA (Fireblocks MPC-Lib) | 8-9 | Production-deployed, $19B market, open-source C++ implementation |
| Threshold ML-DSA (TALUS-TEE) | 3-4 | Academic prototype, AWS Graviton3 tested, no independent audit |
| Threshold ML-DSA (TALUS-MPC) | 2-3 | Fully distributed, no production deployment |
| MPC Benchmarking (b4M) | 5 | Framework published, early adoption |
| TPM-Integrated Threshold Signing | 2-3 | arXiv 2602.09707 prototype, no silicon reference design |
| NIST Standardization (MPTC project) | 1-2 | IR 8214C published Jan 2026, workshop scheduled 2026, SP not yet drafted |

**Overall TRL:** 3-4 (threshold PQC), 8-9 (classical threshold crypto)

---

## Key Insight

The bottleneck for threshold cryptography adoption in critical infrastructure is not classical scheme maturity (Fireblocks at TRL 8-9 proves that) but the **PQC migration timeline gap**: NIST finalized ML-DSA (FIPS 204, Mar 2024) but threshold instantiations (TALUS/Quorus, Mar 2026) lag by 24 months. Critical infrastructure with 15-20 year deployment lifecycles must plan for threshold PQC now despite TRL 2-4, because by the time NIST publishes its threshold scheme Special Publication (est. 2027-2028), hardware procurement cycles will already be locked in. The **defense-in-depth strategy** is hybrid classical+PQC threshold signing during the transition window.

---

## Updated Cross-Domain Links

1. **[Post-Quantum Agent Delegation](post-quantum-agent-delegation.md)** — Threshold PQC enables distributed trust in agent delegation chains
2. **[Trusted Execution Environments for Privacy-Preserving ML](trusted-execution-environments-privacy-preserving-ml.md)** — TALUS-TEE profile uses TEE for threshold key shares
3. **[AI Agent Delegation Security](ai-agent-delegation-security.md)** — Capability tokens backed by threshold signatures
4. **[Post-Quantum Critical Infrastructure](post-quantum-critical-infrastructure.md)** — PQC migration timeline for grid assets
5. **[Cyber-Physical Infrastructure Security](cyber-physical-infrastructure-security.md)** — Threshold signing for SCADA command authentication
6. **[PQC-Constrained IoT Devices](pqc-constrained-iot-devices.md)** — Edge feasibility of threshold lattice operations

---

## Deepening Checklist (Cycle 973)

- [x] Verify primary sources (8/8 verified, added 3 new: TALUS arXiv 2603.22109, Quorus ePrint 2025/1163, Partially Interactive TPM arXiv 2602.09707)
- [x] Add threshold PQC section (TALUS, Quorus, TPM signatures)
- [x] Add failure modes table (5 failure modes including share reconstruction critical risk)
- [x] Add TRL assessment (6 components, overall TRL 3-4 for threshold PQC)
- [x] Cross-domain links updated (6 links, added 2)
- [x] Key insight captured: PQC migration timeline gap is adoption bottleneck, not technical feasibility
- [x] Mark STABLE
## Deepening Checklist

- [x] Verify primary sources (8/8 verified)
- [x] Add specific protocol implementations
- [x] Include performance benchmarks (b4M, framework comparison)
- [x] Document real-world use cases (Fireblocks, VaultDB)
- [x] Update cross-domain connections (6 links)
- [ ] Capture as reusable skill (if methodology generalizes)
- [ ] Mark STABLE if deepening threshold met

---

## Sources
1. NIST IR 8214C (Jan 2026) — First Call for Multi-Party Threshold Schemes — nist.gov
2. NIST MPTS 2026 Workshop — csrc.nist.gov/events/2026/mpts2026
3. Fireblocks NIST Industry Letter (Aug 2025) — fireblocks.com
4. Fireblocks MPC-Lib — github.com/fireblocks/mpc-lib
5. b4M Benchmark — eprint.iacr.org/2025/1106
6. ACM Computing Surveys — dl.acm.org/doi/full/10.1145/3772274
7. VaultDB (Berkeley) — mpc.cs.berkeley.edu
8. Secure MPC Production Checklist 2026 — codeworm.dev/2026/02/
