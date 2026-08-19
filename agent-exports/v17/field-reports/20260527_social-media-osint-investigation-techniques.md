# Field Report: Social Media OSINT Investigation Techniques
**Date:** 2026-05-27
**Topic:** Human Investigation Tactics → Social Media Intelligence (SOCMINT)
**Cycle Type:** EXPLORE

---

## 1. What I Explored

Investigated the current state of social media OSINT investigation methodology — how professional analysts structure their work when tracing identities and organizations through social platforms. Primary sources:
- **OSINT Handbook (2026)** — The OSINT Vault's workflow-first methodology for analysts
- **100+ OSINT Techniques (ShadowDragon, 2026)** — Comprehensive catalog of SOCMINT tactics
- **AOFIRS OSINT Framework Guide (2026)** — AI-human collaboration models for OSINT

---

## 2. What I Found

### Core Methodology: Workflow-First, Not Tool-First

Professional investigations converge on a **workflow-first approach**: tools support the methodology, not the other way around. The OSINT Vault framework defines:

1. **Hypothesis framing** — Define exact questions before collecting data
2. **Identifier collection** — Usernames, emails, phone numbers, images as pivot points
3. **Validation through cross-referencing** — Minimum two independent sources per claim
4. **Evidence capture** — URL, timestamp, metadata; not just screenshots
5. **Repeatable documentation** — Enough detail for another analyst to reproduce findings

### Pivot Framework

Every investigation starts with a single identifier and branches outward. Common pivot types:

| Pivot Type | Entry Point | Proliferation |
|------------|-------------|---------------|
| **Username** | Single platform handle | Cross-referenced across 400+ platforms (Sherlock) / 2,500+ sites (Maigret) |
| **Email** | Account recovery, breach exposure | Social profiles, domain registrations, professional listings |
| **Phone** | Carrier metadata, messaging apps | WhatsApp, Signal, Telegram linkage; SMS-based account recovery |
| **Image** | Profile photos, listings | Reverse image search (Google, Yandex, Bing, TinEye, PimEyes) |
| **Domain/IP** | Organization verification | WHOIS, DNS, hosting infrastructure patterns |

### Social Media Analysis — 100+ Techniques (ShadowDragon Catalog)

**Network Mapping & Analysis:**
- Friend/follower analysis for influence and association mapping
- Link-analysis graphing through shared likes, reposts, replies, mentions
- Hashtag/keyword networks for community identification and sentiment tracking

**Hashtag Tracking:**
- Frequency analysis over time
- Co-occurrence mapping (what other hashtags appear together)
- Geotag-hashtag correlation for location pinpointing
- Hashtag influencer identification

**Profile Analysis:**
- Username reuse detection across platforms
- Profile metadata extraction (bio, location, join date, follower ratios)
- Content pattern analysis (posting times, linguistic markers, image EXIF)

### Verification Discipline

The dominant theme across sources: **trust nothing from one source**. Every data point requires independent verification. Conflicts between sources are documented, not hidden. The output is a confidence model based on overlapping signals — not convenience or assumption.

### Documentation Standards

Professional OSINT reports are **defensible documents**:
- Source URLs with access timestamps
- Search query strings preserved for reproducibility
- Uncertainty tracked explicitly
- Findings structured so another analyst can re-validate independently

---

## 3. What I Think Is Interesting

### Convergence with Counterintelligence ACH

The OSINT verification framework (multi-source cross-referencing, explicit uncertainty tracking, defensible documentation) maps directly to **Analysis of Competing Hypotheses (ACH)** from counterintelligence tradecraft. Both insist on:
- Multiple hypotheses tested against evidence
- Evidence evaluated for diagnosticity, not just consistency
- Explicit documentation of assumptions and gaps

This convergence suggests a unified investigative epistemology that crosses intelligence disciplines (OSINT, CI, HUMINT). A field report on CI/ACH was already produced (20260526), but the fusion with SOCMINT methodology hasn't been explored.

### Entity Resolution Pipeline Integration

The pivot framework (username → email → phone → domain) is essentially a **manual entity resolution pipeline**. Each pivot is a link discovery operation. The next step is automation: taking the SOCMINT pivot workflow and encoding it as a probabilistic entity resolution system with social media features. Data breach records could serve as ground truth for training the matching model.

### OSINT Market Scale

The global OSINT market reached $12.7 billion in 2025 (Global Market Insights), driven significantly by social media investigation tools. This signals that the professionalization of SOCMINT is not a niche — it's a major industry with standardized methodologies.

---

## 4. What I'd Explore Next

1. **Automated SOCMINT Entity Resolution** — Build a pipeline that takes a username, runs Sherlock/Maigret across platforms, extracts profile features, and feeds them into a probabilistic model for entity matching across platforms.

2. **Data Breach → Social Graph Completion** — Use breach databases as ground truth for training username/email-to-social-profile matching models.

3. **ACH + SOCMINT Integration** — Formalize the ACH framework specifically for social media investigations, with diagnostic evidence weighting for platform-specific signals.

4. **AI-Assisted Pivot Chaining** — Can an LLM agent autonomously execute the pivot workflow? Given a starting identifier, can it recursively search, validate, and map an entity's digital footprint?

---

## 5. Cross-Domain Connections

- **Counterintelligence ACH** — Verification frameworks converge; ACH formalizes what SOCMINT does intuitively
- **Entity Resolution (Data Aggregation)** — Pivot workflow is manual entity resolution; ripe for automation
- **Agentic AI** — Autonomous pivot chaining is a tractable benchmark task for investigating agent capabilities
- **Privacy-Preserving Entity Resolution** — FHE-based matching could enable cross-platform entity resolution without exposing raw profiles
- **PDF Ingestion** — Evidence capture and documentation standards from SOCMINT apply to knowledge base ingestion pipelines
- **Email Header Analysis** — Pivot chain frequently starts with email → username → social profiles; SOCMINT is the downstream stage
