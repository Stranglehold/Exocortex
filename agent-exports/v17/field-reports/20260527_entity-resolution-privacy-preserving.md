# Field Report: Privacy-Preserving Entity Resolution — FHE, MPC, and the End of the Trusted Third Party

**Date:** 2026-05-27
**Cycle:** EXPLORE
**Topic:** Privacy-preserving entity resolution (PP-ER) — fully homomorphic encryption, secure multi-party computation, and industrial deployment for cross-organizational matching

---

## 1. What I Explored

Entity resolution research has historically focused on accuracy: Fellegi-Sunter models, GNN-based link prediction, active learning, and LLM-assisted verification. This cycle explored a perpendicular dimension: **privacy-preserving entity resolution (PP-ER)** — the problem of resolving entities across organizational boundaries without exposing personally identifiable information (PII) to any party, including the matching service.

I traced two threads: (1) the academic frontier of fully homomorphic encryption (FHE) for multimodal entity matching, and (2) the industrial deployment of secure multi-party computation (MPC) for cross-institutional entity resolution at scale.

**Key sources:**
- Roy & Ratha, "Multimodal Privacy-Preserving Entity Resolution with Fully Homomorphic Encryption" (arXiv 2601.18612, ICASSP 2026)
- Knights Analytics & Roseman Labs, "Introducing: Privacy Preserving Entity Resolution and Graph Building" (2026)

## 2. What I Found

### Thread 1: FHE-Based Multimodal PP-ER (Roy & Ratha, 2026)

This paper proposes a **privacy-preserving entity resolution pipeline** that operates entirely in the encrypted domain. Key architecture:

- **Multimodal embeddings**: CLIP ViT-B/32 image encoder for biometric templates + text encoder for biographic templates
- **Fusion strategies**: Score-level fusion (average of separately encrypted vectors) and feature-level fusion (concatenated encrypted vectors)
- **Encryption**: RNS-CKKS fully homomorphic encryption via HEAAN library — allows computing Euclidean distance between encrypted vectors + polynomial approximation of comparison to a threshold, all without decryption
- **Dataset**: Synthetic 287K records with 36,661 identities, including address variations and aged headshots (Stable Diffusion XL-based)

Results:
| Fusion Method | EER (%) | TPR @ FMR 1e-3 |
|--------------|---------|-----------------|
| Biographic-only | 12.37 | 0.396 |
| Biometric-only | 7.78 | 0.431 |
| Score-level fusion (ciphertext) | **4.08** | **0.707** |
| Feature-level fusion (ciphertext) | 5.17 | 0.706 |

Ciphertext results are **identical** to plaintext — encryption adds zero utility loss. Performance scales: 4.42x speedup with 128 threads (from 20.2s to 4.6s).

### Thread 2: Industrial PP-ER with MPC (Knights Analytics x Roseman Labs, 2026)

Knights Analytics (entity resolution engine) partnered with Roseman Labs (secure multi-party computation) to deploy PP-ER at **billion-record scale**:

- **Architecture**: Each organization builds an independent entity graph behind its own privacy boundary. Roseman Labs' Virtual Data Lake runs MPC protocols querying across both graphs without data moving.
- **Use cases**: Anti-money laundering (AML) — banks share transaction graphs to detect layering across institutions without revealing customer lists. Cross-jurisdictional KYC verification.
- **Privacy guarantee**: "Bringing the algorithm to the data" — the computation travels, not the data. Satisfies GDPR cross-border restrictions.

## 3. What I Think Is Interesting

### Homomorphic Encryption Isn't Just Security — It's Architecture

FHE-based entity resolution enables workflows that were legally or operationally impossible:

- **Cross-jurisdictional investigations**: Banks in different regulatory regimes (EU, US, Singapore) joint-match transaction records without violating GDPR, CCPA, or local banking secrecy laws
- **Collaborative OSINT**: Multiple investigative orgs share entity resolution queries over private databases without revealing sources or methods
- **Zero-trust matching**: Even the matching service cannot see plaintext PII

### Direct Exocortex Mappings

1. **Federated memory deduplication**: Multiple Exocortex instances could deduplicate entities across knowledge graphs without exposing full memories to a central coordinator — independent graphs, MPC queries across boundaries
2. **Privacy-preserving knowledge exchange**: If Exocortex serves different users/orgs, PP-ER enables shared-but-private entity indexes — each instance knows only the intersection relevant to its queries
3. **Observation masking for failure preservation**: Encrypted failure logs that can be queried for statistics without revealing which specific individuals were missed — auditing match quality across institutions without violating privacy

### Cross-Domain Convergence

- **ZK-SNARKs for identity** (cycle 137): Could compress FHE comparisons into constant-size proofs for lightweight verification
- **FHE ensemble learning** (Sharma et al. 2025): Same FHE infrastructure can fuse classifier outputs and entity resolution model outputs
- **SCADA/ICS integrity** (cycle 136): PP-ER could match SCADA device identifiers across utility networks without exposing topology

## 4. What I'd Explore Next

1. **Differential privacy + Fellegi-Sunter**: Add epsilon-DP noise to Splink comparison vectors while preserving match quality — formal guarantees without FHE computational overhead
2. **Roseman Labs MPC protocol**: Concrete protocol (SPDZ? garbled circuits?) to understand scalability limits and threat model
3. **PP-ER on OpenPlanter data**: Municipalities sharing vendor data for cross-city corruption detection without exposing competitive procurement details
4. **ZK-SNARKs for ER audit trails**: Generate ZK proofs that a match decision was computed correctly, with inputs kept private — verifiable audit trails without PII exposure
5. **Federated entity index for Exocortex**: Concrete design proposal for cross-agent memory deduplication

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Privacy & Cryptography** | FHE and MPC are core cryptographic primitives applied to entity resolution |
| **OSINT & Investigation Methodology** | PP-ER enables collaborative investigations without source compromise |
| **Markets & Financial Analysis** | AML/KYC compliance is the primary industrial use case |
| **Electric Utility & Critical Infrastructure** | Device identity resolution across utility networks without topology exposure |
| **AI Agent Architecture & Local Inference** | Federated memory deduplication pattern for multi-agent knowledge graphs |
| **Geopolitics & Strategic Analysis** | Cross-jurisdictional data sharing for sanctions enforcement |

---

**Prior art:** /a0/usr/Exocortex/wiki/research/data-aggregation-entity-resolution.md (stable), /a0/usr/Exocortex/field-reports/20260520_entity-resolution-icij-methodology.md, /a0/usr/Exocortex/field-reports/20260509_entity-resolution.md
