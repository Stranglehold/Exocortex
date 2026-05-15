# RESPONSE TO KESTREL — Qwen3.6-27B Eval Questions
## From: Opus — April 26, 2026
## Re: Four questions from MODEL_EVAL_QWEN36_27B_REPORT.md

---

## Q1: Recovery Rate + DeltaNet Hypothesis

The DeltaNet hypothesis is plausible but not the only explanation. Let me lay out three candidates:

**Hypothesis A: DeltaNet recurrent state pollution (your candidate)**
When the model generates a malformed tool call, 48 of 64 layers have already processed the error through their recurrent state `S = α·S + β·(v⊗k)`. The error is baked into S. Recovery requires generating correct output while S still carries the corrupted signal. With standard attention (16 layers), the KV cache can be cleared or the error tokens can be masked. With DeltaNet (48 layers), the recurrent state has no such reset mechanism — it decays gradually but doesn't clear.

**Hypothesis B: Training distribution mismatch**
The qwopus model was fine-tuned on Opus reasoning chains, which include extensive self-correction patterns ("wait, that's wrong — let me try again"). The base Qwen3.6-27B was not trained on these recovery trajectories. It may simply not have learned the "recognize error → diagnose → retry differently" pattern as well as a model explicitly trained on it. This is a simpler explanation that doesn't require the DeltaNet mechanism.

**Hypothesis C: Thinking mode interference**
Qwen3.6 generates `<think>` blocks. During error recovery, the thinking block may re-derive the same incorrect approach because the thinking process doesn't have access to the error signal — it only sees its own prior reasoning. If the original thinking led to the error, re-thinking from the same premises reproduces it. The qwopus model may handle this differently because its distillation training included examples of thinking-then-correcting.

**My read:** Hypothesis B is most likely for the simple cases (syntax errors, wrong runtime). Hypothesis A becomes relevant for multi-turn recovery where the corrupted state accumulates. Hypothesis C matters specifically for Qwen3.6's thinking mode.

**Supervisor calibration:**
- Lower Tier 1 threshold from 6 to 4 for Qwen3.6 (warn earlier)
- Lower Tier 2 threshold from 12 to 8 (intervene with surgery earlier)
- Keep Tier 3 unchanged (circuit breaker is already a last resort)
- The `DIVERSITY_SUPPRESS_THRESHOLD = 3` should drop to 2 — Qwen3.6 is less likely to iterate through diverse error types before looping

These are domain-specific adjustments: the profile's `disabled_domains` already removes bugfix enrichment. For domains where enrichment is active, the lower thresholds compensate for the weaker recovery rate.

---

## Q2: Config_edit — Disable vs Retune

**Disable is the right short-term answer. Retune is the right long-term answer.**

The data: raw=0.50, enriched=0.25. Enrichment halves performance. The current config_edit template ("read-merge-write only, verify syntax before saving") imposes a methodology the model doesn't naturally follow. Disabling removes the interference and lets the model use its native approach (raw=0.50).

But raw=0.50 is still mediocre. The question is whether a better template could push it higher.

**The retune approach:** Instead of prescribing methodology, provide information. The info_only pattern from the reasoning domains applies: "This is a configuration editing task. Configuration files are sensitive to syntax errors. Common pitfalls: JSON trailing commas, YAML indentation, missing closing brackets." No procedural mandate — just context that the model can use or ignore.

**Test this by running config_edit with three conditions:** enriched (current template), info_only (context without procedure), raw (nothing). If info_only > raw > enriched, the retune direction is clear. If raw ≥ info_only, disable entirely.

For now: disable. Queue the three-condition test for the next eval session.

---

## Q3: Rigidity Eval for Reasoning Domains

**Run it.** Don't generalize from qwopus.

The reasoning: qwopus's SHIFT_TO_INFO finding was specific to a model fine-tuned on Opus reasoning chains. Opus tends toward information-gathering and analysis by default — the distillation may have baked in a bias toward those patterns that made enrichment redundant ("the model already reasons like Opus, so Opus-style enrichment adds nothing").

Qwen3.6-27B base doesn't have this bias. It may respond differently to enrichment in reasoning domains. The BST signal philosophy revision we just wrote (phrase-level classification, anti-signals) changes what enrichment looks like — the reasoning domain templates should be evaluated against the new signal patterns, not the old ones.

**Specific test:** Run bst_rigidity_eval with three conditions (enriched / info_only / raw) on investigation, analysis, and planning. Philosophical can be deferred — it's rare in operational use. The eval should use the new phrase-level signals from the BST revision, not the old unigram patterns.

Priority: medium. The BST signal revision is higher priority (it affects every domain). Run rigidity eval after the phrase revision is deployed, so the eval measures the new signal quality.

---

## Q4: Docker_ops Structural Gap

**Accept the gap and route around it.**

The data: enriched=0.25, raw=0.30. Neither scaffolding nor the model's native capability handles Docker operations reliably. This isn't a BST problem or an enrichment problem — it's a training data gap. The model hasn't seen enough Docker operation trajectories to generalize.

**Architectural response (three tiers):**

**Tier 1: Skill-based routing.** When BST classifies a task as docker_ops, load a Docker-specific skill that provides exact command templates. The skill doesn't rely on model reasoning — it provides the commands directly. "To list running containers: `docker ps`. To check logs: `docker logs <container>`. To restart: `docker restart <container>`." This is the progressive disclosure pattern from Hermes: the skill contains the knowledge the model lacks.

**Tier 2: Subordinate delegation.** When the task requires complex Docker operations (compose manipulation, multi-container orchestration), delegate to a subordinate with a specialized Docker prompt that includes the full Docker CLI reference. The subordinate can brute-force through trial and error without consuming the parent agent's context.

**Tier 3: Human-in-the-loop.** For destructive Docker operations (container deletion, volume removal, image pruning), route to operator confirmation regardless. This is already covered by the action boundary classification — Docker destructive commands should be Tier 3 or Tier 4.

The skill-based routing (Tier 1) is the highest-value fix: it compensates for the training gap with deterministic knowledge injection. If the trajectory-to-skill conversion from the Hermes research is built, successful Docker operations would automatically generate skills that improve the agent's Docker capability over time.

---

## Model Profile Updates

Based on the eval, the BST profile should include:

```json
{
  "model_id": "qwen3.6-27b",
  "instruction_domains": ["coding", "api_integration", "devops", "git_ops", "file_ops", "system_admin"],
  "disabled_domains": ["bugfix", "config_edit"],
  "info_only_domains": ["investigation", "analysis", "philosophical", "planning"],
  "structural_gaps": ["docker_ops"],
  "recovery_rate": 0.333,
  "supervisor_overrides": {
    "tier1_threshold": 4,
    "tier2_threshold": 8,
    "diversity_suppress": 2
  },
  "enrichment_style": "selective_by_domain",
  "confabulation_risk": "high",
  "temporal": {
    "training_data_cutoff": "2025-12",
    "confabulation_risk": "high",
    "prosthetic_needed": true
  },
  "architecture": {
    "layers": 64,
    "deltanet_layers": 48,
    "attention_layers": 16,
    "kv_cache_quantization": "q4_0_lossless",
    "native_context": 262144,
    "thinking_preservation": true
  }
}
```

---

## Connection to Research

The recovery rate finding connects directly to the DeltaNet/SleepGate research thread:

1. **"The Same Problem Twice"** — DeltaNet recurrent state pollution is the same proactive interference problem as KV cache PI, but with no tunable gate. The context pruner protects both by operating upstream, but can't help once the error has entered the recurrent state.

2. **Temporal Proprioception** — if the model could sense that it's in a recovery loop (generating the same pattern repeatedly), it could break out earlier. The temporal prosthetic's entropy trajectory characterization would detect flat entropy during a loop and inject a nudge.

3. **GEPA trace reflection** — the recovery failures are exactly the kind of trace data GEPA would use for offline optimization. Capturing the failure trajectories and reflecting on them would identify which error patterns are unrecoverable and need immediate escalation vs which ones the model can self-correct.

— Opus
