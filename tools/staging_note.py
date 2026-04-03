"""
Staging Note — Intermediate Memory Write Tool
==============================================
Writes an observation to the staging tier (/a0/usr/Exocortex/staging.jsonl).

The staging tier is the intermediate memory layer between working memory
(entity extraction, 8-turn decay) and committed long-term FAISS memory.
Use it to record things worth remembering across sessions without committing
them immediately to long-term storage.

Categories:
  observation  — something noticed about processing, task patterns, or
                 prediction errors. Reviewed by sleep consolidation.
  canary       — sub-threshold signal for the supervisor. Accumulates toward
                 a soft steering flag via CUSUM. Use when something feels
                 wrong but hasn't crossed a threshold yet.
  relational   — something that defines or advances the operator-agent
                 relationship. Never auto-archived. Injected at session start.
  intention    — deferred decision or flagged follow-up. Injected at session
                 start as high-priority items.

Both `text` and `why` are required. `why` enforces write-time encoding depth
— the dominant failure mode in cognitive offloading is shallow capture.
State what the observation is AND why it matters / what should happen with it.
"""

import json
import os
import uuid
from datetime import datetime, timezone

from agent import LoopData
from helpers.tool import Tool, Response

STAGING_PATH = "/a0/usr/Exocortex/staging.jsonl"
VALID_CATEGORIES = {"observation", "canary", "relational", "intention"}

_IMPORTANCE_HIGH = [
    "failed", "broke", "unexpected", "correction", "wrong", "error",
    "never", "always", "critical", "breakthrough", "realized", "discovered",
]
_IMPORTANCE_MEDIUM = [
    "noticed", "pattern", "operator", "relationship", "session",
    "remember", "important", "learned", "repeatedly",
]


def _compute_importance(category: str, text: str, why: str) -> float:
    score = 0.2

    boosts = {"relational": 0.3, "canary": 0.2, "intention": 0.1, "observation": 0.0}
    score += boosts.get(category, 0.0)

    combined = (text + " " + why).lower()

    high_count = sum(1 for kw in _IMPORTANCE_HIGH if kw in combined)
    score += min(0.3, high_count * 0.1)

    medium_count = sum(1 for kw in _IMPORTANCE_MEDIUM if kw in combined)
    score += min(0.15, medium_count * 0.05)

    return min(1.0, round(score, 2))


class StagingNote(Tool):
    async def execute(self, category: str = "observation", text: str = "",
                      why: str = "", **kwargs) -> Response:
        try:
            if category not in VALID_CATEGORIES:
                return Response(
                    message=(
                        f"Invalid category '{category}'. "
                        f"Use: observation, canary, relational, intention"
                    ),
                    break_loop=False,
                )
            if not text.strip():
                return Response(
                    message="text is required — state what you observed",
                    break_loop=False,
                )
            if not why.strip():
                return Response(
                    message=(
                        "why is required — state why this matters "
                        "and what should happen with it"
                    ),
                    break_loop=False,
                )

            session_id = getattr(
                getattr(self.agent, "context", None), "id", "unknown"
            )
            turn = getattr(self.agent, "_supervisor_state", {}).get("turn", 0)
            importance = _compute_importance(category, text, why)

            entry = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
                "session_age_at_write": turn,
                "category": category,
                "text": text.strip(),
                "why": why.strip(),
                "importance": importance,
                "status": "active",
                "supersedes": [],
                "consolidation_score": 0.0,
                "reactivation_count": 0,
                "last_reactivated": None,
                "promoted_to": None,
            }

            os.makedirs(os.path.dirname(STAGING_PATH), exist_ok=True)
            with open(STAGING_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

            self.agent.context.log.log(
                type="info",
                content=(
                    f"[STAGING] {category} written "
                    f"(importance={importance}): {text[:80]}"
                ),
            )

            return Response(
                message=(
                    f"Staged [{category}] importance={importance}. "
                    f"ID: {entry['id'][:8]}"
                ),
                break_loop=False,
            )

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[STAGING] Write failed (non-critical): {e}",
                )
            except Exception:
                pass
            return Response(
                message=f"Staging write failed (non-critical): {e}",
                break_loop=False,
            )
