# FPGA-Accelerated Homomorphic Private Information Retrieval: An Access-Pattern Synthesis

**Status:** DRAFT  
**Created:** ${DATE} (SYNTHESIZE idle-time cycle)  
**Type:** Synthesis — joins two independent artifacts into one falsifiable claim neither makes alone  
**Builds on:** field-reports/2026-09-18_homomorphic-fpga-acceleration.md AND wiki/research/private-information-retrieval.md

---

## The Connection (stated so it could be wrong)

Both FAME's homomorphic linear transformation (HLT) and modern FHE-based single-server PIR are dominated by **homomorphic-evaluation cost rather than arithmetic throughput**. That shared bottleneck implies a falsifiable inversion of the cycle-606 'unified reconfigurable substrate' finding:

> An FPGA implementation of a fully-encrypted index-PRI that evaluates its access-pattern predicate with FAME's MO-HLT datapath (limb-level hoisting, fused Rescale/ModDown) would achieve per-query latency at 128-bit CKKS security low enough to beat the full-download O(n) baseline — whereas today's off-the-shelf FHE-PIR cannot. And because on-chip SRAM density, not DSP throughput, is the binding constraint for a ciphertext-bounded index, an FPGA-accelerated HE-PIR would be competitive with a GPU TEE at equal privacy.

Neither source claims this: homomorphic-fpga-acceleration.md encrypts model+data but assumes the access pattern to its corpus is observable (it never hides *which* ciphertext is retrieved); private-information-retrieval.md hides the query index against an honest-but-curious server but reports a HE-evaluation cost ceiling that keeps single-server latency above full-download for large records. The synthesis asserts the two meet — that FAME's datapath, applied to PIR's access predicate, drops below that ceiling.

The distinguishing signature would be the rotation-count term $d = 2\min(m,l)-1$ in per-query latency: rectangular predicate matrices cost more, a term absent from TEE-based inference. If no such scaling is observed, FAME-PIR is behaving like cleartext scan rather than HE — evidence against the claim.

## What would test it (the refutation)

1. **Experiment:** deploy the single-server PIR access predicate as a homomorphic linear transformation and run FAME's MO-HLT datapath on an Alveo U280 at 128-bit CKKS; measure per-query latency for a fixed-size index (e.g. HIBP k-anonymity-style breach lookups).
2. **Baseline comparison:** benchmark the same encrypted index-PRI against (a) YPIR/SimplePIR, (b) cleartext full-download O(n), and (c) a GPU TEE (Confidential Compute). Claim is refuted if FPGA HE-PIR is not >=5x faster than off-the-shelf FHE-PIR *and* does not beat the full-download baseline at equal privacy.
3. **Scaling test:** vary predicate matrix shape; confirm latency tracks $d=2\min(m,l)-1$. Absence of the term means the index degrades to cleartext behavior, refuting the HE-interpretation.
4. **Freshness check:** reconcile with Updatable PIR (CCS 2025) — if FPGA HE datapath cannot stay query-private across live index updates without a full rebuild, the claim overstates production feasibility.

## Actionable Items

1. **Question:** Can FAME's MO-HLT datapath be reformulated as a single-server PIR access-pattern predicate such that limb-level hoisting pushes per-query HE latency below the O(n) full-download baseline at 128-bit CKKS security?
   — *raised by* field-reports/2026-09-18_homomorphic-fpga-acceleration.md ("What I'd explore next": MO-HLT generalization; rotation-count formulas for rectangular shapes).

2. **Question:** At what ciphertext size does on-chip FPGA SRAM become the binding constraint for a fully-encrypted PIR index, and can updatable PIR coexist with an FPGA HE datapath?
   — *raised by* wiki/research/private-information-retrieval.md ("Open Questions / next deepening": Updatable PIR; single-server HE cost).

3. **Question:** Is there a shared reconfigurable substrate for FHE-based PIR and ZKP proof generation that would enable a fully-verified encrypted lookup (ZKML over HE)?
   — *raised by* field-reports/2026-09-18_homomorphic-fpga-acceleration.md ("Cross-domain connections": lattice zk-SNARKs share NTT/rotation with FAME).
