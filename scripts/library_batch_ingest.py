#!/usr/bin/env python3
"""
library_batch_ingest.py — Exocortex Library Batch Ingest

Ingests entire directory trees of books/documents into the library without
the agent needing to call library_add one file at a time.

Usage:
    python library_batch_ingest.py <root_dir> [options]

Options:
    --container     Container name (default: flamboyant_bell)
    --collection    Override collection name (default: use subfolder name)
    --dry-run       Show what would be ingested without doing it
    --only-new      Skip files already in the catalog (default: True)
    --limit N       Process at most N files (useful for testing)
    --log FILE      Write progress log to FILE (default: stdout only)
    --skip-errors   Continue on individual file failures (default: True)

Behavior:
    - Walks <root_dir> recursively
    - Groups files by immediate parent folder → collection
    - Calls library_add for each eligible file via Agent Zero's API
    - Reports per-collection progress and final summary

File filter:
    - Supported: .pdf .txt .md .html .htm .epub
    - Skipped: hidden files, system files, > 200 MB

Example:
    # Ingest the full Humble Bundle collection from inside the container
    python scripts/library_batch_ingest.py /a0/usr/workdir/books

    # Dry run first to see what would happen
    python scripts/library_batch_ingest.py /a0/usr/workdir/books --dry-run

    # Ingest only the Hacking folder
    python scripts/library_batch_ingest.py "/a0/usr/workdir/books/Hacking 2.0"

This script runs LOCALLY (on the Windows host or inside the container)
and talks to the Agent Zero REST API to invoke library_add. The agent
handles all the FAISS logic — this script is just a file-system walker
and API caller.

Alternatively, run it directly inside the container with --direct flag,
which imports library.py directly (bypasses Agent Zero).
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm", ".epub"}
MAX_FILE_MB          = 200
DEFAULT_CONTAINER    = "flamboyant_bell"


def parse_args():
    p = argparse.ArgumentParser(
        description="Batch-ingest a directory tree into the Exocortex library."
    )
    p.add_argument("root_dir", help="Root directory to walk")
    p.add_argument("--container",  default=DEFAULT_CONTAINER,  help="Agent Zero container name")
    p.add_argument("--collection", default="",   help="Override collection name (default: parent folder)")
    p.add_argument("--dry-run",    action="store_true",         help="Show files without ingesting")
    p.add_argument("--only-new",   action="store_true", default=True, help="Skip already-ingested files")
    p.add_argument("--limit",      type=int, default=0,         help="Max files to process (0=all)")
    p.add_argument("--log",        default="",                  help="Write log to this file")
    p.add_argument("--skip-errors", action="store_true", default=True)
    p.add_argument("--direct",     action="store_true",         help="Run inside container, import library.py directly")
    p.add_argument("--api-url",    default="",                  help="Agent Zero API URL (if not --direct)")
    p.add_argument("--api-key",    default="",                  help="Agent Zero API key (if not --direct)")
    return p.parse_args()


# ── File discovery ─────────────────────────────────────────────────────────────

def discover_files(root: Path):
    """Walk root, yield (file_path, collection_name) pairs."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        dirpath_obj = Path(dirpath)

        # Collection = immediate child of root, or root itself
        try:
            rel = dirpath_obj.relative_to(root)
            parts = rel.parts
            collection = parts[0] if parts else root.name
        except ValueError:
            collection = root.name

        for filename in sorted(filenames):
            if filename.startswith("."):
                continue
            filepath = dirpath_obj / filename
            if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            try:
                size_mb = filepath.stat().st_size / 1024 / 1024
            except OSError:
                continue
            if size_mb > MAX_FILE_MB:
                print(f"  SKIP (too large: {size_mb:.0f} MB): {filepath}")
                continue
            yield filepath, collection


def load_existing_catalog(catalog_path="/a0/usr/workdir/library/catalog.json"):
    """Return set of original_path values already in the catalog."""
    if not os.path.exists(catalog_path):
        return set()
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {d.get("original_path", "") for d in data.get("documents", [])}
    except Exception:
        return set()


# ── Direct mode (inside container, no API) ────────────────────────────────────

def run_direct(args):
    """
    Import library.py directly and call LibraryAdd without Agent Zero.
    Requires running inside the container (or with A0 on PYTHONPATH).
    """
    # Set up Python path
    sys.path.insert(0, "/a0")
    sys.path.insert(0, "/a0/python")

    import asyncio

    # Lazy import after path setup
    from tools.library import _load_catalog, _save_catalog, _get_or_create_collection
    from tools.library import _safe_filename, _infer_format, _parse_topics, _make_id
    from tools.library import LIBRARY_DOCS_DIR, CATALOG_PATH, MEM_SUBDIR  # workdir paths
    from tools.library import AREA_CHUNK, AREA_BOOK, CHUNK_SIZE, CHUNK_OVERLAP
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    from python.helpers.memory import Memory
    from python.helpers.document_query import DocumentQueryHelper
    import shutil
    from datetime import datetime

    root   = Path(args.root_dir)
    files  = list(discover_files(root))
    log    = open(args.log, "a", encoding="utf-8") if args.log else None

    def emit(msg):
        print(msg)
        if log:
            log.write(msg + "\n")
            log.flush()

    existing = load_existing_catalog(CATALOG_PATH) if args.only_new else set()
    total = skipped = added = failed = 0

    emit(f"\n[BATCH] Direct mode — {len(files)} eligible files in {root}")
    if args.dry_run:
        emit("[BATCH] DRY RUN — no changes will be made\n")

    async def _ingest_one(filepath, collection_name):
        nonlocal added, failed, skipped
        total_ref = [0]

        path_str = str(filepath)
        if args.only_new and path_str in existing:
            emit(f"  SKIP (already in library): {filepath.name}")
            skipped += 1
            return

        title = filepath.stem.replace("_", " ").replace("-", " ").title()
        collection = args.collection or collection_name

        emit(f"  ADD  [{collection}] {filepath.name}")
        if args.dry_run:
            return

        try:
            os.makedirs(LIBRARY_DOCS_DIR, exist_ok=True)
            dest_name = _safe_filename(filepath.name)
            dest_path = os.path.join(LIBRARY_DOCS_DIR, dest_name)
            if os.path.exists(dest_path) and dest_path != path_str:
                stem, sfx = os.path.splitext(dest_name)
                dest_name = f"{stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}{sfx}"
                dest_path = os.path.join(LIBRARY_DOCS_DIR, dest_name)
            if path_str != dest_path:
                shutil.copy2(path_str, dest_path)

            # Extract text (no agent context available — use document_query directly)
            try:
                from python.helpers.document_query import DocumentQueryHelper as DQH

                class _FakeAgent:
                    config = type("c", (), {"code_exec_docker_enabled": False, "code_exec_ssh_enabled": False})()
                    def __init__(self): pass

                helper = DQH(_FakeAgent())
                doc_uri = f"file://{dest_path}"
                text = await helper.document_get_content(doc_uri, add_to_db=False)
            except Exception:
                # Fallback: plain text read
                try:
                    text = Path(dest_path).read_text(encoding="utf-8", errors="replace")
                except Exception as e2:
                    raise RuntimeError(f"text extraction failed: {e2}")

            if not text or not text.strip():
                raise RuntimeError("no text extracted")

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
            )
            chunks = splitter.split_text(text)
            if not chunks:
                raise RuntimeError("no chunks produced")

            added_date  = datetime.now().isoformat(timespec="seconds")
            library_id  = _make_id("lib", title + added_date)

            catalog = _load_catalog()
            col_id  = _get_or_create_collection(catalog, collection)
            topics_json = "[]"
            book_summary = text[:500].replace("\n", " ").strip()

            chunk_docs = [
                Document(
                    page_content=chunk,
                    metadata={
                        "area": AREA_CHUNK,
                        "library_id": library_id,
                        "collection_id": col_id,
                        "document_uri": f"file://{dest_path}",
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

            lib_mem = await Memory.get_by_subdir(MEM_SUBDIR, preload_knowledge=False)
            await lib_mem.insert_documents(chunk_docs + [book_doc])

            entry = {
                "library_id":    library_id,
                "collection_id": col_id,
                "title":         title,
                "author":        "",
                "format":        _infer_format(path_str),
                "source_path":   dest_path,
                "original_path": path_str,
                "added_date":    added_date,
                "topics":        [],
                "chunk_count":   len(chunks),
                "notes":         "",
            }
            catalog["documents"].append(entry)
            col = catalog["collections"][col_id]
            if library_id not in col["book_ids"]:
                col["book_ids"].append(library_id)
                col["book_count"] = len(col["book_ids"])
            _save_catalog(catalog)

            emit(f"       → {len(chunks)} chunks  ({library_id})")
            added += 1

        except Exception as e:
            emit(f"  ERROR: {filepath.name} — {e}")
            failed += 1
            if not args.skip_errors:
                raise

    async def _run_all():
        count = 0
        # Group by collection for cleaner output
        by_col: dict = {}
        for fp, col in files:
            by_col.setdefault(col, []).append(fp)

        for col_name in sorted(by_col):
            emit(f"\n[COLLECTION] {col_name} — {len(by_col[col_name])} file(s)")
            for fp in by_col[col_name]:
                await _ingest_one(fp, col_name)
                count += 1
                if args.limit and count >= args.limit:
                    emit(f"\n[BATCH] --limit {args.limit} reached, stopping.")
                    return

    asyncio.run(_run_all())

    if log:
        log.close()

    emit(f"\n[BATCH COMPLETE]")
    emit(f"  Added   : {added}")
    emit(f"  Skipped : {skipped}  (already in library)")
    emit(f"  Failed  : {failed}")
    if args.dry_run:
        emit("  (dry run — no actual changes made)")


# ── API mode (talk to Agent Zero) ─────────────────────────────────────────────

def run_via_api(args):
    """
    Walk the directory and call Agent Zero's /api_message endpoint for each
    file, asking the agent to run library_add.

    Less efficient than --direct (one HTTP round-trip per file + LLM routing),
    but works from the Windows host without needing Python A0 deps.
    """
    import urllib.request
    import urllib.error

    api_url = args.api_url or "http://localhost:8008/api_message"
    api_key = args.api_key

    root  = Path(args.root_dir)
    files = list(discover_files(root))

    print(f"\n[BATCH] API mode — {len(files)} files, endpoint: {api_url}")
    if args.dry_run:
        print("[BATCH] DRY RUN\n")

    existing = set()  # API mode: rely on idempotency in library_add

    added = failed = skipped = 0
    for i, (filepath, collection_name) in enumerate(files):
        if args.limit and i >= args.limit:
            print(f"[BATCH] --limit {args.limit} reached.")
            break

        collection = args.collection or collection_name
        msg = (
            f'library_add path="{filepath}" collection="{collection}"'
        )
        print(f"  [{i+1}/{len(files)}] {msg[:80]}")
        if args.dry_run:
            continue

        payload = json.dumps({"message": msg}).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = resp.read().decode("utf-8")
                if "[LIBRARY] Already" in body or "already in library" in body.lower():
                    skipped += 1
                elif "[LIBRARY] Added" in body:
                    added += 1
                else:
                    print(f"    Response: {body[:200]}")
                    added += 1
        except Exception as e:
            print(f"    ERROR: {e}")
            failed += 1
            if not args.skip_errors:
                sys.exit(1)

        time.sleep(0.2)  # brief pause between requests

    print(f"\n[BATCH COMPLETE]  Added={added}  Skipped={skipped}  Failed={failed}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    root = Path(args.root_dir)
    if not root.exists():
        print(f"Error: directory not found: {root}")
        sys.exit(1)

    if args.direct:
        run_direct(args)
    else:
        # Default: API mode (but print instructions if no URL)
        if not args.api_url and not args.dry_run:
            print("Tip: use --direct when running inside the container for faster ingest.")
            print("     use --api-url + --api-key to drive via Agent Zero REST API.")
            print("     use --dry-run to preview without ingesting.\n")
        run_via_api(args)


if __name__ == "__main__":
    main()
