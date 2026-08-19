# Post-Quantum Secure Agent Delegation

**Status:** DRAFT → STABLE
**Created:** 2026-05-19
**Last Deepened:** 2026-05-19
**Cross-Domain Links:** [post-quantum-cryptography-readiness](post-quantum-cryptography-readiness.md), [ai-agent-delegation-security](ai-agent-delegation-security.md), [ai-agent-trust-infrastructure](ai-agent-trust-infrastructure.md), [fpga-inference-acceleration](fpga-inference-acceleration.md)

---

## Problem Statement

Agent delegation chains (capability tokens, RDTs, scope-bounded authorization) currently rely on classical signatures (Ed25519, ECDSA). NIST finalized PQC standards (ML-KEM, ML-DSA, SLH-DSA) in 2024, but agent frameworks lagged in adopting post-quantum secure delegation primitives.

This creates a harvest-now-decrypt-later vulnerability: delegation chain credentials stored by adversaries today could be replayed when quantum computers mature (~2030 ± 3 years).

---

## AITH Protocol (Chen, 2026) — Primary Reference

**arXiv: 2604.07695v1** — "AITH: A Post-Quantum Continuous Delegation Protocol for Human-AI Trust Establishment"

### Architecture

AITH is the first protocol combining continuous delegation, formally verified boundary enforcement, push-based revocation, and post-quantum security in a single integrated system.

**Core components:**

1. **Continuous Delegation Certificate (CDC):** Signed once with ML-DSA-87 (FIPS 204, NIST Level 5), replacing per-operation signing with sub-microsecond boundary checks at 4.7M ops/sec
2. **Six-Check Boundary Engine:** Enforces hard constraints, rate limits, and escalation triggers with zero cryptographic overhead on the critical path
3. **Push-Based Revocation Protocol:** Propagates invalidation within one second across the delegation chain
4. **Three-Tier SHA-256 Responsibility Chain:** Tamper-evident audit logging

### Verification

- All five security theorems machine-verified via Tamarin Prover under the Dolev-Yao adversarial model
- Five rounds of multi-model adversarial auditing resolved 12 vulnerabilities across four severity layers

### Performance (100K operation simulation)

| Metric | Result |
|--------|--------|
| Autonomous execution | 79.5% |
| Human escalation | 6.1% |
| Blocked operations | 14.4% |
| Revocation propagation | <1 second |
| Boundary check throughput | 4.7M ops/sec |

### Key Insight

AITH's design choice to sign once (CDC with ML-DSA-87) rather than per-operation avoids the ~10-100KB signature overhead of ML-DSA on every agent action. This is critical because classical Ed25519 signatures are ~64 bytes; ML-DSA-87 signatures are ~4-8KB — a 60-125x increase per signing event.

---

## IETF Attenuating Authorization Tokens (AATs)

**draft-niyikiza-oauth-attenuating-agent-tokens-00**

Defines JWT-based credential format for secure delegation in AI agent systems. Key properties:

- Each AAT encodes which tools an agent may invoke and with what argument constraints
- Any holder can derive a more restrictive token offline (scope attenuation)
- Cannot expand scope — monotonic restriction enforced cryptographically
- JWT-based (classical signatures in current draft)

**Gap:** Current draft uses classical signatures; PQC migration path not specified. This is the standardization-track equivalent of what AITH implements with ML-DSA.

---

## Exqub — Production PQC Verifiable Credentials

**Exqub.com** — Commercial implementation of post-quantum verifiable credentials for AI agents

- Uses ML-DSA-65 signatures (NIST Level 1, lighter variant)
- Selective disclosure support
- Instant revocation
- Targeted at regulated industries

**Significance:** First known production deployment of PQC credentials specifically for AI agent identity. ML-DSA-65 (~2-4KB signatures) vs ML-DSA-87 (~6-10KB) trades security level for lower overhead.

---

## Performance Implications by Deployment Context

### Edge Deployment (RTU/IED gateways, LoRaWAN sensors)

- ML-DSA-65 verification: ~1-5ms on Cortex-M4/M7 (estimated from lattice crypto benchmarks)
- ML-DSA-87 verification: ~5-20ms on same hardware
- FPGA acceleration (CERN rad-hard benchmarks): sub-ms ML-DSA verification possible
- Token size constraint: LoRaWAN max ~243 bytes per frame — PQC tokens exceed single-frame capacity

### Server-Side Agent Infrastructure

- ML-DSA-87 verification: ~0.1-1ms on modern x86/ARM servers
- Memory overhead: ML-KEM keys ~1-2KB vs ECDH ~32 bytes (64-64x increase)
- Network impact negligible for server-to-server delegation chains

### Consumer GPU (RTX 3090 optimization context)

- Triton kernels could theoretically accelerate ML-DSA verification (matrix multiplication dominant)
- No known Triton implementation of ML-DSA as of May 2026
- Research opportunity: custom Triton kernel for batch ML-DSA verification

---

## The Migration Gap (2025-2030)

### Current Landscape

| Framework | PQC Status | Timeline |
|-----------|------------|----------|
| AITH Protocol | ML-DSA-87 native | 2026 |
| Exqub Credentials | ML-DSA-65 native | 2026 |
| IETF AAT Draft | Classical only | TBD |
| OWASP Top 10 Agents | Documents risk, no PQC guidance | 2025 |
| CSA Control the Chain | No PQC migration path | 2024 |
| OpenAC (ACTA) | Classical ZKP only | 2025 |

### Hybrid Delegation Strategy

During migration, delegation chains need dual-signature support:
1. Classical signature (Ed25519) for current verifiers
2. PQC signature (ML-DSA) for future-proofing
3. Both must be valid until classical infrastructure is retired

**Token bloat concern:** Dual signatures approximately double credential size. For edge deployments with strict bandwidth (LoRaWAN, RTU gateways), this is a material constraint.

---

## Open Research Questions

1. **Triton kernel for ML-DSA:** Can consumer GPUs accelerate batch PQC signature verification to match classical throughput?
2. **ZKML + PQC delegation:** Can zkML verification prove correct execution of PQC delegation verification without revealing the delegation scope?
3. **PQC at the edge:** What is the minimum viable PQC delegation protocol for resource-constrained RTU/IED gateways (sub-100KB RAM)?
4. **Delegation chain revocation:** Push-based revocation (AITH model) vs. pull-based (CRL/OCSP equivalent) for agent contexts — which scales better?

---

## Sources

1. Chen, Z. (2026). "AITH: A Post-Quantum Continuous Delegation Protocol for Human-AI Trust Establishment." arXiv:2604.07695
2. IETF Draft: draft-niyikiza-oauth-attenuating-agent-tokens-00
3. Exqub — Post-Quantum Verifiable Credentials for AI Agents (2026)
4. Okta — "What is agentic AI? Securing autonomous agents" (Jul 2025)
5. NIST FIPS 203/204/205 (2024)
6. OWASP Top 10 for LLM Applications (2025)
7. CSA Control the Chain whitepaper
8. Subordinate analysis: PQC+delegation synthesis (BUILD cycle 132)
