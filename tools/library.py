"""
library.py — Exocortex Document Library Tools  v2.0
=====================================================

Persistent reference library with hierarchical collection structure and
two-stage routing search. Completely separate from agent episodic memory.

Architecture (three tiers in one FAISS subdir "library"):
  area="library_collection"  — one entry per collection, summary text
  area="library_book"        — one entry per book, title + first 500 chars (routing proxy)
  area="library"             — content chunks (deep storage)

Search: query → route against book summaries → top N books → chunk search
within only those books. Precision stays high regardless of library size.

Five tools:
  library_add         — ingest a local file (PDF, text, HTML, markdown)
  library_list        — list collections (default) or books within a collection
  library_search      — two-stage semantic search
  library_remove      — delete a document and all its FAISS entries
  library_collections — list collections with summaries and book counts

Catalog: /a0/usr/library/catalog.json   (tree: collections → book metadata)
FAISS:   /a0/usr/memory/library/        (persistent, separate from agent memory)
Docs:    /a0/usr/library/docs/          (file copies)

Spec: specs/LIBRARY_SPEC_L3.md
"""

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from python.helpers.tool import Tool, Response

# ── Constants ─────────────────────────────────────────────────────────────────

LIBRARY_DIR      = "/a0/usr/library"
LIBRARY_DOCS_DIR = "/a0/usr/library/docs"
CATALOG_PATH     = "/a0/usr/library/catalog.json"
MEM_SUBDIR       = "library"

AREA_CHUNK      = "library"
AREA_BOOK       = "library_book"
AREA_COLLECTION = "library_collection"

CHUNK_SIZE    = 800
CHUNK_OVERLAP = 80
MAX_FILE_MB   = 200          # raised from 50 MB; warn but allow up to 200 MB
ROUTING_LIMIT = 10           # book candidates from routing stage
SEARCH_LIMIT  = 5            # default chunk results

# ── Catalog helpers ───────────────────────────────────────────────────────────

def _load_catalog() -> dict:
    if not os.path.exists(CATALOG_PATH):
        return {"version": "2.0", "collections": {}, "documents": []}
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # migrate v1.0 → v2.0
        if data.get("version") == "1.0":
            data["version"] = "2.0"
            if "collections" not in data:
                data["collections"] = {}
        return data
    except Exception:
        return {"version": "2.0", "collections": {}, "documents": []}


def _save_catalog(catalog: dict) -> None:
    os.makedirs(LIBRARY_DIR, exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)


def _make_id(prefix: str, seed: str) -> str:
    return prefix + "_" + hashlib.sha256(seed.encode()).hexdigest()[:8]


def _safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


def _infer_format(path: str) -> str:
    ext = Path(path).suffix.lower().lstrip(".")
    return ext if ext in ("pdf", "txt", "md", "html", "htm", "epub") else "unknown"


def _parse_topics(topics) -> List[str]:
    if not topics:
        return []
    if isinstance(topics, list):
        return [t.strip() for t in topics if t.strip()]
    if isinstance(topics, str):
        return [t.strip() for t in topics.split(",") if t.strip()]
    return []


def _get_or_create_collection(catalog: dict, name: str, summary: str = "") -> str:
    """Return collection_id for name, creating entry if absent."""
    col_id = _make_id("col", name)
    if col_id not in catalog["collections"]:
        catalog["collections"][col_id] = {
            "collection_id": col_id,
            "name": name,
            "summary": summary or f"{name} reference collection.",
            "book_ids": [],
            "book_count": 0,
        }
    return col_id


def _find_book(catalog: dict, library_id: str) -> Optional[dict]:
    return next((d for d in catalog["documents"] if d.get("library_id") == library_id), None)


def _find_collection_by_name(catalog: dict, name: str) -> Optional[dict]:
    name_lower = name.lower()
    for col in catalog["collections"].values():
        if col["name"].lower() == name_lower or name_lower in col["name"].lower():
            return col
    return None

# ── Memory helper ─────────────────────────────────────────────────────────────

async def _get_lib_memory():
    from python.helpers.memory import Memory
    return await Memory.get_by_subdir(MEM_SUBDIR, preload_knowledge=False)

# ── Tools ─────────────────────────────────────────────────────────────────────

class LibraryAdd(Tool):
    """
    Ingest a document into the Exocortex library.

    Args:
      path        — absolute path to file in container (required)
      title       — human label (default: filename stem)
      collection  — collection name, e.g. "Hacking 2.0" (default: parent folder name)
      author      — author string (optional)
      topics      — comma-separated topic tags (optional)
      notes       — free-text annotation (optional)
    """

    async def execute(self, **kwargs) -> Response:
        path       = str(kwargs.get("path", "")).strip()
        title      = str(kwargs.get("title", "")).strip()
        collection = str(kwargs.get("collection", "")).strip()
        author     = str(kwargs.get("author", "")).strip()
        topics     = _parse_topics(kwargs.get("topics", []))
        notes      = str(kwargs.get("notes", "")).strip()

        if not path:
            return Response(message="[LIBRARY] Error: 'path' argument required.", break_loop=False)
        if not os.path.exists(path):
            return Response(message=f"[LIBRARY] Error: file not found: {path}", break_loop=False)

        file_mb = os.path.getsize(path) / 1024 / 1024
        if file_mb > MAX_FILE_MB:
            return Response(
                message=f"[LIBRARY] Error: file too large ({file_mb:.1f} MB, max {MAX_FILE_MB} MB). "
                        f"Use library_batch_ingest for very large files.",
                break_loop=False,
            )

        if not title:
            title = Path(path).stem.replace("_", " ").replace("-", " ").title()
        if not collection:
            collection = Path(path).parent.name or "General"

        fmt = _infer_format(path)

        catalog = _load_catalog()

        # Duplicate check
        existing = next((d for d in catalog["documents"] if d.get("original_path") == path), None)
        if existing:
            return Response(
                message=f"[LIBRARY] '{title}' already in library as {existing['library_id']}. "
                        f"Use library_remove first to re-ingest.",
                break_loop=False,
            )

        # Copy file to library docs dir
        os.makedirs(LIBRARY_DOCS_DIR, exist_ok=True)
        dest_name = _safe_filename(Path(path).name)
        dest_path = os.path.join(LIBRARY_DOCS_DIR, dest_name)
        if os.path.exists(dest_path) and dest_path != path:
            stem, suffix = os.path.splitext(dest_name)
            dest_name = f"{stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"
            dest_path = os.path.join(LIBRARY_DOCS_DIR, dest_name)
        if path != dest_path:
            shutil.copy2(path, dest_path)

        # Extract text
        if file_mb > 50:
            print(f"[LIB-ADD] Large file ({file_mb:.0f} MB) — extraction may take a moment...", flush=True)
        try:
            from python.helpers.document_query import DocumentQueryHelper
            helper = DocumentQueryHelper(self.agent)
            doc_uri = f"file://{dest_path}"
            text = await helper.document_get_content(doc_uri, add_to_db=False)
        except Exception as e:
            return Response(message=f"[LIBRARY] Error extracting text: {e}", break_loop=False)

        if not text or not text.strip():
            return Response(
                message=f"[LIBRARY] Error: no text extracted from '{path}'. "
                        f"File may be encrypted or image-only without OCR.",
                break_loop=False,
            )

        # Chunk
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        chunks = splitter.split_text(text)
        if not chunks:
            return Response(message="[LIBRARY] Error: no chunks produced.", break_loop=False)

        added_date  = datetime.now().isoformat(timespec="seconds")
        library_id  = _make_id("lib", title + added_date)
        col_id      = _get_or_create_collection(catalog, collection)
        topics_json = json.dumps(topics)
        book_summary = text[:500].replace("\n", " ").strip()

        # Build chunk documents
        chunk_docs = [
            Document(
                page_content=chunk,
                metadata={
                    "area": AREA_CHUNK,
                    "library_id": library_id,
                    "collection_id": col_id,
                    "document_uri": doc_uri,
                    "title": title,
                    "collection": collection,
                    "topics": topics_json,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "added_date": added_date,
                },
            )
            for i, chunk in enumerate(chunks)
        ]

        # Book routing document (summary proxy for two-stage search)
        book_doc = Document(
            page_content=f"{title}. {book_summary}",
            metadata={
                "area": AREA_BOOK,
                "library_id": library_id,
                "collection_id": col_id,
                "title": title,
                "collection": collection,
                "added_date": added_date,
            },
        )

        try:
            lib_mem = await _get_lib_memory()
            await lib_mem.insert_documents(chunk_docs + [book_doc])
        except Exception as e:
            return Response(message=f"[LIBRARY] Error storing to FAISS: {e}", break_loop=False)

        # Update catalog
        entry = {
            "library_id":    library_id,
            "collection_id": col_id,
            "title":         title,
            "author":        author,
            "format":        fmt,
            "source_path":   dest_path,
            "original_path": path,
            "added_date":    added_date,
            "topics":        topics,
            "chunk_count":   len(chunks),
            "notes":         notes,
        }
        catalog["documents"].append(entry)
        col = catalog["collections"][col_id]
        if library_id not in col["book_ids"]:
            col["book_ids"].append(library_id)
            col["book_count"] = len(col["book_ids"])
        _save_catalog(catalog)

        print(f"[LIB-ADD] '{title}' ({library_id}) → {collection} — {len(chunks)} chunks", flush=True)
        return Response(
            message=(
                f"[LIBRARY] Added \"{title}\" to collection \"{collection}\"\n"
                f"library_id: {library_id}\n"
                f"Chunks: {len(chunks)}  |  Topics: {', '.join(topics) or '(none)'}\n"
                f"Use library_search to query it."
            ),
            break_loop=False,
        )


class LibraryList(Tool):
    """
    List the library.

    With no arguments: shows all collections with summaries and book counts.
    With collection="name": lists books within that collection.

    Args:
      collection — collection name (optional; substring match)
      topic      — filter books by topic tag (optional)
    """

    async def execute(self, **kwargs) -> Response:
        collection_filter = str(kwargs.get("collection", "")).strip()
        topic_filter      = str(kwargs.get("topic", "")).strip().lower()

        catalog = _load_catalog()
        collections = catalog.get("collections", {})
        documents   = catalog.get("documents", [])

        if not documents:
            return Response(
                message="[LIBRARY] Library is empty. Use library_add to ingest documents.",
                break_loop=False,
            )

        # Collection view (no filter, or collection specified)
        if collection_filter:
            col = _find_collection_by_name(catalog, collection_filter)
            if not col:
                return Response(
                    message=f"[LIBRARY] No collection matching '{collection_filter}'.",
                    break_loop=False,
                )
            books = [d for d in documents if d.get("collection_id") == col["collection_id"]]
            if topic_filter:
                books = [b for b in books if any(topic_filter in t.lower() for t in b.get("topics", []))]

            lines = [f"[LIBRARY — {col['name']}]  {col.get('summary', '')}"]
            lines.append(f"  {len(books)} book(s)\n")
            lines.append(f"  {'library_id':<16} {'title':<45} {'chunks':>6}  added")
            lines.append("  " + "-" * 80)
            for b in books:
                lid    = b.get("library_id", "")
                title  = b.get("title", "")[:43]
                chunks = b.get("chunk_count", 0)
                added  = b.get("added_date", "")[:10]
                lines.append(f"  {lid:<16} {title:<45} {chunks:>6}  {added}")
            return Response(message="\n".join(lines), break_loop=False)

        # Top-level collection summary view
        total_books = len(documents)
        total_cols  = len(collections)
        lines = [f"[LIBRARY — {total_books} books across {total_cols} collection(s)]", ""]
        lines.append(f"  {'collection_id':<16} {'name':<35} {'books':>5}  summary")
        lines.append("  " + "-" * 95)
        for col in sorted(collections.values(), key=lambda c: c["name"]):
            cid     = col["collection_id"]
            name    = col["name"][:33]
            count   = col.get("book_count", len(col.get("book_ids", [])))
            summary = col.get("summary", "")[:50]
            lines.append(f"  {cid:<16} {name:<35} {count:>5}  {summary}")
        lines.append("")
        lines.append("  Use library_list collection=\"<name>\" to see books in a collection.")
        lines.append("  Use library_search to find relevant content.")
        return Response(message="\n".join(lines), break_loop=False)


class LibrarySearch(Tool):
    """
    Two-stage semantic search across the library.

    Stage 1: find the most relevant books using book-level summary routing.
    Stage 2: search content chunks within only those books.

    Args:
      query         — natural language search query (required)
      library_id    — restrict to one book, skip routing (optional)
      collection    — restrict to one collection (optional)
      limit         — max chunk results (default 5, max 20)
    """

    async def execute(self, **kwargs) -> Response:
        query         = str(kwargs.get("query", "")).strip()
        library_id    = str(kwargs.get("library_id", "")).strip()
        collection_q  = str(kwargs.get("collection", "")).strip()
        limit         = min(int(kwargs.get("limit", SEARCH_LIMIT)), 20)

        if not query:
            return Response(message="[LIBRARY] Error: 'query' argument required.", break_loop=False)

        lib_mem = await _get_lib_memory()

        # Resolve collection_id from name if provided
        collection_id = ""
        if collection_q and not library_id:
            catalog = _load_catalog()
            col = _find_collection_by_name(catalog, collection_q)
            if col:
                collection_id = col["collection_id"]

        try:
            chunks = await _two_stage_search(
                query=query,
                lib_mem=lib_mem,
                limit=limit,
                library_id=library_id or None,
                collection_id=collection_id or None,
            )
        except Exception as e:
            return Response(message=f"[LIBRARY] Search error: {e}", break_loop=False)

        if not chunks:
            scope = ""
            if library_id:   scope = f" in book {library_id}"
            elif collection_q: scope = f" in collection '{collection_q}'"
            return Response(
                message=f"[LIBRARY SEARCH: \"{query}\"]{scope} — no results above threshold.",
                break_loop=False,
            )

        scope_label = ""
        if library_id:    scope_label = f" (book {library_id})"
        elif collection_q: scope_label = f" (collection: {collection_q})"
        lines = [f"[LIBRARY SEARCH: \"{query}\"]{scope_label} — {len(chunks)} result(s)\n"]

        for i, doc in enumerate(chunks, 1):
            meta       = doc.metadata
            title      = meta.get("title", "unknown")
            lid        = meta.get("library_id", "")
            collection = meta.get("collection", "")
            ci         = meta.get("chunk_index", "?")
            total      = meta.get("total_chunks", "?")
            snippet    = doc.page_content[:350].replace("\n", " ")
            if len(doc.page_content) > 350:
                snippet += "..."
            lines.append(f"{i}. {title}  [{collection}]  ({lid}, chunk {ci}/{total})")
            lines.append(f"   \"{snippet}\"\n")

        return Response(message="\n".join(lines), break_loop=False)


class LibraryRemove(Tool):
    """
    Remove a document from the library.
    Deletes content chunks, book routing entry, catalog entry, and file copy.

    Args:
      library_id — the lib_xxxxxxxx ID from library_list (required)
    """

    async def execute(self, **kwargs) -> Response:
        library_id = str(kwargs.get("library_id", "")).strip()
        if not library_id:
            return Response(message="[LIBRARY] Error: 'library_id' required.", break_loop=False)

        catalog = _load_catalog()
        entry   = _find_book(catalog, library_id)
        if not entry:
            return Response(
                message=f"[LIBRARY] library_id '{library_id}' not found.", break_loop=False
            )

        title = entry.get("title", library_id)

        # Remove all FAISS entries (chunks + book routing)
        chunk_count = 0
        try:
            lib_mem  = await _get_lib_memory()
            all_docs = lib_mem.db.get_all_docs()
            ids = [
                doc_id for doc_id, doc in all_docs.items()
                if doc.metadata.get("library_id") == library_id
            ]
            if ids:
                await lib_mem.delete_documents_by_ids(ids)
                chunk_count = len(ids)
        except Exception as e:
            return Response(
                message=f"[LIBRARY] Error removing from FAISS: {e}", break_loop=False
            )

        # Remove file copy
        src = entry.get("source_path", "")
        if src and os.path.exists(src):
            try:
                os.remove(src)
            except OSError:
                pass

        # Update collections
        col_id = entry.get("collection_id", "")
        if col_id and col_id in catalog["collections"]:
            col = catalog["collections"][col_id]
            col["book_ids"] = [b for b in col["book_ids"] if b != library_id]
            col["book_count"] = len(col["book_ids"])
            # Remove empty collections
            if col["book_count"] == 0:
                del catalog["collections"][col_id]

        catalog["documents"] = [
            d for d in catalog["documents"] if d.get("library_id") != library_id
        ]
        _save_catalog(catalog)

        print(f"[LIB-REMOVE] '{title}' ({library_id}) — {chunk_count} entries deleted", flush=True)
        return Response(
            message=f"[LIBRARY] Removed \"{title}\" ({library_id}) — {chunk_count} FAISS entries deleted.",
            break_loop=False,
        )


class LibraryCollections(Tool):
    """
    List all collections with summaries and book counts.
    Alias for library_list with no arguments — useful for an explicit collections overview.

    Args:
      update_summary — update the summary for a collection
        collection   — collection name (required with update_summary)
        summary      — new 1-sentence summary (required with update_summary)
    """

    async def execute(self, **kwargs) -> Response:
        update = kwargs.get("update_summary", False)

        if update:
            collection_name = str(kwargs.get("collection", "")).strip()
            new_summary     = str(kwargs.get("summary", "")).strip()
            if not collection_name or not new_summary:
                return Response(
                    message="[LIBRARY] update_summary requires both 'collection' and 'summary'.",
                    break_loop=False,
                )
            catalog = _load_catalog()
            col = _find_collection_by_name(catalog, collection_name)
            if not col:
                return Response(
                    message=f"[LIBRARY] No collection matching '{collection_name}'.",
                    break_loop=False,
                )
            old = col["summary"]
            col["summary"] = new_summary

            # Re-embed the collection routing entry
            try:
                lib_mem  = await _get_lib_memory()
                all_docs = lib_mem.db.get_all_docs()
                old_ids  = [
                    doc_id for doc_id, doc in all_docs.items()
                    if doc.metadata.get("area") == AREA_COLLECTION
                    and doc.metadata.get("collection_id") == col["collection_id"]
                ]
                if old_ids:
                    await lib_mem.delete_documents_by_ids(old_ids)
                col_doc = Document(
                    page_content=f"{col['name']}. {new_summary}",
                    metadata={
                        "area": AREA_COLLECTION,
                        "collection_id": col["collection_id"],
                        "name": col["name"],
                    },
                )
                await lib_mem.insert_documents([col_doc])
            except Exception as e:
                return Response(
                    message=f"[LIBRARY] Catalog updated but FAISS re-embed failed: {e}",
                    break_loop=False,
                )

            _save_catalog(catalog)
            return Response(
                message=f"[LIBRARY] Collection \"{col['name']}\" summary updated.\n"
                        f"  Old: {old}\n  New: {new_summary}",
                break_loop=False,
            )

        # Default: display all collections
        catalog     = _load_catalog()
        collections = catalog.get("collections", {})
        documents   = catalog.get("documents", [])

        if not collections:
            return Response(
                message="[LIBRARY] No collections yet. Use library_add to ingest documents.",
                break_loop=False,
            )

        lines = [f"[LIBRARY COLLECTIONS — {len(collections)} total, {len(documents)} books]\n"]
        for col in sorted(collections.values(), key=lambda c: c["name"]):
            count   = col.get("book_count", 0)
            summary = col.get("summary", "(no summary)")
            lines.append(f"  {col['collection_id']}  {col['name']}  ({count} books)")
            lines.append(f"    {summary}")
            lines.append("")
        lines.append("Use library_collections update_summary=true collection=\"...\" summary=\"...\" to refine a summary.")
        return Response(message="\n".join(lines), break_loop=False)


# ── Two-stage search ──────────────────────────────────────────────────────────

async def _two_stage_search(
    query: str,
    lib_mem,
    limit: int = 5,
    library_id: Optional[str] = None,
    collection_id: Optional[str] = None,
) -> List[Document]:
    """
    Stage 1: find relevant books via book routing entries.
    Stage 2: search content chunks filtered to those books.

    If library_id is given, skip routing and search only that book's chunks.
    If collection_id is given, restrict routing to books in that collection.
    """

    # Direct scoped search — no routing needed
    if library_id:
        chunk_filter = f"area == '{AREA_CHUNK}' and library_id == '{library_id}'"
        return await lib_mem.search_similarity_threshold(
            query=query, limit=limit, threshold=0.4, filter=chunk_filter
        )

    # Stage 1: route against book summaries
    book_filter = f"area == '{AREA_BOOK}'"
    if collection_id:
        book_filter += f" and collection_id == '{collection_id}'"

    book_hits = await lib_mem.search_similarity_threshold(
        query=query, limit=ROUTING_LIMIT, threshold=0.25, filter=book_filter
    )

    if not book_hits:
        # Fallback: flat search across all chunks (library is empty or routing fails)
        chunk_filter = f"area == '{AREA_CHUNK}'"
        if collection_id:
            chunk_filter += f" and collection_id == '{collection_id}'"
        return await lib_mem.search_similarity_threshold(
            query=query, limit=limit, threshold=0.4, filter=chunk_filter
        )

    # Stage 2: search chunks within top routed books
    relevant_ids = list(dict.fromkeys(
        h.metadata.get("library_id", "") for h in book_hits
        if h.metadata.get("library_id")
    ))[:5]

    id_clauses   = " or ".join(f"library_id == '{lid}'" for lid in relevant_ids)
    chunk_filter = f"area == '{AREA_CHUNK}' and ({id_clauses})"

    results = await lib_mem.search_similarity_threshold(
        query=query, limit=limit, threshold=0.4, filter=chunk_filter
    )

    # If routing was too aggressive and filtered out good results, fall back
    if not results:
        chunk_filter_broad = f"area == '{AREA_CHUNK}'"
        if collection_id:
            chunk_filter_broad += f" and collection_id == '{collection_id}'"
        return await lib_mem.search_similarity_threshold(
            query=query, limit=limit, threshold=0.4, filter=chunk_filter_broad
        )

    return results
