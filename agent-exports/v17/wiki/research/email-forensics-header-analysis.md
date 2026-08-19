# Email Forensics & Header Analysis

**Status: STABLE**
**Created: 2026-05-20**
**Last deepened: 2026-05-20**
**Domain: OSINT / Cybersecurity**
**Primary sources: RFC 5321, RFC 5322, RFC 7208 (SPF), RFC 6376 (DKIM), RFC 7489 (DMARC), NIST TN.1945, UserSearch methodology**

---

## Overview

Email header analysis is the forensic examination of metadata embedded in email messages to trace origin, verify authenticity, detect spoofing, and extract investigative intelligence. While the body of an email can be forged, the headers contain a chain of custody that — when properly interpreted — reveals the true path an email traveled from sender to recipient.

Three core investigative questions drive header analysis:
1. **Origin**: Where did this email actually come from? (IP address, ISP, geographic location)
2. **Authenticity**: Was this email genuinely sent by the claimed domain? (SPF, DKIM, DMARC)
3. **Identity**: What can the headers reveal about the sender's infrastructure, habits, and opsec?

---

## 1. Email Header Anatomy

### Core RFC Standards

Email headers are governed by two foundational RFCs:

- **RFC 5321 (SMTP)** — Defines the envelope: the `MAIL FROM` command (return-path) used for delivery and bounces. This is the *transport-layer* sender, invisible to the recipient's mail client.
- **RFC 5322 (Internet Message Format)** — Defines the message format: the `From:` header displayed to the user. This is the *presentation-layer* sender — and the one most easily spoofed.

The distinction between RFC 5321 `MAIL FROM` and RFC 5322 `From:` is the root cause of most email spoofing. SPF authenticates the envelope (5321); DKIM authenticates the message (5322); DMARC requires alignment between the two.

### The Received Chain

Every mail server that handles an email prepends a `Received:` header. Reading from bottom (oldest) to top (most recent) reconstructs the delivery path:

```
Received: from mail.example.com (mail.example.com [203.0.113.1])
    by inbound.recipient.com with ESMTP id xYz123
    for <victim@recipient.com>; Mon, 19 May 2026 14:30:00 -0400 (EDT)
```

Key fields in each Received header:
| Field | Investigative Value |
|-------|-------------------|
| `from` | Hostname claimed by sending server (may be forged) |
| `[IP address]` | Actual IP — the ground truth. Cannot be faked in genuine Received headers |
| `by` | Receiving mail server hostname |
| `with` | Protocol used (ESMTP, ESMTPA for authenticated, LMTP) |
| `id` | Unique message ID assigned by this hop |
| `for <email>` | Intended recipient at this hop |
| Timestamp | Temporal chain of custody — inconsistent timezones or impossible sequences signal forgery |

### Critical Investigative Headers

| Header | Purpose | Forensics Value |
|--------|---------|----------------|
| `Return-Path` | Envelope sender (RFC 5321) | Bounce destination; often differs from From: in spoofed mail |
| `From:` | Displayed sender (RFC 5322) | What the user sees — easily spoofed without authentication |
| `Reply-To` | Where replies go | Spoofers often set this to a different address they control |
| `Message-ID` | Globally unique identifier | Format reveals sending MUA/server software and sometimes hostname |
| `X-Originating-IP` | Original sender IP | Present in some webmail (Hotmail classic, older Yahoo); increasingly rare as providers strip it |
| `X-Mailer` | Sending software | Reveals client: Outlook, Thunderbird, Apple Mail, or custom scripts |
| `DKIM-Signature` | DomainKeys signature | Contains signing domain (d=), selector (s=), and body hash (bh=) |
| `Authentication-Results` | Receiver's auth verdict | Shows SPF/DKIM/DMARC pass/fail — the recipient server's ground truth |
| `X-Sender-IP` | Sender IP (Yahoo) | Yahoo-specific IP disclosure |
| `X-PHP-Originating-Script` | PHP script path | Present in mail sent via PHP `mail()` function — reveals server path structure |

---

## 2. Authentication Forensics: SPF, DKIM, DMARC

### SPF (Sender Policy Framework) — RFC 7208

SPF works at the **envelope level** (RFC 5321 `MAIL FROM`). The receiving server checks if the sending IP is authorized by the domain's SPF DNS record:

```bash
dig TXT example.com | grep spf
# example.com. 300 IN TXT "v=spf1 ip4:192.0.2.0/24 include:_spf.google.com -all"
```

SPF mechanisms:
| Mechanism | Meaning |
|-----------|---------|
| `+ip4:1.2.3.4` | Allow this IP (pass) |
| `include:domain` | Include another domain's SPF |
| `?all` | Neutral — no policy |
| `~all` | Softfail — accept but mark |
| `-all` | Hardfail — reject |

**Forensic insight**: A domain with `?all` has no meaningful SPF protection. A domain with `-all` that still shows SPF=fail indicates a forged sender. SPF breaks on email forwarding unless the forwarder rewrites the envelope sender (SRS).

### DKIM (DomainKeys Identified Mail) — RFC 6376

DKIM operates at the **message level**. The sending server cryptographically signs the message body and selected headers. The receiving server verifies the signature against a public key published in DNS:

```bash
dig TXT selector._domainkey.example.com
```

DKIM-Signature header fields:
| Field | Meaning | Forensics Value |
|-------|---------|----------------|
| `d=` | Signing domain | The domain that signed the message — may differ from From: domain |
| `s=` | Selector | Identifies which key was used; can reveal service provider (e.g., `google`, `pm`) |
| `bh=` | Body hash | Hash of canonicalized body — tampering detection |
| `h=` | Signed headers | Which headers are covered by the signature |
| `b=` | Signature data | The actual cryptographic signature |

**Forensic insight**: A DKIM signature with `d=gmail.com` on an email From: `ceo@corporation.com` means Gmail's servers signed it — the sender used Gmail's SMTP, not the corporation's infrastructure. This can be legitimate for small businesses, or can signal a compromised Gmail account being used to impersonate.

### DMARC (Domain-based Message Authentication) — RFC 7489

DMARC ties SPF and DKIM together with a **policy**. It requires **alignment** — either the SPF-authenticated domain OR the DKIM signing domain must match the RFC 5322 `From:` domain:

```bash
dig TXT _dmarc.example.com
# v=DMARC1; p=reject; rua=mailto:dmarc@example.com; ruf=mailto:forensic@example.com
```

DMARC policies:
| Policy | Meaning |
|--------|---------|
| `p=none` | Monitor only — no action on failures |
| `p=quarantine` | Send failures to spam |
| `p=reject` | Reject failures outright |

**Forensic insight**: A domain with `p=reject` is hardened against spoofing. If you receive a spoofed email claiming to be from a domain with `p=reject`, the recipient's server misconfiguration is at fault. `p=none` domains are vulnerable — DMARC reports from `rua=` addresses can reveal spoofing attempts against that domain.

### Authentication Results Interpretation

`Authentication-Results` header from the recipient server is the **ground truth** for any investigation:

```
Authentication-Results: mx.google.com;
       spf=pass (google.com: domain of sender@example.com designates 192.0.2.1 as permitted sender) smtp.mailfrom=sender@example.com;
       dkim=pass header.i=@example.com;
       dmarc=pass (p=REJECT sp=NONE dis=NONE) header.from=example.com
```

If this header shows `spf=fail` / `dkim=fail` / `dmarc=fail`, the email is forged regardless of what the From: field displays.

---

## 3. IP Tracing and Geolocation

### Extracting the Originating IP

Modern webmail providers (Gmail, Yahoo, Outlook.com) typically strip the sender's originating IP from headers. However, several patterns still expose it:

1. **Self-hosted/exchange servers**: Corporate and legacy mail servers often include the sender's internal or public IP in the first `Received:` hop
2. **Older ISPs**: Some regional ISPs and web hosts still include `X-Originating-IP`
3. **PHP mail() scripts**: Contact forms using PHP's `mail()` function may include `X-PHP-Originating-Script` revealing the web server path and sometimes client IP in `Received:`
4. **Mobile clients**: Email sent from mobile carrier SMTP servers may include carrier-assigned IPs traceable to region

### IP Geolocation and Enrichment

Once an IP is extracted:

```bash
# MaxMind GeoLite2 (free)
mmdblookup -f /usr/share/GeoIP/GeoLite2-City.mmdb --ip 203.0.113.45

# WHOIS for ASN/ISP
whois 203.0.113.45

# IPinfo API
curl ipinfo.io/203.0.113.45
```

Investigative dimensions:
| Data Point | What It Reveals |
|------------|----------------|
| ISP/ASN | Residential vs. corporate vs. hosting/VPS |
| City/Region | Geographic origin — cross-reference with claimed location |
| Proxy/VPN detection | Known VPN exit nodes, Tor exit nodes, hosting IPs |
| Abuse contacts | ISP abuse email for escalation |

**Key forensic principle**: An email from "London office" that originates from a Nigerian residential ISP IP is a red flag. An email From: `@company.com` that originates from a DigitalOcean VPS IP suggests a compromised server or scripted sending.

---

## 4. Email Provider Fingerprinting

### Webmail vs. Corporate Mail

Provider fingerprinting from headers:

| Provider | Signature in Headers |
|----------|---------------------|
| Gmail (personal) | `Received: from mail-sor-f41.google.com`, `DKIM-Signature: d=gmail.com` |
| Google Workspace | `Received: from mail-sor-f41.google.com`, `DKIM-Signature: d=company.com` |
| Microsoft 365/Exchange | `Received: from *.protection.outlook.com`, `X-MS-Exchange-*` headers |
| ProtonMail | `Received: from mail.protonmail.ch`, DKIM `d=protonmail.com` |
| Yahoo | `Received: from sonic*.mail..*.yahoodns.net`, `X-YMail-OSG` |
| Self-hosted Postfix | `Received: from * with ESMTP id *`, typical UNIX timestamp format in Message-ID |
| SendGrid/Mailgun | `Received: from *.sendgrid.net`, `DKIM-Signature: d=sendgrid.net` |

### Message-ID Format Analysis

The `Message-ID` format often reveals the sending software:

```
# Gmail
<CA+H3s5xyz@mail.gmail.com>

# Microsoft Exchange
<abc123@EXCHANGE01.company.local>

# Unix/mail (Postfix)
<202605191430.12345@hostname.example.com>

# PHPMailer
<abc123@server-hostname>
```

### Disposable Email Detection

Burner accounts use disposable domains. Detection workflow:

```bash
# Check MX records — disposable providers use specific infrastructure
dig MX 10minutemail.com +short
# Known disposable MX patterns: mailinator.com, trashmail.de, guerrillamail.com

# Check SOA record — may leak admin's real email
dig SOA suspicous-domain.com +short
# Output: ns1.example.com. admin.personal@gmail.com. 2026051901 7200 3600 1209600 3600
```

The SOA record's `RNAME` field (admin email) has unmasked burner operators who registered domains with their personal email.

---

## 5. Anti-Spoofing and Phishing Investigation

### Spoofing Detection Workflow

1. **Check Authentication-Results**: If the recipient's server shows SPF/DKIM/DMARC failures, the email is definitively spoofed
2. **Compare Return-Path vs From**: A mismatch is suspicious but not definitive (legitimate mailing lists work this way)
3. **Trace Received chain**: The bottom-most Received header should originate from infrastructure matching the claimed domain
4. **Check Reply-To**: Spoofed emails often set Reply-To to an attacker-controlled address
5. **Analyze Message-ID format**: Does it match the claimed domain's usual Message-ID pattern?

### Common Spoofing Patterns

| Pattern | Detection |
|---------|-----------|
| Display name spoof | `From: "CEO Name" <attacker@gmail.com>` — the display name fools mobile clients. Check actual email address. |
| Cousin domain | `@company.co` vs `@company.com` — lookalike domains. Check domain registration date and DNS. |
| Unicode homograph | `@cοmpany.com` (Greek omicron) vs `@company.com` — visually identical. Check raw headers for punycode. |
| Reply-to hijack | `From: legitimate@real.com`, `Reply-To: attacker@fake.com` — replies go to attacker. |
| Forwarded email injection | Spoofed message wrapped in a forward from a compromised account. Check the outermost headers. |

### Phishing Email Forensics

Beyond authentication, analyze:

- **URLs**: Extract all links. Check domain registration dates (WHOIS) — phishing domains are typically <30 days old
- **Attachments**: Analyze attachment hashes against VirusTotal; check file type magic bytes vs. extension mismatch
- **Language patterns**: Grammar errors, urgency cues, unusual greetings
- **Brand consistency**: Compare headers/X-Mailer with legitimate emails from the same organization

---

## 6. Tools and Automation

### Header Parsing and Analysis

| Tool | Function |
|------|----------|
| `mxtoolbox.com/EmailHeaders.aspx` | Online header analyzer — parses and visualizes Received chain |
| `Messageheader Toolbox (Microsoft)` | Online tool specifically for Exchange/365 headers |
| `Google Admin Toolbox Messageheader` | Parse headers with Google's analyzer |
| `MXToolbox SPF/DKIM/DMARC` | DNS record verification tools |

### DNS and Domain Investigation

```bash
# SPF record
dig TXT example.com | grep spf

# DKIM (requires selector — check DKIM-Signature: s=)
dig TXT selector._domainkey.example.com

# DMARC
dig TXT _dmarc.example.com

# MX records
dig MX example.com +short

# Full domain investigation
dig ANY example.com
whois example.com
```

### OSINT Investigation Platforms

| Tool | Capability |
|------|-----------|
| **Have I Been Pwned** | Breach database — check if email appears in known data breaches |
| **Dehashed** | Breach database — search email across breach collections with password/credential context |
| **Holehe** | Open-source tool checking email registration across 120+ sites via password reset analysis |
| **Hunter.io** | Find email address format patterns for a domain; verify email existence |
| **Epieos** | Reverse email lookup — find linked Google accounts, Skype, social profiles |
| **IntelX** | Email search across leak databases, paste dumps, and dark web sources |
| **Gravatar** | Check if email has a Gravatar profile (avatar, username, profile URL) |
| **MxToolbox** | Comprehensive DNS toolkit — blacklist check, header analysis, SPF/DKIM/DMARC verification |

### Automated Investigation Scripts

```python
# Basic email header parser in Python
import email
import email.policy

with open('email.eml', 'rb') as f:
    msg = email.message_from_binary_file(f, policy=email.policy.default)

# Extract Received chain
received_headers = msg.get_all('Received', [])
for h in reversed(received_headers):  # Oldest first
    print(f"Hop: {h}")

# Authentication results
auth_results = msg.get('Authentication-Results', 'Not present')
print(f"Auth: {auth_results}")

# Key headers
for hdr in ['From', 'Reply-To', 'Return-Path', 'Message-ID', 'DKIM-Signature', 'X-Originating-IP']:
    val = msg.get(hdr, 'Not present')
    print(f"{hdr}: {val}")
```

---

## 7. Breach Intelligence and Identity Pivoting

### Breach Context Analysis

When an email appears in breach databases, the *type* of breach provides behavioral intelligence:

| Breach Type | Implication |
|-------------|-------------|
| Ashley Madison, AdultFriendFinder | Lifestyle/risk indicators |
| LinkedIn 2012, Dropbox 2016 | Account age — indicates long-term primary identity |
| Chegg, Edmodo | Educational history — likely student during breach period |
| Collection #1, Comb lists | Credential circulated among threat actors — may be used for credential stuffing |
| Specific service (PayPal, Amazon) | Commerce history — confirms usage of that platform |

### Password Pivot Technique

Users rarely invent unique passwords. A password found in a breach can link accounts:

1. Extract password from breach (e.g., `Company2023!`)
2. Search for other accounts using similar password patterns in the same breach collection
3. Common pattern: `[Company][Year][!]` — the username/email with `Company2023!` may have another account using `Company2024!`

### Avatar and Username Cross-Referencing

- **Gravatar**: Extract avatar, run reverse image search (Google Images, TinEye, FaceCheck.id)
- **Username pivot**: Extract the username portion of the email (`name` from `name@domain.com`) and search across 3,000+ platforms via username enumeration tools
- **Google Calendar trick**: Create an event and add the target email as a guest — Google often resolves the email to the account's display name
- **Password recovery hints**: Initiate recovery flows on major platforms to reveal partial recovery emails (`j****@gmail.com`) or phone numbers (`...ends in 45`)

---

## 8. Cross-Domain Connections (Exocortex)

| Exocortex Concept | Connection to Email Forensics |
|-------------------|-------------------------------|
| **Epistemic Integrity** | Email authentication (SPF/DKIM/DMARC) is an epistemic verification protocol — each layer independently verifies claims about origin. The `Authentication-Results` header is the evidence ledger. Direct analog: every claim requires verifiable provenance. |
| **Entropy-as-Signal** | Email headers with forged Received chains exhibit entropy anomalies — inconsistent timezone formats, impossible hop sequences, non-monotonic timestamps. Anomaly detection on header entropy can flag spoofing without explicit auth checks. |
| **Deterministic Scaffolding** | Email protocol (SMTP → SPF → DKIM → DMARC) is a layered deterministic scaffolding — each layer constrains the next. The architecture parallels Exocortex's stacked verification layers. |
| **Context Pruner** | In OSINT investigation, not all headers carry equal signal. Pruning low-signal headers (List-Unsubscribe, X-Priority non-anomalous) focuses analysis on forensically relevant headers — parallel to context pruning in LLM reasoning. |
| **Build the Environment** | The anti-spoofing architecture (SPF + DKIM + DMARC) embodies the principle: build an environment where trust is protocol-enforced, not assumed. Aligns with Exocortex's philosophy of deterministic, verifiable scaffolding. |
| **Proactive Interference** | Old breach data (2012 LinkedIn) persists and interferes with current identity assessment. An email's breach history is a form of proactive interference — past compromises continue to influence present trust evaluation. |
| **History of Intelligence Operations** | SIGINT traffic analysis (identifying communicants from metadata, not content) is the direct predecessor of email header forensics. The Received chain is the email equivalent of radio direction-finding and traffic pattern analysis. |
| **Human Investigation & OSINT** | Email header analysis is a core OSINT investigation technique. The structured workflow (headers → IP → geolocation → breach → identity) exemplifies the OSINT pivot chain methodology. |
| **Privacy & Cryptography** | SPF/DKIM/DMARC are applied cryptography for identity assurance. DKIM's RSA signature verification and DMARC's policy enforcement operate on the same principles as certificate transparency and public-key infrastructure. |

---

## 9. References

- RFC 5321 — Simple Mail Transfer Protocol
- RFC 5322 — Internet Message Format
- RFC 7208 — Sender Policy Framework (SPF) Version 1
- RFC 6376 — DomainKeys Identified Mail (DKIM) Signatures
- RFC 7489 — Domain-based Message Authentication, Reporting, and Conformance (DMARC)
- NIST Technical Note 1945 — Email Authentication Mechanisms: DMARC, SPF and DKIM
- M3AAWG — Trust in Email Begins with Authentication (white paper)
- UserSearch — Reverse Email OSINT: The Complete Guide to Tracing Digital Identity (2025)

---

*Page last updated: 2026-05-20. Status: STABLE.*
