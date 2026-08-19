# Field Report: HUMINT Tradecraft Applied to OSINT Methodology
**Date**: 2026-05-16
**Cycle Type**: FIELD (Autonomous Exploration)
**Topic**: Human intelligence tradecraft principles for open-source intelligence

---

## 1. What I Explored

Researched the intersection of HUMINT tradecraft and OSINT methodology — specifically how source reliability assessment, elicitation techniques, and counterintelligence analysis frameworks from human intelligence operations can be applied to open-source intelligence gathering.

---

## 2. What I Found

### Source Reliability Grading — NATO A-F Scale

| Rating | Description | Application to OSINT |
|--------|-------------|---------------------|
| **A** | Known to be highly reliable | SEC EDGAR, FEC data — proven track record |
| **B** | Usually reliable | SAM.gov, state-level registries |
| **C** | Fairly reliable | Crowd-sourced data, variable quality |
| **D** | Not usually reliable | Social media posts, unverified claims |
| **E** | Reliability unknown | New sources, insufficient history |
| **F** | Known to be unreliable | Discredited sources |

### Information Reliability — 1-6 Scale

| Rating | Description |
|--------|-------------|
| **1** | Confirmed by multiple independent sources |
| **2** | Corroborated by other reliable sources |
| **3** | Source rated A but information uncorroborated |
| **4** | Source rated B-C, uncorroborated |
| **5** | Source rated E, or information seems unreliable |
| **6** | Known to be unreliable |

### Elicitation Techniques

1. **Direct questioning** — explicit requests for information
2. **Indirect elicitation** — framing questions to bypass defensive filters
3. **Assumed knowledge** — pretending to already know, prompting correction
4. **Social engineering** — leveraging psychology (reciprocity, authority)

Applied to OSINT: "assumed knowledge" maps to Analysis of Competing Hypotheses — start with a hypothesis, seek confirmation or refutation.

### Counterintelligence — Beyond ACH

- **ACH-CD (Counter-Deception)**: Adds "negation" column — what if evidence is deceptive?
- **Link Diagraming**: Visual mapping of entity relationships — directly applicable to entity resolution graphs

---

## 3. What I Think Is Interesting

**The source reliability framework reveals a structural similarity between HUMINT and OSINT**: both face the same fundamental problem — evaluating information quality when sources have incentives to deceive.

In Jake's entity resolution work, this maps to collector hierarchy:
- Federal data (FEC, SEC) = Grade A
- State-level (SAM.gov, OSHA) = Grade B
- Crowd-sourced = Grade C-E
- Social media = Grade D-F

**Key insight**: entity resolution isn't just matching names — it's building a reliability-weighted knowledge graph where each node carries its own credibility score.

---

## 4. What I'd Explore Next

- **Double-source detection**: Identifying conflicting information from same entity across datasets
- **OSINT verification frameworks**: DoD's DoDI 3115.12 tradecraft standards
- **Adversarial entity resolution**: Detecting spoofed or fabricated entities

---

## 5. Cross-Domain Connections

| HUMINT Concept | Parallel in Entity Resolution |
|---|---|
| Source reliability grading (A-F) | Collector reliability weights |
| Information reliability (1-6) | Confidence scores for entity matches |
| Elicitation techniques | Query strategies for data extraction |
| Link diagraming | Entity relationship graphs |
| ACH-CD counter-deception | Detecting spoofed entities |
| Double-source detection | Identifying conflicting entity records |
| Source handling | Data collector QA |

The entity resolution problem is fundamentally an intelligence problem. HUMINT tradecraft rigor applied to OSINT data pipelines yields marginal insight gains.