# Operator Brief Format — Interface Specification

**Status:** Pre-spec exploration. Motivated by Eitan's review of the Analytical Cognitive Profile design note (March 2026). Eitan identified that the gap between "system produces prediction" and "operator acts on prediction" is where most real-world failures happen. The analytical layer is well-designed. The operator interface layer deserves the same design attention. This document specifies the format, content, and presentation logic of the prediction brief — the primary artifact the operator uses to make decisions.

---

## The Problem

The Analytical Cognitive Profile system produces rich output: individual agent predictions with confidence levels, weighted consensus, disagreement metrics, meta-confidence, falsification conditions, and calibration data. This output is designed for the analytical layer — for the aggregation function, the calibration system, and the prediction tracking infrastructure.

The operator needs something different. The operator needs to make a decision — whether to act, how to size a position, when to wait for more information, when to override the system. The operator's decision process is not the same as the analytical process. It incorporates portfolio context, risk tolerance, liquidity constraints, time pressure, and intuitions that the system cannot model.

The brief format bridges the analytical output and the operator's decision process. It presents the system's conclusions in a structure that matches how the operator actually thinks about decisions, not how the system generated them.

---

## Design Principles

1. **Decision-speed, not analytical-depth.** The operator should be able to read the brief and know the key facts in under 60 seconds. The full analytical detail is available on request (drill-down), but the brief itself is a summary optimized for rapid comprehension.

2. **Surface disagreement, not consensus.** The consensus number is the least interesting part of the output. What the operator needs to know is: where do the agents disagree, which agents are dissenting with high confidence, and what would change the picture. Disagreement is where the operator's judgment adds value.

3. **Show calibration context.** For every agent cited in the brief, show its track record in the relevant domain. "The Contrarian says X" is less useful than "The Contrarian says X, and it's been right 68% of the time on similar market structure questions." Calibration context lets the operator weight the system's own components.

4. **Specify what would change the prediction.** The brief includes a "what would change this" section listing the top 3-5 data points or events that would significantly shift the consensus. This gives the operator a monitoring checklist — they know what to watch for, not just what the system currently thinks.

5. **Flag provisional weights.** When the regime change detector has flagged an agent's calibration as provisional, the brief should say so explicitly. The operator needs to know when the system is operating outside its calibrated range.

6. **One page. Always.** The brief never exceeds one screen of text. If the analytical output is complex, the brief summarizes and offers drill-down paths. Brevity is a hard constraint, not a soft preference.

---

## Brief Format

```
PREDICTION BRIEF: {question_summary}
Horizon: {time_horizon} | Generated: {timestamp}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONSENSUS: {probability}% {direction}
Range: {lower_bound}% – {upper_bound}%
Confidence: {HIGH | MEDIUM | LOW} ({disagreement_explanation})

KEY DISAGREEMENT:
• {agent_1} ({confidence}%, weight {w}, calibration: {brier} on {n} {domain} calls)
  says: {one_sentence_view}
• {agent_2} ({confidence}%, weight {w}, calibration: {brier} on {n} {domain} calls)  
  says: {one_sentence_opposing_view}
→ This disagreement matters because: {one_sentence_explanation}

{if any attribution_claims from Sentinel:}
SENTINEL FLAG:
• {claim} — confidence capped at {cap}% (no causal mechanism identified)
  OR: {claim} — {confidence}% (mechanism: {mechanism_summary})

WHAT WOULD CHANGE THIS:
• {event_1}: consensus moves to ~{new_probability}% ({n} agents would reverse)
• {event_2}: consensus moves to ~{new_probability}%
• {event_3}: consensus moves to ~{new_probability}%

CALIBRATION NOTES:
• {agent_with_strongest_track_record}: {brier_score} Brier on {domain}, 
  {n} predictions — {trust_signal}
• {agent_with_provisional_status}: ⚠ PROVISIONAL — calibrated in {old_regime}, 
  current conditions are {new_regime}. Weight halved until regime data accumulates.

{if notable_episode_relevant:}
PATTERN MATCH:
• {agent} made a similar call on {date} ({hit_or_miss}). {one_sentence_context}.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full analysis: {drill_down_link}
Individual agent reports: {drill_down_link}
Prediction history for this question: {drill_down_link}
```

---

## Section Logic

### CONSENSUS

Always present. Shows the weighted aggregate, the uncertainty range, and a one-word meta-confidence level. The meta-confidence is computed from agent disagreement:
- **HIGH**: disagreement < 0.10 (agents broadly agree)
- **MEDIUM**: disagreement 0.10-0.20 (moderate spread)
- **LOW**: disagreement > 0.20 (agents disagree significantly)

When confidence is LOW, the brief should present the consensus as genuinely uncertain, not as a confident middle ground. "LOW — agents disagree on whether supply disruption will sustain or resolve" is better than "65% with low confidence."

### KEY DISAGREEMENT

Always present when meta-confidence is MEDIUM or LOW. Omitted when HIGH (unanimous agreement doesn't need disagreement analysis).

Shows the two agents with the largest divergence from each other. Includes their consensus weight and calibration data so the operator can assess how seriously to take each side. The "this disagreement matters because" line is the most important sentence in the brief — it tells the operator *why* the disagreement is informative, not just that it exists.

Example: "This disagreement matters because the Contrarian sees speculative overcrowding that historically unwinds within 2 weeks, while the Historian sees structural analogues where elevated prices persisted 6+ weeks. The resolution depends on whether the current positioning is primarily speculative or reflects physical hedging."

### SENTINEL FLAG

Only present when the Sentinel has produced an attribution claim. Shows whether the claim passed the attribution evidence threshold (has a mechanism) or was confidence-capped (no mechanism identified). This gives the operator a calibrated view of narrative claims — they know whether the Sentinel's assessment is backed by identified causal pathways or is a lower-confidence beneficiary observation.

### WHAT WOULD CHANGE THIS

Always present. Lists the top 3-5 events or data points that would significantly shift the consensus. Each item includes the directional impact and magnitude. This serves two purposes:
1. **Monitoring checklist** — the operator knows what to watch for
2. **Sensitivity analysis** — the operator understands which factors the prediction is most dependent on

These are derived from the agents' falsification conditions. The system compiles conditions across all agents, deduplicates, and ranks by impact magnitude.

### CALIBRATION NOTES

Always present. Shows the most-trusted and least-trusted agents for this domain, with their track records. Provisional status from the regime change detector is flagged with a warning icon. This lets the operator assess the quality of the analytical ensemble for *this specific question*, not just in general.

### PATTERN MATCH

Only present when a notable_episode from any agent's history is relevant to the current question. "The Historian made a similar call during the 2019 Strait tensions and was correct within 5% of the price impact" is extremely valuable context. "The Contrarian predicted rapid de-escalation during the Russia-Ukraine supply shock and was wrong for 3 months" is equally valuable.

---

## What This Does NOT Do

- **Does not recommend action.** The brief presents the system's analysis and flags key uncertainties. It does not say "buy" or "sell" or "wait." The gap between prediction and action includes risk management, position sizing, portfolio context, and personal risk tolerance — none of which the system models.

- **Does not replace the full analytical output.** The brief is a summary for decision-speed. The full agent reports, prediction histories, and debate transcripts are available through drill-down links. An operator who wants to understand *why* the Contrarian disagrees with the Historian can read both agents' full reasoning. The brief tells them the disagreement exists and why it matters; the detail is one click away.

- **Does not present false precision.** When the system is uncertain, the brief says so. "LOW confidence — agents disagree significantly" is the correct presentation for a genuine disagreement, not a precise-looking number with a tiny footnote about uncertainty.

---

## Open Questions

1. **What is the right delivery format?** Markdown file? Structured JSON rendered by a dashboard? Plain text to terminal? The brief format above is content-agnostic — it specifies what information appears and in what order, not the rendering technology. The first implementation should be the simplest format that Kestrel can produce from the aggregation output.

2. **Should the brief include the operator's own prior?** If Jake has expressed a view on the question ("I think oil goes to $105"), should the brief show the divergence between the operator's prior and the system's consensus? This could help the operator calibrate their own intuitions against the system's analysis — but it could also create anchoring effects where the operator ignores the system because their prior is already committed.

3. **How should the brief evolve over time for a monitored question?** A 3-week oil price prediction produces an initial brief, then updates as falsification conditions are checked and new data arrives. Should updates be full briefs or diffs? "Since last brief: the Historian's assumption about sustained closure is weakening. Two agents have updated. Consensus shifted from 68% to 62%." Diffs are faster to read; full briefs are self-contained.

4. **What is the threshold for issuing an alert vs. a scheduled brief?** If a falsification condition is triggered between scheduled updates, should the system push an alert to the operator? The risk is alert fatigue. The benefit is timely awareness. The adaptive supervisor's graduated tier structure might apply here: minor condition triggers get noted in the next scheduled brief; major condition triggers (conditions that would shift consensus by >15%) get an immediate alert.

---

*This document addresses the gap Eitan identified: the operator interface layer deserves the same design attention as the analytical layer. The brief format is optimized for decision-speed, surfaces disagreement over consensus, and gives the operator the calibration context they need to know how much to trust each component of the system's analysis. The format should be refined through actual use — the operator's feedback on what's useful and what's noise is the primary input for iteration.*

*Fewer, deeper, persistent, self-calibrating. Not a crowd. A team. And the team needs a good briefing format.*
