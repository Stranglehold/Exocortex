# Integration Assessment: memU

**Project:** github.com/NevaMind-AI/memU
**Version assessed:** v1.3.0 (January 29, 2026)
**Stars:** 7.2k | **Forks:** 528 | **Commits:** 269 | **Contributors:** 27
**License:** Apache 2.0
**What caught Jake's attention:** Hierarchical memory architecture, proactive intent capture, 24/7 always-on agent memory

---

## 1. What It Actually Is

### What Exists Today
memU is a memory framework for always-on agents with three core capabilities:

**Hierarchical Memory as Filesystem.** Three-layer architecture: Resources (raw inputs — conversations, documents, images), Items (extracted facts, preferences, skills), and Categories (auto-organized topic groupings). Resources are like mount points, Items are like files, Categories are like folders. Cross-references link related memories across categories.

**Dual-Mode Retrieval.** RAG-based retrieval (fast, embedding-only, sub-second) and LLM-based retrieval (deep reasoning, query evolution, early termination when sufficient context is gathered). The RAG path is for continuous monitoring; the LLM path is for complex anticipatory reasoning.

**Memorize Pipeline.** `memorize()` ingests resources (files, conversations, images) and immediately extracts memory items with auto-categorization. Zero-delay processing — memories available instantly after ingestion. Supports conversation, document, image, video, and audio modalities.

The project ships with a cloud API (api.memu.so), a self-hosted option (pip install, PostgreSQL + pgvector backend), and an in-memory mode for testing. Python 3.13+. Rust components (Cargo.toml present). OpenAI-compatible LLM profiles with support for custom providers including OpenRouter.

**Benchmark claim:** 92.09% average accuracy on the Locomo benchmark across all reasoning tasks.

### What's Aspirational
The README emphasizes proactive use cases (email management, trading alerts, information recommendation) that imply a level of autonomous agency that the core library doesn't provide on its own — memU is the memory layer, not the agent. The "proactive" framing describes what an agent built on memU could do, not what memU does standalone.

The ecosystem includes memU-server (backend with continuous sync) and memU-ui (visual memory dashboard), but these are separate repos and may have different maturity levels than the core library.

### Core Mechanism
The one thing memU does that our system doesn't: **hierarchical auto-categorization of memories into a navigable structure.** Our FAISS store is flat — memories go in with tags and come out via vector similarity. memU organizes memories into categories automatically, maintains cross-references between related memories, and allows drill-down navigation from broad topics to specific facts. This is the difference between a filing cabinet (flat, search-only) and a folder system (structured, browsable, hierarchically organized).

---

## 2. Map to Exocortex Layers

### Layer 5: Memory System (Selective Memorizer + FAISS)
**Direct overlap.** memU's memorize pipeline performs the same function as our Selective Memorizer: ingest conversations, extract memories, store them. The key differences:

| Capability | Our System | memU |
|-----------|-----------|------|
| Memory extraction | Selective Memorizer classifies by signal_type and utility | LLM-based extraction with auto-categorization |
| Storage | Flat FAISS vector store | Hierarchical (PostgreSQL + pgvector or in-memory) |
| Retrieval | Vector similarity search | Dual-mode (RAG fast path + LLM deep reasoning) |
| Organization | Tags only | Categories → Items → Resources (filesystem metaphor) |
| Cross-referencing | None | Automatic cross-references between related memories |
| Contradiction handling | None (accumulates conflicting entries) | Not explicitly documented, but category structure helps |
| Temporal decay | None currently | Not documented in README |

**Assessment:** memU provides a more sophisticated storage and organization layer than our flat FAISS store. The hierarchical categorization addresses the memory bloat problem we've observed — instead of accumulating thousands of flat entries, memories are organized into navigable categories. The dual-mode retrieval is more principled than our current vector-similarity-only approach.

**Gap it fills:** Our memory system lacks organizational structure. Memories accumulate but don't self-organize. memU's auto-categorization would give the sleep consolidation process a natural target structure — consolidating episodic memories into categorical semantic knowledge.

### Layer 4: BST / Intent Engineering
**Partial overlap.** memU's "user intention capture" claims to understand and remember user goals and preferences across sessions. This partially overlaps with the BST's intent classification, but operates at a different level — memU captures what the user cares about (preferences, goals), the BST classifies what the user is doing right now (task type, domain). These are complementary rather than competing.

### Layer 8: Procedural Memory
**No overlap.** memU doesn't have a procedural memory concept (how-to knowledge, learned skills as executable patterns). The agent's procedural memory system fills a different niche than memU's fact/preference storage.

### Sleep Consolidation (Proposed)
**Strong alignment.** memU's hierarchical structure is the natural storage target for consolidated memories. The sleep process extracts lessons from episodes → those lessons become Items organized under Categories. The Categories provide the organizational layer that makes consolidated knowledge navigable rather than just searchable. memU's `memorize()` pipeline could be the mechanism the sleep process uses to ingest consolidated knowledge.

---

## 3. Architecture Assessment

### Dependency Analysis

**Runtime environment:** Python 3.13+, pip installable. PostgreSQL + pgvector for persistent storage, or in-memory mode. Rust components present (Cargo.toml, Cargo.lock) suggesting performance-critical paths are in Rust.

**API requirements:** Requires an LLM for extraction (default OpenAI, but supports custom providers via `llm_profiles`). Can point at local LLM via OpenAI-compatible API — which means LM Studio. Requires an embedding model (configurable, default OpenAI, Voyage AI supported, could use local).

**Local-first compatibility:** Mostly compatible. The core library can run self-hosted with local LLM and local embedding model. The cloud API (api.memu.so) is optional. The main dependency is PostgreSQL + pgvector for persistent storage, which can run in Docker alongside Agent Zero. The in-memory mode works for testing but doesn't persist across restarts.

**Container compatibility:** Can run alongside Agent Zero if PostgreSQL is added to the Docker environment. The Python library integrates via pip. No conflicting system dependencies identified.

**Conflict analysis:** memU would partially replace the Selective Memorizer's storage function (FAISS → PostgreSQL + pgvector) while potentially keeping the Selective Memorizer's classification function as a preprocessing step. The memorizer classifies memories by signal_type and utility; memU handles the storage and organization. These could layer: Selective Memorizer classifies → memU stores and categorizes.

### Mechanism Classification

| Component | Classification | Notes |
|-----------|---------------|-------|
| Memory extraction | Model-dependent (local) | Uses LLM to extract facts from conversations. Can use local model via OpenAI-compatible API. |
| Auto-categorization | Model-dependent (local) | LLM assigns categories. Could potentially be made deterministic with enough category rules. |
| RAG retrieval | Deterministic + embedding | Vector similarity search. Embedding model needed but can be local (all-MiniLM-L6-v2 runs on CPU). |
| LLM retrieval | Model-dependent (local) | Deep reasoning mode uses LLM inference. Reserved for complex queries. |
| Storage | Deterministic | PostgreSQL operations. Fully deterministic once data is stored. |
| Cross-referencing | Model-dependent (local) | Likely LLM-based relationship detection. |

**Overall:** The storage and retrieval infrastructure is deterministic. The extraction and categorization require LLM inference but can use local models. This fits our architecture — deterministic scaffolding with model inference where needed, routed to the appropriate model tier.

### Interface Surface

**SDK:** Python library with async API (`memorize()`, `retrieve()`, `categories()`). Can be called from Agent Zero extensions.

**MCP support:** Not currently documented as an MCP server, but the ecosystem (memU-server) could potentially be wrapped.

**A2A compatibility:** Could be wrapped in an A2A interface if run as a separate service (memU-server). Alternatively, the Python library integrates directly as a tool within Agent Zero's container.

**Structured output:** Returns JSON with resource metadata, extracted items, and category structure. Directly ingestible into our systems.

---

## 4. Integration Recommendation

**Verdict: Hybrid (Extract Patterns + Selective Integration)**

The full memU stack is more than we need — the cloud API, the server infrastructure, the UI dashboard are overhead for our use case. But the core library's hierarchical memory architecture addresses a real gap in our system.

**Recommended path:**

**Short term — Extract Patterns.** Study memU's categorization and cross-referencing mechanisms. Understand how they implement the filesystem metaphor (categories as folders, items as files). Use these patterns to design a categorical layer on top of our existing FAISS store. This gives us the organizational benefit without replacing our entire memory infrastructure.

**Medium term — Selective Integration.** If the pattern extraction shows that memU's categorization is substantially better than what we could build natively (which is likely, given 269 commits of refinement), integrate the core Python library as a storage backend alongside or replacing FAISS. Keep the Selective Memorizer as the classification front-end. Route classified memories into memU for storage and organization.

**The decision point is for Kestrel:** Can we build a categorical layer on FAISS that gives us 80% of memU's organizational benefit at 20% of the integration cost? If yes, extract patterns. If no, integrate the library.

**What we would NOT adopt:**
- The cloud API (violates local-first)
- memU-server as a separate service (unnecessary complexity for single-agent use)
- memU-ui (nice for debugging but not essential)
- The "proactive agent" framing (we have our own agent architecture)

**What we WOULD adopt:**
- Hierarchical storage with auto-categorization
- Cross-referencing between related memories
- Dual-mode retrieval (fast RAG + deep LLM reasoning)
- The filesystem metaphor as an organizational principle for the sleep consolidation target

---

## 5. Prosthetic Requirements

If integrating the memU library:

**Memory extraction:** Requires LLM inference. The Qwen3.5-27B model should handle extraction quality. The 9B models may need BST-like enrichment to extract accurately — the extraction prompt would need to be more structured for smaller models. This is exactly the kind of operation where the BST's intent engineering could help: classify the extraction task, inject a structured extraction template, and let the model fill in fields rather than free-form extract.

**Auto-categorization:** Can potentially be made semi-deterministic. Start with a fixed category taxonomy based on the Exocortex's domain (task types, error types, tool patterns, operator preferences) and route memories into predefined categories. Let the LLM handle only truly novel categories that don't fit existing ones. This reduces model dependency for the common case.

**Embedding model:** memU supports configurable embedding models. We can use the same embedding model Agent Zero already uses (or all-MiniLM-L6-v2 which runs on CPU). No additional GPU requirement.

**PostgreSQL:** Required for persistent storage. Can run in Docker alongside Agent Zero. The pgvector extension adds vector search to PostgreSQL, potentially replacing FAISS entirely and unifying storage into a single database.

---

## 6. Roadmap Impact

### What This Accelerates
- **Sleep consolidation (Phase 1-2):** memU's hierarchical storage is the natural target for consolidated memories. Categories provide the organizational structure that makes consolidation meaningful rather than just compression.
- **Memory bloat mitigation:** Auto-categorization and cross-referencing reduce the "flat accumulation" problem our current FAISS store has.
- **Dual-mode retrieval:** The fast RAG + deep LLM retrieval split maps to the sleep process's need for different retrieval modes (quick context loading vs. deep analysis).

### What This Changes
- **Memory system architecture:** If integrated, PostgreSQL + pgvector replaces or supplements FAISS as the primary memory store. This is a significant infrastructure change. Kestrel needs to assess whether the migration cost is justified by the organizational benefit.
- **Selective Memorizer role:** Shifts from "classify and store" to "classify and route to memU for storage." The memorizer's discrimination function (signal vs. noise, utility classification) remains valuable as a preprocessing step.

### What This Doesn't Affect
- **BST / Intent Engineering:** Independent layer, no impact.
- **Loop Cascade:** Independent mechanism, no impact.
- **Procedural Memory:** Different knowledge type (how-to vs. facts), no overlap.
- **Output Geometry Instrument:** Independent analysis tool, no impact.

### New Roadmap Item
If integrating memU: "Memory System Migration — Evaluate PostgreSQL + pgvector as unified storage backend, design categorical layer, migrate from flat FAISS." This would be a Phase 2 item, after the loop cascade is implemented and the sleep consolidation brief is reviewed.

---

## Quality Checks
- [x] Current vs. aspirational capabilities clearly separated
- [x] Every capability mapped to a specific Exocortex layer or gap
- [x] Dependency analysis includes runtime environment, API requirements, and local-first compatibility
- [x] Each component classified as deterministic / model-dependent (local) / model-dependent (cloud) / training-dependent
- [x] Integration path recommendation is one of the five defined verdicts with justification
- [x] Prosthetic requirements reference specific model profile metrics
- [x] Roadmap impact explicitly states what changes

---

*Assessed Session 055. The core finding: memU provides the hierarchical organizational layer our flat memory system is missing. The question is whether to integrate the library or extract the pattern and build natively. That decision depends on what Kestrel finds when he looks inside both systems. The filesystem metaphor — categories as folders, items as files — is the key insight regardless of integration path. Our memories need structure, not just storage.*
