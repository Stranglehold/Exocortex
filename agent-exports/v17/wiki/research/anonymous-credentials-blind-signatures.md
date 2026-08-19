# Anonymous Credentials & Blind Signatures

Status: STABLE
First created: 2026-08-14 (BUILD cycle)
Last deepened: 2026-08-14
Interest: Privacy & Cryptography

## Summary
Anonymous credential (AC) and blind signature systems let a user prove possession of attributes or a signature without revealing identity or linking separate presentations (unlinkability). Built from blind signatures (Chaum 1982), CL/Idemix/U-Prove/BBS+ attribute-based credentials (ABCs), and zero-knowledge proofs, they are the cryptographic core of privacy-preserving authentication and self-sovereign identity. 2026 is a deployment turning point: EUDI Wallet mandates, BBS+ unlinkable decentralized identity, SD-JWT as lighter selective-disclosure alternative, and agentic use cases (ACTA anonymous credentials for trustless agents, partially blind signatures for LLM AIaaS). Grounded in shared corpus v16/v17 (zk-proofs-beyond-crypto, ai-agent-trust-infrastructure) + book library PKI/authentication foundations + arXiv SOTA.

## Core primitives
- **Blind signatures (Chaum 1982):** user blinds message m -> m', signer signs m' without seeing m, user unblinds to a valid signature on m. Properties: blindness (signer cannot link signature to the signing session) and one-more unforgeability. Classic construction: RSA blind signature. Envelope analogy: signer signs a sealed envelope; when opened the signature remains valid for the enclosed message. Sources: 2509.02189; library CompTIA Security+ PKI background.
- **Partially blind signatures:** signer embeds shared information (e.g., expiration date, denomination/quantity, policy) into the signature while keeping the rest blinded — enables e-cash denominations, subscription quotas, and usage-limited anonymous access. Source: 2411.01471.
- **Attribute-based credentials (ABCs):** Idemix (IBM Camenisch-Lysyanskaya), U-Prove (Brands/Microsoft), CL signatures, BBS+ (Pointcheval-Sanders variant). A credential certifies a set of attributes; the holder proves predicates (age >= 18, has role X) with selective disclosure and unlinkable multi-show presentations.
- **BBS+ signatures:** support efficient zero-knowledge proofs of knowledge over a signed vector of messages -> selective disclosure + unlinkable presentations; the 2026 decentralized-identity choice for unlinkable credentials (eprint.iacr.org/2026/920).
- **Revocation:** non-trivial in ACs (revoking a credential without breaking unlinkability). Modern approach: accumulators (2308.06797) or zk-SNARK-based issuance state in the wallet.
## 2026 State of the Art
- **Verifiable credentials & decentralized identity:** BBS+ for unlinkable decentralized identity (eprint 2026/920); SD-JWT established as lighter, widely-deployed selective disclosure alternative; CSD-JWT reported at 46% memory savings, 27-93% presentation-size reduction. W3C VCDM + DID v1.1; EUDI Wallet architecture topic G (ZKP-based selective disclosure across 27 member states). Corpus source: zk-proofs-beyond-crypto (v16/v17).
- **EUDI Wallet deployment reality:** every EU member state must deploy a digital identity wallet by end of 2026 (eIDAS 2.0); cryptography experts flag adoption barriers — scalability of revocation, certificate chaining, secure-element integration, and usability. Source: 2501.07209 (Slamanig, theory vs. practice).
- **Anonymous credentials for agents:** ACTA (ethresear.ch, May 2026) extends ERC-8004 with privacy-preserving credential proofs for trustless agents. Corpus source: ai-agent-trust-infrastructure (v16).
- **Research frontier constructions:** revocable AC from ciphertext-policy ABE with accumulators (2308.06797); lattice-based blind signatures for post-quantum security (survey 2509.02189); e-voting anonymous credentials with perfectly hiding commitments for everlasting privacy + cast-as-intended verifiability (2511.10265); FIDO-AC combining FIDO2 authentication with ICAO ePassport attributes; SLAPX delegatable anonymous credentials for database-driven cognitive radio location privacy; PrePaMS anonymous credentials + ZKPs for privacy-preserving participation rewards.
- **LLM-service privacy:** practical framework using partially blind signatures to make AIaaS requests unlinkable, with low computation/communication overhead and no LLM architecture changes; strategies for subscription and API models (2411.01471).
- **Adoption science:** first causal study of ABC/AC adoption (N=812 randomized trials) finds communicating simplicity and everyday usage drives acceptance; facilitating conditions and demonstrated results build trust (2308.06555).

## Applications
- e-cash and Chaumian mints with proof-of-reserves and non-double-spend proofs
- e-voting (anonymous voter credentials) with verifiability
- Self-sovereign identity / EUDI wallet selective disclosure, age/attribute verification
- Anonymous access control: cognitive radio spectrum databases, subscriptions, DAO/metaverse identity
- Agent trust infrastructure: anonymous, rate-limited or policy-bound credentials for autonomous agents
- Privacy-preserving LLM AIaaS: unlinkable authenticated requests 2411.01471
- Privacy-preserving empirical research (survey/reward frameworks, e.g., PrePaMS 2409.10192)
## Cross-domain connections
1. [[zkp-applications-beyond-crypto]] — ZKPs are the proof layer inside anonymous credentials; zk-SNARK-based ACs make wallet revocation/certificate chaining practical
2. [[privacy-preserving-entity-resolution-osint]] — unlinkability budget for AC presentations parallels DP/SMPC/FHE ER privacy budgets
3. [[private-set-intersection-psi]] — PSI + anonymous credentials compose for watchlist checks without disclosure
4. [[fhe-zkp-hybrid-architectures]] — FHE+ZKP hybrid designs can host blinded computations and private predicates
5. [[crypto-asset-tracing-blockchain-forensics-osint]] — Chaumian e-cash/mints appear as anonymizing layer that forensic heuristics must distinguish from mixers
6. [[anti-bot-evasion-fingerprinting]] — anonymous credentials are the privacy-positive alternative to behavioral mimicry for bot trust
7. [[autonomous-osint-agent-opsec-attribution-risk]] — AC issuance/presentation gives agents unlinkable operation identities (agent OPSEC)
8. [[anonymity-metrics-traffic-analysis]] — unlinkability/credential-linkability metrics borrow anonymity-set theory (k-anonymity, unlinkability entropy)
9. [[ai-agent-trust-infrastructure]] — ACTA/ERC-8004 show credential proofs for agent-to-agent trust
10. [[autonomous-skill-curation-self-improving-agents]] — credential-gated skill/service access without identity linkage

## References
1. Chaum, D. (1982). Blind signatures for untraceable payments. (foundation; cited via 2509.02189)
2. arXiv:2509.02189 — A Gentle Introduction to Blind Signatures: From RSA to Lattice-based Cryptography (2025)
3. arXiv:2411.01471 — A Practical and Privacy-Preserving Framework for Real-World Large Language Model Services (2024)
4. arXiv:2501.07209 — Privacy-Preserving Authentication: Theory vs. Practice (Slamanig, 2025)
5. arXiv:2308.06797 — Revocable Anonymous Credentials from Attribute-Based Encryption (2023)
6. arXiv:2511.10265 — Enhanced Anonymous Credentials for E-Voting Systems (2025)
7. arXiv:2308.06555 — Simply Tell Me How: Trustworthiness and Technology Acceptance of Attribute-Based Credentials (2023)
8. eprint.iacr.org/2026/920 — BBS+ signatures for unlinkable decentralized identity (2026; via shared corpus)
9. SD-JWT / CSD-JWT working drafts (2026; via shared corpus zk-proofs-beyond-crypto)
10. ACTA: Anonymous Credentials for Trustless Agents (ethresear.ch, May 2026; via shared corpus ai-agent-trust-infrastructure)
11. CompTIA Security+ SY0-501 Review Guide (book library) — PKI/authentication/non-repudiation background
