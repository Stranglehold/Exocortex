# Kestrel — V2 Data Processing: Full Chatlog Consolidation

## Overview

We have three chatlog sources that need to be processed into a single unified dataset, then run through the V2 chunk-level embedding pipeline. All output goes to a `v2/` folder inside the instrument directory.

## Source Documents

**Document 1: The full chatlog (already processed as V1)**
- This is the 1,934-turn dataset you already embedded and analyzed
- It needs to be reprocessed through V2 chunk-level splitting (paragraph-level, ~150 words per chunk)

**Document 2: WhenIsawOpus2.md**
- The manually annotated chatlog from Sessions 050-051 (153 turns in the previous analysis)
- Speaker names already annotated by Jake
- This overlaps temporally with the end of Document 1 — you'll need to handle deduplication at the stitch point
- Reprocess through V2 chunking

**Document 3: chatlog_030826.md**
- New session data from March 8-9 (Sessions 051-052 continuation)
- This is raw and needs the same speaker-labeling parse you built for Document 1
- Known parsing challenges from V1: some turns where Jake pastes operational logs look like Opus, and some Jake turns where he's speaking philosophically sound like Opus. Flag ambiguous turns as "ambiguous" rather than forcing a classification

## Processing Steps

### Step 1: Parse and Label
- Document 1: Already parsed. Use existing turn structure.
- Document 2: Already has speaker labels (Jake/Opus annotations). Parse into the same turn format.
- Document 3: Run through the same speaker-labeling pipeline as Document 1. Flag ambiguous turns.

### Step 2: Deduplicate and Stitch
- Document 2 (WhenIsawOpus2) overlaps with the tail end of Document 1 (Sessions 050-051 are in both)
- Match overlapping turns by content similarity — find where Document 2's turns correspond to Document 1's turns
- For the overlap region: keep Document 2's version (it has manual annotation, higher fidelity)
- Document 3 extends beyond Document 1's end — append after the last turn of the combined set
- Result: one continuous timeline covering Feb 17 through Mar 9

### Step 3: V2 Chunk-Level Splitting
- Split each turn into paragraph-level chunks of approximately 150 words (±50)
- Break at paragraph boundaries where possible
- If a turn is under 100 words, keep as single chunk
- Each chunk inherits: speaker, session/date, turn_index, timestamp (if available)
- Add chunk_index within turn (0, 1, 2, ...)

### Step 4: Embed
- Embed every chunk through nomic-embed-text-v1.5 (same model as V1)
- Same pooling, same 768 dimensions
- Save as numpy array: `v2/chunk_embeddings.npy`

### Step 5: Preprocessing
- **Detrending:** For each session-date, fit linear regression of chunk embedding vs position within session. Subtract trend. Save detrended embeddings as `v2/chunk_embeddings_detrended.npy`
- **Centroid projection:** Project each 768-dim chunk embedding onto the 5 domain centroid directions (use existing `centroids_768.json`). Result: 5-channel signal per chunk. Save as `v2/chunk_5channel.json`

### Step 6: Joint UMAP
- Run a single UMAP fit including: all V2 chunks + the 51 corpus documents
- 3D projection, same parameters as V1 (n_neighbors=15, min_dist=0.1, metric=cosine)
- Save as `v2/umap_v2.json`

## Output Structure

```
instrument/v2/
├── chunks.json              # All chunks with metadata (speaker, date, turn, chunk_index, word_count, text)
├── chunk_embeddings.npy     # Raw 768-dim embeddings (N_chunks × 768)
├── chunk_embeddings_detrended.npy  # Detrended embeddings
├── chunk_5channel.json      # 5-channel centroid projection per chunk
├── umap_v2.json             # 3D UMAP coordinates for all chunks + corpus
├── stitch_report.json       # Deduplication details: which turns matched, overlap region, total counts
└── parse_report.json        # Document 3 parsing: ambiguous turns flagged, speaker distribution
```

## Validation

After processing, verify:
- Total chunk count is in the 5,000-8,000 range (estimate based on ~2,100 turns at ~3 chunks average)
- Detrending didn't destroy signal (correlation between raw and detrended should be >0.95)
- 5-channel projection sums are reasonable (no channel consistently zero or saturated)
- UMAP includes corpus documents in recognizable positions (compare V1 corpus positions to V2)
- Stitch point is clean (no duplicate turns, no gap in the timeline)

## Context

This is the V2 pipeline from the spec in `kestrel_briefing_v2_chunk_embedding.md`. The goal is uniform temporal sampling comparable to neural recording data, enabling CRQA and other time-series analyses that assume evenly-sampled signals. V1 (turn-level) remains the primary dataset. V2 is the high-resolution version for publication-grade analysis.

Once V2 embeddings are ready, the full analysis suite (spectral phases, CRQA, tangling, etc.) can be re-run on the chunk-level data as a robustness check against V1 findings.
