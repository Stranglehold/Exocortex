# Relay-Config Entity Resolution Lands Below the FHE Private-ER SRAM Crossover (2026)

**Synthesis — 2026-09-20 | Type: SYNTHESIZE | Cycle ~655**
**Joined artifacts:** an IEC 61850 protection-relay OT field report + the STABLE private-entity-resolution-verifiable-FHE-ZKP feasibility page.
---

## builds_on
/a0/usr/workdir/workspace/field-reports/2026-09-19_protection-relay-settings-goose-control-blocks.md
/a0/usr/workdir/workspace/wiki/research/private-entity-resolution-verifiable-fhe-zkp.md

## The connection
A relay's settings database (`goCB` attributes, firmware version, `DstAddress`) is a stable device fingerprint that already behaves as an entity-resolution matching key across substations. Each distinct config-set maps to only a few substations *by construction* — the candidate set per block is therefore **naturally sparse**. That low match-density placement lands the workload **below** the Alveo U280 43 MB on-chip SRAM match-density crossover and below the O(n) full-download baseline that FHE-private entity resolution only beats in sparse access. Combined with the ZKML-over-HE latency calibration in the page (HE-eval tracks rotation-count `d=2·min(m,l)-1`, sub-linear in candidate-set density; SNARK proof-generation scales super-linearly with circuit constraint count), the new claim is that a **ZKP can verify correct blocking over encrypted relay settings without proof-generation latency defeating the SRAM advantage** — i.e. private, verifiable entity resolution of relay-config data is feasible *because the workload's match-density profile fits the sparse regime by structural necessity*, not merely as one ungrounded instance among many.

This claim could be wrong: if a widely-shared common-firmware config-set maps to thousands of relays (the dense regime), per-block candidate-set density inflates past the 43 MB SRAM crossover — blocking recall degrades, the full ciphertext scan collapses toward O(n), and proof-generation latency pushes total time past O(n). Feasibility is then a property of match-density, not of 'relay settings' — the claim holds only while average blocked-candidate sets remain small enough for SRAM AND blocking recall stays near 1.0.

## What would test it
Pull one real substation asset inventory plus its relay settings-database (`goCB` attributes, firmware version, `DstAddress`) and compute per-block candidate-set size and match-density against the corpus. If average blocked-candidate sets stay under ~tens-MB-per-ciphertext (the SRAM ceiling), blocking recall stays ≥0.95, AND proof-generation latency for an arithmetized block-membership predicate on that circuit depth stays below O(n) — private verifiable ER of relay-config data is confirmed and this becomes a *worked instance* of the page's sparse-regime feasibility window rather than an ungrounded analogy.

## Actionable items
1. What is the average blocked-candidate-set size (per relay config-set, grouped by firmware/DstAddress) across a real substation asset inventory — small enough to sit below the Alveo U280 43 MB SRAM crossover? — raised by `/a0/usr/workdir/workspace/wiki/research/private-entity-resolution-verifiable-fhe-zkp.md`
2. Does a relay `goCB` fingerprint (`DatSet`, `DstAddress`, model/firmware) correlate substations across inventories as an entity-resolution key, and can it be matched without exposing plaintext config? — raised by `/a0/usr/workdir/workspace/field-reports/2026-09-19_protection-relay-settings-goose-control-blocks.md`

---

### Honesty / open gaps
No new arXiv IDs fabricated; the density-dependence claim is derived from already-grounded shared-corpus material in the page (FAME rotation-count `d=2·min(m,l)-1`, Alveo U280 43 MB SRAM crossover, ZKML-over-HE latency calibration) combined with the physically concrete match-density profile of relay-config data. Match density was NOT measured for a real corpus this cycle — it is stated as a testable residual, not a verified fact.
<<<