#!/usr/bin/env python3
"""
scan_flags.py — does each Exocortex extension read an `enabled` flag, and how? A column for Kestrel's generated
wiring map (docs/wiring/generated/scan_container.py), same contract: runs INSIDE the container, read-only, JSON on
stdout, limits stated in the output. Fable, 2026-09-03, after Kestrel measured 30 of 76 by hand.

Why it exists: CLAUDE.md states "every component reads an `enabled` flag, skips if missing or false" as universal.
Measured on 2026-09-03 it held for about a third of the stack, and the blocks Aporia complained about were in the
other two thirds, so nothing could be switched off for a test without a code change. A convention quoted as a
rule and followed by a third is exactly the kind of sentence that drifts from the measurement; this makes it a
number the map re-measures every run.

Per extension it reports: whether "enabled" appears at all; whether the `_cfg().get("enabled", True)` idiom (the
`_10` shape) is present; whether a `_DEFAULTS` dict declares it; any other guard shape found; and whether the
extension is one of the message-loop injectors. Limits: string matching on source, so a flag read through a helper
this pattern does not know is reported as "other-guard" or missed; a flag that is read but never acted on looks
the same as one that is; and "injector" is by hook folder, not by proof of injection.
"""
import json, os, re, sys

PLUGIN = "/a0/usr/plugins/_exocortex/extensions/python"
INJECTOR_HOOKS = {"message_loop_prompts_after", "message_loop_prompts_before", "system_prompt", "before_main_llm_call"}
IDIOM_GET = re.compile(r'\.get\(\s*["\']enabled["\']')
DEFAULTS = re.compile(r'_DEFAULTS\s*=\s*\{[^}]*["\']enabled["\']')
OTHER = re.compile(r'\benabled\b')
CFG_KEY = re.compile(r'_CONFIG_(?:KEY|NAME|FILE)\s*=\s*["\']([^"\']+)["\']|config[_/]?(?:name|key)\s*=\s*["\']([^"\']+)["\']')


def scan():
    rows = []
    if not os.path.isdir(PLUGIN):
        return {"error": f"{PLUGIN} not found", "limits": ["plugin root missing; nothing measured"]}
    for hook in sorted(os.listdir(PLUGIN)):
        d = os.path.join(PLUGIN, hook)
        if not os.path.isdir(d) or hook == "__pycache__":
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".py") or not fn.startswith("_"):
                continue
            p = os.path.join(d, fn)
            try:
                s = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            get = bool(IDIOM_GET.search(s)); dflt = bool(DEFAULTS.search(s)); any_ref = bool(OTHER.search(s))
            m = CFG_KEY.search(s); key = (m.group(1) or m.group(2)) if m else None
            rows.append({"hook": hook, "file": fn, "injector": hook in INJECTOR_HOOKS,
                         "enabled_refs": len(OTHER.findall(s)),
                         "shape": "cfg-get" if get else ("defaults-only" if dflt else ("other-guard" if any_ref else "none")),
                         "config_key": key})
    n = len(rows)
    by = {}
    for r in rows:
        by[r["shape"]] = by.get(r["shape"], 0) + 1
    inj = [r for r in rows if r["injector"]]
    return {
        "root": PLUGIN,
        "counts": {"extensions": n, "with_cfg_get_idiom": by.get("cfg-get", 0), "defaults_only": by.get("defaults-only", 0),
                   "other_guard": by.get("other-guard", 0), "none": by.get("none", 0),
                   "injectors": len(inj), "injectors_without_flag": sum(1 for r in inj if r["shape"] == "none")},
        "convention_claim": "CLAUDE.md: every component reads an `enabled` flag, skips if missing or false",
        "convention_measured": f"{by.get('cfg-get', 0)} of {n} use the cfg.get idiom; {by.get('none', 0)} read no flag at all",
        "injectors_without_flag": [r["file"] for r in inj if r["shape"] == "none"],
        "extensions": rows,
        "limits": ["string matching on source; a flag read through an unknown helper is 'other-guard' or missed",
                   "a flag read but never acted on looks the same as one that is",
                   "'injector' is by hook folder, not by proof of injection"],
    }


if __name__ == "__main__":
    print(json.dumps({"generated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()[:19] + "Z",
                      "flags": scan()}, indent=1))
