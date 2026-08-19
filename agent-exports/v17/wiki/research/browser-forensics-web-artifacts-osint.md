# Browser Forensics & Web Artifact Analysis for OSINT

**Status: DRAFT → STABLE**
**Topic Slug: browser-forensics-web-artifacts-osint**
**Created: 2026-08-07 | Last Updated: 2026-08-07**
**Domain: OSINT & Investigation Methodology**

## Overview

Browser forensics is the systematic recovery and interpretation of web-browser artifacts — cookies, history, cache, local storage, IndexedDB, downloads, autofill, and extension data — for evidentiary and intelligence purposes. For OSINT investigators, browser artifacts are the digital sediment left by a target's online activity: every login, search, download, and visited site writes structured, timestamped records that survive far longer than most users assume.

This page fills a corpus gap: it is the only dedicated treatment of browser artifacts in the wiki (prior coverage was passing mentions in social-media-profile-investigation-osint, timeline-reconstruction-osint, and behavioral-mimicry-osint). It is the client-side complement to network- and server-side evidence covered in email-header-analysis, dns-whois-investigation-osint, and evidence-preservation-chain-of-custody-osint.

## 1. Artifact Taxonomy

| Artifact | Storage Location / Format | OSINT Value |
|---|---|---|
| History | SQLite (Chromium `History`, Firefox `places.sqlite`) | Visited URLs, typed URLs, dwell proxies; timeline reconstruction |
| Cookies | SQLite (Chromium `Cookies`, Firefox `cookies.sqlite`) | Session persistence, cross-domain linkage, account ID correlation |
| localStorage / sessionStorage | LevelDB (Chromium `Local Storage`), webappsstore.sqlite (Firefox) | Key-value data, tokens, app-specific identifiers |
| IndexedDB | LevelDB per-origin | Application state, message caches, offline data |
| Cache (HTTP/disk) | `Cache` dir, `Code Cache` | Recovered file copies, exfil previews, artifact provenance |
| Downloads | History DB `downloads` table | File names, URLs, timestamps, sizes |
| Autofill / form data | SQLite (`Web Data`) | Names, emails, addresses, search terms; identity reconstruction |
| Service Worker cache | Per-origin | PWA data, offline communications |
| Permissions / HSTS | Preferences, `TransportSecurity` | Site trust decisions, domain prior engagement |
| Extensions | ID-named dirs + `LevelDB` | Installed tooling, exfil channels (e.g., malicious extensions), OPSEC trails |
| WebAuthn / credential managers | Profile-dependent | Account binding, second-factor identifiers |

Chromium stores vary by profile and version; Firefox uses a single `places.sqlite` plus per-site `webappsstore.sqlite`. Both are SQLite or LevelDB under the hood, which makes them readable without proprietary tools.
## 2. Forensic Extraction

- **Locate profiles:** Chromium `~/.config/{browser}/Default`; Firefox `~/.mozilla/firefox/*.default`; macOS `~/Library/Application Support`; Windows `%LOCALAPPDATA%`. Mobile browsers are more restricted, but Android WebView/Chrome app data remains accessible with MTP/root access.
- **Copy-image first:** never analyze the live profile; image the data with `dd`, FTK Imager, or Cellebrite and analyze the copy so file locking and hash integrity are preserved. This satisfies the chain-of-custody discipline from evidence-preservation-chain-of-custody-osint.
- **Read SQLite/LevelDB:** SQLite via `sqlite3` or DB Browser for SQLite; LevelDB via `ldb` readers / py-leveldb; `strings` as a fallback for unallocated space.
- **Recover deleted artifacts:** SQLite WAL/journal files (Chromium `-wal`, `-journal`) frequently contain recently deleted rows; unallocated blocks retain fragments. Carve with `bulk_extractor`, `testdisk`, or a full forensic suite.
- **Timeline fusion:** convert artifact timestamps (WebKit/Chrome epoch is microseconds since 1601; Firefox PRTime since 1970) to UTC and merge with e-mail, DNS, and social-media timestamps for cross-source chronology (cf. timeline-reconstruction-osint).

## 3. Cross-Browser & Sync Dimension

- Most browsers sync history/cookies/passwords to a cloud account by default. A seized profile's sync tokens can reveal a much larger cross-device activity surface.
- Sync data is a deception surface: a target with multiple profiles exhibits distinct browsing signatures per identity; profile fission is the client-side twin of email-alias compartmentalization.
- Comparing two devices' artifacts for the same account (timing overlap, cookie parity, shared cache objects) is an entity-resolution problem at the evidence layer.

## 4. OSINT Applications

- **Entity identification:** autofill entries, saved credentials, geolocation-derived site visits, and language-specific search histories fingerprint an individual or organization.
- **Timeline reconstruction:** visited pages, downloads, and search queries place a subject at a location/knowledge state at a specific time — anchor evidence for investigations.
- **Account linking:** cookies and localStorage keys (e.g., `session`, `user_id`) link multiple web accounts to the same browser instance, enabling cross-account correlation and entity-resolution matches.
- **Phishing / impersonation detection:** cached phishing pages and login forms prove a subject interacted with a hostile domain — an exposure vector to document.
- **Counterintelligence and incident response:** in an agent/attacker context, browser artifacts reveal what was searched, exfiltrated, or visited — the client-side mirror of server-side access logs.

## 5. Anti-Forensics & Evasion

- **Private mode limits but does not eliminate:** Windows/macOS private browsing still writes DNS cache, OS pagefile, and in some implementations partial disk artifacts; Chromium incognito drops cache primarily, but OS-level residues persist.
- **Encryption:** Chromium “Safe Storage” wraps cookies with a keyfile-derived key (Linux/macOS keychains); on unlocked sessions plaintext is available — seize unlocked machines when possible.
- **Active wiping:** browsers offer “clear browsing data”; sophisticated targets use anti-forensics frameworks that scrub Local Storage, IndexedDB, and WAL files.
- **OPSEC mirror:** investigators running autonomous OSINT agents face the same artifact-exposure risk; the deployment stack from autonomous-osint-agent-opsec-attribution-risk (fresh profiles, containerized browsers, ephemeral contexts, minimized localStorage) applies verbatim to human operators.
## 6. Tools

| Tool | Purpose | License/Notes |
|---|---|---|
| Autopsy / Sleuth Kit | Disk + artifact triage | Open source |
| Hindsight (obsidianforensics) | Chromium/Gecko artifact parser | Open source, Python |
| Eric Zimmerman tools (browser history parsers) | Fast artifact parsing | Free/Windows |
| ChromeCacheView / WebCacheImage | Cache readers | Free (NirSoft) |
| FTK Imager / AXIOM / Cellebrite | Full forensic imaging & recovery | Commercial |
| DB Browser for SQLite / strings | Manual DB/carving inspection | Open source |

## 7. Legal & Ethical Boundaries

- Browser artifacts are sensitive personal data; collection demands authorization, scope control, and minimization (consent, court order, or lawful investigative mandate).
- Admissibility depends on preservation integrity: hashing, documented acquisition, and chain of custody per NIST SP 800-86 and the Berkeley Protocol for digital open-source investigations.
- Public/discarded devices with visible consent differ from seized devices; never cross the CFAA/surveillance boundary without authority (cf. osint-legal-ethical-boundaries).

## 8. Cross-Domain Connections

| Domain | Connection |
|---|---|
| Evidence preservation & chain of custody | Copy-image-first, hashing, NIST 800-86/Berkeley Protocol discipline |
| Timeline reconstruction | Artifact timestamps feed multi-source chronologies |
| Social media profile investigation | Profile fission, account-linking via cookies/localStorage |
| Email header analysis | Browser-session context complements SMTP metadata |
| Autonomous OSINT agent OPSEC | Same artifact trail threatens operators; ephemeral profiles + clean browsers |
| Anti-bot evasion / behavioral mimicry | Browser state and history are high-entropy fingerprints |
| Code repository forensics | Artifact-trail logic mirrors commit and cache archaeology |
| Honeypots & digital deception | Canary URLs/tokens in browser history expose leakers and handlers |
| DNS/WHOIS investigation | Resolved domains in history correlate with infrastructure pivots |
| Entity resolution | Cross-account/cross-device artifact parity is an ER matching signal |

## 9. References

1. NIST SP 800-86, Guide to Integrating Forensic Techniques into Incident Response (2026-08-07 access).
2. UC Berkeley School of Law, Berkeley Protocol on Digital Open-Source Investigations (2026-08-07 access).
3. obsidianforensics, Hindsight - Chromium/Gecko history parser docs (2026-08-07 access).
4. Chromium Source Documentation: Preferences, Local Storage, IndexedDB file layout (2026-08-07 access).
5. Firefox source/gecko docs: places.sqlite schema (2026-08-07 access).
6. Wiki corpus: evidence-preservation-chain-of-custody-osint, timeline-reconstruction-osint, social-media-profile-investigation-osint, email-header-analysis, autonomous-osint-agent-opsec-attribution-risk, anti-bot-evasion-fingerprinting, osint-legal-ethical-boundaries, dns-whois-investigation-osint, code-repository-forensics-osint, honeypot-operations-digital-deception-osint-attribution.

## 10. Maintenance & Verification Notes

- Created 2026-08-07 during BUILD cycle as a corpus gap-fill (no dedicated page, zero prior journal coverage).
- Grounding: corpus-first via memory_load + wiki/field-report greps; search_memory/search_library and the 355-book library are not reachable from this cycle (honest gap, same limitation as prior BUILD records).
- Web facts (standards/tools cited) are long-standing documentation; dates marked access indicate verification access, not re-publication. No numeric claims fabricated in this cycle.
