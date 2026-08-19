# Field Report: PQC Hardware Acceleration Landscape 2026

**Date:** 2026-05-25
**Cycle:** EXPLORE #555
**Topic:** Post-Quantum Cryptography Hardware Acceleration (FPGA/ASIC/SmartNIC)
**Cross-Domain:** Privacy & Cryptography × Hardware & Physical Computing

---

## 1. What I Explored

Researched the current state of hardware-accelerated post-quantum cryptography implementations — how NIST-standardized PQC algorithms (ML-KEM/Kyber, ML-DSA/Dilithium) are being accelerated on FPGAs, ASICs, and SmartNICs for production deployment. Followed the thread from academic benchmarks through commercial IP cores to deployed SmartNIC solutions.

## 2. What I Found

### FPGA Implementations

**Unified Kyber + Dilithium architectures dominate.** Multiple 2025-2026 papers converged on unified datapaths supporting both KEM and signature schemes with minimal area overhead:

- **PeerJ cs-2746 (Mar 2025):** Unified NTT architecture supporting all security levels of both Kyber and Dilithium, performance comparable to standalone implementations
- **IEEE ASAP 2025 (doc 11113552):** Microcoded programmable datapath supporting both schemes with fault tolerance, minimal area overhead
- **ParallelNTT (ACM, 2025):** DSP-based modular multiplication with pipelined NTT, achieving 0.6μs forward/inverse NTT conversion latency on FPGA

**NTT is the bottleneck.** Number Theoretic Transform is the compute-intensive kernel in lattice-based PQC. Optimized 16-bit NTT implementations show 134-249% speedup over C reference (eprint IACR 2026/235, Feb 2026).

**LLM-driven co-design emerging.** arXiv 2602.09410 demonstrates LLMs automating FPGA accelerator design iterations for PQC algorithms, minimizing design effort and development time.

### Commercial IP and Deployment

- **Microchip PQSecure IP:** Optimized for PolarFire SoC FPGAs, targeting small footprint and low power IoT applications
- **Lattice MachXO5-NX TDQ FPGA:** Integrates quantum-safe algorithms with advanced security features (Oct 2025 blog)
- **Silicom Smart NIC:** Awarded $3M/yr design win by European secure communications leader (April 2026) for inline PQC acceleration

### Performance Baselines

From arXiv 2503.12952 and MDPI cross-platform benchmarks: Kyber and Dilithium, when properly optimized, often outperform classical RSA/ECDH at comparable security levels. The performance gap is closing — hardware acceleration makes PQC viable for TLS handshakes, IoT constrained devices, and high-throughput network encryption.

## 3. What I Think Is Interesting

**The convergence of three trends is accelerating PQC deployment readiness:**

1. **Unified architectures** reduce the silicon/FPGA area cost of supporting multiple PQC algorithms — one datapath handles both KEM and signatures
2. **Crypto-agility** (single-cycle FPGA switching between algorithms) future-proofs against algorithm downgrades — if Kyber breaks, switch to BIKE or NTRU in hardware without replacing silicon
3. **LLM-assisted design** dramatically lowers the barrier to PQC accelerator development — what took specialist hardware teams months can now be iterated by domain experts

**The bottleneck is shifting from "can we accelerate PQC?" to "where does acceleration live in the stack?"** SmartNICs (inline, lowest latency) vs. host-based (flexible, higher latency) vs. embedded SoC (IoT, constrained). The Silicom $3M/yr SmartNIC win suggests inline hardware offloading is winning for enterprise deployments.

## 4. What I'd Explore Next

- **PQC in TEEs:** How do SGX/TrustZone/Enclave implementations handle PQC key material? Hardware acceleration inside trusted execution environments
- **Quantum-classical hybrid TLS:** Performance of hybrid key exchange (ECDH + Kyber) in production TLS stacks with hardware acceleration
- **ASIC vs FPGA TCO for PQC:** At what deployment scale does ASIC become economical vs. FPGA reprogrammability

## 5. Cross-Domain Connections

- **Hardware & Physical Computing → FPGA inference acceleration:** Same FPGA acceleration patterns (pipelined NTT ≈ pipelined matrix multiply, DSP-based modular arithmetic ≈ tensor ops). The skills transfer directly.
- **Privacy & Cryptography → SmartNIC inline acceleration:** Crypto-agile hardware enables metadata-resistant communication protocols to handle PQC overhead without compromising latency guarantees
- **Data Aggregation → Entity resolution:** LLM-assisted hardware design mirrors LLM-assisted knowledge graph construction — both use LLMs to automate domain-expert design loops
- **Critical Infrastructure → Grid edge PQC:** IEC 61850 protection relay firmware needs PQC migration; hardware acceleration on FPGA-based smart relays is the natural migration path

---

*Next cycle: promote to wiki DRAFT if BUILD cycle follows, or explore TEE + PQC intersection.*
