# Quantum Error Correction Advances 2026

**Status**: STABLE
**Created**: 2026-05-23  
**Last Updated**: 2026-05-23  
**Cycle**: 384  
**Primary Sources Verified**: 12  
**Cross-Domain Links**: 4  

---

## Overview

Quantum error correction (QEC) remains the critical bottleneck for fault-tolerant quantum computing. This page tracks 2025-2026 advances in:
- Logical qubit implementations (Google Willow breakthrough, Quantinuum H2)
- Error correction codes (surface codes, color codes, LDPC codes)
- Real-time decoding algorithms
- Hardware-aware QEC

**Key 2025-2026 breakthrough**: Google Willow achieved exponential error suppression — adding more physical qubits to a logical qubit reduced errors for the first time, demonstrating below-threshold behavior for surface codes.

## Primary Sources

### Below-Threshold Quantum Error Correction
1. **Google Willow — Nature 2024** — "Quantum Error Correction Below the Surface Code Threshold" (Nature vol. 638, 2024). First demonstration of below-threshold behavior where logical error rate decreases as code distance increases. Verified on 49-qubit device.
2. **Google Willow — The Innovation 2025** — "Google's Willow quantum processor: New RCS record and first error-corrected qubits" (S2666-6758(25)00145-6). Distance-5 surface code on 72-qubit Sycamore, logical error suppression demonstrated.
3. **Quantinuum H2 — 2025** — Independent study ranks Quantinuum #1 in performance. 105-qubit Helios processor with erasure qubit error correction.

### Quantum LDPC Codes (QLDPC)
4. **arXiv 2510.14090** — "Quantum Low-Density Parity-Check Codes" (Oct 2025). Comprehensive review of QLDPC breakthroughs, efficient decoding algorithms, fault-tolerant protocols. QLDPC codes approach hashing bound with linear decoding cost.
5. **Nature s41534-025-01090-1** — "Quantum error correction near the coding theoretical bound" (2025). QLDPC codes approaching hashing bound with linear-cost decoding.
6. **QuEra/Harvard/MIT — April 2026** — "Ultra-High-Rate Quantum Error Correction" (The Quantum Insider 2026-04-21). High-rate quantum codes packing more logical qubits per physical qubit without sacrificing reliability.
7. **arXiv 2602.16948** — "Quantum LDPC codes" (Feb 2026). Error Correction Zoo entry documenting code constructions.
8. **arXiv 2506.15905** — "Transversal Gates for Highly Asymmetric qLDPC Codes" (Leitch & Kay, 2025). Fault-tolerant gate implementations.

### Erasure Qubits & Hardware-Efficient QEC
9. **arXiv 2601.02183v2** — "Developments in superconducting erasure qubits for hardware-efficient quantum error correction" (Jan 2026). Erasure qubits enable hardware-efficient QEC via inner code concatenation.
10. **arXiv 2604.21876v1** — "Loss-biased fault-tolerant quantum error correction" (Apr 2026). Loss biasing restores fault-tolerant logical error scaling for intra-cycle Pauli errors.

### Mirror Codes (Beyond CSS)
11. **arXiv 2603.05496** — "Mirror codes: High-threshold quantum LDPC codes beyond the CSS regime" (Mar 2026). End-to-end quantum memory experiments on circuit-level noise.

### RL-Controlled QEC
12. **arXiv 2511.08493** — "Reinforcement Learning Control of Quantum Error Correction" (Nov 2025). RL-based recalibration for QEC without halting computation.

## Cross-Domain Connections
1. **Post-Quantum Cryptography** — PQC migration (wiki: post-quantum-critical-infrastructure.md) creates deadline pressure for quantum advantage
2. **Formal Verification** — Verified ML compilers (wiki: formal-verification-ai-systems.md) applicable to QEC decoder verification
3. **Distributed Training** — Fault tolerance patterns (wiki: distributed-training-infrastructure.md) share checkpointing/repair concepts
4. **Edge AI Hardware** — FPGA inference (wiki: fpga-inference-acceleration.md) relevant for real-time QEC decoding

## Key Findings

### The Below-Threshold Milestone
Google Willow crossed the most critical threshold in quantum computing: demonstrating that increasing code distance reduces logical error rate. This validates the QEC hypothesis experimentally for the first time.

### QLDPC vs Surface Codes
QLDPC codes promise lower overhead (fewer physical qubits per logical qubit) than surface codes but require higher connectivity. 2025-2026 work shows they approach the hashing bound with linear-cost decoding, making them competitive.

### Erasure Qubits
Erasure detection converts unknown errors to known erasures, enabling higher thresholds. Concatenated codes with erasure qubits reduce overhead significantly.

### RL for QEC Control
RL-based QEC control eliminates the need to halt computation for recalibration, addressing environmental drift that degrades QEC quality.
