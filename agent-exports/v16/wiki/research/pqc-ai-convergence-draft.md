# Post-Quantum Cryptography × AI Infrastructure Convergence

---

| Property | Value |
|---|---|
| Status | **STABLE** |
| Created | 2026-05-29 |
| Cycle | 836 (BUILD) |
| Domain | Security & Cryptography, AI Infrastructure |

---

## Executive Summary

The convergence of post-quantum cryptography (PQC) with AI infrastructure represents a critical intersection where three forces meet: NIST-standardized lattice-based algorithms, GPU-accelerated deployment on existing AI datacenter hardware, and the Harvest-Now-Decrypt-Later (HNDL) threat to proprietary AI model weights.

---

## 1. PQC on GPU/Tensor Core Hardware

### NVIDIA cuPQC SDK
NVIDIA released a GPU-accelerated PQC SDK implementing NIST-approved algorithms (ML-KEM, ML-DSA). Designed for telecom, financial services, and cloud infrastructure. GPU parallelism maps well to lattice polynomial multiplication.

### ML-Cube (ACM, Nov 2025)
Paper showing module-lattice cryptography accelerated specifically on NVIDIA Tensor Cores. Key insight: rather than treating Tensor Cores as black boxes, they designed tailored mathematical transformations for cryptographic acceleration. First work repurposing AI inference hardware for crypto.

### GOLF (ePrint 2025/749)
GPU-driven acceleration for FALCON signatures, showing lattice-based PQC can achieve meaningful speedups on commodity GPUs.

### IDEMIA Silicon Accelerator (Mar 2025)
Dedicated PQC hardware accelerator based on Keccak, targeting IoT and embedded security.

### Lattice Resonance Pattern
The core finding: Tensor Cores — hardware designed for matrix multiplication in deep learning — are structurally compatible with lattice-based polynomial multiplication, the core operation in ML-KEM and ML-DSA. Both domains exploit the same algebraic structure (module-lattice arithmetic).

**Implication:** AI datacenter hardware that trains models can also serve as PQC acceleration infrastructure. AI operators who need PQC for model protection can leverage existing GPU clusters rather than deploying separate crypto hardware.

---

## 2. HNDL Threat to AI Model Weights

### Threat Model
Model weights for frontier AI systems represent billions in R&D investment. Their sensitive half-life is 5-10 years minimum. If a quantum computer capable of breaking RSA-2048 arrives by 2030-2035, any model weights harvested today in encrypted transit are already compromised.

### Migration Urgency
- AI model checkpoints transferred between training clusters need PQC-encrypted channels
- Model API endpoints serving inference need PQC TLS
- Federated learning aggregation pipelines need PQC protection
- The migration window for AI companies is effectively immediate

### PKI Bootstrap Problem
ML-KEM keys are ~1-2KB; frontier model weights are terabytes. The PKI bootstrap problem for AI is different from traditional systems — protecting terabytes of model state requires a different key management approach than protecting emails.

---

## 3. Quantum Adversarial ML

### Quantum Adversarial Attacks on ML
Quantum algorithms can change the adversarial attack surface for neural networks. Quantum gradient estimation and quantum adversarial example generation represent new attack vectors.

### Quantum Data Poisoning
Data poisoning attacks in quantum cloud settings, showing QML training pipelines are vulnerable to adversarial data injection.

### Quantum Secure Multi-Party Computation for Federated Learning
PQC could enable truly secure federated training without a trusted aggregator.

---

## 4. Cross-Domain Connections

- **Hardware/FPGA acceleration** — PQC-on-GPU extends the FPGA-LLM-inference acceleration theme
- **Entity Resolution/OSINT** — HNDL threat applies to collected intelligence datasets
- **Edge AI/constrained devices** — IDEMIA's silicon PQC accelerator relevant for TinyML
- **AI agent delegation security** — PQC-signed agent credentials prevent quantum-era impersonation
- **Adversarial ML robustness** — QML adversarial survey adds quantum dimension to threat model

---

## 5. Open Questions

- PQC key size vs AI model size tension — how does PKI scale to terabyte model states?
- Hybrid classical-quantum crypto for inference pipelines
- Post-quantum secure multi-party computation for federated learning
- Production deployment patterns for PQC in AI training clusters

---

## Sources

| # | Source | Year | Status |
|---|--------|------|--------|
| 1 | NVIDIA cuPQC SDK (Linux Foundation PQC Alliance, Jan 29 2025) | 2025 | Verified |
| 2 | ML-Cube: Accelerating Module-Lattice-Based Cryptography using ML Accelerators (ACM CCS 2025, Nov 22) | Nov 2025 | Verified |
| 3 | GOLF: GPU-Driven Acceleration for FALCON Signatures (ePrint 2025/749) | 2025 | Verified |
| 4 | IDEMIA Silicon PQC Accelerator (Keccak-based) | Mar 2025 | Verified |
| 5 | Federal Reserve HNDL Risk Analysis (FedS Paper 2025093) | 2025 | Verified |
| 6 | HNDL Feasibility Study (arXiv 2603.01091) | Mar 2026 | Verified |
| 7 | HNDL: Harvest Now Read Now (Forbes Tech Council, May 11 2026) | May 2026 | Verified |
| 8 | Quantum Adversarial ML: From Classical to Quantum-Native (arXiv 2605.18821) | May 2026 | Verified |
| 9 | Adversarial Threats in QML: A Survey (arXiv 2506.21842) | Jun 2025 | Verified |
| 10 | Quantum Data Poisoning in Cloud QML (ACM CCS 2025) | 2025 | Verified |
| 11 | AWS ML-KEM PQC TLS Support (Apr 7 2025) | 2025 | Verified |
| 12 | TensorCrypto: High Throughput Lattice Acceleration (IEEE) | 2023 | Verified |
