#!/usr/bin/env python3
"""
Cache Metrics Report — consumer for _02_cache_metrics_logger's JSONL ledger.
Computes prompt-cache hit ratio and an estimated cost per model.

Run (in container):  /opt/venv-a0/bin/python3 cache_metrics_report.py [ledger.jsonl]

Prices are the DEEPSEEK spec estimates ($/M tokens) from specs/DEEP_TOKEN_OPTIMIZATION.md
— labelled as estimates, not billed truth. The cache hit/miss split IS billed truth
(straight from DeepSeek's usage object).
"""
import json
import sys

LEDGER = "/a0/usr/Exocortex/cache_metrics.jsonl"

PRICES = {  # $/M tokens (spec estimates)
    "deepseek-v4-pro":   {"hit": 0.0145, "miss": 1.74, "out": 3.48},
    "deepseek-v4-flash": {"hit": 0.003,  "miss": 0.20, "out": 0.60},
}


def main(path: str = LEDGER) -> None:
    agg: dict = {}
    n = 0
    try:
        f = open(path, encoding="utf-8")
    except FileNotFoundError:
        print(f"No ledger at {path}")
        return
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            u = rec.get("usage")
            if not u:
                continue  # skip diagnostic / non-usage lines
            m = rec.get("model", "?") or "?"
            a = agg.setdefault(m, {"calls": 0, "prompt": 0, "hit": 0, "miss": 0, "out": 0, "reason": 0})
            prompt = u.get("prompt_tokens", 0) or 0
            hit = u.get("prompt_cache_hit_tokens")
            miss = u.get("prompt_cache_miss_tokens")
            if hit is None:
                ptd = u.get("prompt_tokens_details") or {}
                hit = ptd.get("cached_tokens", 0) or 0
                miss = max(prompt - hit, 0)
            ctd = u.get("completion_tokens_details") or {}
            a["calls"] += 1
            a["prompt"] += prompt
            a["hit"] += hit or 0
            a["miss"] += miss or 0
            a["out"] += u.get("completion_tokens", 0) or 0
            a["reason"] += ctd.get("reasoning_tokens") or 0
            n += 1

    print(f"Calls with usage: {n}\n")
    grand = 0.0
    for m, a in sorted(agg.items()):
        prompt = a["prompt"]
        ratio = (a["hit"] / prompt * 100) if prompt else 0.0
        pr = PRICES.get(m, PRICES["deepseek-v4-pro"])
        cost = (a["hit"] * pr["hit"] + a["miss"] * pr["miss"] + a["out"] * pr["out"]) / 1_000_000
        grand += cost
        reason_pct = (a["reason"] / a["out"] * 100) if a["out"] else 0.0
        print(f"[{m}] calls={a['calls']}")
        print(f"  prompt={prompt}  cache_hit={a['hit']}  cache_miss={a['miss']}  hit_ratio={ratio:.1f}%")
        print(f"  completion={a['out']}  reasoning={a['reason']} ({reason_pct:.0f}% of output)")
        print(f"  est_cost=${cost:.5f}  (spec prices)\n")
    print(f"TOTAL est_cost=${grand:.5f}  over {n} calls")
    if n:
        print(f"avg est_cost/call=${grand/n:.5f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else LEDGER)
