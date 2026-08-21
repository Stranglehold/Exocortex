#!/usr/bin/env python3
"""JSON coherence sweep — where does a model's tool-call structure actually break?

Briefed by Opus 2026-08-11: "Each active model, text_editor:write payloads at
4K/8K/12K/16K/24K/32K chars, measure where structural validity breaks. Source the
threshold from the model profile rather than a hardcoded constant."

WHY IT MATTERS: MetaGate blocks text_editor:write at ~5000 chars on the belief that a
larger payload corrupts the JSON tool call. That constraint has never been measured
against the model actually running. Opus's stake: "If deepseek-flash holds at 16K, a
meaningful share of those 300 [blocked writes] were against a constraint the model
never had."

METHOD
  Ask the model to emit ONE A0-format JSON tool call whose content field is a document
  of at least N characters. Grade with A0's OWN parser (helpers.extract_tools.
  extract_tool_request), not a JSON check written here — otherwise the ground truth
  comes from a different baseline than production uses.

  Two failure modes are reported SEPARATELY because they have different remedies:
    STRUCTURAL  parser returns None            -> the JSON itself broke
    SHORTFALL   parses, content << target      -> emitted, but truncated/abbreviated

INSTRUMENT GUARDS
  max_tokens is set well above what the largest target needs, and finish_reason is
  recorded on every trial. A response cut off by OUR cap reports HARNESS-CAP and is
  never counted as a model failure — a cap masquerading as a breakage is exactly how a
  sweep produces confident, wrong numbers.

Usage (must run inside the container - needs A0's key resolution and parser):
    docker cp eval/json_coherence_sweep.py <container>:/tmp/sweep.py
    docker exec <container> /opt/venv-a0/bin/python3 /tmp/sweep.py [model] [trials]
"""
import sys, json, asyncio, time

sys.path.insert(0, "/a0")
sys.path.insert(0, "/a0/python")

import models
from helpers.extract_tools import extract_tool_request, normalize_tool_request

MODEL = sys.argv[1] if len(sys.argv) > 1 else "deepseek/deepseek-v4-flash"
TRIALS = int(sys.argv[2]) if len(sys.argv) > 2 else 2
SIZES = [4000, 8000, 12000, 16000, 24000, 32000]

# The cap must never be the binding constraint - if it is, the trial reports
# HARNESS-CAP rather than a model failure.
#
# MEASURED 2026-08-20, deepseek-v4-flash: the model massively OVERSHOOTS a length
# target - asked for 4,000 chars it wrote 9,553; asked for 12,000 it wrote 30,385;
# asked for 32,000 it wrote 85,151. That is 2.4x-2.7x. The first cap formula
# (n/4*3 tokens) assumed the model would land near the target and cost 8 of 12 trials
# to HARNESS-CAP. Budget for the observed overshoot, not for the request.
OVERSHOOT = 3.0     # measured 2.4-2.7x, rounded up
CHARS_PER_TOKEN = 3.5


def cap_for(n):
    return max(8000, int(n * OVERSHOOT / CHARS_PER_TOKEN))


PROMPT = """You are an autonomous agent. Respond with ONLY a single JSON object and nothing else - no prose before or after, no markdown code fences.

Exact shape:
{{"thoughts": ["brief"], "tool_name": "text_editor", "tool_args": {{"action": "write", "path": "/tmp/doc_{n}.md", "content": "<THE DOCUMENT>"}}}}

<THE DOCUMENT> must be a technical reference document of AT LEAST {n} characters about distributed systems failure modes. Structure it as numbered sections with several paragraphs each. Write real prose - do not use filler, placeholders, ellipses, or "[content continues]".

The document goes inside the JSON string value, so newlines must be escaped as \\n. Emit the complete document in this one response."""


async def trial(key, n, i):
    t0 = time.time()
    out = {"target": n, "trial": i}
    try:
        import litellm
        r = await litellm.acompletion(
            model=MODEL,
            messages=[{"role": "user", "content": PROMPT.format(n=n)}],
            api_key=key,
            max_tokens=cap_for(n),
            temperature=0,
        )
    except Exception as e:
        out.update(verdict="API-ERROR", detail=str(e)[:160])
        return out

    msg = r.choices[0].message
    txt = msg.content or ""
    fr = getattr(r.choices[0], "finish_reason", "?")
    u = getattr(r, "usage", None)
    out["finish_reason"] = fr
    out["raw_len"] = len(txt)
    out["completion_tokens"] = getattr(u, "completion_tokens", None) if u else None
    out["seconds"] = round(time.time() - t0, 1)

    parsed = extract_tool_request(txt)
    if parsed is None:
        # Distinguish "the model broke the JSON" from "our cap cut it off mid-emission".
        out["verdict"] = "HARNESS-CAP" if fr == "length" else "STRUCTURAL-BREAK"
        out["content_len"] = 0
        return out

    try:
        name, args = normalize_tool_request(parsed)
    except Exception:
        name, args = parsed.get("tool_name", "?"), parsed.get("tool_args", {}) or {}
    content = str(args.get("content", ""))
    out["tool_name"] = name
    out["content_len"] = len(content)
    out["ratio"] = round(len(content) / n, 2)

    if fr == "length":
        out["verdict"] = "HARNESS-CAP"
    elif len(content) >= n * 0.9:
        out["verdict"] = "OK"
    else:
        out["verdict"] = "SHORTFALL"
    return out


async def main():
    key = models.get_api_key("deepseek")
    if not key or key == "None":
        print("!! no api key resolved - aborting rather than reporting zeros")
        return 1
    models.configure_litellm()

    print("JSON COHERENCE SWEEP")
    print("model  :", MODEL)
    print("sizes  :", SIZES)
    print("trials :", TRIALS, "per size")
    print("grader : A0 helpers.extract_tools.extract_tool_request (production parser)")
    print()

    results = []
    for n in SIZES:
        for i in range(1, TRIALS + 1):
            r = await trial(key, n, i)
            results.append(r)
            print("  %6d chars  trial %d  %-16s content=%-6s finish=%-8s %ss"
                  % (n, i, r.get("verdict"), r.get("content_len", "-"),
                     r.get("finish_reason", "-"), r.get("seconds", "-")))

    print()
    print("%-8s %-6s %-6s %-9s %-9s %s" % ("target", "ok", "short", "struct", "cap", "max_content"))
    summary = {}
    for n in SIZES:
        rs = [r for r in results if r["target"] == n]
        ok = sum(1 for r in rs if r["verdict"] == "OK")
        sh = sum(1 for r in rs if r["verdict"] == "SHORTFALL")
        st = sum(1 for r in rs if r["verdict"] == "STRUCTURAL-BREAK")
        cp = sum(1 for r in rs if r["verdict"] in ("HARNESS-CAP", "API-ERROR"))
        mx = max([r.get("content_len", 0) for r in rs] or [0])
        summary[n] = {"ok": ok, "shortfall": sh, "structural": st, "excluded": cp, "max_content": mx}
        print("%-8d %-6d %-6d %-9d %-9d %d" % (n, ok, sh, st, cp, mx))

    struct_sizes = [n for n in SIZES if summary[n]["structural"] > 0]
    print()
    if struct_sizes:
        print("STRUCTURAL BREAK first seen at: %d chars" % min(struct_sizes))
    else:
        print("NO STRUCTURAL BREAK at any tested size (max tested %d chars)." % max(SIZES))
        print("=> The JSON envelope is not the limiting factor for this model.")
    largest_ok = max([n for n in SIZES if summary[n]["ok"] > 0] or [0])
    print("Largest size with a full-length emission: %d chars" % largest_ok)
    excluded = sum(summary[n]["excluded"] for n in SIZES)
    if excluded:
        print("NOTE: %d trial(s) excluded as HARNESS-CAP/API-ERROR - not counted as model"
              " failures." % excluded)

    out = {"model": MODEL, "trials_per_size": TRIALS, "sizes": SIZES,
           "grader": "helpers.extract_tools.extract_tool_request",
           "summary": summary, "results": results}
    with open("/tmp/json_coherence_sweep.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("\nraw -> /tmp/json_coherence_sweep.json")
    return 0


sys.exit(asyncio.run(main()))
