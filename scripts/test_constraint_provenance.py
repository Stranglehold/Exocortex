#!/usr/bin/env python3
"""Known-positive gate for helpers/constraint_provenance.py.

    docker cp scripts/test_constraint_provenance.py <c>:/tmp/tcp.py
    docker exec <c> /opt/venv-a0/bin/python3 /tmp/tcp.py

The negatives carry most of the weight. This mechanism SUPPRESSES the agent's accumulated
lessons, so a false positive silently mutes working knowledge — the expensive direction,
and the same direction every lexical critic in this repo failed in. Specifically tested:

  * no snapshot          -> must NOT suppress (else rollout mass-mutes every existing lesson)
  * limit TIGHTENED      -> must NOT suppress (the lesson is MORE relevant, not less)
  * limit relaxed < 2x   -> must NOT suppress (not a change of kind)
"""

import sys

sys.path.insert(0, "/a0/usr/plugins/_exocortex/helpers")
sys.path.insert(0, "/a0/python")
sys.path.insert(0, "/a0")

import constraint_provenance as cp


def snap(tier="local_small", limit=5000, kind="write_size", ec="oversized_tool_write"):
    s = {"captured_at": "2026-08-01T00:00:00Z", "error_class": ec,
         "model": {"model_id": "m", "profile": "p", "tier": tier}}
    if limit is not None:
        s["constraint"] = {"kind": kind, "base_limit": limit, "source": "config"}
    return s


def run():
    orig_ctx, orig_probes = cp._model_context, dict(cp.PROBES)
    cases = []

    def scenario(name, recorded, now_tier, now_limit, expect, expect_reason=""):
        cp._model_context = lambda agent=None: {"model_id": "m", "profile": "p",
                                                "tier": now_tier}
        cp.PROBES["oversized_tool_write"] = (
            (lambda agent=None: None) if now_limit is None
            else (lambda agent=None: {"kind": "write_size", "base_limit": now_limit,
                                      "source": "config"}))
        stale, why = cp.staleness(recorded, None, relax_factor=2.0)
        ok = (stale == expect) and (expect_reason in why)
        cases.append((name, stale, expect, why, ok))

    # --- must suppress ---
    scenario("limit relaxed 5,000 -> 100,000 (20x)", snap(), "local_small", 100000,
             True, "relaxed")
    scenario("limit relaxed exactly 2x (boundary)", snap(), "local_small", 10000,
             True, "relaxed")
    scenario("tier local_small -> local_large", snap(), "local_large", 5000,
             True, "tier changed")
    scenario("constraint no longer resolves", snap(), "local_small", None,
             True, "no longer resolves")

    # --- must NOT suppress ---
    scenario("no snapshot at all", None, "local_large", 100000, False)
    scenario("snapshot without constraint block", snap(limit=None), "local_small", 100000,
             False)
    scenario("limit TIGHTENED 5,000 -> 2,000", snap(), "local_small", 2000, False)
    scenario("limit relaxed only 1.5x", snap(), "local_small", 7500, False)
    scenario("nothing changed", snap(), "local_small", 5000, False)

    cp._model_context, cp.PROBES = orig_ctx, dict(orig_probes)

    w = max(len(c[0]) for c in cases)
    print("%-*s  %-7s %-7s %s" % (w, "scenario", "stale", "want", "reason"))
    print("-" * (w + 44))
    ok_all = True
    for name, stale, expect, why, ok in cases:
        ok_all &= ok
        print("%-*s  %-7s %-7s %-38s %s"
              % (w, name, stale, expect, why[:38], "OK" if ok else "*** WRONG ***"))

    # Round-trip through disk, since that is how it is actually used.
    import tempfile, os
    d = tempfile.mkdtemp()
    s = cp.snapshot(None, "oversized_tool_write")
    wrote = cp.write(d, s)
    back = cp.load(d)
    rt = wrote and back is not None and back.get("error_class") == "oversized_tool_write"
    print("\ndisk round-trip:", rt, "| sidecar:", os.path.basename(cp.path_for(d)))
    ok_all &= rt

    # The sidecar must be a DOTFILE: A0's skill discovery rglobs but skips dot-entries,
    # and validate_skill_md drops a skill whose frontmatter fails — an invalid skill is
    # invisible, not loudly broken.
    dot = os.path.basename(cp.path_for(d)).startswith(".")
    print("sidecar is a dotfile (invisible to skill discovery):", dot)
    ok_all &= dot

    # skill_dir_of must accept either form the surfacer might hand it.
    a = cp.skill_dir_of("/a0/usr/skills/auto-generated/failure-lessons/x/SKILL.md")
    b = cp.skill_dir_of("/a0/usr/skills/auto-generated/failure-lessons/x")
    print("skill_dir_of md/dir agree:", a == b, "|", a)
    ok_all &= (a == b)

    print("\nRESULT:", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(run())
