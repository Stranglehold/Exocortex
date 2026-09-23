"""
failure_fingerprint.py — shared fingerprint / quarantine store (A1, three-strike)

WHY THIS IS A SHARED MODULE AND NOT TWO COPIES
----------------------------------------------
A1 has a producer and a consumer at DIFFERENT hooks:

  tool_execute_before  `_20_meta_reasoning_gate`  computes the op signature, and
                                                  ENFORCES quarantine on it
  tool_execute_after   `_32_failure_fingerprint`  RECORDS the failure against it

If those two computed a signature even slightly differently, nothing would ever
match, quarantine would never fire, and the whole mechanism would be silently
inert while looking installed. That is the single most common defect class in this
codebase — producer built, consumer assumed — so the signature is defined exactly
once, here, and both ends import it.

TWO DIFFERENT IDENTIFIERS, ON PURPOSE
-------------------------------------
`fingerprint()`    = (tool, error_class, normalized message)
                     Identifies "the same FAILURE". Only knowable AFTER execution.

`op_signature()`   = (tool, normalized significant args)
                     Identifies "the same ATTEMPT". Knowable BEFORE execution.
                     This is what the gate can match on to refuse a retry.

`entry_key()`      = (fingerprint, op_signature)
                     The ledger key, and what accumulates strikes: "this exact call
                     failed this exact way". Three strikes means one call, three times.

The distinction is forced by the hook contract, verified against A0 v2.9 core
(`agent.py` ~L1192): `tool_execute_before` receives `tool_args` and `tool_name`;
`tool_execute_after` receives `response` and `tool_name` and **no args at all**.
So the gate stashes the op signature on the agent and the recorder reads it back.
You cannot fingerprint an error before it happens, and you cannot match args after
the fact — hence two identifiers.

STRIKES ARE PER ATTEMPT (2026-09-23, Opus ruling)
-------------------------------------------------
Strikes used to be keyed by the failure alone, and every strike overwrote the entry's
op_signature, so the block landed on whichever call struck last. Measured: the hung-
terminal message normalizes the same whatever script is running, so six strikes from
different calls (cycles 676-732) accumulated on one entry, and strike 6 (a terminal
command, 2026-09-23 15:44:01Z) moved the block off every short python script and onto
every short terminal command. "Quarantined after N identical failures" was never a
claim about identical calls. Keying on (failure, attempt) makes it one: different
calls accumulate independently, and an entry's op_signature never changes.

SESSION STATE IS NOT EVIDENCE ABOUT THE CALL
--------------------------------------------
`terminal_session_hung` is matched on one message, A0's `fw.code.running.md`, which
`code_execution_tool.handle_running_session` returns at the START of a call when the
session is still busy with an earlier command. The new call's code never reaches the
shell. So those strikes describe the session, and resetting the session removes their
cause: a call that resets session N (`reset: true`, or runtime "reset") deletes every
`terminal_session_hung` entry for session N, at any strike count. Other classes struck
code that did run, and a reset does not change what that code does, so they stay.

QUARANTINE-BORN LESSONS CARRY THEIR PROVENANCE
----------------------------------------------
A quarantine files an ANTI-PATTERN, and sleep Phase 5 turns it into an AgentEvolver
experience. The tags `qfp:<entry key>` and `qkey:<invalidation key>` go with it, and
`lesson_suppressor()` stops serving the lesson once the key rotates or the entry is no
longer quarantined. Suppress, never delete: the store keeps everything and the tool
filters on read.

STORE LOCATION
--------------
`/a0/usr/workdir/workspace/office/` — runtime state lives OUTSIDE the plugin so an
Exocortex update cannot destroy accumulated quarantine state. Same directory as
engine_state.json and control.json.

No LLM calls. Everything here is deterministic string handling and arithmetic.
"""

import hashlib
import json
import os
import re
import time

OFFICE = "/a0/usr/workdir/workspace/office"
LEDGER_PATH = os.path.join(OFFICE, "failure_fingerprints.json")
ENGINE_STATE = os.path.join(OFFICE, "engine_state.json")

# Files whose change invalidates accumulated strikes. Per Opus: a fingerprint is
# invalidated by a gating code change or a model profile change. If the thing that
# produced the failure has changed, prior strikes are no longer evidence about the
# current system.
_INVALIDATORS = [
    "/a0/usr/plugins/_exocortex/extensions/python/tool_execute_before/_20_meta_reasoning_gate.py",
    # This file too (2026-09-23): op_signature() lives here, so a change to how an ATTEMPT is
    # identified turns every stored signature into a statement in the old scheme. Without this
    # line, a quarantine recorded under the old scheme would outlive a fix to the scheme itself.
    "/a0/usr/plugins/_exocortex/helpers/failure_fingerprint.py",
    "/a0/usr/plugins/_model_config/presets.yaml",
]

DEFAULTS = {
    "enabled": True,
    "window_cycles": 50,      # rolling window; strikes older than this do not count
    "strikes_to_quarantine": 3,
    "max_entries": 500,       # hard cap so the ledger cannot grow without bound
}

CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"

# The agent-data key the gate stashes the op signature under and the recorder
# reads it back from. Declared ONCE here so the two halves cannot drift apart:
# a mismatched literal in either file would leave quarantine permanently inert
# with nothing failing loudly enough to notice.
OP_SIG_KEY = "_op_signature"

# Same contract for the call's terminal session and whether the call resets it. The gate
# clears both at the start of every call and sets them only after its arguments are
# normalized, so a call that stops early leaves them empty instead of stale.
OP_SCOPE_KEY = "_op_scope"
OP_RESET_KEY = "_op_reset"

# Tools whose calls run inside a numbered terminal session.
_SESSION_TOOLS = {"code_execution_tool"}

# Classes whose strikes describe the session rather than the call (see the header). A
# session reset deletes these for that session. Every other class survives a reset.
_SESSION_STATE_CLASSES = {"terminal_session_hung"}


def cfg() -> dict:
    """Config with explicit defaults; missing section degrades gracefully."""
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            c = json.load(fh).get("failure_quarantine", {})
    except Exception:
        c = {}
    return {**DEFAULTS, **(c if isinstance(c, dict) else {})}


# ── normalization ────────────────────────────────────────────────────────────
# The whole mechanism turns on this. Two occurrences of "the same" failure differ
# in line numbers, ids, paths, byte counts and timestamps. Under-normalize and
# every occurrence looks unique, so strikes never accumulate and quarantine never
# fires. Over-normalize and unrelated failures collide, so we quarantine work that
# was never broken. Order matters: paths are replaced before bare numbers, because
# paths contain digits.

_RX_PATH = re.compile(r"(?:/[\w.\-]+){2,}/?")            # /a0/usr/... style paths
_RX_WINPATH = re.compile(r"[a-zA-Z]:\\\\[^\s\"']+")
_RX_HEX = re.compile(r"\b(?:0x)?[0-9a-f]{8,}\b", re.I)   # hashes, ids, addresses
_RX_UUID = re.compile(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b", re.I)
_RX_TIME = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}\S*")
_RX_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")
_RX_WS = re.compile(r"\s+")


def normalize_message(msg: str, max_len: int = 400) -> str:
    """Collapse the incidental detail so 'the same failure' hashes the same."""
    s = (msg or "")[-max_len * 4:]          # only the tail carries the error
    s = _RX_TIME.sub("<ts>", s)
    s = _RX_UUID.sub("<uuid>", s)
    s = _RX_WINPATH.sub("<path>", s)
    s = _RX_PATH.sub("<path>", s)
    s = _RX_HEX.sub("<hex>", s)
    s = _RX_NUM.sub("<n>", s)
    s = _RX_WS.sub(" ", s).strip().lower()
    return s[:max_len]


def _h(*parts) -> str:
    return hashlib.sha256("\x1f".join(str(p) for p in parts).encode("utf-8", "replace")).hexdigest()[:16]


def fingerprint(tool: str, error_class: str, message: str) -> str:
    """Identity of a FAILURE. Post-execution only."""
    return _h("fp", tool or "", error_class or "", normalize_message(message))


def _normalize_arg(v: str, max_len: int = 120) -> str:
    """Light normalization for ARGUMENTS — deliberately NOT normalize_message().

    Caught by test T2: normalize_message() replaces paths with `<path>`, which is
    correct for an error message (the path is incidental noise) and catastrophic
    for an argument (the path IS the target). Under that normalizer, writing to
    `wiki/a.md` and `wiki/b.md` produced the same op signature, so quarantining one
    write would have blocked every other write to any path — refusing legitimate
    work, which is the worst failure this mechanism can have.

    So arguments keep their paths and their numbers. Only case and whitespace are
    normalized.

    The residual risk runs the other way: an argument carrying a genuinely volatile
    value (a session id, a nonce) makes the same logical attempt look distinct each
    time, so strikes do not accumulate and we under-quarantine. That is the safe
    direction to fail. Under-quarantining leaves the status quo — a loop that
    continues. Over-quarantining blocks work that was never broken.
    """
    return _RX_WS.sub(" ", (v or "")).strip().lower()[:max_len]


# Arguments whose VALUE is the identity of the call. They are hashed in full instead of being
# reduced to a length bucket. The bucket is right for a document body, where another argument
# (the path) names the target; it is wrong when the payload IS the target. For
# code_execution_tool the script is the whole call. Bucketed, every 121-999-char python script
# carried one signature, so three hung-terminal failures (cycles 676-711) quarantined every short
# python call Aporia made from 2026-09-21 to 09-23. That included the journal write that would
# have corrected a stale belief.
#
# Hashed EXACTLY, apart from outer whitespace and line endings. Collapsing inner whitespace or
# case (what _normalize_arg does) would make a script whose fix IS an indentation or a path's
# case look identical to the broken one, and block the fix. Under-quarantining is the safe
# direction (see _normalize_arg).
_IDENTITY_ARGS = {("code_execution_tool", "code")}


def op_signature(tool: str, args: dict | None) -> str:
    """Identity of an ATTEMPT. Pre-execution.

    Only the *shape* of the call is used, not full payloads: a 20KB document body
    differs on every call and would make every attempt unique. Long string values
    are reduced to a length bucket so 'write a big file to X' matches itself across
    cycles while still separating different targets. Arguments in _IDENTITY_ARGS are
    the exception: their content is hashed, so only a truly identical attempt matches.
    """
    norm = []
    for k in sorted((args or {}).keys()):
        v = (args or {})[k]
        if isinstance(v, str):
            if (tool, k) in _IDENTITY_ARGS:
                norm.append(f"{k}=<sha:{_h('arg', v.replace(chr(13) + chr(10), chr(10)).strip())}>")
            elif len(v) > 120:
                norm.append(f"{k}=<str:{len(v) // 1000}k>")
            else:
                norm.append(f"{k}={_normalize_arg(v)}")
        elif isinstance(v, (int, float, bool)) or v is None:
            norm.append(f"{k}={v}")
        else:
            norm.append(f"{k}=<{type(v).__name__}>")
    return _h("op", tool or "", "|".join(norm))


def entry_key(fp: str, op_sig: str) -> str:
    """Ledger key: this failure, from this attempt. What strikes accumulate on."""
    return _h("entry", fp or "", op_sig or "")


def op_scope(tool: str, args: dict | None) -> dict | None:
    """The terminal session a call runs in, read the way A0 reads it; None if it has none.

    Mirrors `code_execution_tool._execute`: `int(self.args.get("session", 0))`. Pass the
    gate's NORMALIZED args, since A0 only ever sees those.
    """
    if tool not in _SESSION_TOOLS:
        return None
    try:
        return {"tool": tool, "session": int((args or {}).get("session", 0))}
    except (TypeError, ValueError):
        return None


def is_session_reset(tool: str, args: dict | None) -> bool:
    """True when this call resets its session: the same test A0 applies.

    Mirrors `code_execution_tool._execute`:
    `bool(self.args.get("reset", False) or runtime_arg == "reset")`, where runtime_arg is
    lowered and stripped. So the string "false" counts as a reset, because A0 treats it
    as one.
    """
    if tool not in _SESSION_TOOLS:
        return False
    a = args or {}
    runtime = str(a.get("runtime", "") or "").lower().strip()
    return bool(a.get("reset", False) or runtime == "reset")


# ── environment ──────────────────────────────────────────────────────────────

def current_cycle() -> int:
    """Cycle counter from engine_state.json; 0 if unavailable (never raises)."""
    try:
        with open(ENGINE_STATE, encoding="utf-8") as fh:
            return int(json.load(fh).get("cycle_count") or 0)
    except Exception:
        return 0


def invalidation_key() -> str:
    """Hash of the gating code + model config.

    Cheap content hash rather than mtime: `docker cp -p` preserves mtime, so mtime
    is not a reliable change signal in this environment (learned the hard way —
    `find -newer` was blind to every deploy for the same reason).
    """
    parts = []
    for p in _INVALIDATORS:
        try:
            with open(p, "rb") as fh:
                parts.append(hashlib.md5(fh.read()).hexdigest()[:12])
        except Exception:
            parts.append("absent")
    return _h("inv", *parts)


# ── ledger ───────────────────────────────────────────────────────────────────

def load_ledger() -> dict:
    try:
        with open(LEDGER_PATH, encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict) and isinstance(d.get("entries"), dict):
            return d
    except Exception:
        pass
    return {"invalidation_key": invalidation_key(), "entries": {}}


def save_ledger(d: dict) -> bool:
    """Atomic write. A torn ledger would either lose quarantines or wedge work."""
    try:
        os.makedirs(OFFICE, exist_ok=True)
        tmp = LEDGER_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=2)
        os.replace(tmp, LEDGER_PATH)
        return True
    except Exception:
        return False


def _prune(ledger: dict, cycle: int, conf: dict) -> None:
    """Drop strikes that fell out of the rolling window, and cap total size.

    Quarantined entries are NOT pruned by the window — a quarantine persists until
    it is explicitly invalidated or released. Ageing a quarantine out silently
    would let the agent resume a failure loop with no record of why.
    """
    win = int(conf["window_cycles"])
    dead = [
        fp for fp, e in ledger["entries"].items()
        if not e.get("quarantined") and cycle and (cycle - int(e.get("last_cycle") or 0)) > win
    ]
    for fp in dead:
        ledger["entries"].pop(fp, None)

    cap = int(conf["max_entries"])
    if len(ledger["entries"]) > cap:
        ranked = sorted(
            ledger["entries"].items(),
            key=lambda kv: (bool(kv[1].get("quarantined")), int(kv[1].get("last_cycle") or 0)),
        )
        for fp, _e in ranked[: len(ledger["entries"]) - cap]:
            ledger["entries"].pop(fp, None)


def check_invalidation(ledger: dict) -> bool:
    """Reset strikes if the gating code or model config changed. True if reset."""
    now = invalidation_key()
    if ledger.get("invalidation_key") == now:
        return False
    ledger["invalidation_key"] = now
    ledger["entries"] = {
        fp: e for fp, e in ledger["entries"].items() if e.get("manual_hold")
    }
    return True


# ── the two operations the extensions call ───────────────────────────────────

def record_failure(tool: str, error_class: str, message: str,
                   op_sig: str, evidence: dict | None = None,
                   scope: dict | None = None) -> dict:
    """Register one failure of one attempt.

    Returns {fingerprint, failure, strikes, quarantined, invalidated}. `fingerprint` is the
    ledger key, the id `release()` takes; `failure` is the failure's own identity.
    """
    conf = cfg()
    ledger = load_ledger()
    invalidated = check_invalidation(ledger)
    cycle = current_cycle()
    _prune(ledger, cycle, conf)

    fp = fingerprint(tool, error_class, message)
    key = entry_key(fp, op_sig)
    e = ledger["entries"].get(key)

    if e is None:
        e = {
            "tool": tool, "error_class": error_class,
            "failure": fp,
            # Part of the key, so it is set here once and never overwritten: the block
            # cannot move to another call.
            "op_signature": op_sig,
            "scope": scope,
            "strikes": 0, "first_cycle": cycle, "last_cycle": cycle,
            "quarantined": False, "quarantined_at_cycle": None,
            "normalized": normalize_message(message, 200),
        }
        ledger["entries"][key] = e

    # A strike only counts inside the rolling window. Outside it, this is a fresh
    # occurrence rather than a continuation, and the count restarts at 1.
    win = int(conf["window_cycles"])
    if cycle and (cycle - int(e.get("last_cycle") or 0)) > win:
        e["strikes"] = 0
        e["first_cycle"] = cycle

    e["strikes"] = int(e.get("strikes") or 0) + 1
    e["last_cycle"] = cycle
    e["last_seen"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if e["strikes"] >= int(conf["strikes_to_quarantine"]) and not e["quarantined"]:
        e["quarantined"] = True
        e["quarantined_at_cycle"] = cycle
        e["evidence"] = {
            "error_class": error_class,
            "causal_chain": (evidence or {}).get("causal_chain", ""),
            "raw_output_tail": ((evidence or {}).get("raw_output_tail") or "")[:600],
            "strikes_at_quarantine": e["strikes"],
        }

    save_ledger(ledger)
    return {
        "fingerprint": key,
        "failure": fp,
        "strikes": e["strikes"],
        "quarantined": bool(e["quarantined"]),
        "invalidated": invalidated,
    }


def is_session_state(entry: dict | None) -> bool:
    """True for an entry that a reset of its session would delete."""
    e = entry or {}
    return e.get("error_class") in _SESSION_STATE_CLASSES and isinstance(e.get("scope"), dict)


def clear_session(scope: dict | None) -> list:
    """A call reset this terminal session: delete the strikes that described its state.

    Deletes every `_SESSION_STATE_CLASSES` entry scoped to this session at ANY strike count,
    so no stale 1-2 strikes carry past the reset. Entries of other classes are kept: their
    code ran and failed, and a reset does not change that code (Opus ruling, 2026-09-23).
    A `manual_hold` entry is kept too, as it is on invalidation: an operator's hold is not
    lifted by something the agent does. Returns the deleted keys.
    """
    if not scope:
        return []
    ledger = load_ledger()
    if check_invalidation(ledger):
        save_ledger(ledger)          # everything not held is already gone
        return []
    gone = [
        k for k, e in ledger["entries"].items()
        if e.get("scope") == scope
        and e.get("error_class") in _SESSION_STATE_CLASSES
        and not e.get("manual_hold")
    ]
    for k in gone:
        ledger["entries"].pop(k, None)
    if gone:
        save_ledger(ledger)
    return gone


def find_quarantine(op_sig: str) -> dict | None:
    """Pre-execution lookup: is this attempt under quarantine? Returns entry or None."""
    if not op_sig:
        return None
    ledger = load_ledger()
    if check_invalidation(ledger):
        save_ledger(ledger)
        return None
    for fp, e in ledger["entries"].items():
        if e.get("quarantined") and e.get("op_signature") == op_sig:
            return {**e, "fingerprint": fp}
    return None


def release(fingerprint_id: str) -> bool:
    """Maintainer override — clear one quarantine."""
    ledger = load_ledger()
    e = ledger["entries"].get(fingerprint_id)
    if not e:
        return False
    e["quarantined"] = False
    e["strikes"] = 0
    e["released_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return save_ledger(ledger)


def quarantined_entries() -> list:
    """All active quarantines — for Phase 5 consumption and the ops panel."""
    ledger = load_ledger()
    return [{**e, "fingerprint": fp}
            for fp, e in ledger["entries"].items() if e.get("quarantined")]


# ── lessons a quarantine files ───────────────────────────────────────────────
# Opus ruling, 2026-09-23. A quarantine files an ANTI-PATTERN and sleep Phase 5 turns it
# into an AgentEvolver experience, which the agentevolver tool serves back to the agent.
# Before this, nothing retracted it: on 2026-09-23 three of the five 'general' experiences
# she would be served said code_execution_tool "is quarantined" after that quarantine had
# been cleared. constraint_provenance cannot reach these (it curates SKILL.md sidecars),
# so the lesson carries its own provenance and is checked when it is read.

_QUARANTINE_TAGS = ("quarantine", "three-strike")


def quarantine_lesson_tags(key: str) -> list:
    """Provenance tags for a lesson filed from ledger entry `key`, under the current code."""
    return [f"qfp:{key}", f"qkey:{invalidation_key()}"]


def _lesson_fields(tags_or_meta) -> tuple:
    """(tags, qfp, qkey) from an anti-pattern's tag list or an experience's metadata dict."""
    if isinstance(tags_or_meta, dict):
        tags = [str(t) for t in (tags_or_meta.get("tags") or [])]
        qfp = tags_or_meta.get("quarantine_fingerprint")
        qkey = tags_or_meta.get("quarantine_invalidation_key")
    else:
        tags = [str(t) for t in (tags_or_meta or [])]
        qfp = qkey = None
    for t in tags:
        if t.startswith("qfp:") and not qfp:
            qfp = t[len("qfp:"):]
        elif t.startswith("qkey:") and not qkey:
            qkey = t[len("qkey:"):]
    return tags, qfp, qkey


def lesson_provenance(tags_or_meta) -> tuple:
    """(qfp, qkey) that a lesson carries; either is None when absent."""
    _tags, qfp, qkey = _lesson_fields(tags_or_meta)
    return qfp, qkey


def is_quarantine_lesson(tags_or_meta) -> bool:
    """Filed by a quarantine: carries both the quarantine and three-strike tags."""
    tags, _qfp, _qkey = _lesson_fields(tags_or_meta)
    return all(t in tags for t in _QUARANTINE_TAGS)


def lesson_suppressor():
    """A predicate(tags_or_metadata) -> True when a lesson must not be served.

    Only quarantine lessons are ever suppressed; anything else, including an untagged
    lesson, passes through. A quarantine lesson is suppressed when it has no provenance,
    when the code that filed it has changed (qkey), or when the ledger no longer holds
    its entry as quarantined (qfp). Reads the ledger and the key once; writes nothing.
    """
    key_now = invalidation_key()
    live = {k for k, e in load_ledger().get("entries", {}).items() if e.get("quarantined")}

    def suppressed(tags_or_meta) -> bool:
        if not is_quarantine_lesson(tags_or_meta):
            return False
        _tags, qfp, qkey = _lesson_fields(tags_or_meta)
        if not qfp or not qkey:
            return True
        return qkey != key_now or qfp not in live

    return suppressed
