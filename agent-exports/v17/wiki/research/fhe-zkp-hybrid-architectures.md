# FHE-ZKP Hybrid Computation Architectures

**Status: STABLE**
**Created: 2026-07-14**
**Deepened: 2026-07-14**
**Domain: Privacy & Cryptography**
**Interests:** Homomorphic encryption practical state of the art, Zero-knowledge proof applications beyond crypto, Hardware acceleration for privacy-preserving computation

## Overview

Fully Homomorphic Encryption (FHE) and Zero-Knowledge Proofs (ZKPs) solve complementary problems in privacy-preserving computation. FHE enables computation on encrypted data, preserving data confidentiality. ZKPs prove computation integrity without revealing inputs. Together, they form a complete privacy-preserving computation stack: encrypted computation (FHE) coupled with verifiable correctness (ZKP). This page synthesizes convergence patterns, deployment architectures, hardware acceleration landscapes, security considerations, and 2026 research frontiers.

## The Complementarity Theorem

| Property | FHE | ZKP | FHE+ZKP Hybrid |
|----------|-----|-----|----------------|
| Data confidentiality | ✓ Encrypts inputs and computation | ✗ Prover knows inputs | ✓ FHE encrypts; ZKP never sees plaintext |
| Computation integrity | ✗ No guarantee of correct execution | ✓ Cryptographic proof of correctness | ✓ ZKP verifies FHE execution |
| Privacy model | Hide data from server | Hide data from verifier | Hide data from everyone — server and verifier |
| Trust model | Trust server to execute correctly | Trust prover to execute honestly | Trust neither — verify cryptographically |
| Performance (2026) | ~10,000× slowdown vs plaintext (FHE); ~100× with GPU/TPU acceleration | 1,000-10,000× proving overhead (zkSNARK); ~100× with UniZK systolic array | Additive — bottleneck at FHE layer; TEE-hybrid reduces bootstrapping overhead 40-60% |
| Maturity | Production for specific workloads (Zama, OpenFHE, DESILO) | Production for blockchain L2s, identity | Emerging — clinical trial verification, verifiable AI inference |

### Why Not Just Use One?

- **FHE alone**: The server can return garbage results, and the client cannot detect it. No integrity guarantee.
- **ZKP alone**: The prover must know the data to generate a proof. No confidentiality.
- **TEE alone**: Side-channel vulnerabilities (Intel SGX repeatedly broken); requires hardware trust.
- **FHE+ZKP**: Confidentiality + integrity without hardware trust. The cryptographic "trust but verify" stack.

## Deployment Architecture Patterns

### Pattern 1: Sequential — FHE Compute → ZKP Verify

The most deployed pattern. Server performs FHE computation on encrypted data, generates a ZKP proving correct execution, and returns both the encrypted result and the proof. Client verifies the ZKP before decrypting.

**Real-world example**: Cross-institutional clinical trial verification (EU Horizon 2026 healthcare consortia).

**Performance**: HE operations ~100-1,000× slower than plaintext; adding ZKP proof layer compounds overhead. Viable only for high-value use cases where trustlessness justifies cost.

**Implementation stack**: Concrete-ML (TFHE) + zkSNARK proof of correct inference execution.

### Pattern 2: Interleaved — ZKP during FHE Bootstrapping

Bootstrapping (FHE noise reduction) is the most expensive operation in leveled FHE schemes, consuming ~80% of computation. ZKPs prove each bootstrapping step was performed correctly, enabling untrusted bootstrapping nodes in distributed FHE systems.

**Key insight**: If bootstrapping can be outsourced to untrusted nodes with ZKP verification, FHE throughput scales horizontally without trust assumptions on the bootstrapping infrastructure.

**Research status**: Theoretical — no production deployment. Requires efficient ZKP circuits for CKKS/TFHE bootstrapping operations, which are complex polynomial computations.

### Pattern 3: Compositional — ZKP-of-FHE for Regulatory Compliance

A ZKP proves that a specific FHE computation was performed according to a published algorithm, enabling regulatory compliance without revealing the underlying data. This is the cryptographic equivalent of an audited financial statement — prove the accounting rules were followed, not the transaction details.

**Applications**:
- **GDPR compliance**: Prove personal data was processed according to stated purposes without revealing the data.
- **AML/KYC**: Prove sanction screening was performed on encrypted transaction data; ZKP verifies the screening algorithm was correctly applied.
- **Financial audit**: Prove netting calculations comply with Basel III without exposing individual counterparty positions.

**Implementation**: Concrete-ML + ZKP verification of the model architecture + inference path. The ZKP proves the model architecture matches the audited specification.

### Pattern 4: TEE-Hybrid — HE + TEEs for Bootstrapping Offload

While not a pure FHE+ZKP combination, the HE+TEE hybrid pattern is the most practical deployment today and serves as a stepping stone toward fully cryptographic trustlessness.

| Component | Role |
|-----------|------|
| Intel SGX / AMD SEV | Key management, bootstrapping offload |
| FHE (CKKS, TFHE) | Encrypted computation on untrusted cloud |
| ZKP (optional) | Verify TEE execution integrity |

**Performance**: Reduces HE overhead by 40-60% for bootstrapping operations.
**Trade-off**: TEE side-channel vulnerabilities (SGX repeatedly broken; AEPIC, ÆPIC Leak, Plundervolt, SGAxe).
**Production**: Microsoft Azure confidential computing, Google Cloud Confidential VMs.

### Pattern 5: Multi-Layer Privacy Stacks

A 2025-2026 trend: combining multiple privacy technologies in layered architectures rather than pursuing a single silver bullet.

**BlockIntelChain (2025)**: DP (ε=0.1, 92% utility preservation) + ZKP (94% verification accuracy) + FHE + SMPC for IoT threat intelligence sharing. 923 TPS at 500 nodes, 99.6% consensus.

**Design principle**: Each layer addresses a specific privacy dimension — DP for statistical privacy, ZKP for computation integrity, FHE for data confidentiality, SMPC for distributed trust.

## Hardware Acceleration Landscape (2026)

### The Convergence Gap

FHE and ZKP have independently developed specialized hardware acceleration, but **no unified FHE+ZKP ASIC exists as of mid-2026**. This is the primary hardware blocker for practical FHE+ZKP hybrid deployments.

| Accelerator | Target | Architecture | Performance | Status |
|-------------|--------|-------------|-------------|--------|
| **Falcon** (ASPLOS 2026) | FHE | Algorithm-hardware co-design; 28nm fabrication | End-to-end execution for lightweight parameters | Research — ASPLOS 2026 |
| **UniZK** (ASPLOS 2025) | ZKP | Systolic-array with extra local links; NTT + hash + polynomial | Unified kernel support across ZKP primitives | Research — ASPLOS 2025 |
| **CROSS** (2025) | FHE on TPU | Compiler transforms HE workloads to INT8 matrix multiplications for TPU v6e | Higher throughput/watt than GPU (Cheddar, WarpDrive) | Research — ISCA 2025 |
| **UNIT** (IEEE 2025) | TFHE on FPGA | Unified FPGA-based TFHE accelerator | Memory-efficient TFHE operations | Research |
| **NVIDIA Cheddar** | FHE+ZK | GPU library for FHE/ZK inference | Production GPU acceleration | Released 2026 |
| **Intel Heracles** (ISSCC 2026) | FHE | Programmable FHE accelerator | ~25ms encrypted inference | Announced — production TBD |
| **DARPA DPRIVE** | FHE | FPGA-based FHE acceleration | Classified performance targets | Government program — ongoing |

**Key insight**: FHE accelerators (Falcon, UNIT) and ZKP accelerators (UniZK) use fundamentally different hardware primitives — FHE requires large-integer modular arithmetic with high memory bandwidth; ZKP requires NTT, hash functions, and polynomial arithmetic. A unified accelerator would need to support both workloads efficiently, which remains an open hardware design problem.

### The CROSS TPU Breakthrough

CROSS (2025) demonstrated that existing AI accelerators (Google TPU v6e) can achieve ASIC-level energy efficiency for FHE by transforming high-precision modular arithmetic into low-precision (INT8) matrix multiplications — the native operation of AI accelerators. This suggests a convergence path: **AI inference hardware can double as FHE hardware**, potentially enabling FHE+ZKP on the same AI accelerator used for the model being verified.

## Security Considerations

### VHE Cryptanalysis (Cheon & Jang, 2025)

Chatel et al. (CCS) introduced two lightweight Verifiable Homomorphic Encryption (VHE) schemes: Replication Encoding (REP) and Polynomial Encoding (PE). Albrecht et al. (Eurocrypt) used a similar approach for Verifiable Oblivious PRF (vADDG).

**Attack result (arXiv:2502.12628)**:
- **vADDG**: Claimed 80-bit security parameters → less than 10 bits of concrete security after forgery attack. **Complete break**.
- **REP/PE**: Probability-1 forgery attack with linear time complexity when using FHE.

**Lesson**: Embedding verification secrets within HE ciphertexts is fragile. The homomorphic property that enables computation also enables attackers to manipulate verification secrets. Production FHE+ZKP systems should use **separate cryptographic layers** — FHE for computation, independent ZKP for verification — rather than lightweight embedding schemes.

### Trusted Setup vs Transparent Setup

| Setup Type | Example | Risk |
|-----------|---------|------|
| Trusted setup | Groth16 zk-SNARK | Toxic waste ceremony required; if compromised, proofs can be forged |
| Transparent setup | STARKs, Jolt (Lasso lookup), Plonky3 | No trusted setup; higher proof sizes |

**Recommendation for FHE+ZKP**: Use transparent-setup ZKP systems (STARKs, Jolt Atlas) for FHE execution verification. The FHE+ZKP hybrid already has a high performance overhead — adding trusted-setup ceremony risk for the verification layer is unnecessary and creates a single point of failure.

## 2026 Research Frontiers

### 1. ZKMLOps — Unified Zero-Knowledge ML Operations Framework

A 2025-2026 research convergence trend toward a unified ZKMLOps framework that integrates ZKPs into all stages of the ML pipeline (data preprocessing, training, inference, monitoring). This is the operational deployment framework that FHE+ZKP hybrids need to move from research to production.

**Current state**: Inference verification is well-studied; data preprocessing and training stages remain underexplored.

### 2. zkVC — Fast Zero-Knowledge Proof for Private and Verifiable Computing

arXiv:2504.12217 (Zhang et al., 2025): A zkVM architecture optimized for verifiable computation with privacy guarantees. Designed to close the performance gap between general-purpose zkVMs and domain-specific proof systems.

### 3. TCU — Trusted Compute Units

Castillo et al. (arXiv:2504.15717, 2025): A composable framework enabling dApps to flexibly offload computations to TEEs, zkVMs, or FHE backends with unified proof-of-correctness. This is the architectural pattern for heterogeneous verifiable computation — the FHE+ZKP hybrid as a pluggable backend.

### 4. Hardware Convergence

The open problem: design a single accelerator that efficiently handles both FHE (large-integer modular arithmetic, high memory bandwidth) and ZKP (NTT, hash, polynomial arithmetic). CROSS's TPU-based approach suggests AI hardware may be the convergence substrate. UniZK's systolic-array architecture with reconfigurable local links is the closest existing design to a unified solution.

## Exocortex Integration Pathways

1. **Encrypted Entity Resolution**: FHE computes entity matches across private datasets; ZKP proves the Fellegi-Sunter algorithm was correctly applied. Direct extension of [[differential-privacy-osint-entity-resolution]] and [[homomorphic-encryption-state-of-art]].
2. **Verifiable Agent Inference**: zkLLM (Jolt Atlas) proves agent outputs come from the claimed model; FHE encrypts the inference request so the model provider cannot see what was asked. Together: private query + verifiable response. Bridges [[zkml-verifiable-ai-inference]] and [[local-to-frontier-bridging]].
3. **Trustless Multi-Agent Coordination**: Agents exchange encrypted data via FHE; ZKPs prove each agent followed the coordination protocol. Enables [[multi-agent-orchestration-patterns]] without a trusted orchestrator.
4. **Regulatory Compliance Layer**: ZKP-of-FHE for provable GDPR/AML compliance in [[osint-legal-ethical-boundaries]].
5. **Oracle Fabrication Detection**: zkLLM proofs make oracle fabrication cryptographically detectable — extends [[counterintelligence-analysis-frameworks]] and [[entity-resolution-agent-safety]] with cryptographic integrity guarantees.
6. **Federated Learning with Verifiable Aggregation**: HHE (PASTA+BFV) for client-side encryption with 2,000× bandwidth reduction; ZKP verifies server-side aggregation correctness. Addresses the [[privacy-preserving-federated-learning-critical-infrastructure]] trust gap.

## Cross-Domain Connections

| Domain | Connection | Significance |
|--------|-----------|-------------|
| Entity Resolution | FHE+ZKP enables cross-silo entity matching | Solves PII-sharing blocker — [[differential-privacy-osint-entity-resolution]] |
| Epistemic Integrity | zkLLM + FHE = private + verifiable inference | Completes agent trust stack — [[counterintelligence-analysis-frameworks]] |
| Multi-Agent Architecture | Trustless coordination via FHE+ZKP | Removes central orchestrator — [[multi-agent-orchestration-patterns]] |
| Hardware/Physical Computing | Unified FHE+ZKP accelerator | Open hardware design problem — [[rtx-3090-cuda-optimization]], [[fpga-inference-acceleration]] |
| Federated Learning | HHE + ZKP aggregation verification | Closes critical infrastructure FL trust gap — [[privacy-preserving-federated-learning-critical-infrastructure]] |
| OSINT/Legal Boundaries | ZKP-of-FHE compliance proofs | Regulatory forcing function — [[osint-legal-ethical-boundaries]] |
| Local-to-Frontier Bridging | zkLLM for verified model outputs without weight disclosure | Private model verification — [[local-to-frontier-bridging]] |
| SCADA/ICS Security | FHE-encrypted anomaly detection + ZKP-verified alert logic | Auditable critical infrastructure AI — [[scada-ics-security]] |
| Post-Quantum Cryptography | FHE (lattice-based) is already post-quantum; ZKP needs PQ migration | Different migration timelines for each layer — [[post-quantum-cryptography-critical-infrastructure]] |
| Verifiable AI Inference | zkML + FHE composition | Private inference with integrity guarantees — [[zkml-verifiable-ai-inference]] |
| Financial Intelligence | ZKP-of-FHE for AML screening; cross-bank encrypted transaction monitoring | Privacy-preserving FININT — [[financial-intelligence-entity-resolution]] |
| Supply Chain Analysis | Encrypted supply chain graph computation; ZKP-verified provenance claims | Confidential supply chain reconstruction — [[supply-chain-network-analysis-osint]] |

## References

1. Jolt Atlas (2026). "Verifiable Inference via Lookup Arguments." arXiv:2602.17452.
2. CROSS: Leveraging ASIC AI Chips for Homomorphic Encryption. Tong et al. (2025). ISCA 2025. arXiv:2501.07047.
3. Falcon: Algorithm-Hardware Co-Design for Efficient FHE Acceleration. Zhang et al. ASPLOS 2026.
4. UniZK: Accelerating Zero-Knowledge Proof with Unified Hardware. ASPLOS 2025.
5. UNIT: A Highly Unified and Memory-Efficient FPGA-Based Accelerator for Torus FHE. IEEE 2025.
6. Cryptanalysis on Lightweight Verifiable Homomorphic Encryption. Cheon & Jang (2025). arXiv:2502.12628. ← **SECURITY WARNING**: vADDG 80-bit claim broken to <10-bit.
7. zkVC: Fast Zero-Knowledge Proof for Private and Verifiable Computing. Zhang et al. (2025). arXiv:2504.12217.
8. Trusted Compute Units: A Framework for Chained Verifiable Computations. Castillo et al. (2025). arXiv:2504.15717.
9. BlockIntelChain: A Blockchain-based Cyber Threat Intelligence Sharing Architecture. Nature Scientific Reports (2025). DOI:10.1038/s41598-025-29152-6.
10. Privacy-Preserving Machine Learning Techniques: Cryptographic Approaches, Challenges, and Future Directions. Applied Sciences 16(1), 277 (2026).
11. A Survey of Zero-Knowledge Proof Based Verifiable Machine Learning. arXiv:2502.18535v2 (2026).
12. FHE-SQL: Fully Homomorphic Encrypted SQL Database. arXiv:2510.15413 (2025).
13. SAFETY: Secure gwAs in Federated Environment Through a Hybrid solution with Intel SGX and Homomorphic Encryption. arXiv:1703.02577 (2017).
14. Hybrid Homomorphic Encryption Framework for Federated Learning (PASTA+BFV). Costa et al. arXiv:2603.26417 (2026).
15. Intel Heracles programmable FHE accelerator. ISSCC 2026.
16. NVIDIA Cheddar GPU library for FHE/ZK inference (2026).
17. DARPA DPRIVE FPGA FHE acceleration program.
18. EU Horizon 2026 healthcare consortia — FHE+ZKP clinical trial verification.
19. Exocortex internal: v16 field reports (2026-05-15, 2026-05-22, 2026-06-02), v16 wiki (homomorphic-encryption-practical-deployment, zkml-verification, homomorphic-encryption-production-deployment-2026), v17 wiki (zkml-verifiable-ai-inference, homomorphic-encryption-state-of-art).

---
**Verification Status:** STABLE — deepened from 91 to ~240 lines with shared corpus (v16/v17, 5+ documents), web research (5+ ArXiv papers, 3 hardware publications), and cross-domain mapping (12 connections). Hardware convergence gap (no unified FHE+ZKP ASIC) verified against 2025-2026 literature. VHE security warning grounded in cryptanalytic result (arXiv:2502.12628).
