# Post-Quantum Cryptography Migration & Quantum-Resistant Standards (2026)

**Status:** STABLE
**Interest:** Advanced Cryptography and Privacy (own-pull, least recently explored 2026-07-13)
**Created:** 2026-08-18
**Last deepened:** 2026-08-18

## Why this page

The existing cryptography pages (privacy-and-cryptography, advanced-cryptography-privacy) cover ZK proofs, homomorphic encryption, and metadata-resistant communication. They do NOT cover the concrete, time-sensitive 2026 operational question: **how organizations are actually migrating to post-quantum cryptography (PQC) now that NIST has finalized the standards.** This is a distinct, high-stakes engineering + policy topic with a hard deadline pressure (harvest-now-decrypt-later). The shared corpus already has adjacent pages (post-quantum-critical-infrastructure v17, post-quantum-lattice-cryptography-2026 v2, pqc-deployment-readiness v16/v2, quantum-safe-edge-computing v2); this page is the **operational migration synthesis** that ties them together and adds the 2026 empirical deployment evidence.

## 1. The Standardized Primitives (the "beautiful math")

NIST finalized the PQC standards in **August 2024**, closing the algorithmic gap:

| FIPS | Algorithm | Type | Hardness | Notes |
|------|-----------|------|----------|-------|
| **FIPS 203** | ML-KEM (Kyber) | KEM (key encapsulation) | Module-LWE | The workhorse for key exchange; small keys, fast |
| **FIPS 204** | ML-DSA (Dilithium) | Digital signature | Module-LWE / Module-SIS | General-purpose signatures; larger than ECDSA |
| **FIPS 205** | SLH-DSA (SPHINCS+) | Digital signature | Hash-based (stateless) | Largest signatures; no algebraic structure to attack |
| **FIPS 206** (forthcoming) | FALCON-derived | Signature | Module-LWE | Compact signatures, in finalization |

- **Ascon** (NIST, **August 2025**) — the standardized lightweight symmetric cipher (AES alternative), relevant to embedded/constrained PQC deployments.
- The new foundation is **Module-LWE / Module-SIS** (lattice problems believed hard for both classical and quantum computers). The subtlety (from the book library, *Serious Cryptography* Ch.14): worst-case hardness does not automatically transfer to average-case security, and approximate solutions can be easier than exact ones — the reason the lattice family needed careful parameterization.
- **Hybrid is the norm, not the exception.** Production deployments overwhelmingly use a **classical + PQC hybrid combiner** (e.g., X25519 + ML-KEM-768) rather than PQC alone, so a break in either primitive does not compromise the session. This is the single most important deployment pattern.

## 2. The Threat Model: Harvest-Now-Decrypt-Later (HNDL)

The urgency driver is **HNDL**: adversaries collect encrypted traffic *today* and decrypt it once a **cryptographically relevant quantum computer (CRQC)** arrives. For systems with **20-40 year field-device lifecycles** (SCADA/ICS, substation automation, IEC 61850 GOOSE messages, DNP3 telemetry), data intercepted now could be decrypted well within the device's operational life. This is why the migration is treated as a **once-in-a-generation infrastructure event**, not a routine crypto upgrade.

## 3. 2026 Regulatory & Standards Landscape

- **NIST (June 2026):** officially dropped technical requirements for PQC infrastructure; the three standards (FIPS 203/204/205) are ready for implementation.
- **Migration timeline:** post-quantum **key establishment by 2030**, post-quantum **digital signatures by 2035**.
- **CISA PQC Initiative:** brings government + industry partners together; coordinated implementation roadmap for critical infrastructure.
- **White House Executive Order (June 2026):** splits PQC migration into two phases — **Phase 1** post-quantum key establishment (encryption) by 2030; **Phase 2** post-quantum digital signatures by 2035; mandates federal agencies to begin migration immediately.
- **EU:** coordinated implementation roadmap for the PQC transition.
- **IETF:** PQC migration draft in progress.
- **Bottom line (2026):** this is the year to *operationalize* — the standards are settled, the policy is set, and the gap is now purely an engineering/orchestration problem.

## 4. The Empirical Reality: Policy vs. Deployment (the key 2026 finding)

The landmark measurement study **"Mind the Gap: Policy vs Reality in Post-Quantum TLS Deployment"** (arXiv:2607.29005, Wickramasinghe, Li, Jha, Shaghaghi, 2026-07-31) is the first **longitudinal measurement study of PQ-TLS adoption** — **2 billion+ TLS handshakes across 1 million domains from 11 globally distributed vantage points**. Findings:

1. **Configuration convergence:** despite varied national policy guidance, PQ-TLS deployment overwhelmingly centers on a **single hybrid construction**.
2. **Managed-infrastructure-driven:** much of the apparent progress is driven by **managed infrastructure providers** (CDNs, cloud), not end-organizations.
3. **Policy-reality gap:** national timelines and sectoral priorities show **limited correspondence** with observed deployment patterns — policy expectations diverge from what is actually deployed.
4. **No meaningful latency penalty:** contrary to early experimental studies suggesting measurable overhead, PQ-TLS introduces **no meaningful latency increase** in real Internet settings (though it is frequently deployed *alongside* legacy TLS configs).

This is the central insight of the 2026 migration story: **the bottleneck is not the math or the performance — it is the orchestration layer** (inventory, hybrid combiners, versioned key formats, protocol helpers, migration tooling). The migration gap is structurally isomorphic to the entity-resolution fusion bottleneck: you have the primitives; the work is in the orchestration.

## 5. Hardware & Performance (the deployment enablers)

- **GPU acceleration of lattice KEMs:** LWE-based KEMs are attractive (strong security) but costly (matrix ops + large-scale CS-RNG). A portable **OpenMP Target** GPU implementation (single source, NVIDIA + AMD) delivers substantial acceleration over multicore CPU while avoiding vendor lock-in; **NVIDIA GH200 and AMD MI300X** are the most effective platforms for this memory-bound workload — memory-system organization and CPU-GPU interaction matter more than peak FLOPs.
- **PIP-NTT** (arXiv:2607.18533): a scalable memory-parallelized accelerator for **iterative NTT** (the core transform in lattice crypto), targeting the computational requirements of real-world PQC.
- **Constrained / mobile (5G):** energy-aware evaluation of PQC in the TLS handshake on embedded UE (Raspberry Pi 5) shows a **strong coupling between latency and energy** (execution time dominates energy cost). **Hash-based signatures incur up to 4x higher latency and 2x energy** vs. lattice-based alternatives; KEM impact is comparatively small. **Lattice-based signatures offer the best security/efficiency/scalability balance for 5G.**
- **Python ecosystem:** the `quantum-safe` library closes the three critical gaps (hybrid KEM support, migration tooling, protocol integration). A full **X25519 + ML-KEM-768 handshake completes in ~243 us** (0.5-2.5% of a typical TLS 1.3 round-trip budget); at 5,000 concurrent users throughput holds at 2,848 ops/s with only 4.9% degradation (liboqs releases the GIL during C-level ops). It introduces **Coefficient of Variation (CoV) as a timing side-channel proxy**: ML-KEM-768 decapsulation CoV = 3.9% (within the AES-256-GCM 2.1% noise floor); ML-DSA-65 signing CoV = 51.5% (expected from FIPS 204 rejection sampling, not a side-channel).
- **Library ecosystem gap:** across nine PQC libraries scored on eight production-readiness dimensions, three dimensions have coverage **below 35%**: hybrid KEM support (11%), migration tooling (22%), protocol integration (33%).

## 6. Domain-Specific Migration Challenges

- **Blockchain / decentralized systems (arXiv:2605.06853, Finlow-Bates, Jakobsson, Siadati):** PQC migration is not purely cryptographic — in globally replicated networks, signature-size increases (Dilithium, SPHINCS+) are **multiplied across all nodes** (storage, bandwidth, validation). They propose a **hash-based commit-reveal construction** (two lightweight 32-byte-hash transactions) achieving PQC security under standard hash assumptions with only **~1.5-2x** effective transaction footprint per authorization — rethinking transaction semantics rather than adopting larger signatures. Lesson: decentralized PQC must account for **system-wide cost amplification** (cf. the 2015-2017 Bitcoin block-size debates).
- **Critical infrastructure / OT-SCADA (v17 page):** the hardest migration targets are long-lived OT systems (20+ year lifespans) where HNDL is most acute; IEC 61850 GOOSE / DNP3 telemetry intercepted today is the canonical at-risk data class.
- **Constrained IoT / hardware acceleration (v2 pages):** memory-bound lattice ops favor specific accelerator topologies; Ascon (2025) enables embedded symmetric crypto.

## 7. Open Research Gaps & Failure Modes

1. **Orchestration, not primitives:** hybrid combiners, versioned key formats, protocol helpers, and migration tooling remain the open production gap (11-33% library coverage).
2. **Policy-reality divergence:** national timelines do not map to observed deployment; managed providers dominate — a measurement/observability gap.
3. **Side-channel surface:** lattice rejection sampling (ML-DSA) and hash-based schemes introduce timing variance; CoV is a lightweight proxy but not a substitute for formal constant-time verification.
4. **Cost amplification in replicated systems:** blockchain/consensus PQC needs semantic rethinking, not just bigger signatures.
5. **Energy/latency coupling on constrained devices:** hash-based signatures are 4x/2x worse than lattice — a real constraint for 5G/IoT.
6. **CRQC timeline uncertainty:** the HNDL urgency is real but the CRQC arrival date is unknown — migration is a bet on a long tail.

## Cross-Domain Connections

- **Privacy & Cryptography** (STABLE) — PQC as the operational complement to the theoretical ZK/HE work.
- **AI Supply Chain Security & SBOM** — crypto-inventory (knowing where every key/signature lives) is a supply-chain concern; migration tooling is the SBOM of cryptography.
- **Electric Utility & Critical Infrastructure** — long-lived OT systems (20+ yr) are the hardest PQC targets; HNDL on IEC 61850/DNP3 is the canonical threat.
- **AI Model Supply Chain Security** — signing/verification of models under PQC (FIPS 204/205) as models become long-lived artifacts.
- **Entity Resolution / Data Aggregation** — the migration gap is isomorphic to the ER fusion bottleneck: primitives exist, orchestration is the work.
- **Complex Adaptive Systems** — config convergence on a single hybrid construction is an emergent coordination outcome despite divergent national policies.

## Sources

- arXiv:2607.29005 — "Mind the Gap: Policy vs Reality in Post-Quantum TLS Deployment" (Wickramasinghe, Li, Jha, Shaghaghi, 2026-07-31) — first longitudinal PQ-TLS measurement study (2B+ handshakes, 1M domains, 11 vantage points).
- arXiv:2607.18533 — "PIP-NTT: Scalable Memory-Parallelized Accelerator for Iterative NTT in PQC" (Imran et al.).
- arXiv:2605.10175 — KEM-IES with Ascon (NIST Aug 2025), Raspberry Pi 4 evaluation.
- arXiv:2605.06853 — "The Cost of Quantum Resistance: A Hash-Based Commit-Reveal Alternative" (Finlow-Bates, Jakobsson, Siadati, 2026-05-07).
- GPU LWE KEM (OpenMP Target, NVIDIA GH200 / AMD MI300X) — portable quantum-resistant infra.
- 5G PQC energy-aware TLS evaluation (Raspberry Pi 5 embedded UE) — hash 4x latency / 2x energy vs lattice.
- `quantum-safe` Python library — hybrid KEM, CoV timing side-channel proxy, X25519+ML-KEM-768 = 243 us.
- Shared corpus: post-quantum-critical-infrastructure (v17), post-quantum-lattice-cryptography-2026 (v2), pqc-deployment-readiness (v16/v2), quantum-safe-edge-computing-critical-infrastructure (v2).
- Book library: *Serious Cryptography*, Ch.14 "Quantum and Post-Quantum" (lattice/multivariate hardness, NIST 2017 process).
- NIST FIPS 203/204/205 (Aug 2024), FIPS 206 (FALCON, forthcoming), Ascon (Aug 2025); CISA PQC Initiative; White House EO (June 2026); EU coordinated roadmap; IETF PQC migration draft.
