#!/usr/bin/env python3
"""test_recall_trace.py — controls for build-order item 2a, the container-side recall trace.

  Q  recall_query.build_query_with_source returns the three sources, and build_query's TEXT is
     unchanged against the deployed version on the same inputs.
  T  memory_recall_tag.trace: row shape; `ids: []` recorded; early/error only when set; never
     raises (a path it cannot open returns False and prints); 16 threads x 100 rows all parse.
  E  _92 driven the way A0 calls it (execute(loop_data=...)), A0's modules stubbed: EXACTLY ONE
     row per call on every path: subordinate, no_db, no_docs, no_query, full with ids, full with
     none, idle recent_work, a pipeline that raises, an exception before the trace, and an
     exception AFTER the trace (co-retrieval), which must not add a second row.
  O  _92 against the helpers the container runs NOW (their md5s asserted, not assumed). That is
     the state between a deploy and the container restart: both helpers are imported by bare name
     and survive the plugins reload. Recall must still run on the old bounded build_query text,
     write no row, raise nothing, and print that the trace is unavailable.
  M  _35: memory_load with ids -> one row and the tag; with none -> one row, no tag; another
     tool -> no row.
  R  scripts/recall_trace_report.py on fixtures: attribution by context_id and time, NO-TOOL,
     constant ids, early counts, CHARGE-ONLY, unjoined rows, the journal join, a broken journal
     line reported, clipping at whitespace only, --since; and the CLI: a missing trace exits 3
     with UNVERIFIED, partial local paths exit 1.

    python scripts/test_recall_trace.py
"""
import asyncio
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import types

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PLUGIN = os.path.join(REPO, "plugins", "_exocortex")
HELPERS = os.path.join(PLUGIN, "helpers")
# The env overrides exist for mutation checks (point one at a deliberately broken copy and the
# matching check must fail); a normal run uses the repo files.
EXT92 = os.environ.get("TEST_EXT92") or os.path.join(PLUGIN, "extensions", "python", "message_loop_prompts_after", "_92_memory_enhancement.py")
EXT35 = os.environ.get("TEST_EXT35") or os.path.join(PLUGIN, "extensions", "python", "tool_execute_after", "_35_recall_tag_memory_load.py")
REPORT = os.environ.get("TEST_REPORT") or os.path.join(HERE, "recall_trace_report.py")

# What agent-zero-v2 ran when this was written (docker exec md5sum, 2026-09-25 ~02:45Z), byte-identical
# to this commit's files. Pinned so the O test keeps testing the pre-trace helpers after 2a is committed.
DEPLOYED_AT = "22ddb30"
DEPLOYED_MD5 = {"recall_query.py": "cb8921d9b1ce315f86174e168b7c37b0",
                "memory_recall_tag.py": "32ae2a1f8ff500599debeea1b0ca20d0"}

TMP = tempfile.mkdtemp(prefix="recall_trace_test_")
TRACE = os.path.join(TMP, "recall_trace.jsonl")
os.environ["EXO_RECALL_TRACE_PATH"] = TRACE   # read when memory_recall_tag is imported

passed = failed = 0


def check(label, cond, detail=""):
    global passed, failed
    print(("  PASS  " if cond else "  FAIL  ") + label + (("  [%s]" % (detail,)) if (detail and not cond) else ""))
    passed += bool(cond)
    failed += (not cond)


# ── A0 stand-ins: only what the two extensions and recall_query touch ─────────────────────────────

class LoopData:
    def __init__(self, **kw):
        self.iteration = -1
        self.user_message = None
        self.history_output = []
        self.last_response = ""
        self.extras_persistent = {}
        self.__dict__.update(kw)


class Msg:
    def __init__(self, text):
        self.text = text

    def output_text(self):
        return self.text


def install_a0_stubs():
    agent_mod = types.ModuleType("agent")
    agent_mod.LoopData = LoopData
    agent_mod.Agent = type("Agent", (), {"DATA_NAME_SUPERIOR": "_superior"})
    helpers_pkg = types.ModuleType("helpers")
    helpers_pkg.__path__ = []
    ext = types.ModuleType("helpers.extension")

    class Extension:
        def __init__(self, agent=None, **kwargs):
            self.agent = agent
    ext.Extension = Extension
    hist = types.ModuleType("helpers.history")
    hist.output_text = lambda tail: "\n".join(str(x) for x in tail)
    helpers_pkg.extension, helpers_pkg.history = ext, hist
    mem = types.ModuleType("plugins._memory.helpers.memory")

    class Memory:
        result = None

        @staticmethod
        async def get(agent):
            return Memory.result
    mem.Memory = Memory
    mods = {"agent": agent_mod, "helpers": helpers_pkg, "helpers.extension": ext,
            "helpers.history": hist, "plugins._memory.helpers.memory": mem}
    for name in ("plugins", "plugins._memory", "plugins._memory.helpers"):
        p = types.ModuleType(name)
        p.__path__ = []
        mods[name] = p
    sys.modules.update(mods)
    return Memory


class FakeContext:
    def __init__(self, cid, idle):
        self.id = cid
        self.data = {"idle_cycle": {"n": 1}} if idle else {}
        self.log = types.SimpleNamespace(log=lambda **kw: None)

    def get_data(self, k):
        return self.data.get(k)


class FakeAgent:
    def __init__(self, cid="ctxA", number=0, superior=None, idle=False, iteration=None):
        self.context = FakeContext(cid, idle)
        self.number = number
        self.data = {} if superior is None else {"_superior": superior}
        self.config = types.SimpleNamespace(memory_recall_similarity_threshold=0.3)
        if iteration is not None:
            self.loop_data = LoopData(iteration=iteration)

    def get_data(self, k):
        return self.data.get(k)

    def set_data(self, k, v):
        self.data[k] = v

    def parse_prompt(self, name, **kw):
        return "PROMPT(%s)" % name


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def rows():
    if not os.path.exists(TRACE):
        return []
    with open(TRACE, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def one(label, new, **want):
    ok = len(new) == 1 and all(new[0].get(k) == v for k, v in want.items())
    check(label, ok, new)


sys.path.insert(0, HELPERS)
Memory = install_a0_stubs()
import recall_query as rq          # noqa: E402  the working-tree helpers (the change under test)
import memory_recall_tag as mrt    # noqa: E402

check("trace() writes where the test says (the env var is read at import)", mrt.TRACE_PATH == TRACE, mrt.TRACE_PATH)

OLD = os.path.join(TMP, "deployed")
os.makedirs(OLD)
for fn in DEPLOYED_MD5:
    blob = subprocess.run(["git", "-C", REPO, "show", "%s:plugins/_exocortex/helpers/%s" % (DEPLOYED_AT, fn)],
                          capture_output=True, check=True).stdout
    with open(os.path.join(OLD, fn), "wb") as fh:
        fh.write(blob)

# ── Q ────────────────────────────────────────────────────────────────────────────────────────────
print("Q. recall_query: the source, and build_query's text unchanged against the deployed version")
old_rq_q = load_module("deployed_recall_query_q", os.path.join(OLD, "recall_query.py"))
charge = "charge " * 700    # ~4,900 characters: over the bound, like the real activation charge
cases = {
    "user_message": (FakeAgent(idle=False), LoopData(user_message=Msg("what failed in " + charge))),
    "recent_work": (FakeAgent(idle=True), LoopData(user_message=Msg(charge), history_output=["tool result A", "tool result B"],
                                                   last_response="I checked the index " * 90)),
    "idle_charge": (FakeAgent(idle=True), LoopData(user_message=Msg(charge))),
}
for want, (ag, ld_) in cases.items():
    text, src = rq.build_query_with_source(ag, ld_, 1200)
    check("%s: source is %s" % (want, want), src == want, src)
    check("%s: build_query returns the same text" % want, rq.build_query(ag, ld_, 1200) == text)
    check("%s: identical to the DEPLOYED build_query's text" % want, old_rq_q.build_query(ag, ld_, 1200) == text)
    check("%s: bounded (%d chars)" % (want, len(text)), 0 < len(text) <= 1200, len(text))
check("max_chars None or 0 falls back to the default bound",
      rq.build_query_with_source(*cases["user_message"], None)[0] == rq.build_query_with_source(*cases["user_message"], 0)[0]
      == rq.build_query_with_source(*cases["user_message"], rq.DEFAULT_MAX_CHARS)[0])

# ── T ────────────────────────────────────────────────────────────────────────────────────────────
print("T. trace(): row shape, never raises, concurrent writes")
before = len(rows())
ag = FakeAgent(cid="ctxT", number=2)
ok = mrt.trace(ag, ["b", "a", "a", "", None], "_92", turn=4, source="user_message")
r = rows()[-1]
check("returns True and appends one row", ok is True and len(rows()) == before + 1)
check("row carries context, agent, turn, via, source",
      (r["context_id"], r["agent"], r["turn"], r["via"], r["source"]) == ("ctxT", 2, 4, "_92", "user_message"), r)
check("ids sorted, unique, blanks dropped", r["ids"] == ["a", "b"], r["ids"])
check("no early/error keys when unset", "early" not in r and "error" not in r, r)
check("`at` is UTC ISO with Z", r["at"].endswith("Z") and "T" in r["at"], r["at"])
mrt.trace(ag, [], "_92", turn=0, early="no_db")
r = rows()[-1]
check("an empty recall is recorded as ids []", r["ids"] == [] and r["early"] == "no_db", r)
mrt.trace(ag, ["x"], "_92", turn=1, error=["memories"])
check("error recorded when set", rows()[-1].get("error") == ["memories"], rows()[-1])
saved_path = mrt.TRACE_PATH
mrt.TRACE_PATH = TMP          # a directory: open() fails
buf = io.StringIO()
raised = res = None
with contextlib.redirect_stdout(buf):
    try:
        res = mrt.trace(ag, ["x"], "_92")
    except Exception as e:
        raised = e
mrt.TRACE_PATH = saved_path
check("never raises on a path it cannot open; returns False", raised is None and res is False, (res, raised))
check("...and prints the gap", "[RECALL-TRACE] write failed" in buf.getvalue(), buf.getvalue()[:200])
n_before = len(rows())


def worker(k):
    for j in range(100):
        mrt.trace(FakeAgent(cid="c%d" % k), ["m%d" % j, "pad" * 300], "_92", turn=j, source="user_message")


ts = [threading.Thread(target=worker, args=(k,)) for k in range(16)]
[t.start() for t in ts]
[t.join() for t in ts]
good = bad = 0
with open(TRACE, encoding="utf-8") as fh:
    for line in fh:
        try:
            json.loads(line)
            good += 1
        except Exception:
            bad += 1
check("16 threads x 100 rows: all parse, none lost", bad == 0 and good == n_before + 1600, (good, bad, n_before))

# ── E ────────────────────────────────────────────────────────────────────────────────────────────
print("E. _92 driven the way A0 calls it: exactly one row per execute()")
captured, PIPE_MODE = [], {}
IDS = {"area != 'solutions'": ["m1", "m2"], "area == 'solutions'": ["s1"]}


async def fake_pipeline(db, all_docs, query, bst, roles, thr, cap, area, *rest):
    captured.append((query, area))
    mode = PIPE_MODE.get(area, "hit")
    if mode == "raise":
        raise RuntimeError("pipeline boom")
    return [] if mode == "empty" else [(area, 0.9)]


def boom(*a, **k):
    raise RuntimeError("boom")


def patch(mod):
    mod._load_config = lambda: {}
    mod._load_profile_memory_section = lambda: None
    mod._get_bst_domain = lambda agent: None
    mod._run_pipeline = fake_pipeline
    mod._with_provenance = lambda result, obs, cfg: "TXT"
    mod._update_access = lambda result, all_docs: list(IDS[result[0][0]])
    mod._log_co_retrieval = lambda *a, **k: None
    mod._mt = None


def fake_db(docs):
    return types.SimpleNamespace(db=types.SimpleNamespace(get_all_docs=lambda: docs), _save_db=lambda: None)


def run92(mod, agent, loop_data, memory_result="db"):
    Memory.result = fake_db({"m1": object()}) if memory_result == "db" else memory_result
    n0 = len(rows())
    buf_ = io.StringIO()
    with contextlib.redirect_stdout(buf_):
        asyncio.run(mod.MemoryEnhancement(agent=agent).execute(loop_data=loop_data))
    return rows()[n0:], buf_.getvalue()


def ld(it=3, msg="what is the index state", **kw):
    return LoopData(iteration=it, user_message=Msg(msg) if msg is not None else None, **kw)


m92 = load_module("ext92_new", EXT92)
patch(m92)
new, _ = run92(m92, FakeAgent(superior=object()), ld())
one("subordinate: early=subordinate, ids [], turn and hook recorded", new, early="subordinate", ids=[], turn=3, via="_92")
new, _ = run92(m92, FakeAgent(), ld(), memory_result=None)
one("no db: early=no_db", new, early="no_db", ids=[])
new, _ = run92(m92, FakeAgent(), ld(), memory_result=fake_db({}))
one("no docs: early=no_docs", new, early="no_docs", ids=[])
new, _ = run92(m92, FakeAgent(), ld(msg=None))
one("no query: early=no_query, with the source", new, early="no_query", source="user_message", ids=[])
captured.clear()
new, _ = run92(m92, FakeAgent(cid="ctxF"), ld(it=5, msg="x" * 5000))
one("full run: the injected ids, turn, source, context", new, ids=["m1", "m2"], turn=5, source="user_message", context_id="ctxF")
check("full run: no early/error keys", bool(new) and "early" not in new[0] and "error" not in new[0], new)
check("full run: the pipeline got the bounded query",
      bool(captured) and len(captured[0][0]) <= 1200, len(captured[0][0]) if captured else None)
PIPE_MODE["area != 'solutions'"] = "empty"
new, _ = run92(m92, FakeAgent(), ld())
one("full run that finds nothing: ids [], not early", new, ids=[])
check("...and not marked early", bool(new) and "early" not in new[0], new)
PIPE_MODE.clear()
new, _ = run92(m92, FakeAgent(idle=True), ld(last_response="I re-ran the probe and the library answered"))
one("idle turn with recent work: source recent_work", new, source="recent_work", ids=["m1", "m2"])
PIPE_MODE["area != 'solutions'"] = "raise"
new, _ = run92(m92, FakeAgent(), ld())
one("memories pipeline raises: error ['memories'], ids []", new, error=["memories"], ids=[])
PIPE_MODE.clear()
PIPE_MODE["area == 'solutions'"] = "raise"
new, _ = run92(m92, FakeAgent(), ld(extras_persistent={"solutions": "A0 text"}))
one("solutions pipeline raises: error ['solutions'], memory ids kept", new, error=["solutions"], ids=["m1", "m2"])
PIPE_MODE.clear()
new, _ = run92(m92, FakeAgent(), ld(extras_persistent={"solutions": "A0 text"}))
one("both pipelines hit: memory and solution ids in one row", new, ids=["m1", "m2", "s1"])
m92._load_config = boom
new, _ = run92(m92, FakeAgent(), ld())
one("exception before the trace: one row, early=exception", new, early="exception", error="RuntimeError", ids=[])
patch(m92)
m92._log_co_retrieval = boom
new, _ = run92(m92, FakeAgent(), ld())
one("exception AFTER the trace (co-retrieval): still one row, the full one", new, ids=["m1", "m2"])
patch(m92)
a = FakeAgent()
run92(m92, a, ld())
check("the recall tag still records the ids (its path is unchanged)",
      set(a.get_data(mrt.RECALLED_KEY) or []) == {"m1", "m2"}, a.get_data(mrt.RECALLED_KEY))

# ── O ────────────────────────────────────────────────────────────────────────────────────────────
print("O. _92 against the helpers the container runs now (between the deploy and the restart)")
for fn, want in DEPLOYED_MD5.items():
    got = md5(os.path.join(OLD, fn))
    check("deployed %s is what the test loads (md5 %s)" % (fn, want[:8]), got == want, got)
saved_mods = {k: sys.modules.get(k) for k in ("recall_query", "memory_recall_tag")}
old_rq = sys.modules["recall_query"] = load_module("recall_query", os.path.join(OLD, "recall_query.py"))
old_mrt = sys.modules["memory_recall_tag"] = load_module("memory_recall_tag", os.path.join(OLD, "memory_recall_tag.py"))
check("the deployed helpers really lack the new functions",
      not hasattr(old_rq, "build_query_with_source") and not hasattr(old_mrt, "trace"))
m92o = load_module("ext92_old_helpers", EXT92)
patch(m92o)
check("the new _92 imported the cached (deployed) recall_query", m92o.recall_query is old_rq)
captured.clear()
a = FakeAgent(cid="ctxO")
ldo = ld(it=2, msg="y" * 5000)
n0 = len(rows())
buf = io.StringIO()
raised = None
with contextlib.redirect_stdout(buf):
    try:
        Memory.result = fake_db({"m1": object()})
        asyncio.run(m92o.MemoryEnhancement(agent=a).execute(loop_data=ldo))
    except Exception as e:
        raised = e
check("nothing raises", raised is None, raised)
check("recall still ran", len(captured) >= 1, captured)
q = captured[0][0] if captured else ""
check("the query is the deployed build_query's bounded text (%d chars)" % len(q),
      q == old_rq.build_query(a, ldo, 1200) and 0 < len(q) <= 1200)
check("no trace row is written", len(rows()) == n0, len(rows()) - n0)
check("the 'unavailable' line prints", "Recall trace unavailable" in buf.getvalue(), buf.getvalue()[-300:])
check("the deployed tag still records the ids", set(a.get_data(old_mrt.RECALLED_KEY) or []) == {"m1", "m2"})
for k, v in saved_mods.items():
    sys.modules[k] = v

# ── M ────────────────────────────────────────────────────────────────────────────────────────────
print("M. _35: every memory_load call writes one row")
m35 = load_module("ext35_new", EXT35)


def run35(agent, response, tool_name):
    n0_ = len(rows())
    with contextlib.redirect_stdout(io.StringIO()):
        asyncio.run(m35.RecallTagMemoryLoad(agent=agent).execute(response=response, tool_name=tool_name))
    return rows()[n0_:]


a = FakeAgent(cid="ctxM", iteration=7)
hit = types.SimpleNamespace(message="id: abc123\nContent: first\n\nid: def456\nContent: second\n")
new = run35(a, hit, "memory_load")
one("memory_load with ids: one row", new, via="memory_load", source="tool:memory_load", turn=7,
    ids=["abc123", "def456"], context_id="ctxM")
check("...and the tag holds them", set(a.get_data(mrt.RECALLED_KEY) or []) == {"abc123", "def456"})
a2 = FakeAgent(cid="ctxM2", iteration=1)
new = run35(a2, types.SimpleNamespace(message="No memories found for the query"), "memory_load")
one("memory_load that found nothing: one row, ids []", new, ids=[], via="memory_load")
check("...and no tag", not a2.get_data(mrt.RECALLED_KEY))
check("another tool: no row", run35(a2, hit, "code_execution_tool") == [])

# ── R ────────────────────────────────────────────────────────────────────────────────────────────
print("R. recall_trace_report on fixtures")
rep_mod = load_module("recall_trace_report", REPORT)
FX = os.path.join(TMP, "fx")
os.makedirs(FX)


def wj(name, rows_, extra_lines=()):
    p = os.path.join(FX, name)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        for x in rows_:
            fh.write(json.dumps(x) + "\n")
        for line in extra_lines:
            fh.write(line + "\n")
    return p


def T(at, ctx, ids, via="_92", source="recent_work", agent=0, turn=0, **kw):
    return dict(at=at, context_id=ctx, agent=agent, turn=turn, via=via, source=source, ids=ids, **kw)


trace_rows = [
    T("2026-09-25T01:01:00Z", "A", ["m1", "m2"]),
    T("2026-09-25T01:02:00Z", "A", ["m1", "m3"], turn=1),
    T("2026-09-25T01:03:00Z", "A", ["m1"], turn=2),
    T("2026-09-25T01:04:00Z", "A", ["m9"], via="memory_load", source="tool:memory_load", turn=2),
    T("2026-09-25T01:05:00Z", "A", [], agent=1, source=None, early="subordinate"),
    T("2026-09-25T02:01:00Z", "B", ["m1", "m2", "m7"], source="idle_charge"),
    T("2026-09-25T02:02:00Z", "B", ["m1", "m2", "m7"], source="idle_charge", turn=1),
    T("2026-09-25T02:03:00Z", "B", [], source="idle_charge", turn=2, early="no_query"),
    T("2026-09-25T02:30:00Z", "C", ["m5"], source="user_message"),
    T("2026-09-25T01:30:00Z", "A", ["m4"]),    # after A's ending, and no later one: unjoined
]
endings = [
    {"at": "2026-09-25T01:00:00Z", "event": "fired", "cycle": 800, "context_id": "A"},
    {"at": "2026-09-25T01:10:00Z", "event": "ended", "cycle": 800, "context_id": "A", "type": "MAINTAIN",
     "outcome": "completed", "elapsed_s": 600, "heartbeat_age_s": 30},
    {"at": "2026-09-25T02:00:00Z", "event": "fired", "cycle": 801, "context_id": "B"},
    {"at": "2026-09-25T02:20:00Z", "event": "ended", "cycle": 801, "context_id": "B", "type": "BUILD",
     "outcome": "reaped", "elapsed_s": 1200, "heartbeat_age_s": 1200},
]
ACT = ("MAINTAIN: pruned stale entries and verified PS-ANALYZE=216 receipts across the store "
       + "then wrote the summary " * 8).strip()
journal = [
    {"type": "cycle_close", "timestamp": "2026-09-25T01:09:00+00:00", "cycle_number": 800,
     "cycle_type": "MAINTAIN", "context_id": "A", "activity": ACT},
    {"type": "cycle_close", "timestamp": "2026-09-25T00:09:00+00:00", "cycle_number": 799,
     "cycle_type": "MAINTAIN", "context_id": "Z", "activity": "older"},
]
pt, pe = wj("trace.jsonl", trace_rows), wj("endings.jsonl", endings)
pj = wj("journal.jsonl", journal, extra_lines=['{"type": "cycle_close", "broken'])
tr = rep_mod.load(pt)[0]
en = rep_mod.load(pe)[0]
jo, rep_j, skip_j, _ = rep_mod.load(pj)
check("the broken journal line is reported, not dropped silently", len(skip_j) + len(rep_j) == 1, (rep_j, skip_j))
rep = rep_mod.build_report(tr, en, jo)
cyc = {c["context_id"]: c for c in rep["cycles"]}
check("two ended cycles", sorted(cyc) == ["A", "B"], sorted(cyc))
A, B = cyc.get("A", {}), cyc.get("B", {})
check("A: 5 rows (3 full _92, 1 memory_load, 1 early)",
      (A.get("rows"), A.get("full_92"), A.get("memory_load"), A.get("early")) == (5, 3, 1, {"subordinate": 1}), A)
check("A: m1 on every full turn", A.get("constant_ids") == ["m1"], A.get("constant_ids"))
check("A: the heartbeat advanced, so not NO-TOOL", A.get("no_tool") is False, A)
check("B: heartbeat_age == elapsed, so NO-TOOL", B.get("no_tool") is True, B)
check("B: m1 m2 m7 on every full turn", B.get("constant_ids") == ["m1", "m2", "m7"], B.get("constant_ids"))
check("A: closed, with its journal activity; B: no close",
      A.get("closed") is True and A.get("activity") == ACT and B.get("closed") is False)
cov = rep["coverage"]
check("early returns counted by reason", cov["early_by_reason"] == {"subordinate": 1, "no_query": 1}, cov["early_by_reason"])
check("unjoined: C's row, and A's row after A ended",
      rep["unjoined"]["rows"] == 2 and rep["unjoined"]["by_context"] == {"C": 1, "A": 1}, rep["unjoined"])
mem = {m["id"]: m for m in rep["memories"]}
check("m1 recalled on 5 turns in 2 contexts", (mem.get("m1") or {}).get("turns") == 5 and mem["m1"]["contexts"] == 2, mem.get("m1"))
check("m7 is CHARGE-ONLY; m1 is not", mem.get("m7", {}).get("charge_only") is True and mem["m1"]["charge_only"] is False)
c = rep_mod.clip(ACT, 56)    # a character cut at 56 would read "PS-ANALYZE=21"
check("clip cuts at whitespace, never inside a token (no '=21')",
      c.startswith("MAINTAIN: pruned stale entries and verified ...(+") and "=21" not in c, c)
rep2 = rep_mod.build_report(tr, en, jo, since=rep_mod.cw.parse_ts("2026-09-25T01:50:00Z"))
check("--since keeps only cycle B", [x["context_id"] for x in rep2["cycles"]] == ["B"], [x["context_id"] for x in rep2["cycles"]])


def cli(*args):
    r_ = subprocess.run([sys.executable, REPORT] + list(args), capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    return r_.returncode, r_.stdout, r_.stderr


code, out, err = cli("--trace", pt, "--endings", pe, "--journal", pj)
check("CLI: exit 0 on the fixtures", code == 0, (code, (out + err)[-300:]))
check("CLI: prints the NO-TOOL flag and the A17 line", "NO-TOOL" in out and "A17" in out, out[:400])
code, out, err = cli("--trace", pt, "--endings", pe, "--journal", pj, "--json")
try:
    ok = len(json.loads(out)["cycles"]) == 2
except Exception:
    ok = False
check("CLI: --json parses and carries both cycles", ok, (out + err)[:200])
code, out, err = cli("--trace", os.path.join(FX, "absent.jsonl"), "--endings", pe, "--journal", pj)
check("CLI: a missing trace exits 3 with UNVERIFIED, not a zero report", code == 3 and "UNVERIFIED" in out, (code, out[:300]))
code, out, err = cli("--trace", pt)
check("CLI: partial local paths refused (exit 1)", code == 1, (code, err[:200]))

print("\nRESULT: %d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
