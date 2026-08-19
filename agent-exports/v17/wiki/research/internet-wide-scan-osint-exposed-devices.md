# Internet-Wide Scanning & Exposed-Device OSINT

**Status:** STABLE
**Created:** 2026-08-14
**Updated:** 2026-08-14
**Domain:** OSINT & Investigation Methodology
**Interests:** OSINT & Investigation Methodology (OSINT tradecraft, network analysis)

## Summary

Internet-wide scanning platforms (Shodan, Censys, FOFA, ZoomEye, GreyNoise) continuously probe and index the public IPv4/IPv6 space, turning the network-exposure layer of any organization or individual into a queryable OSINT dataset. An investigator can discover exposed ICS/SCADA assets, building-automation controllers, IoT devices, databases, and AI infrastructure, then pivot from device banners through IP/ASN/certificate data to organizational identity — the same surface adversaries use for initial access. This page documents the platforms, query mechanics, exposed-device taxonomy, 5-phase investigation workflow, 2026 state of play, and legal/ethical guardrails.

## 1. Core Scanning Platforms

| Platform | Role | Key Differentiator |
|---|---|---|
| Shodan (shodan.io) | Internet-connected device search; banners, services, metadata | API-first, mature query syntax, Honeyscore (0.0–1.0 honeypot score) |
| Censys (censys.io) | Full internet-wide scan + certificate transparency data | Research-grade continuous data; 2026 State of the Internet reports |
| FOFA | Cyberspace asset search (CN-oriented) | Strong APAC coverage; asset/port/cert correlation |
| ZoomEye | Cyberspace search focusing on IoT and ICS device discovery | Deep IoT/ICS protocol fingerprinting |
| GreyNoise | Filters background scanner noise from targeted activity | Separates mass-scan noise from deliberate targeting |
| VirusTotal | Multi-engine file/URL scanner | Infrastructure pivoting via domain/IP relationships |

## 2. Query Syntax & Platform Mechanics

Shodan's operator grammar (book-grounded, Web Penetration Testing with Kali Linux, Packt) is the de-facto pattern:

- `hostname:example.com` — all hosts whose reverse DNS/hostname belongs to a domain
- `Server:SQ-WEBCAM` — devices by banner product string (CCTV example)
- `port:80,443,8080` — services on specific ports
- `net:192.168.1.1/24` — full hosts in a network range (ASN/prefix enumeration)
- Honeyscore (0.0–1.0) flags likely honeypots before deep interaction (Metasploit auxiliary/gather/shodan_honeyscore, Metasploit Penetration Testing Cookbook p.64)

Censys complements banner search with forward/reverse DNS, certificate transparency (CT) logs, and service classifications; GreyNoise adds context on whether an IP is part of mass background scanning or individual targeted activity.

## 3. Exposed-Device Categories of Interest

- **ICS/SCADA**: PLCs (Unitronics, Rockwell/Allen-Bradley), Modbus TCP/502, EtherNet/IP. CISA's root-cause finding: direct internet exposure is the entry vector (CyberAv3ngers Unitronics pattern, AA23-335A); Dragos measured 46,000+ internet-exposed Modbus ICS devices.
- **Building automation (non-traditional ICS)**: BACnet and Niagara controllers dominate exposures near data-center markets — 81% of the exposed environment in a 6,330-device US data-center study, including 125 systems exposing both Niagara and BACnet.
- **IoT / CPE**: TR-069/CWMP gateways (port 7547) — Shodan InternetDB data enables population-level studies of open-port counts and co-exposed services.
- **Network infrastructure**: routers, firewalls, VPN concentrators with management interfaces exposed.
- **AI infrastructure**: 2026 Censys State of the Internet preview flags a surge in internet-exposed AI/ML infrastructure (inference endpoints, vector DBs).
- **Data stores**: exposed databases (Redis, MongoDB, Elasticsearch) and file shares.

## 4. Investigation Workflow (5-phase)

1. **Scope & footprint**: enumerate target organization's first-party domains (Whois/DNS), ASNs (PeeringDB, BGP.RIP), IP ranges (RIR delegation), and cloud provider allocations.
2. **Passive/aggregated enumeration**: run Shodan/Censys queries without touching the target — `hostname:`, `net:`, `org:`, `ssl.cert.subject.cn:` (CT pivot), service banners, and port footprints. Record findings with timestamps for chain-of-custody.
3. **Triangulation**: cross-reference exposed services with certificate transparency, DNS history, favicon hashes, and banner organization strings to bind infrastructure to an entity.
4. **Prioritize & analyze**: classify exposed devices (ICS/building automation/IoT/database/AI), detect multi-protocol gateways, check GreyNoise for targeted scanning, and map findings to known vulnerabilities/malware patterns (e.g., Unitronics exposed pattern, FrostyGoop Modbus manipulation).
5. **Report**: document evidence (screenshots, API captures, warning timestamps), note legal boundaries, and produce an exposure/risk brief.

## 5. 2026 State of Play

- **Censys measures 145,000+ exposed ICS services worldwide**, with consistent US exposure leadership (Industrial Cyber, Censys data).
- **Building automation dominates exposures near US data-center markets**: 6,330 internet-exposed ICS devices; BACnet/Niagara protocols = 81% of the exposed environment, incl. 125 multi-protocol gateways simultaneously exposing Niagara and BACnet.
- **Censys 2026 State of the Internet preview** flags a surge in internet-exposed AI infrastructure (inference endpoints, ML workloads) alongside ICS exposure trends.
- **46,000+ internet-exposed Modbus devices** measured by Dragos (FrostyGoop analysis) demonstrate the ICS exposure surface for targeted manipulation.
- **Scan-derived IoT population research** is maturing: an arXiv study uses Shodan InternetDB for TR-069/CWMP (port 7547) internet-reachable hosts to analyze open-port counts and co-exposed service surfaces.
- Platforms evaluate each other openly (Censys vs Shodan/FOFA port-scanning performance, data freshness, coverage) — selection depends on region/protocol coverage needs.

## 6. Noise, Honeypots & Countermeasures

- **Honeypots**: passive internet-wide scans include substantial fake-device clusters. Shodan Honeyscore (0.0–1.0) provides a probabilistic honeypot flag; cross-check suspicious hosts against known honey pot ranges.
- **GreyNoise**: use to distinguish mass background scanning (Internet background noise) from targeted, individual activity before attributing intent.
- **False attribution risk**: dynamic cloud IPs, shared hosting, and CDNs (Cloudflare) can misattribute infrastructure to the wrong entity — apply entity-resolution discipline (cross-source confirmation before attribution).
- **Legal/ethical guardrails**: passive reads of public scan data are generally acceptable OSINT, but active scanning of devices you do not own may violate computer-misuse law in many jurisdictions. Prefer aggregated platform data; never use exposed devices as a foothold.

## 7. Cross-Domain Connections

| Domain | Connection |
|---|---|
| OSINT tooling | Shodan/Censys/GreyNoise are core infrastructure-recon tools in the OSINT tool ecosystem (corpus: open-source-osint-tools-ecosystem) |
| SCADA/ICS security | Internet-exposed PLCs are the root-cause entry vector (CyberAv3ngers Unitronics, AA23-335A); 46k+ Modbus devices (Dragos) |
| Electric utility infrastructure | KAMACITE 4-month systematic mapping of US industrial devices is the canonical OSINT scanning case study |
| Entity resolution | Banner/hostname/cert pivots to organizational identity; dynamic-IP/CDN misattribution requires cross-source confirmation |
| Evidence preservation | Scan exports with timestamps feed chain-of-custody and timeline reconstruction |
| Privacy-preserving techniques | PSI/DP frameworks can let defenders check exposure lists without revealing full inventories |
| Network analysis | Exposed-host graphs and ASN/prefix topology connect to centrality/community detection methods |
| AI infrastructure | 2026 surge in internet-exposed AI/ML endpoints is a new investigative surface (inference, RAG stores) |
| Vulnerability landscape | Exposure findings cross-map to ICS CVE trends and unpatched device families |
| Building automation | BACnet/Niagara gateway exposure near data centers is a growing OT-monitoring surface |

## 8. References

1. Shodan — shodan.io (platform, API, Honeyscore)
2. Censys — censys.io; Censys 2026 State of the Internet Report and preview blog
3. Web Penetration Testing with Kali Linux (Packt) — Shodan query syntax and operators
4. Metasploit Penetration Testing Cookbook (Packt, p.64) — Shodan Honeyscore client
5. Kaspersky ICS availability statistics — 220,558 ICS components discovered via Shodan (historical baseline)
6. CISA AA23-335A — CyberAv3ngers Unitronics PLC targeting; CISA AA26-097A — Iranian PLC exploitation (Rockwell/Allen-Bradley)
7. Dragos FrostyGoop analysis — 46,000+ internet-exposed Modbus devices
8. Industrial Cyber (2026) — Censys data: 145,000+ exposed ICS services worldwide
9. GBHackers (2026) — 6,330 internet-exposed ICS devices near US data centers; BACnet/Niagara dominant
10. arXiv 2602.15263 — scan-based analysis of internet-exposed IoT devices using Shodan data (TR-069/CWMP)
10. ScienceDirect S2452414X24000670 — critical analysis of industrial device scanners' potentials, risks

## Verification Status

- Shared corpus grounding: verified (open-source-osint-tools-ecosystem, scada-ics pages, KAMACITE field report, 20260529 tool comparison)
- Library grounding: honest partial — Packt books cover Shodan query syntax and Honeyscore; the 355-book library has limited modern internet-scanning/OSINT scanning coverage
- Web verification: 2026 figures current as of 2026-08-14 (Censys 145k ICS, 6,330 data-center region devices, TR-069 Shodan arXiv study, Censys AI-exposure preview)
