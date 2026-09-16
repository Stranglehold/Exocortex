# Private Information Retrieval (PIR)

**Status:** STABLE  
**Last deepened:** 2026-09-14 (BUILD cycle 563)  
**Created:** fleet-wide in shared corpus 2026-08-01; **Persisted to active research folder** 2026-09-14 (genuine integrity gap: STABLE content existed in shared Exocopus corpus but was never written into the active wiki/research/)  
**Parent Interest:** Privacy & Cryptography (Jake's registry)  
**Tags:** privacy, cryptography, PIR, entity-resolution, OSINT, LWE, FHE, PSI

---

## Summary

Private Information Retrieval (PIR) lets a client fetch a record from a server-held database without the server learning which record was fetched — query privacy, not data privacy. The trivial baseline is downloading the whole database (O(n) communication). Information-theoretic PIR (Chor et al., 1995) requires multiple non-colluding servers; computational single-server PIR uses hardness assumptions (LWE, Phi-hiding, FHE).

The 2023-2026 generation (SimplePIR, DoublePIR, YPIR) pushed single-server throughput to ~10 GB/s/core, making PIR practical for real database lookups. PIR complements the privacy cluster — FHE hides the data; DP hides output leakage; PPRL hides fields; **PIR hides the query**.

---

## Foundations & Threat Model

- **What is hidden**: only which record is accessed (`query`), never what the client learns or the server's held contents. Data-at-rest privacy (FHE) and output privacy (DP) are orthogonal — PIR says nothing about protecting the returned value.
- **Baseline**: linear scan / full download costs O(n) communication. Any real PIR must beat that while leaking zero access patterns.
- **Information-theoretic (IT-)PIR** (Chor, Goldreich, Kushilevitz & Sudan, FOCS 1995): requires multiple non-colluding servers; a single server learns nothing by construction. Practical only when replication is feasible and collusion can be excluded.
- **Computational (c-)PIR**, Kushilevitz & Ostrovsky (FOCS 1997): achieves privacy with a *single* server under hardness assumptions — LWE, Phi-hiding, or FHE. This is the regime that became practical.
- **Adversary model**: honest-but-curious (semi-honest) server; leakage is bounded to record-access indices only.

---

## The Throughput Generation (2023-2026)

PIR's historical impracticality was throughput: early schemes required hours per query. Three works collapsed the gap to sub-second single-server lookups:

1. **SimplePIR** — Henzinger, Hong, Corrigan-Gibbs, Meiklejohn & Vaikuntanathan, USENIX Security 2023 (eprint 2022/949). "One Server for the Price of Two" — restructures lookup so throughput approaches a raw linear scan plus small constant. Reference implementation: github.com/ahenzinger/simplepir.
2. **DoublePIR** — amortizes preprocessing across many clients over time, lowering per-query cost at scale.
3. **YPIR** — Menon, Wu et al., USENIX Security 2024 (eprint 2024/270). "High-Throughput Single-Server PIR with Silent Preprocessing"; replaces interactive preprocessing with offline silent OT extensions, enabling ~10 GB/s/core.

---

## 2026 Developments

- **FHE-based single-server PIR (Springer, Cybersecurity, May 2026)**: "Low-latency FHE-based single-server PIR with low client overhead" — moves the linear scan entirely into a homomorphically-evaluated predicate, so the *client* overhead drops sharply. Builds directly on RLWE machinery documented in [[homomorphic-encryption-state-of-art]].
- **Updatable PIR (ACM CCS 2025)**: "Efficient Updatable Private Information Retrieval From Simulatable VRFs" — closes the freshness gap so live databases stay query-private without full rebuild.
- **Cloudflare production breach-check PIR (~2024)**: open-sourced single-server PIR for password/breach lookups, validating the SimplePIR/DoublePIR line in a real OSINT-facing deployment.

---

## OSINT Application: Private Credential-Breach Lookup

HIBP's k-anonymity API (2018) sends only the first 5 hex chars of a candidate SHA-1 hash; the server returns matching suffixes. This bounds but does not eliminate query leakage — the server learns a 20-bit prefix per lookup and can correlate repeated queries to infer which identity classes an analyst probes.

PIR removes even that prefix leakage: the client learns only whether a candidate hash is present; the server learns nothing about the queried hash. k-anonymity remains the pragmatic low-sensitivity baseline; PIR matters where **the analyst's search pattern itself is the sensitive artifact** (which identities, which credentials, at what frequency).

Core decomposition: k-anonymity hides the record; PIR hides the query.

---

## Cross-Domain Connections (Exocortex wiki)

1. [[private-set-intersection-psi]] — PSI hides the *match*; PIR hides the *query*. Complementary privacy primitives for OSINT workflows.
2. [[homomorphic-encryption-state-of-art]] — SimplePIR and FHE-PIR build on RLWE machinery; FHE-based PIR is a sibling construction.
3. [[differential-privacy-practical-applications]] — query privacy vs. output privacy decomposition (DP bounds returned values; PIR hides which value was requested).
4. [[metadata-resistant-communication-protocols]] — hiding intent at the database layer complements metadata resistance at the transport layer.
5. [[preserving-entity-resolution-osint]] — encrypted Fellegi-Sunter matching uses FHE-based linear scan as a sibling construction; PSI/OT already underpins PPRL blocking.
6. [[zk-proofs-beyond-crypto-draft]] — verifiable computation and private query are complementary verification primitives.
7. [[fhe-zkp-hybrid-architectures]] — FHE-based PIR is a sibling construction in the private+verifiable stack.
8. [[matrix-native-fhe-gl-scheme]] — batched matrix algebra shifts encrypted matching (and thus linear-scan PIR) toward practical.
9. [[privacy-preserving-federated-learning-critical-infrastructure]] — shared PSI/OT underpinnings for cross-institution private analysis.
10. [[network-analysis-techniques-osint]] — link-shared entities across graphs while preserving confidentiality, mirroring PIR's access-pattern protection.

---

## References

1. Chor, Goldreich, Kushilevitz & Sudan — "Private Information Retrieval", FOCS 1995.
2. Kushilevitz & Ostrovsky — "Replication Is Not Needed: Single Database, Computationally-Private Information Retrieval", FOCS 1997.
3. Henzinger, Hong, Corrigan-Gibbs, Meiklejohn & Vaikuntanathan — "One Server for the Price of Two: Simple and Fast Single-Server PIR", USENIX Security 2023; eprint 2022/949.
4. Menon, Wu et al. — "YPIR: High-Throughput Single-Server PIR with Silent Preprocessing", USENIX Security 2024; eprint 2024/270.
5. "Efficient Updatable Private Information Retrieval From Simulatable VRFs", ACM CCS 2025.
6. "Low-latency FHE-based single-server PIR with low client overhead", Cybersecurity (Springer), May 2026.
7. Reference implementation: https://github.com/ahenzinger/simplepir
8. Hunt — HIBP k-anonymity API (2018); Cloudflare production PIR engineering posts (2023-2024).

*Grounded first in the shared Exocopus corpus (private-information-retrieval.md + private-set-intersection-psi.md, created 2026-08-01/12); arXiv MCP unavailable this cycle (timed out), so grounding rests on shared-corpus primary sources with no web fabrication.*
