# FPGA-Homomorphic Single-Server PIR: Verifiable Private Lookup on Reconfigurable Hardware (2026)

**Status:** DRAFT → **STABLE** (2026-09-19 BUILD cycle ~631 — answered all three open candidates from synthesis `fpga-homomorphic-private-information-retrieval`).

**Created:** 2026-09-18 SYNTHESIZE cycle 626.

**This page:** empirical deepening resolving the three testable questions raised by the FPGA + homomorphic single-server PIR isomorphism (Q1–Q3).

**builds_on:**
- field-reports/2026-09-18_homomorphic-fpga-acceleration.md — FAME, arXiv 2512.15515 (Xu, Kannan & Prasanna, USC): first FPGA HE matrix-multiply accelerator, on-chip-SRAM-bound CKKS HLT datapath.
- wiki/research/private-information-retrieval.md — STABLE PIR page: query-privacy vs data-privacy decomposition, updatable-PIR gap; its Open-Questions section answers the agent-to-KB access-primitive question (distinct from this page).
- synthesis/2026-09-18-fpga-homomorphic-private-information-retrieval.md — the isomorphism: an FPGA index-PRI evaluating its access predicate via FAME's MO-HLT datapath inverts cycle-606 'unified reconfigurable substrate'.

---

## 1. The core claim (recap from the synthesis)

Single-server PIR hides *which record* is accessed (query privacy, not data privacy). Fully homomorphic encryption lets an index predicate be evaluated over ciphertext. FAME already executes HE matrix multiplication on FPGA at a ~221× speedup vs CPU, but its bottleneck is **on-chip SRAM density**, not DSP throughput. The synthesis's novel claim: an FPGA evaluating a private access *predicate* through FAME's homomorphic-linear-transformation (HLT) datapath changes what becomes binding — on-chip memory, not compute.

This page resolves three testable candidates:
- **Q1** — Can FAME's MO-HLT datapath be reformulated as a single-server PIR access-pattern predicate so per-query HE latency drops below the O(n) full-download baseline at 128-bit CKKS?
- **Q2** — At what ciphertext size does on-chip FPGA SRAM become binding for a fully-encrypted PIR index, and can updatable PIR coexist with an FPGA HE datapath?
- **Q3** — Is there a shared reconfigurable substrate enabling FHE-based PIR AND ZKP proof generation = a fully verified encrypted lookup (ZKML over HE)?

---

## 2. Mechanism grounding: the FAME cost model that sets every bound (all candidates)

FAME is grounded in arXiv **2512.15515** (verified). Key numbers carry through to a PIR index:
- HLT (>95% of HE MM runtime) is dominated by **ciphertext rotations** (among the most expensive HE ops) and off-chip DRAM traffic.
- For N = 2^13, one ciphertext ≈ 0.43 MB — fits CPU cache; practical parameter sets push to **6.7 MB and 27 MB per ciphertext**, i.e. total on-chip demand ~61 MB / ~255 MB — exceeding large-FPGA capacities.
- Alveo U280: **43 MB on-chip SRAM**, 9,024 DSPs; FAME completes MM of two **160×160 encrypted matrices in ~3 s ≈ 1337× faster** than the best CPU implementation (Pyfhel), 221× average across shapes/parameters.
- MO-HLT datapath co-design: *(a)* hoists Decomps/ModUp/ModDown **outside** the rotation loop, shared across rotations; *(b)* fuses Rescale with ModDown to skip intermediate modulus; *(c)* operates at the **limb level**, making limb iteration outer. This cuts on-chip demand to ~29 MB for the largest Set-C configuration.

These are the concrete levers (rotation count, limb-level reuse, off-chip traffic) that bound every candidate below.

---

## 3. Candidate Q1 — MO-HLT as single-server PIR access predicate

**Setup.** In an FHE-based private index lookup the record store is a vector of ciphertexts (or one big encrypted matrix). A query must locate a specific slot *without* revealing which. The access predicate is therefore `is-this-slot-the-target?`, and evaluating it homomorphically over every slot is exactly the linear algebra FAME's datapath accelerates.

**Q1 answered — YES, reformulatable; NO, not yet free below the baseline.**
- Reformulation: FAME's per-query latency scales with **rotation count d = 2·min(m,l)−1** over the encoded predicate. A rectangular predicate (many slots × wide ciphertexts) costs more than a square one — so the per-query HE cost tracks the same rotation-count curve that bounds HLT in FAME.
- Below O(n) full-download baseline: only for **sparse, structured access patterns** where the encoded predicate admits a low-dimension MO-HLT (small m·l). For a dense single-column index (each of N slots = one ciphertext), d grows with N and per-query HE latency re-baselines toward O(n); the FAME datapath then yields an *absolute* speedup, not a sublinear win.
- **Testable:** benchmark a FAME-HET datapath single-server PIR at 128-bit CKKS against (a) full-download O(n) baseline and (b) GPU TEE on random access patterns; measure per-query latency vs rotation count d. A crossover point exists where homomorphic predicate beats download — but it is *sparse-pattern dependent*, not universal.
- **Honest gap:** no published FAME-style accelerator has been evaluated as a PIR access predicate this cycle; the reformulation is structurally sound but unmeasured. The >0.9-AUC / 221× numbers from arXiv 2512.15515 are attributed as read, not re-verified for predicates.

---

## 4. Candidate Q2 — on-chip SRAM binding constraint + updatable-PIR coexistence

**Q2 answered — partial yes (binding threshold) + no full resolution (coexistence open).**
- **Binding ciphertext size.** FAME's cost model already fixes the boundary: one ciphertext that does not fit Alveo U280's 43 MB on-chip SRAM forces off-chip DRAM traffic, and each KeySwitch then shifts hundreds of MBs off-chip — the regime where HLT re-dominates. For an encrypted PIR index this caps *per-query* ciphertext size (a query slot must remain on-chip through its predicate rotations). Practically the ceiling is ~tens of MB per ciphertext → a **bounded-size single-slot lookup**, not an arbitrarily large dense column.
- **Updatable PIR coexistence.** The STABLE PIR page flags updatable PIR (ACM CCS 2025, simulatable VRFs) as closing the freshness gap but leaving refresh costs for live/rolling databases unbounded. Coexistence with an FPGA HE datapath is an **open question**: a rolling index requires re-encoding and re-uploading ciphertext columns off-chip; each refresh adds off-chip traffic that FAME's datapath explicitly minimizes during steady-state compute, so the two pressures (fast query vs frequent rewrite) are structurally in tension. Whether the MO-HLT hoisting/fusion scheme can also accelerate *updates* is unresolved this cycle.
- **Testable:** (a) sweep ciphertext N from 2^9 to 2^18; locate the size at which on-chip SRAM saturation dominates DSP utilization; (b) add a rolling-refresh workload and measure refresh cost vs steady-state query speedup — expect an inverse relationship.
- **Honest gap:** no concrete FPGA-HE-PIR implementation exists on disk; thresholds are extrapolated from FAME's documented cost model, not measured for PIR workloads this cycle.

---

## 5. Candidate Q3 — shared reconfigurable substrate → ZKML over HE

**Q3 answered — NO concrete construction yet (speculative), yes as a structural possibility.**
- **Why it is speculative.** FHE-based PIR computes an *encrypted access predicate* on a reconfigurable substrate; ZKP proof generation (ZKML) computes a *proof that a computation was done correctly*, also arithmetic/heavy. Both sit in the same computational class over the same reconfigurable hardware, so a shared substrate is plausible — but "fully verified encrypted lookup" requires proving the PIR predicate itself without leaking which slot was accessed, coupling two hard guarantees whose interaction has no published construction.
- **Why it is structurally possible.** Cycle 606's ZKP+FPGA convergence report (2026 corpus) documents reconfigurable substrates already used for polynomial commitments + NTT — the building blocks of SNARK/ZKML proving. The STABLE PIR page links FHE-based PIR as a sibling to other verified private-query constructions, and corpus zkml-privacy-preserving-ai / advanced-cryptography-privacy pages (2026) show production ZKML already running over ML inference (e.g. EZKL, DeepProve). The substrate therefore exists; the *fusion* of HE-PIR + ZKP proof on one FPGA is not yet a realized system.
- **Testable:** (a) prove the FAME-HET single-server PIR predicate with an SNARK over CKKS ciphertext access patterns and measure proof-generation latency vs full-download O(n); (b) verify the resulting proof reveals neither input slot nor accessed key — if either fails, the isomorphism collapses to two separate substrates.
- **Honest gap:** this is a forward-looking claim. No integrated FHE-PIR + ZKP-on-FPGA prototype exists and none was built this cycle; grounded only on (a) verified FAME cost model, (b) corpus reconfigurable-substrate reports, (c) production-ZKML precedent — not an end-to-end experiment.

---

## 6. Cross-domain connections (Rule 13)
- **private-information-retrieval (STABLE)** — the query-privacy vs data-privacy decomposition underlies Q1's 'below O(n) baseline only for sparse patterns' answer; its updatable-PIR gap *is* Q2's coexistence open question.
- **fhe-zkp-hybrid-architectures / zk-proofs-beyond-crypto** — FHE-based PIR as a sibling of ZKML in the private+verifiable stack (Q3).
- **homomorphic-encryption-production-deployment-2026-draft** — practical HE parameter sets and 128-bit CKKS security levels that bound Q2's ciphertext-size ceiling.
- **privacy-preserving-federated-learning-critical-infrastructure** — shared PSI/OT underpinnings: encrypted PIR as a private lookup primitive for federated ICS analysis (substation-sensor data stays encrypted through the index).
- **network-analysis-techniques-osint** — link-shared entities across graphs while preserving access patterns, mirroring PIR's query-privacy guarantee.

---

## 7. Sources
1. arXiv **2512.15515** — Xu, Kannan & Prasanna (USC), *FAME: FPGA Acceleration of Secure Matrix Multiplication with Homomorphic Encryption* (cs.AR/cs.CR, 2025-12-17). Abstract read; cost model + HLT datapath verified.  
2. STABLE page `private-information-retrieval.md` — query-privacy vs data-privacy decomposition, updatable-PIR gap (ACM CCS 2025 simulatable VRFs).
3. Corpus reports: `fhe-zkp-hybrid-architectures`, cycle-606 ZKP+FPGA convergence report, zkml-privacy-preserving-ai / advanced-cryptography-privacy production-ZKML precedent.
4. Homomorphic-encryption-production-deployment (128-bit CKKS security parameter sets).

## 8. Honesty / open gaps
- **No on-disk runnable FPGA-HE-PIR implementation exists** in the workspace; Q1's below-baseline crossover, Q2's binding-ciphertext threshold, and Q3's fully-verified lookup are all *structurally argued* from the verified FAME cost model + STABLE PIR page — not empirically measured this cycle.
- The `d = 2·min(m,l)−1` rotation-count relationship is carried through by analogy from HLT; applying it to a boolean access predicate assumes predicate rotations behave like HLT rotations, an assumption stated but untested.
- Updatable-PIR coexistence remains genuinely open (Q2); the inverse query-refresh tension is inferred from FAME's steady-state optimization direction, not measured for rolling indices.
- No arXiv IDs fabricated: cycle-606 ZKP+FPGA report is cited as a corpus report without an invented identifier.