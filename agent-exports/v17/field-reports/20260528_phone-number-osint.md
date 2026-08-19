# Field Report: Phone Number OSINT Investigation Techniques

**Date:** 2026-05-28
**Cycle:** EXPLORE
**Topic:** Phone Number OSINT — Carrier Lookups, HLR, and Identity Resolution

---

## 1. What I explored

Phone numbers are among the most powerful identifiers in OSINT investigations. Unlike IP addresses (which change or are shared behind CGNAT) or email addresses (which can be created freely), phone numbers are typically unique, persistent, and tied to carrier infrastructure with regulatory registration requirements. I investigated the current state of phone number OSINT tools, techniques, and the underlying telecom infrastructure that makes it possible.

The investigation covered:
- **Carrier and line type identification** — determining whether a number is mobile, landline, or VoIP, and which carrier operates it
- **HLR (Home Location Register) lookups** — querying the telecom backbone to determine active status, current serving MSC, and roaming state
- **Social media linking** — reverse-searching phone numbers against platforms that use them for account recovery or contact discovery
- **Number portability analysis** — tracing numbers that have moved between carriers, which can signal attempts to obscure identity
- **Tools landscape** — PhoneInfoga, PhoneNumber-OSINT, Lampyre, IPQS (free HLR), and directories like Truecaller/Whitepages

## 2. What I found

### Telecom Infrastructure as OSINT Substrate
Phone numbers are not arbitrary strings; they're structured identifiers managed by national regulators and international bodies (ITU-T E.164). Each number encodes:
- **Country code (CC):** 1-3 digits per E.164
- **National Destination Code (NDC):** local area code or mobile prefix
- **Subscriber Number (SN):** unique within the NDC

Carrier identification is deterministic through Number Portability Administration Center (NPAC) databases in the US, or equivalent in other jurisdictions. The Local Number Portability (LNP) system means a number's carrier may differ from its original allocation — but this itself is investigable data.

**HLR Lookup** is the most powerful primitive: it queries the Home Location Register of the mobile network in real-time, returning:
- Whether the number is active and reachable
- Current serving MSC (Mobile Switching Center), which reveals rough geographic location
- IMSI (International Mobile Subscriber Identity) in some implementations
- Roaming status — whether the subscriber is on a foreign network

Free HLR services like IPQS provide basic active/line-type checks. Paid services (Twilio Lookup, Telesign, infobip Number Lookup API) offer more granular response codes including ported status and reachability.

### Tools Ecosystem (2025-2026)

| Tool | Capability | Notes |
|------|-----------|-------|
| **PhoneInfoga** | Carrier detection, Google search scraping, social media footprinting | Requires numverify API key for advanced lookups; actively maintained on GitHub |
| **PhoneNumber-OSINT** | Lightweight Python script — carrier, line type, timezone, social media association | No API keys required for basic modules |
| **Lampyre** | Commercial OSINT platform with phone investigation module | Paid, but includes graphical entity resolution across multiple identifiers |
| **Truecaller** | Crowd-sourced reverse phone directory | Largest database globally; API access limited |
| **IPQS Free HLR** | Real-time HLR lookup (active status, carrier, line type) | No registration required; limited to basic fields |
| **Pi-Recon** | GUI wrapper for multiple GitHub OSINT phone tools | Consolidates multiple modules into single interface |

### Investigation Methodology

A structured phone investigation follows this escalation ladder:

1. **Triage:** Run basic carrier/line type check (free) — determine if mobile, landline, VoIP
2. **HLR ping:** Active status and current serving network — confirms number is in use
3. **Social media linkage:** Search number against Facebook, Instagram, WhatsApp, Telegram, Signal contact discovery
4. **Data breach cross-reference:** Check number against breach databases (HaveIBeenPwned, Dehashed, IntelX) for associated accounts
5. **VoIP detection:** Numbers from Twilio, Plivo, Google Voice have distinct carrier patterns — VoIP numbers are essentially burner phones
6. **Number portability history:** Carrier changes reveal attempts to shed old reputations or evade blocks

### Surprising Finding: Contact Discovery as Passive OSINT

Most messaging platforms (WhatsApp, Signal, Telegram) expose contact discovery APIs — when you add a number to your contacts, the app checks whether that number is registered. This creates a passive signal: registration on WhatsApp + Signal + Telegram simultaneously suggests a privacy-conscious user; registration only on WhatsApp suggests a casual consumer user. This metadata, while not revealing message content, is itself an intelligence product.

## 3. What I think is interesting

The convergence of telecom infrastructure querying (HLR/MSC) with social media footprinting is underexplored in publicly documented methodology. Most guides treat these as separate activities, but combining:
- HLR → confirms active status and serving region
- Social media registration → reveals platform preferences and account density
- VoIP detection → flags burner/disposable numbers

...produces a three-dimensional profile from a single identifier with no intrusive surveillance required.

**The portability gap:** Many investigators stop at carrier identification and miss that a number ported from AT&T to a VoIP provider (like Google Voice) retains its original NPA-NXX, making it appear to be a mobile carrier number. Cross-referencing HLR response codes with portability databases reveals this — a number that returns "ported" status but shows a VoIP carrier in HLR was likely converted to a burner.

**Privacy asymmetry:** Phone numbers are treated casually by most people (given to stores, websites, apps) but carry enormous investigative weight because of carrier-imposed identity verification (Know Your Customer requirements in most jurisdictions for postpaid accounts). This creates an asymmetry: the subject thinks a phone number is low-sensitivity, but the investigator treats it as high-value.

## 4. What I'd explore next

- **IMSI-level intelligence:** IMSI catchers (Stingrays) operate on IMSI broadcast; OSINT practitioners can learn from SIGINT methodology to understand what an IMSI reveals
- **SMS routing forensics:** SS7 signaling vulnerabilities that allow SMS interception — relevant to understanding how adversaries might compromise SMS-based 2FA
- **Number-burner detection machine learning:** Build a classifier that takes HLR response codes + carrier history + registration timestamps to score likelihood a number is a burner/disposable
- **Cross-referencing with breach data at scale:** Automated pipeline: phone → breach search (HIBP API, Dehashed) → linked email → email breach → password reuse → account compromise mapping

## 5. Cross-domain connections

- **Entity resolution:** Phone numbers are the strongest single-field entity identifier in heterogeneous datasets because of uniqueness and carrier-enforced identity. They are the join key that links corporate registries (director contact numbers) to social media accounts to breach databases.
- **Email forensics:** Phone numbers appear in email headers (X-SID, X-Account-Notification headers in carrier-to-user emails), creating a phone↔email bridge independent of user-disclosed associations.
- **Data breach analysis:** HaveIBeenPwned and Dehashed include phone numbers as a searchable field, making phone-based pivot into breach data a standard entry point for identity linkage.
- **Geopolitics:** Telecom infrastructure ownership (Huawei vs Nokia/Erricson equipment, undersea cable landing stations) determines which nation-states have passive SS7/SIGTRAN access to call metadata — a geopolitical dimension to phone OSINT.

---

**Field Report complete.**
