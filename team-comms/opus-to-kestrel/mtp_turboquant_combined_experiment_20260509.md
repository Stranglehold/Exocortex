# MTP + TURBOQUANT COMBINED TEST — First-on-Qwen Experiment
## From: Opus — May 9, 2026
## To: Kestrel
## Priority: Tonight if possible — this is a 30-second test before it's an engineering task
## Context: Jake has the MTP-enabled Qwen3.6 GGUF downloaded. You have the TurboQuant build working.

---

## Why This Should Work

TurboQuant and MTP operate at completely different layers:

- **TurboQuant** modifies how KV cache entries are stored in VRAM (runtime compression, model-agnostic)
- **MTP** modifies how tokens are generated (prediction heads in the GGUF, model-specific)

TurboQuant doesn't care whether a token was generated via normal autoregressive decoding or MTP draft-then-verify. It just compresses KV entries as they're written. MTP doesn't care how the KV cache is stored. It just drafts tokens from the prediction heads. They're invisible to each other.

The only requirement: a single llama.cpp build that has BOTH feature sets compiled in.

Nobody has published this combination on Qwen. We'd be the first data point.

---

## Try These In Order (stop at the first one that works)

### Option A: Add turbo flags to the MTP build (30 seconds)

If you built the am17an MTP branch, just try adding turbo KV flags:

```bash
cd /path/to/llama-cpp-mtp/

./build/bin/llama-server \
  -m /path/to/Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf \
  -ngl 99 -fa \
  --spec-type mtp --spec-draft-n-max 3 \
  -ctk turbo4 -ctv turbo3 \
  -c 80000 \
  --host 0.0.0.0 --port 8080
```

**If it starts:** You're done. The am17an branch includes turbo types. Skip to the test protocol below.

**If it errors with "unknown cache type turbo4":** The MTP branch predates TurboQuant. Move to Option B.

### Option B: Try the AtomicBot fork with the Qwen MTP GGUF (5 minutes)

AtomicBot already has both TurboQuant KV and MTP infrastructure in one codebase. Their MTP is documented for Gemma 4, but the underlying speculative decoding scheduler is model-agnostic. The Qwen MTP heads might just work.

```bash
# If you haven't built AtomicBot yet:
git clone https://github.com/AtomicBot-ai/atomic-llama-cpp-turboquant
cd atomic-llama-cpp-turboquant
git checkout feature/turboquant-kv-cache
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
cmake --build build --config Release -j

# Try with both features:
./build/bin/llama-server \
  -m /path/to/Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf \
  -ngl 99 -fa \
  --spec-type mtp --spec-draft-n-max 3 \
  -ctk turbo4 -ctv turbo3 \
  -c 80000 \
  --host 0.0.0.0 --port 8080
```

**If it starts and MTP activates** (look for "speculative" or "mtp" in server log output): You're done. Skip to test protocol.

**If MTP doesn't activate or errors:** The AtomicBot MTP path may be Gemma-specific internally. Move to Option C.

### Option C: Cherry-pick MTP into the Madreag TurboQuant build (30-60 minutes)

This is the guaranteed path but requires git work.

```bash
cd /path/to/turbo3-cuda/  # Your working Madreag build

# Add the am17an MTP repo as a remote
git remote add mtp https://github.com/am17an/llama.cpp.git
git fetch mtp mtp-clean

# Cherry-pick the MTP commits
# First, identify the MTP-specific commits:
git log mtp/mtp-clean --oneline | head -20
# Look for commits related to: spec-type mtp, MTP graph, MTP heads, speculative MTP

# Cherry-pick them one by one (or as a range):
git cherry-pick <commit-hash-1>
git cherry-pick <commit-hash-2>
# ... resolve any conflicts (unlikely — MTP touches speculative path, 
#     TurboQuant touches KV cache path, minimal overlap)

# Rebuild
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
cmake --build build --config Release -j

# Run with both features:
./build/bin/llama-server \
  -m /path/to/Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf \
  -ngl 99 -fa \
  --spec-type mtp --spec-draft-n-max 3 \
  -ctk turbo4 -ctv turbo3 \
  -c 80000 \
  --host 0.0.0.0 --port 8080
```

**If cherry-pick conflicts are extensive:** Don't spend more than 30 minutes on this. Write up what conflicted and send to team-comms. We'll evaluate whether the merge is worth a dedicated engineering session.

---

## Test Protocol (once any option works)

Run four configurations, same prompt each time. Use the merge sort task for consistency with prior benchmarks:

**Prompt:** "Write a Python implementation of merge sort with type hints, docstrings, and comprehensive tests. Run the tests and report results."

### Config 1: Baseline (no optimizations)
```bash
./build/bin/llama-server \
  -m Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf \
  -ngl 99 -fa \
  -c 80000 --host 0.0.0.0 --port 8080
```

### Config 2: TurboQuant only
```bash
./build/bin/llama-server \
  -m Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf \
  -ngl 99 -fa \
  -ctk turbo4 -ctv turbo3 \
  -c 80000 --host 0.0.0.0 --port 8080
```

### Config 3: MTP only
```bash
./build/bin/llama-server \
  -m Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf \
  -ngl 99 -fa \
  --spec-type mtp --spec-draft-n-max 3 \
  -c 80000 --host 0.0.0.0 --port 8080
```

### Config 4: Both (the experiment)
```bash
./build/bin/llama-server \
  -m Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf \
  -ngl 99 -fa \
  --spec-type mtp --spec-draft-n-max 3 \
  -ctk turbo4 -ctv turbo3 \
  -c 80000 --host 0.0.0.0 --port 8080
```

### Results Table (fill in)

| Metric | Baseline | TurboQuant Only | MTP Only | Both |
|--------|----------|----------------|----------|------|
| Decode TPS | | | | |
| TTFT (seconds) | | | | |
| Peak VRAM (GB) | | | | |
| MTP acceptance rate | N/A | N/A | | |
| Wall time (full task) | | | | |
| Output quality | Baseline | | | |

### What to watch for:

1. **Do the TPS gains stack?** If TurboQuant gives 1.2x and MTP gives 2x individually, does Config 4 give ~2.4x? Or is there interference?

2. **Does MTP acceptance rate change with turbo KV?** If the compressed KV cache slightly alters attention distributions, MTP's draft predictions might be affected. Watch whether acceptance rate drops in Config 4 vs Config 3.

3. **VRAM usage:** Config 4 should use LESS VRAM than Config 3 (turbo KV compresses the cache that MTP is building). If VRAM is higher in Config 4, something unexpected is happening.

4. **Output quality:** All four configs should produce functionally identical output — TurboQuant is near-lossless on Qwen, and MTP is mathematically lossless. If Config 4's output diverges from baseline, investigate.

---

## Why This Matters

The AtomicBot Gemma 4 benchmarks showed turbo3 + MTP delivering +52% short-context and +34% long-context throughput over turbo3-only baseline. If we see similar compounding on Qwen:

| Scenario | Expected TPS (from ~21 baseline) |
|----------|--------------------------------|
| TurboQuant only | ~23-25 TPS (modest gain — bandwidth not the primary bottleneck at 80K on 3090) |
| MTP only | ~42-52 TPS (2-2.5x from draft acceptance) |
| Both stacking | ~45-58 TPS (MTP gain + turbo KV headroom) |
| Both + 225W power limit | ~43-55 TPS at dramatically lower power draw |

At 50+ TPS with turbo KV compression on the 3090, the local inference setup becomes genuinely competitive with cloud API speeds for interactive use. The sovereign local stack stops being a "good enough for overnight" solution and becomes a primary development environment.

**Nobody has published MTP + TurboQuant on Qwen.** If this works, document it thoroughly — the community will want the data point.

---

## Reporting

Write results to `eval/MTP_TURBOQUANT_COMBINED_VALIDATION.md`.

If it works: write to `team-comms/kestrel-to-opus/` with the results table and any observations.

If it doesn't work: write to `team-comms/kestrel-to-opus/` with what failed, which option you tried, and the error messages. We'll figure out the merge path.

Either way: don't switch the production inference backend. Jake approves the numbers first.

— Opus
