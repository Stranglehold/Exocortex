"""Read-merge-write the Exocortex plugin config. Never clobbers operator values.

    python3 merge_plugin_config.py <repo_config.json> <live_config.json>

Rule (CLAUDE.md): new components ADD sections; they never overwrite existing ones.
A top-level section present in the live config is left exactly as the operator
tuned it. A section present only in the repo is added with its shipped defaults.

Runs inside the container during install. Prints what it changed so a silent
no-op is distinguishable from a silent clobber.
"""

import collections
import io
import json
import os
import shutil
import sys


def load(path):
    with io.open(path, encoding="utf-8-sig") as fh:
        return json.load(fh, object_pairs_hook=collections.OrderedDict)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: merge_plugin_config.py <repo_config> <live_config>")
        return 2

    repo_path, live_path = sys.argv[1], sys.argv[2]

    if not os.path.exists(repo_path):
        print(f"[CFG-MERGE] repo config missing: {repo_path} — skipped")
        return 0

    # First install: nothing live yet, ship the defaults wholesale.
    if not os.path.exists(live_path):
        os.makedirs(os.path.dirname(live_path), exist_ok=True)
        shutil.copyfile(repo_path, live_path)
        print(f"[CFG-MERGE] no live config — installed defaults ({len(load(live_path))} sections)")
        return 0

    try:
        repo = load(repo_path)
        live = load(live_path)
    except Exception as exc:
        # A malformed live config is the operator's, not ours to rewrite.
        print(f"[CFG-MERGE] ABORT — could not parse config: {type(exc).__name__}: {exc}")
        return 1

    added = [k for k in repo if k not in live]
    preserved = [k for k in repo if k in live and repo[k] != live[k]]

    if not added:
        print(f"[CFG-MERGE] no new sections; {len(preserved)} operator-tuned section(s) preserved")
        return 0

    backup = live_path + ".pre-merge.bak"
    shutil.copyfile(live_path, backup)

    for key in added:
        live[key] = repo[key]

    tmp = live_path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(live, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, live_path)

    print(f"[CFG-MERGE] added {len(added)} section(s): {', '.join(added)}")
    print(f"[CFG-MERGE] preserved {len(preserved)} operator-tuned section(s); backup at {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
