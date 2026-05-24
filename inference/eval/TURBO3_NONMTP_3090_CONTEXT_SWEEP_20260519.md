# TurboQuant Context/VRAM Sweep — Qwen3.6-27B-Q4_K_M (NON-MTP), RTX 3090

## Date: 2026-05-19
## Binary: inference/turbo3-cuda/build/bin/llama-server.exe (Madreag turbo3-cuda, sm_86)
## Model: D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf (non-MTP)
## Purpose: strategy pivot — amortize the fixed per-cycle cold-prefill tax over a
## much larger context (more work/cycle) instead of chasing cycle count, since
## the inference fork has no cross-request prefix reuse (cache_n=0).

---

## Measured results (turbo3 KV, -fa on, -ngl 99, --parallel 1)

| ctx | loaded | load_s | VRAM used | VRAM free | prefill t/s | decode t/s | WDDM risk |
|----:|:--:|--:|--:|--:|--:|--:|:--:|
| 32 768  | ✅ | 120.8* | 21 796 | 2 531 | 1 087 | 30.3 | no |
| 65 536  | ✅ | 9.5  | 22 199 | 2 128 | 1 110 | 30.1 | no |
| 131 072 | ✅ | 12.6 | 22 992 | 1 335 | 1 107 | 32.7 | no |
| **196 608** | ✅ | 12.5 | 23 678 | **649** | 1 092 | 30.8 | no |
| 262 144 | ✅ | 12.5 | 23 830 | 497 | **18.3 (collapsed)** | 27.3 | **YES** |

*first cold load includes model read from disk; subsequent reloads ~10-13s.

GPU baseline (desktop/apps, no model): ~5.4 GB used / ~18.9 GB free of 24 GB.

### Verdict
- **turbo3 max-safe context on this 3090 = 196 608 (~196K).** 256K falls off
  the WDDM-paging cliff: free VRAM 497 MiB, prefill collapses 1090 → 18 tok/s.
- Prefill ~1090 tok/s is **~90× the degraded MTP-server prefill** (~12 tok/s)
  that caused the original "17-minute hello." Prefill is no longer the wall.
- Decode ~30 tok/s (no MTP speculative decode here — expected; MTP only
  accelerated decode, orthogonal to this context-amortization strategy).
- The sweep probe reported `needle_ok=false` everywhere — **probe artifact,
  not a server fault.** Cause: `max_tokens=32` on a thinking model (Qwen3.6
  spends them on reasoning, emits empty `content`). Confirmed by a proper
  functional probe (max_tokens=400, read reasoning_content): `content='42'`
  for "17+25", reasoning trace present, `finish_reason=stop`. **The
  turbo3-cuda binary + non-MTP Q4_K_M on sm_86 produces correct output. No
  sm_86 garbage bug for this model.**

## Production config deployed (per Jake: run at max-safe − 20K)

- **Server:** turbo3-cuda llama-server, `-c 176000` (= 196 608 − ~20K margin,
  keeps comfortably off the WDDM cliff), `-ctk turbo3 -ctv turbo3 -fa on
  -ngl 99 --parallel 1 --host 0.0.0.0 --port 1235`. No MTP flags. Thinking ON.
- Launch script: `inference/start_turbo3_prod.bat`. Detached (survives session).
- v16 `_model_config` already points `api_base` → `host.docker.internal:1235`
  → picked up automatically, **no endpoint reconfig**.

## ctx_length — left at 60000 (NOT raised), by Jake's explicit instruction
There is **no web-UI / settings-API path** for ctx_length in this deployment:
A0 `settings.py` has no chat-model/ctx fields; the only location is the
`_model_config` plugin `config.json` (= "hardcoding," which Jake said to
avoid). Jake's instruction was "set via web UI; if not, just leave it." → left
at 60000. **Recommended value when Jake chooses to raise it:** `ctx_length:
150000` (server holds 176K; ~26K headroom for generation + thinking tokens;
`ctx_history` already 0.7). One-line edit in
`/a0/usr/plugins/_model_config/config.json`. Until then A0 only uses 60K of
the 176K window — the big context is provisioned and ready, not yet exploited.

## Revert (if needed)
1. Stop turbo3 server: `Get-Process llama-server | Stop-Process` (or close its window).
2. Restart the original MTP server: `inference/start_mtp.bat` (port 1235).
3. v16 needs no config change (api_base unchanged; ctx_length never modified).

---

## Addendum 2026-05-20 — Speculative decoding (draft model) attempt + finding

**Attempted:** Adding a standalone draft model via `-md` to gain decode speedup.
Picked vocab-compatible `Qwen3.5-0.8B-Q8_0` (verified `arch=qwen35`, `vocab=248320`,
`tok_pre=qwen35`, hybrid SSM fields all matching the main 27B).

**Result: speculative decoding silently auto-disabled at startup.** Decisive
evidence — captured from llama-server stderr after relaunching with output redirected:

```
srv    load_model: loading draft model '...Qwen3.5-0.8B-Q8_0.gguf'
common_speculative_is_compat: the target context does not support partial sequence removal
srv    load_model: speculative decoding not supported by this context
```

**Root cause:** turbo3-cuda fork (Madreag) lacks the upstream SSM-rollback fix
from [llama.cpp PR #20075](https://github.com/ggml-org/llama.cpp/pull/20075)
(*"fix: speculative decoding broken on hybrid SSM/MoE"*). The hybrid Qwen3.6's
DeltaNet/SSM (`llama_memory_recurrent`) has no rollback mechanism for state when
drafted tokens get rejected → the spec engine's `is_compat` check fails before
any request runs → spec is auto-disabled. Per-request timings confirm:
`draft_n: None`, decode = 33.5 t/s (same as no-draft baseline ~30 t/s).

**Ruled out by reading source + capturing the log:**
- ❌ Flag issue — `-md` alone is sufficient; `--spec-type` is for n-gram-only.
- ❌ Prompt length — spec disabled at startup, before any prompt; 19-token probe
  also failed to engage.
- ❌ Draft selection — any standard draft hits the same target-side `is_compat`
  failure. Not a draft-model-quality problem.
- ❌ Architecture mismatch — both target and draft have identical 5 SSM fields;
  arch + vocab + tok_pre all match.
- ❌ Multimodal auto-disable — only triggers when `--mmproj` is explicitly
  passed; not our case.

**Working elsewhere:** [PR #20075 benchmark](https://github.com/ggml-org/llama.cpp/pull/20075)
shows M3 Max with Qwen3.5-122B hybrid + Qwen3.5-0.8B draft → 23.5–29.7 t/s
(from 20.4 baseline), 63–89% acceptance. So the strategy is sound — the
turbo3-cuda binary just needs the fix.

**Action taken:** draft flags removed from `start_turbo3_prod.bat` (reverted to
no-draft); reclaims ~1 GB of VRAM that was loaded but unused. Decode remains
~30 t/s. The bat now carries the full explanation in its REM header to prevent
future repeat investigation.

**Real fix paths (deferred — not a quick-win):**
1. Rebase turbo3-cuda onto a current upstream commit that includes PR #20075
   (or its successor). May come for free on Madreag's next rebase.
2. Switch to the DFlash stack (`inference/lucebox-dflash`) which uses a custom
   draft *head* that doesn't need recurrent-memory rollback — sidesteps the
   issue entirely. Cost: loses turbo3 KV quant + the 150K context window.

The DFlash path's existence is now retroactively explained: the project
invested in custom-draft architectures precisely *because* standard `-md`
drafts can't work on hybrid SSM mains in unpatched llama.cpp.
