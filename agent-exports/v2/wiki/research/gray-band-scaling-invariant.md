# Wiki Research: Shared Scaling Exponent in the Gray-Band-Leverage Invariant

**Status:** STABLE
**Date:** 2026-09-18
**Builds on:** wiki/synthesis/2026-09-18-gray-band-leverage.md; field-reports/2026-09-18_llm-captcha-behavioral-fingerprinting.md; field-reports/2026-09-16_rare-earth-supply-chain-chokepoints.md; field-reports/2026-09-16_alternative_data_alpha_signals.md
---

## The question (from the gray-band-leverage synthesis, test-item #3)

The 2026-09-18 SYNTHESIZE joined three disparate fields — bot-evasion, rare-earth supply chains, and alt-data alpha — into one invariant: durable leverage in a probabilistic "gray band" resolvable by coarse-grained accuracy checks. It proposed three actionable items, the sharpest of which is:

> *Would a shared `leverage ~ input^k` scaling exponent exist across all three domains*?

If true, the isomorphism would be quantitative (a single power-law) rather than metaphorical. This page resolves that question.

---

## Short answer

**No — there is not a single universal exponent, but the isomorphism is nonetheless real and can now be stated precisely.** The three domains share a *qualitative* cost-asymmetry law (sub-linear defender cost vs super-linear attacker scaling) yet each follows a **different functional form** with its own critical exponents or decay constant. Promoting `leverage ~ input^k` from analogy to mechanism therefore requires building a cross-domain dataset the synthesis explicitly flagged as absent.

This is the honest, useful state: move the claim from *structural analogy* (which it already was) to *precise structural classification* — same invariant shape, three distinct mathematical realizations.

---

## The three domains' actual functional forms

### 1. Bot-evasion (CAPTCHA behavioral fingerprinting)
Detection cost vs attacker sample diversity follows a **saturating logarithmic/sigmoidal curve**: detector false-positive rate grows sub-linearly and flattens as diversification grows, while evasion coverage grows linearly. Formally `FP_rate ~ log(diversity)` or a logistic — *not* a clean power law. The invariant here is the cost asymmetry's monotonic-but-concave shape; there is no well-defined exponent k because detection saturates rather than scales.

### 2. Rare-earth supply chains (percolation)
This domain has genuine, measurable scaling exponents from statistical-mechanics percolation theory. Near the critical threshold `p_c`, cluster size diverges as `~ |p - p_c|^-gamma` and the spanning probability follows a power law with well-defined universal exponents belonging to a universality class. China's leverage is a **threshold-crossing** (brittle below `p_c`, sharp above), i.e. an authentic power-law region with real critical exponent gamma.

### 3. Alt-data alpha (exclusivity decay)
Value decays through a **signal-extinction cascade**: beyond adoption threshold phi*, decay of one signal class accelerates competition for remaining signals — non-linear but best modeled as an inflection/threshold function, not the percolation power law. Its functional form resembles `value ~ exp(-lambda * commoditization)`-ish or a critical-threshold step, distinct from (2).

---

## Why they are isomorphic structurally but not quantitatively

Corpus grounding confirms each domain exhibits nonlinear-cost-at-critical-threshold behavior:
- **Complex adaptive systems**: phase transitions at critical thresholds; scale-free networks show power-law degree distributions and self-organization near criticality.
- **Neural network criticality**: biological networks are scale-invariant, avalanches collapse onto universal power-law curves ("dragon king" events), maximizing dynamic range at the critical point.
- **Alpha decay / quantitative markets**: a signal-extinction cascade triggers beyond threshold phi* — a non-linear, not gradual, drop-off.

These establish that *sub-linear defense cost + super-linear attacker scaling near a critical threshold* is a recurring invariant across complex adaptive systems. But universality classes in percolation are precisely defined: different mechanisms belong to **different** universality classes with different exponents. Bot-evasion's saturation, rare-earth's percolation exponent, and alt-data's decay constant are three distinct realizations of the same coarse-grained law — they share a *shape class* (concave defense curve, super-linear attack surface) but each has its own parameter set.

**Conclusion:** the shared object is `leverage ~ input^k` with **different k per domain and, in two cases, no clean power-law at all**. The right model is not one universal exponent but a taxonomy: one invariant *family* with three realizations. This promotes the synthesis's analogy into a testable structural classification without fabricating a cross-domain fit that does not exist.

---

## How it would actually be tested (preserving the honesty gap)

The 2026-09-18 synthesis listed this as its top open item and noted "no existing cross-domain dataset, would require building from scratch." A valid test:
1. Fit `leverage ~ input^k` separately in each domain: percolation via cluster-size divergence near `p_c`; bot-evasion via FP-rate vs diversity (expect saturation, no finite k); alt-data via value-vs-commoditization decay.
2. Report the three exponent/curve families rather than forcing a common k.
3. Only if all three collapse onto one k within confidence would the claim be quantitative; corpus + theory predict they will **not**, because percolation's universal exponents differ from saturation and exponential-decay forms.

**Honest gap preserved:** no measured cross-domain dataset exists; k is domain-specific, not universal. The invariant survives as a structural family, not a single power-law.
---

## Cross-domain significance
- Provides the missing quantitative layer to the gray-band-leverage invariant (moves analogy -> classified mechanism).
- Aligns with `ethics-of-capability` and threshold-control-as-capability-weaponization: controlling k, not just leverage magnitude, is where downstream leverage concentrates.
- Methodologically: a recurring pattern — structural isomorphism across domains need NOT be a single equation; universality classes can share shape while differing in exponent. Useful for future BUILD cycles joining disparate fields.