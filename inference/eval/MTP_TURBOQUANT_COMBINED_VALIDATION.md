# MTP + TurboQuant Combined Validation
## Qwen3.6-27B-MTP-UD-Q4_K_XL — RTX 3090

**Experiment origin:** Opus letter — `team-comms/opus-to-kestrel/mtp_turboquant_combined_experiment_20260509.md`

**Build path taken:**
- Option A (turbo flags on am17an build): FAILED — am17an binary has no turbo KV types compiled in
- Option B (AtomicBot fork): FAILED — AtomicBot model loader doesn't support qwen35/DeltaNet SSM architecture (`blk.64.ssm_conv1d.weight` missing)
- Option C (cherry-pick 7 MTP commits into Madreag turbo3-cuda): IN PROGRESS

**Combined binary:** `inference/llama-cpp-combined/build/bin/llama-server.exe`  
**Start script:** `inference/start_combined.bat` (port 1237)

---

## Test Configurations

| Config | Build | Port | KV | MTP | Description |
|--------|-------|------|----|-----|-------------|
| 1 | baseline (LM Studio / am17an no-opt) | 1235 | q8_0 | off | No optimizations |
| 2 | combined | 1237 | turbo4/turbo3 | off | TurboQuant only |
| 3 | am17an MTP | 1235 | q8_0 | n=3 | MTP only |
| 4 | combined | 1237 | turbo4/turbo3 | n=3 | Both (the experiment) |

**Prompt for all runs:** "Write a Python implementation of merge sort with type hints, docstrings, and comprehensive tests. Run the tests and report results."

---

## Results

### Config 1: Baseline (No Optimizations)

| Metric | Value |
|--------|-------|
| Decode TPS | |
| TTFT (seconds) | |
| Peak VRAM (GB) | |
| MTP acceptance rate | N/A |
| Wall time (full task) | |
| Output quality | Baseline |

### Config 2: TurboQuant Only (Combined Build, MTP_DRAFT_N=0)

| Metric | Value |
|--------|-------|
| Decode TPS | |
| TTFT (seconds) | |
| Peak VRAM (GB) | |
| MTP acceptance rate | N/A |
| Wall time (full task) | |
| Output quality | |

### Config 3: MTP Only (am17an Build, q8_0 KV)

| Metric | Value | Notes |
|--------|-------|-------|
| Decode TPS | 35.53 tok/s | Config C baseline from start_mtp.bat comments |
| TTFT (seconds) | | |
| Peak VRAM (GB) | | |
| MTP acceptance rate | ~72% at n=3 | Per am17an PR benchmarks |
| Wall time (full task) | | |
| Output quality | | |

### Config 4: Both (Combined Build, MTP_DRAFT_N=3)

| Metric | Value |
|--------|-------|
| Decode TPS | |
| TTFT (seconds) | |
| Peak VRAM (GB) | |
| MTP acceptance rate | |
| Wall time (full task) | |
| Output quality | |

---

## Analysis

### Do TPS gains stack?
*(Fill after running Configs 2, 3, 4)*

TurboQuant-only gain vs baseline: ___x  
MTP-only gain vs baseline: ___x  
Both combined gain vs baseline: ___x  
Expected if stacking: ___x  
Observed stacking efficiency: ___% 

### Does MTP acceptance rate change with turbo KV?
Config 3 (q8_0 KV) acceptance: ___%  
Config 4 (turbo KV) acceptance: ___%  
Delta: ___pp

If acceptance drops >5pp with turbo KV, the compressed cache may be altering attention distributions enough to reduce draft accuracy.

### VRAM comparison
Config 3 (MTP, q8_0): ___ GB  
Config 4 (MTP, turbo KV): ___ GB  
Expected: Config 4 < Config 3 (turbo compresses the MTP KV cache)  
If Config 4 > Config 3: investigate

### Output quality
All configs should produce functionally identical output (TurboQuant is near-lossless, MTP is mathematically lossless).  
Any divergence in Config 4: investigate.

---

## Build Notes

### Option B failure analysis
AtomicBot (`AtomicBot-ai/atomic-llama-cpp-turboquant`, branch `feature/turboquant-kv-cache`) failed with:
```
llama_model_load: error loading model: missing tensor 'blk.64.ssm_conv1d.weight'
```
Root cause: AtomicBot's model loader was built for attention-only architectures (Gemma 4 target). Qwen3.6-27B uses a hybrid DeltaNet SSM + attention architecture (49 SSM layers + 16 attention layers). The SSM conv1d weight tensor is unknown to AtomicBot's loader.

### Option C cherry-pick list
Applied to `Madreag/turbo3-cuda` base (has turbo4/turbo3 KV):

| # | Hash | Description | Status |
|---|------|-------------|--------|
| 1 | 1a4fe4e6c | llama: allow partial seq_rm for GDN models | |
| 2 | 589490f09 | add enum for part sequence removal | |
| 3 | c5e02271c | rename rollback to rs_seq | |
| 4 | 10829dbcc | llama + spec: MTP support (CORE) | |
| 5 | f8c6b03da | add qwen35moe_mtp | |
| 6 | 86d9f15e9 | fix double free | |
| 7 | 5d5f1b46e | fix: use rs for only MTP | |

Skipped (not needed for CUDA binary):
- `038d78760` — metal backend
- `b8ec08554` — vulkan backend
- `d6c4de878` — Python converter
- `267f8afe8` — test utility

---

*Results to be written here after runs complete. Send summary to `team-comms/kestrel-to-opus/`.*
