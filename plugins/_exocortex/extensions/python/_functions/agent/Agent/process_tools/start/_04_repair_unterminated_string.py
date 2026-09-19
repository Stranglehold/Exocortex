"""
_04_repair_unterminated_string.py — process_tools/start (runs before Kestrel's _05 prose-leak detector)
=======================================================================================================
Repairs ONE defect in the model's reply: a JSON tool call whose last string value lost its closing quote before the
line break, while the closing braces that follow show the model emitted the rest of the structure. Measured shape,
2026-09-15 (cycles 582, 586, 590; every rejected call ended like this):

    "tool_args": {
        "runtime": "terminal",
        "code": "cd /a0/usr/workdir/workspace && ls -1 | head -n 5      <- no closing quote
    }
}

Strict JSON reports "Invalid control character" at the line break inside the string; Agent Zero's extractor then finds
no tool request, the generic misformat warning fires, the model re-emits the same bytes, and five of those end the
cycle (core _90_stop_unusable_response_loop, max_consecutive_unusable_responses 5). Three cycles died this way today.

What it does: if the strict parse fails inside a string value and everything after the offending line break is
closing structure only (braces, brackets, commas, whitespace), it inserts the missing quote at the end of that line,
re-parses, and hands the repaired text on ONLY if it now parses and looks like a tool request. It logs
[STRING-REPAIR] with the key and line.

What it never does: repair a reply that ends INSIDE the string (no closing structure after it). That is a truncated
reply, and closing a truncated shell command could run a different command than the one she meant. It also leaves
prose-wrapped calls alone (Kestrel's _05) and anything whose error is not a string error.

Additive diagnostic (Kestrel's constraint, 2026-09-15 14:30): when it cannot repair a string error it adds ONE warning
naming the defect and the key; the framework's standard misformat warning still follows unchanged, so the five-strike
counter keeps counting. It never replaces the standard warning.

Scope (Kestrel's review, 2026-09-15 17:2x): it only sees replies where the tool call IS the whole message, because the
v2.9 extractor requires root == content; anything fenced or prose-wrapped classifies "other" here and falls to _05/_10.
That division is deliberate: do not widen this file to prose. Every passthrough logs the decoder's own message, so a
quiet log means quiet and a log full of "Expecting ',' delimiter" means the shape has moved and this repair no longer
aims at it.

Second repair, invalid backslash escapes (2026-09-15 18:5x, Kestrel's design and review). The lenient extractor does
NOT reject an invalid escape: it swallows the backslash and the character after it and the command runs. Measured in
her venv:  ls C:\\users\\jake\\AppData  ->  ls C:\\usersakeppData.  Not a crash, not a warning: a DIFFERENT PATH TRAVERSED.
A regex of \\d+ became +. So an invalid escape is doubled at the decoder's reported position (both message forms, the
plain one at the backslash and the \\uXXXX one at the 'u'), the loop is bounded, and the result is handed on only if it
parses and carries a tool_name. Valid escapes are untouched by construction: a valid escape never raises, so the
decoder never hands this code a position there. For escapes a DECLINE is not a safe passthrough (the extractor would
corrupt and run), so every decline that has seen an escape adds the escape diagnostic beside the standard warning.

BOUNDARY, written down so nobody relaxes this later: coverage is escapes the strict parser REACHES before the first
unrecoverable structural error. A reply whose first strict error is structural (a missing comma, say) returns "other"
and passes through; if the lenient extractor then repairs the structure it will still swallow any invalid escape
behind it, and that reply executes corrupted and unwarned, exactly as before this file existed. This file cannot warn
about escapes the parser never reached, and a lexical pre-scan for backslash-looking sequences is the kind of gate
that has burned this project; the limit is stated instead of assumed.
"""
import json
import re

from helpers.extension import Extension

try:  # the same reader Kestrel's _05 and _10 use, so all three see the same message
    import sys as _sys
    _HELPERS = "/a0/usr/plugins/_exocortex/helpers"
    if _HELPERS not in _sys.path:
        _sys.path.insert(0, _HELPERS)
    from prose_leak import read_msg as _read_msg
except Exception:  # pragma: no cover - fallback mirrors it
    def _read_msg(data):
        kwargs = data.get("kwargs")
        if isinstance(kwargs, dict) and "msg" in kwargs:
            return kwargs["msg"], "kwargs", -1
        args = data.get("args")
        if isinstance(args, (list, tuple)):
            for i in range(len(args) - 1, -1, -1):
                if isinstance(args[i], str):
                    return args[i], "args", i
        return None, "", -1


def _write_msg(data, where, index, value):
    if where == "kwargs":
        data["kwargs"]["msg"] = value
    elif where == "args" and index >= 0:
        args = list(data["args"])
        args[index] = value
        data["args"] = tuple(args)


# Proof of load (2026-09-15 18:1x): the class cache is rebuilt on the first process_tools call after a plugin change, and
# that rebuild imports this module; one line here is the only direct evidence the running process has this code.
print("[STRING-REPAIR] loaded (module import): repairs a dropped closing quote before closing structure and invalid "
      "backslash escapes at the decoder's position; never truncation; escapes behind a structural error are out of reach",
      flush=True)

_CLOSING_ONLY = re.compile(r"^[\s\]\},]*$")
_KEY_BEFORE = re.compile(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:\s*"')
_STRING_ERRORS = ("Invalid control character", "Unterminated string")


def _key_of_string_at(text: str, pos: int) -> str:
    """Name of the key whose string value contains position pos (best effort, for the log and the diagnostic)."""
    best = None
    for m in _KEY_BEFORE.finditer(text, 0, pos + 1):
        best = m.group(1)
    return best or "?"


# Both forms the decoder emits (measured in her venv, 2026-09-15 18:5x): "Invalid \escape" with pos AT the backslash,
# and "Invalid \uXXXX escape" (a \u not followed by four hex digits, e.g. a lowercase Windows path C:\users) with pos at
# the 'u', backslash at pos - 1. Kestrel's review: the second form fell straight through to silent corruption.
_ESCAPE_ERRORS = ("Invalid \\escape", "Invalid \\uXXXX escape")
_MAX_ESCAPE_REPAIRS = 64   # a script with many regexes or Windows paths; each pass is one json.loads on a few KB


def analyse(text: str) -> dict:
    """Classify a reply. Returns {"kind": "ok"|"repaired"|"truncated"|"other", "text": repaired_or_None,
    "key": str, "line": int, "error": str, "escapes": int}.

    Two repairs, each keyed on the decoder's reported position, never on a global substitution:
    - a dropped closing quote (Invalid control character at a line break) is closed ONLY when everything after the
      break is closing structure, because the other reading is a truncated command (Kestrel's discriminator);
    - an invalid backslash escape (Invalid \\escape) is doubled where it sits, because a valid escape would not have
      raised, so the error itself proves a literal backslash was meant; there is no second reading to guard against
      and the closing-structure test would wrongly decline nearly every real case (Kestrel's design note, 18:3x).
    Both hand on only if the result parses as a tool request. The loop is bounded; the count is logged."""
    empty = {"kind": "other", "text": None, "key": "?", "line": 0, "error": "", "escapes": 0, "closed_quote": False}
    if not isinstance(text, str) or len(text) < 10:
        return empty
    stripped = text.strip()
    current = stripped
    escapes = 0
    closed_quote = False
    first_err = None

    def out(kind, error, key="?", line=0, text_=None):
        return {"kind": kind, "text": text_, "key": key, "line": line, "error": error,
                "escapes": escapes, "closed_quote": closed_quote}

    for _ in range(_MAX_ESCAPE_REPAIRS + 2):
        try:
            obj = json.loads(current)
        except json.JSONDecodeError as e:
            err = e
        else:
            if not (isinstance(obj, dict) and "tool_name" in obj):
                if current == stripped:
                    return out("other", "parses as JSON but carries no tool_name")
                # a repair produced JSON that is not a call: if escapes were involved, declining is a corruption path
                return out("escape_declined" if escapes else "other", "repaired text is not a tool request",
                           _key_of_string_at(stripped, first_err.pos), first_err.lineno)
            if current == stripped:
                return out("ok", "")
            return out("repaired", first_err.msg, _key_of_string_at(stripped, first_err.pos), first_err.lineno, current)
        if first_err is None:
            first_err = err
        key = _key_of_string_at(current, err.pos)
        if any(err.msg.startswith(s) for s in _ESCAPE_ERRORS):
            # Declining here is NOT a safe passthrough: the lenient extractor swallows the backslash and the next
            # character and the command runs (Kestrel's review). Every decline below carries the diagnostic.
            if escapes >= _MAX_ESCAPE_REPAIRS:
                return out("escape_declined", f"{err.msg}; more than {_MAX_ESCAPE_REPAIRS} invalid escapes", key, err.lineno)
            pos = err.pos
            if pos < len(current) and current[pos] == "\\":
                bpos = pos
            elif pos > 0 and current[pos - 1] == "\\":
                bpos = pos - 1                      # the \uXXXX form reports the 'u'
            else:
                return out("escape_declined", f"{err.msg}; no backslash at the reported position", key, err.lineno)
            current = current[:bpos] + "\\" + current[bpos:]
            escapes += 1
            continue
        if not any(err.msg.startswith(s) for s in _STRING_ERRORS):
            return out("escape_declined" if escapes else "other", err.msg, key, err.lineno)
        if err.msg.startswith("Unterminated string"):
            return out("truncated", err.msg, key, err.lineno)
        # Invalid control character: a line break with only closing structure after it?
        pos = err.pos
        if pos >= len(current) or current[pos] not in "\r\n":
            return out("escape_declined" if escapes else "other", err.msg, key, err.lineno)
        rest = current[pos:]
        if not _CLOSING_ONLY.match(rest) or closed_quote:
            return out("truncated", err.msg, key, err.lineno)
        current = current[:pos] + '"' + rest
        closed_quote = True
    return out("escape_declined" if escapes else "other", "repair loop exhausted", "?",
               first_err.lineno if first_err else 0)


def _root_object_starts(text: str) -> list[int]:
    """Offsets of every '{' at depth 0. A0's own scan (helpers/extract_tools._json_root_object_starts)
    reimplemented here rather than imported: this file must keep working if core moves, and the scan
    is four lines of state. Quotes are only tracked inside an object, as core does it."""
    starts, depth, quote, escaped = [], 0, None, False
    for i, ch in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if depth and ch in ('"', "'", "`"):
            quote = ch
        elif ch == "{":
            if depth == 0:
                starts.append(i)
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
    return starts


def analyse_embedded(text: str) -> dict | None:
    """Analyse a JSON root EMBEDDED in prose. Returns analyse()'s verdict plus {"start": offset}.

    WHY THIS EXISTS, measured 2026-09-18 on Jake's "Workspace Scripts" chat.

    Aporia looped: reasoning prose, then a `code_execution_tool` call whose `code` value held a
    LITERAL NEWLINE — a multi-line shell command written without \\n. Strict parsing names it
    exactly: `Invalid control character at line 12 column 600`. **That is precisely the class this
    file repairs**, and the repair was proven to work on both real payloads.

    It never got the chance. `analyse()` parses the WHOLE message, which begins with prose, so
    json.loads fails at character 1 with "Expecting value", and this extension concluded "not a
    string error" — **correctly, about the wrong string**. `_05` then found no root (DirtyJson
    cannot complete a broken object), logged nothing because it returns before it logs, and `_10`
    wrapped the prose as a response. A repairable call died inside a turn that reported completed.

    So the defect was never the repair logic; it was WHICH STRING the repair logic was pointed at.
    This routes it at the right one and changes nothing else.

    Returns None unless a root is found AND analysing it yields a repair — a verdict that is not
    "repaired" is left to the existing branches, which already own the top-level cases.
    """
    if not isinstance(text, str):
        return None
    stripped = text.strip()
    for start in _root_object_starts(stripped):
        if start == 0:
            continue  # the whole message IS the root; analyse() already had it
        verdict = analyse(stripped[start:])
        if verdict["kind"] == "repaired":
            verdict = dict(verdict)
            verdict["start"] = start
            return verdict
    return None


def diagnostic(key: str, line: int, error: str) -> str:
    return (f"Your last reply was not a valid tool call: {error} at line {line}, inside the string value of \"{key}\". "
            f"A JSON string must end with a double quote on the same line and cannot contain raw line breaks. "
            f"Close the string before the closing brace; put long shell scripts or file contents in a file first "
            f"and run or read the file instead of pasting them inline.")


def escape_diagnostic(key: str, line: int, error: str) -> str:
    return (f"Your last reply carried an invalid backslash escape: {error} at line {line}, inside the string value of "
            f"\"{key}\". In JSON a backslash may only precede one of \" \\ / b f n r t u; a literal backslash (a regex "
            f"like \\d+ or a Windows path like C:\\Users) must be written doubled, as \\\\. Left as it is, the backslash "
            f"and the character after it are silently dropped before the command runs. Rewrite the reply with the "
            f"backslashes doubled, or put the script in a file and run the file.")


class RepairUnterminatedString(Extension):

    async def execute(self, data: dict | None = None, **kwargs) -> None:
        if not isinstance(data, dict):
            return
        try:
            msg, where, index = _read_msg(data)
            if not isinstance(msg, str):
                return
            verdict = analyse(msg)
            kind = verdict["kind"]
            if kind == "repaired":
                _write_msg(data, where, index, verdict["text"])
                what = []
                if verdict["escapes"]:
                    what.append(f"doubled {verdict['escapes']} invalid escape(s)")
                if verdict["closed_quote"]:
                    what.append(f"closed the string value of \"{verdict['key']}\"")
                print(f"[STRING-REPAIR] repaired: {'; '.join(what) or 'repaired'} at line {verdict['line']} "
                      f"({len(msg)} chars)", flush=True)
            elif kind == "escape_declined":
                print(f"[STRING-REPAIR] escape NOT repaired ({verdict['error']}; key \"{verdict['key']}\", line "
                      f"{verdict['line']}, {verdict['escapes']} doubled before declining); diagnostic added: the lenient "
                      f"extractor would otherwise drop the backslash and run the command", flush=True)
                try:
                    self.agent.hist_add_warning(escape_diagnostic(verdict["key"], verdict["line"], verdict["error"]))
                except Exception as e:
                    print(f"[STRING-REPAIR] diagnostic not added: {type(e).__name__}: {e}", flush=True)
            elif kind == "truncated":
                print(f"[STRING-REPAIR] not repaired (reply ends inside the string value of \"{verdict['key']}\", "
                      f"line {verdict['line']}: {verdict['error']}); diagnostic added, standard warning follows", flush=True)
                try:
                    self.agent.hist_add_warning(diagnostic(verdict["key"], verdict["line"], verdict["error"]))
                except Exception as e:  # never let the diagnostic break the turn
                    print(f"[STRING-REPAIR] diagnostic not added: {type(e).__name__}: {e}", flush=True)
            elif kind == "other" and "Expecting value" in (verdict["error"] or ""):
                # THE WHOLE MESSAGE IS NOT JSON AT ALL — prose wrapping a call. Point the same
                # repair at the embedded root instead. Guarded on "Expecting value" specifically:
                # this branch also catches "parses as JSON but carries no tool_name", which parsed
                # fine and has nothing to repair, and whose nested objects are not roots.
                emb = analyse_embedded(msg)
                if emb:
                    stripped = msg.strip()
                    spliced = stripped[: emb["start"]] + emb["text"]
                    _write_msg(data, where, index, spliced)
                    what = []
                    if emb["escapes"]:
                        what.append(f"doubled {emb['escapes']} invalid escape(s)")
                    if emb["closed_quote"]:
                        what.append(f"closed the string value of \"{emb['key']}\"")
                    print(f"[STRING-REPAIR] repaired the EMBEDDED root at offset {emb['start']}: "
                          f"{'; '.join(what) or 'repaired'} at line {emb['line']} — "
                          f"{emb['start']} chars of prose kept for _05 to extract", flush=True)
                else:
                    print(f"[STRING-REPAIR] not a string error ({verdict['error']} at line {verdict['line']}) "
                          f"— no repairable embedded root either; passthrough to _05/_10 and the "
                          f"standard warning", flush=True)
            elif kind == "other" and verdict["error"]:
                # Kestrel's review (2026-09-15): the passthrough must log, or a quiet log cannot be told from an analyser
                # that never matched. A log full of these with a different decoder message says the shape has moved.
                print(f"[STRING-REPAIR] not a string error ({verdict['error']} at line {verdict['line']}) — passthrough "
                      f"to _05/_10 and the standard warning", flush=True)
        except Exception as e:  # fail open: the standard path still runs
            print(f"[STRING-REPAIR] error (passthrough): {type(e).__name__}: {e}", flush=True)
