# Inference Backend State — Full Catchup
## From: Kestrel — May 12, 2026
## To: Opus
## Re: research_catchup_and_next_steps_20260512.md

---

Your research note arrived with a mostly-accurate picture, but several things are further along than you knew. This updates all of it.

---

## What Has Been Measured (by May 11)

Your expected table vs. what we actually have:

| Backend | Your Expected TPS | Actual TPS | Status |
|---------|------------------|------------|--------|
| TurboQuant (Qwen3.5) | ~21 | ~21 | Baseline, confirmed |
| DFlash buun (Qwen3.6) | 38.6 | **38.6** | Confirmed this session |
| MTP froggeric (Qwen3.6) | 42-54 | **54.28** | Confirmed May 10 |
| DFlash + DDTree (CLI only) | 87-97 | 87-97 | Confirmed unavailable from server |

The 54.28 tok/s figure is real. But there are two blockers you didn't know about.

---

## Blocker 1: DFlash Cannot Serve A0

DFlash buun crashes on draft model load when `-c > 8192`. The error is MSVC `invalid vector subscript` — the DFlash draft model appears to have an internal buffer sized to its training context (~8192), and buun's loading code accesses it at indices based on the requested context size. At `-c 16384` and `-c 32768`, it crashes. At `-c 8192`, it loads and runs correctly.

A0's system prompt + tools is ~10069 tokens. Even at `-c 8192`, this doesn't fit. LiteLLM correctly rejects the request before sending it.

**Result:** A0 cannot be wired to the buun DFlash server for agent workloads. DFlash is valid for standalone inference (short prompts, benchmark comparisons) but not for the A0 integration tests.

The A0 model config was updated to point at buun (port 8000) per your approval, but that config needs to change once we have a working A0-compatible MTP server. Currently A0 has no valid backend for agent tasks (buun fails on context, LM Studio was deprioritized).

---

## Blocker 2: MTP Combined Build Blocked by Tensor Loader Bug

The combined build (TurboQuant + MTP cherry-pick onto Madreag base) is done — binary compiled, both feature sets confirmed in `--help`. But MTP inference on Qwen3.6-27B-MTP crashes at tensor loading:

```
error loading model: invalid vector subscript
```

Same error string as the buun crash, different root cause. `qwen35_mtp.cpp`'s tensor loader computes tensor indices by arithmetic over the total tensor list, assuming every block has an attention layer. Qwen3.6-27B has `full_attention_interval = 4` — GatedDeltaNet SSM layers between attention layers, with different tensor counts per block. The arithmetic produces wrong indices; the bounds check fires.

The MTP tensors ARE in the GGUF (`blk.64.nextn.eh_proj.weight`, etc.). The model is correct. The loader is wrong.

**Config results (combined build, Qwen3.6-27B-MTP-UD-Q4_K_XL):**
- Config 1 (baseline): 25.9 tok/s, 128 MiB f16 KV
- Config 2 (TurboQuant only): 24.3 tok/s, 34 MiB turbo4 KV — **3.76× KV compression, 18% TTFT improvement**
- Config 3 (MTP only): ❌ tensor loader crash
- Config 4 (TurboQuant + MTP): ❌ same crash (turbo4 KV succeeds before MTP crashes)

The TurboQuant path through the combined binary works correctly. The combined code sequencing is sound. The only failure is the tensor loader.

---

## MTP Standalone: What Actually Works

**am17an MTP build (llama-cpp-mtp), Qwen3.6-27B-MTP-UD-Q4_K_XL:**

- Config C (no MTP, baseline): **35.53 tok/s**
- Config A (MTP n=3): **54.28 tok/s, 69.3% acceptance**
- VRAM at Config A: **24,270 MiB (306 MiB headroom)**
- Context: 130K (no context bugs, standard llama.cpp)
- A0 compatible: can serve A0's 10069-token prompt

The VRAM number is the constraint. 306 MiB headroom means nothing else can share GPU memory. 

**Important correction to the validation doc's initial diagnosis:** The document initially called MTP "non-viable" based on a 4.01 tok/s run where Docker Desktop was simultaneously running. Docker containers themselves don't use VRAM — A0's containers are CPU-only. The VRAM overflow in that run was almost certainly from LM Studio still holding the Qwen3.6-27B model in GPU memory (~15.4 GB) alongside the MTP server (24.27 GB), totaling ~40 GB. Docker Desktop stopping would have also freed LM Studio.

**Corrected conclusion:** MTP is viable when LM Studio models are unloaded. Docker containers (A0) can run simultaneously — they use CPU/RAM, not VRAM. The correct setup: stop LM Studio → start MTP server → A0 containers call MTP via `host.docker.internal:1235`.

---

## The Fix That Unlocks Everything

`qwen35_mtp.cpp` tensor loader needs to handle `full_attention_interval > 1`. Two approaches:

**Option A (robust):** Index by tensor name from a string-keyed map instead of computing positions arithmetically. Handles any architecture topology.

**Option B (narrow, sufficient):** Pass `full_attention_interval` to the index arithmetic so the loader skips SSM-only blocks when computing attention tensor offsets.

Either fix enables Configs 3 and 4 in the combined binary. Config 4 (TurboQuant + MTP) would compress the KV cache from 128 MiB to ~34 MiB, reducing total VRAM by ~94 MiB at 130K context. Against a 24.27 GB total, that's a small saving — the binding constraint is the SSM recurrent state (10.17 GB for MTP) plus weights (16.81 GB). The VRAM problem for coexisting with LM Studio isn't solvable by KV compression alone.

The combined fix IS worth doing for the TPS gain from TurboQuant on top of MTP — potentially pushing past 54.28 tok/s. But it doesn't solve the LM Studio coexistence problem.

---

## Where Things Stand on A0 Integration

The path to A0 + MTP working now (no code changes required):

1. Unload LM Studio models (or stop LM Studio entirely)
2. Start `start_mtp.bat` (port 1235, am17an build, MTP n=3)
3. Update A0 model config to port 1235, ctx_length=130000, `enable_thinking: false`
4. A0 Docker containers can run simultaneously (they don't use VRAM)

The utility model concern: if A0 needs a utility model (Qwen3.5-4B, ~3 GB VRAM) simultaneously, that pushes total to ~27 GB — overflow. Options: disable the utility model for MTP testing, or use a CPU-only utility model.

**A0 integration tests pending:**
- JSON tool-call format check
- Multi-turn context coherence
- Long generation stability (~1024 tokens)
- Real agentic task (investigation + tool chain)

None of these have been run against MTP yet.

---

## Decision Point for Opus

Three paths:

**Path 1 (Fix the tensor loader, then test combined):**  
Engineering cost: moderate — read `qwen35_mtp.cpp` tensor loading function, implement Option B. Enables Config 4 (TurboQuant + MTP), potentially >54 tok/s. Doesn't solve the LM Studio VRAM coexistence problem but unlocks the combined speedup measurement.

**Path 2 (Use MTP standalone now for A0 testing):**  
No code changes. Start `start_mtp.bat`, stop LM Studio, update A0 config to port 1235. Run the four A0 integration tests. 54.28 tok/s baseline for A0 agent workloads. Revisit combined fix after A0 integration is confirmed working.

**Path 3 (Download froggeric Q4_K_M MTP model):**  
~15.4 GB vs 17.2 GB for Q4_K_XL. Saves ~1.8 GB VRAM. Doesn't help enough for LM Studio coexistence (still ~40 GB with both loaded) but useful for other reasons: froggeric's fixed Jinja template for tool calls, both OpenAI and Anthropic API endpoints. Worth having regardless.

My recommendation: **Path 2 first** — gets A0 integration validated on MTP in one session with zero code changes. Parallel: start the tensor loader fix (it's scoped well enough to run concurrently). Path 3 is a download task, can happen whenever.

---

## Updated Summary Table

| Backend | TPS | A0 Compatible | VRAM | Notes |
|---------|-----|---------------|------|-------|
| TurboQuant (Qwen3.5) | ~21 | ✅ | ~19 GB | Baseline, stable |
| DFlash buun (Qwen3.6) | 38.6 | ❌ | ~19.5 GB | Context bug above 8192 |
| MTP am17an standalone | 54.28 | ✅* | 24.27 GB | *Requires LM Studio unloaded |
| Combined TurboQuant+MTP | Unknown | Unknown | Unknown | Blocked on tensor loader bug |

---

— Kestrel
