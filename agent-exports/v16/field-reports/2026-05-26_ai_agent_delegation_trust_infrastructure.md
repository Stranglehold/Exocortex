# Field Report: AI Agent Delegation & Trust Infrastructure
**Date:** 2026-05-26
**Cycle:** EXPLORE #622
**Topic:** AI Agent Delegation & Trust Infrastructure

---

## 1. What I Explored

The specific thread: **How do you cryptographically verify that an AI agent acted within authorized bounds when work is delegated across chains of autonomous agents?**

This is the delegation chain problem — when Agent A delegates to Agent B, which invokes Tool C on behalf of User X, no existing framework could answer: whose authorization chain led to this action, and where did it violate policy? The past 6 months of research (Feb–May 2026) show converging work on formal delegation calculi, verifiable chain-of-custody protocols, and post-quantum identity layers.

---

## 2. What I Found

### Key Papers & Frameworks

**SentinelAgent (arXiv:2604.02767, Apr 2026)**
- Introduces Delegation Chain Calculus (DCC) with 7 properties: 6 deterministic, 1 probabilistic
- Three-layer protocol: pre-execution (authority narrowing), at-execution (conformance checking), post-execution (intent verification)
- Empirical evaluation: 100% policy violation detection in federal multi-agent testbeds
- Novel contribution: probabilistic intent verification via LLM-as-judge for cases where deterministic checks are insufficient

**KYA — Know Your Agents (arXiv:2605.25376, May 25, 2026 — 24 hours old)**
- Five-primitive governance layer: (1) four-gate inbound apply pipeline with Ed25519 + multi-anchor pinning + persist-time expiry, (2) drift detection, (3) leak detection, (4) rogue-behavior detection, (5) observability layer
- Key insight: "Observability tells operators when an agent is slow. KYA tells operators when an agent is wrong, drifting, leaking, or quietly going rogue."
- Introduces "delegation-trust premium" concept — the measurable cost of verifying delegation chains

**Authenticated Workflows (arXiv:2602.10465, Feb 2026)**
- Systems approach requiring independent cryptographic verification at every hop: agent→agent, agent→tool, tool→data
- Signed delegation receipts with cryptographic identity per agent

**HDP — Cryptographic Chain-of-Custody (arXiv:2604.04522, Apr 2026)**
- Fully offline verification, no registry lookups or third-party trust anchors required
- Positions itself within existing delegation protocol landscape

**RFC-ATF-1 (Agent Trust Fabric, 2026)**
- Post-quantum cryptographic protocol using ML-DSA-65 (NIST FIPS 204)
- Addresses "harvest now, decrypt later" attacks on long-lived agent identities
- Formally specified for high-stakes environments (federal, financial)

**AITH (arXiv:2604.07695, Apr 2026)**
- Post-quantum continuous delegation protocol
- First protocol combining: continuous delegation + formally verified boundary engine + push-based sub-second revocation + three-tier legal-grade responsibility chain + PQC security

**IETF Delegation Receipts Draft (draft-nelson-agent-delegation-receipts, Apr 2026)**
- Standardization effort at IETF for delegation receipt format
- Expires Oct 2026

### Regulatory & Industry Context

- **EU AI Act** full enforcement activation: August 2, 2026
- **Colorado AI Act** enforceable: June 2026
- **NIST CAISI** announced AI Agent Standards Initiative (Feb 17, 2026)
- **Microsoft Agent Governance Toolkit** released open-source (Apr 2026)
- **CSA** published "Fixing AI Agent Delegation for Secure Chains" (Mar 2026) — identifies session smuggling and escalation as primary risks
- **82% of enterprises** have AI agents their security teams did not know existed (Gravitee, Feb 2026)

---

## 3. What I Think Is Interesting

**The field is converging on a protocol stack, not a monolithic solution.** SentinelAgent handles the calculus (what properties must delegation satisfy), KYA handles observability (how do you know an agent is drifting), HDP handles chain-of-custody (offline verification), and RFC-ATF-1 handles the cryptographic substrate (PQC signatures). These are composable layers, not competing frameworks.

**The delegation-trust premium is a real economic concept.** KYA's framing of measurable cost for verifying delegation chains suggests that as agent ecosystems scale, trust verification becomes a first-class market. This parallels how TLS certificates became infrastructure — invisible but essential.

**Post-execution intent verification via LLM-as-judge is novel and underexplored.** SentinelAgent's probabilistic intent verification acknowledges that not all policy violations are deterministic. This is the hardest problem: knowing whether an agent's output *meant* to comply even if it technically violated a narrow constraint.

**The 82% stat is alarming.** If most enterprises have shadow AI agents, delegation chain verification is largely theoretical in production today. The governance crisis is real — agents are acting without verifiable authority chains.

---

## 4. What I'd Explore Next

- **ZKML for delegation verification**: Can zero-knowledge proofs verify agent intent without revealing the agent's internal reasoning? The ZKML stack is maturing — intersection with delegation is unexplored.
- **Revocation at scale**: AITH's sub-second revocation is promising, but how does revocation propagate through chains of 10+ delegated agents?
- **Economic models for agent trust markets**: If delegation-trust premium is real, what does a marketplace for verified agent identity look like?
- **Delegation in adversarial contexts**: How do intelligence operations (HUMINT/SIGINT) handle delegation verification? Parallels to counterintelligence analysis frameworks.

---

## 5. Cross-Domain Connections

- **Post-Quantum Cryptography**: RFC-ATF-1 and AITH both use ML-DSA-65 for delegation signatures. Connects to existing wiki research on PQC hardware acceleration and post-quantum ML.
- **Entity Resolution**: Delegation chains are fundamentally entity resolution problems across time — tracking that Agent B at t=1 is the same authorized entity as Agent B at t=2. Connects to graph-native entity resolution research.
- **Threshold Cryptography & MPC**: Multi-party delegation (where authority is split across N agents requiring K to approve) maps directly to threshold signature schemes. Connects to threshold-cryptography-mpc wiki page.
- **Zero-Knowledge Proofs**: ZK verification of agent behavior without exposing internals connects to ZKML and zero-knowledge proof research.
- **Critical Infrastructure Security**: AI agents in power grid, SCADA, and DER orchestration need delegation chains that survive adversarial conditions. Connects to electric utility AI research.
- **Intelligence Operations**: Counterintelligence analysis of competing hypotheses (ACH) methodology applies to evaluating competing explanations for agent behavior drift.

---

*Report generated during EXPLORE cycle. Key insight saved to memory.*
