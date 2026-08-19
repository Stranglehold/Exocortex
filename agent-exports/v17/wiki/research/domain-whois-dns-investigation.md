# Domain WHOIS & DNS Investigation for Organization Identification

**Status: STABLE**
**Created: 2026-07-04**
**Last Updated: 2026-07-04**

## Summary
Domain WHOIS and DNS investigation is a foundational OSINT technique for identifying individuals and organizations behind domain registrations, mapping infrastructure, and uncovering relationships between entities through shared hosting, nameservers, registration patterns, Certificate Transparency logs, and tracking ID correlation. This page covers the complete investigation workflow from initial WHOIS lookup through DNS enumeration, passive intelligence gathering, and entity resolution integration.

---

## 1. WHOIS Investigation

### 1.1 Protocol and Data Model
WHOIS protocol (RFC 3912) operates as a plain-text query-response system on port 43. RDAP (Registration Data Access Protocol, RFC 7480-7485) is the structured JSON-based successor, mandated for all gTLD registries by ICANN. RDAP supports authentication for accredited access to otherwise-redacted fields, producing machine-parseable output. Key WHOIS fields for investigation:

| Field | OSINT Value |
|-------|------------|
| Registrant email/organization | Primary identity pivot for reverse WHOIS |
| Registration date | Age-based triage (3-day-old "bank login" domains = phishing) |
| Expiration date | Domain lifecycle analysis |
| Nameservers | Infrastructure pivot — more stable than registrant data |
| Registrar | Pattern recognition across campaigns |
| Status codes | clientHold, pendingDelete — domain state intelligence |

### 1.2 WHOIS vs RDAP Data Consistency
Research by Fernandez et al. (2024) analyzing 164 million WHOIS and RDAP records across 55 million domains found that 7.6% of domains show inconsistent data on critical fields including IANA ID, creation dates, and nameservers. Investigators should cross-reference both protocols when attribution is contested.

### 1.3 Historical WHOIS
GDPR enforcement (May 2018) redacted most personal data from public WHOIS. Historical WHOIS databases provide pre-GDPR snapshots and registration change timelines:
- **Pre-2018 snapshots**: Full registrant name, email, organization
- **Post-2018 value**: Nameserver changes, registrar transfers, privacy protection shifts
- A domain switching to privacy service immediately before a known attack date is a high-signal indicator

### 1.4 Tools

| Tool | Type | Key Capability |
|------|------|---------------|
| `whois` (CLI) | Direct query | RFC 3912 lookup |
| ICANN Lookup | Free web | Authoritative gTLD data |
| DomainTools | Commercial | Historical WHOIS, reverse WHOIS, Iris investigation platform |
| WhoisXML API | Commercial | Bulk WHOIS, reverse WHOIS, DNS history |
| SecurityTrails | Freemium | Historical DNS, WHOIS, reverse DNS, domain associations |
| WhoisFreaks | Commercial | Live + historical WHOIS, reverse WHOIS, IP WHOIS, bulk API |
| ViewDNS.info | Free | WHOIS, reverse IP, DNS tools |
| whois.domaintools.com | Free web | Current WHOIS lookup |

---

## 2. DNS Investigation

### 2.1 DNS Record Types for OSINT

| Record | OSINT Value |
|--------|------------|
| A/AAAA | Infrastructure identification — hosting IP, CDN detection |
| MX | Mail server infrastructure — shared MX across domains = strong link |
| NS | Authoritative nameservers — shared hosting/operator detection |
| TXT (SPF) | Sender Policy Framework — authorized mail servers, domain verification strings |
| TXT (DKIM) | Cryptographic signing — organizational identifiers in selector |
| TXT (DMARC) | Domain-based Message Authentication — policy posture (none/quarantine/reject) |
| TXT (other) | SaaS verification tokens (Google Workspace, Microsoft 365, Stripe, etc.) |
| SOA | Zone serial number (update frequency patterns), admin email (RNAME) |
| CNAME | Service dependency mapping — reveals CDN, hosting, or platform providers |
| PTR | Reverse DNS — IP-to-hostname, often reveals hosting provider |
| CAA | Certificate Authority Authorization — PKI practices, approved CAs |

### 2.2 Email Security Posture (SPF / DKIM / DMARC)

Email authentication records serve as both security posture indicators and OSINT leads:
- **SPF**: Lists authorized outbound mail servers — reveals email provider (Google, Microsoft, Proofpoint, Mimecast)
- **DKIM**: Selector values may contain organizational identifiers
- **DMARC**: Policy level (`p=none` vs `p=reject`) indicates organizational security maturity. A domain with `p=none` for years is meaningfully easier to spoof — relevant for phishing campaign assessments

Tools: MXToolbox, Dmarcian, EasyDMARC, Mail-Tester.

### 2.3 Certificate Transparency (CT) Logs

All publicly trusted SSL certificates are permanently logged in Certificate Transparency logs. This is the highest-yield passive subdomain enumeration method:
- Extract every certificate ever issued for the root domain
- Parse Subject Alternative Names (SANs) for complete subdomain list
- Discovers forgotten infrastructure: `staging.`, `dev-api.`, `oldvpn.`, `internal-test.`
- No active scanning required — entirely passive and public-record-based

**Primary CT search tools**: crt.sh (free, unlimited), Censys Search, SecurityTrails, Google CT Search.

### 2.4 Passive DNS and Historical DNS

Farsight DNSDB, SecurityTrails, and PassiveTotal maintain historical DNS resolution data:
- Track A record changes over time (infrastructure migration, takedowns)
- Identify all domains that ever resolved to a given IP (reverse passive DNS)
- Early detection of malicious domains before mail campaigns launch (Fernandez et al., 2022 — passive DNS + SPF analysis)

### 2.5 Tools

| Tool | Type | Capability |
|------|------|-----------|
| `dig` / `nslookup` (CLI) | Direct query | Full DNS record querying |
| dns.google | Free web | Authoritative DNS resolution |
| DNSChecker | Free web | Global DNS propagation check |
| MXToolbox | Free web | MX, SPF, DKIM, DMARC, blacklist checks |
| DNSDumpster | Free | DNS recon, domain research, visual mapping |
| SecurityTrails | Freemium | DNS history, reverse DNS, passive DNS, domain associations |
| crt.sh | Free | Certificate Transparency log search |
| Censys | Freemium | Internet-wide scanning, certs, DNS, services |
| Shodan | Freemium | Internet-connected device/service discovery |
| `dnsrecon` (CLI) | Open source | DNS enumeration, zone transfer attempts, brute-force |
| `theHarvester` | Open source | Email, subdomain, DNS, and virtual host harvesting |
| osint.sh | Free web | DNS records, GA/Analytics ID correlation, historical WHOIS |

---

## 3. Extended Investigation Toolkit

### 3.1 Tracking ID Correlation

Shared identifiers embedded in page source link domains that otherwise appear unrelated:
- **Google Analytics ID** (`G-XXXXXXXXXX` or UA-XXXXXXX-X)
- **Google AdSense publisher ID** (`ca-pub-XXXXXXXXXX`)
- Pivoting via SpyOnWeb, DNSlytics, or osint.sh reveals entire domain networks
- Fraud investigators regularly tie scam site networks to single operators via shared tracking IDs

### 3.2 Google Dorking

Targeted search operators surface accidentally indexed content:
```
site:example.com filetype:pdf
site:example.com intext:"password"
site:example.com intitle:"index.of"
```
Reveals exposed backups, internal logs, directory listings, and documents uploaded without access controls. Google Hacking Database (Exploit-DB) catalogs thousands of dorks.

### 3.3 Cloud Storage Exposure

Misconfigured S3 buckets and Azure blobs are common exposure vectors. Investigation approach:
- Search bucket-naming conventions tied to target organization
- Use GrayhatWarfare, Buckets, S3Scanner for bucket discovery
- Common findings: backup files, internal docs, source code, config files with credentials

### 3.4 Wayback Machine / Web Archives

Internet Archive stores snapshots going back decades, enabling:
- Recovery of deleted pages (old staff directories, pricing, admin panels)
- Detection of rebranding or ownership pivots
- Historical content comparison for compromise/defacing detection
- Tools: web.archive.org, archive.today

---

## 4. Investigation Methodology

### 4.1 Structured Workflow (VisualNotes 2026)

1. **WHOIS lookup** → current registration data; age triage first
2. **DNS enumeration** → A, MX, NS, TXT, SOA, CNAME, CAA; full record set
3. **Email security posture** → SPF, DKIM, DMARC; organizational maturity indicator
4. **Certificate Transparency** → CT log search for subdomain discovery
5. **Historical reconnaissance** → Wayback Machine for deleted/changed content
6. **Cloud storage exposure** → bucket discovery and permission checks
7. **Tracking ID correlation** → shared analytics/ad IDs across domains
8. **Google Dorking** → accidentally indexed sensitive content

### 4.2 IP Investigation Parallel Track (WhoisFreaks 2026)

When investigating IP addresses from firewall logs, email headers, or domain A records:
1. **IP WHOIS lookup** → RIR allocation, network owner, abuse contact, CIDR block
2. **Threat intelligence cross-reference** → AbuseIPDB, VirusTotal, Shodan for known malicious activity
3. **Reverse DNS** → all domains pointing to the IP (shared hosting detection)
4. **Reverse IP/Passive DNS** → find all domains that ever resolved to the IP

### 4.3 Pivot Points and Chaining

| Pivot Source | Technique | Result |
|-------------|-----------|--------|
| Registrant email | Reverse WHOIS | All domains registered with same email |
| Organization name | Reverse WHOIS | Complete domain portfolio |
| Nameservers | Reverse NS/DNS | Domains sharing hosting infrastructure |
| IP address | Reverse IP/DNS | Co-hosted domains |
| SSL certificate SHA-1 | crt.sh, Censys | Domains sharing same cert |
| Google Analytics ID | SpyOnWeb, osint.sh | Entire domain network |
| MX record | MX lookup | Shared mail infrastructure |
| Phone number | Reverse WHOIS (normalized) | Identity linkage |

### 4.4 Entity Resolution Integration

WHOIS/DNS fields map naturally to Fellegi-Sunter probabilistic record linkage:
- **Comparison variables**: Registrant email fuzzy match, organization Jaro-Winkler, nameserver exact match, IP subnet proximity
- **Blocking keys**: Registrar × registration year, nameserver × TLD, IP /24 subnet
- **Temporal evidence**: Registration date proximity as linkage weight
- **Email normalization**: Gmail dot-stripping, plus-addressing, domain normalization

---

## 5. Cross-Domain Connections

| Connected Page | Connection |
|---------------|-----------|
| [[email-header-analysis]] | MX/SPF/DKIM/DMARC validation; email-to-domain attribution |
| [[metadata-analysis-osint]] | WHOIS as metadata extraction; EXIF comparison |
| [[knowledge-graph-construction]] | Domain-to-entity graph construction; Neo4j integration |
| [[financial-intelligence-entity-resolution]] | Domain registration patterns in fraud; shell company linkage |
| [[geolocation-osint]] | IP geolocation from A records; hosting location analysis |
| [[social-media-osint]] | Domain-to-social-profile correlation via shared identifiers |
| [[counterintelligence-analysis-frameworks]] | Infrastructure mapping for attribution; threat actor profiling |
| [[influence-operations-detection-countermeasures]] | Domain registration patterns in disinformation campaigns |
| [[data-breach-analysis-identity-linkage]] | WHOIS email correlation with breach databases (HIBP) |
| [[synthetic-data-osint]] | Synthetic WHOIS data generation for detection algorithm testing |
| [[open-source-osint-tools-survey]] | Tool coverage taxonomy; integration assessment |
| [[humint-tradecraft-osint]] | Source reliability rating (Admiralty Code) applied to WHOIS sources |

---

## 6. References

1. Fernandez, S., Hureau, O., Duda, A., & Korczynski, M. (2024). \"WHOIS Right? An Analysis of WHOIS and RDAP Consistency.\" arXiv:2406.02046. *Analysis of 164M WHOIS/RDAP records showing 7.6% field inconsistency.*
2. Fernandez, S., Korczynski, M., & Duda, A. (2022). \"Early Detection of Spam Domains with Passive DNS and SPF.\" arXiv:2205.01932. *Passive DNS + SPF configuration for pre-campaign spam domain detection.*
3. RFC 3912: WHOIS Protocol Specification
4. RFC 7480-7485: Registration Data Access Protocol (RDAP)
5. ICANN Temporary Specification for gTLD Registration Data (2018)
6. Sharma, A. (2026). \"How to Investigate Any Domain: A Practical OSINT Workflow.\" VisualNotes. *10-step domain investigation methodology covering WHOIS, DNS, CT logs, dorking, tracking ID correlation.*
7. WhoisFreaks Team (updated 2026). \"What Is WHOIS OSINT? Domain and IP Investigation Workflow.\" *7-step workflow: live WHOIS → historical → reverse WHOIS → nameserver pivot → IP WHOIS → DNS → documentation.*
8. Google Hacking Database (GHDB), Exploit-DB. *Curated Google dork collection for exposed sensitive content discovery.*
9. crt.sh — Sectigo Certificate Transparency Log Search
10. SecurityTrails — Passive DNS, Reverse DNS, Historical WHOIS, Domain Associations

---

## Verification Status
Last verified: 2026-07-04. Status: STABLE. Claims verified against public RFC specifications (3912, 7480-7485), peer-reviewed arXiv papers (2406.02046, 2205.01932), and published OSINT workflow guides (VisualNotes 2026, WhoisFreaks 2026). Cross-referenced with 11 existing Exocortex wiki pages. 10 sources, 12 cross-domain connections.
