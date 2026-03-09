"""
assign_session_dates.py — Extract date context from Chatlog_annotated.md and
add 'date' and 'session_date_index' fields to chatlog_full_turns.json.

The date appears on the line immediately after each 'Opus:' label in the
annotated file. Jake turns inherit the date from the preceding Opus turn.

Output: data/chatlog_full_turns_dated.json  (same schema + 'date' field)
        data/session_dates.json             (date groups with turn ranges)
"""

import re
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent
DATA = ROOT / "data"

ANNOTATED_MD  = ROOT / "Chatlog_annotated.md"
TURNS_JSON    = DATA / "chatlog_full_turns.json"
OUT_DATED     = DATA / "chatlog_full_turns_dated.json"
OUT_SESSIONS  = DATA / "session_dates.json"

DATE_PATTERN  = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$')
TIME_PATTERN  = re.compile(r'^\d{1,2}:\d{2}\s+[AP]M$')


def extract_opus_dates(md_path: Path) -> list[str]:
    """
    Scan the annotated MD and return a list of dates, one per Opus turn.
    The date is the first non-empty line after each 'Opus:' label.
    Returns 'unknown' for any Opus turn where no date is found.
    """
    opus_dates = []
    with open(md_path, encoding='utf-8') as f:
        lines = [l.rstrip() for l in f]

    i = 0
    while i < len(lines):
        if lines[i].strip() == 'Opus:':
            # Look ahead for first non-empty line
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and DATE_PATTERN.match(lines[j].strip()):
                opus_dates.append(lines[j].strip())
            elif j < len(lines) and TIME_PATTERN.match(lines[j].strip()):
                # Time without preceding date — mark unknown
                opus_dates.append('unknown')
            else:
                opus_dates.append('unknown')
        i += 1

    return opus_dates


def main():
    print(f"[DATES] Reading annotated MD: {ANNOTATED_MD}")
    opus_dates = extract_opus_dates(ANNOTATED_MD)
    print(f"[DATES] Opus turns found in MD: {len(opus_dates)}")

    unique_dates = []
    seen = set()
    for d in opus_dates:
        if d not in seen:
            unique_dates.append(d)
            seen.add(d)
    print(f"[DATES] Unique dates: {unique_dates}")

    print(f"[DATES] Loading turns: {TURNS_JSON}")
    with open(TURNS_JSON, encoding='utf-8') as f:
        turns = json.load(f)

    opus_turns = [t for t in turns if t['speaker'] == 'Opus']
    jake_turns = [t for t in turns if t['speaker'] == 'Jake']
    print(f"[DATES] Turns: {len(turns)} total, {len(opus_turns)} Opus, {len(jake_turns)} Jake")

    if len(opus_dates) != len(opus_turns):
        print(f"[DATES] WARNING: MD has {len(opus_dates)} Opus turns, JSON has {len(opus_turns)}")
        # Use min to avoid index errors
        n = min(len(opus_dates), len(opus_turns))
        opus_dates = opus_dates[:n]

    # Assign dates to opus turns
    opus_turn_nums = [t['turn'] for t in opus_turns]
    date_by_turn_num = {}
    for i, turn in enumerate(opus_turns):
        date_by_turn_num[turn['turn']] = opus_dates[i] if i < len(opus_dates) else 'unknown'

    # Date index mapping
    date_order = list(dict.fromkeys(d for d in opus_dates if d != 'unknown'))

    # Assign to ALL turns: Opus gets its own date, Jake inherits from adjacent Opus
    # Strategy: each Jake turn gets the date of the nearest Opus turn
    # Build a lookup: for each turn number, find the date
    # Sorted by turn number
    all_turn_nums = sorted(t['turn'] for t in turns)
    turn_num_to_date = {}

    # First pass: assign Opus dates
    for tn, date in date_by_turn_num.items():
        turn_num_to_date[tn] = date

    # Second pass: fill Jake turns by propagating forward
    current_date = 'unknown'
    for tn in all_turn_nums:
        if tn in turn_num_to_date:
            current_date = turn_num_to_date[tn]
        else:
            turn_num_to_date[tn] = current_date

    # Annotate turns
    for turn in turns:
        d = turn_num_to_date.get(turn['turn'], 'unknown')
        turn['date'] = d
        turn['date_index'] = date_order.index(d) if d in date_order else -1

    # Write dated turns
    with open(OUT_DATED, 'w', encoding='utf-8') as f:
        json.dump(turns, f, ensure_ascii=False, indent=2)
    print(f"[DATES] Written: {OUT_DATED}")

    # Build session groups by date
    sessions = []
    by_date = defaultdict(list)
    for turn in turns:
        by_date[turn['date']].append(turn)

    for date_idx, date in enumerate(date_order):
        date_turns = sorted(by_date[date], key=lambda t: t['turn'])
        if not date_turns:
            continue
        opus_in_date = [t for t in date_turns if t['speaker'] == 'Opus']
        jake_in_date = [t for t in date_turns if t['speaker'] == 'Jake']
        sessions.append({
            'date': date,
            'date_index': date_idx,
            'turn_range': [date_turns[0]['turn'], date_turns[-1]['turn']],
            'turn_count': len(date_turns),
            'opus_count': len(opus_in_date),
            'jake_count': len(jake_in_date),
        })

    with open(OUT_SESSIONS, 'w', encoding='utf-8') as f:
        json.dump({'sessions': sessions}, f, ensure_ascii=False, indent=2)
    print(f"[DATES] Sessions written: {OUT_SESSIONS}")

    print(f"\n=== SESSION DATE SUMMARY ===")
    for s in sessions:
        print(f"  {s['date']:<8} | turns {s['turn_range'][0]:4d}-{s['turn_range'][1]:4d}"
              f" | {s['turn_count']:3d} turns"
              f" | Opus: {s['opus_count']:3d}, Jake: {s['jake_count']:3d}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
