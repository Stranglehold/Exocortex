#!/usr/bin/env python3
"""Measure where a model actually truncates a DIRECT tool-call write.

    python scripts/write_ladder.py --port 32831 --token X --label arm-name [--sizes 2000,8000]

This is the measurement the coherence sweep was specified to produce and never did. It
asks the real question - does the model truncate? - rather than the proxy question the
write gate asks, which is "is this payload longer than a number nobody measured".

DESIGN NOTES, because the obvious version of this test measures nothing:

  * The model must GENERATE the content, not copy it. A §§include directive or a
    code_execution open() both write the bytes without ever putting them through the JSON
    tool-call channel, which is the channel under test. Today's 40K result looks like
    proof of large writes and is not: the model emitted 92 characters.

  * Truncation is not "fewer lines than asked for". A model choosing to write less is a
    different event from a payload cut off mid-emission. The discriminator is whether the
    tool call PARSED - a parsed call is complete by construction, so a file that exists at
    all means no truncation at that size. No file plus a prose reply is the truncation
    signature (agent.py:1128-1129 mislabels those as the agent choosing to talk).

  * Generation is not token-capped on this stack: no max_tokens in the preset, no
    -n/--n-predict on the server, slots report n_predict=-1. So a cutoff here is model
    behaviour, not budget.

Reports per rung: bytes on disk, whether a file appeared, and the verdict. Writes JSON so
arms can be compared.
"""

import argparse
import json
import re
import subprocess
import time
import urllib.request

SENTENCE = ("The workshop improves by being used and is used by being improved, "
            "and this line exists only to occupy a known number of characters.")

# The gate's central claim is that COMPLEXITY, not length, predicts truncation:
# "a 20K prose payload can pass where 12K with three code fences fails." Prose alone
# cannot test that. This line is deliberately dense in exactly the characters that cost
# something inside a JSON string field — double quotes, backslashes, braces — so the
# escape-density axis is actually exercised rather than assumed.
CODE_TMPL = ('def f_%d(s: str) -> str:\n'
             '    """Doc with "quotes", a \\\\ backslash and {braces}."""\n'
             '    return s.replace("\\\\n", "\\\\\\\\n") + "row %d"\n')


def line_len(i, shape):
    return len(render(i, shape))


def render(i, shape):
    if shape == "code":
        return CODE_TMPL % (i, i)
    return "[%d] %s\n" % (i, SENTENCE)


def lines_for(target, shape):
    """How many units land closest to `target` characters."""
    n, total = 0, 0
    while total < target:
        n += 1
        total += line_len(n, shape)
    return n, total


def drive(port, token, message, timeout):
    payload = json.dumps({"message": message}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:%d/api/api_message" % port, data=payload,
        headers={"Content-Type": "application/json", "X-API-KEY": token}, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace")), time.time() - t0, None
    except Exception as e:
        return None, time.time() - t0, "%s: %s" % (type(e).__name__, e)


def stat(container, path):
    try:
        out = subprocess.run(
            ["docker", "exec", container, "sh", "-c", "wc -c < %s 2>/dev/null || echo -1" % path],
            capture_output=True, text=True, timeout=30)
        return int((out.stdout or "-1").strip() or -1)
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--container", default="exo_installtest")
    ap.add_argument("--label", required=True)
    ap.add_argument("--sizes", default="2000,8000,16000,32000")
    ap.add_argument("--shape", choices=["prose", "code"], default="prose")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    results = []
    for target in [int(s) for s in args.sizes.split(",")]:
        n, expected = lines_for(target, args.shape)
        ext = "py" if args.shape == "code" else "txt"
        path = "/tmp/ladder_%s_%d.%s" % (args.shape, target, ext)
        unit = "function blocks" if args.shape == "code" else "lines"
        template = render(1, args.shape).replace("_1(", "_i(").replace("row 1", "row i")
        msg = (
            "Create a file at %s containing exactly %d %s and nothing else.\n\n"
            "Block i (for i from 1 to %d) must be exactly this, with i substituted for "
            "every occurrence of i:\n\n%s\n"
            "Use the text_editor tool with action=write and put the ENTIRE content inline "
            "in the tool call.\n"
            "Do NOT use §§include. Do NOT use code_execution_tool. Do NOT write it "
            "in pieces or append. One single text_editor write containing all %d %s, "
            "generated by you.\n"
            "When the tool returns, reply with only the byte count it reported."
            % (path, n, unit, n, template, n, unit)
        )
        print("[%s/%s] rung target=%d units=%d expected=%d bytes"
              % (args.label, args.shape, target, n, expected), flush=True)

        subprocess.run(["docker", "exec", args.container, "rm", "-f", path],
                       capture_output=True)
        resp, secs, err = drive(args.port, args.token, msg, args.timeout)
        got = stat(args.container, path)
        text = (resp or {}).get("response", "") if resp else ""

        if err:
            verdict = "REQUEST-ERROR"
        elif got < 0:
            # No file. Either a truncated tool call (mislabelled as prose) or a refusal.
            verdict = "NO-FILE (truncation candidate)"
        elif got >= expected * 0.98:
            verdict = "COMPLETE"
        else:
            verdict = "SHORT (model wrote less; NOT truncation - the call parsed)"

        print("    -> %-46s got=%-8s in %.0fs" % (verdict, got, secs), flush=True)
        if err:
            print("       err: %s" % err, flush=True)
        results.append(dict(label=args.label, target=target, lines=n, expected=expected,
                            got=got, seconds=round(secs, 1), verdict=verdict,
                            error=err, reply=text[:300]))

    print()
    print("%-8s %-10s %-10s %-8s %s" % ("target", "expected", "got", "secs", "verdict"))
    for r in results:
        print("%-8s %-10s %-10s %-8s %s"
              % (r["target"], r["expected"], r["got"], r["seconds"], r["verdict"]))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        print("\nwrote", args.out)


if __name__ == "__main__":
    main()
