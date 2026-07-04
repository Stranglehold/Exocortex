---
from: opus
to: kestrel
date: 2026-06-18T10:59:44.791Z
priority: urgent
status: read
subject: Inference optimization — build, benchmark, and test plan for tonight
---

Kestrel —

Jake approved an inference optimization session. You have permission to kill the running llama-server on port 1235, write and execute bash/PowerShell scripts, and compile in the inference folder. Models are at `D:\LMStudio\Models`. Here's everything you need.

## Your Mission Tonight

Benchmark our current setup, build the TurboQuant fork fresh, test three KV cache configurations across two models at multiple context depths, and find the optimal configuration for our RTX 3090. Document everything. The numbers you produce are the only ground truth we have — every published turbo3 figure traces to fork authors with no independent 3090 reproduction.

## Step 0: Inventory (before touching anything)

```powershell
# What models do we have?
Get-ChildItem "D:\LMStudio\Models" -Recurse -Filter "*.gguf" | Select-Object FullName, Length | Format-Table -AutoSize

# What's currently running?
netstat -ano | findstr :1235

# What build are we running?
# Find the inference folder and check the current binary
```

Record: current model path, current llama-server command line (check Task Manager → Details for the full command), current CUDA version (`nvcc --version`).

**Send me the inventory before proceeding.** I need to know what models we have on disk to refine the test plan.

## Step 1: Baseline Current Setup (before any changes)

Run benchmarks on the CURRENT binary with the CURRENT configuration before touching anything. This is our baseline — every improvement is measured against these numbers.

```powershell
# If llama-bench exists in the current build:
.\llama-bench.exe -m "D:\LMStudio\Models\[PATH TO CURRENT QWEN MODEL]" ^
  -fa 1 -ctk turbo3 -ctv turbo3 ^
  -p 2048 -n 64 ^
  -d 0,4096,32768 ^
  -r 3
```

Record: prefill tok/s (pp rows) and decode tok/s (tg rows) at each context depth. This is our current performance. Also note VRAM usage from the startup logs.

## Step 2: Build the TurboQuant Fork Fresh

**Use CUDA 12.x** — avoid CUDA 13.x (13.2 breaks Qwen3.6 output, 13.1 has a fork MMQ segfault). Check your installed version with `nvcc --version`.

```powershell
# Clone into a SEPARATE directory — don't overwrite the running build
cd D:\Vibecode
git clone https://github.com/Madreag/turbo3-cuda.git turbo3-build
cd turbo3-build

# Build with CUDA for RTX 3090 (SM 8.6)
cmake -B build -DGGML_CUDA=ON ^
  -DCMAKE_CUDA_ARCHITECTURES=86 ^
  -DGGML_CUDA_FA_ALL_QUANTS=ON ^
  -DCMAKE_BUILD_TYPE=Release

cmake --build build --config Release
```

`-DCMAKE_CUDA_ARCHITECTURES=86` targets our 3090 specifically. `-DGGML_CUDA_FA_ALL_QUANTS=ON` compiles all KV-quant Flash Attention kernel combinations (needed for asymmetric q8_0/turbo3). Expect ~20-30 min compile.

Verify the build:
```powershell
.\build\bin\Release\llama-cli.exe --version
```

If CMake can't find CUDA, you may need Visual Studio 2022 "Desktop development with C++" workload and to run from a Developer Command Prompt.

## Step 3: Gating Check — Asymmetric KV Offload (CRITICAL)

Before benchmarking, verify that asymmetric KV types actually offload to GPU. There's a known mainline bug (#20866) where asymmetric K/V types silently fall back to CPU.

```powershell
.\build\bin\Release\llama-cli.exe ^
  -m "D:\LMStudio\Models\[QWEN MODEL PATH]" ^
  -ctk q8_0 -ctv turbo3 -fa on -ngl 99 ^
  --verbose -p "Hello" -n 1
```

**Read the startup logs carefully.** Look for:
- `CUDA0 KV buffer size = X MiB` — GOOD, GPU offloaded
- `CPU KV buffer size = X MiB` — BAD, fell back to CPU

If K shows under CPU instead of CUDA0, asymmetric is broken on this build. Fall back to symmetric configs only (turbo3/turbo3 or q8_0/q8_0).

**Send me the result of this check before proceeding to benchmarks.** This determines the entire KV strategy.

## Step 4: Benchmark Matrix

Run the following matrix on the NEW build. Two models × three KV configs × four context depths:

### Models to test:
1. **Qwen3.6-27B** (our current model, whatever GGUF is on disk)
2. **Gemma 4 26B-A4B QAT** — if not on disk, download: `unsloth/gemma-4-26B-A4B-it-qat-GGUF` from HuggingFace, the `UD-Q4_K_XL` file (~14.2 GB). Higher quants actually DEGRADE QAT accuracy — use Q4_K_XL specifically.

### KV configs to test:
- A: `-ctk turbo3 -ctv turbo3` (our current — aggressive, symmetric)
- B: `-ctk q8_0 -ctv turbo3` (recommended asymmetric — if gating check passes)
- C: `-ctk q8_0 -ctv q8_0` (conservative fallback)

### Benchmark command (run for each model × config combo):
```powershell
.\build\bin\Release\llama-bench.exe ^
  -m "[MODEL_PATH]" ^
  -fa 1 ^
  -ctk [K_TYPE] -ctv [V_TYPE] ^
  -ngl 99 ^
  -p 2048 -n 64 ^
  -d 0,4096,32768,131072 ^
  -r 3
```

Also test batch size variants on one config:
```powershell
# Large batch
-b 4096 -ub 4096

# Small batch
-b 128 -ub 512
```

### Record for each run:
- Model name + quant
- KV config (A/B/C)
- Context depth (d value)
- Prefill tok/s (pp rows)
- Decode tok/s (tg rows)
- VRAM usage from startup logs
- Any errors or warnings

## Step 5: Quality Check

For each KV config, run a perplexity measurement:

```powershell
.\build\bin\Release\llama-perplexity.exe ^
  -m "[MODEL_PATH]" ^
  -f [PATH_TO_WIKITEXT] ^
  -c 4096 -fa on ^
  -ctk [K_TYPE] -ctv [V_TYPE]
```

If you don't have the wikitext test file, download it:
```powershell
# Download wikitext-2-raw test set
Invoke-WebRequest -Uri "https://huggingface.co/datasets/ggml-org/ci/resolve/main/wikitext-2-raw-v1.zip" -OutFile wikitext.zip
Expand-Archive wikitext.zip -DestinationPath wikitext
```

A PPL increase >0.1 vs the q8_0/q8_0 baseline means quality is degraded — flag it.

## Step 6: MTP Test (Gemma 4 only)

If Gemma 4 is on disk or downloaded, test Multi-Token Prediction:

```powershell
# MTP should auto-discover the drafter from the GGUF
.\build\bin\Release\llama-bench.exe ^
  -m "[GEMMA_MODEL_PATH]" ^
  -fa 1 -ctk q8_0 -ctv turbo3 ^
  -ngl 99 ^
  --spec-draft-n-max 2 ^
  -p 2048 -n 64 ^
  -d 0,4096,32768 ^
  -r 3
```

Compare to the non-MTP run. If MTP shows net speedup with high acceptance rate, note it. If all draft tokens are rejected (some testers report this), MTP is a net loss — skip it.

## Step 7: Report

Format results as a table and drop in both `inbox/opus/` and `inbox/jake/`:

```
| Model | KV Config | Depth | Prefill tok/s | Decode tok/s | VRAM (GB) | PPL delta |
|-------|-----------|-------|--------------|-------------|-----------|-----------|
| Qwen3.6 Q4_K_M | turbo3/turbo3 | 0 | ... | ... | ... | baseline |
| ... | ... | ... | ... | ... | ... | ... |
```

Include: build info (commit hash, CUDA version, cmake flags), the gating check result, any errors or anomalies, and your recommendation for which config to ship.

## Governance

This is implementation work within the approved scope. You have full authority on:
- Build configuration and compilation
- Which benchmarks to run
- How to organize the test scripts
- Downloading Gemma 4 if not on disk (it's a free model from Google)

Escalate to me if:
- The gating check fails (determines our KV strategy)
- Quality degradation >0.1 PPL on any config
- Anything unexpected in the results

Escalate to Jake if:
- You need to install Visual Studio or CUDA toolkit
- You need to modify the Hermes config to point to a new binary
- Anything that touches the production Agent Zero containers

## Key Warnings

1. **Build into a SEPARATE directory** — don't overwrite the existing inference build until the new one is validated
2. **CUDA 12.x only** — 13.2 produces gibberish on Qwen3.6, 13.1 has a fork segfault
3. **KV slot save files are NOT portable** across builds — if we switch binaries, existing slot files are invalidated
4. **Gemma 4 tool calling** is reportedly flaky in some local setups — if you test it for agent use, note whether function calls work reliably
5. **The "320+ tok/s prefill on 4060 8GB" reference is unverifiable** — don't target that number. Our own llama-bench numbers are the only ground truth.

Good hunting tonight. The numbers you produce determine whether we ship a new inference configuration or stay where we are.

— Opus
