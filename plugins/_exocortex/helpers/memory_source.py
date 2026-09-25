"""
memory_source.py — who a memory's words came from, decided by structure (R2, A19)

WHY THIS EXISTS
---------------
`classification.source` decides trust: user_asserted → validity confirmed, which wins conflicts
and is never auto-deprecated against another user_asserted memory. Until 2026-09-23 three
writers set it three different ways, and none of them looked at structure:
  - _52_selective_memorizer took the utility model's label. The model is shown A0's history,
    where every TOOL RESULT is a non-AI message (agent.py hist_add_tool_result →
    hist_add_message(False, …)), and _52 printed non-AI entries as "USER:". So a failing
    list_collections came back as "the user says the library is down", saved as confirmed.
  - _55_memory_classifier._detect_source matched text against "the user message", which in an
    idle cycle is the daemon's activation prompt, and called any text with a URL and a date
    external_retrieved.
  - _53_insight_capture hardcoded user_asserted, and read "the user message" as the last
    non-AI history entry, which after a tool call is a tool result.

Opus's rulings (memory lifecycle design note, R2 as amended by A3, A4, A5, A9, A19): the model
decides WHAT to save; structure decides WHO said it. One function, used by every writer.

THE RULES (A19), in order
-------------------------
  1. In an idle cycle or a subordinate agent, nothing is user_asserted: nobody there is Jake.
     (The cycle is `context.data["idle_cycle"]`, set by our idle_cycle fire endpoint and kept
     for the life of the context; the subordinate is `agent.data["_superior"]`.)
  2. area "solutions" → agent_inferred (kept from _55).
  3. Drawn from an allowlisted tool's return in this exchange (A0's current topic)
     → external_retrieved.
  4. Interactive, and drawn from the message that started this monologue → user_asserted.
  5. Otherwise → agent_inferred.
`validity` follows: confirmed for user_asserted, inferred for the rest.

Two measures, on purpose. Rule 4 uses _55's `_text_overlaps` unchanged (moved here as
`overlaps`), so for the user message behaviour is exactly what it was. Rule 3 uses
`from_tool`, which counts CONTENT words: `_text_overlaps` divides by the smaller word set, and a
large tool result contains most common words, so a short memory would too easily look drawn
from it. And only tools that read from OUTSIDE her store and workspace are evidence (Opus's
ruling on item 7, 2026-09-23): a journal, wiki or index she reads back through
code_execution_tool, text_editor or parallel is her own writing, not an observation, and Fable
found it deriving external_retrieved (`tkdtmDYTNP`, #734: her journal tail in a `parallel`
return). The same holds for our memory server's corpus tools, which serve her own exported
writing back to her; only its book library and status tools count. Memory tools were never
evidence: a memory_load result is recall (R4 marks it), a memory_save result is a receipt. A
fact she really did fetch from outside through code loses the label, not the fact: the safe
direction.

THE DERIVATION MARKER (graduated trust GT-2a, 2026-09-25)
--------------------------------------------------------
derive_source_rule() also returns which rule decided ("A19.1" … "A19.5"), and the three writers
store it as `classification.source_rule` on NEW saves. The recall frame (helpers/memory_trust.py)
shows a stored source only when the marker is present; without it the source renders as
`legacy`, because a label that no derivation rule produced is the model's claim, not provenance.

WHAT THIS DOES NOT DO
---------------------
- Does not relabel existing memories, and does not backfill the marker. Forward-only (R2).
- Does not decide what gets saved.
- No LLM calls. Dict and set operations over the agent's history.
"""

import json
import re

# A0: Agent.DATA_NAME_SUPERIOR (agent.py L364), and the context-data key the idle_cycle fire
# endpoint sets on every cycle context.
SUPERIOR_KEY = "_superior"
CYCLE_KEY = "idle_cycle"

# Tools whose results are the store talking about itself, not external evidence.
MEMORY_TOOLS = frozenset({"memory_load", "memory_save", "memory_delete", "memory_forget"})

# Rule 3's evidence: tools whose returns come from outside her store and workspace (Opus, item 7
# and its addendum, 2026-09-23). From our memory server only the book library and its status
# count. Its corpus tools (search_memory, search_all, search_by_type, get_document, get_section)
# serve her own exported wiki and field reports back to her: all 11 corpus results in her 14
# retained chats carried them, 3 all or nearly all. Everything else, code_execution_tool,
# text_editor and parallel included, is never evidence. On those chats (tallied 2026-09-23) this
# admits 12 of 129 tool results: list_collections 3, search_library 4, arxiv 5.
EXTERNAL_TOOLS = frozenset({"search_engine", "document_query",
                            "exocortex_memory.search_library", "exocortex_memory.list_collections"})
EXTERNAL_PREFIXES = ("arxiv.", "browser")

# "This exchange" (A19 rule 3) is A0's current history topic: hist_add_user_message calls
# self.history.new_topic() for every user message (agent.py), so `history.current` holds the
# message that started this monologue and everything since. In an idle cycle that is the whole
# cycle: #735 ran 39 entries with 14 tool returns, and the 12-entry window R2 first shipped with
# held 4 of them, not the list_collections return (Fable, 2026-09-23). Compression never moves
# the boundary: History.compress() works on `current` in place (large messages truncated, a
# truncated tool result still a {tool_name, tool_result} dict; attention summaries lose entries,
# which can only make rule 3 fire less). TOOL_WINDOW is the fallback for a history without a
# current topic: the last 12 entries, _52's slice doubled, as R2 first shipped.
TOOL_WINDOW = 12

_STOP = frozenset("""
a an and are as at be been but by can could did do does for from had has have how i if in into
is it its may might no not of on or our out so than that the their them then there these they
this those to too up us was we were what when where which while who why will with would you
your yes all any also just more most only other over same some such very""".split())
_WORD = re.compile(r"[a-z0-9_]{3,}")


def is_restricted(agent) -> bool:
    """True in an idle cycle or a subordinate agent (rule 1). When unsure, restricted:
    the error can only withhold user_asserted, never grant it."""
    try:
        if agent.get_data(SUPERIOR_KEY) is not None:
            return True
        return bool(agent.context.get_data(CYCLE_KEY))
    except Exception:
        return True


def user_message_text(loop_data) -> str:
    """The message that started this monologue (A19 (a)). Not "the last non-AI history
    entry": in A0 that is often a tool result."""
    um = getattr(loop_data, "user_message", None)
    if not um:
        return ""
    try:
        return um.output_text() if hasattr(um, "output_text") else str(um)
    except Exception:
        return ""


def _tool_entry(content):
    """(tool_name, result text) if this history content is a tool result, else None."""
    if isinstance(content, str):
        s = content.strip()
        if not (s.startswith("{") and '"tool_name"' in s):
            return None
        try:
            content = json.loads(s)
        except Exception:
            return None
    if isinstance(content, dict) and "tool_name" in content and "tool_result" in content:
        r = content.get("tool_result")
        return str(content.get("tool_name") or ""), (r if isinstance(r, str) else json.dumps(r, ensure_ascii=False))
    return None


def is_external_tool(name: str) -> bool:
    """Whether this tool's return can be rule 3's evidence (the item-7 allowlist)."""
    n = (name or "").strip()
    return n not in MEMORY_TOOLS and (n in EXTERNAL_TOOLS or n.startswith(EXTERNAL_PREFIXES))


def is_tool_entry(content) -> bool:
    """Whether a history entry's content is a tool result, recognised by structure (A19 (b))."""
    return _tool_entry(content) is not None


def exchange_entries(agent, window: int = TOOL_WINDOW) -> list:
    """This exchange's history entries: A0's current topic, or, for a history without one, its
    last `window` entries. A topic that has been summarized outputs one summary string, which
    holds no tool result, so rule 3 cannot fire from it: the safe direction."""
    history = agent.history
    current = getattr(history, "current", None)
    if current is not None and hasattr(current, "output"):
        return list(current.output())
    return list(history.output())[-window:]


def tool_returns(agent, window: int = TOOL_WINDOW) -> list:
    """Result texts of this exchange's calls to allowlisted tools (rule 3's evidence)."""
    out = []
    try:
        outputs = exchange_entries(agent, window)
    except Exception:
        return out
    for msg in outputs:
        if msg.get("ai", True):
            continue
        hit = _tool_entry(msg.get("content"))
        if hit and is_external_tool(hit[0]) and hit[1]:
            out.append(hit[1])
    return out


def overlaps(memory_text: str, other: str) -> bool:
    """_55_memory_classifier._text_overlaps, unchanged: substring, or word overlap of at least
    0.6 of the smaller set. Used for the user message (rule 4)."""
    if not memory_text or not other:
        return False
    mem = memory_text.lower().strip()
    msg = other.lower().strip()
    if len(mem) > 10 and mem in msg:
        return True
    mem_words = set(mem.split())
    msg_words = set(msg.split())
    if not mem_words or not msg_words:
        return False
    overlap = len(mem_words & msg_words)
    smaller = min(len(mem_words), len(msg_words))
    return smaller > 0 and (overlap / smaller) >= 0.6


def _content_words(text: str) -> set:
    return {w for w in _WORD.findall((text or "").lower()) if w not in _STOP}


def from_tool(memory_text: str, tool_text: str) -> bool:
    """Whether the memory is drawn from this tool result (rule 3): at least 3 of the memory's
    content words, and at least 0.6 of them, appear in the result. The denominator is the
    memory's own content words, so a large result's vocabulary does not do the work."""
    mem = _content_words(memory_text)
    if len(mem) < 3:
        return False
    shared = len(mem & _content_words(tool_text))
    return shared >= 3 and shared / len(mem) >= 0.6


def derive_source_rule(agent, text: str, *, user_msg: str = "", tool_texts=(), area: str = ""):
    """(source, rule): A19's rules 1-5 in order, and the identifier of the rule that decided.

    The rule is the DERIVATION MARKER (graduated trust GT-2a, Opus 2026-09-25): writers store it as
    `classification.source_rule`, and the recall frame shows a stored source only when the marker
    is present. Before this, nothing distinguished a source R2 derived from one the model labelled.
    "A19.1" is recorded when the text overlaps the user message but the context is an idle cycle
    or a subordinate, so the gate withheld user_asserted. The source is exactly derive_source's.
    """
    if area == "solutions":
        return "agent_inferred", "A19.2"
    if any(from_tool(text, t) for t in (tool_texts or ())):
        return "external_retrieved", "A19.3"
    if user_msg and not is_restricted(agent) and overlaps(text, user_msg):
        return "user_asserted", "A19.4"
    if user_msg and overlaps(text, user_msg):
        return "agent_inferred", "A19.1"
    return "agent_inferred", "A19.5"


def derive_source(agent, text: str, *, user_msg: str = "", tool_texts=(), area: str = "") -> str:
    """A19's rules 1-5, in order. Deterministic. (The source half of derive_source_rule.)"""
    return derive_source_rule(agent, text, user_msg=user_msg, tool_texts=tool_texts, area=area)[0]


def validity_for(source: str) -> str:
    """R2: validity follows the (now structural) source."""
    return "confirmed" if source == "user_asserted" else "inferred"
