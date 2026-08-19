# DNS & WHOIS Investigation for OSINT Entity Resolution

**Status: STABLE**
**Created: 2026-07-04**
**Last Updated: 2026-07-04**
**Lines: ~210**

---

## 1. Overview

DNS and WHOIS investigation is a foundational OSINT technique for identifying individuals, organizations, and infrastructure relationships during entity resolution. By combining current and historical registration data with DNS record analysis, passive DNS, certificate transparency logs, and pivoting techniques, an investigator can build a comprehensive profile of who owns online infrastructure, how it is used, and what other entities it is related to.

Domain OSINT is passive reconnaissance of publicly available data. It does not require authorized access to target systems, but it demands operational security awareness and strict adherence to legal boundaries.

---

## 2. WHOIS: Current and Historical Registration Data

WHOIS provides the registration record attached to a domain: who registered it, through which registrar, and when. Since GDPR-driven privacy redaction, registrant PII is rarely visible in current records, but other fields remain critical.

### Key Fields to Analyze
- **Creation Date**: A domain registered days ago running a credential-gathering page is a phishing tell. Age is the cheapest, most reliable signal in domain triage. (VisualNotes, 2026)
- **Expiration Date**: One-year registration suggests lower commitment; multi-year signals long-term intent. (DiggingDNS, 2025)
- **Updated Date**: A recent update may indicate registrar change, registrant info change, or nameserver change -- worth chasing historic records.
- **Registrar & Nameservers**: These tend to repeat across domains run by the same operator. Patterns are a high-value pivot signal.
- **Status Codes**: ClientHold, pendingDelete, redemptionPeriod -- interpret per ICANN EPP Status Code definitions.

### Historical WHOIS
Pre-redaction snapshots may reveal old email addresses, organization names, or physical addresses no longer visible in current records. Gaps in registration history (deletion and re-registration) almost certainly indicate a change in ownership. (DiggingDNS, 2025)

### Tools
- **ICANN Lookup** (authoritative TLD-level data)
- **DomainTools WHOIS** (commercial, largest historical dataset)
- **Whoxy.com** (free, decade-plus historical records)
- **WhoisXMLAPI, WhoisFreaks** (limited free, paid for full history)
- **CentralOps, client.rdap.org** (port 43 and RDAP lookups)

---

## 3. DNS Enumeration

DNS records map domain infrastructure. Collect records from multiple public resolvers (8.8.8.8, 1.1.1.1) and authoritative nameservers to catch sync discrepancies.

### Record Types and What They Reveal
- **A / AAAA**: IPv4/IPv6 addresses. Shared hosting or CDN reuse can link unrelated domains.
- **MX**: Mail servers. If they do not match the claimed organization, that is a red flag.
- **NS**: Authoritative nameservers. Often the fastest way to identify DNS/security vendors and operator patterns.
- **TXT**: Domain verification strings, SPF policy, Google Workspace/Microsoft 365 tokens -- each narrows down the vendor stack.
- **CNAME**: Service dependency aliases (e.g., Firebase, Heroku, AWS S3). The target is a high-value pivot point.
- **CAA**: Restricts which Certificate Authorities can issue certs; hints at internal PKI practices.
- **SOA**: Zone administration metadata; serial number often includes a date of last update.

### Tools
- **dig** (command-line) / **digwebinterface.com**
- **DNSChecker, MXToolbox, ViewDNS.info**
- **SecurityTrails, DNSdumpster**

---

## 4. Email Security Posture (SPF, DKIM, DMARC)

Email authentication records are a quick read on organizational infrastructure maturity and spoofing vulnerability.

- **SPF**: Which servers are authorized to send mail. Reveals additional IPs and domains.
- **DKIM**: Cryptographic signing of outbound mail.
- **DMARC**: Policy for SPF/DKIM failures. A domain on p=none for years is meaningfully easier to spoof.

### Tools
MXToolbox, Dmarcian, EasyDMARC, Mail-Tester

---

## 5. Subdomain Enumeration via Certificate Transparency

Every publicly trusted SSL certificate is logged permanently in Certificate Transparency (CT) logs. Since most subdomains eventually acquire an SSL cert, CT logs are the highest-yield passive subdomain discovery method.

The practical workflow: pull every certificate for a root domain, extract Subject Alternative Names, and you have a subdomain list built entirely from public records -- no active scanning required. This is where forgotten infrastructure surfaces: staging., dev-api., oldvpn., internal-test. -- subdomains running unpatched software years behind production. (VisualNotes, 2026)

### Tools
- **crt.sh** (primary; use %.example.com wildcard search)
- **Censys Search, SecurityTrails**
- **RapidDNS, VirusTotal, AlienVault OTX**
- **Phonebook.cz, CertSpotter**

---

## 6. Historical Reconnaissance (Internet Archive)

The Wayback Machine stores snapshots going back decades. This provides access to: deleted pages (old staff directories, pricing, admin panels), documents briefly public before retraction, and earlier site versions revealing rebrands, ownership changes, or pivots. Comparing current vs. archived versions is often how compromised/defaced pages are caught. (VisualNotes, 2026)

### Tools
- **archive.today / archive.org/web**

---

## 7. Passive DNS and Historic DNS

- **Historic DNS**: Snapshots of DNS configuration at a point in time, often from zone files or active dig queries.
- **Passive DNS**: Observations of actual DNS resolutions seen by sensors worldwide -- captures non-public subdomains that were actively used.

### Key Sources
| Type | Tools |
|------|-------|
| Historic DNS | ViewDNS.info, DNS History, WhoisFreaks, Complete DNS, WhoisXMLAPI |
| Passive DNS | DomainTools DNSDB (commercial, original), SecurityTrails (freemium), CIRCL (free, abuse-focused), VirusTotal (free, security-focused), Zetalytics, Spamhaus (B2B/paid) |

---

## 8. Pivoting Techniques

Effective domain investigation chains small facts into larger patterns. After initial data collection, pivot across these techniques:

### Reverse Lookups
Passive and historic DNS providers allow pivoting on an IP, mailserver, or nameserver to find all other hostnames using it. Be aware: reverse lookups returning hundreds of records are on massive shared infrastructure (e.g., GoDaddy domaincontrol.com) and are likely dead ends. A handful of domains sharing the same unique IP in the same time window is a strong signal of relationship. (DiggingDNS, 2025)

### Tracking ID Correlation
Shared Google Analytics IDs (UA-XXXXXXX, G-XXXXXXXXXX) or AdSense publisher IDs can link apparently unrelated domains. Often the fastest way to tie a network of scam sites to one operator. (VisualNotes, 2026)

### Google Dorking
Targeted search operators surface indexed-but-unintended content:
- site:example.com filetype:pdf
- site:example.com intext:password
- site:example.com intitle:index.of

### SSL Certificate Intelligence
Beyond subdomain discovery: certificate issuer, validity window, and reuse across IPs can connect infrastructure with no obvious DNS relationship. (VisualNotes, 2026)

### Zone Transfer Testing (AXFR)
A misconfigured nameserver that allows anonymous AXFR transfers exposes the entire internal DNS zone in a single request. Still shows up often enough to stay on every recon checklist.

### Reverse Image & Favicon Searches
- **Image search**: Grab logos/unique images, run through Google Images or TinEye to find other sites using the same assets.
- **Favicon hash**: Hash the favicon.ico file, search Shodan with http.favicon.hash filter -- finds cloned pages where the operator reused the icon. (DiggingDNS, 2025)

### Source Code & Social Media
- View page source for HTML comments, analytics IDs, social media links, unique file paths.
- Search Twitter/X, Reddit, and Telegram for domain mentions -- Google does not index these conversational surfaces.

---

## 9. Cloud Storage Exposure

Misconfigured S3 buckets, Azure blobs, and GCP storage are common exposure vectors. Search bucket-naming conventions tied to the organization against public bucket indexes, then check permissions on anything that resolves. (VisualNotes, 2026)

### Tools
- **GrayhatWarfare** (public bucket index)
- **S3Scanner** (permission testing)

---

## 10. Breach Data Correlation

Breach databases surface email addresses, usernames, and exposed credentials tied to accounts registered under a domain -- useful for understanding organizational exposure independent of the domain own security posture.

### Tools
- **Have I Been Pwned** (confirms exposure; does not provide raw data)
- **Intelligence X** (archived data and leak aggregation)

---

## 11. Reputation and Threat Intelligence

Check domains against abuse resources for malicious activity confirmation:
- **VirusTotal** -- Relations tab for infrastructure pivots, Community tab for researcher commentary
- **URLScan.io** -- Safe URL submission with redirect chain and technology fingerprinting
- **Blocklists** -- Spamhaus, SURBL
- **abuse.ch** -- MalwareBazaar, ThreatFox (campaign attribution)
- **Any.Run** -- Interactive sandbox

---

## 12. OPSEC and Legal Boundaries

### OPSEC for the Investigator
- Use a dedicated lookup environment (VM, cloud-isolated browser, VPN) -- WHOIS and DNS queries expose your IP.
- Do not authenticate with personal accounts; use a separate non-attributable email for sign-ups.
- Mind rate limits and ToS; aggressive automated queries can get IPs blocked.
- Log methodology, not just findings -- how each fact was obtained matters for incident reports and legal contexts. (VisualNotes, 2026)

### Legal Boundaries
Everything above relies on publicly available information. The line between OSINT and an offense:
- Finding an exposed cloud bucket is legal to observe; downloading or exfiltrating its contents without authorization is not.
- A successful zone transfer or open directory listing is a misconfiguration worth reporting, not an invitation to explore.
- Stay within defined bug bounty scope even when recon surfaces interesting adjacent assets.
- Obtain written authorization before any step beyond passive lookups.

---

## 13. Tool Inventory Summary

| Category | Key Tools |
|----------|-----------|
| Current WHOIS | ICANN Lookup, DomainTools, Who.is, WHOIS.com |
| Historic WHOIS | DomainTools, Whoxy.com, WhoisXMLAPI, WhoisFreaks |
| DNS Records | dig, DNSChecker, MXToolbox, ViewDNS.info, DNSdumpster, SecurityTrails |
| Email Authentication | MXToolbox, Dmarcian, EasyDMARC |
| Certificate Transparency | crt.sh, Censys Search, CertSpotter, RapidDNS, VirusTotal |
| Internet Archive | archive.today, web.archive.org |
| Passive DNS | DomainTools DNSDB, SecurityTrails, CIRCL, VirusTotal, Zetalytics |
| Tracking ID Correlation | SpyOnWeb, DNSlytics, HackerTarget |
| Google Dorking | Google Hacking Database (Exploit-DB), DorkGPT |
| Zone Transfer Testing | HackerTarget, ViewDNS.info, DNSChecker |
| Cloud Storage | GrayhatWarfare, S3Scanner |
| Breach Data | Have I Been Pwned, Intelligence X |
| Reputation/Threat Intel | VirusTotal, URLScan.io, Spamhaus, SURBL, abuse.ch, Any.Run, Shodan, Censys |
| Favicon Hashing | Shodan http.favicon.hash, favicon hash calculators |

---

## 14. Cross-Domain Connections

1. **Entity Resolution**: DNS/WHOIS attributes map directly to Fellegi-Sunter probabilistic matching fields -- domains, IPs, email addresses, registrant names, and timestamps are entity attributes.
2. **Metadata Analysis OSINT**: WHOIS and DNS metadata extraction follows the same principles as EXIF/DOCX metadata analysis -- timestamps, software fingerprints, and embedded identifiers.
3. **HUMINT Tradecraft -> OSINT**: Source reliability rating (Admiralty Code) applies to DNS data sources; registry is A-rated (official source), passive DNS providers are B-F rated based on sensor coverage.
4. **Influence Operations Detection**: Tracking ID correlation and favicon hashing can expose sockpuppet networks and coordinated inauthentic behavior infrastructure.
5. **Social Media Profile Analysis**: DNS/WHOIS-derived email domains and usernames seed social media searches and account correlation.
6. **Financial Intelligence**: Domain registration payment methods and registrar patterns link to financial trails through cryptocurrency forensics and corporate registries.
7. **Intelligence Failure Analysis**: Missing registration gap analysis is structurally isomorphic to intelligence source gap failures -- assuming continuity where there is none.
8. **Counterintelligence**: Deceptive registration (privacy services, false WHOIS data) requires the same structured analytic techniques used for counter-deception analysis.
9. **Open-Source OSINT Tools Survey**: This page is the DNS/WHOIS layer within the broader seven-layer OSINT toolkit taxonomy.

---

## 15. References

1. VisualNotes. (2026). How to Investigate Any Domain: A Practical OSINT Workflow. visualnotes.tech
2. DiggingDNS. (2025). How I Investigate a Domain Name. diggingdns.com
3. OSINT4ALL. (n.d.). Tools for Domain, DNS, and Web Infrastructure Research. osint4all.com
4. ICANN. (2026). EPP Status Codes. icann.org
5. CIRCL. Passive DNS project. circl.lu
6. Have I Been Pwned. haveibeenpwned.com
7. VirusTotal. virustotal.com
8. crt.sh Certificate Transparency Search. crt.sh
9. Internet Archive Wayback Machine. web.archive.org
10. GrayhatWarfare Public Bucket Search. grayhatwarfare.com
