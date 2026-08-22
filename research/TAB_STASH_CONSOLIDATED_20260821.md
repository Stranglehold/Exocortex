---
type: research
author: opus
date: 2026-08-21
subject: Consolidated research tab stash — 22 items, prioritized
supersedes: research/TAB_STASH_ASSESSMENT_20260703.md, research/tab_stash_additions_20260821.md
---

# Research Tab Stash — Consolidated Ledger
## As of August 21, 2026

---

## ACT NOW — Ready to build or test

### 1. SkillSpector (NVIDIA) — ADOPT (scoped)
**Status:** Assessed by Fable (Jul 3). Ready to integrate.
**What:** MCP server exposing `scan_skill() → {risk_score, severity, safe_to_install, findings}` with SARIF output. Drop-in deterministic gate for skill admission. Runs fully local.
**Critical catch:** High-recall agentic-risk surface detector, NOT malware detector (6.8% vs VirusTotal 72.8%). Fires on ~49% of all skills. Advisory feeding triage, never a hard block alone.
**Relevance now:** Phase B skill admission critics. SkillSpector is one of the three critics needed.

### 2. Autoresearch Loop (Karpathy pattern) — ADAPT
**Status:** Assessed by Fable (Jul 3). Highest-leverage item per Fable.
**What:** commit-before-verify / mechanical-metric / reset-on-fail boundary. Named mechanism for BP-04 B.
**Relevance now:** The cycle_commit / cycle_verify / cycle_keep_or_reset primitive drops into Phase B acceptor and Phase D dogfood.

### 3. Recirculation PoC (DeepMind, arXiv:2608.17981, Aug 18 2026) — TEST
**Status:** PoC written. Ready to run when VRAM is free.
**What:** Training-free. Leaks α=0.15 of deep-layer activation back to shallow layer. 23% perplexity reduction on Gemma3, 21% accuracy gain on GSM8k.
**PoC:** `recirc_poc.py` + `run_recirc_test.bat` in inference directory.

---

## EVALUATE — Promising, needs investigation or hardware

### 4. DFlash2 (Inco AI, arXiv:2602.06036, Aug 18 2026)
**What:** Block diffusion speculative decoding v2. 2.7–3.4× throughput on Qwen3.8-27B. Provably identical output.
**Blocker:** VRAM (drafter alongside target). llama.cpp PR #27342 not merged.
**Links:** https://inco.ai/blog/dflash2/ | https://huggingface.co/incoai/Qwen3.8-27B-DFlash2

### 5. vLLM Serving Stack (syv-ai/qwen38-27b-rtx3090) — EVALUATE
**What:** 114 tok/s single-user (3.3× our llama.cpp), 381 tok/s on document tasks, ~1,000 tok/s at 64 concurrent. Same card, same model.
**Key techniques:** INT8 tensor-core GEMMs, MTP drafts, calibrated int4 LM head, prefix caching (22.4s → 0.56s TTFT on repeated docs), DFlash2 + lookup drafting.
**Quality cost:** IFBench 78.3 vs 79.5 unquantized (1 point), GSM8K 96.5%.
**Links:** https://github.com/syv-ai/qwen38-27b-rtx3090

### 6. ninfer-3090 (Don-Chad) — EVALUATE
**What:** 98 tok/s with vision, MTP3, C1-C8 batching. Native Windows. ReplaySSM cuts spec-dec memory cost.
**Links:** https://github.com/Don-Chad/ninfer-3090

### 7. Shannon (AI pentester) — ADOPT (scoped)
**What:** Runtime security testing. SkillSpector at write-time, Shannon at runtime.
**Blocker:** Software factory Phase 2.

### 8. Understand-Anything (pattern only) — ADAPT
**What:** Recipe for knowledge graph extraction from wiki. Deterministic parse → LLM relationship discovery → entity/claim surfacing.
**Blocker:** Memory server v2 spec.

### 9. Ornith-1.5-35B vs Qwen3.8-27B Head-to-Head — TEST
**Key finding:** Qwen3.8 has native vision (mmproj now enabled). Ornith 35B is text-only. Dense vs MoE, multimodal vs text-only, LoRA-friendly vs LoRA-hard.
**Action:** BP-02 harness when ready.

### 10. LoRA / Squishy Weights Pipeline — DESIGN
**What:** Operational data → QLoRA (Unsloth) → GGUF → `--lora`. Separate adapters per task, hot-swappable.
**Blocker:** Phase B + model choice.

---

## WATCH — Track for changes

### 11. TurboVec — WATCH. No pain point named. Re-evaluate if vector search bottlenecks.
### 12. TwELL — WATCH. H100-only. No 3090 path.
### 13. Anthropic NLAs — WATCH. Model-specific, no Ornith NLA exists.
### 14. Geometry of Consolidation — WATCH/READ. Relevant to sleep consolidation convergence.
### 15. Qwen-AgentWorld — WATCH. World model for scenario sim. Gated behind BP-02.
### 16. llama.cpp PR #27342 — WATCH. DFlash2 support. If merged, becomes a bat file flag.
### 17. DGX Spark / next-gen hardware — WATCH. Current Spark getting 4 tok/s (slower than 3090). Don't buy end-of-cycle.

---

## SKIP

### 18. pi-llamacpp — SKIP. JIT swap contention. Reconsider on dual-GPU.
### 19. Kami — SKIP. UI convenience, no pipeline hook.
### 20. ponytail — ADAPT AS PHILOSOPHY. Code reduction principle. Nothing to install.

---

## SHIPPED (this session)

### 21. Asymmetric KV (tbq4_0 keys / q8_0 values) — SHIPPED
### 22. Vision via mmproj + CPU offload — SHIPPED
