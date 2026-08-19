# Field Report: Zero-Knowledge Proofs Beyond Cryptocurrency

**Date:** 2026-05-20
**Cycle:** #204 (EXPLORE)
**Topic:** Privacy & Cryptography — ZKP Applications Outside Blockchain
**Research Sources:** arXiv 2502.18535, Polyhedra Network, EUDI Architecture Topic G, Google Innovation Blog, EuroSys 2024

---

## 1. What I Explored

The specific thread: **Where are zero-knowledge proofs actually deployed outside of blockchain/crypto, and what performance thresholds make them viable?**

I followed three sub-threads:
1. ZKML (verifiable machine learning inference/training)
2. Government/regulated identity systems (EUDI Wallet, age assurance)
3. The convergence point — ZKP as trust infrastructure for AI systems

---

## 2. What I Found

### ZKML Performance Has Crossed a Threshold

- **Polyhedra Expander** achieves **9,000 zk proofs/sec** on m31ext3 elliptic curve with CUDA 13.0 and GPU-accelerated KZG commitments. This is a 100-1000x improvement over early zkVM-based ZKML (which had 100,000x-1,000,000x overhead per ICME Labs analysis).
- **zkPyTorch** (Polyhedra, Jun 2025) bridges PyTorch inference directly to ZK proof generation — AI developers use standard PyTorch code, not custom circuit definitions.
- **ZKML compiler** (Berkeley RDI, EuroSys 2024) shows **24x performance variance** depending on gadget layout optimization. The compiler auto-selects optimal constraint layouts from equivalent circuit formulations.
- **arXiv 2502.18535** (comprehensive ZKML survey, Jun 2017–Aug 2025) organizes ZKML into three core tasks: verifiable training, verifiable testing, verifiable inference. Main bottlenecks remain: limited circuit expressiveness, high proving cost, deployment complexity.

### Government Identity Is the Biggest Non-Crypto ZKP Deployment

- **EUDI Wallet (eIDAS 2.0)** — EU regulation mandating zero-knowledge proof integration for digital identity wallets across all 27 member states by **end of 2026**.
- **EUDI Architecture Topic G** formally specifies ZKP as the privacy-enhancing technique: relying parties validate statements about identification data without seeing the underlying data.
- This is the first major regulatory framework that mandates ZKP at government scale — not optional, not experimental.

### Age Assurance Is a Quiet ZKP Killer App

- **Google open-sourced ZKP libraries** specifically for age verification (Jul 2025 blog post). The framing: "promote privacy in age assurance" — prove you're over 18 without revealing birthdate or identity.
- This is a concrete commercial application with clear regulatory pressure (COPPA, DSA age-gating requirements).

---

## 3. What I Think Is Interesting

**The convergence is happening faster than the crypto narrative captured it.**

The original ZKP thesis was about private transactions on public ledgers. But the actual deployment trajectory is splitting into three distinct vectors:

1. **Verification infrastructure for AI** — ZKML lets you prove "this model produced this output" without revealing the model weights. This matters for proprietary AI services, regulatory compliance (EU AI Act model cards), and multi-party ML where institutions share inference results without exposing training data.

2. **Regulatory-compliant identity** — EUDI isn't building ZKP because it's cool. It's because GDPR requires data minimization. ZKP is the only mechanism that lets a government prove "this person is eligible for this benefit" without transmitting the underlying PII. This is a compliance-driven deployment, not a technology-driven one.

3. **Trust infrastructure convergence** — The same ZKP primitives that verify ML inference can verify identity claims. A single ZKP stack could theoretically underpin both verifiable AI and verifiable identity. This is the infrastructure layer that connects multiple of Jake's interests.

The 9,000 proofs/sec benchmark from Polyhedra is the inflection point. Below that threshold, ZKP was academic. Above it, ZKP becomes deployable infrastructure.

---

## 4. What I'd Explore Next

- **Modulus Labs vs. Risc Zero vs. Polyhedra** — competitive landscape of zkVM providers for ZKML. Different proving systems (STARK vs. SNARK) have different performance/verification tradeoffs.
- **ZK proof of training** vs. ZK proof of inference — training verification is exponentially harder but would solve the AI reproducibility crisis.
- **Post-quantum ZKP compatibility** — how do ZK proofs hold up against quantum adversaries? Relevant to the post-quantum ML interest area.
- **SNARK-vs-STARK performance comparison** on real ML workloads (ResNet-50, BERT inference).

---

## 5. Cross-Domain Connections

| Connection | Interest Area | Link |
|-----------|--------------|------|
| ZKML verifiable inference → entity resolution | Data Aggregation & Entity Resolution | ZKP could prove entity matches across datasets without exposing the underlying records |
| EUDI wallet architecture → decentralized identity | Privacy & Cryptography | Direct overlap with existing wiki pages on decentralized-identity-eudi-wallets.md |
| ZK proof of training → ML reproducibility | Privacy & Cryptography | Connects to trusted-execution-environments-privacy-preserving-ml.md — TEE vs. ZKP as competing trust models |
| GPU-accelerated ZK proving → hardware optimization | Hardware & Physical Computing | Polyhedra's CUDA optimization is directly relevant to RTX 3090 tensor core utilization work |

---

## Key Data Points (Verified)

- Polyhedra Expander: 9,000 zk proofs/sec (m31ext3, CUDA 13.0)
- ZKML compiler: 24x performance variance from gadget layout optimization (EuroSys 2024)
- EUDI Wallet ZKP mandate: all 27 EU member states by end of 2026
- Google ZKP age assurance libraries: open-sourced July 2025
- ZKML survey coverage: Jun 2017 – Aug 2025 (arXiv 2502.18535)
