"""
memory_save re-save gate (tool_execute_before, _19_) — R4's refusal half (A11, A20), and the
harness-field strip (A24)

Removes the fields the harness owns from memory_save's arguments, then refuses a memory_save
whose text repeats a memory recalled into this monologue.

THE STRIP (A24, Opus 2026-09-23; ships in stage 2)
--------------------------------------------------
A0's memory_save puts every extra argument straight into the memory's metadata
(plugins/_memory/tools/memory_save.py: `metadata = {"area": area, **kwargs}`). A tool call could
therefore carry its own `classification` (source user_asserted, validity confirmed) and skip
R2's structural derivation, or its own `subject_key`, `lineage`, `volatility` or `observed_at`
and steer R1 and R3. These five are removed before the tool runs. A0 hands this extension the
same `tool_args` dict it then unpacks into `tool.execute` (agent.py: "Allow extensions to
preprocess tool arguments"), so removing them here removes them from the save. `id` and
`timestamp` need nothing: `insert_documents` overwrites both. On 2026-09-23 she passed only
`text` and `area` (6 calls in 14 chats), so today this removes nothing. It closes the door before
R1b opens a window next to it. It fails open like the rest of the gate: an error leaves the
arguments as they were.

WHY
---
Recall re-seeds the store. A memory recalled into a cycle is saved again as if it were new
evidence, and each copy makes the next recall more likely.
  - 09-08 (Fable's third carrier): each MAINTAIN recalled a status memory and authored a new
    one whose tail carried the recalled frame, keeping the 09-02 belief alive.
  - 2026-09-23: 50 of the 66 "search_library is down" memories came in through memory_save,
    and A0's memory_save has no duplicate check of any kind (`insert_text(text, {"area": area,
    **kwargs})`). _52 at least refuses near-duplicates store-wide at 0.9; this path had nothing.
The injectors mark what they recall (helpers/memory_recall_tag.py). This gate reads the marks.

THE CHECKS (A20), in order
--------------------------
  1. The incoming text, normalized (case, whitespace), equals a recalled memory's text → refuse.
     The same after removing ONE leading recall head ("recalled memory (saved …):", _92's line
     above each recalled body), so a copy of the injected block is caught (Fable, 2026-09-25).
     Shadow, never refusing: a recalled body contained WHOLE in a save it does not equal is logged
     as would-refuse "containment" (Opus's ruling: containment waits on this measurement).
Every refusal and every shadow event is a row in state/resave_gate.jsonl (GATE_LOG).
  2. A similarity search for the incoming text, at threshold 0.9 (the threshold _52 already
     applies store-wide), returns a memory that was recalled this monologue → refuse. One
     embedding per memory_save, and the recalled side needs none: the store's own index answers.
  3. Otherwise the save goes through.
Only recalled memories count. A near-duplicate of something NOT recalled this monologue is
not this gate's business. That would be store-wide dedup for memory_save, which A20 did not
rule.

FAILS OPEN
----------
Unlike the forget guard beside it, which fails closed because deletion cannot be undone, this
gate fails open. If it cannot read the recalled set, the store, or the similarity search, the
save goes through, which is exactly today's behaviour (the design's degradation rule). Refusing
a legitimate save would lose information; letting a re-save through loses nothing new.

WHAT IT DOES NOT DO
-------------------
- Does not refuse a save that adds new evidence to a recalled one below 0.9. The subject-key
  check (R1b) is where that belongs.
- Does not touch any tool but memory_save.
- No LLM calls. One embedding, through the store's own search.
"""

import json
import os
import re
import sys
import threading
from datetime import datetime, timezone

from helpers.extension import Extension
from helpers.errors import RepairableException

_EXOCORTEX_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _EXOCORTEX_HELPERS not in sys.path:
    sys.path.insert(0, _EXOCORTEX_HELPERS)

TOOL = "memory_save"
SIMILARITY = 0.9        # A20: the threshold _52's _is_duplicate applies store-wide
# OFF 2026-09-24 (live finding, Kestrel). A0's relevance score is (1 + cos) / 2
# (plugins/_memory/helpers/memory.py L612, on a FAISS IndexFlatIP), so 0.9 here is cosine 0.8,
# not "near-identical". In cycle 750 this check refused three genuinely NEW memories in a row
# (02:54:24, 02:55:02, 02:55:52Z), all written in her BUILD status template, against recalled
# status memories 843lBLvV11 and vZf7EtWTak. The verbatim check below (A11) stays on. Opus
# re-rules A20 with the scale known; True restores the check exactly as it was.
SIMILARITY_CHECK = False
SEARCH_LIMIT = 20       # near-duplicates at 0.9 are few; a small cap keeps every one of them
_WS = re.compile(r"\s+")
# A24: metadata the harness writes (R2 source/validity, R1 key, lineage, R3 time and volatility).
HARNESS_FIELDS = ("subject_key", "classification", "lineage", "volatility", "observed_at")


def strip_harness_fields(tool_args) -> list:
    """Remove the harness-owned fields from memory_save's arguments, in place; return the names
    removed. Fails open: on any error the arguments stay as they were found."""
    removed = []
    try:
        if not isinstance(tool_args, dict):
            return removed
        present = [f for f in HARNESS_FIELDS if f in tool_args]
        kept = {f: tool_args[f] for f in present}
        try:
            for f in present:
                del tool_args[f]
                removed.append(f)
        except Exception:
            tool_args.update(kept)                  # put back whatever was removed
            return []
    except Exception:
        return []
    return removed


def normalize(text: str) -> str:
    return _WS.sub(" ", (text or "")).strip().lower()


# A recall head as _92's _with_provenance renders it, on its own line above the body:
# "recalled memory (saved <date>; ...):" or "recalled memory (save date unknown; ...):".
_RECALL_HEAD = re.compile(r"^\s*recalled memory \((?:saved |save date unknown)[^\n]*\):[ \t]*\r?\n",
                          re.IGNORECASE)


# ── The gate ledger (2026-09-25; Opus's A20 ruling + Fable's shadow check) ──────────────────────
# One row per refusal (the memory id it matched and the rule), and one per SHADOW event: a recalled
# body that appears whole inside a save it does not equal. Those saves pass; the row is what the
# containment decision waits on ("near-zero cost on 20+ productive cycles"), because a refusal log
# alone can never show them. Printing to stdout was the only record before; docker logs do not
# survive a container recreate, and this joins to cycle_endings.jsonl by context_id.
GATE_LOG = os.environ.get("EXO_RESAVE_GATE_LOG", "/a0/usr/plugins/_exocortex/state/resave_gate.jsonl")
_GATE_LOCK = threading.Lock()


def log_gate_event(agent, memory_id, rule, refused, **extra) -> bool:
    """Append one ledger row. Never raises; a failed write is printed, so a gap is visible."""
    try:
        row = {"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "context_id": getattr(getattr(agent, "context", None), "id", None),
               "agent": getattr(agent, "number", None),
               "memory_id": str(memory_id), "rule": rule, "refused": bool(refused)}
        row.update(extra)
        d = os.path.dirname(GATE_LOG)
        if d:
            os.makedirs(d, exist_ok=True)
        line = json.dumps(row, ensure_ascii=False) + "\n"
        with _GATE_LOCK:
            with open(GATE_LOG, "a", encoding="utf-8") as fh:
                fh.write(line)
        return True
    except Exception as e:
        print("[RESAVE-GATE] ledger write failed (%s: %s); this event is unrecorded" % (type(e).__name__, e),
              flush=True)
        return False


def strip_recall_head(text: str) -> str:
    """The text with ONE leading recall head removed when it starts with one; otherwise unchanged.

    Fable, 2026-09-25: check 1 compared a save only with the recalled BODY, so a save that copied
    the injected block whole (head line + body) was not equal to it and passed, and the head went
    into the store as content: the 09-08 mechanism. With check 2 off, nothing else caught it.
    Scope: one leading head. A copy of several blocks, or with the section header above, still
    passes, as before. Fails open: an error returns the text unchanged.
    """
    try:
        return _RECALL_HEAD.sub("", text or "", count=1)
    except Exception:
        return text


def _doc_id(doc) -> str:
    return str((getattr(doc, "metadata", None) or {}).get("id") or "")


def _unpack(item):
    return item[0] if isinstance(item, tuple) else item


class MemoryResaveGate(Extension):

    async def execute(self, tool_name: str = "", tool_args: dict | None = None, **kwargs) -> None:
        if tool_name != TOOL:
            return
        removed = strip_harness_fields(tool_args)
        if removed:
            print("[RESAVE-GATE] removed harness-owned fields from memory_save: %s" % ", ".join(removed), flush=True)
        text = str((tool_args or {}).get("text") or "")
        if not text.strip():
            return
        try:
            import memory_recall_tag as mrt
            recalled = mrt.recalled(self.agent)
        except Exception:
            return                                  # fail open
        if not recalled:
            return

        try:
            from plugins._memory.helpers.memory import Memory
            db = await Memory.get(self.agent)
            docs = db.db.get_all_docs() if db and db.db else {}
        except Exception:
            return                                  # fail open

        # 1. verbatim, after normalization; and again with one leading recall head removed, so a
        #    copy of the injected block (head line + body) is the same text (Fable, 2026-09-25)
        mine = normalize(text)
        mine_body = normalize(strip_recall_head(text))
        if mine_body == mine:
            mine_body = ""                           # no head was removed: one comparison is enough
        contained = []
        for doc in docs.values():
            did = _doc_id(doc)
            if did not in recalled:
                continue
            body = normalize(getattr(doc, "page_content", ""))
            if body == mine:
                self._refuse(did, doc, "repeats memory %s word for word", "verbatim")
            if mine_body and body == mine_body:
                self._refuse(did, doc, "repeats memory %s word for word, recall head included",
                             "verbatim_with_head")
            if body and body in mine:
                contained.append((did, len(body)))

        # Shadow containment (Fable, 2026-09-25): reached only when check 1 refused nothing, so every
        # body listed here sits inside the save without equalling it. Logged as would-refuse; the
        # save goes through. No behaviour change; the ledger write never raises.
        for did, n in contained:
            log_gate_event(self.agent, did, "containment", False,
                           chars_incoming=len(mine), chars_recalled=n)

        # 2. a near-paraphrase of a recalled memory (off: see SIMILARITY_CHECK)
        if not SIMILARITY_CHECK:
            return
        try:
            hits = await db.search_similarity_threshold(query=text, limit=SEARCH_LIMIT, threshold=SIMILARITY)
        except Exception:
            return                                  # fail open
        for item in hits or []:
            doc = _unpack(item)
            did = _doc_id(doc)
            if did in recalled:
                self._refuse(did, doc, "is near-identical to memory %%s (similarity >= %.1f)" % SIMILARITY,
                             "similar")

    def _refuse(self, did: str, doc, how: str, rule: str = "") -> None:
        """`how` is a clause with one %s for the memory id, e.g. "repeats memory %s word for word".
        Every refusal is written to the gate ledger with the id it matched (Opus, 2026-09-25)."""
        when = str((getattr(doc, "metadata", None) or {}).get("timestamp") or "")
        what = how % did
        log_gate_event(self.agent, did, rule or "unnamed", True)
        print("[RESAVE-GATE] refused memory_save: it %s, recalled this turn (%s)" % (what, when), flush=True)
        raise RepairableException(
            "memory_save refused: this text %s%s, and that memory was recalled into this turn. "
            "A recalled memory is not new evidence, and saving it again makes it look more "
            "established than it is. Save what this turn observed or decided. If something has "
            "changed since that memory, say what changed and how you know."
            % (what, (", saved %s" % when) if when else ""))
