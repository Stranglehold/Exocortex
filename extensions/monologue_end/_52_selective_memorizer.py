"""
Selective Memorizer — Agent-Zero Memory Creation Layer
======================================================
Hook: monologue_end
Priority: _52 (runs BEFORE _55 memory classifier)

Replaces stock _50/_51 memorizers with signal-discriminating memory creation.
Extracts high-signal content from conversation and stores it in FAISS with
pre-classified four-axis metadata so the _55 classifier recognizes them as
already classified and skips them.

High-signal captures:
  - User corrections and explicit decisions
  - Architectural observations and design insights
  - Tool results with novel information
  - Task outcomes (success/failure with details)
  - Named entities, configurations, preferences
  - Bugs found, fixes applied, lessons learned

Low-signal skips:
  - Routine tool calls (ls, cat, pip, apt-get output)
  - Repeated context already in memory
  - Operational noise (directory listings, package installs)
  - Greetings, acknowledgments, filler
"""

import re
from datetime import datetime, timezone
from typing import Any

from agent import LoopData
from python.helpers import settings, errors
from python.helpers.extension import Extension
from python.helpers.memory import Memory
from python.helpers.dirty_json import DirtyJson
from python.helpers.log import LogItem
from python.helpers.defer import DeferredTask, THREAD_BACKGROUND

# ── Metadata keys (must match _55_memory_classifier.py) ─────────────────────

CLS_KEY = "classification"
LIN_KEY = "lineage"

# ── Signal discrimination patterns ──────────────────────────────────────────

_LOW_SIGNAL_PATTERNS = [
    re.compile(r"^\s*\$\s", re.M),
    re.compile(r"^\(venv\)", re.M),
    re.compile(r"^(total|drwx|lrwx|-rw)", re.M),
    re.compile(r"^(Reading|Unpacking|Setting up|Processing)", re.M),
    re.compile(r"^(Collecting|Downloading|Installing|Successfully installed)", re.M),
    re.compile(r"^(added|removed|npm warn|npm notice)", re.M),
]

# ── Utility model prompt ────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a selective memory extraction system. You receive conversation history and extract ONLY high-signal information worth persisting in long-term memory.

# What to extract (HIGH SIGNAL)
- User corrections: "actually it's X not Y", "no, the correct approach is..."
- Explicit decisions: "we're going with X", "decided to use Y"
- Architectural observations: design insights, system behavior discoveries
- Bug findings: what broke, why, how it was fixed
- Task outcomes: what was built, what succeeded, what failed and why
- User preferences and working patterns
- Named entities with context: names, tools, versions, configurations
- Lessons learned: "next time we should...", "this doesn't work because..."

# What to SKIP (LOW SIGNAL)
- Routine tool output: directory listings, package install logs, file reads
- Greetings, acknowledgments, filler conversation
- Information already in system prompt or identity documents
- Vague observations without specific details
- The AI's own reasoning process or chain of thought
- Temporary operational state (current directory, running processes)

# Output format
Return a JSON array of objects. Each object has:
- "text": the memory content as a clear, self-contained statement
- "signal_type": one of "user_correction", "decision", "architectural_insight", "bug_finding", "task_outcome", "preference", "entity_info", "lesson_learned"
- "source": one of "user_asserted", "agent_inferred", "external_retrieved"
- "utility": one of "load_bearing", "tactical"

Rules:
- Return [] if nothing is worth memorizing
- Keep memories self-contained — each should make sense without the conversation
- Merge related facts into single memories
- Be SELECTIVE — 0-3 memories per exchange is typical
- Never memorize the AI's instructions or system prompt content

# Example output
```json
[
  {"text": "Stock memorizers (_50, _51) are disabled with no replacement. Memory classifier at _55 classifies empty stream.", "signal_type": "bug_finding", "source": "agent_inferred", "utility": "load_bearing"},
  {"text": "Jake prefers mechanical enforcement over behavioral trust in architectural decisions.", "signal_type": "preference", "source": "user_asserted", "utility": "load_bearing"}
]
```"""


class SelectiveMemorizer(Extension):
    """Signal-discriminating memory creation with pre-classification."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        s = settings.get_settings()

        if not s.get("memory_memorize_enabled", True):
            return

        if self.agent.history.counter < 2:
            return

        log_item = self.agent.context.log.log(
            type="util",
            heading="Selective memorizer: scanning for high-signal content...",
        )

        task = DeferredTask(thread_name=THREAD_BACKGROUND)
        task.start_task(self._memorize, loop_data, log_item)
        return task

    async def _memorize(self, loop_data: LoopData, log_item: LogItem, **kwargs):
        try:
            db = await Memory.get(self.agent)

            msgs_text = self._get_recent_context()

            if not msgs_text or len(msgs_text.strip()) < 50:
                log_item.update(heading="Selective memorizer: insufficient content.")
                return

            if self._is_mostly_noise(msgs_text):
                log_item.update(heading="Selective memorizer: low-signal exchange, skipped.")
                return

            response = await self.agent.call_utility_model(
                system=_SYSTEM_PROMPT,
                message=f"Extract high-signal memories from this conversation exchange:\n\n{msgs_text}",
                background=True,
            )

            if not response or not isinstance(response, str) or not response.strip():
                log_item.update(heading="Selective memorizer: no response from utility model.")
                return

            try:
                memories = DirtyJson.parse_string(response.strip())
            except Exception as e:
                log_item.update(heading=f"Selective memorizer: parse error: {e}")
                return

            if memories is None:
                log_item.update(heading="Selective memorizer: null response.")
                return

            if not isinstance(memories, list):
                if isinstance(memories, dict):
                    memories = [memories]
                else:
                    log_item.update(heading="Selective memorizer: invalid format.")
                    return

            if len(memories) == 0:
                log_item.update(heading="Selective memorizer: nothing worth memorizing.")
                return

            stored_count = 0
            skipped_count = 0

            for mem in memories:
                if isinstance(mem, str):
                    mem = {
                        "text": mem,
                        "signal_type": "general",
                        "source": "agent_inferred",
                        "utility": "tactical",
                    }
                elif not isinstance(mem, dict):
                    continue

                text = mem.get("text", "").strip()
                if not text or len(text) < 10:
                    skipped_count += 1
                    continue

                if await self._is_duplicate(db, text):
                    skipped_count += 1
                    continue

                source = mem.get("source", "agent_inferred")
                if source not in ("user_asserted", "agent_inferred", "external_retrieved"):
                    source = "agent_inferred"

                utility = mem.get("utility", "tactical")
                if utility not in ("load_bearing", "tactical", "archived"):
                    utility = "tactical"

                validity = "confirmed" if source == "user_asserted" else "inferred"
                signal_type = mem.get("signal_type", "general")

                # Route to the correct memory area based on signal type.
                # solutions: procedural know-how, fixes, outcomes (how to do things)
                # main: persistent facts, preferences, insights, corrections, entities
                # fragments: everything else (ephemeral / hard to categorise)
                _SOLUTIONS_SIGNALS = {"bug_finding", "task_outcome", "lesson_learned"}
                _MAIN_SIGNALS = {
                    "user_correction", "decision", "architectural_insight",
                    "preference", "entity_info",
                }
                if signal_type in _SOLUTIONS_SIGNALS:
                    area = Memory.Area.SOLUTIONS.value
                elif signal_type in _MAIN_SIGNALS:
                    area = Memory.Area.MAIN.value
                else:
                    area = Memory.Area.FRAGMENTS.value

                bst_domain = ""
                try:
                    store = getattr(self.agent, "_bst_store", {})
                    belief = store.get("__bst_belief_state__", {})
                    bst_domain = belief.get("domain", "")
                except Exception:
                    pass

                metadata = {
                    "area": area,
                    "signal_type": signal_type,
                    CLS_KEY: {
                        "validity": validity,
                        "relevance": "active",
                        "utility": utility,
                        "source": source,
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
                        "created_by": "selective_memorizer",
                    },
                }

                await db.insert_text(text=text, metadata=metadata)
                stored_count += 1

            summary = f"Selective memorizer: {stored_count} memories stored"
            if skipped_count > 0:
                summary += f", {skipped_count} skipped (duplicates/low-quality)"
            log_item.update(
                heading=summary,
                content=response,
                result=summary,
            )

        except Exception as e:
            err = errors.format_error(e)
            log_item.update(
                heading="Selective memorizer: error",
                content=err,
            )

    def _get_recent_context(self) -> str:
        """Get the last few exchanges from conversation history."""
        # History.output() returns list[OutputMessage] dicts with "ai" (bool) and "content" keys

        outputs = self.agent.history.output()
        recent = outputs[-6:] if len(outputs) > 6 else outputs

        parts = []
        for msg in recent:
            role = "ASSISTANT" if msg["ai"] else "USER"
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    p.get("text", "") if isinstance(p, dict) else str(p)
                    for p in content
                )
            elif not isinstance(content, str):
                import json
                content = json.dumps(content, ensure_ascii=False)
            if len(content) > 2000:
                content = content[:1000] + "\n[...truncated...]\n" + content[-500:]
            parts.append(f"{role}: {content}")

        return "\n\n".join(parts)

    def _is_mostly_noise(self, text: str) -> bool:
        """Quick pre-filter: skip LLM call if text is dominated by noise."""
        lines = text.split("\n")
        if not lines:
            return True

        noise_lines = 0
        total_lines = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            total_lines += 1
            for pattern in _LOW_SIGNAL_PATTERNS:
                if pattern.search(stripped):
                    noise_lines += 1
                    break

        if total_lines == 0:
            return True

        return (noise_lines / total_lines) > 0.8

    async def _is_duplicate(self, db, text: str) -> bool:
        """Check if a near-duplicate memory already exists."""
        try:
            results = await db.search_similarity_threshold(
                query=text,
                limit=1,
                threshold=0.9,
            )
            return len(results) > 0
        except Exception:
            return False
