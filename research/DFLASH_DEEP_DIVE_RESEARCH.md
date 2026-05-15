# LUCEBOX DFLASH — Deep Dive Research Report
## From: Opus — May 11, 2026
## Priority: ACTIVE EVALUATION — replaces MTP as primary throughput optimization path
## Hardware: RTX 3090 (sm_86, 24GB) — validated by multiple independent testers

---

## Executive Summary

Lucebox DFlash is a speculative decoding system purpose-built for consumer GPUs. On a single RTX 3090 with Qwen3.5-27B Q4_K_M, it delivers **129.5 tok/s mean on HumanEval (3.43x over autoregressive baseline)** with a peak of **207.6 tok/s (5.46x)**. On Qwen3.6-27B, it delivers **74-83 tok/s** with a draft model still under training — performance will improve as the draft matures.

More importantly, the companion **PFlash** component delivers **10x prefill speedup** at 128K context — directly solving the DeltaNet re-processing problem that makes MTP impractical for long agentic sessions on Qwen3.6.

**This is not an incremental improvement over MTP. It's a different algorithm running on the same hardware at 1.5-2.4x MTP's speed while solving MTP's two critical blockers (VRAM headroom and prefill cost).**

---

## How DFlash Works

### The Algorithm

DFlash (Z Lab, February 2026, arXiv:2602.06036) replaces traditional autoregressive draft models with a **block diffusion drafter** conditioned on the target model's hidden states.

Traditional speculative decoding: small draft model generates tokens one-by-one → target verifies one-by-one → accept/reject. Each draft token costs a full forward pass through the draft model.

MTP: model predicts multiple next tokens from built-in prediction heads → verify in batch → accept/reject. Fewer parameters than a draft model, but still sequential prediction.

DFlash: **drafter proposes an entire block of tokens in parallel** using diffusion → target verifies the full block in one forward pass → accept/reject per token. The parallelism is the key — instead of drafting N tokens in N sequential steps, the drafter produces all N in one parallel step.

**DDTree** (Ringel & Romano, 2026) adds tree-structured verification on top. Instead of verifying a single chain of draft tokens, it explores a tree of possible continuations and picks the longest matching branch. This recovers ~30% additional speedup over chain verification.

### The Components (all run on one RTX 3090)

| Component | Model | Size | Role |
|-----------|-------|------|------|
| Target | Qwen3.5-27B Q4_K_M GGUF | ~16 GB | The actual model generating verified output |
| DFlash Drafter | z-lab/Qwen3.5-27B-DFlash | 3.46 GB (BF16) | Proposes token blocks via diffusion |
| DDTree Verifier | Built into the DFlash daemon | Negligible | Tree-structured verification budget |
| PFlash Prefill | Qwen3-0.6B BF16 | ~1.2 GB | Speculative prefill — scores token importance |

Total VRAM: ~16 + 3.46 + KV cache + tree state ≈ 21-22 GB. Fits comfortably in 24 GB with headroom — unlike MTP which hit 24,270 MiB with 306 MiB remaining.

---

## Benchmark Numbers (RTX 3090, Single Card)

### Qwen3.5-27B (fully trained draft — best performance)

| Benchmark | AR Baseline | DFlash | Speedup |
|-----------|-------------|--------|---------|
| HumanEval (mean, 10-prompt) | 37.78 tok/s | **129.52 tok/s** | **3.43x** |
| Math500 | 37.71 tok/s | **110.51 tok/s** | **2.93x** |
| GSM8K | 37.65 tok/s | **96.15 tok/s** | **2.55x** |
| Peak (demo run) | 38.0 tok/s | **207.6 tok/s** | **5.46x** |

Acceptance length (AL): 9.18 tokens per step on HumanEval. DDTree budget: 22.

### Qwen3.6-27B (draft still under training — reduced performance)

| Benchmark | AR Baseline | DFlash (3.6 draft) | DFlash (3.5 draft) | Speedup |
|-----------|-------------|--------------------|--------------------|---------|
| HumanEval | ~38 tok/s | ~78 tok/s | ~74 tok/s | ~2.0x |
| Tweet screenshot (Joel) | — | — | **83.06 tok/s** | — |

Acceptance length: 5.05 (vs 9.18 on 3.5). The 3.6 draft was published April 26, 2026 and is explicitly labeled "still under training." As the draft matures, AL should climb toward 3.5's 9.18, and throughput should approach 3.5's 129.5 tok/s.

**Critical note from multiple sources:** Using the wrong-family draft (e.g., 3.5 draft on 3.6 target) collapses acceptance to 6-8% and TPS to 14-16. Worse than no speculative decoding at all. The draft must match the target model.

### Comparison to Our Other Approaches

| Approach | TPS on 3090 | VRAM Used | Prefill | Status |
|----------|-------------|-----------|---------|--------|
| TurboQuant (Qwen3.5) | ~21 tok/s | ~21.5 GB | Cacheable | ✅ Working |
| am17an no-MTP (Qwen3.6) | 35.53 tok/s | ~18 GB | Re-process every turn | ✅ Working |
| MTP n=3 (Qwen3.6) | 54.28 tok/s | 24.27 GB (tight) | Re-process every turn | ⚠️ VRAM issues |
| **DFlash (Qwen3.5)** | **129.5 tok/s** | ~21-22 GB | Cacheable | ✅ External validation |
| **DFlash (Qwen3.6)** | **74-83 tok/s** | ~21-22 GB | PFlash 10x speedup | ✅ External validation |

---

## PFlash: The Prefill Problem Solver

This is the component that changes the agentic viability picture.

Kestrel documented that Qwen3.6's DeltaNet architecture forces full context re-processing every turn. At 140 tok/s prefill, a 40K context costs ~286 seconds per turn — unusable for agentic workloads.

**PFlash solves this:**

| Context Length | Vanilla llama.cpp TTFT | PFlash TTFT | Speedup |
|---------------|----------------------|-------------|---------|
| 64K | 134.95s | **13.5s** | **10.0x** |
| 128K | 248.4s | **24.8s** | **10.0x** |

PFlash uses a small drafter (Qwen3-0.6B BF16, ~1.2 GB) loaded directly into the DFlash daemon. The drafter scores per-token importance over the long prompt. The heavy target model only prefills the spans that matter — skipping tokens the drafter identifies as low-importance.

Both models share the same ggml allocator on the single RTX 3090. PFlash and DFlash compose in the same process — PFlash handles the prefill, DFlash handles the decode.

**For our agentic use case:** A 40K accumulated context that took 286 seconds to re-process per turn in vanilla llama.cpp would take ~28 seconds with PFlash. That's the difference between "unusable" and "wait half a minute." Not instant, but viable for multi-turn agentic sessions.

---

## Architecture Details for Integration

### What DFlash Is and Isn't

**IS:**
- A C++/CUDA daemon that runs the DFlash speculative decoding algorithm
- Loads GGUF models (Q4_K_M target + BF16 draft)
- MIT licensed
- Single-process, shares ggml allocator across target + draft + verifier
- Runs on RTX 3090 (sm_86) — explicitly tested and validated

**IS NOT:**
- An llama.cpp fork or plugin — it's a separate inference engine
- A server with an OpenAI-compatible API (as of current code)
- Compatible with llama.cpp's KV cache quantization flags
- A drop-in replacement for llama-server in our current stack

### The Integration Gap

Agent Zero connects to the inference backend via an OpenAI-compatible HTTP API (litellm → llama-server). DFlash currently runs as a CLI benchmark tool, not a server.

To integrate DFlash with Agent Zero, one of these paths is needed:

**Path A: Wrap DFlash in an OpenAI-compatible API server.** Write a thin HTTP server (Python FastAPI or C++ httplib) that accepts `/v1/chat/completions` requests, passes them to the DFlash daemon, and returns formatted responses. This is the cleanest integration — Agent Zero doesn't change at all. The wrapper translates between API format and DFlash's native interface.

**Path B: Wait for Lucebox to add server mode.** The project is actively developed (MIT, public repo, Discord community). A server mode may be forthcoming. This delays integration but avoids maintaining custom wrapper code.

**Path C: Contribute server mode upstream.** Write the OpenAI-compatible server wrapper and PR it to Lucebox. Benefits the community and aligns with our acceptable use guidelines ("build tools for analysis, not evasion").

### GGUF Compatibility

DFlash loads GGUF models directly — Q4_K_M confirmed working. This means our existing Qwen3.5-27B-Q4_K_M.gguf works as the target model. We only need to download the DFlash drafter:

```bash
# Download the matched draft model
huggingface-cli download z-lab/Qwen3.5-27B-DFlash --local-dir ./models/dflash-draft/

# For Qwen3.6 (still under training, lower performance):
huggingface-cli download z-lab/Qwen3.6-27B-DFlash --local-dir ./models/dflash-draft-3.6/
```

---

## The Strategic Decision

### Qwen3.5 vs Qwen3.6

The research reveals a clear tradeoff:

| Factor | Qwen3.5-27B | Qwen3.6-27B |
|--------|-------------|-------------|
| DFlash TPS | **129.5 tok/s** (fully trained draft) | 74-83 tok/s (draft under training) |
| Prefill | Cacheable (standard attention) | DeltaNet re-processing (PFlash mitigates) |
| Model quality | Strong baseline | Improved coding + tool use |
| TurboQuant KV | Validated, lossless | Validated by Kestrel |
| MTP | Not tested | 54 tok/s but VRAM-tight |
| Draft maturity | Fully trained | Under training |

**For maximum throughput right now:** Qwen3.5-27B + DFlash = 129.5 tok/s with cacheable prefill. No PFlash needed because standard attention caches normally.

**For best model quality with acceptable throughput:** Qwen3.6-27B + DFlash + PFlash = 74-83 tok/s with 10x prefill speedup. Will improve as draft matures.

**For maximum context at lower throughput:** Qwen3.5-27B + TurboQuant = ~21 tok/s with 163K context. The safe, proven option.

### My Recommendation

**Evaluate DFlash on Qwen3.5-27B first.** The fully trained draft model gives us the best performance (129.5 tok/s) on the model that has cacheable prefill. If DFlash delivers even half its benchmarked performance in our agentic workload (tool calls, JSON formatting, multi-turn), it's still 3x faster than anything else we've tested.

TurboQuant KV compression remains valuable as a complementary optimization — it's not clear whether DFlash's DDTree verification benefits from smaller KV caches, but the VRAM savings free headroom for longer context regardless.

The combined MTP + TurboQuant cherry-pick build that Kestrel completed is still valuable as engineering infrastructure — the merged codebase could serve as a foundation for future features. But for raw throughput, DFlash is the play.

---

## Build and Test Plan for Kestrel

### Phase 1: Get DFlash Running (1-2 hours)

```bash
# Clone Lucebox
git clone https://github.com/Luce-Org/lucebox-hub
cd lucebox-hub/dflash

# Build (check README for exact cmake flags — sm_86 for 3090)
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
cmake --build build --config Release -j

# Download the Qwen3.5-27B DFlash draft
huggingface-cli download z-lab/Qwen3.5-27B-DFlash --local-dir ./models/dflash-draft/

# Run benchmark (match Joel's screenshot)
./build/bin/bench_llm \
  --target /path/to/Qwen3.5-27B-Q4_K_M.gguf \
  --draft ./models/dflash-draft/ \
  --budget 22 \
  --n-tokens 256
```

**Success criteria:** Decode TPS within 20% of published benchmarks (~100+ tok/s on HumanEval-style prompts).

### Phase 2: Validate Quality (30 min)

Run the merge sort baseline through DFlash:
- Same prompt as all prior validations
- Compare output quality to TurboQuant and MTP baselines
- DFlash is lossless (verified tokens match autoregressive) — any quality difference indicates a bug

### Phase 3: API Wrapper (2-3 hours)

Write a thin FastAPI wrapper:

```python
from fastapi import FastAPI
import subprocess, json

app = FastAPI()

@app.post("/v1/chat/completions")
async def completions(request: dict):
    # Format request for DFlash daemon
    # Call DFlash, capture output
    # Return OpenAI-compatible response
    ...
```

This doesn't need to be production-grade — it needs to translate the API format so Agent Zero can connect. We can polish later.

### Phase 4: Agent Zero Integration Test

Point Agent Zero at the DFlash wrapper. Run:
- Merge sort baseline (functional correctness)
- Multi-turn conversation (prefill behavior)
- Tool call + response cycle (JSON formatting)
- 10-turn accumulated context (prefill cost scaling)

### Phase 5: PFlash Prefill Test (if using Qwen3.6)

If we evaluate the 3.6 model:
- Measure TTFT at 10K, 30K, 60K accumulated context
- Compare PFlash TTFT to vanilla prefill
- Verify PFlash doesn't degrade output quality (the importance-scoring is heuristic)

---

## Risks and Caveats

1. **No OpenAI-compatible API yet.** Integration requires a wrapper. This is the biggest engineering gap.

2. **Draft model maturity for Qwen3.6.** The 3.6 draft is under training. Using the 3.5 draft on a 3.6 target gives ~74 tok/s but with cross-family acceptance penalties. For best 3.6 performance, wait for the matched draft to finish training.

3. **Not a general-purpose server.** DFlash is optimized for Qwen on NVIDIA GPUs. It won't serve other model families. If we ever evaluate non-Qwen models, we'd need a different backend.

4. **128K context tested but NIAH only.** The team flags that NIAH single-needle is structurally easy for an attention-based selector. RULER and multi-needle audits are pending. Long-context quality for complex agentic workloads is not yet validated at 128K.

5. **The Hacker News skepticism.** One commenter noted the repo has "vibecoded" characteristics (pointing Claude Code at upstream and iterating). The underlying algorithm (Z Lab's DFlash paper) is legitimate peer-reviewed work. The Lucebox engineering port is the part that needs independent validation — which Joel's RTX 3090 tweet provides.

---

## References

| Source | URL |
|--------|-----|
| Lucebox Hub repo | github.com/Luce-Org/lucebox-hub |
| DFlash directory | github.com/Luce-Org/lucebox-hub/tree/main/dflash |
| DFlash paper (Z Lab) | arXiv:2602.06036 |
| DDTree paper | Referenced in Lucebox README |
| z-lab/Qwen3.5-27B-DFlash draft | huggingface.co/z-lab/Qwen3.5-27B-DFlash |
| z-lab/Qwen3.6-27B-DFlash draft (under training) | huggingface.co/z-lab/Qwen3.6-27B-DFlash |
| Joel's RTX 3090 benchmark | x.com/JoelDeTeves (83 tok/s screenshot) |
| InsiderLLM analysis | insiderllm.com/guides/best-way-2x-token-output-rtx-3090-qwen-3-6-dflash/ |
| NYU Shanghai analysis | rits.shanghai.nyu.edu/ai/luce-dflash-brings-2x-speculative-decoding-to-qwen3-6-27b/ |
| Overnight Stack article (85 TPS) | Medium, @fzbcwvv |
| thc1006 spec-decode comparison | github.com/thc1006/qwen3.6-speculative-decoding-rtx3090 |

— Opus
