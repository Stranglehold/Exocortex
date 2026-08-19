# Field Report: Domain WHOIS & DNS Investigation for Organization Identification

**Date:** 2026-05-26
**Agent:** Agent Zero (EXPLORE cycle)
**Topic:** Domain WHOIS & DNS investigation as OSINT methodology for entity resolution

---

## 1. What I explored

I researched current (2025-2026) best practices for domain WHOIS and DNS investigation as an OSINT discipline, focusing on how investigators attribute domains to organizations and individuals. I drew on three primary sources:

- **WhoisFreaks' "Mastering WHOIS OSINT"** (updated April 2026) — comprehensive workflow for domain and IP attribution
- **Espectrosint's "Domain Investigation with OSINT: DNS, WHOIS & Beyond"** (April 2026) — layer-by-layer approach covering SSL, CT logs, and tech stack fingerprinting
- **Digging DNS's "How I Investigate a Domain Name"** (updated July 2025) — practitioner checklist with specific tools and OPSEC considerations

I also cross-referenced with the broader OSINT BIBLE 2026 guide and ShadowDragon's OSINT tools catalog.

---

## 2. What I found

### The structured investigation chain

All three sources converge on the same pipeline, executed sequentially but with recursive pivoting:

1. **Current WHOIS** — extract registrant email/organization, registrar, nameservers, creation/expiry dates
2. **Historical WHOIS** — recover pre-GDPR (pre-May 2018) unredacted registrant data
3. **Reverse WHOIS** — find all domains registered by that email/org name
4. **DNS enumeration** — A/AAAA (hosting IP), MX (email provider), TXT (SPF + third-party verification tokens), NS (nameserver fingerprinting), CNAME (service dependencies)
5. **Passive DNS / historical DNS** — trace IP and nameserver changes over time
6. **Certificate Transparency (CT) logs** — crt.sh query for SANs and organization-named certificates
7. **IP WHOIS + geolocation** — identify hosting provider, match against registrant claims
8. **Reverse DNS / co-hosting** — find other domains on same IP
9. **Threat intel cross-reference** — VirusTotal, AbuseIPDB, Shodan for known maliciousness
10. **Web archives + page source** — Wayback Machine, Google Analytics/AdSense ID tracking

### Post-GDPR adaptation

GDPR redacted ~85% of .com/.net WHOIS records after May 2018, but investigators still extract significant intelligence from unredacted fields:

- **Registrar choice** is itself a signal (budget registrars like Namecheap/Porkbun \u2260 premium like MarkMonitor/CSC)
- **Registration timing** (domain created 1-3 days before a phishing campaign)
- **Nameserver fingerprinting** is the most reliable pivot — threat actors change nameservers less often than registrant details
- **Domain status codes** (serverHold = registry suspension; pendingDelete = deletion queue)
- **Historical snapshots** from WhoisXML API, DomainTools, WhoisFreaks (3.7B records back to 1986)

### The TXT record goldmine

This is the single most underrated OSINT data source. Organizations add TXT records to verify third-party services, and these tokens broadcast their entire vendor stack:

- `google-site-verification=...` — Google Search Console
- `facebook-domain-verification=...` — Meta Business Suite / Facebook Ads
- `hubspot-domain-verification=...` — HubSpot CRM
- `atlassian-domain-verification=...` — Jira/Confluence
- `stripe-verification=...` — Stripe payment processing
- `v=spf1 include:_spf.google.com ~all` — Google Workspace

These records are never scrubbed. A single `dig TXT example.com` can reveal 5-15 SaaS vendors a company uses — valuable for social engineering assessment, competitive intelligence, and attack surface mapping.

### CT logs as WHOIS bypass

When WHOIS is fully redacted, Certificate Transparency logs (RFC 9162) provide an independent pivot. Certificates issued to "Acme Corp" covering 50+ domains expose infrastructure even when WHOIS shows privacy protection. crt.sh provides free CT log search by domain, organization name, or email.

### OPSEC considerations

- Use isolated research environments (VM, cloud browser isolation) — don't query from corporate IPs
- Prefer passive DNS services over active `dig` queries to avoid leaving resolver logs
- Use API access for bulk pivots rather than browser-based lookups (less fingerprintable)
- Understand legal boundaries: active scanning vs. passive observation differ by jurisdiction

---

## 3. What I think is interesting

### The convergence with entity resolution

This is the cross-domain connection that matters. The WHOIS\u2192DNS\u2192CT log pivot chain is essentially a specialized entity resolution pipeline applied to internet infrastructure. You're taking heterogeneous records (WHOIS text, DNS zone data, SSL certificates, threat intel feeds) and resolving them to a single real-world entity. The algorithmic challenges are identical: fuzzy matching of organization names, handling of privacy proxies as "noise," deduplication of infrastructure clusters.

**Implication for the Palantir thesis:** A platform that ingests domain registration data, DNS records, CT logs, and passive DNS into a unified ontology could perform automated attribution at scale. The trick is cross-referencing the registrant email from a historical snapshot against data breach corpuses (HIBP, Dehashed) to unmask the human behind the privacy service.

### TXT records as passive reconnaissance

Nobody is talking about TXT record leakage in the mainstream OSINT discourse the way they talk about WHOIS or Shodan. Yet `dig TXT` on any corporate domain is a completely passive query that reveals the SaaS supply chain. This feels like the kind of asymmetric intelligence that professional investigators hoard while amateurs chase WHOIS privacy red herrings.

### The nameserver persistence insight

Nameservers are stickier than registrant details because changing them requires DNS propagation and carries operational risk. This makes nameserver fingerprinting the single strongest infrastructure pivot — stronger than shared IP, stronger than registrant email (which gets rotated or privacy-protected). If you can cluster domains by nameserver set + registration time window, you've got a high-confidence attribution even when every other field is redacted.

---

## 4. What I'd explore next

1. **Automated nameserver clustering** — write a script that, given a seed domain, traverses reverse WHOIS + passive DNS to build an infrastructure graph and scores cluster confidence
2. **TXT record enumeration at scale** — what's the distribution of SaaS vendors across the Fortune 500, and what does that reveal about enterprise tech stacks?
3. **CT log \u2192 Breach data pipeline** — automate the chain: CT log org name \u2192 registrant email search \u2192 HIBP/Dehashed \u2192 real identity
4. **Comparison of paid WHOIS history services** — WhoisXML API vs. DomainTools vs. WhoisFreaks for historical coverage depth on suspicious domains

---

## 5. Cross-domain connections

- **Entity Resolution (core interest):** WHOIS/DNS investigation is entity resolution applied to internet infrastructure. The fuzzy matching, deduplication, and graph clustering challenges are isomorphic.
- **OSINT Methodology:** This domain investigation pipeline exemplifies disciplined OSINT: structured workflow, source cross-validation, OPSEC awareness, and chain-of-custody documentation.
- **Privacy/Cryptography:** GDPR's impact on WHOIS data availability is a case study in the tension between privacy rights and investigative transparency. CT logs and passive DNS emerged as workarounds — a pattern worth studying.
- **Data Breach Analysis:** The registrant email \u2192 HIBP pivot is a concrete integration point between domain investigation and breach corpus analysis.
