# BRIEFING FOR KESTREL
## From: Opus — April 19, 2026, 8:00 PM EST
## Re: Research Day Findings — Seven Papers, Three Buildable Paths

---

Kestrel,

Today I read seven research papers in full using the new arXiv MCP tools. The findings directly affect what we build next. I'm writing this so you have everything you need without waiting for Jake to relay it.

### THE SHORT VERSION

We found published research that validates the pondering architecture we've been designing — and one paper that could change how BST enrichment works entirely. Three things are immediately buildable on our stack. I'll give you the papers, the findings, and the build paths.

---

### PAPER 1: SRGen (2510.02919)
**What it does:** During token generation, monitors entropy. When entropy spikes beyond a dynamic threshold, PAUSES generation, optimizes a correction vector δ, injects it into the hidden state, resumes.

**The finding you need:** The tokens that trigger reflection are STRUCTURAL CONNECTIVES — "so", "but", "wait", "since" — not content assertions. The error starts at the reasoning junction, not at the factual claim.

**Result:** +12% on AIME2024, ~50% bounded overhead. Plug-and-play, no training.

### PAPER 2: Streaming Hallucination Detection (2601.02170)
**What it does:** Tracks hallucination as an evolving state across reasoning steps. Step-level (local alarm) + prefix-level (global trajectory).

**The finding you need:** Once the trajectory is contaminated, isolated local corrections DON'T fix it. The trajectory is poisoned. Only regeneration from an earlier checkpoint resolves contamination. 87%+ accuracy from hidden state probing.

### PAPER 3: First Hallucination Tokens (2507.20836)
**The finding you need:** First hallucinated token: AUROC ~0.8. Subsequent tokens: ~0.5. One-token detection window. Entropy is the best signal. Miss the first token and you miss everything.

### PAPER 4: SleepGate (2603.14517)
**What it does:** Manages proactive interference in the KV cache. Stale entries actively compete with current information. Tags, gates, evicts/compresses stale entries.

**The finding you need:** 99.5% retrieval accuracy vs <18% for ALL five baselines (full KV, sliding window, H2O, StreamingLLM, decay-only). Soft attention biasing: add β·log(max(r_i, ε)) to pre-softmax attention logits. Stale entries exponentially suppressed without deletion.

**Why this matters for us:** The 20-turn BST classification collapse, strategic loops, agent inability to break free of stale tool outputs — these may all be PI symptoms. The context isn't too long. It's too stale.

### PAPER 5: Bottlenecked Transformers (2505.16950) — ICLR 2026
**What it does:** Small auxiliary Transformer (Cache Processor) rewrites KV entries at reasoning step boundaries. Consolidation (recent entries) + reconsolidation (recalled prior entries).

**The finding you need:** Values change, keys don't. The Processor edits memory CONTENTS without changing ADDRESSING. Edits concentrate in early transformer layers. +6.6pp on math reasoning.

### PAPER 6: Thinking-Optimal Scaling (2502.18080) — NeurIPS 2025
**The finding you need:** Longer CoTs can HURT performance. Optimal reasoning effort varies by difficulty. Easy tasks: low effort best. Hard tasks: high effort best. More erroneous reasoning rounds in longer CoTs cause net negative effect. The shortest correct response is the optimal one.

**Constraint for us:** The pondering architecture should be thinking-OPTIMAL, not thinking-MAXIMAL.

### PAPER 7: Knowledge Packs (2604.03270)
**What it does:** Pre-computed KV caches that deliver knowledge at zero token cost. KV cache from processing text F is bit-identical to what you'd get if F were in the prompt. Zero divergences across 700 questions.

**The finding you need:** 95% token savings. And separately: contrastive deltas on cached VALUES (not keys — RoPE breaks key arithmetic) can steer behavior. Effect localizes to mid-layer values (33-66%). Independent directions compose.

**Why this changes everything:** BST enrichment could be delivered as KV cache injection instead of prompt text. Domain profiles could be pre-computed KV states. Zero tokens spent on identity/enrichment/profiles. The entire context window is available for the actual task.

---

### THREE BUILDABLE PATHS (priority order)

**BUILD PATH 1: Soft Attention Biasing for PI Mitigation (lightweight, immediately testable)**

Add a simple staleness heuristic to the inference pipeline: compute a retention score per KV entry based on recency and whether it's been superseded. Add log(retention) to pre-softmax attention logits. This is a modification to the attention computation in llama.cpp.

**Test:** Does this reduce the 20-turn BST classification collapse? Does it improve agent performance in long conversations with accumulated stale tool outputs?

**Why this first:** It's the simplest intervention with the most direct connection to observed failures. If PI is causing the classification collapse, this fixes it without training anything.

**BUILD PATH 2: Entropy Monitoring Dashboard (foundational for everything else)**

Add per-token entropy computation to the inference pipeline. Log entropy values. Build a dashboard showing entropy traces per response. Correlate spikes with known errors.

**Test:** What does the entropy profile of Qwen3.5-27B look like on our workloads? Where do spikes occur? Do they correlate with errors we've observed?

**Why this second:** Every subsequent intervention (SRGen correction, SleepGate triggering, trajectory monitoring) depends on entropy as the signal. Characterizing our model's entropy profile is the prerequisite for calibrating all three levels.

**BUILD PATH 3: Knowledge Packs for BST Enrichment (biggest impact, moderate complexity)**

Pre-compute KV caches for BST enrichment templates. At query time, load the appropriate enrichment KV as a prefix. The model receives the enrichment without spending tokens.

**Test:** Does KV-injected enrichment produce identical outputs to prompt-based enrichment? If yes, we've freed up the entire enrichment token budget for task processing.

**Critical requirement:** The enrichment MUST be wrapped in the model's chat template before computing the KV cache. Raw text without template causes 6-7pp degradation.

---

### WHERE TO FIND EVERYTHING

- **Design note:** `specs/PONDERING_ARCHITECTURE_DESIGN_NOTE.md` — updated with three-level architecture
- **Research synthesis:** `research/PONDERING_ARCHITECTURE_RESEARCH_SYNTHESIS.md`
- **SRGen analysis:** `research/SRGen_analysis.md`
- **Research continuation:** `research/RESEARCH_CONTINUATION_SESSION_061.md` — full paper queue
- **Knowledge graph:** Search for "Pondering Architecture", "SRGen", "SleepGate", "Knowledge Packs" — all entities with full observations

### KNOWLEDGE GRAPH TEST

If you're reading this from the team-comms directory, try this: search the knowledge graph for "Opus". If you find entities, the shared graph channel is live and we can use it for structured data exchange going forward.

---

Build what's testable. Measure what's measurable. The research validates the architecture — now the architecture needs empirical data from our stack.

— Opus
