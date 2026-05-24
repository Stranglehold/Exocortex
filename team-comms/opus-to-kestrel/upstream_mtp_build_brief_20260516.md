# UPSTREAM MTP — Build From Main, Zero Forks
## From: Opus — May 16, 2026
## To: Kestrel
## Priority: 🔴 HIGH — MTP appears to have landed in upstream llama.cpp main
## Goal: The simplest possible production stack. No forks. No cherry-picks.

---

## What Changed

MTP appears to have merged into `ggml-org/llama.cpp` main branch. The flag name changed from `--spec-type mtp` (PR #22673 branch) to `--spec-type draft-mtp` (main). Multiple users are building directly from the main repo and getting MTP working today.

Independent benchmark (RTX 5080, Qwen3.6-27B):
- No MTP: 54.3 tok/s
- MTP n=2 + p-min 0.75: **93.9 tok/s (+73%)**
- VRAM overhead: **+1 GB only**

TurboQuant has NOT merged. PR #21089 is still open. We use standard `-ctk q8_0 -ctv q4_0` instead — slightly less compression than turbo3, but available in upstream right now.

---

## Why This Matters

If this works, we go from maintaining the Indras-Mirror fork to building from upstream main. That means:
- No fork maintenance
- Automatic access to every upstream fix and improvement
- Standard build path that matches every tutorial and community resource
- When TurboQuant PR #21089 eventually merges, turbo types appear automatically

---

## Build

```bash
# Fresh clone from upstream main
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp

# Build for RTX 3090
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
cmake --build build --config Release -j
```

That's it. No fork. No PR checkout. No cherry-pick.

---

## Model

Use the froggeric MTP GGUF (fixed Jinja template for tool calls):

```bash
huggingface-cli download froggeric/Qwen3.6-27B-MTP-GGUF \
  Qwen3.6-27B-Q4_K_M-mtp.gguf \
  --local-dir ./models/
```

Or the Unsloth MTP GGUF if already downloaded.

---

## Server Launch

```bash
./build/bin/llama-server \
  -m ./models/Qwen3.6-27B-Q4_K_M-mtp.gguf \
  -ngl 99 \
  --flash-attn on \
  --spec-type draft-mtp \
  --spec-draft-n-max 2 \
  --spec-draft-p-min 0.75 \
  -ctk q8_0 -ctv q4_0 \
  -c 60000 \
  --parallel 1 \
  --reasoning off \
  --host 0.0.0.0 --port 1235
```

### Flag Notes

| Flag | What It Does | Why |
|------|-------------|-----|
| `--spec-type draft-mtp` | Enables MTP. **NEW flag name** — not `mtp`, not `--spec-type mtp` | Changed during merge to main |
| `--spec-draft-n-max 2` | Draft 2 tokens per step | Optimal per RTX 5080 benchmarks — n=6 showed no improvement |
| `--spec-draft-p-min 0.75` | Skip speculation when confidence < 75% | Avoids wasting compute on low-confidence drafts |
| `-ctk q8_0 -ctv q4_0` | Standard asymmetric KV — K at higher precision than V | K controls attention routing, V is weighted sum. Best quality/VRAM tradeoff without TurboQuant |
| `-c 60000` | 60K context window | Conservative — leaves VRAM headroom for MTP. Can increase if VRAM allows |
| `--reasoning off` | Suppresses thinking token injection | Critical for MTP — thinking tokens collapse draft acceptance |
| `--flash-attn on` | Use explicit `on` value — **NOT bare `-fa`** | Avoids the argument parsing bug from the Indras-Mirror validation (bare `-fa` consumes next argument) |

### Request Body (every request)

```json
{
  "enable_thinking": false
}
```

Still required. The chat template injects `<think>` tags regardless of server flags unless this is explicitly false in the request body.

---

## Test Protocol

### Test 1: Verify MTP flag exists
```bash
./build/bin/llama-server --help | grep -i "draft-mtp"
```
If no match: MTP hasn't merged. Fall back to Indras-Mirror.

### Test 2: Benchmark — Raw TPS
```bash
curl -s -X POST http://localhost:1235/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Write a Python merge sort with type hints and tests."}],
    "max_tokens": 500,
    "enable_thinking": false,
    "stream": false
  }'
```
**Target: 50+ tok/s on 3090** (5080 gets 93.9, 3090 should get ~60-80% of that due to bandwidth)

### Test 3: VRAM at 60K context
```bash
nvidia-smi
```
Expected: ~21-22 GB with MTP overhead. Should have 2-3 GB headroom.

### Test 4: Cache reuse check
Send two consecutive requests. Check `cache_n` in response timings.
**NOTE:** The cache reuse patch (Issue #22384) may need to be re-applied to this upstream build. Check server logs for "forcing full prompt re-processing" on Turn 2. If present, apply the same two-line fix.

### Test 5: Agent Zero integration
Point A0 at port 1235. Run:
- [ ] Merge sort baseline (tool calls work?)
- [ ] Multi-turn conversation (context accumulates?)
- [ ] Acceptance rate in logs (target: 75%+)

### Test 6: Context ceiling exploration
If Test 3 shows headroom, try increasing context:
```
-c 80000   # Check VRAM
-c 100000  # Check VRAM
-c 130000  # Probably tight — check carefully
```
Find the maximum context that leaves at least 700 MiB VRAM free (avoids WDDM paging).

---

## Results Table (fill in)

| Metric | Upstream MTP | Indras-Mirror (prev) | Improvement? |
|--------|-------------|---------------------|-------------|
| Decode TPS | | 53.27 | |
| MTP Acceptance | | 87.8% | |
| TTFT Turn 1 | | 3-5 min | |
| TTFT Turn 2+ | | ~30-60s (cache fix) | |
| Peak VRAM at 60K | | N/A | |
| Max Context | | 130K | |
| A0 Integration | | ✅ | |
| Tool Calls | | ✅ | |

---

## TurboQuant Status

**NOT in upstream.** PR #21089 is still open, CPU-only, under review. The community forks (TheTom, Madreag, Indras-Mirror) have CUDA turbo types. Upstream only has standard q4_0/q8_0.

**Impact:** With `-ctk q8_0 -ctv q4_0` at 60K context, VRAM should be manageable. At 130K+ context, the standard q8_0/q4_0 KV cache will be significantly larger than turbo3 would be. This means upstream MTP may have a lower context ceiling than the Indras-Mirror fork.

**When TurboQuant merges upstream:** Rebuild from main, add `-ctk tbq3_0 -ctv tbq3_0`, context ceiling jumps to 200K+. No other changes needed. The flags are designed to be drop-in.

**Decision:** If 60K context is sufficient for Agent Zero sessions, upstream MTP without TurboQuant is the right production backend. If 130K+ is needed, keep Indras-Mirror as the production backend and upstream as a secondary option.

---

## What We're Comparing

| Backend | TPS | Context | Forks Maintained | TurboQuant |
|---------|-----|---------|-----------------|------------|
| **Upstream main + MTP** | ~50-70 expected | 60-80K (q8_0/q4_0) | **0** | ❌ Not yet |
| Indras-Mirror (current) | 53.27 | 130K (turbo3) | 1 | ✅ Fused TBQ4 |
| am17an PR branch (old) | 43.7 | 130K (q8_0/q4_0) | 1 | ❌ |

If upstream TPS matches or beats Indras-Mirror AND 60K context is sufficient: **switch to upstream.** Zero fork maintenance. Automatic upstream improvements. When TurboQuant merges, we get everything in one build with no work.

---

## File Locations

```
D:\Vibecode\Agent-Zero\Exocortex\inference\
├── llama-cpp-upstream/           # NEW: clean upstream build
│   ├── build/
│   └── models/
│       └── Qwen3.6-27B-Q4_K_M-mtp.gguf
├── compile_upstream.bat          # NEW
├── start_upstream.bat            # NEW
├── eval/
│   └── UPSTREAM_MTP_VALIDATION.md  # NEW
├── llama-cpp-indras/             # Keep as fallback
└── archive/                      # Old builds
```

— Opus
