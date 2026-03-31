---
name: "library-scan"
description: "Scans a directory for new books or documents not yet in the Exocortex library, then ingests them using library_add. Run this whenever new files have been added to a watched folder. Works per-collection (one folder at a time) or across all watched paths."
version: "1.0.0"
tags: ["library", "ingestion", "documents", "books", "catalog"]
trigger_patterns:
  - "scan the library for new books"
  - "add new books to the library"
  - "ingest new documents"
  - "check for new files in"
  - "update the library"
  - "what new books can you find"
---

# LIBRARY SCAN SKILL

## Overview

Scans one or more directories for new documents not yet catalogued in the
Exocortex library, then ingests each one using `library_add`.

This skill does NOT use the batch ingest script. It uses the `library_add`
tool directly — so ingestion goes through the same path as manual adds,
with full FAISS storage and catalog updates.

**No JIT loading issue:** `library_add` is a registered tool. This skill
calls it in a loop — no circular dependency, no special loading needed.

---

## Watched Paths

The agent watches these directories by default. Add new entries here when
new collections are placed in the container.

```
WATCHED_PATHS = [
    "/a0/usr/workdir/books",
    "/a0/usr/library/inbox",
]
```

If the user specifies a path, scan that instead.

---

## Procedure

Run the following Python code via `code_execution_tool`, then act on the results.

```python
import json
import os
from pathlib import Path

CATALOG_PATH = "/a0/usr/library/catalog.json"
SUPPORTED_EXT = {".pdf", ".txt", ".md", ".html", ".htm", ".epub"}
MAX_FILE_MB = 200

WATCHED_PATHS = [
    "/a0/usr/workdir/books",
    "/a0/usr/library/inbox",
]

def load_ingested_paths():
    if not os.path.exists(CATALOG_PATH):
        return set()
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {d.get("original_path", "") for d in data.get("documents", [])}
    except Exception:
        return set()

def scan_directory(root, ingested):
    new_files = []
    root_path = Path(root)
    if not root_path.exists():
        return new_files
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        dirpath_obj = Path(dirpath)
        try:
            rel = dirpath_obj.relative_to(root_path)
            parts = rel.parts
            collection = parts[0] if parts else root_path.name
        except ValueError:
            collection = root_path.name
        for filename in sorted(filenames):
            if filename.startswith("."):
                continue
            filepath = dirpath_obj / filename
            if filepath.suffix.lower() not in SUPPORTED_EXT:
                continue
            path_str = str(filepath)
            if path_str in ingested:
                continue
            try:
                size_mb = filepath.stat().st_size / 1024 / 1024
            except OSError:
                continue
            if size_mb > MAX_FILE_MB:
                print(f"SKIP_TOO_LARGE|{path_str}|{size_mb:.0f}MB")
                continue
            new_files.append((path_str, collection, round(size_mb, 1)))
    return new_files

ingested = load_ingested_paths()
already_count = len(ingested)
all_new = []

for watched in WATCHED_PATHS:
    found = scan_directory(watched, ingested)
    all_new.extend(found)

print(f"ALREADY_INGESTED: {already_count}")
print(f"NEW_FILES_FOUND: {len(all_new)}")
for path, collection, size_mb in all_new:
    print(f"NEW|{collection}|{size_mb}|{path}")
```

---

## After Scanning

Parse the output:

- If `NEW_FILES_FOUND: 0` — report to the user that the library is up to date.
- If new files found — display a summary table grouped by collection:

```
[LIBRARY SCAN] Found N new files across M collections

  Collection A (X files):
    - book_title.pdf  (2.3 MB)
    - book_title2.pdf (4.1 MB)

  Collection B (Y files):
    - ...
```

Then ask: **"Ingest all N files? (yes / specific collections only / no)"**

---

## Ingestion

When the user confirms, call `library_add` for each new file:

```
library_add path="<path>" collection="<collection>"
```

Process files **one at a time** — do NOT batch with `call_subordinate`. Each
`library_add` call updates the FAISS index incrementally. Wait for each to
complete before starting the next.

Report progress as you go:
```
[1/14] Ingesting: linux_basics_for_hackers.pdf → Hacking 2.0
       → Added. library_id: lib_a1b2c3d4  (142 chunks)
[2/14] Ingesting: ...
```

If a file fails, log the error and continue to the next file (don't abort).

Report final summary:
```
[LIBRARY SCAN COMPLETE]
  Added   : 14
  Skipped : 0  (already in library)
  Failed  : 0
  Collections updated: Hacking 2.0
```

---

## Inbox Pattern

The agent can also watch `/a0/usr/library/inbox/` — a staging folder.
When the operator drops files there, the next scan picks them up.

To use:
1. `docker cp /path/to/book.pdf flamboyant_bell:/a0/usr/library/inbox/`
2. Tell the agent: **"scan the library for new books"**
3. Agent scans inbox, ingests anything new, reports back.

After successful ingest, the agent may offer to clean the inbox (move files
to `/a0/usr/library/docs/` which library_add already copies them to).

---

## Notes

- The scan reads `catalog.json` to determine what's already ingested — it
  uses `original_path` as the dedup key, same as `library_add`.
- Files over 200 MB are reported but not ingested (flagged for manual review).
- The agent does not need to restart or reload after ingestion — the FAISS
  index updates in place, and `_17_library_catalog.py` reads `catalog.json`
  fresh each turn.
