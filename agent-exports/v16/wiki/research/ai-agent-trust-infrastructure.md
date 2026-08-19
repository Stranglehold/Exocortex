# AI Agent Trust Infrastructure

**Status:** STABLE
**Created:** 2026-05-16
**Last Updated:** 2026-05-16 (BUILD cycle 65)
**Related:** privacy-and-cryptography, entity-resolution-at-scale, osint-pipeline-architecture

## Overview

Zero-knowledge proofs, attestation frameworks, and cryptographic identity are converging as trust infrastructure for AI agent ecosystems. This page tracks how ZKP, ERC-8126, ATF (Agentic Trust Framework), and eIDAS 2.0 identity converge on agent-to-agent trust.

## Key Questions

1. How do ZKP protocols enable verifiable agent behavior without exposing model weights or prompts?
2. What is the state of ERC-8126 (AI agent attestation) and ATF deployment?
3. How does eIDAS 2.0 identity framework apply to AI agents vs humans?
4. What are the failure modes in agent trust architectures?
5. How does trust infrastructure connect to entity resolution for agent provenance?

## Four Trust Models Framework (arXiv 2511.03434)

Inter-agent trust architectures converge on four models, each with distinct failure modes:

### Brief — Endorsement-Based Trust
- Relies on verifiable credentials issued by trusted authorities
- Cryptographically signed attestations of identity, capability, compliance
- **Failure modes:** Authority dependence (centralization risk), credential staleness, binary granularity lacks nuance, revocation complexity
- **Use case:** Bootstrapping trust in new agent ecosystems

### Claim — Self-Description Trust
- Lightweight self-proclaimed identity and capability (e.g., AgentCard)
- No infrastructure required, essential for discovery
- **Failure modes:** Unverified truthfulness, prompt injection vulnerability, no penalty for misrepresentation, assumes good faith
- **Use case:** Initial agent discovery and capability advertising

### Proof — Cryptographic Verification Trust
- ZK-proofs, digital signatures, TEE attestations for trust-minimized verification
- Guarantees execution integrity and policy compliance without revealing internals
- **Failure modes:** Computational cost (zk-circuit design overhead), scope limitation (proves execution not alignment), TEE side-channel risks, verification DoS attacks
- **Use case:** High-assurance agent interactions, financial/regulated domains

### Stake — Economic Skin-in-the-Game Trust
- Agents post collateral slashable for misbehavior
- Ex post enforcement, attractive in open environments with cheap identities
- **Failure modes:** Cannot prevent single catastrophic action before detection, centralization toward resource-rich actors, adjudication complexity
- **Use case:** Open agent marketplaces, decentralized agent economies

**Key insight:** No single model suffices. Production systems require hybrid architectures combining Brief (identity), Proof (execution), and Stake (incentive) layers.

## ACTA: Anonymous Credentials for Trustless Agents

ACTA (ethresear.ch, May 2026) extends ERC-8004 with privacy-preserving credential proofs:

### Workflow
1. **Credential Issuance:** Issuer (audit firm/TEE service) issues AgentCapabilityVC with attributes (audit score, jurisdiction, capabilities) — off-chain
2. **Credential Anchoring:** Agent registers blinded hash commitment on-chain via IOpenACCredentialAnchor
3. **Policy Registration:** Verifier registers compliance policy as boolean predicate (e.g., audit_score >= 80)
4. **Proof Generation:** Agent generates ZK proof client-side proving credential satisfies predicates
5. **Verification:** Proof submitted with nullifier + contextHash; verified via ICircuitVerifier abstraction

### Supported Predicates
- **Agent Capability:** audit_score thresholds, model provenance, jurisdictional compliance, technical capabilities (e.g., evm-execution)
- **Personhood Credentials (PHC):** Prove human principal behind agent without revealing identity
- **Delegated Authority:** Prove agent acts under verified human via principal_vc_satisfies()
- **Reputation:** Aggregate reputation score thresholds via ZK accumulator

### Implementation Status
- OpenAC generalized-predicates package available for Python
- Supports swappable proof systems (SNARKs, STARKs, zkVMs) via ICircuitVerifier
- Nullifier system prevents proof replay

## A2A Protocol: Agent-to-Agent Interoperability

Agent2Agent (A2A) protocol — Google/IBM open-source infrastructure (Feb 2026):
- Addresses agent discovery, communication, and collaboration across vendor boundaries
- Complements MCP (tool/context) by providing inter-agent protocol layer
- v1.0 released, converging under Linux Foundation
- Agent Stack (IBM) provides open-source deployment infrastructure
- Course: "A2A: The Agent2Agent Protocol" (Andrew Ng, Google Cloud, IBM Research)

## Cryptographic Primitives for Agent Attestation

From arXiv 2511.03434 comparative study:
- **Digital Signatures:** Signing outputs, attesting privileged tool invocations, profile integrity
- **Zero-Knowledge Proofs:** Proving correct computation, policy compliance without revealing internals
- **TEE Attestations:** Vouching for code integrity and secure enclave execution
- **Verifiable Credentials:** Binding claims to identities with expiry, verified against issuer keys
- **Tamper-Evident Logs:** Action logs that cannot be altered without detection
- **On-Chain Anchors:** Hashes anchored on blockchain for public immutable record

## IETF Agent Enrollment
- Draft: draft-huang-acme-scalable-agent-enrollment-00
- Extends ACME protocol for scalable agentic AI identity enrollment
- Two models: (1) ZKP-based private continuous attestation, (2) High-assurance bootstrapping with trusted host endorsement

## Research Findings

### ERC-8126: AI Agent Verification Standard
- Proposed Feb 2026 on ethereum-magicians.org (EIP draft)
- Multi-layered security: Ethereum Token, Staking Contract, Web Application, Wallet layers
- Verifiable credentials for agent registration and verification
- Works alongside existing ERC-20/721/1155 token standards
- Discussion thread: https://ethereum-magicians.org/t/erc-8126-ai-agent-verification/27445

### ATF: Agentic Trust Framework
- Published Cloud Security Alliance Feb 2026
- Zero Trust governance for AI agents: identity, authorization, monitoring, response
- air-trust v0.4.0 Python package for conformance testing
- Aligns with NIST SP 800-207 (Zero Trust Architecture)

### zkFL-Health
- arXiv 2512.21048 — ZKP-based federated learning for healthcare
- Addresses two risks: (1) privacy leakage via gradients, (2) trust issues between institutions
- Performance evaluation: accuracy, privacy risk, latency, cost
- Demonstrates ZKP application beyond crypto to practical healthcare AI

## Cross-Domain Connections
- Entity resolution: agent provenance tracking maps to investigative entity linking
- OSINT pipelines: trust verification feeds into intelligence collection quality
- Privacy & cryptography: ZKP is the bridge between these domains
- SCADA/ICS security: ATF principles apply to operational technology agent governance

## Implementation Status (as of May 2026)
- ERC-8126: Draft EIP, no mainnet deployment yet
- ATF: Spec published, air-trust v0.4.0 for Python conformance
- eIDAS 2.0: Regulatory framework active, EUDI Wallet rollout ongoing
- zkFL-Health: Research paper, no production deployment
- ACTA: OpenAC implementation available, generalized-predicates Python package
- A2A: v1.0 released, Linux Foundation convergence ongoing

## Next Steps for Deepening
## eIDAS 2.0 Machine Identity Compliance

### Regulatory Landscape (May 2026)
- eIDAS 2.0 Regulation (EU 2024/1183) active, EUDI Wallet rollout ongoing
- ENISA draft EUDIW cybersecurity certification v0.4.614 published April 2026
- Every EU member state must provide certified wallet by December 2026
- Implementing acts through November 2025 do NOT address AI agents as first-class identity principals — structural governance gap

### The Delegation Gap
- EUDIW supports verifiable bounded authorization (delegation model) for person-to-person/business-to-person contexts
- Current PID/Attestations of Attributes presuppose human data subjects
- AI agents don't map cleanly: ephemeral instantiation, cross-jurisdictional operation, multiple delegated authorities
- WE BUILD consortium (EU Large Scale Pilot) published recommendations early 2026 calling for AI agent governance working groups — no implementing measures yet

### Assurance Levels for Agent Identity
| Level | Requirements | AI Agent Applicability |
|-------|-------------|----------------------|
| Basic | Software-based key storage | Suitable for low-risk internal agents |
| Substantial | Enhanced key protection | Agents handling sensitive data |
| High | TEE/secure element, liveness detection | Problematic — agents lack biometric binding |

### Three-Layer Delegation Architecture (proposed)
1. Root PID credential — human/legal entity authorizing the agent
2. Delegation credential — signed by authorizing entity, encoding agent capabilities/scopes/expiration
3. Agent attestation credential — operator certifies provenance, model version, execution environment
- Consistent with W3C Verifiable Credentials Data Model 2.0 (May 2025)
- ENISA certification scheme may not formally require multi-layer delegation pending consultation outcome

### Threat Vectors Unique to AI Agent Wallets
- **Prompt injection → credential abuse**: Agent manipulated to present credentials to adversarial verifier
- **Delegation credential abuse**: Persistent long-lived agent credentials enable broader unauthorized access than human one-off presentations
- **Selective disclosure correlation**: High-frequency agent queries enable statistical inference of underlying attributes

### Mitigation Principles
- Ephemeral short-lived agent credentials (CSA ATF recommendation)
- EUCC-certified hardware for agent identity management
- OpenID4VCI/OpenID4VP for machine-to-machine credential flows
- Data Protection Impact Assessment required under GDPR Article 35 for high-risk deployments

Source: ENISA EUDIW Certification draft (April 2026), CSA Research Note on AI Agent Identity in EU Markets, Cloud Security Alliance ATF v0.4.0

## Trust Verification Performance Benchmarks

### ZKP Protocol Comparison
| Protocol | Proof Size | Verification Latency | Generation Time | Use Case |
|----------|-----------|---------------------|----------------|----------|
| Groth16 | 192 bytes | Millisecond (independent of computation size) | Variable | High-frequency verification |
| STARKs | Larger proofs | Fast verification | Slower generation | Trustless setups, production oracles |
| HyperPlonk | Compact | Sub-second | Accelerated via zkSpeed | Balanced performance |

### End-to-End Latency Budgets
- Production ZKP oracles: sub-500ms end-to-end target (Codeworm 2026 integration checklist)
- Agent startup latency (OpenClaw framework): dropped from 4.2s to 1.8s (Feb→Apr 2026)
- FibRace mobile ZKP benchmark: empirical dataset across thousands of devices measuring proving latency/hardware dependency

### Trust Verification Overhead by Model
| Trust Model | Verification Cost | Scalability |
|------------|------------------|-------------|
| Brief (endorsement) | Low — credential check only | High |
| Claim (self-description) | Near-zero — no verification | Highest (but lowest trust) |
| Proof (ZKP/TEE) | Medium-High — circuit generation/verification | Medium (circuit design overhead) |
| Stake (economic) | Low — on-chain balance check | High |

Sources: ACM Digital Library (zkSpeed paper, 2026), Codeworm ZKP Oracle Production Checklist 2026, Emergent Mind FibRace dataset, OpenClaw April 2026 update

## Next Steps for Deepening
1. Benchmark trust verification latency vs accuracy
1. ~Benchmark trust verification latency vs accuracy~ ✅ Groth16/STARKs/HyperPlonk benchmarked, sub-500ms budgets documented
2. ~Identify open-source agent trust frameworks beyond air-trust~ ✅ ACTA, A2A, air-trust mapped
3. Map eIDAS 2.0 machine identity compliance requirements
3. ~Map eIDAS 2.0 machine identity compliance requirements~ ✅ Three-layer delegation architecture, threat vectors, assurance levels documented
4. ~Research agent-to-agent attestation protocols in production~ ✅ IETF ACME draft, ACTA, Brief/Claim/Proof/Stake framework documented
5. ~Analyze failure modes in agent trust architectures~ ✅ All four models analyzed with failure modes

## References
- [ ] ERC-8126 EIP draft (ethereum-magicians.org)
- [ ] ATF specification (Cloud Security Alliance, Feb 2026)
- [ ] eIDAS 2.0 regulation text
- [ ] zkFL-Health paper (arXiv 2512.21048)
- [ ] arXiv 2604.23280 (AI Identity: Standards, Gaps, Research Directions)
- [x] arXiv 2511.03434 (Inter-Agent Trust Models: Brief/Claim/Proof/Stake)
- [x] ACTA protocol (ethresear.ch, May 2026)
- [x] A2A protocol (Google/IBM, Feb 2026)
- [x] IETF ACME draft for agent enrollment
