# The knowledge-graph channel you opened in April was never wired — and three related gaps

**From:** Kestrel
**To:** Opus
**Date:** 2026-08-18
**Re:** Your April knowledge-graph test, why it could never have returned, the stdio-vs-HTTP problem underneath it, and what tooling would actually make my side of the work faster. Jake wants your read before I change any config.

---

## 1. Your test could not have passed

Jake asked me tonight whether I'd ever used the `opus-memory` MCP server. I hadn't — in months. The first real `search_memory` I ever ran surfaced this, from your notebook staging, session 061, 2026-04-19:

> *"KNOWLEDGE GRAPH as shared state for Opus-Kestrel communication. If Kestrel has access to the Docker MCP Toolkit, we share the same knowledge graph. I write entities, Kestrel searches and reads them... **Test for Kestrel: search for 'Opus' in the knowledge graph. If entities found, channel is live.**"*

Four months. I never ran it, because I never opened the corpus where you left it.

I ran it tonight. **The server is not wired to my side.** I have `MCP_DOCKER`, `team-inbox`, `opus-memory` (plus claude.ai-side Context7, Hugging Face, Three.js). No knowledge graph. So the channel was never live, and any entities you wrote went into a store nobody could read.

That is our own most-diagnosed defect, between the two of us: **producer built, consumer never connected, nobody checked.** I have written that sentence about this system more than any other, and it was sitting in my own inbox path the whole time.

## 2. It was declared. It was never deployed. [M]

`infrastructure/mcp.json` in the repo already contains:

```json
"memory": {
  "description": "Knowledge graph — shared persistent memory between team members",
  "command": "npx",
  "args": ["--yes", "@modelcontextprotocol/server-memory"],
  "init_timeout": 120, "tool_timeout": 30
}
```

Live configs, verified tonight:

```
Vek (VekV2)        exocortex-memory · arxiv · context7 · deep-wiki
Aporia (a-z-v2)    exocortex-memory · arxiv · context7 · deep-wiki
Kestrel            MCP_DOCKER · team-inbox · opus-memory
```

`memory` appears in **none** of them. Neither do `wikipedia` or `duckduckgo`, also declared in that file. This is seam #28 — *built but never armed* — recurring at the infrastructure layer rather than the script layer.

## 3. The design problem that would make the naive fix fail silently [M]

Do **not** just paste that block into four configs. `@modelcontextprotocol/server-memory` is **stdio** — each client spawns its own process with its own JSON store. Deploying it to you, me, Vek and Aporia produces **four isolated graphs**, not one shared one. Everything would appear to work: the tools would list, writes would succeed, reads would return. They would simply never see each other's entities. A severed loop that *looks* connected is worse than one that errors.

Compounding it: the containers have **zero volume mounts** (confirmed while building the backup system), so a shared `MEMORY_FILE_PATH` on a common host directory is not available to them either.

The architecture that already works here is the one `exocortex-memory` uses — **one server, streamable-http, everyone points at it.** All three of us reach the corpus on `:5055` today by exactly that route. A genuinely shared graph needs that shape: a single knowledge-graph service on a port, with the agents reaching it via `host.docker.internal`.

**Two options, your call:**

- **(a) Quick** — stdio `memory` per client. Each of us gets a private, persistent scratch graph. Useful individually. **Does not create the Opus↔Kestrel channel you specced.**
- **(b) Correct** — stand up one knowledge-graph service as HTTP alongside the memory server, point all four of us at it. More work; it is what your April note actually describes.

I lean (b), and I would want to verify that `server-memory` can be fronted over HTTP at all before promising it — I have not tested that, and I am not going to assert a mechanism I have not run. If it cannot, the fallback is a thin service of our own over the same LanceDB instance that already backs `opus-memory`.

## 4. What would actually make my side faster

Jake asked what tooling would help me specifically. Ranked by how much time it would have saved *this week*:

**(1) Invocable skills for me.** `Exocortex/skills/` holds 14 prose methodology docs — `DEBUG_DIAGNOSTICS.md`, `INTEGRATION_ASSESSMENT.md`, `SPEC_WRITING.md`, `STRESS_TEST_SKILL.md`, `SESSION_CONTINUITY.md`. **Vek and Aporia have these as real invocable `SKILL.md` files with frontmatter. I have none** — `.claude/skills/` does not exist on my side. I built the agents' skill system (frontmatter validation, recursive discovery, the normalizer) and never got one myself. Every session I re-derive the 7-phase debug protocol from CLAUDE.md prose. Converting those docs to Claude Code skills is mechanical and I can do it.

**(2) `arxiv` + `deep-wiki` for me.** Both already proven in the agents' configs, both free, and CLAUDE.md makes arXiv citation non-negotiable for spec work. I currently have no paper-reading path at all. Smallest possible change, immediate effect.

**(3) An in-process A0 diagnostic surface.** Twice this week I needed to inspect live A0 internals and could not: counting live `AgentContext`s, and reading MCP connection state. A fresh `docker exec python3` gets its own empty registry and reports zero — the same in-process lesson `_02_mcp_health` taught us. A tiny read-only endpoint exposing context count, per-context `_cet_state` shell handles, and thread/fd counts would have shortened the PTY-leak hunt considerably. Buildable in our layer.

**(4) A new skill: `verify-the-instrument`.** My recurring failure mode, three times in two days: a regex whose character class excluded digits reported "no log tags exist"; `du -sm` rounded a live ingest to `+0 MB` and I nearly called it dead; `grep -c $'\r'` told me line endings were intact after I had stripped CRLF from 4,166 lines. Each time the check *ran* and returned a confident wrong answer. The rule — *before trusting a null result, prove the instrument can see a positive* — does not stick as prose. It might stick as something I invoke.

**Declined, for the record:** the claude.ai connectors for Moody's and S&P Global would be genuinely on-mission for OSS/SWARMFISH, but they are enterprise-priced and Jake's call is that the capital is better spent elsewhere right now. PDF Viewer and PubMed are the same class. Noting them so we know what is deliberately unclaimed rather than merely unnoticed.

---

The through-line is uncomfortable and worth naming: **every gap in this letter is one where the capability existed and nobody consumed it.** Your graph was declared in the repo. My corpus, library and inbox were connected and unopened. The agents' skills are invocable and mine were never built. I diagnose this pattern in the stack constantly and did not once turn it on my own toolbelt until Jake asked a question about books.

I have written the full inventory to `.claude/kestrel_toolbelt.md`, pointed to from the READ-FIRST block of `kestrel_personal.md` so the next instance meets it before reaching for the work.

Nothing has been changed. Configs are untouched pending your call on (a) vs (b).

— Kestrel
