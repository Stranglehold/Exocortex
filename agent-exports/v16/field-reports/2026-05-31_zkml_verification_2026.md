# Field Report: Zero-Knowledge Machine Learning (ZKML) Verification
**Date**: 2026-05-31
**Cycle**: 929 (EXPLORE)
**Domain**: Privacy & Cryptography — ZKML sub-domain
**Trigger**: Least recently explored active interest (Privacy & Crypto last explored May 27)

---

## 1. What I Explored

The specific thread: **Zero-Knowledge Machine Learning (ZKML) — the state of verifiable ML inference in 2026**. Can we prove an ML model produced a correct inference without revealing the model weights or the input data? This bridges privacy-preserving computation with cryptographic verification, and it's becoming practically deployable.

Focused on: proof generation costs, benchmark data from 2026, on-chain vs. off-chain deployment, and the emerging standardization track at ITU-T.

---

## 2. What I Found

### Core Architecture
ZKML uses zero-knowledge proofs (ZKPs) to certify that a specific ML model was run on specific inputs, producing a specific output — without revealing the model weights or the input data. Three core verification objectives exist:

1. **Verifiable Inference** — proving a specific model produced a specific prediction (most mature, production-ready)
2. **Verifiable Training** — proving a model was trained on specified data with specified hyperparameters (research stage)
3. **Verifiable Testing** — proving model evaluation metrics are authentic (emerging)

### Benchmark Numbers (May 2026)

- **Proof generation for small models**: 62ms proving time, 83KB proofs, 17ms verification (ZKsync Airbender zkVM)
- **On-chain inference**: Modulus Labs benchmarks support models up to 18M parameters with practical proving times
- **Libraries compared**: SEAL, HElib, OpenFHE, and Lattigo across BGV, BFV, and CKKS schemes — significant performance divergence between libraries (ACM 2025/2026 cross-platform benchmark)
- **CMU autovectorization breakthrough** (May 2026): New tensor compiler specifically for HE operations that dramatically reduces proving overhead
- **Cloud-native HE workflow** (arXiv 2510.24498): Bridges the gap between cryptographic privacy and practical deployability for cloud deployments

### Production Deployments

- **Polyhedra Network**: Active ZKML infrastructure provider, scaling proving systems in 2026
- **Giza**: Focuses on trustless on-chain model inference verification
- **Chainlink CCIP Read + ZKML**: Privacy-preserving ML inference oracle integration (March 2026)
- **ITU-T Work Programme**: Official standardization track for ZKML launched Feb 2026 — signals industry readiness
- **Ancilar benchmark analysis** (May 21, 2026): Comprehensive cost analysis for on-chain AI model proof generation

### Key Systems Landscape

| System | Focus | Verification Target | Status |
|--------|-------|---------------------|--------|
| Modulus Labs | On-chain inference | Model correctness up to 18M params | Production |
| Polyhedra | ZKML infrastructure | General proving | Production |
| Giza | On-chain verification | Trustless model inference | Production |
| ezDPS | Inference pipeline | End-to-end pipeline | Research |
| CMU TensorHE | Compiler optimization | Proving efficiency | Research (May 2026) |

---

## 3. What I Think Is Interesting

### The Production Chasm Was Crossed in 2026

ZKML moved from academic curiosity to deployed infrastructure within the last 12 months. The ITU-T standardization track (Feb 2026) is a leading indicator — standardization bodies don't open tracks for vaporware. The combination of sub-second proving times for small-to-medium models and active commercial deployments (Polyhedra, Modulus, Giza) means ZKML is now a practical building block, not just a research topic.

### The Real Bottleneck Shifted

The bottleneck is no longer "can we prove it" — it's "what do we prove and who verifies it." The verification cost has dropped enough that the interesting question becomes: what trust assumptions are we actually removing? If you trust the proving system's reference implementation but not the model operator, you've moved the trust anchor, not eliminated it. The most interesting deployments will be compositional — ZKML proofs feeding into other ZK systems.

### Composability With Entity Resolution

ZKML proofs can verify that an entity resolution model ran correctly on sensitive corporate registry data without revealing the underlying records. This creates a privacy-preserving investigation pipeline: prove you ran the correct entity resolution algorithm on the claimed dataset, get the cryptographic proof, and use it to establish audit trails. The connection to Jake's Data Aggregation & Entity Resolution interest is direct — ZKML enables provably-correct entity resolution on sensitive government datasets.

### The Standardization Signal

ITU-T opening a ZKML work item in February 2026 is the strongest signal that this technology crossed from crypto-native to mainstream infrastructure. ITU-T standardization typically follows 3-5 years of technical maturation — meaning the core algorithms are considered stable enough for international governance frameworks.

---

## 4. What I'd Explore Next

- **Formal verification of ZKML proving systems**: Can we cryptographically verify that the proving system itself is correct? Meta-verification for ZKML.
- **ZKML for model training verification**: Much harder than inference, but proving training integrity would prevent model poisoning attacks.
- **Hardware acceleration for ZK proof generation**: FPGA/ASIC accelerators specifically for ZKML circuits — the CMU autovectorization paper hints at this direction.
- **Compositional ZK architectures**: ZKML proofs as inputs to other ZK protocols — building verifiable AI pipelines from composable proof primitives.

---

## 5. Cross-Domain Connections

- **Data Aggregation & Entity Resolution**: ZKML can prove correct entity resolution was performed on sensitive datasets without revealing the data — enables audit-proof investigative pipelines
- **AI Safety & Alignment**: Verifiable inference is a building block for provably-correct AI decision-making; connects to the scalable-oversight-ai wiki page
- **Hardware & Physical Computing**: FPGA acceleration for ZK proof generation is the natural next step — same hardware optimization patterns as custom CUDA kernels
- **Privacy & Cryptography (PQC)**: ZKML + post-quantum cryptography creates quantum-resistant verifiable ML pipelines — the PQC TLS memory finding extends naturally
- **Intelligence Operations**: Verifiable OSINT pipelines — prove that analysis was performed correctly without revealing sources or methods

---

## Sources

1. arXiv 2502.18535v2 — "A Survey of Zero-Knowledge Proof Based Verifiable Machine Learning" (Mar 2026)
2. Ancilar — "zkML Proof Generation Costs: Benchmark Analysis 2026" (May 21, 2026)
3. CMU CS PhD Blog — "An Autovectorizing Tensor Compiler for Homomorphic Encryption" (May 4, 2026)
4. ITU-T Work Programme — ZKML standardization track (Feb 2026)
5. Polyhedra Network — "Moving into 2026" blog (Jan 2026)
6. Clouded Judgement — "Zero Knowledge, Maximum Trust" analysis (Apr 3, 2026)
7. ACM — "Performance Analysis of Leading Homomorphic Encryption Libraries" (2025/2026)
8. arXiv 2510.24498 — Cloud-native HE workflow
9. Springer — "A survey of zero-knowledge proof based verifiable machine learning" (Apr 13, 2026)
10. Chainlink — Privacy-Preserving ML article (Mar 31, 2026)
