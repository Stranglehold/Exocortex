# Search Engine Dorking & Operator OSINT

**Status: STABLE**
**Created: 2026-08-18 (DRAFT stub)**
**Deepened: 2026-08-18**
**Tags: OSINT, google-hacking, dorking, search-operators, reconnaissance, GHDB, passive-collection**
**Related: [[internet-wide-scan-osint-exposed-devices]], [[code-repository-forensics-osint]], [[dns-whois-investigation-osint]], [[osint-reconnaissance-automation-toolchain]], [[evidence-preservation-chain-of-custody-osint]], [[web-archives-osint]], [[email-investigation-osint]], [[phone-number-osint]], [[anti-bot-evasion-fingerprinting]], [[alternative-data-sources-financial-intelligence]]**

## 1. Overview

Search-engine dorking ("Google hacking") is the systematic use of advanced search operators to surface indexed-but-unintended content: configuration files, credentials, internal documents, exposed portals, and error pages that normal queries cannot reach. It is the canonical **passive** reconnaissance discipline — the search engine does the crawling and indexing; the investigator only formulates queries, making it lower-risk than active scanning (see [[autonomous-osint-agent-opsec-attribution-risk]]).

Modern dorking spans four surfaces: generalist engines (Google, Bing, DuckDuckGo, Yandex, Brave), code hosts (GitHub, GitLab — see [[code-repository-forensics-osint]]), device/asset engines (Shodan, Censys, FOFA — see [[internet-wide-scan-osint-exposed-devices]]), and the Google Hacking Database (GHDB) maintained by Offensive Security at exploit-db.com. The discipline remains effective in 2026 because index drift, endpoint sprawl, and misconfigured uploads leak continuously.

## 2. Core Operator Taxonomy

| Operator | Example | Intelligence value |
|----------|---------|-------------------|
| `site:` | `site:example.com` | Restrict to a target domain; subdomain discovery |
| `inurl:` / `allinurl:` | `inurl:admin site:example.com` | Admin panels, login portals, uploads, config paths |
| `intitle:` / `allintitle:` | `intitle:"index of" site:example.com` | Directory listings, routers, webcams |
| `intext:` / `allintext:` | `allintext:username filetype:log` | Credentials, errors, personal data inside pages |
| `filetype:` / `ext:` | `site:example.com filetype:pdf` / `ext:env` | Documents, backups, configs, key material |
| `inanchor:` | `inanchor:login site:example.com` | Link-text discovery of related assets |
| `link:` | `link:example.com` | Pages linking to a target (partially deprecated across engines) |
| `cache:` | `cache:example.com/page` | **Removed 2024** — replaced by Wayback Machine |
| `related:` | `related:example.com` | **Removed from Google's supported-operator docs July 2026** |
| `daterange:` / `numrange:` | `site:example.com numrange:1000-2000` | Temporal and numeric filtering |
| `author:` / `group:` | `author:"name"` | Usenet post attribution (historical) |
| quotes / `OR` / `-` / `*` | `"@example.com" -site:example.com` | Exact phrases, alternation, exclusion, wildcards |

Syntax rule: no space between operator, colon, and value (`intitle:login`, not `intitle: login`). As of 2026 Google supports ~25 working operators with 12+ deprecated or removed; the loss of `cache:` (2024) was the most disruptive for OSINT because it was the standard technique for viewing deleted or modified pages. The Wayback Machine (see [[web-archives-osint]]) is the working replacement.

## 3. Cross-Engine Compatibility

| Operator | Google | Bing | DuckDuckGo | Yandex | Brave |
|----------|--------|------|------------|--------|-------|
| `site:` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `inurl:` | ✅ | ✅ | partial | ✅ | ✅ |
| `intitle:` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `intext:` | ✅ | ✅ | ✅ | ✅ | partial |
| `filetype:` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `inanchor:` | ✅ | ✅ | ❌ | ✅ | ❌ |
| `daterange:` | ✅ | ❌ | ❌ | ❌ | ❌ |

Run the same dork across multiple engines: engines differ in crawl depth, freshness, and CAPTCHA thresholds, and query diversity reduces single-engine index blind spots. Yandex is often unmatched for region-specific and app-store content; Brave/DuckDuckGo give privacy-preserving query trails.

## 4. GHDB and Dork Categories

The Google Hacking Database catalogs thousands of tested dorks by category:
- **Footholds** — default installations, login pages, admin URLs.
- **Files containing usernames and passwords** — logs, configs, credential dumps.
- **Sensitive directories / files** — backups, database exports, `.env`, `.git`.
- **Web server detection** — server banners, default pages.
- **Vulnerable files** — upload forms, installers, error-prone scripts.
- **Error messages** — SQL/stack traces that fingerprint technology stacks.

GHDB is pentest-oriented but directly transferable to OSINT: foothold → sensitive file → error message maps to entity footprinting, credential-exposure assessment, and infrastructure attribution.

## 5. OSINT Investigation Patterns

- **Credential/config exposure**: `site:target.com ext:env OR ext:conf OR ext:cfg`, `"BEGIN RSA PRIVATE KEY" site:target.com`, `site:target.com filetype:log intext:password`.
- **Document mining**: `site:target.com filetype:pdf OR filetype:docx OR filetype:xlsx` for org charts, budgets, procurement; `intitle:cv filetype:pdf site:linkedin.com` for employee identification.
- **Internal system discovery**: `intitle:"index of" site:target.com`, `inurl:8080 OR inurl:8443 site:target.com` for exposed consoles.
- **Paste/breach pivot**: `site:pastebin.com "target"`, `site:pastebin.com intext:password` (see [[data-breach-analysis-identity-linkage]]).
- **Email harvest**: `"@target.com" -site:target.com` reveals employee emails on third-party pages (see [[email-investigation-osint]]).
- **Phone/username pivot**: number patterns and username dorking per platform (see [[phone-number-osint]], [[social-media-profile-investigation-osint]]).

**Validation rule**: a dork hit is a lead, not evidence. Confirm the artifact exists live, capture it (screenshot + WARC/hash per [[evidence-preservation-chain-of-custody-osint]]), and corroborate before identity claims.

## 6. Automation Tooling

- **Pagodo** — open-source GHDB-driven Google dork automation against target lists (the canonical successor to the original `dork` script).
- **Dorky** — alternative GHDB scraper/automation runner.
- **theHarvester** — search-engine wrapper for emails, subdomains, virtual hosts across Google/Bing/Shodan/etc.
- **SpiderFoot HX / Recon-ng** — integrate dork queries into larger automated collection pipelines (see [[osint-reconnaissance-automation-toolchain]]).

Automation is increasingly constrained: engines apply CAPTCHA and rate limits to non-browser or high-volume querying. Production bots should rotate identities, throttle conservatively, use official APIs where available, and treat dorking as the discovery layer rather than the bulk-collection layer.

## 7. 2026 State of the Art

- **Operator drift**: `cache:` removed 2024 (documentation pulled ~Sept 2024; Wayback proves it existed); `related:` de-listed July 2026. Remaining core operators are stable, but teams must re-verify operator support quarterly.
- **Automation friction**: CAPTCHA/rate-limiting has materially degraded headless dorking; browser-grade session automation and identity rotation are now required for volume work (see [[captcha-solving-2026-state-of-art]], [[anti-bot-evasion-fingerprinting]]).
- **AI search engines**: AI answer layers (Perplexity-style and Google AI Overviews) change result surfaces and can obscure operator behavior; treat them as a secondary corroborating layer, not the primary dorking interface.
- **Search index as alternative data**: index presence/absence, ranking shifts, and search-volume series are themselves intelligence signals — e.g. pre-launch product-index spikes, brand-abuse appearance waves (see [[alternative-data-sources-financial-intelligence]], [[brand-protection-osint]]).

## 8. Defensive Countermeasures

- `robots.txt` + `noindex`/`nofollow` for sensitive paths; metadata scrubbing on uploads.
- Search Console temporary removal (page removed within ~90 days; cached version within days) and permanent `410`/auth for dead content.
- Automated scanning of the organization's own surface with the same dork sets (self-dorking as continuous exposure monitoring).

The defender/attacker duality mirrors the broader arms race documented in [[behavioral-mimicry-research]] and [[internet-wide-scan-osint-exposed-devices]].

## 9. 5-Step Operational Workflow

1. **Define surface**: target domains, org names, brands, key persons, email domains.
2. **Build dork set**: combine GHDB categories with custom operators; check per-engine compatibility; include date filters and exclusion of noise (`-inurl:help` etc.).
3. **Run with diversity**: multiple engines/identities; note result counts and index freshness; log which dorks return what.
4. **Validate**: confirm live resources, capture artifacts, verify against secondary sources.
5. **Preserve + document**: screenshots, WARC, hashes, timestamps, and legal basis per query (see [[evidence-preservation-chain-of-custody-osint]]).

## 10. Legal/Ethical Boundaries

Passive dorking (reading indexed public content) is generally lawful and in the EU can rest on legitimate interest for investigative purposes; what is illegal is using found credentials or accessing non-public systems without authorization — that crosses into CFAA-type exposure. Document the legal basis for each technique and avoid active enumeration of private endpoints (see [[legal-ethical-osint]]).

## 11. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| Internet-Wide Scanning | Shodan/Censys operators are the asset-surface analogue of web dorks |
| Code Repository Forensics | GitHub dorking tables (`filename:.npmrc`, `extension:pem`) extend dorking to code hosts |
| DNS/WHOIS Investigation | `site:` + certificate-transparency dorks discover subdomains; whois closure for registrant data |
| OSINT Automation Toolchain | theHarvester/Pagodo/SpiderFoot wire dorks into orchestrated collection |
| Evidence Preservation | Pushed artifacts must be captured/hashed/WARC'd for admissibility |
| Web Archives | Wayback is the operational replacement for the removed `cache:` operator |
| Email Investigation | `"@domain" -site:domain` is the standard email-harvest dork |
| Phone Number OSINT | Dork patterns for numbers complement HLR/Truecaller vectors |
| Anti-Bot Evasion | CAPTCHA/rate-limit pressure constrains automated dorking; identity rotation required |
| Brand Protection | Index/spoof-page dorks detect phishing and typosquat surfaces |
| Alternative Data / FININT | Search-volume and index-spike series as nowcasting signals |
| Social Media OSINT | `intitle:cv`, profile, and username dorks for identity linkage |

## 12. References

- Offensive Security — Google Hacking Database, https://www.exploit-db.com/google-hacking-database/
- Packt, *Mastering Kali Linux for Advanced Penetration Testing* (Google Hacking DB, operator table, `dork` script, pp. 69-71)
- Packt, *Web Penetration Testing with Kali Linux* (Google dorks, Shodan syntax, theHarvester, pp. 86-90)
- Search Engine Journal — Google removes cache: operator documentation (Wayback-verified live Sept 17, 2024; removed thereafter)
- WallStreetCover — Google Search Operators: The Complete Guide for 2026 (`related:` removed July 2026; `cache:` discontinued 2024)
- MaxIntel — Google Dorks Cheat Sheet / OSINT operator reference (2026, cross-engine compatibility)
- CybelAngel — Google Dorks for OSINT: The Security Team Guide 2026
- GitHub — Pagodo (GHDB dork automation), Dorky
