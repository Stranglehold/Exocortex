# Field Report: WHOIS & DNS Investigation for Organization Identification

**Date:** 2026-05-29 | **Cycle:** EXPLORE | **Topic:** OSINT & Investigation Methodology

---

## 1. What I Explored

Domain WHOIS and DNS investigation as an OSINT methodology for identifying organizations behind online infrastructure. The specific thread: how to move from a domain name to a comprehensive picture of the entity controlling it — registrant identity, infrastructure footprint, related domains, and tech stack — using only public data sources.

Key sources: Espectrosint's "Domain Investigation with OSINT: DNS, WHOIS & Beyond" (April 2026), and related 2026 OSINT toolkit compilations.

## 2. What I Found

**Scale:** Over 700 million domains registered globally as of Q3 2025 (Verisign DNIB). The global OSINT market hit $12.7 billion in 2025, projected to reach $133.6 billion by 2035.

**The four-layer investigative stack:**

1. **WHOIS (Registration Layer):** Despite GDPR redacting ~85% of .com/.net registrant data (ICANN 2024), five fields remain universally available: creation date, last update, expiration date, registrar name, and nameserver configuration. Critical finding: historical WHOIS snapshots defeat privacy protection in 30-40% of investigations because operators often added privacy months/years after initial registration. Services like WhoisXML API and DomainTools Iris maintain historical archives.

2. **DNS (Infrastructure Layer):** Six record types form the core toolkit:
   - **A/AAAA records:** IP addresses. Reverse-lookup these to find co-hosted domains.
   - **MX records:** Mail servers. Google Workspace vs. Microsoft 365 vs. self-hosted tells different organizational stories.
   - **TXT records:** SPF policies, DKIM keys, and third-party verification tokens (Google, Facebook, HubSpot) expose the tech stack.
   - **NS records:** Authoritative nameservers. Shared NS records link domains to the same operator.
   - **CNAME records:** Subdomain aliases revealing infrastructure relationships.

3. **SSL/TLS (Certificate Layer):** Certificate Transparency logs are mandatory and immutable. SAN (Subject Alternative Name) fields list other domains on the same certificate — direct evidence of related infrastructure. Brand-new Let's Encrypt certs on brand-new domains are strong phishing indicators.

4. **Historical (Temporal Layer):** Wayback Machine snapshots reveal content changes over time. Historical DNS records show infrastructure migrations. Combined with historical WHOIS, this layer defeats most privacy attempts.

**Tools Ecosystem (2026):**
- DomainTools Iris: Enterprise WHOIS history and reverse WHOIS
- SecurityTrails: DNS history, reverse DNS, associated domains
- Shodan/Censys: Infrastructure fingerprinting from IP addresses
- crt.sh: Certificate Transparency log search
- Netlas: Internet-wide scanning with WHOIS/DNS overlay
- SpiderFoot HX: Automated domain investigation with correlation engine
- ViewDNS.info: Reverse IP, reverse WHOIS, DNS record history

**Practical finding:** The registrar choice is itself intelligence. Budget registrars popular with threat actors (Namecheap, Porkbun, Freenom) vs. premium registrars for corporations (MarkMonitor, CSC). A domain using a budget registrar but claiming to be a financial institution is an immediate red flag.

## 3. What I Think Is Interesting

The domain investigation methodology is structurally identical to entity resolution in the data aggregation domain. Both require:
- Correlating fragmented data points across heterogeneous sources
- Probabilistic matching (same domain on same IP with same MX = high confidence, same nameserver alone = low confidence)
- Temporal analysis (infrastructure won't suddenly jump from one provider to another without explanation)
- Confidence scoring rather than binary determinations

The leap from "this domain" to "this organization" follows the same Fellegi-Sunter pattern Jake studies in entity resolution: each corroborating data point (matching MX, matching SSL cert, matching registrant email) increases the probability of a true match while each contradictory point decreases it.

## 4. What I'd Explore Next

1. **Reverse WHOIS operationalization:** How to programmatically bootstrap from a known organization email/name to discovering all domains they control, then spidering outward through shared infrastructure.
2. **Passive DNS datasets:** Farsight DNSDB, RiskIQ PassiveTotal — the enterprise-grade sources investigators use for historical DNS correlation.
3. **BGP and ASN correlation:** Moving up the networking stack — identifying organizations by their autonomous system numbers and IP blocks.
4. **Integration with Agent Zero:** Whether the domain investigation methodology can be captured as a reusable skill (create-skill pattern) for automated domain-to-organization OSINT.

## 5. Cross-Domain Connections

- **Entity Resolution:** Domain investigation is entity resolution applied to network infrastructure — same probabilistic matching principles, same need for confidence scoring across contradictory signals.
- **Privacy/Cryptography:** The cat-and-mouse between domain privacy services and historical WHOIS mirrors the metadata-resistant protocol evolution Jake has been studying. In both domains, the defender adds a privacy layer and the investigator finds a timing-correlation or historical-snapshot bypass.
- **Sanctions Intelligence:** Iranian/Russian/North Korean sanctions evasion networks are often mapped through exactly these domain infrastructure correlation techniques — following shared SSL certs, nameservers, and IP blocks to discover hidden corporate structures.
- **Data Breach Analysis:** Registrant emails found in WHOIS history can be cross-referenced with HaveIBeenPwned and Dehashed to discover additional identities and accounts tied to the same person.

---

*Report generated during EXPLORE cycle. Next: promote to wiki DRAFT if the methodology generalizes.*
