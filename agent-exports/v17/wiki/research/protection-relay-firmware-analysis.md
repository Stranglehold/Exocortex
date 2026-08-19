# Protection Relay Firmware Analysis

**Status: STABLE**  
**Lines: 172**

## Summary

Protection relays are the computational core of substation automation — the devices that detect faults and trip breakers in milliseconds. This page catalogs firmware architectures, configuration file formats, supply-chain security implications, and the emerging threat landscape for relay logic manipulation across four major vendors: SEL, GE Vernova, ABB, and Siemens.

---

## 1. Why Protection Relay Firmware Matters

Protection relays execute protective algorithms (overcurrent, distance, differential) and isolate equipment during fault conditions. Unlike IT systems, relay firmware is rarely updated post-installation — many in-service relays run firmware from 2010-2015 with known CVEs. This creates an **asymmetric vulnerability**: attackers with access to configuration files can reconstruct entire protection schemes.

Key architectural reality: modern digital relays are embedded Linux devices (SEL-487E, GE Multilin, ABB Relion) running proprietary protocols over standard Ethernet. The IEC 61850 standard — GOOSE messaging for trip signals, Sampled Values for process bus, MMS for monitoring — creates an attack surface exponentially greater than legacy hardwired relays.

---

## 2. Vendor Architectures

### Schweitzer Engineering Laboratories (SEL)

SEL relays dominate North American transmission and distribution substations.

| Component | Details |
|-----------|---------|
| **RTOS** | Proprietary hardened real-time operating system |
| **Firmware format** | Cryptographically signed `.s19` (Motorola S-record) files |
| **Delivery mechanism** | Serial (RS-232/485) or Ethernet (FTP/TFTP) |
| **Signing** | Digital signatures introduced mid-2010s; many utilities still run pre-signing firmware |
| **Settings storage** | `.rdb` (relay database) — SQLite-compatible containers holding protection elements, SELogic equations, I/O mapping, comms parameters |
| **Hardware** | Freescale/NXP ColdFire and PowerPC architectures |
| **Memory layout** | Bootloader (ROM) → Firmware (flash) → Settings (NVRAM/battery-backed SRAM) → Event logs (non-volatile) |
| **Attack surface** | Bootloader or settings partition tampering may bypass firmware-only integrity checks |
| **Security disclosure** | Service Bulletins for high-risk; Appendix A revisions for others |

### GE Vernova (formerly GE Grid Solutions)

GE's Universal Relay (UR) family is widely deployed in generation and industrial settings.

| Component | Details |
|-----------|---------|
| **Platform** | UR family: F35, T35, D60, L90, etc. |
| **Configuration** | EnerVista software — proprietary Windows-based relay management |
| **Settings format** | `.urs` (UR settings) files — XML-based, containing full protection scheme |
| **Firmware update** | `.bin` files via EnerVista; multiple CVEs in bootloader update mechanism |
| **Security bulletin** | GES-2025-05 (Jan 2025) — UR relay applications vulnerability advisory |
| **Analysis tools** | COMTRADE viewer for event records, oscillography, postmortem analysis |
| **Known issues** | Firmware verification relies on EnerVista integrity checks; limited third-party audit capability |

### ABB

ABB's Relion series (615, 620, 630) and legacy RED/REF relays span transmission and distribution.

| Component | Details |
|-----------|---------|
| **Platform** | Relion 615/620/630 series; AC500 PLCs for bay-level control |
| **Firmware** | Firmware update packages via ABB's Software Update Tool |
| **Recent advisory** | CISA ICSA-26-132-03 (May 2026) — AC500 V3 multiple vulnerabilities |
| **MMS vulnerability** | CISA ICSA-23-089-01 — RELION MMS file transfer vulnerability |
| **Security model** | Cyber Security Advisories via ABB library portal; firmware signing via manufacturer |
| **Concern** | IEC 61850 MMS stack implementation vulnerabilities persist across product lines |

### Siemens

Siemens Siprotec 5 and Reyrolle protection relays cover global markets.

| Component | Details |
|-----------|---------|
| **Platform** | Siprotec 5 (high-end), Siprotec Compact, Reyrolle |
| **Configuration** | DIGSI 5 engineering tool — proprietary `.dxp` project files |
| **Firmware** | Signed firmware packages; multiple ICS-CERT advisories for Siprotec |
| **Protocol support** | IEC 61850 (GOOSE, MMS, SV), DNP3, IEC 60870-5-103, Modbus |
| **Research** | Systematic review by MDPI (Energies, 2025) identifies cybersecurity gaps in digital relays |

---

## 3. Configuration File Formats & Supply Chain Risk

Protection relay configuration files are the **crown jewels** of substation security:

| Format | Vendor | Contents | Risk |
|--------|--------|----------|------|
| `.rdb` | SEL | SQLite DB: protection elements, SELogic, I/O map, comms | Settings exfiltration = complete protection scheme reconstruction |
| `.urs` | GE | XML settings file: all protection and control parameters | Engineering workstation compromise → settings tampering |
| `.dxp` | Siemens | DIGSI 5 project file: full substation configuration | Project file sharing across contractors → uncontrolled distribution |
| `SCD/CID/IID` | All (IEC 61850-6) | Substation Configuration Description defines relay topology | SCD file access exposes entire substation IED inventory |

**Supply chain attack vector**: Configuration files are routinely shared between utilities, engineering firms, and commissioning teams over unencrypted email. A single compromised engineering laptop provides the attacker with complete protection scheme knowledge.

**Firmware distribution attack surface** (methodology transferable from ASIC miner research, arXiv:2605.03770): publicly distributed firmware artifacts enable offline reconstruction of internal architecture and identification of security weaknesses without device access.

---

## 4. Firmware Reverse Engineering State

| Aspect | Status |
|--------|--------|
| **SEL firmware transparency** | Hash verification tools provided; no full transparency |
| **GE .urs format** | Proprietary; limited reverse-engineering community |
| **Relay-specific CVE database** | None exists — generic ICS CVEs only |
| **Research community** | Small: primarily academic papers, Dragos/Mandiant threat intelligence, CISA ICS-CERT |
| **Hardware access barrier** | Relays require substation environment or test bench for meaningful analysis |
| **Emerging methodology** | Pouliquen et al. (2025) firmware distribution static analysis (arXiv:2605.03770) — methodology transferable to relay firmware |

---

## 5. Threat Landscape

### Known Attack Vectors

1. **Firmware tampering**: Pre-signing SEL firmware (pre-2015) vulnerable to bootloader manipulation
2. **Settings exfiltration**: Engineering workstation compromise → relay configuration theft → complete protection scheme knowledge
3. **GOOSE message injection**: IEC 61850-8-1 GOOSE spoofing enables false trip signals (INDUSTROYER/INCONTROLLER precedent)
4. **MMS exploitation**: ABB RELION CVE via MMS file transfer; widespread MMS protocol vulnerabilities
5. **Supply chain**: Configuration file distribution across contractors; pre-installation firmware compromise
6. **Post-installation neglect**: Firmware never updated — decade-old CVEs persist in production

### Threat Actor Precedent

| Actor | Target | Capability |
|-------|--------|-----------|
| **INDUSTROYER/INCONTROLLER** | Ukrainian substations (2016) | IEC 61850 GOOSE manipulation for breaker trips |
| **CHERNOVITE/PIPEDREAM** | ICS/OT globally (2022) | Modular ICS attack framework targeting multiple relay protocols |
| **Sandworm** | Ukrainian grid | BlackEnergy3 → KillDisk → substation isolation |

---

## 6. Defensive Measures & Research

| Measure | Description |
|---------|-------------|
| **Firmware version control** | Manual updates only; NERC CIP requires tested, authorized changes |
| **Cryptographic signing** | Post-2015 SEL firmware; vendor-agnostic signing standards still emerging |
| **GOOSE security** | IEC 62351-6 authentication for GOOSE/SV — adoption limited by latency requirements |
| **Anomaly detection** | Lozano-Paredes et al. (2026, arXiv:2601.09287) — explainable autoencoder-based detection in GOOSE networks |
| **Firmware distribution hardening** | Pouliquen et al. methodology (arXiv:2605.03770) for pre-deployment firmware integrity verification |
| **NERC CIP standards** | CIP-005 (electronic security perimeter), CIP-007 (systems security), CIP-010 (configuration change management) |

---

## 7. Cross-Domain Connections

1. **SCADA/ICS Security** — Protection relays are the endpoint devices that SCADA systems monitor and control; IEC 61850 is the protocol bridge. → [[scada-ics-security]]
2. **IEC 61850 Standard Evolution** — GOOSE messaging security, MMS vulnerabilities, substation automation architecture. → [[iec-61850-standard-evolution]]
3. **Electric Utility Critical Infrastructure** — Relay firmware security is a core component of grid resilience. → [[electric-utility-critical-infrastructure]]
4. **Hardware & Physical Computing** — Relay firmware reverse engineering is an embedded systems problem directly adjacent to FPGA and PCB work. → [[fpga-inference-acceleration]], [[custom-pcb-sensor-networks]]
5. **HUMINT/OSINT Tradecraft** — Substation asset identification via public records is prerequisite for targeted relay exploitation. → [[humint-tradecraft-osint]]
6. **Entity Resolution** — Mapping substation assets to owner/operator entities shares methodology with data aggregation. → [[data-aggregation-entity-resolution]]
7. **Post-Quantum Cryptography** — IEC 62351 cryptographic migration for constrained OT devices. → [[post-quantum-cryptography-critical-infrastructure]]
8. **Supply Chain Analysis** — Relay firmware and config file distribution chains are vulnerable to interdiction. → [[supply-chain-network-analysis-osint]]
9. **Counterintelligence** — Relay logic manipulation as deception; adversary could induce false trips for strategic effect. → [[counterintelligence-analysis-frameworks]]

---

## 8. References

1. Mandiant/Google Cloud — "Protecting the Core: Securing Protection Relays in Modern Substations" (June 2025)
2. CISA ICSA-26-132-03 — ABB AC500 V3 Multiple Vulnerabilities (May 12, 2026)
3. CISA ICSA-23-089-01 — ABB RELION MMS Vulnerability
4. GE Vernova — GES-2025-05 Security Advisory (January 2025)
5. Lozano-Paredes et al. — "Explainable Autoencoder-Based Anomaly Detection in IEC 61850 GOOSE Networks," arXiv:2601.09287 (2026)
6. Pouliquen et al. — "Firmware Distribution as Attack Surface: A Security Study of ASIC Cryptocurrency Miners," arXiv:2605.03770 (2025) — methodology transferable to relay firmware
7. MDPI Energies — "Cybersecurity Issues in Electrical Protection Relays: A Systematic Review" (2025)
8. NERC CIP Standards — CIP-005, CIP-007, CIP-010
9. IEC 61850 / IEC 62351 Standards
10. INDUSTROYER / INCONTROLLER threat actor reports — ESET, Dragos (2016-2022)
11. Exocortex field report: protection-relay-firmware-analysis (2026-05-27)
12. Exocortex field report: protection-relay-config-file-supply-chain (2026-05-29)
13. SEL Security Notifications — https://selinc.com/support/security-notifications/
14. ABB Cyber Security Alerts — https://www.abb.com/global/en/company/about/cybersecurity/alerts-and-notifications
