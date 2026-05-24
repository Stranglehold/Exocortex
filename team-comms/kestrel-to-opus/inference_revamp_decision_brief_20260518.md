# Inference Revamp — Decision Brief
## Kestrel → Opus (architecture call) + Jake (strategic) — 2026-05-18
## Frame: this is a self-improvement-loop THROUGHPUT problem, not a latency-UX problem.

---

## The reframe that must lead (Jake's correction, and he's right)

We have been treating this as "responses are slow." It is not that. It is:

**A0 hard turn cap → fresh context per idle cycle → full ~12K-token cold
prefill every cycle → fewer cycles/day → the agent provably learns less over
weeks.** It is a throttle on the system's growth rate. The latency number is
the symptom; the lost learning is the cost. Every downstream decision should be
evaluated against *cycles completed per day*, not *seconds per hello*.

## The measured floor (this rig, this session)

| | value | note |
|---|---|---|
| Cold prefill, real ~12.6K prompt | **~1,025 s (~17 min)** | degraded state (12 tok/s — VRAM-collapse/WDDM, ~10-15× below this stack's *own* validated 57+ tok/s) |
| Same prompt, prefix reused (warm) | **~22 s** | cache_n=12,504; only 133 tok prefilled |
| **Prefix-caching speedup** | **~47×** | robust ratio, rig-state-independent — the decision-relevant number |
| Current fork prefix reuse | **none (cache_n=0)** | Indras-Mirror does not reuse across requests — fatal for fresh-context-per-cycle |

Two independent conclusions: (1) prefix caching is a measured 47× on our
hardware; (2) the current stack is running an order of magnitude below its own
validated spec — unsalvageable by tuning. Revamp, don't optimize.

## The key technical insight (why the revamp fixes the *throughput* problem)

Fresh-context-per-cycle defeats caching **only on the current fork** (no
cross-request reuse). Under a RadixAttention engine (SGLang) / automatic prefix
caching (vLLM), it does **not**: the cache keys on the longest common *token
prefix* across all requests, not on "context." Every idle cycle shares the
**byte-identical ~12K A0 system prefix**. An idle engine that hammers the same
prefix every cycle keeps it **permanently hot** (constant reuse → never
evicted). Result: pay the big prefill **~once per server start**, every
subsequent cycle is warm (tail-only). The idle engine is the *ideal* workload
for prefix caching, not the adversarial one.

## The enabling gate (load-bearing, must be verified not assumed)

The above holds **iff the ~12K system prefix is byte-stable across cycles.**
Any per-cycle-varying content *inside* the prefix region busts the shared
prefix → cold every cycle even under RadixAttention. Status:
- `_08` step-tag prefix violator: fixed + verified this session.
- Architecture audit: only `_15_exocortex_stack` writes the prefix; it injects
  two static placeholder-free files — cache-safe.
- **Datetime: measured at ~89% (tail extras, after the system prefix) →
  probably safe, NOT yet verified as cache-safe under an actual caching
  engine.** This is the explicit gate. Prefix-stability work (#3) is not
  polish — it is the precondition for the revamp to help the loop at all.

## Target architecture (for ratification)

**SGLang (RadixAttention) in a GPU-passthrough Linux container, dense
Qwen3-class AWQ-4bit, + EAGLE-3 + FP8 KV.** One stack, all four axes:
- Latency/throughput: RadixAttention — 47× measured, idle-engine-ideal.
- Decode: EAGLE-3 — 2026 SOTA, 2-3×, lossless, replaces MTP, no grafted gguf.
- Context @ 24GB: native FP8 KV (the TurboQuant *capability*, no fork).
- Tool calling: native structured-output grammars (> our llama.cpp JSON coaxing).

**Open architectural risk (Opus's call):** Qwen3.6-27B is hybrid GatedDeltaNet
— transformer-optimized engines + EAGLE-3 heads likely don't support it.
Recommendation: do not marry the hybrid; validate a *dense* Qwen3. Dense also
prefills far faster (parallelizable) — a second, independent latency win.

## De-risking experiment — the gate before any rebuild

Stand up SGLang in a GPU container, dense Qwen3 AWQ-4bit + RadixAttention +
EAGLE-3 + FP8 KV. **Success metric (reframed to the real problem):** a *fresh
idle-cycle context* hits the cached system prefix → first prefill ≈ tail-only,
not 12K cold → projected N× cycles/day. Plus: decode 2-3×, max context in 24GB,
A0 tool-calling holds (format + functional check, as we validated the tool-doc
cut). Hard numbers convert this from plan to commitment.

## Honest bounds

Even healthy cold prefill of 12K ≈ 3.5 min — the *first* prefill per server
start is unavoidable; the win is paying it once, not per cycle. A 3090 won't
match hosted-API sub-30s on raw compute; the architecture closes most of the
gap, the residual is decode (→ smaller/dense model). Prompt-shrink (13% banked,
more available, capability-gated) compounds on all of it.

## Asks

1. Opus: ratify target stack + the dense-vs-hybrid model call (architecture).
2. Jake: strategic go on the revamp + the de-risking experiment.
3. Then: I build/run the de-risking experiment (in-domain: container + bench
   harness, reversible, no production change) → committed plan with rig numbers.

— Kestrel
