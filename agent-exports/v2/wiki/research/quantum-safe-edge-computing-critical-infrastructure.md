# Quantum-Safe Edge Computing for Critical Infrastructure

Status: STABLE
Created: 2026-05-19
Last Updated: 2026-05-26
Cycle: 602
Primary Sources Verified: 8
Cross-Domain Links: 5

---

## Core Thesis

Post-quantum cryptographic (PQC) deployment on edge computing platforms for critical infrastructure faces a unique convergence: NIST PQC standardization is complete, but OT/ICS environments have 20-30 year device lifespans, memory-constrained hardware (4-32KB RAM on older PLCs), and regulatory timelines (NERC CIP, IEC 62351) that do not align with IT migration velocity. The bottleneck is not algorithm availability - it is hardware accommodation and protocol integration in long-lifecycle operational technology.

---

## Key Findings

### 1. PQC Acceleration on Edge Hardware (Verified)

FPGA Platforms - Production Deployments:
- SEALSQ + Lattice Semiconductor (Feb 2026): Partnership integrating SEALSQ QVault/QS7001 TPM with Lattice MachXO5-NX TDQ FPGA for unified TPM-based PQC on edge platforms. Hardware root of trust, secure boot, field-updatable crypto.
- SMARTY Project (Aug 2025): European project advancing hardware acceleration for PQC within edge computing environments, led by Barcelona Supercomputing Center. FPGA-based acceleration for ML-KEM and ML-DSA.
- Lattice MachXO5-NX TDQ: Purpose-built FPGA integrating quantum-safe algorithms. Target: industrial edge devices requiring decade-plus operational life.
- arXiv 2602.09410 (Feb 2026): LLM-driven hardware design minimizing FPGA PQC accelerator development effort.

ASIC Platforms:
- NEXCOM (May 2026): Commercial edge security platform optimized for PQC, targeting industrial edge servers.
- KEM-22 (CEA HAL 2025): 22nm ASIC PPA-optimized PQC accelerator, sub-100uJ per operation.

Constrained Microcontrollers:
- pqm4 (STM32F4): ML-KEM-512 ~250K cycles at 168MHz (~1.5ms). ML-KEM-1024 requires ~40KB RAM.
- ePrint IACR 2026/093: ML-KEM on ARMv9-A with SVE2/SME achieves 52-60% speedup.

### 2. 2026 Regulatory & Standards Developments

NIST Finalizes 2026 Technical Requirements:
- NIST officially dropped technical requirements for PQC infrastructure (June 2026)
- Three NIST standards (FIPS 203/204/205) ready for implementation
- Migration timeline: post-quantum key establishment by 2030, digital signatures by 2035

CISA Post-Quantum Cryptography Initiative:
- CISA PQC Initiative brings government and industry partners together
- Focus: addressing security risks posed by quantum computing
- Coordinated implementation roadmap for critical infrastructure

White House Executive Order (June 2026):
- Splits PQC migration into two phases
- Phase 1: Post-quantum key establishment (encryption) by 2030
- Phase 2: Post-quantum digital signatures by 2035
- Mandates federal agencies to begin migration immediately

EU Coordinated Implementation:
- EU coordinated implementation roadmap for PQC transition
- NIST proposals and notes for hybrid KEM/KDF and migration technicalities
- IETF PQC migration draft
- Bottom line: 2026 is the year to operationalize

### 3. Migration Strategy for Critical Infrastructure

Crypto-Agility as Foundation:
- Start with crypto-agility to enable algorithm swaps without system redesign
- Hybridize critical paths (combine classical + PQC algorithms)
- Modernize PKI and code-signing infrastructure
- Scale through disciplined pilots

OT/ICS-Specific Considerations:
- Protocol integration in long-lifecycle devices (20-30 year lifespans)
- Memory-constrained hardware (4-32KB RAM on older PLCs)
- Regulatory timelines (NERC CIP, IEC 62351) misaligned with IT migration velocity
- Hardware root of trust via FPGA/TPM integration (SEALSQ QVault example)

### 4. Production Deployment Patterns

Hybrid KEM/KDF Approaches:
- Combine ML-KEM (Kyber) with classical ECDH for backward compatibility
- IETF PQC migration draft specifies hybrid key establishment
- Reduces risk during transition period

Code-Signing Migration:
- Linux Foundation Model Signing Project advancing
- Sigstore/Cosign integration for model signing
- SPDX 3.0 AI Profile for software bill of materials
- Critical for supply chain integrity in edge deployments
