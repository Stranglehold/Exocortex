"""Route safetensors tensor loads through CPU instead of straight to CUDA.

WHY: safetensors' device="cuda" path allocates via CUDA's pinned/staging machinery.
On WSL2 that pool is capped (~1 GiB) AND degrades with churn - large allocations start
failing even from an apparently empty pool. Measured: a 254 MB pinned alloc failed alone
after release, on a process where 256 MB had succeeded minutes earlier.

Loading to CPU (pageable) and then .to(device) uses a plain synchronous cudaMemcpy, which
needs no pinned staging at all. Slower per tensor; does not touch the broken path.

Fully reversible: delete this file / drop it from PYTHONPATH.
"""
import os

if os.environ.get("FT_CPU_STAGE") == "1":
    try:
        import safetensors
        import torch

        _orig_safe_open = safetensors.safe_open

        class _CpuStagedOpen:
            """Proxy that mimics safe_open's handle but stages through CPU."""

            def __init__(self, *args, **kwargs):
                self._target = str(kwargs.pop("device", "cpu"))
                kwargs["device"] = "cpu"
                self._inner = _orig_safe_open(*args, **kwargs)
                self._entered = None

            def __enter__(self):
                self._entered = self._inner.__enter__()
                return self

            def __exit__(self, *exc):
                return self._inner.__exit__(*exc)

            def _h(self):
                return self._entered if self._entered is not None else self._inner

            def get_tensor(self, name):
                t = self._h().get_tensor(name)
                if self._target != "cpu":
                    t = t.to(self._target)          # pageable -> device, no pinning
                return t

            def keys(self):
                return self._h().keys()

            def metadata(self):
                return self._h().metadata()

            def get_slice(self, name):
                return self._h().get_slice(name)

            def __getattr__(self, item):
                return getattr(self._h(), item)

        safetensors.safe_open = _CpuStagedOpen
        print("[ft-cpu-stage] safetensors.safe_open patched: CPU staging enabled", flush=True)
    except Exception as exc:  # never break startup
        print("[ft-cpu-stage] patch FAILED (%s) - continuing unpatched" % exc, flush=True)
