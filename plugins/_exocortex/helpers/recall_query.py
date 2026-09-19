"""
recall_query.py — what we hand the embedder when recalling memories.

ONE implementation, imported by `_55_memory_relevance_filter` and `_56_memory_enhancement`. Both
carried a byte-identical `_get_query` before this file existed, and a rule that lives in two files
is free to drift silently — the same reason `helpers/attendedness.py` was extracted from `_07`.

WHAT WAS MEASURED, 2026-09-16 (Fable, from LM Studio's own server log, 42 h)
---------------------------------------------------------------------------
2,882 embedding requests, **919 truncated, and every truncated one was a RECALL QUERY** — never a
memory. 1,800 of them embedded the raw idle activation charge, 785 at exactly 2,120 tokens against
nomic-embed-v1.5's hard 2,048 ceiling. Not one of ~235 real memory texts was truncated.

TWO DEFECTS, TWO MECHANISMS. They are separable and this file fixes both differently:

  1. TRUNCATION — the query overflows the embedder. Fixed by `max_chars`, applied
     **unconditionally**, on every context. A query that does not fit is silently cut, and the cut
     end is the part the model wrote most recently.

  2. CONSTANCY — on an idle cycle the query is the activation charge, which is the SAME TEXT every
     turn. Measured downstream: "Query expansion: 13 candidates" on 410 of 436 runs, "6 memories
     injected" on all 224 turns, and only TWO distinct id-sets in the last 40 co-retrieval entries.
     Same question every turn, same memories every turn. Fixed by building the query from the
     RECENT WORK instead — but only on an idle cycle, where the "user message" is a fixed charge
     rather than something a person actually asked.

On a driven turn the user message IS the question, so the source is left exactly as it was. Only
the bound applies there.

WHY THE BOUND IS 1,200 CHARACTERS BY DEFAULT
--------------------------------------------
nomic-embed-v1.5 caps at 2,048 tokens and the GGUF header says so — it is the file, not a setting.
At a conservative 3 characters per token (paths and code run denser than prose) 1,200 chars is
~400 tokens: a fivefold margin, so no realistic tokenisation truncates.

The margin is deliberate rather than timid. **Shorter is also better for retrieval.** A 2,120-token
query averages to semantic mush, which is exactly what the measurement shows — a constant of that
length returned the same six memories every turn for a day. The bound is a retrieval-quality
decision as much as a truncation fix.

Configurable at `memory_enhancement.recall_query.max_chars`; this default applies when unset.

!! EDITING THIS FILE LATER NEEDS A CONTAINER RESTART !!
--------------------------------------------------------
Read in the container 2026-09-17, because it is not obvious and it will cost someone an hour.

The EXTENSION that imports this (`_56`) is reloaded cheaply: `helpers/modules.import_module`
(modules.py:12-24) does `spec_from_file_location` + `exec_module` on every load and **never
consults or writes `sys.modules`**, so `_56`'s body — including its `import recall_query` —
re-executes whenever the plugins watchdog clears the extension cache. That is why deploying this
helper needs no restart the FIRST time.

THIS file does not get that. It is imported by bare name, so it DOES land in `sys.modules`, and
`after_plugin_change` calls `modules.purge_namespace("plugins")`, which deletes only names equal to
or under `plugins.` (modules.py:83-93). `recall_query` is not under that namespace, so it survives
every reload. **Edit this file and the running process keeps the old one until the container
restarts.**

And the deploy order follows from the same mechanism: **this helper must land BEFORE `_56`.** The
watchdog fires on any change under `extensions/`, not on `helpers/`. If `_56` arrives first it
re-executes against a helper that does not exist yet, sets `recall_query = None`, and stays that
way — copying the helper afterwards triggers nothing, so nothing reloads it.
"""

from typing import Any

#: Must match `helpers/attendedness.py` IDLE_MARKER_KEY and `api/idle_cycle.py`. The in-process
#: marker set for the duration of an idle cycle; presence is the signal, never `is True`.
IDLE_MARKER_KEY = "idle_cycle"

DEFAULT_MAX_CHARS = 1200

#: How many trailing history entries to render for the recent-work query. Four covers her last
#: message and the tool result before it with room for the pair that preceded them.
HISTORY_TAIL = 4


def _bound(text: str, max_chars: int) -> str:
    """Trim to `max_chars`, keeping the TAIL.

    The most recent text is the most relevant to what she is doing now, and it is also the part a
    head-truncation would throw away.
    """
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def is_idle_cycle(agent) -> bool:
    """True when this context is an idle cycle. Presence of the marker is the signal.

    Fails to False on any error, which leaves the query source unchanged — the pre-existing
    behaviour. This guard decides which TEXT to embed, never whether to act, so failing to the old
    behaviour is the safe direction.
    """
    try:
        return agent.context.get_data(IDLE_MARKER_KEY) is not None
    except Exception:
        return False


def _recent_work(loop_data) -> str:
    """Her last response plus the tail of history — what she is actually working on."""
    parts = []
    try:
        tail = getattr(loop_data, "history_output", None) or []
        if tail:
            from helpers import history as _history
            parts.append(_history.output_text(tail[-HISTORY_TAIL:]))
    except Exception:
        pass
    try:
        last = getattr(loop_data, "last_response", "") or ""
        if last:
            parts.append(last)
    except Exception:
        pass
    return "\n\n".join(p for p in parts if p)


def _user_message(loop_data) -> str:
    """The original behaviour, unchanged: the user message as the query."""
    try:
        um = getattr(loop_data, "user_message", None)
        if not um:
            return ""
        if hasattr(um, "output_text"):
            return um.output_text()
        return str(um)
    except Exception:
        return ""


def build_query(agent, loop_data, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """The text handed to the embedder for memory recall.

    Idle cycle  -> the recent work, bounded. Falls back to the bounded user message if history is
                   unavailable, so the truncation fix still applies when the source switch cannot.
    Driven turn -> the user message, bounded. Source unchanged.
    """
    if max_chars is None or max_chars <= 0:
        max_chars = DEFAULT_MAX_CHARS

    if is_idle_cycle(agent):
        recent = _recent_work(loop_data)
        if recent:
            return _bound(recent, max_chars)
        # No history to work from — still bound it. Falling through to the unbounded charge is the
        # defect this file exists to remove, so the bound is never skipped.
    return _bound(_user_message(loop_data), max_chars)
