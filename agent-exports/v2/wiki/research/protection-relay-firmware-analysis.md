# Protection Relay Firmware Analysis

## Status: STABLE

## Topic Overview
Protection relay firmware analysis at the intersection of operational technology security, power grid reliability, and cybersecurity research. Protection relays are embedded devices that detect electrical faults and trip circuit breakers to isolate damaged equipment. Modern digital relays run proprietary firmware handling IEC 61850 GOOSE/MMS messaging, fault recording, and adaptive protection logic.

## Major Vendor Firmware Architectures

### Schweitzer Engineering Laboratories (SEL)
- Products: SEL-751 (feeder), SEL-787 (transformer), SEL-700G (generator), SEL-700BT (motor bus transfer), SEL-710-5 (motor protection)
- Firmware architecture: ARM-based embedded Linux, proprietary real-time protection kernel
- Update mechanism: firmware hash verification available; SEL publishes Latest Software Versions page
- Security disclosure: Service Bulletins for high-risk, instruction manual Appendix A for others
- CVE-2024-2103: Inclusion of undocumented features vulnerability (CVSS 6.5), privileged access required, affects SEL-700BT, SEL-700G, SEL-710-5, SEL-751, SEL-787-2/-3/-4 — allows unpredictable relay behavior

### GE Vernova (Multilin)
- Products: Multilin 8 Series (845 transformer, G60 generator), Multilin 350 (feeder), UR platform
- Firmware architecture: proprietary RTOS on PowerPC/ARM, EnerVista Launchpad for settings management
- Update mechanism: two-step process (settings file conversion → firmware load via serial/USB/network)
- Settings database: proprietary .set format, managed via UR Setup / Launchpad software

### ABB
- Products: Relion 600 series (REC670 generator, REX640, REC615/615 distribution)
- Firmware architecture: proprietary RTOS, Relion Engineering System (RES) for configuration
- Update mechanism: firmware update releases tied to lifecycle management; ideal at commissioning or periodic testing
- Security advisory: MMS File Transfer vulnerability published for Distribution Automation products

## Known Vulnerability Classes

1. **Undocumented/hidden features** — SEL CVE-2024-2103 (privileged access required)
2. **Cryptographic weakness** — Schneider PowerLogic P5 CVE-2024-5559 (risky crypto algorithm, allows DoS/reboot/full control via front panel)
3. **Protocol-level** — IEC 61850 GOOSE flooding, MMS file transfer abuse, SV/GOOSE masquerade
4. **Authentication bypass** — weak default credentials, insecure serial/USB update paths
5. **Supply chain** — firmware update integrity verification gaps

## IEC 62351 Security Standards

- IEC 62351-3:1: Role-based access control (RBAC)
- IEC 62351-3:2: Secure IP-based communication (TLS/IPsec)
- IEC 62351-3:3: Secure serial communication
- IEC 62351-3:4: Secure application-level exchange
- IEC 62351-4: Security monitoring
- IEC 62351-6: Cryptographic key management
- IEC 62351-3:10 (2024): MACsec for Layer 2 IEC 61850 protocols
- Limited adoption in field due to legacy relay constraints (memory, CPU, interoperability)

## Research Literature

- MDPI Energies 2025: "Cybersecurity Issues in Electrical Protection Relays: A Comprehensive Survey" — systematic review of relay vulnerability classes, IEC 62351 adoption gaps, and modern defense architectures
- CISA ICS Advisory Project: open-source dashboard tracking all CISA ICS advisories including relay vendor vulnerabilities
- Undercode Testing: "OT Cybersecurity: Evolution of Protection Relays" — analysis of relay modernization security debt and Zero Trust transition needs

## Firmware Reverse Engineering State

- SEL provides firmware hash verification tools but not full transparency
- GE Vernova settings files (.set format) are proprietary; limited reverse engineering community
- No public CVE database specifically for relay firmware (vs. generic ICS)
- Research community small: primarily academic papers, Dragos threat intelligence, CISA ICS-CERT
- Hardware access barrier: relays require substation environment or test bench for meaningful analysis

## PQC Migration Readiness

- Most protection relays do not yet implement cryptographic authentication for firmware updates
- IEC 62351-3:2 TLS/TLS-PSK would need PQC algorithm replacement
- SEL/GE/ABB have not published PQC migration roadmaps for relay platforms
- Relay firmware update mechanisms typically use vendor-signed packages (proprietary crypto)

## Cross-Domain Links
- [iec-61850-protection-relay-cybersecurity](iec-61850-protection-relay-cybersecurity.md) — IEC 61850 protocol layer security
- [post-quantum-critical-infrastructure](post-quantum-critical-infrastructure.md) — PQC migration for OT devices
- [ai-driven-der-orchestration](ai-driven-der-orchestration.md) — DER integration with relay coordination
- [autonomous-cyber-operations-ai-red-teaming](autonomous-cyber-operations-ai-red-teaming.md) — OT red teaming methodology
- [grid-edge-software-defined-networking](grid-edge-software-defined-networking.md) — SDN at grid edge
- [ai-predictive-maintenance-critical-infrastructure](ai-predictive-maintenance-critical-infrastructure.md) — relay health monitoring

## Verified Primary Sources (8)
1. SEL Security Notifications — selinc.com/support/security-notifications/
2. SEL CVE-2024-2103 (NVD) — undocumented features in SEL-700BT/700G/710-5/751/787
3. Schneider ICSA-24-331-02 (CISA) — CVE-2024-5559 PowerLogic P5 risky crypto
4. ABB Firmware Update Release — new.abb.com/medium-voltage/protection-relay-services/firmware-update-release
5. GE Vernova Software Tools — gevernova.com/grid-solutions/software-tools (EnerVista Launchpad)
6. MDPI Energies 2025 "Cybersecurity Issues in Electrical Protection Relays" — mdpi.com/1996-1073/18/14/3796
7. IEC 62351 series (2024) — syc-se.iec.ch/deliveries/cybersecurity-guidelines
8. CISA ICS Advisory Project — icsadvisoryproject.com

## Key Insight
Protection relay firmware represents a high-value, low-visibility attack surface: substation automation is increasingly networked (IEC 61850), firmware update mechanisms are proprietary with limited cryptographic transparency, and the research community is small relative to the criticality of the domain. The combination of legacy hardware constraints, slow patching cycles, and physical access requirements creates a unique security posture distinct from IT or general ICS.
