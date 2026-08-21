#!/usr/bin/env python3
"""Live view of what llama-server is actually doing, including while generating.

WHY THIS EXISTS
On 2026-08-21 an hour went into diagnosing a server that had silently fallen off the
GPU. The evidence that settled it was process counters -- 71.4 CPU-seconds per 10s wall
against 10% GPU utilisation -- because llama.cpp's own output went to a console nobody
was reading and there was no log file. The startup line states offload plainly. This
tool exists so that is never inferred again.

WHAT IT SHOWS (polls /metrics and /slots, both enabled in start_qwen38_prod.bat)
  state      slot idle / processing, and how many requests are deferred (queued)
  ctx        KV cache tokens in use and the ratio against the window
  speed      prompt tokens/s (prefill) and predicted tokens/s (generation)
  gpu/cpu    GPU utilisation, VRAM free, and llama-server's CPU burn

THE ALARM WORTH HAVING
A 27B running on CPU looks like: high CPU seconds, low GPU utilisation, VRAM near
full. That combination is flagged explicitly, because on the night it happened every
individual number looked survivable and only the combination was damning.

Deliberately NOT keyed on a substring appearing in the prompt or log text -- a check
that fires on a token present in normal output is worse than no check (playbook, and
wiring seam #30's cousin).

Usage:
    python scripts/watch_llama.py                  # defaults to :1235, 5s interval
    python scripts/watch_llama.py --port 1235 --interval 2
    python scripts/watch_llama.py --once           # single sample, for scripts
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request

PROM_KEYS = {
    "llamacpp:prompt_tokens_seconds": "prompt_tps",
    "llamacpp:predicted_tokens_seconds": "gen_tps",
    "llamacpp:kv_cache_usage_ratio": "kv_ratio",
    "llamacpp:kv_cache_tokens": "kv_tokens",
    "llamacpp:requests_processing": "processing",
    "llamacpp:requests_deferred": "deferred",
    "llamacpp:n_past_max": "n_past_max",
}


def fetch(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return "ERR:%s" % type(e).__name__


def parse_prom(text):
    out = {}
    if text.startswith("ERR:"):
        return out
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.rsplit(" ", 1)
        if len(parts) != 2:
            continue
        name = parts[0].split("{")[0].strip()
        if name in PROM_KEYS:
            try:
                out[PROM_KEYS[name]] = float(parts[1])
            except ValueError:
                pass
    return out


def gpu_sample():
    """GPU utilisation and free VRAM. Returns (util_pct, free_mib) or (None, None)."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        util, free = r.stdout.strip().splitlines()[0].split(",")
        return int(util), int(free)
    except Exception:
        return None, None


def cpu_seconds():
    """llama-server CPU seconds consumed so far, or None."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$p=Get-Process llama-server -ErrorAction SilentlyContinue;"
             " if($p){ '{0}' -f $p.CPU } else { '' }"],
            capture_output=True, text=True, timeout=15,
        )
        v = r.stdout.strip()
        return float(v) if v else None
    except Exception:
        return None


def sample(port):
    m = parse_prom(fetch("http://127.0.0.1:%d/metrics" % port))
    slots_raw = fetch("http://127.0.0.1:%d/slots" % port)
    slots = None
    if not slots_raw.startswith("ERR:"):
        try:
            slots = json.loads(slots_raw)
        except Exception:
            slots = None
    util, free = gpu_sample()
    return m, slots, util, free, slots_raw


def describe_slots(slots):
    if not isinstance(slots, list):
        return "unavailable"
    busy = sum(1 for s in slots if isinstance(s, dict) and s.get("is_processing"))
    return "%d/%d busy" % (busy, len(slots))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=1235)
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()

    print("watching llama-server on :%d  (Ctrl-C to stop)" % a.port)
    print("%-8s %-12s %-22s %-24s %s"
          % ("time", "slots", "ctx", "speed", "gpu / cpu"))

    prev_cpu, prev_t = cpu_seconds(), time.time()
    first = True
    while True:
        if not first:
            time.sleep(a.interval)
        first = False

        m, slots, util, free, slots_raw = sample(a.port)
        now = time.time()
        cpu_now = cpu_seconds()
        cpu_rate = None
        if cpu_now is not None and prev_cpu is not None and now > prev_t:
            cpu_rate = (cpu_now - prev_cpu) / (now - prev_t)
        prev_cpu, prev_t = cpu_now, now

        if not m and slots is None:
            print("%-8s server not answering /metrics or /slots (%s)"
                  % (time.strftime("%H:%M:%S"), slots_raw[:40]))
            if a.once:
                return 1
            continue

        ctx = "kv %s tok (%.0f%%)" % (
            int(m.get("kv_tokens", 0)), 100 * m.get("kv_ratio", 0.0))
        speed = "prefill %.0f t/s  gen %.1f t/s" % (
            m.get("prompt_tps", 0.0), m.get("gen_tps", 0.0))
        gpucpu = "%s%% util, %s MiB free" % (
            util if util is not None else "?", free if free is not None else "?")
        if cpu_rate is not None:
            gpucpu += ", cpu %.1f cores" % cpu_rate

        deferred = int(m.get("deferred", 0))
        line = "%-8s %-12s %-22s %-24s %s" % (
            time.strftime("%H:%M:%S"), describe_slots(slots), ctx, speed, gpucpu)
        print(line)
        if deferred:
            print("         %d request(s) DEFERRED - queued behind the active slot"
                  % deferred)

        # The combination that cost an hour on 2026-08-21. Any one of these alone is
        # survivable; together they mean the model is executing on CPU.
        if (cpu_rate is not None and cpu_rate > 3.0
                and util is not None and util < 30
                and free is not None and free < 1000):
            print("         !! LIKELY CPU OFFLOAD: cpu %.1f cores, gpu %d%%, only %d MiB"
                  " VRAM free. A 27B on CPU prefills a small prompt in tens of minutes."
                  % (cpu_rate, util, free))
            print("         !! check the server log's load-time offload lines before"
                  " blaming the client.")

        if a.once:
            return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
