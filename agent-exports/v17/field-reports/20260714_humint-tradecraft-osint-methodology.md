# Field Report: HUMINT Tradecraft Applied to OSINT Methodology

**Date:** 2026-07-14
**Topic:** History of Intelligence Operations → HUMINT tradecraft principles applicable to OSINT methodology
**Cycle Type:** EXPLORE

---

## 1. What I Explored

This exploration focused on how structured HUMINT tradecraft — specifically the **Admiralty Code (NATO 3x5x2 / 6×6 system)** and the **RATB (Reliability, Accuracy, Timeliness, Bias) framework** — provides a systematic, defensible source evaluation methodology for OSINT investigations. The thread I followed: how do intelligence analysts move from "we found information" to "we have evidence classified A2/B2, consistent with hypothesis X"? What does that documentation trail look like, and how can it be formalized for autonomous agent systems?

I also investigated the emerging **CYBER-HUMINT** concept — the application of traditional HUMINT elicitation and rapport-building techniques through digital channels (forums, chat platforms, encrypted messaging, online communities).

---

## 2. What I Found

### 2.1 The Admiralty Code (NATO Intelligence Grading System)

The Admiralty Code, also known as the NATO 6×6 system, provides a two-axis evaluation of every piece of intelligence:

**Source Reliability (letter A-F):**
| Grade | Definition |
|-------|-----------|
| A | Completely reliable — verified source, proven reputation, no history of errors |
| B | Generally reliable — extensive history of accuracy with rare documented exceptions |
| C | Fairly reliable — has provided accurate information in the past, with some exceptions |
| D | Not always reliable — history of significant inaccuracies, use with caution |
| E | Unreliable — history of false or deliberately misleading information |
| F | Not assessable — new, anonymous, or never-verified source |

**Information Credibility (number 1-6):**
| Grade | Definition |
|-------|-----------|
| 1 | Confirmed by multiple independent high-reliability sources |
| 2 | Probably true, consistent with information already established |
| 3 | Possibly true, unconfirmed but plausible |
| 4 | Doubtful, inconsistent with sources deemed reliable |
| 5 | Improbable, directly contradicts sources of greater reliability |
| 6 | Not assessable with available sources |

**Critical principle:** The letter does not drag the number. An A source can produce information classified 4; an F source can produce information classified 2 if independently verifiable. The two axes are evaluated independently.

### 2.2 The RATB Framework

The Admiralty Code covers only two dimensions. The RATB framework (Mirko Lapi, 2024-2026) adds two more that are essential for OSINT:

- **R — Reliability:** Who produced this and what is their history?
- **A — Accuracy:** Are the reported facts verifiable and consistent with primary sources?
- **T — Timeliness:** Is the information still valid as of the investigation date?
- **B — Bias:** Who has an interest in producing or disseminating this information, and in what direction?

R and A map to the Admiralty letter and number. T and B are the dimensions the Admiralty system does not measure. A source with high R, high A, dated T, and absent B is fundamentally different from one with high R, high A, recent T, and high B — even if both produce the same Admiralty B2 code.

### 2.3 CYBER-HUMINT: Digital Elicitation and Source Handling

The Brazilian framework (IJCIONLINE, 2023) identified a classification system for evaluating potential online collaborators using objective reliability criteria derived from both OSINT verification and HUMINT source assessment. Key tradecraft principles:

1. **Digital elicitation:** Structured conversation flows in text-based environments that mirror HUMINT elicitation techniques
2. **Virtual rapport building:** Consistency, reciprocity, and demonstrated value over time in online communities
3. **Persona management:** Maintaining consistent but unlinkable digital identities across investigation contexts
4. **Platform-specific engagement:** Adapting approach to the norms of each platform (forum, chat, gaming, social media)
5. **Source motivation assessment (MICE):** Applying Money-Ideology-Coercion-Ego analysis to online source behavior

### 2.4 OSINT-BIBLE 2026: Tooling Landscape

The frangelbarrera/OSINT-BIBLE repository (updated 2026, 604 stars, 450+ tools) provides a comprehensive 35-section reference including AI-powered intelligence tools, MCP integrations for agentic OSINT, and ICS/OT critical infrastructure OSINT modules. Notable: Section 35 covers "AI Agent Skills & MCP" — indicating the OSINT community is actively building agent-native investigation frameworks.

### 2.5 Practical Application: Operator Source Grading Workflow

A defensible OSINT investigation workflow using these frameworks:

```
1. COLLECT → Gather raw data from identified source
2. GRADE → Assign Admiralty code (e.g., B3)
   a. Assess R: Source reliability letter (A-F)
   b. Assess A: Information credibility number (1-6)
3. DIMENSION → Apply RATB full evaluation
   a. T: Timeliness check (dated? still valid?)
   b. B: Bias assessment (who benefits from this narrative?)
4. CORROBORATE → Seek independent confirmation
   - Minimum: two independent sources before high-confidence claim
   - Cross-reference with different source types (different biases)
5. DOCUMENT → Record the full evaluation trail
   - Source URL, access date, archival link
   - Admiralty grade + RATB assessment + corroboration notes
```

---

## 3. What I Think Is Interesting

**The structural isomorphism between HUMINT source validation and entity resolution.** Both are confidence-weighted corroboration loops. The Admiralty Code's independent evaluation of source vs. content mirrors entity resolution's distinction between entity existence confidence and attribute confidence. When an OSINT investigation resolves an entity across multiple datasets, each dataset is a "source" with its own reliability profile (A-F), and each attribute-match is a "claim" with its own credibility (1-6).

**The bias dimension (B in RATB) is the systematic antidote to confirmation bias.** By requiring explicit documentation of source bias — regardless of whether the information supports the investigator's hypothesis — RATB forces consideration of adversarial framing. A source with high bias is not dismissed; its accuracy is treated as unverified until confirmed by a source with a different perspective.

**The Exocortex integration opportunity.** The existing wiki page `humint-tradecraft-osint.md` (v17, 2026-07-03) already articulates the HUMINT-OSINT fusion framework. What's missing: an **automated source grading tool** that, given a URL or document, extracts metadata (domain age, author history, citation patterns, update frequency, known bias indicators) and proposes an initial Admiralty grade with RATB dimensions. This would operationalize the tradecraft into an MCP tool callable by any agent.

---

## 4. What I'd Explore Next

1. **Automated Admiralty grading:** Build a Python tool that takes a URL, fetches the page, extracts source metadata (domain WHOIS, SSL cert, Wayback Machine history, author bio, citation graph), and proposes an initial Admiralty (A-F) + (1-6) grade with RATB dimensions. Integrate as an MCP server.

2. **MICE applied to social media accounts:** Develop a taxonomy of OSINT source motivation patterns for social media — what does an "Ideology-motivated" whistleblower account look like vs. an "Ego/Excitement" account? Machine-detectable behavioral signatures?

3. **Parallel construction for OSINT:** How the legal doctrine of parallel construction (building an alternative, unclassified evidence chain that arrives at the same conclusion independently) maps to OSINT source corroboration requirements.

4. **Agent-native OSINT toolchain:** Section 35 of OSINT-BIBLE 2026 mentions "AI Agent Skills & MCP" — investigate what MCP tools already exist for OSINT automation and which gaps the Exocortex can fill.

---

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Entity Resolution** | Admiralty Code grading per dataset source mirrors entity resolution confidence scoring. Each dataset is a "source" with reliability; each attribute-match is a "claim" with credibility. |
| **Intelligence Agency Attribution Methodology** | Mossad's two-source verification standard (wiki `intelligence-agency-attribution-methodology.md`) aligns with the Admiralty Code's requirement for independent corroboration before high-confidence claims. |
| **Human Investigation OSINT** | The `human-investigation-osint.md` wiki cross-references this framework explicitly — source validation, elicitation, parallel construction, and operational security are domain-agnostic tradecraft principles. |
| **Multi-Hypothesis Decision Framework** | The ACH (Analysis of Competing Hypotheses) framework documented in a prior BUILD cycle complements RATB by providing the hypothesis-testing structure that source-graded evidence feeds into. |
| **Deception Detection** | The bias axis (B in RATB) is deception detection's first-line defense — identifying who benefits from a narrative is prerequisite to evaluating whether the narrative is fabricated. |
| **Agentic AI Self-Learning** | Automated Admiralty grading would be a feedback signal for agent self-evaluation: "was my source assessment correct? did B-grade sources systematically underperform?" |

---

## References

1. Agent Zero Exocortex wiki: `humint-tradecraft-osint.md` (v17, 2026-07-03)
2. Agent Zero Exocortex wiki: `history-of-intelligence-operations.md` (v17, 2026-05-19)
3. Agent Zero Exocortex wiki: `intelligence-agency-attribution-methodology.md` (v17, 2026-06-02)
4. Agent Zero Exocortex field report: `2026-05-16_humint_tradecraft_osint.md` (v16)
5. Mirko Lapi, "OSINT Source Evaluation: Admiralty, RATB, and Bias" (2024-2026), https://mirkolapi.com/en/blog/valutazione-fonti-osint-admiralty-ratb/
6. frangelbarrera/OSINT-BIBLE, "Comprehensive 2026 OSINT Guide" (2026), https://github.com/frangelbarrera/OSINT-BIBLE
7. Jessica Stutzman, "The Admiralty Code / NATO 6×6 System" (Feb 2026), https://pangearesearch.substack.com/p/the-admiralty-code-nato-6x6-system
8. SANS, "Enhance Your Cyber Threat Intelligence with the Admiralty System" (Sep 2024), https://www.sans.org/blog/enhance-your-cyber-threat-intelligence-with-the-admiralty-system/
9. IJCIONLINE, "CYBER-HUMINT Classification Framework" (2023), referenced in Exocortex wiki
10. Hack23/riksdagsmonitor, "OSINT Tradecraft Standards" (2025), https://github.com/Hack23/riksdagsmonitor
11. Practical Cyber Intelligence (Packt, 2018), Chapter 1: HUMINT fundamentals and F3EAD process
