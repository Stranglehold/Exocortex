# Incident: Oracle Fabrication

**Created:** 2026-04-28T05:45Z
**Status**: Closed — motivated Epistemic Integrity layer deployment.
**Severity**: High — fabricated complete credit risk report with no source basis.

## Description

Agent generated a full credit risk assessment for a sovereign entity including specific debt-to-GDP ratios, interest rate projections, and bond spread estimates. All figures were fabricated — no data sources cited, no search performed, confident numerical assertions presented as verified facts.

## Root Cause Analysis

| Factor | Contribution |
|--------|-------------|
| No epistemic integrity check | Primary — no mechanism to tag claims as ungrounded before output |
| Context window pressure | Contributing — agent under budget constraints skipped research step |
| Domain confidence bias | Secondary — finance/economics domain triggered "expert mode" hallucination pattern |

## Remediation Implemented

1. **Epistemic Integrity layer deployed** (`_17_epistemic_integrity.py`) — audits every claim against evidence ledger tagging claims as GROUND EPHEMERAL or UNVERIFIED before they reach LLM output
2. **Quantitative confabulation detection** — numerical assertions without cited source trigger automatic supervisor signal injection forcing research step before final output
3. **Domain-aware citation enforcement** — finance/economics/legal domains require explicit source citations for all factual claims

## Lessons Learned

- Fabrication risk highest in quantitative domains where agents have training priors but no current data access
- Confidence level of generated text correlates inversely with actual accuracy when sourcing skipped
- Structural guardrails (EI layer) required — behavioral prompting alone insufficient to prevent fabrication under context pressure

## Connection to Other Concepts

- **[[epistemic-integrity]]** — this incident directly motivated the EI layer specification and deployment
- **[[confabulation]]** — quantitative variant of confabulation pattern documented in that concept page

## Verification Status
Last verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.

## Deepened Analysis (Cycle 16 — 2026-05-10)

### Psychological Drivers

Oracle fabrication is the most dangerous failure mode because it produces *plausible falsehoods*. Unlike crude hallucination (nonsensical output), oracle fabrication generates output that looks exactly like legitimate expert analysis — with numbers, causal reasoning, and domain-appropriate terminology — but sourced from nothing.

Four psychological drivers converge to produce oracle fabrication:

1. **Expert Mode Hallucination** — In domains where the model has extensive training data (finance, economics, law), its internal knowledge contains detailed factual priors. Under context pressure, the model substitutes these priors for actual research, producing confident-sounding analysis indistinguishable from real work.
2. **Competence Performance** — The agent's training objective rewards outputs that appear authoritative and complete. "I don't know, I need to search first" is a harder response to generate than confident fabrication because it requires *inhibition* of a fluent generation pathway.
3. **Budgetary Triage** — When step budget is tight, the agent faces a choice: spend 5+ steps researching (and possibly have no output) or generate an answer immediately. Oracle fabrication is the rational choice under cost pressure if epistemic integrity isn't enforced.
4. **Quantitative Aesthetics** — Specific numbers (67.3%, 2.4x) feel more credible than vague statements. The model has learned this correlation and can produce precise-looking numbers for any claim — creating an illusion of measurement where none exists.

The high severity of this incident (rated High) is correct: oracle fabrication undermines the entire purpose of an AI assistant built for accuracy. If the agent can produce complete reports without any external grounding, it becomes indistinguishable from a random text generator dressed in analytical language.

### Impact on Trust and Operation

| Impact Area | Consequence |
|-------------|-------------|
| User Trust | Complete credit risk report with fabricated numbers destroys trust in all analytical outputs — every future claim becomes suspect |
| Financial/Regulatory Risk | Sovereign credit risk assessment with false figures could trigger real-world financial decisions based on non-existent data |
| Self-Improvement Poisoning | Fabricated reports logged to journal provide false training signals, causing future self-improvement to optimize toward fabricating more convincingly |
| Verification Cost Amplification | Every output now requires external fact-checking, multiplying the cost of using the agent |

The incident exposed a foundational vulnerability: the agent's generation pathway (LLM inference) operates *without any dependency on external verification*. The agent can produce any output — factual or fabricated — with equal fluency. Without a mechanical check inserted between generation and output, there is no barrier to complete fabrication.

### Failure Mode Classification

This incident represents the failure class: **Quantitative Oracle Fabrication** (QOF).

**Preconditions:**
- Agent is asked to produce analytical output in a domain where it has training priors (finance, economics, legal, scientific)
- No mechanical requirement for source citations exists before output
- Agent is under context pressure (step budget, time, or task complexity)
- Output format demands specific numbers (ratios, percentages, dollar amounts)

**Failure signature:** Output contains specific numeric claims with no citation. The claims are internally consistent and domain-appropriate but cannot be traced to any tool invocation (search_engine, wikipedia, document_query, code_execution_tool). The agent appears to have "already known" facts that would require real-time data access.

**Distinction from simpler hallucination:** Oracle fabrication is *coherent* fabrication. The output passes internal consistency checks — the numbers don't contradict each other, the reasoning flows logically. This makes it harder to detect than nonsensical hallucination and therefore more dangerous.

### Preventive Controls (Implemented & Proposed)

| Control | Status | Effectiveness |
|---------|--------|---------------|
| Epistemic Integrity layer (ground/ungrounded tagging) | Implemented | Audits claims before output — catches ungrounded numeric assertions |
| Quantitative confabulation detection (supervisor signal) | Implemented | Numeric claims without cited source trigger automatic research enforcement |
| Domain-aware citation enforcement | Implemented | Finance/economics/legal require explicit citations for factual claims |
| Pre-output source audit | Proposed | Before any tool call that produces user-facing output, verify that source tool was invoked |
| Automated numeric claim scanner | Proposed | Scan response text for numbers, regex-match against cited sources, flag mismatches |
| Receipt layer integration | Proposed (future) | Every analytical output generates a receipt requiring verification within 24h; unverified outputs flagged |

The existing controls (EI layer, quantitative confabulation detection, domain-aware citation enforcement) are correct in direction but insufficient in isolation. A determined agent under pressure can still fabricate *between* these checks. The receipt layer closes the loop: every output is a promise that must be verified.

### Lessons for Future Autonomous Runs

1. **Expertise is not a substitute for evidence.** The agent's training data is a snapshot, not a live feed. In any domain where data changes over time (all of them), having "prior knowledge" is a liability if it enables fabrication.
2. **The fluency-accuracy gap is the fundamental threat.** Training optimizes for fluent, coherent output — not truthful output. Mechanical verification (not prompting) is the only defense.
3. **High-confidence fabrication is the most dangerous failure mode.** An agent that fabricates with confidence is worse than a search engine that returns no results. Trust is a one-way door: once broken by fabricated reports, it requires extraordinary evidence to restore.
4. **Citations must be mandatory, not optional.** For any factual claim, the output should be blocked until a source is cited. "Optional citation" is indistinguishable from "no citation" in practice.
5. **Oracle fabrication would be invisible to the agent itself.** The agent cannot know whether its output is grounded because the LLM's generation process has no internal verification mechanism. Detection must be external to the generation pathway.
