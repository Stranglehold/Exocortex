# Field Report: Domain WHOIS & DNS Investigation — Live Techniques for Organization Identification

**Date:** 2026-05-28
**Topic:** domain-whois-dns-investigation
**Cycle Type:** EXPLORE
**Web search availability:** Unavailable (search_engine and DuckDuckGo returned empty)

---

## 1. What I Explored

This cycle investigated the practical application of Domain WHOIS and DNS investigation techniques for identifying organizations behind internet-accessible services. The existing wiki page provides a comprehensive technical reference, but no dedicated field report existed for this topic. This cycle bridges theory to practice by running live terminal-based WHOIS/DNS queries and mapping the investigation pivot chain to real tools and data.

## 2. What I Found

### 2.1 Live Investigation Results

Two target domains: `example.com` (IANA-reserved) and `iana.org` (Internet Assigned Numbers Authority).

**example.com WHOIS:** Registrar RESERVED-Internet Assigned Numbers Authority (IANA ID 376), created 1995-08-14, expires 2026-08-13, nameservers ELLIOTT.NS.CLOUDFLARE.COM and HERA.NS.CLOUDFLARE.COM, DNSSEC signedDelegation, triple server lock (clientDeleteProhibited/TransferProhibited/UpdateProhibited).

**iana.org DNS+RDAP:** A record 192.0.43.8, MX mail.iana.org (192.0.43.6), SPF strict policy (ip4:192.0.43.6 ip4:192.0.43.7 -all), DMARC p=none (monitoring only), SOA ns.icann.org hostmaster.icann.org. RDAP returned structured JSON with entity handles and vCard contacts. DNS-over-HTTPS successfully resolved via Google Public DNS.

### 2.2 Investigation Pivot Chain (Validated)

1. ENTRY POINT: Domain/email/IP
2. WHOIS/RDAP: Registration metadata, nameservers, dates
3. DNS ENUMERATION: A/AAAA, MX, NS, SOA, TXT via dig
4. NAMESERVER PIVOT: Reverse lookup for co-hosted domains
5. IP ANALYSIS: Geolocation, ASN, CIDR
6. PASSIVE DNS: Historical IP resolutions
7. SSL CERTIFICATES: Certificate Transparency logs
8. ENTITY RESOLUTION: Link to known organizations
9. CROSS-VALIDATION: Social media, breach databases, corporate registries

## 3. What I Think Is Interesting

**RDAP Is the Present, Not the Future.** RDAP specifications were published in 2015. As of 2026, RDAP adoption is complete at the registry level, but many OSINT tools still teach WHOIS first. The live `whois` command actually queries RDAP behind the scenes — a compatibility layer masking the transition. RDAP's JSON output is machine-readable with standardized error codes and differentiated access.

**DMARC as Organizational Fingerprint.** iana.org's DMARC record (p=none) means the domain isn't enforcing anti-spoofing. For a critical internet governance organization, this signals that DMARC enforcement is not universal. In investigations, p=reject signals mature security posture; p=none suggests monitoring phase.

**DNSSEC as Dual-Use Signal.** example.com has DNSSEC signed. In investigations, DNSSEC status serves two purposes: confirming DNS response authenticity, and — when absent on a financial/government domain — flagging suspicion.

## 4. What I'd Explore Next

1. Passive DNS integration via DNSDB/VirusTotal/SecurityTrails API
2. Certificate Transparency automation (crt.sh query + SAN extraction + organization cross-reference)
3. Nameserver co-hosting analysis — highest-leverage pivot in the investigation chain
4. Email-to-domain forensics pipeline: email headers → domain → nameservers → hosting provider
5. GDPR redaction workarounds: RDAP differentiated access, registrar law enforcement portals, Wayback Machine domain purchase history

## 5. Cross-Domain Connections

| Connection | Domain | Mechanism |
|-----------|--------|-----------|
| Entity Resolution | Data Aggregation | Domain registrant → corporate registry cross-reference. Same entity appears as registrant, SSL O= field, ASN org name, corporate registry entry — requiring Fellegi-Sunter weighted matching |
| Email Forensics | OSINT Investigation | Email headers contain Received-SPF and DKIM results referencing domains. WHOIS on those domains reveals sending infrastructure owner — closing the loop between email header analysis and domain investigation |
| IP Geolocation | OSINT Investigation | A/AAAA records produce IPs. IP geolocation → ASN → organization name. DNS is the bridge between domain investigation and IP-based identification |
| Data Breach Analysis | Identity Linkage | Breach databases contain email addresses. MX record lookup reveals mail hosting provider — confirming whether email belongs to an organization (matches MX) or is personal (Gmail/Yahoo) |
| Anti-Bot Evasion | Web Research | Cloudflare-protected domains reveal registrar but not hosting provider via WHOIS — requiring passive DNS or CT logs to bypass |
| Counterintelligence Analysis | History of Intelligence | Domain registration patterns form a temporal signature. CI analysis frameworks can distinguish infrastructure patterns of APT29, Lazarus, or legitimate organizations |

---

*Field report written during EXPLORE cycle (May 28, 2026). Web search was unavailable; findings derived from live terminal investigation and existing wiki knowledge. Primary contribution: demonstrating domain investigation techniques are executable within the Agent Zero container without external API dependencies.*
