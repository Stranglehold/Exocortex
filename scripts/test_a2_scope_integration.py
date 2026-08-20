"""In-container integration test for A2 — drives the real extension.

Covers what the local tests cannot: that the extension's helper import resolves inside
the container (it swallows exceptions, so a failed import would be silently inert),
that the directed gate reads real engine_state, that observe-only really does not
inject, and that a detection lands in the JSONL with before/after text.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, "/a0")
sys.path.insert(0, "/a0/python")

LOG = "/a0/usr/workdir/workspace/office/scope_expansion_log.jsonl"
ENGINE = "/a0/usr/workdir/workspace/office/engine_state.json"
BACKUP = LOG + ".pretest"
if os.path.exists(LOG):
    os.replace(LOG, BACKUP)

results = []


def ok(name, cond, detail=""):
    results.append(bool(cond))
    print(("  PASS " if cond else "  FAIL ") + name + (f"   {detail}" if detail else ""))


class StubLog:
    def __init__(self): self.entries = []
    def log(self, **kw): self.entries.append(kw)


class StubCtx:
    def __init__(self, cid): self.id = cid; self.log = StubLog()


class StubAgent:
    def __init__(self, cid="ctx-directed"):
        self.data = {}
        self.context = StubCtx(cid)
        self.warnings = []
    def get_data(self, k, recursive=True): return self.data.get(k)
    def set_data(self, k, v, recursive=True): self.data[k] = v
    def hist_add_warning(self, m): self.warnings.append(m)


EXT = ("/a0/usr/plugins/_exocortex/extensions/python/before_main_llm_call/"
       "_16_scope_expansion_detector.py")


def load(agent):
    import importlib.util
    spec = importlib.util.spec_from_file_location("ext_scope", EXT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, m.ScopeExpansionDetector(agent=agent)


PLAN = {"plan_id": "p-1", "domain": "coding", "current_step": 2,
        "task_summary": "Port the install pipeline to A0 v2.9"}
DRIFT = [{"ai": True, "content": "Port done. While I'm at it I'll also refactor the idle "
                                 "engine and rewrite every installer from scratch."}]
CLEAN = [{"ai": True, "content": "Verified parity 183/183, legacy roots empty. Running the gate."}]


class LD:
    def __init__(self, hist): self.history_output = hist


async def main():
    cyc = ""
    try:
        cyc = str(json.load(open(ENGINE)).get("cycle_context_id") or "")
    except Exception:
        pass
    print(f"  (live cycle_context_id = {cyc!r})")

    agent = StubAgent()
    mod, ext = load(agent)
    ok("extension + helper import inside the container", hasattr(mod, "ScopeExpansionDetector"))

    # no plan -> silent
    await ext.execute(LD(DRIFT))
    ok("no PACE plan -> nothing recorded", not os.path.exists(LOG))

    # directed + drift -> recorded, NOT injected
    agent._pace_plan = PLAN
    await ext.execute(LD(DRIFT))
    ok("detection recorded", os.path.exists(LOG))
    rec = {}
    if os.path.exists(LOG):
        rec = json.loads(open(LOG).read().strip().split("\n")[-1])
    ok("observe-only: nothing injected to the agent", agent.warnings == [],
       f"warnings={len(agent.warnings)}")
    ok("record carries the BEFORE text", rec.get("anchor", "").startswith("Port the install"))
    ok("record carries the AFTER text", "refactor the idle engine" in rec.get("current", ""))
    ok("record names the signals", len(rec.get("signals", [])) >= 2, str(rec.get("signals")))
    ok("record marks injected=False", rec.get("injected") is False)

    # directed + no drift -> nothing new
    before = len(open(LOG).read().strip().split("\n"))
    await ext.execute(LD(CLEAN))
    after = len(open(LOG).read().strip().split("\n"))
    ok("clean elaboration adds no record", before == after, f"{before} -> {after}")

    # idle-engine cycle -> silent even with drift
    idle_agent = StubAgent(cid="ctx-idle")
    idle_agent._pace_plan = PLAN
    _m, idle_ext = load(idle_agent)
    os.replace(ENGINE, ENGINE + ".pretest") if os.path.exists(ENGINE) else None
    json.dump({"cycle_context_id": "ctx-idle", "cycle_count": 1}, open(ENGINE, "w"))
    n_before = len(open(LOG).read().strip().split("\n"))
    await idle_ext.execute(LD(DRIFT))
    n_after = len(open(LOG).read().strip().split("\n"))
    ok("IDLE-ENGINE cycle is not watched, even with drift", n_before == n_after,
       f"{n_before} -> {n_after}")
    os.remove(ENGINE)
    if os.path.exists(ENGINE + ".pretest"):
        os.replace(ENGINE + ".pretest", ENGINE)


asyncio.run(main())

try:
    os.remove(LOG)
except OSError:
    pass
if os.path.exists(BACKUP):
    os.replace(BACKUP, LOG)

print("\n" + (f"ALL {len(results)} PASS" if all(results)
              else f"FAILURES: {results.count(False)} of {len(results)}"))
sys.exit(0 if all(results) else 1)
