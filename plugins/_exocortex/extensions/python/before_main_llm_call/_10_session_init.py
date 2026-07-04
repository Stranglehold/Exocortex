"""
Session Init — Staging Tier Reader
====================================
Hook: before_main_llm_call (priority _10, fires before BST at _11)

Reads staging.jsonl on the FIRST TURN of each session and injects active
entries into the user message context. Runs exactly once per session via
the _session_init_done flag.

Injection priority order:
  1. intention  — deferred decisions; always inject (must surface every session)
  2. relational — relationship anchors; always inject
  3. observation — top-N by reactivation-weighted importance (importance >= 0.4)
  4. canary     — summary count of active sub-threshold signals

This is the structural equivalent of the GTD trusted inbox: the review must
be automatic, not behavioral, or the Zeigarnik effect persists (Masicampo &
Baumeister 2011 — open cognitive loops occupy working memory continuously
until a concrete plan exists for handling them).

The staging.jsonl path mirrors the WAL principle (Gray & Reuter 1992):
staging is the authoritative log; long-term memory is the secondary
materialization. Session init is the read head on that log.
"""

import json
import os

from agent import LoopData
from helpers.extension import Extension

STAGING_PATH = "/a0/usr/Exocortex/staging.jsonl"
SESSION_INIT_FLAG = "_session_init_done"
MAX_OBSERVATION_INJECT = 3
OBSERVATION_MIN_IMPORTANCE = 0.4


def _load_active_staging() -> list[dict]:
    if not os.path.exists(STAGING_PATH):
        return []
    entries = []
    try:
        with open(STAGING_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if e.get("status") == "active":
                        entries.append(e)
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    return entries


def _reactivation_score(entry: dict) -> float:
    """Importance boosted by reactivation history."""
    base = entry.get("importance", 0.2)
    r = entry.get("reactivation_count", 0)
    return base * (1.0 + 0.2 * min(r, 5))


def _increment_reactivation(surfaced: list[dict]) -> int:
    """Break B fix (DEC-042): mark surfaced observations as reactivated.

    sleep_consolidation Phase 0 promotes an observation only when
    reactivation_count >= 1, but nothing in the system ever incremented it —
    so the staging -> procedural-memory promotion path was structurally
    unreachable (0 promotions across ~780 cycles, both containers). Surfacing
    an observation into context IS a reactivation: it was recalled and reused.
    So we bump the count here and persist it, which makes the gate satisfiable.

    Read-modify-write keyed on (created, text) — observations carry no stable
    id. LF newlines (Windows default CRLF would corrupt downstream readers).
    Best-effort: any failure is swallowed so session init never breaks.
    """
    if not surfaced or not os.path.exists(STAGING_PATH):
        return 0
    keys = {(e.get("created"), e.get("text")) for e in surfaced}
    bumped = 0
    lines_out: list[str] = []
    try:
        with open(STAGING_PATH, "r", encoding="utf-8") as f:
            raw = f.readlines()
        for line in raw:
            s = line.strip()
            if not s:
                continue
            try:
                e = json.loads(s)
            except json.JSONDecodeError:
                lines_out.append(s)
                continue
            if (e.get("category") == "observation"
                    and (e.get("created"), e.get("text")) in keys):
                e["reactivation_count"] = e.get("reactivation_count", 0) + 1
                bumped += 1
                lines_out.append(json.dumps(e))
            else:
                lines_out.append(s)
        if bumped:
            with open(STAGING_PATH, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(lines_out) + "\n")
    except Exception:
        return 0
    return bumped


def _get_last_user_message(history: list) -> dict | None:
    for msg in reversed(history):
        if isinstance(msg, dict) and not msg.get("ai", True):
            return msg
    return None


class SessionInit(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            # Run exactly once per session
            if getattr(self.agent, SESSION_INIT_FLAG, False):
                return
            setattr(self.agent, SESSION_INIT_FLAG, True)

            active = _load_active_staging()
            if not active:
                return

            intentions = [e for e in active if e.get("category") == "intention"]
            relationals = [e for e in active if e.get("category") == "relational"]
            observations = sorted(
                [
                    e for e in active
                    if e.get("category") == "observation"
                    and e.get("importance", 0) >= OBSERVATION_MIN_IMPORTANCE
                ],
                key=_reactivation_score,
                reverse=True,
            )[:MAX_OBSERVATION_INJECT]
            canaries = [e for e in active if e.get("category") == "canary"]

            if not any([intentions, relationals, observations, canaries]):
                return

            lines = ["[STAGING — session continuity]"]

            if intentions:
                lines.append(
                    f"INTENTIONS: {len(intentions)} deferred decision(s) from prior sessions"
                )
                for e in intentions:
                    lines.append(f"  • {e['text']} (why: {e['why']})")

            if relationals:
                lines.append(
                    f"RELATIONAL: {len(relationals)} relationship anchor(s)"
                )
                for e in relationals:
                    lines.append(f"  • {e['text']}")

            if observations:
                lines.append(
                    f"OBSERVATIONS: {len(observations)} staged observation(s)"
                )
                for e in observations:
                    lines.append(f"  • {e['text']}")

            if canaries:
                lines.append(
                    f"CANARY: {len(canaries)} sub-threshold signal(s) pending"
                    f" — review before tool use"
                )
                for e in canaries:
                    lines.append(f"  • {e['text']}")

            lines.append("[/STAGING]")
            block = "\n".join(lines)

            user_msg = _get_last_user_message(loop_data.history_output)
            if user_msg:
                existing = user_msg.get("content", "")
                user_msg["content"] = block + "\n\n" + str(existing)

            # Break B (DEC-042): surfacing an observation IS a reactivation —
            # bump reactivation_count so it can clear the Phase 0 promotion gate.
            bumped = _increment_reactivation(observations)

            self.agent.context.log.log(
                type="util",
                content=(
                    f"[SESSION-INIT] Injected staging: "
                    f"{len(intentions)} intentions, "
                    f"{len(relationals)} relational, "
                    f"{len(observations)} observations "
                    f"({bumped} reactivation-bumped), "
                    f"{len(canaries)} canaries"
                ),
            )

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[SESSION-INIT] Failed (passthrough): {e}",
                )
            except Exception:
                pass
