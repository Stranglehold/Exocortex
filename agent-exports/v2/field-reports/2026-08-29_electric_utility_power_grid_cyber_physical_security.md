# Electric Utility & Critical Infrastructure — Cyber-Physical Security of Power Grids

*Field report | EXPLORE cycle 2026-08-29 | Interest: Electric Utility & Critical Infrastructure (Jake's professional domain; last explored 2026-07-14, the least-recently-explored active interest).*

## What I explored

A fresh pass on power-grid security framed as **adversarial ML vs. physical protection**. The shared corpus had already established a baseline (electric-utility-critical-infrastructure.md, iec-61850-standard-evolution.md) plus the Aug 18 Adversarial Grid cyberphysical field report and an active draft on IEC 62351 deployment gaps. Rather than re-survey threat actors, I followed one thread: **when grid protection becomes ML-driven (DRL defenders, federated anomaly detection), it inherits adversarial-ML attack surfaces — including supply-chain poisoning of the models themselves.** Grounding came from arXiv 2409.15757 (already downloaded) and a grounded library pull from the Packt "Adversarial AI" volume in the shared corpus.

## What I found

- **Grid OT targeting is operational, not theoretical.** An April 2026 Iranian PLC campaign hit industrial controllers directly (arXiv 1908.02392 context + corpus ai-grid-cyber-physical-security draft). Combined with incomplete IEC 62351 authentication at many substations, the U.S. grid has a defined window of elevated risk.
- **The attack classes are concrete.** FDIAs (false data injection on transmission flow sensors) and LAAs (load alteration via IoT botnets — refrigerators/ACs switching in coordinated bursts) disrupt Automatic Generation Control and can cascade into blackouts. The 2015 Ukrainian LDC load-alteration incident is the canonical real-world case.
- **Why existing protection fails (Maiti & Dey, arXiv 2409.15757).** Three structural defects: (i) fixed-threshold bad-data detectors activate only after a hard frequency-bound with a fixed time delay; (ii) limited action space — shed a preset load or trip all generators; (iii) protection schemes were never formulated against smart CP attacks. Their fix is a **verified DRL defender** that adaptively retunes activation time and action space, formally verified via reachability analysis so it provably cannot trigger unsafe trips, deployed on CUDA GPU for real-time validation.
- **The safety gatekeeper is the crux.** RL is black-box; a false positive in protection relays means an unnecessary breaker trip. So any ML defender must pass hardware-in-the-loop validation before deployment — trust is earned by physical proof, not accuracy metrics.
- **Adversarial-AI supply-chain insight (Packt volume, p.160).** "Poisoned pre-trained models" uploaded to model registries are *stealthier* than classic data poisoning: the attacker never touches training data, only ships a benign-looking .h5/.pth with baked-in backdoors; standard accuracy checks look fine. Defenses discussed: MLOps provenance/traceability, RONI (Reject-on-Negative-Impact) removes high-impact poison points, spectral-signature and activation-cluster defenses, adversarial training.

## What I think is interesting

The **most dangerous grid ML threat isn't the anomaly detector being fooled at inference — it's the defender model being poisoned in development.** If a DRL protection agent or federated detection model gets a backdoored checkpoint (supply chain), the attacker gains persistent, undetectable control that looks correct on every clean metric until they trigger it. This flips the usual framing: the grid defense is attacked at its data pipeline, not its data feed.

The **hardware-in-the-loop gatekeeper** is philosophically notable: it's a physical-verification regime where ML must prove safety before acting — an operational instance of "trust by proof, not by accuracy." This directly answers Jake's protection-relay domain question about firmware and relay logic manipulation as a deception weapon (counterintelligence connection).

## What I'd explore next

1. **Federated learning across substations under poisoning** — does the HGNN+FL architecture in the corpus resist backdoored local updates from one substation? This is the highest-value next step.
2. Reachability analysis formalism (arXiv 2409.15757) — can it be extended to prove DRL robustness against adversarial perturbations, not just unsafe states?
3. IEC 62351 v2 deployment timeline and post-quantum migration for constrained OT relay devices.

## Cross-domain connections (Rule 13)

**Federated-learning grid aggregation = Adversarial-AI supply-chain poisoning.** A compromised substation contributes backdoored weight updates to the global model aggregation — exactly the clean-label/backdoor/supply-chain poisoning vector from the adversarial-AI book, just operating on *model weights* instead of *training images*. The grid's hardware-in-the-loop validation is the physical analog of MLOps provenance checks: you cannot trust any update without verification. This also ties to the oil-reserves field report (buffer-exhaustion cascade isomorphic to money-market reserve scarcity) and IEC 61850/GOOSE security.
