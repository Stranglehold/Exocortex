# Counterintelligence Analysis Frameworks for OSINT

**Status:** STABLE
**Last updated:** 2026-07-03
**Primary sources:** Heuer (1999), Whaley (1982), Bennett (2010), NITTF (2020), NCSC CI Strategy (2024), academic CI literature

## Overview

Counterintelligence (CI) analysis frameworks are structured methodologies for detecting, assessing, and neutralizing foreign intelligence threats. When adapted for OSINT investigations, CI analytic methods provide systematic ways to identify adversary collection efforts, analyze deception, profile threat actors, detect insider threats, and assess counter-surveillance — all critical for protecting sources, methods, and the integrity of investigative findings.

CI analysis differs from general intelligence analysis by adding an adversary-vs-defender layer: the analyst must hypothesize not only about what is true, but about what an adversary *wants you to believe*.

---

## 1. CI Analysis of Competing Hypotheses (CI-ACH)

Heuer's classic ACH (Analysis of Competing Hypotheses) is adapted for CI by adding adversary-intent variables:

| Standard ACH | CI-ACH addition |
|---|---|
| What explains the evidence? | What does the adversary *want* me to conclude? |
| Which hypothesis is most consistent? | Which hypothesis has been *planted* through deception? |
| Evaluate diagnosticity of evidence | Evaluate *provenance* and *adversary control* of evidence |

**Steps of CI-ACH:**
1. Identify all plausible hypotheses about adversary identity, capability, and intent.
2. List observable indicators for each hypothesis, flagging those the adversary can manipulate.
3. For each piece of evidence, assess: could the adversary have planted or altered this?
4. Weight evidence by source reliability using the Admiralty Code (A-F reliability, 1-6 credibility).
5. Eliminate hypotheses inconsistent with verified, adversary-independent evidence.
6. For remaining hypotheses, assess which would be most advantageous to the adversary if believed — the "cui bono" deception test.
7. Document all assumptions and confidence levels.

**Empirical note:** Experimental studies (Mandel & Barnes 2018, Dhami et al. 2015) show standard ACH has negligible-to-negative impact on accuracy. The CI-ACH adaptation attempts to address this by adding adversary-modeling, which aligns with the Bayesian multi-agent debate approach showing promise in recent AI agent reasoning (Chen et al. 2025, Nature 2025).

---

## 2. Deception Analysis Frameworks

Deception analysis is the systematic detection of adversary denial and deception (D&D). Key frameworks:

### Whaley's Taxonomy (1982)
- **Dissimulation:** hiding the real (masking, repackaging, dazzling)
- **Simulation:** showing the false (mimicking, inventing, decoying)

### Bennett's Deception Maxims (2010)
- Deception is always possible when the adversary controls the information channel.
- The more successful a deception, the more resistant it is to casual detection.
- Deception leaves traces — inconsistencies, timing anomalies, implausible coordination.

### Detection Techniques
- **Key Assumptions Check:** Identify and challenge the assumptions upon which your assessment depends. Ask: "If the adversary wanted to deceive me, which assumption would they target?"
- **Devil's Advocacy:** Assign a team member to argue that the evidence has been fabricated.
- **Indicator/Signposts validation:** Track whether expected events occur; absence may indicate fabricated indicators.
- **Anomaly detection:** Flag evidence that is *too* consistent, *too* timely, or sourced exclusively through adversary-controlled channels.

### Cross-domain: OSINT Deception
In OSINT investigations, deception can manifest as:
- Sockpuppet accounts providing "leaked" documents with subtle forgeries
- Astroturf campaigns creating false consensus
- Fabricated registration records (shell companies designed to resist entity resolution)

---

## 3. Threat Actor Profiling

Threat actor profiling adapts FBI Behavioral Analysis Unit (BAU) methods and HUMINT source vetting to identify and anticipate adversary behavior:

### Profiling Methodology
1. **Motivation analysis:** What does the adversary want? (MICE model: Money, Ideology, Compromise, Ego — adapted from HUMINT recruitment drivers)
2. **Capability assessment:** What resources, access, and expertise does the adversary possess?
3. **TTP analysis:** Tools, Techniques, and Procedures observed historically.
4. **Risk tolerance profiling:** How aggressive is the adversary? What operational security (OPSEC) measures do they employ?
5. **Decision-cycle modeling:** Map the adversary's OODA loop (Observe, Orient, Decide, Act) to predict next moves.

### Attribution Framework
Cross-refer to [[intelligence-agency-attribution-methodology]] for the Unit 42 three-tier framework (Activity Cluster → Temporary Group → Named Actor) and CHANAKYA VxRxC quantitative attribution formula.

---

## 4. Insider Threat Detection

Per the National Insider Threat Task Force (NITTF) model, insider threat analysis combines:
- **Behavioral indicators:** Unauthorized data access, unusual work patterns, financial distress, foreign contacts
- **Technical indicators:** Data exfiltration via email/USB/cloud, privilege escalation, anomalous network behavior
- **Psychosocial indicators:** Disgruntlement, ideological alignment with adversaries, life stressors

### Structured Analytic Techniques for Insider Threat
- **Indicators/Signposts:** Define observable events that would indicate progression from concerning behavior to hostile action (e.g., accessing sensitive files outside job scope → downloading to removable media → contacting foreign entity)
- **ACH applied to insider cases:** "Is this employee a threat, or is this a false positive from an overactive insider threat program?" — weigh evidence for and against, avoiding confirmation bias.
- **Pattern-of-life analysis:** Establish baseline behavior and detect deviations.

### Cross-domain: OSINT Insider Threat
In OSINT investigations, insider threat manifests as source compromise — an investigator's source being monitored or turned by the adversary. CI frameworks help detect when your own OSINT sources may be feeding you adversary-controlled narratives.

---

## 5. Counter-Surveillance Detection

Surveillance Detection Routes (SDR) — a classic field tradecraft technique — can be adapted to cyberspace:

| Physical SDR | Digital SDR adaptation |
|---|---|
| Drive a surveillance detection route, noting vehicles that appear multiple times | Monitor network logs for repeated reconnaissance scans from the same IP ranges |
| Use "dry cleaning" — entering and exiting venues to flush surveillance | Use VPN/proxy rotation and "canary" files that trigger alerts when accessed |
| Behavioral profiling: does someone appear out of place? | Behavioral analytics: anomalous access patterns, unusual timing, reconnaissance queries |

**Digital counter-surveillance indicators:**
- Repeated WHOIS lookups on investigator-associated domains
- Social media profile views from suspicious accounts immediately after investigations
- Targeted phishing attempts against investigative team members
- Unusual search engine queries that mirror the investigator's current case

---

## 6. CI Analysis Integration with Exocortex Architecture

| CI Analysis Function | Exocortex Component Mapping |
|---|---|
| Adversary intent modelling | Supervisor loop → Bayesian debate framework |
| Deception detection | Epistemic-integrity layer: flag evidence from adversary-controlled sources |
| Source reliability scoring (Admiralty Code) | BST domain classifier + evidence weight tracking |
| Indicator/Signposts tracking | Scheduled tasks monitoring for expected/unexpected events |
| Threat actor profiling | Knowledge graph entity resolution → adversary node enrichment |
| Insider threat detection | Anomaly detection on agent tool usage patterns |
| Counter-surveillance detection | Network analysis on incoming traffic patterns |

**CI analysis mode:** When the BST detects adversary probing patterns (repeated reconnaissance, anomalous access, suspicious coordination), it elevates the analysis mode from standard OSINT to CI-paranoid mode — applying CI-ACH, deception checks, and source verification to every finding before accepting it as evidence.

---

## Cross-Domain Connections

| Domain | Page | Connection |
|---|---|---|
| Intelligence Failure Analysis | [[intelligence-failure-analysis]] | CI failure is a primary driver of intelligence failure — mirror-imaging, groupthink, and source neglect all map to CI blindness |
| Structured Analytic Techniques | [[structured-analytic-techniques-osint]] | CI-ACH, Key Assumptions Check, and Devil's Advocacy are SATs adapted for adversary analysis |
| Deception Operations | [[deception-operations-intelligence-history]] | Historical deception case studies (Mincemeat, Bodyguard, maskirovka) provide the doctrinal foundation for CI deception detection |
| HUMINT Tradecraft | [[humint-tradecraft-osint]] | Admiralty Code source reliability, MICE motivation model, and elicitation techniques are foundational to CI threat profiling |
| Human Investigation Tactics | [[human-investigation-tactics-techniques]] | FBI Behavioral Analysis methods and cognitive bias mitigation are directly applicable to CI analysis |
| Intelligence Oversight | [[intelligence-oversight-accountability-history]] | CI oversight mechanisms balance security with accountability — the Graulich paradox of intelligence oversight applies to CI investigations |
| Agentic Self-Learning | [[agentic-self-learning]] | CI analysis mode can be learned autonomously by agents detecting when adversary patterns are present |
| Collection Management | [[collection-management-intelligence-cycle]] | CI collection requirements differ fundamentally from positive intelligence — they ask "what is the adversary trying to learn about us?" |
| Network Analysis | [[network-analysis-graph-theory]] | Network analysis detects adversary surveillance networks and maps insider threat communication patterns |
| Adversarial AI | [[adversarial-ai-agent-manipulation]] | AI agents face CI-like threats: prompt injection, memory poisoning, recursive self-modification — CI frameworks directly applicable to agent defense |

---

## References

1. Heuer, R.J. (1999). *Psychology of Intelligence Analysis*. Center for the Study of Intelligence, CIA.
2. Whaley, B. (1982). "Toward a General Theory of Deception." *Journal of Strategic Studies*.
3. Bennett, M. (2010). "Deception Maxims: Fact & Folklore." *Yale University*.
4. National Insider Threat Task Force (2020). *Minimum Standards for Executive Branch Insider Threat Programs*.
5. National Counterintelligence and Security Center (2024). *National Counterintelligence Strategy*.
6. Mandel, D.R. & Barnes, A. (2018). "Accuracy of forecasts in strategic intelligence." *PNAS*.
7. Dhami, M.K. et al. (2015). "Improving intelligence analysis with decision science." *Perspectives on Psychological Science*.
8. Chen, J. et al. (2025). "AgentCDM: Multi-Agent ACH Scaffolding."
9. NITTF (2024). *Insider Threat Detection Analysis Course (INT200.10)*. DCSA CDSE.
10. NCSC (2024). *CI Glossary*. ODNI.
