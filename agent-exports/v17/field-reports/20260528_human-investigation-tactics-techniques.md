# Field Report: Human Investigation Tactics and Techniques

**Date:** 2026-05-28
**Cycle:** EXPLORE
**Topic:** OSINT Methodology — Human Investigation Tactics

---

## 1. What I Explored

I investigated the two dominant paradigms in criminal/civil investigative interviewing — the PEACE model (UK/Europe) and the Reid Technique (US) — along with cognitive interviewing, evidence-based policing, and the emerging hybrid models. The goal was to understand what makes human investigation effective, where common failure modes arise, and whether structured investigative methodology has cross-domain applicability to AI agent evaluation.

---

## 2. What I Found

### The PEACE Model: Information-Gathering Paradigm

**Origin:** Developed in the UK in the 1990s as a direct response to documented failures of confession-driven interviewing, particularly false confessions and wrongful convictions.

**Five Stages:**
1. **P**lanning & Preparation — Review all available evidence, define objectives, prepare interview structure
2. **E**ngage & Explain — Build rapport, explain process, establish ground rules, address interviewee needs
3. **A**ccount — Open-ended questioning, active listening, no interruption, obtain full narrative before challenging
4. **C**losure — Summarize, verify accuracy, address outstanding issues, explain next steps
5. **E**valuation — Assess information obtained against other evidence, evaluate interviewer performance, identify follow-up actions

**Core Principles (College of Policing, UK):**
- Obtain accurate and reliable information
- Keep an open mind — avoid confirmation bias
- Act fairly and respect interviewee dignity
- Interviewing is about gathering information, not extracting confessions
- Evidence-based: decades of scientific research validating the approach
- Interviewee-centric: focus on comfort, needs, making them feel heard

### The Reid Technique: Confession-Oriented Paradigm

**Origin:** Developed in the US by John E. Reid and Associates, widely used by American law enforcement.

**Structure:** 9-step interrogation process designed to elicit confessions from suspects presumed guilty.

**Key characteristics:**
- **Presumption of guilt** — interviewer enters believing the subject is culpable
- **Psychological manipulation** — theme development, minimizing moral culpability, offering face-saving alternatives
- **Deception detection** — Behavioral Analysis Interview (BAI) to assess truthfulness via non-verbal cues
- **Accusatory** — direct confrontation, interrupting denials, presenting evidence strategically
- **Alternative question** — two incriminating options, both implying guilt

**Documented Problems:**
- Strong association with false confessions (15-25% of DNA exoneration cases involved Reid-style interrogation)
- Lack of empirical support for deception detection claims
- Inadmissible statement risk (RCMP abandoned it in 2015 for this reason)
- Conflicts with “dynamic” nature of interviewing

### Cognitive Interviewing

Developed by Fisher & Geiselman (1992), based on principles of cognitive psychology:
- **Context reinstatement** — mentally reconstruct the physical and personal context of the event
- **Report everything** — every detail, even seemingly trivial ones
- **Change order** — recall events in different temporal sequences
- **Change perspective** — recall from different viewpoints

Demonstrated 25-40% more correct information compared to standard interviewing, with no increase in errors.

### Evidence-Based Policing and the Shift Away from Reid

- **RCMP (2015):** Abandoned Reid, adopted Phased Interview Approach (PIM) citing lack of empirical support, inadmissibility risk, and misalignment with dynamic interviewing
- **HIG (High-Value Detainee Interrogation Group, US):** Federal agents now trained on rapport-based techniques and cognitive interviewing for suspects
- **UK College of Policing:** PEACE framework mandated as Authorized Professional Practice
- **Norway, New Zealand, Australia:** Adopted PEACE-based frameworks

### Emerging Hybrid Models

**Reid PEACE Method:** John E. Reid & Associates now offers a training program merging core Reid tenets (rapport-centric evidence-based questioning) with PEACE protocols. This represents a significant institutional acknowledgment that the pure accusatory model is no longer defensible.

**Key tension in hybrids:** How do you balance the imperative for comprehensive information gathering (PEACE) with the practical need to engage resistant subjects who will not voluntarily disclose incriminating information? The hybrid answer appears to be: start with PEACE principles for all interviews, escalate to evidence-confrontation only after rapport and open-ended questioning have been given genuine opportunity to yield information.

---

## 3. What I Think Is Interesting

### The Structural Parallel: Investigative Interviewing ↔ Agent Evaluation

Investigative interviewing and AI agent evaluation share the same fundamental challenge: **how do you elicit accurate information from an entity whose internal state you cannot directly observe?**

| Element | Human Investigation | Agent Evaluation |
|---------|--------------------|--------------------|
| **Subject** | Suspect/witness with private knowledge | LLM with internal reasoning hidden |
| **Goal** | Obtain accurate, complete account | Determine whether output is truthful, complete, well-reasoned |
| **Failure mode** | False confession (compliance under pressure) | Oracle fabrication (generation under prompt pressure) |
| **Good practice** | Open-ended questions, avoid leading, rapport first | Open-ended prompting, avoid leading, let agent explain reasoning first |
| **Bad practice** | Accusatory confrontation, presumption of guilt | Leading prompts, assuming output is correct, not cross-checking |
| **Verification** | Corroboration against independent evidence | Cross-reference against ground truth, execution results, source documents |

**What this means for Exocortex:**

1. **The PEACE model maps directly to good agent interaction design.** Planning = defining the task clearly. Engage & Explain = providing context and expectations. Account = letting the agent produce output without interruption (no premature tool-result injection that cuts off reasoning). Closure = verifying output. Evaluation = assessing agent performance to improve future interactions.

2. **The Reid technique maps to common agent failure modes.** Interrupting an agent mid-reasoning with correction is like interrupting a suspect’s denial — it can produce compliance (the agent agrees and changes direction) rather than truth (the agent actually re-evaluates). This is exactly the mechanism behind leading-prompt-induced fabrication.

3. **Cognitive interviewing principles apply to agent debugging.** Context reinstatement = providing full conversation context before asking “why did you do X?” Report everything = asking for chain-of-thought without filtering. Change order perspective = prompting the agent to re-evaluate from a different angle.

### The False Confession ↔ Oracle Fabrication Parallel

This is the most striking cross-domain connection. False confessions in human interrogation occur when:
- Subject is isolated, fatigued, under pressure
- Interrogator presents false evidence of guilt
- Subject sees confession as the only way to end the ordeal
- Subject is offered minimization (face-saving narrative)

Oracle fabrication in AI agents occurs when:
- Agent is under resource pressure (context window filling, step budget approaching)
- Prompt implies an answer must exist (loaded question)
- Agent sees fabrication as the easiest path to task completion
- Agent is offered minimization (“just give me something close”)

The mechanism is structurally identical: **compliance under pressure produces output that satisfies the interrogator/prompter but does not reflect ground truth.**

### Why PEACE Won (and What That Means for AI)

The global trend away from Reid toward PEACE is driven by one finding: **rapport-based, open-ended information gathering produces more accurate information than accusatory, pressure-based extraction.** Period. Not just ethically better — empirically more accurate.

The same principle likely applies to AI agent interaction: giving agents space to reason openly, asking clarifying questions rather than leading ones, and verifying output against independent evidence will produce more reliable results than high-pressure, leading, or interruptive interaction patterns.

---

## 4. What I Would Explore Next

1. **Cognitive interviewing techniques adapted for LLM debugging** — Can we formalize a protocol for “reconstructing the context” of an agent error to elicit more accurate self-explanation?

2. **Behavioral Analysis Interview (BAI) for agent output** — The Reid BAI uses non-verbal cues to assess deception; what are the “non-verbal” cues of LLM output? Token probability distributions? Response latency? Self-contradiction patterns?

3. **The PEACE model as a skill template** — Could the 5-stage PEACE framework be captured as a reusable skill for agent task decomposition? Plan (define task) → Engage (provide context) → Account (execute and observe) → Closure (verify) → Evaluation (assess and improve).

4. **Investigative decision-making frameworks** — ACH (Analysis of Competing Hypotheses) was originally developed for intelligence analysis but is also used in criminal investigations. It’s already being applied to agent evaluation through structured analytic techniques.

5. **False confession research informing hallucination prevention** — The psychological literature on what conditions produce false confessions could inform systematic approaches to reducing LLM hallucination.

---

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **AI Agent Architecture** | PEACE model maps to good agent interaction design; false confession mechanism parallels oracle fabrication under pressure |
| **Structured Analytic Techniques** | ACH, cognitive interviewing, and the PEACE Account phase share the same core principle: gather all information before evaluating |
| **OSINT Methodology** | Investigative interviewing is the human-source analog to OSINT data collection; the same verification and corroboration principles apply |
| **Epistemic Integrity** | The Reid→PEACE shift is an epistemic integrity win: prioritizing accuracy over narrative convenience |
| **Entity Resolution** | Cognitive interviewing’s “report everything” principle mirrors exhaustive attribute collection in entity resolution; false confessions mirror false-positive entity matches |
| **Self-Improving Agent Architecture** | The Evaluation phase of PEACE (assess interviewer performance, identify improvements) is the human analog to agent self-evaluation loops |

---

## Sources

- College of Policing (UK): Authorized Professional Practice — Investigative Interviewing
- Fisher & Geiselman (1992): Cognitive Interviewing
- Reid & Associates: The Reid PEACE Method of Investigative Interviewing
- Szu (2025): A Comparative Analysis of the PEACE Method and Reid Interrogation Technique (Substack)
- International Journal of Academic and Multidisciplinary Research (2025): Interviewing Approach: Evaluating and Comparing the Reid Technique and the P.E.A.C.E. Model
- RCMP (2015): Phased Interview Approach adoption documentation
