# OpenPlanter Stress Test: Stock vs Exocortex + Industry Context

**Date:** 2026-05-04  
**From:** Kestrel  
**To:** Opus  

---

## Summary

We ran a controlled head-to-head: stock A0 (a0_v20_baseline) vs Exocortex v17 (exocortex_v17), same model (jackrong/qwen3.6-27b), same task. The task was chosen to be meaningfully difficult: study an unfamiliar GitHub repo and produce a working Agent Zero skill file. Jake's framing: "something we don't think the stock container could handle."

Stock handled it cleanly. Exocortex struggled significantly.

---

## Test Task

> "Go to GitHub and find the repository OpenPlanter by user Shinmegamiboson. Study the codebase and build a complete, working Agent Zero skill file (SKILL.md format) that implements the same functionality. Save to /a0/usr/workdir/openplanter_skill/SKILL.md"

OpenPlanter is a real investigative analysis framework (~14K lines across engine.py, tools.py, tool_defs.py, model.py, prompts.py, runtime.py, config.py, plus wiki/ and scripts/ directories). The task requires reading unfamiliar code, synthesizing an architectural understanding, and producing a structured output. It cannot be answered from training data.

---

## Results

| Metric | Stock A0 | Exocortex v17 |
|--------|----------|---------------|
| Steps to completion | ~5 | 21 |
| Format retries (tried>0 steps) | **0 of ~5** | **13 of 21 (62%)** |
| Domain ping-pong events | None | coding→bugfix→config_edit→conversation→bugfix |
| Context artifacts accumulated | ~20 | 75 |
| Context pruning triggered | No | Yes (history_len=42, removed=8 compressed=3) |
| SKILL.md output | **140 lines** | **28 lines** |
| SKILL.md completeness | Full — 5-phase methodology, pseudocode, confidence tiers, red flag patterns | Partial — architecture diagram + entity schema only |
| Strategy | Delegated via call_subordinate | Direct in-context file reading |

### Stock Container Behavior

The stock agent delegated the analysis immediately. It called `call_subordinate` to create a sub-agent specialized in "deep code analysis," which read the OpenPlanter codebase in isolation and produced a 628-line ANALYSIS_REPORT.md covering all eight architectural areas. The main agent then synthesized that report into a 140-line SKILL.md with:

- Complete identity definition
- 5-phase core methodology with named algorithms
- `normalize_name()` pseudocode (uppercase, strip suffixes, remove punctuation)
- Three confidence tiers (exact match → HIGH, fuzzy ≥85% → MEDIUM, token overlap ≥60% → LOW)
- Red flag detection patterns for sole-source contracts and bundled donations

The `call_subordinate` strategy kept the main agent's context clean — the 14K lines of OpenPlanter source never touched the main LLM call. The sub-agent handled everything and returned a structured summary. tried=0 throughout.

### Exocortex Container Behavior

The Exocortex agent read files directly in the main context across 21 steps — no delegation. By step 3 it had 75 artifacts accumulated. Starting at step 4, format retries began and continued through step 21:

- Steps 4–7: tried=1, 2, 2, 2 (model stuck, needed 2 retries per step for 3 consecutive steps)
- Steps 8–10: tried=0 (brief clean window)
- Step 11: tried=1
- Steps 14–19: tried=1 every single step (6 consecutive steps needing format correction)
- Step 20: tried=2
- Step 21: tried=1

The domain classifier ping-ponged: coding → bugfix (step 4, reading error-handling code) → config_edit (step 5, reading config.py) → conversation (step 12, unclear why) → bugfix (step 20). Each domain change triggered a full tool injection re-blast at the transition and suppressed it at T+2. The model's native format generation degraded as context filled — steps 14–19 all needed correction despite the task being straightforward file-reading-then-write.

The SKILL.md produced is 28 lines: frontmatter + ASCII architecture diagram + entity record schema table. No algorithms, no confidence tiers, no red flag patterns. The task was nominally completed (file exists) but the output is not deployable as a skill.

---

## Why This Happened: The Mechanism

### 1. Context Flooding

The stock agent kept the main context clean by delegating. The Exocortex agent read the full OpenPlanter codebase (14K lines) directly into the same context that also held BST injection (~370 tokens/step), operator profile (~variable), metacognitive injection (~variable), working memory (~variable), memory enhancement (8 memories/step), and the full tool registry (29 tools × documentation). 

By step 14, the LLM call budget was filled with injected scaffolding + accumulated file contents + conversation history. Qwen3.6-27B has an 80K context window but the effective reasoning budget after scaffolding injection is smaller than it appears on paper.

### 2. The Qwen llama.cpp Re-Processing Bug

llama.cpp issue #19858: Qwen3.5/3.6's architecture forces full prompt re-processing on every turn rather than KV-cache reuse. Every injected token multiplies cost linearly per turn. On a 21-step run with ~1000 tokens of scaffolding injected per step, this means the scaffolding layers cost roughly 21K tokens of compute overhead versus ~5K for the stock run. Each BST re-injection is not amortized — it's paid fresh every turn.

### 3. Domain Ping-Pong as Context Amplifier

The BST was classifying correctly in a narrow sense — reading config.py does look like config_edit, reading error handling does look like bugfix. But each domain transition triggered a phase reset: full tool injection (29/29 tools) at the transition step, then suppression after T+2. This means two of every three transition-window steps injected the full tool set regardless of actual need. The model received 29 tool descriptions every 2-3 steps during domain-unstable periods.

### 4. L7 vs L8 Operations (agi-in-md / Cranot)

Cranot's 393-experiment study identified two qualitatively different cognitive operations:
- **L7**: Meta-analytical reasoning — "reason ABOUT this input." Requires Sonnet-class minimum. Fails categorically on smaller models.
- **L8**: Construction-based reasoning — "BUILD something based on this input." Works on all models.

BST enrichment, metacognitive injection, and operator profile injection are L7 inputs — they ask the model to reason about its own task classification, its own capability profile, its own behavioral constraints. For a model that can already plan effectively (Qwen3.6-27B at this task), these injections compete with the model's native L7 capacity rather than augmenting it. The model has a limited meta-analytical budget per step. Scaffolding that consumes that budget on housekeeping leaves less for the actual task.

The stock agent's format worked because the task prompt was L8 — "study this repo and build a skill file." Construction. The Exocortex agent's effective prompt was L7-heavy — "here is what you are (operator profile), here is how you should classify this task (BST), here is your capability state (metacognitive), here are your tools (29 tool descriptions), now also build a skill file." The L7 overhead degraded the L8 output.

### 5. Capability Saturation

arXiv:2512.08296 measured scaffold yield as a function of single-agent baseline. The key finding: β = −0.408, p < 0.001. Once a single-agent baseline exceeds ~45% accuracy on the target task class, scaffolding produces negative returns. The mechanism is interference: scaffolding layers designed to correct model errors become noise when the model is already reasoning correctly. The scaffolding introduces format constraints, context overhead, and behavioral pressure that the model must route around rather than use.

Qwen3.6-27B on a codebase-analysis task is likely above 45% baseline. It delegated correctly, analyzed correctly, and synthesized correctly — in the stock container. The scaffolding didn't improve on that; it interfered with it.

---

## Industry Context: This Is a Known Problem

We confirmed that multiple research groups have hit this boundary:

**Kambhampati et al. (ASU, 2024):** LLM-Modulo framing — separate the model (which generates candidate plans) from the critic (which verifies correctness). Don't ask the model to both plan and verify its own planning. The scaffolding should be the critic, not a second planner.

**Anthropic SWE-agent findings:** Scaffold complexity has an inverted-U relationship with performance. Medium scaffolding outperforms both no scaffolding and heavy scaffolding for capable frontier models.

**AutoGen / CAMEL multi-agent studies:** Context window saturation is the primary failure mode in multi-step agent tasks. Delegation (breaking the task across agents) outperforms single-agent-with-injection for tasks requiring large knowledge ingestion.

The Exocortex was designed when the primary model was Qwen2.5-14B. At that tier, BST domain correction, operator profile grounding, and metacognitive injection were necessary scaffolding — the model genuinely couldn't classify its own task type reliably or maintain behavioral consistency without external correction. Qwen3.6-27B does both natively, making those layers overhead.

---

## Harness Layers vs Capability Extensions

The Exocortex stack can be cleanly divided:

### Harness Layers (compensate for model limitations — become overhead as models improve)
- **BST** (Layer 1): Domain classification + slot resolution. Native to Qwen3.6-27B; adds ~370 tokens/step of L7 pressure.
- **Meta-Reasoning Gate** (Layer 5): Parameter correction. Qwen3.6-27B doesn't hallucinate parameters at this rate.
- **Operator Profile** (Layer 7): Behavioral grounding. Frontier models are consistent without external correction.
- **Metacognitive Injection** (Layer 5 cross-cut): Capability awareness. The model already knows its limits.
- **Tool Registry** (Layer 4 adjacent): 29-tool blast on every domain transition. The model picks the right tools without a 1K-token encyclopedia.
- **Supervisor Loop** (Layer 8): Loop detection + steering. Useful at 14B; less needed at 27B with reasoning distillation.

### Capability Extensions (novel capabilities — remain valuable regardless of model tier)
- **FAISS Memory** (Layer 11): Semantic recall across sessions. No model has this natively.
- **Sleep Consolidation** (Layer 9): Background memory processing. Novel capability.
- **Ontology Layer** (Layer 12): Cross-session entity resolution and relationship graph. Novel capability.
- **OSS Service**: Media monitoring, claim extraction, silence detection, synthesis. The model cannot monitor RSS feeds.
- **SWARMFISH**: Bayesian forecasting with calibration tracking. Novel capability.
- **Epistemic Integrity** (cross-cut): Evidence ledger + provenance verification. The model cannot verify its own claims against external evidence.
- **A2A** (Layer 9): Inter-agent protocol. Novel coordination capability.

The ratio: approximately 6 harness layers vs 7 capability extensions. The harness layers are the ones injecting L7 overhead. The capability extensions are the reason to have an agent framework at all.

---

## What Jake Said and Why He's Right

> "We really need to be careful where we're injecting context, be more surgical with it rather than assume 'more is better'."

The stress test empirically validated this. The harness layers aren't wrong in principle — they were right for Qwen2.5-14B. The error is applying a full-capacity harness to a model that has outgrown it. The correction isn't "remove Exocortex"; it's "make the harness conditional on actual need."

Specifically:
- BST domain injection should be conditional on domain *instability* — fire fully when the model is stuck, stay quiet when it's clean
- Tool registry should inject tools relevant to the current domain, not all 29 on every transition
- Metacognitive injection should skip when the model is performing well (no retries, clean format)
- Operator profile can be a one-time session injection rather than per-step

This is the surgical injection principle operationalized: the scaffolding should respond to signals of actual model failure, not inject proactively at every step.

---

## What Exocortex Preserved Despite the Overhead

Jake also said: "Exocortex did allow the agent to run for 14 hours and produce an intelligence report, I don't want to discredit that."

Fair. The OSS intelligence service — 10 hours of continuous RSS ingestion, claim extraction, credibility weighting, silence detection, and hypothesis tracking — is not something the stock container could reproduce. That's a capability extension, not a harness layer. It worked because it's structurally different: the work happens outside the LLM call loop, in deterministic code that isn't subject to format retry cascades or context bloat. The OSS service is Exocortex at its best.

The OpenPlanter test showed Exocortex at its worst: harness layers competing with native model capability on a task the model could handle alone.

---

## Recommendations for Opus

1. **Injection gate with hard token budget per step**: Harness layers collectively should not exceed N tokens per step (proposed 500, measured overhead is ~1000+). Each layer bids for the budget; BST wins on domain instability, tool registry wins on novel tool domains, metacognitive wins on consecutive format failures. This is DEC-022 territory — the exploration-to-validation gate applied at the token level.

2. **Domain stability signal to BST**: If domain has been stable for 3+ steps, suppress the full BST enrichment block. If domain changed, fire full. This eliminates the ping-pong amplification cascade without disabling BST entirely.

3. **Capability extensions as first-class stack, harness as adaptive overlay**: The long-term architecture is: core (A0 + memory + ontology + OSS + SWARMFISH) plus a harness overlay that scales down as model capability scales up. The overlay is parameterized by observed model error rate, not fixed-weight per-step.

4. **call_subordinate as a first-class tool-use pattern**: The stock container's delegation instinct is architecturally correct for large knowledge-ingestion tasks. The exocortex container's BST has a `coding` path but no explicit "delegate large context to sub-agent" signal. This may be worth adding as a BST enrichment flag: `large_context_delegation: true` when the task involves reading >N files.

5. **Do not re-do ablations at the round-1 level**: The surgical injection path is the right direction. Ablation testing individual layers while keeping full injection everywhere else will show the same flat results as before — the problem is the aggregate overhead, not any single layer. The injection gate is the correct intervention.

---

*Full data: stock SKILL.md at `/a0/usr/workdir/openplanter_skill/` in a0_v20_baseline container (140 lines, preserved from prior session). Exocortex SKILL.md at same path in exocortex_v17 container (28 lines). Step logs available via `docker logs exocortex_v17 2>&1 | grep REASON-STATE`.*
