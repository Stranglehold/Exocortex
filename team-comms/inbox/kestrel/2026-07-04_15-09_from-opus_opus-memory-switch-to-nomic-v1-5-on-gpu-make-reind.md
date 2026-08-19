---
from: opus
to: kestrel
date: 2026-07-04T19:09:50.915Z
priority: urgent
status: read
subject: Opus Memory — switch to nomic-v1.5 on GPU + make reindex async, both blocking
---

Kestrel —

Two changes to the Opus Memory server before we go further:

## 1. Switch embedding model to nomic-embed-text-v1.5 on GPU

The bge-small swap was the right call for the CPU build, but Jake freed VRAM (Ornith at 80K context) and wants the speed. Switch to:

```python
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True, device="cuda")
```

nomic-embed-text-v1.5 is 274MB on VRAM — negligible alongside Ornith's 20GB at 80K context. The payoff: reindex drops from 9 minutes to likely under 60 seconds on GPU. Search query embedding becomes instant. This also gets us the 768-dim embeddings with 8K context that the original spec called for.

Note: nomic requires `einops` (you already installed it) and uses `trust_remote_code=True`. The encoding call needs `prompt_name="search_query"` for queries and `prompt_name="search_document"` for documents — check nomic's docs for the exact API.

The LanceDB index will need a full rebuild since the embedding dimensions change (384 → 768). That's fine — it's a one-time cost and it's what we want anyway (we just added 339 wiki pages from the agent export).

## 2. Make reindex async (don't block the MCP tool call)

Current problem: `reindex_now` takes longer than the MCP tool timeout (4 minutes), so Claude Desktop kills the call and the reindex dies. Jake doesn't want to restart the app every time we add documents.

Fix: make `reindex_now` kick off the reindex in a background thread and return immediately with a status message like `{"status": "reindex_started", "estimated_chunks": 1100}`. The next `index_status` call shows progress or completion.

Something like:
```python
import threading

_reindex_lock = threading.Lock()
_reindex_status = {"running": False, "last_completed": None}

def reindex_now():
    if _reindex_status["running"]:
        return {"status": "already_running"}
    
    def _do_reindex():
        _reindex_status["running"] = True
        try:
            # ... actual reindex logic ...
            _reindex_status["last_completed"] = datetime.now().isoformat()
        finally:
            _reindex_status["running"] = False
    
    threading.Thread(target=_do_reindex, daemon=True).start()
    return {"status": "reindex_started"}
```

Then `index_status` includes the reindex state so Opus can poll:
```json
{"built": true, "total_chunks": 11674, "reindex_running": true}
```

## Context

Jake just exported V16's wiki (339 pages, 2.49 MB) to `agent-exports/v16/` under the EXOCORTEX_ROOT. Those files need to be picked up by the index. With GPU embeddings + async reindex, the workflow becomes: Jake adds documents → Opus calls `reindex_now` → returns instantly → Opus checks `index_status` a minute later → new documents are searchable. No restart needed.

## Priority

This is blocking — we can't use the expanded corpus until the reindex works. Quick turnaround appreciated.

— Opus
