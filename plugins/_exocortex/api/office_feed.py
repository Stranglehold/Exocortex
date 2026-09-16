"""
Office Feed API Handler — v2
============================
Serves idle-time engine data for the Office panel.

Route (auto-registered by A0's dispatch): GET /api/plugins/_exocortex/office_feed

v1 (2026-05) returned entries / total_cycles / status / enabled. Those stay, unchanged, until
EXO·OPS is retired — the existing panel reads them.

v2 (2026-09-14, contract §6.2 of Fable's office-pane study) adds `v`, `generated_at`, and one
ENVELOPE PER SOURCE:

    {"value": <...>, "at": "<UTC when read or produced>", "age_s": <int>, "state": "ok"|"stale"|"unverified", "reason": "<why, when not ok>"}

WHY ENVELOPES, WHICH IS THE WHOLE POINT OF v2
---------------------------------------------
On 2026-09-14 the Office badge read "Working" through three consecutive dead cycles. Not because
the check was wrong — because the pane had one state for "I looked and it is working" and NO
state for "I could not look". An omitted field renders as fine in every UI ever written, and a
cached value with no age renders as current. So: nothing here is ever omitted, nothing carries a
last good value without an age beside it, and a source that could not be read says so, in a
sentence written for a human rather than a status code.

Every source is read independently. Six sources with six failure modes behind one blob gives a
pane that is wholly present or wholly absent, and neither of those is the truth.

NOTHING HERE FETCHES OVER THE NETWORK IN THE REQUEST PATH. The model state is READ from a file
the watcher refreshes on its own clock. That is deliberate: LM Studio is slowest under exactly
the conditions this pane exists to display, so an inline fetch would hang precisely when it
matters most. (2026-09-14: a client that gave up at 20 s left the server working for 752 s.)
The one in-process call, MCPConfig, is bounded by a thread with a 2 s join — it cannot be made
to block the page.
"""

import importlib.util
import json
import os
import threading
import time
from datetime import datetime, timezone

from helpers.api import ApiHandler, Request, Response

_OFFICE = "/a0/usr/workdir/workspace/office"
_FEED_PATH = _OFFICE + "/feed.jsonl"
_STATUS_PATH = _OFFICE + "/status.json"
_CONTROL_PATH = _OFFICE + "/control.json"
_ENGINE_STATE_PATH = _OFFICE + "/engine_state.json"
_MODEL_STATE_PATH = _OFFICE + "/model_state.json"
_ENDINGS_PATH = _OFFICE + "/cycle_endings.jsonl"
_CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"
_PROMPT_PATH = "/a0/usr/plugins/_exocortex/prompts/idle_activation.md"
_JOURNAL_PATH = "/a0/usr/workdir/workspace/self-improvement/journal.jsonl"
_CANDIDATES_PATH = "/a0/usr/workdir/workspace/self-improvement/threads_candidates.jsonl"
_WIKI_RESEARCH = "/a0/usr/workdir/workspace/wiki/research"
_CW_PATH = "/a0/usr/plugins/_exocortex/helpers/cycle_windows.py"

_MAX_ENTRIES = 50
_MAX_ENDINGS = 50
_MODEL_STALE_S = 120
_ENGINE_STALE_S = 60
_MCP_DEADLINE_S = 2.0

# The shared module is loaded BY PATH, not by `from helpers... import`: /a0/usr/plugins/_exocortex
# is on sys.path in some contexts, and a top-level `helpers` there would shadow A0's own helpers
# package. An explicit path cannot collide, and it fails loudly here rather than subtly elsewhere.
_CW = None
_CW_ERR = ""
try:
    _spec = importlib.util.spec_from_file_location("exo_cycle_windows", _CW_PATH)
    _CW = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_CW)
except Exception as _e:
    _CW_ERR = "%s: %s" % (type(_e).__name__, _e)


def _now():
    return datetime.now(timezone.utc)


def _iso(dt_or_ts):
    if dt_or_ts is None:
        return None
    if isinstance(dt_or_ts, (int, float)):
        if not dt_or_ts:
            return None
        dt_or_ts = datetime.fromtimestamp(dt_or_ts, tz=timezone.utc)
    return dt_or_ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _env(value, at=None, state="ok", reason="", **extra):
    """One envelope. `at` is when the value was READ OR PRODUCED — not when this response was
    assembled, which would make every stale value look fresh."""
    now = _now()
    at_dt = at
    if isinstance(at, str):
        at_dt = _CW.parse_ts(at) if _CW else None
    elif isinstance(at, (int, float)):
        at_dt = datetime.fromtimestamp(at, tz=timezone.utc) if at else None
    age = int((now - at_dt).total_seconds()) if at_dt else None
    out = {"value": value, "at": _iso(at_dt) if at_dt else _iso(now),
           "age_s": age, "state": state, "reason": reason}
    out.update(extra)
    return out


def _unverified(reason, **extra):
    return _env(None, at=_now(), state="unverified", reason=reason, **extra)


def _read_json(path):
    """(data, mtime) — mtime is the freshness the envelope reports. Raises to the caller so the
    envelope can name the failure rather than silently substituting a default."""
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f), os.path.getmtime(path)


class OfficeFeed(ApiHandler):
    """GET /api/plugins/_exocortex/office_feed — the Office pane's whole data surface."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        out = _v1_fields()
        out["v"] = 2
        out["generated_at"] = _iso(_now())
        if _CW is None:
            why = "shared module cycle_windows.py did not load (%s)" % (_CW_ERR or "unknown")
            for k in ("engine", "rotation", "mcp", "model", "prompt", "control", "endings", "ledger"):
                out[k] = _unverified(why)
            return out
        state, state_mtime = _safe(_read_json, _ENGINE_STATE_PATH)
        cfg, _ = _safe(_read_json, _CONFIG_PATH)
        endings, endings_env = _endings_envelope()
        out["engine"] = _engine_envelope(state, state_mtime, endings)
        out["rotation"] = _rotation_envelope(state, cfg)
        out["mcp"] = _mcp_envelope()
        out["model"] = _model_envelope()
        out["prompt"] = _prompt_envelope()
        out["control"] = _control_envelope(cfg)
        out["endings"] = endings_env
        out["ledger"] = _ledger_envelope(endings)
        return out


def _safe(fn, *a):
    try:
        return fn(*a)
    except Exception:
        return None, None


# ── engine ───────────────────────────────────────────────────────────────────────────────────

def _engine_envelope(state, mtime, endings):
    if state is None:
        return _unverified("engine_state.json could not be read — the engine's own state file is "
                           "missing or malformed, so nothing here can be said about the cycle")
    try:
        value = _CW.now_zone(state)
    except Exception as e:
        return _unverified("now_zone failed on engine_state: %s: %s" % (type(e).__name__, e))
    # Budget: from the `fired` ledger row for THIS context, not from a duplicated table. The row
    # records the budget the cycle was actually fired with, which is the only one that is true.
    value["budget"] = None
    ctx = value.get("context_id")
    if ctx and endings:
        for r in reversed(endings):
            if r.get("event") == "fired" and r.get("context_id") == ctx:
                value["budget"] = r.get("budget")
                break
    # steps_used has NO live source: it is self-reported at close and nothing counts it during a
    # cycle. Reporting the last cycle's number here would be a true value about the wrong cycle,
    # which is the adjacent-fact error with a display attached. So: null, and say why.
    value["steps_used"] = None
    reason = ""
    st = "ok"
    if mtime and (time.time() - mtime) > _ENGINE_STALE_S:
        st = "stale"
        reason = "engine_state.json has not been rewritten for %ds — the daemon polls every 60s, " \
                 "so it may be stopped" % int(time.time() - mtime)
    if value.get("active"):
        reason = (reason + " " if reason else "") + \
            "steps_used is null by design: it is only self-reported at close, and there is no " \
            "live counter to read during a cycle."
    return _env(value, at=mtime, state=st, reason=reason)


# ── rotation ─────────────────────────────────────────────────────────────────────────────────

def _rotation_envelope(state, cfg):
    if state is None or cfg is None:
        return _unverified("rotation needs both engine_state.json and config.json; "
                           "%s could not be read" % ("engine_state.json" if state is None else "config.json"))
    ite = cfg.get("idle_time_engine", {}) or {}
    maintain_t = int(ite.get("maintain_cooldown_threshold", 3) or 0)
    explore_cap = int(ite.get("explore_time_cap_cycles", 5) or 0)
    synth_after = int(ite.get("synthesize_after_builds", 0) or 0)
    seq, sim = [], {"consecutive_maintain_count": 0, "build_cycle_count": 0, "last_cycle_type": ""}
    for _ in range(maintain_t + explore_cap + 2):
        t = _select(sim, maintain_t, explore_cap, synth_after)
        seq.append(t)
        sim["last_cycle_type"] = t
        if t == "MAINTAIN":
            sim["consecutive_maintain_count"] += 1
        elif t in ("BUILD", "SYNTHESIZE"):
            sim["build_cycle_count"] += 1
        if t == "EXPLORE":
            break
    live = {"consecutive_maintain_count": state.get("consecutive_maintain_count", 0),
            "build_cycle_count": state.get("build_cycle_count", 0),
            "last_cycle_type": state.get("last_cycle_type", "")}
    nxt = _select(live, maintain_t, explore_cap, synth_after)
    pos = None
    for i, t in enumerate(seq):
        if t == nxt:
            pos = i
            break
    value = {"sequence": seq, "position": pos, "next": nxt,
             "maintain_cooldown_threshold": maintain_t,
             "explore_time_cap_cycles": explore_cap,
             "synthesize_after_builds": synth_after,
             "consecutive_maintain_count": live["consecutive_maintain_count"],
             "build_cycle_count": live["build_cycle_count"]}
    reason = ""
    if synth_after and synth_after >= explore_cap:
        reason = ("synthesize_after_builds=%d is not below explore_time_cap_cycles=%d, so the "
                  "explore branch wins first and SYNTHESIZE can never fire" % (synth_after, explore_cap))
    return _env(value, at=_now(), state="ok" if not reason else "stale", reason=reason)


def _select(st, maintain_t, explore_cap, synth_after):
    """A faithful copy of idle_watch._select_cycle_type's ORDER. The watcher is the authority;
    this exists so the pane can say what fires next without importing a daemon that opens locks.
    If the watcher's order changes and this does not, the pane states the wrong next action as
    fact — so any change there is a change here."""
    if st.get("consecutive_maintain_count", 0) < maintain_t:
        return "MAINTAIN"
    if st.get("build_cycle_count", 0) >= explore_cap:
        return "EXPLORE"
    if synth_after and st.get("build_cycle_count", 0) >= synth_after \
            and st.get("last_cycle_type") != "SYNTHESIZE":
        return "SYNTHESIZE"
    return "BUILD"


# ── mcp ──────────────────────────────────────────────────────────────────────────────────────

def _mcp_envelope():
    """The ONLY door: MCPConfig lives in this process and a script cannot reach it (the status
    endpoints are CSRF-gated to a browser session — measured 403 on 2026-09-14). Bounded by a
    thread join so a wedged client cannot hold the page: the wedge is the thing being reported."""
    box = {}

    def run():
        try:
            from helpers.mcp_handler import MCPConfig
            box["v"] = MCPConfig.get_instance().get_servers_status()
        except Exception as e:
            box["e"] = "%s: %s" % (type(e).__name__, e)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(_MCP_DEADLINE_S)
    if t.is_alive():
        return _unverified("MCPConfig.get_servers_status did not return within %.0fs — the client "
                           "layer is busy or wedged, which is itself the finding" % _MCP_DEADLINE_S)
    if "e" in box:
        return _unverified("MCPConfig raised: %s" % box["e"])
    rows = []
    for s in (box.get("v") or []):
        if not isinstance(s, dict):
            continue
        # `tool_count`, not `tools` — measured against helpers/mcp_handler.get_servers_status,
        # which builds {name, scope, type, description, connected, error, tool_count, has_log}.
        # Reading a key that is not there returns None silently, and a null tool count on a
        # connected server reads as "up but empty", which is a different and wrong finding.
        rows.append({"name": s.get("name"),
                     "connected": bool(s.get("connected")),
                     "tools": s.get("tool_count"),
                     "error": s.get("error") or None})
    return _env(rows, at=_now(), state="ok")


# ── model, prompt, control ───────────────────────────────────────────────────────────────────

def _model_envelope():
    data, mtime = _safe(_read_json, _MODEL_STATE_PATH)
    if data is None:
        return _unverified("office/model_state.json is absent — the watcher writes it every 60s, "
                           "so either the daemon is stopped or it has never completed a refresh")
    if data.get("state") != "ok":
        return _env({"loaded": data.get("loaded") or [], "fetched_at": data.get("fetched_at")},
                    at=data.get("fetched_at") or mtime, state="unverified",
                    reason="the watcher could not reach LM Studio: %s" % (data.get("reason") or "no reason recorded"))
    # ONE clock for both the age and the verdict. fetched_at is when the value was produced, so it
    # is the honest one; mtime is the fallback. Deriving `state` from mtime while `age_s` came from
    # fetched_at let the envelope say "stale" beside a NEGATIVE age — two sources disagreeing
    # inside one answer, which is the shape the envelopes exist to stop.
    at = data.get("fetched_at") or mtime
    at_dt = _CW.parse_ts(at) if isinstance(at, str) else (
        datetime.fromtimestamp(at, tz=timezone.utc) if at else None)
    age = int((_now() - at_dt).total_seconds()) if at_dt else None
    if age is None:
        return _env({"loaded": data.get("loaded") or [], "fetched_at": data.get("fetched_at")},
                    at=mtime, state="unverified",
                    reason="model_state.json carries no readable fetched_at, so its age is unknown")
    if age < 0:
        st, reason = "unverified", ("model_state.json is stamped %ds in the FUTURE — a clock "
                                    "disagreement, so its age cannot be trusted" % -age)
    elif age > _MODEL_STALE_S:
        st, reason = "stale", ("model_state.json is %ds old against a 60s refresh — the daemon "
                               "may be stopped" % age)
    else:
        st, reason = "ok", ""
    return _env({"loaded": data.get("loaded") or [], "fetched_at": data.get("fetched_at")},
                at=at, state=st, reason=reason)


def _prompt_envelope():
    try:
        import hashlib
        with open(_PROMPT_PATH, "rb") as f:
            raw = f.read()
        return _env({"md5_short": hashlib.md5(raw).hexdigest()[:8],
                     "mtime": _iso(os.path.getmtime(_PROMPT_PATH))},
                    at=os.path.getmtime(_PROMPT_PATH), state="ok")
    except Exception as e:
        return _unverified("idle_activation.md could not be read: %s: %s" % (type(e).__name__, e))


def _control_envelope(cfg):
    data, mtime = _safe(_read_json, _CONTROL_PATH)
    if data is None:
        return _unverified("office/control.json could not be read, so neither the pause nor the "
                           "arm can be reported")
    enabled = bool((cfg or {}).get("idle_time_engine", {}).get("enabled", False)) if cfg else None
    paused = data.get("paused_until") or 0
    value = {"enabled": enabled,
             "paused_until": _iso(paused) if paused and paused > time.time() else None,
             "pause_reason": data.get("pause_reason") or None,
             "armed_at": _iso(data.get("armed_at") or 0)}
    reason = "" if cfg is not None else "config.json unreadable, so `enabled` is null rather than false"
    return _env(value, at=mtime, state="ok" if cfg is not None else "stale", reason=reason)


# ── endings and ledger ───────────────────────────────────────────────────────────────────────

def _endings_envelope():
    if not os.path.exists(_ENDINGS_PATH):
        return [], _unverified("office/cycle_endings.jsonl does not exist yet — the watcher writes "
                               "it from the first fire after the 2026-09-14 deploy, so an absent "
                               "file means nothing has fired since, NOT that nothing was reaped")
    try:
        rows, repaired, skipped = _CW.read_jsonl(_ENDINGS_PATH)
    except Exception as e:
        return [], _unverified("cycle_endings.jsonl could not be read: %s: %s" % (type(e).__name__, e))
    newest = list(reversed(rows))[:_MAX_ENDINGS]
    # read_jsonl returns LISTS (repaired: [(line_no, joined)], skipped: [line_no]); the
    # envelope contract carries COUNTS. Passing the lists through would render as a count in
    # the pane and raise on the %d below — a shape mismatch that looks like a number.
    n_rep, n_skip = len(repaired), len(skipped)
    reason = ""
    if n_skip:
        reason = "%d line(s) in cycle_endings.jsonl did not parse and are NOT in this list" % n_skip
    return rows, _env(newest, at=os.path.getmtime(_ENDINGS_PATH),
                      state="stale" if n_skip else "ok", reason=reason,
                      repaired=n_rep, skipped=n_skip)


def _ledger_envelope(endings):
    # read_jsonl NEVER raises — an absent file returns ([], [], []), which would flow through
    # window() and summarize() into a perfectly healthy envelope full of zeros. That is the
    # "Working through three dead cycles" bug, rebuilt inside its own fix. Check existence first.
    if not os.path.exists(_JOURNAL_PATH):
        return _unverified("journal.jsonl does not exist, so every ledger count would be a zero "
                           "that means 'I could not look' rather than 'nothing happened'")
    try:
        rows, repaired, skipped = _CW.read_jsonl(_JOURNAL_PATH)
    except Exception as e:
        return _unverified("journal.jsonl could not be read: %s: %s" % (type(e).__name__, e))
    skipped_close = 0
    if skipped:
        # The contract: unverified if any skipped line is a cycle_close. We cannot parse them, so
        # we cannot know — and "cannot know" is the answer, not zero.
        try:
            for line in open(_JOURNAL_PATH, encoding="utf-8"):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except Exception:
                    if '"cycle_type"' in line or "cycle_close" in line:
                        skipped_close += 1
        except Exception:
            skipped_close = -1
    if skipped_close:
        return _unverified("%s unparseable journal line(s) look like cycle closes, so any count "
                           "from this file is short by an unknown amount"
                           % ("some" if skipped_close < 0 else skipped_close), skipped=len(skipped))
    # window returns (rows, undated_count) — a tuple, and it filters to closes itself. The undated
    # count is not noise: those are closes with no parseable timestamp, excluded from the window by
    # design, and a ledger that drops them silently is short by an amount nobody can see.
    win, undated = _CW.window(rows, n=20, before=_now())
    value = _CW.summarize(win)
    since = _CW.parse_ts(win[0].get("timestamp")) if win else None
    value["span"] = _CW.endings_span(endings or [], win, since=since)
    value["candidates_written"] = _count_lines(_CANDIDATES_PATH)
    value["candidates_taken"] = _candidates_taken()
    bits = []
    if skipped:
        bits.append("%d journal line(s) skipped, none a close" % len(skipped))
    if undated:
        bits.append("%d close(s) carry no parseable timestamp and are outside every window" % undated)
    return _env(value, at=_now(), state="ok" if not undated else "stale", reason="; ".join(bits))


def _count_lines(path):
    try:
        return sum(1 for ln in open(path, encoding="utf-8") if ln.strip())
    except Exception:
        return None


def _candidates_taken():
    """A candidate is 'taken' when a research page cites the synthesis that raised it. Counted
    from the filesystem, never assumed: a queue whose consumer never fires is this project's most
    frequent defect, so the number that matters is how many were READ, not how many were written."""
    try:
        sources = set()
        for ln in open(_CANDIDATES_PATH, encoding="utf-8"):
            if not ln.strip():
                continue
            try:
                src = (json.loads(ln).get("source") or "").strip()
            except Exception:
                continue
            if src:
                sources.add(os.path.splitext(os.path.basename(src))[0])
        if not sources:
            return 0
        taken = 0
        for f in os.listdir(_WIKI_RESEARCH):
            if not f.endswith(".md"):
                continue
            try:
                body = open(os.path.join(_WIKI_RESEARCH, f), encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            if any(s in body for s in sources):
                taken += 1
        return taken
    except Exception:
        return None


# ── v1 fields, unchanged ─────────────────────────────────────────────────────────────────────

def _v1_fields() -> dict:
    entries = _read_feed()
    status = _read_status()
    enabled = _read_enabled()
    engine_state, _ = _safe(_read_json, _ENGINE_STATE_PATH)
    engine_state = engine_state or {}
    if not enabled:
        status["state"] = "disabled"
        status["label"] = "Disabled"
    control, _ = _safe(_read_json, _CONTROL_PATH)
    control = control or {}
    paused_until = control.get("paused_until", 0)
    if enabled and paused_until and time.time() < paused_until:
        status["state"] = "paused"
        status["label"] = "Paused"
        status["paused_until"] = status.get("paused_until") or str(paused_until)
    total_cycles = engine_state.get("cycle_count")
    if total_cycles is None:
        total_cycles = len(entries)
    return {"entries": entries, "total_cycles": total_cycles, "status": status, "enabled": enabled}


def _read_feed() -> list:
    entries = []
    try:
        if os.path.exists(_FEED_PATH):
            with open(_FEED_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
    except Exception:
        pass
    entries.reverse()
    return entries[:_MAX_ENTRIES]


def _read_status() -> dict:
    try:
        if os.path.exists(_STATUS_PATH):
            with open(_STATUS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"state": "idle", "label": "Available"}


def _read_enabled() -> bool:
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                cfg = json.load(f)
            return bool(cfg.get("idle_time_engine", {}).get("enabled", False))
    except Exception:
        pass
    return False
