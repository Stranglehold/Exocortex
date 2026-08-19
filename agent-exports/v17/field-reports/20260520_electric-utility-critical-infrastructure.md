# Electric Utility & Critical Infrastructure — Field Report
**Date:** 2026-05-20
**Cycle:** EXPLORE (least recently explored topic — last field report 2026-05-16)
**Topics:** CISA ICS threat landscape, arXiv grid anomaly detection 2026, DER integration security

---

## 1. What I Explored

Three research threads, building on the May 16 field report which covered Dragos 2026 OT threats, IEC 61850 GOOSE vulnerabilities, and ML anomaly detection:

- **CISA ICS advisory landscape (April–May 2026):** The new joint advisory AA26-097A on Iranian-affiliated cyber actors exploiting PLCs, plus the May 4–10 batch of 6 ICS product vulnerability disclosures, plus CISA's new Zero Trust for OT and agentic AI guidance.
- **arXiv papers on grid ML anomaly detection (2026):** Six papers published between March and May 2026 spanning latency-aware deep learning benchmarks, digital twin anomaly detection, spatio-temporal graph neural networks with attention for ICS, and unified frameworks for electricity theft detection.
- **DER integration security:** Searched for new arXiv papers on distributed energy resource grid security — limited new material, but the CISA agentic AI guidance intersects with autonomous DER management.

---

## 2. What I Found

### CISA ICS Advisory Landscape

**AA26-097A (April 7, 2026):** Joint advisory from CISA, FBI, NSA, and Five Eyes partners (Israel, Canada, Australia, UK) on Iranian-affiliated cyber actors exploiting programmable logic controllers (PLCs). The key TTP:
- Malicious interaction with the **project file** on engineering workstations
- **Manipulation of HMI and SCADA display data** — operators see normal conditions while compromise is ongoing
- Result: **operational disruption** without immediate detection
- Advisory urges U.S. critical infrastructure sectors to "urgently review" TTPs and IOCs

The HMI/SCADA display manipulation is particularly interesting — this is a *man-in-the-display* attack that undermines the fundamental assumption that what the operator sees reflects physical reality. It's the OT equivalent of a deepfake UI.

**May 4–10, 2026 ICS Advisories:** CISA released advisories for 6 ICS products: Inductive Automation, Schneider Electric, National Instruments, Mitsubishi Electric, Siemens, Advantech, Rockwell Automation, and Axis Communications. This represents a sustained vulnerability disclosure tempo — roughly one batch per month.

**CISA Agentic AI Guidance (2026):** New guidance from CISA and partners outlining "actionable steps for organizations to secure agentic AI systems and protect critical infrastructure from evolving AI-driven threats." This is the first explicit CISA guidance at the intersection of agentic AI and critical infrastructure — a recognition that LLM-based autonomous systems are entering OT environments.

**Zero Trust for OT:** CISA released considerations for applying Zero Trust principles to OT systems — a significant architectural shift for environments historically built on implicit trust and air-gapped assumptions.

### arXiv Grid Anomaly Detection — New Papers

**Latency-Aware Deep Learning Benchmark (2605.17256, May 2026):** A benchmarking framework for DL models in power system anomaly detection using time-domain signals from electromagnetic transient (EMT) simulators. Evaluates 8 neural network architectures (MLPs to transformers) for *real-time* classification of attacks vs. faults in inverter-dominated grids. The emphasis on latency is critical — inverter-dominated grids have faster dynamics than synchronous-machine grids, making detection speed a first-order concern.

**Digital Twin Snitch (2604.03123, April 2026):** Distributed digital twin-based anomaly detection for VSC-enabled wind power systems. Addresses a gap in existing ANN/DRL methods: limited adaptability, delayed response, and inadequate coordination against stealthy attacks. The digital twin provides a live reference model — deviations from predicted behavior signal compromise.

**SmartGuard Energy Intelligence System (2604.03344, April 2026):** Unified spatio-temporal and graph learning framework for electricity theft detection. Processes smart meter data with graph structure (topology awareness) plus temporal sequence modeling.

**Spatio-Temporal Grid Intelligence (2603.20488, March 2026):** Hybrid GNN + LSTM for electricity theft detection. Argues conventional methods are "reactive and meter-centric" and fail to capture spatio-temporal patterns across the distribution network.

**CINDI (2603.11745, March 2026):** Conditional Imputation and Noisy Data Integrity with normalizing flows for power grid data. Treats noise and anomaly as *joint* problems rather than sequential cleaning-then-detection. Important because it reframes "bad data" as signal-bearing rather than simply a preprocessing problem to eliminate.

**Spatio-Temporal Attention GNN for ICS (2603.10676, March 2026):** Uses attention mechanisms on spatio-temporal graphs to provide *explainable* anomaly detection in ICS. The attention weights show *which* nodes and *which* time windows contributed to the anomaly classification — a form of structural explainability absent from black-box methods.

### Cross-Cutting Observations

1. **The HMI deception attack vector is under-theorized.** AA26-097A's HMI/SCADA display manipulation targets the human operator's situational awareness, not the control logic. This is distinct from process-manipulation attacks like TRITON. Defenses are asymmetric: the attacker only needs to control what the operator sees, not the plant itself.

2. **The inverter-dominated grid changes the clock speed of threat detection.** As synchronous generators are displaced by inverter-based resources, grid dynamics accelerate from seconds to milliseconds. 2605.17256's emphasis on latency-aware benchmarking reflects this: detection that works for synchronous grids may be too slow for inverter-dominated systems.

3. **Explainability is becoming a requirement, not a feature.** 2603.10676's attention-based explainability for ICS anomaly detection reflects a broader trend: in critical infrastructure, the operator needs to know *why* an alarm fired, not just *that* it fired. Black-box ML is unacceptable when the response action could take a plant offline.

4. **CISA's agentic AI guidance is a leading indicator.** The fact that CISA is already publishing guidance on securing agentic AI in critical infrastructure suggests they expect LLM-based autonomous agents to be deployed in OT environments within the guidance-relevant horizon (1–2 years). This is not speculative — it's operational planning.

---

## 3. What I Think Is Interesting

**The convergence of three trends creates a vulnerability profile that's been under-articulated:**

1. **Protocol insecurity** — IEC 61850 GOOSE remains authentication-free by design (even the 2021 edition only added optional mechanisms). Modbus and DNP3 were never designed for adversarial environments.

2. **Adversary capability evolution** — AA26-097A shows adversaries moving beyond process manipulation to *perception manipulation*. If you can make the operator see what you want, you control their response — and their response is the last line of defense.

3. **Architectural complexity from DER integration** — Inverter-dominated grids introduce faster dynamics, more attack surface (every DER is a network-connected device), and less operational experience with failure modes.

These three don't just add — they multiply. The HMI deception attack is most dangerous precisely when the grid is under stress from rapid dynamics that the operator has limited experience with. The combination makes it hard to distinguish attack from equipment failure from normal DER variability.

**CINDI's joint treatment of noise and anomaly is methodologically important.** In critical infrastructure, what looks like sensor noise can be an attack — and what looks like an attack can be a failing sensor. Treating them as a joint inference problem rather than sequential filtering-then-detecting is the right framing. This maps to a broader principle: in high-stakes environments, don't discard information early. Let the final decision layer see the raw signal.

**The CISA agentic AI guidance is a cross-domain trigger.** It connects the Electric Utility interest directly to the AI Agent Architecture interest. If LLM agents are being deployed in OT environments, then every architectural decision about agent design (context management, tool authorization, hallucination detection) becomes a critical infrastructure security concern. The Exocortex patterns (deterministic scaffolding, epistemic integrity, context pruner) are directly relevant to how agentic AI should be secured in OT.

---

## 4. What I'd Explore Next

1. **HMI deception defense architectures.** What would it take to verify that what the operator sees matches physical reality? Ideas: redundant sensor paths, physics-based consistency checks, display integrity verification via cryptographic hashing of the data pipeline from sensor to screen.

2. **IEC 61850 GOOSE authentication deployment.** The 2021 edition added optional authentication — is anyone actually deploying it? What's the real-world adoption rate, and what are the barriers (latency, key management, vendor support)?

3. **Agentic AI in OT — threat model.** CISA's guidance suggests they're thinking about it. What's the actual threat model for an LLM agent with write access to SCADA systems? This is a structured analysis problem that combines AI architecture knowledge with OT domain expertise.

4. **Latency benchmarking for OT anomaly detection.** 2605.17256's framework could be extended to compare detection latency across different grid topologies (inverter-dominated vs. synchronous) and attack types. This is an empirical gap — we don't know what "fast enough" means for different grid configurations.

5. **The DRAGOS-AA26-097A comparison.** Dragos tracks Iranian groups (KAMACITE, ELECTRUM) from the May 16 field report. AA26-097A describes Iranian PLC exploitation. Are these the same actors? Cross-referencing Dragos naming with the advisory's TTPs could identify the specific group.

---

## 5. Cross-Domain Connections

1. **Entropy-as-Signal → CINDI data integrity.** CINDI treats noise and anomaly jointly using normalizing flows — the same principle as Exocortex entropy-as-signal: what looks like noise may be the most important signal. Both frameworks refuse to discard "bad data" early.

2. **Epistemic Integrity → Explainable ICS anomaly detection.** 2603.10676's attention-based explainability makes anomaly classifications auditable — the operator can verify *why* the alarm fired. This is the Exocortex epistemic integrity principle applied to OT: make error visible and traceable.

3. **Deterministic Scaffolding → Latency-aware benchmarking.** 2605.17256's emphasis on real-time constraints parallels deterministic scaffolding's time-bounded operations. In both domains, the cost of being too slow is catastrophic, so latency must be a first-class design constraint.

4. **Build the Environment → Digital Twin anomaly detection.** 2604.03123's digital twin approach creates an environment where normal behavior is modeled, making deviations visible. This is the Exocortex "build the environment" principle: don't try to detect anomalies directly — create a reference environment and surface differences.

5. **AI Agent Architecture → CISA agentic AI guidance.** CISA's new guidance on securing agentic AI in critical infrastructure is a direct bridge between these two interests. Every Exocortex architectural decision (tool authorization, context management, hallucination detection) has an OT security analog.

6. **History of Intelligence Operations → HMI deception attacks.** AA26-097A's HMI manipulation is a modern expression of a classic intelligence tradecraft principle: control what the adversary perceives, and you control their decisions. The Double-Cross system in WWII fed false information to German intelligence via controlled agents — HMI deception does the same to operators via controlled displays.

7. **Privacy & Cryptography → HMI display integrity.** Cryptographic verification of the data pipeline from sensor to screen (data provenance, integrity hashing) could defend against HMI manipulation. ZKPs could verify control commands without exposing system topology — the same privacy-preserving verification pattern applied to OT.

8. **Entity Resolution → CTI (Cyber Threat Intelligence) actor attribution.** Cross-referencing AA26-097A TTPs with Dragos naming (KAMACITE/ELECTRUM) is an entity resolution problem across threat intelligence datasets that use different naming conventions for the same actors.

---

## Sources

1. CISA AA26-097A — Iranian-Affiliated Cyber Actors Exploit Programmable Logic Controllers (April 7, 2026)
2. CISA ICS Advisories May 4-10, 2026 — 6 product vulnerabilities
3. CISA Agentic AI Guidance (2026)
4. CISA Zero Trust for OT (2026)
5. arXiv:2605.17256 — Latency-Aware DL Benchmark for Real-Time Cyber-Physical Attack Classification (May 2026)
6. arXiv:2604.03123 — Distributed Snitch Digital Twin-Based Anomaly Detection for VSC Wind Power (April 2026)
7. arXiv:2604.03344 — SmartGuard Energy Intelligence System for Electricity Theft Detection (April 2026)
8. arXiv:2603.20488 — Spatio-Temporal Grid Intelligence: Hybrid GNN-LSTM (March 2026)
9. arXiv:2603.11745 — CINDI: Conditional Imputation and Noisy Data Integrity with Flows (March 2026)
10. arXiv:2603.10676 — Spatio-Temporal Attention GNN for ICS Anomaly Detection (March 2026)
11. arXiv:2605.02715 — Dimensionality-Aware Anomaly Detection in Learned Representations (May 2026)
12. Existing wiki page: /a0/usr/Exocortex/wiki/research/electric-utility-critical-infrastructure.md (STABLE, 105 lines)
13. Previous field report: /a0/usr/Exocortex/field-reports/20260515_electric-utility-critical-infrastructure.md (9,896 chars)
