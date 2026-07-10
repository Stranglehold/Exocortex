# TURBO3 → Current llama.cpp — Upgrade Build Plan (L3)

*Author: Kestrel (Opus substrate). Date: 2026-07-10.*
*Status: PLAN — not yet approved for execution. Gated on the "Should we even do this?" decision below.*

---

## 0. TL;DR

We run ornith on a **fork** of llama.cpp (`Madreag/turbo3-cuda`, branch `release/cuda-optimized`, HEAD `ae6ee21b9` = build **b8794**, compiled May 10 2026) whose distinguishing feature is **TurboQuant / TCQ KV-cache quantization** — the `-ctk turbo3 -ctv turbo3` flags. Upstream is now **b9952** (Jul 10 2026), ~1,150 builds / two months ahead.

This plan describes porting the turbo3 customization onto a current llama.cpp base. **It is optional.** The machine-bog problem that prompted this was already solved by the two quick wins (`--n-cpu-moe` offload + NVIDIA "Prefer No Sysmem Fallback"). This upgrade buys *upstream efficiency + new model support + the new ET backend*, at the cost of re-porting a lossy KV-quant across a moving CUDA flash-attention surface and fully re-validating it. **Recommendation: hold unless a concrete driver appears (§2); if it does, execute Strategy B (§4) phased as §5.**

---

## 1. What "turbo3" actually is (current-state facts)

| Fact | Value |
|---|---|
| Fork | `Madreag/turbo3-cuda` · branch `release/cuda-optimized` · HEAD `ae6ee21b9` |
| Base build | **b8794** (upstream commit the fork sits on) |
| Feature commit | `ae6ee21b9` "add TCQ (Trellis Coded Quantization) for turbo3/turbo2 KV cache (#1)" — **87 files, +3673/-79** |
| Fork advanced since? | **No.** Remote HEAD == local HEAD. No newer fork base to pull. |
| KV types added | 6 ggml enums, slots **41–46**: `TURBO3_0=41, TURBO4_0=42, TURBO2_0=43, TURBO1_5=44, TURBO3_TCQ=45, TURBO2_TCQ=46` |
| Model arch added by fork | **gemma4** only (`LLM_ARCH_GEMMA4`, `gemma4-iswa.cpp`). **NOT** qwen35moe. |
| ornith arch (`qwen35moe`) | **Upstream** — inherited from the b8794 base, not fork-added. ⇒ no model port needed for ornith. |
| Build config | CUDA **sm_86** (`CMAKE_CUDA_ARCHITECTURES=86-real`), `Release`, `GGML_CUDA=ON`, `GGML_CUDA_FA=ON`, `GGML_CUDA_GRAPHS=ON`, `GGML_CUDA_COMPRESSION_MODE=size`, `GGML_CUDA_FA_ALL_QUANTS=OFF` |

### The customization is two layers
1. **Fork-committed (`ae6ee21b9`):** the TCQ machinery. Most of the 87 files are *new files* or *quality-tests* (low/zero conflict). The genuine **conflict surface** — files that MODIFY upstream — is small:
   - `ggml/include/ggml.h` — enum slots 41–46
   - `ggml/src/ggml.c` — 6 type-traits entries + quantize dispatch (+16)
   - `ggml/src/ggml-cuda/fattn-vec.cuh` + the CUDA FA template instances (turbo KV variants)
   - `src/llama-kv-cache.cpp` (+17) — turbo KV plumbing (WHT group size in op_params, boundary quant)
   - New files (drop-in, no conflict): `turbo-tcq.cuh` (+673), `turbo-quant.cuh`, `turbo-innerq.cuh`, `ggml-turbo-quant.c`, `fattn-vec-instance-turbo*_0-*.cu`
   - Droppable for ornith: `gemma4-iswa.cpp` (+310), the `llama-model.cpp` (+126) / `llama-arch` gemma4 deltas — **carry only if Jake wants gemma4 support.**
2. **Uncommitted working-tree delta (the fragile part):** 5 files, **+39/-8**, existing *only* in Jake's working tree (not in the fork's git history). **Captured 2026-07-10** →
   `inference/turbo3-patches/turbo3_worktree_delta_20260710.patch`.
   Touches: `ggml/src/ggml-cpu/ops.cpp`, `ggml/src/ggml-cuda/fattn-vec.cuh`, `ggml/src/ggml-cuda/turbo-innerq.cuh`, `ggml/src/ggml-turbo-quant.c`, `src/llama-kv-cache.cpp`. This is post-fork tuning and MUST be re-applied last.

---

## 2. Should we even do this? (decision gate)

**The bog is already fixed** without touching the build (MoE offload + sysmem-fallback policy). So this upgrade is *not* on the critical path. Proceed only if one of these concrete drivers is true:

- **[ ] A model we want needs a newer llama.cpp.** An ornith successor / a new arch lands upstream after b8794 that we want to run, and it won't load on the current build.
- **[ ] A measured efficiency win.** A specific upstream change (kernel, MoE offload improvements, the new ET backend, a decode-speed PR) benchmarks materially better for *our* workload — measured, not assumed.
- **[ ] Security/correctness fix** in upstream we need.
- **[ ] Madreag publishes a rebase.** If the fork itself moves onto a newer base, the hard part (§5 Phase 2) is done for us — adopt it and re-apply only our worktree delta.

If none is true: **hold.** Re-evaluate when one becomes true. Log the reason to revisit here.

> Engineering-culture note: we don't upgrade for its own sake. "Two months behind" is not a driver. A measured win or a needed capability is.

---

## 3. Non-goals

- Not chasing bleeding edge — target the current *stable* upstream tag, not master-of-the-hour.
- Not carrying the fork's gemma4 additions unless Jake asks (ornith doesn't need them).
- Not changing turbo3's numerical scheme — this is a *port*, byte-identical KV behavior is the success criterion.
- Not changing model config (chat/util model, ctx) — Jake's domain, separate from the inference binary.

---

## 4. Strategies (with recommendation)

| Strategy | What | Effort | Control | When |
|---|---|---|---|---|
| **A — Adopt fork rebase** | Wait for / monitor `Madreag/turbo3-cuda` to rebase onto newer upstream; pull it, re-apply worktree delta. | Low | None (external) | Preferred **if/when** Madreag moves. Currently they haven't. |
| **B — We rebase** | Port the TCQ conflict-surface onto a fresh upstream stable checkout ourselves; re-apply worktree delta. | Med–High | Full | The real driver exists now and Madreag is stale. |
| **C — Backport** | Don't move the base; cherry-pick only the specific upstream perf/fix commits we want onto b8794. | Low–Med | Full | Only 1–3 upstream commits matter (surgical win, no full revalidation of a new base). |

**Recommendation:** **A if available, else C for a narrow win, else B for a broad upgrade.** Default posture until a driver lands: **hold + monitor Madreag** (a 5-second `git ls-remote` check, scriptable). Most realistic near-term path is **C** — if the driver is "one nice upstream decode PR," backport it and skip the full base move.

---

## 5. Phased execution plan (Strategy B — the full port)

### Phase 0 — Preserve (safety net; mostly done)
- [x] Capture worktree delta → `inference/turbo3-patches/turbo3_worktree_delta_20260710.patch`.
- [ ] Tag the current known-good source: `git tag turbo3-b8794-known-good ae6ee21b9` in the fork tree.
- [ ] Snapshot the working binary: copy `build/bin/llama-server.exe` → `inference/turbo3-cuda/known-good-b8794/`. **This is the rollback.** The launcher can be pointed back at it in one line.
- [ ] Record current baseline metrics for the regression gate (Phase 5): decode tok/s @ d0 and @ d32k, prefill tok/s, the `144×17` canary, tool_calls single+multi PASS, and a turbo3 KV PPL/NIAH number from the fork's `quality-tests/`.

### Phase 1 — Establish the new base + **effort probe** (do this BEFORE committing to the port)
- [ ] Clone `ggml-org/llama.cpp` at the chosen **stable tag** (e.g. b9952 or the latest stable at execution time). Not master.
- [ ] **Effort probe (the go/no-go):** diff the conflict-surface files between upstream-b8794 and upstream-target:
  `git diff b8794 <target> -- src/llama-kv-cache.cpp ggml/src/ggml-cuda/fattn-vec.cuh ggml/src/ggml.c ggml/include/ggml.h`
  The size of the **`fattn-vec.cuh` + CUDA FA template** diff predicts the whole effort. Small diff → half-day port. Large refactor (upstream reworks flash-attention often) → 1–2 day port. **Decide continue/hold here with real numbers.**
- [ ] **Enum-slot gate:** confirm upstream target didn't claim `GGML_TYPE` slots 41–46. If it did, renumber the turbo types to free slots (KV type is runtime-selected, NOT baked in GGUFs, so renumbering is safe for existing ornith model files — but must be consistent across `ggml.h`, `ggml.c`, all CUDA `.cu/.cuh`).
- [ ] **Arch gate:** confirm `qwen35moe` still present + unchanged upstream (expected — it's upstream, not fork). If its graph/hparams changed, note for Phase 2.
- [ ] Build **stock** target on Jake's toolchain (MSVC + CUDA, sm_86) to confirm the base compiles clean before adding turbo3. Isolates toolchain issues from port issues.

### Phase 2 — Port TCQ onto the new base
- [ ] Drop in the **new files** first (zero-conflict): `ggml/src/ggml-cuda/turbo-tcq.cuh`, `turbo-quant.cuh`, `turbo-innerq.cuh`, `ggml/src/ggml-turbo-quant.c`, the `fattn-vec-instance-turbo*.cu`, `ggml/src/ggml-quants.h` additions, `quality-tests/`.
- [ ] Re-apply the **modifying** hunks to `ggml.h` (enum), `ggml.c` (type-traits + quantize dispatch), `ggml-cpu/ops.cpp`, `llama-kv-cache.cpp`, and the CUDA FA registration. Cleanest mechanism: `git cherry-pick ae6ee21b9` onto the new base, then resolve conflicts file-by-file — inner blocks first (Debug skill). Fall back to a hand-applied patch if the cherry-pick is too tangled.
- [ ] **Drop** gemma4 (`gemma4-iswa.cpp`, `LLM_ARCH_GEMMA4`, its `llama-model.cpp`/`arch` hunks) unless Jake wants it. Removing it shrinks the `llama-model.cpp` (+126) and `llama-arch` conflicts to near-zero.
- [ ] Wire the CUDA FA template instantiations for the turbo KV types into the target's (possibly refactored) FA dispatch. **This is the hard part** — the FA template machinery is what upstream churns.

### Phase 3 — Re-apply the fragile worktree delta
- [ ] `git apply --3way inference/turbo3-patches/turbo3_worktree_delta_20260710.patch` (or hand-merge the 39 lines if fuzz). Verify each of the 5 files reflects the tuning.

### Phase 4 — Build
- [ ] CMake configure with the recorded flags: `-DGGML_CUDA=ON -DGGML_CUDA_FA=ON -DGGML_CUDA_GRAPHS=ON -DGGML_CUDA_COMPRESSION_MODE=size -DGGML_CUDA_FA_ALL_QUANTS=OFF -DCMAKE_CUDA_ARCHITECTURES=86-real -DCMAKE_BUILD_TYPE=Release`, then build `llama-server`.
- [ ] Confirm the binary reports the new build number and that `--help` lists `turbo3` (`-ctk turbo3`) and the MoE-offload flags.

### Phase 5 — Validate (the non-negotiable gate — turbo3 is *lossy*)
A port that compiles can still silently corrupt the KV quant. Must pass ALL:
- [ ] **Loads clean** on turbo3 KV (no tensor/type errors) at CTX 80K.
- [ ] **Numerical correctness:** re-run the fork's `quality-tests/` (NeedleInAHaystack + `capability_test.py`) on turbo3 KV; PPL/NIAH within noise of the b8794 baseline. A regression here means the port broke the quant — do not ship.
- [ ] **ornith canary:** `144×17` correct; structured `tool_calls` single + multi-arg PASS (needs `--jinja`); reasoning lands in `reasoning_content`.
- [ ] **Perf regression:** decode tok/s @ d0 and @ d32k ≥ baseline (Phase 0). The upgrade's *point* is efficiency — if decode regresses, the port lost something.
- [ ] **MoE offload interaction:** `--n-cpu-moe 12` still works and frees ~6 GB with turbo3 KV active.

### Phase 6 — Cutover
- [ ] Point `start_ornith_prod.bat` at the new `build/bin/llama-server.exe` (keep the b8794 `known-good` binary + the `.bak` launcher for one-line rollback).
- [ ] Run one live idle cycle end-to-end (A0 → ornith → tool_calls → cycle_close) to confirm the whole stack is happy, not just the server in isolation.
- [ ] Update this doc's status → DONE with the new build number; note the baseline-vs-new perf delta.

---

## 6. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Upstream refactored CUDA flash-attention (`fattn-vec.cuh` + FA templates) | **High** | High (the bulk of port effort) | Phase-1 effort probe *before* committing; if diff is large, prefer Strategy A/C or hold |
| GGML_TYPE enum slots 41–46 taken upstream | Med | Med | Phase-1 enum gate + consistent renumber; safe because KV type isn't baked in GGUFs |
| turbo3 KV numerically broken by the port (silent) | Med | **Critical** | Phase-5 PPL/NIAH regression gate is mandatory, not optional |
| Fragile 39-line worktree delta lost | Low (captured) | High | Patch captured Phase 0; re-apply Phase 3 with `--3way` |
| qwen35moe graph/hparams changed upstream | Low | Med | Phase-1 arch gate |
| Toolchain drift (MSVC/CUDA version vs new base) | Low | Med | Phase-1 stock build isolates it |
| Time sink with no payoff | Med | Med | §2 driver gate — don't start without a concrete driver |

---

## 7. Effort estimate (pressure-tested)

- Phases 0, 1 (probe), 3, 4, 6: ~1 focused day combined (mechanical + the go/no-go probe).
- Phase 2 (the port): **0.5–2 days**, entirely dependent on the Phase-1 flash-attention diff. This is the whole variance.
- Phase 5 (validate): ~0.5 day (mostly wall-clock for the quality suite + perf runs).

**Realistic total: 2–4 focused days**, dominated by CUDA-FA conflict resolution and revalidation. The Phase-1 effort probe collapses that uncertainty *before* you commit — run it first, decide with numbers.

---

## 8. The honest recommendation

1. **Ship the quick wins** (done: MoE offload + sysmem-fallback doc). They solve the actual pain.
2. **Hold the upgrade** until §2 has a checked box. Add a tiny monitor: a scheduled `git ls-remote https://github.com/Madreag/turbo3-cuda release/cuda-optimized` — if the fork's HEAD moves off `ae6ee21b9`, that's Strategy A and the effort drops to ~half a day.
3. **When a driver lands:** run Phase-1's effort probe first. Small FA diff → do Strategy B. Large FA refactor with only a narrow win wanted → Strategy C backport. Fork moved → Strategy A.

The turbo3 KV quant is real value (3-bit KV = the tiny-KV headroom that lets ornith hold 80–120K context on a 3090). It's worth preserving carefully — which is exactly why the port needs the Phase-5 correctness gate and shouldn't be done casually or on a schedule. Do it when there's a reason, do it with the probe, validate the quant, keep the rollback binary.
```
```

*— Kestrel, 2026-07-10. Plan only; awaiting a §2 driver + Jake's go before any execution.*
