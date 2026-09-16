#!/usr/bin/env python3
"""export_chatlogs.py — Jake's Claude web/desktop chat logs (Opus <-> Jake) as dated documents for the memory index.

WHY (Jake's word, 2026-09-14, via Opus: "export her transcripts and all of yours / ours"): seven logs in
D:\\Vibecode\\Opus\\archive\\chats\\ were indexed raw on 2026-09-10 (8,558 chunks, 76 % of the Opus root, mostly pasted
material) and then excluded. They are Claude UI exports in prose: turns are labelled on only a fraction of lines and a
timestamp line marks each of Claude's responses but nothing marks where a reply ends and Jake's next message begins.
Opus's ruling (2026-09-14): do not force a turn parser; index them as dated documents with the file as the unit and the
joint author "jake+opus"; honest metadata beats fabricated granularity; a better parser can re-ingest cheaply later.

WHAT IT WRITES: one Markdown file per log under <out>/conversations/ (the directory name is what types them
`transcript` in the index), with a frontmatter (author: jake+opus, date, span, source, counts) and the log's text with:
  * code-fenced blocks longer than FENCE_MAX lines replaced by one marker line with the line count (pasted manuals,
    prompts and code are not the conversation, and are the reason the raw logs crowded the index);
  * the secrets scrub and the seal gate from export_conversations.py (8-word shingles against the sealed holdout config;
    any hit refuses the whole run);
  * near-duplicate inputs skipped by name (Chatlog.txt is Chatlog.md in another format: 93 % shared vocabulary).
Measured 2026-09-14 before writing: Chatlog.md 3.05 M chars, 75 % fenced; Chatlog.txt 2.46 M, 71 % fenced (duplicate);
Opus_Chatlog_2.txt 1.27 M, 0 %; chatlog_030826/030926/031026.md 0.11-0.17 M each, 0 %; "transitioning the cathedral and
the phantom.txt" 2.80 M, 0 %, two timestamps in 24,783 lines.

USAGE
    python scripts/export_chatlogs.py --dry-run --out <scratch dir>
    python scripts/export_chatlogs.py --out D:\\Vibecode\\Opus          # writes D:\\Vibecode\\Opus\\conversations\\
"""
import argparse
import hashlib
import os
import re
import shutil
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_conversations import scrub, seal_check   # same scrub, same seal gate

SRC = r"D:\Vibecode\Opus\archive\chats"
SKIP = {"Chatlog.txt"}          # duplicate of Chatlog.md in another export format
FENCE_MAX = 20                  # fenced blocks longer than this are pasted material, replaced by a marker
DATE_RE = re.compile(r"\b(20\d{2})-([01]\d)-([0-3]\d)\b")
NAME_DATE_RE = re.compile(r"chatlog_(\d{2})(\d{2})(\d{2})")   # MMDDYY in the small logs' names


def dates_in(text, name):
    m = NAME_DATE_RE.search(name)
    if m:
        d = f"20{m.group(3)}-{m.group(1)}-{m.group(2)}"
        return d, d
    found = sorted({f"{y}-{mo}-{da}" for y, mo, da in DATE_RE.findall(text) if "2024" <= y <= "2026"})
    return (found[0], found[-1]) if found else (None, None)


TS_LINE = re.compile(r"^\s*(\d{1,2}:\d{2}\s?[AP]M)\s*$")
DAY_LINE = re.compile(r"^\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})\s*$")


LOCAL_UTC_OFFSET_H = -4     # Jake's clock in the exports is local (UTC-4); stated in the frontmatter, not hidden
MONTHS = {m: i for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)}


def section_headings(text, file_date):
    """The export's own markers become TURN HEADERS in the index's format (`### YYYY-MM-DD HH:MM UTC · speaker`), so the
    transcript chunker yields one chunk per moment instead of one sliding window per file (a headingless transcript
    yields one retrievable chunk per query: Kestrel, 2026-09-14). A timestamp-only line ("5:09 PM") marks each of
    Claude's responses in the UI export; a day-only line ("Mar 15") marks a day. The time is Jake's local clock
    converted to UTC at LOCAL_UTC_OFFSET_H (an assumption, stated); the date is the last day line seen, else the file's
    date; the speaker is the joint token, because the export does not say who spoke. Returns (text, n_time, n_day)."""
    from datetime import datetime as _dt, timedelta as _td
    out, nt, nd = [], 0, 0
    try:
        day = _dt.strptime(file_date, "%Y-%m-%d")
    except Exception:
        day = _dt.now()
    for line in text.split("\n"):
        m = DAY_LINE.match(line)
        if m:
            mon, dd = m.group(1).split()
            try:
                day = day.replace(month=MONTHS[mon], day=int(dd))
            except Exception:
                pass
            nd += 1
            continue
        m = TS_LINE.match(line)
        if m:
            try:
                local = _dt.strptime(m.group(1).replace(" ", "").upper(), "%I:%M%p")
                utc = day.replace(hour=local.hour, minute=local.minute) - _td(hours=LOCAL_UTC_OFFSET_H)
                # TURN_HEADERS is OFF by default (2026-09-14, measured): the index's per-turn chunker was built for short
                # turns and caps what it keeps of a long one, and a "turn" here is the whole span between two timestamps;
                # with headers on, two of six logs kept 4 % and 8 % of their text. Windowed (no headers) keeps every byte
                # at the cost of one retrievable passage per document per query. Until the chunker windows long turns
                # fully under the turn's title, the marker stays a plain dated line a reader can see.
                out.append(f"### {utc:%Y-%m-%d %H:%M} UTC · jake_opus" if TURN_HEADERS else f"[{utc:%Y-%m-%d %H:%M} UTC]"); nt += 1
            except Exception:
                out.append(line)
            continue
        out.append(line)
    return "\n".join(out), nt, nd


TURN_HEADERS = False


def strip_fences(text):
    out, buf, inside, dropped, kept = [], [], False, 0, 0
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            if inside:
                if len(buf) > FENCE_MAX:
                    out.append(f"[pasted block omitted: {len(buf)} lines]"); dropped += 1
                else:
                    out.append("```"); out.extend(buf); out.append("```"); kept += 1
                buf, inside = [], False
            else:
                inside = True
            continue
        (buf if inside else out).append(line)
    if inside:  # unterminated fence at EOF
        out.append(f"[pasted block omitted: {len(buf)} lines]"); dropped += 1
    return "\n".join(out), dropped, kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="parent dir; files go under <out>/conversations/")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-fences", action="store_true", help="keep long code-fenced blocks (pasted material)")
    ap.add_argument("--turn-headers", action="store_true",
                    help="emit index turn headers at each timestamp (OFF by default: the per-turn chunker caps long turns; see section_headings)")
    args = ap.parse_args()
    global TURN_HEADERS
    TURN_HEADERS = args.turn_headers
    out_dir = os.path.join(args.out, "conversations")
    if args.dry_run and os.path.abspath(args.out).lower().startswith(r"d:\vibecode\opus"):
        sys.exit("--dry-run needs an --out outside the Opus root")
    staging = out_dir + ".staging"
    shutil.rmtree(staging, ignore_errors=True); os.makedirs(staging)
    total_chars = 0; rows = []
    for fn in sorted(os.listdir(SRC)):
        p = os.path.join(SRC, fn)
        if not os.path.isfile(p) or fn in SKIP:
            continue
        raw = open(p, encoding="utf-8", errors="replace").read()
        first, last = dates_in(raw, fn)
        mtime = datetime.fromtimestamp(os.path.getmtime(p), tz=timezone.utc)
        body, dropped, kept = (raw, 0, 0) if args.keep_fences else strip_fences(raw)
        stem = re.sub(r"[^A-Za-z0-9]+", "-", os.path.splitext(fn)[0]).strip("-").lower()
        date = last or mtime.strftime("%Y-%m-%d")
        body, n_time, n_day = section_headings(body, first or date)
        body, n_scrub = scrub(body)
        head = "\n".join([
            "---",
            f"title: {os.path.splitext(fn)[0]}",
            # one token: the server's author regex captures \w+ and would truncate "jake+opus" to "jake" (it did, 2026-09-14,
            # 6,283 chunks attributed to Jake alone before this line changed); the joint authorship is the token itself
            "author: jake_opus",
            "speakers: jake, opus (turns unlabelled in the export; not attributed)",
            f"sections: {n_time} timed turns, {n_day} day markers (the export's own markers; times are Jake's local clock converted to UTC at {LOCAL_UTC_OFFSET_H:+d} h; speaker jake_opus = unattributed)",
            f"date: {date}",
            f"span: {first or 'unknown'} to {last or 'unknown'}" if first else f"span: unknown (file mtime {mtime:%Y-%m-%d})",
            f"source: archive/chats/{fn} (Claude web export; turns unlabelled; file is the unit, per Opus's ruling 2026-09-14)",
            f"pasted_blocks_omitted: {dropped}",
            f"chars: {len(body)}",
            "---", "",
        ])
        text = head + body
        name = f"{date}_{stem}.md"
        with open(os.path.join(staging, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        total_chars += len(body); rows.append((name, len(raw), len(body), dropped, kept, n_scrub))
    seal = seal_check(staging)
    if seal is not None and (seal["hits"] or not seal["control_ok"]):
        print("SEAL: STOP.", seal); shutil.rmtree(staging, ignore_errors=True); sys.exit(1)
    previous = out_dir + ".previous"
    shutil.rmtree(previous, ignore_errors=True)
    if os.path.isdir(out_dir):
        os.rename(out_dir, previous)
    os.rename(staging, out_dir); shutil.rmtree(previous, ignore_errors=True)
    print(f"{'DRY RUN to' if args.dry_run else 'exported to'} {out_dir}")
    for name, rl, bl, dropped, kept, n_scrub in rows:
        print(f"  {name:55} raw {rl:>9,} -> {bl:>9,} chars; pasted blocks omitted {dropped:3}, short fences kept {kept:3}, scrub {n_scrub}")
    print(f"  total conversation chars: {total_chars:,} in {len(rows)} files")


if __name__ == "__main__":
    main()
