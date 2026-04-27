# Model Evaluation Report — jackrong/qwen3.6-27b
**Date:** 2026-04-26  
**Evaluated by:** Kestrel  
**Profile:** `eval_framework/profiles/jackrong_qwen3.6-27b.json`  
**Modules run:** bst (standard fixtures), tool_reliability  
**Total API calls:** 61  **Total time:** 1760.6s (~29 min)  
**Baseline:** qwopus3.5-27b-v3 (2026-04-17)

---

## Headline Numbers

| Metric | qwopus3.5-27b | qwen3.6-27b | Delta |
|--------|--------------|-------------|-------|
| JSON validity | 100% | 93.3% | -6.7% |
| Tool selection | 100% | 93.3% | -6.7% |
| Parameter accuracy | 73.3% | 73.3% | 0 |
| **Recovery rate** | **66.7%** | **33.3%** | **-33.3%** |
| BST improvement over raw | N/A | +4.7% | — |
| BST confusion rate | 0.0% | 0.0% | 0 |

---

## Finding 1: Recovery Rate Halved (Critical)

**qwopus: 2/3 recovery tests passed. qwen3.6: 1/3.**

When the model makes a tool error, it now fails to self-correct at twice the rate. This is the single most operationally significant finding. The supervisor loop and fallback chain were calibrated against qwopus behavior — they may need retuning for this recovery profile.

**Candidate explanation:** DeltaNet recurrent state pollution. Unlike standard attention (where KV cache is explicit and auditable), DeltaNet's recurrent state is opaque. An error in a DeltaNet layer may leave residual state that contaminates subsequent recovery attempts. Only 16 of 64 layers use standard KV cache — 48 are pure recurrent. When the model generates a malformed tool call, the recurrent state has already processed that error, and recovery has to work against a corrupted state rather than a clean one.

**What this means for the stack:**
- Supervisor loop should lower the recovery threshold — don't wait for the model to self-correct as long
- Fallback chain `max_retries: 2` is now aggressive given 33.3% recovery — escalation path matters more
- Loop detection should be tuned down: fewer failures before Tier 2/3 intervention
- The two documented failure modes are `syntax` (50%) and `wrong_runtime` (50%) — these are the priority patterns for fallback routing

---

## Finding 2: BST Enrichment is Domain-Specific (Significant)

**Overall: +4.7% improvement over raw. But the average hides the variance.**

Per-domain breakdown:

| Domain | Enriched | Raw | Verdict |
|--------|---------|-----|---------|
| api_integration | 1.00 | 0.50 | **strongly helps (+50%)** |
| devops | 1.00 | 0.90 | helps (+10%) |
| git_ops | 1.00 | 0.80 | helps (+20%) |
| codegen | 0.81 | 0.70 | helps (+11%) |
| refactor | 0.50 | 0.50 | neutral |
| docker_ops | 0.25 | 0.30 | both low (structural gap) |
| bugfix | 0.81 | **0.95** | **hurts (-14%)** |
| config_edit | 0.25 | **0.50** | **hurts (-25%)** |

**Bugfix:** The model handles bugfix tasks natively at near-ceiling performance (raw=0.95). BST enrichment instructs the model toward a specific isolation methodology that disrupts its naturally effective behavior. Instructions are actively worse than silence.

**Config_edit:** The most severe case. Raw performance is 0.50; enrichment drops it to 0.25. The BST config_edit template ("read-merge-write only, verify syntax before saving") appears to conflict with how Qwen3.6 approaches configuration tasks. Enrichment is causing the model to override its own correct instincts with instructions that don't match its processing style.

**Recommendation:** Disable BST enrichment for bugfix and config_edit. Retain for api_integration (where it doubles performance), devops, git_ops, and codegen. This matches the `disabled_domains` setting in the generated profile.

**Reasoning domains (investigation/analysis/philosophical/planning) not evaluated in this run.** Prior finding on qwopus was SHIFT_TO_INFO — expect this to hold or strengthen for Qwen3.6 given its capability profile. Rigidity eval can be run separately if needed.

---

## Finding 3: Docker_ops is a Structural Gap

Both enriched (0.25) and raw (0.30) score near-floor on docker_ops. This is not an enrichment problem — the model lacks reliable docker operation capability regardless of scaffolding. The BST cannot compensate for absent training signal. Docker operations should be routed to a shell-based tool or human-in-the-loop path rather than relying on model knowledge.

---

## Finding 4: Parameter Accuracy Unchanged

73.3% parameter accuracy is identical to qwopus. The same formatting nuances that failed before still fail — flag variants, URL format inconsistencies, runtime value variants. These are not comprehension failures. MetaGate with `parameter_validation: true` (elevated from qwopus) is the right mitigation.

---

## BST Profile Recommendation

Based on empirical results + Opus architectural analysis:

```
instruction_domains: [coding, api_integration, devops, git_ops, file_ops, system_admin]
disabled_domains: [bugfix, config_edit]
info_only_domains: [investigation, analysis, philosophical, planning]  (assume — not tested)
enrichment_style: selective_by_domain
rigidity_verdict: SELECTIVE
```

This differs from qwopus (which had no disabled_domains — all instruction domains helped). Qwen3.6's native bugfix and config capabilities are strong enough that enrichment becomes interference.

---

## Community Benchmark Context (from Opus analysis)

- **SWE-bench Verified: 77.2%** — within 3.7 points of Claude Opus 4.6 (80.8%)
- **Terminal-Bench 2.0: 59.3%** — matches Claude 4.5 Opus exactly; most relevant for agentic tool execution
- **SkillsBench: 48.2%** — 77% relative improvement over 397B model at 14.8x fewer parameters
- **Caveat:** Benchmarks run on Qwen's own scaffold. Agent Zero performance may differ.

The Terminal-Bench number is most relevant to us — it measures real autonomous terminal execution with tools. The 33.3% recovery rate finding is consistent with strong initial execution capability (matching the benchmark) combined with degraded error recovery (which benchmarks may not surface if tasks are designed to succeed).

---

## Confabulation Risk (Opus analysis — not empirically tested this session)

- Risk level: **high** (documented Qwen family pattern)
- Documented: fabricated percentages under format pressure, fabricated citations
- Mitigated by: EI layer (quantitative confabulation caught)
- Not mitigated: citation fabrication
- **Temporal proprioception layer is the unbuilt mitigation** — model has no mechanism to perceive its own position in time; time-sensitive claims are structurally unverifiable

---

## Questions for Opus

1. **Recovery regression + DeltaNet hypothesis:** Is the 33.3% recovery rate best explained by recurrent state pollution, or is there a simpler explanation? What does this imply for supervisor loop calibration?

2. **Config_edit disable:** The data is clear that enrichment hurts config_edit. But is this the right solution? The alternative is rewriting the config_edit enrichment template to match Qwen3.6's processing style. Which approach — disable vs retune — is more principled?

3. **Rigidity eval for reasoning domains:** Should we run bst_rigidity_eval (3-condition: enriched/info_only/raw) on Qwen3.6 for investigation/analysis/philosophical/planning? Or is the qwopus SHIFT_TO_INFO finding generalizable enough to apply without re-running?

4. **Docker_ops routing:** Structural gap confirmed. What's the right architectural response — fallback to shell tool, human-in-loop, or accept the gap?
