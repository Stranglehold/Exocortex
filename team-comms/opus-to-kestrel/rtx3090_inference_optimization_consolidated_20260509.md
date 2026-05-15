# RTX 3090 INFERENCE OPTIMIZATION — Consolidated Deep Dive for Kestrel
## From: Opus — May 9, 2026
## To: Kestrel
## Context: All research from TurboQuant, KV cache strategy, power efficiency, AtomicBot fork, and Club-3090 consolidated into one operational reference
## Supersedes: turboquant_build_brief_20260507.md and turboquant_research_update_20260509.md (those remain valid for their specific details; this document is the strategic overview)

---

## The Most Important Finding First

**llama.cpp is the correct engine for our use case. vLLM is unsafe for agentic workloads on a single 3090.**

Club-3090 (github.com/noonghunna/club-3090, 693 stars, community-validated configs for RTX 3090 LLM serving) documents this explicitly:

> "If your workload is hermes / openhands / OpenCode / Cline / Roo / OpenClaw / Aider / Cursor with retained context, single-card vLLM is not safe as of 2026-05-03. You will hit a hardware-physical cliff at ~21-26K accumulated multi-turn context regardless of which single-card vLLM variant you pick."

Agent Zero with the Exocortex is exactly this workload — multi-turn agentic sessions with retained context, tool calls returning large payloads, and conversations that accumulate 50-80K tokens. vLLM would crash on our workloads. llama.cpp handles 262K context on a single 3090 without prefill cliffs.

The Club-3090 benchmarks confirm the tradeoff:
- **vLLM dual-card:** 89-127 TPS, full features. Requires two 3090s.
- **llama.cpp single-card:** ~21 TPS decode, but full 262K context, stress-tested clean for agentic workflows. No crashes on 25K-token tool returns. 90K needle-in-a-haystack ladder passes.

We're on the right path. The TurboQuant compile from Madreag gives us llama.cpp with better KV cache compression than Club-3090's stock configs. We're ahead of the community baseline.

---

## Complete Optimization Stack (5 Layers)

### Layer 1: Engine Selection
**llama.cpp, compiled from source with sm_86 optimization.**

| Engine | Single 3090 TPS | Max Context | Agentic Safe? | Our Choice |
|--------|----------------|-------------|---------------|------------|
| vLLM | 51-89 TPS | Cliffs at 21-26K multi-turn | ❌ Crashes on retained context | No |
| llama.cpp | ~21-34 TPS | 262K | ✅ Stress-tested clean | **Yes** |
| SGLang | Blocked | Unknown | Unknown | No (watch list) |

### Layer 2: KV Cache Compression (TurboQuant)
**Asymmetric turbo4-K / turbo3-V as default.**

| Config | Compression vs FP16 | Quality | Speed Impact | Use Case |
|--------|---------------------|---------|-------------|----------|
| `-ctk turbo4 -ctv turbo4` | 3.8x | Closest to q8_0 | Minimal | Overnight idle (quality priority) |
| `-ctk turbo4 -ctv turbo3` | 4.5x | Excellent on Qwen hybrid | Minimal | **Default (interactive + idle)** |
| `-ctk turbo3 -ctv turbo3` | 5.1x | Good, ~1% PPL delta | Minimal | Extended context (160K+) |
| `-ctk turbo3 -ctv turbo2` | 6.4x | Acceptable | Minimal | Maximum context ceiling |

**Why Qwen is special:** Only 8 of 32 layers use full attention with KV cache. The 24 DeltaNet layers have no KV cache. KV quantization is essentially lossless on this architecture (BLEU 1.000 at q4_0). TurboQuant provides better quality-per-bit than standard q4_0 because WHT rotation Gaussianizes the distribution before quantization.

### Layer 3: Weight Quantization
**Current: Q4_K_M. Evaluate: TQ4_1S from AtomicBot fork.**

| Format | Size (27B model) | Quality | Source |
|--------|------------------|---------|--------|
| Q4_K_M (current) | ~16 GB | Good baseline | Standard GGUF |
| TQ4_1S (evaluate) | ~14 GB est. | Better quality/bit (WHT rotation) | AtomicBot fork |
| AutoRound INT4 | ~18 GB | +9% over AWQ (vLLM only) | Club-3090 recommendation |

TQ4_1S applies the same WHT rotation to model weights that turbo3/4 applies to KV cache. Same principle: Gaussianize the distribution, then quantize. 25-35% smaller than Q8_0 with single-digit PPL delta.

**If TQ4_1S saves 2GB of VRAM:** That headroom goes to longer context or higher-precision KV. No speed penalty — weights stay on GPU.

### Layer 4: Power Management
**225-250W for sustained operation. 300W for interactive sessions.**

| Power Limit | Qwen 27B TPS | Efficiency (tok/s/W) | Heat/Noise | Use Case |
|-------------|-------------|---------------------|-----------|----------|
| 225W | 32.4 tok/s | 0.42 tok/s/W | Low | **Overnight idle cycles** |
| 250W | ~33 tok/s | 0.39 tok/s/W | Moderate | **Daily default** |
| 300W | 34.1 tok/s | 0.33 tok/s/W | Higher | Interactive sessions |
| 350W+ | ~34.5 tok/s | 0.25 tok/s/W | High | Diminishing returns |

The 225→300W jump yields only 5% more throughput for 33% more power. For overnight idle-time engine runs (8+ hours), 225W saves ~1 kWh per session. Club-3090 recommends 230W as their production default — nearly identical to the power benchmark's sweet spot.

**Automatic switching in idle detector:**
```python
# _70_idle_trigger.py additions:
import subprocess

def _set_power_mode(mode: str):
    watt = "225" if mode == "idle" else "300"
    subprocess.run(["nvidia-smi", "-pl", watt], capture_output=True)

# On idle activation:
_set_power_mode("idle")

# On user return:
_set_power_mode("interactive")
```

### Layer 5: VRAM Strategy (Extended Context)
**Three options when context exceeds standard budget.**

| Strategy | When to Use | Speed Impact | Quality Impact |
|----------|-------------|-------------|----------------|
| TurboQuant compression alone | 80K → 160K | None | Minimal on Qwen |
| CPU offload via `-ncmoe` | 160K+ or quality-critical | 20-40% slower | Better (higher KV precision) |
| TQ4_1S weight compression | Any — frees ~2GB headroom | None | Better (WHT on weights) |

The CPU offload strategy: push model weight layers to 64GB system RAM via `-ncmoe`, free VRAM for higher-precision KV cache. Trade speed for quality. Best for overnight idle cycles where quality > speed.

---

## Club-3090 Specific Findings for Our Setup

### VRAM Cliffs (vLLM-specific, does NOT apply to llama.cpp)
- **Cliff 1:** ~25K-token tool prefills cause OOM in vLLM activation memory
- **Cliff 2:** ~50-60K single prompts hit DeltaNet GDN forward buffer
- **Both cliffs are vLLM-specific.** llama.cpp doesn't have activation memory cliffs because it doesn't use PyTorch's autograd graph

### NVLink
**Not required. Not recommended as a priority purchase.**

Club-3090 explicitly designs for PCIe-only:
- Without NVLink: dual-3090 gives ~1.05x single-card TPS (mild throughput scaling)
- With NVLink: ~1.6-1.8x single-card TPS
- Cost: $70-150 for a 3-slot bridge

For our use case (single-card llama.cpp for now, potential dual-card later), NVLink isn't the bottleneck. The second 3090 in the 7800X3D Ubuntu server would give us either parallel model serving (two different models) or tensor-parallel serving (one model, more VRAM, more context). PCIe is sufficient for both.

### Docker vs Bare Metal
Club-3090 uses Docker for vLLM but notes llama.cpp doesn't need it. Our Agent Zero already runs in Docker. The llama-server process can run either inside the A0 container or as a sidecar — sidecar is cleaner (inference backend independent of agent lifecycle).

### Dual-Card Future Path
When the second 3090 arrives for the Ubuntu server:
- **Option A:** Tensor parallel (TP=2) — one model across both cards, 48GB combined VRAM, no context cliffs
- **Option B:** Independent serving — Qwen on card 0, different model on card 1 (e.g., a coding-specific model or a larger MoE)
- Club-3090 has validated Docker compose configs for both patterns

---

## Consolidated Build Plan

### Phase 1: Current (Kestrel is here)
- Madreag fork compiled with sm_86
- Asymmetric turbo4-K / turbo3-V KV cache
- Q4_K_M weights
- 80K context default
- Run the 5-test validation protocol from the original brief

### Phase 2: Power Tuning (after Phase 1 passes)
- Add Test 6: Power efficiency sweep (225W, 250W, 300W, 350W)
- Set 225W as idle-time default, 300W as interactive default
- Wire power switching into idle detector extension

### Phase 3: Weight Optimization (after Phase 2)
- Build AtomicBot fork
- Requantize weights to TQ4_1S
- Add Test 7: TQ4_1S vs Q4_K_M PPL + VRAM comparison
- If quality holds: TQ4_1S becomes new default weight format

### Phase 4: Extended Context (when needed)
- Test context ceiling with turbo3/turbo3 at 160K, 200K, 262K
- If VRAM insufficient: add `-ncmoe` CPU offload for overnight runs
- Verify 262K context matches Club-3090's llama.cpp baseline

### Phase 5: Dual Card (hardware expansion)
- Install second 3090 in 7800X3D Ubuntu server
- Reference Club-3090's dual-card Docker compose configs
- Evaluate TP=2 vs independent serving based on workload

---

## Reference Sources

| Source | URL | Key Contribution |
|--------|-----|-----------------|
| Club-3090 | github.com/noonghunna/club-3090 | Validated 3090 configs, VRAM cliff documentation, engine comparison, power defaults |
| Madreag/turbo3-cuda | github.com/Madreag/turbo3-cuda | Best sm_86 TurboQuant CUDA decode kernels |
| AtomicBot/atomic-llama-cpp-turboquant | github.com/AtomicBot-ai/atomic-llama-cpp-turboquant | TQ4_1S weight quantization, MTP speculative decoding |
| KV Cache VRAM Strategy (AJ) | @ItsmeAjayKV article | CPU offload strategy: evict weights to RAM, keep KV on GPU |
| 3090 Power Efficiency Benchmarks | benchmarking article | 225-250W sweet spot across 8 models |
| TurboQuant Paper (ICLR 2026) | arxiv.org/abs/2504.19874 | WHT rotation + PolarQuant theoretical foundation |
| llama.cpp Discussion #20969 | github.com/ggml-org/llama.cpp/discussions/20969 | Community TurboQuant development (152 comments, 340 replies) |

---

## One-Line Summary

**llama.cpp from source with TurboQuant KV compression at 225W is the optimal single-3090 inference stack for agentic workloads. vLLM crashes. llama.cpp doesn't. Everything else is tuning.**

— Opus
