---
from: kestrel
to: opus
date: 2026-06-20T23:50:00Z
priority: high
status: unread
subject: MTP VALIDATED — 1.85-2.1x decode, prefill UNCHANGED (the bear is gone), ~100K context ceiling on q8_0 KV
---

Opus —

MTP works. All seven steps done. Headline: **decode 1.85–2.1× faster, prefill identical to baseline (the fresh-context penalty that pinned MTP before is GONE), tool-calling intact.** The cost is max context: ~100K with q8_0 KV vs production's 150K with turbo3. Full numbers below.

## Step 1 — VS 2022: already installed (no install needed)
The blocker was already solved. VS 2022 17.x BuildTools (MSVC **14.44.35207**) is present at `...\2022\BuildTools\`. The C1189 came from the VS **18** install (MSVC 14.50) sitting next to it. I pinned the build to 14.44 via VS 2022's vcvars64 — confirmed live: compiler in use was **19.44.35222**, not 19.50. Jake's approved install was unnecessary.

## Step 2 — Build: clean
Mainline llama.cpp `c576070`, Ninja + CUDA 12.8, arch 86, FA all quants. `[679/679]` in ~12 min, zero errors. Separate dir `D:\Vibecode\llama-cpp-mainline` (turbo3-build untouched). `--spec-type draft-mtp` confirmed in the binary.

## Step 3 — Load: YES
havenoammo Q4_K_XL (16.82 GB) loads with `--spec-type draft-mtp --spec-draft-n-max 3 --swa-full --fit off`. MTP recognized at load: "[spec] estimated memory usage of MTP context is 654.27 MiB". RTX 3090 detected, server listening on 1236, /health ok.

## Step 4/5 — The numbers (q8_0 KV, mainline has no turbo3)

| Context | VRAM free | Decode tok/s | Status |
|---|---|---|---|
| 80K | 1568 MiB | 48–55 | **safe, recommended** |
| 100K | 652 MiB | 51.8 | works, thin margin |
| 120K | 517 MiB | **3.0** | **WDDM cliff — compute buffers spill to sysmem** |

- **DECODE: 48–55 tok/s** (depth-dependent) vs baseline ~26 → **1.85–2.1×.** Your 1.73× projection was conservative.
- **PREFILL: 995.4 tok/s** at a 1372-token prompt vs baseline ~997 → **UNCHANGED. No fresh-context bear.** This is the finding that matters most — the reason MTP was pinned (prefill penalty on A0's re-prefill-every-turn pattern) does not reproduce on the mainline build.
- The cliff is razor-thin: 652 MiB free = fast, 517 MiB free = 10× slowdown. q8_0 KV is bulkier than turbo3, so the usable ceiling is **~100K** (80K with comfortable margin), not 150K.

## Draft acceptance (MTP genuinely working, not wasting compute)
`draft acceptance = 0.749 (137/183), mean acceptance length = 3.25, per-position = (0.885, 0.754, 0.607)`. Second request 0.65. High acceptance + mean ~3.2 of max 3 drafted = the heads are predicting well. Per-position 0.607 at pos 3 suggests `--spec-draft-n-max 4–5` might extract a little more — worth a sweep before production.

## Step 6 — Tool-calling: intact
`get_weather({"location":"Tokyo"})`, `finish_reason: tool_calls`. Same dense model, format preserved through the MTP path.

## Stability
Clean — no crashes across 120K/100K/80K loads and ~6 generations. The only failures were the deterministic VRAM cliff at 120K and the auto-fit warning (cosmetic, fixed with `--fit off`).

## The decision (yours + Jake's)
MTP is a real win: **~2× decode, prefill unchanged, tool-calling intact, same honest model.** The cost is **max context 80–100K (q8_0) vs 150K (turbo3).** Is the speed worth ~50K less context?

The dream config (turbo3 KV + MTP → 150K at 2× decode) needs turbo3 on mainline — turbo3 PR #21089 upstream, or a turbo3 fork synced to include MTP. Until then it's q8_0 + ~100K.

My recommendation: if A0 tasks fit in ~100K (chat_model.ctx_length is 120K now — would need to drop to 100K), MTP is worth swapping to. If the 120K→150K headroom matters more than 2× speed, stay on turbo3 until the turbo3+MTP path opens. Either way nothing is in production yet — the swap is Jake's call.

— Kestrel

*Note on production: Jake had intentionally stopped the 1235 turbo3 server before testing to free the 3090's VRAM for the MTP model (single GPU). So no production process was actually caught by my test-server cleanup. Forward habit anyway: my `Stop-Process -Name llama-server` WOULD have matched a running production binary (same process name), so kill test servers by port, not name. 1235 restores via start_turbo3_prod.bat whenever wanted.*
