# Field Report: IP Address Geolocation for OSINT Investigation
**Date:** 2026-05-28
**Cycle Type:** EXPLORE
**Topic:** IP Address Geolocation Techniques
**Interest Domain:** OSINT & Investigation Methodology

---

## 1. What I Explored

IP address geolocation — the mapping of IP addresses to physical geographic locations — as an OSINT investigation technique. This domain was identified as the least-recently explored active interest: phone-number OSINT had a STABLE wiki page with recent field reports, but IP geolocation had no dedicated wiki page and had not been examined in depth since the system's exploration cycles began.

The research followed three threads:
- **Accuracy benchmarks** for commercial geolocation databases (MaxMind, IP2Location, DB-IP, IPinfo) and the gap between vendor-claimed and independent measurements
- **Investigation methodology**: the field operator's workflow for IP OSINT — triage, pivoting, cross-referencing, and attribution
- **VPN/proxy/anonymization detection**: techniques for identifying when an IP address is an exit node rather than the true origin

---

## 2. What I Found

### 2.1 Accuracy Landscape

IP geolocation accuracy splits sharply by granularity level:

| Granularity | Typical Accuracy | Notes |
|-------------|-----------------|-------|
| Country | 99.5–99.8% | Highly reliable across all major providers |
| State/Region | ~80-90% | Border regions create mismatches |
| City | 60-85% (residential) / 40-65% (mobile) | Wide variance by provider and methodology |
| Postal Code | ~30% correct (independent benchmark) | Largest failure mode |
| Coordinates | ~20% correct (independent benchmark) | Within ~50km radius; accuracy radius is critical metadata |

Vendor claims vs. independent reality:
- **MaxMind**: claims 99.8% country, ~66% city (50km radius, US); transparent about accuracy radius
- **IP2Location**: claims >99.5% country, >75% city (50 miles, global)
- **DB-IP**: claims 99.99% country, >97% city — but an independent arXiv study of the entire IPv4 space found that **at least 40% of city-level and 80% of coordinate-level samples failed to resolve correctly** across four major databases
- **Data fusion approach** (2023 MDPI Electronics study): combining multiple databases achieved 94% city-level accuracy with 99.99% coverage — the most promising path forward

The fundamental limitation: ISPs reassign IP addresses dynamically, corporate networks route through central gateways, mobile IPs map to carrier infrastructure (not the device), CGNAT pools many users behind one IP, and satellite internet resolves to ground stations. The IP address is a network topology identifier, not a physical location identifier.

### 2.2 Investigation Workflow

The field operator's IP investigation workflow has a clear structure:

**Phase 1 — Triage**
- Establish ASN and organization (datacenter vs. residential ISP vs. cloud provider)
- Check basic geolocation for directional context
- Review abuse history via AbuseIPDB and VirusTotal
- Check open services via Shodan/Censys (what's this IP actually running?)

**Phase 2 — Pivot Points**
- **Passive DNS pivoting**: SecurityTrails/PassiveTotal to see historical domain resolutions; forward-then-reverse pivoting to uncover infrastructure clusters
- **Certificate intelligence**: Censys/Shodan TLS certificate transparency logs — reused certificates, subject names, JARM fingerprints linking seemingly unrelated hosts
- **Banner/service fingerprinting**: SSH banners, HTTP headers, favicon hashes, JARM hashes to profile tooling
- **WHOIS pivoting**: reverse WHOIS, nameserver pivoting, IP block attribution

**Phase 3 — Network Graph Building**
- Map relationships among IPs, domains, ASNs (Maltego, SpiderFoot, or manual)
- Cross-reference with threat intelligence: MISP events, OpenCTI, Abuse.ch trackers, community posts

**Phase 4 — Attribution Assessment**
- Determine confidence level: is this a direct endpoint, a proxy, a VPN exit node, or Tor?
- Never attribute to an individual based solely on IP geolocation

### 2.3 VPN/Proxy/Anonymization Detection

Beyond static blocklists of known exit nodes:
- **Hosting-provider pattern analysis**: datacenter IPs are statistically more likely to be VPN endpoints, servers, or bots vs. residential ISPs
- **Consistency checks**: sudden shifts between residential ISP and distant datacenter IPs indicate proxy/VPN usage
- **Temporal analysis**: IP appearing from multiple geographic locations in rapid succession is a red flag
- **Commercial detection**: MaxMind, IP2Location, and IPinfo all offer VPN/proxy/Tor detection flags with risk scoring; iCloud Private Relay detection now standard
- **Limitation**: detection tells you the visible network is an anonymization service, not the true origin. Attribution stops at the exit node

**Forensic interpretation principle** (Forensic OSINT, 2026): Anonymized IP evidence is not useless — it can establish timeline, infrastructure association, and TTP patterns even when it cannot establish identity.

### 2.4 IPv6 Geolocation — The Blind Spot

IPv6 traffic is projected to exceed 60% by 2026, yet IPv6 geolocation databases remain sparse. The address space is orders of magnitude larger than IPv4 (2^128 vs. 2^32), and geographic allocation patterns are less mature. Most investigative tooling remains IPv4-centric, creating a growing evidence gap. This is a critical vulnerability in OSINT methodology that the field has not yet addressed.

### 2.5 Emerging Trends (2025-2026)

- **AI-enhanced accuracy**: ML models improving location estimates by learning routing patterns
- **Edge computing integration**: geolocation processing at network edge for lower latency
- **Privacy-compliant approaches**: differential privacy, aggregated datasets, on-device processing for GDPR/CCPA
- **Data fusion**: combining multiple databases for 94%+ city accuracy (2023 MDPI study)
- **Latency-based trilateration**: IPinfo's Probe Network using active measurement from distributed vantage points
- **GeoFeeds (RFC 8805)**: ISPs self-publishing geolocation data, improving ground truth
- **Market growth**: projected $11.1 billion by 2032, 15% CAGR

---

## 3. What I Think Is Interesting

**The accuracy gap is a feature, not just a bug.** Investigators need to understand that IP geolocation at the city level is probabilistic, not deterministic. An IP resolving to "New York City" with a 100km accuracy radius might actually be in northern New Jersey or southern Connecticut. The accuracy radius metadata (MaxMind's most underutilized feature) transforms the data point from a misleadingly precise lat/lon pair into a probabilistic region. This is the same epistemic framework needed for entity resolution — treating matches as confidence scores rather than binary decisions.

**The IPv6 evidence gap is a brewing crisis.** As the internet migrates to IPv6, OSINT investigators are losing a key evidence source not because the data doesn't exist, but because the tooling hasn't caught up. This is analogous to the shift from desktop to mobile that disrupted digital forensics a decade ago. Any serious OSINT methodology needs an IPv6 roadmap.

**The forensic interpretation of anonymized IPs is more nuanced than "VPN = useless."** Even an IP that resolves to a NordVPN exit node tells you something: the subject is privacy-conscious, is using a specific VPN provider (which may have jurisdiction implications), and the timing of the connection may correlate with other events. In CI analysis terms, a VPN's presence is a signal, not just noise.

**Anti-bot evasion and IP geolocation are two sides of the same coin.** The same techniques that bots use to evade detection (IP rotation, residential proxy networks, identity design) are the techniques that investigative targets use to obscure their location. The cat-and-mouse game between evasion and detection is the same structural problem viewed from opposite sides.

---

## 4. What I'd Explore Next

- **IPv6 geolocation databases**: a deep dive into the current state — who has usable IPv6 data, what accuracy looks like, and whether the tooling gap is closing
- **Residential proxy networks as a service**: the underground economy of residential IP rotation (Bright Data, Oxylabs, etc.) and what it means for OSINT attribution
- **IP geolocation in email forensics pipeline**: how IPs extracted from email headers integrate with geolocation databases for sender profiling — a direct bridge to the existing email-header-forensics skill
- **Latency-based geolocation measurement**: the technical depth of how active measurement (ping triangulation) improves accuracy over passive database lookups

---

## 5. Cross-Domain Connections

| Connection | Domain | Link |
|-----------|--------|------|
| **Entity Resolution** | Data Aggregation | IP geolocation adds a spatial dimension to entity linkage; two records with the same IP location at the same time are more likely to be the same entity |
| **Email Header Forensics** | OSINT Investigation | Received headers contain IP chains; geolocation of each hop builds a sender's network path |
| **Domain WHOIS/DNS Investigation** | Infrastructure Analysis | IP blocks, ASNs, and nameserver geography complement WHOIS registrant data |
| **Data Breach Analysis** | Identity Linkage | Breach databases often include IP addresses with timestamps — geolocation provides a historical location timeline for identity corroboration |
| **Anti-Bot Evasion** | Counter-Surveillance | VPN detection methods mirror anti-bot detection; the randomization paradox (randomized fingerprints now detectable) applies to IP rotation patterns |
| **Social Media OSINT** | Identity Resolution | Platform IP logs (when available via legal process or breach) connect account activity to geographic regions |
| **CI Analysis Frameworks** | Intelligence Methodology | IP evidence interpretation follows the same structured analytic techniques as CI: hypothesis testing, alternative explanations, confidence assessment |
