# Elicitation Tradecraft: Non-Interrogative Intelligence Collection

**Status: DRAFT → STABLE**
**Last updated: 2026-08-18**

## Overview

Elicitation is the intelligence-discipline skill of extracting information through structured conversation **without the source realizing the target of collection**. Unlike interrogation — where the subject knows they are being questioned and the interaction is adversarial — elicitation works through normal-appearing dialogue, exploiting universal social-psychological mechanisms: the desire to correct errors, the flattery of being seen as an expert, and the ritual of reciprocal small talk. It is the HUMINT technique most directly transferable to OSINT because it is fundamentally a **question-design discipline**: control the information environment without controlling the person.

This page consolidates prior HUMINT/elicitation work (20260529 techniques field report, 20260703 HUMINT-to-OSINT field report, 20260714 cyber-HUMINT methodology, humint-tradecraft-osint wiki page) into a discipline-level treatment and extends it with 2026 LLM-era evidence.

## 1. Why elicitation matters: collection without coercion

- **Stealth is structural, not cosmetic.** The source is unwitting; there is no deniability problem, no interrogation ethics bar, and no transcript that looks like a collection event. The information reveals itself in normal social exchange.
- **Efficiency against open targets:** in business, conference, and online-community settings, most people voluntarily disclose more than operational security allows. Elicitation converts those natural disclosures into collection.
- **Counterintelligence relevance:** CI programs train personnel to recognize elicitation precisely because it is the favored collection method against cleared employees, travelers, and researchers. The defense maps 1:1 to the offense.

## 2. Core psychological mechanisms

- **Correction impulse** — the strongest documented driver: people cannot tolerate an actionable false statement in their domain of expertise. The elicitor states a plausible-but-wrong fact; the target corrects it, revealing the truth. (Balthatsar 2024; CDSE "Accidental Conversations"; FBI CI Division elicitation brochure). Three variants: mildly-wrong claim, misattributed source, exaggerated figure.
- **Rapport-as-prerequisite** — police source-handler research (PMC 2021) confirms rapport is "fundamental to the success of intelligence elicitation". Rapport is built through demonstrated domain knowledge (credibility), norm-conforming small talk (predictability), and mutual self-disclosure (reciprocity).
- **Ego and expertise bait** — people disclose to be seen as experts, insiders, or helpful. "You probably wouldn't know — this is pretty specialized" is a direct invitation.
- **Feigned ignorance** — the inverse of bait: the elicitor plays naive and invites the target to educate them, leveraging the teaching impulse.
- **Quoting a third party** — attributing a claim to "a friend / a colleague / something I read" lowers the target's guard because correction no longer feels personal; it also gives the target a face-saving frame.
- **Conversational norms** — reciprocity obligations, question-answer adjacency, and discomfort with silence in social settings all create pressure to fill gaps with information.

## 3. Technique taxonomy (20-technique CDSE family, grouped)

| Group | Example techniques | Psychological lever |
|---|---|---|
| Correction family | False statement, misquote, exaggerated figure | Correction impulse |
| Ego family | Flattery, expertise bait, appeal to insider status | Ego/status |
| Ignorance family | Feigned ignorance, help me think through this | Teaching impulse |
| Attribution family | Third-party quote, rumor relay | Attribution shielding |
| Reciprocity family | Self-disclosure, small concessions, gift of information | Reciprocation |
| Challenge family | Direct challenge, devil's advocate | Contrarian impulse |
| Context family | Casual settings, travel chat, conference bar | Guard reduction |

Operational sequencing: **establish baseline → build rapport → open-ended broad questions → narrow progressively → terminate naturally.** Never telegraph the true target; keep every question individually innocuous and collectively diagnostic.


## 4. Business and private-sector adaptation

- The same six core techniques (correction, flattery, feigned ignorance, third-party quote, self-disclosure, direct challenge) appear in commercial competitive-intelligence and sales training (van Helzing 2024).
- Law-enforcement and regulatory investigators use elicitation in interviews before rights warnings when lawful and ethical boundaries permit.
- **Security awareness countermeasure:** organizations now teach employees the warning patterns: too-flattering interest in technical details, politely wrong statements in one's field, requests to "just double-check" figures, and conversations that drift back to work topics.

## 5. Cyber-HUMINT and digital elicitation (2023-2026)

- **Digital elicitation** is structured conversation flows in text-based environments mirroring HUMINT elicitation (Brazilian IJCIONLINE 2023 framework).
- **Virtual rapport building** uses consistency, reciprocity, and demonstrated value over time in online communities — slower than in-person, but persistent and logged.
- **Persona management** and **platform-specific engagement** (forum/chat/gaming/social media) adapt approach norms per venue.
- **Digital Case Officer** (SCSP 2025 proposal): AI-augmented HUMINT using LLMs for cover identity development, behavioral analysis, and communication-pattern recognition in CIA/FBI/DIA operations.
- **C-HUMINT:** Hungarian security studies (Belügyi Szemle 2020) treat OSINT, SOCMINT, and social engineering as intertwined with no fixed conceptual boundaries.

## 6. LLM-era evidence and agent isomorphism

- **Behavioral elicitation as red-team method:** modern LLM evaluation elicits target behaviors via multi-turn interaction; online methods recover failure cases static single-turn benchmarks miss (45/19/77% success with a few thousand queries across three tasks, arXiv). The method family (prior-knowledge / offline-interaction / online-learning) mirrors human elicitation's move from prepared gambits to adaptive conversational probing.
- **LLMs are poor elicitors of implicit needs:** ReqElicitGym (arXiv:2602.18306, 2026) shows current LLMs elicit *less than half* of users' implicit requirements in conversational requirements elicitation, and effective questions emerge only in later dialogue turns — an empirical gap directly parallel to the correction-impulse/deniability gap in human elicitation.
- **Isomorphism to agent tool-use:** conversational elicitation is a budgeted information-acquisition loop — each question is a query with a cost and a marginal-information return, exactly like agentic tool selection. The known failure (delaying effective questions) is an agent-search-policy failure, not a language failure.
- **OSINT application:** phased questioning without telegraphing the true target is already standard practice in the team's HUMINT-to-OSINT mapping; LLM-era chat interfaces (support bots, community AI assistants) are emerging unwitting elicitation surfaces — both for defenders (test what they leak) and investigators (interact to confirm entity details).


## 7. Defense and counter-elicitation

- Recognition training: CDSE job aids, FBI CI Division brochures, and corporate insider-threat curricula teach the same warning signs (unusual interest, false statements, excessive flattery, probing questions outside the conversation's frame).
- Structural controls: compartmentalization, need-to-know, and the OPSEC habit of asking "why does this person need this?" before answering.
- **Agent defense analogue:** the irreversibility-gate and entity-aware-action-gate architecture is the autonomous counterpart to human counter-elicitation — it gates disclosure by utility and trust, not by impulse.

## 8. Cross-domain connections (10)

1. [[humint-tradecraft-osint]] — MICE, source handling, Admiralty Code; parent discipline page
2. [[human-investigation-tactics]] — PEACE model vs Reid; cognitive interviewing
3. [[autonomous-osint-agent-opsec-attribution-risk]] — OPSEC boundary; asking vs being asked
4. [[social-engineering-detection]] — defense taxonomy overlap
5. [[influence-operations-detection-countermeasures]] — narrative manipulation as mass elicitation
6. [[intelligence-failures-strategic-surprise]] — collection is not the bottleneck; elicitation is collection
7. [[agentic-deep-research-pipelines]] — budgeted question policies
8. [[entity-resolution-agent-safety]] — entity-aware action gating as counter-elicitation for agents
9. [[brand-protection-osint]] — impersonation as elicitation vector
10. [[clandestine-communications-tradecraft]] — comms-layer counterpart to conversation-layer tradecraft

## 9. References

- CDSE Counterintelligence, "Accidental Conversations" job aid (20 elicitation techniques)
- FBI Counterintelligence Division, Elicitation brochure
- Balthatsar, "The Art of Elicitation (CIA Trick)" (2024) — correction-impulse mechanics
- van Helzing, "The Art of Elicitation: Intelligence Tradecraft for Business" (2024)
- Agent Zero field report 20260529_humint-elicitation-techniques
- Agent Zero field report 20260703_humint-tradecraft-osint (PMC 2021 rapport finding)
- Agent Zero field report 20260714_humint-tradecraft-osint-methodology (IJCIONLINE 2023 cyber-HUMINT)
- Paludan et al., "If we misunderstand the client, we misspend 100 hours" — conversational AI and response types for information elicitation (arXiv)
- "Behavior Elicitation in Multi-Turn Conversations" (arXiv) — online behavior elicitation 45/19/77%
- Jin et al., "ReqElicitGym: An Evaluation Environment for Interview Competence in Conversational Requirements Elicitation" (arXiv:2602.18306, 2026)

*Library grounding note: the shared 355-book library contains HUMINT/cyber-intelligence taxonomy (Practical Cyber Intelligence, Packt) but no dedicated elicitation-depth title — an honest gap; the book is cited for HUMINT collection-methods context.*
