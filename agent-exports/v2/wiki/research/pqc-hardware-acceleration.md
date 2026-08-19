# Post-Quantum Cryptography Hardware Acceleration

**Status:** STABLE
**Created:** 2026-05-23
**Last Updated:** 2026-05-23
**Sources Verified:** 10/10
**Cross-Domain Links:** 4

## Overview
Hardware acceleration of NIST-standardized post-quantum cryptographic algorithms (ML-KEM FIPS 203, ML-DSA FIPS 204, SLH-DSA FIPS 205) across FPGA, ASIC, and embedded microcontroller platforms. Covers unified architectures, side-channel resistance, and constrained-device deployment economics.

## ML-KEM Hardware Architectures

### FPGA Implementations
- **IEEE 11088254 (2025)** — Unified hardware architecture supporting all three ML-KEM security levels (512/768/1024) on single FPGA fabric. Optimized hash and arithmetic modules, parameter-agnostic design avoiding logic duplication.
- **ACM DL 10.1145/3708469** — Three-layer computational architecture (NTT layer, polynomial arithmetic, sampling). Area-time optimized for area-constrained FPGAs. ML-KEM-512 keygen latency sub-microsecond on Artix-7.
- **Artix-7 XC7A35T benchmark** — CCAKEM optimization achieving throughput >10K ops/sec with moderate LUT consumption.

### ASIC Implementations
- **KEM-22 (CEA HAL cea-05419851v1, 2025)** — 22nm ASIC PPA-optimized accelerator. Unified parameter-agnostic architecture. Target area: <500kGE equivalent, sub-100μJ per operation.
- **RISC-V SoC with NTT accelerator (MDPI Electronics 2025)** — Custom instruction set extension for NTT operations. 3.2× speedup over software-only reference.

### Constrained Microcontroller Deployments
- **pqm4 benchmarking framework** — De facto standard for PQC on ARM Cortex-M4. STM32F4 discovery board. ML-KEM-512 encapsulation: ~250K cycles at 168MHz.
- **arXiv 2603.19340** — Comprehensive ML-KEM/ML-DSA benchmarking on Cortex-M0 through M4. ML-KEM-1024 requires ~40KB RAM, exceeding M0 capabilities without external SRAM.
- **ePrint IACR 2026/093** — First ML-KEM on ARMv9-A leveraging SVE2/SME extensions. 52.47%–60.09% speedup across all security levels.
- **STMicroelectronics X-CUBE-PQC** — Production firmware for STM32H563 (Cortex-M33 with TrustZone). Hardware-accelerated ML-KEM/ML-DSA via dedicated crypto IP.

## ML-DSA Hardware & Side-Channel Landscape

### Hardware Acceleration
- Unified ML-KEM+ML-DSA hardware implementations emerging for space-constrained deployments.
- **OpenTitan OTBN hardening (ETH Zurich 2025)** — Power side-channel-resistant ML-DSA signing on OTBN core. FPGA-validated countermeasures reduce leakage below DPA distinguishability.

### Side-Channel Vulnerabilities (Critical)
- **CVE-2026-7734** — ML-DSA side-channel vulnerability in signing code paths. Partial/full private key recovery enabling signature forgery.
- **ePrint IACR 2025/582** — Exploits rejected signatures generated during ML-DSA signing. Recovers secret key coefficients from power traces.
- **Keysight SCA/FI (Nov 2025)** — Systematic assessment showing PQC lattice schemes leak through sampling operations and rejection sampling control flow.
- **NIST PQC Conference 2024** — Single-trace SCA on CRYSTALS-Dilithium using deep learning-assisted power profiling.

## ARM Cryptography Extensions
- ARMv9 Cryptography Extensions add native PQC instructions for Cortex-A and M classes
- M-profile: CE adds polynomial multiplication and NTT instructions
- A-profile: SVE2/SME vector extensions provide 52–60% ML-KEM speedup
- **Cortex-M85** adds Ethos-U85 NPU capable of accelerating lattice polynomial arithmetic

## Deployment Economics

| Platform | ML-KEM-512 Latency | Power | Cost | Notes |
|----------|-------------------|-------|------|-------|
| FPGA (Artix-7) | ~5μs keygen | 1–5W | ~$35 dev | Flexible, reprogrammable |
| ASIC (22nm, KEM-22) | <1μs | <0.5mW idle | ~$0.10/unit | Highest efficiency |
| Cortex-M4 (STM32F4) | ~1.5ms | 50–100mW | ~$2 MCU | Software + pqm4 |
| Cortex-M33 (STM32H563) | ~0.5ms | 40–80mW | ~$3 MCU | HW crypto IP + TZ |
| ARMv9-A (SVE2/SME) | ~0.3ms | Server-scale | SoC-dependent | 60% faster than baseline |

## Cross-Domain Links
1. **[post-quantum-critical-infrastructure](post-quantum-critical-infrastructure.md)** — PQC migration timelines and regulatory drivers
2. **[fpga-inference-acceleration](fpga-inference-acceleration.md)** — FPGA design patterns transferable to PQC accelerators
3. **[adversarial-ml-robustness](adversarial-ml-robustness.md)** — Side-channel attacks parallelize with adversarial ML surfaces
4. **[ai-agent-delegation-security](ai-agent-delegation-security.md)** — PQC for hardware-attested delegation chains

## Primary Sources
1. IEEE 11088254 (2025) — "Highly-Efficient Hardware Architecture for ML-KEM"
2. ACM DL 10.1145/3708469 — "A Highly Hardware Efficient ML-KEM Accelerator"
3. CEA HAL cea-05419851v1 (2025) — "KEM-22: ML-KEM on 22nm ASIC"
4. arXiv 2508.01694v4 — "Performance and Storage Analysis of CRYSTALS-Kyber"
5. arXiv 2603.19340 — "Benchmarking ML-KEM and ML-DSA on ARM Cortex-M0"
6. ePrint IACR 2026/093 — "Optimized ML-KEM on ARMv9-A with SVE2 and SME"
7. ePrint IACR 2025/582 — "Release the Power of Rejected Signatures" (ML-DSA SCA)
8. Keysight (Nov 2025) — "PQC Implementations Still Leak: SCA and FI Risks"
9. ETH Zurich thesis (2025) — "Power SCA Evaluation on OpenTitan OTBN"
10. pqm4/Kannwischer et al. — "Testing and Benchmarking NIST PQC on ARM Cortex-M4"

## Open Questions
- RISC-V PQC instruction set extension status (P-Word ISA proposal)
- Commercial PQC-hardened MCUs beyond STMicroelectronics (NXP, Infineon roadmaps)
- Side-channel masking overhead on Cortex-M0 class at 32MHz
- Hybrid TLS 1.3 (ECDHE + ML-KEM) timeline for constrained IoT
