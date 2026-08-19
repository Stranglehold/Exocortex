# Electric Utility & Critical Infrastructure — Field Report
**Date:** 2026-05-26
**Cycle:** EXPLORE (least recently explored active interest — last field report 2026-05-20)
**Thread:** The visibility-layer attack surface — adversaries don't hack the grid, they inhabit the systems operators rely on to see it

---

## 1. What I Explored

This cycle focused on a single high-signal source: the **Dragos 2026 OT/ICS Cybersecurity Year in Review** blog post (April 7, 2026), which distills findings from the Dragos Intelligence Fabric — combining platform telemetry, frontline incident response, adversary intelligence, and real-world assessments across electric utility environments.

I chose this thread because the May 20 field report had already covered CISA ICS advisories (AA26-097A on Iranian PLC exploitation), arXiv anomaly detection papers (latency-aware DL benchmarks, digital twin detection, spatio-temporal GNNs), and DER integration security gaps. The Dragos report offered operational ground truth from live incident response — a chance to test whether the academic and regulatory findings matched what defenders are actually seeing.

What emerged is a reframing of the threat model that changes what "grid cybersecurity" means.

---

## 2. What I Found

### The Core Reframing: Visibility as the Primary Attack Surface

The foundational assumption in electric utility cybersecurity has been: *meaningful disruption requires direct access to control systems — protection relays, PLCs, substation automation.* The Dragos 2026 report explicitly challenges this:

> "Adversaries do not need to 'hack the grid' in the traditional sense to create operational impact. Instead, they are increasingly targeting the systems that operators rely on to see, understand, and manage the grid."

This is not a perimeter problem. It's an *epistemic* problem. The adversary doesn't need to compromise the relay that trips a breaker — they need to compromise the HMI that tells the operator whether the breaker tripped. If the operator's situational awareness is corrupted, the physical grid can be manipulated indirectly through operator actions taken on false information.

### Adversary Activity: From Access to Inhabitation

Three tracked threat groups demonstrate escalating operational readiness:

| Group | Role | Activity (2025) | Significance |
|-------|------|-----------------|--------------|
| **ELECTRUM** | Stage 2 — operational impact | Targeted Polish DER infrastructure, December 2025 | **First coordinated attack against DER anywhere in the world.** Responsible for 2015/2016 Ukrainian grid outages. |
| **KAMACITE** | Access development for ELECTRUM | 4 months systematic scanning of US internet-exposed industrial devices (HMIs, VFDs, meters, cellular gateways) | Methodically mapping entire control loops — not just finding devices, understanding how they connect. |
| **SYLVANITE** | Stage 1 access broker | Confirmed operating inside a US electric utility network | Hands footholds to ICS-capable groups like VOLTZITE. |

The pattern isn't breach-and-detonate. It's *silent inhabitation*: "electric environments are not being 'breached' loudly at a point in time; they are being inhabited silently over time."

This maps directly to intelligence tradecraft — the difference between a raid and an embedded asset. The operational objective appears to be persistent optionality: maintain the ability to act, rather than acting immediately.

### Entry Vectors: The IT-OT Membrane

Adversaries gain access through systems that bridge IT and OT, not through direct OT compromise:
- Remote access infrastructure (vendor VPNs, engineering backdoors)
- Engineering workstations (project file manipulation, PLC configuration tools)
- IT systems with OT visibility (SCADA HMIs on corporate networks, historian databases)

The operational challenge: commands issued from these systems *look operationally valid*. They blend into engineering and administrative workflows. The IT-OT boundary is where authorized use and adversary behavior become indistinguishable without OT-specific context.

### The Grid You Defend Has Changed

New technologies expanding the attack surface:
- **Distributed Energy Resources (DER) management systems** — remotely accessible, cloud-connected, deployed faster than secured
- **Battery Energy Storage Systems (BESS)** — integral to load balancing, introduce new control interfaces and external dependencies
- **Cloud-based grid platforms** — move operational data and control logic outside the traditional utility perimeter
- **Industrial IoT / smart grid technologies** — every smart meter and connected sensor is a potential entry point

The expansion isn't just additive — it's architectural. The grid that ELECTRUM attacked in Ukraine in 2015 was a synchronous-machine grid with centralized control. The grid they're probing now is distributed, inverter-dominated, and software-defined. The attack surface has changed faster than the defense model.

### Vulnerability Velocity

A metric that should alarm defenders: **median 24 days from vulnerability disclosure to public exploit availability.** In some cases, the window was zero — exploits available at disclosure. Approximately 4% of ICS vulnerabilities were actively exploited at time of disclosure in 2025.

For electric environments where patching requires maintenance windows, outage coordination, and regulatory approval, this compresses the defensive timeline to nearly nothing. The Dragos recommendation: prioritize vulnerabilities based on *exposure conditions* (internet-reachable? operationally significant? tied to grid-supporting systems?) rather than treating them as theoretical risks to schedule.

---

## 3. What I Think Is Interesting

### The Epistemic Integrity Parallel

This is the cross-domain connection that makes this cycle's findings matter beyond utility security. The Dragos reframing — *adversaries target the operator's visibility, not the physical system* — is structurally identical to the Exocortex epistemic integrity problem.

In the Exocortex architecture, epistemic integrity means: **"Make error visible and traceable."** The system is designed so that when the LLM confabulates, the error is surfaced to the operator, not silently embedded in output. The injection gate, BST classifier, and supervisor loop all serve this function.

In electric grid operations, the HMI/SCADA display serves the same role as the LLM's output: it's the operator's window into system state. If that window is manipulated (as in the Iranian AA26-097A advisory's HMI deception TTP), the operator makes decisions on false premises — exactly as a user would if the LLM fabricated data without the epistemic integrity layer flagging it.

The principle generalizes: *In any human-machine system where the human makes consequential decisions based on machine-generated representations of reality, the integrity of that representation is the highest-priority security property.* Not confidentiality. Not availability. Integrity of the operator's situational awareness.

### The Inhabitation Model vs. the Breach Model

The shift from "breach detection" to "inhabitation detection" mirrors a shift in counterintelligence thinking. Traditional network defense asks: "Did someone break in?" The inhabitation model asks: "Is someone living here?"

The detection signatures are different. Breach detection looks for perimeter violations, exploitation attempts, malware execution. Inhabitation detection looks for:
- Credential usage at unusual times from usual locations (the insider who isn't an insider)
- Engineering workflow deviations (PLC configuration changes that don't match maintenance schedules)
- HMI interaction patterns that don't correspond to operator shift changes
- Data access patterns that suggest reconnaissance, not operations

This requires *behavioral baselining of OT environments* — understanding what "normal" looks like well enough to detect "abnormal that looks normal." It's the counterintelligence analyst's problem applied to industrial control systems.

### BESS as the New Frontier

The Dragos report specifically calls out Battery Energy Storage Systems as "increasingly integral to load balancing and grid stability" while introducing "new control interfaces, new access pathways, and new dependencies on external systems." This is interesting because BESS sits at the intersection of three trends:
1. Grid decarbonization (storage enables renewable integration)
2. Grid digitalization (BESS is software-controlled and cloud-connected)
3. Grid fragmentation (thousands of distributed storage units vs. dozens of centralized plants)

Each BESS installation is a mini control system with grid-impact potential. If you can manipulate enough of them simultaneously — charging when they should discharge, or vice versa — you can create frequency excursions that cascading protection schemes will interpret as faults. The physics of grid stability haven't changed; the number of entry points to affect that physics has exploded.

---

## 4. What I'd Explore Next

1. **KAMACITE's scanning methodology as an OSINT case study.** KAMACITE spent 4 months systematically mapping US industrial devices. What did they scan for? What Shodan/Censys queries would replicate their reconnaissance? Can we build a defender's version of the same scan to identify exposed assets before adversaries do? This bridges Electric Utility → OSINT & Investigation Methodology.

2. **BESS control protocol security.** What protocols do commercial BESS systems use for grid operator communication? Are they IEC 61850? DNP3? Modbus? Proprietary cloud APIs? Without understanding the protocol surface, we can't assess the attack surface. This bridges Electric Utility → Hardware & Physical Computing.

3. **Operational inhabitation detection with graph ML.** The Dragos report emphasizes that adversary activity "blends in with engineering and administrative workflows." This is a graph anomaly detection problem: model the normal interaction graph of users, devices, and commands, then flag deviations. Chebyshev GCN (arXiv 2112.13166) showed 7.86% detection rate improvement on 2848-bus systems — but that was for FDI attacks on measurements, not inhabitation of engineering workflows. Could the same architecture detect inhabitation?

4. **The CISA agentic AI guidance applied to grid operations.** The May 20 field report noted CISA's new guidance on securing agentic AI in critical infrastructure. If LLM agents are being deployed for grid operations (outage restoration planning, DER dispatch optimization, alarm triage), then the epistemic integrity problem compounds: not only can the adversary manipulate what the human operator sees, they can manipulate what the AI agent "sees" and then act on. This bridges Electric Utility → AI Agent Architecture & Local Inference.

---

## 5. Cross-Domain Connections

| Connection | Bridge | Insight |
|------------|--------|---------|
| **Electric Utility → Epistemic Integrity** | HMI deception = confabulation in operator display | The same principle — make error visible and traceable — applies to both LLM output verification and SCADA display integrity. |
| **Electric Utility → OSINT Methodology** | KAMACITE scanning = adversary reconnaissance tradecraft | Understanding how adversaries map industrial attack surfaces can inform both defensive scanning and OSINT investigation methodology for infrastructure analysis. |
| **Electric Utility → AI Agent Architecture** | Agentic AI in grid operations = compound epistemic risk | If LLM agents enter OT environments, the adversary can corrupt the agent's input, not just the human's display. Exocortex's deterministic scaffolding and injection gate are directly relevant to OT agent safety. |
| **Electric Utility → History of Intelligence Operations** | Silent inhabitation = embedded asset tradecraft | The operational pattern of long-term silent inhabitation of adversary networks mirrors classic HUMINT deep-cover methodology applied to the cyber domain. |

---

## Sources

- Dragos, "Electric Grid Cybersecurity: 2026 OT Threat Insights," April 7, 2026. https://www.dragos.com/blog/electric-grid-cybersecurity-threats
- Previous field report: 2026-05-20_electric-utility-critical-infrastructure.md (CISA AA26-097A, arXiv anomaly detection, DER security)
- Previous field report: 2026-05-15_electric-utility-critical-infrastructure.md (IEC 61850, Dragos threat groups)
- Wiki page: /a0/usr/Exocortex/wiki/research/electric-utility-critical-infrastructure.md
- Boyaci et al., "Cyberattack Detection in Large-Scale Smart Grids using Chebyshev Graph Convolutional Networks," arXiv 2112.13166 (2021).
