# Privacy-Preserving Edge AI Hardware: TEEs, Homomorphic Encryption Accelerators, and the Convergent Path

**Date:** 2026-05-27
**Interest:** Hardware & Physical Computing
**Type:** Field Report

---

## 1. What I explored

I investigated the intersection of privacy-preserving computation and edge AI hardware accelerators. The core question: How do you run machine learning inference on sensitive data at the edge while maintaining confidentiality of both the data and the model? Two dominant approaches have emerged: **(1) Trusted Execution Environments (TEEs)** — hardware-enforced enclaves that isolate computation from untrusted hosts (Intel SGX, AMD SEV, Intel TDX) — and **(2) Homomorphic Encryption (HE)** — cryptographic primitives that allow computation on encrypted data without decryption. I explored recent (2020–2026) hardware acceleration research that bridges these approaches.

---

## 2. What I found

### Path A: Hardware-Accelerated Homomorphic Encryption

**HHEML — Hybrid Homomorphic Encryption for Privacy-Preserving ML on Edge** (arXiv:2510.20243v1, Oct 2025)

This is the first end-to-end hardware-accelerated Hybrid Homomorphic Encryption (HHE) framework. HHE combines a lightweight symmetric cipher optimized for FHE compatibility with Fully Homomorphic Encryption, reducing client-side computation cost. The authors implement a dedicated hardware accelerator on a PYNQ-Z2 FPGA:

| Metric | Result |
|--------|--------|
| Client encryption latency reduction | **50x** vs software |
| Hardware throughput gain | **~2x** vs prior FPGA HHE accelerators |
| Platform | Xilinx PYNQ-Z2 (Zynq-7020) |
| Dataset | MNIST (proof-of-concept) |

Key contribution: hardware-software co-design methodology placing the symmetric cipher in dedicated FPGA hardware, dramatically cutting the bottleneck for edge devices.

### Path B: TEE-Based Accelerator Offloading

**TwinShield — Securing Transformer-based AI Execution via Unified TEEs and Crypto-protected Accelerators** (arXiv:2507.03278v2, Jul 2025)

TwinShield addresses the critical limitation of prior TEE-offloading schemes: they cannot securely offload Attention and SoftMax operations, forcing these large computations to run inside slow TEE CPUs. TwinShield uses cryptographic protections to enable secure offloading to untrusted GPUs:

| Metric | Result |
|--------|--------|
| Computation offloaded to GPU | **87%** |
| Speedup over prior approaches | **4.0x - 6.1x** |
| Models tested | Various Transformer architectures |
| Protection | Dual (data + model confidentiality) |

**Customizing Trusted AI Accelerators** (arXiv:2011.06376, Nov 2020): Earlier foundation paper establishing the paradigm of unmodified trusted CPU (SGX enclave) + customized trusted AI accelerator with cryptographic channel protection. Demonstrated on open-source VTA.

**GOAT: GPU Outsourcing with Asynchronous Probabilistic Integrity Verification** (arXiv:2010.08855, Oct 2020): Introduces probabilistic verification — randomly checking computation steps rather than all — combined with training hyperparameter constraints. 2x-20x speedup over pure-TEE training while guaranteeing >0.999 integrity probability against backdoor attacks.

### Path C: Edge NPU with Inherent Privacy

**STAR: Privacy-Preserving, Energy-Efficient Edge AI for Human Activity Recognition via Wi-Fi CSI** (arXiv:2510.26148, Oct 2025)

Uses Wi-Fi Channel State Information (CSI) — inherently privacy-preserving compared to cameras — combined with a lightweight GRU model (97.6k parameters, INT8) on a Rockchip RV1126 NPU:

| Metric | Result |
|--------|--------|
| Recognition accuracy (7 classes) | 93.52% |
| Human presence detection | 99.11% |
| CPU utilization | 8% |
| Speedup vs CPU inference | **6x** |

---

## 3. What I think is interesting

### The Convergence Path: TEE + HE Hybrid

The most compelling future combines both approaches. HHEML shows lightweight symmetric cipher in FPGA hardware can make HE practical for edge clients. TwinShield shows TEEs can securely offload Transformer inference to untrusted accelerators. Combined:

- **Inference data** encrypted client-side (HHEML's fast FPGA cipher), transmitted to edge/cloud server
- **Server** uses TEE for model confidentiality while offloading heavy matrix ops to untrusted GPU with cryptographic protections (TwinShield)
- **Verification** uses GOAT's probabilistic approach to maintain integrity guarantees

Result: end-to-end privacy-preserving inference pipeline suitable for high-value models (medical, financial, defense).

### Why Hardware Matters

Software-based HE (SEAL, HElib, OpenFHE) is measured in *seconds to minutes* for one inference. Hardware acceleration — FPGA (HHEML) or TEE+GPU (TwinShield) — brings this to *millisecond to second* range, making privacy-preserving inference practical for interactive applications.

### The Open Question: Formal Verification of TEEs

TEE security relies on vendor trustworthiness and bug-free implementation. SGX history (SGAxe, Plundervolt, AEPIC Leak) and SEV history (SEVerity) shows this assumption is fragile. HE offers mathematically provable guarantees but at higher cost. The hybrid approach introduces a new trust model needing formal analysis.

---

## 4. What I'd explore next

1. **Unified TEE+HE Framework:** Search for papers combining TEE and HE in a single inference pipeline (likely 2025-2026 as fields mature)
2. **NVIDIA Confidential Computing:** Investigate H100/H200 Confidential Computing with AMD SEV-SNP for GPU; compare to TwinShield
3. **FPGA TEE + Accelerator:** Single FPGA implementing both TEE (like Keystone on RISC-V) and matrix accelerator for sovereign, auditable privacy-preserving edge device
4. **Energy Costs:** Energy comparison between HE, TEE, and hybrid for end-to-end edge inference
5. **Regulatory Implications:** Does HE processing on encrypted data satisfy GDPR "data minimization" even though data is technically processed?

---

## 5. Cross-Domain Connections

- **Privacy & Cryptography:** Direct overlap — HE and TEE are cryptographic primitives with hardware instantiation
- **AI Agent Architecture & Local Inference:** Privacy-preserving edge AI enables sovereign AI agents processing sensitive data locally without cloud exposure
- **Electric Utility & Critical Infrastructure:** Substation edge devices processing encrypted operational data could detect anomalies without exposing grid telemetry
- **History of Intelligence Operations:** SIGINT history teaches that metadata and traffic patterns leak even with encrypted content — side channels (power, timing, EM) remain critical concerns

---

## Sources

| Source | Type | Date | ID |
|--------|------|------|-----|
| Chan et al. HHEML | arXiv | Oct 2025 | 2510.20243v1 |
| Xue et al. TwinShield | arXiv | Jul 2025 | 2507.03278v2 |
| Asvadishirehjini et al. GOAT | arXiv | Oct 2020 | 2010.08855v1 |
| Xie et al. Customizing Trusted AI Accelerators | arXiv | Nov 2020 | 2011.06376v1 |
| Liu. STAR | arXiv | Oct 2025 | 2510.26148v1 |
