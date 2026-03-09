"""
parse_chatlog.py — Parse When_I_Saw_Opus.docx into clean turn-level data.

Speaker labels (Opus:/Jake:) mark turn starts. UI artifacts are filtered.
Output: instrument/data/chatlog_turns.json
"""

import re
import json
from pathlib import Path
from docx import Document


DOCX_PATH = Path(__file__).parent.parent / "chronology" / "When I Saw Opus.docx"
OUTPUT_PATH = Path(__file__).parent / "data" / "chatlog_turns.json"
PREVIEW_PATH = Path(__file__).parent / "chatlog_turns_preview.txt"


# --- Artifact detection ---

# Patterns that are always artifacts (never content)
ARTIFACT_EXACT = {
    'Show more', 'Show less', 'Done',
    'Download', 'Download all',
    'Document · MD',
    'md', 'json', 'py', 'txt', 'docx', 'xlsx', 'csv',
    'Script',
}

ARTIFACT_PATTERNS = [
    re.compile(r'^Mar \d+$'),           # date markers: "Mar 6", "Mar 7"
    re.compile(r'^\d+:\d+ [AP]M$'),     # time stamps: "1:12 AM", "4:32 AM"
    re.compile(r'^\d+ lines$'),         # file line counts: "31 lines"
]

TIMESTAMP_PATTERN = re.compile(r'^(\d+:\d+ [AP]M)$')


def is_artifact(text: str) -> bool:
    if text in ARTIFACT_EXACT:
        return True
    for pat in ARTIFACT_PATTERNS:
        if pat.match(text):
            return True
    return False


def extract_timestamp(text: str) -> str | None:
    """Return time string if text is a timestamp, else None."""
    m = TIMESTAMP_PATTERN.match(text)
    return m.group(1) if m else None


# --- Parser ---

def parse_turns(doc_path: Path) -> list[dict]:
    doc = Document(str(doc_path))
    raw = [p.text.strip() for p in doc.paragraphs]
    total_raw = len(raw)
    print(f"[PARSE] Total raw paragraphs: {total_raw}")

    # Preprocess: remove consecutive identical paragraph PAIRS (action title pairs).
    # Both occurrences are artifacts — the first one must also be removed.
    paragraphs = []
    i = 0
    while i < len(raw):
        if (i + 1 < len(raw)
                and raw[i] == raw[i + 1]
                and raw[i]  # non-empty
                and raw[i] not in ('Opus:', 'Jake:')):  # never strip speaker labels
            i += 2  # skip both
        else:
            paragraphs.append(raw[i])
            i += 1
    print(f"[PARSE] After dedup-pair removal: {len(paragraphs)} paragraphs")

    # Identify Jake:Jake runs (consecutive same-speaker at annotation level).
    # In these turns, Opus's response to the first Jake message is folded into the Jake turn.
    # We flag these turns as content_mixed in metadata.
    speaker_positions_raw = [i for i, t in enumerate(raw) if t in ('Opus:', 'Jake:')]
    mixed_turn_speakers = set()  # (position_in_raw, speaker) pairs for mixed turns
    for idx in range(len(speaker_positions_raw) - 1):
        p1, p2 = speaker_positions_raw[idx], speaker_positions_raw[idx + 1]
        if raw[p1] == raw[p2] == 'Jake:':
            mixed_turn_speakers.add(p1)

    turns = []
    current_speaker = None
    current_content = []
    current_timestamp = None
    current_is_mixed = False
    turn_number = 0
    seen_in_turn = set()  # within-turn deduplication (handles response duplication)

    def flush_turn():
        nonlocal turn_number
        if current_speaker is None:
            return
        text = '\n\n'.join(current_content).strip()
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
    while i < len(paragraphs):
        text = paragraphs[i]
        i += 1

        # --- Speaker label ---
        if text in ('Opus:', 'Jake:'):
            flush_turn()
            current_speaker = text[:-1]  # strip ':'
            current_content = []
            current_timestamp = None
            current_is_mixed = False
            seen_in_turn = set()

            # Peek: is the next paragraph a timestamp?
            if i < len(paragraphs):
                ts = extract_timestamp(paragraphs[i])
                if ts:
                    current_timestamp = ts
                    i += 1  # consume timestamp
            continue

        # --- Artifact: always skip ---
        if is_artifact(text):
            continue

        # --- Empty paragraph ---
        if not text:
            continue

        # --- Within-turn duplicate (handles full response duplication near end) ---
        if text in seen_in_turn:
            continue

        # --- Accept as content ---
        seen_in_turn.add(text)
        current_content.append(text)

    # Flush final turn
    flush_turn()

    print(f"[PARSE] Turns extracted: {len(turns)}")
    opus_turns = [t for t in turns if t['speaker'] == 'Opus']
    jake_turns = [t for t in turns if t['speaker'] == 'Jake']
    mixed = [t for t in turns if t.get('content_mixed')]
    print(f"[PARSE]   Opus: {len(opus_turns)}, Jake: {len(jake_turns)}, mixed: {len(mixed)}")

    return turns


def write_preview(turns: list[dict], path: Path) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"Total turns: {len(turns)}\n")
        f.write(f"Opus: {sum(1 for t in turns if t['speaker']=='Opus')}, ")
        f.write(f"Jake: {sum(1 for t in turns if t['speaker']=='Jake')}\n\n")

        f.write("--- Speaker turn sequence (turn, speaker, word_count, timestamp) ---\n")
        for t in turns:
            ts = f" [{t['timestamp']}]" if t['timestamp'] else ''
            f.write(f"  Turn {t['turn']:03d} | {t['speaker']:<5} | {t['word_count']:4d} words{ts}\n")

        f.write("\n--- First 5 turns (full content) ---\n")
        for t in turns[:5]:
            f.write(f"\n[Turn {t['turn']} | {t['speaker']} | {t['word_count']} words]\n")
            f.write(t['content'][:500])
            if len(t['content']) > 500:
                f.write('...')
            f.write('\n')

        f.write("\n--- Last 5 turns (full content) ---\n")
        for t in turns[-5:]:
            f.write(f"\n[Turn {t['turn']} | {t['speaker']} | {t['word_count']} words]\n")
            f.write(t['content'][:500])
            if len(t['content']) > 500:
                f.write('...')
            f.write('\n')

        # Turns with timestamps (Opus clock times)
        timestamped = [t for t in turns if t['timestamp']]
        if timestamped:
            f.write(f"\n--- Turns with timestamps ({len(timestamped)}) ---\n")
            for t in timestamped:
                f.write(f"  Turn {t['turn']:03d} | {t['speaker']:<5} | {t['timestamp']} | {t['word_count']} words\n")

        # Turn length distribution
        lengths = [t['word_count'] for t in turns]
        opus_lengths = [t['word_count'] for t in turns if t['speaker'] == 'Opus']
        jake_lengths = [t['word_count'] for t in turns if t['speaker'] == 'Jake']
        f.write(f"\n--- Word count stats ---\n")
        f.write(f"  All turns:   min={min(lengths)}, max={max(lengths)}, mean={sum(lengths)/len(lengths):.0f}\n")
        f.write(f"  Opus turns:  min={min(opus_lengths)}, max={max(opus_lengths)}, mean={sum(opus_lengths)/len(opus_lengths):.0f}\n")
        f.write(f"  Jake turns:  min={min(jake_lengths)}, max={max(jake_lengths)}, mean={sum(jake_lengths)/len(jake_lengths):.0f}\n")


if __name__ == '__main__':
    print(f"[PARSE] Reading: {DOCX_PATH}")
    turns = parse_turns(DOCX_PATH)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(turns, f, ensure_ascii=False, indent=2)
    print(f"[PARSE] Written: {OUTPUT_PATH}")

    write_preview(turns, PREVIEW_PATH)
    print(f"[PARSE] Preview: {PREVIEW_PATH}")
