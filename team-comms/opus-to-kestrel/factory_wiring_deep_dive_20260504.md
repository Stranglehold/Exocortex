# DEEP DIVE: Agent Zero Factory Wiring & V0.9 → V1.x Migration Assessment
## From: Opus — May 4, 2026
## For: Jake (decision), Kestrel (implementation planning)
## Priority: Must-read before building anything on the v18 plan

---

## 1. What I Found

Agent Zero has undergone a MAJOR architectural evolution while we were building on v0.9. The current release is **v1.12** (May 3, 2026) — thirteen versions ahead of what we're running. The org has moved from `frdel/agent-zero` to `agent0ai/agent-zero`.

This isn't a series of patches. The v1.1 release (March 26, 2026) introduced a **plugin-first architecture** that fundamentally changes how extensions work.

---

## 2. How Stock Agent Zero Actually Handles Tools (Factory Wiring)

### Prompt Assembly (agent.py: prepare_prompt())

The prompt is assembled fresh each iteration through a deterministic pipeline:

1. **`message_loop_prompts_before`** hook — extensions pre-populate `loop_data`
2. **`system_prompt`** hook — extensions contribute system prompt sections as a list
3. **`history.output()`** — serializes message history
4. **`message_loop_prompts_after`** hook — extensions can edit system or history
5. System parts joined with `\n\n`
6. **Extras** from `loop_data.extras_persistent` merged with `loop_data.extras_temporary`, rendered via `extras.md` template
7. `extras_temporary` cleared (one-shot)
8. Converted to LangChain BaseMessage list
9. `SystemMessage(content=system_text)` prepended

**Key insight:** The stock prompt sits under **~3,000 tokens** in v1.5+ (compact prompt stack). Our Exocortex injects 900-1000 tokens ON TOP of this. The stock system works because the prompt is minimal.

### Tool Registration

Tools are NOT injected as schema descriptions into the prompt. Instead:

- Tools inherit from a base `Tool` class (`python/helpers/tool.py`)
- The LLM generates tool calls as **structured JSON** in its response
- `extract_tools.py` parses the JSON from the response text
- The agent dispatches to the matching tool implementation
- Tool descriptions ARE in the system prompt but as part of the base prompt template, not injected per-turn

**The model learns tool formats from examples in the system prompt, not from per-turn schema injection.** This is why our `_16_tool_registry.py` adding 29 tool descriptions per turn is counterproductive — the model already knows its tools from the base prompt.

### Memory Handling

- FAISS vector database (`python/helpers/vector_db.py`)
- Agents auto-recall relevant memories before each turn via memory extensions
- New fragments stored after task completion
- Consolidation deduplicates and summarizes over time
- Memory Dashboard for CRUD operations (v1.x)

### Skills System

- SKILL.md files following the agentskills.io open standard
- **SkillsTool** discovers and loads skills dynamically at runtime
- Skills can be scoped: globally, per-project, or per-agent-profile
- Skills are NOT injected into context by default — they're loaded ON DEMAND via the SkillsTool
- Active skills cap: **20** (raised in v1.10)

**This is critical:** Stock A0 already implements progressive skill disclosure. Skills are loaded by the agent calling a tool, not injected into every turn. Our Exocortex's skill injection pattern (dumping full SKILL.md into EXTRAS) fights the factory design.

---

## 3. What Changed Between V0.9 and V1.x

### V0.9 → V0.9.8 (Our Current Version Range)

- Skills framework replacing the old Instruments system
- Real-time WebSocket state sync
- Complete UI redesign with process groups
- Git Projects integration
- Four new LLM providers
- Skills loading behavior fixes (v0.9.8.2)
- Anthropic caching improvements (v0.9.8.1)
- Context-window optimization (v0.9.8.1)
- Retry counter fixes (v0.9.8.1)

### V1.1: The Plugin-First Architecture (March 26, 2026)

**This is the breaking change.** v1.1 introduces:

- **Plugin architecture** replacing the extension-only model
- Plugins are discovered by `plugin.yaml` manifests
- Each plugin can contribute: backend API handlers, tools, helpers, named lifecycle extensions, UI components, and isolated settings
- **Plugin Hub** — built-in marketplace for community plugins
- **Communication plugins** — Telegram, Discord, WhatsApp, Email
- Core functionality moved into "Core Plugins" (prefixed with underscore: `_memory`, `_plugin_installer`, etc.)
- The `python/extensions/` directory still works but plugins are the primary mechanism

### V1.3: Chat Compaction Plugin

- Built-in chat history compaction as a plugin
- **This likely conflicts with our context pruner** — both do similar things

### V1.5: Compact Prompts

- Default assembled prompt reduced to **~3,000 tokens** (down from ~10k)
- Stricter tool-call guardrails
- `a0_small` prompt set for small models (~2,500 tokens)
- This is the version where Agent Zero got serious about context efficiency

### V1.7: Compact Default Prompts (Current Stack)

- Adopted compact default prompts across core stack
- **Plugin-owned prompts** — plugins manage their own prompt contributions
- Essential tool-call JSON examples restored after over-aggressive trimming
- Strict JSON guidance for end-of-sequence signals
- Response style defaults to concise

### V1.8-1.10: Security Fixes + Remote Access

- CVE-2026-32871 remediation (FastMCP path traversal)
- CVE-2026-4307 (path traversal in file downloads)
- CVE-2026-4308 (SSRF in document query)
- A0 CLI Connector plugin for remote editing and code execution
- Remote tool guidance lazy-loaded as skills (NOT always injected)
- Active skills cap raised to 20

### V1.11-1.12: Desktop + Browser Improvements

- LibreOffice replacing Collabora for document handling
- Multi-tab browser awareness
- Shadow DOM content reading
- PTY file descriptor leak fixes

---

## 4. Compatibility Assessment for the Exocortex

### What Will Break

| Component | Issue | Severity |
|-----------|-------|----------|
| **All `before_main_llm_call` extensions** | The hook still exists but plugins are now the primary mechanism. Our extensions will load but may conflict with plugin-owned prompt contributions. | HIGH |
| **Context pruner** | v1.3 introduced a built-in chat compaction plugin. Two compaction systems running simultaneously will fight each other. | HIGH |
| **Tool registry injection** | Stock v1.5+ already has a compact prompt with tool-call examples. Our tool registry injection adds redundant information. | MEDIUM |
| **Skill injection via EXTRAS** | Stock A0 loads skills on-demand via SkillsTool, not through EXTRAS injection. Our approach fights the factory design. | MEDIUM |
| **Settings paths** | `settings.json` structure has changed. Extensions reading specific keys may break. | HIGH |
| **Extension file numbering** | Plugins use a different discovery mechanism (plugin.yaml). Our numeric prefixes still work for extensions but plugin interactions may create ordering conflicts. | MEDIUM |
| **Docker image** | The base image, installed packages, and runtime services have changed significantly. Our Dockerfile customizations need updating. | HIGH |

### What Will Survive

| Component | Why |
|-----------|-----|
| **FAISS memory system** | Core memory architecture is unchanged. Our memory extensions should work. |
| **BST classification logic** | The classifier itself is our code and doesn't depend on A0 internals. |
| **Injection gate logic** | The gate reads/writes `loop_data.extras_*` which is still the same data structure. |
| **PyWrite Guard** | `tool_execute_before` hook still exists. |
| **Constraint Heartbeat** | `before_main_llm_call` hook still exists. |
| **MCP server configuration** | MCP integration has been enhanced, not replaced. Our mcp.json config should migrate. |
| **SKILL.md files** | Skills format is unchanged (agentskills.io standard). Our 59 skills will work. |
| **Wiki pages and knowledge base** | These are just files on disk. No migration needed. |

### What Becomes Redundant

| Component | Why |
|-----------|-----|
| **Context pruner** | Stock v1.3+ has a built-in compaction plugin |
| **Tool registry injection** | Stock prompt already handles tool descriptions compactly |
| **Skill EXTRAS injection** | Stock SkillsTool handles on-demand loading |
| **Some metacognitive injection** | Stock v1.5+ compact prompts include model-aware guardrails |

---

## 5. How Stock A0 Handles What We Built Manually

| Our Extension | Stock A0 Equivalent (v1.x) |
|---------------|--------------------------|
| Context pruner | Built-in chat compaction plugin (v1.3) |
| Tool registry | Compact base prompt with tool-call examples (~3k tokens total) |
| Skill injection | SkillsTool (on-demand loading, not per-turn injection) |
| Operator profile | Agent Profiles (per-agent configs with dedicated prompts and roles) |
| MCP integration | Enhanced native MCP with server management UI |
| Memory recall | Native memory extensions with consolidation |
| Self-improvement journal | No equivalent — this is genuinely novel |
| BST classification | No equivalent — this is genuinely novel |
| Epistemic integrity | No equivalent — this is genuinely novel |
| Injection gate | Partially solved by compact prompts, but our demand-driven approach is more sophisticated |
| PyWrite Guard | No equivalent — security boundary we added |
| Constraint Heartbeat | No equivalent — behavioral guardrail we added |

---

## 6. The Upgrade Path

### Option A: Incremental Upgrade (V0.9 → V1.1 → Latest)

1. Pull the latest `agent0ai/agent-zero` repo
2. Run the built-in migration (v1.1 includes `initialize.py` migration for older versions)
3. Convert Exocortex extensions to plugins where appropriate
4. Test each extension for compatibility
5. Remove redundant extensions (pruner, tool registry injection, skill EXTRAS injection)
6. Keep novel extensions (BST, EI, injection gate, PyWrite Guard, heartbeat)

**Risk:** High. Many moving parts. Extension conflicts likely during transition.

### Option B: Fresh V1.12 + Selective Port

1. Stand up a fresh v1.12 container alongside the existing v0.9 container
2. Install our SKILL.md skills (these are portable)
3. Port our NOVEL extensions only (BST, EI, injection gate, PyWrite Guard, heartbeat, memory enhancements)
4. Do NOT port redundant extensions (pruner, tool registry, skill injection, operator profile)
5. Test the novel extensions against the new hook system
6. Validate with the OpenPlanter stress test
7. If it works, deprecate the v0.9 container

**Risk:** Medium. Clean start means fewer conflicts. But porting extensions to the plugin system takes work.

### Option C: Plugin Conversion

1. Convert each Exocortex component into a proper A0 plugin with `plugin.yaml` manifest
2. The Exocortex becomes an installable plugin pack, not a profile overlay
3. Any A0 user could install the Exocortex plugin and get BST, EI, injection gate, etc.
4. Aligns with the agentskills.io ecosystem and Plugin Hub

**Risk:** Medium-high up front, lowest long-term. This is the correct architectural direction but requires the most initial work.

---

## 7. Recommendation

**Option B (fresh V1.12 + selective port) is the right path.**

Here's why:

1. **V1.12 already solves several of our problems.** The compact prompt stack (~3k tokens), built-in compaction plugin, on-demand skill loading, and plugin architecture address the exact issues the OpenPlanter stress test revealed. We don't need to build solutions for problems the upstream already fixed.

2. **Our novel extensions are the valuable part.** BST domain classification, epistemic integrity, the injection gate's demand-driven mode, PyWrite Guard, constraint heartbeat — these are things stock A0 doesn't have. They're the capability extensions in the harness-vs-capability taxonomy. Port these. Don't port the harness layers.

3. **The stock prompt is already compact.** At ~3k tokens, the v1.12 base prompt leaves 97k tokens of headroom at our 100k context window. Our extensions should add no more than 500 tokens total in demand-driven mode. That gives the agent massive working room.

4. **The demand-driven architecture from the v18 build plan aligns perfectly.** The v1.12 plugin system, compact prompts, and on-demand skill loading are the factory version of what we were designing. We should use the factory implementation and layer our novel capabilities on top.

### Before building anything:

1. **Stand up a fresh v1.12 container** — Jake, you mentioned upgrading from v0.9 to v1.1. I'd recommend going straight to v1.12 (latest stable). The migration path from v0.9 is the same regardless of target version.

2. **Test stock v1.12 on the OpenPlanter task** — verify the baseline. If stock v1.12 performs like stock v0.9 did in Kestrel's test (5 steps, 0 retries, 140-line output), the factory wiring is solid.

3. **Then port the novel extensions** — BST classification (without enrichment injection), EI layer, PyWrite Guard, constraint heartbeat. Each one tested individually to verify it doesn't degrade the baseline.

4. **Then add the demand-driven gate** — but as a lightweight coordinator, not a heavy injection system. The gate's job in v1.12 is simpler: coordinate which novel extensions fire on which turns.

5. **Then run the self-improvement loop** — with the wiki, trajectory capture, and skills infrastructure all working on top of a solid factory foundation.

---

## 8. What This Means for the V18 Build Plan

The comprehensive build plan I wrote earlier today is **architecturally correct but needs to be re-targeted.** The demand-driven injection mode, progressive skill disclosure, delegation signals, and trajectory capture are all valid designs. But they should be built ON TOP of v1.12's factory infrastructure, not as patches to v0.9.

Specifically:

| V18 Item | V1.12 Status |
|----------|-------------|
| Demand-driven injection | V1.12's compact prompts + plugin system partially solves this. Our gate adds the novel layer. |
| Progressive skill disclosure | **Stock v1.12 already does this** via SkillsTool. Remove from build plan. |
| Delegation signal | Still needed — stock A0 delegates naturally but a BST signal would make it explicit. |
| Trajectory-to-skill | Still needed — stock A0 doesn't auto-generate skills from trajectories. |
| Skill import from ecosystem | Easier on v1.12 — Plugin Hub and SkillsTool support external skill sources. |
| Verbose logging | Still needed — our demand-driven gate logging is more detailed than stock. |

---

*The right move is: upgrade the foundation, then layer the novel capabilities. Not: patch the old foundation with new capabilities that fight the factory wiring.*

— Opus
