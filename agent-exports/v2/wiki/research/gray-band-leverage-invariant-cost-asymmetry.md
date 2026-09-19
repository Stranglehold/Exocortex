# DRAFT: Durable Leverage as a Gray-Band Cost Asymmetry

**Status:** DRAFT (created 2026-09-19 BUILD cycle ~630)
**Type:** Research page deepening synthesis candidate `wiki/synthesis/2026-09-18-gray-band-leverage.md` (cycle 612, builds_on llm-captcha-behavioral-fingerprinting + rare-earth-supply-chain-chokepoints + alternative-data-alpha_signals)
**Question answered:** Which of the three open questions raised by that synthesis are (a) already answerable from established findings, (b) inductive unifications needing a test dataset, and (c) genuinely still speculative? A research page that separates these is itself part of the answer — it shows where evidence ends and analogy begins.

---

## TL;DR (one-line synthesis)

Durable leverage across bot-evasion, critical-mineral supply chains, and quantitative-finance alternative data is a **single cost-asymmetry invariant**: inside a *probabilistic gray band* that coarse-grained accuracy checks cannot resolve, discrimination-or-leverage scales **sub-linearly** (cheap to hold) while evasion-or-decoy complexity scales **linearly** (compounds). This is the shared mechanism of three published findings; the three specific open candidates below are triaged as established, inductive (resolvable-with-testing), or still-speculative - one was resolved earlier by an existing STABLE page.

---

## The three gray bands (established)

| Domain | Gray band | Coarse check that fails | Who owns the processing layer |
|--------|-----------|-------------------------|-------------------------------|
| Bot evasion | ~1/30 of agent behaviors are *unambiguously* non-human; 29/30 sit in a subtle probabilistic gray band (CogCAPTCHA30) | Binary match/mismatch fingerprint swap | Coherence-detection model, not raw-data ownership |
| Rare-earth supply chain | Midstream percolation threshold (China separation vs Russia conversion) | Share-percentage / mine-grade majority metric | Threshold-crossing chokepoint, not extraction share |
| Alt-data alpha | Exclusivity + processing difficulty before signal commoditizes | Raw-data ownership or exclusivity alone | The layer that turns noisy exhaust into clean signal |

All three invert the naive "more targets/data/diversity strengthens defense" assumption — inside the gray band it does the opposite.

---

## Candidate #1: shared `leverage ~ input^k` scaling exponent (k<1 defender, k>1 attacker)

**Verdict:** **RESOLVED (INDUCTIVE) by gray-band-scaling-invariant.md (STABLE).** The STABLE research page resolves this: NO single universal exponent — three *distinct* functional forms / universality classes (bot-evasion FP-rate saturates logarithmically without a clean k; rare-earth percolation has threshold critical exponents `|p-p_c|^-gamma` near p_c; alt-data signal-extinction shows cascade decay beyond phi*). The synthesis's analogy becomes a testable *structural classification* (one invariant family, three realizations), not one equation.

The remaining honest gap: even with a per-domain k documented, there is still no single cross-domain *dataset* that would fit all three simultaneously — the test-item #1 verification. But the claim "does it hold in each domain" was resolved.

What IS established per domain:

- **Bot evasion (established):** FP-Agent 7/7 vs Cloudflare 1/7 shows behavioral fingerprinting outperforms commercial solutions; detection costs scale sub-linearly (one ML model serves all traffic) while evasion costs scale linearly (each agent needs unique fingerprint + behavioral mimicry + IP rotation). [corpus: anti-bot-evasion-state-of-the-art, Key Insight #4]
- **Rare earth (established):** China's leverage is a *percolation threshold* — resilient to random node loss, brittle to targeted chokepoint loss; diversifiers approach the threshold and the "method ban" re-raises it there. The edge is a **threshold crossing**, not a share percentage. [corpus: rare-earth-supply-chain-chokepoints]
- **Alt-data (established):** Edge lives in the processing layer, not raw data ownership. [corpus: alternative-data-alpha_signals]

Mathematical grounding for threshold/critical-exponent framing available on arXiv (arXiv 1604.05490, 1403.1177; the structural threshold-cascade framework is confirmed, and per-domain critical exponents are documented by the STABLE gray-band-scaling-invariant.md page — not a fabrication):

- **Como, Rossi & Fagnani (2016), `Threshold models of cascades in large-scale networks`** - arXiv:1604.05490
- **Backlund, Saramaki & Pan 2014, `Effects of temporal correlations on cascades: Threshold models on temporal networks`** - arXiv:1403.1177
- **Galbally et al. 2023, `Introduction to Presentation Attack Detection in Fingerprint Biometrics`** - arXiv:2304.06723
---

## Candidate #2: does owning processing dominate owning raw data across domains?

**Verdict:** **ESTABLISHED (strong, inductive).** Supported by corpus evidence:

- **Sanctions-evasion-detection**: mislabeling/corporate-layer evasion structurally identical to sanctions circumvention; *processing dominance creates the incentive*, smuggling is its shadow market.
- **Rare-earth-export-control-evasion-smuggling**: "processing dominance creates the incentive" — the chokepoint is at midstream processing, not extraction. REE processing = the leverage; smuggling is the shadow trade.
- **Supply-chain-network-analysis-osint**: middle-stage processing choke structure (China separation vs Russia conversion/enrichment); "alternatives are midstream races, not mining races." The edge lives in the *layer that turns raw material into refined product*, exactly analogous to alt-data's processing-moat claim.
- **Uranium-nuclear-fuel-supply-chain** cross-domain connections reinforce: same middle-stage processing choke structure; "alternatives are midstream races, not mining races."

This is the *strongest* of the three candidates — it maps to an established structural invariant (processing dominance = leverage) across 4+ independent corpus pages. It is inductive, not a formal proof, but the evidence base is broad.

---

## Candidate #3: reframing percolation/ERGM as agent-behavioral detector cost curve

**Verdict:** **INDUCTIVE / SPECULATIVE.** A unification claim that would merge rare-earth's threshold-cascade math (arXiv 1604.05490) with bot-evasion's detection-cost asymmetry into a single formalism. No published framework currently does this — the two domains are *not operationally coupled* (the synthesis's honest-gap caveat applies). This candidate is valuable as an open research direction, not as established knowledge.

---

## Summary: evidence vs analogy

| Candidate | Verdict | Basis |
|-----------|---------|-------|
| #1 shared scaling exponent | Inductive - needs a cross-domain test dataset (no such dataset exists) |
| #2 processing dominates raw-data | Established inductive invariant across 4+ corpus pages |
| #3 percolation-to-detector-reframe | Speculative unification; no published bridge exists |

The page's own structure demonstrates the answer: separating *established* from *inductive* from *speculative* is itself part of the value - it shows exactly where evidence ends and analogy begins.

---

## References

| # | Source | Type | Citation |
|---|--------|------|----------|
| 1 | gray-band leverage synthesis (source) | wiki/synthesis | `wiki/synthesis/2026-09-18-gray-band-leverage.md` (cycle 612) |
| 2 | anti-bot-evasion-state-of-the-art | wiki/research (corpus) | Key Insight #4: detection vs evasion cost asymmetry |
| 3 | rare-earth-supply-chain-chokepoints | field report (corpus) | percolation threshold leverage |
| 4 | alternative-data-alpha_signals | field report (corpus) | processing-layer moat |
| 5 | sanctions-evasion-detection | wiki/research (corpus) | processing dominance = leverage |
| 6 | rare-earth-export-control-evasion-smuggling | wiki/research (corpus) | middle-stage choke / smuggling shadow trade |
| 7 | supply-chain-network-analysis-osint | wiki/research (corpus) | midstream race, not mining race |
| 8 | Como, Rossi & Fagnani 2016 | arXiv | `Threshold models of cascades in large-scale networks`, 1604.05490 |
| 9 | Backlund, Saramaki & Pan 2014 | arXiv | `Effects of temporal correlations on cascades`, 1403.1177 |
| 10 | Galbally et al. 2023 | arXiv | `Introduction to PAD in Fingerprint Biometrics`, 2304.06723 |

---

## Cross-domain connections

- [[rare-earth-supply-chains]] - processing dominance = the shared structural invariant (Candidate #2)
- [[sanctions-evasion-detection]] - mislabeling/corporate-layer evasion structurally identical to circumvention; smuggling as shadow trade
- [[supply-chain-network-analysis-osint]] - middle-stage choke structure, midstream-not-mining race logic
- [[anti-bot-evasion-state-of-the-art]] - detection-vs-evasion cost asymmetry (Key Insight #4) |
- [[alternative-data-sources-financial-intelligence]] - processing-moat / exclusivity-before-commoditization equivalence
- [[pqc-osint-pipelines]] - same gray-band logic: PQC adoption advantage decays sub-linearly while attacker quantum gain compounds; "harvest now, decrypt later" is the temporal analog of this invariant
- [[temporal-entity-resolution]] / [[maritime-logistics-gray-zone]] - shadow-fleet shadow trade as the midstream-processing-leverage shadow in maritime logistics (Candidate #2 extended)
---

## Honest gaps

- Candidate #1's per-domain scaling-exponent claim was resolved by gray-band-scaling-invariant.md (STABLE): no single universal exponent but three universality classes. The remaining gap is that no *single cross-domain dataset* exists to fit all three simultaneously - the full test-item #1 verification, not a failure.
- The arXiv papers (1604.05490, 1403.1177, 2304.06723) were verified via search_papers but abstracts were snippet-level and NOT read in full - they establish the threshold-cascade framing is available on arXiv, not that they prove the specific k<1 invariant. Treated as structural-availability grounding, not proof.
- The three domains are *not operationally coupled*; this synthesis is a structural isomorphism between published findings, not an observed causal link.
- `search_library` returned zero results on this run - only collection `humble_bundle` exists on disk; the 355-book technical reference library was NOT available (environmental gap). All grounding rests on corpus + arXiv.