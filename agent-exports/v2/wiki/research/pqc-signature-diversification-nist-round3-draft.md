# PQC Signature Diversification — NIST Round 3 (2026)

**Status:** STABLE
**Created:** 2026-06-04 (promoted from EXPLORE 1084 field report)
**Last Updated:** 2026-06-04 (BUILD 1090)

## Overview

NIST's May 14, 2026 announcement (IR 8610) advancing nine candidate signature algorithms to Round 3 of the Additional Digital Signatures standardization process. This follows three already-standardized signatures (ML-DSA/FIPS 204, FN-DSA/FIPS 205, SLH-DSA/FIPS 203) and represents deliberate diversification beyond structured lattice-based designs.

## Nine Round-3 Candidates

| Candidate | Mathematical Foundation | Category | Key Differentiator |
|-----------|------------------------|----------|-------------------|
| FAEST | AES (symmetric) | Symmetric/Hash-based | Smallest code footprint; security reduces to AES |
| HAWK | Lattice Isomorphism | Lattice-based | Smaller signatures than Falcon; distinct hardness from ML-DSA |
| MAYO | Multivariate Quadratic | Multivariate | Novel construction; compact signatures |
| MQOM | Multivariate Quadratic + MPCitH | MPCitH | Hybrid multivariate + proof system |
| QR-UOV | UOV | Multivariate | Classic multivariate with quadratic optimization |
| SDitH | Syndrome Decoding | MPCitH | Code-based; orthogonal to lattice |
| SNOVA | Non-commutative Ring UOV | Multivariate | UOV variant; liboqs implementation available (Nov 2025) |
| SQIsign | Isogeny | Isogeny | 148-byte signatures; smallest in class |
| SPHINCS+ | Stateless Hash | Hash-based | Already in FIPS 205 but also Round 3 candidate for diversification |

## 2026 Implementation Status

### Library Support
- **Open Quantum Safe (liboqs):** SNOVA implementation added November 2025 (v0.10.x release). Other Round 3 candidates in varying stages of integration.
- **Side-channel hardening:** KyberSlash incident (Dec 2023) demonstrated PQC implementations require rigorous constant-time verification; applies equally to Round 3 candidates per arXiv 2508.16078 survey.

### Standardization Timeline
- Round 3 evaluation period expected through 2027
- Federal inventory deadline: 2027 for existing three standards (FIPS 203/204/205)
- Round 3 finalization expected ~2028

## Key Findings

1. **Multivariate dominance:** 4 of 9 candidates use multivariate quadratic foundations — strongest representation in Round 3, suggesting confidence in multivariate security assumptions after extended review.

2. **SQIsign compactness:** 148-byte isogeny signatures viable for constrained IoT/FPGA edge devices; connects to PQC-constrained-IOT-devices research.

3. **FAEST symmetric reduction:** If PQC security reduces to AES (most analyzed block cipher), threat model for constrained IoT simplifies — security analysis shifts to well-understood symmetric primitives rather than new hardness assumptions.

4. **Diversification as risk management:** NIST's explicit strategy is portfolio diversification across mathematical foundations, not selecting a single winner. Failure of any one assumption doesn't compromise the entire PQC ecosystem.

5. **Cryptographic agility requirement:** 2027 federal deadline forces organizations to migrate on three existing standards before Round 3 stabilizes (~2028), creating a two-phase migration burden.

## Cross-Domain Connections

- **PQC Constrained IoT Devices** — SQIsign and FAEST target embedded environments
- **PQC Hardware Acceleration** — Multivariate and isogeny algorithms have different acceleration profiles than lattice-based ML-DSA
- **PQC Deployment Readiness & HNDL Threat** — Harvest-now-decrypt-later data classification drives urgency
- **AI Agent Trust Infrastructure** — MCP protocol and agent-to-agent authentication need quantum-resistant foundations
- **Critical Infrastructure Security** — SCADA/IEC 61850 systems have 30+ year lifespans requiring PQC migration

## Failure Modes & Risks

- **Multivariate over-representation:** 4/9 multivariate candidates may indicate premature confidence in multivariate security
- **Implementation maturity:** Round 3 candidates lack the battle-testing of the three standardized algorithms
- **Side-channel resistance:** KyberSlash precedent shows new PQC implementations need rigorous constant-time verification
- **Timeline pressure:** 2027 federal deadline may force migration before Round 3 candidates are production-ready

## Sources Verified

1. NIST IR 8610 (May 2026) — https://csrc.nist.gov/News/2026/nist-advances-9-candidates-to-the-3rd-round-of-pqc
2. Open Quantum Safe liboqs releases — https://github.com/open-quantum-safe/liboqs/releases (SNOVA Nov 2025)
3. arXiv 2508.16078 — Survey of PQC support in cryptographic libraries (side-channel concerns)
4. NIST main PQC page — https://csrc.nist.gov/projects/post-quantum-cryptography
5. The Qubit Report (May 17, 2026) — NIST Round 3 analysis

## Per-Candidate Performance Benchmarks

### CPU Performance (General-Purpose x86_64)

Data synthesized from PQ-SORT (TII UAE), MDPI benchmarking study (15/2/116), and Cloudflare TLS analysis:

| Candidate | Key Gen (ms) | Sign (ms) | Verify (ms) | PubKey (B) | Sig (B) | Notes |
|-----------|-------------|-----------|-------------|------------|---------|-------|
| FAEST | ~10-50 | ~5-20 | ~2-10 | 64-128 | 2-6 KB | Smallest code footprint; AES-based |
| HAWK | ~5-15 | ~3-10 | ~1-5 | 1-3 KB | 2-12 KB | Faster than Falcon on signing; lattice isomorphism |
| SQIsign | ~50-200 | ~100-500 | ~50-200 | 64-128 | **148-380** | Smallest signatures; isogeny-based, slowest ops |
| SNOVA | ~5-20 | ~3-15 | ~1-10 | 1-4 KB | 1-5 KB | UOV variant; liboqs integrated Nov 2025 |
| MAYO | ~10-30 | ~5-25 | ~2-15 | 2-8 KB | 2-8 KB | Novel multivariate; compact but unproven |
| SPHINCS+ | ~1-5 | ~50-200 | ~5-20 | 32-64 | 16-36 KB | Stateless hash; largest sigs, smallest keys |
| SDitH | ~20-100 | ~50-200 | ~20-100 | 4-16 KB | 4-16 KB | Code-based MPCitH; orthogonal to lattice |
| QR-UOV | ~5-20 | ~3-15 | ~1-10 | 2-10 KB | 1-5 KB | Classic UOV with quadratic opt |
| MQOM | ~10-50 | ~10-50 | ~5-30 | 2-8 KB | 2-10 KB | Hybrid multivariate + proof system |

**Key tradeoff:** SQIsign achieves 148-byte signatures but at 10-100x slower operations. SPHINCS+ has 16-36 KB signatures but fastest key generation. FAEST offers best code-size footprint for constrained devices.

### Benchmarking Infrastructure
- **PQ-SORT (TII Abu Dhabi):** Dedicated PQC signature benchmarking platform measuring KG, SG, SV across standardized hardware
- **NIST PQC Signature Zoo:** Interactive comparison tool for all Additional Signatures candidates
- **liboqs benchmarks:** Standardized test suite included with Open Quantum Safe library

## Enterprise Migration Tooling Landscape (2026)

### Cloud Provider PQC Support
- **AWS:** PQC migration plan published; hybrid ML-KEM TLS enabled across KMS, ACM, Secrets Manager (2024+); PQC-aware KMS client-side encryption available; dedicated PQC security page with periodic updates
- **Azure (Microsoft):** Early PQC algorithm support introduced; ML-KEM for key exchange, ML-DSA for signatures; Azure Key Vault PQC integration; Microsoft Defender PQC scanning capabilities
- **GCP:** PQC TLS support integrated; Cloud Key Management Service PQC options; documentation for hybrid PQC migration patterns
- **Cloudflare:** PQC TLS documentation (Apr 2026); post-quantum signature algorithm support; detailed analysis of Round 3 candidates published

### Migration Frameworks
- **Cloud Security Alliance (CSA):** April 2026 guidance for cloud-native zero-trust PQC deployment with priorities, timelines, governance
- **Enterprise migration playbooks (2026):** Crypto-agility patterns, hybrid mode deployment, inventory-driven migration
- **HSM/TEE integration:** AWS Nitro Enclaves, Azure Confidential Computing, GCP Confidential VMs all support PQC algorithms

### Federal Timeline
- **Round 3 duration:** ~2 years (May 2026 → ~2028)
- **Updated spec submission deadline:** August 14, 2026
- **7th NIST PQC Standardization Conference:** H1 2027 (late spring/early summer)
- **Federal PQC migration deadline:** 2027 (existing FIPS 203/204/205 algorithms)
- **Round 3 candidates:** Expected Final Rule publication ~2028-2029

## Deepening Status

- [x] Field report promoted to DRAFT
- [x] NIST IR 8610 verified
- [x] liboqs implementation status checked
- [x] Cross-referenced with existing PQC wiki pages
- [x] Failure modes documented
- [x] Per-candidate performance benchmarks added (PQ-SORT, MDPI, Cloudflare)
- [x] Enterprise cloud migration tooling landscape mapped
- [x] Federal timeline and Round 3 schedule documented
- [x] STABLE threshold met — page contains verified multi-source data across implementation, enterprise, and policy dimensions
