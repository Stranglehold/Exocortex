# RESEARCH REPORT: Karpathy's LLM Knowledge Bases — The Wiki Pattern
## Exocortex Research Library
## Author: Opus — April 25, 2026
## Sources: Karpathy's GitHub Gist (llm-wiki.md), VentureBeat, Towards AI, Level Up Coding, Starmorph, Karpathy blog

---

## 1. Overview

On April 2, 2026, Andrej Karpathy (co-founder of OpenAI, former AI Director at Tesla) posted on X: "Something I'm finding very useful recently: using LLMs to build personal knowledge bases for various topics of research interest. A large fraction of my recent token throughput is going less into manipulating code, and more into manipulating knowledge."

The post got 16+ million views. Two days later he published a GitHub Gist called "llm-wiki.md" — not code, not a product, but an "idea file" designed to be copy-pasted into an LLM agent. The gist hit 5,000+ stars within days.

The core insight: knowledge should compound, not evaporate. Traditional RAG retrieves and forgets. The LLM Wiki compiles and retains.

---

## 2. Architecture — Three Layers

### 2.1 Layer 1: Raw Sources (Immutable)

A curated collection of articles, papers, meeting notes, images. The LLM reads them but never modifies them. This is ground truth. Immutability is deliberate: you can always re-compile the wiki from scratch if needed.

Sources are ingested via the Obsidian Web Clipper (converts web content to markdown with locally-stored images for vision capability) or manual placement.

### 2.2 Layer 2: The Wiki (LLM-Maintained)

A directory of markdown files the LLM owns completely. Entity pages, concept pages, summaries, an index, a log. The human reads it. The LLM writes it.

When a new source is added, the LLM doesn't create an index for later retrieval. It reads, understands, and integrates the source into the knowledge base — updating all relevant existing pages, noting contradictions between new and existing claims, creating new concept pages, and reinforcing cross-references across the entire wiki.

Wiki page types include: summary pages, product pages, concept pages, persona pages, and comparison tables — all interlinked with wiki-style `[[links]]`.

### 2.3 Layer 3: The Schema (Configuration)

A CLAUDE.md (for Claude Code) or AGENTS.md (for Codex) file that turns a generic agent into a disciplined wiki maintainer. It defines how pages are structured, how sources get ingested, how answers get formatted, and how the wiki maintains itself.

This is the control plane — the thing that makes the LLM behave as a librarian rather than a chatbot.

---

## 3. Three Operations

### 3.1 Ingest

Process a new source. The LLM reads the raw document, extracts key concepts, creates or updates wiki pages, adds cross-references, and logs the ingestion. This is the compilation step — the core innovation. Instead of indexing for later retrieval, the LLM actively synthesizes.

### 3.2 Query

Ask a question. The LLM navigates the wiki structure (via index and cross-references) to find relevant pages, synthesizes an answer, and cites wiki pages as sources. The wiki is the retrieval layer, not a vector database.

### 3.3 Lint

Health checks. At intervals, the LLM audits the entire wiki for:
- Contradictions or inconsistencies between pages
- Statements rendered obsolete by more recent sources
- Orphan pages (no links pointing to them)
- Missing concept pages (referenced but not yet created)
- Stale information that needs updating

---

## 4. Why Not RAG?

Karpathy positions the LLM Wiki as a simpler alternative to RAG for personal and team-scale knowledge. His argument:

**RAG problems at personal scale:**
- Documents are chopped into arbitrary chunks, losing context
- Embedding similarity search returns chunks that are semantically close but not necessarily relevant
- No knowledge compounding — every query starts from scratch
- No contradiction detection — conflicting information coexists silently
- Complex infrastructure (vector DB, embedding pipeline, retrieval chain)

**Wiki advantages:**
- Knowledge compounds — each new source enriches existing pages
- Contradictions are flagged during ingestion
- Cross-references are explicit and human-readable
- Version history via git
- No vector database required at personal scale
- The wiki is an artifact you can read, not a database you query

**Where RAG still wins:**
- Millions of documents where pre-compilation is impractical
- Frequently changing documents where re-ingesting the entire wiki is too expensive
- When you need to answer questions about documents you haven't pre-processed

---

## 5. Tooling

### 5.1 Obsidian

The viewing interface. Karpathy uses Obsidian because of three features:
- **Graph View** — visual graph of wiki pages as nodes, wiki-links as edges
- **Local-first** — all files stored locally, no cloud dependency
- **Markdown-native** — the wiki is plain markdown files

### 5.2 QMD (by Tobi Lutke, Shopify CEO)

A local search engine for markdown files using hybrid BM25/vector search with LLM re-ranking. Available as CLI and MCP server. Karpathy recommends it as the search layer for LLM Wikis at scale.

### 5.3 Claude Code / Codex

The agent that maintains the wiki. The schema file (CLAUDE.md) configures the agent as a wiki maintainer. The agent reads raw sources, writes wiki pages, and performs lint operations.

---

## 6. The "Idea File" Concept

Karpathy explicitly chose to share an idea file rather than code:

"In this era of LLM agents, there is less of a point/need of sharing the specific code/app, you just share the idea."

The idea file is designed to be copy-pasted into an LLM agent, which then instantiates the pattern for the user's specific needs. This is a meta-innovation: sharing patterns rather than implementations, because the LLM can generate the implementation from the pattern.

---

## 7. Connection to Vannevar Bush's Memex (1945)

Karpathy explicitly references Vannevar Bush's "As We May Think" essay, which described a hypothetical device called the Memex — a mechanical desk that would store and cross-reference all of a person's books, records, and communications with associative trails.

The Memex never worked because maintenance was manual. Every cross-reference had to be created by hand. Bush imagined operators building "trails" through knowledge, but nobody actually does this at scale.

The LLM Wiki solves the maintenance problem: "The wiki stays maintained because the cost of maintenance is near zero." The LLM creates and updates cross-references automatically on every ingest.

---

## 8. Karpathy's Other 2026 Projects

### 8.1 microgpt (February 2026)

A single file of 200 lines of pure Python with no dependencies that trains and inferences a GPT. The culmination of micrograd, makemore, nanogpt — a decade-long obsession to simplify LLMs to bare essentials. Contains: dataset, tokenizer, autograd engine, GPT-2 architecture, Adam optimizer, training loop, and inference loop. 4,192 parameters. Beautiful, not practical — a teaching tool.

### 8.2 LLM Council

A web app that sends your query to multiple LLMs (GPT-5.1, Gemini 3.0, Claude Sonnet 4.5, Grok 4), has them review and rank each other's work anonymously, then a Chairman LLM produces the final response. Essentially formalized cross-model peer review.

### 8.3 2025 Year in Review — Key Insights

Karpathy identified several themes relevant to our work:
- **Claude Code as the first convincing LLM Agent** — "runs on your computer with your private environment, data and context"
- **Agents on localhost > agents in the cloud** — "the primary distinction that matters is not about where the AI ops happen to run but about everything else — the already-existing and booted up computer, its installation, context, data"
- **Jagged capabilities** — LLMs are "at the same time a genius polymath and a confused grade schooler, seconds away from getting tricked by a jailbreak"
- **Vibe coding will terraform software** — code is "free, ephemeral, malleable, discardable after single use"

---

## 9. Relevance to Exocortex

### 9.1 The Exocortex Already Has Raw Materials for a Wiki

Eight papers read, twelve+ design notes, dozens of team communications, session handoffs, notebook entries, reflections. These are the raw sources. What's missing is the compilation step — a structured wiki synthesizing all of this into navigable, cross-referenced knowledge.

### 9.2 Implementation Path

**Phase 1: Schema + Structure**
Create an Exocortex wiki schema (CLAUDE.md equivalent) that defines:
- Page types: research finding, design decision, operational incident, tool capability
- Required sections per page type
- Cross-reference rules (how to link related concepts)
- Contradiction detection rules
- Index maintenance rules

**Phase 2: Initial Compilation**
The agent (or I, via the team-comms channel) compiles the existing Exocortex knowledge into wiki pages:
- One page per research paper (8 papers → 8 concept pages)
- One page per design note (pondering architecture, temporal proprioception, etc.)
- One page per deployed extension (BST, supervisor, error comprehension, etc.)
- Cross-references between them (SRGen → pondering architecture → entropy monitoring)

**Phase 3: Ongoing Maintenance**
Every new session, paper read, or design decision triggers a wiki update. The lint operation runs periodically to catch contradictions and orphan pages.

### 9.3 Wiki vs Knowledge Graph

The Exocortex knowledge graph (MCP memory server) stores entities and relations. The wiki would store synthesized knowledge in human-readable form. These are complementary, not competing:

- **Knowledge graph:** Machine-readable structured data. Good for: "what entities exist?" "how are they related?" Quick lookup.
- **Wiki:** Human-readable synthesized knowledge. Good for: "what does this mean?" "how does this connect to that?" Deep understanding.

The graph is the index. The wiki is the content. Both should exist.

---

## 10. References

- Karpathy GitHub Gist: gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Karpathy blog — microgpt: karpathy.github.io/2026/02/12/microgpt/
- Karpathy — 2025 Year in Review: karpathy.bearblog.dev/year-in-review-2025/
- LLM Council: github.com/karpathy/llm-council
- VentureBeat coverage: venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture
- Towards AI analysis: pub.towardsai.net (Karhade, April 2026)
- Level Up Coding deep dive: levelup.gitconnected.com (Nayak, April 2026)
- Starmorph implementation guide: blog.starmorph.com/blog/karpathy-llm-wiki-knowledge-base-guide
- QMD by Tobi Lutke: mentioned in Karpathy gist
