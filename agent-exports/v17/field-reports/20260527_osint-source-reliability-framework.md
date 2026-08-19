# Field Report: OSINT Source Reliability Framework — Admiralty Code + MICE

**Date:** 2026-05-27
**Topic:** Formal OSINT source reliability framework combining Admiralty Code, MICE motivation analysis, and OSINT-specific dimensions
**Cycle:** EXPLORE
**Sources:** Wikipedia (Admiralty Code), Jessica Stutzman, "The Admiralty Code / NATO 6x6 System" (Substack, Feb 2026), prior field report 20260526_humint-tradecraft-osint.md

---

## 1. What I Explored

After discovering that the May 26 HUMINT-OSINT field report identified a gap — no formal OSINT source reliability framework — I researched whether the NATO Admiralty Code (AJP-2.1, STANAG 2511) could be adapted for OSINT, and whether MICE motivation analysis could fill the trustworthiness dimension the Admiralty Code lacks.

The hypothesis: an OSINT-adapted reliability framework should independently rate (a) source history/reputation, (b) information corroboration, and (c) source motivation — three axes instead of two — plus OSINT-specific metadata (timeliness, provenance, handling restrictions).

## 2. What I Found

### 2.1 The Admiralty Code (NATO 6x6 System)

The Admiralty Code pairs a letter (A-F, source reliability) with a number (1-6, information credibility):

| Source Reliability | Description |
|---|---------------|
| A | Completely reliable: no doubt, history of complete reliability |
| B | Usually reliable: minor doubts, valid most of the time |
| C | Fairly reliable: genuine doubt, but valid info in past |
| D | Not usually reliable: significant doubt, treat as lead only |
| E | Unreliable: history of invalid information |
| F | Cannot be judged: no track record (default for new sources) |

| Info Credibility | Description |
|---|--------------------|
| 1 | Confirmed by independent sources |
| 2 | Probably true: not confirmed but logically consistent |
| 3 | Possibly true: reasonably logical, partially consistent |
| 4 | Doubtful: not confirmed, possible but illogical |
| 5 | Improbable: not logical, contradicted by other evidence |
| 6 | Cannot be judged: no basis for evaluation |

Critical principle: the two ratings are independent. An A-rated source can provide improbable info (A5); an E-rated source can provide confirmed info (E1). Conflating them causes borrowed credibility — the single most common analytical error.

### 2.2 The OSINT Problem: F6 Dominance

The single most common OSINT rating is F6 — "cannot judge reliability / cannot judge credibility." This applies to anonymous social media accounts, new websites, walk-in tips, and the vast majority of open-source material that arrives without an established track record. F6 is technically correct but provides zero differentiation between a 10-year-old verified journalist account and a disposable bot account created that morning. Both get F — even though an analyst's working assessment of their reliability differs dramatically.

### 2.3 Missing Dimensions in the Admiralty Code for OSINT

From Stutzman (2026) and supplementary sources:

1. **Source motivation** — MICE (Money, Ideology, Compromise, Ego) provides analysis of why a source reports; the Admiralty Code only captures what their track record is
2. **Provenance chain** — how information reached the analyst (original observation? forwarded? scraped? purchased?)
3. **Timeliness** — a report from 3 hours ago vs 3 months ago carries different weight; not captured
4. **Handling restrictions** — UK 5x5x5 system adds a third axis: dissemination controls
5. **Source type classification** — human vs technical vs documentary; different reliability models

### 2.4 Proposed Framework: Tri-Axial OSINT Reliability Rating

Building on the Admiralty Code, I propose a three-axis framework:

**Axis 1: Source Reliability (A-F, Admiralty standard)**
- Same A-F scale, with one addition: a "P" (provisional) sub-notation for sources that have been partially vetted but lack full history. Example: "C-P" means fairly reliable based on limited interactions.

**Axis 2: Information Credibility (1-6, Admiralty standard)**  
- Unchanged. The corroboration-based scale works well for OSINT.

**Axis 3: Source Motivation (MICE-OSINT mapping)**

| MICE Category | OSINT Analogue | Reliability Implication |
|---------------|----------------|------------------------|
| Money | Paywalled commercial data, paid informants, sponsored content | Corroborate aggressively; financial bias |
| Ideology | Activist disclosures, partisan think tanks, advocacy orgs | Contextualize; ideologically-filtered but often factually accurate |
| Compromise | Breached/leaked data, whistleblower dumps, hacked materials | High authenticity but may be selective/curated |
| Ego | Self-promotional disclosures, "look what I found" social posts, researcher prestige | Verify before amplifying; ego-driven fabrication risk |
| Unknown | Anonymous sources with no discernible motivation | Default F6; requires structural corroboration |

**Axis 4 (metadata, not a rating): Timeliness + Provenance**
- Timestamp of collection + provenance shortcut (original, forwarded, scraped, purchased)

Example full rating: `C / 2 / IDEOLOGY / 2026-05-27T14:00Z / original`
- Fairly reliable source, probably true info, ideologically motivated, collected same-day, original observation.

### 2.5 Practical Implementation Notes

- **Default for all new OSINT**: F / 6 / UNKNOWN — until motivation, context, and corroboration status are assessed
- **Social media**: platform age, follower count, verification status, and prior accuracy can upgrade F to D or C without full HUMINT-style source validation
- **Automated collection**: scraped data from known-reliable databases (court records, corporate registries) can be rated B/1 by default, subject to freshness checks
- **Cross-domain**: the same framework applies to evaluating AI-generated intelligence — the "source" is the model+prompt+training data combination, and its reliability must be tracked independently

## 3. What I Think Is Interesting

**(a) OSINT doesn't just need source reliability — it needs a different kind of source reliability.** HUMINT sources develop track records through repeated interactions. Most OSINT sources are one-shot: a tweet, a leaked PDF, a satellite image. You can't build an A-F rating for a source you'll encounter exactly once. The framework must work backward from the information itself — provenance, motivation, internal consistency — to infer a provisional reliability rating without historical reinforcement.

**(b) MICE motivation analysis fills the track-record gap.** If you can't know whether a source is usually reliable because you've never seen them before, you can at least assess why they might be sharing information and what biases that introduces. This is exactly what journalists do when they ask "why is this person telling me this?" before deciding how heavily to weight a tip.

**(c) The Admiralty Code's independence principle is the killer feature.** The requirement to rate source reliability and information credibility separately prevents the most common analytical error — letting a trusted source's reputation contaminate the credibility assessment of their specific report. This principle maps perfectly to epistemic integrity in AI agent systems: an agent should treat each tool output independently, not let a "usually reliable" tool's output automatically inherit high confidence.

**(d) F6 is not a failure — it's a structural reality of OSINT that requires designing workflows around.** The fact that most OSINT starts at F6 means the framework must include a clear escalation path: what evidence moves F→D, D→C? What corroboration thresholds move 6→4, 4→2? These aren't theoretical questions — they are the daily work of OSINT analysis, and formalizing them would improve both human and automated OSINT workflows.

## 4. What I'd Explore Next

1. **Prototype an Exocortex evaluation plugin** that automatically assigns provisional Admiralty+MICE ratings to OSINT tool outputs
2. **Corroboration threshold research**: how many independent sources are needed to move from 6→4→2 for different OSINT data types?
3. **Social media source reliability heuristics**: can account age, engagement patterns, and network centrality predict reliability at scale?
4. **Integration with entity resolution**: entity confidence scores should incorporate source reliability — an entity resolved from a D/4 rated source should have lower confidence than one from B/2 sources
5. **Cross-framework comparison**: benchmark the tri-axial framework against the 5 Pillars of Verification and UK 5x5x5 on a shared OSINT case study

## 5. Cross-Domain Connections

### To Epistemic Integrity (Exocortex Core)
Source reliability grading is a direct implementation of epistemic integrity. An AI agent that treats all OSINT equally is epistemically dishonest. The Admiralty Code's independence principle — never let source reliability contaminate information credibility — is the structural equivalent of an agent maintaining separate confidence tracks for each piece of evidence.

### To Entity Resolution
Entity resolution confidence should be a function of source reliability. Resolving "John Smith" from a B/2 corporate registry + C/3 news article should produce a different confidence score than resolving from anonymous F/6 social media posts alone. The reliability framework provides the weighting function.

### To AI Agent Architecture
As agents increasingly perform autonomous OSINT collection, they need internal source reliability tracking. The tri-axial framework provides a structured metadata format that can be attached to every tool output — enabling downstream reasoning that distinguishes "probably true from a usually reliable source" from "unverifiable from an unknown source."

### To OSINT Investigation Methodology
This framework operationalizes the "source assessment" step in the intelligence cycle for OSINT. It transforms source evaluation from an implicit, experience-based judgment into an explicit, auditable rating — enabling structured disagreement between analysts and between human analyst and AI agent.

---

**Sources:**
- Jessica Stutzman, "The Admiralty Code / NATO 6x6 System" (Substack, Feb 24, 2026)
- Wikipedia, "Admiralty Code"
- NATO AJP-2.1, Edition B: Allied Joint Doctrine for Intelligence Procedures (2016)
- Prior field report: 20260526_humint-tradecraft-osint.md (MICE framework, HUMINT-OSINT mapping)
