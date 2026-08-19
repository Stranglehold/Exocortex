# Field Report: HUMINT Tradecraft Principles Applied to OSINT Methodology

**Date:** 2026-05-26
**Topic:** HUMINT tradecraft principles applicable to OSINT methodology
**Cycle:** EXPLORE
**Sources:** Grey Dynamics, OSINT Investigations (Substack), Police1, LinkedIn, IntelMSL

---

## 1. What I Explored

I investigated how Human Intelligence (HUMINT) tradecraft can be mapped onto Open Source Intelligence (OSINT) investigation workflows. The premise: HUMINT has decades of institutional knowledge about source assessment, psychological profiling, and information validation. OSINT practitioners are essentially doing HUMINT at scale through digital proxies. The tradecraft should transfer.

I followed threads on:
- The MICE framework (Money, Ideology, Compromise, Ego) for source motivation analysis
- The HUMINT pyramid of source sensitivity, quantity, and value
- Interrogation techniques and their digital analogues
- Cultural competency as force multiplier
- The evolving HUMINT-OSINT complementarity

## 2. What I Found

### HUMINT Pyramid Maps to OSINT Data Hierarchy

Michael Herman\'s pyramid (via Grey Dynamics):
- **Bottom tier** (high quantity, low sensitivity, low value): business contacts, casual travelers
- **Middle tier**: political opponents, exiles, occasional informants
- **Top tier**: agents, informers, defectors

OSINT mapping:
- **Bottom tier**: public social media, press releases, corporate registries, LinkedIn
- **Middle tier**: leaked databases, dark web forums, semi-public records (PACER, FOIA)
- **Top tier**: insider leaks, breached proprietary data, whistleblower submissions

Key insight: bottom-tier sources remain valuable for puzzle-piece connections despite proliferation of open-source information.

### MICE Framework as OSINT Subject Assessment

- **Money**: analyze financial records, cryptocurrency flows, campaign finance, procurement patterns
- **Ideology**: ideological posturing on social media, forum signatures, organizational affiliations reveal predictive behavior
- **Compromise/Coercion**: doxxed subjects, blackmailed individuals — information available but potentially contaminated
- **Excitement/Ego**: explains why subjects post incriminating content, hackers brag on forums, insiders leak to journalists

### Interrogation Techniques → Digital Investigation Methods

| HUMINT Type | OSINT Analogue |
|---|---|
| Cooperative and friendly | Well-structured APIs, open data portals, RSS feeds |
| Neutral and non-partisan | Paywalled content, CAPTCHA-protected pages, rate-limited APIs |
| Hostile and antagonistic | Bot-protected sites, anti-scraping measures, actively monitored forums |

Interrogator qualities map to OSINT traits: patience (rate limits), adaptability (changing web architectures), perseverance (dead-end searches).

### OSINT-HUMINT Integration Thesis

Multiple sources converge: OSINT is not replacing HUMINT — it makes HUMINT practitioners more effective. Police1: "two truths are better than one" — HUMINT claims verified by OSINT are stronger than either alone. Conversely, OSINT findings direct HUMINT collection.

### Agent Handler\'s Toolkit

Substack series demonstrates translation of HUMINT target development into OSINT search methodology. Search operators (AND, OR, NOT, filetype, site, AROUND(n)) applied with case-officer mindset: anticipate how information appears on webpages, multilingual search essential.

## 3. What I Think Is Interesting

### The Hidden Structure of OSINT

Most OSINT literature focuses on tools rather than cognitive frameworks. HUMINT provides three high-value imports:

1. **MICE as subject classification**: classify likely motivation before searching — financially motivated, ideologically driven, or compromised. Search strategy changes with classification.

2. **HUMINT pyramid as data triage**: start at bottom tier and work up. Low-tier sources inform where to look at higher tiers.

3. **Interrogator mindset as search methodology**: adapt tool selection and query construction to data source "personality."

### The Validation Gap

HUMINT has built-in validation through source triangulation. OSINT\'s equivalent is algorithmic, but HUMINT reminds us source motivation matters. A breached database (compromised source in MICE terms) deserves same skepticism as coerced HUMINT intel. We lack formal taxonomies for OSINT source reliability incorporating motivation analysis.

## 4. What I\'d Explore Next

1. **Formal OSINT Source Reliability Framework**: combine MICE motivation analysis with A-F reliability ratings
2. **Digital Interrogation Patterns**: search query patterns inspired by interrogation techniques
3. **HUMINT Case Study Translation**: abstract principles from historical cases (Ashraf Marwan, Eli Cohen, Nancy Wake) into OSINT patterns
4. **MICE-AI Connection**: apply MICE framework to assess AI-generated intelligence from autonomous OSINT collection

## 5. Cross-Domain Connections

### To Entity Resolution
MICE classification determines whether multiple records refer to same person. Financially motivated vs ideologically motivated individuals appear in different record types.

### To Exocortex Epistemic Integrity
HMI deception in electric utility attacks mirrors HUMINT concept of hostile interrogation sources. AI agents must maintain epistemic integrity against adversarial data — resisting deception and fabrication.

### To OSINT Investigation Methodology
May 19 field report identified epistemic risk from AI acceleration. MICE classification provides antidote: structured skepticism about source motivation before analysis.

### To Agentic AI Self-Learning
Autonomous OSINT agents need MICE-like classification in assessment frameworks. An agent treating a breached database with same confidence as an official filing produces garbage. HUMINT institutional knowledge should be encoded into agent guardrails.

---

**Sources:** Grey Dynamics "A Guide to Human Intelligence (HUMINT)" (full), The Agent Handler\'s OSINT Toolkit #1 (Substack), Police1 "Two Truths Are Better than One", LinkedIn "From Tools to Tradecraft" by Dusty McLean, IntelMSL (attempted, 403).
