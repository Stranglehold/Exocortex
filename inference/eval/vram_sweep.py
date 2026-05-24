#!/usr/bin/env python3
"""
VRAM + Throughput Sweep
=======================
Sends prompts of increasing token length to a running llama-server,
records peak VRAM (MiB) and decode tok/s at each context length.

Useful for:
  - Finding the VRAM cliff where inference offloads to CPU
  - Comparing Config C (no MTP) vs Config A (MTP n=3) VRAM overhead
  - Validating KV cache scaling assumptions

Usage:
    # Default sweep against MTP server (port 1235):
    python vram_sweep.py

    # Sweep against TurboQuant server (port 1234):
    python vram_sweep.py --port 1234

    # Custom context steps:
    python vram_sweep.py --steps 5000,20000,50000,100000,130000

    # Fewer generated tokens per step (faster sweep):
    python vram_sweep.py --max-tokens 50

The script keeps max_tokens small (default 80) because we care about
KV cache fill during prefill, not generation length. Lower max_tokens
means faster sweep with the same VRAM data.
"""

import argparse
import json
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error

# Default context lengths to test (tokens).
# Chosen to cover the range from "trivial" to "near model max".
DEFAULT_STEPS = [2_000, 5_000, 10_000, 20_000, 40_000, 60_000, 80_000, 100_000, 120_000, 130_000]

# Filler text used to pad prompts to target token length.
# Plain prose, ~4 chars/token. Model sees it as a summarisation task.
_FILLER = (
    "The development of artificial intelligence has progressed rapidly over the past decade. "
    "Language models have grown from simple pattern matchers to sophisticated reasoning systems "
    "capable of engaging in complex, multi-step problem solving across diverse domains. "
    "These systems are now deployed in production environments where reliability and performance "
    "are critical requirements that must be carefully measured and validated. "
    "Researchers continue to explore new architectures, training techniques, and deployment "
    "strategies that improve efficiency without sacrificing capability. "
)


# ── VRAM polling ──────────────────────────────────────────────────────────────

def _get_vram_mib() -> int:
    """Return current GPU memory usage in MiB, or -1 on failure."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        return int(r.stdout.strip().split("\n")[0])
    except Exception:
        return -1


def _poll_vram(stop: threading.Event, peak: list) -> None:
    """Background thread: poll nvidia-smi every 500 ms, update peak[0]."""
    while not stop.is_set():
        v = _get_vram_mib()
        if v > peak[0]:
            peak[0] = v
        time.sleep(0.5)


# ── Prompt construction ───────────────────────────────────────────────────────

def _build_prompt(target_tokens: int) -> str:
    """
    Build a prompt that will consume approximately target_tokens of KV cache.
    Uses ~4 chars/token as the approximation for English prose.
    Wraps filler in a summarisation task so the model produces a short output.
    """
    chars = target_tokens * 4
    body = (_FILLER * (chars // len(_FILLER) + 1))[:chars]
    return (
        f"Summarise the following passage in exactly one sentence:\n\n"
        f"{body}\n\n"
        f"One-sentence summary:"
    )


# ── Inference ─────────────────────────────────────────────────────────────────

def _infer(port: int, prompt: str, max_tokens: int) -> dict | None:
    """POST to /v1/chat/completions, return the timings dict or None on error."""
    payload = json.dumps({
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        f"http://localhost:{port}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            return json.loads(resp.read()).get("timings", {})
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}", end="")
    except Exception as e:
        print(f"ERR({e})", end="")
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="VRAM + throughput sweep across context lengths.")
    ap.add_argument("--port",       type=int, default=1235,
                    help="llama-server port (default 1235 for MTP build, 1234 for TurboQuant)")
    ap.add_argument("--max-tokens", type=int, default=80,
                    help="Tokens to generate per step (default 80 - keep small for speed)")
    ap.add_argument("--steps",      type=str, default=None,
                    help="Comma-separated context lengths, e.g. 5000,20000,80000,130000")
    ap.add_argument("--output",     type=str, default=None,
                    help="File to write a copy of all output alongside stdout")
    args = ap.parse_args()

    # Tee stdout to file if --output specified
    if args.output:
        class _Tee:
            def __init__(self, f): self._f = f
            def write(self, s):
                sys.__stdout__.write(s)
                self._f.write(s)
            def flush(self):
                sys.__stdout__.flush()
                self._f.flush()
        sys.stdout = _Tee(open(args.output, "w", encoding="utf-8"))

    steps = DEFAULT_STEPS
    if args.steps:
        steps = sorted(int(x.strip()) for x in args.steps.split(","))

    baseline_vram = _get_vram_mib()

    print()
    print(f"  VRAM + Throughput Sweep")
    print(f"  Port: {args.port}  |  Max gen tokens/step: {args.max_tokens}")
    print(f"  Baseline VRAM (server idle): {baseline_vram:,} MiB")
    print(f"  Steps: {[f'{s//1000}K' for s in steps]}")
    print()
    header = f"  {'Ctx (K tok)':>11} | {'Actual toks':>11} | {'Peak VRAM':>10} | {'KV delta':>9} | {'Prefill t/s':>11} | {'Decode t/s':>10} | Note"
    print(header)
    print("  " + "-" * (len(header) - 2))

    results = []

    for target in steps:
        prompt = _build_prompt(target)
        print(f"  {target/1000:>10.1f}K | ", end="", flush=True)

        # Start VRAM poller
        peak = [baseline_vram]
        stop = threading.Event()
        t = threading.Thread(target=_poll_vram, args=(stop, peak), daemon=True)
        t.start()

        timings = _infer(args.port, prompt, args.max_tokens)

        stop.set()
        t.join(timeout=2)

        if timings is None:
            print(f"{'?':>11} | {'—':>10} | {'—':>9} | {'—':>11} | {'—':>10} | REQUEST FAILED")
            results.append((target, None, None, None, None))
            continue

        actual_toks  = timings.get("prompt_n", target)
        peak_vram    = peak[0]
        kv_delta     = peak_vram - baseline_vram
        prefill_tps  = timings.get("prompt_per_second", 0.0)
        decode_tps   = timings.get("predicted_per_second", 0.0)

        note = ""
        if peak_vram >= 24_000:
            note = "!! VRAM at limit"
        elif peak_vram >= 23_000:
            note = "!! VRAM high"
        if decode_tps > 0 and decode_tps < 10:
            note = (note + " !! CPU offload likely").strip()

        print(
            f"{actual_toks:>11,} | "
            f"{peak_vram:>9,} | "
            f"{kv_delta:>+9,} | "
            f"{prefill_tps:>11.1f} | "
            f"{decode_tps:>10.2f} | "
            f"{note}"
        )
        results.append((target, peak_vram, kv_delta, prefill_tps, decode_tps))

    # Summary
    print()
    valid = [(ctx, dec) for ctx, *_, dec in results if dec is not None and dec > 0]
    if len(valid) >= 2:
        ctx0, tps0 = valid[0]
        ctx1, tps1 = valid[-1]
        print(f"  Decode tok/s at {ctx0//1000}K ctx: {tps0:.2f}")
        print(f"  Decode tok/s at {ctx1//1000}K ctx: {tps1:.2f}")
        if tps0 > 0:
            change_pct = (tps1 - tps0) / tps0 * 100
            print(f"  Change across sweep: {change_pct:+.1f}%")
    print()

    # Predict overflow point from KV scaling (if we have enough data)
    vram_deltas = [(ctx, kv) for ctx, _, kv, *_ in results if kv is not None and ctx > 0]
    if len(vram_deltas) >= 2:
        # Linear fit: KV delta ≈ rate * ctx_tokens
        avg_rate = sum(kv / ctx for ctx, kv in vram_deltas if ctx > 0) / len(vram_deltas)
        free_for_kv = 24_576 - baseline_vram
        predicted_max_ctx = int(free_for_kv / avg_rate) if avg_rate > 0 else 0
        print(f"  KV cache rate: ~{avg_rate * 1000:.3f} MiB per 1K tokens")
        print(f"  Predicted VRAM overflow at: ~{predicted_max_ctx:,} tokens ({predicted_max_ctx//1000}K)")
    print()


if __name__ == "__main__":
    main()
