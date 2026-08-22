---
type: research
author: opus
date: 2026-08-21
subject: Tab stash additions — DFlash2, Recirculation PoC, asymmetric KV
---

# Research Tab Stash — Additions from Aug 20–21 Session

## EVALUATE: DFlash2 (Inco AI, Aug 18 2026)

**What:** Block diffusion speculative decoding v2. Parallel drafting with a path selector (2M params, 0.6% latency) and local convolution (16.5M params, 0.7% latency). Achieves 2.7–3.4× autoregressive throughput on Qwen3.8-27B with provably identical output.

**Why it matters:** The Qwen3.8-27B DFlash2 drafter already exists (`incoai/Qwen3.8-27B-DFlash2`). Runs on SGLang, vLLM, and has an open llama.cpp PR (#27342 — not merged). NVIDIA measured up to 15× on Blackwell. For agent workloads that generate thousands of tokens per cycle, 3× throughput is the difference between 35 tok/s and ~100 tok/s.

**Blocker:** VRAM. The drafter needs to load alongside the target model. On a single 3090 at 98% utilization with the 27B, probably not feasible. Becomes practical with the second 3090 or if the llama.cpp PR merges with a CPU-offload path for the drafter.

**Watch:** llama.cpp PR #27342. If it merges to mainline, this becomes a flag in the bat file.

**Links:**
- Blog: https://inco.ai/blog/dflash2/
- Paper: https://arxiv.org/abs/2602.06036
- Drafter: https://huggingface.co/incoai/Qwen3.8-27B-DFlash2
- NVIDIA benchmark: https://developer.nvidia.com/blog/boost-inference-performance-up-to-15x-on-nvidia-blackwell-using-dflash-speculative-decoding/

---

## EVALUATE: Recirculation (DeepMind, arXiv:2608.17981, Aug 18 2026)

**What:** Training-free inference-time technique. Leaks a small fraction (α=0.15) of activation from a deep layer back to a shallow layer at each token step. 23% perplexity reduction on Gemma3, 21% accuracy increase on GSM8k. Tested across Gemma3, Qwen3, Ministral, Pythia, Phi2.

**Why it matters:** Free capability upgrade for any model, no retraining. Improves state tracking (relevant to T03 confabulation) and reasoning. The adaptive variant (learning just mixing coefficients) matches full fine-tuning performance.

**Blocker:** Prefill cost — requires serial processing during prefill (each token processed sequentially). For A0's fresh-context-per-cycle pattern, the prefill penalty may be significant. Needs empirical testing.

**PoC ready:** `recirc_poc.py` + `run_recirc_test.bat` prepared, tests on Qwen2.5-1.5B via HuggingFace. Run when VRAM is free. If results are positive, next step is llama.cpp C++ modification.

**Connection to SEL:** Recirculation makes the model a dynamical system — same concept as the SEL walker maintaining state across steps. Philosophically aligned with "deterministic scaffolding beats probabilistic reasoning."

---

## SHIPPED: Asymmetric KV Quantization (tbq4_0 keys / q8_0 values)

**What:** Keep keys at tbq4_0 (quality loss ~0.4%, negligible), upgrade values to q8_0 (quality loss drops from ~1.4% to <0.1%). Values directly influence output token probabilities; keys mostly affect attention routing.

**VRAM cost:** ~3,700 MiB total KV (up from 2,417), delta +1,280 MiB. With mmproj on CPU (--no-mmproj-offload), total VRAM ~21,500 MiB, leaving ~2.2 GB free after embedder.

**Applied to:** `start_qwen38_prod.bat`, committed alongside vision (mmproj + --no-mmproj-offload).
