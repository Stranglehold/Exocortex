# Phone Number OSINT & Investigation
**Status: STABLE**
**Created: 2026-05-20 | Deepened: 2026-05-20**
**Interest: OSINT & Investigation Methodology**
**Related: [[human-investigation-osint]], [[reverse-image-search-visual-osint]], [[data-aggregation-entity-resolution]], [[anti-bot-evasion]]**

## Summary

A phone number is a uniquely powerful OSINT identifier — harder to change than an email, more personal than a username, and persistently linked across platforms. Phone OSINT is the systematic collection and analysis of publicly available data tied to a phone number to establish identity, surface online accounts, and build entity resolution links. The core insight: phone numbers are reused across messaging apps, financial services, social media, e-commerce, and business directories, making them a digital fingerprint. This page documents the full investigation workflow from carrier-level intelligence through to cross-platform identity resolution.

## Research Findings

### I. Phone Number Anatomy & Pre-Investigation Triage

Before running OSINT tools, classify the number to narrow the investigative path:

| Attribute | Intelligence Value |
|-----------|-------------------|
| **Country code** | Jurisdiction for privacy laws, dominant carrier patterns |
| **Area code (NPA-NXX)** | Geographic origin; cross-reference with number portability (LNP) — ported numbers break geographic assumptions |
| **Line type** (wireless, landline, VoIP, non-fixed VoIP) | VoIP/non-fixed numbers (Google Voice, TextNow, Burner) indicate deliberate anonymity; landline = likely business or residential |
| **Carrier** (HLR lookup) | MVNO vs major carrier (MVNOs like Mint, Visible require less ID verification) |
| **Age on account** | Newly activated numbers associated with fraud/throwaway patterns |


### IA. The E.164 Numbering Plan

The ITU-T E.164 standard defines the international public telecommunication numbering plan. Every phone number is structured as:

- **CC** (Country Code): 1-3 digits (e.g., 1 for US/Canada, 91 for India, 44 for UK)
- **NDC** (National Destination Code): variable length, includes area codes and mobile prefixes
- **SN** (Subscriber Number): the unique subscriber identifier within the NDC

Maximum total length: 15 digits. This structure is critical for OSINT triage:
- Country Code determines jurisdictional privacy laws (GDPR in +3X/+4X, PIPL in +86)
- Mobile prefix within NDC reveals original carrier and rough geographic origin
- Short codes (4-6 digits) indicate automated services, not individual subscribers
- Non-E.164 numbers (VoIP, satellite) bypass traditional carrier attribution

The E.164 numbering space is managed by the ITU and delegated to national regulators (FCC in US, TRAI in India, BEREC in EU). Number assignments are public record; national numbering plans reveal which prefixes are mobile, landline, toll-free, premium-rate, or machine-to-machine (IoT).

**Tool:** `phonenumbers` Python library (Google's libphonenumber port) — parses, validates, and formats E.164 numbers, extracts carrier and geolocation data.

**Key tool:** PhoneInfoga (`sundowndev/PhoneInfoga`) — automates number validation, carrier lookup, VoIP detection, and generates Google dorks for the number. Python CLI; requires Numverify API key for full functionality. Free demo at `demo.phoneinfoga.crvx.fr`.

### II. The Reverse Phone Lookup Workflow (5-tier methodology)

**Tier 1 — Google Dorking (baseline, zero-cost)**

Search the number as an exact phrase in quotes across multiple formats:
- `"+1 555-123-4567"`
- `"5551234567"` 
- `"(555) 123-4567"`

Site-specific dorks:
- `"+1 555-123-4567" site:linkedin.com/in`
- `"+1 555-123-4567" site:pastebin.com`
- `"+1 555-123-4567" filetype:xls OR filetype:csv`
- `"+1 555-123-4567" site:github.com`

Rationale: quotation marks force exact sequence match. The number may appear on a company contact page, personal blog, social media bio, forum post, or leaked database.

**Tier 2 — Crowdsourced Caller ID (mass-directory approach)**

Platforms that build databases from user contact uploads:
- **Truecaller** — 350M+ users. Searches via web interface (Google/Microsoft login required). Returns: registered name, profile picture, email (sometimes), spam/SPAM score. Critical caveat: the name shown may be how someone *else* saved the contact (e.g., "John Useless" or "Scam Likely"), not necessarily the user's self-chosen display name.
- **Sync.me** — Similar crowdsourced model, web-based search.
- **EyeofGod_bot** (Telegram bot) — Aggregates data from multiple sources; use with caution and ethics.

**Tier 3 — Caller ID Spoofing & CNAM Lookup (US-only, active probing)**

- **SpyDialer** — Three lookup modes: (1) **Voicemail lookup:** calls the number directly into voicemail bypassing ringing, plays recorded greeting — a confirmed owner name. (2) Photo lookup: searches for profile images linked to the number across social/messaging apps. (3) Name lookup: cross-references public data sources.
- **CallerIDTest** — Queries CNAM (Calling Name) database. CNAM is the name businesses pay telecoms to display on caller ID. Definitive for business numbers; often unpopulated for personal lines.

**Tier 4 — People Search Engines / Data Brokers (US-focused deep dive)**

- **TruePeopleSearch** — Free, powerful aggregator of public records. Phone search returns: full name of current owner, age, current and historical addresses, relatives/associates list. US numbers only.
- **ZLOOKUP, OkCaller, NumBuster** — Lighter-weight reverse lookup services; varying accuracy.

**Ethical note on data brokers:** These services compile public records (property records, utility bills, voter registration). The data is publicly sourced but the aggregation creates a privacy amplifier — a distinction relevant to operational security and GDPR compliance analysis.

**Tier 5 — Integrated Workflow Automation (professional OSINT)**

- **IntelTechniques Tools** (Michael Bazzell): Provides a unified dashboard that queries dozens of services (Google, TruePeopleSearch, SpyDialer, etc.) with a single phone number entry. Does not store data; it's a query router. Essential for operational consistency.
- **OSINT Industries** (commercial): Consolidates breach databases, social media registrations, business directories, and messaging app associations into a single report with source attribution. Includes data visualization via "Palette" (digital evidence board). Enterprise platform with separate access tiers for law enforcement, government, and journalists.

### III. Cross-Platform Account Discovery

Phone numbers gate access to services that will reveal or confirm identity without interaction:

| Platform | What's Revealed | Method |
|----------|----------------|--------|
| **WhatsApp** | Profile picture, display name, About text, Last Seen (if public) | Save contact → view profile; business accounts show business name, website, hours, location |
| **Telegram** | Username, display name, profile photo, bio | Saved Contacts → Add by phone number; bots like @PhoneFinderBot |
| **Signal** | Profile name (if contacts have it) | Same mechanism; Signal stores less metadata |
| **UPI apps** (India: PhonePe, Google Pay, Paytm) | Bank-verified real name, profile picture, sometimes bank name | Enter number in "Send to Contact" — metadata loads before initiating transfer. **Legal and passive** — no transaction required. |
| **Forgotten Password flows** | Partially masked email (e.g., j***@gmail.com) or phone confirmation | Enter number on login recovery pages of major services; observe what's exposed |
| **Ride-sharing / food delivery apps** | Receipt-linked emails, name fragments | Check if number is registered in Uber, Ola, Zomato, Swiggy |

### IV. Breach Correlation & Data Leak Investigation

Phone numbers are among the most commonly breached data points. Techniques:

- **HaveIBeenPwned** — Check if number appears in known breaches; returns breach name and date
- **Dehashed** — Requires login; links phone numbers to breached emails, usernames, passwords
- **Google dorking for dumps:** `"phone_number" site:pastebin.com`, `"phone_number" filetype:txt`, GitHub search (people accidentally commit contact lists)
- **OSINT Industries** integrates breach data with source attribution — ethically important as manual breach search can cross legal boundaries

**Risk classification:** Breach data varies in legality depending on jurisdiction. GDPR Article 5(1)(c) (data minimization) and CFAA in the US create legal exposure for investigators who download or retain breach databases. Platform-mediated access (HiBP API, OSINT Industries) provides legal insulation.

### V. Phone Discovery (Forward Lookup)

Starting from a name, email, or business to find the associated phone number:

1. **Company websites** — "About" and "Contact" pages; especially for sales/client-facing roles
2. **Professional directories** — Licensed professionals (dentists, surveyors, attorneys) in state/provincial registries with public contact numbers
3. **LinkedIn** — Profile contact sections; also combined with Google dorking
4. **WHOIS records** — Historical WHOIS data (pre-GDPR redaction) often contains registrant phone numbers
5. **Email signature scraping** — If email address is known, Google dork for: `"@company.com" "phone"`

### VI. International & Regional Considerations

| Region | Key Tools / Approaches |
|--------|----------------------|
| **India** | UPI payment lookup (bank-verified names), Truecaller (dominant), PhoneInfoga |
| **US** | SpyDialer voicemail, TruePeopleSearch, CNAM lookup, IntelTechniques |
| **EU/EEA** | GDPR limits data broker aggregation; Google dorking and social media check remain primary; carrier-level lookups more tightly regulated |
| **China** | Phone number tied to real-name registration; WeChat/Alipay integration provides strong identity linkage in domestic context |

**Number portability (LNP):** Area codes cannot be relied upon for geographic origin in any country with LNP (US since 2003, EU since 2003-2007, India since 2011, etc.). A 212 area code does not mean NYC — it could be ported to a carrier in Wyoming. Always verify carrier via HLR lookup.

### VII. Countermeasures & Operational Security & Operational Security

For individuals protecting their own number:
- Use **Google Voice** or **Burner** numbers for public-facing registrations
- Disable contact syncing in Truecaller (prevents upload of your contact list)
- Use **Jumbo** or **SimpleLogin** for email/phone masking
- Avoid linking phone to public social media profiles
- Check your own number through these tools periodically (self-audit OSINT)

## Cross-Domain Connections

1. **Entity Resolution Pipeline:** Phone number is a high-fidelity linking key for the OpenPlanter entity resolution pipeline (`entity_resolution.py`). When authoritative identifiers (EIN, DUNS) are unavailable, phone number provides a probabilistic match key with lower false-positive rates than name-only matching. Deterministic matching on phone + postal code yields high precision for individual identity resolution.

2. **Anti-Bot Evasion:** The OSINT phone lookup workflow faces the same anti-bot challenges as web scraping — Truecaller, SpyDialer, and search engines deploy rate limiting, CAPTCHAs, and fingerprinting. TLS/JA3 fingerprinting and browser fingerprinting techniques from [[anti-bot-evasion]] are directly applicable to scaling phone OSINT investigations.

3. **Email Forensics → Phone Correlation:** Email headers often contain originating IPs; those IPs geolocate to ISPs that assign phone numbers. Cross-referencing email breach data with phone carrier records creates identity clusters. The bidirectional pivot (email→phone, phone→email) is described in [[email-forensics-header-analysis]] and [[domain-whois-dns-investigation]].

4. **Human Investigation OSINT:** Phone number investigation feeds the broader HUMINT-OSINT methodology from [[humint-tradecraft-osint]]. The Admiralty Code scoring system applies: Google dork results = A2 ("completely reliable source, probably true"), breach data = B3 ("usually reliable, possibly true"), Truecaller crowdsourced names = C2 ("fairly reliable, probably true").

5. **Graph Theory:** Phone numbers are high-centrality nodes in a communication network — one number connects to many email addresses, social media accounts, physical addresses, and other phone numbers. Community detection on phone number graphs reveals organizational structures (family units, corporate hierarchies, criminal networks). See [[network-analysis-graph-theory]].

6. **Privacy & Cryptography:** Metadata-resistant communication protocols (Signal, Briar, Cwtch) specifically address the phone number as identifier problem. Signal's sealed sender and phone number privacy features are direct responses to the OSINT techniques documented here. See [[privacy-cryptography]].


### VIII. SS7 Protocol Vulnerabilities & Carrier Network Intelligence

Signaling System No. 7 (SS7) is the protocol backbone of global telecom networks — it handles call setup, SMS routing, number portability, prepaid billing, and roaming for 2G/3G networks. SS7 was designed in the 1970s with implicit trust between carriers and no authentication, making it a critically vulnerable OSINT vector:

- **Location tracking:** SS7 `ATI` (Any-Time Interrogation) and `PSI` (Provide Subscriber Information) messages can request a phone's cell-level location. Security researchers demonstrated this against US Congress members in 2016 on *60 Minutes*.
- **Call/SMS interception:** `USSD` and `SRI-SM` messages can redirect calls and SMS. A 2025 TechCrunch exposé documented a surveillance vendor actively exploiting SS7 to track phone locations.
- **EFF FCC filing (May 2024):** The EFF formally demanded FCC investigation of SS7 and Diameter (LTE/5G signaling) security, noting that "SS7 vulnerabilities are not theoretical" and demanding transparency from carriers on their signaling firewall implementations.
- **Dark web SS7 exploitation:** SOS Intelligence documented SS7 exploitation services available on Dark Web marketplaces, including location lookups and SMS interception, priced from $50-$500 per target.
- **Misattribution risk:** Attackers route SS7 requests through intermediate carriers, making attribution difficult. Carriers can implement signaling firewalls (e.g., AdaptiveMobile, Enea) to cross-correlate traffic across all network generations.

**OSINT relevance:** SS7 intelligence is not a consumer OSINT technique — it requires carrier-level access or purchased exploit services. However, understanding SS7 informs the *reliability* of carrier data: caller ID that can be spoofed via SS7 manipulation, location data that may be fabricated, and SMS-based 2FA that can be intercepted. The Admiralty Code would rate SS7-derived intelligence as B3 ("usually reliable, possibly true") at best.

### IX. Burner Phone & Throwaway Number Detection

Burner phones and throwaway numbers (Google Voice, TextNow, Burner, Hushed, 2ndLine) present a critical OSINT challenge — they create a deliberate barrier between phone number and identity. Detection signals include:

| Signal | Indicator |
|--------|-----------|
| **Non-fixed VoIP** (NPA-NXX lookup) | Numbers from known VoIP ranges (e.g., TextNow: NY NPA, Google Voice: often CA NPA) — PhoneInfoga classifies these as "non-fixed VoIP" |
| **Recent activation date** | HLR lookup reveals age-on-account; numbers activated in last 30 days are high-probability throwaway |
| **Carrier or MVNO** | TextNow, FreedomPop, TracFone MVNOs have minimal KYC requirements vs major carriers (Verizon, AT&T, T-Mobile) |
| **No associated accounts** | Number returns zero results on Truecaller, Google search, and breach databases — unlikely for a personal number |
| **Usage pattern** | Number used for a single transaction (classified ad, marketplace sale) and never again |
| **Number recycling** | Carriers recycle disconnected numbers after 45-90 days. A number previously associated with a different person will produce stale results. Check "last seen" dates on lookup services. |

**Counter-technique:** Even burner numbers leave metadata traces — SMS OAuth flows (WhatsApp, Signal) require a number for verification; those apps maintain account creation timestamps. A number used for even one online account creates a breach datapoint. The pivot from phone → WhatsApp/Telegram/Signal profile image → reverse image search can de-anonymize a burner number.

### X. IMSI, IMEI & SIM-Card Intelligence

Beyond the phone number, the underlying identifiers provide forensic depth:

- **IMSI** (International Mobile Subscriber Identity): 15-digit identifier stored on the SIM card, unique globally. The IMSI reveals the home network (MCC+MNC: Mobile Country Code + Mobile Network Code). IMSI catchers (Stingrays) exploit this at the physical layer — not an OSINT technique, but understanding IMSI explains why location data from telecom metadata is reliable: SIM cards are harder to swap than phone numbers.
- **IMEI** (International Mobile Equipment Identity): 15-digit identifier unique to the physical device. An IMEI ties a phone number to a specific handset. If law enforcement has the IMEI (from a warrant), it survives SIM swaps. OSINT tools cannot query IMEI databases directly, but IMEI-to-model lookup reveals the device make/model, which can be correlated with device-specific digital traces (User-Agent strings, app fingerprints).
- **SIM swap detection:** A SIM swap transfers a phone number to a new SIM card. Indicators: carrier changes suddenly, or account ownership changes. SIM swapping is both a fraud vector (account takeover via SMS 2FA) and an OSINT dead end — the number now belongs to a different person.

### XI. Legal & Regulatory Frameworks

Phone OSINT operates within overlapping legal regimes. Key constraints by jurisdiction:

| Jurisdiction | Key Law | OSINT Implication |
|-------------|---------|-------------------|
| **United States** | TCPA (Telephone Consumer Protection Act), CFAA, state privacy laws | Automated dialing or SMS to numbers without consent is prohibited. OSINT lookup is generally legal, but accessing carrier databases (HLR) without authorization may violate CFAA. |
| **European Union** | GDPR, ePrivacy Directive | Phone numbers are personal data. Processing (including OSINT lookup) requires a lawful basis. Passive research (Google dorking) is likely legitimate interest; automated API querying may need explicit consent or documented legitimate interest. |
| **India** | IT Act 2000, DPDP Act 2023, TRAI regulations | Phone number is personal data under DPDP. UPI-based lookup (phone→name) is a public feature of UPI but mass scraping could trigger DPDP penalties. |
| **China** | PIPL (Personal Information Protection Law), Cybersecurity Law | Phone numbers are personal information. Processing requires consent or statutory permission. OSINT tools that query Chinese carrier databases operate in legal gray zones. |
| **Global** | M-LATF (Mobile Location Analytics Task Force), GSMA guidelines | The GSMA maintains guidelines for signaling security and location data access. Commercial OSINT tools (OSINT Industries, EchoSec) operate under these frameworks. |

**Operational rule:** Passive techniques (Google dorking, Truecaller search, public breach data lookup) are universally lower-risk than active techniques (HLR querying, SMS triggering, automated API enumeration). When conducting OSINT investigations, document the legal basis for each technique used.

### XII. Carrier HLR Lookup Depth

The Home Location Register (HLR) is the master subscriber database for a mobile network. An HLR lookup returns:

- **MCC/MNC** (Mobile Country Code / Mobile Network Code): Identifies the home network
- **Portability status:** Whether the number has been ported (LNP — Local Number Portability)
- **Roaming status:** Current serving network (VLR — Visitor Location Register)
- **Line type:** Mobile, landline, VoIP
- **IMEI** (in some implementations)

**OSINT tools for HLR:** `hlr-lookups.com` API, Twilio Lookup API, Numverify API. HLR lookups are not free — pricing ranges from $0.005-$0.05 per lookup. The GSMA requires HLR lookup providers to have a legitimate use case; many OSINT-oriented HLR services operate from jurisdictions without enforcement.

**LNP complications:** Since 2003 (US), number portability means a number's area code no longer reliably indicates geographic location. A 212 (NYC) area code number may now be assigned to a subscriber in California. Always verify porting status via HLR before making geographic assumptions.

### XIII. Smishing & Phone-Based Attack Infrastructure

Phone numbers are both a target and a tool for investigation. Smishing (SMS phishing) infrastructure leaves traces:

- **Short codes:** 5-6 digit numbers leased from carriers for mass SMS. Short code registries (US Short Code Directory, Common Short Code Administration) are public record — lookup reveals the brand that leased the code.
- **SMS gateways:** Services like Twilio, Vonage, Plivo, and AWS SNS provide SMS APIs. Investigators can identify gateway providers via SMS gateway databases and subpoena Twilio/Vonage for account records.
- **URL shorteners in SMS:** Smishing payloads use URL shorteners (bit.ly, tinyurl). These services provide click analytics; many allow public access to basic metadata. Expand shortened URLs with `curl -I` to trace final destination.
- **Domain registration:** Phishing domains in SMS (e.g., `netflx-verify.com`) can be WHOIS-looked up for registrant data. See [[domain-whois-dns-investigation]].


## Implementation Notes

- **Source material:** Three web-scraped OSINT guides (OSINT Industries Nov 2025, CavemenTech Jul 2025, Spyboy Jun 2025) — all cached as HTML in `/a0/usr/workdir/phone_osint_*.html`
- **Tool availability:** PhoneInfoga is open-source (GitHub: sundowndev/PhoneInfoga). IntelTechniques Tools is free. OSINT Industries has a free trial tier. TruePeopleSearch is free but US-only.
- **Ethical framework:** All techniques documented are passive (no social engineering, no unauthorized access, no transaction initiation). The distinction between OSINT (legal) and doxing (illegal) is intent and consent — this page documents the former for legitimate security research, threat intelligence, and identity verification.
- **Automation potential:** The multi-tier workflow is scriptable: (1) PhoneInfoga for validation, (2) Google dork generation, (3) Truecaller API (where available), (4) aggregation into report. See `/a0/usr/Exocortex/field-reports/20260520_entity-resolution-icij-methodology.md` for automated entity resolution patterns.

## References

- OSINT Industries. "OSINT Phone Number Investigations: How to Use Phone OSINT Tools." November 2025. (Cached: `/a0/usr/workdir/phone_osint_osintindustries.md`)
- CavemenTech. "How to Find a Phone Number's Owner: The Ultimate OSINT Guide (2025)." July 2025. (Cached: `/a0/usr/workdir/phone_osint_cavementech.md`)
- Spyboy. "Phone Number OSINT: The Ultimate Guide to Reconnaissance Using Just a Mobile Number (Legally)." June 2025. (Cached: `/a0/usr/workdir/phone_osint_spyboy.md`)
- Bazzell, Michael. *OSINT Techniques: Resources for Uncovering Online Information.* IntelTechniques.
- PhoneInfoga (GitHub): `https://github.com/sundowndev/PhoneInfoga`
- HaveIBeenPwned API: `https://haveibeenpwned.com/API/v3`
- North American Numbering Plan Administration (NANPA) — area code and carrier lookup data
