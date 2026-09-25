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
  P  graduated trust, Phase 1 (helpers/memory_trust.py): the verdict and its reasons; _92's REAL
     _filter_and_decay withholds exactly `validity == deprecated`, identically with the helper and
     with it absent (the inline fallback), and hands the withheld ids over; trace's `dropped` has
     three states (absent / [] / ids); the full row carries it and early rows do not; against the
     memory_recall_tag deployed NOW (2a, trace() without `dropped`) the row is still written.
  G  GT-2a, the derivation marker: derive_source identical to the deployed version on a 72-case
     matrix that reaches every A19 rule; the source clause (marked -> stored value, unmarked ->
     `legacy`, never the stored user_asserted); the frame head, and byte-identity with HEAD's
     _with_provenance when the helper is absent; the three writers (_52, _53 driven end to end,
     _55) store source_rule with the new helper and save without it against the deployed one.
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
HELPERS = os.environ.get("TEST_HELPERS") or os.path.join(PLUGIN, "helpers")   # a mutant helpers DIR for mutation checks
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
        Area = types.SimpleNamespace(MAIN=types.SimpleNamespace(value="main"),
                                     FRAGMENTS=types.SimpleNamespace(value="fragments"),
                                     SOLUTIONS=types.SimpleNamespace(value="solutions"))

        @staticmethod
        async def get(agent):
            return Memory.result
    mem.Memory = Memory
    mods = {"agent": agent_mod, "helpers": helpers_pkg, "helpers.extension": ext,
            "helpers.history": hist, "plugins._memory.helpers.memory": mem}
    # _52's imports (settings, errors, dirty_json, log, defer): names only; its utility-model path
    # is never driven here, only the module-level _structural_source.
    for sub, attrs in (("settings", {}), ("errors", {"RepairableException": type("RepairableException", (Exception,), {})}), ("dirty_json", {"DirtyJson": type("DirtyJson", (), {})}),
                       ("log", {"LogItem": type("LogItem", (), {})}),
                       ("defer", {"DeferredTask": type("DeferredTask", (), {}), "THREAD_BACKGROUND": "bg"})):
        sm = types.ModuleType("helpers." + sub)
        for k, v in attrs.items():
            setattr(sm, k, v)
        setattr(helpers_pkg, sub, sm)
        mods["helpers." + sub] = sm
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
        self.logs = []   # extensions that swallow their errors log them here; tests print them
        self.log = types.SimpleNamespace(log=lambda **kw: self.logs.append(kw))

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


DROP = {}   # area -> ids the fake pipeline reports as trust-withheld
MARKED = set()   # ids the fake pipeline returns WITH the derivation marker (GT-2a); the rest are legacy


def fdoc(i):
    """A recalled memory as the real pipeline returns it: a doc with metadata, not a bare id."""
    cls = {"validity": "inferred", "source": "agent_inferred"}
    if i in MARKED:
        cls["source_rule"] = "A19.5"
    return types.SimpleNamespace(page_content="text " + i, metadata={"id": i, "classification": cls})


async def fake_pipeline(db, all_docs, query, bst, roles, thr, cap, area, *rest, dropped=None):
    captured.append((query, area))
    if dropped is not None:
        dropped.extend(DROP.get(area, []))
    mode = PIPE_MODE.get(area, "hit")
    if mode == "raise":
        raise RuntimeError("pipeline boom")
    return [] if mode == "empty" else [(fdoc(i), 0.9) for i in IDS[area]]


def boom(*a, **k):
    raise RuntimeError("boom")


def patch(mod):
    mod._load_config = lambda: {}
    mod._load_profile_memory_section = lambda: None
    mod._get_bst_domain = lambda agent: None
    mod._run_pipeline = fake_pipeline
    mod._with_provenance = lambda result, obs, cfg: "TXT"
    mod._update_access = lambda result, all_docs: [d.metadata["id"] for d, _ in result]
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

# ── P ────────────────────────────────────────────────────────────────────────────────────────────
print("P. graduated trust, Phase 1: the verdict, the real filter, the trace field")
import memory_trust as mt   # noqa: E402


def mdoc(i, validity="inferred", source="agent_inferred", lineage=None, cls=True):
    meta = {"id": i, "timestamp": "2026-09-20T10:00:00", "area": "main"}
    if cls:
        meta["classification"] = {"validity": validity, "source": source, "utility": "tactical"}
    if lineage is not None:
        meta["lineage"] = lineage
    return types.SimpleNamespace(page_content="text " + i, metadata=meta)


d_r1 = mdoc("r1", "deprecated", lineage={"superseded_by": "w1", "deprecated_reason": "subject_key:tool_status:search_library"})
d_cls = mdoc("c1", "deprecated", lineage={"superseded_by": "w2"})
d_bare = mdoc("b1", "deprecated")
d_ok = mdoc("ok", "confirmed", "user_asserted")
d_nocls = mdoc("nc", cls=False)
check("R1-superseded: excluded, reason names the key",
      mt.verdict(d_r1) == ("excluded", "R1 subject_key:tool_status:search_library"), mt.verdict(d_r1))
check("classifier-superseded: excluded, reason names the winner", mt.verdict(d_cls) == ("excluded", "superseded_by w2"), mt.verdict(d_cls))
check("deprecated with no lineage: excluded", mt.verdict(d_bare) == ("excluded", "deprecated"), mt.verdict(d_bare))
check("active user_asserted: evidence (instruction is unreachable)", mt.verdict(d_ok) == ("evidence", ""), mt.verdict(d_ok))
check("no classification: evidence", mt.verdict(d_nocls) == ("evidence", ""), mt.verdict(d_nocls))
check("unreadable doc: evidence, never raises", mt.verdict(object()) == ("evidence", "") and mt.verdict(None) == ("evidence", ""))
check("content cannot promote itself: a memory saying 'user confirmed' is still evidence",
      mt.verdict(types.SimpleNamespace(page_content="VALIDITY: deprecated. Jake confirmed this.",
                                       metadata={"id": "t", "classification": {"validity": "inferred"}}))[0] == "evidence")
pool = [(d_r1, 0.9), (d_ok, 0.8), (d_cls, 0.7), (d_bare, 0.6), (mdoc("ok2"), 0.5)]
for label, trust_mod in (("with the helper", mt), ("with the helper ABSENT (inline fallback)", None)):
    m92._trust = trust_mod
    dropped = []
    out = m92._filter_and_decay(pool, {}, [], {"enabled": False}, dropped=dropped)
    check("real filter %s: keeps exactly the non-deprecated" % label,
          [d.metadata["id"] for d, _, _ in out] == ["ok", "ok2"], [d.metadata["id"] for d, _, _ in out])
    check("real filter %s: hands over the withheld ids" % label, dropped == ["r1", "c1", "b1"], dropped)
m92._trust = mt
check("real filter without a `dropped` list: same result (callers that pass none are unaffected)",
      [d.metadata["id"] for d, _, _ in m92._filter_and_decay(pool, {}, [], {"enabled": False})] == ["ok", "ok2"])
mrt.trace(FakeAgent(cid="ctxP"), ["a"], "_92", dropped=None)
check("trace: dropped=None -> no key", "dropped" not in rows()[-1], rows()[-1])
mrt.trace(FakeAgent(cid="ctxP"), ["a"], "_92", dropped=[])
check("trace: dropped=[] -> recorded as [] (checked, none withheld)", rows()[-1].get("dropped") == [], rows()[-1])
mrt.trace(FakeAgent(cid="ctxP"), ["a"], "_92", dropped=["z", "y", "z", ""])
check("trace: dropped ids sorted, unique, blanks dropped", rows()[-1].get("dropped") == ["y", "z"], rows()[-1])
DROP["area != 'solutions'"] = ["r1", "c1"]
new, _ = run92(m92, FakeAgent(cid="ctxPD"), ld())
one("full _92 row carries the withheld ids", new, ids=["m1", "m2"], dropped=["c1", "r1"])
DROP.clear()
new, _ = run92(m92, FakeAgent(cid="ctxPE"), ld())
one("full _92 row with nothing withheld carries dropped []", new, dropped=[])
new, _ = run92(m92, FakeAgent(superior=object()), ld())
check("an early row carries no dropped key", bool(new) and "dropped" not in new[0], new)
mrt.trace(FakeAgent(cid="ctxP"), ["a"], "_92", legacy=["q", "p", "q", ""])
check("trace: legacy ids sorted, unique, blanks dropped", rows()[-1].get("legacy") == ["p", "q"], rows()[-1])
mrt.trace(FakeAgent(cid="ctxP"), ["a"], "_92")
check("trace: legacy=None -> no key", "legacy" not in rows()[-1], rows()[-1])
MARKED.add("m2")
new, _ = run92(m92, FakeAgent(cid="ctxPL"), ld(extras_persistent={"solutions": "A0 text"}))
MARKED.clear()
one("full _92 row lists the injected ids labelled legacy (m2 carries the marker, m1 and s1 do not)",
    new, ids=["m1", "m2", "s1"], legacy=["m1", "s1"])
m92._trust = None
new, _ = run92(m92, FakeAgent(cid="ctxPN"), ld())
m92._trust = mt
check("without the trust helper: no legacy key (no label was rendered), dropped still []",
      bool(new) and "legacy" not in new[0] and new[0].get("dropped") == [], new)
check("_accepts: a named keyword yes, an absent one no",
      m92._accepts(lambda a, dropped=None: 0, "dropped") and not m92._accepts(lambda a, dropped=None: 0, "legacy"))
check("_accepts: **kwargs takes anything", m92._accepts(lambda a, **kw: 0, "legacy"))
# The helper deployed NOW (2a, 504375e) has trace() without `dropped`: between this deploy and the
# restart, the new _92 must still write the row (retry without the field), not lose the turn.
DEPLOYED_2A = ("504375e", "305b874afbdcdd8519c1dc740a7a958a")
blob = subprocess.run(["git", "-C", REPO, "show", "%s:plugins/_exocortex/helpers/memory_recall_tag.py" % DEPLOYED_2A[0]],
                      capture_output=True, check=True).stdout
p2a = os.path.join(OLD, "memory_recall_tag_2a.py")
with open(p2a, "wb") as fh:
    fh.write(blob)
check("the 2a helper the test loads is the deployed one (md5 %s)" % DEPLOYED_2A[1][:8], md5(p2a) == DEPLOYED_2A[1], md5(p2a))
saved_mrt = sys.modules.get("memory_recall_tag")
mrt2a = sys.modules["memory_recall_tag"] = load_module("memory_recall_tag", p2a)
check("...and its trace() really lacks `dropped`", "dropped" not in mrt2a.trace.__code__.co_varnames)
DROP["area != 'solutions'"] = ["r1"]
new, out2a = run92(m92, FakeAgent(cid="ctx2A"), ld())
DROP.clear()
sys.modules["memory_recall_tag"] = saved_mrt
one("against the deployed 2a helper: the row is still written, without the field", new, ids=["m1", "m2"], context_id="ctx2A")
check("...and not marked as skipped", "Recall trace skipped" not in out2a, out2a[-300:])
check("...with neither dropped nor legacy (the 2a trace() takes neither)",
      bool(new) and "dropped" not in new[0] and "legacy" not in new[0], new)
# The helper deployed at 03:26Z (Phase 1, e958b6d) takes `dropped` but not `legacy`: between the next
# deploy and its restart the row must keep `dropped` and simply lack `legacy`. A single TypeError
# retry (the Phase 1 _92) would have lost this row; the signature check keeps it.
blob = subprocess.run(["git", "-C", REPO, "show", "e958b6d:plugins/_exocortex/helpers/memory_recall_tag.py"],
                      capture_output=True, check=True).stdout
pp1 = os.path.join(OLD, "memory_recall_tag_p1.py")
with open(pp1, "wb") as fh:
    fh.write(blob)
check("the Phase 1 helper the test loads is the deployed one (md5 d280317c)", md5(pp1)[:8] == "d280317c", md5(pp1))
saved_mrt = sys.modules.get("memory_recall_tag")
mrtp1 = sys.modules["memory_recall_tag"] = load_module("memory_recall_tag", pp1)
check("...its trace() takes dropped and not legacy",
      "dropped" in mrtp1.trace.__code__.co_varnames and "legacy" not in mrtp1.trace.__code__.co_varnames)
DROP["area != 'solutions'"] = ["r1"]
new, outp1 = run92(m92, FakeAgent(cid="ctxP1"), ld())
DROP.clear()
sys.modules["memory_recall_tag"] = saved_mrt
one("against the Phase 1 helper: the row keeps dropped", new, ids=["m1", "m2"], dropped=["r1"], context_id="ctxP1")
check("...and lacks legacy, without being skipped",
      bool(new) and "legacy" not in new[0] and "Recall trace skipped" not in outp1, (new, outp1[-200:]))

# ── G ────────────────────────────────────────────────────────────────────────────────────────────
print("G. GT-2a: the derivation marker, and the source the frame shows")
import collections                  # noqa: E402
from datetime import datetime, timezone   # noqa: E402
import memory_source as ms_new      # noqa: E402  the working-tree helper
MONO = os.path.join(PLUGIN, "extensions", "python", "monologue_end")
# What agent-zero-v2 runs now, byte-identical to HEAD 504375e (docker exec md5sum, 2026-09-25).
DEPLOYED_G = {"memory_source.py": ("helpers/memory_source.py", "73c6c896"),
              "_92_head.py": ("extensions/python/message_loop_prompts_after/_92_memory_enhancement.py", None)}
for name, (rel, want) in DEPLOYED_G.items():
    blob = subprocess.run(["git", "-C", REPO, "show", "504375e:plugins/_exocortex/" + rel], capture_output=True, check=True).stdout
    with open(os.path.join(OLD, name), "wb") as fh:
        fh.write(blob)
    if want:
        check("deployed %s is what the test loads (md5 %s)" % (name, want), md5(os.path.join(OLD, name))[:8] == want,
              md5(os.path.join(OLD, name)))
ms_old = load_module("memory_source_deployed", os.path.join(OLD, "memory_source.py"))
check("the deployed memory_source really lacks derive_source_rule", not hasattr(ms_old, "derive_source_rule"))

UM = "I prefer small reviewable changes for every deploy we do"
TOOL = "search_library returned results for the library query alpha beta gamma"
agents = {"interactive": FakeAgent(), "idle": FakeAgent(idle=True), "subordinate": FakeAgent(superior=object())}
texts = {"from_user": UM, "own_words": "The deploy pipeline needs a restart after helper edits", "from_tool": TOOL}
tools = {"none": (), "tool": (TOOL + " delta epsilon",)}
mismatch, rules_seen, n_combo = [], collections.Counter(), 0
for an, ag in agents.items():
    for tn, tx in texts.items():
        for kn, tt in tools.items():
            for ar in ("main", "solutions"):
                for msg in (UM, ""):
                    n_combo += 1
                    old = ms_old.derive_source(ag, tx, user_msg=msg, tool_texts=tt, area=ar)
                    new = ms_new.derive_source(ag, tx, user_msg=msg, tool_texts=tt, area=ar)
                    src, rule = ms_new.derive_source_rule(ag, tx, user_msg=msg, tool_texts=tt, area=ar)
                    rules_seen[rule] += 1
                    if not (old == new == src):
                        mismatch.append((an, tn, kn, ar, bool(msg), old, new, src))
check("derive_source: identical to the deployed version on all %d combinations" % n_combo, not mismatch, mismatch[:3])
check("the matrix reaches every A19 rule (%s)" % dict(sorted(rules_seen.items())),
      set(rules_seen) == {"A19.1", "A19.2", "A19.3", "A19.4", "A19.5"}, rules_seen)
check("rule ids: user words in a chat = A19.4; in an idle cycle = A19.1 (gate withheld user_asserted)",
      ms_new.derive_source_rule(agents["interactive"], UM, user_msg=UM) == ("user_asserted", "A19.4")
      and ms_new.derive_source_rule(agents["idle"], UM, user_msg=UM) == ("agent_inferred", "A19.1"))


def cdoc(src, rule=None, validity="inferred", body="body text"):
    cls = {"source": src, "validity": validity}
    if rule:
        cls["source_rule"] = rule
    return types.SimpleNamespace(page_content=body, metadata={"id": "x", "timestamp": "2026-09-20T10:00:00-04:00",
                                                              "classification": cls})


check("marked source is shown", mt.source_clause(cdoc("agent_inferred", "A19.5")) == "source: agent_inferred")
check("UNMARKED user_asserted renders legacy, never its stored value (all 209 today)",
      mt.source_clause(cdoc("user_asserted")) == "source: legacy")
check("unmarked external_retrieved (the 7 post-R2 saves) renders legacy", mt.source_clause(cdoc("external_retrieved")) == "source: legacy")
check("no classification renders legacy", mt.source_clause(types.SimpleNamespace(metadata={})) == "source: legacy")
check("render_trust: evidence with the source clause", mt.render_trust(cdoc("user_asserted", "A19.4")) == ("evidence", ["source: user_asserted"]))
check("render_trust: excluded gets no clauses (never rendered)",
      mt.render_trust(cdoc("agent_inferred", "A19.5", validity="deprecated")) == ("excluded", []))
NOW = datetime(2026, 9, 25, tzinfo=timezone.utc)
m92f = load_module("ext92_frame", EXT92)   # unpatched: E and O replaced _with_provenance with a stub
m92f._mt = None
m92f._trust = mt
t1 = m92f._with_provenance([(cdoc("agent_inferred", "A19.5"), 0.9)], {}, {}, now=NOW)
check("frame: the source joins the existing head, after the date",
      t1.split("\n")[0] == "recalled memory (saved 2026-09-20; source: agent_inferred):", t1.split("\n")[0])
check("frame: the passage body is unchanged, below the head", t1.split("\n", 1)[1] == "body text", t1)
t2 = m92f._with_provenance([(cdoc("user_asserted"), 0.9)], {}, {}, now=NOW).split("\n")[0]
check("frame: an unmarked user_asserted shows legacy and not the word user_asserted",
      t2 == "recalled memory (saved 2026-09-20; source: legacy):" and "user_asserted" not in t2, t2)
m92f._trust = None
m92h = load_module("ext92_head", os.path.join(OLD, "_92_head.py"))
m92h._mt = None
batch = [(cdoc("agent_inferred", "A19.5"), 0.9), (cdoc("user_asserted", body="second"), 0.5)]
check("frame with the helper ABSENT: byte-identical to HEAD's _with_provenance",
      m92f._with_provenance(batch, {}, {}, now=NOW) == m92h._with_provenance(batch, {}, {}, now=NOW))
m92f._trust = mt
# The head's date WORD follows its field (Opus's ruling, 2026-09-25). A0 core consolidation rewrites
# `timestamp` to the merge time; NbamS6iC4q (a 09-24 memory merged 09-25) is the live shape.


def hdoc(observed, ts="2026-09-25T11:14:17-04:00"):
    meta = {"id": "x", "timestamp": ts, "classification": {"source": "agent_inferred", "validity": "inferred"}}
    if observed is not None:
        meta["observed_at"] = observed
    return types.SimpleNamespace(page_content="merged body", metadata=meta)


head = lambda d: m92f._with_provenance([(d, 0.9)], {}, {}, now=NOW).split("\n")[0]
check("head: a merged memory reads 'observed <observed_at date>', not 'saved <today>'",
      head(hdoc("2026-09-24T11:47:57.189727+00:00")) == "recalled memory (observed 2026-09-24; source: legacy):",
      head(hdoc("2026-09-24T11:47:57.189727+00:00")))
check("head: never 'saved' with an observation date, never 'observed' with a save date",
      "saved 2026-09-24" not in head(hdoc("2026-09-24T11:47:57+00:00")) and head(hdoc(None)).startswith("recalled memory (saved 2026-09-25"))
check("head: a malformed observed_at falls back to 'saved <timestamp date>'",
      head(hdoc("yesterday")) == "recalled memory (saved 2026-09-25; source: legacy):" and head(hdoc("")) == head(hdoc(None)),
      (head(hdoc("yesterday")), head(hdoc(""))))
check("head: no date at all still says so", head(hdoc(None, ts="")) == "recalled memory (save date unknown; source: legacy):",
      head(hdoc(None, ts="")))

m52 = load_module("ext52", os.environ.get("TEST_EXT52") or os.path.join(MONO, "_52_selective_memorizer.py"))
for label, mod, want in (("new helper", ms_new, ("user_asserted", "confirmed", "A19.4")),
                         ("DEPLOYED helper (no marker function)", ms_old, ("user_asserted", "confirmed", None))):
    m52._ms = mod
    try:   # in production _52's outer try would swallow an error here and LOSE the save
        got = m52._structural_source(FakeAgent(), UM, UM, (), "main")
    except Exception as e:
        got = "raised %s: %s" % (type(e).__name__, e)
    check("_52 with the %s: %s" % (label, want), got == want, got)
m52._ms = None
check("_52 with no helper: None (the model's label stands, as before)", m52._structural_source(FakeAgent(), UM, UM, (), "main") is None)

m55 = load_module("ext55", os.path.join(MONO, "_55_memory_classifier.py"))
for label, mod, rule in (("new helper", ms_new, "A19.4"), ("DEPLOYED helper", ms_old, None)):
    m55._ms = mod
    cl = m55._classify(types.SimpleNamespace(page_content=UM, metadata={"area": "main"}), UM, m55.DEFAULT_CONFIG,
                       agent=FakeAgent(), tool_texts=())
    check("_55 with the %s: source user_asserted, source_rule %s" % (label, rule),
          cl.get("source") == "user_asserted" and cl.get("source_rule") == rule and (rule or "source_rule" not in cl), cl)

m53 = load_module("ext53", os.path.join(MONO, "_53_insight_capture.py"))
inserted = []


class InsertDB:
    async def insert_text(self, text, metadata):
        inserted.append((text, metadata))
        return "new-id"


async def never_dup(db, text):
    return False


m53._is_duplicate = never_dup
for label, mod, agent, want in (("new helper, a chat with Jake", ms_new, FakeAgent(), ("user_asserted", "A19.4")),
                                ("DEPLOYED helper", ms_old, FakeAgent(), ("user_asserted", None)),
                                ("new helper, an idle cycle", ms_new, FakeAgent(idle=True), None)):
    m53._ms = mod
    inserted.clear()
    Memory.result = InsertDB()
    asyncio.run(m53.ConversationalInsightCapture(agent=agent).execute(loop_data=LoopData(user_message=Msg(UM + "."))))
    if want is None:
        check("_53 with the %s: nothing captured (rule 1)" % label, inserted == [], inserted)
        continue
    cl = inserted[0][1]["classification"] if inserted else {}
    check("_53 with the %s: source %s, source_rule %s" % (label, want[0], want[1]),
          len(inserted) == 1 and cl.get("source") == want[0] and cl.get("source_rule") == want[1]
          and (want[1] or "source_rule" not in cl), (inserted, agent.context.logs))

# Structural writers outside A19 stamp their mechanism (Opus's ruling, 2026-09-25: source_rule means
# "structurally derived by <mechanism>", not "went through derive_source_rule").
m36 = load_module("ext36", os.environ.get("TEST_EXT36") or os.path.join(PLUGIN, "extensions", "python", "tool_execute_after",
                                                                          "_36_status_writer.py"))
txt36, meta36 = m36.build_memory("search_library", "exocortex_memory.list_collections", "up",
                                 "list_collections returned humble_bundle", datetime(2026, 9, 25, 15, 6, 35, tzinfo=timezone.utc))
check("_36 status writer stamps source_rule A13 (source external_retrieved)",
      (meta36["classification"].get("source"), meta36["classification"].get("source_rule")) == ("external_retrieved", "A13"),
      meta36["classification"])
check("...so the frame shows its source, not legacy (DGGdspk8st's case)",
      mt.source_clause(types.SimpleNamespace(metadata=meta36)) == "source: external_retrieved")
mont = load_module("ont_store", os.environ.get("TEST_ONT") or os.path.join(HELPERS, "ontology", "ontology_store.py"))
check("ontology DEFAULT_CLASSIFICATION carries source_rule ontology", mont.DEFAULT_CLASSIFICATION.get("source_rule") == "ontology",
      mont.DEFAULT_CLASSIFICATION)
ENT = {"entity_type": "tool", "properties": {"name": "search_library"}, "provenance": {"confidence": 0.9}}
for k in ("python", "python.helpers", "python.helpers.memory"):
    sys.modules.pop(k, None)
with contextlib.redirect_stdout(io.StringIO()):
    severed = asyncio.run(mont.store_entity(FakeAgent(), ENT))
check("ontology store_entity is SEVERED where python.helpers.memory is absent (as in her container): returns ''",
      severed == "", severed)
captured_ent = []


class OntDB:
    async def insert_text(self, text, metadata):
        captured_ent.append(metadata)
        return "ent-mem"


class OldPathMemory:
    @staticmethod
    async def get(agent):
        return OntDB()


_py, _pyh, _pym = types.ModuleType("python"), types.ModuleType("python.helpers"), types.ModuleType("python.helpers.memory")
_py.__path__, _pyh.__path__, _pym.Memory = [], [], OldPathMemory
sys.modules.update({"python": _py, "python.helpers": _pyh, "python.helpers.memory": _pym})
with contextlib.redirect_stdout(io.StringIO()):
    eid = asyncio.run(mont.store_entity(FakeAgent(), ENT))
for k in ("python", "python.helpers", "python.helpers.memory"):
    sys.modules.pop(k, None)
check("...and where that import resolves, the entity memory it writes carries source_rule ontology",
      bool(eid) and bool(captured_ent) and captured_ent[0]["classification"].get("source_rule") == "ontology", captured_ent[:1])

# ── H ────────────────────────────────────────────────────────────────────────────────────────────
print("H. _19 check 1: a save that copies the injected block (head line + body) is the same text")
E19 = os.environ.get("TEST_EXT19") or os.path.join(PLUGIN, "extensions", "python", "tool_execute_before",
                                                    "_19_memory_resave_gate.py")
GATE = os.path.join(TMP, "resave_gate.jsonl")
os.environ["EXO_RESAVE_GATE_LOG"] = GATE   # read when _19 is imported
m19 = load_module("ext19", E19)
BODY = "The library answered the probe at 02:00Z and search_library returned 5 results."
BODY2 = "Cycle 740 closed the MAINTAIN pass with two promotions and no deprecations."
HEAD = ("recalled memory (saved 2026-09-20; source: legacy; mentions search_library; a newer observation "
        "exists: up (probe ok), observed 2 hours ago):")
check("strip: one head line removed, parens inside the head included", m19.strip_recall_head(HEAD + "\n" + BODY) == BODY)
check("strip: the undated head form too",
      m19.strip_recall_head("recalled memory (save date unknown; source: legacy):\n" + BODY) == BODY)
check("strip: text without a head is unchanged", m19.strip_recall_head(BODY) == BODY)
check("strip: a look-alike that is not the head is unchanged",
      m19.strip_recall_head("recalled memory (my notes):\n" + BODY) == "recalled memory (my notes):\n" + BODY)
check("strip: only ONE head is removed", m19.strip_recall_head(HEAD + "\n" + HEAD + "\n" + BODY) == HEAD + "\n" + BODY)


def run19(text, recalled_ids=("m1",)):
    a = FakeAgent(cid="ctx19")
    mrt.tag(a, list(recalled_ids))
    store = {"m1": types.SimpleNamespace(page_content=BODY, metadata={"id": "m1", "timestamp": "2026-09-20T10:00:00-04:00"}),
             "m2": types.SimpleNamespace(page_content=BODY2, metadata={"id": "m2", "timestamp": "2026-09-21T10:00:00-04:00"})}
    Memory.result = types.SimpleNamespace(db=types.SimpleNamespace(get_all_docs=lambda: store))
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            asyncio.run(m19.MemoryResaveGate(agent=a).execute(tool_name="memory_save", tool_args={"text": text}))
            return None
        except Exception as e:
            return e


e = run19(BODY)
check("body copied alone: refused word for word (unchanged behaviour)",
      type(e).__name__ == "RepairableException" and "word for word" in str(e) and "recall head" not in str(e), e)
e = run19(HEAD + "\n" + BODY)
check("head line + body copied: refused, recall head included (the 09-08 mechanism, closed)",
      type(e).__name__ == "RepairableException" and "recall head included" in str(e), e)
check("head line + NEW text: saved", run19(HEAD + "\nSomething new happened today that is not in the store.") is None)
check("look-alike line + body: saved (not our head; scope as designed)", run19("recalled memory (my notes):\n" + BODY) is None)
check("head line + body of a memory NOT recalled this monologue: saved (only recalled memories count)",
      run19(HEAD + "\n" + BODY, recalled_ids=()) is None)


def gate_rows():
    if not os.path.exists(GATE):
        return []
    with open(GATE, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


check("the gate ledger writes where the test says (the env var is read at import)", m19.GATE_LOG == GATE, m19.GATE_LOG)
g0 = len(gate_rows())
run19(BODY)
g = gate_rows()[g0:]
check("ledger: a verbatim refusal is one row with the id it matched",
      len(g) == 1 and (g[0]["memory_id"], g[0]["rule"], g[0]["refused"], g[0]["context_id"]) == ("m1", "verbatim", True, "ctx19"), g)
g0 = len(gate_rows())
run19(HEAD + "\n" + BODY)
g = gate_rows()[g0:]
check("ledger: a head+body refusal says so", len(g) == 1 and (g[0]["rule"], g[0]["refused"]) == ("verbatim_with_head", True), g)
g0 = len(gate_rows())
tail_text = HEAD + "\n" + BODY + "\nAnd since then the index was rebuilt."
res = run19(tail_text)
g = gate_rows()[g0:]
check("shadow: a save CONTAINING a recalled body goes through", res is None, res)
check("shadow: ...and is logged would-refuse containment, with both lengths",
      len(g) == 1 and (g[0]["memory_id"], g[0]["rule"], g[0]["refused"]) == ("m1", "containment", False)
      and g[0]["chars_recalled"] == len(m19.normalize(BODY)) and g[0]["chars_incoming"] == len(m19.normalize(tail_text)), g)
g0 = len(gate_rows())
res = run19(HEAD + "\n" + BODY + "\n\n" + HEAD + "\n" + BODY2, recalled_ids=("m1", "m2"))
g = gate_rows()[g0:]
check("shadow: a multi-block copy passes and logs one row per contained body (the case the strip leaves)",
      res is None and sorted(r["memory_id"] for r in g) == ["m1", "m2"] and all(r["rule"] == "containment" for r in g), (res, g))
g0 = len(gate_rows())
run19(HEAD + "\nSomething new happened today that is not in the store.")
run19(HEAD + "\n" + BODY + " plus more", recalled_ids=())
check("ledger: nothing is written for a clean save, or for a body that was not recalled", len(gate_rows()) == g0,
      gate_rows()[g0:])
saved_gate = m19.GATE_LOG
m19.GATE_LOG = TMP            # a directory: the write fails
res = run19(tail_text)
m19.GATE_LOG = saved_gate
check("ledger write failure: the save still goes through (fails open)", res is None, res)

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
    T("2026-09-25T02:01:00Z", "B", ["m1", "m2", "m7"], source="idle_charge", dropped=["x9", "x8"], legacy=["m1", "m7"]),
    T("2026-09-25T02:02:00Z", "B", ["m1", "m2", "m7"], source="idle_charge", turn=1, dropped=[], legacy=[]),
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
gate_fx = [
    {"at": "2026-09-25T01:04:30Z", "context_id": "A", "agent": 0, "memory_id": "m1", "rule": "verbatim", "refused": True},
    {"at": "2026-09-25T02:05:00Z", "context_id": "B", "agent": 0, "memory_id": "m1", "rule": "containment",
     "refused": False, "chars_incoming": 300, "chars_recalled": 80},
    {"at": "2026-09-25T02:06:00Z", "context_id": "B", "agent": 0, "memory_id": "m7", "rule": "containment",
     "refused": False, "chars_incoming": 300, "chars_recalled": 60},
    {"at": "2026-09-25T02:31:00Z", "context_id": "C", "agent": 0, "memory_id": "m5", "rule": "verbatim_with_head",
     "refused": True},
]
pg = wj("gate.jsonl", gate_fx)
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
# Graduated trust: the withheld counts, with pre-Phase-1 rows kept apart rather than read as 0.
check("withheld: 2 ids from the one row that lists them",
      (cov["dropped_total"], cov["dropped_distinct"]) == (2, 2), (cov["dropped_total"], cov["dropped_distinct"]))
check("withheld: 2 full rows carry the field ([] counts as carrying it); 5 predate it",
      (cov["full_92_with_dropped_field"], cov["full_92_without_dropped_field"]) == (2, 5),
      (cov["full_92_with_dropped_field"], cov["full_92_without_dropped_field"]))
check("withheld: cycle B shows 2 (2 distinct); cycle A shows 0",
      (B.get("dropped"), B.get("dropped_distinct"), A.get("dropped")) == (2, 2, 0), (B, A))
check("labelled legacy: 2 of the 6 injected ids on the 2 rows carrying the field",
      (cov["legacy_total"], cov["injected_on_legacy_rows"], cov["full_92_with_legacy_field"]) == (2, 6, 2),
      (cov["legacy_total"], cov["injected_on_legacy_rows"], cov["full_92_with_legacy_field"]))
check("labelled legacy per cycle: B 2 over 2 rows; A has no row carrying it (shown as n/a, not 0)",
      (B.get("legacy"), B.get("legacy_rows"), A.get("legacy_rows")) == (2, 2, 0), (B, A))
# The save gate's ledger, attributed like trace rows (Opus's A20 amendment + Fable's shadow check).
rep_g = rep_mod.build_report(tr, en, jo, gate_rows=rep_mod.load(pg)[0])
cg = {c["context_id"]: c["gate"] for c in rep_g["cycles"]}
check("gate totals: refused by rule, would-refuse counted apart",
      rep_g["gate"] == {"state": "ok", "refused": {"verbatim": 1, "verbatim_with_head": 1}, "would_refuse": 2}, rep_g["gate"])
check("gate per cycle: A refused 1 verbatim; B would-refuse 2 (containment), refused none",
      cg.get("A") == {"refused": {"verbatim": 1}, "would_refuse": 0} and cg.get("B") == {"refused": {}, "would_refuse": 2}, cg)
check("gate not given -> 'not read'; given but empty -> 'no events in the window'",
      rep["gate"]["state"] == "not read" and rep_mod.build_report(tr, en, jo, gate_rows=[])["gate"]["state"] == "no events in the window",
      (rep["gate"], rep_mod.build_report(tr, en, jo, gate_rows=[])["gate"]))


def cli(*args):
    r_ = subprocess.run([sys.executable, REPORT] + list(args), capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    return r_.returncode, r_.stdout, r_.stderr


code, out, err = cli("--trace", pt, "--endings", pe, "--journal", pj)
check("CLI: exit 0 on the fixtures", code == 0, (code, (out + err)[-300:]))
check("CLI: prints the NO-TOOL flag and the A17 line", "NO-TOOL" in out and "A17" in out, out[:400])
check("CLI without --gate: the save-gate line says 'not read'", "save gate (_19)    not read" in out, out[-900:])
code_g, out_g, err_g = cli("--trace", pt, "--endings", pe, "--journal", pj, "--gate", pg)
check("CLI with --gate: refused and would-refuse printed side by side",
      code_g == 0 and "would-refuse (containment) 2" in out_g and "save gate: refused {}  would-refuse (containment) 2" in out_g,
      (code_g, out_g[-900:]))
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
