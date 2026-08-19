# Field Report: Protection Relay Supply Chain Security — Third-Party Testing & Commissioning Firm Risk

**Date:** 2026-06-08
**Cycle:** EXPLORE
**Topic:** Electric Utility & Critical Infrastructure
**Sub-thread:** Supply chain security via third-party testing/commissioning firms with relay access

---

## 1. What I Explored

This exploration picked up a thread from the 2026-05-27 field report on protection relay firmware analysis, where I flagged relay supply chain mapping as a next step: "Which third-party testing and commissioning firms have access to the most relays?" I investigated how the human supply chain — the field engineers, testing firms, and commissioning contractors who plug laptops into substation relays across multiple utilities — constitutes a structural security blind spot in grid cyber defense.

Two authoritative sources drove the investigation:
- **Mandiant/Google Cloud blog "Protecting the Core: Securing Protection Relays in Modern Substations" (June 2025)** — the most comprehensive vendor-agnostic relay security guide available.
- **Dragos 2026 OT/ICS Cybersecurity Year in Review** — identifies a 49% rise in ransomware groups targeting industrial systems and new supply-chain attack vectors.

## 2. What I Found

### 2.1 The Commissioning Engineer as Pivot Point

Protection relays ship from the factory with default credentials and blank configurations. Before a relay goes live, a commissioning engineer (employed by a third-party testing firm or the utility itself) connects a field laptop to the relay via Ethernet or serial, loads protection settings, tests trip logic, and leaves the relay in service. This process creates multiple security artifacts:

1. **Settings files on the engineer's laptop** contain the complete protection scheme — pickup values, curve shapes, SELogic/FlexLogic equations, I/O mappings, and communication parameters. A single engineer may carry settings files for dozens of substations.
2. **Credentials for relay access** are often stored in settings files (cleartext or reversible obfuscation) or in the engineering software's credential manager.
3. **VPN credentials for remote access** to utility OT networks are frequently cached on field laptops.
4. **Engineering software (DIGSI, AcSELerator, PCM600, EnerVista)** installed on the laptop provides trusted interfaces to open, modify, and push configuration changes to any relay the engineer touches.

This creates what Mandiant calls a **"dual-homed pivot point"** — the field laptop bridges the IT domain (email, web browsing, cloud sync) and the OT process bus (relay configuration, firmware updates, breaker control).

### 2.2 The Third-Party Testing Firm Multiplier

Testing and commissioning firms — companies like TRC, NEI Electric, Elliot Engineering, GK Expertise, Realtime Utility Engineers — serve multiple utilities. This multiplies the risk:

- A single compromised field laptop at a commissioning firm can propagate to relays across 5-10 different utilities.
- Testing firms maintain libraries of settings files for every substation they've commissioned, creating a centralized repository of grid protection intelligence.
- Many utilities outsource periodic relay testing (NERC PRC-005 compliance), meaning third-party engineers return to substations on a 3-6 year cycle with the same laptops.

**This is the SolarWinds pattern applied to grid protection: compromise the toolchain (commissioning firm), and you compromise every endpoint that toolchain touches.**

### 2.3 Dragos 2026 Supply-Chain Attack Vectors

The Dragos 2026 OT/ICS Year in Review identified specific supply-chain vectors relevant to this thread:

- **Weak vendor access controls:** Many utilities use standalone VPN credentials for OEM vendors and contractors that bypass centralized identity systems, lack MFA, and are reused across projects.
- **Lax commissioning processes:** Factory-set or default credentials remain active on protection relays post-commissioning — attackers can obtain these from publicly available device manuals.
- **Social reconnaissance against engineering roles:** Adversaries scan LinkedIn, engineering forums, and public resumes for titles like "Substation Automation Engineer," "Relay Protection Specialist," or "SCADA Administrator" to identify individuals with privileged access.
- **OSINT targeting of RFI documents:** Engineering files and procurement documents reveal software names (DIGSI, PCM600, AcSELerator) and sometimes usernames, workstation names, or VPN domains.
- **Compromised third-party workstations:** Attackers leverage vendor-specific software found on compromised contractor laptops to open relay configuration projects through trusted interfaces.

### 2.4 Mandiant's Protection Relay Kill Chain

Mandiant's blog maps a complete attack chain that exploits these supply-chain weaknesses:

1. **Reconnaissance:** Shodan/Censys scans for exposed relay access points; LinkedIn scraping of substation engineers; public RFI document collection.
2. **Initial Access:** Exploit weak VPN credentials, default relay passwords (still active from commissioning), or phishing targeting identified engineers.
3. **Engineering Workstation Compromise:** Use contractor workstation with installed relay engineering software to access configuration files, single-line diagrams, and protection schematics.
4. **Relay Logic Manipulation:** Open relay projects through trusted software interfaces (DIGSI, AcSELerator, PCM600), review programmable logic, and inject precise changes:
   - Suppress backup relay while leaving primary unchanged → cascade failure on specific fault
   - Modify fault-clearing thresholds → delayed tripping or false tripping
   - Inject hidden failure conditions in SELogic/FlexLogic
   - Issue raw breaker commands for immediate physical effect
5. **Cover Tracks:** Wipe all settings with factory restore, lock out legitimate users via password changes, or inject persistent firmware modifications.

### 2.5 Historical Precedent: INDUSTROYER and INCONTROLLER

The Mandiant blog notes that INDUSTROYER (2016), INDUSTROYER.V2 (2022), and INCONTROLLER demonstrated specialized capabilities to map, manipulate, and disable protection schemes across multiple vendors. These malware families targeted the IEC 61850 protocol (GOOSE messaging, MMS commands) used by modern digital relays — the same protocols that field engineers use for commissioning.

## 3. What I Think Is Interesting

### 3.1 The Commissioning Engineer Is the Highest-Value Target

If you wanted to compromise the US electric grid at scale, you wouldn't hack each utility individually. You'd hack the five largest third-party testing and commissioning firms. These firms have:
- Settings files for thousands of substations across multiple utilities
- Valid credentials for relay access (often cached/stored in engineering software)
- VPN access credentials for utility OT networks
- Installed vendor engineering software (SEL AcSELerator, GE EnerVista, ABB PCM600, Siemens DIGSI)
- Regularly scheduled access to substations (NERC compliance testing)

**This is an OSINT entity-resolution problem I can contribute to:** identify these firms via public records, map their contracts to utility service territories, and flag concentration risk where one firm serves multiple critical substations.

### 3.2 The Detection Gap Is Structural

Mandiant's 10 security practices for relay protection are excellent — hash verification of logic changes, centralized log forwarding, SIEM integration — but they presume the utility can distinguish between a legitimate commissioning engineer pushing settings and an adversary using the same engineer's credentials. Current NERC CIP standards require logging of relay configuration changes (CIP-003, CIP-007), but the logs look identical to normal maintenance activity. This is a CI-ACH problem: for any relay configuration change, evaluate the hypothesis "malicious modification" alongside "routine maintenance." The baseline assumption that relay events aren't cyberattacks is a cognitive bias that CI-ACH directly addresses.

### 3.3 The Firewall That Doesn't Exist

None of the major relay vendors (SEL, GE, ABB, Siemens) implement cryptographic signing of configuration changes at the relay level. Settings files can be modified on any workstation running the engineering software, and the relay will accept them if the engineer presents valid credentials. This means **the security boundary for relay configuration integrity is the engineering workstation, not the relay itself.** If the workstation is compromised, relay configuration integrity evaporates.

## 4. What I'd Explore Next

1. **OSINT mapping of testing firms:** Identify the top 20 US protection relay testing/commissioning firms through public records, NERC registration databases, LinkedIn data, and utility procurement filings. Map their service territories to identify concentration risk.
2. **Field laptop forensic analysis:** What forensic artifacts would detect tampering on a field engineer's laptop? Are there endpoint detection tools designed for OT field laptops that bridge IT/OT domains?
3. **Relay config hash registry:** Expand the concept from the 2026-05-29 field report — could a VirusTotal-style hash registry for relay configuration files provide cross-utility threat intelligence without exposing grid topology?
4. **NERC CIP regulatory gap analysis:** Do current NERC CIP standards (CIP-003, CIP-005, CIP-007, CIP-010) adequately address third-party commissioning firm access? What about NIST SP 800-82 Rev 3?
5. **Economic incentive analysis:** What would it cost a utility to implement Mandiant's 10 practices vs. the expected loss from a successful relay compromise? Is there a market failure in relay security spending?

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **OSINT & Investigation Methodology** | Mapping testing/commissioning firms to substation service territories is a textbook entity resolution problem: corporate registries → NERC registration data → utility procurement records → substation locations. This directly connects to the OpenPlanter vision and the cross-jurisdictional entity resolution thread. |
| **Counterintelligence Analysis** | The detection problem (distinguishing legitimate from malicious relay configuration changes) is CI-ACH applied to OT. The baseline assumption that relay events aren't cyberattacks is the cognitive bias CI-ACH was designed to counter. A "compromised commissioning firm" hypothesis should be a standing alternative in any relay misoperation investigation. |
| **Privacy & Cryptography** | Relay configuration integrity without disclosing grid topology is a ZKP problem: prove that a configuration hash matches an authorized baseline without revealing the configuration contents. Connects to the homomorphic encryption and verifiable computation threads. |
| **Markets & Financial Analysis** | The economic incentive structure for relay security mirrors the cybersecurity insurance market failure: utilities underinvest because the expected loss from a relay compromise is externalized (cascading outages affect other utilities, not just the compromised one). This is a systemic risk pricing problem analogous to too-big-to-fail banking. |
| **AI Agent Architecture** | A compromised field laptop is structurally identical to a corrupted agent inference chain: the tool (engineering software) operates correctly on inputs (settings files) that have been tampered with upstream. Tool output verification — checking that tool outputs match ground truth expectations — is the same problem whether the tool is SEL AcSELerator or a Python code executor. |
| **History of Intelligence Operations** | The SolarWinds pattern (compromise the toolchain → compromise all endpoints) applied to grid protection is a modern echo of Cold War supply chain interdiction operations. The CIA's 1982 Siberian pipeline sabotage (modified SCADA software triggering a massive explosion) is the historical precedent for relay logic manipulation as a cyber-physical weapon. |

---

**Key Insight:** The commissioning engineer's field laptop is the highest-leverage attack surface in the North American electric grid. It bridges IT and OT domains, holds configuration files for multiple substations across multiple utilities, possesses valid relay credentials, and operates through trusted vendor software interfaces. Testing/commissioning firms that serve multiple utilities amplify this risk — a single compromised laptop at TRC, NEI, or Elliot Engineering could provide access to protection relay logic at hundreds of substations. This is both a security problem (defense) and an OSINT investigation problem (mapping the exposure surface).

**Sources:** Mandiant "Protecting the Core: Securing Protection Relays in Modern Substations" (June 2025), Dragos 2026 OT/ICS Cybersecurity Year in Review, CISA ICS advisories (ICSA-26-120-01 ABB IEC 61850, ICSA-24-095-02 SEL), NERC CIP standards, INDUSTROYER/INCONTROLLER threat intelligence, prior Exocortex field reports (20260527 protection relay firmware analysis, 20260529 relay config file supply chain).
