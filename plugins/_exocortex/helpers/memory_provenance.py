"""
memory_provenance.py — which chat and which models produced a memory, stamped at creation

WHY THIS EXISTS
---------------
Opus's ruling of 2026-09-04 (Q3, tier 1, "cheap partial"), re-ruled 2026-09-27: every new memory
carries, mechanically, the conditions it was formed under. The agent never sees or writes these
fields. Two findings make them the first question of any later forensics:
- Sep 8: THE MODEL IS THE VARIABLE. Ornith re-adopted a belief from recall where Qwen did not.
- 2026-09-26: memory SH98WOqit7 cites a message id, 'M_49826', that nothing in the code or logs
  ever emitted. It was written by _52's utility call, so the confabulation belongs to the WRITER
  model, not the chat model whose conversation was being summarised. One model field could not
  tell those apart; that is why there are two.

WHERE THE STAMP LIVES: a sidecar, never the memory itself (Opus, 2026-09-27, option B)
--------------------------------------------------------------------------------------
state/memory_provenance.jsonl, one JSON line per new memory, keyed by memory id. NOT in the
memory's metadata: A0's memory_load tool prints every metadata key back to the agent
(Memory.format_docs_plain), so a stamp in `lineage` would put chat ids and model ids into her
tool output — the very shape memory SH98WOqit7 teaches her to reject as injection, and a break of
the 09-04 principle that the agent never sees these fields. Nothing she reads changes, byte for
byte. An id absent from the sidecar is a memory that predates the stamp (Q3: flag, don't
suppress). The sidecar must travel with any backup or restore of the memory store.

WHAT IS STAMPED (one sidecar line: {id, stamped_at, created_by, and the fields below})
-----------------------------------------------------------------------------------------
  chat_id          the A0 context id whose conversation produced the material ("" = none)
  preset           the effective model preset of that chat, per-chat override honoured.
                   In Ornith2 the chat and utility slots name the SAME model and differ only in
                   the thinking switch, which lives in the preset. Without it, "was this written
                   while the utility still had thinking on?" (SH98WOqit7) is unanswerable.
  chat_model       "<provider>/<name>" of that chat's chat slot
  writer_model     "<provider>/<name>" of the model that wrote the text, or "deterministic"
  attribution      how chat_id was determined, most to least trustworthy:
      exact            the writer stamped itself, in the creating context
      same_monologue   _55 saw it in the only chat whose monologue was running when it was made
      memorize_window  written by A0's post-monologue memorizers or consolidation; matched to the
                       one chat whose monologue ended at most window_s seconds before it
      preload          A0's knowledge import, outside any chat: chat and model fields are empty
      first_seen       none of the above: the chat that first saw it. Unreliable by design.
  writer_inferred  True when created_by was inferred by _55 rather than written by the writer

HOW THE CHAT IS FOUND FOR WRITES WE DO NOT OWN
----------------------------------------------
A0's Memory.insert_text is not @extensible in v2.12 (plugins/_memory/helpers/memory.py:470), and
its memorizers insert AFTER monologue_end, so _55 first sees their memories in a LATER monologue.
Measured on the live store 2026-09-27: 847 memories stamped that way, gap p50 76 s, p90 1,178 s,
29 % more than 120 s late, often in another chat. A ledger of monologue start/end events
(state/monologue_ledger.jsonl, one JSON line each) lets _55 match a memory's creation time to the
chat that made it.

Memory `timestamp` metadata is A0's LOCAL time with an offset ("2026-09-26T02:35:50-04:00").
It is parsed with its offset; a naive time is treated as unknown, never guessed.

WHAT THIS DOES NOT DO
---------------------
- Does not stamp or alter existing memories. They predate the stamp (Q3: flag, don't suppress).
- Does not suppress, rank or filter anything on these fields.
- Does not record the extension-stack hash (deferred) or the cycle type (joinable later from
  chat_id and time against the cycle ledger).
- Never falls back to another preset's model. A resolver failure stamps "", not a guess.
- No LLM calls. File reads and appends, and string handling only.

CONFIG (plugin config.json, section "memory_provenance"; absent -> these defaults)
  enabled   True   — False turns every stamp and ledger write off
  window_s  120    — A0's consolidation timeout is 60 s (memory_consolidation.py:37), plus slack
"""

import json
import os
from datetime import datetime, timedelta, timezone

PLUGIN_CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"
LEDGER_PATH = "/a0/usr/plugins/_exocortex/state/monologue_ledger.jsonl"
SIDECAR_PATH = "/a0/usr/plugins/_exocortex/state/memory_provenance.jsonl"

DEFAULT_WINDOW_S = 120
ACTIVE_HORIZON_S = 10800      # a monologue open longer than the idle engine's hung cap is not trusted
LEDGER_TAIL_BYTES = 512 * 1024
LEDGER_TRIM_BYTES = 2 * 1024 * 1024
LEDGER_KEEP_LINES = 2000

ATTRIBUTIONS = ("exact", "same_monologue", "memorize_window", "preload", "first_seen")
MEMORIZER_WRITERS = ("_50_memorize_fragments", "_51_memorize_solutions", "consolidation")

_PREFIX = "[MEM-PROV]"


def _log(msg: str) -> None:
    try:
        print(f"{_PREFIX} {msg}", flush=True)
    except Exception:
        pass


def cfg() -> dict:
    """Config with explicit defaults. Absent section -> defaults, never a crash."""
    out = {"enabled": True, "window_s": DEFAULT_WINDOW_S}
    try:
        with open(PLUGIN_CONFIG_PATH, encoding="utf-8") as fh:
            section = (json.load(fh) or {}).get("memory_provenance", {})
        if isinstance(section, dict):
            out.update({k: section[k] for k in out if k in section})
    except Exception:
        pass
    return out


# ── time ─────────────────────────────────────────────────────────────────────

def parse_time(value):
    """An aware datetime from ISO text with an offset or Z. None if naive or unparseable."""
    try:
        t = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except Exception:
        return None
    return t if t.tzinfo is not None else None


def doc_time(metadata):
    """When A0 says the memory was written: its `timestamp`, local time WITH offset."""
    return parse_time((metadata or {}).get("timestamp"))


# ── who and which models ─────────────────────────────────────────────────────

def chat_id_of(agent) -> str:
    try:
        return str(agent.context.id or "")
    except Exception:
        return ""


def _model_str(slot_cfg) -> str:
    if not isinstance(slot_cfg, dict):
        return ""
    name = str(slot_cfg.get("name") or "").strip()
    if not name:
        return ""
    provider = str(slot_cfg.get("provider") or "").strip()
    return f"{provider}/{name}" if provider else name


def model_ids(agent, mc=None) -> dict:
    """{preset, chat_model, utility_model} from A0's own resolver, the one the agent builds its
    models from (per-chat override included). Each part is "" if it cannot be resolved."""
    out = {"preset": "", "chat_model": "", "utility_model": ""}
    if mc is None:
        try:
            from plugins._model_config.helpers import model_config as mc
        except Exception:
            return out
    try:
        out["preset"] = str(mc.get_effective_preset_name(agent) or "").strip()
    except Exception:
        pass
    try:
        out["chat_model"] = _model_str(mc.get_chat_model_config(agent))
    except Exception:
        pass
    try:
        out["utility_model"] = _model_str(mc.get_utility_model_config(agent))
    except Exception:
        pass
    return out


def writer_model_for(slot: str, ids: dict) -> str:
    """The model that wrote the text: the utility or chat slot, or none at all."""
    if slot == "utility":
        return ids.get("utility_model", "")
    if slot == "chat":
        return ids.get("chat_model", "")
    if slot == "deterministic":
        return "deterministic"
    return ""


def current(agent, mc=None) -> dict:
    """This context: chat_id plus its model ids. Read once per extension run."""
    return {"chat_id": chat_id_of(agent), **model_ids(agent, mc)}


# ── the sidecar ──────────────────────────────────────────────────────────────

def record(mem_id: str, fields: dict, path: str = SIDECAR_PATH, now=None) -> bool:
    """Append one stamp line for `mem_id`. O_APPEND keeps concurrent lines whole. Never raises."""
    try:
        if not mem_id or not cfg()["enabled"]:
            return False
        row = {"id": str(mem_id), "stamped_at": (now or datetime.now(timezone.utc)).isoformat(),
               **{k: v for k, v in (fields or {}).items() if k != "id"}}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, separators=(",", ":"), default=str) + "\n")
        _index_add(path, str(mem_id))
        return True
    except Exception as e:
        _log(f"sidecar append skipped for {mem_id}: {type(e).__name__}: {str(e)[:80]}")
        return False


# Ids already in the sidecar, read incrementally. _55 checks it so a memory the memory_save hook
# stamped exactly does not get a second, weaker line. Module-level: the helper is imported by bare
# name and survives the plugin reload, so the index is read in full once per process.
_INDEX = {}  # path -> {"offset": int, "ids": set}


def _index_add(path: str, mem_id: str) -> None:
    ent = _INDEX.get(path)
    if ent is not None:
        ent["ids"].add(mem_id)


def stamped_ids(path: str = SIDECAR_PATH) -> set:
    """Every id in the sidecar. Reads only the bytes added since the last call."""
    ent = _INDEX.setdefault(path, {"offset": 0, "ids": set()})
    try:
        size = os.path.getsize(path)
    except Exception:
        return ent["ids"]
    if size < ent["offset"]:  # replaced or truncated: start over
        ent["offset"], ent["ids"] = 0, set()
    if size == ent["offset"]:
        return ent["ids"]
    try:
        with open(path, "rb") as fh:
            fh.seek(ent["offset"])
            data = fh.read()
    except Exception:
        return ent["ids"]
    cut = data.rfind(b"\n")
    if cut < 0:  # no complete line yet
        return ent["ids"]
    for line in data[:cut].decode("utf-8", errors="replace").splitlines():
        try:
            mid = json.loads(line).get("id")
        except Exception:
            continue
        if mid:
            ent["ids"].add(str(mid))
    ent["offset"] += cut + 1
    return ent["ids"]


# ── the exact stamp: writers we own, and memory_save ─────────────────────────

def exact_fields(agent, writer: str, slot: str, mc=None, cur=None) -> dict:
    """The stamp for a memory written in this context. `slot` names the model that wrote the
    text: "utility", "chat" or "deterministic"."""
    c = cur if cur is not None else current(agent, mc)
    return {"created_by": writer, "chat_id": c.get("chat_id", ""), "preset": c.get("preset", ""),
            "chat_model": c.get("chat_model", ""), "writer_model": writer_model_for(slot, c),
            "attribution": "exact", "writer_inferred": False}


def stamp_exact(mem_id: str, agent, writer: str, slot: str, mc=None, cur=None,
                path: str = SIDECAR_PATH) -> bool:
    """Record an exact stamp for `mem_id`. Never raises; False if nothing was written."""
    try:
        if not mem_id or not cfg()["enabled"]:
            return False
        return record(mem_id, exact_fields(agent, writer, slot, mc, cur), path)
    except Exception as e:
        _log(f"stamp_exact skipped for {mem_id}: {type(e).__name__}: {str(e)[:80]}")
        return False


# ── writes we do not own: infer the writer, find the chat ────────────────────

def _nonempty(value) -> bool:
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return str(value if value is not None else "").strip() not in ("", "[]", "{}", "None", "null")


def infer_writer(metadata) -> str:
    """Which path wrote a memory that did not stamp itself. Order matters: a consolidation merge
    also carries area fragments or solutions."""
    m = metadata or {}
    if m.get("knowledge_source") in (True, "True", "true"):
        return "knowledge_import"
    if _nonempty(m.get("consolidated_from")):
        return "consolidation"
    area = str(m.get("area") or "")
    if area == "fragments":
        return "_50_memorize_fragments"
    if area == "solutions":
        return "_51_memorize_solutions"
    return "unknown"


def active_chats_at(entries, t, horizon_s: int = ACTIVE_HORIZON_S) -> set:
    """Chats with a monologue open at time t: starts minus ends per chat, within the horizon.
    A lost end event makes a chat look open, which makes attribution ambiguous (first_seen):
    the error runs toward "don't know", never toward a wrong chat."""
    lo = t - timedelta(seconds=horizon_s)
    depth = {}
    for e in sorted(entries, key=lambda e: e["_t"]):
        if e["_t"] < lo or e["_t"] > t:
            continue
        c = e.get("chat_id") or ""
        depth[c] = depth.get(c, 0) + (1 if e.get("event") == "start" else -1)
    return {c for c, d in depth.items() if d > 0 and c}


def attribute(metadata, entries, cur: dict, window_s: int = DEFAULT_WINDOW_S) -> dict:
    """The stamp fields for a memory _55 first sees unstamped. Pure: no I/O, never raises.

    `entries` are ledger events (read_ledger); `cur` is the context _55 runs in (current()).
    """
    writer = infer_writer(metadata)
    out = {"created_by": writer, "writer_inferred": True}
    if writer == "knowledge_import":
        out.update({"chat_id": "", "preset": "", "chat_model": "", "writer_model": "",
                    "attribution": "preload"})
        return out
    t = doc_time(metadata)
    if t is not None:
        if writer in MEMORIZER_WRITERS:
            hi = timedelta(seconds=window_s)
            ends = [e for e in entries if e.get("event") == "end" and e["_t"] <= t <= e["_t"] + hi]
            chats = {(e.get("chat_id") or "", e.get("preset") or "", e.get("chat_model") or "",
                      e.get("utility_model") or "") for e in ends}
            if len(chats) == 1:
                cid, preset, chat_model, utility_model = next(iter(chats))
                if cid:
                    out.update({"chat_id": cid, "preset": preset, "chat_model": chat_model,
                                "writer_model": utility_model, "attribution": "memorize_window"})
                    return out
        else:
            me = cur.get("chat_id") or ""
            if me and active_chats_at(entries, t) == {me}:
                out.update({"chat_id": me, "preset": cur.get("preset", ""),
                            "chat_model": cur.get("chat_model", ""),
                            "writer_model": "", "attribution": "same_monologue"})
                return out
    out.update({"chat_id": cur.get("chat_id", ""), "preset": cur.get("preset", ""),
                "chat_model": cur.get("chat_model", ""),
                "writer_model": cur.get("utility_model", "") if writer in MEMORIZER_WRITERS else "",
                "attribution": "first_seen"})
    return out


def stamp_unowned(mem_id: str, metadata, entries, cur: dict, window_s: int = DEFAULT_WINDOW_S,
                  path: str = SIDECAR_PATH) -> str:
    """_55's call for a memory it first sees unstamped. Returns the attribution recorded, or ""
    when nothing was written (disabled, already stamped, or an error). Never raises."""
    try:
        if not mem_id or not cfg()["enabled"] or str(mem_id) in stamped_ids(path):
            return ""
        fields = attribute(metadata, entries, cur, window_s)
        return fields["attribution"] if record(mem_id, fields, path) else ""
    except Exception as e:
        _log(f"stamp_unowned skipped for {mem_id}: {type(e).__name__}: {str(e)[:80]}")
        return ""


# ── the ledger ───────────────────────────────────────────────────────────────

def ledger_entry(event: str, agent, mc=None, now=None) -> dict:
    return {"t": (now or datetime.now(timezone.utc)).isoformat(), "event": event,
            **current(agent, mc)}


def append_ledger(entry: dict, path: str = LEDGER_PATH) -> bool:
    """Append one line. O_APPEND keeps concurrent writers' lines whole. Never raises."""
    try:
        if not cfg()["enabled"]:
            return False
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(entry, separators=(",", ":"), default=str) + "\n")
        _maybe_trim(path)
        return True
    except Exception as e:
        _log(f"ledger append skipped: {type(e).__name__}: {str(e)[:80]}")
        return False


def _maybe_trim(path: str) -> None:
    try:
        if os.path.getsize(path) <= LEDGER_TRIM_BYTES:
            return
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.writelines(lines[-LEDGER_KEEP_LINES:])
        os.replace(tmp, path)
    except Exception:
        pass


def read_ledger(path: str = LEDGER_PATH, tail_bytes: int = LEDGER_TAIL_BYTES) -> list:
    """The ledger's recent events, each with a parsed "_t". Unreadable lines are skipped."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - tail_bytes))
            data = fh.read().decode("utf-8", errors="replace")
    except Exception:
        return []
    lines = data.splitlines()
    if size > tail_bytes and lines:
        lines = lines[1:]  # the first line of a tail read may be cut
    out = []
    for line in lines:
        try:
            e = json.loads(line)
        except Exception:
            continue
        t = parse_time(e.get("t")) if isinstance(e, dict) else None
        if t is not None and e.get("event") in ("start", "end"):
            e["_t"] = t
            out.append(e)
    return out


# ── memory_save's id, and the self-test that guards the parse ────────────────

SAVED_TEMPLATE = "fw.memory_saved.md"
_SELFTEST_ID = "MPSELFTEST42"


def parse_saved_id(message: str, template_text: str) -> str:
    """The id in memory_save's reply, using the template the agent actually renders.

    `template_text` is that template rendered with a known id. Everything around the id is
    literal; if the reply does not match the template's shape, return "" rather than guess.
    """
    try:
        if not template_text or _SELFTEST_ID not in template_text:
            return ""
        before, after = template_text.split(_SELFTEST_ID, 1)
        before, after = before.strip(), after.strip()
        msg = (message or "").strip()
        if not msg.startswith(before) or (after and not msg.endswith(after)):
            return ""
        core = msg[len(before):len(msg) - len(after) if after else None].strip()
        return core if core and all(ch.isalnum() or ch in "_-" for ch in core) else ""
    except Exception:
        return ""


def rendered_template(agent) -> str:
    """fw.memory_saved.md as this agent renders it (prompt overrides included), with a known id.
    "" if it cannot be rendered — the caller then leaves the memory to _55."""
    try:
        return str(agent.read_prompt(SAVED_TEMPLATE, memory_id=_SELFTEST_ID) or "")
    except Exception:
        return ""
