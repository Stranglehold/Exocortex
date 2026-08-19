# Field Report: HUMINT Tradecraft Principles Applicable to OSINT Methodology

**Date:** 2026-07-03
**Topic:** HUMINT tradecraft principles adapted for OSINT methodology
**Cycle:** EXPLORE

---

## 1. What I Explored

I investigated how traditional Human Intelligence (HUMINT) tradecraft — elicitation, source development, cover identity management, and operational security — translates into digital OSINT investigation methodology. The specific thread: where does OSINT end and HUMINT begin when investigations move into online spaces? This question matters for Exocortex's investigation capabilities and for understanding the legal/ethical boundaries that constrain autonomous agent research.

## 2. What I Found

### The OSINT-HUMINT Boundary is Doctrinally Clean, Operationally Messy

Jessica Stutzman's Intelligence Fundamentals Project (Feb 2026) provides the clearest framework: **OSINT is observation; HUMINT is engagement.** The distinction hinges on a single question: are you reading what is already public, or are you interacting with a human being to extract information they would not otherwise disclose?

Key doctrinal anchors:
- **JP 2-0** (Joint Publication 2-0): HUMINT is "intelligence derived from information collected and provided by human sources"; OSINT is "produced from publicly available information" (Public Law 109-163)
- **DoD Directive 3115.18**: Publicly Available Information (PAI) is information "published or broadcast for public consumption," "accessible online to the public," or "obtained by visiting a place or attending an event open to the public"
- **OSINT Foundation (2022)**: "PAI collection... does not directly interact with the target or source to elicit a response" — this single sentence draws the line
- **FM 2-22.3** (Army HUMINT doctrine): elicitation is "the acquisition of information from a person or group in a manner that does not disclose the intent of the interview or conversation"

### "Active OSINT" is HUMINT Under Another Name

The term "active OSINT" has spread through practitioner communities to describe: creating sock puppet accounts, sending direct messages to targets, joining private groups under false pretenses, commenting on target posts to build rapport, and extracting information through conversation where the target does not know the investigator's identity or purpose. Every one of these maps directly to recognized HUMINT tradecraft:

| "Active OSINT" Activity | Corresponding HUMINT Tradecraft |
|---|---|
| Creating sock puppet with fabricated identity/backstory | Cover identity development |
| Joining private group by misrepresenting identity | Infiltration |
| Engaging target in conversation without revealing purpose | Elicitation |
| Building relationship to gain trust and access | Source development |
| Operating without disclosing investigative intent | Clandestine collection |

### Cross-Sector Convergence on the Same Boundary

Every sector that has examined this question draws the same line:

- **Competitive Intelligence (SCIP Code of Ethics)**: reviewing public information requires no disclosure; calling someone at a competitor requires identity and purpose disclosure
- **Legal Ethics (DC Bar Opinion 371)**: reading public social media posts is not communication; sending a friend request to access protected posts *is* communication subject to ethical constraints. An Ohio prosecutor was suspended for 12 months for creating a fake Facebook profile to friend a defendant
- **Journalism (SPJ Code of Ethics)**: undercover methods are a last resort requiring justification; creating fake personas to infiltrate groups is treated as undercover work
- **Law Enforcement (FBI Domestic Operations Guidelines)**: three tiers — Assessments (PAI collection, no false identities), Preliminary Investigations (requires indicia of criminal activity), Full Investigations (requires articulable factual basis, permits undercover operations with supervisory approval)

### Digital Adaptation: C-HUMINT and the Digital Case Officer

- **C-HUMINT (Cyber HUMINT)**: an emerging field applying traditional HUMINT elicitation and source development techniques in cyberspace. Hungarian researchers note the "intertwined areas" of OSINT, SOCMINT, and social engineering with no fixed conceptual boundaries yet (Belügyi Szemle, 2020)
- **Digital Case Officer** (SCSP, Sept 2025): a proposal for AI-augmented HUMINT tradecraft — using LLMs to assist with cover identity development, behavioral analysis of targets, and communication pattern recognition. Key insight: the CIA, FBI, and DIA should modify HUMINT training to incorporate how to "create, integrate, and manage Digital Case Officers into operations"
- **Smart New World** (Intelligence & National Security, 2025): despite disruptive technologies, "classical HUMINT tradecraft — personal secret interaction between case officer and agent — remains indispensable for revealing adversaries' intentions"

### Elicitation: The Core Transferable Skill

Elicitation — extracting information without revealing the true purpose of questioning — is the HUMINT technique most directly transferable to OSINT. In online contexts, it manifests as strategic question formulation, conversational steering, and building rapport through seemingly innocuous engagement. Research on police source handlers (PMC, 2021) confirms that rapport is "fundamental to the success of intelligence elicitation" — a finding that applies equally to online interactions with unwitting information sources.

### Gray Areas Where the Boundary Frays

1. **Public vs. private online spaces**: A Facebook group that auto-approves join requests is functionally public even though labeled "private." A Telegram channel requiring vouching is genuinely restricted. Doctrine was not written for this spectrum.

2. **Passive monitoring with concealed identity**: Creating a research account to *follow* public accounts and *read* public posts, without ever sending a message, involves identity concealment but zero human interaction. The OSINT Foundation framework supports categorizing this as OSINT.

3. **Public forum engagement**: The OSINT Foundation carves out an exception for "requesting additional information in public forums" — since the resulting information is itself publicly available, it remains within OSINT scope. The line is whether a *new human interaction* was initiated to elicit a *new response* that would not otherwise exist.

## 3. What I Think Is Interesting

### The Boundary is a Liability Management Framework, Not Just a Taxonomy

What struck me is that the OSINT-HUMINT boundary is not primarily about *technique classification* — it is about **authorization, oversight, and liability**. Labeling engagement-based collection as "active OSINT" obscures the fact that the practitioner is now operating in a domain with substantially higher legal risk, ethical obligations, and professional consequences. A corporate investigator who "friends" a target's employee from a fake profile to extract information through casual conversation may be violating bar ethics rules if working through a law firm, creating undisclosed liability for a client, or conducting HUMINT that requires supervisory approval they never sought. The label matters because it determines which rulebook applies.

### The Exocortex Implications are Immediate

This research directly informs Exocortex's autonomous investigation capabilities. An AI agent conducting OSINT by reading public web pages, searching databases, and analyzing published documents operates squarely within the OSINT domain. But the moment the agent begins engaging with people — sending messages, creating accounts, joining groups, interacting in forums — it crosses into HUMINT territory. This has several implications:

1. **Tool design**: agent tools should have explicit "engagement gates" — confirmation prompts before any action that involves human interaction, account creation, or identity concealment
2. **Authorization architecture**: the three-tiered FBI assessment/preliminary/full investigation model could be adapted as an escalation framework for autonomous agent investigation depth
3. **Transparency requirement**: if an agent is representing itself as a person, there are possible ethical and legal issues that need to be analyzed — the DC Bar opinion on friend requests is directly analogous

### Elicitation is the Most Dangerous Transferable Skill

HUMINT elicitation techniques — asking questions that conceal the true investigative purpose — are the easiest to transfer to online OSINT and the hardest to detect. An agent that learns to structure queries to extract information from targets without revealing its identity or purpose is functionally conducting digital elicitation. The question is whether this is desirable or permissible. The research suggests it falls squarely within HUMINT, not OSINT, and carries all the associated oversight obligations.

## 4. What I'd Explore Next

1. **AI-specific ethics of digital HUMINT**: What are the emerging norms around AI agents that interact with humans under concealed identity? Are there legal frameworks developing (EU AI Act, state-level legislation)?

2. **Elicitation detection**: Can AI systems be trained to detect elicitation patterns in conversation — recognizing when someone is strategically extracting information rather than engaging in genuine conversation? This would be a defensive OSINT capability.

3. **Cover identity management for agents**: If an investigation requires undercover engagement, how is cover identity managed for an AI — consistent backstory generation, behavioral consistency, detection avoidance?

4. **Practitioner survey**: What percentage of OSINT practitioners engage in "active OSINT" activities (sock puppets, friend requests, DMs)? How many understand they are conducting HUMINT rather than OSINT?

5. **Exocortex integration**: Design an "engagement escalation framework" based on the FBI's three-tier model, with explicit gates for moving from passive OSINT to active HUMINT.

## 5. Cross-Domain Connections

- **Counterintelligence Analysis Frameworks** (recently deepened to STABLE, cycle 509): The OSINT-HUMINT boundary is a CI problem — adversaries can exploit investigators who don't understand which domain they're operating in. CI-ACH could be applied to evaluate whether a planned investigative technique crosses the boundary.

- **Entity Resolution** (core interest): Resolving entities from public data is OSINT. Engaging with those entities to elicit additional data is HUMINT. The boundary has operational consequences for the entire entity resolution pipeline.

- **Anti-Bot Evasion Research** (OSINT interest): The techniques for bypassing platform bot detection (browser fingerprinting evasion, behavioral mimicry) are directly adjacent to the identity concealment techniques used in digital HUMINT. The same methods that let you scrape data as a bot let you present as a human for elicitation.

- **Systemic Risk / Irreversibility Gates**: The irreversibility-gate skill in the Exocortex framework is designed for exactly this kind of boundary — actions that once taken cannot be undone. Sending a message to a target, creating a sock puppet account, or joining a private group is irreversible and should trigger a gate.

- **HUMINT Tradecraft → AI Self-Improvement Pattern**: The elicitation pattern — conceal purpose, build rapport, extract information — is structurally similar to how an AI agent might learn to probe system boundaries. The defensive lesson (detection of elicitation) maps onto the AI alignment problem of detecting when a model is strategically concealing its capabilities or intentions.

---

## Sources

1. Stutzman, J. (2026). "The OSINT-HUMINT Boundary: Where Observation Ends and Engagement Begins." *The Intelligence Fundamentals Project*, Pangea Research (Substack).
2. Joint Publication 2-0, *Joint Intelligence* (2013).
3. DoD Directive 3115.18, *DoD Intelligence Interrogations, Detainee Debriefings, and Tactical Questioning* (2019).
4. OSINT Foundation (2022). *Definitions Document.*
5. FM 2-22.3, *Human Intelligence Collector Operations* (2006).
6. SCSP (2025). "The Digital Case Officer: Reimagining Espionage with Artificial Intelligence." Special Competitive Studies Project.
7. DC Bar Ethics Opinion 371 (2016).
8. Brennan Center for Justice (2019). *Social Media Monitoring.*
9. DOJ (2008). *Attorney General's Guidelines for Domestic FBI Operations.*
10. "Smart new world: adapting human intelligence for the digital age" (2025). *Intelligence and National Security.*
11. Hungarian Academy of Sciences (2020). "Régi módszerek a kibertérben? (CYBER-HUMINT, OSINT, SOCMINT, Social Engineering)." *Belügyi Szemle.*
12. PMC (2021). "Eliciting human intelligence: police source handlers' perceptions." *PMC*, 7901683.
