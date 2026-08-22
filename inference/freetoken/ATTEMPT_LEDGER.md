# FreeToken on this box — attempt ledger

**Purpose:** every configuration tried, what it did, and what that rules out. Written because
we kept re-trying neighbours of the same failure. Append a row before you conclude anything;
if a row already covers your idea, it is not a new experiment.

**Box:** RTX 3090 (24,576 MiB, sm_86) · Windows 10 · WSL2 Ubuntu · driver 596.36 · CUDA 13.2
· FreeToken 0.1.2 in `~/freetoken-env` · host RAM 128 GB, **WSL sees 62 GB**

**Target:** `ornith-ai/Ornith-1.5-35B-A3B-NVFP4` (22 GB on disk, mixed precision —
attention FP8, dense+experts NVFP4)

---

## The two distinct failure modes seen so far

| mode | signature | where |
|---|---|---|
| **A — VRAM OOM** | dies during weight placement, clear error | serve path, GPU-resident attempts |
| **B — hard hang** | `state=D`, `wchan=dxgvmb_send_sync_msg`, **cputicks frozen**, RSS ~976 MB | offload/bank path, WSL2 GPU-PV layer |

Mode B is the important one. `dxgvmb_send_sync_msg` is WSL2's GPU paravirtualisation
(dxgkrnl) making a **synchronous call to the Windows host GPU driver that never returns**.
RSS froze at **976 MB**, which sits right on the **~1.00 GiB cumulative `cudaHostRegister`
ceiling measured directly** with an incremental pin loop (`ulimit -l unlimited` confirmed as
root, so not an rlimit). Ornith's banks need **16.9 GiB** pinned.

FreeToken's own `freetoken/moe/host_banks.py` docstring: the PAGEABLE/LOCKED modes "are
reserved for platforms where the pin quota cannot cover every layer (Windows/WDDM); their
movement paths are **not implemented here**."

---

## Attempts

| # | date | config | result | rules out |
|---|------|--------|--------|-----------|
| 1 | 08-21 | serve raw HF, `--moe-backend offload` | OOM (mode A) | — backend selected but weights never laid out for banks |
| 2 | 08-21 | `--memory-ratio` 0.85 → 0.95 | OOM (mode A) | memory ratio is not the lever |
| 3 | 08-21 | ctx 80K → 32K → 16K | OOM (mode A) | context size is not the lever |
| 4 | 08-21 | `--nvfp4-backend marlin` forced | OOM (mode A) | NVFP4 kernel choice is not the lever; sm_86 supports marlin |
| 5 | 08-21 | `--moe-cache-rate 0.05` | OOM (mode A) | cache rate is not the lever |
| 6 | 08-21 | `--max-running-requests 1` | OOM (mode A) | concurrency is not the lever |
| 7 | 08-21 | `ft checkpoint` → FTW conversion | **OOM'd the WSL VM** (ft RSS 24 G, throughput 380→9.6 MB/s, killed) | parallel bank builder too heavy here |
| 8 | 08-21 | `freetoken_convert_serial.py` (forces library's own serial builder) | not completed | — the flag `--expert-load serial` exists only on `ft serve`, not `ft checkpoint` |
| 9 | 08-22 | `--moe-backend auto` + `--moe-cache-auto`, ctx 80K, ratio 0.85 | **hard hang, mode B, 44 min, zero CPU** | `auto` resolves to the offload/hybrid family = the pinning path |
| 10 | 08-22 | **`--moe-backend cpu`** | **NO HANG** — real CPU use, died in 12 s at weight-load 67 % on `_iter_weights_attn_fp8` → `f.get_tensor()`. VRAM peak **4,859 MiB of 24,576** | mode B defeated; `cpu` DOES bypass the bank/pin path |
| 11 | 08-22 | `--moe-backend cpu` + `PYTORCH_ALLOC_CONF=expandable_segments:False` | identical failure, VRAM peak 4,865 MiB. Override verified applied (engine returns early when the env var is set) | **expandable_segments is NOT the cause** |

| 12 | 08-22 | `--moe-backend cpu` + **CPU-staging shim** (`sitecustomize` wraps `safetensors.safe_open`, loads to CPU then `.to(device)`) | **weight load SOLVED** — got all the way to `phase=expert_banks`, RAM 13→35 G, then `RuntimeError: cudaHostRegister failed for 0.2 GiB`. Clean error, RAM released, no VM OOM | staging path fixed; bank pinning is the real wall |
| 13 | 08-22 | `--moe-backend fused`, ctx 8192, ratio 0.95, shim on | `ValueError: nvfp4 experts require --moe-backend offload or cpu, got 'fused'` | **closes the backend search space — only offload/cpu exist for nvfp4, and both pin** |

**Every attempt 1–9 used a backend in the offload/hybrid family.** `auto` documents itself
(launcher `.sh` line 122) as resolving "a MoE model to the offload family, and to HYBRID."
So all nine attempts are the *same* path, and mode B says that path cannot work here.

### Also established (not attempts, but bounding facts)

- **Qwen3.8-27B is DENSE** — log: *"qwen3_5 is a dense model (no routed experts); ignoring
  MoE settings."* It can never use the offload path; FreeToken was never the right engine
  for it. FP8 (~28 GB) OOM'd at 39 % of shards.
- **Quantisation is correct** — we did get NVFP4 (22 GB, not 36). FP8 ≠ NVFP4 (~1 B/param
  vs ~0.5). But the checkpoint is **mixed**: FP8 attention stays resident regardless of
  expert offload, so "22 GB won't fit 24 GB" was too coarse — the FP8 portion binds first.
- **`model.safetensors.index.json` was missing** from the original snapshot. `ft serve`
  never fetches it; `ft checkpoint` requires it. Fixed via explicit `hf_hub_download`.
- **Killing a mode-B hang worked** — TERM then KILL cleared it; no `wsl --shutdown` needed,
  despite the `D` state. Containers and Docker were unaffected throughout.

---

## MEASURED 2026-08-22 — the pin ceiling, reproduced exactly

`ft bench bw` (ran to completion, exit 0) and a direct torch pin probe on an idle GPU:

```
CPU STREAM read   27.5 GB/s          <- fine
PCIe linear H2D   26.0  D2H 24.3     <- fine
nvfp4 CPU-MoE     19.9 GB/s          <- AVAILABLE
pcie gather       UNAVAILABLE - cudaHostAlloc failed: out of memory
```
```
VRAM free 22.76 / 24.00 GiB          <- not a VRAM problem
single pin 1 / 8 / 64 / 256 MB: OK   <- pinning itself works
cumulative:  CEILING at 1.00 GiB -> CUDA error: out of memory
```

**Exactly 1.00 GiB cumulative, reproducible, on an otherwise idle card.** Ornith's banks
need 16.9 GiB — ~17x short. No flag tunes this. Single allocations up to 256 MB succeed, so
the limit is on the *cumulative* pinned pool, not on any one request.

**The decisive detail everyone (me included) walked past:** for **nvfp4 — our dtype —
CPU-MoE is AVAILABLE at 19.9 GB/s.** Only pcie-gather is dead. `auto` picked `offload`
because *hybrid* was unavailable, and `--help` confirms `auto` only ever resolves within
"the offload family (offload, or hybrid when a `ft bench bw` profile recommends it)".
So `cpu` was never reachable through `auto` — it had to be forced. That is attempt #10.

### Basics checked 2026-08-22

- **`CUDA_HOME` is unset and there is no CUDA toolkit in WSL** (`/usr/local/cuda*` absent,
  `nvcc` not on PATH). torch 2.11.0+cu130 ships its own runtime and
  `torch.cuda.is_available()` is True, so the GPU works — but the **fp8** pcie-gather path
  reports *"Could not find CUDA installation. Please set CUDA_HOME"* because it needs nvcc
  to build a kernel. Real gap; **not** the cause of the pin failure (which fails identically
  for bf16/mxfp4/ds_fp4 with a plain `cudaHostAlloc` OOM).
- `ft` has **no** doctor/env subcommand. Subcommands are: serve, shell, ctl, daemon, launch,
  checkpoint, bench.
- Model snapshot is present at 22 GB — no re-download occurring.
- A mode-B hang **is** killable (TERM then KILL); no `wsl --shutdown` required, and Docker
  plus both containers were unaffected across the whole 44-minute hang.

---

## ROOT CAUSE, ISOLATED 2026-08-22 — it is the pinned pool, and it DEGRADES

Reproduced the failing call standalone (`safetensors.safe_open(device="cuda")` + `get_tensor`
over every tensor), which is what FreeToken does at `weight.py:230/458`.

```
run A (all tensors)      FAILED at #38,903 of 38,909  -> model.visual.merger.linear_fc2.weight (18.9 MB)
                         loaded 9.29 GiB   VRAM free 21.81 GiB
run B (vision skipped)   FAILED after 86,286 allocs   -> lm_head.weight (254.3 MB)
                         loaded 17.79 GiB  VRAM free 21.81 GiB
```

**`free` never moved off 21.81 GiB in either run.** Device VRAM is not the constraint and
never was. Skipping vision got 2.2x further, so **vision is NOT the cause** and neither is an
allocation-count ceiling (86k allocs succeeded).

### The largest tensors

```
1017.1 MB  model.language_model.embed_tokens.weight  BF16  [248320, 2048]
 254.3 MB  lm_head.weight                            U8    [248320, 1024]
  18.9 MB  model.visual.merger.linear_fc2.weight     BF16  [2048, 4608]
```

### The direct pin test — and where my tidy model broke

I predicted embed_tokens (1017 MB) eats a fixed 1024 MB budget leaving ~7 MB, so the next
alloc >7 MB must fail. **Partly wrong**, and the way it is wrong matters:

```
[1] pin 1017 MB:                          OK
[2] +4 / +7 / +19 MB while holding it:    OK      <- 1036 MB total, ABOVE my claimed ceiling
[2] +254 MB while holding it:             FAILED
[3] 254 MB ALONE after releasing all:     FAILED  <- but 256 MB succeeded on a FRESH process
```

So there is **no clean fixed ceiling**. The WSL2 pinned pool **does not properly return freed
memory** — after enough allocation churn, large pinned allocations fail even from an
apparently empty pool. It is fragmentation/leak in the GPU-PV pinned allocator, which is why
the failure point moves with load order rather than sitting at one tensor.

That also retro-explains attempts 1–6: those were logged as "VRAM OOM (mode A)" but VRAM was
almost certainly never the binding resource. `cudaHostAlloc` failure and device OOM report the
**same** `cudaErrorMemoryAllocation` string, and I read it as VRAM.

### Confirmed upstream — this is a known platform limit, not our config

NVIDIA developer forums + microsoft/WSL issues: WSL2 cudaHostAlloc failures start "at roughly
300MB"; Docker-on-WSL2 users report a wall "beyond about 1GB"; limits are lower than native
Windows "due to additional WSL2->WDDM machinery"; and **"the memory limit is managed by
Windows, and the NVIDIA driver doesn't control or set the limit."** No flag reaches it.

### memlock is misconfigured but IRRELEVANT (proven, not assumed)

`ulimit -l` for user `jake` is **65536 KB (64 MB)**, hard limit the same.
`/etc/security/limits.d/99-freetoken-memlock.conf` sets `* memlock unlimited` but never
applies: PAM's `pam_limits.so` is only in `/etc/pam.d/login` and `/etc/pam.d/su`, and
`wsl.exe -- bash` opens no PAM session. systemd IS pid 1 and `DefaultLimitMEMLOCK` is
commented out in `/etc/systemd/system.conf`.

**But it cannot be the cause:** we pinned **1.00 GiB with a 64 MB memlock**. CUDA pinned
memory on WSL2 is not accounted against mlock. Fixing it needs root (sudo wants a password)
and would change nothing. Worth fixing for correctness only.

---

## VERDICT 2026-08-22 — CLOSED. Every path ends in an explicit engine error.

```
fused    -> ValueError: nvfp4 experts require --moe-backend offload or cpu
offload  -> pins expert banks -> cudaHostRegister fails (WSL2 ~1 GiB, needs 16.9)
cpu      -> same bank pinning -> cudaHostRegister failed for 0.2 GiB
```
And swallowing the pin failure does not help — `offload_cache.set_bank_sources` explicitly:
```python
if any(r != HostResidency.PINNED.value for r in residency):
    raise NotImplementedError("non-pinned host bank layers need platform-specific
        movement paths that are not implemented; only pinned layers are served")
```
The pageable movement paths genuinely do not exist. Going further is not a workaround, it is
implementing FreeToken's missing WSL/WDDM support. **Stop here.**

## WHAT WAS ACTUALLY SOLVED (keep this — it is reusable)

`inference/freetoken/sitecustomize_cpu_stage.py` — wraps `safetensors.safe_open` so tensors
load to CPU and then `.to(device)`, using a plain pageable cudaMemcpy instead of safetensors'
pinned CUDA path. Enabled with `FT_CPU_STAGE=1` + `PYTHONPATH`. **Verified end to end:**

```
before: FAILED at #38,903 of 38,909 (visual.merger) / after skipping vision, at lm_head
after : ALL SHARDS LOADED OK — 94,396 tensors, 21.80 GiB
```

This is the fix for the *weight-loading* half and it works. It is worth keeping for native
Linux, another engine hitting the same wall, or a future FreeToken that implements pageable
banks. It does not and cannot fix expert-bank pinning.

---

## Untried levers (the actual remaining search space)

| lever | why it might matter | status |
|---|---|---|
| `--moe-backend cpu` | ~~untried~~ | **DONE #10 — works, defeats the hang; blocked further downstream** |
| `--moe-backend fused` | all-GPU; would fail on VRAM, but fails *cleanly* and confirms mode A vs B | untried |
| `--expert-load serial` | exists on `ft serve` (not `ft checkpoint`); lower peak during bank build | untried |
| **tiny model end-to-end** | we have never proven FreeToken serves *anything* on this box | superseded — `ft bench bw` exercised CUDA + PCIe + host alloc directly and gave a sharper answer |

---

## Basics not yet verified

Listed because assuming these is how we burn hours. Check before the next round of flags.

1. **Has FreeToken ever served any model here?** Nine attempts, all on one 35 B MoE. A ~0.5 B
   dense model proves install + CUDA + GPU-PV + HTTP in about a minute. If that fails, the
   problem was never Ornith.
2. Snapshot completeness — all shards present, not just total size.
3. Does `ft` ship a doctor/env-check subcommand we never ran?
4. Is there a known FreeToken/WSL2 issue upstream? Never searched.

---

*Append rows. Do not re-run a row that already exists — check the table first.*
