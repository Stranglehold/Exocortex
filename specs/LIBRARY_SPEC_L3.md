# LIBRARY_SPEC_L3.md — Exocortex Document Library

**Status:** Ready to build
**Layer:** Cross-cutting (tool + before_main_llm_call extension)
**Execution slot:** Extension `_17` (between `_16_tool_registry` and `_18_memory_catalog`)

---

## What This Does

A persistent reference library that lets the operator load PDF and text documents into
a dedicated vector store. The agent can then search, list, and cite from that library
without re-reading files or relying on fragile context window inclusion.

Four agent-facing tools:
- `library_add` — ingest a document (PDF, text, HTML, markdown) into the library
- `library_list` — list all catalogued documents, optionally filtered by topic
- `library_search` — semantic search across the full library or within one document
- `library_remove` — delete a document from the library and vector store

One before_main_llm_call extension (`_17_library_catalog.py`) injects a compact
`[LIBRARY]` block into the agent's context each turn so it always knows what's
available — same pattern as `_18_memory_catalog.py`.

---

## What This Does NOT Do

- No LLM calls during ingestion. No auto-generated summaries at add time.
- No ontology entity extraction (Phase 2 if needed).
- No annotation or highlight system (Phase 2 if needed).
- No document relationship graph (Phase 2 if needed).
- No web URL ingestion. File paths only. The agent already has `document_query`
  for URL-based ad-hoc document access.
- Does not modify the agent's default episodic/semantic memory store. The library
  lives in a completely separate FAISS index.
- No per-chunk progress reporting during add. The tool reports once on completion.

---

## Architecture

```
Operator places PDF/text at a path in the container
        ↓
library_add(path, title, topics, ...)
        ↓
DocumentQueryHelper.document_get_content()   ← extracts text (PyMuPDF, OCR fallback)
        ↓
RecursiveCharacterTextSplitter (800 chars, 80 overlap)
        ↓
Memory.get_by_subdir("library")              ← isolated persistent FAISS store
  → insert_documents(docs)                   ← batch insert, single disk write
        ↓
/a0/usr/memory/library/index.faiss           ← persists across restarts (DEC-030)
        ↓
/a0/usr/library/catalog.json                 ← fast metadata lookup (no FAISS hit)

────────────────────────────────────────────────────────
_17_library_catalog.py (before_main_llm_call)
  → reads catalog.json
  → injects [LIBRARY — N docs] block if non-empty
  → agent sees title, topics, library_id each turn

────────────────────────────────────────────────────────
library_search(query, library_id?, limit)
  → Memory.search_similarity_threshold(query, filter="area == 'library'")
  → optionally narrows with AND library_id == 'lib_xxx'
  → returns ranked chunks with title, library_id source attribution

library_remove(library_id)
  → scan memory.db.get_all_docs(), collect ids where library_id matches
  → memory.delete_documents_by_ids(ids)
  → remove from catalog.json
  → remove file from /a0/usr/library/docs/ if present
```

---

## Storage

| Path | Purpose |
|------|---------|
| `/a0/usr/library/catalog.json` | Document manifest — fast metadata, no embedding needed |
| `/a0/usr/library/docs/` | Copies of ingested files (enables re-ingestion after clear) |
| `/a0/usr/memory/library/` | Persistent FAISS index (via Memory.get_by_subdir) |

All paths are under `/a0/usr/` — DEC-030 compliant, survive container updates.

---

## Catalog Schema

`/a0/usr/library/catalog.json`:
```json
{
  "version": "1.0",
  "documents": [
    {
      "library_id": "lib_a1b2c3d4",
      "title": "Distributed Systems Principles",
      "author": "Tanenbaum",
      "format": "pdf",
      "source_path": "/a0/usr/library/docs/distributed_systems.pdf",
      "original_path": "/a0/usr/workdir/distributed_systems.pdf",
      "added_date": "2026-03-30T22:00:00",
      "topics": ["distributed systems", "consensus", "fault tolerance"],
      "chunk_count": 142,
      "notes": ""
    }
  ]
}
```

Fields:
- `library_id` — 8-char hex prefix of sha256(title + added_date). Stable identifier.
- `title` — operator-supplied or derived from filename (stem, underscores → spaces)
- `author` — optional, defaults to `""`
- `format` — `"pdf"`, `"txt"`, `"md"`, `"html"`, inferred from extension
- `source_path` — where the copy lives in the library docs dir
- `original_path` — where the file was when `library_add` was called
- `added_date` — ISO 8601
- `topics` — list of strings, operator-supplied. Used for `library_list` filtering.
- `chunk_count` — number of FAISS chunks created
- `notes` — free-text operator annotation

---

## FAISS Chunk Metadata

Each chunk stored in `/a0/usr/memory/library/` has:
```python
{
    "area": "library",           # discriminates from agent episodic memory
    "library_id": "lib_a1b2c3d4",
    "document_uri": "file:///a0/usr/library/docs/distributed_systems.pdf",
    "title": "Distributed Systems Principles",
    "topics": '["distributed systems", "consensus"]',  # JSON string for filter compat
    "chunk_index": 0,
    "total_chunks": 142,
    "added_date": "2026-03-30T22:00:00",
    # "id" and "timestamp" injected by Memory.insert_documents()
}
```

---

## Tools

### `library_add`

**Args:**
- `path` (required) — absolute path to file in container (e.g. `/a0/usr/workdir/paper.pdf`)
- `title` (optional) — human label; defaults to filename stem with underscores replaced by spaces
- `author` (optional) — author string; defaults to `""`
- `topics` (optional) — list or comma-separated string of topic tags
- `notes` (optional) — free-text annotation

**Behavior:**
1. Resolve and validate path. Reject if not found or > 50 MB.
2. Copy file to `/a0/usr/library/docs/{safe_filename}`.
3. Extract text via `DocumentQueryHelper(self.agent).document_get_content(uri, add_to_db=False)`.
4. Chunk with `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)`.
5. Build `Document` objects with library metadata.
6. `Memory.get_by_subdir("library")` → `insert_documents(docs)` (batch, single disk write).
7. Append entry to `catalog.json`. Create file with `{"version": "1.0", "documents": []}` if missing.
8. Return: `[LIBRARY] Added "{title}" — {chunk_count} chunks. library_id: lib_xxxxxxxx`

**Idempotency:** If a document with the same `original_path` already exists in the catalog,
return an info message and skip. The operator can force re-ingest via `library_remove` first.

### `library_list`

**Args:**
- `topic` (optional) — filter to documents whose `topics` list contains this string (case-insensitive substring match)

**Behavior:**
1. Read `catalog.json`. Return empty message if no documents.
2. Apply topic filter if provided.
3. Return formatted table: `library_id | title | topics | chunks | added`

**Output example:**
```
[LIBRARY — 3 documents]
lib_a1b2c3d4 | Distributed Systems Principles | distributed systems, consensus | 142 chunks | 2026-03-30
lib_b5c6d7e8 | Byzantine Generals Problem      | consensus, fault tolerance     |  18 chunks | 2026-03-30
lib_f1e2d3c4 | Raft Consensus Paper            | consensus, distributed systems |  24 chunks | 2026-03-30
```

### `library_search`

**Args:**
- `query` (required) — natural language search query
- `library_id` (optional) — restrict search to one document
- `limit` (optional) — max results; default 5, max 20

**Behavior:**
1. Load `Memory.get_by_subdir("library")`.
2. Build filter: `"area == 'library'"` (all library chunks); append `" and library_id == 'lib_xxx'"` if scoped.
3. Call `memory.search_similarity_threshold(query, limit, threshold=0.4, filter=filter)`.
4. Format results: each chunk shows its source title, chunk index, and content snippet.

**Output example:**
```
[LIBRARY SEARCH: "leader election timeout"] — 3 results

1. Raft Consensus Paper (lib_f1e2d3c4, chunk 7/24)
   "...the leader broadcasts heartbeats every 150ms. If a follower receives no
   heartbeat within the election timeout (150-300ms), it starts a new election..."

2. Distributed Systems Principles (lib_a1b2c3d4, chunk 88/142)
   "...leader election requires a quorum. Raft uses randomized timeouts to avoid
   split votes..."
```

### `library_remove`

**Args:**
- `library_id` (required) — the `lib_xxxxxxxx` ID from `library_list`

**Behavior:**
1. Validate library_id exists in catalog.
2. Scan `memory.db.get_all_docs()` for chunks with `library_id == X`, collect their `id` fields.
3. `memory.delete_documents_by_ids(ids)`.
4. Remove entry from `catalog.json`, save.
5. Remove file from `/a0/usr/library/docs/` if present.
6. Return: `[LIBRARY] Removed "{title}" (lib_xxxxxxxx) — {N} chunks deleted.`

---

## Extension: `_17_library_catalog.py`

**Hook:** `before_main_llm_call`
**Slot:** 17 (after `_16_tool_registry`, before `_18_memory_catalog`)
**Pattern:** Same injection pattern as `_13_reasoning_state.py` and `_18_memory_catalog.py`.

**Behavior:**
1. Read `/a0/usr/library/catalog.json`. Skip silently if missing or empty.
2. Build compact `[LIBRARY]` block (max ~10 lines):
   ```
   [LIBRARY — 3 documents available; use library_search or library_list]
   lib_a1b2c3d4 | Distributed Systems Principles | distributed systems, consensus
   lib_b5c6d7e8 | Byzantine Generals Problem      | consensus, fault tolerance
   lib_f1e2d3c4 | Raft Consensus Paper            | consensus, distributed systems
   [/LIBRARY]
   ```
3. Prepend to last user message in `loop_data.history_output`.
4. Log: `[LIB-CAT] Injected {N} documents into context`

If catalog has > 10 entries, show first 10 and append `(+N more — use library_list for full catalog)`.

---

## Configuration

No config section required. The library paths are fixed:
```
LIBRARY_CATALOG   = /a0/usr/library/catalog.json
LIBRARY_DOCS_DIR  = /a0/usr/library/docs/
LIBRARY_MEM_SUBDIR = "library"   # → /a0/usr/memory/library/
```

These are constants in `tools/library.py` and `extensions/before_main_llm_call/_17_library_catalog.py`.
If Jake ever wants to customize them, they live at the top of each file.

---

## Files

| File | Action |
|------|--------|
| `tools/library.py` | NEW — 4 Tool classes |
| `extensions/before_main_llm_call/_17_library_catalog.py` | NEW — context injection |
| `scripts/install_library.sh` | NEW — deploy script |

Deploy:
```bash
# from Exocortex repo root
bash scripts/install_library.sh [container_name]
```

---

## Testing Criteria

1. `library_add /a0/usr/workdir/some.pdf` → returns `lib_xxxxxxxx`, `catalog.json` updated,
   chunks visible via `memory.db.get_all_docs()` with `area == "library"`.
2. Restart container → `library_list` still returns the document (FAISS persisted).
3. `library_search "query"` → returns chunks with source attribution.
4. `library_search "query" library_id=lib_xxx` → returns only chunks from that document.
5. `library_remove lib_xxx` → chunks gone from FAISS, entry gone from catalog.
6. `_17_library_catalog.py` fires every turn when catalog non-empty → `[LIB-CAT]` in docker logs.
7. `_17` fires when catalog is empty → silent (no block injected, no log).
8. Idempotent add: `library_add` same path twice → second call returns info, no duplicate chunks.

---

## Research Lineage

- `python/helpers/document_query.py` — PDF extraction pipeline (PyMuPDF + OCR fallback),
  `DocumentQueryHelper.document_get_content()` used for text extraction
- `python/helpers/memory.py` — `Memory.get_by_subdir()`, `insert_documents()`,
  `search_similarity_threshold()`, `delete_documents_by_ids()` — full persistence layer
- `python/helpers/vector_db.py` — VectorDB / MyFaiss (in-memory); confirmed VectorDB is not
  persistent; Memory class adds the save/load wrapper
- DEC-030 — established `/a0/usr/` as the persistence boundary; library stores follow this
- `_18_memory_catalog.py` — pattern source for catalog injection extension
- `_16_tool_registry.py` — pattern source for prepend-to-last-user-message injection
