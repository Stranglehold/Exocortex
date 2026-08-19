# Messaging Platform OSINT Investigation

**Status: STABLE**
**Created: 2026-08-02 (DRAFT stub)**
**Deepened: 2026-08-03**
**Tags: OSINT, entity-resolution, telegram, discord, whatsapp, signal, identity-linkage, timeline-reconstruction**
**Related: [[phone-number-osint]], [[social-media-profile-investigation-osint]], [[social-media-forensics-osint]], [[metadata-resistant-messaging]], [[data-breach-analysis-identity-linkage]], [[email-header-analysis]]**

## Summary

Messaging platforms are high-density identity and behavior surfaces for OSINT: they combine stable identifiers (phone numbers, usernames, opaque user IDs), public group/channel content, rich metadata (registration signals, join times, device data), and graph structure (who talks to whom, shared invite links). This page documents the platform-specific investigation surface for Telegram, Discord, WhatsApp, and Signal, with tooling, metadata parsing, legal/ToS boundaries, and integration into the broader Exocortex entity-resolution pipeline.

A core analytical frame: **messaging OSINT is the operator side of the metadata arms race documented in [[metadata-resistant-messaging]]**. Centralized platforms expose metadata by design; the investigator's job is to convert that metadata into entity-resolution evidence, while understanding that the same techniques fail cleanly against P2P/metadata-resistant protocols.

## 1. Platform Architecture and Data Exposure Surfaces

| Platform | Identifier model | Public surface | Server-visible metadata | OSINT relevance |
|----------|-----------------|----------------|------------------------|-----------------|
| **Telegram** | Phone number + username; numeric user IDs; global search index | Channels, groups, public profiles, bot APIs | IP (on registration/login), approximate geolocation per session, device list, contact graph | Highest — public channel corpus is algorithmic-curation-free (TeraGram 5.9B messages) |
| **Discord** | Opaque snowflake user IDs; server-invite links; global username@discriminator (legacy) / display names | Server invite links, member lists, audit logs in shared servers, embed metadata | IP (voice + gateway), account creation date (from snowflake), guild-join graph | High for community/network mapping and timeline reconstruction |
| **WhatsApp** | Phone number; no public directory by design | Click-to-chat links, business catalogs, group invite links | IP, contact graph (who is in which group), online status timing, registration state | Medium — deliberate absence of a public directory makes registration-check and business-surface signals the main vectors |
| **Signal** | Phone number; no public directory; sealed sender | Private by default; only registration/uniqueness signals are exposed | IP, contact graph (server knows who messages whom), registration timestamp | Low-medium — registration checks + contact discovery are the only practical OSINT vectors |

**Key exposure principle**: the more a platform is a *broadcast* medium (Telegram channels) or a *community* medium (Discord servers), the larger its public corpus. The more a platform optimizes for *private dyadic* messaging (WhatsApp, Signal), the smaller the public surface and the more the investigator must rely on metadata side-channels (registration, click-to-chat, group invites).

## 2. Telegram OSINT

- **Identifier architecture**: registration is phone-bound; each account has a numeric `user_id`, optional public `@username`, and profile metadata. Usernames are globally unique but changeable, so `user_id` is the stable entity anchor; username is a temporal fingerprint.
- **Global search index**: public groups/channels are indexed and keyword-searchable in-app and via the Bot API. This is the single largest public message corpus among messaging apps.
- **Scale evidence (web-verified, arXiv)**: TeraGram (arXiv:2605.15956) collects **5.9B+ messages from 712k channels/groups (2015–2025)** with forward/reaction/poll metadata; group-verse analysis (arXiv:2409.02525) engineered an open-source collector and analyzed **51M messages across 669 public groups**; Telegram Monitor (arXiv:2202.04737) demonstrated real-time political-group monitoring. MTProto 2.0 formal verification (arXiv:2012.03141) confirmed sound authentication/chat with a rekeying UKS flaw — protocol-level robustness does not remove the metadata exposure.
- **Collection vectors**: Bot API (official, rate-limited, exposes channel/group posts + member/forward metadata); MTProto client libraries (telethon/pyrogram; full session-level access); gateways such as Apify's `telegram-channel-scraper` (35 fields/message, no phone/API key for public channels); saved-message/export files from Telegram Desktop exports (HTML/JSON with join timestamps and admin actions).
- **Entity resolution signals**: username to user_id linkage; forwarded-from attribution; admin/owner listings; join-date inference from channel member history; cross-referencing a phone number against the registration API; linked public profile photos to reverse-image search.
- **Timeline reconstruction**: channel edit/delete history is server-side; local exports preserve message edit timestamps and admin-log actions; forward chains reveal campaign or amplification patterns.

## 3. Discord OSINT

- **Snowflake IDs (deterministic, independently decodable)**: Discord snowflakes are `(timestamp_ms - 1420070400000) << 22 | worker << 17 | process << 12 | increment`. Decoding a user ID yields **account creation time** to the millisecond — a stable artifact for account-age fingerprinting and cross-platform same-user correlation (same creation window across platforms is a weak-match ER feature in the Fellegi-Sunter sense).
- **Invite links**: guild invites are high-entropy short tokens; they act as **propagation artifacts** — a shared invite in a leaked chat, breach log, or public paste links two communities to the same source account. Invite metadata (expiry, max uses, inviter) adds attribution.
- **Guild/member surface**: servers the target shares expose member lists, roles, join-order persistence, and bot/service accounts. Audit logs (permission-gated) record user/bot actions and are a timeline-reconstruction goldmine when accessible.
- **Entity resolution signals**: global/display username across servers; avatar history + rehosted hashes (pivot to reverse-image search); shared-server intersections as corroborating graph edges; connection to breach data — infostealer logs frequently bundle Discord tokens and handles with corporate email, GitHub usernames, crypto wallets, and home IPs in one timestamped package (corpus-verified, data-breach field report 20260704).
- **API hygiene**: unauthenticated endpoints are rate-limited and ToS-constrained; tool-directory marketing claims are thin on verifiable tradecraft and should be treated as unverified.
## 4. WhatsApp OSINT

- **Deliberately small public surface**: no public profile directory. Practical vectors: (1) **registration/contact-discovery check** — adding a number to contacts reveals whether that number is on WhatsApp (corpus-verified passive signal: registration footprint across WhatsApp + Telegram + Signal triangulates a user's privacy posture, phone-number OSINT field report 20260528); (2) **click-to-chat / wa.me links** — embedded in seller listings, form posts, and breach dumps; each link implies a phone number and often a business context; (3) **business catalogs/status** — business profiles expose catalog items, hours, and sometimes location.
- **Group metadata**: group invite links leak group names, admin phone patterns, and member-growth dynamics. Group chat exports (email-chat export) preserve timestamps, phone numbers, and media — useful for corroborating timeline evidence from device seizures.
- **Forensic note (library-verified, Practical Mobile Forensics)**: WhatsApp/Signal/Telegram app data on-device is often recoverable from SQLite databases even when "secure" — WAL/journal files can hold portions of supposedly encrypted chats; media saved by the user is a separate recovery surface. Base64 "encoding" is not encryption.

## 5. Signal OSINT

- **Registration/uniqueness check**: the only widely usable OSINT vector is whether a number is registered (contact discovery). Sealed Sender hides sender identity from the server for messages, but the server retains subscriber metadata (who has an account, registration/pattern).
- **Metadata limits**: content E2EE; no public corpus; no global identifier namespace beyond phone. Signal's adversarial relationship to OSINT is documented in [[metadata-resistant-messaging]] — including March 2026 Sealed Sender caveats and PQXDH migration. Practical approach: treat Signal presence as a corroborating *boolean* (exists/not exists) rather than a rich source.
- **Triangulation use-case**: phone-number OSINT field report frames it well — registration on WhatsApp + Signal + Telegram simultaneously suggests deliberate privacy hygiene; registration only on WhatsApp suggests casual consumer usage. That classification itself is an intelligence output.

## 6. Metadata vs Content: The Adversarial Frame

- Content encryption (Telegram secret chats, WhatsApp E2EE, Signal) protects payload; **metadata remains the investigative product**: identifiers, timestamps, graph edges, device signals.
- Platforms sit on a spectrum: Telegram broadcast/public corpus (max exposure) → Discord guild corpus (community-gated) → WhatsApp business/group metadata (minimal public) → Signal registration-only (minimal).
- The inverse relation to [[metadata-resistant-messaging]] is structural: BOTH parties extract the same signals (IP, timing, device fingerprint, contact graph). The investigator converts them into identity evidence; the privacy protocol destroys or hides them. This is the metadata arms race: OSINT adjusts as privacy technology advances, and privacy protocols harden against known observation techniques.
- **Dark matter problem** (corpus-verified): targets on P2P/metadata-resistant systems appear as connections known to exist but unobservable via traditional phone/email/username pivots. Methodology must plan for observation failure states.

## 7. Legal/Ethical Boundaries and ToS Risks

- Bulk-scraping Telegram public channels is legally contested across jurisdictions (GDPR applicability to personal data, platform ToS prohibiting automated access, potential CFAA-type exposure). Wiki corpus precedent: [[legal-ethical-osint]], [[evidence-preservation-chain-of-custody-osint]].
- Passive OSINT (registration checks, reading public content, decoding public IDs) is generally permissible; active enumeration (mass member harvesting, API-probing for private data, using stolen tokens) crosses into unlawful collection and often collapses under third-party doctrine.
- Discord API/Telegram Bot API use requires platform compliance; account-based scrapers risk platform bans and may violate terms. For evidence admissibility (FRE/Berkeley Protocol lineage), preserve collection context, timestamps, and hash the artifacts (see [[evidence-preservation-chain-of-custody-osint]]).
## 8. 5-Phase Investigation Workflow

1. **Anchor**: identify the target's known identifiers (phone number, username, user_id, email) and classify platform footprint via registration checks.
2. **Collect public surface**: Telegram public channels/groups via exports or scraper; Discord same-server context; wa.me/click-to-chat links; preserved/exported chats.
3. **Extract metadata**: decode snowflake timestamps, forward chains, admin logs, join times, device/session fingerprints; cross-reference with breach-data attributes (corpus: infostealer logs bundle handles/tokens).
4. **Resolve**: feed extracted attributes into Fellegi-Sunter-style probabilistic matching — matching user creation windows, username patterns, avatar hashes, shared community intersections. Cross-platform same-user correlation is the core ER task (see [[osint-entity-resolution-methods]]).
5. **Preserve and report**: log collection provenance, hash artifacts, timestamp everything; produce timeline reconstruction and attributed entity graph with confidence levels.

## 9. Tooling Ecosystem (non-exhaustive)

| Tool type | Examples | Notes |
|-----------|----------|-------|
| Telegram client libraries | Telethon, Pyrogram, MTProto SDKs | Session-level; full metadata access; ToS-sensitive |
| Telegram scrapers/services | Apify telegram-channel-scraper, Telegram Monitor (arXiv) | 35 fields/message public channels; research-grade affordances |
| Datasets | TeraGram (5.9B msgs), group-verse 51M corpus | Research/validation use; ground truth for training ER classifiers |
| ID decode / lookups | Snowflake decoders, Discord user-ID lookups | Timestamp decodes verified; third-party corpus claims vary |
| Registry/people-search | Phone registry checks, wa.me link mining, Signal registration probes | Passive; rate-limit aware |
| Forensic tooling | UFED/Physical Analyzer, Magnet IEF, SQLite inspectors | On-device app DB extraction; court-tested in mobile forensics |
| Cross-platform enumeration | Sherlock/Maigret (username), reverse-image search | Username reuse is the most common—and most reliable—telegram/discord/forum linking signal |

## 10. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **Data Breach Analysis** | Infostealer logs bundle Discord tokens/handles with corporate email, GitHub, wallets, home IP in one timestamped package — high-fidelity ER anchor |
| **Phone-Number OSINT** | Registration footprint across platforms (WhatsApp+Telegram+Signal) is a passive classifier of user privacy posture |
| **Metadata-Resistant Messaging** | Structural inverse: the same signals (IP, timing, graph, device) that OSINT extracts are what privacy protocols destroy; 'dark matter' observation failure state |
| **Social Network Analysis** | Group/channel co-membership and invite propagation are graph edges; platform subgraphs feed SNA theory (weak ties, structural holes) |
| **Evidence Preservation** | Bulk collection requires provenance logging, hashing, and timestamps for admissibility |
| **Entity Resolution** | Snowflake creation time, username reuse, avatar hashes, shared-guild intersections are Fellegi-Sunter attribute features for cross-platform matching |
| **Timeline Reconstruction** | Chat exports, forward chains, admin logs, and snowflake timestamps reconstruct activity patterns across platforms |
| **AI/Agent Monitoring** | Telegram broadcast corpus is algorithm-curation-free — a clean observational window for influence operations and market signaling |

## 11. References

Verified via search/corpus this cycle:
- TeraGram: Structured Longitudinal Telegram Dataset (arXiv:2605.15956) — 5.9B messages, 712k channels/groups, 2015–2025.
- Topic-wise Exploration of the Telegram Group-verse (arXiv:2409.02525) — 51M messages, 669 groups, open collector.
- Telegram Monitor (arXiv:2202.04737) — Brazilian political groups/channels real-time monitoring.
- Automated Symbolic Verification of Telegram's MTProto 2.0 (arXiv:2012.03141) — soundness + rekeying UKS flaw.
- Apify telegram-channel-scraper — 35 fields/message, no phone/API key for public channels.
- Practical Mobile Forensics (Packt) — on-device Telegram/Wickr/Signal SQLite/WAL recovery; encoding vs encryption.
- Shared corpus: phone-number-osint field report 20260528 (contact discovery as passive OSINT); data-breach field report 20260704 (infostealer linkage); metadata-resistant-messaging (dark matter / arms race); social-media-forensics-osint.

Unverified/flag: DiscordGate tools directory claims; most third-party 'Discord lookup' services (API stability varies). Snowflake decoding is deterministic and independently re-derivable.
