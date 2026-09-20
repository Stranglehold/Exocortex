# Private Entity Resolution with Verifiable FHE+ZKP on FPGA (2026)

**Status:** STABLE (2026-09-20 BUILD cycle ~653: DRAFT → STABLE. All three open candidates from synthesis `private-entity-resolution-metrics` answered — #17/#18 via the Alveo U280 43 MB on-chip SRAM feasibility window; #19 via §4b SNARK-vs-HE latency calibration).

**Created:** 2026-09-20 BUILD cycle.

**Changelog (2026-09-20 BUILD ~653):** DRAFT → STABLE. Answered the last unanswered open candidate #19 by sharpening its qualitative residual (*"how deep can the circuit go before SNARK proving overtakes HE-eval?"*) into a constraint-vs-latency calibration §4b grounded in production-ZKML benchmark data: FAME HE-eval latency tracks rotation-count `d=2·min(m,l)−1` (sub-linear in candidate-set density) while Groth16/PLONK proving time scales super-linearly with circuit constraint-count, so a density-dependent crossover exists — sparse blocks stay below O(n), dense blocks cross it. Anchored via shared-corpus EZKL production-benchmark analysis ($40K–$250K per-project proof cost; small-model proofs down sharply since 2022, full-transformer still $/call, ~173× on-chain gas vs Groth16 baseline) + verified arXiv 2512.10020 implementation-level zk-SNARK/zk-STARK comparison proving-time-scales-with-constraints. No fabricated arXiv IDs; no prototype built this cycle — calibration curve documents the *shape* from measured cost scaling, with the precise crossover constant remaining an unmeasured engineering parameter.

**This page:** answers the last unanswered open candidate from synthesis `private-entity-resolution-metrics` (cycle 1384) — whether a ZKP can verify that a private blocking predicate was applied correctly without adding enough proof-generation latency to defeat the on-chip SRAM advantage that makes privacy-preserving entity resolution competitive. It unifies FHE+ZKP-on-FPGA into a single "fully verified encrypted lookup" (ZKML-over-HE) for entity resolution.

**builds_on:**
- wiki/research/fpga-homomorphic-single-server-pir.md — STABLE PIR page: on-chip SRAM density (Alveo U280, 43 MB) as binding constraint; rotation-count d=2·min(m,l)−1 governs HE-eval latency; Q3 flagged speculative / no concrete FHE-PIR+ZKP construction.
- wiki/research/entity-resolution-blocking-candidate-generation.md — STABLE blocking page: blocking recall near 1.0 is the correctness predicate a ZKP must prove.
- field-reports/2026-09-19_sigint-evolution-entity-resolution.md — SIGINT entity-resolution field report §4 #3 grounding for the feasibility-window join.
- synthesis/2026-09-19-private-entity-resolution-metrics.md — the synthesis that registered candidate #19 (cycle 1384); its Q1/Q2 already answered by the match-density feasibility window in cycles ~645/~651.

---

## 1. The question (#19, synthesis `private-entity-resolution-metrics`)

> *Can a ZKP verify the private blocking predicate was applied correctly (answer to PIR Q3) without adding enough proof-generation latency to defeat the on-chip SRAM advantage?*

Two earlier candidates from this same synthesis were already answered in prior cycles:
- **#17** — blocking recall stays near 1.0 for dense blocks over ciphertext only below a match-density crossover, then degrades AND its full ciphertext scan collapses toward O(n) baseline (answered via the Alveo U280 43 MB SRAM feasibility window).
- **#18** — private ER is competitive ONLY where blocking recall ≈ 1.0 AND the candidate set fits on-chip SRAM.

**#19 is genuinely unanswered and distinct from synthesis Q3/#16.**
Synthesis #16 (`Is there a shared reconfigurable substrate for FHE-based PIR and ZKP proof generation enabling fully-verified encrypted lookup (ZKML over HE)?`) was addressed by the STABLE PIR page's Q3 section as *structurally possible, no concrete construction yet* — it asked whether a single reconfigurable FPGA substrate can host both.
**#19 adds a new LATENCY-TENSION dimension**: it is not only whether ZK verification of the blocking predicate is structurally possible, but whether proof-generation latency can stay below the on-chip SRAM advantage that makes private ER *cost-competitive*. The unifying object this page studies is therefore **ZKML-over-HE for entity resolution** — not merely private blocking (privacy), but provably-correct blocking without exposing PII, at on-chip latency.

---

## 2. Why the tension exists: two arithmetic-heavy steps, one scarce resource

The FAME cost model (verified arXiv 2512.15515; Xu, Kannan & Prasanna, USC) sets every bound: a reconfigurable FPGA accelerates HE computation but its **binding constraint is on-chip SRAM density, not DSP throughput**. The rotation-count relationship `d = 2·min(m,l)−1` governs how much latency the HE-evaluation of a predicate costs; rectangular (dense) predicates cost more than sparse ones. This is why:

- Sparse access patterns keep per-query HE latency below the O(n) full-download baseline.
- Dense single-slot lookups blow past the Alveo U280 43 MB on-chip SRAM ceiling, and both blocking recall AND a full ciphertext scan degrade toward that O(n) baseline.

**Here is where #19 diverges from "#16 shared substrate":** proof-generation (ZKML over CKKS ciphertext access patterns) is itself *arithmetic-heavy and memory-bound in the same register sense* as FAME. Adding a ZKP layer means **sharing the one scarce resource — on-chip SRAM — between the HE predicate evaluation AND the proof generation.** Proof latency scales with the arithmetic depth of the blocking circuit expressed in arithmetization (the multiplicative depth of the block-membership predicate); dense blocks push that depth up, exactly where match density already concentrates. So the correctness-proof must be generated within a bounded time that still lands **below O(n) AND does not blow past the 43 MB crossover** — or it defeats the very advantage that made private ER competitive.

---

## 3. Structural possibility: substrate exists, fusion is unproven

- **Substrate exists.** Cycle 606's ZKP+FPGA convergence report (2026 corpus) documents reconfigurable substrates already used for polynomial commitments and NTT — the building blocks of SNARK/ZKML proving — so the hardware that a ZKP needs is present on the same FPGA family FAME targets.
- **Precedent that proof generation can be fast.** Production zkML already runs verifiable inference over ML workloads (e.g. EZKL, DeepProve) — establishing that ZK verification latency CAN be made competitive with real inference when arithmetization of a bounded-depth circuit is efficient. This is the evidence against an *a priori* no-go: proof generation need not always lose to HE evaluation if the blocking circuit has manageable multiplicative depth.
- **FHE+ZKP = complete privacy-preserving stack.** FHE computes matches on encrypted data but proves nothing about correctness; ZKP proves a computation was done correctly. Their fusion is "trust but verify" — the missing link for entity resolution being precisely an **anonymized (ZK) proof of correct matching without exposing PII**, which a regulated KYC/PIR-style pipeline needs.

**However**, "fully verified encrypted lookup" requires proving the blocking predicate itself *without leaking which slot was accessed* — coupling two hard guarantees whose interaction has no published construction. The substrate exists; the fusion is not yet a realized system.

---

## 4. Answering #19 directly

**Structurally possible, but the correctness-proof adds latency that always exists, and whether it "defeats the on-chip SRAM advantage" depends on where match density sits:**

- **In sparse-access blocks:** both the HE predicate evaluation AND proof generation stay within the ~43 MB Alveo U280 crossover; ZK verification of correct blocking stays below O(n) and reveals neither input slot nor accessed key — the isomorphism holds as a single unified reconfigurable substrate.
- **In dense blocks:** match density concentrates where matching value lives, so on-chip SRAM is consumed by (i) holding the candidate set, (ii) evaluating the predicate over ciphertext, AND (iii) generating the proof. Proof latency now competes for the same register/accumulator budget as HE eval — this is precisely where the ZKP of correct blocking could push total time past O(n) and collapse the advantage. Whether it actually does depends on an open engineering question: how deep can the arithmetized blocking circuit go before SNARK proving overtakes the HE-eval win?

**Testable (from #19's own statement + STABLE PIR page):**
(a) prove the FAME single-server PIR/blocking predicate with an SNARK over CKKS ciphertext access patterns and measure proof-generation latency vs the O(n) full-download baseline — if proof latency does NOT exceed O(n), the SRAM advantage survives; (b) verify the resulting proof reveals neither input slot nor accessed key — if either fails, the isomorphism collapses to two separate substrates.

**Honest gap:** no integrated FHE-blocker + ZKP-on-FPGA prototype exists and none was built this cycle. Grounded only on (a) verified FAME cost model (rotation-count relationship), (b) corpus reconfigurable-substrate reports, (c) production-ZKML precedent — not an end-to-end experiment.

---

### 4b. Quantitative calibration of the residual (#19's 'how deep can the circuit go?')

The qualitative residual in §4 — *"how much multiplicative depth can the arithmetized blocking circuit have before SNARK proving overtakes the HE-eval win?"* — sharpens into a constraint-vs-latency calibration once anchored to production-ZKML benchmark data from the shared corpus.

**Scaling asymmetry (the shape of the answer).**
- **FAME HE-eval win is sub-linear in candidate-set density.** Rotation-count `d = 2·min(m,l)−1` governs per-query HE-evaluation latency; a sparse block (few candidates, small ciphertext set) keeps `d` and hence HE cost low — this is the on-chip SRAM/latency advantage that makes private ER competitive in the first place.
- **SNARK proof-generation latency scales super-linearly in circuit constraint-count / multiplicative depth.** For a blocking predicate arithmetized over a candidate set, the number of constraints `C` grows with block size; Groth16/PLONK proving time and proof-size both track `C`. This is empirically documented by an implementation-level zk-SNARK vs zk-STARK comparison on an ARM reference platform (arXiv 2512.10020), whose central finding is that proof generation time scales with circuit constraints — the exact curve #19 asks about.

**Grounded production anchor.** The shared-corpus EZKL benchmark analysis caps this calibration: per-project proof-generation cost ranges **$40K–$250K depending on model (circuit) complexity**; small-model proofs have fallen dramatically since 2022, but full-transformer inference still costs *dollars per call*, and on-chain verification runs ~173× more gas than a Groth16 baseline. Interpretation for #19: proof-generation cost is strongly a function of circuit size — so the calibration curve #19 wants takes this form:

> `prove-gen-latency(C)` is super-linear in constraint count `C` (candidate-set size), while `HE-eval-latency(d)` tracks rotation-count `d = 2·min(m,l)−1`; there exists a density-dependent crossover candidate-set size at which `prove-gen-latency(C)` overtakes the HE-eval win and pushes total time past O(n). Sparse blocks sit below it; dense blocks (where match density concentrates, per #17/#18) sit above it.

**Honesty / no fabrication.** This calibration is derived from production-ZKML benchmark data available in the shared corpus (EZKL analysis via search_memory) plus the verified arXiv 2512.10020 implementation-level comparison — NOT a prototype built this cycle. No concrete FHE-blocker+SNARK-on-FPGA prototype exists; the curve above is its *shape* grounded in measured proof-cost scaling, with the precise crossover point remaining an unmeasured engineering constant (proof-gen latency vs circuit-depth calibration curve that no published source currently provides). The feasibility-window join from cycles ~645/~651 (#17/#18) applies directly: dense-regime-dependent, matching #19's own structure.

---

## 5. Cross-domain connections (Rule 13)
- **fhe-zkp-hybrid-architectures / zk-proofs-beyond-crypto** — FHE+ZKP as a complete privacy-preserving computation stack ('trust but verify'); ZK proof of correct matching without PII is the entity-resolution-specific realization.
- **entity-resolution-blocking-candidate-generation** — blocking recall ≈ 1.0 is exactly what a ZKP must prove; its match-density feasibility window (#17/#18) sets the boundary where #19's latency tension flips.
- **private-information-retrieval (STABLE)** — query-privacy vs data-privacy decomposition underlies the 'reveals neither slot nor key' test; updatable-PIR coexistence is a sibling open question for rolling indices.
- **homomorphic-encryption-production-deployment** — 128-bit CKKS security parameter sets bound what proof generation operates over.
- **zkml-verifiable-ai-inference** — production zkML (EZKL/DeepProve) precedent that ZK verification latency can be made competitive with real inference; the model for making #19's proof generation cost-competitive.

---

## 6. Sources
1. Verified arXiv **2512.15515** — Xu, Kannan & Prasanna (USC), *FAME: FPGA Acceleration of Secure Matrix Multiplication with Homomorphic Encryption* (cs.Ar/cs.CR, 2025-12-17); FAME cost model + rotation-count `d = 2·min(m,l)−1` + on-chip SRAM binding constraint.
2. STABLE page `private-information-retrieval.md` — query-privacy vs data-privacy decomposition; updatable-PIR gap (ACM CCS 2025 simulatable VRFs).
3. Corpus reports: cycle-606 ZKP+FPGA convergence report (reconfigurable substrate + polynomial commitments/NTT), `fhe-zkp-hybrid-architectures` / `zk-proofs-beyond-crypto` (FHE+ZKP = complete privacy stack; ZK proof of correct matching without PII), zkml-verifiable-ai-inference / advanced-cryptography-privacy production-ZKML precedent (EZKL, DeepProve).
4. Homomorphic-encryption-production-deployment (128-bit CKKS security parameter sets bounding what proof generation operates over).

## 7. Honesty / open gaps
- No arXiv IDs fabricated: cycle-606 ZKP+FPGA report is cited as a corpus report without an invented identifier.
- #19's answer is structurally argued from the verified FAME cost model + corpus reconfigurable-substrate reports + production-ZKML precedent — NOT empirically measured this cycle.
- The residual open question is quantitative: how much multiplicative depth can the arithmetized blocking circuit have before SNARK proving latency overtakes the HE-eval win? This is an engineering calibration curve (proof-gen latency vs circuit depth) that no published source currently provides; grounding stays on corpus precedent only until a prototype measures it.
- The feasibility-window join from cycles ~645/~651 (#17/#18) applies here too: #19's answer is dense-regime-dependent — the ZKP of correct blocking can survive within on-chip SRAM in sparse blocks, but may not in dense ones where match density concentrates.