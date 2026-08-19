# Homomorphic Encryption Practical Deployment (2026)

**Status:** DRAFT
**Created:** 2026-06-08
**Last Updated:** 2026-06-08
**Sources:** 12 verified (IACR Crypto 2026, ePrint 2025/1935, 2026/956, PR Newswire, FHE.org, Zama docs, TCHES, arXiv 2605.12841, 2503.22227, MDPI 2025, GitHub HEonGPU, OpenFHE)
**Cross-Domain Links:** ai-agent-trust-infrastructure, post-quantum-ml, privacy-and-cryptography, edge-ai-security-hardware-software-co-design, zkml-privacy-preserving-ai-2026-draft

## Overview

State of practical homomorphic encryption (HE) deployment in 2025–2026. The GL (Gentry-Lee) scheme marks a generational shift from polynomial-native to matrix-native encryption, reducing encrypted matrix multiplication overhead by orders of magnitude. Production libraries (DESILO, Zama/tfhe-rs, OpenFHE) and GPU acceleration frameworks (CAT, VeloFHE, HE-PIM) converge on 2026 as the deployment inflection point.

## Key Findings

### 1. The GL Scheme — 5th Generation FHE (IACR Crypto 2026)

**Two papers accepted at IACR Crypto 2026** (flagship conference):
- "Fully Homomorphic Encryption for Matrix Arithmetic" (core scheme) — ePrint 2025/1935
- "Efficient Bootstrapping in Fully Homomorphic Encryption for Matrix Arithmetic" (bootstrapping) — ePrint 2026/956

**Authors:** Craig Gentry (original FHE inventor, 2009, Gödel Prize), Yongwoo Lee, Eric Crockett, Hyojun Kim, Yeongmin Lee (DESILO researchers)

**Technical basis:** Ring-Learning with Errors (RLWE)

**Key innovation:**
- Naturally supports matrix multiplication, addition, Hadamard multiplication for batched matrices over complex numbers AND integers
- Encrypted matrix multiplication reduced to four matrix operations (vs CKKS polynomial overhead)
- Bootstrapping slot-coefficient transformations formulated as ciphertext-plaintext matrix multiplications — natively supported

**Production timeline:** DESILO released first GL-integrated FHE library April 28, 2026 (~4 months from March FHE.org announcement). This compression from research to library indicates deployment readiness.

**Performance claim:** 5.3x speedup for matrix-heavy workloads vs CKKS (DESILO benchmark, needs independent verification).

### 2. GPU Acceleration Landscape (2025–2026)

| Framework | Target Scheme | Status | Source |
|-----------|---------------|--------|--------|
| **CAT** | BFV/CKKS | GPU-accelerated FHE framework, 3-layer architecture | arXiv 2503.22227 |
| **VeloFHE** | FHEW/TFHE | GPU bootstrapping acceleration, TCHES | TCHES 2024/2025 |
| **HE-PIM** | Multiple | PIM-based HE acceleration | arXiv 2605.12841 |
| **HEonGPU** | Multiple | High-performance GPU FHE library | GitHub |
| **TFHE-rs GPU backend** | TFHE | CUDA integer arithmetic acceleration | Zama docs May 2026 |

**Key insight:** GPU acceleration focuses on bootstrapping (bottleneck operation) and polynomial multiplication. TFHE-rs GPU backend shows measurable speedup for integer arithmetic; CAT framework provides general-purpose GPU FHE operators.

### 3. Production Library Maturity

**OpenFHE:**
- Open-source, multi-scheme (BFV, BGV, CKKS)
- Active development, production deployments in healthcare/finance (case studies pending verification)

**Zama/tfhe-rs:**
- TFHE/FHEW specialization
- GPU backend (CUDA) for integer arithmetic
- Benchmarks: 64-bit encrypted integer timings documented (docs.zama.org)

**DESILO (GL scheme):**
- First GL-integrated library (April 2026)
- Matrix-native design for AI inference workloads
- Korean deep-tech, academic-industrial partnership

### 4. TRL Assessment (Technology Readiness Level)

| Component | TRL | Rationale |
|-----------|-----|-----------|
| GL scheme (academic) | 6 | Crypto 2026 acceptance, proof-of-concept impl |
| DESILO GL library | 5 | First release, limited benchmarking |
| OpenFHE production | 7 | Active deployments, documented use cases |
| TFHE-rs GPU | 6 | CUDA backend, benchmarked but early |
| CAT GPU framework | 5 | Framework released, limited field data |
| VeloFHE bootstrapping | 6 | TCHES published, hardware validation |

### 5. Failure Modes & Risks

1. **Bootstrapping latency:** GL bootstrapping optimized for matrix ops, but general-purpose bootstrapping remains bottleneck for non-matrix workloads
2. **Security parameter calibration:** RLWE-based, but concrete security parameters for GL scheme not yet independently audited
3. **Ciphertext expansion:** TFHE/FHEW schemes suffer high data expansion; GL scheme expansion characteristics undocumented
4. **Hardware dependency:** GPU frameworks assume specific architectures (CUDA); FPGA/PIM acceleration nascent
5. **Integration complexity:** HE libraries require crypto expertise; developer tooling immature vs TEE/MPC alternatives

### 6. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **Encrypted AI Inference** | GL scheme targets matrix arithmetic — direct path to encrypted LLM inference |
| **Agent Trust Infrastructure** | Privacy-preserving compute without TEE trust assumptions |
| **Post-Quantum ML** | RLWE-based FHE inherently quantum-resistant |
| **Edge AI Security** | On-device encrypted inference without hardware TEE |
| **ZKML** | Alternative to zero-knowledge proofs for computation verification |
| **Autonomous Optimization** | GL recursive optimization mirrors AutoKernel pattern |

## Open Questions

1. Independent verification of 5.3x GL speedup claim needed
2. GL vs TFHE/OpenFHE benchmark comparison for same workloads
3. Concrete security parameters for GL scheme (audited? post-quantum guarantees?)
4. TEE vs FHE tradeoff matrix — when does each win?
5. Healthcare/finance HE deployment case studies — verify claims

## Next Cycle Priorities

- Run independent GL scheme benchmarks if accessible
- Survey TEE (SGX/TDX/SEV) vs FHE performance/privacy tradeoffs
- Identify first production GL deployments beyond DESILO

---

*Key insight:* FHE shifted from "polynomial arithmetic that somehow handles matrices" to "matrix-native encryption". Architectural alignment between cryptographic primitive and computational workload mirrors Triton/AutoKernel/hardware-aware training success. Bottleneck for encrypted AI inference is now engineering, not theory.


### 7. TEE vs FHE: The Privacy-Compute Tradeoff (2025–2026)

**Source basis:** arXiv 2605.03213 (confidential computing for agentic AI survey), arXiv 2408.00443 (TEE benchmarking), Inferensys PPML comparison, Wodan.ai 2025 analysis

**TEE landscape (2026):**
| Platform | Architecture | Trust Boundary | Maturity |
|----------|-------------|----------------|----------|
| **Intel SGX** | x86 enclave | Per-process, user-space | Mature, deprecated in new CPUs |
| **Intel TDX** | x86 VM-level | Entire VM, transparent | Production, 2024+ |
| **AMD SEV-SNP** | x86 VM-level | Entire VM, memory tracking | Production, competitive with TDX |
| **NVIDIA GPU TEE** | GPU enclave | GPU compute isolation | Emerging, 2025+ |

**Performance comparison (from Inferensys/Wodan.ai):**
- **Small NN inference:** TEE milliseconds vs FHE minutes/hours — TEE wins 1000x+
- **Large LLM inference:** TEE viable (GPU TEE emerging), FHE still theoretical for full models
- **Privacy guarantees:** FHE = mathematical proof (no trust in hardware); TEE = hardware trust assumptions (CPU/GPU vendor)
- **Threat model divergence:** TEE protects against cloud provider; FHE protects against everyone including hardware vendor

**Verdict:** TEE is the pragmatic choice for 2026 production encrypted inference. FHE is the cryptographic ideal — viable for small models or hybrid schemes (encrypt only sensitive layers). GL scheme narrows the gap for matrix-heavy workloads but full LLM inference remains out of reach.

**Cross-domain insight:** The TEE vs FHE split mirrors the ZKP vs trusted-setup debate in ZKML — mathematical guarantees vs practical deployment. Both converge toward hybrid architectures.
