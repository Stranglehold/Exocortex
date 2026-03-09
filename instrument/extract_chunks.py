"""
extract_chunks.py — V2 pipeline: chunk turns into uniform ~150-word segments.

Resamples the 1,934-turn chatlog at paragraph/chunk level to create a
uniformly-sampled signal comparable to continuous neural recording (fNIRS/EEG).

Each chunk inherits full metadata from its parent turn. Short turns (< 100 words)
remain as single chunks. Long turns split at paragraph boundaries, targeting
~150 words per chunk (±50 word tolerance).

Inputs:
    data/chatlog_full_turns_dated.json

Outputs:
    data/chunks.json          — chunk records with full metadata
    data/chunks_report.txt    — distribution summary (no embeddings needed)
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).parent
DATA = ROOT / "data"

TURNS_JSON   = DATA / "chatlog_full_turns_dated.json"
OUT_CHUNKS   = DATA / "chunks.json"
OUT_REPORT   = DATA / "chunks_report.txt"

TARGET_WORDS   = 150   # target chunk size
MIN_WORDS      = 80    # minimum to split (turns below this = single chunk)
MAX_WORDS      = 200   # soft ceiling before forcing a split


def split_into_paragraphs(text: str) -> list[str]:
    """Split on double newlines, then on single newlines, keeping non-empty."""
    # Try double-newline paragraph breaks first
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if len(paras) > 1:
        return paras
    # Fall back to single newlines
    paras = [p.strip() for p in text.split('\n') if p.strip()]
    if len(paras) > 1:
        return paras
    # No paragraph structure — return as single block
    return [text.strip()]


def count_words(text: str) -> int:
    return len(text.split())


def chunk_turn(turn: dict) -> list[dict]:
    """
    Split a single turn into chunks. Returns list of chunk dicts.
    Each chunk inherits turn metadata and adds chunk_index / total_chunks.
    """
    text = turn.get('content', '').strip()
    wc = count_words(text)

    # Short turns stay as a single chunk
    if wc < MIN_WORDS:
        return [_make_chunk(turn, text, 0, 1)]

    # Split at paragraph boundaries, then merge/split to hit target size
    paragraphs = split_into_paragraphs(text)

    # Greedy merge: accumulate paragraphs until we hit TARGET_WORDS
    raw_chunks = []
    current_parts = []
    current_wc = 0

    for para in paragraphs:
        para_wc = count_words(para)

        # If adding this paragraph would overshoot MAX_WORDS and we already
        # have some content, flush current buffer first
        if current_wc + para_wc > MAX_WORDS and current_wc >= MIN_WORDS:
            raw_chunks.append(' '.join(current_parts))
            current_parts = [para]
            current_wc = para_wc
        else:
            current_parts.append(para)
            current_wc += para_wc

        # Flush if we're at or past target
        if current_wc >= TARGET_WORDS:
            raw_chunks.append(' '.join(current_parts))
            current_parts = []
            current_wc = 0

    # Flush remainder
    if current_parts:
        remainder = ' '.join(current_parts)
        # If remainder is tiny and we already have chunks, merge into last
        if count_words(remainder) < 40 and raw_chunks:
            raw_chunks[-1] = raw_chunks[-1] + ' ' + remainder
        else:
            raw_chunks.append(remainder)

    total = len(raw_chunks)
    return [_make_chunk(turn, chunk_text, idx, total)
            for idx, chunk_text in enumerate(raw_chunks)]


def _make_chunk(turn: dict, text: str, chunk_idx: int, total_chunks: int) -> dict:
    return {
        'chunk_id':            None,           # assigned after all chunks collected
        'turn_id':             turn['turn'],
        'speaker':             turn['speaker'],
        'date':                turn.get('date', 'unknown'),
        'date_index':          turn.get('date_index', -1),
        'word_count':          count_words(text),
        'text':                text,
        'chunk_within_turn':   chunk_idx,
        'total_chunks_in_turn': total_chunks,
    }


def main():
    print(f"[CHUNKS] Loading turns: {TURNS_JSON}")
    with open(TURNS_JSON, encoding='utf-8') as f:
        turns = json.load(f)
    print(f"  {len(turns)} turns loaded")

    # Extract chunks
    all_chunks = []
    for turn in turns:
        chunks = chunk_turn(turn)
        all_chunks.extend(chunks)

    # Assign sequential chunk IDs
    for i, chunk in enumerate(all_chunks):
        chunk['chunk_id'] = i

    print(f"  {len(all_chunks)} chunks extracted")

    # Write output
    with open(OUT_CHUNKS, 'w', encoding='utf-8') as f:
        json.dump({'chunks': all_chunks}, f, ensure_ascii=False, indent=2)
    size_kb = OUT_CHUNKS.stat().st_size // 1024
    print(f"  Written: {OUT_CHUNKS} ({size_kb} KB)")

    # ── Distribution Report ───────────────────────────────────────────────────

    chunk_wcs = [c['word_count'] for c in all_chunks]
    jake_chunks = [c for c in all_chunks if c['speaker'] == 'Jake']
    opus_chunks = [c for c in all_chunks if c['speaker'] == 'Opus']

    # Chunks per turn distribution
    chunks_per_turn = Counter(c['total_chunks_in_turn'] for c in all_chunks
                              if c['chunk_within_turn'] == 0)
    single_chunk_turns = chunks_per_turn.get(1, 0)
    multi_chunk_turns  = sum(v for k, v in chunks_per_turn.items() if k > 1)

    # Per-session chunk counts
    by_session = defaultdict(list)
    for c in all_chunks:
        by_session[c['date']].append(c)

    lines = [
        "=== V2 CHUNK EXTRACTION REPORT ===",
        "",
        f"Source turns:       {len(turns):>6}",
        f"Total chunks:       {len(all_chunks):>6}",
        f"Expansion ratio:    {len(all_chunks)/len(turns):.2f}x",
        "",
        "── Chunk word count distribution ──",
        f"  Mean:   {sum(chunk_wcs)/len(chunk_wcs):.0f} words",
        f"  Median: {sorted(chunk_wcs)[len(chunk_wcs)//2]} words",
        f"  Min:    {min(chunk_wcs)}",
        f"  Max:    {max(chunk_wcs)}",
        f"  < 50 words:    {sum(1 for w in chunk_wcs if w < 50):>5}",
        f"  50-100 words:  {sum(1 for w in chunk_wcs if 50 <= w < 100):>5}",
        f"  100-150 words: {sum(1 for w in chunk_wcs if 100 <= w < 150):>5}",
        f"  150-200 words: {sum(1 for w in chunk_wcs if 150 <= w < 200):>5}",
        f"  > 200 words:   {sum(1 for w in chunk_wcs if w >= 200):>5}",
        "",
        "── By speaker ──",
        f"  Jake chunks: {len(jake_chunks):>5}  "
        f"(mean {sum(c['word_count'] for c in jake_chunks)//max(1,len(jake_chunks))} words)",
        f"  Opus chunks: {len(opus_chunks):>5}  "
        f"(mean {sum(c['word_count'] for c in opus_chunks)//max(1,len(opus_chunks))} words)",
        f"  Jake:Opus ratio: 1:{len(opus_chunks)/max(1,len(jake_chunks)):.1f}",
        "",
        "── Turns by chunk count ──",
    ]
    for k in sorted(chunks_per_turn):
        label = f"{k} chunk{'s' if k > 1 else ''}"
        lines.append(f"  {label:<12} {chunks_per_turn[k]:>4} turns")
    lines += [
        f"  Single-chunk turns: {single_chunk_turns} ({100*single_chunk_turns//len(turns)}%)",
        f"  Multi-chunk turns:  {multi_chunk_turns} ({100*multi_chunk_turns//len(turns)}%)",
        "",
        "── Per session ──",
    ]
    for date in sorted(by_session.keys(), key=lambda d: (d == 'unknown', d)):
        sess_chunks = by_session[date]
        j = sum(1 for c in sess_chunks if c['speaker'] == 'Jake')
        o = sum(1 for c in sess_chunks if c['speaker'] == 'Opus')
        lines.append(f"  {date:<12} {len(sess_chunks):>4} chunks  "
                     f"(Jake: {j}, Opus: {o})")

    report = '\n'.join(lines)
    sys.stdout.buffer.write(('\n' + report + '\n').encode('utf-8', errors='replace'))

    with open(OUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n  Report written: {OUT_REPORT}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
