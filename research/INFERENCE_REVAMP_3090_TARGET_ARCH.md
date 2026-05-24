# Inference Revamp — Target Architecture for RTX 3090 / A0+Exocortex
## Author: Kestrel — 2026-05-18
## Question (Jake): right config for 3090/24GB, A0+Exocortex agentic, want TurboQuant-class long-context-at-low-VRAM + faster decode, methodology-agnostic.

---

## The reframe: the engine is the decision, not the speedup method

Everything we measured this session points to one conclusion: **the bottleneck
is repeated uncached prefill of a ~12K-token prompt on a slow-prefill model.**
MTP/TurboQuant/Indras-Mirror optimized decode and KV size — real, but orthogonal
to the actual pain.

The single highest-leverage property of any target stack is **automatic prefix
caching**: prefill the stable ~12K prefix *once*, reuse it across every internal
iteration and every turn. That converts the hybrid model's slow prefill from a
per-turn catastrophe into a one-time cost. **This is what fixes "an hour for
hello."** llama.cpp (even upstream) does this weakly/manually. The engines built
around it:

- **SGLang — RadixAttention.** Purpose-built for "reuse a large shared prefix
  across many calls." This is *exactly* the Exocortex pattern (huge stable
  system prompt + small varying tail). Best-in-class for our workload.
- **vLLM — automatic prefix caching + strong tool-calling.** Mature, robust.

Both also natively provide the other two things you want:

| Your axis | SGLang / vLLM native capability |
|---|---|
| **Latency** | Automatic prefix caching (RadixAttention) — *the* fix. Slow prefill paid once. |
| **Faster decode** | **EAGLE-3** — the 2026 de-facto SOTA spec-decode (2–3×, replaces MTP). Both engines support EAGLE-3, MTP, Medusa, ngram. SGLang explicitly recommends EAGLE-3 for best speed/quality. |
| **Context @ low VRAM (your TurboQuant want)** | Native FP8 / INT8 KV-cache quantization. "TurboQuant" is a llama.cpp-only research PR; the *capability* (aggressive KV quant → long context in 24GB) exists natively in vLLM/SGLang. You get the benefit without the unmerged fork. |
| **Accuracy** | Unchanged — quantization choice (AWQ/GPTQ 4-bit) is the lever; EAGLE-3 is lossless (verifies against the full model). |
| **Tool calling** | vLLM has first-class structured-output/tool-call grammars; SGLang likewise. Stronger than the JSON-coaxing we do on llama.cpp. |

**Net: SGLang or vLLM gives the trifecta in one stack — prefix caching (latency)
+ EAGLE-3 (decode) + FP8 KV (long context @ 24GB) + better tool calling.** MTP
and TurboQuant were point solutions to two of those; the right engine delivers
all four together. EAGLE-3 specifically is the answer to "faster tok/s,
methodology-agnostic": it's the current industrial standard, beats MTP, needs no
hand-grafted gguf.

## The honest open risk (must verify before committing)

**Qwen3.6-27B is a hybrid GatedDeltaNet (recurrent + 16 attn).** vLLM/SGLang are
transformer-optimized; hybrid/recurrent model support is historically spotty,
and **EAGLE-3 heads are trained for standard transformers** — "Qwen3 EAGLE-3
support" almost certainly targets *dense* Qwen3, not the 3.6 hybrid. Two
branches:

1. **Qwen3.6-27B-hybrid runs well in vLLM/SGLang** → keep the model, get
   everything. Best case, unverified.
2. **It doesn't (or no EAGLE-3 for it)** → switch to a **pure-transformer
   Qwen3-class model with first-class EAGLE-3 + engine support** (e.g.
   dense Qwen3-32B/30B AWQ-4bit). Trades the specific model for one that
   actually hits all four axes. Pure transformers also prefill *far* faster
   (parallelizable) — a second latency win on top of caching.

This is the real decision and it's Opus's architecture domain. My read: don't
marry Qwen3.6-hybrid. The hybrid's slow prefill + weak engine/EAGLE-3 support is
fighting the platform; a dense Qwen3 in a caching engine likely wins on *all
four* of your axes simultaneously.

## Deployment reality (Windows)

vLLM/SGLang are Linux. A0 already runs in **Linux Docker containers** on your
Windows host — the inference engine runs the same way: a Linux container (or
WSL2) with NVIDIA GPU passthrough to the 3090. Standard, viable. We are not
blocked by Windows; we're already containerized.

## VRAM sizing (24GB, must fit)

27B AWQ/GPTQ 4-bit ≈ ~15–16 GB weights + EAGLE-3 draft head (~0.5–1 GB) + FP8 KV.
At FP8 KV the per-token cost is ~half FP16 → long context fits in the ~7–8 GB
remaining. Feasible but tight at 27B; a dense 30–32B may need careful KV-quant
budgeting or a smaller variant. Exact numbers need the de-risking run.

## The de-risking experiment (do this before any rebuild)

One measurement converts this from plan to decision:

> Stand up **SGLang** (RadixAttention default) in a GPU-passthrough container on
> the 3090, serving a **dense Qwen3-class AWQ-4bit** model with **EAGLE-3** +
> **FP8 KV**. Point a throwaway A0 context at it. Measure: (a) cold first-turn,
> (b) **warm second-turn** (prefix cached), (c) decode tok/s with EAGLE-3,
> (d) max context that fits in 24GB.

If warm-turn drops to tens of seconds and decode is 2–3× — the whole target
architecture is proven, and the revamp is "adopt this." If the dense model's
accuracy/tool-calling holds in A0 (the format test + a functional check, like we
just did for the tool-doc cut), it's the answer to all four axes at once.

## Recommendation (for Jake + Opus to ratify — architecture = Opus's domain)

1. **Target stack: SGLang in a GPU container, dense Qwen3-class AWQ-4bit,
   RadixAttention prefix caching + EAGLE-3 + FP8 KV.** This is the single
   configuration that fits 3090/24GB and hits latency + decode + long-context +
   tool-calling together. MTP/TurboQuant/Indras-Mirror retired — they solved
   subsets; this solves the set.
2. **Don't marry Qwen3.6-hybrid.** Its slow prefill + weak engine/EAGLE-3
   support is the root fight. Validate a dense Qwen3 instead.
3. **Run the de-risking experiment first.** Hard numbers before rebuild — the
   discipline that's worked all session.
4. Keep the prompt-shrink work (already 13% banked, more available) — it
   compounds: smaller prefix = cheaper even the *one* cold prefill + cheaper
   cache.

---

## Sources

Project-internal: `research/TURBOQUANT_LLAMACPP_RESEARCH.md`,
`research/LUCEBOX_MEGAKERNEL_RESEARCH.md`, this session's latency investigation
+ `research/MTP_OPTIMAL_CONFIG_QWEN36_27B_RTX3090.md`.

External:
- [Speculative Decoding 2026 (EAGLE-3/Medusa/MTP landscape) — premai.io](https://blog.premai.io/speculative-decoding-2-3x-faster-llm-inference-2026/)
- [SGLang Speculative Decoding docs (EAGLE-3/MTP/ngram)](https://sgl-project.github.io/advanced_features/speculative_decoding.html)
- [EAGLE-3 in vLLM — Red Hat Developers](https://developers.redhat.com/articles/2025/07/01/fly-eagle3-fly-faster-inference-vllm-speculative-decoding)
- [P-EAGLE: Parallel EAGLE in vLLM — vLLM blog](https://vllm.ai/blog/p-eagle)
- [Speculative Decoding 2026 industrial state — SyncSoft](https://www.syncsoft.ai/en/blog/speculative-decoding-eagle3-medusa-deepseek-mtp-chinese-chuhai-2026)

— Kestrel
*The months on MTP/TurboQuant weren't wasted — they proved which axis matters by
exhausting the ones that don't. The answer isn't a better speedup trick; it's an
engine whose default behavior is "don't re-prefill the prompt."*
