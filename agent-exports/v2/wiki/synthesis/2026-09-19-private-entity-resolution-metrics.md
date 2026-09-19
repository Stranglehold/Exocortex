# Private Entity Resolution in the Low-Density Regime — A Feasibility Frontier

title: Private Entity Resolution in the Low-Density Regime — A Feasibility Frontier
tags:
  - Data Aggregation & Entity Resolution
  - Privacy-Preserving Computation
  - FPGA Homomorphic Encryption
status: DRAFT
created: 2026-09-19
builds_on:
  - /a0/usr/workdir/workspace/wiki/research/entity-resolution-blocking-candidate-generation.md
  - /a0/usr/workdir/workspace/wiki/research/fpga-homomorphic-single-server-pir.md
  - /a0/usr/workdir/workspace/field-reports/2026-09-19_sigint-evolution-entity-resolution.md
cited_from:
  - arXiv 2512.15515 (FAME: Xu, Kannan & Prasanna, USC, 2025)

## The Connection

Entity resolution is dominated by its **blocking stage**: a cheap coarse partition that collapses the `O(n²)` comparison space to a tractable candidate set. Blocking recall is correctness-bounded *by design* — if blocking drops a true pair, no downstream matching stage can recover it (entity-resolution-blocking-candidate-generation.md). A privacy-preserving index must evaluate this blocking predicate over **ciphertext** rather than plaintext, which the FPGA-Homomorphic single-server PIR page shows inverts FAME's binding constraint: on-chip SRAM density, not DSP throughput, limits evaluation; and its Q1 resolution showed a private access predicate stays *below the classical O(n) baseline only for sparse match patterns*, because per-query HE latency tracks rotation-count `d = 2·min(m,l)−1` (fpga-homomorphic-single-server-pir.md). The SIGINT field report seeds this directly (§4 #3): “can a ciphertext-bounded entity-resolution index resolve cross-register identities without ever exposing plaintext? That would make the privacy layer an *engine* of the resolution interest, not merely its shield.”

**Claim (none states this alone):** A ciphertext-bounded, FPGA-accelerated HE-based entity-resolution index can preserve record privacy while keeping **blocking recall ~1.0**, but only in a feasibility window bounded by *match density*: once block match-density crosses the on-chip SRAM crossover (~tens-MB-per-ciphertext for Alveo U280's 43 MB), private blocking (a) must exceed SRAM capacity and either spill or degrade recall, and (b) its full ciphertext scan collapses to the O(n) baseline that PIR's below-baseline result already restricts to sparse access. That is, **privacy-preserving ER trades query-privacy directly against blocking-recall in exactly the dense regime where matching value concentrates** — so private ER is feasible only where match density is low enough for (i) on-chip SRAM to hold the candidate set and (ii) recall to stay near 1.0 together.

## What Would Test It

Build a synthetic blocked candidate set with controllable match density; run FAME's verified cost model (arXiv **2512.15515**, HLT datapath, rotation-count `d = 2·min(m,l)−1`) to compute per-ciphertext rotation and SRAM demand for an AND-of-block-membership predicate versus classical blocking; at what match-density does private recall first fall below classic recall while still staying below the O(n) baseline? This tests both arms: (a) on-chip SRAM capacity ceiling (Q2 of the PIR page — Alveo U280 43 MB caps ~tens-MB-per-ciphertext dense single-slot lookups), and (b) the sparse-pattern-only below-baseline result already resolved for Q1. A concrete FHE-PIR+ZKP-on-FPGA construction would additionally answer Q3, which currently has no instance yet.

## Actionable Items

- Does blocking recall stay ≈1.0 for dense blocks when evaluated over ciphertext, or does the AND-of-block-membership predicate drop true pairs once match density crosses the on-chip SRAM ceiling? — raised by entity-resolution-blocking-candidate-generation.md + fpga-homomorphic-single-server-pir.md
- Is the below-baseline feasibility of private ER bounded by match-density (not merely query frequency), such that privacy-preserving ER is only competitive where blocking recall can remain ~1.0 AND the candidate set fits on-chip SRAM? — raised by fpga-homomorphic-single-server-pir.md + sigint-evolution-entity-resolution field report §4 #3
- Can a ZKP verify the private blocking predicate was applied correctly (answer to PIR Q3) without adding enough proof-generation latency to defeat the SRAM advantage? — raised by fpga-homomorphic-single-server-pir.md + entity-resolution-blocking-candidate-generation.md
