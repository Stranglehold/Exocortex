# TurboQuant Build Validation
## Fork: Madreag/turbo3-cuda
## Hardware: RTX 3090 (sm_86) · CUDA 12.8
## Model: Qwen3.6-27B Q4_K_M (`D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf`)
## Date: [fill in]

---

## Build Info

| Field | Value |
|-------|-------|
| Commit hash | |
| Build date | |
| CUDA version | 12.8 |
| Binary path | `inference\turbo3-cuda\build\bin\Release\llama-server.exe` |

---

## Test 1: Perplexity (Quality)

Dataset: WikiText-2 (`wiki.test.raw`)

Command template:
```
llama-perplexity -m <model> -ngl 99 -fa -ctk <K> -ctv <V> -f wiki.test.raw
```

| Config | ctk | ctv | PPL | vs q4_0 delta | Notes |
|--------|-----|-----|-----|---------------|-------|
| q4_0 baseline | q4_0 | q4_0 | | — | |
| turbo3 symmetric | turbo3 | turbo3 | | | expect ~1% |
| turbo4 symmetric | turbo4 | turbo4 | | | expect ≈ q8_0 |
| turbo4/turbo3 asymmetric | turbo4 | turbo3 | | | default config |

**Qwen3.5 note:** Published testing shows q4_0 KV is LOSSLESS (BLEU 1.000) on Qwen3.5 due to DeltaNet linear layers on 24/32 layers absorbing quantization noise. Expect turbo results to be at or above this baseline.

**Pass criteria:** turbo3 PPL within 2% of q4_0 baseline.

---

## Test 2: Speed Benchmark (Decode + Prefill)

Command template:
```
llama-bench -m <model> -ngl 99 -fa -ctk <K> -ctv <V> -p 4096 -n 128 -d 0,8000,32000,64000 -r 3
```

### q4_0 baseline

| Context depth | Prefill (t/s) | Decode (t/s) |
|---------------|---------------|--------------|
| 0 | | |
| 8 000 | | |
| 32 000 | | |
| 64 000 | | |

### turbo3 symmetric

| Context depth | Prefill (t/s) | Decode (t/s) | Decode vs baseline |
|---------------|---------------|--------------|---------------------|
| 0 | | | |
| 8 000 | | | |
| 32 000 | | | expect +34-47% |
| 64 000 | | | expect +34-47% |

### turbo4/turbo3 asymmetric (default config)

| Context depth | Prefill (t/s) | Decode (t/s) | Decode vs baseline |
|---------------|---------------|--------------|---------------------|
| 0 | | | |
| 8 000 | | | |
| 32 000 | | | |
| 64 000 | | | |

**Pass criteria:** Decode speed at 32K+ context equal to or better than q4_0 baseline.

---

## Test 3: VRAM Usage

Monitor with `nvidia-smi` during each config at matching context length.

| Config | Context | VRAM used | Headroom | Notes |
|--------|---------|-----------|----------|-------|
| q4_0 baseline | 32 768 | | | |
| turbo3 symmetric | 32 768 | | | |
| turbo3 symmetric | 80 000 | | | |
| turbo3 symmetric | 131 072 | | | |
| turbo3 symmetric | 160 000 | | | |
| turbo3 symmetric | 196 608 | | | OOM if headroom <0 |

**Note for dashboard.html:** Once Test 3 numbers are in, update the VRAM reference table in `inference/dashboard.html` with turbo3-specific values (currently shows Q4_0 estimates).

---

## Test 4: Functional Validation (Merge Sort)

Prompt: "Write a Python script that implements merge sort and test it with a list of 10 random integers."

Run this prompt through Agent Zero with each KV config (swap `start.bat` config, restart server).

| Config | Step count | JSON errors | Output correct | Notes |
|--------|------------|-------------|----------------|-------|
| q4_0 baseline | | | | |
| turbo3 symmetric | | | | |
| turbo4/turbo3 asymmetric | | | | |

**Pass criteria:** Identical output and step count across all configs. Any regression is a hard stop — do not switch production backend.

---

## Test 5: Context Length Ceiling

Objective: Find maximum context that fits 24 GB with turbo3 KV and no OOM.

```
llama-server -m <model> -ngl 99 -fa -ctk turbo3 -ctv turbo3 -c <CTX> --host 0.0.0.0 --port 1234
```

| Context | OOM? | VRAM peak | Usable? | Notes |
|---------|------|-----------|---------|-------|
| 80 000 | | | | NousResearch reference |
| 131 072 | | | | |
| 160 000 | | | | ST-013 relevance point |
| 196 608 | | | | |
| 262 144 | | | | likely OOM |

**ST-013 connection:** If turbo3 fits at 160K+, subordinate overflow (Test D) may be addressable by context expansion alone rather than requiring reduced extension stacks (DEC-028 subordinate profiles). Document which context level resolves the overflow symptom.

---

## Summary

| Item | Result | Pass? |
|------|--------|-------|
| Build succeeded | | |
| Test 1: PPL within 2% | | |
| Test 2: decode speed ≥ baseline at 32K | | |
| Test 3: VRAM measured | | |
| Test 4: merge sort identical | | |
| Test 5: context ceiling identified | | |

**Recommended production config:**

```
KV_TYPE_K=
KV_TYPE_V=
CTX_SIZE=
```

**Recommendation:** [ SWITCH / HOLD / FALLBACK TO q4_0 ]

**Reason:**

---

*Write results to team-comms when complete. Do not switch production inference backend until Jake approves benchmark numbers.*
