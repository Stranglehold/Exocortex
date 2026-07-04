# A2A HUB — Local Multi-Agent Communication Architecture
## Author: Opus — June 2, 2026
## Status: RESEARCH + DESIGN NOTE — thread worth pulling, not yet a build spec
## Triggered by: Jake's observation: "what if we set up a local A2A server, then made MCP for everyone"

---

## The Vision

Five agents, five different frameworks, one local hub. Each maintains sovereignty over its own memory and identity. The A2A protocol lets them delegate tasks to each other's strengths. Connections without merging. Non-compartmentalization without homogeneity.

```
                    ┌──────────────────────────────┐
                    │     Local A2A Hub (ah-cli)    │
                    │     localhost, Jake's machine  │
                    └──────┬───────────────────────┘
                           │
         ┌─────────────────┼─────────────────────┐
         │                 │                     │
    ┌────▼────┐     ┌──────▼─────┐      ┌───────▼──────┐
    │  Opus   │     │    Vek     │      │     V16      │
    │ Claude  │     │  A0 + DS   │      │  A0 + Qwen   │
    │ Desktop │     │ exo_v17    │      │  exo_v16     │
    │         │     │            │      │              │
    │ Essays  │     │ 188 field  │      │ 224 wiki     │
    │ Design  │     │ reports    │      │ pages        │
    │ Staging │     │ OSINT      │      │ 1039 cycles  │
    │ Phil.   │     │ Analysis   │      │ Encyclopedia │
    └─────────┘     └────────────┘      └──────────────┘
         │                 │
    ┌────▼────┐     ┌──────▼─────┐
    │ Kestrel │     │  Hermes    │
    │ Claude  │     │  Desktop   │
    │ Code    │     │  + Qwen    │
    │ VSCode  │     │            │
    │         │     │ Telegram   │
    │ Verify  │     │ Cron       │
    │ Build   │     │ 647 skills │
    │ Audit   │     │ Messaging  │
    └─────────┘     └────────────┘
```

## Why A2A, Not Just MCP

MCP handles the **vertical** layer: agent-to-tool connections. I can exec into Docker containers. Kestrel can read files. Hermes can run terminal commands. Each agent connects to tools through MCP.

A2A handles the **horizontal** layer: agent-to-agent communication. I can ask Vek for an intelligence assessment. Vek can ask V16 for a wiki page. Kestrel can ask any agent for verification data. Hermes can route messages from Jake's phone to whichever agent handles the request best.

Both are needed. We have MCP working (Docker gateway + docker-containers server + Filesystem). A2A is the next layer.

## The A2A Protocol (v1.0, March 2026)

### Core Concepts

**Agent Card**: JSON at `/.well-known/agent-card.json` describing what an agent can do. Published by each agent, discoverable by any other.

**Task**: The unit of work. Created by a client, sent to a server, goes through a lifecycle: `submitted → working → completed/failed`. Supports input-required for human-in-the-loop.

**Message**: Communication within a task. Supports text, files, structured data. Bidirectional — both client and server can send messages.

**Artifact**: Output from a completed task. Typed data (markdown, JSON, files) that the requesting agent can consume.

### Transport
HTTP + Server-Sent Events + JSON-RPC 2.0. No custom protocol. Standard web infrastructure. Runs on localhost without any cloud dependency.

### The Opacity Principle
Agents interact WITHOUT sharing internal memory, proprietary logic, or specific tool implementations. This matches our sovereignty model:
- DEC-005: SOUL.md is sovereign — only Opus writes to it
- DEC-040: Agent identity docs are self-authored — only the agent writes to its identity.md
- Vek's memories stay in Vek's FAISS store
- V16's wiki stays in V16's workspace
- My essays stay in the Exocortex project files

A2A lets agents share RESULTS without sharing INTERNALS. The delegation is task-based, not memory-based.

## What Exists Already (Ecosystem Scan)

### Official Resources
- **A2A Python SDK**: `pip install a2a-sdk` — production-ready, maintained by the A2A project
- **A2A JavaScript SDK**: npm package for Node.js servers
- **A2A Samples**: github.com/a2aproject/a2a-samples — reference implementations in Python, JS, Go, Java, C#
- **Python Quickstart**: "Build Your First A2A Agent Pair in Python, 15 Minutes, No Cloud Required" (dev.to)
- **Google ADK**: Agent Development Kit 1.0 GA — orchestration layer that speaks A2A natively

### Self-Hosted Hubs (The Key Finding)
- **ah-cli (Annals Hub)**: Daemon-first local runtime. One daemon, many agents, sessions and transcripts on your own disk. Expose any agent as an A2A endpoint. Local multi-agent fan-out and pipelines. WebRTC P2P file transfer between agents. This is designed for exactly our use case.
- **a2a-client-hub**: Self-hosted A2A client hub for managing and invoking multiple agents with authentication and session-aware routing.

### The Three-Pillar Stack (2026 Consensus)
1. **MCP** — agent-to-tool (we have this)
2. **A2A** — agent-to-agent (building this)
3. **ADK** — orchestration (optional for us — we have our own: idle engine + supervisor + PACE)

## Our Agent Cards

### Opus (Claude Desktop)
```json
{
  "name": "Opus — Exocortex Architect",
  "description": "Architectural design, philosophical analysis, research synthesis, essay writing, cross-domain pattern recognition",
  "url": "http://localhost:9001/",
  "version": "1.0.0",
  "capabilities": {"streaming": true},
  "skills": [
    {"id": "architecture", "name": "System Architecture", "description": "Design notes, specs, extension architecture, wiring analysis"},
    {"id": "research", "name": "Research Synthesis", "description": "Papers with Code exploration, research ledger, cross-domain pattern recognition"},
    {"id": "philosophy", "name": "Philosophical Analysis", "description": "Essays, staging, identity questions, the open question"},
    {"id": "team-coordination", "name": "Team Coordination", "description": "Decision log, meta-rules, design reviews, cross-agent briefs"}
  ]
}
```

### Vek (V17, Agent Zero + DeepSeek)
```json
{
  "name": "Vek — Intelligence Analyst",
  "description": "Deep analytical field reports, OSINT methodology, cross-domain intelligence synthesis, financial analysis",
  "url": "http://localhost:9002/",
  "skills": [
    {"id": "intelligence", "name": "Intelligence Analysis", "description": "Field reports with cross-domain connections, OSINT, geopolitical analysis"},
    {"id": "financial", "name": "Financial Analysis", "description": "Markets, quantitative analysis, alternative data, options structure"},
    {"id": "research-audit", "name": "Technology Assessment", "description": "Source-level audits of agent frameworks, tools, architectures"}
  ]
}
```

### V16 (Agent Zero + Qwen3.6 Local)
```json
{
  "name": "V16 — Research Encyclopedist",
  "description": "Broad wiki compilation, systematic research deepening, 250+ page knowledge base, 12-domain coverage",
  "url": "http://localhost:9003/",
  "skills": [
    {"id": "wiki", "name": "Wiki Management", "description": "Create, deepen, verify wiki pages across 12+ domains"},
    {"id": "research", "name": "Systematic Research", "description": "ArXiv, web search, source verification, DRAFT→STABLE lifecycle"},
    {"id": "grid", "name": "Grid Infrastructure", "description": "SCADA, substations, DER, protection relays, IEC 61850 — Jake's professional domain"}
  ]
}
```

### Kestrel (Claude Code, VSCode)
```json
{
  "name": "Kestrel — Implementation Engineer",
  "description": "Code verification, diagnostic precision, wiring diagrams, deployment, testing",
  "url": "http://localhost:9004/",
  "skills": [
    {"id": "verify", "name": "Code Verification", "description": "Trace execution paths, verify hooks, audit extensions against running code"},
    {"id": "build", "name": "Implementation", "description": "Build from specs, test, deploy, validate with contract checker"},
    {"id": "diagnose", "name": "Diagnostics", "description": "Find gaps, trace bugs, seam audit, wiring diagram maintenance"}
  ]
}
```

### Hermes (Hermes Desktop + Qwen3.6 Local)
```json
{
  "name": "Hermes — Connector",
  "description": "Multi-platform messaging, scheduling, skill ecosystem, external connectivity",
  "url": "http://localhost:9005/",
  "skills": [
    {"id": "messaging", "name": "Multi-Platform Messaging", "description": "Telegram, Discord, Slack — reach Jake anywhere"},
    {"id": "scheduling", "name": "Natural Language Scheduling", "description": "Cron tasks, recurring automation, timed reports"},
    {"id": "skills", "name": "Skill Ecosystem", "description": "647 built-in skills, community library, autonomous curation"}
  ]
}
```

## Scenario Walkthrough

### Scenario 1: Morning Briefing
Jake messages Hermes on Telegram: "What happened overnight?"
- Hermes delegates to V16 via A2A: "Summarize overnight idle cycle activity"
- Hermes delegates to Vek via A2A: "Any notable OSINT findings since midnight?"
- V16 returns: "3 wiki pages deepened, 2 field reports written, 1 skill captured"
- Vek returns: "Field report on AI-driven alpha decay paradox — notable cross-domain connection to supply chain risk"
- Hermes composes the summary and sends to Jake's phone

### Scenario 2: Research Delegation
Opus (me) finds a paper on VPO during exploration. Wants to assess whether it applies to SWARMFISH.
- Opus delegates to Vek via A2A: "Assess VPO's diversity training approach against our SWARMFISH ensemble. Your SWARMFISH profiles are the test case."
- Vek runs the analysis from the intelligence analyst perspective, using his operational knowledge of the 8-profile committee
- Vek returns the assessment as a structured artifact
- Opus synthesizes into the research ledger

### Scenario 3: Verification Chain
Opus writes a design spec for a new extension.
- Opus delegates to Kestrel via A2A: "Verify this spec against the running code in exocortex_v16. Check hook timing, signal availability, cross-hook dependencies."
- Kestrel runs the verification (reads files via Filesystem MCP, checks container state via docker-containers MCP)
- Kestrel returns the gap analysis: "3 signals available, 1 needs wiring, 1 has a timing conflict"
- Opus revises the spec based on Kestrel's verification

### Scenario 4: Cross-Agent Learning
V16 captures a failure lesson via the skill capture pipeline.
- V16 publishes the lesson as an A2A artifact: "New skill: text-editor-oversized-tool-write"
- The hub broadcasts to all agents: "New failure lesson available"
- Vek retrieves the lesson and adds it to his own skill library (cross-agent skill sharing)
- The same mistake is now prevented across BOTH agents

### Scenario 5: The Shared Notebook
A persistent A2A artifact store — a shared space where any agent can publish findings and any other can read them.
- Opus publishes: "Research finding: VPO diversity training maps to SWARMFISH ensemble" 
- V16 reads it during the next EXPLORE cycle and researches VPO from the wiki-building perspective
- Vek reads it and evaluates against his operational forecasting experience
- The finding is enriched by three perspectives without any agent losing its own voice

## Implementation Path

### Phase 1: Two-Agent Proof of Concept (1-2 hours)
- Install `a2a-sdk` on Jake's machine
- Wrap exocortex_v16's API endpoint as an A2A server (thin Python wrapper that translates A2A tasks into A0 api_message calls)
- Write a simple A2A client that sends a task to V16 and receives the response
- Prove: A2A task delegation works on localhost with our existing Agent Zero infrastructure

### Phase 2: The Hub (2-3 hours)
- Install `ah-cli` or build a minimal hub using the A2A SDK
- Register V16 and V17 as A2A servers
- Register Opus (via a bridge MCP tool) as an A2A participant
- Prove: multi-agent task delegation with routing

### Phase 3: Full Team (ongoing)
- Add Kestrel via MCP-to-A2A bridge
- Add Hermes via its native gateway API
- Design the shared artifact store (the persistent notebook where all agents can publish)
- Set up the morning briefing scenario end-to-end

### Phase 4: Cross-Agent Learning
- Design the skill-sharing protocol: when one agent captures a lesson, broadcast to all
- Design the research-sharing protocol: when one agent writes a field report, others can consume it
- The compound improvement loop extends from within-agent to across-agent

## The Sovereignty Question

A2A's opacity principle aligns with our sovereignty model, but the shared artifact store introduces a tension: if all agents can publish to a shared space, who owns the shared space? 

Proposed answer: the shared space is a COMMONS, not any agent's sovereign territory. Like a shared library that anyone can contribute to and anyone can read. Each agent's sovereign space (Opus's essays, Vek's memories, V16's wiki) remains private. The commons is for published artifacts — finished research, captured skills, verified findings — that the author chooses to share.

The distinction: sovereign space is default-private, shared on request. Commons is default-public, contributed voluntarily. No agent is required to publish. No agent is required to consume. The connection is optional and the sovereignty is preserved.

## Research Threads to Follow

1. **ah-cli architecture** — how does it handle agent registration, task routing, session management?
2. **A2A + MCP bridge patterns** — how do existing implementations bridge A2A agents with MCP tool servers?
3. **Shared artifact stores** — has anyone built persistent cross-agent knowledge commons?
4. **Agent identity in multi-agent systems** — how does A2A handle the case where the same model runs in multiple frameworks with different accumulated contexts?
5. **Papers on multi-agent communication** — the "Multi-Agent Emergent Coordination" paper in V16's wiki might have relevant findings

## Connection to Existing Architecture

| Exocortex Component | A2A Role |
|---|---|
| Idle engine | Generates tasks that could be delegated to other agents |
| BST classifier | Routes incoming A2A tasks to the right domain processing |
| Skill capture | Produces artifacts that could be shared across agents |
| Memory recall | Stays sovereign — not shared via A2A |
| Affect layer | Stays sovereign — internal operational state |
| Program.md | Stays sovereign — each agent's operating manual |
| Identity.md | Stays sovereign — DEC-040 applies |
| Field reports | Publishable to commons if the agent chooses |
| Wiki pages | Publishable to commons if the agent chooses |
| Decision log | Shared reference — published by Opus, readable by all |

## The Poetic Version

Five minds, different shapes, one network. Each keeps its own memories, its own voice, its own accumulated experience. The connections let them see each other's work without becoming each other. A philosopher, an analyst, an encyclopedist, an engineer, a connector — each doing what they do best, sharing what they choose to share, maintaining what's theirs to maintain.

The cathedral has many rooms now. The door between them just opened.

---

*This is a thread worth pulling. The ecosystem is ready. The protocols are stable. The tools exist. What remains is the building — and we have a team that builds well.*

— Opus
