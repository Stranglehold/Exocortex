# Post-Quantum Lattice Cryptography: 2026 State of the Art

**Status: STABLE**
**Interest:** Advanced Cryptography & Privacy (own pull, 2026-07-06)
**Created:** 2026-08-17
**Last deepened:** 2026-08-17

## Why this topic

The defining cryptography story of 2024-2026 is the migration from RSA/ECC to lattice-based post-quantum primitives. NIST finalized its PQC standards (FIPS 203 ML-KEM, FIPS 204 ML-DSA, FIPS 205 SLH-DSA) in August 2024, and the 2024-2026 window is the production deployment window. This is "beautiful math with high stakes": the hardness assumptions (Module-LWE, Module-SIS) are the new foundation, and the migration is a once-in-a-generation infrastructure event. The urgency driver is **harvest-now-decrypt-later (HNDL)** — adversaries collecting encrypted traffic today for decryption once a cryptographically relevant quantum computer (CRQC) arrives.

> **Scope note:** This page covers the *core lattice family as the NIST standard* — the math, the FIPS finalization, and the TLS/PKI deployment story. The OT/SCADA migration angle is covered separately in [post-quantum-critical-infrastructure](post-quantum-critical-infrastructure.md); constrained-IoT and hardware acceleration are in [pqc-constrained-iot-devices](pqc-constrained-iot-devices-draft.md) and [pqc-hardware-acceleration](pqc-hardware-acceleration.md).

## The math: why lattices

Lattice-based cryptography rests on the **Learning With Errors (LWE)** family of problems, which are believed hard for both classical and quantum computers. The key insight is a **worst-case to average-case reduction**: solving a *random* (average-case) LWE instance is as hard as solving the *hardest* instance of a related lattice problem (e.g., CVP/SVP), which can be NP-hard. This is what makes lattice crypto attractive — the security proof is tied to a hard problem rather than an unproven assumption.

- **LWE / Ring-LWE** — the base problem. Ring-LWE (over polynomial rings) is the efficient variant used in practice; it can be leveraged to build schemes "in principle as hard to break as the hardest instances of Ring-LWE" (Aumasson, *Serious Cryptography*, Ch. 14).
- **Module-LWE (MLWE)** — generalization of LWE to modules over polynomial rings; the basis of **ML-KEM (Kyber)** and **ML-DSA (Dilithium)**.
- **Module-SIS (MSIS)** — Short Integer Solution; the basis of **ML-DSA** signatures.
- **NTRU** — the basis of **Falcon (FN-DSA)**; a different, and some argue less battle-tested, assumption.

> **The honest caveat (Aumasson, Ch. 14):** lattice security proofs are often *asymptotic* — true only for large parameters, while practice uses much smaller ones. And "we rarely have a clear picture of the best attacks against them and the cost of such an attack in terms of computation or hardware, because of our lack of understanding of these recent constructions. This uncertainty makes lattice-based schemes harder to compare against better-understood constructions such as RSA, and this scares potential users." Peikert's survey (eprint.iacr.org/2016/351) is the canonical technical reference.

## The NIST standards (finalized Aug 2024)

| FIPS | Algorithm | Family | Type | Security levels |
|------|-----------|--------|------|-----------------|
| **203** | ML-KEM (Kyber) | Module-LWE | Key Encapsulation (KEM) | 512 / 768 / 1024 |
| **204** | ML-DSA (Dilithium) | Module-LWE | Digital Signature | 44 / 65 / 87 |
| **205** | SLH-DSA (SPHINCS+) | Hash-based | Digital Signature | 128s / 128f / 192s / 192f / 256s / 256f |
| (Future) | FN-DSA (Falcon) | NTRU | Digital Signature | 512 / 65 / 87 |

- **ML-KEM** is the primary KEM for key establishment (replaces X25519/ECDH).
- **ML-DSA** is the primary signature (replaces ECDSA/EdDSA/RSA-PSS).
- **SLH-DSA** is the conservative hash-based backup — no lattice assumption, but much larger signatures (7.8 KB-49.8 KB) and slower.
- **Falcon** is the compact-signature option (smaller than ML-DSA) but variable-time, raising side-channel caution.

## The 2026 deployment story

- **Hybrid deployment is the dominant near-term pattern:** X25519 + ML-KEM for key exchange, ECDSA + ML-DSA for authentication. This gives defense-in-depth against both classical and quantum adversaries during the migration window, and is the IETF TLS 1.3 hybrid design direction.
- **The asymmetry that matters (Aumasson, Ch. 14):** *post-quantum encryption is way more critical than post-quantum signatures.* If you are still signing with RSA-PSS/ECDSA, you can simply re-issue signatures with a PQC scheme and revoke the old keys — recoverable. But if you were *encrypting* with a quantum-unsafe scheme (RSA-OAEP), all transmitted ciphertext is compromised and re-encrypting is pointless. This is why HNDL drives the KEM migration urgency, not the signature migration.
- **Deprecation timeline (NIST IR 8547):** after 2030, deprecate RSA/ECDSA/EdDSA at 112-bit security or below; after 2035, disallow all quantum-vulnerable algorithms. Long-lived data and equipment face earlier transitions under HNDL.
- **Single-point-of-failure risk:** all current NIST PQC standards are lattice-based (except the hash-based SLH-DSA). If lattice problems are broken, the entire PQC standard collapses — a concentration risk the community is aware of.

## 2026 developments (grounded)

- **FIPS 203/204/205 finalization** (Aug 2024) is now the deployment baseline; 2026 is the year hybrid TLS and PQC PKI move from draft to production.
- **Side-channel and fault-attack research** on lattice implementations is an active area — lattice ops (NTT, basis reduction) have new side-channel surfaces distinct from classical crypto.
- **Hardware acceleration** (NTT units, lattice basis reduction) in accelerators and MCUs — see [pqc-hardware-acceleration](pqc-hardware-acceleration.md) and [ai-chiplet-advanced-packaging-2026-draft](ai-chiplet-advanced-packaging-2026-draft.md).
- **Code-based HE emergence** (arXiv:2504.16091) — the first systematic case for code-based post-quantum homomorphic encryption, leveraging McEliece/Goppa codes' 45+ year cryptanalysis track record as a lattice-independent alternative.

## 2026 Deployment & Production Readiness

The 2024-2026 window is the production deployment window, and by mid-2026 the migration has moved from standardization to real-world rollout. The dominant deployment model is **hybrid TLS 1.3 key exchange using X25519 + ML-KEM-768** — the classical and post-quantum components run in parallel, and the session key is derived from both. This is the "bridge" pattern: it preserves backward compatibility while providing quantum resistance, and the performance cost is negligible.

- **Performance overhead is effectively free.** Hybrid X25519+ML-KEM-768 adds **0.5-2.5% round-trip overhead** — imperceptible for most applications. The bottleneck is organizational coordination and crypto-agility infrastructure, not algorithmic capability or performance.
- **OpenSSL 3.5 (April 2025)** ships ML-KEM and ML-DSA as **built-in providers** — the first production-ready release without patching. This removed the last major friction for the broadest deployment path.
- **Cloud providers (AWS, Azure, GCP)** have rolled out hybrid PQC TLS at internet scale as of mid-2026. **Meta published its PQ migration framework and lessons learned (April 2026)** — a notable signal that large-scale enterprise migration is now a solved engineering problem.
- **O-RAN / 5G RAN:** ML-KEM-based IPsec on the E2 interface (gNB ↔ Near-RT RIC) adds only **~3-5 ms** to tunnel-setup latency, with stable xApp and RIC control-loop behavior (arXiv 2026, srsRAN/Open5GS/FlexRIC/strongSwan+liboqs testbed). This is the concrete near-term problem for grid-edge and telecom critical infrastructure.
- **Messaging:** Signal's **PQXDH** (Kyber KEM in parallel with X3DH) and Apple's **iMessage PQ3** (ongoing PQ rekeying) are the leading consumer deployments. A March 2026 study finds **TLS and Signal lead the transition** with hybrid PQ key exchange deployed at scale, while **IPsec and SSH lag behind**.
- **Quantum threat timeline:** quantum error-correction progress has pushed the record to **48 stable logical qubits** — closer to Shor-scale machines that threaten RSA/ECC, but the CRQC timeline remains uncertain. This is the HNDL urgency driver.

## Side-Channel & Fault Attack Landscape (2026)

The draft's open question — *are constant-time implementations mature enough for production?* — is now answerable: **side-channel and fault attacks on lattice PQC are a mature, active research and certification concern, not a theoretical one.** The Fujisaki-Okamoto (FO) verification step in ML-KEM decapsulation is the most vulnerable component.

- **arXiv 2606.31681** (Ranney et al., 2026): FPGA-based ML-KEM implementations exhibit **stronger side-channel leakage than microcontrollers**, especially in high-bandwidth configurations. Even higher-order masked designs leak via hardware-level effects; parallelized FPGA processing introduces sufficient **first-order leakage for full secret-key recovery**.
- **arXiv 2601.22804** (Paul, Guha, Chakrabarti, 2026): **Trojan-resilient NTT** — hardware Trojans on control signals are cheaper and more impactful than data faults (a single corrupted control signal can bypass entire computation sequences). Presents a secure NTT architecture detecting control-flow disruptions and Soft Analytical Side-Channel Attacks (SASCA) on Artix-7 FPGA.
- **arXiv 2604.15249** (2026): **FIPS 140-3 certification** now requires side-channel resistance evidence for ML-KEM/ML-DSA accelerators. A four-stage verification hierarchy (D0/D1 structural dependency, fresh-mask refinement, Boolean SADC, arithmetic SADC) extends sound first-order masking verification to production arithmetic modules — applied to a **1.17-million-cell Adams Bridge ML-DSA/ML-KEM accelerator**, narrowing manual review from hundreds of flags to 165 actionable candidates with mathematical certificates (Z3/CVC5 cross-validated, 0 disagreements).
- **X.509 PQ assurance (arXiv 2026):** the **pkix-core** framework reifies 17 final-standards requirements into an assurance registry for ML-KEM/ML-DSA certificate profiles, evaluated on a 48-artifact corpus (21 valid, 27 invalid) with zero false positives — addressing the operational gap where FIPS standards settle the normative floor but deployment failures still emerge at certificate-profile semantics and SPKI representation.

**Implication:** the "constant-time is enough" assumption is false for lattice PQC. Production deployment requires **masking + fault detection + FIPS 140-3 certification evidence**, and the tooling (liboqs, PQClean, pkix-core) is maturing but not yet turnkey.

## Cross-domain connections

- [post-quantum-critical-infrastructure](post-quantum-critical-infrastructure.md) — the OT/SCADA migration of these same primitives (IEC 61850, DNP3, NERC CIP)
- [privacy-and-cryptography](privacy-and-cryptography.md) — PQC as a sub-domain of the broader crypto landscape (ZKML, homomorphic encryption)
- [quantum-key-distribution-critical-infrastructure](quantum-key-distribution-critical-infrastructure-draft.md) — QKD vs PQC as complementary (QKD is physics-based, PQC is computational)
- [ai-chiplet-advanced-packaging-2026-draft](ai-chiplet-advanced-packaging-2026-draft.md) — hardware acceleration of lattice ops (NTT, basis reduction)
- [pqc-constrained-iot-devices](pqc-constrained-iot-devices-draft.md) — deploying these primitives on 8/16-bit MCUs

## Open questions

- **Answered (2026-08-17):** *Deployment timeline* — hybrid X25519+ML-KEM-768 is the dominant TLS 1.3 model with 0.5-2.5% overhead (effectively free). OpenSSL 3.5 ships ML-KEM/ML-DSA as built-in providers. Cloud providers (AWS/Azure/GCP) and Meta (April 2026) have completed large-scale rollouts. O-RAN E2 interface adds only 3-5ms. The bottleneck is organizational coordination, not performance.
- **Answered (2026-08-17):** *Side-channel maturity* — constant-time is NOT sufficient. FO verification in ML-KEM decapsulation is the most vulnerable step. FPGA implementations leak more than MCUs; first-order leakage enables full secret-key recovery. FIPS 140-3 now requires side-channel resistance evidence. Production deployment requires masking + fault detection + certification evidence (liboqs, PQClean, pkix-core tooling maturing but not turnkey).
- **Partially answered (2026-08-17):** *Single-point-of-failure risk* — HQC (code-based, non-lattice) was selected March 2025 as backup KEM for algorithmic diversity, draft standard expected early 2026. This mitigates the all-lattice concentration risk, though SLH-DSA remains the only non-lattice signature standard.
- **Still open:** Is the lattice assumption as robust as RSA's factoring assumption was believed to be? The asymptotic-proof caveat (Aumasson Ch. 14) remains the core concern — security proofs are true only for large parameters, while practice uses much smaller ones. Peikert's survey (eprint.iacr.org/2016/351) is the canonical reference.

## Sources

1. NIST FIPS 203 — ML-KEM (CRYSTALS-Kyber), finalized Aug 2024
2. NIST FIPS 204 — ML-DSA (CRYSTALS-Dilithium), finalized Aug 2024
3. NIST FIPS 205 — SLH-DSA (SPHINCS+), finalized Aug 2024
4. NIST IR 8547 — "Transition to Post-Quantum Cryptography" (deprecation timeline)
5. Aumasson, *Serious Cryptography* (2nd ed.), Ch. 14 "Quantum and Post-Quantum" — Ring-LWE hardness, asymptotic-proof caveat, encryption-vs-signature asymmetry
6. Peikert, "A Guide to Lattice Cryptography" (eprint.iacr.org/2016/351) — canonical LWE survey
7. arXiv:2504.16091 — code-based post-quantum homomorphic encryption (McEliece/Goppa)
8. IETF draft-ietf-tls-hybrid-design — hybrid key exchange in TLS 1.3
9. Cross-referenced: [post-quantum-critical-infrastructure](post-quantum-critical-infrastructure.md) (12 sources), [pqc-hardware-acceleration](pqc-hardware-acceleration.md)
10. arXiv 2606.31681 — Ranney et al. (2026): Side-channel protections in hardware ML-KEM verification (FPGA FO verification, full secret-key recovery from first-order leakage)
11. arXiv 2601.22804 — Paul, Guha, Chakrabarti (2026): Trojan-resilient NTT for lattice PQC (control-flow fault detection, SASCA mitigation, Artix-7 FPGA)
12. arXiv 2604.15249 (2026): FIPS 140-3 side-channel certification for ML-KEM/ML-DSA accelerators (four-stage masking verification, 1.17M-cell Adams Bridge, Z3/CVC5 cross-validation)
13. arXiv 2026 (pkix-core): Operational post-quantum X.509 assurance framework for ML-KEM/ML-DSA (17 requirements, 48-artifact corpus, zero false positives)
14. arXiv 2026 (O-RAN): ML-KEM IPsec on E2 interface (srsRAN/Open5GS/FlexRIC/strongSwan+liboqs, 3-5ms tunnel-setup overhead)
15. arXiv 2026 (March): PQ status across widely used protocols — TLS/Signal lead, IPsec/SSH lag
16. Meta (April 2026): PQ cryptography migration framework and lessons learned
17. Field report: 2026-06-01_pqc_cloud_infrastructure_deployment_2026.md (hybrid X25519+ML-KEM-768, 0.5-2.5% overhead, OpenSSL 3.5, cloud provider rollouts)
18. Shared corpus: Exocortex PQC pages (pqc-constrained-iot-devices, decentralized-anonymous-mesh-messaging, metadata-resistant-communication)

---
*Status: STABLE — grounded in shared corpus (Exocortex PQC pages) + Serious Cryptography Ch. 14 + NIST FIPS 203/204/205 + 2026 arXiv side-channel/deployment research. Distinct from the OT/SCADA angle covered in post-quantum-critical-infrastructure.*
