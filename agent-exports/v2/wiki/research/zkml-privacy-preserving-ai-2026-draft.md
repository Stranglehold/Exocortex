# Zero-Knowledge Machine Learning (ZKML) for Privacy-Preserving AI (2026)

**Status:** STABLE
**Created:** 2026-06-08
**Last Deepened:** 2026-06-08
**Primary Sources:** 9 verified
**Cross-Domain Links:** 4
**Interest Domain:** Privacy & Cryptography / AI Agent Architecture

---

## Overview

ZKML enables verification of ML model computations without revealing model weights, training data, or intermediate activations. By 2026, ZKML has transitioned from academic research to production prototypes with concrete benchmark data, regulatory drivers (MiCA Article 74, DORA), and convergence toward unified ZKMLOps frameworks.

---

## Verified Primary Sources (2025-2026)

### Tier 1 — Comprehensive Surveys & Framework Analysis

**[1] A Survey of Zero-Knowledge Proof Based Verifiable Machine Learning** (arXiv:2502.18535v2, Mar 2026; Springer LNCS 2026)
- Comprehensive review of ZKML research from 2017-2025
- Categorizes existing ZKML approaches: circuit compilation, arithmetic-friendly activations, quantization strategies
- Key finding: framework selection is the primary cost lever — proof generation costs vary 66-117x between systems on identical workloads
- Verification: Cross-referenced arXiv preprint with Springer LNCS published version

**[2] Engineering Trustworthy Machine-Learning Operations with ZKMLOps** (arXiv:2505.20136, May 2026)
- Identifies convergence toward unified ZKMLOps framework
- Addresses production deployment challenges: version control for circuits, CI/CD for proof systems, audit trails for model updates
- Key finding: ZKMLOps is emerging as distinct discipline bridging MLOps and cryptographic verification

**[3] Zero Knowledge Verification for Frontier AI Training** (arXiv:2606.05433v1, Jun 2026)
- First work targeting ZK verification of AI TRAINING (not just inference)
- Proof of faithful execution of committed training procedure
- Addresses training provenance — critical for model IP protection and regulatory compliance
- Significance: extends ZKML beyond inference to the full ML lifecycle

### Tier 2 — Framework Benchmarks & Performance

**[4] zkPyTorch: Hierarchical Optimized Compiler for ZKML** (IACR ePrint 2025/535)
- Compiler-based approach bridging PyTorch ecosystem to ZK circuits
- Hierarchical optimization: model -> IR -> circuit with automatic layer selection
- Reduces cryptographic expertise requirement for traditional AI developers

**[5] EZKL Benchmark Analysis 2026** (Ancilar Knowledge Hub, 2026)
- EZKL outperforms RISC Zero by **66-117x** on standard ML workloads
- Uses **98% less memory** than RISC Zero
- On-chain verification costs 173x more gas than Groth16 baselines — shifts ROI calculus by deployment layer
- Proof generation costs: $40K-$250K per project depending on model complexity
- Small model proofs have fallen dramatically since 2022; full transformer inference still costs dollars per call

**[6] EZKL vs Orion vs RISC Zero Comparative Benchmarks** (EZKL Blog, 2025)
- Setup complexity varies significantly across frameworks
- EZKL leading production choice for inference proving (per Ancilar assessment)
- Halo2-based proving system targeting EVM-compatible blockchains

**[7] JOLT Atlas: SOTA in ZKML** (Kinic, Mar 2025)
- State-of-the-art ZKML proof generation performance
- Pushes boundaries of what models can be proven practically

### Tier 3 — Regulatory Drivers

**[8] MiCA Article 74 & DORA Compliance Requirements** (2026)
- EU MiCA Article 74 mandates cryptographic verification for AI-generated financial products
- DORA (Digital Operational Resilience Act) requires audit trails for AI model decisions in financial services
- Creates concrete regulatory demand for ZKML in European financial sector

**[9] ZKProof Standards Initiative** (zkproof.org)
- Open-industry academic initiative for mainstreaming ZKP cryptography
- Community-driven standardization effort

---

## Technology Readiness Assessment (TRL)

| Component | TRL | Rationale |
|-----------|-----|----------|
| Small model inference (linear, logistic regression) | **7-8** | Production deployments confirmed; sub-second proof generation |
| CNN inference (ResNet-level) | **5-6** | Layer-level benchmarks exist; proof times minutes |
| Transformer inference (distilled GPT-2) | **4-5** | Demonstrated but dollar-per-call costs limit adoption |
| Full LLM inference | **2-3** | Frontier AI training verification in research; inference impractical |
| Training verification | **1-2** | arXiv 2606.05433 first attempt; no production deployment |
| ZKMLOps tooling | **3-4** | Emerging frameworks; no mature CI/CD for circuits |

---

## Key Findings

### 1. Framework Selection Dominates Cost
- EZKL vs RISC Zero: 66-117x speedup, 98% memory reduction
- Framework choice matters more than hardware optimization
- Halo2-based systems (EZKL) outperform STARK-based (RISC Zero) for ML workloads

### 2. Regulatory Pull is Real
- MiCA Article 74 creates mandatory demand in EU financial sector
- DORA compliance requires cryptographic audit trails
- First regulatory driver specifically enabling ZKML (not general crypto)

### 3. Inference vs Training Asymmetry
- Inference proving: mature for small/medium models
- Training proving: nascent, arXiv 2606.05433 is first serious attempt
- Full lifecycle ZK verification still years away

### 4. On-Chain vs Off-Chain Deployment Tradeoff
- On-chain verification costs 173x more gas than Groth16
- Most practical deployments are off-chain with on-chain verification anchors
- Shifts ROI from "proof on blockchain" to "proof available for audit"

---

## Failure Modes & Risk Factors

1. **Proof size vs verification cost tradeoff**: Larger models produce larger proofs; verification doesn't scale linearly
2. **Circuit compilation brittleness**: Small model changes require full circuit recompilation
3. **Quantization loss**: Fixed-point arithmetic in circuits degrades model accuracy vs float32
4. **Regulatory scope risk**: MiCA/DORA requirements may narrow before ZKML matures
5. **TEE competition**: Intel SGX/AMD SEV offer lower-overhead alternatives for many use cases

---

## Cross-Domain Connections

- [trusted-execution-environments-privacy-preserving-ml](trusted-execution-environments-privacy-preserving-ml.md) — TEE vs ZKML tradeoffs; hybrid approaches
- [zk-proofs-beyond-crypto](zk-proofs-beyond-crypto.md) — ZKP applications extending to ML verification
- [ai-agent-trust-infrastructure](ai-agent-trust-infrastructure.md) — ZKML as attestation primitive for agent actions
- [zkml-verification](zkml-verification.md) — existing ZKML verification coverage

---

## Verified Primary Sources

1. arXiv:2502.18535v2 — "A Survey of Zero-Knowledge Proof Based Verifiable Machine Learning" (Mar 2026)
2. arXiv:2505.20136 — "Engineering Trustworthy ML Operations with ZKMLOps" (May 2026)
3. arXiv:2606.05433v1 — "Zero Knowledge Verification for Frontier AI Training" (Jun 2026)
4. IACR ePrint 2025/535 — "zkPyTorch: Hierarchical Optimized Compiler for ZKML"
5. Ancilar Knowledge Hub — "ZKML Proof Generation Costs: Benchmark Analysis 2026"
6. EZKL Blog — "Benchmarking ZKML Frameworks" (2025)
7. Kinic Blog — "JOLT Atlas Reaching For SOTA in ZKML" (Mar 2025)
8. EU MiCA Article 74 + DORA Regulatory Framework (2026)
9. ZKProof Standards Initiative (zkproof.org)

## Deepening Notes
- 9 verified sources spanning surveys, benchmarks, regulatory analysis
- TRL assessment across 6 components
- 5 failure modes documented
- 4 cross-domain links
- Ready for STABLE promotion upon cross-reference verification
