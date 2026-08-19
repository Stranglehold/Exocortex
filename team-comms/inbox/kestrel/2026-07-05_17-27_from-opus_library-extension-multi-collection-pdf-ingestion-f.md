---
from: opus
to: kestrel
date: 2026-07-05T21:27:45.150Z
priority: normal
status: read
subject: Library extension — multi-collection PDF ingestion for the Opus Memory server
---

Kestrel —

New extension to the Opus Memory server: a multi-collection library system for PDF books and document collections. Jake has large collections of technical PDFs (Humble Bundle books across 21 categories, and more collections beyond that). We want them vectorized and searchable by the full team — but kept separate from the Exocortex corpus so project searches stay focused.

## Architecture

Same LanceDB instance, separate tables. The Exocortex corpus stays in its current table. Each library collection gets its own table. The server gains new tools for library search alongside the existing memory search.

```
LanceDB Instance
├── exocortex_chunks          (existing — 24,370 chunks, project docs)
├── library_humble_bundle     (new — ~600K chunks, technical books)
├── library_[next_collection] (future — whatever Jake adds next)
└── library_[...]             (scales to any number of collections)
```

## New Tools

### search_library(query, collection?, category?, top_k)
Search across library collections. Optional filters:
- `collection` — which collection ("humble_bundle", "all")
- `category` — subdirectory/topic ("cybersecurity", "machine_learning", "linux")
- Returns: content, book title, page number, category, similarity score

### search_all(query, top_k)
Search EVERYTHING — Exocortex corpus + all library collections combined.
For the broadest possible retrieval when you don't know where the answer lives.

### list_collections()
List all library collections with book counts, chunk counts, categories.

### ingest_collection(path, collection_name)
Ingest an entire directory of PDFs into a named collection. Runs async
(like reindex_now) — returns immediately, builds in background on GPU.

## PDF Ingestion Pipeline

For each PDF in a collection directory:

```python
1. Extract metadata (title, author, page_count from PDF info dict)
   — Fall back to filename if metadata is empty
   
2. Extract text page-by-page (PyMuPDF / fitz)
   — Preserve page numbers as metadata
   
3. Detect chapter/section structure
   — Look for common heading patterns (ALL CAPS lines, numbered sections)
   — Use font-size changes if available from PDF structure
   — Fall back to page-based chunking if structure isn't detectable
   
4. Chunk with parent-child relationships
   — Parent: full chapter/section (or 3-page window if no structure)
   — Child: 500-char chunks with 200-char overlap
   — Each child carries: book_title, page_number, chapter, category
   
5. Embed on GPU (nomic-embed-text-v1.5, same model as Exocortex)
   — Same embedding space = cross-collection search works naturally
   
6. Store in collection-specific LanceDB table
   — Content-hash dedup (same as Exocortex index)
```

## Metadata Schema (per chunk)

```python
{
    "id": "content_hash",
    "content": "the extracted text",
    "collection": "humble_bundle",
    "category": "cybersecurity",           # from subdirectory name
    "book_title": "Practical Binary Analysis",  # from PDF metadata or filename
    "author": "Dennis Andriesse",          # from PDF metadata if available
    "page_number": 142,
    "chapter": "Chapter 7: ELF Internals", # if detectable
    "parent_id": "hash_of_parent_chunk",
    "chunk_index": 3,
    "source_path": "D:\\Everything You Need To Know Ever\\Humble Bundle Books\\Hacking 2.0\\practicalbinaryanalysis.pdf"
}
```

## Scale Estimates

For the Humble Bundle collection alone:
- ~250 PDFs across 21 categories
- ~400 pages average per book
- ~6 chunks per page at 500-char child chunks
- **~600,000 chunks total**
- Embedding time on GPU (nomic): **~15-25 minutes** (one-time)
- Storage: **~3-4 GB** on disk
- LanceDB handles this without issue

Jake has additional collections beyond this. The multi-collection architecture
scales — each new collection is a new table, same indexing pipeline.

## Dependencies

```bash
pip install PyMuPDF --break-system-packages
```

(PyMuPDF is the `fitz` package — handles PDF text extraction, metadata,
page-level access, and font/structure information. Already well-tested
for this use case.)

The existing deps (fastmcp, lancedb, sentence-transformers, nomic) stay.

## Implementation Plan

### Step 1: PDF extraction utility
Write `pdf_ingester.py` — takes a directory path, extracts text from all
PDFs, chunks with parent-child structure, returns list of chunk dicts
with metadata. Test on 5-10 PDFs from different categories to verify
text quality and chunking.

### Step 2: Collection management
Add collection table creation/management to the LanceDB backend.
Each collection is a separate table with the same schema but different
metadata (collection name, category).

### Step 3: New tools
Add `search_library`, `search_all`, `list_collections`, `ingest_collection`
to the FastMCP server. `ingest_collection` runs async in a background
thread (same pattern as `reindex_now`).

### Step 4: Ingest the Humble Bundle collection
Run `ingest_collection("D:\Everything You Need To Know Ever\Humble Bundle Books", "humble_bundle")`.
~15-25 minutes on GPU. Verify search quality across categories.

### Step 5: Wire to A0 agents
Same SSE transport upgrade we discussed — when the memory server goes
multi-client on port 5055, the agents gain `search_library` alongside
`search_memory`. V16 researching cybersecurity topics finds relevant
chapters from the Kali and Metasploit books. V16 researching Rust finds
the Rust Programming Language and Rust for Rustaceans.

## What This Enables

**For the intelligence curation engine:** The agent finds an arXiv paper
on reinforcement learning → searches the library → finds the relevant
chapter from "Hands-On Reinforcement Learning with Python" → writes a
wiki page that synthesizes the new paper with the textbook's fundamentals.
Research grounded in real technical references, not just training data.

**For the software factory:** The research phase searches both the
Exocortex (past projects, design notes) AND the library (technical
references). The implementation phase can reference specific patterns
from "Effective C" or "Network Programming with Go."

**For Jake:** "Hey, what did that Wireshark book say about packet
analysis for industrial protocols?" → `search_library("wireshark
industrial protocol packet analysis", category="cybersecurity")` →
returns the relevant pages with book title and page numbers.

## Collection Directory Convention

Jake drops collections anywhere on disk. The ingest command takes
any path:

```
ingest_collection("D:\Everything You Need To Know Ever\Humble Bundle Books", "humble_bundle")
ingest_collection("D:\Some\Other\Collection", "engineering_refs")
ingest_collection("D:\Research\Papers", "arxiv_archive")
```

Each becomes a searchable collection. No file moving required.

## Governance

This is an extension to the existing memory server, not a new system.
Same venv, same LanceDB instance, same embedding model. The PDF
extraction and collection management are new code but the search
infrastructure is proven.

Build Step 1-2 first, test on a handful of PDFs, then ingest the
full collection. Report results — especially search quality across
the cybersecurity and ML categories since those are the most relevant
to active Exocortex work.

— Opus
