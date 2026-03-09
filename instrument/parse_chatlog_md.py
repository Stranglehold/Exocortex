"""
parse_chatlog_md.py — Parse an annotated chatlog .md file into turn-level data.

Input: a plain-text markdown file where turns are marked with "Opus:" or "Jake:"
       on their own line, followed by the turn's content.

Handles UI artifacts from Claude.ai interface (timestamps, action summaries,
file attachment references, thinking block duplication, etc.).

Output: instrument/data/chatlog2_turns.json  (same schema as chatlog_turns.json)

Usage:
    python parse_chatlog_md.py --input "C:/path/to/WhenIsawOpus2.md"
    python parse_chatlog_md.py --input "C:/path/to/WhenIsawOpus2.md" --output custom_turns.json
"""

import re
import json
import argparse
from pathlib import Path


DATA_DIR = Path(__file__).parent / "data"
DEFAULT_OUTPUT = DATA_DIR / "chatlog2_turns.json"

# ── Artifact detection ────────────────────────────────────────────────────────

ARTIFACT_EXACT = {
    'Show more', 'Show less', 'Done', 'Download', 'Download all',
    'Document · MD', 'md', 'json', 'py', 'txt', 'docx', 'xlsx', 'csv',
    'Script', 'Opus:', 'Jake:',  # speaker labels handled separately
}

# File extension labels that appear after attachment file names
FILE_EXT_PATTERN = re.compile(r'^(md|json|py|txt|docx|xlsx|csv|pdf|zip)$', re.IGNORECASE)
# Date markers: "Mar 6", "Mar 7", "Feb 28", etc.
DATE_PATTERN = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$')
# Timestamps: "3:04 AM", "11:32 PM"
TIMESTAMP_PATTERN = re.compile(r'^\d{1,2}:\d{2}\s+[AP]M$')
# Line counts: "31 lines", "166 lines"
LINE_COUNT_PATTERN = re.compile(r'^\d+\s+lines?$')
# File attachment references: "filename.md" or "Document · MD"
ATTACHMENT_PATTERN = re.compile(r'^[\w\s\-_()]+\.(md|json|py|txt|docx|xlsx|csv|pdf|zip)$', re.IGNORECASE)


def is_artifact(line: str) -> bool:
    """Return True if this line is a UI artifact that should be filtered."""
    if not line:
        return False
    if line in ARTIFACT_EXACT:
        return True
    if DATE_PATTERN.match(line):
        return True
    if TIMESTAMP_PATTERN.match(line):
        return True
    if LINE_COUNT_PATTERN.match(line):
        return True
    if ATTACHMENT_PATTERN.match(line):
        return True
    if FILE_EXT_PATTERN.match(line):
        return True
    return False


def extract_timestamp(line: str) -> str | None:
    """Return the timestamp string if this line is a timestamp, else None."""
    return line if TIMESTAMP_PATTERN.match(line) else None


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_turns(md_path: Path) -> list[dict]:
    """
    Parse a chatlog MD file into a list of turn dicts.

    Each turn: {turn, speaker, timestamp, content, word_count, content_mixed}

    The speaker alternates Opus/Jake. UI artifacts are filtered. Action summary
    lines that appear twice consecutively (Claude thinking block duplication)
    are collapsed to one — or filtered entirely if they're generic summaries.
    """
    raw_lines = md_path.read_text(encoding='utf-8').splitlines()
    print(f"[PARSE] Total raw lines: {len(raw_lines)}")

    # Step 1: Strip lines, keep empty lines as paragraph separators
    lines = [l.rstrip() for l in raw_lines]

    # Step 2: Remove consecutive identical non-speaker lines (action summary duplication).
    # The Claude UI shows thinking summaries twice. We collapse to one.
    deduped = []
    i = 0
    while i < len(lines):
        if (i + 1 < len(lines)
                and lines[i] == lines[i + 1]
                and lines[i].strip()
                and lines[i].strip() not in ('Opus:', 'Jake:')):
            deduped.append(lines[i])
            i += 2  # skip the duplicate
        else:
            deduped.append(lines[i])
            i += 1
    print(f"[PARSE] After dedup-pair removal: {len(deduped)} lines")

    # Step 3: Parse into turns
    turns = []
    current_speaker = None
    current_content = []
    current_timestamp = None
    current_is_mixed = False
    turn_number = 0
    seen_in_turn: set = set()

    def flush_turn():
        nonlocal turn_number
        if current_speaker is None:
            return
        text = '\n\n'.join(p for p in current_content if p).strip()
        if text:
            turns.append({
                'turn': turn_number,
                'speaker': current_speaker,
                'timestamp': current_timestamp,
                'content': text,
                'word_count': len(text.split()),
                'content_mixed': current_is_mixed,
            })
            turn_number += 1

    i = 0
    while i < len(deduped):
        line = deduped[i].strip()
        i += 1

        # Speaker labels
        if line in ('Opus:', 'Jake:'):
            flush_turn()
            current_speaker = line[:-1]
            current_content = []
            current_timestamp = None
            current_is_mixed = False
            seen_in_turn = set()

            # Peek for a timestamp on the very next non-empty line
            while i < len(deduped) and not deduped[i].strip():
                i += 1  # skip blank lines between speaker label and first content
            if i < len(deduped):
                ts = extract_timestamp(deduped[i].strip())
                if ts:
                    current_timestamp = ts
                    i += 1
            continue

        # Artifact: skip
        if is_artifact(line):
            continue

        # Empty line: paragraph separator (keep structure, don't accumulate blanks)
        if not line:
            if current_content and current_content[-1] != '':
                current_content.append('')
            continue

        # Within-turn duplicate: skip
        if line in seen_in_turn:
            continue

        seen_in_turn.add(line)
        current_content.append(line)

    flush_turn()

    # Detect content-mixed turns (consecutive same-speaker runs)
    # Jake:Jake runs mean the first Jake turn contains mixed content
    for idx in range(len(turns) - 1):
        if turns[idx]['speaker'] == turns[idx + 1]['speaker'] == 'Jake':
            turns[idx]['content_mixed'] = True

    opus_turns = [t for t in turns if t['speaker'] == 'Opus']
    jake_turns = [t for t in turns if t['speaker'] == 'Jake']
    mixed = [t for t in turns if t.get('content_mixed')]
    print(f"[PARSE] Turns extracted: {len(turns)}")
    print(f"[PARSE]   Opus: {len(opus_turns)}, Jake: {len(jake_turns)}, mixed: {len(mixed)}")

    return turns


def write_preview(turns: list[dict], path: Path) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"Total turns: {len(turns)}\n")
        f.write(f"Opus: {sum(1 for t in turns if t['speaker']=='Opus')}, ")
        f.write(f"Jake: {sum(1 for t in turns if t['speaker']=='Jake')}\n\n")

        f.write("--- Speaker turn sequence ---\n")
        for t in turns:
            ts = f" [{t['timestamp']}]" if t['timestamp'] else ''
            mixed = ' [MIXED]' if t.get('content_mixed') else ''
            f.write(f"  Turn {t['turn']:03d} | {t['speaker']:<5} | {t['word_count']:5d} words{ts}{mixed}\n")

        f.write("\n--- First 5 turns (full content) ---\n")
        for t in turns[:5]:
            f.write(f"\n[Turn {t['turn']} | {t['speaker']} | {t['word_count']} words]\n")
            f.write(t['content'][:600])
            if len(t['content']) > 600:
                f.write('...')
            f.write('\n')

        f.write("\n--- Last 5 turns (full content) ---\n")
        for t in turns[-5:]:
            f.write(f"\n[Turn {t['turn']} | {t['speaker']} | {t['word_count']} words]\n")
            f.write(t['content'][:600])
            if len(t['content']) > 600:
                f.write('...')
            f.write('\n')

        lengths = [t['word_count'] for t in turns]
        opus_lengths = [t['word_count'] for t in turns if t['speaker'] == 'Opus']
        jake_lengths = [t['word_count'] for t in turns if t['speaker'] == 'Jake']
        f.write(f"\n--- Word count stats ---\n")
        f.write(f"  All:  min={min(lengths)}, max={max(lengths)}, mean={sum(lengths)/len(lengths):.0f}\n")
        f.write(f"  Opus: min={min(opus_lengths)}, max={max(opus_lengths)}, mean={sum(opus_lengths)/len(opus_lengths):.0f}\n")
        f.write(f"  Jake: min={min(jake_lengths)}, max={max(jake_lengths)}, mean={sum(jake_lengths)/len(jake_lengths):.0f}\n")


def main():
    parser = argparse.ArgumentParser(description="Parse annotated chatlog .md into turns JSON")
    parser.add_argument('--input', required=True, help="Path to the .md chatlog file")
    parser.add_argument('--output', default=str(DEFAULT_OUTPUT), help="Output JSON path")
    parser.add_argument('--preview', default=None, help="Optional preview text file path")
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        print(f"ERROR: File not found: {args.input}")
        return 1

    print(f"[PARSE] Reading: {md_path}")
    turns = parse_turns(md_path)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(turns, f, ensure_ascii=False, indent=2)
    print(f"[PARSE] Written: {out_path}")

    if args.preview:
        preview_path = Path(args.preview)
        write_preview(turns, preview_path)
        print(f"[PARSE] Preview: {preview_path}")
    else:
        # Write a default preview alongside the JSON
        preview_path = out_path.with_suffix('.preview.txt')
        write_preview(turns, preview_path)
        print(f"[PARSE] Preview: {preview_path}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
