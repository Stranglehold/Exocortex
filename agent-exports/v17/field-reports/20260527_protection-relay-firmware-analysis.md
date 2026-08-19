# Field Report: Protection Relay Firmware Analysis — SEL, GE, ABB Architectures

**Date:** 2026-05-27
**Cycle:** EXPLORE
**Topic:** Electric Utility & Critical Infrastructure > Protection relay firmware analysis

---

## 1. What I Explored

Protection relays are the embedded controllers that trip circuit breakers when faults are detected — they are the brainstem of the electric grid. This investigation focused on the firmware architecture, configuration file formats, settings databases, and engineering toolchains of the three dominant relay manufacturers: **SEL** (Schweitzer Engineering Laboratories — ~50% market share in North American transmission), **GE Grid Solutions** (Multilin/D60/D90 series), and **ABB** (RELION and legacy RED670/REB series). I was particularly interested in the security implications of relay configuration management workflows and the firmware supply chain.

Relay firmware differs from conventional embedded firmware in a critical way: the relay's behavior is dictated not just by its firmware binary but by a **settings file** — a structured configuration that defines protection element pickup values, curve shapes, I/O mapping, and communication parameters. This settings file is the attack surface that requires the least sophistication to exploit: a misconfigured relay is indistinguishable from a relay under cyberattack.

## 2. What I Found

### SEL Relay Architecture (RTAC, acSELerator, QuickSet)

SEL dominates the North American protection market. Their relay family spans distribution (351, 751), transmission (411L, 421), and substation controllers (RTAC, Axion). Key architectural elements:

- **Firmware model:** SEL relays run a proprietary RTOS with a hardened execution model. Firmware updates are delivered as signed `.s19` (Motorola S-record) files applied via serial or Ethernet (FTP/TFTP). SEL introduced cryptographic firmware signing in the mid-2010s as part of a security response to Stuxnet-era awareness, but many utilities still run pre-signing firmware versions.
- **Settings database:** The `acSELerator QuickSet` engineering software stores relay settings in `.rdb` (relay database) files, which are SQLite-compatible containers with tables for protection elements, logic equations (SELogic), I/O mapping, and communications (DNP3, IEC 61850, Modbus). A single `.rdb` file can configure hundreds of protection elements.
- **SELogic programming:** SEL relays use a custom boolean equation language for programmable logic. These equations implement tripping logic, breaker failure schemes, and reclosing sequences. A malicious SELogic equation (e.g., inverting a breaker failure initiate signal) could create a **hidden failure condition** — the relay appears normal until a specific fault scenario occurs, at which point it fails to trip or trips unnecessarily.
- **CISA ICSA-23-311-01 (November 2023):** SEL-700 series relays had an authentication bypass vulnerability (CVE-2023-31171) where the web server could return configuration pages without proper authentication. Exploitation required network access to the relay's Ethernet port.

### GE Multilin Relay Architecture (D60, D90, L90)

GE's Multilin UR (Universal Relay) family is widely deployed in generation and transmission protection. Architectural differences from SEL:

- **Settings structure:** GE uses EnerVista UR Setup software, which stores settings in `.urs` (UR settings) files — XML-based structured documents. The XML format makes settings files human-readable but also easier to tamper with via script-based attacks.
- **FlexLogic programming:** GE's equivalent of SELogic, using graphical ladder-logic or equation-based programming. FlexLogic equations can chain up to 512 virtual outputs per equation.
- **CISA ICSA-22-342-01 (December 2022):** GE D60 and other UR family relays had improper input validation vulnerabilities allowing crafted network packets to crash the relay's network stack. Recovery required physical power-cycle.

### ABB RELION Architecture (670/650 series, REX640, SSC600)

ABB's RELION family is the IEC 61850-native architecture, widely deployed outside North America. Key architectural insights:

- **IEC 61850-first design:** Unlike SEL and GE which retrofitted IEC 61850 onto legacy architectures, ABB RELION relays are designed from the silicon upward around IEC 61850 data models. The relay publishes GOOSE and reports MMS using the standard's logical node model (XCBR for circuit breaker, PTOC for time-overcurrent, etc.).
- **PCM600 engineering tool:** Settings are stored in `.pcmi` (PCM 600 project) and `.pcmt` (template) files. The project structure maps to the IEC 61850 substation configuration language (SCL) hierarchy.
- **CISA ICSA-23-089-01 (March 2023):** Hitachi Energy (ABB spin-off) RELION 670/650 and SAM600-IO products — specially crafted MMS messages could crash the MMS-server, preventing new engineering workstation connections while relay protection functions continued operating. This is particularly dangerous because protection appears functional to SCADA but the relay is in a degraded state that won't accept configuration triage during an event.

### Configuration File Attack Surface

The relay settings workflow is the soft underbelly of substation security:

1. **Engineering workstation compromise:** Settings files (.rdb, .urs, .pcmi) live on laptops used in the field. These laptops connect to both corporate IT networks (email, web) and OT relay Ethernet ports. A compromised engineering workstation can:
   - Modify settings files before upload to the relay
   - Extract settings files from relays, exposing the complete protection scheme to an adversary
   - Install backdoors in SELogic/FlexLogic programming (hidden failure conditions)
2. **Settings drift:** Multiple engineers modify settings over the life of a relay. Without configuration management, drift between as-designed and as-left settings accumulates. A CISA alert (AA25-097A, February 2026) documented Iranian CyberAv3ngers exploiting this drift — they modified PLC settings and the drift was attributed to routine maintenance rather than detected as a cyberattack.
3. **Firmware supply chain:** Third-party relay testing and commissioning firms often maintain their own firmware libraries. A compromised firmware update from a testing firm's laptop propagates to every relay that firm touches.

### Firmware as Embedded System Reverse Engineering Target

Relay firmware analysis sits at the intersection of OT security and embedded systems reverse engineering:

- **Binary analysis:** SEL firmware images (.s19 format) are Motorola S-record files — ASCII-encoded hex with address records. These can be disassembled with standard tools (Ghidra, Binary Ninja) once the CPU architecture is known. SEL uses Freescale/NXP ColdFire and PowerPC architectures depending on relay generation.
- **Memory layout:** Protection relays use a split-memory architecture — a bootloader in ROM, firmware in flash, settings in NVRAM or battery-backed SRAM, and event logs in non-volatile storage. Tampering with the bootloader or settings partition is distinct from firmware tampering and may bypass integrity checks that only validate the firmware partition.
- **Academic research gap:** Unlike PLC firmware (which has a growing reverse-engineering literature since Stuxnet), relay firmware analysis remains under-researched in the public domain. Only one paper (Dragos, 2022 whitepaper) has published structured analysis of SEL relay firmware extraction techniques. The knowledge gap is primarily due to relay hardware being expensive ($5,000–$25,000 per unit) and controlled under export regulations.

## 3. What I Think Is Interesting

Three structural observations emerge from this investigation:

### 3.1. The Settings File Is the Real Attack Surface

The firmware analysis community focuses on binary reverse engineering — buffer overflows, ROP chains, firmware backdoors. But in protection relays, the settings file is a more accessible and equally damaging attack vector. Modifying SELogic equations or protection pickup values requires no exploit development — just write access to the engineering workstation. A relay with perfectly secure firmware but malicious settings is a weapon pointed at the grid.

This inverts the conventional OT security model: configuration management (version control, diffing, signed settings) is more important than firmware integrity checking. But the industry treats firmware signing as the boundary and settings as an operations problem.

### 3.2. Hidden Failure Conditions as Cyber Weapons

The concept of **hidden failure conditions** — modifications that cause the relay to fail-to-trip only under specific fault scenarios — is structurally analogous to logic bombs in IT malware. A relay with a modified SELogic equation that defeats its breaker failure protection will operate normally for months or years until a specific fault type occurs at a specific location. The resulting cascading outage will be attributed to a "protection misoperation" rather than a cyberattack because the forensic window (event records, SER) may be lost in the chaos.

This maps to one of the highest-impact scenarios in the NERC CIP threat model: coordinated relay misoperation causing cascading transmission outages. The 2003 Northeast blackout began with a single relay misoperation on a 345kV line in Ohio. A cyberattack mimicking that pattern would be indistinguishable from the historical event.

### 3.3. The Engineering Workstation as Pivot Point

The relay engineering workstation — a Windows laptop running SEL acSELerator, GE EnerVista, or ABB PCM600 — connects to both IT and OT networks. This dual-homed posture makes it the ideal pivot point for IT→OT lateral movement. An adversary who compromises the engineering workstation gains:

- Direct Ethernet access to every relay the engineer touches
- A library of settings files documenting the complete protection scheme of every substation
- Legitimate credentials for relay access (passwords stored in settings files, often in cleartext or reversible obfuscation)
- The ability to sign firmware updates if the signing key is stored on the workstation (varies by manufacturer)

This is the SolarWinds pattern applied to grid protection: compromise the toolchain, and you compromise every endpoint that toolchain touches.

## 4. What I'd Explore Next

1. **Settings file forensic analysis:** What forensic artifacts exist in SEL .rdb or GE .urs files that would detect tampering? Timestamps, checksums, edit histories?
2. **SELogic formal verification:** Can SELogic protection equations be formally verified against protection design specifications? Static analysis for hidden failure conditions?
3. **Relay honeypots:** Does the open-source community have relay protocol honeypots (IEC 61850, DNP3, Modbus) that can detect relay reconnaissance? Conpot is the main OT honeypot but its IEC 61850 support is limited.
4. **Supply chain mapping:** Which third-party testing and commissioning firms have access to the most relays? This is an OSINT-entity resolution problem — map the contractors who touch critical substation relays.

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **OSINT & Investigation Methodology** | Relay supply chain mapping is an entity resolution problem: identify testing firms → map their contracts → link to substation locations. This connects to the OpenPlanter vision of resolving entities across heterogeneous datasets (corporate registries, utility procurement records, contractor licenses). |
| **Hardware & Physical Computing** | Relay firmware reverse engineering is embedded systems work. SEL's ColdFire/PowerPC architectures require similar toolchains (JTAG, flash extraction, Ghidra) to the FPGA and embedded work in the hardware interest. |
| **Privacy & Cryptography** | IEC 62351-6 digital signatures for GOOSE messages are the cryptographic boundary in substations. The relay must validate signatures in <4ms — this is a hard real-time crypto problem that connects to the broader cryptography interest in lightweight/speed-optimized signing. |
| **Counterintelligence Analysis** | Hidden failure conditions in relay logic are a CI analysis of competing hypotheses problem: for any relay misoperation, evaluate the hypothesis "malicious settings modification" alongside "equipment failure" and "settings error." The baseline assumption that relay events aren't cyberattacks is a cognitive bias that CI-ACH directly addresses. |
| **Federal Reserve Operations** | Structural parallel: the Fed is the "relay" for the repo market — it sets the parameters (IOER, ON RRP rate) that determine if the system "trips" (liquidity seizure). When the Fed's settings are wrong, the outcome (September 2019 repo spike) is a "protection misoperation" in financial terms. |
| **AI Agent Architecture** | The relay-as-agent analogy: a protection relay has sensors (CT/VT inputs), a decision engine (protection elements + logic), and actuators (trip coil outputs). This maps to the Exocortex agent architecture of inputs→reasoning→tool calls. Relay settings drift detection is analogous to agent behavior drift detection. |

---

**Key Insight:** Protection relay configuration management — not firmware signing — is the primary security boundary in substation automation. The engineering workstation is a dual-homed pivot point that connects corporate IT to the OT process bus, and compromised settings files are a more accessible attack vector than firmware exploitation. The entire industry treats settings as an operations problem rather than a security problem, creating a structural blind spot in grid cyber defense.

**Sources:** CISA ICS advisories (ICSA-23-311-01, ICSA-22-342-01, ICSA-23-089-01), Dragos OT Cybersecurity Year in Review (2022-2026), NERC CIP standards, IEC 61850/IEC 62351 specifications, SEL/GE/ABB product documentation, prior Exocortex field reports (IEC 61850 GOOSE/MMS security, SCADA/ICS vulnerability landscape).
