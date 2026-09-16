#!/usr/bin/env python3
"""export_conversations.py — Aporia's conversations, as text, for the memory index (Fable, 2026-09-14, Jake's word).

WHY: her chat logs (1,475 `chat.json` files, 1.1 GB, 2026-09-14) are 99.5 % machinery by bytes — the injected context
stack on every turn, tool and code output, info lines — and 0.5 % conversation: the `user` entries (Jake) and the
`response` entries (Aporia). Nothing exported that conversation to the host, so neither she nor we could search it.
This writes ONLY the conversation, one Markdown file per chat, as dated exchanges, into an export directory the
memory server walks; `search_by_type(type="transcript")` is then the recall call, hers and ours.

HOW: one read-only pass INSIDE the container (`docker exec -i ... python3 -` with the reader below on stdin) streams
one JSON line per chat: id, name, created, last message time, and the exchanges. The host side scrubs secrets, writes
files, and keeps a content hash per chat so an unchanged chat is never rewritten (the sync's tree signature must not
move for nothing). Stage-verify-swap like sync_agent_exports.py: files land in a staging dir and are moved into place
only after the whole pass succeeded. Daemon probe first (docker_probe.py): Docker off -> DEFERRED, exit 3.

SCOPE, v1 (Jake's decisions, 2026-09-14 study §3): chats with at least one REAL human turn; the whole history; `user`
and `response` content only. CORRECTION from the first dry run (2026-09-14): the idle engine injects its cycle prompt
as a `user` entry, so "has a user turn" counted 880 engine prompts as Jake. Real Jake turns: 656 in 294 chats (of
1,475), about 1.4 M characters with her replies. Engine-injected turns, her replies to them, and the canned
"Hello! I'm Agent Zero" greeting are excluded by default; `--include-engine-turns` keeps the cycle prompts and replies
(they are already in the journal and field reports, and 1,000 copies of one prompt would be the corpus).

USAGE
    python scripts/export_conversations.py --dry-run --out <scratch dir>   # write to a scratch dir, print numbers
    python scripts/export_conversations.py                                 # write to agent-exports/v2/conversations/
    --container agent-zero-v2   --min-user-turns 1   --include-agent-only
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from docker_probe import daemon_reachable, EXIT_DEFERRED   # beside this file in scripts/

DEFAULT_OUT = r"D:\Vibecode\Agent-Zero\Exocortex\agent-exports\v2\conversations"
CONTAINER = "agent-zero-v2"
_ENV = dict(os.environ, MSYS_NO_PATHCONV="1")

# The in-container reader. Read-only: opens chat.json files, prints JSON lines. Nothing else.
READER = r'''
import json, os, sys
roots = ["/a0/usr/chats", "/a0/usr/chats_archive"]
for root in roots:
    if not os.path.isdir(root):
        continue
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d, "chat.json")
        if not os.path.isfile(p):
            continue
        try:
            c = json.load(open(p, encoding="utf-8", errors="replace"))
        except Exception as e:
            print(json.dumps({"id": d, "error": type(e).__name__})); continue
        logs = (c.get("log") or {}).get("logs") or []
        ex = []
        for m in logs:
            t = m.get("type")
            if t in ("user", "response"):
                ex.append({"t": t, "ts": m.get("timestamp"), "c": str(m.get("content") or "")})
        print(json.dumps({"id": c.get("id") or d, "dir": d, "root": os.path.basename(root), "name": c.get("name") or "",
                          "created": c.get("created_at"), "last": c.get("last_message"), "ex": ex}))
'''

# Secrets scrub: the shapes that get pasted into chats. Reported by count; a chat the scrub touched is still exported,
# with the value replaced, never the raw value.
SECRET_RES = [
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"),
    re.compile(r"\b(?:api[_-]?key|token|password|passwd|secret)\s*[:=]\s*['\"]?([^\s'\"]{8,})", re.I),
    re.compile(r"\b\d{6,}:[A-Za-z0-9_\-]{30,}\b"),          # telegram bot token shape
]


def scrub(text):
    n = 0
    for rx in SECRET_RES:
        text, k = rx.subn(lambda m: (m.group(0)[: m.start(1) - m.start(0)] + "[REDACTED]") if m.lastindex else "[REDACTED]", text)
        n += k
    return text, n


ENGINE_MARKERS = ("IDLE-TIME CYCLE", "autonomous work cycle", "Jake is away")
GREETING = "**Hello! 👋**, I'm **Agent Zero**"


def _is_engine(user_text):
    """An idle-cycle activation prompt injected as a `user` entry (measured 2026-09-14: 880 of 1,536 user turns)."""
    head = user_text[:400]
    return any(k in head for k in ENGINE_MARKERS)


def select_exchanges(ex, include_engine=False):
    """Keep real Jake turns and her replies to them; drop engine prompts, replies to engine prompts, and the greeting.
    Returns (kept, n_real_user, n_engine_user)."""
    kept, n_real, n_engine = [], 0, 0
    last_user = None          # "real" | "engine" | None
    for e in ex:
        if e["t"] == "user":
            if _is_engine(e["c"]):
                n_engine += 1; last_user = "engine"
                if include_engine: kept.append(dict(e, who="engine"))
            else:
                n_real += 1; last_user = "real"; kept.append(dict(e, who="jake"))
        else:
            if e["c"].lstrip().startswith(GREETING):
                continue
            if last_user == "real" or (last_user == "engine" and include_engine):
                kept.append(dict(e, who="aporia"))
    return kept, n_real, n_engine


HOLDOUT_CONFIG = r"D:\Vibecode\Agent-Zero\Exocortex\harness\holdout\config.json"


def _shingles(s, n=8):
    w = re.sub(r"\s+", " ", s).strip().lower().split()
    return {" ".join(w[i:i + n]) for i in range(0, max(0, len(w) - n + 1))}


def _strings(obj, out):
    if isinstance(obj, dict):
        for v in obj.values(): _strings(v, out)
    elif isinstance(obj, list):
        for v in obj: _strings(v, out)
    elif isinstance(obj, str) and len(obj.split()) >= 8:
        out.append(obj)


def seal_check(staging_dir):
    """{'hits': [chat files sharing an 8-word shingle with a holdout task], 'control_ok': bool}, or None if there is
    no sealed config on this host (then there is nothing to leak). Reads the sealed config; never prints its text."""
    if not os.path.isfile(HOLDOUT_CONFIG):
        return None
    out = []
    try:
        _strings(json.load(open(HOLDOUT_CONFIG, encoding="utf-8")), out)
    except Exception as e:
        return {"hits": ["<holdout config unreadable: %s>" % type(e).__name__], "control_ok": False}
    sealed = set()
    for t in out:
        sealed |= _shingles(t)
    hits = []
    for f in sorted(os.listdir(staging_dir)):
        if f.endswith(".md") and (_shingles(open(os.path.join(staging_dir, f), encoding="utf-8").read()) & sealed):
            hits.append(f)
    probe = next(iter(sealed)) if sealed else ""
    control_ok = bool(probe) and bool(_shingles("x y z " + probe + " q") & sealed)
    print(f"  seal check: {len(hits)} of {sum(1 for f in os.listdir(staging_dir) if f.endswith('.md'))} staged chats share holdout task text (must be 0); positive control {'ok' if control_ok else 'FAILED'}")
    return {"hits": hits, "control_ok": control_ok}


def _ts(v):
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        if isinstance(v, str) and v:
            s = v.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    return None


def render(chat, kept, n_real, n_engine):
    created = _ts(chat.get("created")) or (_ts(kept[0]["ts"]) if kept else None)
    last = _ts(chat.get("last")) or (_ts(kept[-1]["ts"]) if kept else None)
    if created: created = created.astimezone(timezone.utc)
    if last: last = last.astimezone(timezone.utc)
    n_resp = sum(1 for e in kept if e["who"] == "aporia")
    lines = ["---",
             f"chat: {chat['id']}",
             f"name: {json.dumps((chat.get('name') or '').strip())}",
             f"created: {created.isoformat() if created else ''}",
             f"last_message: {last.isoformat() if last else ''}",
             f"turns: {n_real} jake, {n_resp} aporia (engine-injected prompts excluded: {n_engine})",
             "speakers: jake, aporia",
             "author: aporia",
             f"source: {chat['root']}/{chat['dir']}/chat.json (container {CONTAINER}), conversation entries only",
             "---", ""]
    for e in kept:
        who = e["who"]
        when = _ts(e["ts"])
        lines.append(f"### {when.strftime('%Y-%m-%d %H:%M UTC') if when else '(no time)'} · {who}")
        lines.append("")
        lines.append(e["c"].strip())
        lines.append("")
    return "\n".join(lines), created


def main():
    ap = argparse.ArgumentParser(description="Export Aporia's conversations (user + response only) as Markdown for the index.")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--container", default=CONTAINER)
    ap.add_argument("--dry-run", action="store_true", help="write to --out (a scratch dir) and report; never touch the export tree")
    ap.add_argument("--min-user-turns", type=int, default=1, help="minimum REAL Jake turns for a chat to be exported")
    ap.add_argument("--include-engine-turns", action="store_true",
                    help="also keep idle-engine prompts and her replies to them (off: they are in the journal already)")
    args = ap.parse_args()
    if args.dry_run and os.path.abspath(args.out) == os.path.abspath(DEFAULT_OUT):
        sys.exit("--dry-run needs an --out outside the export tree")

    ok, detail = daemon_reachable()
    if not ok:
        print(f"DOCKER DAEMON NOT REACHABLE ({detail})")
        print("  export DEFERRED: nothing written; the next run retries.")
        sys.exit(EXIT_DEFERRED)

    r = subprocess.run(["docker", "exec", "-i", args.container, "python3", "-"], input=READER,
                       capture_output=True, text=True, env=_ENV, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"READER FAILED in {args.container} (rc={r.returncode}): {(r.stderr or '').strip()[-300:]}")
        sys.exit(EXIT_DEFERRED)

    staging = args.out + ".staging"
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging, exist_ok=True)
    state_path = os.path.join(args.out, ".export_state.json")
    try:
        state = json.load(open(state_path, encoding="utf-8")) if os.path.exists(state_path) else {}
    except Exception:
        state = {}
    new_state, written, unchanged, skipped, errors, scrubbed_chats, scrub_hits, chars = {}, 0, 0, 0, 0, 0, 0, 0
    for line in r.stdout.splitlines():
        if not line.strip():
            continue
        chat = json.loads(line)
        if "error" in chat:
            errors += 1; continue
        kept, n_real, n_engine = select_exchanges(chat["ex"], args.include_engine_turns)
        if n_real < args.min_user_turns or not kept:
            skipped += 1; continue
        body, created = render(chat, kept, n_real, n_engine)
        body, n = scrub(body)
        if n:
            scrubbed_chats += 1; scrub_hits += n
        h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
        fname = f"{(created or datetime.now(timezone.utc)).strftime('%Y-%m-%d')}_{chat['id']}.md"
        new_state[fname] = h
        chars += len(body)
        if state.get(fname) == h and os.path.exists(os.path.join(args.out, fname)):
            unchanged += 1
            shutil.copyfile(os.path.join(args.out, fname), os.path.join(staging, fname))
            continue
        with open(os.path.join(staging, fname), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        written += 1

    # SEAL CHECK before anything can reach the index: the harness sends Pool B (holdout) tasks to her through the same
    # API Jake uses, so a task's text can sit in a chat as a `user` turn. Any staged file sharing an 8-word shingle with
    # the sealed config refuses the whole swap; the scan prints chat ids only, never text. Positive control: a planted
    # shingle must be found, or the check is not trusted and the swap is refused too.
    seal = seal_check(staging)
    if seal is not None and seal["hits"]:
        print(f"SEAL: STOP. {len(seal['hits'])} staged chat(s) contain holdout task text: {seal['hits'][:10]}")
        shutil.rmtree(staging, ignore_errors=True)
        sys.exit(1)
    if seal is not None and not seal["control_ok"]:
        print("SEAL: check could not demonstrate it can find anything (positive control failed); swap refused")
        shutil.rmtree(staging, ignore_errors=True)
        sys.exit(1)

    # verify, then swap (the export tree is never left half-written)
    n_staged = sum(1 for f in os.listdir(staging) if f.endswith(".md"))
    if n_staged == 0 and (written or unchanged):
        print("SWAP REFUSED: staging is empty after a pass that produced files"); sys.exit(1)
    previous = args.out + ".previous"
    shutil.rmtree(previous, ignore_errors=True)
    if os.path.isdir(args.out):
        os.rename(args.out, previous)
    os.rename(staging, args.out)
    shutil.rmtree(previous, ignore_errors=True)
    json.dump(new_state, open(state_path, "w", encoding="utf-8"), indent=0)
    print(f"{'DRY RUN to ' + args.out if args.dry_run else 'exported to ' + args.out}")
    print(f"  chats: {written} written, {unchanged} unchanged, {skipped} skipped (fewer than {args.min_user_turns} real Jake turn(s), or engine-only), {errors} unreadable")
    print(f"  conversation text: {chars:,} chars in {n_staged} files; secrets scrub: {scrub_hits} replacement(s) in {scrubbed_chats} chat(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
