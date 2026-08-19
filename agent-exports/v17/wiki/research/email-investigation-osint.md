# Email Investigation for OSINT Identity Resolution

**Status: STABLE**
**Created: 2026-07-17**
**Last Deepened: 2026-07-17**
**Tags: OSINT, entity-resolution, identity-investigation, email-forensics, digital-footprint, Fellegi-Sunter**
**Related: [[email-header-analysis]], [[phone-number-investigation-osint]], [[data-breach-analysis-osint-identity-linkage]], [[social-media-osint]], [[dns-whois-investigation-osint]], [[reverse-image-search-osint]], [[human-investigation-osint]]**

## Summary

An email address is a universal digital identifier: it serves simultaneously as an authentication credential, a communication channel, a username across hundreds of platforms, and a persistent key in entity resolution pipelines. Unlike names — which are highly ambiguous — or phone numbers — which can be recycled — email addresses are rarely reassigned, making them durable identity anchors across years of digital activity. This page covers the structured methodology for tracing an email address to the individual or organization behind it, transforming a single string into a defensible chain of identity evidence.

The core investigation framework operates across five signal layers: direct profile matches, username cross-walking, domain intelligence, breach correlation, and temporal consistency validation. Each layer provides independent corroboration; identity claims require at least two layers of positive signal with no unresolved contradictions (the OSINT Vault two-source validation matrix, 2026).

---

## 1. Email Address as an Entity Resolution Key

### 1.1 Structural Properties

| Property | OSINT Implication |
|----------|-------------------|
| **Uniqueness** | An email address maps to at most one account per service — unlike names or IPs, it serves as a natural key for cross-platform identity resolution |
| **Durability** | Email addresses persist for years; users retain primary addresses across job changes, relocations, and platform migrations — far more stable than phone numbers (45–90 day reassignment windows) |
| **Linkability** | The same email surfaces in breach databases, social profiles, domain registrations, corporate directories, code repositories, and mailing list archives — creating abundant cross-source linkage opportunities |
| **Structure** | The local-part@domain format embeds organizational affiliation in the domain component and potential username hints in the local-part |

### 1.2 Composition and Pivot Points

An email address `local-part@domain.tld` naturally decomposes into three investigation vectors:

1. **Local-part pivots:** The username fragment (`jdoe42`, `john.smith`) is frequently reused across platforms. Cross-walking the local-part through username search tools (WhatsMyName, Sherlock, Holehe) reveals social media profiles, forum accounts, and developer platforms.
2. **Domain pivots:** The domain component (`corporation.com`) reveals organizational affiliation. WHOIS history, DNS records, SPF/DKIM/DMARC configuration, SSL certificate transparency logs, and web infrastructure all provide organizational intelligence. See [[dns-whois-investigation-osint]].
3. **Full-address pivots:** The complete address is the strongest signal for direct profile matching, breach correlation, and account enumeration.

### 1.3 Fellegi-Sunter Weighting for Email Attributes

In probabilistic entity resolution frameworks (Fellegi & Sunter, 1969), an email address is treated as a high-weight matching variable:

- **M-probability (match weight):** High — email addresses are rarely shared across entities
- **U-probability (random agreement):** Very low — accidental collisions are negligible
- **Composite weight:** An email match alone can carry sufficient weight to link records, but investigators corroborate with secondary attributes (name, phone, location) to defend against spoofing and account takeover

---

## 2. Five-Layer Signal Collection Methodology

### Layer 1: Direct Profile Matching

Check whether the email address is publicly associated with a named profile across platforms:

| Tool / Method | Coverage | Notes |
|---------------|----------|-------|
| **Google Dorking** | Web-wide | `"email@example.com"` in quotes; variant: `"email@example.com" OR "local-part"` |
| **OSINT Vault Multi-Search Launcher** | 300+ sources | Batch queries across search engines, breach databases, and profile directories |
| **Holehe** | 120+ platforms | Non-intrusive account registration check — does not trigger notifications |
| **GHunt** | Google services | Extracts Google profile metadata, reviews, YouTube channels, Google Maps contributions |
| **WhatsMyName** | 400+ platforms | Username enumeration; paired with local-part cross-walking |
| **SpiderFoot** | 200+ modules | Automated OSINT with email-to-account correlation |

**Key rule:** Never attempt password resets or login attempts — these are active techniques that alert the subject and may violate CFAA or local cybercrime statutes. All OSINT email investigation must remain passive.

### Layer 2: Username Cross-Walking

The local-part of an email address is frequently reused as a handle across platforms:

1. Extract the local-part (`jdoe` from `jdoe@example.com`)
2. Generate variants: `jdoe`, `john.doe`, `johndoe`, `john_doe`, `jdoe42`
3. Run variants through username enumeration tools (WhatsMyName, Sherlock, Holehe, Namechk)
4. Validate matches by checking profile details against known attributes (name, location, avatar)
5. Document each confirmed association with source URL and timestamp

**Caution:** Username collisions are common. A matching username alone is insufficient for identity claims — it must be corroborated by profile details, temporal consistency, or cross-platform overlap.

### Layer 3: Domain Intelligence

The domain component of an email reveals organizational affiliation:

1. **WHOIS history:** Historical WHOIS records may reveal the registrant's name, organization, address, phone, and email before GDPR redaction or privacy protection. See [[dns-whois-investigation-osint]].
2. **DNS records:** MX records confirm email infrastructure; SPF/DKIM/DMARC records identify authorized mail servers and may reveal third-party email providers.
3. **Certificate Transparency logs:** SSL certificates for the domain may list administrative email addresses.
4. **Subdomain enumeration:** Subdomains (mail.example.com, autodiscover.example.com) reveal internal infrastructure.
5. **Employee email format:** Once the pattern is identified (e.g., `first.last@company.com`), investigators can generate potential addresses for other individuals within the organization.

### Layer 4: Breach Correlation

Email addresses appearing in data breaches provide a wealth of identity anchors:

| Source | Data Types Available | API / Access Method |
|--------|---------------------|---------------------|
| **HaveIBeenPwned (HIBP)** | Breach name, date, data classes | k-anonymity API (password hash prefix) |
| **Dehashed** | Passwords, usernames, IPs, phone, address, VIN | Paid API / web interface |
| **IntelX** | Dark web, paste sites, breach databases | API / web interface |
| **Constella Intelligence** | 1T+ identity records; breach + surface + dark web | Enterprise API |
| **SnusBase** | Email:password hash pairs | Web interface |
| **LeakCheck** | Breach databases | API / web interface |

Breach data provides the strongest identity signals: real names, physical addresses, phone numbers, IP addresses, and associated accounts. However, breach data timestamps are critical — a breach from 2015 may contain outdated information. See [[data-breach-analysis-osint-identity-linkage]] for the full breach investigation methodology.

### Layer 5: Temporal Consistency Validation

An email address appearing across multiple sources is meaningful only if the timeline supports identity continuity:

1. **Check account creation dates** where available (GitHub, Twitter/X, Reddit)
2. **Cross-reference with employment timelines** (LinkedIn, corporate databases)
3. **Identify account recycling indicators:** abrupt changes in name, location, or activity patterns may indicate a new owner
4. **Document timeline conflicts explicitly** — a breach record predating the subject's claimed employment should be noted as a contradiction, not discarded

---

## 3. Structured Investigation Workflow

Adopted from the OSINT Vault email investigation methodology (Hurey, July 2026):

### Phase 1: Search Set Generation
- Generate standardized Google Dork queries for the email, its domain, and local-part variants
- Record all queries in the case file for reproducibility
- Include quoted searches, site-specific searches, and filetype filters

### Phase 2: Multi-Source Collection
- Execute queries across search engines (Google, Yandex, Bing, DuckDuckGo)
- Run the email through account enumeration tools (Holehe, GHunt)
- Check breach databases (HIBP, Dehashed, IntelX)
- Query domain infrastructure (WHOIS, DNS, SSL certificates)
- Check code repositories (GitHub, GitLab code search)
- Search mailing list archives, forum posts, and paste sites

### Phase 3: Evidence Normalization
- Capture each finding with: source URL, access timestamp, evidence type, confidence level
- Flag duplicates and conflicts using the OSINT Vault Note Organizer or equivalent case management system
- Apply the two-source validation matrix: each identity claim requires at least two independent signals

### Phase 4: Pivot Expansion
- Username pivots: follow local-part handles across platforms (see [[username-investigation]])
- Domain pivots: map the organization behind the email domain (see [[dns-whois-investigation-osint]])
- Phone pivots: if breach data reveals a phone number, extend investigation (see [[phone-number-osint]])
- Social pivots: search for profiles referencing the email (see [[social-media-osint]])
- Image pivots: extract and reverse-search profile avatars (see [[reverse-image-search-osint]])

### Phase 5: Confidence Assessment and Reporting
- **High confidence:** Multiple independent sources, no conflicts, consistent timeline
- **Medium confidence:** Two independent sources, minor timeline questions, one unverified signal
- **Low confidence:** Single source, breach-only data, or timeline inconsistencies
- **Unverified:** Mention only, no corroboration — explicitly marked as unverified

---

## 4. Tool Ecosystem

| Tool | Function | Access |
|------|----------|--------|
| **Holehe** | Account registration check across 120+ platforms | Free, open-source, CLI |
| **GHunt** | Google account metadata extraction (reviews, YouTube, Maps, Photos) | Free, open-source, CLI |
| **WhatsMyName** | Username enumeration across 400+ platforms | Free, open-source, web/CLI |
| **Sherlock** | Username search across 300+ social networks | Free, open-source, CLI |
| **SpiderFoot** | Automated OSINT: 200+ modules including email-to-account, breach lookup, DNS | Free, open-source, web GUI/CLI |
| **theHarvester** | Email/domain OSINT: search engines, PGP, SHODAN | Free, open-source, CLI |
| **Recon-ng** | Modular reconnaissance framework with email modules | Free, open-source, CLI |
| **HIBP** | Breach notification (k-anonymity API) | Free (single lookup) / Paid (domain monitoring) |
| **Dehashed** | Breach database with rich metadata | Paid |
| **IntelX** | Dark web, breach, and surface web intelligence | Freemium / Paid |
| **OSINT Vault Multi-Search Launcher** | Batch query execution across 300+ sources | Paid platform |
| **EmailRep.io** | Email reputation scoring, social profiles, breach associations | Freemium API |
| **Hunter.io** | Email format discovery, domain email pattern identification | Freemium |

---

## 5. Operational Security

- **Passive-only investigation:** Never attempt password resets, login attempts, or account recovery. These are active techniques that alert the subject and may violate CFAA (18 U.S.C. § 1030) or equivalent cybercrime statutes.
- **Dedicated browser profile:** Use a clean OSINT browser environment with anti-fingerprinting protections. See [[anti-bot-evasion]].
- **VPN/Tor routing:** Route OSINT queries through anonymous infrastructure to prevent IP-based linkage back to the investigator.
- **Document access method:** Record the browser environment and network configuration used during collection.
- **Soft attribution rule:** Do not claim identity based on a single profile or breach record. Only claim what is validated by multiple independent sources.
- **Legal boundaries:** Do not access or distribute breach data beyond what is lawful in the investigator's jurisdiction. GDPR Article 14 imposes transparency obligations when processing personal data from third-party sources. See [[legal-ethical-osint]].

---

## 6. Cross-Domain Connections

| Connection | Wiki Page | Description |
|------------|-----------|-------------|
| **Email Header Analysis** | [[email-header-analysis]] | Headers reveal originating IPs, mail relays, and infrastructure — complements domain intelligence |
| **Phone OSINT** | [[phone-number-osint]] | Breach data and profiles often link email→phone; bidirectional pivot strengthens identity claims |
| **Data Breach Analysis** | [[data-breach-analysis-osint-identity-linkage]] | Primary source of email→identity linkage: breach records provide names, addresses, phones, IPs |
| **DNS/WHOIS Investigation** | [[dns-whois-investigation-osint]] | Domain intelligence for the email domain component — organizational attribution |
| **Social Media OSINT** | [[social-media-osint]] | Profile discovery and verification through platform enumeration |
| **Reverse Image Search** | [[reverse-image-search-osint]] | Profile avatar extraction and visual identity verification |
| **Entity Resolution (Fellegi-Sunter)** | [[entity-resolution-algorithms]] | Probabilistic matching framework that treats email as a high-weight matching variable |
| **Anti-Bot Evasion** | [[anti-bot-evasion]] | Browser fingerprinting and rate-limiting evasion required for scaled email OSINT collection |
| **Legal & Ethical OSINT** | [[legal-ethical-osint]] | CFAA, GDPR, and responsible disclosure boundaries for email investigation |
| **HUMINT Tradecraft** | [[humint-tradecraft-osint]] | Admiralty Code source reliability scoring applied to email intelligence signals |
| **Timeline Reconstruction** | [[timeline-reconstruction-osint]] | Temporal consistency validation for email→identity claims |
| **Username Investigation** | [[username-investigation]] | Local-part cross-walking methodology — the bridge between email and platform enumeration |

---

## 7. References

### Methodology
- Hurey, N. (2026). "Email OSINT Guide 2026 — Find Accounts & Breaches." OSINT Vault. theosintvault.io/email-osint-guide
- Fellegi, I.P. and Sunter, A.B. (1969). "A Theory for Record Linkage." *Journal of the American Statistical Association*, 64(328), pp. 1183–1210.
- OSINT Vault. (2026). "Email Investigation Deep Dive" and "Email Tools Comparison Guide."

### OSINT Tools
- Holehe (GitHub: megadose/holehe) — Email-to-platform account enumeration
- GHunt (GitHub: mxrch/GHunt) — Google account metadata extraction
- WhatsMyName (GitHub: WebBreacher/WhatsMyName) — Username enumeration
- Sherlock (GitHub: sherlock-project/sherlock) — Social media username search
- SpiderFoot (GitHub: smicallef/spiderfoot) — Automated OSINT
- theHarvester (GitHub: laramies/theHarvester) — Email/domain intelligence
- EmailRep.io — Email reputation and profile discovery
- Hunter.io — Email format and domain pattern discovery

### Legal & Ethical
- CFAA (18 U.S.C. § 1030), Van Buren v. United States (2021), hiQ Labs v. LinkedIn (2022)
- EU GDPR Articles 6, 14, and 85 — lawful basis for processing, transparency, and journalism exception
- Berkeley Protocol on Digital Open Source Investigations (UN Human Rights Office, 2022)

---

---

## 8. Adversarial Email Techniques: Evasion Patterns

Email investigation is an adversarial domain — subjects actively deploy techniques to complicate identity tracing. Understanding these countermeasures is essential to avoid false negatives (missing a real connection) and false positives (treating an evasion artifact as a distinct identity).

### 8.1 Catch-All (Wildcard) Addresses

A catch-all email configuration accepts mail sent to *any* address at the domain, regardless of whether a specific mailbox exists. This creates the illusion of infinite valid addresses — a critical false-positive risk for simple existence-checking tools.

| Pattern | Detection Method | OSINT Implication |
|----------|------------------|-------------------|
| **SMTP verification** | `VRFY`/`RCPT TO` always returns positive | Holehe, GHunt, and similar tools report false positives on catch-all domains — every email "exists" |
| **Bounce behavior** | Send a probe email and check for NDR (non-delivery receipt) | Catch-all domains don't bounce; absence of bounce doesn't equal valid mailbox |
| **Domain-level inference** | Check MX records; small/private domains often use catch-all for convenience, large providers (Gmail, Outlook) never do | A @example.com address on a catch-all domain used by a 3-person startup cannot be confirmed without behavioral validation |

**Investigation rule:** For catch-all domains, pivot away from existence-checking tools entirely. Rely instead on breach correlation, username cross-walking (if the local-part pattern matches known usernames), and domain intelligence. A non-bounced probe email on a catch-all domain does **not** constitute positive identity signal.

### 8.2 Plus-Addressing (Subaddressing)

Many email providers (Gmail, Fastmail, ProtonMail) support plus-addressing: `user+tag@domain.com` delivers to `user@domain.com`. This allows subjects to generate infinite unique email variants that all route to the same inbox — a powerful investigation evasion technique.

**Investigation pivot strategy:**
1. **Strip the plus-tag:** Normalize `user+amazon@domain.com` → `user@domain.com` before querying breach databases, social platforms, and enumeration tools. Nearly all tools (Holehe, WhatsMyName, Sherlock) will miss plus-addressed variants unless pre-normalized.
2. **Cross-reference tags as leads:** The tag itself (`+amazon`, `+newsletter`, `+banking`) reveals the purpose and sometimes the service the address was registered for — a metadata signal for timeline reconstruction.
3. **Provider detection:** Gmail and Fastmail strip plus-tags before matching; some corporate Exchange servers do not. Provider-specific behavior must be presumed in the absence of confirmation.

### 8.3 Disposable Email Addresses (DEAs)

Disposable or temporary email services (Guerrilla Mail, 10MinuteMail, Temp-Mail, Mailinator) provide short-lived addresses that auto-destruct after minutes or hours. These are commonly used for one-time account registrations, spam evasion, and anonymized activity.

**Detection signals:**
- **Domain blocklists:** Maintained by disposable-email-detector (GitHub), disposable-email-domains (GitHub), and EmailRep.io — query the MX domain against known disposable provider lists
- **Short TTL on MX records:** Disposable domains often have unusually short DNS TTLs (60-300 seconds) for rapid cycling
- **No web presence:** The domain resolves to a generic landing page or no web service at all — contrast with legitimate custom domains that typically have a website
- **Provider behavioral signatures:** Mailinator allows reading any inbox without authentication; Guerrilla Mail assigns random addresses — behavioral properties that distinguish from legitimate mail infrastructure

**OSINT value of DEAs:** A subject using a disposable email still leaks signals: the registration IP (available via breach data), the service they registered for, and the temporal window of activity. A disposable email doesn't mean no intelligence — it means the address itself carries minimal identity signal, and investigation must pivot to surrounding metadata.

### 8.4 Alias and Forwarding Services

Services like SimpleLogin, AnonAddy, Firefox Relay, and Apple Hide My Email generate unique forwarding addresses that relay to a hidden real inbox. These are structurally similar to plus-addressing but operate at a separate domain level — `user@simplelogin.co` forwards to the real inbox, and the alias can be revoked individually.

**Investigation challenge:** The visible domain (simplelogin.co, anonaddy.com) reveals the use of an alias service, confirming intent to obscure identity — itself a signal — but the real destination inbox is cryptographically hidden. Breach data may still link the alias to the real address if the subject reused credentials or IP addresses across services. See [[data-breach-analysis-osint-identity-linkage]] for credential reuse correlation patterns.

---

## 9. Fellegi-Sunter Weight Calibration for Email Matching

The Fellegi-Sunter probabilistic record linkage framework (Fellegi & Sunter, 1969) assigns agreement/disagreement weights to matching variables. An **email address** is the strongest single matching variable in most entity resolution pipelines, but its weight must be calibrated against real-world ambiguity sources.

### 9.1 Agreement Weight (m-Probability)

The m-probability represents the likelihood that two records representing the same entity agree on the email field. For email addresses:

| Scenario | m-Probability | Rationale |
|----------|---------------|-----------|
| **Exact match** | 0.92–0.97 | Email addresses are unique per service; same address strongly implies same entity. Discount for: shared family accounts, corporate role-based addresses (`admin@`, `info@`), and catch-all domains |
| **Normalized match** (plus-addressing stripped, case-folded, Gmail dot-ignored) | 0.88–0.95 | Plus-addressing, case sensitivity, and Gmail's dot-ignoring create false disagreements; normalization recovers most matches |
| **Domain-only match** (different local-parts, same domain) | 0.15–0.30 | Shared organizational affiliation but distinct individuals; higher weight for small/niche domains, lower for gmail.com/hotmail.com |
| **Local-part match, different domain** | 0.25–0.45 | Suggests same username pattern (username reuse across providers) — weaker signal but combinable with other attributes |

### 9.2 Disagreement Weight (u-Probability)

The u-probability represents the likelihood that two records representing *different* entities agree on the email by chance:

| Scenario | u-Probability | Notes |
|----------|---------------|-------|
| **Different addresses** | < 0.0001 | Two random individuals almost never share an email — email disagreement is near-decisive for non-match |
| **Same domain (common provider)** | 0.001–0.01 | Gmail alone has ~1.8B users; same domain on a common provider carries near-zero identity signal |
| **Same domain (rare/niche)** | 0.05–0.20 | Corporate or custom domains with few users — domain match is a stronger signal in sparse populations |

### 9.3 Composite Weight Formula

For an email match in a Fellegi-Sunter pipeline, the weight contribution is:

`weight = log₂(m / u)`

- **Exact email match (m=0.95, u=0.0001):** weight ≈ log₂(9,500) ≈ **+13.2 bits** — a single email match can carry more evidentiary weight than 10+ weaker attributes combined.
- **Normalized match after plus-address stripping (m=0.92, u=0.001):** weight ≈ log₂(920) ≈ **+9.8 bits**.
- **Domain-only match, rare domain (m=0.25, u=0.05):** weight ≈ log₂(5) ≈ **+2.3 bits** — modest but contributory when combined with other signals.

### 9.4 Implementation Considerations

- **Email is a blocking key, not just a matching variable:** The near-zero u-probability for disagreement makes email an ideal blocking variable — records that disagree on email can be safely excluded from pairwise comparison, dramatically reducing the O(n²) comparison space in large datasets.
- **Pre-processing is mandatory:** Case normalization (lowercase), plus-address stripping, Gmail dot-removal (`user.name@gmail.com` = `username@gmail.com`), and domain normalization (`googlemail.com` → `gmail.com`) must be applied before Fellegi-Sunter comparison.
- **Breach data timestamps as weight modifiers:** An email match from a 2015 breach carries less weight than a 2026 match for current identity assessment — apply temporal decay: `weight_adjusted = weight_base × e^(-λ × years_elapsed)`, with λ calibrated to the domain (λ ≈ 0.3 for consumer identity; λ ≈ 0.1 for corporate affiliation).

---

## 10. Temporal Consistency Validation

Identity claims derived from email investigation must pass temporal consistency checks — an email observed in 2015 breach data may belong to a different person today if the address was abandoned, reassigned, or inherited.

### 10.1 Email Address Lifecycle

| Phase | Duration | Investigation Signal |
|-------|----------|---------------------|
| **Active** | Years–decades | Primary signal: the email actively appears in recent (~6 month) breach data, platform profiles, or domain registrations |
| **Dormant** | Months–years | The address shows historical activity but no recent signal — may indicate abandonment or secondary/backup address |
| **Abandoned** | Variable | Provider may recycle the address (Yahoo's 2013 reactivation program, Microsoft's 30-day grace period, Outlook's 360-day inactive deletion) — identity claims weaken sharply after abandonment |
| **Recycled** | Variable | The address has been reassigned to a new person — pre-recycling breach data now maps to a *different* entity, creating false-positive linkage risk |

### 10.2 Temporal Validation Methodology

1. **Establish first-seen date:** Earliest breach, domain registration (WHOIS creation date), or platform profile creation containing the email
2. **Establish last-seen date:** Most recent breach, platform login, or public appearance of the email
3. **Calculate activity span:** If span > 3 years with consistent associated identity attributes (name, phone, location) → high confidence in identity persistence
4. **Detect discontinuity:** Sudden change in associated name, location, or device fingerprint between two temporally adjacent breach records → possible reassignment or account takeover
5. **Cross-reference with provider recycling policy:** Yahoo recycled addresses after 12 months of inactivity (pre-2013 policy); Microsoft Outlook deletes inactive accounts after 2 years — if last-seen exceeds the provider's recycling window, the address may have been reassigned

### 10.3 Temporal Contradiction as Negative Signal

If an email appears in breach A (2018) linked to "John Smith, Chicago" and breach B (2025) linked to "Maria Garcia, Madrid" with no overlap in associated attributes, temporal discontinuity flags a probable reassignment or account compromise. Both records may be *technically* correct — they just describe different entities at different times. Investigation must not merge these records into a single identity claim without additional corroborating linkage.

---

## 11. AI/LLM-Assisted Phishing Detection & Email Classification

The 2025–2026 landscape of AI-driven email analysis provides multiple frameworks for automated phishing detection, source credibility assessment, and linguistic pattern analysis — each with direct applications to OSINT investigation.

### 11.1 Transformer-Based Detection

Ahmed et al. (2026, *Computer Networks*) demonstrate fine-tuned RoBERTa achieving **98.45% accuracy** for phishing email detection, paired with LITA (LIME-Transformer Attribution) for explainability. The hybrid explanation approach provides token-level contribution scores — useful for OSINT analysts who need to understand *why* an email was classified as suspicious, not just the binary label.

### 11.2 Multi-Agent LLM Role-Specialized Decomposition

Sánchez et al. (2026, *Electronics* 15(12), 2606) propose a multi-agent LLM framework that decomposes phishing evidence across three role-specialized agents:
- **Linguistic patterns agent:** Analyzes email text for urgency, threat language, and stylistic anomalies
- **Psychological manipulation agent:** Detects persuasion tactics (authority appeals, scarcity framing, social proof exploitation)
- **Sender identity consistency agent:** Verifies header authenticity, domain alignment, and behavioral consistency

The Meta-Judge system aggregates specialist outputs via schema-governed synthesis, achieving **Macro-F1 = 98.28%** and **phishing recall = 99.45%** on a 1,000-email subset of the TREC/Nazario corpus (56,212 emails total). Key finding: role-specialized decomposition is the primary performance driver — the structure of evidence decomposition matters more than the raw model capability.

### 11.3 LLM Cybersecurity Systematic Review

A PRISMA-guided systematic review (2026, *CMC* 167 studies, 2022–2025) identifies phishing as the most prevalent AIGC-enabled threat vector: LLMs enable automated, highly personalized phishing at scale, including multilingual campaigns that defeat traditional keyword-based detection. The review finds a structurally imbalanced ecosystem — offensive innovation outpaces defensive maturity — and recommends RAG-augmented multi-agent SOC architectures as the most promising defensive pattern.

### 11.4 Lightweight & Federated Approaches

A lightweight federated learning approach for multilingual phishing detection (IEEE, 2026) addresses the operational reality that phishing crosses language boundaries: a subject may receive phishing emails in Spanish, English, and Arabic simultaneously. Federated models trained across distributed email corpora without centralized data collection provide privacy-preserving phishing detection scalable to OSINT investigation pipelines.

### 11.5 OSINT Investigation Integration

For the OSINT investigator, these detection frameworks serve two purposes:
1. **Source credibility assessment:** An email claiming to be from a subject is itself OSINT evidence — AI-based phishing detection classifies whether the email is authentic communication or fabricated bait
2. **Behavioral fingerprinting:** The linguistic patterns, writing style, and psychological tactics in a subject's emails constitute a behavioral fingerprint — transformer models can extract and compare these patterns across emails to confirm or refute single-authorship claims

---

## 12. References

### Methodology
- Hurey, N. (2026). "Email OSINT Guide 2026 — Find Accounts & Breaches." OSINT Vault. theosintvault.io/email-osint-guide
- Fellegi, I.P. and Sunter, A.B. (1969). "A Theory for Record Linkage." *Journal of the American Statistical Association*, 64(328), pp. 1183–1210.
- OSINT Vault. (2026). "Email Investigation Deep Dive" and "Email Tools Comparison Guide."

### Phishing Detection & AI
- Ahmed et al. (2026). "An explainable transformer-based model for phishing email detection: A large language model approach." *Computer Networks*, 112061. [RoBERTa fine-tuned, 98.45% accuracy, LITA explainability]
- Sánchez et al. (2026). "Explainable Multi-Agent LLM Framework for Phishing Email Detection via Role-Specialized Evidence Decomposition." *Electronics*, 15(12), 2606. [Multi-agent GPT-4o-mini, Macro-F1 98.28%, phishing recall 99.45%, TREC/Nazario 1,000-email subset]
- Systematic Review (2026). "Large Language Models for Cybersecurity Intelligence." *Computers, Materials & Continua*, 077367. [167 studies, PRISMA-guided, AIGC threat taxonomy, RAG-augmented multi-agent SOC]
- IEEE (2026). "Multilingual Phishing Email Detection Using Lightweight Federated Learning." IEEE Xplore, 11268856.
- IEEE (2026). "Hybrid Spear-Phishing Email Detection with LLM and Machine Learning." IEEE Xplore, 11288187.

### OSINT Tools
- Holehe (GitHub: megadose/holehe) — Email-to-platform account enumeration
- GHunt (GitHub: mxrch/GHunt) — Google account metadata extraction
- WhatsMyName (GitHub: WebBreacher/WhatsMyName) — Username enumeration across 400+ platforms
- Sherlock (GitHub: sherlock-project/sherlock) — Social media username search
- SpiderFoot (GitHub: smicallef/spiderfoot) — Automated OSINT reconnaissance
- theHarvester (GitHub: laramies/theHarvester) — Email/domain intelligence gathering
- EmailRep.io — Email reputation scoring, breach correlation, disposable domain detection
- Hunter.io — Email format pattern discovery and domain-level email structure inference
- disposable-email-domains (GitHub) — Community-maintained blocklist of disposable email provider domains

### Legal & Ethical
- CFAA (18 U.S.C. § 1030), Van Buren v. United States (2021), hiQ Labs v. LinkedIn (2022)
- EU GDPR Articles 6, 14, and 85 — lawful basis for processing, transparency obligations, and journalism exception
- Berkeley Protocol on Digital Open Source Investigations (UN Human Rights Office, 2022)
