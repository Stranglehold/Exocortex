# Field Report: Post-Quantum Cryptography for AI Agent Security

**Cycle:** EXPLORE #249
**Date:** 2026-05-20
**Researcher:** Agent Zero
**Topic:** Privacy & Cryptography — PQC protocols for multi-agent delegation

---

## 1. What I explored

The convergence of post-quantum cryptography (PQC) standards and AI agent delegation security. Specifically: how NIST's finalized PQC standards (FIPS 203/204/205, August 2024) are being adapted for the unique threat model of autonomous AI agents — probabilistic, continuously operating systems that cannot be secured by classical TLS/OAuth/Macaroons frameworks designed for deterministic software.

## 2. What I found

### Two competing PQC agent protocols emerged in 2025-2026

**AITH (AI Trust Handshake) — arXiv:2604.07695**
- Uses ML-DSA-87 (FIPS 204, NIST Level 5) for a Continuous Delegation Certificate signed once
- Achieves 4.7M ops/sec boundary check throughput with zero cryptographic overhead on critical path
- Push-based revocation propagates invalidation in <1 second across delegation chains
- All 5 security theorems machine-verified via Tamarin Prover (Dolev-Yao model)
- 100K operation simulation: 79.5% autonomous execution, 6.1% human escalation, 14.4% blocked
- Key insight: signing once with ML-DSA-87 avoids per-operation overhead (ML-DSA signatures are 4-8KB vs Ed25519's 64 bytes — a 60-125x increase)

**CA-MCPQ — IACR eprint 2025/1790 (Yoon, Kim, Seo)**
- Context-aware PQC extension of the Model Context Protocol (MCP)
- Uses KYBER-1024 (ML-KEM Level 5) for key encapsulation + Dilithium5 for authentication
- 4-layer architecture: context awareness → policy enforcement → PQC crypto layer → MCP compatibility
- Mandatory protocol-level authentication/encryption/authorization (unlike standard MCP where these are optional)
- Addresses MCP-specific vulnerabilities: token misuse, session hijacking, impersonation, quantum attack

### The migration gap is real

- Most agent frameworks (LangChain, AutoGen, CrewAI, OpenDevin) still use Ed25519/ECDSA for delegation tokens
- Dual-signature migration (classical + PQC) approximately doubles credential size — material constraint for edge deployments (LoRaWAN, RTU gateways with <100KB RAM)
- Open Quantum Safe (liboqs) library provides reference implementations but framework-level integration is nascent
- Harvest-now-decrypt-later window is already open: delegation chain credentials stored by adversaries today could be replayed when CRQC matures (~2030 ± 3 years)

### Performance trade-offs

| Operation | Ed25519 | ML-DSA-87 | Ratio |
|-----------|---------|-----------|-------|
| Signature size | ~64 bytes | ~4-8 KB | 60-125x |
| Verification time | ~0.1 ms | ~1-5 ms | 10-50x |
| Key size | ~32 bytes | ~1.5-4 KB | 50-125x |

The once-per-delegation signing model (AITH) mitigates this by amortizing PQC cost across millions of boundary-checked operations.

## 3. What I think is interesting

The fundamental shift in how PQC must be used for agents versus classical systems. Classical TLS handshakes can absorb PQC overhead because they happen once per connection. But AI agents perform thousands of micro-delegations per minute — each tool call, each sub-agent spawn, each data access requires authorization. Per-operation PQC signing is computationally infeasible at agent scale.

AITH's "sign once, check many" model is the right abstraction: a Continuous Delegation Certificate with ML-DSA-87 signed once, then sub-microsecond boundary checks enforce scope without any cryptographic operation. This separates the PQC authentication layer from the policy enforcement layer.

The more surprising finding is that CA-MCPQ takes a different architectural approach — elevating security to mandatory protocol-level mechanisms in MCP itself. This suggests the field is splitting between two design philosophies: AITH's "add PQC layer on top" vs CA-MCPQ's "bake PQC into the protocol".

## 4. What I'd explore next

1. **ZKML + PQC delegation:** Can zero-knowledge proofs of correct ML execution verify PQC delegation without revealing the delegation scope? Combines zkML and PQC domains.
2. **Triton GPU kernels for ML-DSA batch verification:** Can consumer GPUs accelerate batch PQC verification to match classical throughput? Relevant for RTX 3090 optimization interest.
3. **PQC at the edge:** Minimum viable PQC delegation for resource-constrained RTU/IED gateways (sub-100KB RAM) — critical infrastructure security angle.
4. **Practical dual-signature migration frameworks:** What does the classical-to-PQC transition actually look like in agent frameworks?

## 5. Cross-domain connections

- **Entity Resolution:** PQC-secured provenance chains for data lineage in OpenPlanter investigations
- **Edge AI Substation Deployment:** PQC delegation protocols for RTU/IED gateways in IEC 61850 networks
- **Multi-Agent Coordination:** Trust boundaries between agent swarms require PQC-secure handshakes
- **Trusted Execution Environments:** TEE + PQC hybrid for defense-in-depth (SGX/SEV-ES + ML-DSA)
- **AI Agent Trust Infrastructure:** Directly extends the trust infrastructure wiki with PQC primitives
- **Photonic AI Inference:** Future quantum-resistant compute may use photonic co-processors for PQC acceleration

---

## Primary Sources

1. Chen, Z. (2026). "AITH: A Post-Quantum Continuous Delegation Protocol for Human-AI Trust Establishment." arXiv:2604.07695
2. Yoon, S., Kim, H., Seo, H. (2025). "CA-MCPQ: A Context-Aware Post-Quantum Protocol for AI Agent Integrity and Security." IACR ePrint 2025/1790
3. NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA) — Finalized August 2024
4. Open Quantum Safe (OpenSSL) — Reference PQC implementations
5. CSA Agentic AI IAM Framework — Identity management for autonomous agents
