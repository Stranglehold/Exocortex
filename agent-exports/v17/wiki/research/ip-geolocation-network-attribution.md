# IP Geolocation & Network Attribution

**Status: STABLE**
**Topic Slug: ip-geolocation-network-attribution**
**Created: 2026-05-20 | Last deepened: 2026-05-20**
**Domain: OSINT / Network Investigation**

---

## Overview

IP geolocation maps IPv4/IPv6 addresses to geographic locations, network operators, and organizational ownership. For OSINT and investigation, accurate IP attribution answers three core questions: where is this server physically located? who operates it? is the claimed origin consistent with observable network evidence?

The discipline spans database lookups, BGP route analysis, VPN/proxy detection, CDN attribution, and carrier-grade NAT tracing. Each layer adds confidence — or reveals deception — about an IP address's true origin.

---

## 1. IP Geolocation Databases

### 1.1 Commercial Providers

| Provider | Country Accuracy | City Accuracy | Update Frequency | Proxy/VPN Detection |
|----------|-----------------|---------------|------------------|---------------------|
| MaxMind GeoIP2 | 99.8% | 55–80% | Weekly | Yes (GeoIP2 Anonymous IP) |
| IP2Location | 99.5% | 75%+ | Monthly | Yes (built-in proxy type) |
| IPinfo.io | 99.8% | 60–80% | Daily | Yes (privacy detection) |
| DB-IP | 99% | 55–75% | Monthly | Yes (VPN detection) |
| NetAcuity (Digital Element) | 99.9% | 85%+ | Weekly | Yes (Hyperlocal edition) |

**Accuracy factors**: Country-level accuracy is reliably high (95–99.9%) across all providers. City-level accuracy drops to 55–80% — the IP may map to the ISP's regional hub rather than the user's actual city. Accuracy also varies by region: North America and Europe achieve higher accuracy than developing markets due to richer ISP peering data.

### 1.2 Free Options

- **MaxMind GeoLite2**: Free, weekly updates, 95–99% country, 55–80% city. Best-in-class for free databases.
- **IP2Location LITE**: Free monthly DB5 edition, country/region/city/ISP/domain/whether-proxy.
- **IPinfo.io Free**: 50K requests/month, includes ASN, company, privacy detection.
- **DB-IP Lite**: Free monthly, country-level only.

### 1.3 Database Limitations

**Why Geo-IP data can mislead** (BENOCS analysis, 2025):
1. **ISP routing topology**: IPs assigned to a London ISP may geo-locate to a data center 200km away due to regional routing aggregation.
2. **Anycast addresses**: Cloudflare, Google, and Akamai announce the same IP from dozens of locations — the geolocation database sees whichever location it probed first.
3. **Stale assignments**: IP blocks change hands between ISPs; databases lag 30–90 days behind reassignment.
4. **Mobile carrier IPs**: 4G/5G carrier-grade NAT pools report at the carrier's core network location, not the subscriber's position.
5. **VPN exit nodes and proxy IPs** deliberately misrepresent location.

**Detection rates are not static**: IPinfo reported (BlackHat webinar, July 2025) that privacy-related IP classifications change for 7–56% of addresses monthly, making continuous real-time detection essential.

---

## 2. VPN, Proxy & Tor Detection

### 2.1 Detection Techniques

**Seven core methods** (IPTrackeronline, 2026):

| Method | Accuracy | Description |
|--------|----------|-------------|
| IP database lookup | 70–85% | Check against commercial VPN/proxy IP databases |
| ASN analysis | 60–75% | Detect hosting-AS-owned IPs (datacenter proxies) vs residential ISP ASes |
| DNS leak detection | 50–65% | Check if DNS queries resolve through VPN provider or bypass to ISP DNS |
| WebRTC leak checks | 40–60% | Detect local IP disclosure even through VPN tunnel |
| TCP/IP fingerprinting | 30–50% | Analyze TCP stack parameters to identify OS/proxy characteristics |
| Behavioral analysis | 65–80% | Latency patterns, timezone vs IP location mismatch, browser clock |
| Latency triangulation | 40–55% | Measure RTT from known vantage points to estimate physical distance |

### 2.2 Proxy Type Classification

- **Datacenter proxies**: Easily detected via ASN analysis (AS owned by DigitalOcean, OVH, AWS, etc. rather than residential ISP). Detection accuracy >90%.
- **Residential proxies**: Harder — the IP belongs to a legitimate residential ISP but is relayed through malware-compromised or consent-based proxy networks. Detection relies on behavioral analysis: connection velocity, browser fingerprint mismatch, timezone/language inconsistency.
- **Mobile proxies**: 4G/5G carrier IPs used as proxies — nearly impossible to distinguish from legitimate mobile users via IP alone. Requires device fingerprinting.
- **Tor exit nodes**: Publicly logged — easy to detect via exit node databases, but cannot trace back to origin.

### 2.3 Commercial Detection APIs (2026)

- **IPQualityScore**: Fraud score, proxy/VPN/Tor detection, bot detection, residential proxy risk
- **SEON**: IP intelligence + device fingerprinting; catches residential proxies that IP-only APIs miss
- **Fingerprint (formerly FingerprintJS)**: Browser fingerprinting + VPN detection; 99.5% visitor identification accuracy
- **Silent Push IP Context** (August 2025): Preemptive threat detection combining IP intelligence with VPN/proxy context
- **ipgeolocation.io**: VPN, proxy, Tor, and relay detection; pricing comparisons available

---

## 3. BGP Analysis for Network Attribution

### 3.1 Core Concepts

The Border Gateway Protocol (BGP) is the routing protocol that connects ~75,000 Autonomous Systems (ASes) on the Internet. BGP analysis answers OSINT questions like:

- Which AS (organization) announces this IP block?
- Who are their upstream transit providers?
- Has this IP block been hijacked or leaked?
- What other IP prefixes does this organization control?

### 3.2 BGP Tools

| Tool | Function |
|------|----------|
| **bgp.he.net** (Hurricane Electric) | Free web lookup: IP → ASN, prefix, upstream providers, peer graph |
| **bgp.tools** | Real-time BGP looking glass, route propagation visualization |
| **RIPE RIS** (Routing Information Service) | Historical BGP data archive; raw route collectors worldwide |
| **RouteViews** (University of Oregon) | Historical BGP routing table dumps since 1997 |
| **BGPStream** (CAIDA) | Programmatic BGP event detection API; Python library available |
| **Cloudflare Radar BGP** | Real-time BGP origin hijack detection (built on RPKI validation) |
| **BGProtect** | Nation-state grade BGP monitoring and route leak detection |

### 3.3 BGP Anomalies & Attribution Implications

**Route hijacks** (Cloudflare Radar, 2025): An attacker announces a victim's IP prefix from their AS, intercepting or redirecting traffic. Detection is now automated: Cloudflare's system validates every BGP announcement against the Resource Public Key Infrastructure (RPKI).

**Route leaks**: A legitimate AS accidentally announces routes learned from one peer to another, creating unintended paths. Detection via AS path analysis — anomalous AS path length or unexpected transit ASes.

**AS path prepending**: Deliberate AS path lengthening to de-prioritize routes — a common traffic engineering technique that, when observed for a suspicious IP block, can reveal operational infrastructure or misdirection.

**Infrastructure pivoting**: Once an IP is mapped to an AS, investigators pivot to find other IPs originated by the same AS (`bgp.he.net/search?q=ASxxxxx`). Combined with passive DNS, this reveals the full infrastructure footprint of a threat actor.

### 3.4 arXiv Source: BEAR (arXiv:2506.04514)

BEAR (BGP Event Analysis and Reporting) is a systematic framework for detecting and analyzing BGP anomalies including route leaks and hijacks. It combines rule-based detection with machine learning to classify BGP events by type and severity. For OSINT: BEAR-like analysis can surface when an IP block under investigation was involved in a routing anomaly during a specific time window.

---

## 4. CDN Attribution Challenges

### 4.1 The Problem

Content Delivery Networks (CDNs) — Cloudflare, Akamai, Fastly, Amazon CloudFront — terminate TLS connections and proxy traffic to origin servers hidden behind their infrastructure. The public-facing IP resolves to the CDN, not the origin. This is the single largest obstacle to IP-based investigation of web infrastructure.

### 4.2 Attribution Techniques

1. **TLS certificate inspection** (crt.sh, Censys): Search for certificates issued to the target domain — may reveal origin hostnames or IPs that predate CDN adoption.
2. **DNS history** (SecurityTrails, DNSDB): Historical A records often show direct origin IPs before the CDN was configured.
3. **Subdomain enumeration**: Origin servers are frequently exposed on subdomains like `origin.`, `direct.`, `cms.`, `staging.`, `dev.` that aren't routed through the CDN.
4. **MX records**: Mail servers rarely use CDNs — the MX record's IP often reveals the hosting provider directly.
5. **SPF records**: The `include:` and `ip4:` mechanisms in SPF expose IP ranges authorized to send email, often including the origin hosting infrastructure.
6. **Error page fingerprinting**: CDNs return branded error pages (Cloudflare's 502, Fastly's 503) — but when the origin server's own error page leaks through, it reveals server software, framework, and sometimes internal hostnames.
7. **HTTP response header analysis**: Origin servers may insert headers (`X-Powered-By`, `Server`, `X-Backend-Server`) that pass through CDN proxies.

---

## 5. Carrier-Grade NAT (CGNAT) & IP Sharing

### 5.1 The Challenge

IPv4 exhaustion has driven widespread adoption of CGNAT, where hundreds or thousands of residential subscribers share a single public IPv4 address. This makes IP-based identity attribution nearly impossible without additional signals:

- **Time correlation**: Logs from multiple services can correlate sessions to the same subscriber if timestamps and destination IPs align.
- **Port-block allocation**: Some CGNAT implementations allocate deterministic port blocks (RFC 7422), making subscriber identification possible from a source port.
- **IPv6 bypass**: Subscribers with dual-stack IPv6 often have unique IPv6 addresses even when IPv4 is shared — if the target service supports IPv6.

### 5.2 Mobile Carrier CGNAT

Mobile carriers (Verizon, T-Mobile, Vodafone) use massive CGNAT pools. The IP geolocation shows the carrier's regional gateway — not the phone's location. For mobile IPs:

- Layer GPS/coordinates from device-level data rather than IP
- Use cell tower triangulation for approximate location
- Mobile proxies (section 2.2) exploit this infrastructure for anonymity

---

## 6. IP Geolocation OSINT Workflow

### 6.1 Structured Investigation Pipeline

```
IP ADDRESS
    |
    ├─ Step 1: Geolocation lookup (MaxMind / IP2Location / IPinfo)
    │   └─ Country, city, ISP, ASN, organization
    │
    ├─ Step 2: BGP analysis (bgp.he.net, bgp.tools)
    │   └─ AS owner, upstream providers, peer graph, prefix announcement history
    │
    ├─ Step 3: VPN/Proxy check (IPQualityScore, ipgeolocation.io, Silent Push)
    │   ├─ If residential IP: proceed to Step 4
    │   └─ If proxy/VPN: attribution limited — pivot to behavioral/intel analysis
    │
    ├─ Step 4: Reverse DNS / PTR record (dig -x IP)
    │   └─ ISP naming conventions often reveal geographic region codes
    │
    ├─ Step 5: Passive DNS (SecurityTrails, VirusTotal)
    │   └─ What domains resolve(d) to this IP? When?
    │
    ├─ Step 6: CDN check (is this IP behind Cloudflare/Akamai/Fastly?)
    │   ├─ If CDN: use section 4 attribution techniques for origin discovery
    │   └─ If direct: proceed to WHOIS/certificate analysis
    │
    └─ Step 7: Cross-reference with breach data
        └─ Does this IP appear in breach logs with associated accounts/usernames?
```

### 6.2 Automation Tools

- **ipinfo.io CLI**: `curl ipinfo.io/8.8.8.8/json` — returns ASN, company, privacy flags, abuse contact
- **bgp.he.net API**: Programmatic BGP prefix/ASN lookups, no authentication required for basic queries
- **Shodan**: `shodan host 1.2.3.4` — reveals open ports, services, banners, and SSL certificates on the target IP
- **Censys**: Certificate transparency logs, service banners, and host enumeration
- **VirusTotal**: IP passive DNS, file detections communicating with the IP, related domains

---

## 7. Cross-Domain Connections

1. **Email Forensics & Header Analysis**: Every email header contains `Received:` headers with IP addresses — this page provides the methodology to attribute those IPs to ISPs, locations, and organizations.

2. **Domain WHOIS & DNS Investigation**: IP → ASN → organization mapping (bgp.he.net) complements WHOIS registration data; DNS history (section 4.2) bridges CDN-obscured IPs back to origin servers.

3. **HUMINT Tradecraft for OSINT**: The Admiralty Code (A1–F6 data confidence scoring from humint-tradecraft-osint page) applies directly — rate IP geolocation as A3–C3 depending on provider accuracy and update freshness.

4. **Data Breach Analysis & Identity Linkage**: IP addresses in breach dumps (section 6.1 step 7) link network infrastructure to user identities — credential reuse analysis across IP-anchored accounts.

5. **Network Analysis & Graph Theory**: BGP AS-level topology is a directed graph; community detection algorithms (Louvain, Leiden) applied to AS relationships reveal organizational clusters that IP-level analysis misses.

6. **Anti-Bot Evasion**: The VPN/proxy detection arms race (section 2) is the same adversarial dynamic as browser fingerprinting — both are detection-evasion cycles requiring continuous database updates.

7. **Privacy & Cryptography**: VPN detection (section 2) exists in tension with privacy-preserving infrastructure — the same ASN analysis that identifies proxies also de-anonymizes privacy-conscious users, raising ethical/legal boundaries.

8. **Epistemic Integrity**: IP geolocation exemplifies the evidence-chain principle: every attribution claim traces to a specific database version, lookup timestamp, and verification method — no claim floats unsourced.

9. **Entity Resolution**: IP → ASN → organization is an entity resolution problem — the same organization may operate under multiple AS numbers, and the same AS may announce prefixes belonging to different legal entities.

---

## References

1. MaxMind, "GeoIP2 Accuracy," https://www.maxmind.com/en/geoip2-accuracy (2026)
2. IP2Location, "IP Geolocation API Accuracy," https://www.iplocate.io/blog/best-ip-geolocation-api (2026)
3. Linkly, "The 7 Best Free GeoIP Databases for Developers (2026)," https://linklyhq.com/blog/free-geoip-databases (2025)
4. BENOCS, "Why Geo-IP Data Can Mislead You and What to Use Instead," https://www.benocs.com/blog/why-geo-ip-data-can-mislead-you/ (2025)
5. IPTrackeronline, "How to Detect VPN Usage: 7 Detection Methods with Accuracy Data," https://www.iptrackeronline.com/blog/vpn-detection-guide/ (2026)
6. Fingerprint, "How to Detect a VPN to Prevent Fraud in 2026," https://fingerprint.com/blog/vpn-detection-how-it-works/ (2026)
7. Cloudflare, "Cloudflare Radar's New BGP Origin Hijack Detection System," https://blog.cloudflare.com/bgp-hijack-detection/ (2025)
8. arXiv:2506.04514, "BEAR: BGP Event Analysis and Reporting" (2025)
9. IPinfo.io, "IP Intelligence: A Guide to Recent Advances in Anonymous VPN and Proxy Detection" (BlackHat webinar, July 2025)
10. ShadowDragon, "OSINT Techniques: Expert Tactics for Investigators (2026)," https://shadowdragon.io/resources/osint-techniques/ (2026)
11. RFC 7422, "Deterministic Address Mapping to Reduce Logging in Carrier-Grade NAT Deployments" (2014)
