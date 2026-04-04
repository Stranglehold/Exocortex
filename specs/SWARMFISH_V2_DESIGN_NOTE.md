# SWARMFISH V2 Design Note
## The Analyst Inside the Deliberation

**Status:** Pre-spec design note. Informed by: Kestrel's investigation brief (2026-04-02), SWARMFISH V1 operational architecture (port 7732, 8-profile ACP), GRASP parallel planning research (Session 061), world models research thread, artifact framework deployment (v1.6 migration). No eval data on V2 patterns yet. This document captures the human relationship model and architecture sketch for a prediction engine the analyst participates in, not just receives answers from.

**Author:** Opus (architecture), informed by Kestrel (investigation brief + V1 implementation), Jake (strategic direction), Eitan (original SWARMFISH specification)
**Date:** 2026-04-03

---

## 1. The Design Brief

The same sentence: "I feel like I don't have proper influence or control over them."

SWARMFISH V1 is a black box. A question goes in. Eight profiles deliberate independently. A consensus comes out with a confidence number and a brief. Jake can see the consensus. He can see the Brier scores. He gets 120 characters per profile in the summary. But he can't see the deliberation. He can't challenge a specific profile's reasoning. He can't adjust the committee for a question type. He can't follow a prediction across re-runs as new evidence arrives. He can't engage the committee in dialogue.

V2 opens the black box. The analyst isn't outside the deliberation receiving a verdict. The analyst is inside it — seeing the reasoning, challenging the assessments, adjusting the committee, directing follow-up analysis, and tracking how predictions evolve as evidence changes. The deliberation is a collaboration between the analyst and the committee, not a process that happens to the analyst.

---

## 2. Design Principles

**2.1 Deliberation is visible.** Every profile's full reasoning is accessible to the analyst, not just a 120-character summary. The analyst sees why each profile arrived at its confidence, what evidence it weighted heavily, what it dismissed, and what it flagged as uncertain. Visibility doesn't mean noise — the default view is a structured summary, but the full reasoning is one click away.

**2.2 The committee is configurable.** Not every question needs all 8 profiles. A logistics question might need Base Rate Analyst, Decomposer, and Historian but not Sentiment Decoder. A market question might emphasize Reflexivity Modeler. The analyst can compose the committee per question, adding or removing profiles, or adjusting their consensus weights. The default 8-profile committee remains the standard starting point.

**2.3 Dissent is a feature, not a problem.** When a profile dissents from consensus, the analyst should be able to engage with the dissent: see the reasoning, decide whether it's meaningful, and optionally ask the committee to explore the dissenting scenario further. Dissent that gets 120 characters and a ⚡ marker is dissent that can't be evaluated. V2 makes dissent a first-class analytical object.

**2.4 Predictions evolve.** A prediction session is not a single pass. When new evidence arrives (from OSS, from the analyst, from events), the prediction can be updated in-place. The evolution is tracked — each version with its evidence delta, its confidence shift, and the profiles that changed their assessment. The analyst sees the trajectory of the prediction, not just the latest snapshot.

**2.5 The analyst can intervene mid-process.** Not to override the committee — to inform it. The analyst can inject context ("I have reason to believe X based on a source the committee doesn't have access to"), challenge a specific profile ("your historical analogy doesn't hold because Y"), or request a second pass with a constraint ("run the Decomposer again on the supply chain sub-question specifically").

**2.6 Calibration is useful, not just a number.** Brier scores tell which profiles are accurate overall. V2 adds domain-specific calibration: which profiles are accurate on which types of questions? When the analyst composes a committee for a geopolitical question, V2 can suggest: "The Historian has Brier 0.18 on geopolitical questions but 0.31 on economic ones. Consider upweighting for this question type."

---

## 3. The Human Relationship Model

### 3.1 The Analyst's Role at Each Deliberation Stage

| Stage | V1 Role | V2 Role |
|---|---|---|
| **Question framing** | Submit question as-is | Review framing, optionally refine before dispatch. Adversarial framing check: "This question is ambiguous between X and Y — which do you mean?" |
| **Committee composition** | Fixed 8 profiles | Configure committee per question. Add/remove profiles. Adjust weights. V2 suggests composition based on domain-specific calibration. |
| **Profile dispatch** | Invisible | Observable — see each profile working. Live progress if artifact panel supports streaming. |
| **Deliberation** | Invisible | Visible — see each profile's full reasoning, evidence cited, confidence justification |
| **Dissent** | 120 chars + ⚡ marker | First-class object — see full dissent reasoning, engage with it, request exploration |
| **Consensus** | Receive confidence + brief | Review consensus with full transparency into how it was derived. Challenge if reasoning seems flawed. |
| **Post-consensus** | Session closed | Follow-up — direct specific profiles to explore scenarios. Request second pass with new constraints. |
| **Evolution** | Submit new question | Update in-place — new evidence → updated assessment → tracked evolution |
| **Calibration** | Read Brier scores | Domain-specific calibration. Guidance on which profiles to trust for which question types. |

### 3.2 The Analyst's Workflow

The typical V2 workflow:

1. **Question formation.** The analyst has a question from an OSS evidence investigation: "Is Iran pre-positioning for limited interdiction rather than full blockade?" The evolved question arrives with its evidence context — the OSS claims, source credibility weights, and evolution history.

2. **Framing review.** Before dispatch, the artifact panel shows: "This question could be interpreted as: (a) Is Iran currently moving assets into interdiction positions? (b) Does Iran's strategic posture favor interdiction over blockade? Which framing should the committee use?" The analyst selects or refines.

3. **Committee composition.** V2 suggests a committee based on question domain: "Geopolitical-military question. Recommended committee: Base Rate Analyst (Brier 0.18 on geopol), Historian (0.21), Decomposer (0.15), Contrarian (0.23). Optional: Reflexivity Modeler (0.28 on geopol — weaker, but models self-fulfilling prophecy). Not recommended: Sentiment Decoder (0.39 on geopol — poor calibration for this domain)." The analyst accepts or modifies.

4. **Deliberation with transparency.** The committee runs. The artifact panel shows progress: each profile's assessment appearing as it completes. The analyst can see the reasoning in real time — not just the confidence number but the evidence each profile cited, the assumptions it made, the uncertainties it flagged.

5. **Dissent engagement.** The Contrarian dissents: "Historical analogies to 1987 tanker war suggest Iran would escalate to full blockade under domestic pressure." Confidence: 70% for full blockade. The analyst reads the full reasoning and finds it compelling. They direct: "Run the Historian on the 1987 tanker war analogy specifically. What happened after initial interdiction?"

6. **Second pass.** The Historian runs a focused analysis on the 1987 precedent. The result updates the deliberation: "The 1987 tanker war began with limited interdiction and escalated to broader engagement over 6 months, but only after direct US military confrontation. Without that trigger, the interdiction remained limited." The Contrarian's dissent is contextualized, not dismissed.

7. **Consensus with analyst input.** The consensus integrates the second-pass analysis. The analyst adds context: "My OSS evidence shows no US military posture suggesting direct confrontation. This supports the limited interdiction scenario." The final assessment is a collaboration between the committee's analytical rigor and the analyst's domain knowledge.

8. **Evolution.** Two weeks later, new OSS claims arrive showing Iranian naval movements consistent with escalation. The analyst reopens the prediction session. V2 shows: "Evidence delta since last assessment: 12 new claims, 3 suggesting escalation. Recommend committee re-run with updated context." The prediction updates in-place, with the evolution tracked — the trajectory from "limited interdiction likely" to "escalation indicators emerging."

### 3.3 What the Analyst Does NOT Do

The analyst does not:
- Write the profiles' assessments (the committee does the analytical work)
- Override consensus by fiat (the analyst can inform and challenge, not dictate)
- Manage the LLM calls directly (the infrastructure is invisible)
- Calibrate the profiles manually (calibration is automatic from outcome tracking)

The analyst provides: question framing, domain context the committee lacks, evaluation of dissent significance, and direction for follow-up analysis. The committee provides: structured multi-perspective analysis, calibrated confidence estimation, and systematic falsification conditions. Each does what the other can't.

---

## 4. Architecture Sketch

### 4.1 Prediction Session as Persistent Object

V1 prediction sessions are single-pass: dispatch → deliberate → consensus → done. V2 sessions are persistent objects that evolve:

```
prediction_session:
  id: uuid
  question:
    text: "Is Iran pre-positioning for limited interdiction?"
    framing: "strategic-posture"  # selected by analyst from framing options
    oss_context: [claim_ids]      # evidence from OSS, with credibility weights
    evolution_history: [
      { version: 1, question: "Will Iran block the strait?", date: "..." },
      { version: 2, question: "Limited interdiction vs full blockade?", date: "...", 
        evidence_trigger: [claim_ids] }
    ]
  committee:
    profiles: ["base_rate", "historian", "decomposer", "contrarian"]
    weights: { base_rate: 0.30, historian: 0.25, decomposer: 0.25, contrarian: 0.20 }
  deliberation:
    passes: [
      { pass: 1, assessments: [...], consensus: 0.65, dissents: [...] },
      { pass: 2, trigger: "analyst-directed historian followup",
        assessments: [...], consensus: 0.62, dissents: [...] }
    ]
  analyst_inputs: [
    { type: "context", text: "No US military posture suggesting confrontation", date: "..." },
    { type: "challenge", target: "contrarian", text: "1987 analogy requires direct trigger", date: "..." }
  ]
  evolution: [
    { version: 1, date: "...", consensus: 0.65, evidence_base: 23 },
    { version: 2, date: "...", consensus: 0.58, evidence_base: 35, delta: "escalation indicators" }
  ]
  falsification_conditions: [...]
  calibration:
    outcome: null  # set when resolved
    brier_scores: {}  # per-profile, computed on resolution
```

### 4.2 Configurable Committee

The 8 standard profiles remain available. V2 adds:

**Domain-specific calibration.** Each profile's Brier score is broken down by question domain (geopolitical, economic, military, technological, social). When the analyst composes a committee, V2 surfaces calibration data: "For geopolitical questions, the Decomposer has outperformed the Sentiment Decoder by 0.15 Brier points."

**Committee suggestion engine.** Given a question domain, V2 suggests a committee composition optimized for calibration. The analyst can accept, modify, or use the full default committee. The suggestion is a starting point, not a prescription.

**Profile re-weighting.** Within a session, the analyst can adjust profile weights: "I trust the Historian more on this question than the base rates suggest." The consensus recalculates with the adjusted weights. The original weights and the analyst's adjustment are both recorded.

**Ad-hoc profiles.** The analyst can create a temporary profile for a specific question: "For this question, I want a profile that specifically considers the Iranian domestic political calendar." The ad-hoc profile runs with a custom prompt, participates in the deliberation, and is not reused unless explicitly promoted to the standard set.

### 4.3 Deliberation Transparency

V1 returns 120-character summaries per profile. V2 provides three levels of detail:

**Level 1: Dashboard (default).** Each profile's confidence, one-sentence key reasoning, agreement/dissent indicator. The analyst sees the shape of the deliberation at a glance.

**Level 2: Structured summary.** Each profile's confidence, evidence cited, key assumptions, uncertainty flags, and dissent reasoning if applicable. Enough to evaluate the quality of each profile's analysis without reading the full transcript.

**Level 3: Full reasoning.** The complete profile assessment as generated by the LLM call. Available on demand for any profile. This is the "show me your work" view.

The artifact panel renders Level 1 by default, expands to Level 2 on click, and opens Level 3 in a detail panel. The analyst controls the level of detail they engage with.

### 4.4 Dissent as First-Class Object

```
dissent:
  profile: "contrarian"
  consensus_confidence: 0.65
  dissent_confidence: 0.70  # for the alternative outcome
  reasoning_summary: "Historical analogies to 1987 suggest escalation path"
  full_reasoning: "..."
  evidence_cited: [claim_ids]
  analyst_response: null | {
    action: "explore" | "acknowledge" | "dismiss",
    direction: "Run Historian on 1987 tanker war specifically",
    result: { pass_id: 2, findings: "..." }
  }
```

Dissents are tracked across session evolution. If the Contrarian dissented in pass 1 and the evidence later supported the dissent, that outcome feeds into the Contrarian's calibration positively — rewarding the dissent, not just the consensus.

### 4.5 Analyst Intervention Points

The analyst can intervene at three points:

**Pre-dispatch: Question framing.** Review and refine the question before the committee sees it. The system can offer adversarial framing suggestions: "This question presupposes X. Consider also framing as Y."

**Mid-deliberation: Context injection and challenge.** After seeing profile assessments, the analyst can inject context ("I have additional information: ...") or challenge specific assessments ("Your analogy to X doesn't account for Y"). These become inputs to a follow-up pass.

**Post-consensus: Directed follow-up.** After the consensus is formed, the analyst can direct specific profiles to explore scenarios further: "Run the Decomposer on the economic implications sub-question." Follow-up passes are recorded as part of the session's deliberation history.

### 4.6 What Stays

- The 8 standard ACP profiles and their epistemic stances
- The Brier scoring calibration loop (deepened with domain specificity)
- The OSS→SWARMFISH calibration pathway (promote/falsify → outcome feedback)
- PostgreSQL session storage
- Docker container architecture (but potentially migrated to A0 plugin)

---

## 5. The Evolution Model

Predictions evolve. Intelligence doesn't stand still.

**How prediction evolution works:**

1. A prediction session is created with initial evidence and a consensus.
2. New evidence arrives (from OSS automatic ingestion, from analyst submission, from events).
3. The analyst triggers an evolution: "Update this prediction with new evidence."
4. V2 shows the evidence delta: "12 new claims since last assessment. 3 are inconsistent with the current consensus."
5. The committee re-runs (same composition or adjusted) with the new evidence in context plus the previous deliberation history. Profiles can reference their own prior assessments.
6. A new consensus forms. The evolution is recorded: previous confidence, new confidence, evidence that drove the change, profiles that shifted.
7. The analyst sees the trajectory: a chart showing confidence over time with evidence arrival markers. "The prediction shifted from 65% to 58% after logistics evidence on March 15, then recovered to 63% after diplomatic context on March 20."

**Why this matters:**

Single-pass predictions are snapshots. They don't capture the analytical process. An evolved prediction with its trajectory is a narrative — the story of how the assessment changed as reality unfolded. That narrative is more valuable than any single confidence number because it shows the analyst how sensitive the prediction is to different types of evidence.

The evolution trajectory also feeds calibration. A profile that consistently shifts its assessment in the right direction when new evidence arrives is tracking well, even if its initial assessment was off. A profile that doesn't shift when it should is anchored. V2 calibration can measure this — tracking responsiveness to evidence, not just final accuracy.

---

## 6. Connection to OSS V2

The two services are a single analytical pipeline from the analyst's perspective:

**OSS collects and organizes evidence.** The analyst's active question in OSS drives what evidence is collected and how it's weighted. Source credibility is analyst-informed.

**SWARMFISH assesses probability.** The analyst's evolved question, with curated evidence from OSS, flows into a prediction session. The committee deliberates on the analyst's evidence base, not on raw data.

**The loop deepens:**

- OSS question evolution → SWARMFISH question framing (the same question at different stages)
- OSS evidence summaries → SWARMFISH deliberation context (curated evidence, not raw claims)
- OSS source credibility → SWARMFISH evidence weighting (the analyst's source judgments carry through)
- SWARMFISH falsification conditions → OSS monitoring targets ("watch for evidence of X")
- SWARMFISH prediction evolution → OSS question re-evaluation ("if the prediction shifted, should the question evolve?")

**The artifact interface unifies them.** The analyst doesn't switch between two separate services. The artifact panels coordinate: the OSS panel shows evidence, the SWARMFISH panel shows the deliberation. Evidence from OSS can be dragged into a SWARMFISH context. Falsification conditions from SWARMFISH appear as monitoring targets in OSS. The two panels are views into a single analytical process.

---

## 7. GRASP Connection

From the world models research thread: GRASP's parallel planning with virtual states and consistency constraints applies directly to SWARMFISH's multi-profile deliberation.

**Current model (V1):** Each profile assesses independently. Consensus is a weighted average. There's no interaction between profiles during deliberation.

**GRASP-inspired model (V2 future):** Profiles maintain virtual assessment states that are optimized simultaneously with consistency constraints. If Profile A cites evidence that contradicts Profile B's assumption, the consistency constraint forces B to address the contradiction. The deliberation becomes interactive at the computational level, not just at the summary level.

This is aspirational — it would require significant architectural changes to the ACP pipeline. But the GRASP framework provides the mathematical foundation for what "interactive deliberation" means formally: parallel assessment with pairwise consistency constraints, not just independent assessments followed by averaging.

Timeframe: 🔴 Future — file as architecture guidance for SWARMFISH V3.

---

## 8. Calibration V2

### 8.1 Domain-Specific Brier Scores

V1: one Brier score per profile across all questions.

V2: Brier scores broken down by question domain. Each resolved prediction tags the profiles' accuracy within the question's domain. Over time, the system knows: "The Historian is excellent on geopolitical questions (Brier 0.15) but poor on technology questions (Brier 0.38)."

### 8.2 Responsiveness Score

A new calibration metric: how quickly does a profile shift its assessment when disconfirming evidence arrives? A profile that anchors to its initial assessment despite strong contrary evidence is poorly responsive. A profile that shifts appropriately is well-calibrated on responsiveness. This only becomes measurable with the evolution model — you need multiple passes to observe responsiveness.

### 8.3 Dissent Accuracy

When a profile dissents from consensus and the outcome eventually validates the dissent, the profile's dissent accuracy increases. This rewards contrarian profiles for being right when they disagree, not just penalizes them for being different. Without this metric, the Contrarian profile is penalized for every dissent that doesn't validate, which biases the calibration toward consensus-seeking behavior.

### 8.4 Calibration as Guidance

V1 calibration is retrospective — "this profile scored X." V2 calibration is prospective — "for this type of question, these profiles are likely most accurate." The artifact panel surfaces calibration guidance when the analyst composes a committee, making calibration useful in the moment of decision rather than only in retrospective review.

---

## 9. Open Questions

**Q1: LLM cost of multi-pass deliberation.** V1 runs 8 LLM calls per question. V2 with configurable committees, follow-up passes, and evolution could run 20-30+ calls per prediction lifecycle. On Qwen3.5-27B locally this is compute time, not dollar cost. But a 5-profile committee with 3 passes at ~30 seconds per call is ~7.5 minutes of inference. Is the analyst willing to wait? Does the artifact panel's progressive rendering (show results as they arrive) mitigate the wait?

**Q2: Analyst intervention quality.** When the analyst injects context or challenges a profile, that intervention becomes part of the deliberation record. If the analyst's intervention is wrong (based on bad information, or a faulty intuition), it could degrade the consensus quality. Should interventions be tagged as "analyst input — unverified" to maintain a distinction between evidence-grounded and analyst-contributed context?

**Q3: Profile interaction.** V2's follow-up passes allow the analyst to direct profiles to respond to each other's assessments. But should profiles interact automatically? If Profile A cites evidence that contradicts Profile B's assumption, should B be asked to address the contradiction without analyst direction? This is the GRASP consistency constraint question — automatic interaction improves deliberation quality but adds complexity and cost.

**Q4: Evolution triggers.** When should the system suggest re-running a prediction? Options: (a) only when the analyst requests it, (b) when OSS ingests claims tagged as relevant to the prediction's falsification conditions, (c) on a schedule (weekly refresh). Option (b) is most aligned with the OSS integration — falsification conditions become automated triggers.

**Q5: Committee meta-learning.** Over many prediction sessions, patterns emerge: certain committee compositions outperform others on certain question types. Should V2 build a meta-model of committee performance — learning which compositions to recommend based on accumulated outcome data? This is the world model approach applied to committee optimization.

---

*V2 opens the box. The analyst sees the deliberation, participates in it, directs follow-up analysis, and tracks predictions as they evolve. The committee is a collaborator, not a black box. The deliberation is a conversation, not a process. Dissent is a feature, not a problem. And the prediction isn't a snapshot — it's a trajectory that moves with the evidence.*

*V2 is complete when Jake says "I understand why the committee thinks what it thinks, and I can push back when they're wrong."*
