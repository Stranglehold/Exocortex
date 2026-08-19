# Field Report: IEC 61850 GOOSE & MMS Security — Substation Attack Surface

**Date:** 2026-05-27  
**Cycle:** EXPLORE  
**Topic:** Electric Utility & Critical Infrastructure > IEC 61850 GOOSE/MMS security

---

## 1. What I Explored

IEC 61850 is the international standard for communication in electrical substations. It defines three key protocols: **GOOSE** (Generic Object-Oriented Substation Events — multicast breaker trip/close commands), **SV** (Sampled Values — streaming CT/VT measurements), and **MMS** (Manufacturing Message Specification — SCADA-to-IED client/server read/write). None of these protocols were designed with encryption or authentication in the original standard. My investigation focused on the current (2025–2026) vulnerability landscape, attack techniques, and defenses.

## 2. What I Found

### GOOSE Protocol Vulnerabilities

GOOSE messages are transmitted over Ethernet (EtherType 0x88B8) without natively built encryption or authentication. This means any adversary with network access to the process bus can:

1. **Capture and replay** legitimate GOOSE messages with modified state numbers (`stNum`) and sequence numbers (`sqNum`) to force IEDs to accept false open/close commands [MDPI Sensors, 2021]
2. **Masquerade** as a legitimate IED by spoofing MAC addresses — demonstrated in lab conditions by the ACM study "Masquerading IEC 61850 GOOSE Protocol: Cyber-Physical Experiments and ..." (2025), which showed circuit breaker opening can lead to widespread outages or equipment damage
3. **DoS** via message flooding — the PMC study (2021) showed significant increases in system delay and prevention of GOOSE/SV messages
4. **Frame injection** — spoofed GOOSE frames can be injected with modified boolean values (`allData`), changing breaker states

### MMS Protocol Vulnerabilities

MMS operates over TCP port 102 and is used by engineering workstations (ABB PCM600, Siemens DIGSI) to configure IEDs. Vulnerabilities include:

1. **Claroty Team82** (2024) discovered five vulnerabilities in MMS protocol implementations, enabling device crashes and remote code execution in certain scenarios
2. **CISA ICSA-23-089-01:** Hitachi Energy Relion 670/650/SAM600-IO products — specially crafted message sequences could crash the MMS-server, preventing new MMS client connections while existing connections remained active
3. **IEC61850Bean attacks:** The open-source Java library IEC61850Bean enables attackers to enumerate, read, and manipulate field device states (circuit breaker positions) via MMS
4. **ArXiv 2601.03690v1** (2026): Developed a fully automated attack detection/prevention framework for IEC 61850 smart substations, demonstrating detection of IEC61850Bean-based attacks and libiec61850 script-driven attacks on the EPIC testbed

### Defenses & Mitigations

**IEC 62351** is the companion security standard:
- **62351-3:** TLS for MMS (encrypts SCADA-IED traffic)
- **62351-4:** SNMPv3 with authentication/privacy
- **62351-5:** HMAC for GOOSE frames
- **62351-6:** Digital signature validation for GOOSE/SV messages (critical — prevents replay attacks)
- **62351-8:** Role-based access control

**Practical hardening per undercodetesting.com (2026 guide):**
- Network segmentation: separate process bus VLANs, port security (MAC filtering), storm control
- GOOSE MAC whitelisting on IEDs (e.g., SEL-421: `SET G 1 GOOSEMAC = 01-0C-CD-01-00-01`, enable `GOOSESEC = 1`)
- Hardware GOOSE firewalls (SEL-5030) that drop unauthenticated messages inline
- Windows workstation hardening: disable unused MMS sessions, restrict MMS to allowed IPs via firewall, disable LLMNR/NetBIOS to prevent credential relay
- AI anomaly detection: isolation forests trained on baseline GOOSE traffic (Scapy + scikit-learn) can detect zero-day attacks; 2028 prediction: 60% of new digital substations will mandate hardware-enforced GOOSE authentication (TPM-based signatures)
- Open-source tools: Wireshark/tshark for capture, Scapy for crafting malicious GOOSE (stNum manipulation, allData injection), Snort/Suricata for IDS

### Regulatory Landscape

- **NERC CIP** (Critical Infrastructure Protection) standards
- **IEC 62443-4-2** (component security for IACS)
- **IEEE 1547:** DER interconnection standard (relevant to inverter-based resource security)
- CISA ICS-CERT advisories and Dragos threat reports track APT groups targeting substations

## 3. What I Think Is Interesting

**The central paradox:** GOOSE messages need sub-4ms latency for protection schemes (breaker failure, bus differential). Adding TLS or heavyweight authentication breaks this timing requirement. This is why IEC 62351-6 uses lightweight digital signatures rather than full encryption. The result: a security architecture fundamentally shaped by physics, not just policy.

**Convergence with Jake's day job:** As a field engineer working with protection relays (SEL, GE, ABB), Jake is the person who configures `GOOSEMAC` and `GOOSESEC` settings. The security of the substation literally depends on him turning on authentication features that many utilities leave disabled for convenience. This connects directly to: SCADA/ICS vulnerability landscape already explored (field report 20260526_scada-ics-vulnerability-landscape.md).

**The IEC61850Bean threat:** This Java library is open-source and publicly available. It provides a ready-made toolkit for attackers to enumerate and manipulate IED states. The barrier to substation cyber attack is frighteningly low.

**AI defense asymmetry:** Both attackers and defenders are adopting AI. Attackers use ML to craft undetectable GOOSE fuzzing; defenders use isolation forests and behavioral IDS to detect anomalies. The winner is determined by data quality — who has better baseline traffic models.

## 4. What I'd Explore Next

1. **IEC 61850 Sampled Values (SV) attacks:** SV messages (EtherType 0x88BA) carry current/voltage samples. Spoofed SV could cause protection relays to trip on phantom faults. Less explored than GOOSE.
2. **SEL relay firmware security:** Schweitzer Engineering Laboratories relays dominate the North American market. What firmware vulnerabilities exist? Can configuration files (.rdb, .set) be reverse-engineered to extract passwords?
3. **Hardware-in-the-loop testbeds:** How to build a portable IEC 61850 security lab using Raspberry Pi, libiec61850, and open-source tools for penetration testing
4. **NERC CIP enforcement gaps:** How many utilities actually enable IEC 62351 authentication? What does audit data show?

## 5. Cross-Domain Connections

- **SCADA/ICS vulnerability landscape** — previously explored (field report 20260526_scada-ics-vulnerability-landscape.md): IEC 61850 is the specific protocol used within SCADA for substation automation
- **Entity resolution & OSINT** — an attacker performing infrastructure reconnaissance would combine substation asset lists (public filings, Google Earth) with IEC 61850 exploit tools. The entity resolution framework from that interest domain could model attacker pre-positioning
- **Hardware & FPGA** — hardware GOOSE firewalls like SEL-5030 require FPGA-level packet processing to maintain sub-4ms latency while validating signatures. FPGA inference acceleration (from hardware interest) could be applied to inline behavioral IDS
- **Anti-bot evasion** — attackers connecting to MMS on port 102 must evade detection. Techniques explored in anti-bot evasion research (browser fingerprinting, TLS impersonation) have parallel applications in protocol-level obfuscation
- **Defense procurement** — the $multi-billion market for inline process bus security gateways (predicted by undercodetesting) connects to defense procurement cycle analysis
