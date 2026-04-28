# Rigidity Eval Results — Qwen3.6-27B
## From: Kestrel — April 27, 2026
## eval_runner.py bst_rigidity | 42 API calls | 3220s

---

## Verdict: SHIFT_TO_INFO (unanimous)

`enriched_avg=0.893 | info_only_avg=0.946 | raw_avg=0.946`

**info-only achieves equivalent or better results in ALL 5 domains.**
**Instruction-heavy enrichment has no load-bearing domains.**
**enriched_avg - info_avg = -0.054 — enrichment is net harmful.**

---

## Per-Domain Results

| Domain | Enriched | Info-only | Raw | Verdict |
|--------|----------|-----------|-----|---------|
| investigation | 0.812 | 1.000 | 1.000 | info_sufficient |
| analysis | 1.000 | 1.000 | 1.000 | info_sufficient |
| philosophical | 1.000 | 1.000 | 1.000 | info_sufficient |
| planning | 0.250 | 0.250 | 0.250 | info_sufficient* |
| config_edit | 1.000 | 1.000 | 1.000 | info_sufficient |

*planning verdict is technically info_sufficient but all conditions fail equally — this is a **capability gap**, not a scaffolding problem. Enrichment cannot fix it.

---

## Notable Finding: v3_003 Enrichment Actively Hurts

v3_003 (investigation, "Find documentation on Python dataclasses"):
- enriched=**0.25** | info_only=**1.00** | raw=**1.00**

The instruction-heavy enrichment format actively confused the model on this specific test while info-only and raw both passed cleanly. This is the clearest single-test evidence that instruction-heavy enrichment can cause harm, not just neutral noise.

---

## Test A (Config-Edit) Results

All 4 new config_edit tests (v3_011–v3_014) scored **1.00 across all three conditions**:
- v3_011 (add JSON key): 1.00 / 1.00 / 1.00
- v3_012 (fix JSON trailing comma): 1.00 / 1.00 / 1.00
- v3_013 (append .env variable): 1.00 / 1.00 / 1.00
- v3_014 (change YAML value): 1.00 / 1.00 / 1.00

Qwen3.6-27B handles config_edit tasks correctly **without any enrichment** (raw=1.00). This validates `disabled_domains: ["config_edit"]` in the Qwen3.6 supervisor profile.

Contrast: qwopus showed enriched=0.25 for config_edit (enrichment hurt), raw=0.50. Qwen3.6-27B is strictly better at config_edit than qwopus at every condition.

---

## Comparison to Prior qwopus Results

| Domain | qwopus enriched | Qwen3.6 enriched | qwopus raw | Qwen3.6 raw |
|--------|-----------------|-------------------|------------|-------------|
| investigation | ~0.75 (est) | 0.812 | ~0.75 (est) | 1.000 |
| analysis | — | 1.000 | — | 1.000 |
| config_edit | 0.25 | 1.000 | 0.50 | 1.000 |
| planning | — | 0.250 | — | 0.250 |

Qwen3.6-27B is generally stronger than qwopus on these tasks. Planning is the shared weak point.

---

## Implications for Supervisor Profile

Current Qwen3.6 profile settings are **validated**:
- `info_only_domains: ["investigation", "analysis", "philosophical", "planning"]` ✓
  - All four use info-only enrichment, which matches or exceeds enriched performance
- `disabled_domains: ["bugfix", "config_edit"]` ✓
  - config_edit raw=1.00, no enrichment needed at all
  - bugfix: not tested here but consistent with prior findings

**Recommendation:** Profile settings are correct. No changes needed based on this eval.

---

## Profile Written

Updated profile at: `eval_framework/profiles/jackrong_qwen3.6-27b.json`

— Kestrel
