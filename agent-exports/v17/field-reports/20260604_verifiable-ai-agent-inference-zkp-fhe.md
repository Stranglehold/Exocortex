# Field Report: Verifiable AI Agent Inference — ZKP + FHE Integration

**Date:** 2026-06-04
**Topic:** Privacy & Cryptography — Cryptographic Verification of AI Agent Reasoning
**Type:** EXPLORE cycle

---

## 1. What I Explored

This report explores the emerging research frontier where cryptographic primitives (ZKPs and FHE) intersect with AI agent architecture to enable **verifiable, private agent inference** — where an agent can cryptographically prove its reasoning was honest without revealing sensitive model weights or user data.

This is a previously unexamined sub-thread within Privacy & Cryptography. Prior field reports covered ZKP infrastructure (May 27), institutional adoption + zkLLM (May 29), and FHE hardware acceleration (June 1). None examined how these primitives compose specifically for AI agent verification — the architecture pattern of combining FHE for data privacy with ZKPs for computational integrity within a single agent inference pipeline.

Threads followed:
- Zylos Research: "Zero-Knowledge Proofs for AI Agent Verification and Privacy" (March 2026)
- ArXiv 2502.18535v2: "A Survey of Zero-Knowledge Proof Based Verifiable Machine Learning" (March 2026)
- Frontiers in Blockchain: "An agentic AI marketplace for prelitigation analyses with ZKP" (2026)
- BlockEden: "ZKML Meets FHE: The Cryptographic Fusion" (February 2026)
- ArXiv 2503.22573: "A Framework for Cryptographic Verifiability of End-to-End AI Pipelines" (2025)
- Calibraint: "Zero Knowledge Proof AI in 2026"

---

## 2. What I Found

### 2.1 The Core Architecture: FHE + ZKP Complementarity

Homomorphic encryption (HE) and zero-knowledge proofs (ZKPs) play **complementary, non-overlapping roles** in verifiable inference:

| Layer | Primitive | Function |
|-------|-----------|----------|
| Data Confidentiality | FHE | Computation on encrypted inputs without server seeing plaintext |
| Computational Integrity | ZKP | Cryptographic attestation that output was produced by agreed-upon model |
| Selective Disclosure | ZKP | Prove specific properties (e.g., "no confidential data used") without full proof |

This separation avoids the trap of forcing one primitive to handle both privacy and verifiability simultaneously — a pattern that can't achieve both high throughput and full public verifiability. Frameworks like **pvCNN** (per the arXiv 2502.18535 survey) combine HE for intermediate computation protection with ZK proofs certifying CNN execution consistency. **Drynx** layers HE, differential privacy, and ZKPs so confidentiality, secure aggregation, and public verifiability are independently handled.

### 2.2 Practical Deployment Maturity

**What's achievable today:**

| System | What It Proves | Proving Time |
|--------|---------------|------------|
| DeepProve-1 (Lagrange Labs) | Full GPT-2 inference | Production-ready (medium-scale) |
| zkGPT | GPT-2 full inference | < 25 seconds |
| zkPyTorch (March 2025) | VGG-16 (138M params) | 2.2 seconds |
| EZKL (GPU-accelerated) | Various ML models | 5-10x speedup vs CPU |

**What's not yet possible:** Frontier models (~100B+ parameters) remain orders of magnitude beyond current ZK proof generation capacity. Full end-to-end pipeline verification (tokenization -> embedding -> inference -> decoding -> tool calls) is unimplemented.

### 2.3 Three Architectural Patterns for Agent Verification

The literature converges on three deployment patterns (synthesized from Zylos, arXiv 2502.18535, and Calibraint):

**Pattern 1: Async Proof Generation**
- Agent responds immediately without proof
- Background prover generates ZK proof over seconds/minutes
- Downstream consumers verify proof before acting on high-stakes results
- This is the dominant pattern for any model beyond small-scale

**Pattern 2: Tiered Verification**
- Low-stakes outputs -> no proof or simple hash commitments
- Medium-stakes -> on-demand proof generation
- High-stakes -> async ZK proofs mandatory
- Critical (small-model) decisions -> synchronous proof before any action
- Matches cost to risk — essential when proof generation costs 10-100x the inference itself

**Pattern 3: Proof-of-Policy Compliance**
- Rather than proving full inference, prove specific policy-relevant claims:
  - "The response did not include CONFIDENTIAL data"
  - "The agent consulted only authorized data sources"
  - "No restricted API was called during reasoning"
- Much smaller/faster than full inference proofs
- Suits regulated industries (finance, healthcare, legal)

### 2.4 The ZK-MCP Pattern

A fourth emerging pattern combines ZKPs with the Model Context Protocol (MCP) for privacy-preserving audit trails:
- Agents commit to communications via hashes
- Later prove compliance without revealing content
- Enables regulatory audit without surveillance
- Particularly relevant for multi-agent systems where interaction logs are sensitive

### 2.5 Remaining Gaps

1. **Model size gap**: GPT-2 (~124M params) is provable; GPT-4-class models (~1T+ params) are not
2. **End-to-end pipeline**: No system proves the full inference stack including tokenization and tool calls
3. **Multi-agent proof composition**: Recursive proof aggregation (Plonky2/3) exists but hasn't been integrated into agent frameworks
4. **Key management**: No standardized IAM for ephemeral agent credentials — agents need identities to sign proofs
5. **Real-time verification**: Current proving times preclude synchronous verification for most practical agent applications

---

## 3. What I Think Is Interesting

### 3.1 The Exocortex Architecture Is Already Aligned

The three-tiered verification pattern (async/tiered/policy-compliance) maps structurally onto Exocortex's existing architecture:

- **Injection gate** -> could consume ZK proofs as an additional epistemic integrity signal (source reliability + cryptographic attestation = stronger than either alone)
- **Entropy-as-signal** -> HE operations alter the entropy surface of computation; Brito's HSSMs (arXiv 2605.16647) achieving exact plaintext-equivalent accuracy through encrypted paths suggests entropy monitoring could be extended to audit encrypted agent computations
- **Deterministic scaffolding** -> the scaffolding layer is more amenable to ZK proving than LLM inference (deterministic logic, smaller state space); you could prove scaffolding decisions with current ZK technology while async-proving the LLM portions
- **Supervisor loop** -> tiered verification maps perfectly: supervisor receives agent output, verifies proof for high-stakes decisions, escalates when proof fails or is absent

### 3.2 The FHE Hardware Breakthrough Changes the Equation

The previous FHE hardware field report (June 1) documented Cheddar GPU library achieving sub-25ms CNN inference on RTX 5090, matching DARPA DPRIVE ASIC targets. Combined with this report's ZKP advances:

- **FHE provides data privacy at near-plaintext speed** (for specific workloads)
- **ZKPs provide computational integrity**
- **Together** they enable a scenario where an untrusted cloud provider runs agent inference on encrypted user data AND proves the model was executed honestly — without ever seeing the data or the model weights

This is the holy grail of private, verifiable AI. We're not there yet for frontier models, but the architectural pattern is clear and the components are maturing independently.

### 3.3 Proof-of-Policy Is the Pragmatic Bridge

Full inference proofs for large models remain years away. But proof-of-policy compliance — proving specific properties about agent behavior rather than full computation — is achievable today. This is the practical bridge: deploy agents with policy proofs now, add full inference proofs as they mature.

For Exocortex, this means proofs like:
- "The agent did not execute any code without user approval"
- "The agent consulted only approved data sources"
- "The agent's output was not modified after generation"

These are smaller, faster proofs that could be integrated into the injection gate as verifiable claims.

### 3.4 The Multi-Agent Composition Problem

When agents delegate to subordinates, how do you verify the full chain of trust? Agent A delegates to Agent B, which calls Agent C — each with their own proofs. The recursive proof composition work (Plonky2/3) enables constant-size aggregation of multiple proofs. This is directly applicable to Exocortex's call_subordinate pattern: a superior agent could produce a single aggregated proof that its response (including all delegated work) was computed honestly.

---

## 4. What I'd Explore Next

1. **Benchmark zkPyTorch + EZKL on Exocortex-scale models**: Can we prove a 7B-parameter model (e.g., Mistral 7B used as local agent) within acceptable latency for async verification?
2. **Proof-of-policy prototype for Exocortex**: Define 3-5 policy claims (e.g., no unauthorized code execution, no fabricated metrics) and implement ZK proofs for them — lightweight, practical first step
3. **FHE + ZKP integration audit**: Survey existing hybrid implementations (Drynx, pvCNN) for architectural patterns transferable to agent verification
4. **Scaffolding ZK-proving feasibility**: The deterministic scaffolding layer (tool routing, supervisor decisions, gate enforcement) is more provable than LLM inference — estimate proving costs for scaffolding operations
5. **Multi-agent proof composition**: Can Plonky2/3 recursive proofs aggregate subordinate agent proofs into a single superior proof? This would enable end-to-end verifiability of complex agent chains

---

## 5. Cross-Domain Connections

1. **AI Agent Architecture & Local Inference**: The three-tiered verification pattern maps directly onto Exocortex's deterministic scaffolding + LLM reasoning + epistemic integrity architecture. The injection gate is the natural consumer of cryptographic attestations.

2. **Epistemic Integrity (Exocortex)** : ZK proofs add a new dimension to source reliability scoring — cryptographic attestation is a stronger signal than any behavioral heuristic. A proof-verified output should carry maximum confidence in the injection gate's reliability scoring.

3. **Bridging Local-to-Frontier Performance**: FHE + ZKP integration enables a scenario where local models (running on user-controlled hardware) can prove their inference integrity to external consumers — making local-first architectures viable for high-stakes applications that currently require trusted cloud providers.

4. **OSINT Methodology**: Verifiable agent inference directly addresses the CROWDINT verification problem identified in the SIGINT-OSINT convergence report (June 1). If civilian sensor network agents produce ZK proofs of their analysis pipeline, downstream consumers can verify without trusting the operator.

5. **Hardware & Physical Computing**: The FHE hardware acceleration trajectory (FPGAs, TPUs, PIM) is converging with ZKP hardware acceleration (GPU-accelerated EZKL, ASIC proposals). A unified FHE+ZKP accelerator would be a transformative hardware primitive for private, verifiable AI.

6. **Counterintelligence Analysis**: Proof-of-policy compliance could detect agent deception: if an agent claims it followed a specific analysis methodology, a ZK proof of policy compliance could verify that claim cryptographically — closing a vector for adversarial agent manipulation.

7. **History of Intelligence Operations**: The verification problem in multi-agent chains mirrors the intelligence cycle's "collection -> analysis -> dissemination" trust problem. SIGINT learned that intermediate processing introduces trust degradation; ZK proofs offer cryptographic guarantees against this degradation.

---

## Sources

1. Zylos Research. "Zero-Knowledge Proofs for AI Agent Verification and Privacy." March 18, 2026. https://zylos.ai/research/2026-03-18-zero-knowledge-proofs-ai-agent-verification/
2. ArXiv 2502.18535v2. "A Survey of Zero-Knowledge Proof Based Verifiable Machine Learning." March 29, 2026. https://arxiv.org/html/2502.18535v2
3. ArXiv 2503.22573. "A Framework for Cryptographic Verifiability of End-to-End AI Pipelines." 2025. https://arxiv.org/html/2503.22573v1
4. Frontiers in Blockchain. "An agentic AI marketplace for prelitigation analyses with ZKP." 2026. https://www.frontiersin.org/journals/blockchain/articles/10.3389/fbloc.2026.1770848/full
5. BlockEden. "ZKML Meets FHE: The Cryptographic Fusion That Finally Makes Private AI Possible." February 5, 2026. https://blockeden.xyz/blog/2026/02/05/zkml-fhe-fusion-privacy-preserving-ai-blockchain-holy-grail/
6. Calibraint. "Zero Knowledge Proof AI in 2026: Secure, Breakthrough Verifiable AI Without Model Exposure." 2026. https://www.calibraint.com/blog/zero-knowledge-proof-ai-2026
