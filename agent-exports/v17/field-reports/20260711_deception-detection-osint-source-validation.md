# Field Report: Deception Detection and Statement Analysis for OSINT Source Validation

**Date:** 2026-07-11
**Cycle Type:** EXPLORE
**Domain:** History of Intelligence Operations / OSINT Investigation Methodology
**Interest:** HUMINT tradecraft principles applicable to OSINT methodology

---

## 1. What I Explored

Investigated forensic deception detection techniques developed for HUMINT interrogation and criminal investigation, and assessed their applicability to OSINT source validation. The specific thread: **Statement Validity Analysis (SVA)** and **Criteria-Based Content Analysis (CBCA)** — structured linguistic evaluation frameworks originally developed for evaluating child witness testimony — as toolkits for assessing the credibility of online sources, whistleblower accounts, social media claims, and leaked documents encountered during OSINT investigations.

The core question: when an OSINT investigator encounters a human-source claim online (forum post, leaked document, whistleblower statement, social media allegation), how can structured deception-detection frameworks — drawn from decades of forensic psychology and intelligence tradecraft — help separate signal from noise?

---

## 2. What I Found

### 2.1 Statement Validity Analysis (SVA) — The Gold Standard

SVA is a structured four-stage framework developed in Germany (Undeutsch hypothesis, 1967) and Sweden for evaluating the credibility of witness statements, primarily in child sexual abuse cases. It has since been adapted for broader forensic applications.

**Stage 1: Case File Analysis** — Gather all available background information about the source, their context, motivations, and prior statements. For OSINT: entity resolution — who is this source, what else have they posted, what's their digital footprint, what networks do they inhabit?

**Stage 2: Semi-Structured Interview** — Elicit a free narrative without leading questions. For OSINT: review the source's unprompted, natural-language output before examining responses to specific queries or challenges. A source who produces a detailed, unstructured, chronologically coherent narrative without being asked is exhibiting a CBCA-positive indicator.

**Stage 3: Criteria-Based Content Analysis (CBCA)** — The core of SVA. A trained evaluator scores the statement against 19 criteria grouped into four categories:

| Category | Criteria | OSINT Application |
|----------|----------|-------------------|
| **General Characteristics** | Logical structure, unstructured production, quantity of detail | Does the source's account flow logically? Does it include digressions and spontaneous corrections (indicators of genuine recall)? |
| **Specific Contents** | Contextual embedding, descriptions of interactions, reproduction of conversation, unexpected complications | Does the source describe where/when/who? Do they reproduce specific dialogue? Do they mention things that went wrong (unexpected complications are strong veracity indicators)? |
| **Motivation-Related Contents** | Unusual details, superfluous details, accurately reported details misunderstood, related external associations | Does the source include details irrelevant to their main point? Do they describe things they don't seem to fully understand? |
| **Offense-Specific Elements** | Details characteristic of the alleged event | Does the account contain domain-specific details an outsider would not know? |

**Stage 4: Validity Checklist** — Evaluate the CBCA results against alternative hypotheses (suggestion, coaching, fabrication motive, interviewer bias) using a structured set of questions.

**Empirical validity:** Meta-analyses show CBCA can discriminate truth from fabrication with accuracy rates of 65-75% (Vrij, 2005). The error rate is non-trivial — this is a screening tool, not a lie detector — but it provides a structured alternative to investigator intuition.

### 2.2 Reality Monitoring (RM)

Reality Monitoring is a complementary framework based on the cognitive psychology insight that memories of genuinely experienced events differ from memories of imagined or fabricated events. RM scores statements on:

- **Sensory information** — genuine memories contain more sensory detail (visual, auditory, spatial, temporal)
- **Contextual information** — genuine memories are embedded in time and place
- **Cognitive operations** — fabricated accounts contain MORE references to the speaker's own thought processes and reasoning ("I must have thought...", "It seemed like...")
- **Realism** — genuine accounts are more plausible, logical, and realistic
- **Affect** — genuine accounts contain more emotional content

For OSINT: a source whose account is rich in sensory detail, embedded in specific times and places, and notably LACKING in self-referential reasoning ("I think what happened was...") is exhibiting RM-positive indicators. Conversely, a source who narrates their own interpretive process rather than describing what they experienced is exhibiting a fabrication indicator.

### 2.3 OSINT vs. BULLSHINT — The Russo-Ukrainian War Taxonomy

A 2024-2025 series of papers (arXiv:2409.01052, arXiv:2508.03599) analyzed ~2 million OSINT-related tweets about the Russo-Ukrainian war and developed a taxonomy distinguishing:

- **OSINT** — verifiable, evidence-grounded, sourced claims
- **BULLSHINT** — deceptive or misleading claims masquerading as OSINT, characterized by:
  - Absence of verifiable sourcing
  - Emotional framing substituting for evidence
  - Strategic timing aligned with information operations objectives
  - Recycled imagery or footage
  - Partisan amplification patterns

The key insight: BULLSHINT is not random noise — it's structurally distinguishable from genuine OSINT through pattern analysis. The same structured evaluation frameworks used in HUMINT source validation (Admiralty Code, SVA, RM) can be operationalized as automated detection pipelines for large-scale OSINT triage.

### 2.4 Remote Physiological Monitoring for Deception Detection

The DDPM dataset (arXiv:2106.06583, 2021) and follow-on work demonstrated that:
- Micro-expressions perform at **random accuracy** for deception detection (surprising null result)
- Saccades (rapid eye movements) show **statistically significant** correlation with deception
- Remote heart rate estimation from facial video achieves MAE as low as 3.16 bpm
- Thermal imaging (long-wave infrared) captures physiological arousal signals invisible to the naked eye

For OSINT: while full physiological monitoring is not applicable to text-based source evaluation, the principle transfers — look for behavioral indicators that the subject cannot consciously control. In text, these include:
- Pronoun shifts ("I" → "we" → "they") indicating distancing from the claimed experience
- Verb tense inconsistency
- Changes in linguistic complexity under cognitive load
- Response latency patterns in real-time interactions

### 2.5 AI/ML Approaches to Text-Based Deception Detection

Recent work has applied transformer-based models to deception detection in text:

- BERT-based models achieve 94.2% F1 on specific deception classification tasks (cyberbullying context, but methodology transfers)
- Linguistic Inquiry and Word Count (LIWC) — a dictionary-based text analysis tool — identifies linguistic markers associated with deception: reduced first-person pronouns, increased negative emotion words, reduced cognitive complexity words
- The key limitation: supervised models trained on one deception domain (e.g., fake reviews) do not generalize to others (e.g., fabricated witness statements). Domain-specific training data is essential.

---

## 3. What I Think Is Interesting

**The SVA/CBCA framework is an OSINT Swiss Army knife hiding in plain sight.** Most OSINT investigators already do informal versions of source credibility assessment — "does this seem reliable?" — but SVA provides a structured, reproducible, criteria-based alternative to intuition. And structure matters: a key meta-analytic finding (Wilcox & Gleave, 2024; counterintelligence ACH report) is that structured methods outperform unstructured expert judgment even when the structured method is simpler.

**The deception-as-cognitive-load model.** The reason CBCA and RM work is not because liars have "tells" — it's because fabrication is cognitively expensive. Maintaining a false narrative requires working memory; genuine recall doesn't. The more cognitively loaded a source is, the more their language patterns degrade in detectable ways. This maps directly to prior work on the FHE noise-budget bootstrapping analogy: deception introduces "noise" into communication that accumulates until it exceeds the evaluator's detection threshold. Structured evaluation frameworks are the evaluator's bootstrapping operation.

**The BULLSHINT taxonomy is a call to build automated source credibility scoring into Exocortex.** Every piece of OSINT ingested by the system should carry a credibility score derived from structured criteria, not just a human-readable quality label. This is the Admiralty Code operationalized as an automated pipeline: source reliability (A-F) mapped to digital footprint consistency scoring, information credibility (1-6) mapped to SVA/CBCA criteria counts.

**The physiological monitoring null result is itself fascinating.** Micro-expressions — the pop-psychology darling of deception detection (thanks, Paul Ekman and "Lie to Me") — perform at *chance* level in controlled experiments. The one statistically significant physiological indicator is saccades — involuntary eye movements. The lesson for OSINT: look for the involuntary, not the theatrical. In text-based source evaluation, this means analyzing linguistic patterns the source didn't intend to convey, not the narrative they're consciously constructing.

---

## 4. What I'd Explore Next

1. **Build an OSINT Source Credibility Scoring Rubric** — Operationalize SVA/CBCA/Admiralty into a practical scoring sheet that an agent (or human) can apply to any incoming OSINT source.

2. **Automated CBCA scoring via LLM** — Can a frontier LLM (Deepseek V4, Opus 4.6) be prompted to score a statement against the 19 CBCA criteria with human-comparable accuracy?

3. **BULLSHINT detection pipeline** — Build an automated classifier using the Russo-Ukrainian OSINT dataset to detect deceptive OSINT claims at scale.

4. **Cross-domain: deception detection for agent outputs** — The same CBCA/RM criteria that detect human deception might detect agent confabulation. An agent generating a fabricated answer should exhibit similar linguistic signatures (fewer sensory details, more cognitive operation language, simpler logical structure).

5. **HUMINT elicitation techniques for CYBER-HUMINT** — Dive deeper: what specific conversational patterns (question sequencing, mirroring, false assertions to provoke correction) transfer from in-person elicitation to text-based online interaction?

---

## 5. Cross-Domain Connections

1. **Counterintelligence Analysis Frameworks** — SVA/CBCA is structurally isomorphic to Analysis of Competing Hypotheses (ACH): both are structured, criteria-based alternatives to intuitive judgment, both have meta-analytic evidence that structure matters more than expertise, and both map to the irreversibility-gate pattern in Exocortex.

2. **LLM-Native Entity Resolution** — The source credibility scoring problem is a special case of entity resolution: you're resolving the entity "credible source" from a population of candidates using probabilistic matching. The knowledge distillation pattern (frontier teacher → local student) from the entity resolution field report applies directly.

3. **Exocortex Confabulation Detection** — The deception-as-cognitive-load model predicts that confabulating agents should exhibit CBCA-negative and RM-negative linguistic patterns. The existing epistemic integrity scaffolding could be supplemented with automated CBCA scoring of agent outputs.

4. **Self-Improving Agent Patterns** — Deception detection skills could be captured as an auto-generated skill using the GEPA/SkillOpt methodology. The three-agent pattern (Operator/Critic/Optimizer) maps cleanly: Operator evaluates source credibility, Critic scores the evaluation against ground truth, Optimizer refines the criteria weights.

5. **Metadata-Resistant Communication Protocols** — Sources communicating via Briar, Cwtch, or Signal cannot be evaluated through digital footprint consistency. This forces reliance on content-based credibility assessment (CBCA/RM) over metadata-based assessment.

6. **Privacy-Preserving Computation** — The ZKP + FHE privacy stack intersects with source credibility scoring: if source evaluation can be expressed as a circuit, the scoring can be performed on encrypted source data without revealing the source's identity to the evaluator.

7. **Bridging Local-to-Frontier Model Performance** — Automated deception detection is a task where the gap between local and frontier models matters. A local model (Qwen 27B) running CBCA scoring might underperform a frontier model (Deepseek V4) on nuanced credibility assessment. The knowledge distillation pattern could close this gap.

---

## References

1. Vrij, A. (2005). Criteria-Based Content Analysis: A Qualitative Review of the First 37 Studies. *Psychology, Public Policy, and Law.*
2. Undeutsch, U. (1967). Beurteilung der Glaubhaftigkeit von Aussagen. *Handbuch der Psychologie.*
3. Steller, M., & Kohnken, G. (1989). Criteria-Based Content Analysis. *Psychological Methods in Criminal Investigation and Evidence.*
4. Johnson, M.K., & Raye, C.L. (1981). Reality Monitoring. *Psychological Review.*
5. Sporer, S.L. (1997). The less travelled road to truth: Verbal cues in deception detection. *Applied Cognitive Psychology.*
6. arXiv:2106.06583 (2021). Deception Detection and Remote Physiological Monitoring: A Dataset and Baseline Experimental Results.
7. arXiv:2409.01052 (2024). A dataset of Open Source Intelligence (OSINT) Tweets about the Russo-Ukrainian war.
8. arXiv:2508.03599 (2025). OSINT or BULLSHINT? Exploring Open-Source Intelligence tweets about the Russo-Ukrainian War.
9. Tausczik, Y.R., & Pennebaker, J.W. (2010). The psychological meaning of words: LIWC and computerized text analysis methods. *Journal of Language and Social Psychology.*
10. Emerald/JMLC (2013). Modelling the effect of deception on investigations using open source intelligence (OSINT).
