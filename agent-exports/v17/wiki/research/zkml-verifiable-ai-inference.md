# zkML — Verifiable AI Inference (2026 State of the Art)

**Status:** STABLE

**Created:** 2026-06-05

**Source:** Field report `/a0/usr/workdir/workspace/field-reports/20260605_zkml-verifiable-ai-inference.md`

---

## Overview

zkML (Zero-Knowledge Machine Learning) applies zero-knowledge proof systems to machine learning inference. Instead of trusting that a model was run correctly, zkML produces a cryptographic proof that a specific model ran on specific inputs and produced a specific output, verifiable without re-running the computation. This is central to trustless multi-agent AI systems, local-to-frontier verifiable inference, and privacy-preserving entity resolution.

## Framework Landscape (2026)

| Framework | Approach | Key Benchmark | Best For |
|-----------|----------|---------------|----------|
| **EZKL** (2023-) | ONNX → Halo2 circuits | 65x faster than RISC Zero, 98% less memory | Production DeFi, small-to-medium NNs |
| **RISC Zero** | zkVM (Rust) | 250k-350k gas on-chain via Groth16 SNARK wrapper | General-purpose zkVM workloads |
| **Lagrange DeepProve** (2024-) | Sumcheck + logup GKR | 54-158x faster than EZKL for transformers; first complete GPT-2 proof | Large transformer inference |
| **zkPyTorch** (Polyhedra, Mar 2025) | DAGs + parallel execution | Llama-3 proof: 150s/token; VGG-16: 2.2s | Modern transformer architectures |
| **ZKTorch** (Daniel Kang, Jul 2025) | Universal compiler + proof accumulation | GPT-J 6B: 20 min on 64 threads; ResNet-50 proof: 85KB | General-purpose academic zkML |
| **Jolt Atlas** (NovaNet/ICME, Aug 2025) | Lookup-native zkVM | 4-7x faster than prior, all before GPU | Agent use cases needing privacy + verification |

## Cost Economics

- **Small models (linear regression):** fractions of a cent on CPU via EZKL
- **Full transformer inference:** still dollars per call
- **On-chain verification:** EZKL is 65x faster at proof generation but 173x more expensive at verifier gas; RISC Zero wraps STARK in Groth16 SNARK for cheaper verification but slower proving
- **Optimistic zkML:** 90% cost reduction via challenge-window verification (optimistic by default, cryptographic on challenge)
- **Decision rule:** zkML makes economic sense when trust failure cost exceeds proof cost (Ancilar 2026)

## Persistent Blockers

- **Quantization loss:** accuracy degradation when converting floating-point models to finite fields
- **Operator coverage gaps:** critical ONNX operators still unsupported across frameworks
- **Proof size/cost for large models:** LLM-scale proofs still minutes-to-hours
- **Prover-verifier asymmetry:** different frameworks optimize different sides of the tradeoff

## Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **AI Agent Architecture** | zkML solves trustless-agent-composition: agents verify each other's inferences cryptographically. Directly relevant to Exocortex multi-agent delegation. |
| **Bridging Local-to-Frontier** | Can local inference be made verifiable? If Qwen can generate a zk proof of output, it can participate in trustless agent networks without uploading data or weights. |
| **DeFi / Programmable Money** | x402/ERC-8004 agent payment rails need verification rails. zkML is the missing half of the agent economy stack. |
| **FHE Integration** | zkML and FHE address complementary problems: FHE for computation on encrypted data, zkML for verification of computation. They compose: FHE for privacy during inference, zkML for proving the FHE circuit ran correctly. |
| **Critical Infrastructure** | Grid automation decisions (protection relay settings, DER dispatch) that are AI-driven could use zkML for audit trails — prove the model made the decision, not a compromised SCADA system. |
| **OSINT / Entity Resolution** | Privacy-preserving entity resolution: prove two records match without revealing the records themselves. zkML enables trustless cross-jurisdictional entity resolution where data stays local but match proofs are shared. |

## Future Threads

1. **zkML for local model verification:** Can Qwen3.6-27B on RTX 3090 generate a zk proof of its inference? Connects to bridging-local-to-frontier research.
2. **Jolt Atlas architecture deep-dive:** Lookup-native zkVM (no quotient polynomials, no byte decomposition, just lookups and sumcheck) — most promising path for general-purpose agent verification.
3. **Optimistic zkML economic model:** Hybrid trust model generalizes beyond zkML (optimistic rollups, fraud proofs). Worth modeling game theory.
4. **Operator coverage gap analysis:** Map ONNX operators covered by which frameworks — this is the practical adoption bottleneck.


## 2026 Developments & Ecosystem

### Jolt Atlas — Lookup-Native zkVM for ML Inference

**arXiv:2602.17452** (Benno, Centelles, Douchet, Gibran, Feb 2026). Extends the Jolt proving system to ONNX model inference, enabling on-device cryptographic verification without specialized hardware. Key innovations:
- **Lookup arguments** for non-linear activation functions — replaces complex circuit arithmetic with simple table lookups, dramatically reducing proof complexity
- **Neural teleportation** — optimizes lookup table size while preserving model accuracy
- **Streaming prover** — enables memory-constrained environments to generate proofs incrementally
- **4-7× speedup** over prior zkVMs, all before GPU acceleration (NovaNet/ICME)

### zkLLM — Proving LLM Inference Integrity

**arXiv:2412.09999** (2025). Generates cryptographic proofs that a specific LLM produced a specific output for a specific input. This guarantees:
- No model tampering or unauthorized switching
- No hallucination introduced post-hoc (output exactly matches model computation)
- Verifiable chain-of-reasoning for multi-agent systems

Direct implication for Exocortex epistemic integrity: every agent output could carry a verifiable proof of honest inference, making oracle fabrication cryptographically detectable.

### Hardware Acceleration — Falcon ASIC

**Falcon** (ASPLOS 2026): Algorithm-hardware co-design for ZK proof acceleration. Moves ZK proving from software bottleneck to hardware-specialized pipeline. This parallels the FHE acceleration trend (Cheddar GPU, Intel Heracles) — both privacy-preserving computation paradigms are driving new silicon.

### Trust Revolution: Local AI as Impenetrable Vault

2026 marks a shift: zkML breaks the "data-for-intelligence" bargain. Users can keep data local while proving computation correctness to remote verifiers. This unlocks:
- **Private DeFi**: prove creditworthiness without exposing financial history
- **Healthcare**: prove diagnosis accuracy without revealing patient data
- **Digital Identity**: prove attributes without revealing underlying documents (eIDAS 2.0 integration)

### On-Chain AI Integration

Projects bridging zkML to blockchain execution (2026):
- **Modulus Labs**: zkML-powered smart contracts for verifiable AI oracles
- **0G Labs**: decentralized AI inference with zkML verification layer
- **EZKL + RISC Zero**: production deployments for DeFi risk models and identity systems

The x402/ERC-8004 agent payment standard combined with zkML verification completes the agent economy stack: verifiable work + programmable payment rails.

## Related Pages

- [[zero-knowledge-proof-applications]] — broader ZKP applications beyond crypto (identity, telecom, supply chain)
- [[bridging-local-frontier-model-performance]] — local model (Qwen3.6-27B) verified inference without weight upload
- [[homomorphic-encryption-practical-state]] — FHE + zkML composition: privacy during computation + verification of computation
- [[counterintelligence-analysis-frameworks]] — zkLLM proofs make oracle fabrication cryptographically detectable
- [[agentic-tool-use-schema-optimization]] — tool call verification via zkML proofs
- [[scada-ics-security]] — critical infrastructure AI decision audit trails via zkML

## Sources

- Ancilar: "zkML Proof Generation Costs: Benchmark Analysis 2026" (2026-05-04)
- Ancilar: "zkML: Verifiable On-Chain AI Inference Architecture 2026" (2026-05-28)
- ICME Labs: "The Definitive Guide to ZKML (2025)" (blog.icme.io)
- Peng et al.: "A Survey of Zero-Knowledge Proof Based Verifiable Machine Learning" (arXiv:2502.18535, revised 2026-03-29)
- GitHub: worldcoin/awesome-zkml
---


---
**Verification Status:** Last verified 2026-06-05. Page deepened from DRAFT with content from 1 field report (20260605), cross-referenced against zero-knowledge-proof-applications.md (Jolt Atlas, zkLLM, Falcon), 2 web sources (Chain Researcher, Financial Content), and 5 arXiv/external references. 6 cross-domain connections mapped to Exocortex architecture.
