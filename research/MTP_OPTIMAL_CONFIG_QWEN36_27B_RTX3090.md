# MTP / Speculative-Decoding — Optimal Config for Qwen3.6-27B on RTX 3090
## Author: Kestrel — 2026-05-18
## Sources: project empirical record (authoritative for this rig) + llama.cpp official docs + external benchmarks (hypothesis-only)

---

## The reframe that has to come first (honest, load-bearing)

You asked to optimize the MTP flags. The project's *own* measured data says
that is **second-order for the problem we actually have**:

- MTP accelerates **decode** only. It does nothing for **prefill**.
- The latency investigation (this session) proved the ~8-min/turn cost is a
  per-turn **cold prefill of a ~15K-token prompt**, not decode speed.
- `mtp_live_eval_20260513.md` already concluded this in the project's own words:
  *"MTP's generation performance is real (43.7 vs 26.9 tok/s)… the problem is
  upstream of generation [prefill dominates wall time]."*

So: tuning `--spec-draft-n-max` / `p-min` will make a turn's *generation* phase
faster, but the wall-clock pain is prefill. **The highest-value inference-config
lever for latency is `--cache-reuse`, not MTP tuning** (detail in §4). MTP
tuning is still worth doing — it's free speed on the decode phase and it's what
you asked — but I'd be hiding the ball if I optimized n-max without saying the
n-max knob isn't where the 8 minutes live.

---

## 1. High-confidence config — measured on THIS rig, do not re-litigate

| Flag | Value | Evidence (project-measured, RTX 3090 / Qwen3.6-27B) |
|------|-------|------|
| `--reasoning off` | **on (suppress)** | **Single biggest lever.** Indras validation: 73.3% → **87.8% acceptance** with thinking suppressed. Thinking tokens collapse draft acceptance. Non-negotiable. (Server-level only — does NOT disable the model's reasoning per Jake's 2026-05-16 decision; suppresses the empty-tag injection that wrecks the draft.) |
| `-ctk q8_0 -ctv q4_0` | required | q8_0/q8_0 **OOMs the MTP-head buffer** at our context. V→q4_0 saves ~1,016 MiB → MTP head loads. Confirmed in DFlash/MTP/Indras validations. Asymmetric is also correct on quality grounds (K drives attention routing, V is a weighted sum). |
| `--parallel 1` | required | MTP path is single-slot; the entire Exocortex architecture assumes it. |
| `--batch-size` | **≤ 512** | 2048 → compute-buffer WDDM paging → collapse. 512 fixed it (`mtp_latency_report`). Do not raise on a 24 GB card. |
| context | **~60K (Q4_K_S)** | Hard VRAM cliff, not a free dial. Q4_K_S@60K → ~1058 MiB free, stable. 80K → ~710 MiB, stable, 43.7 tok/s. >80–130K → ~100–270 MiB → **WDDM pages → 4–32 tok/s collapse**. Context size is a latency *cliff* on this rig. |
| quant | **Q4_K_S** | 15.0 GB vs Q4_K_XL 16.5 GB → the headroom that keeps WDDM from paging. Q4_K_XL ruled out permanently at our contexts. |
| `--spec-type` | `draft-mtp` | Upstream-main flag name (was `mtp` in the PR branch / Indras). `start_mtp.bat` still uses the old `mtp` — migrate per `upstream_mtp_build_brief`. |

## 2. The genuinely-untested knobs — a real optimization, never swept on the 3090

Every prior 3090 MTP test fixed **n-max=3 with NO explicit p-min**. The official
llama.cpp defaults are `n-max=16`, `p-min=0.75`, `n-min=0`, `p-split=0.10`. So
"our" config has been one point in a space we never explored. External data
conflicts on the optimum (RTX 5080 brief: n=2 best; dredyson blog: dense n=5,
MoE n=3) — **conflicting external numbers mean only a 3090 sweep settles it.**

Recommended sweep (decode tok/s + acceptance %, fixed prompt, `-rea off`,
Q4_K_S@60K, batch 512):

| Axis | Values to test | Why |
|------|----------------|-----|
| `--spec-draft-n-max` | 2, 3, 4, 5 | Project found 3 best *without* p-min; 5080 found 2; dense-model guidance says 5. Card/build dependent — measure. |
| `--spec-draft-p-min` | 0.60, 0.75 (default), 0.85 | Never varied on this rig. 0.75 default is the external recommendation for n≤5; 0.85 for higher n. Higher p-min = skip low-confidence drafts = less wasted verify compute. |
| `--spec-draft-n-min` | 0, 1 | Untested. Forcing a 1-token floor can avoid speculation thrash on low-confidence regions. |

9 core configs (n × p-min) + 2 n-min probes. Each ~2 min (decode benchmark, not
a full agent turn). The acceptance × n-max product is what matters: high
acceptance at n=2 can beat lower acceptance at n=5. Qwen3.6-27B is a hybrid
(GatedDeltaNet recurrent + 16 attn layers), not the 35B-A3B MoE — closer to the
"dense" guidance, but our own recurrent-layer behavior is unique → measure.

**Prediction (to be falsified):** on the 3090, prefill-bound and VRAM-tight, the
decode-phase delta between n=2 and n=5 is real but small in *wall-clock* terms
vs prefill. Expect n=3–4 + p-min 0.75 near-optimal; the sweep's value is
confirming, not transforming.

## 3. New flags surfaced (verify in target build's `--help` before use)

- `--kv-unified` — reduces KV fragmentation at large ctx. Low risk, plausibly
  helps the WDDM-headroom situation. Test.
- `--no-mmap --mlock` — pins model in RAM, prevents OS swap. Directly relevant
  to our WDDM-paging history. Test (watch total RAM).
- `GGML_CUDA_GRAPH_OPT=1` (env) — CUDA-graph launch-overhead reduction. Free if
  it works on this build.
- `--spec-draft-p-split 0.10` (default) — speculative split probability; a
  further knob if the n-max/p-min sweep plateaus.

## 4. `--cache-reuse` — the actual latency lever (cross-finding)

The Indras validation explicitly recorded **`cache_n=0` across identical
back-to-back requests — "this fork explicitly [does not reuse prefix KV]."**
That is the *exact* mechanism behind the per-turn cold-prefill cost the latency
investigation isolated. `--cache-reuse N` is a llama.cpp **server** arg (not in
`speculative.md`; lives in server/common args) that reuses matching KV prefix
chunks across requests with a minimum chunk size N.

This is the single highest-value inference-config item, and it's untested here:

1. In the target build, run `llama-server --help | grep -i cache-reuse` to
   confirm support (the Indras fork lacked it; **upstream main may have it**).
2. If present: launch with `--cache-reuse 256` (start conservative), then
   re-run the 2-turn latency test from the latency investigation. Success =
   turn-2 `cache_n` > 0 and turn-2 prefill ≪ turn-1.
3. This stacks with the prompt-shrink (#1, ~13% already banked) and is
   independent of MTP tuning. MTP tuning + cache-reuse + prompt-shrink are
   three orthogonal levers; **cache-reuse is the one that attacks the measured
   bottleneck.**

## 5. Recommended action order

1. **Confirm `--cache-reuse` in the upstream build** — potentially the rocket
   ship for the real bottleneck (prefill), independent of MTP. (operator/build —
   needs the upstream MTP build the consolidated brief specifies.)
2. **Migrate flag name** `--spec-type mtp` → `draft-mtp` when on upstream.
3. **Run the n-max × p-min sweep** (§2) — free decode-phase speed, settles the
   conflicting external guidance with our own numbers. I can build + run this
   sweep harness (it's a benchmark script against the server — in-domain,
   reversible, no agent/config risk) once the upstream build is up.
4. Keep §1 fixed — measured, do not re-litigate.

---

## Sources

Project-internal (authoritative for this rig): `inference/eval/MTP_BUILD_VALIDATION.md`,
`MTP_TURBOQUANT_COMBINED_VALIDATION.md`, `INDRAS_BUILD_VALIDATION.md`,
`DFLASH_VS_MTP_SERVER_COMPARISON.md`; `team-comms/.../mtp_latency_report_20260514.md`,
`mtp_live_eval_20260513.md`, `mtp_results_20260510.md`,
`upstream_mtp_build_brief_20260516.md`, `consolidated_action_brief_20260516.md`.

External (hypothesis-only, not this rig):
- [llama.cpp speculative.md (official defaults)](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md)
- [MTP llama.cpp Qwen3.6-27B advanced config guide — dredyson.com](https://dredyson.com/how-i-mastered-mtp-speculative-decoding-with-llama-cpp-on-qwen3-6-27b-the-complete-advanced-configuration-guide-that-pros-dont-want-you-to-know/)
- [qwen3.6 speculative decoding RTX 3090 benchmark (thc1006)](https://github.com/thc1006/qwen3.6-speculative-decoding-rtx3090)
- [llama.cpp MTP/spec llama-bench feature request #22947](https://github.com/ggml-org/llama.cpp/issues/22947)

— Kestrel
*MTP tuning is free decode speed and worth doing. But the project's own data
says the 8 minutes are in prefill, and the lever for prefill is `--cache-reuse`,
not `--spec-draft-n-max`. Optimizing the flag you asked about without saying
that would be the instrumentalist lying to the instrument.*
