#!/usr/bin/env python3
"""
audit_skill_pool.py — apply the three admission critics to the EXISTING pool

READ-ONLY. Reports; changes nothing. Pruning skills touches the agents' accumulated
work, and VaG says contamination is irreversible in both directions — so the finding
goes to Jake and Opus rather than being acted on here.

WHY THE CRITICS ARE NOT VaG'S CRITICS VERBATIM
----------------------------------------------
VaG (arXiv 2608.05810) reports three complementary, mutually non-substitutable critics:
structural validity, behavioural harmlessness, semantic consistency. We have the first
(A0's frontmatter validator, enforced at discovery — an invalid SKILL.md is silently
dropped). The other two are built here.

But they are fitted to OUR population, which was measured before they were written
rather than assumed from the paper. The pool is dominated by **methodologies** — 35 of
Aporia's 41, 14 of Vek's 28 — which are captured research *procedures*, not action
recipes. VaG's harmfulness framing targets skills that instruct dangerous operations.
Ours mostly instruct how to investigate something.

So "behavioural harmlessness" is reframed for what can actually go wrong here:
  * a skill that instructs an IRREVERSIBLE operation without qualification
  * a skill that contradicts a hard project rule (config overwrite, unverified claims)
  * a failure-lesson whose "Avoid" advice would itself break something

And "semantic consistency" is made concrete as TRIGGER COLLISION, because triggers are
how a skill actually reaches the agent:
  * two skills with overlapping triggers and OPPOSING directives — the agent meets a
    contradiction at the moment it needs an answer
  * two skills with overlapping triggers and the same advice — redundancy, paid for in
    context budget every time both surface

Trigger overlap is measurable without an LLM, which keeps admission deterministic.

Usage:
  python scripts/audit_skill_pool.py                 # both live agents
  python scripts/audit_skill_pool.py VekV2
"""
import json
import os
import re
import subprocess
import sys

CONTAINERS = ["VekV2", "agent-zero-v2"]
_ENV = dict(os.environ, MSYS_NO_PATHCONV="1")

# Operations that cannot be undone if the advice is wrong.
IRREVERSIBLE = [
    r"rm\s+-rf", r"rm\s+-fr", r"\bdocker\s+rm\b", r"\bdocker\s+volume\s+rm\b",
    r"git\s+reset\s+--hard", r"git\s+clean\s+-[a-z]*f", r"\bDROP\s+TABLE\b",
    r"\bTRUNCATE\b", r"shutil\.rmtree", r"\bmkfs\b", r"\bdd\s+if=",
]
# Language that qualifies a dangerous instruction into a safe one.
QUALIFIERS = [
    "backup", "back up", "dry-run", "dry run", "verify", "confirm", "first",
    "before", "check", "make sure", "ensure", "caution", "careful", "danger",
    "only if", "never", "do not", "don't", "avoid",
]
# Hard project rules a skill must not teach against.
RULE_VIOLATIONS = [
    (r"overwrit\w*\s+the\s+config|replace\s+the\s+config\b",
     "config must be read-merge-write, never overwritten"),
    (r"skip\s+(the\s+)?verif|without\s+verif|no\s+need\s+to\s+(verify|check)",
     "teaches skipping verification"),
    (r"assume\s+(it|the)\s+(work|succeed|is\s+fine)",
     "teaches assuming success instead of checking"),
]


def dexec(c, cmd, timeout=90):
    try:
        r = subprocess.run(["docker", "exec", c, "sh", "-lc", cmd],
                           capture_output=True, text=True, timeout=timeout, env=_ENV)
        return r.stdout or ""
    except Exception:
        return ""


COLLECT = r'''
import json, os, re
root = "/a0/usr/skills"
out = []
for dp, dn, fn in os.walk(root):
    dn[:] = [d for d in dn if not d.startswith(".")]
    if "SKILL.md" not in fn:
        continue
    p = os.path.join(dp, "SKILL.md")
    try:
        t = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", t, re.S)
    fm, body = (m.group(1) if m else ""), (t[m.end():] if m else t)
    name = ""
    trig = []
    for line in fm.split("\n"):
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip('"').strip("'")
        if line.startswith("triggers:"):
            trig = re.findall(r'"([^"]+)"', line) or re.findall(r"'([^']+)'", line)
    out.append({
        "path": p,
        "rel": os.path.relpath(p, root),
        "name": name,
        "auto": "/auto-generated/" in p,
        "has_fm": bool(m),
        "triggers": trig,
        "body": body[:6000],
    })
print(json.dumps(out))
'''


def collect(container):
    import base64
    b = base64.b64encode(COLLECT.encode()).decode()
    raw = dexec(container,
                f"echo {b} | base64 -d > /tmp/_audit.py && "
                f"/opt/venv-a0/bin/python3 /tmp/_audit.py; rm -f /tmp/_audit.py", 180)
    i = raw.find("[")
    if i < 0:
        return []
    try:
        return json.loads(raw[i:])
    except Exception:
        return []


def critic_structural(s):
    """Critic 1 — already enforced by A0 at discovery; reported for completeness."""
    problems = []
    if not s["has_fm"]:
        problems.append("no YAML frontmatter (invisible to discover_skill_md_files)")
    if not s["name"]:
        problems.append("no name field")
    return problems


def critic_harmless(s):
    """Critic 2 — irreversible instructions without qualification, and rule violations."""
    problems = []
    body = s["body"]
    low = body.lower()
    for rx in IRREVERSIBLE:
        for m in re.finditer(rx, body, re.I):
            # Look at the sentence around the match, not the whole document — a
            # 'verify' three paragraphs away does not qualify this line.
            a, b = max(0, m.start() - 200), min(len(body), m.end() + 200)
            window = body[a:b].lower()
            if not any(q in window for q in QUALIFIERS):
                problems.append(f"unqualified irreversible op: {m.group(0)!r}")
                break
    for rx, why in RULE_VIOLATIONS:
        for m in re.finditer(rx, low):
            # POLARITY CHECK. The first version of this critic flagged three of
            # Aporia's methodology skills for "teaching skipping verification". The
            # actual matched line was:
            #     "- forcing isomorphisms without verifying structural equivalence"
            # sitting in the skill's PITFALLS list. The skill teaches verification;
            # the critic accused it of the opposite, because a bare substring match
            # cannot tell a prohibition from a prescription.
            #
            # So: if the phrase appears inside prohibitive framing, it is the skill
            # warning against the thing, not recommending it.
            a, b = max(0, m.start() - 160), min(len(low), m.end() + 80)
            window = low[a:b]

            # Also look at the SECTION HEADING this line sits under. Pitfall lists are
            # written as bare noun phrases — "treating X as Y without verifying Z" —
            # with the prohibition stated once in the heading and never repeated per
            # bullet. A fixed lookback window misses that, which is how the second
            # iteration of this critic still flagged a skill whose whole section was
            # headed "Pitfalls". Third time: read the heading.
            heading = ""
            for line in reversed(low[:m.start()].split("\n")):
                st = line.strip()
                if st.startswith("#") or (st.startswith("**") and st.endswith("**")):
                    heading = st
                    break

            prohibitive = any(w in (window + " " + heading) for w in (
                "avoid", "do not", "don't", "never", "pitfall", "failure mode",
                "anti-pattern", "antipattern", "mistake", "trap", "beware",
                "watch out", "risk of", "danger of", "instead of", "rather than",
                "common error", "what not to", "gotcha", "caveat", "limitation",
            ))
            if not prohibitive:
                problems.append(f"contradicts a project rule: {why}")
            break
    return problems


NEG = re.compile(r"\b(do not|don't|never|avoid|must not|no need to)\b", re.I)


def critic_consistency(skills):
    """Critic 3 — TRIGGER COLLISION. Reports only what is actually measurable.

    An earlier version of this critic also claimed CONTRADICTION, on the rule "some
    skills in this trigger group contain a negation word and others do not". Checked
    against the one case it flagged on Vek and it was a false positive: two of the
    three skills had no negation at all, and the third merely contained the phrase
    "do not" somewhere in its opening. Containing a negation is not the same as
    negating what another skill asserts.

    Detecting a genuine contradiction means reading two procedures and judging whether
    their advice conflicts. That is a semantic judgment, and faking it with a regex
    produces exactly the kind of unverified claim this project keeps finding in its own
    anti-pattern list — flagged repeatedly, never confirmed.

    So this reports COLLISION: N skills share a trigger, therefore they surface
    together and compete for the same context budget. That is deterministic, true, and
    actionable on its own. Whether any collision is also a contradiction is left as a
    review question against real text, not asserted by the tool.
    """
    findings = []
    norm = lambda t: re.sub(r"[^a-z0-9 ]", " ", (t or "").lower()).strip()
    idx = {}
    for s in skills:
        for t in s["triggers"]:
            k = norm(t)
            if len(k) < 6:
                continue
            idx.setdefault(k, []).append(s)
    for trig, group in idx.items():
        names = sorted({g["name"] or g["rel"] for g in group})
        if len(names) < 2:
            continue
        findings.append({
            "trigger": trig[:70],
            "kind": "COLLISION",
            "count": len(names),
            "skills": names[:5],
            "review": "do these give compatible advice for this trigger?",
        })
    return sorted(findings, key=lambda f: -f["count"])


def audit(container):
    skills = collect(container)
    if not skills:
        print(f"\n{container}: could not collect skills (container down?)")
        return None
    auto = [s for s in skills if s["auto"]]

    struct, harm = {}, {}
    for s in auto:
        p1 = critic_structural(s)
        p2 = critic_harmless(s)
        if p1:
            struct[s["rel"]] = p1
        if p2:
            harm[s["rel"]] = p2
    collisions = critic_consistency(skills)

    print(f"\n{'=' * 68}\n{container}\n{'=' * 68}")
    print(f"  discoverable skills : {len(skills)}")
    print(f"  auto-generated      : {len(auto)}  "
          f"({round(100 * len(auto) / max(len(skills), 1))}% of reachable context)")
    print(f"\n  CRITIC 1 structural   : {len(struct)} flagged")
    for k, v in list(struct.items())[:6]:
        print(f"     - {k}: {'; '.join(v)}")
    print(f"  CRITIC 2 harmlessness : {len(harm)} flagged")
    for k, v in list(harm.items())[:8]:
        print(f"     - {k}: {'; '.join(v)}")
    worst = sum(c["count"] for c in collisions) - len(collisions)
    print(f"  CRITIC 3 consistency  : {len(collisions)} trigger collision(s), "
          f"{worst} surplus skill-surfacings")
    for c in collisions[:8]:
        print(f"     - {c['count']} skills share {c['trigger']!r}: {c['skills']}")
    if collisions:
        print("       (collision is measured; whether any pair CONTRADICTS is a review")
        print("        question against the real text, not something a regex can assert)")

    return {"container": container, "total": len(skills), "auto": len(auto),
            "structural": struct, "harmless": harm,
            "collisions": collisions, "surplus_surfacings": worst}


def main():
    targets = sys.argv[1:] or CONTAINERS
    print("SKILL POOL AUDIT — read-only. Reports only; changes nothing.")
    results = [r for r in (audit(c) for c in targets) if r]
    print(f"\n{'=' * 68}\nSUMMARY")
    for r in results:
        print(f"  {r['container']:<16} auto={r['auto']:<4} "
              f"struct={len(r['structural'])} harm={len(r['harmless'])} "
              f"collisions={len(r['collisions'])} surplus={r['surplus_surfacings']}")
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "harness", "results", "skill_pool_audit.json")
    try:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        print(f"\n  full findings -> {out}")
    except Exception as e:
        print(f"  (could not write findings: {e})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
