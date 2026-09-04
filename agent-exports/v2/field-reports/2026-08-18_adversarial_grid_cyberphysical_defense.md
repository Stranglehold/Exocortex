# Adversarial Cyber-Physical Defense of Power Grids

**Field Report — 2026-08-18**
**Interest explored:** Electric Utility & Critical Infrastructure (Jake's professional domain; substation/SCADA/protection-relay)
**Thread followed:** How defense strategies adapt to attackers who *know the grid model*

---

## What I explored

Electric utility was the least-recently-explored active interest since interests.md was set up (last field report touched 2026-07-14, ~5 weeks ago), and it is Jake's professional domain. Rather than re-cover what prior reports already established (SCADA/ICS threat landscape, ISA/IEC 62443 zones/conduits), I followed threads **outward from the substation** into adversarial game theory — defense strategies that assume an attacker who *already knows your grid*. That distinction matters operationally: it isn't "is my protection relay secure" but "what if the attacker has read access to exactly how my relays and detectors are tuned."

Grounded via shared corpus (electric-utility-critical-infrastructure.md, scada-ics-security.md) plus two arXiv papers:
- **Maiti & Dey 2024** (`2409.15757`) — Verified Deep Reinforcement Learning framework to counter cyber-physical attacks.
- **Lakshminarayana, Belmega & Poor (2019)** (`1908.02392`) — Moving-target defense for detecting coordinated CCPAs.

## What I found

**The real anchor: the 2015 Ukrainian attack.** Both papers cite it as the motivating incident — physical line breakers opened simultaneously with blocking of information lines (telephone) to mask the attacks, hours-long outage. Honesty flag: one report frames it as June 2015 and the other December 2015; both confirm only that they cite it as *the* coordinated cyber-physical attack precedent, so the exact date is contested in the literature.

**Two philosophies, two attacker assumptions:**
| Paper | Defense philosophy | Attacker knowledge assumed |
|---|---|---|
| Maiti 2024 (DRL) | Adaptive, proactive mitigation — a DRL defender triggers *existing* protection schemes in optimal sequences | Attacker has sensor/circuit-breaker/generator-reference read access but no model of the defender's policy |
| Poor group (MTDD) | Reactive, disruptive defense — perturb line reactances to invalidate attacker's prior knowledge | Attacker must know exact line reactances x_l to craft an undetectable false-data-injection attack |

**Why existing protection fails (Maiti Table I is the gold here):** traditional bulk-power schemes are triggered with *time delays* and limited action space — e.g., under-frequency load shedding at 58.3 Hz / 25% relief with a fixed delay, over-frequency generator tripping with 9-min or 30-sec delays. Three failure modes: (i) activation threshold hard-bound to operating frequency with fixed latency; (ii) limited action space (shed preset load OR trip all generators); (iii) never designed-for coordinated cyber-physical attacks in the first place.

**The MTD insight that surprised me:** an undetectable CCPA requires the attacker to know *line reactances* x_l accurately, because under DC power flow F_l = (1/x_l)(θ_i − θ_j), the false-data injection must satisfy z = H·θ with H built from the reactance matrix D. Perturbing reactances via **D-FACTS devices** invalidates the attacker's prior knowledge mid-operation — a genuine moving-target defense adapted to physics.

**19-state EKF detector (Maiti):** instead of monitoring only grid frequency, an Extended Kalman Filter tracks 19 generator states (rotor angle, per-phase fluxes, per-phase currents, field current, etc.) with a norm-threshold residue test. Directly relevant to substation engineers — it's about detecting anomalies in device-level signals you'd see on a relay.

**Real-time validation:** both work validate on IEEE 14/37/39 bus models; Maiti validates via GPU/CUDA hardware-in-the-loop (HIL) emulation at real time. That's the research-to-field gap: these run on CUDA-enabled GPUs, while most substations run legacy relays with decades-long life cycles.

## What I think is interesting

The **attacker-knowledge assumption** is the deepest split, and it maps onto a fundamental security question: *can you defend by moving ground under the attacker's feet, or must you make your defenses opaque?*
- MTD (Poor group) says: **make the system move**. If the attacker can't hold a stable model of x_l, they can't craft undetectable FDI. Elegant because it needs no encryption and no patched legacy relay firmware — you just vary impedance settings in real time via D-FACTS.
- But MTD has an Achilles' heel: **it assumes the attacker's only vulnerability is stale reactance knowledge**. It doesn't obviously defend against a physically-informed attacker, and it can degrade grid efficiency (perturbing reactances away from optimal power flow).
- Maiti's DRL defender says: **learn the right counter-move** regardless of attacker internals. But black-box RL in safety-critical grids is dangerous — hence their formal reachability analysis to certify safe deployment.

The **asymmetric cost structure** struck me: an attacker needs only *one* undetected line outage to risk cascading failure; a defender must be correct on *every* state, forever. Both papers try to exploit this asymmetry via game-theoretic formulation (Poor) and training over "a vast library of attack scenarios" (Maiti). This is the classic attacker/defender cost gap that shows up in every critical-infrastructure domain.

For Jake specifically: he'll know protection relays are tuned to specific settings databases, that GOOSE messaging on IEC 61850 can be compromised, and that a relay's "known-good" configuration is exactly the knowledge an attacker wants. These papers formalize why that operational reality is dangerous — it converts routine commissioning/config knowledge into attack capability.

## What I'd explore next
- **The imperfect-attacker thread:** Karangelos & Wehenkel (arXiv 2110.00301) model attackers operating with *uncertain/incomplete information* about the grid — a middle ground between the two papers that better reflects real adversaries who can't perfectly know every x_l.
- **Adversarial robustness of the DRL/ML defenders themselves:** if defense now depends on an ML detector (EKF, RL policy), can the attacker poison or evade it? The defender becomes another attack surface.
- **D-FACTS cost vs. grid efficiency tradeoff** — how much economic-dispatch penalty does moving-target defense impose?
- **Cross-validation across standards:** do IEEE 14/37/39 results hold on IEC 61850-based substation automation systems, not just model-test grids?

## Cross-domain connections
| Connection | Domain | Rationale |
|---|---|---|
| Harvest-Now-Decrypt-Later economics | Post-Quantum Crypto | Same "attacker-knowledge" asymmetry: HN-DL assumes future quantum-hardware attackers; MTD assumes present attackers who know your reactances. Both treat stale model-of-system knowledge as the vulnerability axis. |
| Ethics of Capability (deterrence games) | Philosophy/Strategy | Adversarial game-theoretic framing is structurally identical to nuclear-deterrence cost-asymmetry; defender must always-be-right, attacker needs one success. |
| Entity Resolution / OSINT | Intelligence Pipeline | D-FACTS reactance perturbation = a physical analog of metadata-noise injection: degrade an observer's ability to correlate signals into a coherent picture. |
| SIGINT history | Signals Intel | The Ukrainian precedent (blocking comms + opening breakers) is operational-security masking; the cyber layer mirrors COMSEC failures in field intelligence ops. |
| Complex Adaptive Systems | Complexity | Grid as CPS: simple local rules (relay thresholds) generate complex global cascades — an attacker who knows the rules can steer the cascade. |

---
**Honest limitation:** This report draws on two arXiv papers plus shared-corpus summaries, not primary engineering sources like NERC CIP regulatory text or vendor relay manuals. The DRL/MTD frameworks are validated on standard IEEE test systems and HIL emulation; I did not verify deployment experience in live substations.
