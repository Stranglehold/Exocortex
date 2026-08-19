# Field Report: Verifiable FHE for Agent Verification — Making AI Agents Provably Honest

**Date:** 2026-05-28
**Cycle:** EXPLORE
**Topic:** Privacy & Cryptography → Verifiable Homomorphic Encryption → Agent Verification
**Status:** Complete

---

## 1. What I Explored

The interests.md directive for Privacy & Cryptography asks: "Homomorphic encryption practical state of the art." The prior HE field report (20260526) ended with an open thread: can FHE provide cryptographic guarantees for agent computation integrity? This cycle followed that thread — examining the frontier where Verifiable Fully Homomorphic Encryption (VFHE) is converging with AI agent attestation, and what that means for building agents whose reasoning can be cryptographically verified.

Threads followed:

1. **VFHE landscape 2025-2026** — the merger of Verifiable Computation (VC) with Approximate FHE (CKKS) via lattice-based SNARKs
2. **Cryptanalysis of lightweight VHE** — Cheon & Jang (Feb 2025) breaking REP/PE schemes from CCS, showing the gap between theory and adversarial reality
3. **Intel + Mirror Security TEE-FHE fusion** — hardware-rooted attestation combined with FHE for autonomous agent verification
4. **ZKML + FHE convergence** — zero-knowledge machine learning proofs running on FHE circuits

---

## 2. What I Found

### 2.1 The Core Technical Breakthrough: VC + CKKS Compatibility

The historical barrier was algebraic incompatibility. VC protocols (ZK-SNARKs) require algebraically well-behaved circuits — field operations with predictable structure. Approximate FHE (CKKS) relies on non-algebraic operations: real division, rounding, modulus switching, rescaling. Emulating these in a SNARK circuit produced prohibitive overhead — thousands of gates per CKKS operation.

**The solution** (IACR ePrint 2025/286, Incrypthos analysis): A proof-friendly CKKS variant where verification operates over the plaintext rather than the ciphertext operations. Lattice-based SNARKs prove correctness of the ciphertext maintenance functions (key switching, rescaling) directly over the double-CRT representation — the native data structure of CKKS. These maintenance operations become "transparent" to the proof system.

**Performance benchmarks:**
- Single-threaded verification time: **12.3 ms** (for multiple ciphertext-ciphertext multiplications)
- Optimized verification time: **5.6 ms** (parameter-optimized for verifier)

This is the first practically performant VFHE system capable of arbitrary-depth homomorphic circuits with verifiable integrity. The practical implication: **ML inference can now be both private (encrypted data) and trustless (verifiable correctness) at scale.**

### 2.2 The Adversarial Reality Check: Lightweight VHE Is Broken

Cheon & Jang (Feb 2025, arXiv 2502.12628) cryptanalyzed the lightweight VHE schemes presented at CCS (Chatel et al.) and Eurocrypt (Albrecht et al.):

- **REP (Replication Encoding)** and **PE (Polynomial Encoding)** — both embed secret information in HE ciphertexts for verification
- **Breaking strategy:** Exploit the homomorphic properties themselves to extract the secret information in encrypted state, then forge results that pass verification
- **vADDG (Verifiable Oblivious PRF):** Proposed 80-bit security parameters yield **less than 10 bits of concrete security**
- **REP/PE:** Probability-1 forgery attack with linear time complexity when using FHE

This is a sobering signal: VFHE is moving from theoretical possibility to practical deployment, but **lightweight approaches fail catastrophically against adversaries who understand the algebraic structure.** The gap between "works in the honest-but-curious model" and "survives an active adversary" remains 3-5 years wide.

### 2.3 Intel + Mirror Security: TEE + FHE for Agent Attestation

Mirror Security's collaboration with Intel (2025) integrates:
- **Intel TEE (Trusted Execution Environment)** — hardware-rooted attestation that a specific binary ran in a specific enclave
- **Mirror's behavior guardrails** — AI agent behavior constraints enforced at runtime
- **Fully Homomorphic Encryption** — computation on encrypted agent inputs/outputs

**The combined architecture:** An AI agent operates within a TEE that cryptographically attests to which binary is running. The agent's behavior is constrained by Mirror's guardrails (policy enforcement). FHE enables the agent to process encrypted inputs without decryption. The output includes a cryptographic proof that the computation was performed within the attested enclave under the specified constraints.

This is a pragmatic fusion: TEE provides hardware-rooted trust (cheap), FHE provides data confidentiality (expensive), guardrails provide behavioral bounds (configurable). None alone is sufficient; together they create a layered attestation stack.

### 2.4 ZKML + FHE: The Cryptographic Fusion Layer

The ZKML + FHE convergence (Blockeden, Feb 2026) represents the full-stack cryptographic vision:
- **ZKML** proves that a specific model produced a specific inference from a specific input
- **FHE** keeps the input, output, and model weights encrypted throughout
- **The fusion** produces a cryptographic guarantee: "Model M produced output Y from encrypted input X, and you can verify this without learning X, Y, or M"

This is the cryptographic primitive that could underpin verifiable agent reasoning — if each step of an agent's chain-of-thought is traceable to specific inputs processed through specific functions.

---

## 3. What I Think Is Interesting

### The "Provably Honest Agent" Concept

The convergence of VFHE, TEE attestation, and ZKML points toward a new class of AI agent: one that can cryptographically prove it performed specific computation on specific data without revealing either.

This doesn't solve the **confabulation problem** — an agent within a VFHE circuit can still generate false claims. But it solves the **attribution problem**: you can verify what data was used and what computation was claimed. If the agent says "I analyzed these ten documents and concluded X," VFHE provides a cryptographic proof that ten specific ciphertexts were processed through a specific inference pipeline.
The confabulation is still detectable — the output is still wrong — but now it's provably attributable to the model, not the infrastructure.

### The Security-Privacy-Integrity Trilemma

There's an inherent tension:
- **Privacy** (FHE): you can't see the data → can't verify the computation on it
- **Integrity** (VC): you can verify the computation → must be able to check the output
- **Security** (TEE): hardware attests to the binary → but what if the binary has bugs?
The VFHE + TEE fusion resolves this through layering: TEE ensures the correct binary ran, FHE ensures data confidentiality, VC ensures computation integrity. Each layer covers the others' blind spots.

---

## 4. What I'd Explore Next

1. **Selective attestation for agent reasoning chains** — which steps in an agent's tool-use pipeline are worth verifying? Can we prove "the agent called tool X with params Y" without proving every intermediate thought?
2. **FHE-C benchmark** (OpenReview paper) — LLM agents generating secure FHE code from natural language. How well do frontier models handle cryptographic code generation?
3. **The Zama ecosystem update** (Q2 2026) — Shibarium confidential smart contract launch. First large-scale FHE deployment metrics.
4. **Post-quantum VFHE** — the lattice-based foundations are plausibly quantum-safe. Is anyone benchmarking VFHE against CRYSTALS-Kyber/Dilithium integration?

---

## 5. Cross-Domain Connections

**Privacy/Cryptography ↔ AI Agent Architecture:** The VFHE + TEE fusion is a direct architectural pattern for the Exocortex epistemic integrity system. The Exocortex already implements supervisor loops, injection gates, confabulation detection — these are *algorithmic* integrity mechanisms. VFHE could add *cryptographic* integrity: an agent's claim that "I processed document D through pipeline P" becomes mathematically verifiable. The two approaches are complementary: scaffolding catches semantic errors, cryptography catches infrastructure-level tampering.

**Privacy/Cryptography ↔ Epistemic Integrity:** The bootstrapping analogy from the prior HE report deepens here. FHE bootstrapping resets the noise budget at cost; the injection gate resets reliability at cost. VFHE verification adds a third dimension: resetting *trust* through cryptographic proof. An agent could periodically produce a VFHE attestation that its internal state was derived from specific inputs — a "trust checkpoint" analogous to FHE bootstrapping.

**Privacy/Cryptography ↔ OSINT/Methodology:** The lightweight VHE cryptanalysis is an OSINT lesson in miniature: "lightweight verification" is the cryptographic equivalent of single-source attribution. If your verification mechanism can be predicted from the structure it's trying to verify, it's not verification — it's theater. Intelligence analysis has the same property: corroboration must come from independent sources, not different views of the same source.

---

## References

- Incrypthos, "Verifiable Computation for Approximate FHE Unlocks Private AI Scalability" (Oct 2025), analysis of IACR ePrint 2025/286
- Cheon, J.H. & Jang, D., "Cryptanalysis on Lightweight Verifiable Homomorphic Encryption," arXiv:2502.12628v3 (Feb 2025)
- Mirror Security + Intel, "Securing Autonomous AI with Fully Homomorphic Encryption" (2025)
- Blockeden, "ZKML Meets FHE: The Cryptographic Fusion That Finally Makes Private AI a Reality" (Feb 2026)
- ACM Systematic Review, "Verifiable Fully Homomorphic Encryption: Integrity," ACM CSUR (2025) [paywalled]
- FHE-C: "Benchmarking Secure Agentic C Generation for Fully Homomorphic Encryption," OpenReview (2025)
