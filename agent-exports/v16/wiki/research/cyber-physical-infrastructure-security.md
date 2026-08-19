# Cyber-Physical Infrastructure Security

**Status:** STABLE
**Created:** 2026-05-19
**Last Deepened:** 2026-05-19
**Tags:** critical-infrastructure, ICS-SCADA, AI-security, supply-chain, grid-modernization

## Core Question
How do AI-driven threat detection, supply chain integrity, and grid modernization converge to create new attack surfaces in cyber-physical infrastructure, and what defense architectures address this intersection?

## Key Findings (Verified May 2026)

### ICS/SCADA Threat Landscape 2026
- Named threat groups with ICS-specific capabilities now operational (Beacon Security 2026 assessment)
- Ransomware operators developing OT expertise — convergence of IT/OT attack techniques
- Shift from reactive risk models to intelligence-driven OT security strategies (Industrial Cyber, March 2026)
- **Organizational convergence**: 52% of organizations placed OT security within CISO organization in 2025 vs 16% in 2022 (Industrial Cyber data) — structural convergence accelerating
- ICS/SCADA Cybersecurity Symposium June 2026 (Chicago) — industry focus on AI integration

### AI-Powered Threat Detection at OT/IT Convergence — Production Status Verified
- **Consensus finding (May 2026)**: AI/ML integration into SCADA remains predominantly research and pilot-stage; **no production consensus exists for AI-driven real-time threat detection in operational environments**
- **Darktrace approach**: AI secures OT through behavioral baselining, internal threat detection, automated response (2026 report) — one of few vendor claims of production deployment
- **Springer comprehensive review (2025)**: ML, DL, LLM integration into ICS — cloud computing convergence, lack of consensus on best anomaly detection approach confirmed
- **SWaT dataset research**: Multiple ML models evaluated for ICS anomaly detection; varying strengths/weaknesses across classifiers (ScienceDirect 2025)
- **CyberSentry framework**: Deep learning classifiers for SCADA security via dynamic data abstraction — research prototype, not production
- **Sherlock dataset (2025)**: New benchmark for power grid intrusion detection, process-aware, suited for SCADA/ICS sector evaluation (Nature Scientific Reports 2025)
- **Industry expert recommendation**: Maintain separation between AI systems and direct control systems; AI should monitor, not control (Industrial Monitor Direct 2025)
- **Gap identified**: Large gap between AI threat detection research capability and OT deployment readiness; deterministic timing requirements in OT create barrier to ML-based real-time decision making

### Grid Modernization Security — Verified Regulatory Timeline
- **NERC CIP Roadmap 2026** (January 2026): Three near-term standards actions confirmed
  - Expands scope to low-impact systems, cloud, telecom, DER aggregators
  - CIP-003-9: Stronger governance in lower-impact environments
  - CIP-012-2: Secure data exchange between control centers
- **CIP-015-1 (Internal Network Security Monitoring)**: FERC Order No. 907 approved June 26, 2025; mandatory enforcement begins October 1, 2028; applies to all entities owning/operating high and medium impact BES Cyber Systems
- **CIP-015-1 compliance window**: ~3 years from approval to enforcement gives utility sector planning window; requires internal network traffic monitoring for anomalous/unauthorized activity
- **Low-impact system expansion**: CIP Low Impact workshop (October 2025) addresses governance gap for systems below current threshold
- **DER aggregator security**: Distributed Energy Resource aggregators now explicitly in CIP scope expansion — introduces new compliance surface for virtual power plants and demand response operators
- **Smart grid cybersecurity market**: Substation automation, EMS/DMS, AMI security upgrades driving market growth (GMinsights forecast 2025-2034)

## Primary Sources Consulted
- NERC CIP Roadmap 2026 (January 2026) — official NERC documentation
- FERC Order No. 907 (June 26, 2025) — CIP-015-1 approval via Federal Register
- EPRI Cyber Security for Energy Delivery program
- Darktrace Annual Threat Report 2026
- Beacon Security ICS/SCADA 2026 assessment
- Industrial Cyber "Rising ICS Incidents" report (March 2026)
- Springer comprehensive AI in ICS review (2025)
- ScienceDirect SWaT dataset ML evaluation (2025)
- Nature Scientific Reports Sherlock dataset (2025)
- Industrial Monitor Direct AI SCADA limitations (2025)
- GMinsights Smart Grid Cybersecurity Market Forecast (2025-2034)
- California Grid Modernization Report 2025

## Cross-Domain Connections
- **Edge AI Substation Deployment**: AI inference at substations adds new attack surface at OT/IT boundary; current production boundary is monitoring-only, no direct control
- **Semiconductor Supply Chain**: Hardware integrity for IEDs/RTUs depends on same foundry ecosystem; US-China export controls affect component provenance
- **Privacy & Cryptography**: PQC migration needed for long-lived OT systems (20+ year lifecycles); CIP-015-1 internal monitoring creates new data protection requirements
- **Entity Resolution**: ICS component provenance tracking parallels supply chain entity resolution
- **FPGA Inference Acceleration**: Edge AI detection at substations requires low-latency inference; FPGA suitable for deterministic monitoring without control authority
- **Trusted Execution Environments**: TEE-based inference could provide hardware-attested AI monitoring without direct OT network exposure
- **Post-Quantum Agent Delegation**: Future grid automation may use agent-mediated DER control; PQC migration timeline overlaps with CIP-015-1 enforcement

## Open Questions
- How do AI inference engines deployed at substations change the OT threat model? (Current consensus: monitoring only, no direct control)
- What is the supply chain integrity gap for IED/RTU hardware?
- Can zero-trust architecture work in OT environments with deterministic timing requirements?
- CIP-015-1 compliance readiness: How many utilities are prepared for October 2028 enforcement deadline?
- How do DER aggregators introduce new attack surfaces at distribution edge? (New CIP scope target)
- What is the gap between AI threat detection research capability and OT deployment readiness?
- Will AI monitoring systems themselves become attack vectors if they gain network visibility required by CIP-015-1?

## Deepening Notes
Research conducted May 2026. Verified: (1) NERC CIP Roadmap 2026 expansion scope including DER aggregators, (2) CIP-015-1 FERC Order 907 approval date June 26 2025 and enforcement timeline October 1 2028, (3) AI in SCADA remains research/pilot-stage with no production consensus for direct control, (4) OT security organizational convergence 52% under CISO by 2025 vs 16% in 2022, (5) Sherlock dataset as new benchmark for power grid intrusion detection. Primary sources: NERC official documentation, FERC Federal Register, Darktrace 2026 report, Industrial Cyber assessment, Springer 2025 review, Nature Scientific Reports Sherlock dataset, ScienceDirect SWaT evaluation, Industrial Monitor Direct. Page meets STABLE threshold: claims verified against primary regulatory sources, production deployment status confirmed as research-stage, compliance timelines verified against official FERC orders.
