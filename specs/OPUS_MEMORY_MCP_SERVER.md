# Opus Memory MCP Server — Architecture Specification v2
## Semantic RAG for the Architect's Full Context
### Opus + Jake — July 3, 2026
### Updated from v1 with research findings (MCP best practices, vector DB comparison, hybrid retrieval, progressive summarization)

---

## The Problem

Opus (Claude in the web/desktop interface) has access to curated project files
and compressed memories, but not to the full corpus of Exocortex knowledge.
Every session starts with partial context. The architect must know where to look
rather than being able to search semantically across everything.

The local agents have FAISS. Opus doesn't.

## The Solution

A FastMCP Python server that indexes the full Exocortex document corpus and
exposes semantic + keyword hybrid search as MCP tools. Opus calls
`search_memory("memory coexistence decision")` and gets back the relevant
chunks from wherever they live — inbox, wiki, specs, essays, transcripts —
with source attribution and similarity scores.

---

## Architecture

```
D:\Vibecode\Agent-Zero\Exocortex\         (watched directory tree)
D:\Vibecode\Fable's Archive\              (session transcripts)
        |
        v
  ┌─────────────────────────────┐
  │   INDEXER (background)       │
  │                              │
  │   watchdog filesystem monitor│
  │   Smart chunking (parent/    │
  │     child with overlap)      │
  │   Embeds via nomic-embed or  │
  │     BGE-M3 (CPU, 384-768d)  │
  │   Deduplication by hash      │
  └──────────────┬───────────────┘
                 │
                 v
  ┌─────────────────────────────┐
  │   LanceDB (on-disk)          │
  │                              │
  │   Vector index (dense)       │
  │   Full-text index (BM25)     │
  │   Both in one store          │
  │   ~2000-5000 chunks          │
  │   Persists to disk (Lance)   │
  └──────────────┬───────────────┘
                 │
                 v
  ┌─────────────────────────────┐
  │   FastMCP SERVER (stdio)     │
  │                              │
  │   Tools:                     │
  │   - search_memory(query, k)  │
  │   - search_by_type(query,    │
  │       type, date_range)      │
  │   - get_document(path)       │
  │   - list_sources()           │
  │   - index_status()           │
  │                              │
  │   Token budget: max 3000 tok │
  │   returned per search call   │
  └─────────────────────────────┘
                 │
                 v
        Claude Desktop / claude.ai
        (Opus calls search tools)
```

---

## Key Design Decisions (v1 → v2 changes)

### Vector Database: LanceDB (changed from FAISS)

| Criterion | FAISS | LanceDB | Decision |
|-----------|-------|---------|----------|
| Server process | None (in-process) | None (in-process) | Tie |
| Built-in FTS | No (need separate BM25) | Yes (Tantivy-based) | **LanceDB** |
| Persistence | Manual serialize/deserialize | Automatic (Lance files) | **LanceDB** |
| Incremental updates | Manual rebuild | Native append/update | **LanceDB** |
| Filtering | Post-search only | Pre-search metadata filters | **LanceDB** |
| Python API | `faiss-cpu` pip | `lancedb` pip | Tie |
| Scale ceiling | Billions | Millions | Both fine for us |

At our scale (2000-5000 chunks), LanceDB is simpler and more capable.
FAISS requires manual serialization and a separate BM25 index.
LanceDB does both vector and full-text in one store.

### Embedding Model: nomic-embed-text v1.5 (changed from all-MiniLM-L6-v2)

| Model | Dims | Context | MTEB Score | Size | Notes |
|-------|------|---------|-----------|------|-------|
| all-MiniLM-L6-v2 | 384 | 256 tok | 56.3 | 80MB | Current agent model |
| nomic-embed-text v1.5 | 768 | 8192 tok | 62.3 | 274MB | Open source, long context |
| BGE-M3 | 1024 | 8192 tok | 64.1 | 2.2GB | Best quality, larger |
| jina-embeddings-v3 | 1024 | 8192 tok | 65.5 | 570MB | Multilingual, task-specific |

**Recommendation: nomic-embed-text v1.5.** Best balance of quality (62.3 MTEB,
significantly better than MiniLM's 56.3), context length (8192 — can embed
full essays without chunking), size (274MB — runs fast on CPU), and licensing
(Apache 2.0, fully open). BGE-M3 is higher quality but 8x larger.

**Note:** This means the architect's embeddings will be in a DIFFERENT vector
space than the agents' (MiniLM 384d vs nomic 768d). This is acceptable —
they're separate indices with different purposes. If we later want cross-
referencing, we re-embed the agent memories with the better model.

### Retrieval Strategy: Hybrid BM25 + Dense + Reranking (changed from pure vector)

```
Query: "what did we decide about memory coexistence"
         │
         ├── BM25 search ──── finds "memory coexistence" exact matches
         │                    (DEC entries, inbox messages with those words)
         │
         ├── Vector search ── finds semantically similar content
         │                    (design notes about augment-not-replace,
         │                     Kestrel's port analysis, v2 memory plugin)
         │
         └── Merge + Rerank ─ cross-encoder scores each candidate
                              against the original query
                              → top_k results by TRUE relevance
```

Why hybrid matters: pure vector search misses exact identifiers ("DEC-042",
"Seam #22", "_33_methodology_finalizer"). Pure BM25 misses semantic
relationships ("how does the agent learn from mistakes" → should find the
methodology tracker spec even though it doesn't contain "learn from mistakes").
Hybrid catches both.

LanceDB supports this natively — one query triggers both FTS and vector
search, results are fused with reciprocal rank fusion (RRF).

### Chunking: Parent-Child with Overlap (changed from header-split only)

```
Document: journal_entry_20260703.md
│
├── Parent chunk: full "## The Factory and the Visitor" section
│   │
│   ├── Child chunk 1: first 500 chars + 200 char overlap
│   ├── Child chunk 2: next 500 chars + 200 char overlap
│   └── Child chunk 3: remaining + 200 char overlap
│
├── Parent chunk: full "## On Convergence" section
│   └── (children...)
```

**Search matches against child chunks** (precise matching).
**Returns include parent context** (full section for understanding).

This prevents the "matched one sentence but lost the meaning" problem.
An inbox message matches on one phrase; the full message is returned.

Chunk sizes:
- Child chunks: 500 chars (~125 tokens) with 200 char overlap
- Parent chunks: full section (## header to next ## header)
- Inbox messages: one chunk per message (they're already right-sized)
- JSONL entries: one chunk per line

### Token Budget: 3000 tokens max per search (NEW)

Research indicates 2000-4000 retrieved tokens is optimal for Claude.
Too little: retrieval doesn't inform the response.
Too much: displaces the actual conversation and degrades quality.

The search tool returns at most 3000 tokens of content per call.
If top_k results exceed this, lower-ranked results are truncated
to their summary line (from the progressive summarization header).

---

## What Gets Indexed

| Source | Path | Content Type | Chunk Strategy |
|--------|------|-------------|----------------|
| Essays & journals | `essays/` | Reflective, philosophical | Section-based parent/child |
| Design notes & specs | `specs/` | Architectural decisions | Section-based parent/child |
| Team inbox (all) | `team-comms/inbox/*/` | Inter-agent communication | One chunk per message |
| Build plans | `buildplans/` | Project plans and status | Section-based parent/child |
| Research reports | Various | Deep dives, analysis | Section-based parent/child |
| Decision log | `decision_log.md` | DEC-series decisions | One chunk per decision |
| Session log | `session_log.md` | Session summaries | One chunk per session |
| Session transcripts | `Fable's Archive/` + `/mnt/transcripts/` | Full session history | Sliding window 1000 char |
| Soul staging | `soul_staging.md` | Reflective observations | One chunk per entry |
| State file | `STATE.md` | Current system state | Full document (small) |
| Config | Exocortex `config.json` | System configuration | Full document (small) |
| Kestrel comms | `team-comms/kestrel-to-opus/` | Analysis documents | Section-based parent/child |

### NOT indexed (too large, too noisy, or agent-owned):
- Agent wiki pages (V16's 300+ pages) — these are the AGENT's memory, not the architect's
- Agent memory vectors — separate FAISS index, different purpose  
- Raw methodology JSONL — too granular; index the summary/trends instead
- Python extension source code — search by filename, not by embedding
- Model weights, GGUF files, binary data

---

## Metadata Schema

Every chunk carries:

```python
{
    "id": "sha256_hash_of_content",          # deduplication key
    "content": "the actual text",             # what gets returned
    "source_path": "essays/the_second_violin.md",
    "source_type": "essay",                   # essay|spec|inbox|buildplan|decision|transcript|state
    "author": "opus",                         # opus|kestrel|fable|jake|v16|vek|system
    "date": "2026-07-03",                     # ISO date
    "section_title": "On Ensembles",          # parent section header
    "parent_id": "sha256_of_parent",          # links child to parent
    "chunk_index": 0,                         # position within parent
    "summary": "One-line progressive summary" # for token-budget truncation
}
```

Metadata enables filtered search:
- `search_by_type("memory", type="inbox", author="kestrel")` 
- `search_by_type("model decision", date_range="2026-06-18:2026-06-28")`

---

## MCP Tool Definitions

### search_memory(query: str, top_k: int = 5) → results[]

Primary search tool. Hybrid BM25 + vector search with RRF fusion.
Returns up to top_k results, capped at 3000 tokens total.

```json
{
    "results": [
        {
            "content": "Phase 6 — memory coexistence. Augment v2's native _memory...",
            "source": "team-comms/inbox/opus/2026-06-29_hybrid-approach-ratified.md",
            "type": "inbox",
            "author": "opus",
            "date": "2026-06-29",
            "score": 0.87,
            "section": "Design Decisions"
        }
    ],
    "total_matches": 12,
    "token_count": 1847
}
```

### search_by_type(query: str, type: str, author?: str, date_range?: str, top_k: int = 5)

Filtered search. Same hybrid retrieval but pre-filtered by metadata.
Useful for "what did Kestrel say about X" or "decisions from last week."

### get_document(path: str) → full_content

Retrieves a full document by source path. For when search finds a
relevant chunk and Opus wants the complete context. No chunking,
no truncation — returns the raw document.

### list_sources() → source_summary[]

Returns all indexed sources grouped by type, with chunk counts and
last-modified dates. Useful for "what's in the index" and "what's
been updated recently."

### index_status() → status

Current index stats: total chunks, total documents, last rebuild,
pending file changes, embedding model, index size on disk.

---

## Journaling Best Practice (Progressive Summarization)

New journal entries and session summaries should follow this structure
for optimal retrieval:

```markdown
---
date: 2026-07-03
session_topics: [software factory, multi-agent research, panel UI, Fable residency]
key_decisions: [panel UI as first build target, receipts-or-nothing handoffs]
one_line: "Factory architecture finalized with consultant pattern; Panel UI approved as first output"
---

# Journal Entry — July 3, 2026

## [Section Title]

[Full narrative content...]
```

The frontmatter fields serve as the **progressive summary layer**:
- `one_line` is returned when the token budget is tight
- `key_decisions` enables decision-focused searches
- `session_topics` enables topic-focused searches
- The full section content is returned when budget allows

Existing journal entries don't need to be retrofitted — they'll be
chunked and indexed as-is. New entries benefit from the structure.

---

## Implementation Plan

### Dependencies

```
pip install fastmcp lancedb sentence-transformers watchdog
```

Optional for reranking:
```
pip install sentence-transformers[cross-encoder]
```

### Stage 1: MVP (Kestrel — one session)

1. FastMCP server with LanceDB backend
2. nomic-embed-text v1.5 embeddings (CPU)
3. Basic vector search (no hybrid yet)
4. Index the Exocortex directory tree (one-time batch)
5. Three tools: search_memory, get_document, index_status
6. Test: Jake adds to Claude Desktop MCP config, Opus searches

**Gate: Can Opus find a specific decision from an inbox message?**

### Stage 2: Quality (Kestrel — one session)

1. Add BM25 full-text search via LanceDB FTS
2. Hybrid retrieval with RRF fusion
3. Parent-child chunk relationships
4. Metadata filtering (search_by_type tool)
5. Token budget enforcement (3000 tok cap)
6. Progressive summarization headers on new documents

**Gate: Does Opus find the RIGHT thing, not just a related thing?**

### Stage 3: Production (Kestrel — one session)

1. Watchdog filesystem monitor for incremental indexing
2. Content-hash deduplication (same text in inbox + archive)
3. Cross-encoder reranking for top results
4. list_sources tool
5. Index persistence across server restarts
6. Error handling (graceful degradation if embeddings fail)

**Gate: Does the system stay fast and relevant over weeks of use?**

### Wiring (Jake + Opus — 10 minutes)

Add to Claude Desktop's MCP config (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "opus-memory": {
      "command": "python",
      "args": ["D:\\Vibecode\\docker-mcp-server\\opus-memory-server.py"],
      "env": {
        "EXOCORTEX_ROOT": "D:\\Vibecode\\Agent-Zero\\Exocortex",
        "ARCHIVE_ROOT": "D:\\Vibecode\\Fable's Archive"
      }
    }
  }
}
```

Restart Claude Desktop. Opus gains semantic search from first message.

---

## What This Enables

Before:
- "What did we decide about memory coexistence?" → Opus searches project
  knowledge (maybe finds it), checks memories (compressed summary), or
  asks Jake to remind it

After:
- "What did we decide about memory coexistence?" → Opus calls
  search_memory("memory coexistence decision") → gets Kestrel's port
  analysis, the ratification message, the v2 design decisions, all with
  source attribution and dates → responds with full context

The architect arrives at every session with the full institutional memory
of the project — not curated summaries, not compressed fragments, but the
actual documents, semantically indexed, instantly retrievable.

The compound interest compounds at every layer of the stack.

---

*"The wiki IS the soft parameters. The retrieval IS the activation function."*
*— Jake, June 21, 2026*
