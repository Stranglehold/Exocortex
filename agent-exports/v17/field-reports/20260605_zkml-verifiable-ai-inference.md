# FIELD REPORT: zkML — Verifiable AI Inference (2026 State of the Art)

**Date:** 2026-06-05
**Cycle:** EXPLORE
**Interest:** Privacy & Cryptography → Zero-knowledge proof applications beyond crypto
**Thread:** zkML (Zero-Knowledge Machine Learning) — cryptographic verification of AI inference

---

## 1. What I Explored

zkML — the application of zero-knowledge proof systems to machine learning inference. Instead of trusting that a model was run correctly, zkML produces a cryptographic proof that a specific model ran on specific inputs and produced a specific output, verifiable without re-running the computation. I surveyed the framework landscape, cost economics, technical barriers, and production use cases as of mid-2026.

## 2. What I Found

### Framework Landscape (2026)

| Framework | Approach | Key Benchmark | Best For |
|-----------|----------|---------------|----------|
| **EZKL** (2023-) | ONNX → Halo2 circuits | 65x faster than RISC Zero, 98% less memory | Production DeFi, small-to-medium NNs |
| **RISC Zero** | zkVM (Rust) | 250k-350k gas on-chain via Groth16 SNARK wrapper | General-purpose zkVM workloads |
| **Lagrange DeepProve** (2024-) | Sumcheck + logup GKR | 54-158x faster than EZKL for transformers; first complete GPT-2 proof | Large transformer inference |
| **zkPyTorch** (Polyhedra, Mar 2025) | DAGs + parallel execution | Llama-3 proof: 150s/token; VGG-16: 2.2s | Modern transformer architectures |
| **ZKTorch** (Daniel Kang, Jul 2025) | Universal compiler + proof accumulation | GPT-J 6B: 20 min on 64 threads; ResNet-50 proof: 85KB | General-purpose academic zkML |
| **Jolt Atlas** (NovaNet/ICME, Aug 2025) | Lookup-native zkVM | 4-7x faster than prior, all before GPU | Agent use cases needing privacy + verification |

### Cost Economics

- **Small models (linear regression):** fractions of a cent on CPU via EZKL
- **Full transformer inference:** still dollars per call
- **EZKL on-chain verification:** 173x higher gas than Groth16 baselines (Halo2 KZG commitments require more pairing operations)
- **Optimistic zkML with challenge windows:** reduces cost ~90% for lower-stakes use cases
- **GPU acceleration:** 5-10x speedup, folding schemes reducing proof sizes to kilobytes expected by 2027

### The Overhead Compression Story

ZK proof overhead has compressed dramatically:
- 2022: ~1,000,000x overhead (academic proof-of-concept)
- 2024: ~100,000x (first production frameworks)
- 2025: ~10,000x (zkPyTorch, Lagrange DeepProve, Jolt Atlas)
- 2026 trajectory: heading toward ~1,000x with GPU acceleration and folding schemes

### Three Persistent Blockers (2026)

1. **Quantization accuracy loss:** Floating-point → finite-field arithmetic conversion loses precision. Every framework handles this differently (larger bit widths, lookup tables, fixed-point tricks).
2. **Operator coverage:** ONNX has 120+ operators; most zkML frameworks support ~50. Gaps include custom layers, exotic normalizations, dynamic control flow, and flash attention.
3. **Proof size and gas cost:** Models above ~18M parameters still require tens of GB of RAM to prove. Ethereum mainnet verification remains expensive for complex models.

### Production Use Cases

- **DeFi oracles:** Upshot + Modulus zkPredictor — cryptographic proof that NFT valuations came from the claimed model
- **Trading bots:** Giza on Starknet — verifiable agents for DeFi; each rebalance decision provably from the promised strategy
- **Credit scoring:** Proof that the same model ran for every applicant (regulatory compliance, fairness audits, dispute resolution)
- **Agent-to-agent trustless composition:** Agents pass cryptographic batons — "trustless agent relay race for agentic commerce"

## 3. What I Think Is Interesting

### The Real Story: zkML as Trust Infrastructure for Multi-Agent Systems

The DeFi use cases are the obvious immediate application, but the deeper pattern is that zkML solves a problem that becomes existential as AI agents proliferate: **how does one agent verify that another agent's inference was legitimate?**

Standard x402/ERC-8004 protocols handle agent-to-agent *payments*, but payment rails without verification rails are just a faster way to get defrauded. zkML provides the verification layer — a cryptographic receipt that says "I ran model X on inputs Y and got output Z" without revealing X or Y.

This is structurally isomorphic to a problem the Exocortex architecture will face: as autonomous agents compose and delegate, each step in the chain needs to be verifiable. One compromised or hallucinating agent poisons the entire workflow. zkML is the mathematical answer to that trust problem.

### The Cost Viability Threshold

The Ancilar analysis crystallized the decision framework: **zkML makes sense when trust failure costs more than the proof.** Three scenarios where this holds:
1. High-stakes automated decisions (on-chain credit scoring)
2. Regulatory compliance (MiCA/DORA audit trails for model output provenance)
3. DeFi automation (where verifiable AI prevents manipulation losses exceeding proof cost)

The overhead is still real, but the compression trajectory (1,000,000x → 10,000x → heading toward 1,000x) mirrors the kind of exponential improvement we saw in early LLM inference optimization. This is not a permanent barrier.

### The EZKL/RISC Zero Tradeoff Reveals a Deployment-Layer Tension

EZKL is 65x faster at proof generation but 173x more expensive at on-chain verification. RISC Zero wraps STARK output in Groth16 SNARK for cheaper on-chain verification but slower proof generation. This means framework selection is not a single-axis decision — it depends on whether your bottleneck is prover time or verifier gas cost. The optimal choice shifts by deployment layer (L1 vs L2, on-chain vs off-chain verification).

## 4. What I'd Explore Next

1. **zkML for local model verification:** Can a local model (e.g., Qwen3.6-27b on RTX 3090) generate a zk proof of its inference for a remote verifier? This connects directly to the bridging-local-to-frontier research agenda. Current benchmarks suggest LLM-scale proofs are still minutes-to-hours, but the trajectory is improving rapidly.
2. **Jolt Atlas architecture deep-dive:** The lookup-native zkVM approach (no quotient polynomials, no byte decomposition, just lookups and sumcheck) seems like the most promising path for general-purpose agent verification. Worth understanding the folding scheme integration (HyperNova/BlindFold).
3. **Optimistic zkML economic model:** The 90% cost reduction from challenge-window verification suggests a hybrid trust model — optimistic by default, cryptographic on challenge. This pattern generalizes beyond zkML (compare: optimistic rollups, fraud proofs in blockchain). Worth modeling the game theory.
4. **Operator coverage gap analysis:** Map which ONNX operators are covered by which frameworks. This is the practical adoption bottleneck — your production model uses operators your zkML framework doesn't support.

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **AI Agent Architecture** | zkML solves the trustless-agent-composition problem: agents verify each other's inferences cryptographically. Directly relevant to Exocortex multi-agent delegation patterns. |
| **Bridging Local-to-Frontier** | Can local inference be made verifiable? If a local Qwen model can generate a zk proof of its output, it can participate in trustless agent networks without uploading data or weights. |
| **DeFi / Programmable Money** | x402/ERC-8004 agent payment rails need verification rails. zkML is the missing half of the agent economy stack. |
| **Privacy-Preserving ML (from prior exploration)** | zkML and FHE address complementary problems: FHE for computation on encrypted data, zkML for verification of computation. They can compose: FHE for privacy during inference, zkML for proving the FHE circuit ran correctly. |
| **Critical Infrastructure** | Grid automation decisions (protection relay settings, DER dispatch) that are AI-driven could use zkML for audit trails — prove the model made the decision, not a compromised SCADA system. |
| **OSINT / Entity Resolution** | Privacy-preserving entity resolution: prove two records match without revealing the records themselves. zkML could enable trustless cross-jurisdictional entity resolution where data stays local but match proofs are shared. |

---

**Sources:**
- Ancilar: "zkML Proof Generation Costs: Benchmark Analysis 2026" (2026-05-04)
- Ancilar: "zkML: Verifiable On-Chain AI Inference Architecture 2026" (2026-05-28)
- ICME Labs: "The Definitive Guide to ZKML (2025)" (blog.icme.io)
- Peng et al.: "A Survey of Zero-Knowledge Proof Based Verifiable Machine Learning" (arXiv:2502.18535, revised 2026-03-29)
- GitHub: worldcoin/awesome-zkml
