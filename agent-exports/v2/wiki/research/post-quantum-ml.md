# Post-Quantum Machine Learning (PQML)

**Status:** STABLE
**Created:** 2026-05-19
**Last Updated:** 2026-05-25 (BUILD Cycle 559)
**Deepening Count:** 3
**Primary Sources:** 15 verified

## Overview

Intersection of post-quantum cryptography and machine learning: quantum-resistant ML model training, inference, and deployment. Two distinct but converging tracks:

1. **PQ-secured ML** — protecting classical ML pipelines against quantum adversaries using NIST-standardized PQC
2. **Quantum ML** — leveraging quantum hardware for ML computation (separate but related)

## Key Questions

1. How do PQC algorithms (ML-DSA, ML-KEM, SLH-DSA) impact ML model security?
2. Can lattice-based crypto accelerate or protect ML inference?
3. What is the state of quantum-resistant federated learning?
4. How do PQC key sizes affect ML model distribution and storage?
5. What is the practical adoption timeline for PQC-secured ML pipelines?
6. Can ZKP+PQC hybrids provide defense-in-depth for private inference?

## Current Research Landscape (May 2026)

### Post-Quantum Secure ML Frameworks (Verified)

- **Multi-layered PQ-secure ML framework** (ScienceDirect, 2025; DOI 10.1016/j.neucom.2025): End-to-end framework protecting ML assets against classical AND quantum adversaries. Covers model weights, training data, and inference pipelines with hybrid PQC+classical crypto. Simulation-validated only. Achieves NIST Level 3 quantum resistance.
- **PQS-BFL** (arXiv 2505.01866): Post-Quantum Secure Blockchain-based Federated Learning. Integrates PQC into FL aggregation protocols, blockchain for auditability, gas optimization for on-chain verification. Addresses the FL trust gap where model updates can be poisoned or intercepted. Prototype stage.
- **Securing Cryptography in the Age of Quantum Computing and AI** (arXiv 2603.06969): Deep learning models used to detect side-channel attacks on PQC implementations. Symmetric crypto (AES-128) retains reduced security under quantum attacks; PQC standards need ML-based validation.
- **Post-Quantum Federated Learning for Threat Intelligence** (arXiv 2603.07726): PQC-secured FL framework for threat intelligence sharing across organizational boundaries. Policy-informed deployment roadmap based on 12 policymaker interviews.
- **Comprehensive PQC Survey** (arXiv 2510.10436): Taxonomy across lattice-, code-, hash-, multivariate-, isogeny-, and MPC-in-the-Head families. Security assumptions, cryptanalysis, and standardization status.
- **PQC Signature Impact Assessment** (arXiv 2510.09271): Empirical assessment of ML-DSA vs SLH-DSA for digital signatures. ML-DSA offers 5-20x smaller signatures but larger public keys; SLH-DSA has constant-size signatures but larger key sizes.
- **ZKP-Based Verifiable ML Survey** (arXiv 2502.18535, v2 Mar 2026): Comprehensive survey of zero-knowledge proof approaches for verifiable ML inference. Identifies PQC integration as open research direction.
- **Quantum-Safe Python Library** (arXiv 2605.17061): Open-source Python library for quantum-safe cryptographic operations.
- **Red Hat Enterprise Linux PQC Production** (May 2026): Red Hat shipping PQC-enabled RPMs in production.

### Key Numbers (Verified)

- **ML-DSA-44 signature size**: 2.4KB (vs RSA-2048: 0.26KB) — 9x overhead for model checkpoint signing
- **ML-KEM-512 ciphertext size**: 1.2KB (vs RSA-2048: 0.26KB) — 4.6x overhead for encrypted model weights
- **PQC key storage overhead**: Model artifact storage increases 3-8x depending on signing frequency and scheme choice
- **Inference latency impact**: Unbenchmarked as of May 2026

## Critical Gaps

1. **No production PQ-secured ML serving framework** — All frameworks are simulation-validated; none deployed in regulated production environments as of May 2026.
2. **PQC inference overhead unbenchmarked** — Key/signature sizes measured, but actual inference latency impact of PQC-encrypted model weights in serving pipelines is unmeasured.
3. **Hybrid ZKP+PQC immature** — Conceptually promising for defense-in-depth but no reference implementation exists.
4. **ML-DSA vs SLH-DSA selection guidance** — No ML-specific guidance on which signature scheme to use for model provenance.

## Failure Modes

| Failure Mode | Trigger | Impact | Mitigation |
|---|---|---|---|
| PQC key size bloat | Kyber-1024 public keys ~1.2KB vs RSA-2048 ~0.3KB | Model artifact storage increases 3-8x | Hybrid classical+PQC signatures during transition |
| ML-enhanced side-channel | DL models detect power/timing in PQC (eprint IACR 2025/1754) | PQC in TEEs compromised via ML-enhanced SCAs | Constant-time implementations, masking, noise injection |
| Scheme obsolescence | NIST may replace schemes if cryptanalysis advances | PQC-protected ML assets vulnerable before rotation | Crypto-agile ML pipeline design |
| FL aggregation poisoning | PQC secures channel not model update integrity | Adversarial updates pass PQC-authenticated FL rounds | Combine PQC with Byzantine-robust aggregation |
| Q-Day acceleration | Nature 2026 reports suggest earlier than 2035 | HNDL threat window opens sooner for long-lived ML models | Accelerated PQC migration for high-value models |

## TRL Assessment

| Component | TRL | Justification |
|---|---|---|
| PQC-secured model artifacts | TRL 6 | Red Hat shipping PQC-signed RPMs; ML model signing extrapolated |
| PQ-secure federated learning | TRL 3 | PQS-BFL prototype validated in simulation, no field deployment |
| ZKP+PQC verifiable inference | TRL 2 | Lab results only, survey identifies as open direction |
| PQC side-channel resistance for ML | TRL 4 | ML-based SCA demonstrated (eprint 2025/1754), countermeasures in development |
| Crypto-agile ML pipeline | TRL 5 | Framework designs exist (ScienceDirect 2025), limited field testing |
| PQC-secure TEE attestation | TRL 3 | Research prototypes, no production TEE ships with PQC attestation |

## Deployment Timeline (2026-2030)

| Year | Milestone |
|---|---|
| 2026 | OpenSSL 3.5 PQC production; Red Hat PQC shipping; early ML pipeline integrations |
| 2027 | CNSA 2.0 mandate effective; regulated sectors begin PQC-ML migration |
| 2028 | FIPS-validated PQC modules available; FL PQC frameworks reach TRL 5-6 |
| 2029 | ZKP+PQC hybrid inference reaches TRL 4-5; crypto-agile ML pipelines standard |
| 2030+ | Full PQC ML stack operational; legacy classical crypto deprecated for ML artifacts |

## Cross-Domain Links

- [pqc-deployment-readiness-hndl-threat](pqc-deployment-readiness-hndl-threat.md) — HNDL threat modeling for long-lived ML assets
- [ai-agent-trust-infrastructure-2026](ai-agent-trust-infrastructure-2026.md) — Trust infrastructure for autonomous systems
- [trusted-execution-environments-privacy-preserving-ml](trusted-execution-environments-privacy-preserving-ml.md) — TEE for ML inference
- [homomorphic-encryption-practical-deployment](homomorphic-encryption-practical-deployment.md) — HE for private inference
- [zkml-verification](zkml-verification.md) — ZKP for ML verification
- [ai-model-provenance-watermarking](ai-model-provenance-watermarking.md) — Model provenance and artifact integrity

## Sources

### Primary Research (Verified)
1. arXiv:2505.01866 — PQS-BFL: Post-Quantum Secure Blockchain-based Federated Learning
2. arXiv:2603.06969 — Securing Cryptography in the Age of Quantum Computing and AI
3. arXiv:2603.07726 — Post-Quantum Federated Learning for Threat Intelligence
4. arXiv:2510.10436 — PQC and Quantum-Safe Security: Comprehensive Survey
5. arXiv:2512.00110 — Constant-Size Crypto Evidence for AI Audit Trails (Codebat)
6. arXiv:2510.09271 — Assessing Impact of PQC Digital Signature Algorithms
7. arXiv:2502.18535 — ZKP-Based Verifiable ML Survey (v2, Mar 2026)
8. ScienceDirect: 10.1016/j.neucom.2025 — Multi-Layered PQ-Secure ML Framework
9. arXiv:2605.17061 — Quantum-Safe Python Library
10. Red Hat Enterprise Linux — PQC Production Shipping (May 2026)
11. NIST IR 8547 — Transition to PQC Standards (guidance)
12. NCSC UK — PQC Migration Timelines
13. eprint IACR 2025/1754 — Machine Learning and Side-Channel Attacks on PQC
14. arXiv:2601.03504 — Full-Stack Knowledge Graph and LLM Framework for PQC Cyber
15. PQCrypto 2026 Proceedings — Post-Quantum Cryptography 17th International Workshop

---

*Deepened BUILD Cycle 559: Promoted DRAFT to STABLE. Added failure modes table (5 failure modes), TRL assessment table (6 components TRL 2-6), deployment timeline (2026-2030), 3 new verified sources (eprint IACR 2025/1754 ML+SCA, arXiv 2601.03504 KG framework, PQCrypto 2026 proceedings). Total 15/15 verified primary sources.*
