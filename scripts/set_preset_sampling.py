#!/usr/bin/env python3
"""Apply a model vendor's recommended sampling settings to an A0 preset.

    python scripts/set_preset_sampling.py <container> [--preset Default]
        [--temperature 0.6] [--top-p 0.95] [--top-k 20]
        [--model-name ornith-1.5-35b] [--apply]

WHY THIS EXISTS
---------------
Ornith 1.5's model card recommends temperature 0.6 / top_p 0.95 / top_k 20 (1.0 to
reproduce their published benchmarks). The live preset sets temperature '0'. Benchmarking
the model at 0 measures a different configuration than the one the published numbers
describe, so any comparison run should reconcile that first — or state which it used.

READ-MERGE-WRITE, never overwrite. presets.yaml carries operator settings that have
nothing to do with sampling (ctx_length, api_base, timeouts, a0_api_mode, thinking flags),
and clobbering those to change three numbers is how config edits cause damage here. Only
the named keys are touched, and every other key in the file is asserted unchanged.

DRY RUN BY DEFAULT. Pass --apply to write. Backs up first.

Model configuration is Jake's domain. This exists so the change is one reviewable command
with a diff, not a hand-edit of a YAML file inside a container.
"""

import argparse
import json
import subprocess
import sys

PRESETS = "/a0/usr/plugins/_model_config/presets.yaml"

# Runs INSIDE the container: yaml lives in the A0 venv, and this is the file's home.
REMOTE = r'''# -*- coding: utf-8 -*-
import io, json, sys, datetime
import yaml

path   = "__PATH__"
preset = "__PRESET__"
name   = "__MODELNAME__"
samp   = json.loads("__SAMP__")
apply_ = __APPLY__

raw = io.open(path, encoding="utf-8").read()
data = yaml.safe_load(raw) or []
before = json.loads(json.dumps(data))   # deep copy for the unchanged-keys assertion

hit = None
for p in data:
    if isinstance(p, dict) and p.get("name") == preset:
        hit = p
        break
if hit is None:
    print("!! preset %r not found. present: %s"
          % (preset, [p.get("name") for p in data if isinstance(p, dict)]))
    sys.exit(2)

chat = hit.get("chat")
if not isinstance(chat, dict):
    print("!! preset %r has no chat block" % preset); sys.exit(2)

kwargs = chat.setdefault("kwargs", {})
changes = []
for k, v in samp.items():
    old = kwargs.get(k, "<absent>")
    if str(old) != str(v):
        changes.append((k, old, v))
    kwargs[k] = v
if name:
    old = chat.get("name")
    if old != name:
        changes.append(("chat.name", old, name))
    chat["name"] = name

for k, old, new in changes:
    print("   %-16s %-12s -> %s" % (k, old, new))
if not changes:
    print("   (already at these values)")

# Nothing outside the intended keys may move.
touched = {"kwargs", "name"}
for i, (b, a) in enumerate(zip(before, data)):
    if not isinstance(b, dict):
        continue
    if b.get("name") != preset:
        assert b == a, "UNRELATED PRESET CHANGED: %s" % b.get("name")
    else:
        for key in set(b) | set(a):
            if key == "chat":
                continue
            assert b.get(key) == a.get(key), "UNRELATED KEY CHANGED: %s" % key
        cb, ca = b.get("chat", {}), a.get("chat", {})
        for key in set(cb) | set(ca):
            if key in touched:
                continue
            assert cb.get(key) == ca.get(key), "UNRELATED chat KEY CHANGED: %s" % key
print("   assertion: no unrelated key changed")

if apply_:
    stamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    io.open(path + ".bak-sampling-" + stamp, "w", encoding="utf-8", newline="\n").write(raw)
    io.open(path, "w", encoding="utf-8", newline="\n").write(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    print("   WROTE (backup: %s.bak-sampling-%s)" % (path, stamp))
else:
    print("   DRY RUN - pass --apply to write")
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("container")
    ap.add_argument("--preset", default="Default")
    ap.add_argument("--temperature", default="0.6")
    ap.add_argument("--top-p", default="0.95")
    ap.add_argument("--top-k", default="20")
    ap.add_argument("--model-name", default="")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    samp = {"temperature": a.temperature, "top_p": float(a.top_p), "top_k": int(a.top_k)}
    # Token substitution, NOT .format() — the remote body is Python source full of
    # braces (dict literals, set literals), and every one would need escaping. That is a
    # trap that fails at runtime, not at edit time.
    code = (REMOTE
            .replace("__PATH__", PRESETS)
            .replace("__PRESET__", a.preset)
            .replace("__MODELNAME__", a.model_name)
            .replace("__SAMP__", json.dumps(samp).replace('"', '\\"'))
            .replace("__APPLY__", "True" if a.apply else "False"))

    print("%s | preset=%s" % (a.container, a.preset))
    r = subprocess.run(
        ["docker", "exec", "-i", a.container, "/opt/venv-a0/bin/python3", "-"],
        input=code.encode("utf-8"), capture_output=True, timeout=90)
    sys.stdout.write(r.stdout.decode("utf-8","replace"))
    if r.returncode != 0:
        sys.stderr.write(r.stderr.decode("utf-8","replace"))
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
