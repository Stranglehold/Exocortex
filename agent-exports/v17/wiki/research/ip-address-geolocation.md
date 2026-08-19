# IP Address Geolocation Techniques

**Status: STABLE** | **Last Updated: 2026-07-09** | **Cycles deepened: 2**

IP address geolocation is the process of mapping an IP address to a physical geographic location (country, city, postal code, coordinates). Used for fraud detection, content localization, security investigations, and OSINT attribution. Modern approaches combine database-driven lookups, active latency-based triangulation, and machine learning to achieve ~95% country-level and ~60-80% city-level accuracy, though mobile networks and Global South regions show dramatically higher error rates.

---

## 1. Method Tiers

| Method | Accuracy (Country) | Accuracy (City) | Latency | Use Case |
|--------|-------------------|----------------|---------|----------|
| Database-driven (MaxMind GeoIP2, DB-IP, IP2Location) | 99-99.9% | 50-80% | <1ms | Real-time triage, bulk processing |
| HTML5 Geolocation API (client-side JS) | N/A (browser-dependent) | High (GPS/WiFi) | Client-side only | Web application geolocation |
| DNS-based (GeoDNS) | Coarse (continent) | Low | <5ms | Content delivery, CDN routing |
| Latency-based triangulation (ping, traceroute) | ~95% | ~60% | Minutes | Active measurement, attribution |
| ML-enhanced (RIPE Atlas + CBG, Octant) | ~97% | ~75% | Minutes | Constraint-based, research-grade |
| Hybrid (database + latency + topology) | ~99% | ~85% | Variable | Best-in-class attribution |

**Commercial Accuracy Benchmarks:**
- **MaxMind**: 99.8% country-level, ~66% city-level (independent benchmarks)
- **IPinfo**: comparable country-level, slightly higher city accuracy (~72%)
- **DB-IP**: claims 99.99% country, >97% city — independent arXiv study found at least 40% of city-level and 80% of coordinate-level samples failed across four major databases

**Critical Failure Mode:** For all major databases, postal-code accuracy is ~30% and coordinate accuracy ~20% within ~50km radius. Investigators must log the accuracy radius as metadata — coordinates plotted on a map without error bars are misleading.

---

## 2. Network Type & Geography Disparities (Lost in the Prefix, arXiv:2605.21937)

Nabi, Bliton, Chung & Hasan (2026) conducted the largest-ever evaluation of IP geolocation accuracy using ground truth from RIPE Atlas and UNICEF Giga across 175 countries, testing four major providers (MaxMind GeoLite2, IPinfo, IP2Location, DB-IP).

### Mobile vs Fixed Networks

| Network Type | Median Error (km) | City-Level Failure Rate |
|-------------|-------------------|------------------------|
| Fixed (all providers) | 3–16 km | 9–20% (Europe) |
| Mobile (all providers) | 179–207 km | 53–61% (Asia), 66–72% (Africa) |

**Structural root cause:** Mobile networks and Global South ISPs use coarser BGP prefix announcements. ~70% of mobile prefixes span more than 100 km geographically. The prefix granularity gap — not provider algorithm quality — is the dominant explanatory factor across all databases. Coarser prefixes consistently produce the highest errors regardless of provider, network type, or geography.

### Global South vs Global North

| Region | Failure Rate (City-Level) |
|--------|---------------------------|
| Europe | 9–20% |
| Asia | 53–61% |
| Africa | 66–72% |

**Implication for OSINT:** Investigations targeting entities in Africa or Asia relying solely on database geolocation will have ~2/3 chance of city-level error. Cross-referencing with active measurements or domain WHOIS becomes mandatory in these regions.

---

## 3. OSINT Investigation Workflow

1. **Extract IP** from evidence source (email headers, server logs, platform metadata, breach databases)
2. **Database lookup**: Query MaxMind, IPinfo, DB-IP simultaneously; flag discrepancies (>50km difference between providers = suspect)
3. **WHOIS/RDAP**: Identify RIR (ARIN/RIPE/APNIC/LACNIC/AFRINIC) and registered organization
4. **DNS PTR record**: Check for geographic hints (e.g., `nyc-bb-1.carrier.net`, airport codes)
5. **Latency triangulation** (if accuracy critical): Probe from known-location monitors using RIPE Atlas or perfSONAR
6. **Cross-reference**: Correlate with email headers, web server logs, social media login IPs, WHOIS history
7. **Validation**: Confirm via independent means (business address, corporate registry, job posting location)
8. **Document confidence**: Log accuracy radius, provider used, and timestamp

### Tool Inventory

| Category | Tools |
|----------|-------|
| Database APIs | MaxMind GeoIP2, IPinfo, IP2Location, DB-IP, IPGeolocation.io |
| WHOIS/RDAP | whois CLI, ARIN/RIPE/APNIC RDAP, DomainTools |
| Latency Measurement | RIPE Atlas, perfSONAR, iPlocation.net, ping/traceroute |
| VPN/Proxy Detection | IPQualityScore, IP2Proxy, Fingerprint, MaxMind minFraud |
| OSINT Platforms | Maltego, SpiderFoot, Shodan, Censys |
| BGP/ASN | BGPView, Hurricane Electric BGP Toolkit, CAIDA AS Rank |

---

## 4. VPN, Proxy & Evasion Detection

VPNs, proxies, Tor, and CGNAT deliberately obscure an IP's geographic origin. Detection methods:

| Method | Accuracy | Notes |
|--------|----------|-------|
| Known exit node lists (Tor, public VPN) | ~95% | Maintained by providers; VPN companies constantly rotate IPs |
| TCP/IP stack fingerprinting | ~85% | OS mismatch between claimed and actual stack (p0f, JA3) |
| Behavioral analysis (connection timing, browser fingerprint) | ~80% | EmberSec/VPN detection research; latency anomalies |
| Commercial IP reputation databases | ~90% | IPQualityScore, MaxMind minFraud, IP2Proxy |
| DNS leak detection | ~70% | WebRTC and DNS leak testing |

**Evasion arms race:** Residential proxy networks (BrightData, IPRoyal) route traffic through real consumer IPs, making commercial VPN detection nearly useless. The IP may be geographically correct for the proxy endpoint but incorrect for the actual user. Only behavioral fingerprinting and cross-referencing at scale can distinguish residential proxies from legitimate traffic.

---

## 5. IPv6 Coverage Gap

IPv6 traffic exceeds 60% globally as of 2026, yet IPv6 geolocation databases remain substantially sparser than IPv4. The address space (2^128 vs 2^32) and hierarchical allocation structure make granular coverage inherently harder.

- **Database coverage**: MaxMind and IPinfo offer IPv6 geolocation but at significantly lower granularity (~country-level only for many prefixes)
- **Prefix scale problem**: A single IPv6 /32 allocation can span an entire ISP across multiple countries
- **Active measurement gap**: Few latency-based techniques have been validated at IPv6 scale
- **Tooling gap**: Most investigative tools remain IPv4-centric — a growing blind spot in OSINT methodology

Any serious pipeline needs an IPv6 roadmap including dual-stack measurement infrastructure.

---

## 6. Mobile IP Challenges (CGNAT & 4G/5G)

Mobile networks introduce unique geolocation challenges:

- **CGNAT (Carrier-Grade NAT)**: Multiple subscribers share a single public IP; the visible IP is often in a data center or regional breakout point
- **Centralized breakout**: 4G/5G networks tunnel traffic to centralized gateways — the IP may be 100-500 km from the actual device
- **Cell tower mapping**: CID (Cell ID) and LAC/TAI provide higher accuracy but require radio-layer access not available via OSINT
- **Google Geolocation API**: Commercial service that maps Wi-Fi APs and cell towers to coordinates; requires client-side access

**OSINT workaround**: When mobile IPs are encountered in breach data or logs, treat the IP as a coarse region indicator (~200 km radius) rather than a precise location. Use timestamped sequences of IP changes to infer mobility patterns.

---

## 7. Anycast & Cloud IP Challenges

- **CDNs** (Cloudflare, Akamai, Fastly): A single anycast IP serves traffic from dozens of locations
- **Cloud providers** (AWS, GCP, Azure): IPs are assigned from regional pools; the IP maps to a data center region, not a city
- **Detection**: BGP looking glass tools, Hurricane Electric BGP Toolkit, and Cloudflare Radar can identify anycast prefixes
- **Workaround**: For cloud IPs, use WHOIS to identify the organization; for CDN IPs, geolocation is effectively meaningless — pivot to other signals

---

## 8. Internet Number Resource Allocation

Understanding the IP allocation hierarchy is essential for interpreting geolocation results:

| Registry | Region | WHOIS Server |
|----------|--------|-------------|
| ARIN | North America | whois.arin.net |
| RIPE NCC | Europe, Middle East, Central Asia | whois.ripe.net |
| APNIC | Asia-Pacific | whois.apnic.net |
| LACNIC | Latin America, Caribbean | whois.lacnic.net |
| AFRINIC | Africa | whois.afrinic.net |

RIRs allocate IP blocks to ISPs and organizations; WHOIS/RDAP lookups reveal the registered entity and geographic region. However, registration data may be outdated — organizations relocate, IP blocks are transferred, and subsidiaries register under parent entities in different jurisdictions.

---

## 9. Accuracy Assessment & Benchmarking

**Key findings from empirical literature:**
- Static residential IPs: >95% country, 67-85% city depending on region
- Mobile IPs: as low as 30% city-level (Fallah & Natarajan, 2025)
- Trust the Source (2025): ML-enhanced RTT fingerprinting achieves 25% improvement over pure latency triangulation in low-landmark-density regions
- Combined active + passive topology inferencing achieved ~hundredth-degree accuracy estimates (Fallah & Natarajan, 2025)

**Self-benchmarking recommendations:**
1. Test against known-ground-truth IPs (own IPs, office IPs, VPS IPs)
2. Compare 3+ providers simultaneously; flag >50km discrepancies
3. Record accuracy radius metadata for all lookups
4. Re-test quarterly — databases are updated but stale entries persist

---

## 10. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **Entity Resolution** | IP geolocation adds spatial dimension to entity linkage; co-location at same time strengthens identity match |
| **Email Header Forensics** | Received headers contain IP chains; geolocation of each hop reconstructs sender's network path |
| **Domain WHOIS/DNS Investigation** | IP blocks, ASNs, and nameserver geography complement registrant data |
| **Data Breach Analysis** | Breach databases include IP addresses with timestamps — historical location timeline for identity corroboration |
| **Anti-Bot Evasion** | VPN/proxy detection methods mirror anti-bot detection; the residential proxy arms race affects both domains |
| **Social Media OSINT** | Platform IP logs (via legal process or breach) connect account activity to geographic regions |
| **CI Analysis Frameworks** | IP evidence interpretation follows structured analytic techniques: hypothesis testing, alternative explanations, confidence assessment |
| **Maritime Domain Awareness** | AIS manipulation (GPS spoofing, dark vessels) is structurally the same problem as IP geolocation evasion — adversary obscures location to evade attribution |
| **Metadata-Resistant Communication** | VPNs, Tor, and mix networks deliberately obscure IP geolocation; understanding evasion techniques is necessary to evaluate protocol anonymity guarantees |
| **Satellite Imagery OSINT** | Cross-view geolocation (arXiv:2605.19656, 2606.10166) uses satellite-to-ground fusion to geolocate images — the spatial reasoning inverse of IP geolocation |

---

## 11. Privacy & Legal Boundaries

- **GDPR**: IP addresses are personal data (CJEU C-582/14, Breyer v Germany, 2016) when linkable to individuals
- **CFAA**: Restricts unauthorized access to protected computers
- **ECPA**: Restricts interception of electronic communications
- **VPN/proxy detection**: May be considered surveillance under some jurisdictions
- **OSINT best practice**: Document lawful basis for each lookup; do not bulk-scan without authorization; erase data after investigation purpose is fulfilled

---

## 12. Open Questions & Research Frontiers

1. How to systematically benchmark free IP geolocation APIs for OSINT use cases (accuracy, freshness, rate limits)?
2. What is the accuracy ceiling for city-level geolocation without active probing infrastructure?
3. How does IPv6 geolocation database coverage compare to IPv4 in 2026?
4. Can generative AI improve geolocation by reasoning about contextual clues from multiple signals?
5. What is the intersection of IP geolocation and Starlink/direct-to-cell satellite internet, where ground station locations increasingly diverge from user locations?
6. Can intermediate router discovery (Wang et al.) serve as secondary landmarks in regions with low landmark density?
7. What is the counter-evasion detection rate against residential proxy networks at scale?

---

## References

1. Nabi, Bliton, Chung, Hasan (2026). "Lost in the Prefix: Revisiting IP Geolocation Accuracy Across Networks and Geographies." arXiv:2605.21937.
2. Fallah & Natarajan (2025). "Large-Scale IP Geolocation Accuracy Assessment Using Measurement Datasets." JISIS 2025.I4.040.
3. "Trust the Source: A Latency-Based ML Approach to IP Geolocation" (2025). ScienceDirect, Computer Networks. DOI: 10.1016/j.comnet.2025.111721.
4. MaxMind GeoIP2 Accuracy: https://www.maxmind.com/en/geoip2-city-accuracy-comparison
5. DB-IP: https://db-ip.com/
6. IPinfo: https://ipinfo.io/
7. IP2Location: https://www.ip2location.com/
8. RIPE Atlas: https://atlas.ripe.net/ (measurement platform)
9. Tor Project Exit List: https://check.torproject.org/exit-addresses
10. IPQualityScore VPN detection: https://www.ipqualityscore.com/
11. Carpenter v. United States, 585 U.S. ___ (2018) — CSLI location data and Fourth Amendment
12. Exocortex wiki/research/domain-whois-dns-investigation.md — ASN and IP block investigation
13. Exocortex wiki/research/email-header-forensics-header-analysis.md — Received header IP chain analysis
14. Exocortex wiki/research/geolocation-osint.md — comprehensive geolocation for OSINT
15. Field reports: /a0/usr/workdir/workspace/field-reports/20260528_ip-address-geolocation-techniques.md
