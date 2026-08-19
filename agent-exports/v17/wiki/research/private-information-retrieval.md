# Private Information Retrieval (PIR)

**Status:** STABLE
**Last deepened:** 2026-08-01
**Created:** 2026-08-01 | **Parent Interest:** Privacy & Cryptography
**Tags:** privacy, cryptography, PIR, entity-resolution, OSINT, LWE, FHE

---

## Summary

Private Information Retrieval (PIR) lets a client fetch a record from a server-held database
without the server learning which record was fetched — query privacy, not data privacy. The
trivial baseline is downloading the whole database (O(n) communication). Information-theoretic
PIR (Chor et al. 1995) requires multiple non-colluding servers; computational single-server PIR
uses hardness assumptions (LWE, Phi-hiding, FHE). The 2023–2026 generation (SimplePIR,
DoublePIR, YPIR) pushed single-server throughput to ~10 GB/s/core, making PIR practical for
real database lookups. PIR complements the existing Exocortex privacy cluster (FHE, DP, PPRL):
those hide the data; PIR hides the query.

---

## 1. Problem Statement

- Server holds an n-bit database; client holds index i; goal: client learns DB[i] and server
  learns nothing about i (computational or information-theoretic indistinguishability).
- Downloading the full database is always a valid protocol — the “trivial PIR” baseline.
- Key metrics: server throughput, client communication (amortized per query), hint size
  (one-time offline data), server computation, update cost.

## 2. Taxonomy

| Family | Subtype | Assumption | Example schemes |
|--------|---------|------------|-----------------|
| Information-theoretic (multi-server) | k non-colluding servers | none (perfect) | Chor–Goldreich–Kushilevitz–Sudan 1995 |
| Computational (single-server) | LWE/RLWE-based | LWE | SimplePIR, DoublePIR, FrodoPIR, XPIR, SealPIR |
| Computational (single-server) | FHE-based | RLWE/BFV/CKKS | SealPIR, OnionPIR, Spiral, 2026 low-latency FHE PIR |
| Offline/online (preprocessing) | one-time hint then fast queries | LWE / silent preprocessing | FrodoPIR, SimplePIR, DoublePIR, YPIR |

## 3. Key schemes and milestones

| Scheme | Year | Server throughput | Client comm (per query) | Note |
|--------|------|-------------------|------------------------|------|
| KO (Kushilevitz & Ostrovsky) | 1997 | low | polylog | first single-server computational PIR |
| XPIR | 2016 | ~100s MB/s | polylog | RLWE with NTT optimizations |
| SealPIR | 2018 | ~1 GB/s | small | recursive query expansion, BFV |
| OnionPIR | 2021 | ~1–2 GB/s | constant-ish | layered FHE |
| Spiral | 2022 | ~2–3 GB/s | small | efficient query packing |
| FrodoPIR | 2023 | ~GB/s | 242 KB | LWE with one-time hint |
| SimplePIR | 2023 | 10 GB/s/core | 242 KB (after 121 MB hint per 1 GB DB) | fastest single-server PIR known at publication |
| DoublePIR | 2023 | ~GB/s | 242 KB (after 16 MB hint per 1 GB DB) | trades server work to shrink hint 8× |
| YPIR | 2024 | high | constant-rate | silent preprocessing, first single-server sublinear amortized server time (via later CCS line) |

## 4. 2023–2026 frontier

- **SimplePIR / DoublePIR** (Henzinger, Hong, Corrigan-Gibbs, Meiklejohn, Vaikuntanathan;
  eprint 2022/949, USENIX Security 2023): server does fewer than one 32-bit multiplication and
  one 32-bit addition per database byte; throughput ~10 GB/s/core, approaching memory
  bandwidth. SimplePIR requires a 121 MB hint for a 1 GB database; DoublePIR shrinks the hint
  to 16 MB at the cost of more server computation. Each subsequent query is ~242 KB.
  Reference implementation: github.com/ahenzinger/simplepir.
- **YPIR** (USENIX Security 2024, eprint 2024/270): high-throughput single-server PIR with
  silent preprocessing; uses pseudorandom correlation generators to avoid huge hints.
- **Updatable PIR** (CCS 2025, “Efficient Updatable Private Information Retrieval From
  Simulatable VRFs”, dl.acm.org/doi/10.1145/3708821.3733871): supports database updates
  without forcing clients to re-download hints — critical for real-world rolling datasets.
- **2026 low-latency FHE PIR** (Cybersecurity, Springer, May 2026): FHE-based single-server PIR
  with low client overhead, targeting latency-sensitive deployments.

## 5. Application map

- **Private database lookup**: blocklists, CVE feeds, DNS, WHOIS, registry data — query without
  exposing interest.
- **OSINT / privacy-preserving investigation**: look up a target in breach-corpus and sanctions
  data (HIBP-style) without the operator/server learning which identity is being investigated.
- **Multi-agent systems**: agents query shared knowledge bases without leaking their search intent
  to other agents or the KB host — a natural fit for Exocortex-style shared memory.
- **zkML / verifiable AI**: private retrieval as a component of verifiable inference pipelines.

## 6. Cross-domain connections (Exocortex wiki)

- [[privacy-preserving-entity-resolution-osint]] — PIR complements PPRL: PPRL hides data, PIR hides query.
- [[homomorphic-encryption-state-of-art]] — SimplePIR and FHE-PIR builds on RLWE machinery.
- [[fhe-zkp-hybrid-architectures]] — FHE-based PIR is a sibling construction.
- [[data-breach-analysis-osint-identity-linkage]] — private breach-corpus lookups.
- [[differential-privacy-practical-applications]] — query privacy vs. output privacy decomposition.
- [[multi-agent-orchestration-patterns]] — private shared-memory access patterns.
- [[metadata-resistant-communication-protocols]] — hiding intent at the database layer complements
  metadata resistance at the transport layer.
- [[zkml-verifiable-ai-inference]] — private+verifiable inference stacks.

## 7. Open questions / next deepening

- Practical updatable PIR in production; hint refresh costs for rolling datasets.
- Deployable private breach-lookup service with open protocol (analogous to HIBP k-anonymity).
- PIR as an agent-to-KB access primitive: communication cost per query vs. agent context budgets.

## 8. References

1. Chor, Goldreich, Kushilevitz, Sudan — “Private Information Retrieval”, FOCS 1995.
2. Kushilevitz, Ostrovsky — “Replication Is Not Needed: Single Database, Computationally-Private
   Information Retrieval”, FOCS 1997.
3. Henzinger, Hong, Corrigan-Gibbs, Meiklejohn, Vaikuntanathan — “One Server for the Price of Two:
   Simple and Fast Single-Server PIR”, USENIX Security 2023; eprint 2022/949.
4. Menon, Wu et al. — “YPIR: High-Throughput Single-Server PIR with Silent Preprocessing”,
   USENIX Security 2024; eprint 2024/270.
5. “Efficient Updatable Private Information Retrieval From Simulatable VRFs”, ACM CCS 2025.
6. “Low-latency FHE-based single-server PIR with low client overhead”, Cybersecurity (Springer), May 2026.
7. Reference implementation: https://github.com/ahenzinger/simplepir

## 9. Investigative application: private credential-breach lookup

The most direct OSINT-facing deployment is private breach checking. The current
standard, HIBP k-anonymity API (2018), sends the first 5 hex chars of a candidate
SHA-1 hash; the server returns matching suffixes. That bounds but does not eliminate
query leakage: the server learns a 20-bit prefix per lookup and can correlate repeated
queries to infer which identity classes an analyst probes.

PIR removes even that prefix leakage: the client learns only whether a candidate
hash is present; the server learns nothing about the queried hash. Trajectories:
- Cloudflare open-source PIR for password breach checks (2024) demonstrates
  production single-server PIR, validating the SimplePIR/DoublePIR line.
- k-anonymity remains the pragmatic low-sensitivity baseline; PIR matters where
  the analyst's search pattern itself is the sensitive artifact (which
  identities, which credentials, at what frequency).

Core decomposition: k-anonymity hides the record; PIR hides the query. The
interest pattern is exactly what an observing adversary wants to infer. See
[[autonomous-osint-agent-opsec-attribution-risk]].

References: Cloudflare PIR engineering posts (2023-2024); Hunt, HIBP k-anonymity API (2018).
