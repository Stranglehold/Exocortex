# OSINT Source Reliability & Verification Tradecraft

**Status:** STABLE
**Created:** 2026-08-03
**Deepened:** 2026-08-03
**Domain:** OSINT & Investigation Methodology
**Related interests:** Human investigation tactics, source validation, entity resolution, evidence preservation

---

## Overview

Source reliability is the epistemic load-bearing layer of OSINT. Every conclusion in an investigation — entity attribution, timeline reconstruction, financial linkage — inherits the reliability of the sources beneath it. A single unvetted source can poison an otherwise sound evidence chain, while a properly rated source set lets an investigator weight conflicting claims and state confidence honestly. This page consolidates the reliability-rating doctrine scattered across the Exocortex corpus (Admiralty Code, Berkeley Protocol, threat intelligence lifecycle) into one operational tradecraft page.

Central thesis (from [[humint-tradecraft-osint]]): OSINT source validation and entity resolution are structurally isomorphic confidence-weighted corroboration loops. Rating is not a bureaucratic step — it is the mechanism that makes multi-source fusion sound.

---

## 1. The Admiralty Code (NATO Source Reliability & Information Credibility)

The Admiralty Code, developed by British Royal Navy intelligence during WWII and formalized during the Cold War, remains the standard two-dimensional rating system for intelligence analysis. It separates *who says it* from *how credible it is*.

| Dimension | Scale | Meaning |
|---|---|---|
| Source Reliability | A | Completely reliable |
| | B | Usually reliable |
| | C | Fairly reliable |
| | D | Not usually reliable |
| | E | Unreliable |
| | F | Cannot be judged |
| Information Credibility | 1 | Confirmed by other sources |
| | 2 | Probably true |
| | 3 | Possibly true |
| | 4 | Doubtful |
| | 5 | Improbable |
| | 6 | Cannot be judged |

**Canonical use in OSINT:** a platform account may be rated C (fairly reliable, unknown operator) while a corroborated official document is A. The two axes decouple source identity from content truth, preventing the common fallacy of treating "authoritative-looking" content as true.

---

## 2. Berkeley Protocol Corroboration Requirements

The Berkeley Protocol on Digital Open Source Investigations (OHCHR/UC Berkeley, 2022) is the most rigorous published framework for professional OSINT. Its Analysis phase explicitly includes source reliability assessment, content verification, and cross-source corroboration — including a two-source rule: a critical fact requires independent corroboration before it enters an evidence chain.

| Berkeley Protocol Element | HUMINT Equivalent |
|---|---|
| Corroboration requirement (two-source rule) | Independent verification of source reporting |
| Source reliability assessment | Admiralty Code A-F rating |
| Information credibility evaluation | Admiralty Code 1-6 rating |
| Chain of custody documentation | Intelligence report sourcing trail |
| Privacy and data minimization | Source protection and need-to-know access |

(from [[humint-tradecraft-osint]], grounded in v17 shared corpus)

The Protocol formalizes OSINT tradecraft to a standard comparable to HUMINT doctrine (FM 2-22.3). For Exocortex, it maps directly to the evidence chain-of-custody pipeline in [[evidence-preservation-chain-of-custody-osint]].

---

## 3. Tri-Axial OSINT Reliability Rating (2026 proposal)

The Exocortex field report `20260527_osint-source-reliability-framework` extends Admiralty into three axes plus metadata, addressing the gap that OSINT sources are usually *content*, not human report — so motivation matters:

**Axis 1 — Source Reliability (A-F):** Admiralty standard, with a **P** (provisional) sub-notation for partially vetted sources. Example: `C-P` = fairly reliable based on limited interactions.

**Axis 2 — Information Credibility (1-6):** unchanged Admiralty scale; corroboration-based.

**Axis 3 — Source Motivation (MICE-OSINT mapping):**

| MICE Category | OSINT Analogue | Reliability Implication |
|---|---|---|
| Money | Paywalled commercial data, paid informants, sponsored content | Corroborate aggressively; financial bias |
| Ideology | Activist disclosures, partisan think tanks, advocacy orgs | Contextualize; ideologically-filtered but often factually accurate |
| Compromise | Breached/leaked data, whistleblower dumps, hacked materials | High authenticity but may be selective/curated |
| Ego | Self-promotional disclosures, researcher prestige posts | Verify before amplifying; ego-driven fabrication risk |
| Unknown | Anonymous sources, no discernible motivation | Default F6; requires structural corroboration |

**Axis 4 (metadata, not a rating):** timeliness + provenance shortcut (`original`, `forwarded`, `scraped`, `purchased`).

Full example: `C / 2 / IDEOLOGY / 2026-05-27T14:00Z / original` — fairly reliable source, probably true, ideologically motivated, same-day, original observation.

---

## 4. Verification Workflow (5-phase)

1. **Source identification** — who published, who operates the account/domain, registration/history (see [[dns-whois-investigation-osint]], [[social-media-profile-investigation-osint]]).
2. **Reliability rating** — apply tri-axial rating before using content; default unknown to F6.
3. **Provenance trace** — determine original vs forwarded vs scraped; check timestamps and intermediate hops (see [[email-header-analysis]], [[data-lineage-provenance-entity-resolution]]).
4. **Independent corroboration** — two-source rule; seek channel diversity (different platform, organization, geography); weight by source independence, not volume.
5. **Confidence weighting & reassessment** — enter the [[analysis-of-competing-hypotheses-ach]] or entity-resolution loop; update ratings when new evidence binds or falsifies.

---

## 5. Grounding: Threat Intelligence Lifecycle

Reference-library grounding (Packt, *Practical Cyber Intelligence*, p.52-53, 286) places reliability evaluation inside the standard intelligence cycle: **Direction → Collection → Processing → Analysis → Dissemination**. The Processing step explicitly "evaluates the relevance and reliability of the data" before collation. The Dissemination step feeds back on the "relevancy and veracity" of finished intelligence, tuning the collector — the same feedback loop as Exocortex sleep consolidation.

OSINT feeds are a primary Collection source; reliability scoring is therefore not optional overhead but the Processing stage of the same discipline used in government and corporate CTI.

---

## 6. 2026 Automation & Agentic OSINT

- **Machine-readable ratings:** autonomous agents need reliability attached as metadata to evidence items, not buried in free-text notes; `rating: C-P` and `provenance: original` as first-class fields.
- **AI-content verification layer:** C2PA Content Credentials / SynthID provenance stack is now the primary verification layer for synthetic media (see [[deepfake-synthetic-media-verification-osint]]); a C2PA-unsigned AI-generated image rates low on Axis 1 unless the publisher is vetted.
- **Breach-data selectivity:** leak dumps are Compromise-motivated and frequently curated — high authenticity but selective (see [[data-breach-analysis-osint-identity-linkage]]); corroborate leak items against independent records before entity linkage.
- **Source-reliability decay:** ratings age; a source reliable in 2024 may be compromised or monetized by 2026. Counterintelligence doctrine from [[counterintelligence-analysis-frameworks]] applies: decay reliability on inactivity/suspicion, never assume permanence.
- **Handling vs reliability:** TLP (Traffic Light Protocol) governs *sharing handling*, not truth — do not confuse TLP:RED with "high reliability". They are orthogonal axes.

---

## 7. Cross-Domain Connections

1. **HUMINT tradecraft** — [[humint-tradecraft-osint]]: confidence-weighted corroboration loop isomorphism.
2. **Evidence preservation** — [[evidence-preservation-chain-of-custody-osint]]: chain of custody requires recorded sourcing trail; ratings are part of the record.
3. **Intelligence failure analysis** — [[intelligence-failure-analysis]]: source reliability neglect is a canonical failure pattern (Pearl Harbor, Iraq WMD).
4. **Fusion centers** — [[fusion-centers-multi-int-analysis]]: Admiralty Code is the source-rating standard in multi-INT fusion.
5. **Entity resolution safety** — [[entity-resolution-agent-safety]]: wrong-entity actions (24-26% despite 0% wrong-tool) are reliability failures of source binding.
6. **Counterintelligence** — [[counterintelligence-analysis-frameworks]]: Admiralty Code maps to tool confidence scoring / source reliability decay.
7. **Deepfake verification** — [[deepfake-synthetic-media-verification-osint]]: provenance stack as Axis 1 evidence.
8. **Data breach analysis** — [[data-breach-analysis-osint-identity-linkage]]: motivational axis for breach content.
9. **ACH structured analysis** — [[analysis-of-competing-hypotheses-ach]]: reliability-weighted hypothesis testing.
10. **Autonomous agent OPSEC** — [[autonomous-osint-agent-opsec-attribution-risk]]: an investigatoru2019s own tooling reliability affects source quality.

---

## 8. Tooling & Standards Table

| Standard / Tool | Role in Reliability Tradecraft |
|---|---|
| Admiralty Code (NATO) | Two-axis source + content rating |
| Berkeley Protocol (2022) | Professional methodology incl. two-source rule |
| TLP 2.0 | Handling/sharing marking (orthogonal to reliability) |
| C2PA / Content Credentials | Provenance & digital signature for media |
| W3C PROV | Machine-readable provenance graph |
| MICE framework | Motivational axis (adapted) |
| OSINT tri-axial rating (20260527 field report) | Extended rating for source + content + motivation |

---

## 9. References

1. Exocortex corpus: [[humint-tradecraft-osint]] (v17, Admiralty Code + Berkeley Protocol sections)
2. Field report: 20260527_osint-source-reliability-framework (tri-axial proposal)
3. Berkeley Protocol on Digital Open Source Investigations, OHCHR/UC Berkeley, 2022
4. Packt, *Practical Cyber Intelligence*, p.52-53, 286 (threat intelligence lifecycle)
5. Exocortex corpus: [[evidence-preservation-chain-of-custody-osint]], [[intelligence-failure-analysis]], [[fusion-centers-multi-int-analysis]]

*Grounded corpus-first in shared Exocortex memory + 355-book reference library; no live web used this cycle.*
