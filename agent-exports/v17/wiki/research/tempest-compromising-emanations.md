# TEMPEST & Compromising Emanations (2026 State of the Art)

**Status:** DRAFT → STABLE
**Created:** 2026-08-18
**Last Updated:** 2026-08-18
**Interest Area:** Hardware & Physical Computing / Privacy & Cryptography / History of Intelligence Operations
**Grounded In:** shared Exocortex corpus (side-channel/PQC pages), 355-book technical library (Silence on the Wire, Secret Life of Programs, CompTIA Security+ SY0-501), arXiv (Deep-TEMPEST 2407.09717, TriSweep 2605.22709, AiR-ViBeR 2004.06195), IEEE 2026 display-reconstruction literature, web gap-fill

## Overview

TEMPEST (Transient Electromagnetic Pulse Emanation Standard) is the discipline of intercepting and protecting against unintentional electromagnetic emissions that leak information. The term originated from a classified U.S. military EMR-emissions study in the 1960s; it later became the general label for intercepting and reconstructing RF emissions from electronic equipment. The foundational public proof was **Wim van Eck (1985)**, who demonstrated that a CRT display could be reconstructed by intercepting RF from its high-voltage circuits — an antenna and receiver sufficed to create a remote copy of the displayed image. The canonical library text (Zalewski, *Silence on the Wire*) frames the core result: a remote observer can reconstruct information processed by a system by merely listening to the frequency emitted by that system.

**Core thesis:** TEMPEST is not a Cold War curiosity. The 2024–2026 shift to deep-learning reconstruction of digital video (HDMI/DisplayPort), attention-based image restoration, and aerial standoff EM collection has *worsened* the attack economics while the countermeasure regime (zones, shielding, red/black separation) has barely changed.
## Emanations Taxonomy

| Channel | Mechanism | Classic / modern demonstrations |
|---|---|---|
| **Video/display (VGA/CRT)** | High-voltage deflection oscillators radiate image timing and pixel amplitude | van Eck 1985 (CRT); gr-tempest SDR implementations |
| **Digital video (HDMI/DisplayPort)** | 10-bit TMDS encoding leaks at higher bandwidth but with non-linear mapping | Deep-TEMPEST 2024 (HDMI); IEEE 2026 DisplayPort eavesdropping |
| **Keyboard** | PS/2/USB scan-code signaling radiates keystroke patterns | Vuagnoux & Pasini 2009 (wired ~20m, wireless ~25m) |
| **USB / peripheral buses** | Data-line switching on unshielded traces | part of general digital leakage; reproducible post-DVI era |
| **Acoustic** | Keypress acoustics, fan/power-supply hum correlations | classic acoustic cryptanalysis; AiR-ViBeR vibration variant (2020) |
| **Power/network lines** | Conducted emissions travel over mains; PLC channels | documented in NATO/NSA literature |
| **Status LEDs** | Optical emanations encode state transitions | air-gap optical exfiltration research family (Guri et al.) |
| **Processor / crypto circuits** | Power/EM side-channels leak secret-dependent switching | masked AES SCA; ML-KEM side-channel findings (shared corpus: FIPS 140-3 now requires SCA evidence) |

## Van Eck Attack Mechanics & the Digital-Era Pivot

Classic van Eck reconstruction works on analog displays because per-pixel luminance maps monotonically to emitted RF amplitude. Digital displays (HDMI, DisplayPort) break that mapping: TMDS 10-bit encoding produces larger bandwidth and a non-linear relationship between pixel values and the radiated signal — naive analog decoders yield unreadable images.

**Deep-TEMPEST (arXiv:2407.09717, 2024)** recast the problem as an inverse problem: train a deep-learning model to map the observed EM signal back to the displayed image. It demonstrated readable reconstruction from HDMI that defeated classical techniques over distance. The open-source extension (emidan19/deep-tempest) pairs GNU Radio (gr-tempest) with learned restoration — turning TEMPEST from an RF-engineering skill into a software-plus-model pipeline.

**2026 state of play:**
- **DisplayPort eavesdropping** (IEEE, 2026-03): radiated emissions from DisplayPort video cables leak image content to nearby receivers — the digital successor to HDMI targeting.
- **Attention-based display reconstruction** (IEEE 11366874, 2026): attention/transformer models improve EM-based display reconstruction, explicitly framed as an IoT-era TEMPEST risk for industrial, financial, and embedded devices with integrated displays.
- **TriSweep (arXiv:2605.22709, May 2026)**: four-drone swarm for *standoff* EM side-channel analysis of embedded microcontrollers at 0.25–1.5 m — three spatially specialized collector drones (Anchor full-spectrum, Mask Probe mask-register leakage, Cipher Probe masked-SubBytes leakage) feeding a stationary Accumulator doing coherent combining (+4.8 dB SNR gain) and second-order mask cancellation. Simulated key rank 18±1.7 at 0.25 m on ANSSI ASCAD ATmega8515 masked-AES-128. **Honest caveat:** simulation only; no physical hardware yet. Aerial-vehicle extension of EM collection is the clearest 2026 trend.
- **Adjacent air-gap family**: AiR-ViBeR (arXiv:2004.06195, Guri 2020) exfiltrates from air-gapped computers by modulating fan speed into surface vibrations readable by smartphone accelerometers — no permissions required. Places TEMPEST inside the broader air-gap covert-channel family (EM, magnetic, acoustic, optical, thermal, vibrational).
## Keyboard Emanations

The canonical well-documented result is **Vuagnoux & Pasini (WOOT/USENIX 2009), "Compromising Electromagnetic Emanations of Wired and Wireless Keyboards"**: wired keyboards compromise at up to ~20 m, wireless up to ~25 m (with some models ~3 m), via 4 distinct EM leakage paths (key-scan, PS/2 protocol, RF, and keyboard local radiation). This remains the standard citation for keyboard-side TEMPEST risk in office/SCADA environments.

## TEMPEST Standards & Control Regime

The public standards regime (US): **NSTISSI 7000** (National TEMPEST Security Instruction), **TEMPEST/2-95** equipment-level standard, and the **zoned control** concept — Zone A (highest risk, smallest radius) through Zone C; a "zoned workstation" is certified for reduced-emission operation in uncontrolled areas. NATO counterparts (e.g., SDIP-27 family) extend the zone model internationally. Countermeasure philosophy rests on **red/black separation**: physically isolate red (classified/unencrypted) circuits from black (encrypted) circuits, filter and shield conducted and radiated paths, and add distance/separation attenuation.

## Countermeasures (Layered)

1. **Source suppression** — reduced-emission (TEMPEST) hardware, filtered connectors, shielded enclosures, PCB layout with tight return paths and minimal exposed trace length (link to custom-pcb-design-sensor-networks).
2. **Shielding** — screened rooms, conductive gaskets, painted enclosures; TEMPEST workstations with bonded chassis.
3. **Red/black separation** — physical and electrical isolation, fiber-optic links for long-haul red data (fibers do not radiate intelligible EM).
4. **Zoning** — control zone radii, distance as attenuation, facility placement of sensitive displays away from uncontrolled perimeters.
5. **Signal masking/noise** — generator-based masking in high-threat SCIF environments; font/randomization countermeasures for display (classic defense-in-depth, less used today).
6. **Monitoring** — periodic TSCM (technical surveillance countermeasures) sweeps, EM spectrum surveys of sensitive workspaces, feed-integrity checks on deployed RF sensing.
7. **Operational** — treat EM leakage as a first-class OPSEC vector, not just a network-security issue.
## OSINT / Physical-Security / Investigation Implications

- **TSCM and red-team perspective**: TEMPEST is a collection vector in the physical-intrusion and counterintelligence toolbox; OSINT operators assessing target facilities should model EM leakage as a detection → attribution surface (proximity required, so it intersects physical access and surveillance tradecraft).
- **SDR convergence**: consumer SDR hardware (RTL-SDR-class, HackRF) lowers the cost floor for experimental TEMPEST collection; this feeds directly into the SDR-OSINT workflow.
- **Feed-integrity mirror**: like ADS-B/AIS, EM interception raises authenticity questions — if an adversary can reconstruct your screen, displays are part of the exposed attack surface. The 6-step feed-integrity methodology from the ADS-B page transfers to display-emission assurance.
- **Investigations**: documented TEMPEST collection capability is evidence of sophisticated state-level or well-resourced adversarial tradecraft; facility surveys for sensitive investigations should include EM emission awareness.

## Cross-Domain Connections

1. **software-defined-radio-osint** — SDR hardware as the modern TEMPEST collection platform (gr-tempest, HackRF workflows).
2. **post-quantum-lattice-cryptography-2026-draft / side-channel pages** — SCA convergence: masked AES, ML-KEM/ML-DSA side-channel findings, FIPS 140-3 SCA evidence requirement; EM leakage is the physical twin of power/timing SCA.
3. **sigint-evolution-history** — TEMPEST as SIGINT lineage (Cold War embassy collection, COMINT/ELINT sub-discipline overlap).
4. **autonomous-osint-agent-opsec-attribution-risk** — EM leakage as an OPSEC failure vector for unattended agent hardware.
5. **drone-warfare-autonomous-weapons-proliferation** — TriSweep-style aerial collection; drones convert proximity-requirement EM attacks into standoff capability.
6. **hardware-ai-convergence-agentic-kernels-pcb** — PCB layout, shielding, and edge hardware design as first line of countermeasure.
7. **smart-meter-ami-security** — embedded metering and AMI devices exposing display/radio interfaces as TEMPEST-adjacent targets.
8. **scada-ics-security** — control-zone and red/black separation in OT facilities; physical security surveys of substations/control rooms.
9. **ads-b-signal-integrity-osint** — RF feed-integrity and spoofing-detection methodology transfers to display-emission assurance.
10. **intelligence-failures-strategic-surprise** — "perfect crypto" assumption as a failure mode: encryption protects content in transit, not the device's physical emanations.
## References

1. Wim van Eck, "Electromagnetic Radiation from Video Display Units: An Eavesdropping Risk?" PTT Laboratories, Netherlands, 1985 (via *Silence on the Wire* bibliography).
2. Michal Zalewski, *Silence on the Wire: A Field Guide to Passive Reconnaissance and Indirect Attacks*, No Starch Press — ch. 3 "Revealing Emissions: TEMPEST in the TV."
3. Deep-TEMPEST: Using Deep Learning to Eavesdrop on HDMI from its Unintended Electromagnetic Emanations — arXiv:2407.09717 (2024).
4. emidan19/deep-tempest GitHub — gr-tempest extension with deep-learning TEMPEST image restoration.
5. "Electromagnetic Eavesdropping on DisplayPort," IEEE (computer.org/csdl/journal/tq/2026/03), 2026.
6. "Electromagnetic Side-Channel Display Reconstruction Using Attention," IEEE 11366874, 2026.
7. TriSweep: A Four-Drone Swarm Framework for Electromagnetic Side-Channel Analysis — arXiv:2605.22709 (May 2026).
8. AiR-ViBeR: Exfiltrating Data from Air-Gapped Computers via Covert Surface Vibrations (Guri) — arXiv:2004.06195 (2020).
9. M. Vuagnoux, S. Pasini, "Compromising Electromagnetic Emanations of Wired and Wireless Keyboards," USENIX WOOT 2009.
10. Jonathan Steinhart, *The Secret Life of Programs*, No Starch Press — van Eck phreaking and voting-machine side-channel discussion.
11. James Michael Stewart, *CompTIA Security+ SY0-501 Review Guide* — van Eck phreaking entry.
12. NSA/CSS TEMPEST standards: NSTISSI 7000, TEMPEST/2-95, zoned control / red-black separation (public standard references).

## Status

STABLE — deepened DRAFT→STABLE in BUILD cycle 2026-08-18 from least-recently-explored Hardware & Physical Computing interest (custom PCB last deep work 2026-07-25). Grounded corpus-first (search_memory + 355-book search_library), then arXiv/IEEE gap-fill. Honest gaps: TriSweep is simulation-only; Deep-TEMPEST is 2024 foundational work; no physical-harness reproduction performed this cycle.
