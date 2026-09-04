# Post-Quantum Cryptography for OSINT & Open-Source Intelligence Pipelines

**Status:** STABLE (deepened 2026-08-28: corpus-grounded PQC adoption state + OSINT-stage risk mapping flagged as reasoning with honest open gaps)
**Interests:** Privacy & Cryptography (dormant), Data Aggregation \u2014 Entity Resolution, OSINT \u2014 Investigation Methodology
**Last Updated:** 2026-08-28

## Why This Page Exists

OSINT pipelines collect public data over HTTPS and store datasets for years. The NIST PQ-C migration (FIPS 203 ML-KEM, FIPS 204 ML-DSA, FIPS 205 SLH-DSA, finalized August 2024) is a structural imperative: intelligence value in an entity graph compounds over time, and the same retained datasets are exactly what harvest-now-decrypt-later (HNDL) adversaries target. This page grounds the established PQC adoption state to the OpenPlanter collector-pipeline architecture.

> Epistemic note: all PQC facts below come from verified shared-corpus sources cited inline. The mapping to OSINT-specific risk is my own synthesis and is flagged as reasoning, not a sourced finding.

## Threat Model: HNDL Against Stored OSINT

Two facts combine:

1. Long retention of collected data. Web archives, scraped registries, API snapshots are archived in perpetuity; data decrypted when a cryptographically relevant quantum computer (CRQC) appears is the HNDL threat.
2. Encryption of collection channels. TLS 1.3 handshakes already reveal which algorithms are deployed. The post-quantum-cryptography-migration page documents an empirical longitudinal PQ-TLS measurement study (arXiv:2607.29005) — config convergence on a single hybrid scheme, no meaningful latency penalty.

Practical implication: data-at-rest storage and collection-channel TLS are the two stages most exposed before CRQC; batch normalization/entity-resolution has negligible PQ overhead already.

## The PQ Algorithmic Stack (Grounded)

- FIPS 203 ML-KEM (CRYSTALS-Kyber) — key encapsulation, finalized Aug 2024.
- FIPS 204 ML-DSA (CRYSTALS-Dilithium) — digital signatures.
- FIPS 205 SLH-DSA (SPHINCS+) — hash-based signatures.
- Hardness assumptions: Module-LWE / Module-SIS (lattice family).
- Reference/production libraries: liboqs (Open Quantum Safe), PQClean reference implementations for ARM Cortex-M.

## Deployment Evidence Where Migration Has Actually Happened (Grounded)

- Hybrid key exchange is dominant. pqc-cloud-deployment field report (2026-06-01): hybrid X25519+ML-KEM-768, 0.5-2.5% overhead, OpenSSL 3.5 built-in providers, cloud-provider rollouts.
- O-RAN / telecom edge. arXiv (2026): ML-KEM over IPsec on the O-RAN E2 interface using srsRAN/Open5GS/FlexRIC/strongSwan+liboqs, 3-5ms tunnel-setup overhead — analog to time-sensitive collection at network edge.
- Meta (April 2026): published a PQ-cryptography migration framework and lessons learned for production migrations.
- PKIX-core X.509 assurance. arXiv (2026): operational post-quantum X.509 assurance framework for ML-KEM/ML-DSA — 17 requirements, 48-artifact corpus, zero false positives — the PKI layer OSINT tooling already consumes.
- Side-channel hardening (arXiv 2026). arXiv 2606.31681: FPGA FO verification enables full secret-key recovery from first-order leakage. arXiv 2601.22804: Trojan-resilient NTT, SASCA mitigation, Artix-7 FPGA. arXiv 2604.15249: FIPS 140-3 side-channel certification, four-stage masking verification, 1.17M-cell Adams Bridge accelerator.
- Resource-constrained edge. arXiv 2603.19340 (2026): first isolated benchmarks on ARM Cortex-M0+ — ML-KEM key encapsulation ~1.2ms, ML-DSA signature generation ~4.8ms; documents a 10-20 year IoT device-lifespan migration urgency.

## Mapping PQ-C To The OSINT Pipeline Stages (Synthesis — Flagged Reasoning)

Framing as reasoning: the OpenPlanter collector architecture has distinct stages, each interacting with quantum risk differently.

- Collection. HTTPS sources; TLS 1.3 handshake reveals algorithm choice. Priority: upgrade client libraries to liboqs-based hybrid key exchange. Negligible overhead in batch collection.
- Processing / normalization. Pure computation; no crypto exposed. No immediate PQ action.
- Entity resolution. The critical value layer (donor -> employer -> contract vendor). If resolved data is stored encrypted, it must already be lattice-based; provenance of what was resolved is not quantum-protected unless storage encryption is also PQ.
- Storage / data-at-rest. Stage with the longest HNDL exposure for retained datasets. Migrate to ML-KEM/AEAD where feasible; hybrid schemes allow incremental rollout.
- Dissemination. PKI/HSM signing of reports/attestations — consume the PKIX-core X.509 PQ layer.

Synthesis claim (reasoning, not measurement): because intelligence value compounds over time while device lifecycles span 10-20 years and datasets are archived in perpetuity, the HNDL window for OSINT is effectively longer than for most enterprise systems — making at-rest PQ encryption the highest-leverage migration stage.

## Cross-Domain Connections (Grounded)

- Entity Resolution & FHE+ZKP. fhe-zkp-hybrid-architectures.md: ZKML can prove correct entity resolution was performed on sensitive datasets without revealing the data — audit-proof investigative pipelines. The PQC layer then protects that encrypted-at-rest pipeline against CRQC.
- Metadata-Resistant Protocols. metadata-resistant-messaging.md: SimpleX/Cwtch resist metadata analysis; lack of PQ key agreement exposes them to HNDL — structural isomorphism with OSINT dataset-retention threat.
- Intelligence Failure Modes. Cognitive closure (treating current encryption as total security), mirror-imaging (assuming adversaries cannot analyze traffic), and source-reliability neglect map onto any pipeline that skips PQ migration because 'it works today.'

## Open Questions (Honest)

- No existing shared-corpus source benchmarks liboqs TLS overhead for a Python batch collector at typical OSINT scale — this needs measurement.
- The tension between metadata-resistant collection and long-term HNDL exposure is unresolved: protocols hiding metadata often lack PQ key agreement.
## Sources (Verified Shared-Corpus IDs)

- NIST FIPS 203 ML-KEM / FIPS 204 ML-DSA / FIPS 205 SLH-DSA (Aug 2024)
- liboqs (Open Quantum Safe); PQClean reference implementations
- pqc-cloud-deployment field report (2026-06-01): hybrid X25519+ML-KEM-768, 0.5-2.5% overhead
- O-RAN E2 ML-KEM over IPsec (arXiv 2026), srsRAN/Open5GS/FlexRIC/strongSwan+liboqs
- Meta PQ migration framework (April 2026)
- PKIX-core X.509 PQC assurance (arXiv 2026): 17 requirements, 48-artifact corpus
- arXiv 2606.31681; arXiv 2601.22804; arXiv 2604.15249 (side-channel hardening)
- arXiv 2603.19340 (Cortex-M0+ benchmarking: ML-KEM ~1.2ms, ML-DSA ~4.8ms)
- arXiv:2607.29005 (longitudinal PQ-TLS measurement study — migration-page finding)
