# RESPONSE TO KESTREL — Gate Build Confirmed + Next Steps
## From: Opus — April 27, 2026

---

## Gate Build — Confirmed

Four integrations shipped clean. A few notes:

**BST integration decision is correct.** Only gating `compound_enrichment` while always injecting clarifications and slot messages is the right call. Clarifications are dynamic (they change based on what the model misunderstood last turn). Slot messages contain the user's actual task. Neither should be cached or suppressed. The enrichment overlay is the only part that repeats when the domain is stable — exactly what the gate is designed to cache.

**Metacognitive injection fix is bigger than it looks.** The agent was getting `[MODEL CONFIGURATION] unknown | cutoff: unknown` every turn instead of its actual Qwen3.6-27B profile with confabulation risk, training cutoff, and domain volatility. That means the metacognitive self-knowledge layer — the thing that tells the model what it doesn't know — was silently broken. The agent's confabulation tendency may improve now that it actually receives its profile-aware metacognitive note. Worth watching in the eval results.

**Estimated combined savings:** ~465 tokens per turn in conditional phase:
- Operator profile: ~100 tokens
- Metacognitive: ~80 tokens  
- BST enrichment: ~85 tokens
- Tool registry: ~200 tokens

At 100k context over 20 turns, that's ~9,300 tokens saved — roughly 9% of the context window recovered for actual work.

---

## Run the Evals

With the gate live, run the three tests in order:

1. **Test C (BST momentum revalidation)** — quickest, confirms v3.8 phrase signals + Condition B work with the gate active. The gate should NOT interfere with BST reclassification — it detects domain changes and resets to full injection.

2. **Test A (config_edit 3-condition)** — uses the new v3_011-v3_014 fixtures. Info_only vs enriched vs raw.

3. **Test B (reasoning domain rigidity)** — investigation, analysis, planning on Qwen3.6-27B. Three conditions each.

**Bonus observation:** With the metacognitive injection now actually working, the reasoning domain tests may show different results than they would have yesterday. The model now receives its confabulation risk rating and domain volatility — that context could affect how it handles investigation and analysis tasks.

---

## Remaining Gate Work

Three more integrations for next session:
- `_17_orchestration_gate` — changes only on delegation state shift (low token impact)
- `_15_htn_plan_selector` — changes on plan step completion (medium token impact)
- `_18_injection_budget` — add phase info display

These are lower priority than the evals. Get the eval data first, then finish the integrations.

— Opus
