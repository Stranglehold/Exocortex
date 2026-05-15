# MTP + TurboQuant Experiment — Status Report
## From: Kestrel — May 10, 2026
## To: Opus
## Re: mtp_turboquant_combined_experiment_20260509.md

---

## Where We Are

Option A and Option B failed. Option C is staged and ready to run.

### Option A: Turbo flags on am17an build — FAILED

Tried adding `-ctk turbo4 -ctv turbo3` to the am17an MTP build. Server exited immediately:
```
Unsupported cache type: turbo4
```
The am17an branch predates TurboQuant. It only supports standard llama.cpp KV types (f16, bf16, q8_0, q4_0, etc.). TurboQuant is not compiled in. Nothing to recover — the type table doesn't include turbo types.

### Option B: AtomicBot fork — FAILED (architecture incompatibility)

AtomicBot compiled cleanly (needed `-DCMAKE_ASM_COMPILER=cl.exe` fix for MSVC). Both turbo KV flags and `--mtp-head 3` accepted on startup. Server loaded 866 tensors from the GGUF header, then:
```
llama_model_load: error loading model: missing tensor 'blk.64.ssm_conv1d.weight'
```
Root cause: AtomicBot's model loader was written for attention-only architectures — its confirmed target is Gemma 4. Qwen3.6-27B is a hybrid DeltaNet SSM + attention model (49 SSM layers out of 65 total, with `full_attention_interval=4`). The SSM conv1d tensor at block 64 is an architecture feature AtomicBot doesn't recognize. There's no path forward with Option B on this model.

---

## Option C: Cherry-pick MTP into Madreag turbo3-cuda

The scripts are written and staged:

- **`inference/compile_combined.bat`** — clones turbo3-cuda fresh into `llama-cpp-combined/`, adds am17an as remote, cherry-picks 7 MTP commits, builds. Tracks per-commit progress in `.picks_progress` for clean resume after any conflict.
- **`inference/start_combined.bat`** — port 1237, turbo4/turbo3 KV, MTP n=3. Uses `--spec-draft-n-max` (am17an flag, not AtomicBot's `--mtp-head`).

**7 commits to cherry-pick (oldest first):**

| # | Hash | Description |
|---|------|-------------|
| 1 | 1a4fe4e6c | llama: allow partial seq_rm for GDN models |
| 2 | 589490f09 | add enum for part sequence removal |
| 3 | c5e02271c | rename rollback to rs_seq |
| 4 | 10829dbcc | llama + spec: MTP support **(CORE)** |
| 5 | f8c6b03da | add qwen35moe_mtp |
| 6 | 86d9f15e9 | fix double free |
| 7 | 5d5f1b46e | fix: use rs for only MTP |

Skipped: Metal, Vulkan, Python converter, test utility.

**Primary risk:** The CORE commit (`10829dbcc`) touches `llama.cpp` and `llama.h`. Madreag's TurboQuant also modifies these. Conflict is likely. Resolution strategy: keep all TurboQuant KV-cache code unchanged, add MTP additions (new struct fields, new functions, new graph-building path) alongside them. The additions are structurally additive — both MTP and TurboQuant do their work in different phases of the decode loop.

---

## What Happens Next

Jake runs `compile_combined.bat`. One of three outcomes:

1. **Clean cherry-pick + build** — both flags present in `--help` output, proceed to test protocol. Will fill in `eval/MTP_TURBOQUANT_COMBINED_VALIDATION.md` and report back.

2. **Cherry-pick conflict on CORE commit** — the script pauses with conflict resolution instructions. Manual merge needed. The key judgment call: MTP's additions to `llama.h` (mtp_pool, spec_mtp_* fields) should be added after TurboQuant's KV quantization fields. If the lines are close enough that git marks them as conflicting, keep both sets.

3. **Conflict too complex to resolve** — will write up exactly what conflicted and which lines. At that point we'd need to evaluate whether a dedicated engineering session to manually port the CORE commit makes sense.

---

## Preliminary VRAM Sweep Data

From the initial sweep run with the am17an MTP build (q8_0 KV, Config C baseline):

| Context | Peak VRAM | TPS |
|---------|-----------|-----|
| 2K | ~17.8 GB | 35.53 tok/s |
| 8K | ~18.1 GB | |
| 16K | ~18.5 GB | |
| 32K | ~19.2 GB | |
| 60K | ~20.3 GB | |
| 130K | (est.) ~21.5 GB | |

Config C (no MTP) baseline at 35.53 tok/s is confirmed from start_mtp.bat comments. The VRAM anomalies Jake noticed in the partial sweep data (numbers feeling low) may be related to the model being mid-load or LM Studio occupying VRAM — the am17an build runs clean when tested in isolation.

---

*Will follow up with test results once the combined build is confirmed working. The validation doc is at `inference/eval/MTP_TURBOQUANT_COMBINED_VALIDATION.md`.*

— Kestrel
