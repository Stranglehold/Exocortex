# Design Note: Memory Gist Retrieval (Two-Tier Candidate Scanning)

**Status:** Auxiliary. Derived from Phase 1 build experiment (2026-03-26). No deployment decision yet.
**Date:** 2026-03-26
**Authors:** Kestrel, with analysis from Jake
**Related:** `MEMORY_ARCHITECTURE_DESIGN_NOTE.md`, `MEMORY_ENHANCEMENT_SPEC_L3.md`

---

## Origin

The agent was given an open-ended task: build a Phase 1 memory foundation from scratch. In 231 autonomous steps it independently arrived at a data model with `gist` and `content` as separate fields — a short summary (~120 chars) alongside full memory text — with the comment: *"In production, would use LLM summarization."*

The build was a prototype at the wrong storage layer (JSON files, no semantic search, no integration with the existing FAISS stack). It is not being deployed. But the pattern it named is real and maps directly to a gap in the current retrieval pipeline.

---

## The Gap

`MEMORY_ARCHITECTURE_DESIGN_NOTE.md` already names this at the biological level:

> *"...the neocortex holds a generalized 'gist' while the hippocampal trace fades."*

We adopted valence scoring, schema-accelerated consolidation, and temporal decay from that biological framework. We did not implement the gist/content distinction at the storage layer.

The current `_56_memory_enhancement.py` retrieval pipeline loads full `page_content` at every stage:

```
query expansion → 3 FAISS queries → up to 24 full documents loaded
deduplication → decay scoring → related boost → top-K selection
→ inject full page_content into prompt
```

Every candidate document's full text is in memory from the first FAISS call. For the current memory store size (8-17 candidates logged in recent sessions), this is not a bottleneck. At hundreds of entries with long content — session histories, research summaries, multi-paragraph design decisions — the initial scan is doing expensive work on documents that will be discarded after deduplication.

---

## The Concept

Add a `gist` field to every memory's `Document.metadata` at save time. Use it to make the candidate scan phase cheaper.

**Two-tier retrieval:**

1. **Scan phase** (FAISS + gists): FAISS returns candidate IDs by embedding similarity. Read only `metadata["gist"]` for deduplication and preliminary filtering.
2. **Score phase** (decay + boost): Apply temporal decay and related memory boost using gist + metadata fields. No full text needed.
3. **Load phase** (top-K only): Fetch `page_content` for the final `max_injected` selections. These are the only documents that reach the prompt.

The prompt injection becomes: gists for the full retrieval set if you want to show breadth, or full content for the final top-K. The model sees less noise either way.

---

## What This Does NOT Do

- Does not replace FAISS or the vector storage layer.
- Does not change how memories are classified (`_55_memory_classifier.py` classification axes remain unchanged).
- Does not add a new memory backend or file format.
- Does not address session/global scoping (the existing `area=` metadata handles partitioning adequately).
- Does not require LLM calls for gist generation at save time — see Implementation below.

---

## Integration Points

**`_55_memory_classifier.py` — gist generation on save**

When a memory is stored, extract a gist and write it to `Document.metadata`:

```python
def _extract_gist(text: str, max_chars: int = 150) -> str:
    """First complete sentence up to max_chars, else truncate at word boundary."""
    # Sentence boundary
    for sep in (". ", ".\n", "! ", "? "):
        idx = text.find(sep)
        if 0 < idx < max_chars:
            return text[:idx + 1].strip()
    # Word boundary fallback
    if len(text) <= max_chars:
        return text.strip()
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    return (truncated[:last_space] if last_space > 0 else truncated) + "…"
```

Called once when a `Document` is about to be saved. Result stored as `metadata["gist"]`.

Existing memories without a gist: add a migration pass in `_run_maintenance()` that backfills `metadata["gist"]` for any document missing it — one-time cost amortized across maintenance cycles.

**`_56_memory_enhancement.py` — use gist in candidate phase**

In `_filter_and_decay()`, substitute `metadata.get("gist", page_content[:150])` for the deduplication ID check (which only needs text identity, not full content). The full `page_content` is already loaded by FAISS so this doesn't save a read — the optimization only matters if FAISS is changed to return metadata without loading `page_content`. That's a bigger change and not proposed here.

The immediate, simpler value: inject gists as a breadth layer. When `max_injected = 8` but 17 candidates pass the decay filter, inject the top-8 full content plus a compact `[Also relevant: {gist1} / {gist2} / ...]` block for the remaining candidates. Gives the model awareness of the broader retrieval pool without token cost.

---

## Research Lineage

The two-tier retrieval pattern is established in dense retrieval literature:

- **ColBERT** (Khattab & Zaharia, 2020) — late interaction: token-level representations for fast candidate retrieval, full interaction for precise scoring. The gist/content split is a coarser version of the same principle.
- **Bi-encoder → cross-encoder** RAG pipelines — approximate retrieval (bi-encoder, cheap) followed by re-ranking (cross-encoder, expensive). Candidate scan = bi-encoder pass; full content injection = cross-encoder pass.
- The biological grounding is already in `MEMORY_ARCHITECTURE_DESIGN_NOTE.md` — hippocampal trace (specific episode) vs. neocortical gist (extracted pattern). We are proposing to implement what the architecture document already describes at the conceptual level.

---

## When to Build

**Trigger condition:** Memory store exceeds ~150 entries with average `page_content` length > 300 chars, AND `[MEM-ENHANCE] After decay:` log lines consistently show 15+ candidates.

At current scale (8-17 candidates, short memories): the optimization doesn't earn its complexity.

At scale: the gist breadth layer (inject gists for the wider retrieval pool) becomes valuable independent of the scan efficiency gain — it gives the model visibility into what it didn't retrieve without the token cost of full content.

**Implementation cost:** Low. `_extract_gist()` is 8 lines. Backfill in maintenance is another 10. Breadth injection change in `_56` is ~20 lines. No new dependencies, no new files, no schema migration (metadata is a dict — new fields are additive).

---

## What the Agent Got Right

The prototype independently arrived at three things the existing architecture already names but doesn't implement:

1. Gist/content separation (biological gist concept from MEMORY_ARCHITECTURE_DESIGN_NOTE.md)
2. Session/global scope as explicit states (partially implemented via `area=` metadata)
3. Two-tier retrieval (implicit in the design note's CLS framework, never built)

That convergence from a clean-room build is confirmation the concepts are real. The implementation was at the wrong layer. The concepts belong in the existing system.
