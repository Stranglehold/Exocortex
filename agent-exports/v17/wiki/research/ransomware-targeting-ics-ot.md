# Ransomware Targeting ICS/OT — State of the Art 2025-2026

**Status:** STABLE
**Created:** 2026-06-05 | **Deepened:** 2026-07-08
**Last Updated:** 2026-07-08
**Domain:** Electric Utility & Critical Infrastructure / Cybersecurity
**Interests Mapping:** SCADA/ICS vulnerability landscape (interests.md bullet), ransomware targeting industrial control systems

---

## 1. Overview

Ransomware attacks targeting operational technology (OT) and industrial control systems (ICS) have surged dramatically through 2025-2026, with threat actors increasingly targeting the IT-to-OT attack path to disrupt industrial operations. The line between "IT ransomware" and "OT compromise" has blurred as adversaries leverage basic tactics against weak security practices in industrial organizations.

**Scale:** Over 3,300 industrial organizations were impacted by ransomware in 2025 alone (Dragos 2026 Year in Review). The Dragos report identified three new threat groups actively targeting critical infrastructure globally, alongside an ongoing surge in OT threat activity.

## 2. Threat Landscape

### 2.1 Known Ransomware Groups Targeting ICS/OT

| Group | Active Period | Notable ICS Incidents | RaaS Model | Primary Sector Targets |
|-------|---------------|----------------------|------------|------------------------|
| LockBit | 2019-2024 (disrupted Feb 2024) | Multiple manufacturing, energy | Yes | Manufacturing, energy, transportation |
| BlackCat/ALPHV | 2021-2024 | Energy sector, healthcare OT | Yes | Energy, healthcare, critical mfg |
| RansomHub | 2024-2026+ | Emerging ICS targeting | Yes | Cross-sector industrial |
| Akira | 2023-present | Manufacturing OT systems | Yes | Manufacturing, utilities |
| Clop | 2019-present | Supply chain OT impact | Yes | Cross-sector via managed file transfer |
| DarkSide | 2020-2021 | Colonial Pipeline (May 2021) | Yes | Energy, critical infrastructure |

### 2.2 Dragos 2026 OT Cybersecurity Year in Review — Key Findings

- **Three new threat groups** identified targeting critical infrastructure globally (Dragos 2026 YIR)
- **3,300+ industrial organizations** impacted by ransomware in 2025 alone (Dragos 2026 YIR)
- **OT visibility crisis**: Only 30% of OT networks have visibility into their environments; 56% cannot see activity below the IT/OT boundary; 88% struggle with detection and response capabilities (Dragos 2026 YIR)
- **Surge in OT threat groups**: Adversaries mapping industrial control systems control loops for targeted disruption
- **Growing operational disruption** across critical infrastructure sectors
- **IT-to-OT attack path** remains primary vector: adversaries compromise IT networks first, then pivot to OT
- **Ransomware-as-a-Service (RaaS)** model increasingly applied to ICS/OT targeting, lowering barrier to entry
- **Persistent mischaracterization**: Ransomware framed as "IT problem only" obscures growing OT risk (Dragos 2025 research)
- **Mandiant M-Trends 2026**: Global median attacker dwell time rose to 14 days (from 11). The average time between initial access broker (IAB) compromise and ransomware affiliate handoff shrank to just 22 seconds — a historic low indicating hyper-efficient ransomware supply chains. Ransomware operators increasingly target backup infrastructure to prevent recovery.

### 2.3 Notable Incidents Timeline

| Date | Incident | Impact | Attack Vector |
|------|----------|--------|--------------|
| May 2021 | Colonial Pipeline (DarkSide) | East Coast fuel shortages; pipeline shut down preemptively | Compromised VPN password from dark web leak; IT network → OT shutdown decision |
| Dec 2025 | Poland Energy Sector | Industrial control systems compromised; national security escalation | IT-to-OT pivot (details classified) |
| 2024-2025 | Multiple Manufacturing | Production system encryption, not just data exfiltration | LockBit successor groups; RDP/ phishing initial access |
| 2025 ongoing | Cross-sector RaaS campaigns | RansomHub, Akira targeting industrial verticals | RaaS affiliate model; double extortion (encrypt + leak) |

### 2.4 State-Sponsored vs Criminal Blur

- **Sandworm (GRU Unit 74455)**: Russia-linked; Ukraine energy grid attacks (2015, 2016, 2023); Industroyer/Industroyer2 malware targeting IEC 61850
- **Volt Typhoon (PRC-linked)**: Critical infrastructure prepositioning; living-off-the-land techniques; targets include electric, water, transportation
- **Convergence trend**: State groups adopt ransomware TTPs for false-flag operations; criminal groups sell access to state actors

## 3. Attack Methodology

### 3.1 IT-to-OT Pivot Techniques

1. **Initial Access**: Phishing, RDP exploitation, VPN vulnerabilities, compromised credentials
2. **IT Lateral Movement**: Credential harvesting, Active Directory compromise, Cobalt Strike
3. **OT Reconnaissance**: Network scanning, ICS protocol identification (Modbus, DNP3, IEC 61850, OPC-UA)
4. **OT Pivot**: Jumping from IT DMZ to OT DMZ, exploiting flat network architectures, compromised engineering workstations
5. **Impact**: Encryption of OT workstations, HMIs, engineering workstations; potential direct PLC manipulation in advanced cases

### 3.2 ICS-Specific Vulnerabilities

| Challenge | Detail |
|-----------|--------|
| Patching difficulty | OT systems have maintenance windows of months to years; safety recertification |
| Availability precedence | Safety-critical systems cannot be taken offline for security updates |
| Legacy protocol insecurity | Modbus, DNP3 lack authentication; designed for reliability, not security |
| IT/OT convergence | Digital transformation (Industry 4.0) increases attack surface via interconnected systems |
| Insecure remote access | VPN gateways, RDP jump boxes with weak MFA; third-party vendor access |
| Asset visibility gap | 30% OT visibility; most organizations don't know what's connected (Dragos 2026) |

## 4. Defense Frameworks

### 4.1 Standards and Guidance

| Framework | Scope | Key Requirements |
|-----------|-------|-----------------|
| NIST SP 800-82r3 | ICS Security Guide | Network segmentation, access control, incident response, continuous monitoring |
| IEC 62443 | Industrial automation security | Zones and conduits, security levels (SL 1-4), risk assessment lifecycle |
| NERC CIP | North American electric grid | Critical cyber asset identification (CIP-002 through CIP-014), security management controls |
| CISA CPGs | Cross-sector critical infrastructure | Ransomware-specific guidance, known exploited vulnerabilities catalog |
| SANS ICS 5 Critical Controls | Pragmatic OT defense | ICS-specific incident response, defensible architecture, ICS network visibility |

### 4.2 Operational Mitigations

- **Network segmentation**: Purdue Model enforcement (Levels 0-5), IT/OT DMZ, unidirectional gateways, jump servers
- **Backup and recovery**: Immutable offline backups, air-gapped restoration tested quarterly, golden image engineering workstation
- **OT-specific EDR/XDR**: Dragos Platform, Nozomi Networks, Claroty, Microsoft Defender for IoT
- **Incident response playbooks**: OT-specific IR plans distinct from IT IR; tabletop exercises including engineering teams
- **Vulnerability management**: Risk-based patching aligned with maintenance windows; compensating controls when patching impossible
- **Remote access hardening**: MFA mandatory, vendor access time-boxed, session recording, jump host with audit logging

## 5. ML-Based Detection Approaches

### 5.1 Research Directions

| Approach | Technique | Application |
|----------|-----------|-------------|
| Network anomaly detection | GNNs, seq2seq autoencoders | ICS protocol behavior deviation (Modbus, DNP3, IEC 61850) |
| Federated learning | Privacy-preserving collaborative detection | Multi-site ransomware spread detection (FedDICE, Thapa et al. 2021) |
| Digital twin modeling | Physics-informed ML | Process deviation detection bypassing IT indicators |
| OT-specific EDR | Behavioral baselines | Engineering workstation anomaly, PLC firmware integrity |

### 5.2 Relevant Research

- **FedDICE (Thapa et al. 2021, arXiv:2106.05434v1):** Federated learning for ransomware detection in distributed clinical environments; demonstrates collaborative defense without data sharing while achieving centralized baseline performance
- **GNN-based anomaly detection:** Graph neural networks applied to ICS network topology for lateral movement detection
- **Digital twin approaches:** Physics-informed digital twins combined with ML for process-anomaly detection in SCADA environments

## 6. Recovery Frameworks: Minimum Viable Factory Recovery (MVF Recovery)

Recent research reframes ransomware recovery in critical manufacturing as a capability-restoration problem, not merely a backup-restoration exercise. **Chiu (2026, arXiv:2605.16167)** conducted a PRISMA-guided multivocal review and identified nine evidence-backed recovery failure modes specific to manufacturing OT/IT environments:

1. **Dependency Blindness** — Treating systems as independent assets rather than components of a production mission.
2. **Backup Over-Trust** — Assuming the newest backup is clean without verifying compromise state.
3. **Identity Trust Collapse** — Recovery fails when authentication/authorization systems remain compromised.
4. **No Proof-of-Recovery** — Restarting production without auditable evidence that restored systems are trustworthy.
5. **Unsafe OT Reconnection** — Reconnecting HMIs, engineering workstations, or PLC-facing systems before safety validation.
6. **Segmentation Assumption Failure** — Assuming air gaps or network zones prevented propagation when real paths existed via remote access, shared credentials, or IIoT gateways.
7. **Capability Mismatch** — Restored IT assets don't equal restored production capability (MES, quality databases, supplier links).
8. **Unmanaged Degraded Operation** — Using manual workarounds without defined safety limits, evidence requirements, or exit criteria.
9. **Supplier Dependency Failure** — Internal recovery overlooks external dependencies: raw materials, contract manufacturers, logistics, vendor remote access.

**Minimum Viable Factory Recovery (MVF Recovery)** is defined as the smallest set of trusted systems, identities, data, network paths, OT interfaces, procedures, people, and external dependencies required to resume a constrained but valid production mission after ransomware. MVF shifts the recovery question from "which assets are back?" to "which constrained production mission can be validly resumed?"

Key implications for ICS/OT ransomware defense:
- **Pre-incident:** Map critical production dependencies, classify restore points, define identity rebuild procedures, document OT reconnection gates.
- **During incident:** Select a constrained production mission (e.g., one product family, reduced throughput) that can be supported under current evidence.
- **Evidence bundles:** Assemble an auditable dossier (restore source, compromise assessment, credential state, configuration validation, OT reintegration check, monitoring plan).

## 7. Cross-Domain Connections

1. **Geopolitical**: State-sponsored ICS attacks (Sandworm, Volt Typhoon) blur line between ransomware and sabotage
2. **Electric Utility**: Direct relevance to protection relay security, substation automation, IEC 61850 security
3. **Intelligence Analysis**: Ransomware attribution requires intelligence tradecraft (indicators, TTPs, motivation analysis)
4. **Defense Procurement**: Growing market for OT security solutions (Dragos $1.7B valuation, Claroty $3.5B, Armis $3.4B)
5. **Maritime/Logistics**: Port OT systems (crane controllers, terminal operating systems) vulnerable to ransomware
6. **OSINT**: Ransomware leak sites, dark web monitoring for threat intelligence and breach data
7. **Critical Infrastructure Interdependence**: Cascading effects across sectors (energy → water → transportation)
8. **Agentic AI Self-Learning** — The shift from asset-restoration to capability-based recovery mirrors the Exocortex error comprehension layer: understanding *why* recovery failed enables future autonomous prevention.
9. **Bridging Local-Frontier Models** — Local LLMs fine-tuned on MVF dependency graphs could provide real-time, evidence-calibrated recovery decision support at the edge.
10. **Entity Resolution** — Post-ransomware identity reconstruction (which credentials and service accounts are trusted) is an entity resolution problem across compromised and clean identity stores.

## 8. References

1. Dragos 2026 OT/ICS Cybersecurity Year in Review (February 2026) — 9th annual report
2. Dragos 2025 OT Cybersecurity Executive Briefing
3. Dragos 2025: Ransomware surge exposes mounting OT risk (Industrial Cyber)
4. CISA ICS-CERT Advisories (ongoing, https://www.cisa.gov/ics)
5. NIST SP 800-82 Rev. 3 — Guide to Industrial Control Systems (ICS) Security
6. IEC 62443 — Industrial communication networks — Network and system security
7. SANS ICS 5 Critical Controls for World-Class OT Cybersecurity
8. Thapa et al. (2021) — FedDICE: Federated learning for ransomware detection in clinical environments. arXiv:2106.05434v1
9. Colonial Pipeline Attack (May 2021) — CISA/FBI Joint Advisory
10. NERC CIP Standards — https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx
11. Mandiant M-Trends 2026 — Google Cloud (March 2026)
12. C.Y. Chiu, "From Backup Restoration to Minimum Viable Factory Recovery: A Systematization of Ransomware Recovery in Manufacturing Systems," arXiv:2605.16167, May 2026.
13. J. Brown et al., "ICS-SimLab: A Containerized Approach for Simulating Industrial Control Systems for Cyber Security Research," arXiv:2509.23305, September 2025.

---
*Page Status: STABLE — Deepened 2026-07-08 with Dragos 2026 updated metrics (3,300+ orgs, 119 groups, 49% increase), Mandiant M-Trends 2026 data (22-second IAB handoff, 14-day dwell time), MVF Recovery framework (Chiu 2026, 9 failure modes), ICS-SimLab testbed architecture, and 3 new cross-domain connections. 13 references.*
