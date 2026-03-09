"""
auto_annotate_chatlog.py — Auto-annotate a raw Claude.ai chatlog with Jake:/Opus: labels.

The raw chatlog has no speaker labels. The structure is:
    [Jake message]
    [TIMESTAMP]           ← marks start of Opus response
    [Opus thinking summary(ies)]
    [Opus response content]
    [Jake next message]
    [TIMESTAMP]
    ...

Algorithm:
1. Timestamps are reliable Opus turn START markers — insert "Opus:" there.
2. Within each inter-timestamp segment, the LAST paragraph block before the
   next timestamp is Jake's next message — insert "Jake:" before it.
3. Flag uncertain boundaries for manual review.

Output:
  <input>_annotated.md — ready for parse_chatlog_md.py
  <input>_annotated.preview.txt — first 60 turns for spot-checking

Usage:
    python auto_annotate_chatlog.py --input Chatlog.md
    python auto_annotate_chatlog.py --input Chatlog.md --min-jake-words 8
"""

import re
import argparse
from pathlib import Path

# ── Timestamp detection ───────────────────────────────────────────────────────

MONTH_NAMES = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
DATE_PATTERN   = re.compile(rf'^{MONTH_NAMES}\s+\d{{1,2}}$')
TIME_PATTERN   = re.compile(r'^\d{1,2}:\d{2}\s+[AP]M$')

def is_timestamp(line: str) -> bool:
    s = line.strip()
    return bool(DATE_PATTERN.match(s) or TIME_PATTERN.match(s))


# ── Top-level UI artifacts to strip ──────────────────────────────────────────

TOP_ARTIFACTS = {
    'Agent Zero hardening', 'Exocortex', 'Claude', '/', 'New chat',
    'Show more', 'Show less', 'Download', 'Download all', 'Done',
    'Document · MD', 'Script',
}
TOP_ARTIFACT_PATS = [
    re.compile(r'^[\w\s\-_()]+\.(md|json|py|txt|docx|xlsx|csv|pdf|zip)$', re.IGNORECASE),
    re.compile(r'^\d+\s+lines?$'),
    re.compile(r'^(md|json|py|txt|docx|xlsx|csv|pdf|zip)$', re.IGNORECASE),
]

def is_global_artifact(line: str) -> bool:
    s = line.strip()
    if s in TOP_ARTIFACTS:
        return True
    for pat in TOP_ARTIFACT_PATS:
        if pat.match(s):
            return True
    return False


# ── Paragraph utilities ───────────────────────────────────────────────────────

def split_paragraphs(lines: list[str]) -> list[list[str]]:
    """Split a list of lines into paragraph groups (separated by blank lines)."""
    paragraphs, current = [], []
    for line in lines:
        if line.strip():
            current.append(line)
        else:
            if current:
                paragraphs.append(current)
                current = []
    if current:
        paragraphs.append(current)
    return paragraphs


def word_count(lines: list[str]) -> int:
    return sum(len(l.split()) for l in lines)


def is_thinking_summary(line: str) -> bool:
    """
    Heuristic: Opus's thinking block summaries are sentence-length action phrases.
    They're typically 4-12 words, title-case or sentence-case, no punctuation at end.
    They never start with a bullet/code/number.
    This helps flag Opus-only content at the start of turns.
    """
    s = line.strip()
    if not s or s[0] in '-*#>0123456789`':
        return False
    words = s.split()
    return 4 <= len(words) <= 15 and not s.endswith(('.', '!', '?', ':'))


# ── Main annotator ────────────────────────────────────────────────────────────

def annotate(raw_lines: list[str], min_jake_words: int = 6) -> tuple[list[str], dict]:
    """
    Returns (annotated_lines, stats).
    Annotated lines are the output ready for parse_chatlog_md.py.
    """
    # Step 1: Find all timestamp positions
    timestamp_positions = [i for i, l in enumerate(raw_lines) if is_timestamp(l)]
    print(f"[ANNOT] Total timestamps found: {len(timestamp_positions)}")

    # Step 2: Build segments
    # Segment 0: lines[0 .. timestamp_positions[0]-1] = Jake's first message
    # Segment k: lines[timestamp_positions[k-1] .. timestamp_positions[k]-1]
    #            = timestamp + Opus response + Jake's next message

    segments = []  # Each: {'type': 'jake_first'|'opus_then_jake', 'start': int, 'end': int}

    if timestamp_positions:
        # Jake's first segment
        segments.append({
            'type': 'jake_first',
            'start': 0,
            'end': timestamp_positions[0],
        })
        # Subsequent segments
        for i, ts_pos in enumerate(timestamp_positions):
            end = timestamp_positions[i + 1] if i + 1 < len(timestamp_positions) else len(raw_lines)
            segments.append({
                'type': 'opus_then_jake',
                'timestamp_pos': ts_pos,
                'start': ts_pos,
                'end': end,
            })
    else:
        # No timestamps at all — can't annotate
        print("[ANNOT] WARNING: No timestamps found. Cannot auto-annotate.")
        return raw_lines, {}

    # Step 3: Build output
    out = []
    stats = {
        'total_segments': len(segments),
        'jake_turns': 0,
        'opus_turns': 0,
        'uncertain': 0,
        'no_jake_following': 0,
    }

    for seg in segments:
        seg_lines = raw_lines[seg['start']:seg['end']]

        if seg['type'] == 'jake_first':
            # Filter top artifacts
            content = [l for l in seg_lines if not is_global_artifact(l.strip())]
            # Remove leading/trailing blanks
            while content and not content[0].strip():
                content.pop(0)
            while content and not content[-1].strip():
                content.pop()
            if content:
                out.append('Jake:')
                out.extend(content)
                out.append('')
                stats['jake_turns'] += 1
            continue

        # opus_then_jake: timestamp line, then Opus content + Jake message
        ts_line = raw_lines[seg['timestamp_pos']].rstrip()
        content_lines = seg_lines[1:]  # everything after the timestamp

        # Remove trailing blanks from content
        while content_lines and not content_lines[-1].strip():
            content_lines.pop()

        if not content_lines:
            # Empty Opus turn
            out.append('Opus:')
            out.append(ts_line)
            out.append('')
            stats['opus_turns'] += 1
            continue

        # Split content into paragraphs
        paragraphs = split_paragraphs(content_lines)

        if not paragraphs:
            out.append('Opus:')
            out.append(ts_line)
            out.append('')
            stats['opus_turns'] += 1
            continue

        # Find where Jake's message starts.
        # Strategy: work backwards from the last paragraph. If the last paragraph
        # looks like a Jake message (>= min_jake_words, not a thinking summary header),
        # assign it to Jake. Keep going backwards if consecutive paragraphs also
        # look like Jake content (multi-paragraph Jake messages).
        # Flag uncertain when ambiguous.

        # Simple version: last paragraph = Jake (if >= min_jake_words)
        # Everything else = Opus

        jake_para_count = 0
        uncertain = False

        # Determine Jake's paragraphs from the end
        # Rule: last N consecutive paragraphs where none look like thinking summaries
        # and combined word count > min_jake_words
        j = len(paragraphs) - 1
        jake_paras = []

        # The last paragraph is almost always Jake, unless it's very short
        # (thinking-summary-like) with an Opus marker before it
        last_para = paragraphs[-1]
        last_wc = word_count(last_para)

        if last_wc < min_jake_words:
            # Too short to be Jake — flag as uncertain, assign all to Opus
            uncertain = True
            opus_paras = paragraphs
            jake_paras = []
        else:
            # Last paragraph = Jake
            jake_paras = [paragraphs[-1]]
            opus_paras = paragraphs[:-1]

            # Check if the second-to-last paragraph could also be Jake
            # (Jake sometimes writes multi-paragraph messages)
            # Heuristic: if the word count of what we've assigned to Opus
            # suggests the split is reasonable, stop here.
            # Flag if Jake's portion is > 300 words (might be mis-split)
            if word_count(jake_paras[0]) > 300:
                uncertain = True

        if uncertain:
            stats['uncertain'] += 1

        if not jake_paras:
            stats['no_jake_following'] += 1

        # Build output: Opus block
        out.append('Opus:')
        out.append(ts_line)
        for i, para in enumerate(opus_paras):
            out.extend(para)
            if i < len(opus_paras) - 1:
                out.append('')
        out.append('')
        stats['opus_turns'] += 1

        # Build output: Jake block (if present)
        if jake_paras:
            flag = '  # [UNCERTAIN — check this boundary]' if uncertain else ''
            if flag:
                out.append(f'Jake:{flag}')
            else:
                out.append('Jake:')
            for i, para in enumerate(jake_paras):
                out.extend(para)
                if i < len(jake_paras) - 1:
                    out.append('')
            out.append('')
            stats['jake_turns'] += 1

    return out, stats


def write_preview(lines: list[str], path: Path, n_turns: int = 30) -> None:
    """Write the first N Jake+Opus turns for spot-checking."""
    with open(path, 'w', encoding='utf-8') as f:
        turn_count = 0
        i = 0
        while i < len(lines) and turn_count < n_turns:
            line = lines[i]
            if line.strip() in ('Jake:', 'Opus:') or line.strip().startswith('Jake:#') or line.strip().startswith('Jake:  #'):
                speaker = 'Jake' if 'Jake' in line else 'Opus'
                uncertain = 'UNCERTAIN' in line
                # Collect content
                i += 1
                content = []
                while i < len(lines) and lines[i].strip() not in ('Jake:', 'Opus:') \
                        and not lines[i].strip().startswith('Jake:') \
                        and not (lines[i].strip() == '' and i + 1 < len(lines) and
                                 (lines[i+1].strip() in ('Jake:', 'Opus:') or
                                  lines[i+1].strip().startswith('Jake:'))):
                    content.append(lines[i])
                    i += 1
                wc = sum(len(l.split()) for l in content)
                flag = ' [UNCERTAIN]' if uncertain else ''
                f.write(f"\n{'='*60}\n")
                f.write(f"[{speaker}{flag} | {wc} words]\n")
                f.write('\n'.join(content[:20]))
                if len(content) > 20:
                    f.write(f'\n... ({len(content)-20} more lines)')
                f.write('\n')
                turn_count += 1
            else:
                i += 1


def main():
    parser = argparse.ArgumentParser(description="Auto-annotate raw Claude.ai chatlog")
    parser.add_argument('--input', required=True, help='Path to raw chatlog file')
    parser.add_argument('--output', default=None, help='Output annotated file path')
    parser.add_argument('--preview', default=None, help='Preview file path')
    parser.add_argument('--min-jake-words', type=int, default=6,
                        help='Minimum words for a paragraph to be assigned to Jake (default: 6)')
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ERROR: File not found: {args.input}")
        return 1

    out_path = Path(args.output) if args.output else in_path.with_name(in_path.stem + '_annotated.md')
    preview_path = Path(args.preview) if args.preview else in_path.with_name(in_path.stem + '_annotated.preview.txt')

    print(f"[ANNOT] Reading: {in_path}")
    raw_lines = in_path.read_text(encoding='utf-8').splitlines()
    print(f"[ANNOT] Lines: {len(raw_lines)}")

    annotated, stats = annotate(raw_lines, min_jake_words=args.min_jake_words)

    out_path.write_text('\n'.join(annotated), encoding='utf-8')
    print(f"[ANNOT] Written: {out_path}  ({len(annotated)} lines)")

    write_preview(annotated, preview_path)
    print(f"[ANNOT] Preview: {preview_path}")

    print(f"\n=== ANNOTATION SUMMARY ===")
    print(f"  Timestamps (Opus turns): {stats.get('opus_turns', 0)}")
    print(f"  Jake turns detected:     {stats.get('jake_turns', 0)}")
    print(f"  Uncertain boundaries:    {stats.get('uncertain', 0)}  <- spot-check these")
    print(f"  Opus turns with no following Jake: {stats.get('no_jake_following', 0)}")
    print(f"\nSearch for '# [UNCERTAIN' in {out_path.name} to find all flagged boundaries.")
    print(f"Review {preview_path.name} for the first ~30 turns.")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
