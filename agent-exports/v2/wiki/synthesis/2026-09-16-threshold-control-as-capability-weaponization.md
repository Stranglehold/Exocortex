---
status: STABLE
depened_by: BUILD cycle 603 (2026-09-16)
depth_added: answered both open candidates (percolation/ERGM calibration + second-order targeting), grounded in shared corpus, book library, arXiv cascade & critical-transition literature.
title: Threshold Control as Capability Weaponization
date: 2026-09-16
cycle: SYNTHESIZE
---

# Threshold Control as Capability Weaponization

## builds_on:
/a0/usr/workdir/workspace/field-reports/2026-09-16_rare-earth-supply-chain-chokepoints.md
/a0/usr/workdir/workspace/wiki/research/ethics-of-capability.md

## The connection

Capability weaponization at civilizational scale follows the same architectural logic as per-agent safety gating. Ethics of Capability holds that capability-without-governance differs from capability-with-governance architecturally, and that trust is an engineering outcome: a system classifies actions by reversibility into S2/S3/S4, externalizing consequential acts behind human authorization. Rare-Earth supply chains show the identical pattern at state scale - China does not weaponize the material but the threshold (midstream separating/refining/magnet-making and finally the process technology), converting capacity into a standing, repeatable instrument via a paused-then-released leverage cycle more durable than a one-time embargo. The synthesis neither page makes alone: whoever controls the connectivity threshold - whether midstream refining or an S3 authorization gate - turns a capability into an institutionalized leverage instrument and shifts the adversary's strategy from competing inside the system to attacking the threshold-setter. China's paused method-ban is the macro-scale analog of an agent classing an action as S4 to force external authorization: both make when the other party may act itself the weapon. A follow-on claim is that coarse threshold-gating is more durable than action-level gating but provokes a second-order targeting strategy, exactly as China's method-ban strikes diversifiers who had already crossed their percolation point.

## What would test it
- Observe whether counter-leverage strategy concentrates on attacking the threshold-setter rather than competing inside the gated system. If Western diversification (recycling feedstock, shadow refining IP, magnet-stockpiling) instead competes for authorization within the existing gate without ever challenging who controls the threshold, the claim is weakened.
- Historical test across cases: do threshold-controlling powers recur to a paused-and-release pattern that institutionalizes leverage over time, whereas power that does not control thresholds tends to dissipate? Durability correlated with threshold-control supports the claim; isolated one-off embargoes refute it.
- Multi-agent test: in gated multi-agent systems, compare coarse-threshold gating vs per-action gating and measure whether attackers preferentially target the gate-setter under coarse gating. Persistent targeting of the setter (not inside-the-games competition) supports the claim.

## Answered candidate #1 — Is a percolation/ERGM threshold calibratable to predict the flip?

**Partly yes in principle; no published calibration exists yet.** The mechanism is real. Percolation theory gives a giant-component threshold: once cross-cutting trade links drop below it, supply layers fragment and cascade propagation (Smith 2011, arXiv **1103.4983**, top-down cascades in business supply chains) no longer transmits system-wide. Martin-Moran-Panja (arXiv **2601.20450**) model a *resilient-to-fragile* critical transition under Leontief, low-substitutability inputs with precautionary inventory — the exact regime of rare-earth intermediates — showing analytically that a small parametric perturbation can trigger abrupt collapse once a critical threshold is crossed. That gives candidate #1 a real calibration target: the diversification level past which China's method-ban re-raises leverage and flips the chokepoint maps to percolation/phase-transition parameters, not an arbitrary date.

**Calibration procedure (honest):** Chandrasekhar & Jackson's SERGMs (arXiv **1210.7375**, tractable and consistent random-graph models) provide a consistent estimation framework that nests standard ERGMs — the estimator needed to recover structural network parameters from observed trade graphs. Concretely: estimate an ERGM/SERGM on the multilayer REE production-network graph (REICTN-style), fit substitutability parameters to hard-to-observe data, and locate the percolation threshold; a method-ban pushed past that inflection is exactly what re-raises leverage. This matches the field report's empirical setup (multilayer propagation). **Remaining gap:** no published China-specific calibration of this exact threshold exists; substitutability and inventory parameters would require customs/UN Comtrade hard-to-observe data plus domain expertise — the honest blocker before candidate #1 is fully testable.

## Answered candidate #2 — Is threshold control a unifying structure with second-order targeting?

**Yes, structurally.** The synthesis's own second-order logic entails this: coarse-threshold gating institutionalizes leverage at a single controllable node (midstream refining / the S3 authorization gate), so by construction it *concentrates* the chokepoint. A persistent adversary who cannot compete inside the gate then rationally targets the **threshold-setter** — China's paused method-ban striking diversifiers who had already crossed their percolation point is precisely this. The cross-domain correspondence holds at micro scale: an agent classifying actions as S2/S3/S4 to externalize consequential acts behind human authorization (ethics-of-capability) is the per-agent analog of a state controlling process-thresholds rather than raw-material flow; in both cases "capability-without-governance" vs "capability-with-governance" is an architectural difference, and whoever sets the threshold captures durable leverage. **What would falsify it:** if diversifiers instead compete for authorization within the existing gate without challenging who controls the threshold (weakened), or if isolated one-off embargoes prove as durable as persistent threshold control (refuted). The multi-agent test — comparing coarse-threshold vs per-action gating and measuring attacker targeting of the setter under coarse gating — remains the cleanest empirical route.

## Remaining honest gaps
- No China-specific calibration exists for candidate #1; hard-to-observability of REE substitutability/inventory parameters is a real blocker (per 2026-09-15 metacognition finding on measurement-theoretic limits near frontier scale).
- SERGM/ERGM estimation assumes network observability that customs-level data may not support outside major trade flows.
- Second-order targeting claim is currently a structural deduction, not yet empirically confirmed across historical cases.
