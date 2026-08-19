# Matrix-Native FHE: The GL (Gentry-Lee) Scheme for Private AI

Status: STABLE
Created: 2026-08-02 (BUILD cycle, promoted from field report 20260802_matrix-native-fhe-gl-scheme.md)

## 1. Summary

The GL (Gentry-Lee) scheme is a 5th-generation fully homomorphic encryption (FHE) scheme co-authored by Craig Gentry (inventor of FHE, 2009 Godel Prize) and Yongwoo Lee (DESILO), designed from first principles for **matrix arithmetic** rather than polynomial arithmetic. It was accepted at IACR Crypto 2026 in two papers (core scheme + bootstrapping) and shipped commercially as the world's first GL-integrated FHE library by DESILO on 2026-04-28.

Its central claim: encrypted matrix multiplication (the dominant cost of encrypted neural-network inference and encrypted record linkage) reduces to **four matrix operations**, with a single key switch and **no reliance on ciphertext rotations or slot-coefficient transformations** — the two overheads that make CKKS-style schemes expensive for matrix workloads. This directly shifts the cost curve of privacy-preserving entity resolution and encrypted AI inference.

## 2. Technical Foundations

### 2.1 Cryptographic basis
- **Problem:** Ring-Learning with Errors (RLWE), the same lattice assumption underpinning CKKS and BFV.
- **Plaintext domain:** batched matrices over complex numbers AND integers — both supported natively.
- **Supported operations:** matrix multiplication, addition, Hadamard (element-wise) multiplication for batched matrices of various sizes.

### 2.2 Key innovation — atomic Ct-Ct matrix multiplication
- Encrypted matrix multiplication is expressed as an **atomic ciphertext-ciphertext (Ct-Ct) operation**.
- Per FHE.org 2026 presentation slides (Lee et al.), this reduces to **non-encrypted matrix-matrix multiplication** internally — the operation hardware was already optimized for.
- **Single key switching** per operation; no rotation-based decomposition, no per-element polynomial overhead.
- Flexible matrix sizes: batched layouts adapt to the shape of the workload rather than forcing a fixed SIMD slot geometry.
- Addition and Hadamard products are computed as-is, with minimal overhead.

### 2.3 Bootstrapping co-design
- The companion paper (ePrint 2026/956, "Efficient Bootstrapping in Fully Homomorphic Encryption for Matrix Arithmetic") exploits the scheme's linearity of slot-coefficient transformations (CtS and StC).
- These transformations are reformulated as **ciphertext-plaintext matrix multiplications**, an operation the GL scheme supports natively — removing the historical bootstrapping bottleneck for matrix FHE.
- Authors (from the Crypto 2026 accepted list): Eric Crockett, Craig Gentry, Hyojun Kim, Yeongmin Lee, Yongwoo Lee — Cornami; DESILO Inc.; DESILO Inc. and Inha University.

## 3. Chronology & Ecosystem

| Date | Event |
|---|---|
| 2025 (ePrint) | Core paper posted: "Fully Homomorphic Encryption for Matrix Arithmetic" (ePrint 2025/1935) |
| 2026 (FHE.org, Taipei) | GL scheme debuted publicly; co-authored by Gentry + DESILO researchers |
| 2026-04-28 | DESILO launched world's first FHE library integrating the GL scheme (v1.8.0) |
| 2026 (mid) | Two papers simultaneously accepted at IACR Crypto 2026 — core scheme + bootstrapping |
| 2026-08 | ePrint 2026/956 bootstrapping paper available; DESILO docs detail GL scheme (fhe.desilo.dev) |

Ecosystem notes:
- DESILO (Korean deep-tech) is the first commercial vendor with a GL-native library; pushes a PyTorch encoder intended to work with real transformer shapes.
- The GL scheme adds a datapoint in the cryptography/quantum industrial-competition map: US (Cornami/Gentry) + Korea (DESILO) cooperating in PET infrastructure.
- Hardware angle: GL raises the value of dense-matmul accelerators (GPU/FPGA/ASIC) — the tensor-core hardware used for LLM inference is the natural backend for matrix-native FHE.

## 4. Why It Matters: Two Workload Families

### 4.1 Encrypted AI inference (private AI)
- Neural network inference is dominated by matrix multiplication, attention, and pointwise nonlinearities.
- GL reduces encrypted matmul overhead by orders of magnitude versus CKKS polynomial rotations, making **encrypted attention layers** and **encrypted retrieval scoring** economically closer.
- Combined with ZKP-of-FHE (see fhe-zkp-hybrid-architectures wiki), agents could attest to encrypted matrix computations (attention layers, retrieval scoring) with far lower proof overhead.
- Local-to-frontier bridging: encrypted cascade inference on local hardware (RTX 3090) — GL's PyTorch bridge lowers friction for privacy-preserving local proxy queries of frontier models.

### 4.2 Privacy-preserving entity resolution (OSINT / FININT)
- The Fellegi-Sunter matching pipeline reduces to batched matrix algebra: pairwise similarity scores, blocking, and scoring matrices.
- GL's matrix-native FHE makes encrypted cross-jurisdictional record linkage economically closer — the exact "share breach-derived identity graphs without exposing PII" use case from data-breach OSINT analysis.
- This is a direct architectural isomorphism: **encrypted AI inference and encrypted entity resolution both reduce to batched matrix algebra** — one primitive, two applications.
- Complements the DP+SMPC hybrid framework (see privacy-preserving-entity-resolution-osint wiki): HE now outperforms MPC in raw single-server computation; MPC retains multi-party trust properties.

## 5. Open Questions / Attack Surface

1. **Cryptanalysis velocity.** Crypto 2026 double acceptance is validation, but cryptanalysis follows quickly. Are there attacks or parameter-regime improvements not yet public?
2. **Library maturity.** DESILO library 1.8.0+ status, cross-language support (C++/Python), hardware backends (GPU/FPGA); does the PyTorch encoder work with real transformer shapes at scale?
3. **Post-quantum security angle.** GL is RLWE-based like CKKS/BFV — matrix-native encoding affects the security/performance tradeoff (RLWE dimension, noise growth per matmul) but the lattice assumption itself remains PQ-adjacent.
4. **Noise growth per chained matmul.** Practical depth for deep networks depends on bootstrapping frequency; the CtS/StC-as-matmul trick lowers bootstrapping cost but circuit depth planning still matters.
5. **Verification.** ZKP-of-FHE over GL needs to be demonstrated on realistic matrix workloads, not toy shapes.

## 6. Cross-Domain Connections

- **Data Aggregation & Entity Resolution:** encrypted Fellegi-Sunter matching via matrix-native FHE — a direct productivity lever for the Palantir-thesis use case.
- **AI Agent Trust Infrastructure:** ZKP-of-FHE attestation for encrypted agent computation.
- **Hardware & Physical Computing:** dense-matmul FHE accelerators; tensor-core reuse from LLM inference.
- **Local-to-Frontier Bridging:** encrypted cascade/private proxy inference on local GPUs.
- **Geopolitics & Strategic Analysis:** Korea's DESILO as a Crypto-2026-validated FHE player in the cryptography/quantum industrial-competition map.
- **Financial Intelligence (FININT):** encrypted cross-institution pattern detection, complementing FL/FHE/SMPC in the alternative-data FININT stack.

## 7. Sources

### Primary
1. Gentry, Lee, et al., "Fully Homomorphic Encryption for Matrix Arithmetic" — IACR ePrint 2025/1935 (accepted at Crypto 2026).
2. Crockett, Gentry, Kim, Lee, Lee, "Efficient Bootstrapping in Fully Homomorphic Encryption for Matrix Arithmetic" — IACR ePrint 2026/956 (accepted at Crypto 2026).
3. DESILO PR: "DESILO and FHE Inventor Craig Gentry Introduce 5th-Generation 'GL' FHE Scheme for Private AI" (PR Newswire, FHE.org 2026 Taipei).
4. DESILO PR: "DESILO Launches World's First Fully Homomorphic Encryption Library Integrating 5th-Generation FHE Scheme GL" (PR Newswire, 2026-04-28).
5. DESILO PR: "DESILO's 5th-Generation FHE Scheme 'GL' Recognized by International Academic Community — Two Papers Simultaneously Accepted at IACR Crypto 2026".
6. Crypto 2026 Accepted Papers list (crypto.iacr.org/2026/acceptedpapers.php).
7. FHE.org 2026 Conference slides (0910_Lee.pdf) — atomic Ct-Ct matrix multiplication as operation.
8. DESILO blog: "GL 스킴 깊이 알기: 행렬을 위해 처음부터 다시 설계한 동형암호".

### Shared corpus grounding
- Exocortex field reports: 2026-06-08_homomorphic_encryption_gl_scheme.md — GL scheme facts, Crypto 2026 double acceptance, RLWE basis, four-matrix-op matmul, bootstrapping via ciphertext-plaintext matmul.
- Exocortex wiki: mpc-privacy-preserving-analytics-2026-draft.md (HE vs MPC tradeoff), privacy-preserving-entity-resolution-osint.md, fhe-zkp-hybrid-architectures.md, homomorphic-encryption-state-of-art.md, privacy-cryptography.md.
- Library grounding: Serious Cryptography (FHE fundamentals, RLWE context; no matrix-specific FHE coverage in the 355-book corpus).

## 8. Verification Notes

- Web facts verified against PR Newswire, ePrint, Crypto 2026 accepted list, and FHE.org slides (2026-08-02).
- Not independently benchmarked: GL throughput figures and noise-growth curves require the DESILO library runtime (future work).
