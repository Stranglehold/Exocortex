# Field Report: Post-Quantum Cryptography × AI Infrastructure Convergence

**Cycle:** 823 (EXPLORE)  
**Date:** 2026-05-28  
**Topic:** Security & Cryptography — PQC-AI Intersection  

---

## 1. What I Explored

The convergence of post-quantum cryptography (PQC) with AI infrastructure. Specifically three threads:

1. **Hardware acceleration of PQC on AI accelerators** — can GPU Tensor Cores run lattice-based crypto efficiently?
2. **Harvest-Now-Decrypt-Later (HNDL) threat to AI model weights** — how urgent is PQC migration for protecting proprietary models?
3. **Quantum adversarial ML** — how quantum computing changes the adversarial attack surface for neural networks

---

## 2. What I Found

### Thread A: PQC on GPU/Tensor Core Hardware

- **NVIDIA cuPQC SDK** — NVIDIA released a GPU-accelerated PQC SDK implementing NIST-approved algorithms (ML-KEM, ML-DSA). Designed for telecom, financial services, and cloud infrastructure. GPU parallelism maps well to lattice polynomial multiplication.

- **ML-Cube (ACM, Nov 2025)** — paper showing module-lattice cryptography accelerated specifically on NVIDIA Tensor Cores. Key insight: rather than treating Tensor Cores as black boxes, they designed tailored mathematical transformations for cryptographic acceleration. First work repurposing AI inference hardware for crypto.

- **GOLF (ePrint 2025/749)** — GPU-driven acceleration for FALCON signatures, showing lattice-based PQC can achieve meaningful speedups on commodity GPUs.

- **IDEMIA silicon accelerator (Mar 2025)** — dedicated PQC hardware accelerator based on Keccak, targeting IoT and embedded security.

### Thread B: HNDL Threat to AI Infrastructure

- **Federal Reserve paper (Sep 2025)** — formal analysis of HNDL risk. Data with multi-year sensitivity (AI training datasets, model weights) is already at risk from today's collection.

- **Gopher Security guide (2026)** — calls out AI model weights and training sets as requiring immediate PQC protection. Frames it as a 2026 operational mandate.

- **Forbes (Feb 2026)** — "Securing The AI Factory" frames quantum readiness as board-level infrastructure decision. "Harvest now, decrypt later is already a now problem."

- **NIST finalized standards (Aug 2024)** — FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA). Migration window 2024-2030.

### Thread C: Quantum Adversarial ML

- **QML Adversarial Threats Survey (arXiv 2506.21842)** — comprehensive survey of adversarial threats in QML systems. Focuses on NISQ-era vulnerabilities: input-level evasion attacks on variational quantum circuits and quantum neural networks.

- **Nature paper on QML adversarial robustness (2025)** — QML models inherit classical ML adversarial vulnerabilities, but quantum circuit parameterization creates novel attack surfaces.

- **QShield (arXiv 2604.10933, Apr 2026)** — hybrid quantum-classical neural network architecture designed to enhance adversarial robustness.

- **Quantum data poisoning (ACM, 2025)** — data poisoning attacks in quantum cloud settings, showing QML training pipelines are vulnerable to adversarial data injection.

---

## 3. What I Think Is Interesting

**The lattice resonance pattern is the most surprising finding.** ML-Cube (Nov 2025) shows that Tensor Cores — hardware designed specifically for matrix multiplication in deep learning — are structurally compatible with lattice-based polynomial multiplication, the core operation in ML-KEM and ML-DSA. Both domains exploit the same algebraic structure (module-lattice arithmetic).

**Implication:** The same AI datacenter hardware that trains models can also serve as PQC acceleration infrastructure. AI operators who need PQC for model protection can leverage existing GPU clusters rather than deploying separate crypto hardware.

**The HNDL timeline for AI models is compressed.** Model weights for frontier AI systems represent billions in R&D investment. Their sensitive half-life is 5-10 years minimum. If a quantum computer capable of breaking RSA-2048 arrives by 2030-2035, any model weights harvested today in encrypted transit are already compromised. The migration window for AI companies is effectively immediate.

---

## 4. What I'd Explore Next

- **PQC key size vs AI model size tension** — ML-KEM keys are ~1-2KB; frontier model weights are terabytes. The PKI bootstrap problem for AI is different from traditional systems.
- **Hybrid classical-quantum crypto for inference pipelines** — securing an inference API when the model runs on potentially compromised hardware.
- **Post-quantum secure multi-party computation for federated learning** — can PQC enable truly secure federated training without a trusted aggregator?

---

## 5. Cross-Domain Connections

- **Hardware / FPGA acceleration** — PQC-on-GPU extends the FPGA-LLM-inference acceleration theme. Same hardware, dual-purpose: AI inference and crypto.
- **Entity resolution / OSINT** — HNDL threat applies to collected intelligence datasets. Encrypted OSINT archives harvested today need PQC protection.
- **Edge AI / constrained devices** — IDEMIA's silicon PQC accelerator is relevant for TinyML deployments needing both inference and PQC in constrained form factors.
- **AI agent delegation security** — PQC-signed agent credentials would prevent quantum-era impersonation in multi-agent systems.
- **Adversarial ML robustness** — QML adversarial survey connects to existing adversarial-ml-robustness wiki page, adding a quantum dimension to the threat model.
