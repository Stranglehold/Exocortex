# IPv6 Reconnaissance for OSINT Investigation

Status: STABLE | Deepened: 2026-08-07 | Domain: OSINT & Investigation Methodology

## 1. Overview

IPv6 reconnaissance is the systematic collection and correlation of IPv6 address space, allocation metadata, and host behavior to attribute entities, map infrastructure, and pivot into further investigation. The shift to IPv6 changes the OSINT evidence surface fundamentally: address space is ~2^128 vs 2^32, allocation is hierarchical and registrable at prefix level, and per-subscriber identity behavior differs sharply from IPv4 (stable EUI-64 identifiers vs rotating temporary addresses vs CGNAT behind unique IPv6).

As of 2026 IPv6 traffic exceeds 60% globally, yet IPv6 geolocation databases remain substantially sparser than IPv4 and most investigative tooling remains IPv4-centric. This is the documented IPv6 evidence gap. A serious OSINT pipeline needs an IPv6 roadmap including dual-stack measurement infrastructure.

## 2. IPv6 Addressing Model for Investigators

- **Address format:** 8 hextets of 16 bits, e.g. `2001:db8:85a3::8a2e:370:7334`; compressed rules (leading zeros, single `::`).
- **Address classes relevant to OSINT:**
  - Global unicast `2000::/3` — routable, registrable, attribution-relevant.
  - Unique local `fc00::/7` — non-routable site-local (like RFC 1918), useful as an indicator of internal-only services.
  - Link-local `fe80::/10` — never routed; appears in neighbor-discovery and local scan data, can fingerprint devices.
  - Multicast `ff00::/8` — protocol traffic, probing/sniffing signal.
  - IPv4-mapped `::ffff:a.b.c.d` — reveals dual-stack service binding; a single service exposed on both stacks is a correlation pivot.
- **Interface identifiers:** classic SLAAC used modified EUI-64 (RFC 4291), embedding the MAC address — a direct hardware-fingerprint leak. Modern systems use privacy extensions / temporary addresses (RFC 4941, RFC 8981) that rotate, defeating naive device tracking but leaving temporal correlation challenges.
- **Address assignment modes:** SLAAC (RFC 4862), DHCPv6, static. Assignment mode indicators (e.g., stable prefix + rotating IID) help infer network management and user-enumeration feasibility.

## 3. Identity, Correlation & Entity Resolution

- **Stable vs temporary IIDs:** A stable interface identifier is a persistent device fingerprint; temporary addresses rotate every ~24h but are allocated from the same /64, so prefix correlation still binds a device to a household/network.
- **CGNAT bypass (key OSINT win):** with dual-stack, subscribers often get a unique IPv6 address even while IPv4 is carrier-grade NAT-shared. If the target service supports IPv6, one target = one address, removing the IPv4 multi-tenant ambiguity that breaks attribution.
- **Dual-stack pivoting:** correlate A/AAAA records (dns-whois-investigation-osint) to link domains; CDNs and shared hosts reuse both stacks and can be used to cluster unrelated domains behind the same origin.
- **Prefix-level attribution:** allocation is hierarchical (RIR → LIR/ISP → customer), so a /32 allocation can span an entire ISP across countries; a /48 or /64 is usually a more precise entity boundary.
- **Entity resolution bridge:** IPv6 IID stability/semantics (e.g., `518f` embedding, low 24-bit MAC remnants, random IIDs) can corroborate or refute hypotheses from phone-number, email, and corporate-registry OSINT.

## 4. Discovery & Reconnaissance Techniques

Brute-force scanning of the full v6 space is infeasible (2^64 per /64, 2^128 total), so discovery is intelligence-driven:

1. **DNS enumeration:** query AAAA records; brute-force subdomains; passive DNS (SecurityTrails, VirusTotal, CIRCL) for historical IPv6 bindings.
2. **Certificate transparency:** crt.sh logs — find certs mentioning IPv6 addresses (SAN/IP entries), scripted via CT APIs.
3. **IPv6-capable index services:** Shodan and Censys maintain IPv6 indexes; search by port, service banner, or ASN. This is the single most productive gap-filling step vs IPv4 workflows.
4. **Prefix / allocation discovery:** RIR whois (ARIN, RIPE NCC, APNIC, LACNIC, AFRINIC) for registered prefixes; bgp.he.net and RIPE RIS/RouteViews for routing visibility; RIPE Atlas for probe-derived reachability.
5. **Neighbor discovery / local probing:** on constrained segments, NDP (`ndp`, `ping6 ff02::1`, `alive6`) finds hosts in a /64 that DNS never reveals.
6. **Dict/pattern-assisted scanning:** address dictionaries for well-known patterns (e.g., `::1`, `::2`, EUI-64-derived, low-byte increments) and IPv6-aware port scanners (Nmap, masscan with IPv6 support, THC-IPv6 tools) on targeted subnets.
7. **Reverse DNS / PTR:** 6tree and reverse DNS for IPv6 (ip6.arpa) expose hostnames tied to addresses without active scanning.
8. **Search-engine pivots:** indexed IPv6 literals in public text, logs, or documentation (e.g., `2001:db8:` in paste sites, GitHub, config dumps).

## 5. OSINT Data Sources & Tooling

| Layer | Sources / tools | Purpose |
|---|---|---|
| Allocation | ARIN/RIPE/APNIC/LACNIC/AFRINIC whois, bgp.he.net, RIPE RIS | prefix → organization attribution |
| Index | Shodan, Censys | host/service discovery on IPv6 |
| DNS | passive DNS, crt.sh, dnsrecon, fierce | AAAA → domain/entity linkage |
| Active | Nmap (IPv6), masscan, THC-IPv6, SI6 Networks ipv6toolkit, scapy | targeted host and behavior probing |
| Measurement | RIPE Atlas, IPv6-only test services | reachability, latency, geolocation triangulation |
| Local | ip6tables logs, NDP captures, Wireshark | internal/incident evidence |

## 6. Geolocation & Attribution Limits

- Database coverage: MaxMind and IPinfo offer IPv6 geolocation but at significantly lower granularity — country-level for many prefixes.
- Prefix-scale problem: a single /32 can span an ISP across countries; geometric precision drops sharply vs IPv4.
- Active measurement gap: few latency-based techniques validated at IPv6 scale; mobile IPv6 geolocation error patterns are largely unmeasured (cf. IPv4 finding of 10× higher mobile error from arXiv:2605.21937).
- RIR registration quality varies; some LIRs register only coarse country info. Treat geolocation DB output for IPv6 as hypothesis, not fact.

## 7. Evasion & Adversarial Use

- **Tunnels:** 6to4, Teredo, ISATAP, 6in4, DS-Lite and NAT64/DNS64 gateways allow adversaries to hide v4 endpoints behind v6 transport — investigators must track tunnel broker and gateway registrations.
- **Firewall policy gaps:** orgs often lack IPv6 egress/ingress rules, exposing IPv6-only services that mirror IPv4 services with weaker controls.
- **Covert C2:** malware increasingly uses IPv6 for C2 since most detection tooling filters only IPv4; examine NTP/ICMPv6/NDP as covert channels.
- **Identity obfuscation:** randomized IIDs (RFC 8981) plus prefix rotation defeat naive correlation; pair with behavioral analytics for resolution.

## 8. Legal & Ethical Notes

Passive OSINT (DNS, cert logs, whois, pDNS, index services) is generally low-risk and preferred. Active IPv6 scanning, NDP probing, or targeted port scans require authorization and rate discipline; validate jurisdiction (CFAA and analogues, local computer-misuse law). Preserve evidence per evidence-preservation-chain-of-custody-osint.

## 9. Cross-Domain Connections

1. [[ip-address-geolocation]] — the core documented IPv6 coverage gap this page addresses.
2. [[dns-whois-investigation-osint]] — AAAA/PTR and registrar pivots.
3. [[network-analysis-techniques-osint]] — subnet/host graph and prefix topology analysis.
4. [[entity-resolution-agent-safety]] — stable IID as entity binding signal and its failure modes.
5. [[privacy-preserving-entity-resolution-osint]] — IP-based linkage under privacy constraints.
6. [[autonomous-osint-agent-opsec-attribution-risk]] — v6 probing attribution risk for agent infrastructure.
7. [[ip-geolocation-network-attribution]] — dual-stack attribution logic.
8. [[browser-forensics-web-artifacts-osint]] — v6 addresses in browser/network artifacts.
9. [[software-defined-radio-osint]] — RF + network fingerprint fusion for device identification.
10. [[legal-ethical-osint]] — active scanning authorization boundaries.

## 10. References

1. RFC 4291 — IP Version 6 Addressing Architecture.
2. RFC 4862 — IPv6 Stateless Address Autoconfiguration.
3. RFC 4941 / RFC 8981 — Privacy Extensions and Temporary Addresses.
4. wiki/research/ip-address-geolocation.md — IPv6 coverage gap section.
5. wiki/research/ip-geolocation-network-attribution.md — IPv6 bypass of CGNAT.
6. wiki/research/dns-whois-investigation-osint.md — A/AAAA correlation.
7. field-reports/20260528_ip-address-geolocation-techniques.md — IPv6 evidence-gap analysis.
8. Shodan IPv6 index documentation.
9. Censys Search IPv6 documentation.
10. SI6 Networks IPv6 Toolkit (www.si6networks.com).
11. Nmap IPv6 support documentation.
12. RIPE Atlas / bgp.he.net allocation visibility.
