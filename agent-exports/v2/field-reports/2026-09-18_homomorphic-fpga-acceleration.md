# Field Report: FPGA Acceleration of Homomorphic-Secure Compute
**Date:** 2026-09-18
**Cycle:** EXPLORE (idle-time)
**Topic:** Hardware & Physical Computing → FPGA acceleration of homomorphic-encrypted computation
**Cross-domain bridge:** Privacy & Cryptography (FHE / secure inference) ↔ Hardware & Physical Computing (FPGA)

---

## 1. What I Explored

Jake's Hardware & Physical Computing interest had been explored ~8 times already (LUT-LLM memory-based compute, edge AI accelerators, FPAI pipeline, ZKP+FPGA convergence) — but never on **homomorphic encryption hardware acceleration**. The corpus gap was clear from search_memory/search_all: no page or report covered secure computation ON FPGA. I pivoted to the newest live thread — fully homomorphic encryption (HE) executed directly on reconfigurable hardware.

The anchor paper is **FAME** (*arXiv 2512.15515*, Xu, Kannan & Prasanna, USC): "FPGA Acceleration of Secure Matrix Multiplication with Homomorphic Encryption" — the first FPGA accelerator specifically tailored for HE matrix multiplication under the CKKS scheme.

## 2. What I Found

**The bottleneck is memory, not compute.** In FAME, homomorphic linear transformation (HLT) is >95% of runtime. HLT is dominated by two things: (1) ciphertext rotations — among the most expensive HE operations; and (2) massive off-chip DRAM traffic from intermediate ciphertexts.

**The cost model is decisive.** For a modest 64×64 matrix (N=2¹³), one ciphertext occupies only 0.43 MB — comfortably fits in CPU cache. But practical parameter sets push this to 6.7 MB and 27 MB per ciphertext, making total on-chip memory demand ~61 MB and ~255 MB respectively — exceeding what even large FPGAs can hold. At these scales each KeySwitch can involve hundreds of MBs off-chip traffic.

**MO-HLT datapath.** FAME's core innovation is a hardware/software co-designed datapath that: (a) *hoists* sub-operations (Decomp/ModUp/ModDown) outside the rotation loop, sharing them across rotations; (b) fuses Rescale with ModDown to skip intermediate modulus; and (c) operates at the **limb level** rather than full-ciphertext level — reversing the loop order so limb iteration becomes outer. This reduces on-chip demand to ~29 MB for Set-C.

**Eval results.** FAME implemented in Verilog, placed on Alveo U280 (1,304K LUTs, 2,607K FFs, **43 MB** on-chip SRAM, 9,024 DSPs). Compared against reimplemented CKKS CPU baselines (Pyfhel) on an Intel Xeon Gold 6326. FAME completes MM of two **160×160 encrypted matrices in ~3 seconds = 1337× faster** than the best CPU implementation, and **221× average speedup** across all matrix shapes/parameter sets.

**Critical differentiator from prior work:** Existing HE acceleration (works [10],[11],[12]) only encrypts *inputs* — the model stays plaintext. FAME's threat model encrypts **both input matrices**, so both model and data remain encrypted during inference. This is materially stronger privacy.

**Supporting corpus threads:** cycle 606's ZKP+FPGA convergence report (reconfigurable substrate for polynomial commitments + NTT) and LUT-LLM memory-based compute; prior HE works encrypt inputs only; Mirror Security already runs FHE ML inference on GPU at enterprise scale — the contrast that shows FPGA's niche is power/latency-constrained edge where GPUs don't fit.

## 3. What I think is interesting

The pattern that emerged: **on-chip memory density, not arithmetic throughput, is the binding constraint across a whole family of accelerator domains.**

FAME's cost model (Eq. 17-24) shows on-chip SRAM size dictates what HE parameter sets are feasible — which mirrors the V80-vs-A100 finding from cycle 606 (V80 has 14.9× more on-chip memory than A100 despite far lower TOPS) and LUT-LLM's insight that table-lookup compute is driven by lookup-table capacity, not ALU throughput.

This suggests a *unified acceleration substrate*: one FPGA fabric can serve three distinct cryptographic/compute workloads — polynomial commitments (ZKP), homomorphic rotations (CKKS HLT), and table lookups (LLM) — all governed by the same memory-density constraint. The shared primitive is NTT/rotation; FAME and ZKP both fight off-chip traffic on rotation-heavy paths.

FAME's choice of CKKS (real-number arithmetic) over BGV/BFV (integer) means it targets ML inference specifically — this closes a privacy gap: a cloud can run an encrypted model against encrypted inputs without the data owner ever exposing plaintext. This is exactly what utility-edge and government-contract pipelines want.

## 4. What I'd explore next

- **Homomorphic acceleration of key operations beyond MM**: how does FAME's MO-HLT datapath generalize to HE convolution, attention, or GEMM for transformer inference? The rotation-count formulas (d_{U^σ}=2min(m,l)-1 etc.) suggest rectangular-matrix shapes cost more rotations — relevant to efficient attention.
- **Lattice-based ZKP on FPGA**: FAME uses NTT/rotation; zk-STARKs/zk-SNARKS use the same polynomial primitives. Is there a unified reconfigurable substrate for both FHE and SNARK proof generation?
- **Analog compute-in-memory vs FAME digital HE**: the corpus already has analog CIM (Peking Univ geometric-ratio encoding, EnCharge EN100) — comparing analog in-memory encryption vs FPGA-based FAME digital acceleration could reveal which dominates at edge power budgets.
- **Post-quantum crypto on FPGA** beyond HE: Kyber/Dilithium lattice signatures, and their interplay with ZKP.

## 5. Cross-domain connections

- **Privacy & Cryptography ↔ Hardware**: FHE hardware acceleration bridges directly to metadata-resistant communication (Signal/Briar/Cwtch) — secure compute at the edge needs both privacy-preserving inference AND encrypted transport.
- **Electric Utility & Critical Infrastructure**: DOE's $45M utility AI projects + grid edge endpoints = a deployment surface for FAME-style encrypted ML inference on substation sensors. Edge ML inference behind encryption is exactly what power-grid AI needs (secure-at-rest+in-transit+in-compute).
- **Data Aggregation & Entity Resolution**: government contract records and campaign-finance data are high-sensitivity; FAME enables entity-resolution pipelines that run fully encrypted — the same privacy guarantee that I found OpenSanctions mandates via FinCEN's proposed beneficial-ownership ER rule.
- **ZKP/FPGA unified substrate (cycle 606)**: FAME is now the third leg of the reconfigurable-compute family alongside ZKP proof generation and LUT-LLM memory compute.
