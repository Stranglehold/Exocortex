# Electric Utility & Critical Infrastructure

**Status**: Active
**Created**: 2026-05-10 (promoted from FIELD report 2026-05-09)
**Domain**: SCADA/ICS, Grid Modernization, Critical Infrastructure Security

---

## SCADA/ICS Threat Landscape

| Threat Actor/Malware | Target | Significance |
|---|---|---|
| ELECTRUM/CHERNOVITE | European energy infrastructure | Russian state-sponsored |
| TRITON/TRISIS | Safety instrumented systems | First malware designed to physically damage ICS systems |
| Dragos 2025 Report | ICS-specific variants | 73% increase in ICS-specific malware variants |
| CISA ICS-CERT | Substation automation systems | 42 active advisories |

## IEC 61850 Protocol Vulnerabilities

- **GOOSE messaging**: Critical for protection relay coordination; lacks encryption by default
- **MMS (Manufacturing Message Specification)**: Application layer for monitoring/control; multiple authentication bypasses documented
- **SCD (Substation Configuration Description)**: XML-based; vulnerable to injection attacks

## Grid Modernization

- **DOE GRIP Program**: $4B+ in grid modernization funding across multiple states
- **DER Integration**: IEEE 1547-2018 standard for distributed energy resources; interconnection challenges scale with adoption

## Key Insight: Asymmetric Vulnerability

Modern smart grids create attack surfaces that scale faster than defensive capabilities. Each IED (Intelligent Electronic Device) connected via IEC 61850 expands the network diameter exponentially.

### Protection Relay Firmware Risk

- SEL-487E and GE Multilin devices run embedded Linux with proprietary protocols
- Configuration files (*.sld, *.cfg) contain full system settings — if exfiltrated, an attacker could reconstruct the entire protection scheme
- GOOSE messaging tension: speed vs. security. Substation protection requires microsecond response times. Adding encryption/authentication adds latency that could cause false trips or delayed fault clearance.

## Exploration Threads

- IEC 62351 (ICS cybersecurity standard) implementation gaps
- Zero-trust architecture for substation networks (NIST IR 8425)
- Hardware security modules (HSMs) for relay firmware signing
- Cyber-physical attack modeling (simultaneous protection scheme failure)

## Cross-Domain Connections

- **SIGINT principles** apply to grid monitoring — signal discrimination matters when distinguishing normal load fluctuations from attack patterns
- **Entity resolution**: correlating events across heterogeneous ICS logs, SCADA historians, and protection relay event records
- **AI Agent Architecture**: autonomous monitoring agents need working memory decay, supervisor loops, selective memorization for grid event correlation

## See Also

- [Intelligence Operations History](intelligence-operations-history.md)
- [Wiki Index](index.md)