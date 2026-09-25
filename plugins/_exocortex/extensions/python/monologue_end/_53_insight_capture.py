"""
Conversational Insight Capture — Agent-Zero Cognitive Architecture
==================================================================
Hook: monologue_end
Priority: _53 (after selective memorizer at _52, before classifier at _55)

Deterministic complement to _52_selective_memorizer. Where the selective
memorizer uses a utility model call to extract memories from the full exchange,
this extension uses regex patterns tuned for Jake's specific communication
style: intent signals, preference signals, decisions, and strategic observations
embedded in general conversation.

No LLM calls. Pure pattern matching on the most recent user message.
Stores matched sentences directly to memory with pre-set classification,
which the _55 classifier recognizes as already tagged.

Signal categories:
  - intent:      "I plan to", "I had a plan for", "eventually I want to"
  - preference:  "I prefer", "I'd rather", "I always / I never"
  - decision:    "we decided", "from now on", "I'm going with"
  - observation: "I noticed", "turns out", "I realized", "this explains"
  - framing:     "I view X as", "I don't view X as" — ownership / attribution signals

Deduplicates against existing memory via similarity search at 0.92 threshold.
"""

import re
from datetime import datetime, timezone
from typing import Any

from agent import LoopData
from helpers.extension import Extension
from plugins._memory.helpers.memory import Memory

# R2 (memory lifecycle design, Opus 2026-09-23, A19): who said it is decided by structure in
# helpers/memory_source.py, shared with _52 and _55. If the helper cannot load, this file
# behaves as before.
_EXOCORTEX_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _EXOCORTEX_HELPERS not in __import__("sys").path:
    __import__("sys").path.insert(0, _EXOCORTEX_HELPERS)
try:
    import memory_source as _ms
except Exception:  # pragma: no cover - helper missing
    _ms = None

# ── Configuration ─────────────────────────────────────────────────────────────

MIN_SENTENCE_WORDS = 5        # Skip fragments shorter than this
MAX_SENTENCE_LENGTH = 400     # Skip very long technical strings
DEDUP_THRESHOLD = 0.92        # Similarity score above which we treat as duplicate

CLS_KEY = "classification"
LIN_KEY = "lineage"

# ── Signal patterns (ordered: highest precision first) ────────────────────────

# Intent — stated plans, roadmap items, future work
_INTENT = [
    re.compile(r"\bI (?:plan|intend|aim) to\b", re.IGNORECASE),
    re.compile(r"\bI(?:'m| am) planning to\b", re.IGNORECASE),
    re.compile(r"\beventually I\b", re.IGNORECASE),
    re.compile(r"\bI had a plan (?:to|for)\b", re.IGNORECASE),
    re.compile(r"\bI(?:'ve| have) been (?:thinking about|considering) (?:building|implementing|adding|creating)\b", re.IGNORECASE),
    re.compile(r"\bdown the road I\b", re.IGNORECASE),
    re.compile(r"\bI(?:'d| would) like to (?:implement|build|add|create|deploy|integrate)\b", re.IGNORECASE),
]

# Preference — stated likes, dislikes, working preferences
_PREFERENCE = [
    re.compile(r"\bI prefer\b", re.IGNORECASE),
    re.compile(r"\bI(?:'d| would) (?:rather|prefer)\b", re.IGNORECASE),
    re.compile(r"\bI always\b", re.IGNORECASE),
    re.compile(r"\bI never\b", re.IGNORECASE),
    re.compile(r"\bI (?:like|don't like|dislike|hate|love) (?:the way|how|when|that approach|this approach)\b", re.IGNORECASE),
]

# Decision — confirmed choices, policy changes, going-forward statements
_DECISION = [
    re.compile(r"\b(?:I|we) decided\b", re.IGNORECASE),
    re.compile(r"\bfrom now on\b", re.IGNORECASE),
    re.compile(r"\bgoing forward\b", re.IGNORECASE),
    re.compile(r"\b(?:I'm|we're|I am|we are) (?:switching|moving) (?:to|away from)\b", re.IGNORECASE),
    re.compile(r"\bwe(?:'re| are) going with\b", re.IGNORECASE),
    re.compile(r"\bI(?:'m| am) going with\b", re.IGNORECASE),
]

# Observation — things Jake noticed about the system, discoveries, realizations
_OBSERVATION = [
    re.compile(r"\bI noticed\b", re.IGNORECASE),
    re.compile(r"\bI realized\b", re.IGNORECASE),
    re.compile(r"\bI found (?:that|out)\b", re.IGNORECASE),
    re.compile(r"\bturns? out\b", re.IGNORECASE),
    re.compile(r"\bthis explains\b", re.IGNORECASE),
    re.compile(r"\bthat explains\b", re.IGNORECASE),
    re.compile(r"\bI think this is\b", re.IGNORECASE),
]

# Framing — ownership, attribution, project identity signals
_FRAMING = [
    re.compile(r"\bI (?:view|see|consider) (?:it|this|the repo|the project)\b", re.IGNORECASE),
    re.compile(r"\bI don't view (?:it|this|the)\b", re.IGNORECASE),
    re.compile(r"\bmy (?:heart rate|gut|intuition|experience|background)\b", re.IGNORECASE),
    re.compile(r"\bI view it as\b", re.IGNORECASE),
    re.compile(r"\bI see it as\b", re.IGNORECASE),
]

# (pattern_list, category_name, utility)
_ALL_SIGNAL_GROUPS = [
    (_INTENT,       "intent",       "load_bearing"),
    (_PREFERENCE,   "preference",   "load_bearing"),
    (_DECISION,     "decision",     "load_bearing"),
    (_OBSERVATION,  "observation",  "tactical"),
    (_FRAMING,      "framing",      "tactical"),
]

# Sentences matching these are skipped — too noisy or clearly directed at the agent
_SKIP_IF = [
    re.compile(r"\?"),                            # Questions
    re.compile(r"^(?:please|can you|could you|would you|tell me|show me|help me|what|how|why|when|where|who)\b", re.IGNORECASE),
    re.compile(r"\bI want (?:to (?:understand|know|see|check|look|find|confirm|make sure|verify))\b", re.IGNORECASE),
]

# Sentence splitter — splits on . ! ? followed by whitespace
_SENT_RE = re.compile(r'(?<=[.!?])\s+')


class ConversationalInsightCapture(Extension):
    """Deterministic conversational insight capture — no LLM calls."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            if _ms is not None:
                # R2 rule 1 (A19): in an idle cycle or a subordinate agent the "user" is the
                # daemon's activation prompt or a delegating agent, not Jake. These patterns
                # are tuned to Jake's own speech, so there is nothing here to capture.
                if _ms.is_restricted(self.agent):
                    return
                # A19 (a): the message that started this monologue. The last non-AI history
                # entry, which this used to read, is often a tool result.
                user_msg = _ms.user_message_text(loop_data)
            else:
                user_msg = self._get_recent_user_message()
            if not user_msg or len(user_msg.strip()) < 20:
                return

            sentences = _split_sentences(user_msg)
            if not sentences:
                return

            hits = []
            for sentence in sentences:
                category, utility = _classify(sentence)
                if category:
                    hits.append((sentence.strip(), category, utility))

            if not hits:
                return

            db = await Memory.get(self.agent)
            if not db:
                return

            bst_domain = self._bst_domain()
            stored = 0

            for text, category, utility in hits:
                if await _is_duplicate(db, text):
                    continue

                # R2: derived like every other writer's; for a sentence taken from the user's
                # own message in an interactive context this is user_asserted / confirmed.
                # GT-2a (2026-09-25): the derivation marker, when the loaded helper provides it.
                # The helper-missing fallback below is the old hardcoded label, so it carries no
                # marker, and the recall frame renders it as legacy.
                source_rule = None
                _derive = getattr(_ms, "derive_source_rule", None) if _ms is not None else None
                if _derive is not None:
                    source, source_rule = _derive(self.agent, text, user_msg=user_msg)
                else:
                    source = (_ms.derive_source(self.agent, text, user_msg=user_msg)
                              if _ms is not None else "user_asserted")
                validity = _ms.validity_for(source) if _ms is not None else "confirmed"
                metadata = {
                    "area": Memory.Area.FRAGMENTS.value,
                    "signal_type": f"conversational_{category}",
                    # R3: when the statement was captured (helpers/memory_temporal.py).
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                    CLS_KEY: {
                        "validity": validity,
                        "relevance": "active",
                        "utility": utility,
                        "source": source,
                        **({"source_rule": source_rule} if source_rule else {}),
                    },
                    LIN_KEY: {
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "created_by_role": None,
                        "bst_domain": bst_domain,
                        "classified_at_cycle": 0,
                        "supersedes": None,
                        "superseded_by": None,
                        "access_count": 0,
                        "last_accessed": None,
                        "created_by": "insight_capture",
                    },
                }

                await db.insert_text(text=text, metadata=metadata)
                stored += 1

            if stored > 0:
                self.agent.context.log.log(
                    type="info",
                    content=f"[INSIGHT] Captured {stored} conversational insight(s) from user message",
                )

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[INSIGHT] Error (passthrough): {e}",
                )
            except Exception:
                pass

    def _get_recent_user_message(self) -> str:
        try:
            outputs = self.agent.history.output()
            for msg in reversed(outputs):
                if not msg.get("ai", True):
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        return " ".join(
                            p.get("text", "") if isinstance(p, dict) else str(p)
                            for p in content
                        )
                    return str(content) if content else ""
        except Exception:
            pass
        return ""

    def _bst_domain(self) -> str:
        try:
            store = getattr(self.agent, "_bst_store", {})
            belief = store.get("__bst_belief_state__", {})
            return belief.get("domain", "")
        except Exception:
            return ""


# ── Module-level helpers ──────────────────────────────────────────────────────

def _split_sentences(text: str) -> list[str]:
    raw = _SENT_RE.split(text.strip())
    result = []
    for s in raw:
        s = s.strip()
        if not s:
            continue
        if len(s) > MAX_SENTENCE_LENGTH:
            continue
        if len(s.split()) < MIN_SENTENCE_WORDS:
            continue
        result.append(s)
    return result


def _classify(sentence: str) -> tuple[str | None, str | None]:
    """Return (category, utility) or (None, None) if no signal or should be skipped."""
    for pattern in _SKIP_IF:
        if pattern.search(sentence):
            return None, None

    for pattern_group, category, utility in _ALL_SIGNAL_GROUPS:
        for pattern in pattern_group:
            if pattern.search(sentence):
                return category, utility

    return None, None


async def _is_duplicate(db, text: str) -> bool:
    try:
        results = await db.search_similarity_threshold(
            query=text,
            limit=1,
            threshold=DEDUP_THRESHOLD,
        )
        return len(results) > 0
    except Exception:
        return False
