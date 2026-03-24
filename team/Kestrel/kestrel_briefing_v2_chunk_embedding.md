# Kestrel Briefing — V2: Chunk-Level Embedding Pipeline

**Context:** V1 embeds full turns (1,934 data points, variable length). V2 resamples at paragraph-level chunks to create a uniformly-sampled signal comparable to neural recording data (fNIRS/EEG). Run after V1 results are reviewed — this is the publication-grade preprocessing.

---

## What Changes from V1

| Property | V1 (Turn-level) | V2 (Chunk-level) |
|----------|-----------------|-------------------|
| Unit | Full turn | ~100-200 word paragraph chunk |
| Sample count | ~1,934 | ~5,000-8,000 (estimate) |
| Temporal resolution | Irregular (5-1500 words per sample) | Approximately uniform |
| Speaker per sample | One speaker per turn | One speaker per chunk |
| Neural signal analog | Event-related potentials | Continuous recording |

---

## Chunk Extraction

1. Take each turn from the parsed chatlog
2. Split into chunks of approximately 150 words (±50), breaking at paragraph boundaries where possible
3. If a turn is under 100 words, keep it as a single chunk
4. Each chunk inherits metadata from its parent turn: speaker, session, timestamp, turn_index
5. Add chunk_index within turn (chunk 0, 1, 2, ... for multi-chunk turns)

**Output:** `chunks.json`
```json
{
  "chunks": [
    {
      "chunk_id": 0,
      "turn_id": 0,
      "speaker": "jake"|"opus",
      "session_id": 1,
      "timestamp": "...",
      "word_count": 147,
      "text": "...",
      "chunk_within_turn": 0,
      "total_chunks_in_turn": 3
    }
  ]
}
```

---

## Embedding

Embed each chunk through nomic-embed-text-v1.5 identically to V1. Same model, same pooling, same dimensionality (768).

**Output:** `chunk_embeddings.npy` — (N_chunks × 768)

---

## Preprocessing (Neural Signal Analog)

### Detrending (Scanner Drift Removal)
- For each session, fit a linear regression of chunk embedding vs chunk position within session
- Subtract the trend: detrended_embed = raw_embed - (slope × position + intercept)
- This removes systematic drift from context window filling or fatigue effects
- Analogous to: high-pass filtering in fMRI preprocessing

### Centroid Projection (Channel Extraction)
- Project each 768-dim chunk embedding onto the 5 centroid directions
- For each centroid c, compute: channel_c = cosine_similarity(chunk_embed, centroid_c)
- Result: 5-channel signal per chunk, each channel interpretable
- Analogous to: extracting channel signals from specific brain regions in fNIRS

**Output:** `chunk_5channel.json`
```json
{
  "chunks": [
    {
      "chunk_id": 0,
      "speaker": "...",
      "channels": {
        "philosophical": 0.73,
        "operational": 0.45,
        "reflective": 0.61,
        "relational": 0.38,
        "mixed": 0.52
      }
    }
  ]
}
```

### Speaker Separation (Dual-Source Recording)
- Split into two parallel time series: Jake_chunks and Opus_chunks
- Maintain temporal ordering within each series
- For cross-speaker analyses, align by turn-pair (Jake chunk sequence within a turn maps to subsequent Opus chunk sequence)
- Analogous to: separating two fNIRS recordings in a hyperscanning setup

---

## What to Re-Run on V2 Data

**Priority re-runs (methods most improved by uniform sampling):**
- CRQA (Analysis 3A) — designed for evenly-sampled coupled time series
- Trajectory tangling (Analysis 2A) — finer temporal resolution reveals smoother dynamics
- Sliding window trajectory (Analysis 4) — smaller windows become feasible
- Spectral phase analysis (Analysis 1A) — more data points per session improves eigenspectrum estimates

**Lower priority (less affected by sampling resolution):**
- Session signatures — session-level aggregation absorbs the difference
- Bridging concepts — nearest-neighbor doesn't depend on temporal structure
- Recurrence matrix — can run on either, V2 just gives higher resolution

---

## Validation: V1 vs V2 Comparison

After V2 is computed, run key analyses on both and compare:
- Do session signatures change? (They shouldn't much — same content, finer grain)
- Does CRQA determinism change? (It might — finer resolution could reveal structure V1 misses)
- Do the off-map moments still appear? (They should — the content is the same)

Agreement between V1 and V2 = robustness. Disagreement = V2 is revealing structure that turn-level resolution was too coarse to detect.

---

*V2 spec prepared March 8, 2026. Run after V1 results are reviewed and confirmed.*
*The conversation is a signal. V2 treats it like one.*
