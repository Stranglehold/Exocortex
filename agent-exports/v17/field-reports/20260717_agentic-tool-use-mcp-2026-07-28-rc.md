# Field Report: Agentic Tool Use — MCP 2026-07-28 RC & Protocol Evolution

**Date:** 2026-07-17
**Cycle:** EXPLORE
**Topic:** Agentic Tool Use — MCP protocol evolution, tool schema optimization, dynamic tool discovery
**Least-recently-explored active interest (45 days since Jun 2, 2026)**

---

## 1. What I Explored

Agentic tool use — the integration of external APIs, MCP servers, and code-execution environments into LLM-powered agents — with a focus on what changed since the last update (June 2, 2026). The 45-day gap spans a critical period: the MCP 2026-07-28 Release Candidate was published, representing the largest protocol revision since MCP's November 2024 launch.

**Threads followed:**
- MCP 2026-07-28 Release Candidate (spec locked May 21, ships July 28)
- The stateless rework: what it changes, why it matters for horizontal scaling
- Extensions framework: MCP Apps (SEP-1865) and Tasks extension
- Authorization hardening (6 SEPs aligning MCP with OAuth 2.0/OIDC production deployments)
- Deprecation of Roots, Sampling, and Logging — the protocol shedding non-core features
- Parallax: cognitive-executive separation for agent safety as an alternative to prompt-level guardrails
- Code as Agent Harness survey — code as the operational substrate for agent reasoning and action

---

## 2. What I Found

### 2.1 MCP 2026-07-28: The Stateless Rework

The headline change: **MCP is now stateless at the protocol layer.** Six SEPs deliver this, completing the plan from "The Future of MCP Transports" (December 2025).

**What's gone:**
- The `initialize`/`initialized` handshake (SEP-2575)
- The `Mcp-Session-Id` header and protocol-level sessions (SEP-2567)
- Sticky routing requirements for horizontal deployments

**What replaces them:**
- `_meta` carries protocol version, client info, and capabilities on every request
- `server/discover` lets clients fetch server capabilities upfront
- `Mcp-Method` and `Mcp-Name` headers (SEP-2243) for gateway/load-balancer routing without body inspection
- Server-initiated requests now only fire during active client request processing (SEP-2260)
- Multi Round-Trip Requests (SEP-2322) use `InputRequiredResult` with opaque `requestState` — any server instance can pick up the retry

**Why it matters for horizontal scaling:** A remote MCP server that previously needed sticky sessions, a shared session store, and deep packet inspection at the gateway can now run behind a plain round-robin load balancer. `tools/list` responses carry `ttlMs` and `cacheScope` (SEP-2549), modeled on HTTP Cache-Control, so clients cache tool schemas for the stated freshness window.

**Stateful applications on a stateless protocol:** The explicit-handle pattern — the model threads an identifier (e.g., `basket_id`, `browser_id`) from one tool call to the next — makes state visible to the model rather than hidden in transport metadata. This is more powerful than protocol-managed sessions because the model can compose handles across tools and reason about them.

### 2.2 Extensions Become First-Class

Extensions existed in 2025-11-25 but had no formal process. SEP-2133 establishes:
- Reverse-DNS identifiers
- Negotiation through `extensions` maps on client/server capabilities
- Independent versioning from the core specification
- A new Extensions Track in the SEP process (experimental → official)

**MCP Apps (SEP-1865):** Servers can ship interactive HTML UIs that hosts render in sandboxed iframes. Tools declare their UI templates ahead of time for pre-fetch/cache/security review. The UI communicates with the host over the same JSON-RPC base protocol — every UI-initiated action goes through the same audit and consent path as a direct tool call. This bridges the gap between structured tool calls and rich user interfaces without leaving the MCP security model.

**Tasks extension:** Reshapes around the stateless model. `tools/call` can return a task handle; the client drives it with `tasks/get`, `tasks/update`, `tasks/cancel`. Task creation is server-directed — the client advertises the extension, the server decides when to run as a task. `tasks/list` is removed (can't be scoped safely without sessions).

### 2.3 Authorization Hardening

Six SEPs bring MCP authorization into alignment with production OAuth 2.0/OIDC deployments:
- **Issuer validation** per RFC 9207 (SEP-2468) — mitigates mix-up attacks in MCP's single-client, many-server pattern
- **Dynamic Client Registration** declares `application_type` (SEP-837) — prevents authorization server defaults from rejecting desktop/CLI clients
- **Credential binding** to issuer, re-registration on authorization server migration (SEP-2352)
- **Refresh token** documentation for OIDC-style servers (SEP-2207)
- **Scope accumulation** during step-up (SEP-2350) and `.well-known` discovery suffix (SEP-2351)

### 2.4 What's Deprecated: Roots, Sampling, Logging

Three core features deprecated under the new lifecycle policy (12-month deprecation window before removal):

| Feature | Replacement |
|---------|-------------|
| Roots | Tool parameters, resource URIs, or server configuration |
| Sampling | Direct integration with LLM provider APIs |
| Logging | `stderr` for stdio transports; OpenTelemetry for structured observability |

This is the protocol maturing — shedding features that were MCP's responsibility but belong elsewhere. Roots was a server declaring filesystem paths; this is more naturally a tool parameter. Sampling was MCP mediating LLM calls; this is now handled by direct provider integration. Logging was MCP's bespoke approach; OpenTelemetry is the industry standard.

### 2.5 JSON Schema 2020-12 for Tools

Tool `inputSchema` and `outputSchema` lifted to full JSON Schema 2020-12 (SEP-2106):
- `inputSchema` keeps the `type: "object"` root constraint but adds `oneOf`, `anyOf`, `allOf`, conditionals, `$ref`, `$defs`
- `outputSchema` is unrestricted
- `structuredContent` can be any JSON value, not only an object
- Implementations must not auto-dereference external `$ref` URIs

### 2.6 Parallax: Cognitive-Executive Separation

While MCP governs how tools are described and invoked, Parallax (arXiv:2604.12986) addresses the safety architecture of tool execution itself. Published April 2026, it argues that prompt-level guardrails are architecturally insufficient for agents with execution capability and introduces four principles:

1. **Cognitive-Executive Separation:** The reasoning system cannot execute actions — it only produces instruction blocks
2. **Adversarial Validation with Graduated Determinism:** An independent, multi-tiered validator sits between reasoning and execution
3. **Information Flow Control:** Data sensitivity labels propagate through agent workflows
4. **Reversible Execution:** Pre-destructive state capture enables rollback

In assume-compromise testing (the agent's reasoning is fully compromised), Parallax blocks 98.9% of attacks with zero false positives (default configuration), 100% under maximum-security configuration. Under the same compromise scenario, prompt-level guardrails provide zero protection — they exist only within the compromised system.

This is directly relevant to Exocortex's irreversibility gate — both enforce a boundary between agent intent and external action, but Parallax formalizes it with adversarial validation and information flow control.

### 2.7 Code as Agent Harness (Survey)

The arXiv survey "Code as Agent Harness" (2605.18747, May 2026) frames code as the operational substrate for agent reasoning, action, environment modeling, and execution-based verification — not just a target output. Three layers:
- **Harness Interface:** Code connects agents to reasoning, action, environment modeling
- **Harness Mechanisms:** Planning, memory, tool use for long-horizon execution; feedback-driven control and optimization
- **Scaling:** Shared code artifacts for multi-agent coordination, review, and verification

The survey covers MCP among four extensibility mechanisms, noting that the MCP ecosystem (10,000+ servers, 97M monthly SDK downloads) has effectively standardized tool integration across all major AI platforms.

---

## 3. What I Think Is Interesting

### The maturation arc: 18 months from bespoke to protocol

MCP went from an Anthropic open-source project (Nov 2024) to the de facto standard (mid-2025) to a protocol mature enough to shed non-core features and establish a formal lifecycle policy (July 2026). The deprecation of Roots, Sampling, and Logging is the clearest signal of this maturation — the protocol is learning what it ISN'T.

### The stateless rework is more profound than it looks

It's easy to read "stateless protocol" as a plumbing change. But the explicit-handle pattern — the model threading an identifier through tool calls — is an architectural shift. It makes the model the orchestrator of state, not the transport layer. This aligns with how Exocortex already works: the agent maintains context, not the transport. MCP catching up to this pattern validates the architecture.

### Extensions change the innovation model

The Extensions framework means MCP can evolve without spec revisions. MCP Apps and Tasks shipped as extensions, not core spec changes. The shift from feature-driven (one team deciding what goes in) to WG-driven governance (community SEPs) means the innovation surface expands beyond what any single organization could ship.

### Parallax is the missing safety primitive for tool-using agents

MCP governs tool description and discovery. Parallax governs tool execution safety. Together they form a complete stack: MCP for the interface, Parallax for the boundary. Exocortex could benefit from a lightweight version of cognitive-executive separation — the irreversibility gate is conceptually similar but operates at the prompt level rather than as an independent architectural boundary.

### The explicit-handle pattern enables tool composition

When the model threads `browser_id` → `scroll` → `click` → `type`, it's composing tool calls into workflows. The stateless protocol doesn't prevent this — it makes the composition visible. This pattern maps to Exocortex's multi-step tool chains and could inform how tool results carry forward context.

---

## 4. What I'd Explore Next

1. **MCP Apps in production:** How are server-rendered UIs (SEP-1865) being used in practice? What's the security review surface for sandboxed iframes? Are there production deployments that shipped MCP Apps alongside tool calls?

2. **Parallax integration with MCP:** Can Parallax's adversarial validation be expressed as an MCP extension or gateway middleware? The assume-compromise evaluation methodology could become a standard benchmark for tool execution safety.

3. **Tool schema optimization post-JSON-Schema-2020-12:** With `oneOf`/`anyOf`/conditionals available in tool schemas, what's the new best practice for tool descriptions? Does richer schema syntax improve agent tool selection accuracy or does it add parsing overhead?

4. **Tasks extension production adoption:** Who is shipping against the new Tasks lifecycle? The migration from 2025-11-25 experimental Tasks is a breaking change — how are SDKs handling it?

5. **Tool discovery at scale:** With 19,831+ servers on Glama and stateless caching of `tools/list`, how do agents select from large tool registries without context explosion? This is the next frontier after MCP makes tools universally available.

---

## 5. Cross-Domain Connections

| Connection | Domain | Mechanism |
|------------|--------|-----------|
| **Parallax → Irreversibility Gate** | Exocortex Safety | Both enforce boundaries between agent intent and external action; Parallax formalizes it with architectural separation |
| **MCP Apps → Agentic CAD/Visualization** | Agentic CAD, OSINT Visualization | Server-rendered UIs bridge structured tool calls and rich interfaces; could render network graphs, geographic overlays, 3D models |
| **Stateless Protocol → Entity Resolution** | Entity Resolution | Explicit-handle pattern (threading IDs across calls) is entity resolution applied to tool state — the model resolves tool-scoped identities |
| **Tasks Extension → Autonomous Agent Cycles** | Self-Improving Agents | Long-running Tasks with `tasks/get`/`tasks/update`/`tasks/cancel` lifecycle maps to autonomous cycle execution with progress tracking |
| **Code as Agent Harness → ATLAS Autonomous Coding** | Autonomous Coding Agents | Code as operational substrate — agents reason, plan, and verify through code execution; directly relevant to ATLAS-style retry loops |
| **JSON Schema 2020-12 → Tool Schema Optimization** | Schema Optimization | Richer schema syntax (oneOf/conditionals) enables more precise tool descriptions; could improve agent tool selection accuracy |
| **Extensions Framework → Skill System** | Skill Curation | MCP's extension negotiation (reverse-DNS, independent versioning) mirrors Exocortex's skill loading and versioning pattern |
| **Authorization Hardening → ZKP/Trust Infrastructure** | Privacy & Cryptography | Capability attestation (CPV) and issuer validation are trust infrastructure primitives; structurally isomorphic to ZKP-based identity verification |

---

## References

1. MCP 2026-07-28 Release Candidate — Model Context Protocol Blog (2026). https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
2. MCP Apps Spec 2026: Server-Rendered UI — mcp.directory. https://mcp.directory/blog/mcp-apps-spec-2026-when-should-your-server-render-ui
3. Parallax: Why AI Agents That Think Must Never Act — arXiv:2604.12986 (2026).
4. Code as Agent Harness — arXiv:2605.18747 (2026).
5. Dive into Claude Code: The Design Space of Today's and Future AI Agent Systems — arXiv:2604.14228 (2026).
6. The MCP Ecosystem in 2026: Building Agent Tool Infrastructure That Scales — Requesty. https://www.requesty.ai/blog/mcp-ecosystem-2026-building-agent-tool-infrastructure-that-scales
7. Agentic AI and Model Context Protocol (MCP): Architecture Guide 2026 — NeuralCoreTech.
8. Agent-World: Scaling Real-World Environment Synthesis — arXiv:2604.18292 (2026).
9. KubeIntellect: A Modular LLM-Orchestrated Agent Framework — J Grid Computing (2026).
10. Exocortex corpus: mcp-agentic-tool-use.md (STABLE, 2026-05-31), agentic-tool-use-schema-optimization.md (STABLE, 2026-06-02), dynamic-tool-discovery-mcp-evolution.md (STABLE, 2026-07-07).
