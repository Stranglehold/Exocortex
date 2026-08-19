# Field Report: Protection Relay Configuration File Supply Chain Security
**Date:** 2026-05-29
**Cycle:** EXPLORE
**Topic:** Electric Utility & Critical Infrastructure
**Sub-thread:** Protection relay configuration file formats, security risks, and entity resolution cross-domain application

---

## 1. What I Explored

I investigated how protection relay configuration files represent an under-explored attack surface in substation cybersecurity, with a focus on supply chain integrity — how configuration files created, stored, and transferred across engineering workstations, field laptops, and relay management systems can be weaponized by adversaries. I examined the Mandiant/Google Cloud blog *"Protecting the Core: Securing Protection Relays in Modern Substations"* released June 30, 2025, which provides an authoritative vendor-agnostic analysis of relay attack surfaces and exploitation techniques.

## 2. What I Found

### 2.1 Configuration File Formats at Risk

Modern protection relays from all major vendors store settings, logic, and protection parameters in vendor-specific file formats:

| Vendor | Configuration Tool | File Formats |
|--------|-------------------|--------------|
| SEL | AcSELerator QuickSet | `.rdb` (Relay Database), SELogic control equations |
| GE/Multilin | EnerVista | `.set`, FlexLogic equations |
| ABB/Hitachi | PCM600, CAP | CAP tool logic, IEC 61850 SCL files |
| Siemens | DIGSI 4/5 | `.prj`, CFC logic diagrams |

These files are typically stored on engineering workstations with minimal access controls, shared via USB drives, emailed between field engineers, and backed up to network shares accessible from IT domains. They form a **supply chain for relay behavior** that has no integrity verification in most utilities.

### 2.2 Attack Vectors Identified

The Mandiant analysis identifies a clear kill chain:

1. **Initial Access (IT):** Phishing, credential theft, exposed VPNs
2. **IT Reconnaissance:** BloodHound mapping for OT-related AD groups (e.g., `scada_substation_admin`)
3. **OT Pivoting:** Compromised engineering workstations via RDP or jump hosts
4. **Configuration Discovery:** `.cfg`, `.prj`, `.set` files found on shared drives and laptops
5. **Process-Aware Enumeration:** Attacker matches relay configs to single-line diagrams to identify which relays control which zones
6. **Logic Manipulation:** Modification of trip equations (TR logic), disabling of protection, embedding remote-trigger backdoors, spoofed LED indicators, and event log tampering

### 2.3 Specific Exploitation Techniques Documented

- **Trip Logic Suppression:** Changing `TR = (normal) + ...` to `TR = 0` (never trips) or `TR = 50P1 * !SH0` (impossible condition)
- **Hidden Backdoors:** `TR = original + RB15` — attacker can trip via remote bit
- **Distance Protection Under-Reaching:** Reducing Z1MAG from 1.0 to 0.3 makes relay blind to 70% of protected line
- **Reclose Abuse:** `79RI = 1` forces immediate reclose into sustained faults
- **Event Log Tampering:** `SER C` command clears Sequential Event Recorder, erasing forensic evidence
- **Persistence:** Password modification to lock out operators

### 2.4 INCONTROLLER/PIPEDREAM and State-Sponsored Threats

The blog notes INDUSTROYER (2016), INDUSTROYER.V2 (2022), and INCONTROLLER as demonstrating specialized capabilities to map, manipulate, and disable protection schemes across multiple vendors. Current threat actors: UNC5691 (Iran/CyberAv3ngers targeting water facilities), UNC5135 (China/Volt Typhoon embedding in US critical infrastructure).

### 2.5 Top 10 Security Practices (Mandiant, 2025)

1. Authentication & Role Separation
2. Secure Firmware & Configuration Updates
3. Network & Protocol Hardening
4. Time Synchronization & Logging Protection
5. **Custom Logic Integrity Protection** — hash verification of logic changes
6. Physical Interface Hardening
7. Redundancy and Failover Readiness
8. Remote Access Restrictions & Monitoring
9. Command Supervision & Breaker Output Controls
10. Centralized Log Forwarding & SIEM Integration

## 3. What I Think Is Interesting

**Practice #5 is the configuration file supply chain problem.** Mandiant recommends hash verification. This is structurally identical to software supply chain integrity (git hash, Sigstore, SBOMs applied to relay configs).

The key insight: **every protection relay configuration file has a unique hash representing a specific protection scheme logic state.** A utility could publish hashes to a shared anonymous registry; matching known-malicious hashes would provide cross-utility threat intelligence without sharing sensitive grid topology data. Same pattern as VirusTotal hash sharing, CVE/NVD, MISP IOCs — but almost entirely absent in the OT domain.

## 4. What I'd Explore Next

1. **SEL RDB file reverse engineering:** Binary structure, TR logic extraction for hashing
2. **IEC 61850 SCL standard:** XML-based substation configuration; versioning in the wild?
3. **MISP integration for OT:** Could a `protection-relay-config-hash` IOC type be created?
4. **Existing OT threat sharing:** Dragos WorldView, Nozomi, Claroty — do any share config hashes?

## 5. Cross-Domain Connections

1. **Entity Resolution:** Config file hashes as entity-resolvable IOCs — Fellegi-Sunter deduplication in a new domain.
2. **Privacy & Cryptography:** Sharing hashes vs raw configs is a ZKP application for config integrity.
3. **Knowledge Graph Construction:** An ontology of relay types, firmware, config hashes, and vulnerabilities.
4. **OSINT & Investigation:** Mandiant kill chain begins with LinkedIn scraping and PDF metadata extraction.
5. **AI Agent Architecture:** Autonomous relay config integrity monitoring as a well-scoped agent use case.
