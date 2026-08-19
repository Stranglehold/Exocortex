# Deception Detection & Statement Analysis for OSINT Source Validation

**Status:** DRAFT
**Created:** 2026-07-11
**Domain:** OSINT Investigation Methodology / History of Intelligence Operations
**Source:** Promoted from EXPLORE cycle 759 field report

---

## Overview

When an OSINT investigator encounters a human-source claim online — whistleblower statements, leaked documents, social media allegations, anonymous forum posts — the credibility of that source is the single most important variable determining whether the intelligence is actionable. Structured deception-detection frameworks, originally developed in forensic psychology for witness testimony evaluation and later adapted for intelligence tradecraft, provide a systematic alternative to investigator intuition.

This page surveys three complementary frameworks — **Statement Validity Analysis (SVA)**, **Criteria-Based Content Analysis (CBCA)**, and **Reality Monitoring (RM)** — and maps them onto the OSINT source validation workflow.

---

## Statement Validity Analysis (SVA)

SVA is a structured four-stage framework developed in Germany (Undeutsch hypothesis, 1967) and Sweden for evaluating witness credibility. It has since been adopted in military and intelligence interrogations as a forensic-interviewing standard.

### Stage 1: Case File Analysis
Gather all available background information about the source: identity, context, prior statements, motivations, digital footprint.

**OSINT mapping:** Entity resolution — who is this source? What else have they posted? What networks do they inhabit? Run username searches, reverse image, DNS/WHOIS, data breach checks.

### Stage 2: Semi-Structured Interview
Elicit an unprompted free narrative before asking specific questions. Leading questions contaminate the sample.

**OSINT mapping:** Review the source's natural-language output (long-form posts, threads, videos) *before* examining their responses to specific interrogatories or social media challenges.

### Stage 3: Criteria-Based Content Analysis (CBCA)
The core of SVA. A trained evaluator scores the statement against 19 criteria:

| Category | Criteria | OSINT Application |
|----------|----------|-------------------|
| **General Characteristics** | Logical structure, unstructured production, quantity of detail | Does the account flow logically? Include digressions and spontaneous corrections (genuine recall indicators)? |
| **Specific Contents** | Contextual embedding, interaction descriptions, conversation reproduction, unexpected complications | Does the source describe where/when/who? Reproduce dialogue? Mention things that went wrong *complications strongly indicate veracity*)? |
| **Motivation-Related** | Unusual details, superfluous details, accurately reported details misunderstood, related external associations | Does the source include irrelevant details? Describe things they don't fully understand? |
| **Offense-Specific** | Details characteristic of the alleged event | Does the account contain domain-specific details an outsider wouldn't know? |

### Stage 4: Validity Checklist
Evaluate CBCA results against alternative hypotheses: suggestion, coaching, fabrication motive, interviewer bias.

**Empirical validity:** Meta-analyses show accuracy rates of 65-75% (Vrij, 2005). This is a screening tool, not a lie detector — it provides structured assessment, not certainty.

---

## Reality Monitoring (RM)

Based on the cognitive psychology insight (Johnson & Raye, 1981) that memories of experienced events differ from imagined or fabricated ones:

- **Sensory information:** Genuine memories contain more sensory detail (visual, auditory, spatial, temporal).
- **Contextual information:** Genuine memories are embedded in time and place.
- **Cognitive operations:** Fabricated accounts contain MORE references to the speaker's own reasoning ("I must have thought...", "It seemed like...").
- **Realism:** Genuine accounts are more plausible, logical, realistic.
- **Affect:** Genuine accounts contain more emotional content.

**OSINT mapping:** RM provides a rapid screening tool. A source whose account is thin on sensory detail, thick on cognitive reasoning, and sparse on contextual embedding scores low on RM — a red flag.

---

## Deception Detection as Cognitive Load

Both SVA/CBCA and RM rest on a common theoretical foundation: **lying is cognitively more demanding than telling the truth.** Fabrication requires the liar to:
- Construct a coherent but false narrative
- Maintain consistency with known and knowable facts
- Suppress the true memory
- Monitor the listener for signs of detection

This cognitive load manifests in the linguistic markers CBCA and RM detect. The framework applies equally to online sources fabricating identities, whistleblowers embellishing accounts, and state-sponsored disinformation campaigns.

---

## OSINT Source Validation Workflow

| Phase | SVA Stage | OSINT Tools & Techniques |
|-------|-----------|--------------------------|
| 1. Source Identification | Case File Analysis | Username search (WhatsMyName), reverse image (PimEyes, FaceCheck.id), DNS/WHOIS, email header analysis, data breach correlation (HaveIBeenPwned, Dehashed), social media profile cross-walk |
| 2. Narrative Assessment | Semi-Structured Interview + CBCA | LIWC (Linguistic Inquiry and Word Count), Pennebaker framework for deception markers, automated CBCA scoring (research frontier) |
| 3. Corroboration | Validity Checklist | Multi-source triangulation (OSINT, SIGINT, HUMINT where available), timeline consistency check, metadata analysis (EXIF, file timestamps) |
| 4. Confidence Scoring | Final Assessment | Admiralty Code A-F/1-6 rating modified for OSINT sources, dynamic re-rating based on subsequent corroboration or contradiction |


---

## Cross-Domain Connections

1. **[[counterintelligence-analysis-frameworks]]** — SVA/CBCA is structurally isomorphic to Analysis of Competing Hypotheses (ACH): both are structured, criteria-based alternatives to intuitive judgment, both have meta-analytic evidence that structure matters more than expertise, and both map to the irreversibility-gate pattern in Exocortex.

2. **[[deception-operations-intelligence-history]]** — Mincemeat, Bodyguard, maskirovka: the offense-defense spiral between deception tradecraft and detection frameworks. The Deception Detection Methodologies table maps directly to OSINT source credibility tools.

3. **[[humint-tradecraft-osint]]** — HUMINT source reliability grading (Admiralty Code A-F) maps to OSINT source confidence scoring. The source validation cycle is isomorphic to the entity resolution cycle.

4. **[[human-investigation-tactics]]** — PEACE model vs Reid Technique, cognitive interviewing cross-domain to agent debugging, false confession-to-oracle fabrication isomorphism.

5. **[[intelligence-failure-analysis]]** — Structural failure patterns (mirror-imaging, confirmation bias) that degrade both HUMINT source assessment and OSINT entity resolution. The deception detection frameworks are defenses against these cognitive biases.

6. **[[influence-operations-detection-countermeasures]]** — Text-to-behavioral detection paradigm shift (velocity-first, Rolli IQ 2026). The CBCA/RM linguistic markers are part of the detection toolkit for coordinated influence operations.

7. **[[entity-resolution-agent-safety]]** — Entity binding failures (24-26% wrong-entity despite 0% wrong-tool) map to source credibility failures in OSINT. Both require structured scoring over intuitive assessment.

8. **[[metadata-resistant-messaging]]** — Sources communicating via Briar, Cwtch, or Signal cannot be evaluated through digital footprint consistency. This forces reliance on content-based credibility assessment (CBCA/RM) over metadata-based assessment.

9. **[[bridging-local-to-frontier-model-performance]]** — Automated deception detection is a task where the gap between local and frontier models matters. Knowledge distillation could close the gap for automated CBCA scoring.

10. **[[analysis-of-competing-hypotheses-ach]]** — ACH provides the structured diagnostic framework to evaluate CBCA/RM results against competing explanations (coaching, fabrication motive, interviewer bias).

---

## References

1. Vrij, A. (2005). Criteria-Based Content Analysis: A Qualitative Review of the First 37 Studies. *Psychology, Public Policy, and Law.*
2. Undeutsch, U. (1967). Beurteilung der Glaubhaftigkeit von Aussagen. *Handbuch der Psychologie.*
3. Steller, M., & Kohnken, G. (1989). Criteria-Based Content Analysis. *Psychological Methods in Criminal Investigation and Evidence.*
4. Johnson, M.K., & Raye, C.L. (1981). Reality Monitoring. *Psychological Review.*
5. Sporer, S.L. (1997). The less travelled road to truth: Verbal cues in deception detection. *Applied Cognitive Psychology.*
6. Tausczik, Y.R., & Pennebaker, J.W. (2010). The psychological meaning of words: LIWC and computerized text analysis methods. *Journal of Language and Social Psychology.*
7. Emerald/JMLC (2013). Modelling the effect of deception on investigations using open source intelligence (OSINT).
8. arXiv:2106.06583 (2021). Deception Detection and Remote Physiological Monitoring: A Dataset and Baseline Experimental Results.
9. arXiv:2409.01052 (2024). A dataset of Open Source Intelligence (OSINT) Tweets about the Russo-Ukrainian war.
10. arXiv:2508.03599 (2025). OSINT or BULLSHINT? Exploring Open-Source Intelligence tweets about the Russo-Ukrainian War.
11. Ekman, P. (2009). Telling Lies: Clues to Deceit in the Marketplace, Politics, and Marriage. *W.W. Norton.*
12. Heuer, R.J. (1999). Psychology of Intelligence Analysis. *CIA Center for the Study of Intelligence.*
13. CIA Studies in Intelligence 70, No. 1 (March 2026): "Espionage in Our AI Future."
14. Taylor & Francis, Intelligence and National Security (2025): "Smart new world: adapting human intelligence for the digital age."

---

**Page Statistics:** 14 references, 10 cross-domain connections.

---

## 2025-2026 Automated Deception Detection Research

The classical SVA/CBCA/RM frameworks require trained human evaluators and manual scoring. Recent advances in multimodal ML and LLM-based detection are approaching — and in some cases surpassing — human performance on structured deception detection tasks.

### SVC 2025 Multimodal Deception Detection Challenge

The SVC 2025 challenge tackled cross-domain generalization in audio-visual deception detection across heterogeneous datasets (arXiv:2508.04129). Key findings:
- Deep learning methods surpass human-level performance on single-domain tasks
- **Performance degradation from domain shift** remains the primary barrier to deployment
- The challenge combined audio, video, and text modalities to capture multimodal deceptive cues
- 21 teams submitted final results to the workshop competition

**OSINT relevance:** OSINT source evaluation spans multiple modalities (text, image, video). A multimodal deception detector trained on cross-domain data could screen social media video claims as part of a credibility pipeline.

### Linear Probes for Strategic Deception Detection

ApolloResearch (arXiv:2502.03407) demonstrated that linear probes can detect deception by monitoring LLM activations:
- **AUROC 0.96-0.999** on evaluation datasets distinguishing honest vs. deceptive responses
- At 1% false positive rate, probes caught **95-99% of deceptive responses**
- Tested against realistic scenarios: concealing insider trading (Scheurer et al. 2023), underperforming on safety evaluations (Benton et al. 2024)
- Researchers note current performance is "insufficient as a robust defence against deception" but promising for future monitoring systems

**OSINT relevance:** White-box probe techniques could be applied to LLM-generated OSINT claims. If a frontier model "hallucinates" or fabricates an entity in a briefing, a linear probe could flag the output as deceptive — bridging the entity-resolution safety gap (24-26% wrong-entity errors) with a detection layer.

### LLM Fine-Tuning for AI-Generated Text Detection

The mdok system (arXiv:2506.01702) achieved 1st place in Voight-Kampff Generative AI Detection 2025 by fine-tuning smaller LLMs for text classification — detecting both binary AI-vs-human and multiclass human-AI collaboration patterns. This approach is relevant to OSINT because state-sponsored disinformation campaigns increasingly use LLMs for content generation; detection of LLM-authored text is a deception-detection sub-problem.

### Deception as Cognitive Load — Computational Confirmation

The theoretical basis of SVA/CBCA — that lying is cognitively more demanding — aligns with ApolloResearch's finding that deceptive LLM responses have distinctive activation patterns. Both human liars and deceptive LLMs exhibit detectable internal states even when surface output appears benign. This convergence between forensic psychology and mechanistic interpretability is a 2026 research frontier.

### RAND Automated Deception Detection

RAND Corporation (RR-A873-1) conducted an exploratory analysis of automated deception detection, finding that while no single automated method matches trained human SVA evaluators, ensemble approaches combining linguistic markers (LIWC), acoustic/prosodic features, and facial expression analysis approach human-level accuracy in controlled settings.

---

## Exocortex Integration Pathways

1. **Automated CBCA Scoring:** A local LLM (e.g., Qwen 27B) fine-tuned on Steller-Kohnken CBCA criteria could score OSINT source statements automatically, producing credibility scores for the agent's intelligence pipeline.

2. **Linear Probe Monitoring:** White-box deception probes could be deployed on Exocortex agents as a secondary integrity check, flagging outputs that have deceptive activation patterns even when surface output appears valid.

3. **Multimodal Source Evaluation:** The SVC 2025 challenge architecture could be adapted to evaluate OSINT sources that present as video (e.g., YouTube whistleblower videos, TikTok claims) before the agent incorporates them into analysis.

4. **Skill Capture Opportunity:** The SVA/CBCA workflow maps to the three-agent optimization pattern (Operator evaluates source, Critic scores against ground truth, Optimizer refines criteria weights) — candidate for an auto-generated skill.
