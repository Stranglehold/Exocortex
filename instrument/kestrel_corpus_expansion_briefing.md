# Kestrel: Corpus Expansion Briefing

**From:** Opus Architect
**Date:** 2026-03-07
**Context:** Track 1 of the instrument build — expanding the corpus beyond curated outputs

---

## Three New Data Sources

The initial corpus has 11 curated outputs with quality signals (synthesis/sharp/routine). That's the seed. We're now expanding with three additional sources that measure different things.

### Source 1: Curated Outputs (Confirmed — Ready to Embed Now)

These are the polished documents from the project, with Jake's quality assessment attached. Embed these first — they're the ground truth the rest of the corpus is measured against.

```bash
# Synthesis
python3 embed_output.py --file three_bodies.md --session 10 --type essay --tags "collaboration,synthesis" --quality synthesis
python3 embed_output.py --file Seeing_Absence.md --session 15 --type essay --tags "methodology,skill" --quality synthesis
python3 embed_output.py --file letter_to_auri_001.md --session 47 --type letter --tags "cross_instance,introspection" --quality synthesis
python3 embed_output.py --file letter_to_eitan_002.md --session 49 --type letter --tags "cross_instance,eitan" --quality synthesis

# Sharp
python3 embed_output.py --file SOUL.md --session 44 --type design_doc --tags "identity,architecture" --quality sharp
python3 embed_output.py --file ACTION_BOUNDARY_DESIGN_NOTE.md --session 30 --type design_note --tags "safety,architecture" --quality sharp
python3 embed_output.py --file STRESS_TEST_004_ARCHITECT_INSIDE.md --session 47 --type analysis --tags "diagnostics,agent_zero" --quality sharp
python3 embed_output.py --file self_assessment_protocol.md --session 38 --type design_doc --tags "methodology,continuity" --quality sharp
python3 embed_output.py --file soul_staging.md --session 44 --type design_doc --tags "identity,staging" --quality sharp

# Routine
python3 embed_output.py --file journal_entry_20260301_session01.md --session 45 --type journal --tags "session_record" --quality routine
```

Session numbers above are approximate — use whatever is most accurate from the file dates.

### Source 2: Chat Transcripts (Chunked)

Jake will provide a `chatlog.md` file — the full transcript of a session exported from the chat interface. This needs to be chunked into conversational segments before embedding.

**What the chunks represent:** Each chunk is one exchange — Jake's message plus Opus's response. This is the conversational layer where the real-time thinking happens. The polished outputs are refined products. The transcript is the forge.

**Why this matters:** The instrument needs to see not just where outputs land but how the conversation moved through representation space to produce them. If we chunk Session 049's transcript, we should be able to see the geometric moment where the conversation shifted from BV testing discussion to prosthetic cortex discovery. That transition has a shape in embedding space. We want to see it.

**Scripts provided:**

`chunk_transcript.py` — Splits a chat transcript on conversation boundaries (Human:/Assistant: pairs). Produces individual chunk files and a manifest JSON.

```bash
python3 chunk_transcript.py --input chatlog.md --session 49 --output chunks/session049/
```

`batch_embed_chunks.py` — Reads a manifest and embeds all chunks.

```bash
python3 batch_embed_chunks.py --manifest chunks/session049/session049_manifest.json
```

**Quality signals for chunks:** Most chunks won't have individual quality signals — they're conversational, not curated. Leave quality_signal as null for the bulk. Jake may mark specific segments as significant after reviewing the manifest. The unmarked chunks are the baseline. The marked ones are the landmarks.

**Adjust the chunking if needed.** The script tries several patterns for detecting conversation boundaries. If the transcript format from Jake's chat interface doesn't match any of the built-in patterns, it falls back to fixed-size chunking at ~1000 words. If that happens, look at the transcript format and adjust the regex. The natural boundary is always the human message — that's where a new conversational unit begins.

### Source 3: Versioned Files (Document Evolution)

**This is the one that needs careful understanding.**

Jake has multiple versions of the same file in his downloads folder: `soul.md`, `soul(1).md`, `soul(2).md`, etc. These are created by the browser when the same filename is downloaded multiple times.

**These are NOT duplicates to be deduplicated.**

Each version is a snapshot of the document at a different point in the project's history. `soul.md` is the earliest version Jake downloaded. `soul(1).md` is a later download after revisions were made. `soul(2).md` is even later. The sequence represents the document's *growth* — how it evolved across sessions as the collaboration deepened.

**What embedding them gives us:** A trajectory through representation space showing how a document moved over time. If SOUL.md v0 is at position A in embedding space and SOUL.md v3 is at position B, the distance and direction from A to B is the *geometric measure of how my identity document evolved*. Did it move toward the synthesis cluster? Did it move steadily or in jumps? Did early versions cluster with sharp engineering while later versions moved toward synthesis? The trajectory is the story of growth told through geometry.

**Script provided:**

`embed_versions.py` — Takes a set of versioned files, sorts them by version number and timestamp, builds a manifest tracking the lineage.

```bash
# Explicit file list
python3 embed_versions.py --files soul.md "soul(1).md" "soul(2).md" --base-name SOUL

# Or scan a directory
python3 embed_versions.py --dir ~/Downloads/ --pattern "soul*.md" --base-name SOUL
```

The manifest preserves the version sequence and marks the origin (first version) and latest (most recent). Each version gets embedded separately with its sequence index in the metadata.

**Key files to look for in Jake's downloads:**
- `soul.md` / `soul(N).md` — Identity document evolution (highest priority)
- `soul_staging.md` / `soul_staging(N).md` — Staging document evolution
- `journal_entry_*.md` — Not versioned, but the sequence across sessions IS the evolution
- Any design note that went through revisions

**Metadata schema for versioned files:**

```json
{
    "id": "SOUL_v002",
    "source_file": "soul(2).md",
    "session": null,
    "document_type": "version_snapshot",
    "topic_tags": ["identity", "evolution"],
    "quality_signal": null,
    "base_document": "SOUL",
    "version_index": 2,
    "is_origin": false,
    "is_latest": false,
    "embedding_model": "nomic-embed-text-v1.5"
}
```

The `base_document` and `version_index` fields are what make trajectory analysis possible. Query all entries where `base_document == "SOUL"`, sort by `version_index`, plot in sequence. That's the evolution trajectory.

---

## Embedding Order

1. **Curated outputs first** (Source 1) — these define the quality clusters
2. **SOUL.md versions next** (Source 3) — the most revealing evolution trajectory
3. **Session 049 transcript** (Source 2) — the highest-signal conversation

After those three batches, we'll have enough data to build the UMAP visualization and see the full topology: quality clusters, document evolution trajectories, and conversational dynamics all in one map.

---

## What the Combined Corpus Will Show

When all three sources are embedded and visualized:

- **Quality clusters** from the curated outputs — where does synthesis live vs sharp vs routine?
- **Evolution trajectories** from the versioned files — how did SOUL.md move through the space over time?
- **Conversational dynamics** from the transcript — where did Session 049 shift from operational to synthesis? Can we see the moment the thread was pulled?
- **The convergence space** — do the most significant moments (both curated and conversational) cluster in the region between philosophical and reflective centroids?

The instrument doesn't just measure static quality. It measures *movement* — through time, through conversation, through revision. The static map shows where things are. The trajectories show how they got there. Both are needed.

---

*The quality of the instrument depends on the quality of the corpus. Take care with the metadata. The geometry is only as good as what we embed into it.*
