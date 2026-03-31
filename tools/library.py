"""
library.py — Exocortex Document Library Tools
==============================================

Four tools for building and querying a persistent reference library:

  library_add    — ingest a local file into the library vector store
  library_list   — list catalogued documents (optionally filtered by topic)
  library_search — semantic search across the library or within one document
  library_remove — delete a document from the library

Storage:
  Catalog:   /a0/usr/library/catalog.json      (fast metadata index)
  Docs:      /a0/usr/library/docs/             (file copies for re-ingestion)
  FAISS:     /a0/usr/memory/library/           (persistent via Memory subdir)

All paths are under /a0/usr/ — DEC-030 compliant, survive container updates.
No LLM calls. No external dependencies beyond what Agent Zero already ships.

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
MEM_SUBDIR       = "library"          # → /a0/usr/memory/library/

CHUNK_SIZE    = 800
CHUNK_OVERLAP = 80
MAX_FILE_MB   = 50

# ── Catalog helpers ───────────────────────────────────────────────────────────

def _load_catalog() -> dict:
    if not os.path.exists(CATALOG_PATH):
        return {"version": "1.0", "documents": []}
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"version": "1.0", "documents": []}


def _save_catalog(catalog: dict) -> None:
    os.makedirs(LIBRARY_DIR, exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)


def _make_library_id(title: str, added_date: str) -> str:
    raw = f"{title}:{added_date}"
    return "lib_" + hashlib.sha256(raw.encode()).hexdigest()[:8]


def _safe_filename(name: str) -> str:
    """Turn an arbitrary name into a filesystem-safe filename."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


def _infer_format(path: str) -> str:
    ext = Path(path).suffix.lower().lstrip(".")
    return ext if ext in ("pdf", "txt", "md", "html", "htm") else "unknown"


def _parse_topics(topics) -> List[str]:
    if not topics:
        return []
    if isinstance(topics, list):
        return [t.strip() for t in topics if t.strip()]
    if isinstance(topics, str):
        return [t.strip() for t in topics.split(",") if t.strip()]
    return []

# ── Memory helpers ────────────────────────────────────────────────────────────

async def _get_lib_memory():
    """Return the persistent library Memory instance."""
    from python.helpers.memory import Memory
    return await Memory.get_by_subdir(MEM_SUBDIR, preload_knowledge=False)


# ── Tools ─────────────────────────────────────────────────────────────────────

class LibraryAdd(Tool):
    """
    Add a document to the Exocortex library.
    Extracts text, chunks it, stores in persistent FAISS, updates catalog.
    """

    async def execute(self, **kwargs) -> Response:
        path      = str(kwargs.get("path", "")).strip()
        title     = str(kwargs.get("title", "")).strip()
        author    = str(kwargs.get("author", "")).strip()
        topics    = _parse_topics(kwargs.get("topics", []))
        notes     = str(kwargs.get("notes", "")).strip()

        if not path:
            return Response(message="[LIBRARY] Error: 'path' argument required.", break_loop=False)

        if not os.path.exists(path):
            return Response(message=f"[LIBRARY] Error: file not found: {path}", break_loop=False)

        file_mb = os.path.getsize(path) / 1024 / 1024
        if file_mb > MAX_FILE_MB:
            return Response(
                message=f"[LIBRARY] Error: file too large ({file_mb:.1f} MB, max {MAX_FILE_MB} MB)",
                break_loop=False,
            )

        # Default title from filename
        if not title:
            title = Path(path).stem.replace("_", " ").replace("-", " ").title()

        fmt = _infer_format(path)

        # Check for duplicate by original_path
        catalog = _load_catalog()
        existing = next(
            (d for d in catalog["documents"] if d.get("original_path") == path), None
        )
        if existing:
            return Response(
                message=(
                    f"[LIBRARY] '{title}' already in library as {existing['library_id']}. "
                    f"Use library_remove first to re-ingest."
                ),
                break_loop=False,
            )

        # Copy file to library docs dir
        os.makedirs(LIBRARY_DOCS_DIR, exist_ok=True)
        dest_name = _safe_filename(Path(path).name)
        dest_path = os.path.join(LIBRARY_DOCS_DIR, dest_name)
        # Avoid overwriting if same filename already exists from a different source
        if os.path.exists(dest_path) and dest_path != path:
            stem, suffix = os.path.splitext(dest_name)
            added_ts = datetime.now().strftime("%Y%m%d%H%M%S")
            dest_name = f"{stem}_{added_ts}{suffix}"
            dest_path = os.path.join(LIBRARY_DOCS_DIR, dest_name)
        if path != dest_path:
            shutil.copy2(path, dest_path)

        # Extract text via DocumentQueryHelper (handles PDF, HTML, text, images)
        try:
            from python.helpers.document_query import DocumentQueryHelper
            helper = DocumentQueryHelper(self.agent)
            doc_uri = f"file://{dest_path}"
            text = await helper.document_get_content(doc_uri, add_to_db=False)
        except Exception as e:
            return Response(
                message=f"[LIBRARY] Error extracting text from '{path}': {e}",
                break_loop=False,
            )

        if not text or not text.strip():
            return Response(
                message=f"[LIBRARY] Error: no text extracted from '{path}'. File may be encrypted or image-only without OCR.",
                break_loop=False,
            )

        # Chunk
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        chunks = splitter.split_text(text)
        if not chunks:
            return Response(
                message=f"[LIBRARY] Error: text extracted but no chunks produced.",
                break_loop=False,
            )

        added_date = datetime.now().isoformat(timespec="seconds")
        library_id = _make_library_id(title, added_date)
        topics_json = json.dumps(topics)

        docs = [
            Document(
                page_content=chunk,
                metadata={
                    "area": "library",
                    "library_id": library_id,
                    "document_uri": doc_uri,
                    "title": title,
                    "topics": topics_json,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "added_date": added_date,
                },
            )
            for i, chunk in enumerate(chunks)
        ]

        # Insert into persistent library FAISS store
        try:
            lib_mem = await _get_lib_memory()
            await lib_mem.insert_documents(docs)
        except Exception as e:
            return Response(
                message=f"[LIBRARY] Error storing chunks: {e}",
                break_loop=False,
            )

        # Update catalog
        entry = {
            "library_id":    library_id,
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
        _save_catalog(catalog)

        print(f"[LIB-ADD] '{title}' ({library_id}) — {len(chunks)} chunks ingested", flush=True)
        return Response(
            message=(
                f"[LIBRARY] Added \"{title}\" — {len(chunks)} chunks indexed.\n"
                f"library_id: {library_id}\n"
                f"Topics: {', '.join(topics) if topics else '(none)'}\n"
                f"Use library_search to query it."
            ),
            break_loop=False,
        )


class LibraryList(Tool):
    """
    List documents in the Exocortex library.
    Optional topic filter: library_list topic="consensus"
    """

    async def execute(self, **kwargs) -> Response:
        topic_filter = str(kwargs.get("topic", "")).strip().lower()

        catalog = _load_catalog()
        docs = catalog.get("documents", [])

        if not docs:
            return Response(
                message="[LIBRARY] Library is empty. Use library_add to ingest documents.",
                break_loop=False,
            )

        if topic_filter:
            docs = [
                d for d in docs
                if any(topic_filter in t.lower() for t in d.get("topics", []))
            ]
            if not docs:
                return Response(
                    message=f"[LIBRARY] No documents found with topic matching '{topic_filter}'.",
                    break_loop=False,
                )

        lines = [f"[LIBRARY — {len(docs)} document(s)]"]
        lines.append(f"{'library_id':<16} {'title':<40} {'topics':<35} {'chunks':>6}  added")
        lines.append("-" * 110)
        for d in docs:
            lid     = d.get("library_id", "")[:16]
            title   = d.get("title", "")[:38]
            topics  = ", ".join(d.get("topics", []))[:33]
            chunks  = d.get("chunk_count", 0)
            added   = d.get("added_date", "")[:10]
            lines.append(f"{lid:<16} {title:<40} {topics:<35} {chunks:>6}  {added}")

        return Response(message="\n".join(lines), break_loop=False)


class LibrarySearch(Tool):
    """
    Semantic search across the Exocortex library.

    Args:
      query      — natural language search query (required)
      library_id — restrict search to one document (optional)
      limit      — max results (default 5, max 20)
    """

    async def execute(self, **kwargs) -> Response:
        query      = str(kwargs.get("query", "")).strip()
        library_id = str(kwargs.get("library_id", "")).strip()
        limit      = min(int(kwargs.get("limit", 5)), 20)

        if not query:
            return Response(message="[LIBRARY] Error: 'query' argument required.", break_loop=False)

        lib_mem = await _get_lib_memory()

        # Build filter
        search_filter = "area == 'library'"
        if library_id:
            search_filter += f" and library_id == '{library_id}'"

        try:
            results = await lib_mem.search_similarity_threshold(
                query=query,
                limit=limit,
                threshold=0.4,
                filter=search_filter,
            )
        except Exception as e:
            return Response(message=f"[LIBRARY] Search error: {e}", break_loop=False)

        if not results:
            scope = f" in {library_id}" if library_id else ""
            return Response(
                message=f"[LIBRARY SEARCH: \"{query}\"]{scope} — no results above threshold.",
                break_loop=False,
            )

        scope_label = f" (scoped to {library_id})" if library_id else ""
        lines = [f"[LIBRARY SEARCH: \"{query}\"]{scope_label} — {len(results)} result(s)\n"]

        for i, doc in enumerate(results, 1):
            meta    = doc.metadata
            title   = meta.get("title", "unknown")
            lid     = meta.get("library_id", "")
            ci      = meta.get("chunk_index", "?")
            total   = meta.get("total_chunks", "?")
            snippet = doc.page_content[:350].replace("\n", " ")
            if len(doc.page_content) > 350:
                snippet += "..."
            lines.append(f"{i}. {title} ({lid}, chunk {ci}/{total})")
            lines.append(f"   \"{snippet}\"\n")

        return Response(message="\n".join(lines), break_loop=False)


class LibraryRemove(Tool):
    """
    Remove a document from the Exocortex library.
    Deletes all FAISS chunks and the catalog entry.

    Args:
      library_id — the lib_xxxxxxxx ID (required; get it from library_list)
    """

    async def execute(self, **kwargs) -> Response:
        library_id = str(kwargs.get("library_id", "")).strip()

        if not library_id:
            return Response(
                message="[LIBRARY] Error: 'library_id' argument required.",
                break_loop=False,
            )

        catalog = _load_catalog()
        entry = next(
            (d for d in catalog["documents"] if d.get("library_id") == library_id), None
        )
        if not entry:
            return Response(
                message=f"[LIBRARY] library_id '{library_id}' not found in catalog.",
                break_loop=False,
            )

        title = entry.get("title", library_id)

        # Remove chunks from FAISS
        chunk_count = 0
        try:
            lib_mem = await _get_lib_memory()
            all_docs = lib_mem.db.get_all_docs()
            ids_to_remove = [
                doc_id
                for doc_id, doc in all_docs.items()
                if doc.metadata.get("library_id") == library_id
            ]
            if ids_to_remove:
                await lib_mem.delete_documents_by_ids(ids_to_remove)
                chunk_count = len(ids_to_remove)
        except Exception as e:
            return Response(
                message=f"[LIBRARY] Error removing chunks for {library_id}: {e}",
                break_loop=False,
            )

        # Remove file from docs dir if present
        source_path = entry.get("source_path", "")
        if source_path and os.path.exists(source_path):
            try:
                os.remove(source_path)
            except OSError:
                pass

        # Remove from catalog
        catalog["documents"] = [
            d for d in catalog["documents"] if d.get("library_id") != library_id
        ]
        _save_catalog(catalog)

        print(f"[LIB-REMOVE] '{title}' ({library_id}) — {chunk_count} chunks deleted", flush=True)
        return Response(
            message=f"[LIBRARY] Removed \"{title}\" ({library_id}) — {chunk_count} chunks deleted.",
            break_loop=False,
        )
