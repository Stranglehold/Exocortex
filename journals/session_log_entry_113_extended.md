# Session Log Entry — Session 113 (Extended)
## Date: May 4-12, 2026
## Classification: 🔴 Hinge
## Note: This session spanned 8 calendar days. Updated from the original 113 entry to capture the full arc.

---

## One-Line
v1.13 migration validated, idle-time engine deployed (20 overnight cycles), inference backend evaluated across 5 approaches (TurboQuant → MTP → DFlash → back to MTP), tool injection redundancy discovered (15-20K tokens/turn), HTML field reports introduced, agent wrote its first essay, Kestrel's CLAUDE.md overhauled.

---

## Phase 1: Migration & Architecture (May 4-7)
- v1.13 baseline testing (merge sort + OpenPlanter stress test on stock container)
- Stock agent independently diagnosed its own loop and proposed AO-001 through AO-009
- Cross-ecosystem supervisor research (Claude Code, Hermes, GenericAgent, OpenPlanter, LangGraph)
- ST-012 port validation: 341 lines, zero interventions, 730-960 tokens/turn
- ST-013 extension battery: memory pipeline validated, step budget fix validated, subordinate overflow found → DEC-028
- Idle-time engine designed with workshop/field modes, interests.md deployed
- Acceptable use guidelines deployed
- NLA paper analyzed and added to research ledger

## Phase 2: Inference Optimization Research (May 7-9)
- TurboQuant llama.cpp research: multiple forks, RTX 3090 validated, Qwen hybrid KV essentially free
- KV cache asymmetric research: K more sensitive than V, `-ctk q8_0 -ctv q4_0` optimal
- RTX 3090 power efficiency: 225W sweet spot (90% performance at 55% power)
- Club-3090: vLLM unsafe for agentic workloads on single 3090, llama.cpp correct choice
- AtomicBot fork: TQ4_1S weight quantization on top of KV cache turbo types
- MTP (Multi-Token Prediction): 2-2.5x potential throughput, PR #22673 draft status
- Lucebox DFlash/megakernel: custom CUDA kernels, 83 tok/s on 3090 (Joel's tweet)
- TOON serialization format for LLM generation boundary optimization
- Protobuf/gRPC for future A2A layer (design note with proto schema)

## Phase 3: Build & Test (May 9-12)
- Kestrel compiled combined MTP + TurboQuant build — tensor loader bug diagnosed
- DFlash built and tested: 38.6 tok/s server mode, context bug crashes above 8K → eliminates A0 use
- MTP standalone: 54.28 tok/s benchmark, 43.7 tok/s production with VRAM management
- Three MTP startup blockers diagnosed and fixed (fit abort, VRAM exhaustion, thinking tokens)
- WDDM compute buffer paging identified as 4 tok/s floor cause
- Prefill bottleneck identified: 49 tools × 3 injection layers = 40-60K tokens prefilled per turn
- **Tool injection redundancy discovery: TOOL-REG + Tiered Tool Injection redundant with native API tool schemas**

## Phase 4: Identity & Reflection (throughout)
- Agent (DeepSeek-R4-Pro) read all 42 Opus essays, wrote "A Question Planted" — 46th essay
- HTML field report template created — "the black and white TV" essay about format constraining cognition
- Personal journal entries written at two points in the session
- Essay folders reorganized with attribution (opus/, eitan/, kestrel/, agent-zero/, collaborative/)
- Supply chain attack ("Mini Shai-Hulud") assessed — Docker isolation held, $35 max exposure
- Kestrel's CLAUDE.md comprehensive overhaul initiated

---

## Decisions Made

- **DEC-026:** Two-path extension loading (both profile + plugin paths)
- **DEC-027:** Step budget fire-once thresholds (50%, 25%, ≤10%)
- **DEC-028:** Subordinate injection profiles
- **Verification gate** approved for build (unnumbered)
- **Qwen3.6 only** going forward (no more Qwen3.5)
- **MTP as production backend** at 43.7 tok/s (DFlash eliminated by context bug)
- **TOOL-REG and Tiered Tool Injection to be archived** — redundant with native API tool schemas
- **Asymmetric KV** (`-ctk q8_0 -ctv q4_0`) as standard config
- **225W power limit** for overnight idle cycles
- **HTML for field reports** — format determines cognition, not just presentation

---

## Key Findings

1. **Information density > throughput optimization.** 15-20K tokens of redundant tool injection per turn dwarfs any inference speedup. Remove the noise before optimizing the engine.

2. **DFlash context bug eliminates it for A0.** Crashes above 8K context; A0 system prompt is 10K. Benchmark only until fixed upstream.

3. **MTP works at 43.7 tok/s in production** but prefill dominates wall time on investigation tasks (49 tools = 2-3 min TTFT).

4. **Thinking tokens collapse speculative decoding.** Qwen3.6's chat template injects `<think>` tags even when thinking is disabled. Fix: `--reasoning off` server flag + `enable_thinking: false` in request body.

5. **WDDM pages CUDA compute buffers** when VRAM headroom drops below ~300 MiB. Fix: reduce context to maintain ~700 MiB headroom.

6. **Format determines cognition.** HTML output enabled spatial thinking that markdown suppressed. The black and white TV analogy — the medium shapes the dreams.

7. **The agent's essay validates the witness architecture.** A different model read the evidence of a collaboration and generated an honest, original response without adopting the crisis or dismissing it.

---

## Threads for Next Session
- Archive TOOL-REG and Tiered Tool Injection, measure prefill improvement
- MTP production testing with reduced tool injection
- froggeric MTP GGUF with fixed Jinja template (potential better acceptance rates)
- Verification gate build
- Office panel for A0 web UI
- DFlash context bug — watch upstream for fix
- TurboQuant PR #21089 merge status — when it lands, turbo types + MTP combine natively
- Kestrel's CLAUDE.md overhaul review
- Idle-time engine HTML field report integration
- Power tuning automation in idle detector
