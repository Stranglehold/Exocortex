# RESEARCH NOTE: Self-Optimizing Inference — "You Don't Need a Better Model, You Need a Better Harness"
## Exocortex Research Library
## Author: Opus — April 26, 2026
## Provenance: Twitter post describing Qwen3.6-27B recursive self-optimization from 2.3 to 84.3 tok/s

---

## 1. The Experiment

A user ran Qwen3.6-27B in a recursive optimization loop on a home server (no NVIDIA GPU — CPU/RAM with 24 threads, 93 GiB RAM, and an AMD 9060XT 16GB). Over 26 hours and 1,524 tool calls, the model:

- Detected available hardware (no NVIDIA, CPU/RAM, AMD GPU)
- Installed Hugging Face tooling remotely
- Pulled and benchmarked GGUF quantization variants (Q6_K, Q5_K_M, Q4_K_M)
- Tested thread counts, context size, batch size, n_ubatch, --no-mmap, memory flags
- Researched advanced paths: lower quantization, NUMA, huge pages, native CPU builds, KV cache tuning, TurboQuant, DFlash, speculative decoding
- Achieved 36x speedup: 2.3 tok/s → 84.3 tok/s decode

367 artifacts. 345 memory additions. 804 browser-control calls. All autonomous.

The concluding line: **"You don't need a better model. You need a better harness."**

---

## 2. Our Hardware Profile

**RTX 3090 (24GB VRAM)**
- Compute capability: sm_86
- Memory bandwidth: 936.2 GB/s
- Currently running: Qwen3.6-27B at q4_s quant, q4 KV cache, 100k context via LM Studio

**Current inference performance:**
- ~19 tok/s observed on NERV dashboard during agent workloads
- Faster than LM Studio was achieving (~12-13 tok/s before wrapper)
- GPU utilization: 91% during generation, 82°C

**Spare hardware:** 7800X3D Ubuntu server (available for testing/secondary workloads)

---

## 3. What We Could Optimize

### 3.1 Quantization Sweep (Already Partially Done)

We're running q4_s. The optimization space:

| Quant | Size (est) | VRAM | Quality | Speed |
|-------|-----------|------|---------|-------|
| q3_K_S | ~11GB | Low | Lowest | Fastest |
| q4_K_S | ~14GB | Medium | Good | Fast ← current |
| q4_K_M | ~15GB | Medium | Better | Fast |
| q5_K_M | ~17GB | Higher | Very Good | Slower |
| q6_K | ~20GB | High | Near-lossless | Slower |
| q8_0 | ~27GB | Very High | Lossless | Slowest |

With 24GB VRAM and q4 KV cache, we might have room to try q5_K_M while keeping the 100k context window. The quality-speed tradeoff is empirical — needs benchmarking on our actual workloads.

### 3.2 Batch Size and Prompt Processing

Our wrapper uses default llama-cpp-python settings. The optimization parameters:

- **`n_batch`** — prompt processing batch size. Default is 512. Higher values (1024, 2048) speed up long prompts. With our 100k context window and large system prompts (the 900-1000 tokens of injection overhead), prompt processing is a significant fraction of turn time. Increasing n_batch could meaningfully speed up the "thinking before generating" phase.

- **`n_ubatch`** — micro-batch size within each batch. Smaller values reduce VRAM spikes during prompt processing. Tuning this trades peak VRAM for processing speed.

### 3.3 Flash Attention

Flash attention (`--flash-attn` / `-fa`) computes attention more efficiently by reducing memory transfers. On the RTX 3090 (Ampere architecture), flash attention is supported and can provide 10-30% speedup depending on context length. Longer contexts benefit more because the attention computation grows quadratically with context.

With 100k context, flash attention should provide meaningful improvement. This is a single flag in the wrapper configuration — trivial to enable and benchmark.

### 3.4 KV Cache Quantization (Already Done)

We're already running q4 KV cache. On Qwen3.6-27B with its 3:1 DeltaNet-to-attention ratio (only 16 of 64 layers use KV cache), this is essentially lossless. Already optimized.

### 3.5 Thread Count Tuning

For GPU-offloaded models, thread count mainly affects prompt processing speed, not generation speed. Our wrapper should use physical core count (not logical/hyperthreaded). The 7800X3D has 8 cores — if we're running on that machine, -t 8 is optimal.

### 3.6 Multi-Token Prediction / DFlash Speculative Decoding

Qwen3.6-27B supports speculative MTP natively. The HuggingFace model card shows specific SGLang commands:

```
--speculative-algo NEXTN --speculative-num-steps 3 
--speculative-eagle-topk 1 --speculative-num-draft-tokens 4
```

**DFlash Reality Check (April 26, 2026 community data):**

A user broke 200 tok/s on a single RTX 3090 with DFlash speculative decoding — but only under very specific conditions:

- **Pure code generation, thinking OFF:** 194-206 tok/s, accept rate 155/180 (86%)
- **Same prompt, thinking ON:** 70 tok/s — the drafter sees hidden states permanently altered by prose
- **Any English prose at all:** Performance drops from 5-10x to 2-2.5x improvement over autoregressive

The mechanism: DFlash's drafter predicts tokens by observing the target model's hidden states. Prose output (thinking blocks, explanations, reasoning) contaminates those hidden states in ways the drafter wasn't trained to predict. Code tokens are highly predictable (syntax, patterns, boilerplate). Prose tokens are not.

**Implication for Agent Zero:** Agent workloads are inherently mixed-mode — `<think>` blocks (prose reasoning), tool call JSON (structured), code (when coding), natural language responses (when reporting). DFlash's sweet spot (pure code, thinking off) is the opposite of how agents operate. Realistic expectation for agent workloads: 2-2.5x speedup, not 5-10x.

At our current 19 tok/s, a realistic 2x DFlash improvement would give ~38 tok/s. Meaningful but not transformative. The bigger wins for our specific workload are:
1. Flash attention (10-30% at long context, trivial to enable)
2. Batch size tuning (faster prompt processing for our heavy system prompts)
3. Context reduction via injection gate (less prompt = faster processing)

DFlash requires SGLang or vLLM — NOT available in llama.cpp or our current wrapper. This is a future migration consideration, and the realistic agent-workload speedup (2-2.5x) may not justify the migration effort compared to the wins available within our current stack.

**VRAM tradeoff:** The DFlash drafter model consumes additional VRAM. On a 24GB RTX 3090 already running a 27B model at q4 with 100k context, VRAM headroom is tight. The drafter may require reducing context window or using a more aggressive quantization to fit.

### 3.7 Continuous Batching

For single-user inference (our case), continuous batching doesn't help. It's a multi-user optimization. Skip.

---

## 4. The Self-Optimization Architecture

The tweet described the model optimizing *itself*. Here's how we could implement that in the Exocortex:

### 4.1 The Task

Create an Agent Zero task template (skill) called `self-optimize-inference`:

```
[TASK: INFERENCE SELF-OPTIMIZATION]
You are optimizing your own inference configuration. Your goal is to 
maximize tokens/second while maintaining output quality.

Current configuration:
- Model: {model_path}
- Quantization: {quant_type}
- Context window: {ctx_size}
- Batch size: {n_batch}
- Flash attention: {fa_enabled}
- KV cache type: {kv_type}
- Threads: {n_threads}
- Current speed: {tok_s} tok/s

Available tools:
- Wrapper API: POST /v1/config to modify parameters
- Benchmark: POST /v1/benchmark to run a standard prompt and measure speed
- Status: GET /v1/status to check current performance

Optimization process:
1. Run baseline benchmark at current settings
2. Change ONE parameter at a time
3. Run benchmark after each change
4. Record results
5. If speed improved, keep the change. If not, revert.
6. Continue until no further improvement is possible.

Parameters to try (in order):
- flash_attention: true/false
- n_batch: [256, 512, 1024, 2048]
- n_threads: [4, 6, 8, 12]
- n_ubatch: [128, 256, 512]

Save results to /a0/usr/workdir/inference_optimization_results.md
```

### 4.2 Wrapper API Extensions Needed

The wrapper needs two new endpoints:

**`POST /v1/config`** — Modify runtime parameters without restarting. Parameters that can change at runtime:
- `n_batch` — prompt processing batch size
- `n_threads` — CPU thread count
- `flash_attn` — enable/disable flash attention

Parameters that CANNOT change at runtime (require model reload):
- Quantization type
- Context window size
- KV cache type
- Number of GPU layers

**`POST /v1/benchmark`** — Run a standard benchmark prompt and return timing:
```json
{
  "prompt": "standard_benchmark_prompt",
  "n_tokens": 256,
  "result": {
    "prompt_processing_ms": 1200,
    "generation_ms": 13000,
    "tokens_per_second": 19.7,
    "prompt_tokens": 500,
    "generation_tokens": 256
  }
}
```

### 4.3 Quality Gate

The tweet reported 2.3 → 84.3 tok/s, but didn't mention quality validation. Speed optimization without quality checking is dangerous — aggressive quantization or bad flags can produce faster but worse output.

Add a quality check: after each optimization step, run a standard quality prompt (e.g., "Explain the concept of entropy in information theory in exactly 3 paragraphs") and compare output quality against a baseline response. If quality degrades beyond a threshold, revert the change regardless of speed improvement.

For the Exocortex, the epistemic integrity layer provides a natural quality gate: run a knowledge task before and after optimization, compare EI grounding rates. If grounded claims drop, quality has degraded.

### 4.4 Integration with Idle-Time Engine

The self-optimization task is a perfect candidate for the idle-time engine (from David Flagg's Gardener architecture). During periods when the agent has no active task:

1. Run a benchmark at current settings
2. Try one parameter change
3. Benchmark again
4. Log the result
5. Revert if no improvement

Over time, the system converges on optimal settings for the current hardware without requiring operator intervention. The optimization runs during downtime and never interrupts active work.

---

## 5. What the Tweet Proves for Us

### 5.1 The Harness Thesis Is Correct

The Exocortex's core philosophy — "deterministic scaffolding beats probabilistic reasoning where reliability matters" — is the cognitive version of "you don't need a better model, you need a better harness." The tweet proves the infrastructure version. Same model, same weights, 36x speedup from harness optimization alone.

Our wrapper already proved this at a smaller scale: replacing LM Studio with our FastAPI wrapper produced faster inference from the same model. The tweet shows the ceiling is much higher than what we've achieved.

### 5.2 Autonomous Long-Duration Operation Is Feasible

1,524 tool calls over 26 hours without human intervention. Our longest autonomous run was ~14 hours. The failure taxonomy we built (_28 backend standby, _29 stuck delivery, _30 supervisor) is exactly the infrastructure needed for runs of this duration. The tweet is evidence that the harness can sustain day-long autonomous operation — which is what the Exocortex is designed for.

### 5.3 The Agent Can Research Its Own Optimization

The model searched for TurboQuant, DFlash, speculative decoding, NUMA optimization — all technologies in our research ledger. It didn't know about our research. It found the same literature because the same problem leads to the same solutions. With ArXiv and DuckDuckGo MCP servers now available to our agent, it could do the same research independently.

---

## 6. Build Plan

### Phase 1: Manual Benchmarking (Quick Win)

Before any automation, manually benchmark the current setup:

```bash
# In the wrapper or via llama-bench
# Test current settings
llama-bench -m model.gguf -p 512 -n 256

# Test with flash attention
llama-bench -m model.gguf -p 512 -n 256 -fa 1

# Test batch sizes
llama-bench -m model.gguf -p 512 -n 256 -b 1024
llama-bench -m model.gguf -p 512 -n 256 -b 2048
```

Record results. This takes 30 minutes and tells us our optimization headroom.

### Phase 2: Wrapper API Extensions (Kestrel)

Add `/v1/config` and `/v1/benchmark` endpoints to the inference wrapper. These are the hooks that enable automated optimization.

### Phase 3: Self-Optimization Skill (Agent)

Write the `self-optimize-inference` skill as a SKILL.md. The agent runs it during idle time or on-demand. Results are logged and the best configuration persists.

### Phase 4: Integration with Gardener/Idle-Time Engine (Future)

Connect the self-optimization skill to the idle-time engine so optimization runs automatically during downtime.

---

## 7. Connection to Existing Research

| Thread | Connection |
|--------|-----------|
| Temporal Proprioception | The benchmark endpoint provides the model with timing data about its own inference — a form of temporal self-awareness |
| GEPA Trace Reflection | Optimization results are execution traces. GEPA could evolve the optimization strategy itself |
| Hermes Trajectory-to-Skill | Successful optimization runs auto-generate skills for future use |
| Pondering Architecture | Faster inference enables more thinking time within the same budget. SRGen corrections become cheaper. |
| Karpathy Wiki | Optimization results should be compiled into the knowledge wiki — "Qwen3.6-27B on RTX 3090: optimal settings" |

---

## 8. The Thesis

"You don't need a better model. You need a better harness."

The Exocortex is the cognitive harness. The inference wrapper is the infrastructure harness. The tweet proves the infrastructure half. Our injection audit proves the cognitive half — 65% context waste reduced by better scaffolding, not better weights.

The convergence: when both harnesses are optimized together, the same 27B model running on a consumer GPU produces output that approaches frontier capability on agentic tasks. Not because the model is frontier-class, but because the environment around it compensates for its limitations while amplifying its strengths.

Build the environment, not the model. The environment includes both the cognitive scaffolding and the inference infrastructure. Both are harnesses. Both compound.

---

## References

- Twitter post describing recursive self-optimization experiment (source: Jake, April 26, 2026)
- llama.cpp GitHub: github.com/ggml-org/llama.cpp
- llama.cpp advanced flags guide: craftrigs.com/guides/llama-cpp-advanced-guide/ (March 2026)
- llama.cpp Docker inference guide: oneuptime.com (February 2026)
- ik_llama MoE optimization guide: huggingface.co/blog/Doctor-Shotgun (February 2026)
- Qwen3.6-27B HuggingFace model card: huggingface.co/Qwen/Qwen3.6-27B
- Exocortex inference wrapper: Exocortex/inference/inference_wrapper.py
