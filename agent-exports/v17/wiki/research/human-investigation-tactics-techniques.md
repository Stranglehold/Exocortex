# Human Investigation Tactics and Techniques

**Status:** STABLE
**Created:** 2026-06-02
**Deepened:** 2026-06-02 07:07 EDT
**Topic:** OSINT & Investigation Methodology
**Parent interest:** Human investigation tactics and techniques

## Overview

Human investigation tactics are the mental models, cognitive frameworks, and procedural techniques used by skilled investigators across domains — law enforcement, intelligence analysis, journalism, and private investigation. These techniques predate digital tools and form the cognitive foundation that AI-assisted investigation systems must augment, not replace. Understanding how human investigators think is prerequisite to building tools that extend their capabilities.

This page catalogs core tactics, cognitive frameworks, procedural patterns, and their mapping to Exocortex capabilities.

---

## 1. The Investigative Mindset

### 1.1 Core Dispositions

The investigative mindset is not a single technique but a constellation of dispositions identified across law enforcement and intelligence analysis standards:

- **Skepticism without cynicism** — question every claim, but remain open to evidence that contradicts initial assumptions
- **Intellectual humility** — acknowledge the limits of one's knowledge; uncertainty is not failure, it is precision
- **Persistence** — follow leads beyond the point of convenience; investigative breakthroughs often occur after initial dead ends
- **Pattern recognition** — identify anomalies, repetitions, and structural similarities across disparate data sources
- **Source awareness** — maintain explicit mental models of source reliability, bias, and access limitations

### 1.2 Cognitive Biases in Investigation

Human investigators are vulnerable to cognitive biases that AI systems must detect and compensate for:

| Bias | Description | Mitigation |
|------|-------------|------------|
| Confirmation bias | Seeking evidence that supports existing hypothesis | Mandatory dissent channels, ACH |
| Anchoring | Fixating on initial information despite contradictory evidence | Key Assumptions Check, periodic reset |
| Availability heuristic | Overweighting vivid or recent information | Structured evidence weighting |
| Groupthink | Consensus-seeking in team investigations | Devil's Advocacy, anonymous input |
| Satisficing | Accepting the first adequate explanation | Multi-hypothesis tracking |

---

## 2. Cognitive Frameworks for Investigation

### 2.1 Analysis of Competing Hypotheses (ACH)

Developed by Richards Heuer at CIA, ACH is the gold-standard structured analytic technique for investigation:

1. **Identify all plausible hypotheses** — not just the most likely one
2. **List evidence for and against each hypothesis** — including absent evidence (what should be there but isn't)
3. **Build a diagnostic matrix** — which evidence discriminates between hypotheses?
4. **Refine the matrix** — reconsider hypotheses, add new evidence, delete disproven hypotheses
5. **Draw tentative conclusions** — based on which hypothesis has the fewest inconsistent items
6. **Analyze sensitivity** — how would the conclusion change if key evidence were wrong?
7. **Report conclusions with confidence levels** — not binary true/false

ACH maps directly to Exocortex's epistemic-integrity layer: evidence → validation matrix → confidence score → auditable conclusion.

### 2.2 Key Assumptions Check

Every investigation rests on unstated assumptions. A Key Assumptions Check surfaces them:

1. List all working assumptions (including the ones that seem obvious)
2. For each: why am I confident this is true? What would invalidate it?
3. Identify which assumptions, if wrong, would change the conclusion
4. Assign a confidence level to each assumption
5. Monitor assumptions for signs of invalidation during the investigation

### 2.3 Indicators and Signposts

Rather than predicting outcomes, skilled investigators identify observable indicators:

- **Indicators** — observable events that would signal a hypothesis is correct or incorrect
- **Signposts** — periodic checkpoints where indicators are reviewed
- This technique is particularly valuable for ongoing investigations where the situation evolves

### 2.4 Devil's Advocacy and Red Teaming

Structured dissent prevents groupthink and confirmation bias:

- **Devil's Advocacy** — one team member explicitly argues against the prevailing conclusion
- **Red Teaming** — an independent team attempts to defeat the investigation's conclusions using the same evidence
- **Adversarial Hypothesis** — CIA's method: create a competing hypothesis and attempt to prove it

These techniques map to Exocortex's supervisor-loop dissent channel and SWARMFISH committee structure.

---

## 3. FBI Behavioral Analysis Methods

The FBI's Behavioral Analysis Unit (BAU) applies psychological research and operational experience to criminal investigation:

### 3.1 Criminal Investigative Analysis

- **Crime scene analysis** — reconstructing behavior from physical evidence
- **Modus operandi (MO) vs. signature** — MO is learned behavior that evolves; signature is psychological need that remains stable
- **Victimology** — comprehensive analysis of the victim's background, lifestyle, and risk factors
- **Geographic profiling** — analyzing crime location patterns to infer offender base location

### 3.2 Threat Assessment

- **Structured Professional Judgment (SPJ)** — evidence-based risk factors combined with clinical judgment
- **Pathway to Violence model** — grievance → ideation → research/planning → preparation → breach → attack
- **Leakage analysis** — communications that reveal intent before action

### 3.3 Investigative Interviewing

Modern investigative interviewing has moved from accusatorial models (Reid Technique) to information-gathering models:

| Model | Approach | Used By |
|-------|----------|---------|
| **PEACE Model** | Planning, Engage/Explain, Account, Closure, Evaluation — non-accusatorial, cognitive interviewing | UK, Australia, New Zealand, Norway |
| **Cognitive Interviewing** | Context reinstatement, report everything, reverse order, change perspective | International standard |
| **Reid Technique** | Behavior Analysis Interview + 9-step interrogation — accusatorial, designed to elicit confessions | Historically US, declining |
| **HIG (High-Value Detainee Interrogation Group)** | Rapport-based, information-gathering, science-based | US federal agencies |

Key principle: the PEACE model and cognitive interviewing produce more accurate information with fewer false confessions than accusatorial approaches.

---

## 4. The Intelligence Cycle

Derived from the College of Policing and IALEIA Law Enforcement Analytic Standards (2026):

### 4.1 Traditional Five-Phase Cycle

1. **Direction** — Define intelligence requirements. What do decision-makers need to know? What is the acceptable evidence threshold?
2. **Collection** — Gather raw data from all available sources (HUMINT, SIGINT, OSINT, public records, physical evidence)
3. **Processing** — Collate, evaluate relevance, verify facts/dates/names, identify gaps
4. **Analysis** — Integrate processed information, apply structured techniques, produce intelligence products
5. **Dissemination** — Deliver intelligence to consumers in usable format with confidence ratings

### 4.2 TCPED Extension (Modern Adaptation)

- **Tasking** — formalized requirements process
- **Collection** — multi-INT fusion
- **Processing & Exploitation** — technical processing of collected data
- **Analysis & Production** — analytic judgment with structured methodology
- **Dissemination** — timely delivery to decision-makers

### 4.3 IALEIA Analytic Standards (2026)

The International Association of Law Enforcement Intelligence Analysts defines five core standards:

1. **Objectivity** — analysts must not bias analysis to support a preferred outcome
2. **Timeliness** — analysis must be delivered in time to inform decisions
3. **Accuracy** — conclusions must be supported by evidence and updated as new information arrives
4. **Relevance** — analysis must address the stated intelligence requirement
5. **Source transparency** — reliability ratings and access limitations documented explicitly

---

## 5. Decision-Making Frameworks

### 5.1 National Decision Model (NDM) — UK Policing

The NDM structures police decision-making as a fluid cognitive continuum:

1. **Gather information and intelligence**
2. **Assess threat and risk** and develop a working strategy
3. **Consider powers and policy** — what's legally authorized?
4. **Identify options and contingencies**
5. **Take action and review**

The NDM emphasizes that naturalistic (intuition-based) and rational (analysis-based) decision-making operate on a continuum, not a binary toggle.

### 5.2 OODA Loop (Observe-Orient-Decide-Act)

Developed by Col. John Boyd for air combat, adopted broadly in investigation and business:

- **Observe** — gather data from all available sensors
- **Orient** — contextualize data within mental models, experience, and cultural awareness
- **Decide** — select a course of action from available options
- **Act** — execute, then observe results and loop

The key insight: speed through the loop matters more than perfect decisions. The investigator who iterates faster gains an asymmetric advantage.

### 5.3 Evidence-Based Policing

- **Systematic use of research** in investigative decision-making
- **Randomized controlled trials** (RCTs) for investigative techniques
- **Data-driven resource allocation** — investigate where the evidence indicates impact
- **Crime science principles** — repeat victimization, hot spots, problem-oriented policing

---

## 6. Investigation Patterns and Heuristics

### 6.1 Timeline Reconstruction

- Build a chronological scaffold with known events as anchor points
- Fill gaps with probable sequences based on pattern-of-life data
- Flag interpolation vs. verified facts
- Use multiple independent sources to confirm each timestamp

### 6.2 Link Analysis and Network Mapping

- Map relationships between entities (people, organizations, locations, vehicles)
- Identify central nodes, bridges, and peripheral actors
- Apply social network analysis metrics (betweenness centrality, degree centrality)
- Recognize that absence of a link is also information

### 6.3 Pattern-of-Life Analysis

- Establish baseline behaviors for persons of interest
- Identify deviations from baseline as investigative triggers
- Integrate temporal, spatial, and transactional data
- Apply across domains: financial, communications, physical movement

### 6.4 Anomaly Detection

- Define the expected pattern
- Identify deviations with statistical significance
- Distinguish noise from signal — not every anomaly is meaningful
- Investigate anomalies; do not assume explanations

---

## 7. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Structured Analytic Techniques** (structured-analytic-techniques-osint) | ACH, Key Assumptions Check, Indicators/Signposts, and Devil's Advocacy are the formalized toolkit of investigative cognition |
| **HUMINT Tradecraft** (humint-tradecraft-osint) | Source handling, elicitation, rapport-based interviewing, and assessment techniques adapted from intelligence |
| **Counterintelligence Analysis** (counterintelligence-analysis-frameworks) | Deception detection, Admiralty Code source reliability, CI-ACH for agent investigation |
| **Public Records OSINT** (public-records-databases-osint) | Property, court, and business records feed pattern-of-life analysis and link analysis |
| **Collection Management** (collection-management-intelligence-cycle) | TCPED cycle structures multi-source investigation workflow |
| **Epistemic Integrity** (epistemic-integrity) | Human cognitive bias mitigation maps directly to Exocortex evidence-claim auditing |
| **Agent Memory Architecture** (agent-memory-architecture) | Timeline reconstruction and pattern-of-life analysis require episodic memory with temporal indexing |
| **SWARMFISH** (swarmfish) | Devil's Advocacy and Red Teaming are structurally identical to SWARMFISH's dissenter-analyst convergence |

---

## 8. Exocortex Integration: Human Tactics as Agent Architecture

Human investigation tactics provide the architectural template for AI-assisted investigation. The pattern is consistent across every technique:

1. **Structured process** — every technique is a defined sequence, not ad-hoc reasoning
2. **Evidence preservation** — chain of custody and source documentation are non-negotiable
3. **Multi-source triangulation** — no claim stands on single-source evidence
4. **Confidence qualification** — conclusions carry explicit uncertainty ratings, not binary truth
5. **Dissent institutionalization** — mandatory challenge mechanisms prevent groupthink
6. **Iterative refinement** — conclusions update as new evidence arrives (OODA loop)

These principles are architecture-level constraints for Exocortex investigation subsystems, not optional features.

---

## References

1. IALEIA — "Law Enforcement Analytic Standards" (2026) — five core standards for intelligence analysis: objectivity, timeliness, accuracy, relevance, source transparency
2. FBI — "Behavioral Analysis" (fbi.gov/how-we-investigate/behavioral-analysis) — criminal investigative analysis, threat assessment, behavioral science integration
3. Heuer, Richards J. — "Psychology of Intelligence Analysis" (CIA, 1999) — foundational text on cognitive biases in investigation and ACH methodology
4. National Decision Model — UK College of Policing — structured decision-making framework for law enforcement
5. PEACE Model — UK National Crime Agency — non-accusatorial investigative interviewing framework adopted internationally
6. IALEIA/Global Justice Information Sharing Initiative — "Law Enforcement Analytic Standards" (2nd Edition) — analytic tradecraft standards
7. Boyd, John — OODA Loop — observe-orient-decide-act cycle, adopted from military strategy to investigation
8. Sherman, Lawrence — "Evidence-Based Policing" — systematic use of research in investigative decision-making
9. National Institute of Justice — "Law Enforcement Investigations" (nij.ojp.gov) — research-based investigative procedures and forensic advances
10. Police Chief Magazine — "Investigative Techniques" (June 2025) — AI applications and academic collaborations revolutionizing investigations
11. College of Policing — "Intelligence Cycle" APP — tactical intelligence requirements and analytic tradecraft
12. ScienceDirect — "Decision-Making Framework for Policing" (DMFP, 2024) — heuristic-naturalistic-rational decision continuum
