"""
build_v2_pipeline.py — V2 Full Pipeline: Parse -> Stitch -> Chunk -> Embed -> Detrend -> 5-channel -> UMAP

Sources:
  Doc1: instrument/data/chatlog_full_turns_dated.json   (1934 turns, annotated)
  Doc2: chronology/WhenIsawOpus2.md                     (153 turns, Jake-annotated, overlaps Doc1 tail)
  Doc3: instrument/chatlog_030826.md                    (raw export, Session 052, Mar 8-9)

Stitch logic:
  Doc1 turns 0..1913 (pre-overlap) + Doc2 all turns (override Doc1 turns 1914+) + Doc3 all turns

Outputs (instrument/data/v2/):
  all_turns.json                  stitched turns before chunking
  chunks.json                     ~150-word paragraph chunks
  chunk_embeddings.npy            768-dim raw embeddings (N_chunks × 768)
  chunk_embeddings_detrended.npy  per-session detrended embeddings
  chunk_5channel.json             cosine projection onto 5 domain centroids
  umap_v2.json                    3D UMAP (all chunks + corpus)
  stitch_report.json              deduplication details
  parse_report.json               Doc3 parsing summary

Usage:
  python build_v2_pipeline.py             (run all phases)
  python build_v2_pipeline.py --phase 1   (parse only)
  python build_v2_pipeline.py --phase 2   (stitch only, needs phase 1)
  python build_v2_pipeline.py --phase 3   (chunk only)
  python build_v2_pipeline.py --phase 4   (embed only — skips to checkpoint if present)
  python build_v2_pipeline.py --phase 5   (detrend + 5-channel)
  python build_v2_pipeline.py --phase 6   (UMAP)
"""

import re
import sys
import json
import time
import argparse
import requests
import numpy as np
from pathlib import Path
from collections import defaultdict

# ── cupy optional import ──────────────────────────────────────────────────────
try:
    import cupy as cp
    _GPU = True
    print("[V2] cupy available — GPU acceleration enabled")
except ImportError:
    cp = np
    _GPU = False

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT   = Path(__file__).parent
DATA   = ROOT / "data"
V2     = DATA / "v2"
CHRON  = ROOT.parent / "chronology"

DOC1_TURNS      = DATA / "chatlog_full_turns_dated.json"
DOC2_MD         = CHRON / "WhenIsawOpus2.md"
DOC3_RAW        = ROOT  / "chatlog_030826.md"
CENTROIDS_768   = DATA  / "centroids_768.json"
CORPUS_EMBEDDINGS = DATA / "evolution_embeddings.npy"

# V2 outputs
ALL_TURNS_JSON   = V2 / "all_turns.json"
CHUNKS_JSON      = V2 / "chunks.json"
EMBED_NPY        = V2 / "chunk_embeddings.npy"
EMBED_PART_NPY   = V2 / "chunk_embeddings.part.npy"
DETRENDED_NPY    = V2 / "chunk_embeddings_detrended.npy"
CHANNEL5_JSON    = V2 / "chunk_5channel.json"
UMAP_JSON        = V2 / "umap_v2.json"
STITCH_RPT_JSON  = V2 / "stitch_report.json"
PARSE_RPT_JSON   = V2 / "parse_report.json"

# Embedding API
EMBED_URL   = "http://localhost:1234/v1/embeddings"
EMBED_MODEL = "nomic-embed-text-v1.5"
BATCH_SIZE  = 16
MAX_CHARS   = 8000
CHECKPOINT_EVERY = 100

# Chunking
TARGET_WORDS = 150
MIN_WORDS    = 80
MAX_WORDS    = 200


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: Parse Doc2 (WhenIsawOpus2.md) and Doc3 (chatlog_030826.md)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Artifact patterns (shared) ────────────────────────────────────────────────
_ARTIFACT_EXACT = {
    'Show more', 'Show less', 'Done', 'Download', 'Download all',
    'Document · MD', 'md', 'json', 'py', 'txt', 'docx', 'xlsx', 'csv',
    'npy', 'py', 'Script', '2 / 2',
}
_DATE_PAT      = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$')
_TIMESTAMP_PAT = re.compile(r'^\d{1,2}:\d{2}\s+[AP]M$')
_LINECOUNT_PAT = re.compile(r'^\d+\s+lines?$')
_ATTACHMENT_PAT = re.compile(r'^[\w\s\-_()+.]+\.(md|json|py|txt|docx|xlsx|csv|pdf|zip|npy|faiss|jsx)$', re.I)
_EXT_PAT       = re.compile(r'^(md|json|py|txt|docx|xlsx|csv|pdf|zip|npy|jsx)$', re.I)
# Word sizes are flagged like "347 lines" or "166 lines"
_LINECOUNT2_PAT = re.compile(r'^\d+\s+(lines?|KB|MB)$', re.I)

# Thinking-summary verb starters (for Doc3 parsing)
_THINKING_VERBS = {
    # Past participle action summaries
    'Excavated', 'Synthesized', 'Identified', 'Recognized', 'Validated',
    'Prioritized', 'Contemplated', 'Deliberated', 'Examined', 'Investigated',
    'Surveyed', 'Mapped', 'Catalogued', 'Contextualized', 'Reoriented',
    'Acknowledged', 'Weighed', 'Orchestrated', 'Architected', 'Reconciled',
    'Resolved', 'Celebrated', 'Validated', 'Analyzed', 'Reviewed',
    'Reconstructed', 'Assessed', 'Prepared', 'Oriented', 'Reflected',
    'Marshaled', 'Endorsed', 'Envisioned', 'Retrieved',
    # Present gerund tool-use summaries
    'Reading', 'Writing', 'Examining', 'Synthesizing', 'Mapping', 'Analyzing',
    'Computing', 'Tracing', 'Finding', 'Looking', 'Getting', 'Formatting',
    'Exploring', 'Understanding', 'Checking', 'Extracting', 'Searching',
    'Identifying', 'Confirming', 'Comparing', 'Loading',
}


def is_artifact(line: str) -> bool:
    if not line:
        return False
    if line in _ARTIFACT_EXACT:
        return True
    if _DATE_PAT.match(line):
        return True
    if _TIMESTAMP_PAT.match(line):
        return True
    if _LINECOUNT_PAT.match(line) or _LINECOUNT2_PAT.match(line):
        return True
    if _ATTACHMENT_PAT.match(line):
        return True
    if _EXT_PAT.match(line):
        return True
    return False


def is_thinking_summary(line: str) -> bool:
    """Return True if line looks like an action-summary (thinking block) to strip."""
    words = line.split()
    if not words:
        return False
    # Short lines starting with known thinking verbs
    if len(words) <= 15 and words[0] in _THINKING_VERBS:
        return True
    return False


def collapse_consecutive_dupes(lines: list[str]) -> list[str]:
    """Remove consecutive identical non-empty lines (thinking block duplication)."""
    out = []
    i = 0
    while i < len(lines):
        if (i + 1 < len(lines)
                and lines[i] == lines[i + 1]
                and lines[i].strip()
                and lines[i].strip() not in ('Opus:', 'Jake:')):
            out.append(lines[i])
            i += 2
        else:
            out.append(lines[i])
            i += 1
    return out


# ── Doc2 parser (WhenIsawOpus2.md — has Jake:/Opus: labels) ──────────────────

def parse_doc2(md_path: Path) -> tuple[list[dict], dict]:
    """
    Parse WhenIsawOpus2.md (labeled format with Jake:/Opus: labels) into turns.
    Returns (turns, parse_info). Extracts date markers and assigns to turns.
    """
    raw_lines = md_path.read_text(encoding='utf-8').splitlines()
    lines = [l.rstrip() for l in raw_lines]
    lines = collapse_consecutive_dupes(lines)
    print(f"[DOC2] {len(raw_lines)} raw lines -> {len(lines)} after dedup")

    # Track date markers in sequence alongside speaker labels
    turns = []
    current_speaker = None
    current_content = []
    current_timestamp = None
    current_date = 'unknown'
    turn_number = 0
    seen_in_turn: set = set()

    def flush_turn():
        nonlocal turn_number
        if current_speaker is None:
            return
        text = '\n\n'.join(p for p in current_content if p).strip()
        if text:
            turns.append({
                'turn':       turn_number,
                'speaker':    current_speaker,
                'timestamp':  current_timestamp,
                'date':       current_date,
                'date_index': -1,   # assigned later
                'content':    text,
                'word_count': len(text.split()),
                'source':     'doc2',
            })
            turn_number += 1

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if line in ('Opus:', 'Jake:'):
            flush_turn()
            current_speaker = line[:-1]
            current_content = []
            current_timestamp = None
            seen_in_turn = set()

            # Peek for timestamp or date marker on next non-empty line
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                nxt = lines[i].strip()
                if _DATE_PAT.match(nxt):
                    current_date = nxt
                    i += 1
                    # Peek again for timestamp
                    while i < len(lines) and not lines[i].strip():
                        i += 1
                    if i < len(lines):
                        nxt2 = lines[i].strip()
                        if _TIMESTAMP_PAT.match(nxt2):
                            current_timestamp = nxt2
                            i += 1
                elif _TIMESTAMP_PAT.match(nxt):
                    current_timestamp = nxt
                    i += 1
            continue

        # Date markers that appear mid-content (update current_date for following turns)
        if _DATE_PAT.match(line):
            current_date = line
            continue

        if is_artifact(line):
            continue

        if not line:
            if current_content and current_content[-1] != '':
                current_content.append('')
            continue

        if line in seen_in_turn:
            continue

        seen_in_turn.add(line)
        current_content.append(line)

    flush_turn()

    # Assign date_index
    unique_dates = list(dict.fromkeys(t['date'] for t in turns if t['date'] != 'unknown'))
    for t in turns:
        t['date_index'] = unique_dates.index(t['date']) if t['date'] in unique_dates else -1

    opus_n = sum(1 for t in turns if t['speaker'] == 'Opus')
    jake_n = sum(1 for t in turns if t['speaker'] == 'Jake')
    print(f"[DOC2] Extracted {len(turns)} turns: Opus={opus_n}, Jake={jake_n}")

    parse_info = {
        'source': 'WhenIsawOpus2.md',
        'total_turns': len(turns),
        'opus_turns': opus_n,
        'jake_turns': jake_n,
        'dates': unique_dates,
    }
    return turns, parse_info


# ── Doc3 parser (chatlog_030826.md — raw format, no speaker labels) ───────────

def parse_doc3(raw_path: Path) -> tuple[list[dict], dict]:
    """
    Parse chatlog_030826.md into turns using timestamp-based segmentation.

    Structure: [Jake text] -> TIMESTAMP -> [thinking block] -> Done? -> [Opus response]
    After "Done" in thinking block -> full Opus response follows.
    Without "Done" -> Opus response starts after thinking summaries.

    Date assignment: PM timestamps -> "Mar 8", AM timestamps -> "Mar 9".
    """
    raw_lines = raw_path.read_text(encoding='utf-8').splitlines()
    lines = [l.rstrip() for l in raw_lines]
    lines = collapse_consecutive_dupes(lines)
    print(f"[DOC3] {len(raw_lines)} raw lines -> {len(lines)} after dedup")

    def ts_to_date(ts: str) -> str:
        """Convert timestamp like '5:09 PM' -> 'Mar 8', '12:05 AM' -> 'Mar 9'."""
        return 'Mar 9' if ts.endswith('AM') else 'Mar 8'

    # Split into blocks by timestamp position
    # Each block: [start_idx, end_idx, timestamp_str]
    timestamp_positions = []
    for idx, line in enumerate(lines):
        if _TIMESTAMP_PAT.match(line.strip()):
            timestamp_positions.append((idx, line.strip()))
    print(f"[DOC3] Found {len(timestamp_positions)} timestamps")

    turns = []
    ambiguous_flags = []
    turn_number = 0

    # Content before first timestamp = Jake turn 0
    if timestamp_positions:
        first_ts_idx = timestamp_positions[0][0]
        jake_lines_0 = [lines[j].strip() for j in range(first_ts_idx)
                        if lines[j].strip() and not is_artifact(lines[j].strip())]
        jake_text_0 = ' '.join(
            p for p in jake_lines_0 if p and not is_thinking_summary(p)
        ).strip()
        if jake_text_0:
            turns.append({
                'turn':       turn_number,
                'speaker':    'Jake',
                'timestamp':  None,
                'date':       'Mar 8',
                'date_index': -1,
                'content':    jake_text_0,
                'word_count': len(jake_text_0.split()),
                'source':     'doc3',
                'ambiguous':  False,
            })
            turn_number += 1

    # Process each timestamp block
    for block_idx, (ts_idx, ts_str) in enumerate(timestamp_positions):
        ts_date = ts_to_date(ts_str)

        # Block end: start of next timestamp (or end of file)
        if block_idx + 1 < len(timestamp_positions):
            block_end = timestamp_positions[block_idx + 1][0]
            next_ts_str = timestamp_positions[block_idx + 1][1]
        else:
            block_end = len(lines)
            next_ts_str = None

        block_lines = lines[ts_idx + 1 : block_end]

        # Find LAST "Done" within the block (multi-tool blocks have multiple Done markers)
        done_idx = None
        for j, bl in enumerate(block_lines):
            if bl.strip() == 'Done':
                done_idx = j  # keep scanning, last one wins

        if done_idx is not None:
            # Case A: has Done marker -> Opus response starts after the LAST Done
            opus_raw = block_lines[done_idx + 1:]
        else:
            # Case B: no Done -> skip thinking summaries, rest is Opus response
            # Skip leading thinking summaries and artifacts
            start_opus = 0
            for j, bl in enumerate(block_lines):
                stripped = bl.strip()
                if not stripped:
                    continue
                if is_artifact(stripped) or is_thinking_summary(stripped):
                    start_opus = j + 1
                    continue
                # First line that isn't an artifact or thinking summary = start of Opus text
                start_opus = j
                break
            opus_raw = block_lines[start_opus:]

        # Collect Opus content: strip artifacts and thinking summaries; detect Jake message at end
        # Strategy: find LAST file-ref position in opus_raw, split there.
        # Everything before last file ref (minus artifacts/thinking) = Opus content.
        # Everything after last file ref = Jake's next message.

        # First pass: find index of last artifact line in opus_raw
        last_artifact_idx = None
        for j, bl in enumerate(opus_raw):
            if is_artifact(bl.strip()):
                last_artifact_idx = j

        found_file_ref_separator = last_artifact_idx is not None
        opus_raw_before = opus_raw[:last_artifact_idx] if last_artifact_idx is not None else opus_raw
        opus_raw_after  = opus_raw[last_artifact_idx + 1:] if last_artifact_idx is not None else []

        opus_content_lines = []
        jake_content_lines = []
        post_ref_lines = []

        for bl in opus_raw_before:
            stripped = bl.strip()
            if not stripped:
                if opus_content_lines:
                    opus_content_lines.append('')
                continue
            if is_artifact(stripped) or is_thinking_summary(stripped):
                continue
            opus_content_lines.append(stripped)

        for bl in opus_raw_after:
            stripped = bl.strip()
            if not stripped:
                continue
            if is_artifact(stripped) or is_thinking_summary(stripped):
                continue
            post_ref_lines.append(stripped)

        # post_ref_lines after last file ref = Jake's next message
        if post_ref_lines:
            jake_content_lines = post_ref_lines
        elif next_ts_str is not None and not found_file_ref_separator:
            # No file-ref separator: the last short run of lines before the next timestamp
            # might be Jake's message. Heuristic: if last N lines are short and conversational,
            # extract them as Jake's message.
            if opus_content_lines:
                # Find last non-blank line run
                last_run = []
                tmp = list(reversed(opus_content_lines))
                for line in tmp:
                    if line == '':
                        break
                    last_run.append(line)
                last_run = list(reversed(last_run))
                last_run_text = ' '.join(last_run)
                last_run_wc = len(last_run_text.split())
                # If last run is short (<= 60 words) and not multi-sentence Opus-style,
                # extract as Jake's message
                if last_run_wc <= 60:
                    # Remove last_run from opus_content_lines
                    # Find the boundary
                    n_to_remove = len(last_run) + 1  # +1 for the blank separator
                    for _ in range(n_to_remove):
                        if opus_content_lines:
                            opus_content_lines.pop()
                    jake_content_lines = last_run
                    ambiguous_flags.append(turn_number + 1)  # flag the Jake turn

        # Build Opus turn
        # Re-join paragraph blocks
        opus_paras = []
        current_para = []
        for ln in opus_content_lines:
            if ln == '':
                if current_para:
                    opus_paras.append(' '.join(current_para))
                    current_para = []
            else:
                current_para.append(ln)
        if current_para:
            opus_paras.append(' '.join(current_para))

        opus_text = '\n\n'.join(p for p in opus_paras if p).strip()

        if opus_text:
            turns.append({
                'turn':       turn_number,
                'speaker':    'Opus',
                'timestamp':  ts_str,
                'date':       ts_date,
                'date_index': -1,
                'content':    opus_text,
                'word_count': len(opus_text.split()),
                'source':     'doc3',
                'ambiguous':  False,
            })
            turn_number += 1

        # Build Jake turn (content for NEXT exchange)
        if next_ts_str is not None:
            jake_text = ' '.join(jake_content_lines).strip()
            if not jake_text:
                # No explicit Jake content found — check if next block starts with Jake lines
                # before the timestamp. These are in the NEXT block's "before timestamp" section.
                # Will be handled when processing next block.
                pass
            else:
                turns.append({
                    'turn':       turn_number,
                    'speaker':    'Jake',
                    'timestamp':  None,
                    'date':       ts_to_date(next_ts_str),
                    'date_index': -1,
                    'content':    jake_text,
                    'word_count': len(jake_text.split()),
                    'source':     'doc3',
                    'ambiguous':  turn_number in ambiguous_flags,
                })
                turn_number += 1

    # Final Jake message (after last Opus turn if any content remains)
    # (already handled above via post_ref_lines)

    # Date index assignment for doc3
    doc3_dates = ['Mar 8', 'Mar 9']
    for t in turns:
        t['date_index'] = doc3_dates.index(t['date']) if t['date'] in doc3_dates else -1

    opus_n = sum(1 for t in turns if t['speaker'] == 'Opus')
    jake_n = sum(1 for t in turns if t['speaker'] == 'Jake')
    amb_n  = sum(1 for t in turns if t.get('ambiguous'))
    print(f"[DOC3] Extracted {len(turns)} turns: Opus={opus_n}, Jake={jake_n}, ambiguous={amb_n}")

    parse_info = {
        'source':          'chatlog_030826.md',
        'total_turns':     len(turns),
        'opus_turns':      opus_n,
        'jake_turns':      jake_n,
        'ambiguous_turns': amb_n,
        'ambiguous_ids':   ambiguous_flags,
        'dates':           doc3_dates,
    }
    return turns, parse_info


def phase_1_parse():
    """Parse Doc2 and Doc3, save to V2 staging files."""
    print("\n=== PHASE 1: PARSE ===")
    V2.mkdir(parents=True, exist_ok=True)

    doc2_path = V2 / "doc2_turns.json"
    doc3_path = V2 / "doc3_turns.json"
    parse_info = {}

    if not DOC2_MD.exists():
        print(f"[PHASE1] WARNING: Doc2 not found at {DOC2_MD}")
        doc2_turns = []
        parse_info['doc2'] = {'error': 'file not found'}
    else:
        doc2_turns, pi2 = parse_doc2(DOC2_MD)
        parse_info['doc2'] = pi2
        with open(doc2_path, 'w', encoding='utf-8') as f:
            json.dump(doc2_turns, f, ensure_ascii=False, indent=2)
        print(f"[PHASE1] Doc2 saved: {doc2_path}")

    if not DOC3_RAW.exists():
        print(f"[PHASE1] WARNING: Doc3 not found at {DOC3_RAW}")
        doc3_turns = []
        parse_info['doc3'] = {'error': 'file not found'}
    else:
        doc3_turns, pi3 = parse_doc3(DOC3_RAW)
        parse_info['doc3'] = pi3
        with open(doc3_path, 'w', encoding='utf-8') as f:
            json.dump(doc3_turns, f, ensure_ascii=False, indent=2)
        print(f"[PHASE1] Doc3 saved: {doc3_path}")

    # Save parse report
    with open(PARSE_RPT_JSON, 'w', encoding='utf-8') as f:
        json.dump(parse_info, f, ensure_ascii=False, indent=2)
    print(f"[PHASE1] Parse report: {PARSE_RPT_JSON}")

    return doc2_turns, doc3_turns, parse_info


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: Stitch
# ═══════════════════════════════════════════════════════════════════════════════

def phase_2_stitch(doc2_turns=None, doc3_turns=None):
    """
    Stitch Doc1 + Doc2 + Doc3:
      - Doc1 turns 0-1913 (pre-overlap)
      - Doc2 all turns (replaces Doc1 turns 1914+)
      - Doc3 all turns (new content)
    """
    print("\n=== PHASE 2: STITCH ===")

    # Load Doc1
    print(f"[STITCH] Loading Doc1: {DOC1_TURNS}")
    with open(DOC1_TURNS, encoding='utf-8') as f:
        doc1_turns = json.load(f)
    print(f"[STITCH] Doc1: {len(doc1_turns)} turns")

    # Load Doc2 if not passed
    doc2_path = V2 / "doc2_turns.json"
    if doc2_turns is None:
        with open(doc2_path, encoding='utf-8') as f:
            doc2_turns = json.load(f)
    print(f"[STITCH] Doc2: {len(doc2_turns)} turns")

    # Load Doc3 if not passed
    doc3_path = V2 / "doc3_turns.json"
    if doc3_turns is None:
        with open(doc3_path, encoding='utf-8') as f:
            doc3_turns = json.load(f)
    print(f"[STITCH] Doc3: {len(doc3_turns)} turns")

    # Find stitch point in Doc1: turn 1914 is where Doc2 starts
    # (verified: Doc1[1914] = Doc2[0] = "That reframe changes everything...")
    DOC1_STITCH_POINT = 1914
    doc1_pre = doc1_turns[:DOC1_STITCH_POINT]
    doc1_replaced = doc1_turns[DOC1_STITCH_POINT:]

    print(f"[STITCH] Doc1 pre-stitch: {len(doc1_pre)} turns (0-{DOC1_STITCH_POINT-1})")
    print(f"[STITCH] Doc1 replaced: {len(doc1_replaced)} turns ({DOC1_STITCH_POINT}-{len(doc1_turns)-1})")
    print(f"[STITCH] Doc2 replacement: {len(doc2_turns)} turns")
    print(f"[STITCH] Doc3 extension: {len(doc3_turns)} turns")

    # Build unified date order
    # Doc1 dates (existing)
    doc1_date_order = list(dict.fromkeys(
        t['date'] for t in doc1_turns if t['date'] != 'unknown'
    ))
    # Add Doc2 and Doc3 dates that aren't in Doc1
    all_new_dates = []
    for t in doc2_turns + doc3_turns:
        d = t.get('date', 'unknown')
        if d and d != 'unknown' and d not in doc1_date_order and d not in all_new_dates:
            all_new_dates.append(d)
    # Sort by calendar (rough)
    full_date_order = doc1_date_order + sorted(all_new_dates, key=lambda d: (
        ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].index(d.split()[0]),
        int(d.split()[1])
    ))
    print(f"[STITCH] Unified date order: {full_date_order}")

    # Assemble stitched turns
    combined = []
    new_turn = 0

    for t in doc1_pre:
        ct = dict(t)
        ct['turn'] = new_turn
        ct['source'] = ct.get('source', 'doc1')
        ct['date_index'] = full_date_order.index(ct['date']) if ct['date'] in full_date_order else -1
        combined.append(ct)
        new_turn += 1

    for t in doc2_turns:
        ct = dict(t)
        ct['turn'] = new_turn
        ct['source'] = 'doc2'
        ct['date_index'] = full_date_order.index(ct['date']) if ct['date'] in full_date_order else -1
        combined.append(ct)
        new_turn += 1

    for t in doc3_turns:
        ct = dict(t)
        ct['turn'] = new_turn
        ct['source'] = 'doc3'
        ct['date_index'] = full_date_order.index(ct['date']) if ct['date'] in full_date_order else -1
        combined.append(ct)
        new_turn += 1

    # Write stitched turns
    with open(ALL_TURNS_JSON, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"[STITCH] Stitched turns saved: {ALL_TURNS_JSON} ({len(combined)} turns)")

    # Stitch report
    by_source = defaultdict(int)
    for t in combined:
        by_source[t['source']] += 1

    stitch_report = {
        'total_turns': len(combined),
        'doc1_pre_turns': len(doc1_pre),
        'doc1_replaced_turns': len(doc1_replaced),
        'doc2_turns': len(doc2_turns),
        'doc3_turns': len(doc3_turns),
        'stitch_point_doc1': DOC1_STITCH_POINT,
        'by_source': dict(by_source),
        'date_order': full_date_order,
        'opus_total': sum(1 for t in combined if t['speaker'] == 'Opus'),
        'jake_total': sum(1 for t in combined if t['speaker'] == 'Jake'),
    }
    with open(STITCH_RPT_JSON, 'w', encoding='utf-8') as f:
        json.dump(stitch_report, f, ensure_ascii=False, indent=2)
    print(f"[STITCH] Stitch report: {STITCH_RPT_JSON}")
    print(f"[STITCH] Total: {len(combined)} turns "
          f"(doc1={by_source['doc1']}, doc2={by_source['doc2']}, doc3={by_source['doc3']})")

    return combined


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: Chunk Splitting
# ═══════════════════════════════════════════════════════════════════════════════

def _count_words(text: str) -> int:
    return len(text.split())


def _split_into_paragraphs(text: str) -> list[str]:
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if len(paras) > 1:
        return paras
    paras = [p.strip() for p in text.split('\n') if p.strip()]
    if len(paras) > 1:
        return paras
    return [text.strip()]


def _chunk_turn(turn: dict) -> list[dict]:
    text = turn.get('content', '').strip()
    wc = _count_words(text)

    def make_chunk(txt, cidx, total):
        return {
            'chunk_id':             None,
            'turn_id':              turn['turn'],
            'speaker':              turn['speaker'],
            'date':                 turn.get('date', 'unknown'),
            'date_index':           turn.get('date_index', -1),
            'source':               turn.get('source', 'doc1'),
            'word_count':           _count_words(txt),
            'text':                 txt,
            'chunk_within_turn':    cidx,
            'total_chunks_in_turn': total,
        }

    if wc < MIN_WORDS:
        return [make_chunk(text, 0, 1)]

    paragraphs = _split_into_paragraphs(text)
    raw_chunks = []
    current_parts = []
    current_wc = 0

    for para in paragraphs:
        para_wc = _count_words(para)
        if current_wc + para_wc > MAX_WORDS and current_wc >= MIN_WORDS:
            raw_chunks.append(' '.join(current_parts))
            current_parts = [para]
            current_wc = para_wc
        else:
            current_parts.append(para)
            current_wc += para_wc
        if current_wc >= TARGET_WORDS:
            raw_chunks.append(' '.join(current_parts))
            current_parts = []
            current_wc = 0

    if current_parts:
        remainder = ' '.join(current_parts)
        if _count_words(remainder) < 40 and raw_chunks:
            raw_chunks[-1] = raw_chunks[-1] + ' ' + remainder
        else:
            raw_chunks.append(remainder)

    total = len(raw_chunks)
    return [make_chunk(ct, idx, total) for idx, ct in enumerate(raw_chunks)]


def phase_3_chunk(turns=None):
    """Split stitched turns into ~150-word chunks."""
    print("\n=== PHASE 3: CHUNK ===")

    if turns is None:
        with open(ALL_TURNS_JSON, encoding='utf-8') as f:
            turns = json.load(f)
    print(f"[CHUNK] {len(turns)} turns loaded")

    all_chunks = []
    for turn in turns:
        all_chunks.extend(_chunk_turn(turn))

    for i, c in enumerate(all_chunks):
        c['chunk_id'] = i

    with open(CHUNKS_JSON, 'w', encoding='utf-8') as f:
        json.dump({'chunks': all_chunks}, f, ensure_ascii=False, indent=2)

    kb = CHUNKS_JSON.stat().st_size // 1024
    opus_n = sum(1 for c in all_chunks if c['speaker'] == 'Opus')
    jake_n = sum(1 for c in all_chunks if c['speaker'] == 'Jake')
    print(f"[CHUNK] {len(all_chunks)} chunks "
          f"(Opus={opus_n}, Jake={jake_n}) -> {CHUNKS_JSON} ({kb} KB)")

    return all_chunks


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: Embedding
# ═══════════════════════════════════════════════════════════════════════════════

def get_embeddings_batch(texts: list[str], retries: int = 3) -> list[np.ndarray]:
    """Batch-embed texts via LM Studio API. Returns list of unit-normalized 768-dim vectors."""
    truncated = [t[:MAX_CHARS] if len(t) > MAX_CHARS else t for t in texts]
    for attempt in range(retries):
        try:
            resp = requests.post(
                EMBED_URL,
                json={"model": EMBED_MODEL, "input": truncated},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            data.sort(key=lambda x: x["index"])
            vecs = []
            for item in data:
                v = np.array(item["embedding"], dtype=np.float32)
                norm = np.linalg.norm(v)
                if norm > 1e-9:
                    v /= norm
                vecs.append(v)
            return vecs
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"[EMBED] Retry {attempt+1}/{retries} after {wait}s: {e}")
                time.sleep(wait)
            else:
                raise


def phase_4_embed(chunks=None):
    """Embed all chunks, saving checkpoint every CHECKPOINT_EVERY batches."""
    print("\n=== PHASE 4: EMBED ===")

    if chunks is None:
        with open(CHUNKS_JSON, encoding='utf-8') as f:
            chunks = json.load(f)['chunks']
    n = len(chunks)
    print(f"[EMBED] {n} chunks to embed")

    # Resume from checkpoint if available
    start_idx = 0
    embeddings = np.zeros((n, 768), dtype=np.float32)
    if EMBED_PART_NPY.exists():
        part = np.load(str(EMBED_PART_NPY))
        completed = int(part.shape[0])
        if completed > 0 and completed <= n:
            embeddings[:completed] = part[:completed]
            start_idx = completed
            print(f"[EMBED] Resuming from checkpoint at chunk {start_idx}")

    texts = [c['text'] for c in chunks]

    batch_idx = 0
    for i in range(start_idx, n, BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        vecs = get_embeddings_batch(batch_texts)
        for j, v in enumerate(vecs):
            if i + j < n:
                embeddings[i + j] = v

        batch_idx += 1
        if batch_idx % 10 == 0:
            pct = min(100, 100 * (i + BATCH_SIZE) / n)
            print(f"[EMBED] {i + BATCH_SIZE}/{n} ({pct:.0f}%)")

        # Checkpoint every CHECKPOINT_EVERY batches
        if batch_idx % (CHECKPOINT_EVERY // BATCH_SIZE + 1) == 0:
            np.save(str(EMBED_PART_NPY), embeddings[:i + BATCH_SIZE])

    np.save(str(EMBED_NPY), embeddings)
    if EMBED_PART_NPY.exists():
        EMBED_PART_NPY.unlink()

    print(f"[EMBED] Saved: {EMBED_NPY} shape={embeddings.shape}")
    return embeddings


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: Detrend + 5-Channel Projection
# ═══════════════════════════════════════════════════════════════════════════════

def phase_5_process(chunks=None, embeddings=None):
    """
    5a. Detrend: per-session linear regression of embedding vs position, subtract trend.
    5b. 5-channel: project each 768-dim embedding onto 5 domain centroids.
    """
    print("\n=== PHASE 5: DETREND + 5-CHANNEL ===")

    if chunks is None:
        with open(CHUNKS_JSON, encoding='utf-8') as f:
            chunks = json.load(f)['chunks']

    if embeddings is None:
        embeddings = np.load(str(EMBED_NPY))

    n = len(chunks)
    print(f"[PROCESS] {n} chunks, embeddings shape={embeddings.shape}")

    # ── 5a: Detrend ───────────────────────────────────────────────────────────
    detrended = embeddings.copy()
    date_groups = defaultdict(list)
    for i, c in enumerate(chunks):
        date_groups[c['date']].append(i)

    for date, idxs in sorted(date_groups.items()):
        if len(idxs) < 3:
            continue  # Not enough points to fit a trend
        positions = np.arange(len(idxs), dtype=np.float32)
        E = embeddings[idxs]  # (N_session × 768)

        # Per-dimension linear regression using numpy polyfit
        # For efficiency: fit all 768 dims at once via matrix formulation
        # positions is 1D predictor; solve least-squares for each dimension
        X = np.column_stack([positions, np.ones_like(positions)])  # (N, 2)
        # W = (X^T X)^{-1} X^T E  -> shape (2, 768)
        W, _, _, _ = np.linalg.lstsq(X, E, rcond=None)
        trend = X @ W  # (N, 768)
        for local_i, global_i in enumerate(idxs):
            detrended[global_i] = E[local_i] - trend[local_i]

    # Verify detrending preserves signal
    # Metric: fraction of variance preserved across embeddings
    total_var_raw = float(np.var(embeddings))
    total_var_det = float(np.var(detrended))
    var_preserved = total_var_det / total_var_raw if total_var_raw > 1e-12 else 1.0
    # Also compute per-session mean cosine similarity between raw and detrended
    per_session_cos = []
    for date, idxs in sorted(date_groups.items()):
        if len(idxs) < 2:
            continue
        raw_s = embeddings[idxs]
        det_s = detrended[idxs]
        # mean cosine similarity between matching pairs
        dot = np.sum(raw_s * det_s, axis=1)
        norm_raw = np.linalg.norm(raw_s, axis=1)
        norm_det = np.linalg.norm(det_s, axis=1)
        cos = dot / np.where(norm_raw * norm_det > 1e-12, norm_raw * norm_det, 1.0)
        per_session_cos.append(float(np.mean(cos)))
    mean_cos = float(np.mean(per_session_cos)) if per_session_cos else 0.0
    print(f"[PROCESS] Detrending variance preserved: {var_preserved:.4f}")
    print(f"[PROCESS] Detrending mean per-session cosine similarity: {mean_cos:.4f}")
    if mean_cos < 0.85:
        print("[PROCESS] WARNING: mean cosine < 0.85 — detrending may be too aggressive")

    np.save(str(DETRENDED_NPY), detrended.astype(np.float32))
    print(f"[PROCESS] Detrended saved: {DETRENDED_NPY}")

    # ── 5b: 5-channel projection ───────────────────────────────────────────────
    print(f"[PROCESS] Loading centroids: {CENTROIDS_768}")
    with open(CENTROIDS_768, encoding='utf-8') as f:
        centroids_data = json.load(f)

    # centroids_768.json structure: {"layer": "nomic_768", "centroids": {domain: [768-dim vector]}}
    centroid_dict = centroids_data.get('centroids', centroids_data)  # handle both flat and nested
    domain_names = [d for d in centroid_dict.keys() if isinstance(centroid_dict[d], list)]
    centroid_matrix = np.array([centroid_dict[d] for d in domain_names], dtype=np.float32)
    # Normalize centroids
    norms = np.linalg.norm(centroid_matrix, axis=1, keepdims=True)
    centroid_matrix = centroid_matrix / np.where(norms > 1e-9, norms, 1.0)

    # Cosine similarity: E @ C^T  (N × 5)
    sims = embeddings @ centroid_matrix.T  # (N, 5)

    channel5_records = []
    for i, c in enumerate(chunks):
        channels = {d: float(sims[i, j]) for j, d in enumerate(domain_names)}
        channel5_records.append({
            'chunk_id':  c['chunk_id'],
            'turn_id':   c['turn_id'],
            'speaker':   c['speaker'],
            'date':      c['date'],
            'channels':  channels,
        })

    with open(CHANNEL5_JSON, 'w', encoding='utf-8') as f:
        json.dump({'chunks': channel5_records}, f, ensure_ascii=False, indent=2)
    print(f"[PROCESS] 5-channel saved: {CHANNEL5_JSON} ({len(channel5_records)} records)")

    # Sanity check: no channel consistently zero or saturated
    for j, d in enumerate(domain_names):
        col = sims[:, j]
        print(f"[PROCESS]   {d}: mean={col.mean():.3f}, std={col.std():.3f}, "
              f"min={col.min():.3f}, max={col.max():.3f}")

    return detrended, channel5_records


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6: Joint UMAP
# ═══════════════════════════════════════════════════════════════════════════════

def phase_6_umap(chunks=None, embeddings=None):
    """Run joint 3D UMAP on all V2 chunks + corpus documents."""
    print("\n=== PHASE 6: UMAP ===")

    try:
        import umap
    except ImportError:
        print("[UMAP] ERROR: umap-learn not installed. Run: pip install umap-learn")
        return None

    if chunks is None:
        with open(CHUNKS_JSON, encoding='utf-8') as f:
            chunks = json.load(f)['chunks']

    if embeddings is None:
        embeddings = np.load(str(EMBED_NPY))

    n_chunks = len(chunks)
    print(f"[UMAP] {n_chunks} chunk embeddings")

    # Load corpus embeddings if available
    corpus_embeddings = None
    corpus_labels = []
    if CORPUS_EMBEDDINGS.exists():
        corpus_embeddings = np.load(str(CORPUS_EMBEDDINGS)).astype(np.float32)
        print(f"[UMAP] Corpus embeddings: {corpus_embeddings.shape}")

        # Load corpus metadata for labels
        corpus_meta_path = DATA / "corpus_metadata.json"
        if corpus_meta_path.exists():
            with open(corpus_meta_path, encoding='utf-8') as f:
                meta = json.load(f)
            corpus_labels = [m.get('filename', f'corpus_{i}') for i, m in enumerate(meta)]
        else:
            corpus_labels = [f'corpus_{i}' for i in range(len(corpus_embeddings))]

    # Combine chunk + corpus embeddings
    if corpus_embeddings is not None:
        n_corpus = len(corpus_embeddings)
        all_embeddings = np.vstack([embeddings, corpus_embeddings])
        print(f"[UMAP] Combined: {len(all_embeddings)} total points")
    else:
        all_embeddings = embeddings
        n_corpus = 0
        print("[UMAP] No corpus embeddings found — UMAP on chunks only")

    # Run UMAP
    print("[UMAP] Fitting UMAP (n_neighbors=15, min_dist=0.1, 3D, cosine)...")
    reducer = umap.UMAP(
        n_components=3,
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine',
        random_state=42,
    )
    coords_3d = reducer.fit_transform(all_embeddings)
    print(f"[UMAP] Done. Coordinates shape: {coords_3d.shape}")

    # Build output JSON
    umap_records = []

    # Chunk records
    for i, c in enumerate(chunks):
        umap_records.append({
            'type':     'chunk',
            'chunk_id': c['chunk_id'],
            'turn_id':  c['turn_id'],
            'speaker':  c['speaker'],
            'date':     c['date'],
            'source':   c.get('source', 'doc1'),
            'x': float(coords_3d[i, 0]),
            'y': float(coords_3d[i, 1]),
            'z': float(coords_3d[i, 2]),
        })

    # Corpus records
    for i in range(n_corpus):
        j = n_chunks + i
        label = corpus_labels[i] if i < len(corpus_labels) else f'corpus_{i}'
        umap_records.append({
            'type':     'corpus',
            'doc_id':   i,
            'label':    label,
            'x': float(coords_3d[j, 0]),
            'y': float(coords_3d[j, 1]),
            'z': float(coords_3d[j, 2]),
        })

    with open(UMAP_JSON, 'w', encoding='utf-8') as f:
        json.dump({'points': umap_records}, f, ensure_ascii=False, indent=2)
    print(f"[UMAP] Saved: {UMAP_JSON} ({len(umap_records)} points)")

    return coords_3d


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def run_validation():
    """Post-pipeline validation checks."""
    print("\n=== VALIDATION ===")
    ok = True

    if CHUNKS_JSON.exists():
        with open(CHUNKS_JSON, encoding='utf-8') as f:
            chunks = json.load(f)['chunks']
        n = len(chunks)
        print(f"[VAL] Total chunks: {n}")
        if 5000 <= n <= 8000:
            print(f"[VAL] ✓ Chunk count in expected range (5000-8000)")
        else:
            print(f"[VAL] ⚠ Chunk count {n} outside expected range (5000-8000)")

    if EMBED_NPY.exists() and DETRENDED_NPY.exists():
        raw = np.load(str(EMBED_NPY))
        det = np.load(str(DETRENDED_NPY))
        corr = float(np.corrcoef(raw.flatten()[:100000], det.flatten()[:100000])[0, 1])
        print(f"[VAL] Detrending correlation: {corr:.4f}")
        if corr >= 0.95:
            print("[VAL] ✓ Detrending within acceptable range")
        else:
            print(f"[VAL] ⚠ Detrending correlation {corr:.4f} < 0.95")
            ok = False

    if CHANNEL5_JSON.exists():
        with open(CHANNEL5_JSON, encoding='utf-8') as f:
            ch5 = json.load(f)['chunks']
        domains = list(ch5[0]['channels'].keys()) if ch5 else []
        print(f"[VAL] 5-channel domains: {domains}")
        for d in domains:
            vals = [c['channels'][d] for c in ch5]
            mn, mx, std = min(vals), max(vals), float(np.std(vals))
            zero_count = sum(1 for v in vals if abs(v) < 0.01)
            sat_count  = sum(1 for v in vals if v > 0.99)
            if zero_count > len(vals) * 0.5:
                print(f"[VAL] ⚠ Channel '{d}' mostly zero ({zero_count}/{len(vals)})")
                ok = False
            elif sat_count > len(vals) * 0.5:
                print(f"[VAL] ⚠ Channel '{d}' mostly saturated ({sat_count}/{len(vals)})")
                ok = False
            else:
                print(f"[VAL] ✓ Channel '{d}': mean={np.mean(vals):.3f}, std={std:.3f}")

    if UMAP_JSON.exists():
        with open(UMAP_JSON, encoding='utf-8') as f:
            pts = json.load(f)['points']
        corpus_pts = [p for p in pts if p['type'] == 'corpus']
        chunk_pts  = [p for p in pts if p['type'] == 'chunk']
        print(f"[VAL] UMAP: {len(chunk_pts)} chunk points + {len(corpus_pts)} corpus points")
        if corpus_pts:
            print("[VAL] ✓ Corpus documents present in UMAP")

    return ok


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="V2 pipeline: parse->stitch->chunk->embed->process->umap")
    parser.add_argument('--phase', type=int, default=0,
                        help="Run specific phase (1-6). 0 = run all phases.")
    parser.add_argument('--skip-embed', action='store_true',
                        help="Skip embedding phase (use existing .npy)")
    args = parser.parse_args()

    V2.mkdir(parents=True, exist_ok=True)

    run_all = args.phase == 0

    doc2_turns = doc3_turns = turns = chunks = embeddings = None

    if run_all or args.phase == 1:
        doc2_turns, doc3_turns, _ = phase_1_parse()

    if run_all or args.phase == 2:
        turns = phase_2_stitch(doc2_turns, doc3_turns)

    if run_all or args.phase == 3:
        chunks = phase_3_chunk(turns)

    if (run_all or args.phase == 4) and not args.skip_embed:
        embeddings = phase_4_embed(chunks)
    elif run_all and EMBED_NPY.exists():
        print(f"\n[PHASE 4] Skipped — {EMBED_NPY} exists")
        embeddings = np.load(str(EMBED_NPY))

    if run_all or args.phase == 5:
        phase_5_process(chunks, embeddings)

    if run_all or args.phase == 6:
        phase_6_umap(chunks, embeddings)

    if run_all:
        run_validation()

    print("\n=== V2 PIPELINE COMPLETE ===")
    for f in [CHUNKS_JSON, EMBED_NPY, DETRENDED_NPY, CHANNEL5_JSON,
              UMAP_JSON, STITCH_RPT_JSON, PARSE_RPT_JSON]:
        if f.exists():
            kb = f.stat().st_size // 1024
            print(f"  {f.name:<40} {kb:6d} KB")
        else:
            print(f"  {f.name:<40} (not found)")

    return 0


if __name__ == '__main__':
    sys.exit(main())
