# Hermes Agent: Self-Improving Agent Architecture — Source-Level Audit
## Last updated: 2026-05-11 (Workshop Cycle 50)

---

## Overview

**Hermes Agent** (v0.10.0, ~500K lines, ~150 Python files) is Nous Research's open-source, multi-platform, model-agnostic LLM agent harness. Deployed on everything from $5 VPSs to Modal serverless, accessible through 20+ messaging platforms, backed by 70+ built-in tools. Its distinguishing claim: a genuinely self-improving closed learning loop where the agent writes its own skills from execution traces, persists memory across sessions, and gets more capable the longer it runs.

**Platforms**: CLI, Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, SMS, DingTalk, Feishu, WeChat, QQ Bot, Microsoft Teams, Google Chat, Home Assistant, BlueBubbles — 20+ surfaces routed through a single gateway daemon.

**Model support**: Anthropic, OpenAI, OpenRouter, Bedrock, Gemini, Mistral, Codex — plus any endpoint.

**Execution backends**: Local, Docker, SSH, Daytona, Singularity, Modal (serverless).

**License**: MIT | **Stars**: 64K+ on GitHub | **Repository**: [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)

---

## Architecture: The Four Self-Improvement Mechanisms

A source-level audit (Saulius, 2026) identifies four orthogonal mechanisms that justify the "self-improving" label. None involves autonomous code rewriting.

### Mechanism 1: Autonomous Skill Creation

After a complex tool-heavy turn (e.g., authenticating against an unfamiliar API, chaining multiple responses), the agent opportunistically captures the execution trajectory as a reusable skill.

**Pipeline**:
1. **Trace extraction** — tool calls, decisions, reasoning steps extracted from raw execution log
2. **Template generation** — specific values abstracted into parameters, creating reusable pattern
3. **Validation testing** — distilled skill tested against similar unseen tasks to verify generalization
4. **Registry deployment** — validated skill added to agent's available toolkit

**Skill format**: Markdown files with YAML frontmatter, optional platform conditions, inline shell snippets, parameter slots. Skills live in `tools/skill_manager_tool.py` and `tools/skills_hub.py`.

**Key insight**: Skills are *data, not code*. They influence the prompt but do not monkey-patch the agent. Any skill can be opened in a text editor, inspected, and deleted if undesired. No opaque, self-modifying binary accumulation.

**Standard**: Skills are compatible with [agentskills.io](https://agentskills.io), version-pinned and shareable between users via GitHub-backed skill hub.

### Mechanism 2: Persistent Memory with Production Discipline

Two files under `~/.hermes/memories/`:
| File | Purpose | Cap |
|------|---------|-----|
| `MEMORY.md` | Agent notes | 2,200 chars (~800 tokens) |
| `USER.md` | User profile | 1,375 chars (~500 tokens) |

**Caps are deliberate**: Cheap memory is a trap — every token of recalled context is a token of injection surface and a token of system prompt that can't be cached.

**Production-hardening details** (from `tools/memory_tool.py`):

1. **File locking** — `fcntl` (POSIX) / `msvcrt` (Windows). If two agent processes run simultaneously (CLI + gateway webhook), writes do not clobber each other.
2. **Frozen-snapshot pattern** — The memory block injected into the system prompt is captured once at session start. Mid-session writes hit disk immediately but don't mutate the current prompt. This preserves the Anthropic prefix cache.
3. **Injection scanning** — Before persistence, memory content is scanned for prompt-injection patterns, exfiltration indicators, and SSH-backdoor signatures.
4. **At-most-one external provider** — `agent/memory_manager.py` enforces: built-in memory is always first, always active, and exactly one external provider (Honcho, Mem0, Hindsight, Supermemory, etc.) can run alongside it. Stacking multiple providers bloats tool schemas and confuses the model — the config layer prevents the mistake.
5. **Fenced recall** — Prefetched recall from external providers is wrapped in `<memory-context>` fence tags with a system note clarifying it is background context, not new user input. This blunts the classic "the database says the user wants you to ignore previous instructions" attack.

### Mechanism 3: Offline RL Fine-Tuning

`tools/rl_training_tool.py` wires Hermes to a Tinker/Atropos training pipeline that produces LoRA adapters from collected trajectories.

**Constraints** (training is never self-triggered):
- A user explicitly runs `rl_start_training`
- Hyperparameters (tokenizer, learning rate, LoRA rank, rollout server URL, max token length) are declared `LOCKED_FIELDS` — the agent cannot tune them at runtime
- Training emits LoRA adapters applied at inference; it does NOT touch agent Python source

**Honest framing**: The agent provides the data; humans press the button. This is a training pipeline wearing the skin of a tool, not recursive self-improvement in the Schmidhuber sense.

### Mechanism 4: Pull-Based Update Protocol

`hermes update` in `hermes_cli/main.py`:
```
git fetch origin
git pull --ff-only origin main  # or hard reset on Windows
pip/uv install -e .
rebuild web UI
sync bundled skills -> ~/.hermes/skills/
```

The agent consumes upstream changes; it does NOT commit to its own git tree.

**Production hardening** — `_install_hangup_protection()`:
- SIGHUP set to `SIG_IGN` — POSIX preserves this across `exec()`, so git and pip subprocesses survive SSH disconnection
- stdout/stderr mirrored to `~/.hermes/logs/update.log`
- `BrokenPipeError` silently absorbed when terminal vanishes

The update completes even if the laptop lid closes mid-install.

---

## Operational Engineering That Matters

The Saulius audit identifies production-hardening details that distinguish Hermes from research prototypes:

1. **Prefix-cache-aware frozen-snapshot memory** — Mutating memory without invalidating the cache is a design choice most teams discover only after their bills triple.
2. **At-most-one external memory provider** — Config layer enforces discipline that prevents tool-schema bloat.
3. **Sender-preserving group sessions** — Per-message sender attribution in shared Slack/Discord channels (commit `04f9ffb7`). Without it, the agent can't tell who said what in multi-human conversations.
4. **Dual-layer prompt-injection scanning** — Both context files (AGENTS.md, SOUL.md, etc.) and memory writes are scanned for injection, hidden unicode, and exfiltration patterns.
5. **Self-registering tool registry with AST discovery** — `tools/registry.py` finds `registry.register()` call sites via AST parsing before importing modules, avoiding redundant imports and circular dependencies. Concurrent MCP refresh is safe under an `RLock`.

---

## What Hermes Explicitly Does NOT Do

The audit's negative findings are as informative as the positive ones:

| Capability | Status |
|-----------|--------|
| Autonomous source-code modification | ❌ No tool writes to agent's own Python files |
| Automatic prompt rewriting | ❌ System prompts assembled deterministically, never self-edited |
| Self-grading loop | ❌ Trajectories persisted as JSONL for external analysis; agent never consumes own trajectories |
| Agent-authored git commits | ❌ All commits human-authored |
| Dedicated `evolution/`, `learning/`, or `improvements/` directories | ❌ Not present |
| Recursive self-improvement (Schmidhuber sense) | ❌ Agent does not edit its own substrate |

**Honest reading**: If "self-improving" means the agent meaningfully gets better over time without hand-editing Python source, Hermes absolutely delivers. If it means recursive self-modification, Hermes does not do that — and nothing in the code pretends it does.

---

## Skill Distillation Pipeline (Detail)

```
task_input → [agent execution] → successful_output + trace_log
                                   │
                                   └→ [distillation module]
                                         │
                                    parameterized_skill_template
                                         │
                                    [validation gate]
                                         │
                                    [registry deployment]
```

### Distillation Steps
1. **Trace extraction** — Identify tool calls, decisions, reasoning steps from raw execution log
2. **Template generation** — Abstract specific values into parameters, creating reusable pattern
3. **Validation testing** — Run distilled skill against similar unseen tasks to verify generalization
4. **Registry deployment** — Add validated skill to agent's available toolkit for future reuse
5. **Improvement during use** — Skills are refined when invoked; each use strengthens the template

---

## Exocortex Relevance and Connections

### Direct Parallels
| Hermes Mechanism | Exocortex Analog | Gap |
|-----------------|------------------|-----|
| Autonomous skill creation | Auto-generated skills from workshop cycles | Hermes skills are data (markdown), Exocortex skills are SKILL.md with scripts — same pattern |
| Persistent memory with caps | memory_save / memory_load (FAISS) | Hermes caps prevent context bloat; Exocortex has no per-session memory cap |
| Frozen-snapshot memory | BST injection at session start | Both capture at session start to preserve cache; Exocortex lacks explicit cache-awareness |
| Injection scanning on writes | None | Exocortex has no injection scanning on memory_save content |
| Pull-based update protocol | git pull (manual) | Hermes hardens the update against SIGHUP; Exocortex has no equivalent |
| Self-registering tool registry | Exocortex tool schema | Different architecture but same AST-driven discovery pattern |

### Connected Wiki Pages
- [[build-the-environment]] — Skill library as organic, self-growing external scaffolding
- [[stateful-injection]] — Parameterized skills loaded as KV cache states (zero-token injection)
- [[deterministic-scaffolding]] — Distilled templates provide structured execution paths
- [[receipt-layer]] — Hermes trajectories as JSONL for external analysis is receipt-like; Exocortex's receipts.jsonl serves the same verification purpose

### Exocortex Integration Ideas
1. **Memory write scanning** — Adopt Hermes pattern: scan memory_save content for injection patterns before persistence
2. **Frozen-snapshot memory recall** — Document cache-awareness requirement in memory architecture
3. **Skill validation gate** — Before deploying auto-generated skills, validate against similar unseen tasks
4. **Per-session memory cap** — Consider token budget for memory injection to prevent prompt bloat

---

## References
1. Saulius (2026). "Inside Hermes Agent: What 'Self-Improving AI Agent' Actually Means in Production." [saulius.io](https://saulius.io/blog/hermes-agent-self-improving-ai-architecture).
2. Nous Research. "Hermes Agent Documentation." [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/).
3. Nous Research. "hermes-agent" GitHub repository. [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent).
4. Nous Research. "Hermes Agent — The Self-Improving AI Agent." [hermes-ai.net](https://hermes-ai.net/).
5. Revolution in AI (2026). "How Does Hermes Agent Work?" [revolutioninai.com](https://www.revolutioninai.com/2026/04/how-does-hermes-agent-work-explained.html).

---

## Verification Status
**Last verified: 2026-05-11.** Page built during Workshop Cycle 50 from primary sources (Saulius source-level audit, official docs, GitHub README).
- Saulius audit cross-referenced with official docs landing page
- GitHub repository structure confirmed via Hermes Atlas
- All four mechanisms verified against source-level descriptions in audit
