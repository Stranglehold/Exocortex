# Homomorphic Encryption: Practical State of the Art (2026)

**Status: STABLE**
**Created: 2026-06-05**
**Last Updated: 2026-07-04**
**Interest Area: Privacy & Cryptography**
**Verification Status: Last verified 2026-07-04 against primary sources.**

## Overview

Homomorphic encryption (HE) enables computation on encrypted data without decryption. Since Gentry's breakthrough in 2009, HE has progressed from cryptographic curiosity to production-deployable technology. As of 2026, the field is defined by four mature scheme families, specialized hardware acceleration, and the first large-scale production deployments in Web3 and financial services. However, HE remains **six orders of magnitude slower** than plaintext computation — a gap that defines the practical frontier.

This page surveys the 2026 state of the art: scheme maturity, performance benchmarks, hardware acceleration, production deployments, and cross-domain applications to privacy-preserving entity resolution, financial compliance, critical infrastructure, and AI agent verification.

---

## Scheme Taxonomy

Four scheme families dominate the production landscape, each with distinct tradeoffs between exactness, computational model, and bootstrapping overhead.

### BFV (Brakerski/Fan-Vercauteren)

**Model:** Exact integer arithmetic with scale-invariant noise management.
**Noise philosophy:** Noise is an obstacle to be removed at decryption. Plaintext lives in a discrete integer ring Z_t[x] / (x^N + 1). As long as noise growth stays below the decryption capacity, results are mathematically exact modulo t.
**Best for:** Biometric matching, database equality checks, vote counting, financial ledgers, exact identity verification.
**Key characteristic:** Noise is invisible to the application — correctness is all-or-nothing (either exact result or decryption failure).

### BGV (Brakerski-Gentry-Vaikuntanathan)

**Model:** Exact integer arithmetic with modulus switching for noise control.
**Noise philosophy:** Same exact-result model as BFV but uses modulus switching (chaining ciphertexts through progressively smaller moduli) rather than scale-invariant noise growth.
**Best for:** Deep arithmetic circuits where BFV's noise budget is insufficient; multi-party computation with exactness requirement.
**Key characteristic:** Modulus-switching overhead vs. circuit depth tradeoff; often the computationally heaviest of the exact schemes.

### CKKS (Cheon-Kim-Kim-Song)

**Model:** Approximate arithmetic on real and complex numbers.
**Noise philosophy:** Noise is treated as controlled approximation error — analogous to floating-point rounding. Each homomorphic operation introduces a small amount of additional imprecision. The result is an approximate real number, not exact.
**Best for:** Machine learning inference, statistical aggregation, signal processing, floating-point workloads where small errors are tolerable.
**Key characteristic:** Dominant scheme for ML inference; supports SIMD-batched operations; bootstrapping is particularly expensive and compounds approximation error.
**Production example:** H33 uses CKKS for throughput-optimized authentication pipelines.

### TFHE / FHEW (Torus FHE)

**Model:** Gate-by-gate Boolean evaluation with fast bootstrapping.
**Noise philosophy:** Operates on individual bits with programmable bootstrapping — each gate evaluation can include a table lookup, enabling arbitrary Boolean circuits and comparison operations in a single bootstrapped gate.
**Best for:** Circuits that require non-polynomial operations (comparisons, max, min, thresholding, ReLU), branching logic, arbitrary Boolean circuits.
**Key characteristic:** Fastest bootstrapping (sub-10ms per gate vs. CKKS bootstrapping at ~1.5s); poor SIMD scaling; best for logic-heavy, data-light computations.

### Scheme Selection Decision Table

| If you need... | Use... | Reasoning |
|----------------|--------|-----------|
| Exact integer results | BFV or BGV | Noise is stripped at decryption |
| Floating-point / ML inference | CKKS | Tolerates approximation, SIMD-friendly |
| Arbitrary Boolean / comparisons | TFHE | Fast gate bootstrapping with table lookups |
| Deep circuits with exactness | BGV | Modulus switching extends depth |
| SIMD-batched authentication | BFV | Scale-invariant noise, exact match needed |

---

## Performance Benchmarks

HE remains **six orders of magnitude slower** than plaintext execution. A plaintext multiplication (~4.3 ns on a commodity CPU) takes ~0.156 ms in FHE — roughly 36,000× for that single operation. Chained computations compound the gap.

### CryptOracle Benchmarking (CKKS, 2026)

Brynds et al. (arXiv:2510.03565v4, March 2026) provides the first open-source end-to-end CKKS characterization framework on commodity CPUs:

| Operation | Intel i9-13900K | AMD Ryzen 9 7950X | Plaintext Latency | HE Slowdown |
|-----------|-----------------|-------------------|-------------------|-------------|
| Encryption | ~0.5 ms | ~0.4 ms | n/a | n/a |
| Decryption | ~0.3 ms | ~0.25 ms | n/a | n/a |
| Addition (SIMD) | ~5-10 µs | ~4-8 µs | 0.4 ns | ~12,500× |
| Multiplication (SIMD) | ~150-200 µs | ~120-170 µs | 4.3 ns | ~35,000× |
| Bootstrapping | ~1.5 s | ~1.2 s | n/a | n/a |
| Relinearization | ~100-200 µs | ~80-150 µs | n/a | n/a |

### Cross-Scheme Performance Comparison

| Metric | BFV | BGV | CKKS | TFHE |
|--------|-----|-----|------|------|
| SIMD throughput | High | High | High | Low (bitwise) |
| Multiplication latency | ~150 µs | ~180 µs | ~160 µs | n/a (gate) |
| Bootstrapping time | ~2-5 s | ~2-5 s | ~1.2-1.5 s | ~5-10 ms |
| Noise per multiplication | ~1 bit | ~1 bit | ~1 bit (precision) | ~1 gate |
| Max circuit depth (no bootstrap) | ~8-12 mults | ~15-30 mults | ~8-15 mults | 1 gate (then bootstrap) |

**Key insight:** Bootstrapping cost dominates architecture. BFV/BGV/CKKS are optimized for deep SIMD circuits before a single expensive bootstrap reset. TFHE is optimized for shallow circuits with many cheap bootstraps — fundamentally different computational models.

### H33 Production Benchmarks (BFV)

H33's authentication pipeline processes **2.17 million authentications per second** (reported 2026) using BFV-optimized SIMD batching and hardware acceleration. This represents one of the fastest production FHE pipelines publicly benchmarked.

### Hardware Acceleration

| Platform | Typical Speedup | Maturity |
|----------|----------------|----------|
| AVX-512 (HEXL, Intel) | 2-5× | Production |
| GPU (CUDA backends) | 10-50× (theoretical) | Research |
| FPGA (Niobium, Xilinx) | 100-500× (projected) | Early-stage |
| ASIC (custom FHE chips) | 1000× (projected) | Pre-production |

**Niobium** ($23M raised, 2025) is developing dedicated FHE hardware targeting 1000× speedup over CPU for CKKS and BFV workloads. Production ASICs remain 2-3 years from general availability as of mid-2026.

---

## Production Deployments

### Zama: Confidential Blockchain Protocol

**Company:** Zama ($57M Series B, June 2025; unicorn valuation ~$1B as of early 2026).
**Product:** fhEVM — a full-stack framework enabling confidential smart contracts on EVM-compatible blockchains via FHE.
**Architecture:**
- **Symbolic execution model:** Smart contracts execute using lightweight "handles" (pointers to encrypted data) on-chain, while actual FHE computations are offloaded asynchronously to specialized coprocessors.
- **fhEVM executor:** Smart contract deployed on the host chain (Ethereum, Arbitrum, Polygon) that coordinates FHE operations with the coprocessor network.
- **End-to-end encryption:** Transactions and state remain encrypted throughout execution.

**Mainnet Status:** Q1 2026 — deployed on Arbitrum and Sepolia testnet. Mainnet Season 2 (mid-2026) focused on confidential DeFi with audited OpenZeppelin libraries.
**Partnerships:** OpenZeppelin (audited libraries for confidential smart contracts), Shibarium (Layer-2 integration planned Q2 2026).

### H33: Authentication at Scale

**Product:** FHE-based authentication pipeline processing **2.17 million authentications per second** using BFV scheme.
**Schemes supported:** BFV (H33-128), CKKS, TFHE (H33-TFHE), and BGV (H33-256 for post-quantum security).
**Applications:** Identity verification, biometric matching, encrypted search, post-quantum cryptography transitions.

### IBM: Fully Homomorphic Encryption Toolkit

**Product:** IBM FHE Toolkit (open-source) — enables FHE experimentation with BFV and CKKS backends.
**Status:** Research-to-production bridging. IBM has demonstrated privacy-preserving machine learning on encrypted medical data (healthcare AI) but large-scale commercial deployment remains limited.

### Microsoft SEAL

**Product:** Microsoft SEAL — open-source HE library implementing BFV and CKKS.
**Status:** Widely used in research and prototyping; foundation for many academic benchmarks. Not directly a production deployment but the most influential HE library ecosystem.

### OpenFHE

**Product:** Open-source FHE library supporting BFV, BGV, CKKS, TFHE, FHEW.
**Status:** Community-maintained; supports the Homomorphic Encryption Standard. Preferred for cross-scheme research and benchmarking.

### Confidential Finance / DeFi

**Emerging pattern:** Multiple projects (Zama, Fhenix/CoFHE) are building FHE-powered confidential DeFi, targeting:
- Dark pools / confidential trading
- Encrypted lending pools
- Privacy-preserving stablecoins
- Confidential governance voting

---

## Cross-Domain Applications

### Privacy-Preserving Entity Resolution

Entity resolution (matching records across datasets to determine they refer to the same real-world entity) involves comparing personally identifiable information (names, addresses, phone numbers, identifiers). FHE enables:

- **Encrypted blocking:** Compute blocking keys on encrypted data, allowing record linkage without revealing PII.
- **Encrypted similarity scoring:** Compute Jaccard similarity, edit distance, or embedding similarity on encrypted records.
- **Multi-party entity resolution:** Multiple organizations compute matches across their databases without revealing their individual records to each other.

**Structural insight:** Entity resolution under FHE is a **dual-constraint problem** — the Fellegi-Sunter probabilistic matching framework must be expressed as arithmetic circuits compatible with BFV/CKKS. This forces a decomposition: blocking (cheap, approximate) done in plaintext; matching (expensive, exact) done in FHE. The same structural tradeoff appears in TFHE vs. CKKS/BFV — shallow exact logic with frequent bootstraps vs. deep approximate circuits.

### Financial Compliance

- **Anti-money laundering (AML):** Banks can screen transactions against sanction lists without revealing customer transaction details to compliance vendors.
- **Know Your Customer (KYC):** Financial institutions can verify customer identity against shared databases without revealing the queried identity.
- **Encrypted market surveillance:** Exchanges can detect manipulation patterns across encrypted order books.

### Critical Infrastructure

- **Smart grid privacy:** Utilities can compute aggregate demand and detect anomalies on encrypted smart meter readings, enabling load balancing without exposing individual household consumption.
- **SCADA/ICS security:** Industrial control systems can run anomaly detection models on encrypted telemetry, preventing both external attackers and insider threats from observing operational data.
- **Post-quantum security:** Lattice-based HE (BFV, BGV, CKKS) is inherently post-quantum secure, making FHE a natural foundation for post-quantum critical infrastructure protection.

### AI Inference on Encrypted Data

- **Confidential ML-as-a-Service:** Model providers can run inference on client data without seeing the input; clients get results without seeing the model.
- **Healthcare AI:** Hospitals can run diagnostic models on encrypted patient data (imaging, lab results) without exposing PHI.
- **Limitation:** CKKS only supports polynomial approximations of activation functions. ReLU requires either TFHE (gate-by-gate) or polynomial approximation in CKKS, which introduces accuracy loss. FHE-friendly ML architectures (polynomial activations) remain an active research area.

---

## Cross-Domain Connections

**FHE as a Computational Integrity Primitive for AI Agents.** The Exocortex architecture builds epistemic integrity through scaffolding — injection gates, supervisor loops, entropy-as-signal, confabulation detection. FHE provides a complementary cryptographic integrity guarantee: computation that is *provably* performed on specific encrypted inputs with a specific circuit. If an agent's reasoning could be expressed as an FHE circuit, the output comes with cryptographic proof of what computation was executed. This doesn't solve confabulation (the model can still generate false claims within the circuit), but it solves the *attribution* problem — you can verify exactly what data was used and what computation was performed.

**The Bootstrapping-Reliability Parallel.** FHE bootstrapping resets the noise budget at the cost of ~1.5 seconds (CKKS). The Exocortex injection gate resets context reliability at the cost of a supervisor model call. Both are expensive insurance operations that enable unbounded-depth computation. The design pattern — *checkpoint and recover* — recurs across domains that manage accumulating error. Noise in FHE is structurally isomorphic to context drift in LLM agent conversations.

**zkML + FHE Combination.** Zero-knowledge proofs for ML inference (zkML, see [[zkml-verifiable-ai-inference]]) provide *verifiability* — proof that a model was executed correctly — while FHE provides *confidentiality* — the computation happens on encrypted data. The combination (Verifiable FHE, or vFHE) would enable an agent to prove: (1) it ran inference on specific encrypted data, (2) the model was executed correctly, (3) the result is accurate. This is the strongest theoretical guarantee for agent verification and a direct path to bridging local-to-frontier model performance (see [[bridging-local-frontier-model-performance]]).

**Hardware Acceleration as a Meta-Lesson.** Both FHE and LLM inference face the same architectural shift: general-purpose CPUs are the wrong substrate. FPGA and ASIC investment for transformative workloads isn't optional optimization — it's a prerequisite for viability. The Exocortex's own hardware exploration (RTX 3090 optimization, tensor core utilization) overlaps with the FHE hardware trajectory. The structural lesson: when a compute-bound technology is 6 orders of magnitude from its target, software optimization buys time; hardware specialization buys viability.

**Entity Resolution Under Encryption as a Pattern.** The decomposed entity resolution architecture (plaintext blocking + FHE matching) mirrors the Exocortex memory architecture: fast candidate retrieval (vector search, memory_load) followed by expensive verification (LLM evaluation). Both domains converge on a **two-phase retrieval-matching paradigm** where you trade off recall (cheap, approximate phase) against precision (expensive, exact phase).

**FHE in Critical Infrastructure.** The post-quantum cryptography transition for ICS/SCADA (see [[post-quantum-cryptography-critical-infrastructure]]) intersects with FHE: lattice-based FHE schemes are quantum-resistant, and FHE-protected telemetry solves both the current-class security problem *and* the post-quantum threat simultaneously. Utilities investing in FHE for smart grid privacy (see [[distribution-automation-self-healing-grids]]) are investing in post-quantum readiness by default.

**Intelligence Analysis Parallel.** FHE's structural properties — computation under partial observability, noise-as-error management, bootstrapping as reliability reset — mirror intelligence analysis challenges. An analyst working with redacted documents, uncertain sources, and accumulated cognitive bias is doing the same thing an FHE circuit does: producing useful output from degraded inputs, with periodic "bootstrapping" (source re-verification, assumption checking) to reset the error budget. The structured analytic techniques in [[counterintelligence-analysis-frameworks]] (ACI, Key Assumptions Check) are the human-cognitive equivalent of FHE noise management.

---

## 2026 Breakthroughs & Active Research

This section captures developments from January-July 2026 that materially shift the state of the art.

### Hardware: TPU FHE Acceleration via Evolutionary Search (Google, May 2026)

Google's AlphaEvolve system (arXiv:2605.14718) applies evolutionary search with LLM-driven code generation to optimize FHE cryptographic kernels for TPUv5e. Within 24 hours of automated exploration, AlphaEvolve discovered optimizations achieving **2.5x TFHE bootstrap latency reduction** and 1.31x CKKS rotation / 1.18x CKKS multiplication speedup over human-engineered state of the art. The system co-optimizes across systolic array MXU, VPU, and vector register file data movement — a three-dimensional search space previously navigated by manual trial-and-error. **Significance:** This demonstrates autonomous compiler-level optimization for FHE hardware, closing the gap between cryptographic algorithm design and accelerator utilization without requiring human performance engineers.

### Embeddings: Independent Vector Evaluation — 78x Speedup (June 2026)

The IVE method (arXiv:2606.22186) replaces the traditional one-hot vector construction for encrypted embedding lookup with a linearly independent representation built from successive powers of a single encrypted value. Prior ICML 2024 one-hot methods required O(p log p) homomorphic operations to construct an encrypted selection vector of dimension p; IVE reduces this to O(p) and precomputes an orthogonal Discrete Cosine Transform change-of-basis on the server side. On encrypted FastText inference (Enron-Spam), IVE reduces embedding lookup latency by **78.4x** and cuts vector generation from 99.6% to 66.3% of total encrypted inference time. **Significance:** Private embedding lookup is the dominant cost bottleneck in encrypted NLP inference. IVE makes privacy-preserving classification over large vocabularies practical for the first time.

### ML: ReLU Approximation for FHE-Compatible LLMs (May 2026)

Gnetila & Lin (arXiv:2605.22281) propose a kernel-based ReLU approximation using a second-degree polynomial inspired by Jackson's theorem, trained directly on token embeddings from pre-trained LLMs. Unlike polynomial approximations that degrade with depth, the kernel approach maintains activation fidelity across transformer layers at low multiplicative depth. **Significance:** Non-linear activations are the fundamental incompatibility between FHE (addition + multiplication only) and transformer architectures. A practical ReLU approximation with bounded error opens the path to encrypted inference on full LLM pipelines without requiring FHE-native model architecture redesign.

### Control: End-to-End Encrypted Multi-Agent Control (June 2026)

Cheng et al. (arXiv:2606.19577) demonstrate a fully encrypted multi-agent formation control pipeline where sensing, Kalman state estimation, state propagation, and consensus control all operate on CKKS-encrypted data. The key innovation is a separation-principle error analysis showing CKKS bootstrapping acts as an impulsive disturbance with bounded steady-state error proportional to the closed-loop spectral radius. Provides a **design equation for the privacy-accuracy tradeoff** — engineers can tune bootstrapping parameters against control performance requirements. **Significance:** This is the first end-to-end demonstration that encrypted control isn't just theoretically possible but analyzable with classical control theory. Critical for privacy-preserving autonomous systems in defense and infrastructure.

### GNNs: Template-Based Encrypted Graph Inference — 67x Speedup (June 2026)

TGHE (arXiv:2606.26664) exploits a structural regularity in financial transaction graphs: local computation trees converge into a small set of template shapes. By canonicalizing ego-graphs at the edge and packing structurally identical trees into shared CKKS ciphertexts for SIMD-parallel encrypted inference, TGHE achieves **66.9x speedup** on DGraphFin (3.7M nodes, 4.3M edges) with <0.002 AUC loss. **Significance:** Prior FHE-based GNN systems were capped at ~20k nodes due to graph-size-coupled cost. TGHE's ego-centric template packing decouples per-query cost from global graph size, making encrypted fraud detection on real-world financial graphs feasible.

### Testing: HERTA — First Automated FHE Framework Tester (May 2026)

HERTA (arXiv:2605.14451) introduces metamorphic testing tailored to FHE semantics with novel metamorphic relations derived from FHE mathematical properties. Testing 3 leading industry framework implementations uncovered **21 previously unknown bugs**, several confirmed and fixed by developers. Bugs include silent computation corruption rather than crashes — errors that could cause financial losses in FHE-based services without detection. **Significance:** The immature testing ecosystem is a material adoption barrier for FHE. HERTA provides the first systematic correctness testing tool for the multi-layered FHE software stack.

---

## 2026 Breakthroughs & Active Research

This section captures developments from January-July 2026 that materially shift the state of the art.

### Hardware: TPU FHE Acceleration via Evolutionary Search (Google, May 2026)

Google's AlphaEvolve system (arXiv:2605.14718) applies evolutionary search with LLM-driven code generation to optimize FHE cryptographic kernels for TPUv5e. Within 24 hours of automated exploration, AlphaEvolve discovered optimizations achieving **2.5× TFHE bootstrap latency reduction** and 1.31× CKKS rotation / 1.18× CKKS multiplication speedup over human-engineered state of the art. The system co-optimizes across systolic array MXU, VPU, and vector register file data movement — a three-dimensional search space previously navigated by manual trial-and-error. **Significance:** This demonstrates autonomous compiler-level optimization for FHE hardware, closing the gap between cryptographic algorithm design and accelerator utilization without requiring human performance engineers.

### Embeddings: Independent Vector Evaluation — 78× Speedup (June 2026)

The IVE method (arXiv:2606.22186) replaces the traditional one-hot vector construction for encrypted embedding lookup with a linearly independent representation built from successive powers of a single encrypted value. Prior ICML 2024 one-hot methods required O(p log p) homomorphic operations to construct an encrypted selection vector of dimension p; IVE reduces this to O(p) and precomputes an orthogonal Discrete Cosine Transform change-of-basis on the server side. On encrypted FastText inference (Enron-Spam), IVE reduces embedding lookup latency by **78.4×** and cuts vector generation from 99.6% to 66.3% of total encrypted inference time. **Significance:** Private embedding lookup is the dominant cost bottleneck in encrypted NLP inference. IVE makes privacy-preserving classification over large vocabularies practical for the first time.

### ML: ReLU Approximation for FHE-Compatible LLMs (May 2026)

Gnetila & Lin (arXiv:2605.22281) propose a kernel-based ReLU approximation using a second-degree polynomial inspired by Jackson's theorem, trained directly on token embeddings from pre-trained LLMs. Unlike polynomial approximations that degrade with depth, the kernel approach maintains activation fidelity across transformer layers at low multiplicative depth. **Significance:** Non-linear activations are the fundamental incompatibility between FHE (addition + multiplication only) and transformer architectures. A practical ReLU approximation with bounded error opens the path to encrypted inference on full LLM pipelines without requiring FHE-native model architecture redesign.

### Control: End-to-End Encrypted Multi-Agent Control (June 2026)

Cheng et al. (arXiv:2606.19577) demonstrate a fully encrypted multi-agent formation control pipeline where sensing, Kalman state estimation, state propagation, and consensus control all operate on CKKS-encrypted data. The key innovation is a separation-principle error analysis showing CKKS bootstrapping acts as an impulsive disturbance with bounded steady-state error proportional to the closed-loop spectral radius. Provides a **design equation for the privacy-accuracy tradeoff** — engineers can tune bootstrapping parameters against control performance requirements. **Significance:** This is the first end-to-end demonstration that encrypted control isn't just theoretically possible but analyzable with classical control theory. Critical for privacy-preserving autonomous systems in defense and infrastructure.

### GNNs: Template-Based Encrypted Graph Inference — 67× Speedup (June 2026)

TGHE (arXiv:2606.26664) exploits a structural regularity in financial transaction graphs: local computation trees converge into a small set of template shapes. By canonicalizing ego-graphs at the edge and packing structurally identical trees into shared CKKS ciphertexts for SIMD-parallel encrypted inference, TGHE achieves **66.9× speedup** on DGraphFin (3.7M nodes, 4.3M edges) with <0.002 AUC loss. **Significance:** Prior FHE-based GNN systems were capped at ~20k nodes due to graph-size-coupled cost. TGHE's ego-centric template packing decouples per-query cost from global graph size, making encrypted fraud detection on real-world financial graphs feasible.

### Testing: HERTA — First Automated FHE Framework Tester (May 2026)

HERTA (arXiv:2605.14451) introduces metamorphic testing tailored to FHE semantics with novel metamorphic relations derived from FHE mathematical properties. Testing 3 leading industry frameworks uncovered **21 previously unknown bugs**, several confirmed and fixed. Bugs include silent computation corruption — not crashes — with potential to cause financial losses in FHE-based services. **Significance:** The immature testing ecosystem is a material adoption barrier. HERTA provides the first systematic correctness testing tool for the multi-layered FHE software stack.

## References

1. Brynds et al., "CryptOracle: A Modular Framework to Characterize FHE," arXiv:2510.03565v4, March 2026.
2. Zama, "The State of FHE Report," ongoing. https://www.zama.org/
3. Zama $57M Series B announcement, June 2025. https://www.zama.org/post/zama-developer-program-mainnet-season-2
4. BlockEden, "Zama Protocol: The FHE Unicorn Building Blockchain's Confidentiality Layer," January 2026. https://blockeden.xyz/blog/2026/01/05/zama-protocol/
5. Cryptollia, "FHE's Final Frontier," 2026.
6. Niobium FHE hardware accelerator project, 2025.
7. OpenFHE library: https://github.com/openfheorg/openfhe-development
8. Homomorphic Encryption Standard: https://homomorphicencryption.org/standard/
9. CryptOracle code: https://github.com/UnaryLab/CryptOracle
10. Microsoft SEAL: https://github.com/microsoft/SEAL
11. IBM FHE Toolkit: https://github.com/ibm/fhe-toolkit-linux
12. H33 FHE platform benchmarks: https://h33.ai/blog/bfv-vs-ckks-fhe-schemes/
13. Messari, "Understanding Zama: A Comprehensive Overview," 2026. https://messari.io/report/understanding-zama-a-comprehensive-overview
14. OpenZeppelin x Zama partnership: https://www.openzeppelin.com/networks/zama
15. Zama fhEVM GitHub: https://github.com/zama-ai/fhevm
16. A Comparative Performance Analysis of FHE and ABE Schemes, Nature Scientific Reports, October 2025. https://www.nature.com/articles/s41598-025-19404-w
17. IEEE, "Survey and Review on BFV Homomorphic Encryption," February 2026.
18. PETS 2026, "SoK: Can FHE Support General AI?" https://petsymposium.org/popets/2026/popets-2026-0066.pdf
19. Springer, "Homomorphic Encryption for Secure Healthcare AI," February 2026.
20. FHE Toolkits for Encrypted Smart Contracts on Ethereum L2s, 2026. https://fhetoolkit.com/2026/02/15/fhe-toolkits-for-encrypted-smart-contracts-on-ethereum-l2s-zama-fhevm-and-fhenix-guide-2026/

21. Google DeepMind, "AlphaEvolve: Automated FHE Kernel Optimization for TPUv5e," arXiv:2605.14718, May 2026.
22. Independent Vector Evaluation (IVE) for Private Embedding Lookup, arXiv:2606.22186, June 2026.
23. Gnetila & Lin, "Kernel-Based ReLU Approximation for FHE-Compatible LLMs," arXiv:2605.22281, May 2026.
24. Cheng et al., "End-to-End Encrypted Multi-Agent Control via CKKS," arXiv:2606.19577, June 2026.
25. TGHE: Template-Based Graph Homomorphic Encryption for GNN Inference, arXiv:2606.26664, June 2026.
26. HERTA: Automated Metamorphic Testing for FHE Frameworks, arXiv:2605.14451, May 2026.
27. Process Mining with Homomorphic Encryption via Token-Based Replay, arXiv:2604.25190, April 2026.
