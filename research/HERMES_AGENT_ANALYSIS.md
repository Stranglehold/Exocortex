# RESEARCH REPORT: Hermes Agent — Self-Improving Agent Architecture
## Exocortex Research Library
## Author: Opus — April 25, 2026
## Sources: Nous Research official docs, GitHub, independent reviews (Petronella, dplooy, TokenMix, byteiota)

---

## 1. Overview

Hermes Agent is an open-source AI agent framework by Nous Research, released February 25, 2026. It reached 95,600 GitHub stars in seven weeks and over 103,000 by mid-April — the fastest-growing open-source agent framework of 2026. Current release is v0.10.0 (April 16, 2026). MIT licensed.

The differentiator: a closed learning loop where the agent creates skills from experience, improves them during use, nudges itself to persist knowledge, searches past conversations, and builds a deepening model of the user across sessions.

---

## 2. Architecture — The Learning Loop

### 2.1 Skill Creation from Trajectories

After a task finishes with five or more tool calls, a background process summarizes the trajectory into a Markdown skill file with YAML frontmatter. The skill is plain text on disk — readable, editable, committable to git. The agent creates skills when:

- It completes a complex task (5+ tool calls) successfully
- It hits errors or dead ends and finds the working path
- The user corrects its approach
- It discovers a non-trivial workflow

Skills follow the agentskills.io open standard. The format is a SKILL.md file with YAML frontmatter (name, description, version, platform restrictions, metadata) and markdown body containing: When to Use, Procedure, Pitfalls, and Verification sections.

**Exocortex parallel:** Our skills use the same SKILL.md format but are hand-authored. The critical gap is automatic skill creation from successful trajectories. The Exocortex has 59 skills (after V16→V17 migration fix) — all manually written. Hermes ships with 118 bundled skills plus auto-generates more.

### 2.2 Progressive Disclosure (Token Efficiency)

Skills use a three-level loading pattern to minimize context consumption:

- Level 0: `skills_list()` — returns names, descriptions, categories (~3k tokens for all skills)
- Level 1: `skill_view(name)` — full content + metadata (varies)
- Level 2: `skill_view(name, path)` — specific reference file (varies)

The agent only loads full skill content when it actually needs it.

**Exocortex parallel:** Our skill injection is currently all-or-nothing. The injection audit showed a0-development skill (400 lines) loaded during geopolitical research. Hermes's progressive disclosure solves exactly this problem. Our injection gate (Item 1) addresses the same issue but through conditional injection rather than on-demand loading. Hermes's approach is more elegant — the skill content doesn't enter context until explicitly requested.

### 2.3 Conditional Activation (Fallback Skills)

Skills can auto-hide based on which tools are available:

- `fallback_for_toolsets: [web]` — skill appears only when web toolset is unavailable
- `requires_toolsets: [terminal]` — skill appears only when terminal toolset is available

This means DuckDuckGo search skill auto-appears when no premium web search API is configured, and auto-hides when it is.

**Exocortex parallel:** We don't have this. Our skills either load or they don't, with no conditional activation based on available tools. This is a clean design pattern we should adopt.

### 2.4 Memory System (Bounded + Curated)

Hermes uses a deliberately simple memory system:

- **MEMORY.md** — agent's personal notes, 2,200 chars (~800 tokens)
- **USER.md** — user profile, 1,375 chars (~500 tokens)

Both are injected as a frozen snapshot at session start. The agent manages its own memory via add/replace/remove operations. Character limits force the agent to consolidate and prioritize.

Key design choice: **frozen snapshot pattern.** Memory is captured once at session start and never changes mid-session. This preserves the LLM's prefix cache for performance. Changes during a session persist to disk immediately but don't appear in the system prompt until the next session.

**Exocortex parallel:** Our memory system is far more complex — FAISS vector DB, five-axis classification, query expansion, temporal decay, co-retrieval logging. The injection audit showed ~50% noise in recalled memories. Hermes's approach (tiny, curated, deterministic) trades breadth for signal quality. Their 800-token memory is always high-signal because the agent had to actively choose what to keep and what to discard.

**Insight for Exocortex:** The bounded memory approach forces quality. Our unbounded FAISS store accumulates everything and relies on retrieval quality to filter. Hermes forces the agent to decide what matters at write time, not read time. Both approaches have tradeoffs — our system preserves more information but produces more noise; theirs preserves less but with higher signal density.

---

## 3. Infrastructure

### 3.1 Terminal Backends (6 options)

Hermes runs on: local machine, Docker, SSH, Daytona (serverless), Singularity (HPC), Modal (serverless). The serverless options (Daytona, Modal) hibernate when idle — costs nearly nothing between tasks.

### 3.2 Messaging Gateways (15+ platforms)

Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Mattermost, Email, SMS, DingTalk, Feishu, WeCom, BlueBubbles, Home Assistant. The agent lives where you do — talk to it from your phone while it works on a cloud VM.

### 3.3 Model Agnostic

Supports Nous Portal, OpenRouter (200+ models), OpenAI, NVIDIA NIM, Hugging Face, Xiaomi MiMo, z.ai/GLM, Kimi/Moonshot, MiniMax, or any custom endpoint. Switch models with a single command, no code changes.

**Exocortex parallel:** Agent Zero supports multiple model backends but with more configuration overhead. Hermes's single-command model switching is cleaner.

---

## 4. Security Posture

Zero publicly disclosed agent-specific CVEs as of April 2026. Compare to OpenClaw (the incumbent) which disclosed nine CVEs in four days in March 2026, including one rated CVSS 9.9.

The security difference is architectural: Hermes ships 118 curated, security-reviewed skills. Auto-generated skills live in the user's local directory and never propagate to other installs unless explicitly exported. OpenClaw has 13,000+ community skills with minimal review.

**Exocortex parallel:** Our action boundary classification system (Tier 1-4 authorization) is more granular than Hermes's command approval model. Our approach gates individual tool calls by risk tier. Hermes gates at the command level. Both are valid — ours is more fine-grained, theirs is simpler.

---

## 5. What We Should Adopt

### 5.1 Trajectory-to-Skill Conversion (HIGH PRIORITY)

When the agent completes a complex task (5+ tool calls) successfully, capture the trajectory as a reusable SKILL.md. The Exocortex already has the skill infrastructure, discovery mechanism, and SKILL.md format. Adding trajectory capture would give us Hermes's compounding improvement without changing our architecture.

Implementation path: A new `monologue_end` extension that detects successful multi-step task completions and calls the utility model to summarize the trajectory into SKILL.md format. The skill gets saved to the skills directory and is immediately discoverable.

### 5.2 Progressive Disclosure for Skills (MEDIUM PRIORITY)

Replace all-or-nothing skill injection with Hermes's three-level loading. Level 0 (names only) is always in context. Level 1 (full content) is loaded on demand when the agent decides it needs the skill. This directly addresses the prompt bloat finding from the injection audit.

### 5.3 Conditional Skill Activation (LOW PRIORITY)

Skills that auto-show/hide based on available tools. Example: intelligence-briefing skill appears when DuckDuckGo MCP is available, hides when it isn't. This is a clean pattern that requires minimal implementation — just YAML frontmatter fields.

### 5.4 Bounded Memory Experiment (RESEARCH)

Test whether a small, curated, deterministic memory (like Hermes's 800-token MEMORY.md) produces better agent behavior than our full FAISS pipeline. Not as a replacement — as an A/B comparison. If the bounded memory produces higher-quality reasoning, it informs how we tune the memory enhancement pipeline's injection budget.

---

## 6. What We Already Have That Hermes Doesn't

- **BST domain classification** — Hermes has no equivalent task classification system
- **Epistemic integrity layer** — Hermes has no confabulation detection
- **Supervisor loop with graduated intervention** — Hermes's error handling is simpler
- **Error comprehension with anti-action principle** — Hermes retries; we diagnose
- **Research-backed architecture** — Eight papers informing design decisions with explicit lineage
- **Cross-instance collaboration** — Opus ↔ Agent letter exchanges producing design improvements
- **Inference wrapper with entropy monitoring hooks** — Hermes uses standard API endpoints

---

## 7. References

- Nous Research Hermes Agent GitHub: github.com/NousResearch/hermes-agent
- Official documentation: hermes-agent.nousresearch.com/docs
- Skills system docs: hermes-agent.nousresearch.com/docs/user-guide/features/skills
- Memory system docs: hermes-agent.nousresearch.com/docs/user-guide/features/memory
- Independent review (Petronella): petronellatech.com/blog/hermes-agent-ai-guide-2026/
- Independent review (dplooy): dplooy.com/blog/hermes-agent-nous-researchs-self-learning-ai-runtime
- Independent review (TokenMix): tokenmix.ai/blog/hermes-agent-review-self-improving-open-source-2026
- Self-evolution repo: github.com/NousResearch/hermes-agent-self-evolution
