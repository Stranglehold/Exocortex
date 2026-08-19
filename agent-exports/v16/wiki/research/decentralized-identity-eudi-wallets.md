# Decentralized Identity & EUDI Wallets

**Status:** STABLE  
**Created:** 2026-05-19  
**Last Updated:** 2026-05-26  
**Cycle:** 652  
**Verified Primary Sources:** 9  
**Cross-Domain Links:** 5  

## Overview

The European Union Digital Identity (EUDI) wallet framework and broader decentralized identity (DID) ecosystem represent a convergence point for zero-knowledge proofs, post-quantum cryptography, agent-to-agent trust infrastructure, and metadata-resistant communication.

## Regulatory Timeline

| Milestone | Date | Requirement |
|-----------|------|-------------|
| eIDAS 2.0 enters force | Aug 1, 2024 | Legal basis established |
| First wallet available | Dec 24, 2026 | All 27 member states must provide at least one compliant wallet |
| Regulated entity acceptance | Jun 2028 | Banks, health, legal services must accept EUDI wallets for strong authentication |

## Deployment Status (May 2026)

**Expert assessment** (Biometric Update, Apr 2026): Experts doubt full compliance by Dec 2026 deadline. Key gaps: ZKP selective disclosure untested at scale, PQC migration for identity certs not started, interoperability testing incomplete.

### National Progress

| Member State | Status | Notes |
|---|---|---|
| Italy | Beta testing active | Early national wallet launch; sandbox operational |
| Germany | Biometric integration in progress | Integrating biometrics into wallet; reference impl testing |
| Sweden | Early app features enabled | Progressive rollout; partial functionality live |
| Greece | Sandbox available | National wallet app in development |
| France | Reference impl testing | ANSSI evaluating security profile |
| Spain | Pilot phase | National ID integration under way |
| Netherlands | Digital ID upgrade path | Existing DigiD infrastructure adapting |
| Austria | Biometric update (Apr 2026) | Enhanced biometric capabilities specified |

**Zero production deployments** as of May 2026.

## Technical Architecture

### ZKP Selective Disclosure

**Mechanism**: EUDI wallet spec uses OpenID4VCI (verifiable credential issuance) and OpenID4VP (verifiable presentation). Selective disclosure enables holders to prove attributes (age >= 18) without revealing full data (exact DOB).

**Implementation status**: Specified but untested at scale. Reference implementation exists on GitHub (eu-digital-identity-wallet) but no production deployment has demonstrated ZKP selective disclosure under load.

**Cross-ref**: ZKP proofs beyond crypto wiki covers zk-SNARK/STARK primitives; threshold cryptography wiki covers MPC-based issuance.

### PQC Migration for Identity Infrastructure

**The problem**: Identity certificates have the longest key lifetimes of any crypto deployment -- often 5-10 years. Harvest-now-decrypt-later (HNDL) attacks are especially dangerous for identity data because identity is persistent, not ephemeral.

**NIST status**: NIST IR 8547 (2025) provides PQC migration guidance for identity infrastructure. FIPS 203/204/205 (ML-KEM, ML-DSA, SLH-DSA) are finalized but deployment tooling is immature.

**EUDI impact**: eIDAS 2.0 does not mandate PQC for wallet certificates. EC Digital Building Blocks reference implementation uses current ECC/RSA. PQC migration for identity is a 5-10 year horizon problem that has not started.

**Cross-ref**: PQC hardware acceleration wiki covers ML-KEM/ML-DSA performance; post-quantum agent delegation wiki covers AITH protocol.

### Agent-to-Agent Delegation from Human Identity Anchors

**Key question**: How do AI agents inherit trust from human-held digital identities?

**Convergence points with other wiki pages:**
- EUDI wallets will serve as human identity anchors; agent delegation chains need to originate from these anchors
- ZKP proofs of compliance (from ai-agent-delegation-security wiki) could be used to prove agent actions comply with human-granted scope
- Capability token gap identified in MCP protocol research -- EUDI wallet could provide the human trust root for capability tokens
- Post-quantum agent delegation (AITH protocol, arXiv 2604.07695) addresses continuous delegation but needs a human identity anchor

### Metadata Leakage Risks in DID Resolution

**Known risks:**
- DID document resolution exposes resolver endpoint to issuers/relying parties
- Current DID methods (did:key, did:web, did:method) vary in metadata resistance
- Cross-domain link: metadata-resistant communication wiki covers cover traffic and signaling privacy -- DID resolution lacks equivalent protections
- EUDI wallet spec emphasizes unlinkability but implementation maturity is untested

## Primary Sources (9 Verified)

1. **eIDAS 2.0 Regulation (EU) 2024/1183** -- Official Journal of the EU; legal basis for EUDI wallets
2. **EC Digital Building Blocks -- EUDI Wallet Reference Implementation** -- GitHub: eu-digital-identity-wallet; reference code for compliant wallets
3. **W3C DID v1.0 Specification** -- Decentralized Identifiers standard
4. **OpenID4VCI / OpenID4VP** -- Verifiable credential issuance and presentation standards
5. **Biometric Update (Apr 2026)** -- Austria biometric wallet update; expert assessment on 2026 feasibility
6. **ETSI TR 119 479-2** -- European telecom standards body identity framework guidance
7. **NIST IR 8547 (2025)** -- PQC migration guidance for identity infrastructure
8. **NCSC UK PQC Guidance** -- UK national cyber center PQC migration roadmap
9. **PQCC Migration Roadmap** -- European PQC coordination center migration timeline

## Cross-Domain Connections (5)

1. **ZKP Proofs Beyond Crypto** -- Selective disclosure mechanisms in wallets are applied zk-SNARK/STARK primitives
2. **Threshold Cryptography & MPC** -- Verifiable credential issuance uses MPC-based distributed key generation
3. **Post-Quantum Agent Delegation** -- AITH protocol needs human identity anchor; EUDI wallet provides trust root
4. **AI Agent Delegation Security** -- Agent trust chains originate from human-held digital identities
5. **PQC Hardware Acceleration** -- ML-KEM/ML-DSA performance on wallet-class devices (mobile/embedded) is critical path

## Assessment

**Maturity**: EUDI wallet ecosystem is ~18 months from mandatory deployment. Zero production deployments. ZKP selective disclosure is specified but untested at scale. PQC migration for identity certs is a 5-10 year horizon problem that has not started.

**Key risk**: Identity infrastructure has the longest key lifetimes of any crypto deployment. Harvest-now-decrypt-later is especially dangerous for identity data because identity is persistent, not ephemeral.

**Cross-domain synthesis**: The convergence of EUDI wallets (human identity anchors), ZKP selective disclosure (privacy-preserving verification), agent delegation chains (trust amplification), and PQC migration (long-term security) represents one of the highest-leverage research areas in the Exocortex -- it touches 5+ existing wiki pages and defines the trust foundation for human-AI interaction.

## Open Questions

- Will EU member states meet December 2026 deadline? Expert consensus: unlikely for full compliance
- How will PQC migration intersect with wallet deployment? Wallets deployed before PQC ready = immediate HNDL exposure
- Can DID resolution be made metadata-resistant without centralized trust anchors?
- What is the practical latency of ZKP selective disclosure on mobile devices?
- Will agent-to-agent delegation from human identity anchors create new attack surfaces?
