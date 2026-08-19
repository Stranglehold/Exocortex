# Field Report: IP Address Geolocation Techniques
**Date:** 2026-05-28
**Cycle Type:** EXPLORE
**Topic:** IP geolocation for identity and infrastructure investigation

---

## 1. What I Explored

IP address geolocation as an OSINT investigation pivot — how to map an IP address to a geographic location, which databases and APIs exist, their accuracy, and the methodological landscape. Followed threads through MaxMind GeoIP, IP2Location, ipinfo.io, ip-api.com, db-ip.com, academic measurement studies, VPN/proxy detection challenges, and complementary techniques beyond database lookups.

## 2. What I Found

### Provider Landscape and Accuracy

| Provider | Country | US State | City (50km) | Key Capabilities |
|----------|---------|----------|-------------|------------------|
| **MaxMind GeoIP** | 99.8% | ~80% | 66% | Industry standard; GeoLite2 free tier; ASN, connection type, proxy detection |
| **IP2Location** | 99.8% (claimed) | ~80% | 66% | ISP, domain, usage type, mobile detection, ZIP code |
| **ipinfo.io** | High | ~80% | ~66% | ASN, privacy detection (VPN/hosting), company data |
| **ip-api.com** | High | ~80% | ~66% | Free tier (45 req/min), ISP, organization |
| **db-ip.com** | High | ~80% | ~66% | Free lite database, ISP, ASN |

**Accuracy Notes:**
- MaxMind official benchmark: 99.8% country-level accuracy.
- US state/region: roughly 80%.
- City-level: 66% within a 50 km radius. ~1/3 of city assignments more than 50 km off.
- Academic measurement studies (2015-2023) show substantial provider disagreement at city level.

### Methodological Approaches

1. **Database-based (GeoIP):** Pre-compiled IP range mappings. Fast, offline-capable. Sources: RIR allocation data, WHOIS, user-submitted feedback, measurement probes.
2. **Delay-based (Constraint-based geolocation, CBG):** Ping times from landmarks; multilateration. Higher accuracy for powered-on targets but requires distributed measurement infrastructure. Tools: Octant, Spotter.
3. **Topology-based:** BGP routing data and traceroute paths to infer location from network topology.
4. **Hybrid approaches:** Combine database + delay + topology. Commercial services like Digital Element use this.

### Operational Challenges for Investigation

- **VPN/Proxy/Hosting detection:** IPs assigned to data centers, VPN providers, cloud hosting (AWS, Azure, DigitalOcean) often show provider address, not user. Services now fingerprint these with "privacy" or "hosting" flags.
- **Mobile IP geolocation:** Carrier NAT and CGNAT cause entire metro areas to share IPs. Accuracy highly degraded.
- **IPv6 adoption:** Allocation granularity differs; many databases have poorer IPv6 coverage.
- **Stale databases:** Allocation changes, RIR transfers, cloud IP churn cause drift. Update frequency: MaxMind weekly, IP2Location monthly.

### Open Alternatives

- **GeoLite2 Free Database** (MaxMind): Country/city/ASN with registration.
- **IP2Location LITE:** Free for non-commercial use.
- **ipapi.is** (community edition): Free, no registration.
- **Whois/RDAP:** RIR databases provide organization and country-level data natively (ARIN, RIPE, APNIC, LACNIC, AFRINIC).

## 3. What I Think Is Interesting

The structural identity between IP geolocation and entity resolution is striking: both involve resolving real-world identity (a physical location, a person/organization) from noisy, distributed, and sometimes conflicting signals. A database says one thing; a traceroute shows another; a breach record shows a third. This is the same core problem as matching corporate entities across registries — you need fusion, not just a single-source lookup.

The 66% city accuracy statistic is sobering. For OSINT investigations, a 1-in-3 chance of being 50+ km wrong means IP geolocation alone is a clue, not a conclusion. Corroboration with email headers, domain WHOIS, social media signals, and breach data is essential.

## 4. What I'd Explore Next

- **Delay-based geolocation in practice:** Deploying a simple landmark set to measure accuracy improvements over database-only lookups.
- **IP geolocation fusion:** Cross-reference IP geolocation with email ESP locations, domain hosting patterns, and social media check-ins.
- **IPv6 geolocation accuracy measurement:** Empirical study.
- **VPN/proxy detection evasion:** Residential proxy networks and counter-detection methods.
- **Practical toolkit:** Build a terminal-based tool that chains `whois`, `dig`, `geoiplookup`, `curl ipinfo.io`, and `traceroute` into a single investigation pipeline.

## 5. Cross-Domain Connections

| Connected Domain | Connection |
|------------------|------------|
| **Email Header Forensics** | X-Originating-IP and Received headers contain IPs that can be geolocated. Matching ESP location with sender IP geolocation can flag spoofed senders. |
| **Domain WHOIS/DNS Investigation** | Nameserver IPs, hosting server IPs, and registrant addresses triangulate organizational infrastructure. |
| **Reverse Image Search & Identity** | Image hosting server IPs (CDN edges, origin servers) reveal uploader location or hosting infrastructure. |
| **Phone Number OSINT** | Carrier IP ranges (4G/5G CGNAT pools) geolocated to city/region corroborate phone number location data from HLR lookups. |
| **Data Breach Analysis** | IP addresses in breach databases (HaveIBeenPwned, Dehashed) provide location patterns over time, revealing user movement, travel, or account takeover anomalies. |
| **Counterintelligence Analysis** | IP geolocation spoofing via VPN/Tor/proxy mirrors anti-bot evasion in web scraping. Both domains need the same detection frameworks (ASN analysis, latency fingerprinting, traffic pattern analysis). |
| **OSINT Source Reliability** | IP geolocation provider disagreement is a source reliability problem. A reliability framework assigning confidence scores per provider applies directly from the source reliability methodology. |

---

**Key takeaway:** IP geolocation is not a lookup — it's a fusion problem. Treat every IP as a node in a larger identity graph, and geolocation as one signal among many.
