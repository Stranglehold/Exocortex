#!/usr/bin/env python3
"""Convert an HF checkpoint to FreeToken FTW using the SERIAL expert-bank builder.

    python freetoken_convert_serial.py --model <hf_dir> --out <ftw_dir>

WHY THIS EXISTS
---------------
`ft checkpoint` picks the parallel bank builder automatically and gives no way to override
it. The parallel reader holds a whole-shard ANONYMOUS buffer (`mmap.mmap(-1, size)`) on top
of the ~bank-sized resident set, and on this box that OOM'd the WSL VM while converting
Ornith-1.5-35B-A3B-NVFP4 (21.8 GB of experts).

FreeToken already knows about this. `load_expert_banks` has a low-RAM guard:

    if parallel and not _host_ram_fits_parallel(model_path):
        logger.warning_rank0("expert banks: low free RAM -> serial build ...")
        parallel = False

with `_host_ram_fits_parallel` returning `avail > sum(shard_sizes) + max(shard_size)`.
For us that was ~50 GB available against ~29.3 GB required, so the guard passed and
parallel ran — then died anyway. The estimate is optimistic for this checkpoint: the banks
are PINNED (non-swappable), the dense weights are still resident from step 1, and the FTW
writer holds its own buffers.

So this does not hack around the design; it makes the library take the path it already has
for exactly this situation, by forcing that guard to report "does not fit". The serial
builder uses a reclaimable file mmap instead of an anonymous buffer, which is the whole
point of the fallback.

`--expert-load serial` would do the same thing, but that flag exists only on `ft serve`,
not on `ft checkpoint`.
"""

import argparse
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="source HF safetensors dir")
    ap.add_argument("--out", required=True, help="output FTW dir")
    ap.add_argument("--moe-backend", default="offload")
    ap.add_argument("--shard-gib", type=float, default=4.0,
                    help="output shard size; smaller = lower writer peak (default 4)")
    ap.add_argument("--allow-parallel", action="store_true",
                    help="do NOT force serial (i.e. reproduce stock behaviour)")
    a = ap.parse_args()

    # Machine-readable progress lines so a supervisor can follow this without parsing tqdm.
    os.environ.setdefault("FREETOKEN_CONVERT_PROGRESS", "1")

    import torch
    from freetoken.moe import expert_banks
    from freetoken.checkpoint.convert import convert_checkpoint

    if not a.allow_parallel:
        original = expert_banks._host_ram_fits_parallel

        def _force_serial(model_path, _orig=original):
            verdict = _orig(model_path)
            print("[serial-convert] stock guard said parallel_fits=%s; forcing SERIAL"
                  % verdict, flush=True)
            return False

        expert_banks._host_ram_fits_parallel = _force_serial
        print("[serial-convert] patched _host_ram_fits_parallel -> always False", flush=True)

    print("[serial-convert] model=%s" % a.model, flush=True)
    print("[serial-convert] out=%s  moe_backend=%s  shard_gib=%s"
          % (a.out, a.moe_backend, a.shard_gib), flush=True)

    idx = convert_checkpoint(
        a.model,
        a.out,
        dtype=torch.bfloat16,
        moe_backend=a.moe_backend,
        shard_limit=int(a.shard_gib * (1 << 30)),
    )
    n = len(idx.get("entries", idx)) if isinstance(idx, dict) else "?"
    print("[serial-convert] DONE — index entries: %s" % n, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
