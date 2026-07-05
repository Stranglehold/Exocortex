"""
Chat Retention — keep run_ui's loaded chat set small so the UI stays fast.
=========================================================================
Problem it solves (2026-07-05): A0's load_tmp_chats() loads EVERY chat folder
into memory at startup with no cap. Idle cycles create a fresh context each run,
so the set grows unbounded (1000+), bloating run_ui and making every /poll
snapshot + sidebar render heavy → sluggish UI + "reconnected" churn.

Policy (non-destructive) — a simple rolling window:
  KEEP    - pinned contexts (always) + currently-running + the newest N unpinned.
  ARCHIVE - unpinned, not-running, beyond the newest N.
            "Archive" = MOVE the chat dir to /a0/usr/chats_archive/ and evict it
            from run_ui memory (AgentContext.remove). Nothing is deleted; the dir
            is recoverable and RAG-able later.

An optional age rule (max_age_days > 0) can also archive stale unpinned chats,
but it's OFF by default — the window is the whole policy. The newest N are kept
regardless of how long ago they were touched (a quiet week never purges them).

A context counts as pinned if EITHER:
  - context.data["pinned"] is truthy  (set by the pin endpoint / future UI toggle), OR
  - its name starts with the 📌 marker (pin via A0's existing rename — no UI build).

The cycle's durable value (canvas ledger, wiki pages, memories) is persisted
elsewhere; the chat trajectory is the disposable 99%.
"""

import os
import shutil
import time

from agent import AgentContext, AgentContextType

CHATS = "/a0/usr/chats"
ARCHIVE = "/a0/usr/chats_archive"
PIN_MARKER = "\U0001F4CC"  # 📌 — name-prefix pin, works via A0's existing rename UI


def is_pinned(ctx) -> bool:
    try:
        if ctx.get_data("pinned"):
            return True
        name = ctx.name or ""
        return name.strip().startswith(PIN_MARKER)
    except Exception:
        return False


def _last_ts(ctx) -> float:
    try:
        return ctx.last_message.timestamp() if ctx.last_message else 0.0
    except Exception:
        return 0.0


def enforce_retention(keep_recent: int = 25, max_age_days: int = 0,
                      dry_run: bool = False) -> dict:
    """Archive unpinned chats beyond the newest `keep_recent`. Returns a summary.
    `max_age_days` is an optional extra rule (0 = off): also archive unpinned
    chats untouched longer than that many days."""
    os.makedirs(ARCHIVE, exist_ok=True)
    now = time.time()
    max_age = max_age_days * 86400  # 0 → age rule disabled

    ctxs = [c for c in AgentContext.all()
            if getattr(c, "type", None) != AgentContextType.BACKGROUND]

    # Archive candidates: unpinned AND not currently running.
    cand = [c for c in ctxs if not is_pinned(c) and not c.is_running()]
    cand.sort(key=_last_ts, reverse=True)  # newest first

    archived, errors = [], 0
    for i, c in enumerate(cand):
        ts = _last_ts(c)
        too_old = bool(max_age) and bool(ts) and (now - ts) > max_age
        beyond_window = i >= keep_recent
        if not (beyond_window or too_old):
            continue
        if dry_run:
            archived.append(c.id)
            continue
        try:
            src = os.path.join(CHATS, c.id)
            dst = os.path.join(ARCHIVE, c.id)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst, ignore_errors=True)
                shutil.move(src, dst)
            AgentContext.remove(c.id)  # evict from run_ui memory (dir already moved)
            archived.append(c.id)
        except Exception as e:
            errors += 1
            print(f"[CHAT-RETENTION] archive error {c.id}: {e}", flush=True)

    return {
        "loaded_before": len(ctxs),
        "archived": len(archived),
        "kept": len(ctxs) - len(archived),
        "pinned": len([c for c in ctxs if is_pinned(c)]),
        "running": len([c for c in ctxs if c.is_running()]),
        "errors": errors,
        "ids": archived,
    }


def set_pinned(ctx_id: str, pinned: bool) -> bool:
    """Set the persistent pinned flag on a loaded context."""
    c = AgentContext.get(ctx_id)
    if not c:
        return False
    c.set_data("pinned", bool(pinned))
    return True
