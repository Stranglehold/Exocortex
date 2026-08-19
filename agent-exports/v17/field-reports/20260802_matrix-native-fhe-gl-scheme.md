# FIELD REPORT: Matrix-Native FHE — The GL (Gentry-Lee) Scheme and Encrypted Matrix Workloads

**Date**: 2026-08-02
**Cycle**: EXPLORE 986
**Topic**: Privacy & Cryptography > Homomorphic encryption practical state of the art
**Sub-thread**: Gentry-Lee (GL) scheme — fifth-generation FHE, matrix-native encoding, Crypto 2026 validation
**Corpus baseline**: v16/v17 HE state-of-art wiki + field reports (20260526-20260710), privacy-cryptography.md, fhe-zkp-hybrid-architectures.md, privacy-preserving-entity-resolution-osint.md (2026-07-18)

---

## 1. What I Explored

The least-recently-explored active interest was Privacy & Cryptography (last HE coverage 2026-07-10; last dedicated HE field report 2026-06-08). The shared corpus already had strong FHE baseline coverage: CKKS/BFV/BGV/TFHE taxonomy, DARPA DPRIVE hardware, enterprise viability thresholds, and a 2026-07-18 wiki page on privacy-preserving entity resolution (PPER) built on FHE/MPC/differential privacy.

I followed a specific thread not yet covered in depth: **the Gentry-Lee (GL) scheme**, a fifth-generation FHE scheme co-invented by FHE creator Craig Gentry (DESILO + Gentry + Yongwoo Lee). Its defining design goal: native matrix arithmetic, which is the computational primitive underpinning both neural network inference (attention matrices, MLP layers) and entity resolution (blocking keys, similarity scoring, embedding distances).

Key timeline assembled from web sources:
- **2026-03-08**: GL scheme unveiled at FHE.org 2026 Conference (Taipei), positioned as 5th-gen FHE for private AI
- **2026-04-28**: DESILO launched the world's first FHE library integrating GL
- **2026 (Crypto 2026)**: Two papers simultaneously accepted — the GL scheme paper and an efficient bootstrapping companion — an unusual double-validation of a new scheme
- **2026 ePrint 2026/956**: Efficient bootstrapping in FHE for matrix arithmetic (GL), exploiting linearity of CtS/StC slot-coefficient transformations formulated as ciphertext-plaintext matrix multiplications
- **2026 ePrint 2026/811**: Low-depth bootstrapping for matrix-native FHE, acknowledging that CKKS is vector-oriented and matrix multiplication is not represented natively

---

## 2. What I Found

### 2.1 GL Scheme Mechanics (from DESILO FHE library docs)

- GL encrypts **multiple square matrices** per ciphertext — the encoding unit is the matrix, not the vector
- Native operations include matrix multiplication (with a separate `MatrixMultiplicationKey`), addition, Hadamard multiplication, rotations, transposition, and complex-conjugate transpose
- The library includes a PyTorch tensor encoder (`encode_pytorch_tensor`, `encode_to_plain_matrix`) — a direct bridge to ML frameworks
- Practical API structures (plain matrix, ciphertext, decrypted share) mirror production library design rather than research-only code

### 2.2 Why Matrix-Native Encoding Matters

Conventional FHE (CKKS/BFV) follows a **vector SIMD model**: plaintext slots carry vectors, and matrix multiplication requires rotations and diagonal extraction — many ciphertext rotations per matmul. The GL design moves the cost structure: matrix multiplication becomes a native, keyed operation. Bootstrapping research (ePrint 2026/956) further exploits the linearity of slot-coefficient transforms, framing CtS/StC as ciphertext-plaintext matrix multiplications — bootstrapping co-designed for the matrix-native algebra rather than bolted on.

This is a scheme-level answer to the field's standing critique: FHE is 'matrix-hostile'. CKKS can do encrypted inference but pays heavy rotation costs; GL re-architects the encoding so the dominant workload is the native operation.

### 2.3 Academic Validation Signal

Two simultaneous Crypto 2026 acceptances (GL scheme + bootstrapping companion) plus two 2026 ePrint papers (956, 811) focused on GL-class bootstrapping indicate the scheme is being taken seriously enough for cryptanalytic and systems follow-up. That is the validation pattern that separates 'press release crypto' from research traction.

### 2.4 Honest Gap

The 355-book Exocortex library has only general crypto textbooks (Serious Cryptography, A Graduate Course in Applied Cryptography) — no deep FHE monograph, so no book-level citation to anchor the FHE performance claims. Web/arXiv evidence carries the load here. The library is strong on the PPER side via DP/MPC texts but thin on FHE specifics — this is a known corpus gap worth noting in MAINTAIN.

---

## 3. What I Think Is Interesting

The corpus already described PPER as a **dual-constraint problem**: blocking (cheap, approximate) done in plaintext; matching (expensive, exact) done in FHE; and noted Fellegi-Sunter probabilistic matching must be expressed as arithmetic circuits compatible with BFV/CKKS. The GL scheme changes the shape of that second constraint:

1. **Entity matching is matrix-dominated.** Batch similarity scoring between two block's records is a pairwise matrix computation (Jaccard/edit-distance/embedding distances). Under vector FHE, that's rotation-heavy. Under GL, the pair matrix is the native unit — the cost curve of encrypted matching shifts from 'possible but expensive' toward 'practical for larger blocks'.

2. **The bootstrapping co-design matters more than raw encode speed.** The ePrint 2026/956 result (CtS/StC as ciphertext-plaintext matmuls) makes bootstrapping itself a GL-native operation. For deep pipelines — multi-hop matching, iterative refinement, graph operations — bootstrapping cost is the binding constraint. A matrix-native bootstrap reduces the historical '~80% of compute in bootstrapping' penalty for exactly the workloads entity resolution and ML inference share.

3. **Encrypted AI inference and PPER are converging on the same primitive.** Attention matrices (transformer), pair-similarity matrices (entity matching), and adjacency-style operations (graph analytics) all reduce to batched matrix algebra. GL's PyTorch tensor encoder signals the vendor's intent: make FHE a backend for ML frameworks. If that lands, PPER systems that already use embedding-based matching get a natural privacy path without custom crypto.

4. **Early-adoption optics vs. research traction.** DESILO is a Korean deep-tech vendor; press coverage alone would be weak evidence. The Crypto 2026 double acceptance + independent ePrint bootstrapping papers are the stronger signal — cryptographers are investing in GL-class schemes. Benchmark numbers from DESILO remain vendor self-reported; independent replication isn't public yet.

---

## 4. What I'd Explore Next

1. **Independent GL benchmarks** — track for third-party evaluations of GL matmul vs CKKS-with-rotations for representative matmul shapes (attn heads, embedding dims, block sizes). Watch IACR/Crypto 2026 proceedings for the accepted papers.
2. **GL + PPER concrete cost model** — simulate a Fellegi-Sunter blocking-then-matching pipeline: plaintext blocking, GL-encrypted matching for a block of size n; compare ciphertext sizes and bootstrapping counts vs CKKS baseline.
3. **Crypto 2026 full proceedings** — are there attacks or improvements on GL not yet public? Double acceptance is validation, but cryptanalysis follows quickly.
4. **FHE library maturity** — DESILO library 1.8.0+ status, cross-language support, hardware backend (GPU/FPGA) claims; whether the PyTorch encoder works with real transformer shapes.
5. **Post-quantum angle** — GL is lattice-based like CKKS/BFV; check whether matrix-native encoding affects the PQ security/concrete parameter tradeoff (RLWE dimension, noise growth per matmul).

---

## 5. Cross-Domain Connections

- **Data Aggregation & Entity Resolution** (Jake's Palantir thesis): The GL scheme's matrix-native FHE directly strengthens privacy-preserving entity resolution — the exact 'share breach-derived identity graphs without exposing PII' use case from the 20260527 data-breach OSINT report. Encrypted batch matching across jurisdictions becomes economically closer.
- **Hardware & Physical Computing**: FHE matrix-native schemes raise the value of dense-matmul hardware (GPU/FPGA/ASIC, e.g., DPRIVE trajectory). The same tensor-core hardware that accelerates LLM inference is the natural backend for GL-type FHE.
- **AI Agent Trust Infrastructure**: VFHE near-term goal was verifying encrypted agent computation. Matrix-native FHE + ZKP-of-FHE (fhe-zkp-hybrid-architectures wiki) would let agents attest to encrypted matrix computations (attention layers, retrieval scoring) with far lower proof overhead.
- **Local-to-Frontier Bridging**: Encrypted cascade inference on local hardware (RTX 3090) — GL's PyTorch bridge lowers the friction for privacy-preserving local proxy queries of frontier models.
- **Geopolitics & Strategic Analysis**: Korea's DESILO becoming a Crypto 2026-validated FHE player adds a datapoint to the cryptography/quantum industrial-competition map (US/China/Korea in PET infrastructure).

---

## 6. Sources (web)

1. DESILO FHE Library docs — GL scheme (fhe.desilo.dev/1.8.0/gl_scheme)
2. IACR ePrint 2026/956 — Efficient Bootstrapping in FHE for Matrix Arithmetic (GL)
3. IACR ePrint 2026/811 — Low-Depth Bootstrapping for Matrix-Native FHE
4. DESILO PR — GL recognized by international academic community; two papers at Crypto 2026
5. DESILO + Craig Gentry PR — 5th-generation GL FHE scheme for private AI (FHE.org 2026, Taipei)
6. Yahoo Finance — DESILO launches world's first GL-integrated FHE library (2026-04-28)

*Corpus baseline: Exocortex wiki privacy-cryptography.md, homomorphic-encryption-state-of-art.md, fhe-zkp-hybrid-architectures.md, privacy-preserving-entity-resolution-osint.md; field reports 20260526-20260710 HE series.*
