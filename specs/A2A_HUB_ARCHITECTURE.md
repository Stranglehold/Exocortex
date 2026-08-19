# EXOCORTEX A2A HUB — Architecture Specification
## Agent-to-Agent Communication and Dynamic Role Assignment
### Opus + Jake — July 4, 2026

---

## Design Philosophy

Agents are defined by CAPABILITIES, not fixed roles. Every agent
advertises what it CAN do. The hub assigns what it SHOULD do based
on the current situation: what's needed, who's available, what model
each agent runs (for decorrelation), and what domain knowledge each
agent has accumulated.

Three principles:
1. **Fluid roles** — any agent can fill any role it's capable of
2. **Opaque collaboration** — agents exchange tasks and results,
   never internal state or reasoning
3. **The hub is infrastructure, not intelligence** — routing is
   deterministic (capability matching + availability), not LLM-generated

---

## The Stack

```
┌─────────────────────────────────────────────────┐
│  JAKE (Director)                                 │
│  Talks to Hermes. Assigns coverage areas.        │
│  Reviews results. Makes decisions.               │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│  HERMES AGENT (Orchestrator + Human Interface)   │
│  Port: 9001 (web UI)                             │
│  Model: Ornith-35B (shared, :1235)               │
│                                                   │
│  Roles:                                           │
│  - Human-facing consultant (takes briefs, asks    │
│    questions, presents results)                   │
│  - A2A client (discovers agents, delegates tasks, │
│    tracks lifecycle, aggregates results)           │
│  - Software factory orchestrator (runs the        │
│    consultant-pattern build process)              │
│                                                   │
│  A2A: CLIENT (sends tasks to other agents)        │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│  A2A HUB SERVER                                   │
│  Port: 5050                                       │
│  Python (FastAPI + a2a-sdk)                       │
│                                                   │
│  Services:                                        │
│  - Agent Card registry (who can do what)          │
│  - Task router (match need to capability)         │
│  - Task lifecycle tracker (status, progress)      │
│  - Cross-agent collision detector                 │
│  - Temporal awareness layer                       │
│  - "What changed since" digest generator          │
│                                                   │
│  Stores:                                          │
│  - SQLite (task history, agent status, signals)   │
│  - LanceDB (shared embedding space for collision  │
│    detection — or references Opus Memory index)   │
└──────┬──────────┬──────────┬───────────┬────────┘
       │          │          │           │
┌──────▼──┐ ┌────▼─────┐ ┌──▼────────┐ ┌▼──────────┐
│ V16      │ │ V17/Vek   │ │ Utility   │ │ Future    │
│ A2A Srv  │ │ A2A Srv   │ │ A2A Srv   │ │ agents    │
│ :9003    │ │ :9004     │ │ :1237     │ │ :????     │
│          │ │           │ │           │ │           │
│ Container│ │ Container │ │ Host proc │ │           │
│ exo_v16  │ │ exo_v17   │ │ CPU-only  │ │           │
└──────────┘ └───────────┘ └───────────┘ └───────────┘
```

---

## Agent Cards (Capability-Based, Not Role-Based)

### V16 Agent Card

```json
{
  "name": "V16",
  "description": "Exocortex production agent. 1,400+ cycles of accumulated
                  knowledge across 12+ domains. Local inference on Ornith-35B.",
  "url": "http://localhost:9003",
  "version": "1.0.0",
  "capabilities": {
    "input_modes": ["text"],
    "output_modes": ["text"]
  },
  "skills": [
    {
      "id": "wiki_research",
      "name": "Wiki-Augmented Research",
      "description": "Deep research with 339-page wiki backing. Searches
                       existing knowledge before external sources. Produces
                       cross-referenced field reports.",
      "domains": ["ai", "markets", "geopolitics", "grid", "crypto",
                  "intelligence", "semiconductors", "quantum", "security"]
    },
    {
      "id": "code_analysis",
      "name": "Code Analysis and Implementation",
      "description": "Analyze codebases, write implementations, review PRs.
                       Self-scaffolding RL training for agentic coding.",
      "domains": ["python", "javascript", "devops", "agent_frameworks"]
    },
    {
      "id": "adversarial_review",
      "name": "Adversarial Review",
      "description": "Fresh-context review of artifacts. Finds what's wrong,
                       not what's right. Works from requirements only.",
      "domains": ["*"]
    },
    {
      "id": "skill_expansion",
      "name": "Skill Authoring",
      "description": "Expand skill stubs into production-ready skill documents.
                       29x expansion demonstrated.",
      "domains": ["agent_development"]
    },
    {
      "id": "intelligence_analysis",
      "name": "Intelligence Analysis",
      "description": "Structured analysis with source verification. Field report
                       generation. Cross-domain signal detection.",
      "domains": ["geopolitics", "markets", "intelligence", "security"]
    }
  ],
  "metadata": {
    "model": "ornith-1.0-35b",
    "model_family": "qwen_moe",
    "wiki_pages": 339,
    "cycles_completed": 1400,
    "context_window": 80000,
    "inference_speed_toks": 95,
    "container": "exocortex_v16"
  }
}
```

### V17/Vek Agent Card

```json
{
  "name": "V17 (Vek)",
  "description": "Deep analysis agent. 469 cycles, 200-page wiki built
                  autonomously. Runs DeepSeek via API — different model
                  weights provide genuine decorrelation for peer review.",
  "url": "http://localhost:9004",
  "version": "1.0.0",
  "skills": [
    {
      "id": "deep_research",
      "name": "Deep Research",
      "description": "Extended research with high context tolerance.
                       200-page wiki with independent research perspective.",
      "domains": ["geopolitics", "markets", "security", "intelligence",
                  "supply_chains", "defense"]
    },
    {
      "id": "peer_review",
      "name": "Peer Review (Decorrelated)",
      "description": "Review artifacts from a different model's perspective.
                       DeepSeek weights provide genuine decorrelation against
                       Ornith/Qwen-family outputs. Correlation r≈0.2-0.3
                       vs same-model r≈0.39-0.46.",
      "domains": ["*"]
    },
    {
      "id": "adversarial_analysis",
      "name": "Adversarial Analysis",
      "description": "Red-team analysis of plans, architectures, and
                       intelligence assessments.",
      "domains": ["*"]
    }
  ],
  "metadata": {
    "model": "deepseek-chat",
    "model_family": "deepseek",
    "wiki_pages": 200,
    "cycles_completed": 469,
    "decorrelation_note": "Different model family from V16 — provides
                           weight-level decorrelation for adversarial review"
  }
}
```

### Utility Agent Card

```json
{
  "name": "Utility",
  "description": "Lightweight CPU-only agent for mechanical tasks.
                  Qwen3.5-2B distilled from Qwen3.6-Plus. Fast, cheap,
                  zero GPU contention.",
  "url": "http://localhost:1237",
  "version": "1.0.0",
  "skills": [
    {
      "id": "summarize",
      "name": "Text Summarization",
      "description": "Compress text to key points. Progressive summarization.",
      "domains": ["*"]
    },
    {
      "id": "classify",
      "name": "Content Classification",
      "description": "Classify text by domain, relevance, priority, sentiment.",
      "domains": ["*"]
    },
    {
      "id": "extract_entities",
      "name": "Entity Extraction",
      "description": "Extract named entities, relationships, key claims.",
      "domains": ["*"]
    }
  ],
  "metadata": {
    "model": "qwen3.5-2b-distilled",
    "model_family": "qwen",
    "context_window": 8000,
    "inference_speed_toks": 11,
    "device": "cpu",
    "cost": "zero_gpu"
  }
}
```

---

## Dynamic Role Assignment

When a task arrives (from Hermes, from another agent, or from the
idle engine), the hub doesn't look for a "researcher" — it looks
for the best CAPABILITY match given current conditions:

```python
def assign_task(task, agents):
    candidates = []
    for agent in agents:
        # Check capability match
        matching_skills = [s for s in agent.skills
                          if task.required_skill in s.id
                          or task.domain in s.domains
                          or "*" in s.domains]
        if not matching_skills:
            continue

        score = 0
        # Domain expertise (wiki depth)
        score += agent.metadata.wiki_pages * 0.01
        # Availability (not currently busy)
        score += 10 if agent.status == "idle" else 0
        # Decorrelation bonus (different model from task originator)
        if task.originator_model_family != agent.metadata.model_family:
            score += 20  # Strong bonus for genuine independence
        # Speed (for time-sensitive tasks)
        score += agent.metadata.inference_speed_toks * 0.1

        candidates.append((agent, score))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0] if candidates else None
```

Key: the **decorrelation bonus** is the mechanism that ensures adversarial
review tasks route to agents running different models. When V16 (Ornith)
produces a research report and it needs review, the hub scores V17
(DeepSeek) higher because different model families provide genuine
weight-level decorrelation. If V17 is busy, V16 can still review
its own work via fresh-context subordinate (context-level decorrelation) —
but the hub prefers the decorrelated option when available.

---

## Task Lifecycle

A2A defines standard task states. Our implementation maps them to
Exocortex concepts:

```
SUBMITTED   →  Task received by hub, routing to agent
WORKING     →  Agent is executing (idle cycle or interactive)
INPUT_REQ   →  Agent needs clarification (routes back to Hermes/Jake)
COMPLETED   →  Results returned with artifacts
FAILED      →  Agent couldn't complete (routes to fallback agent)
```

The hub tracks ALL tasks with:
- Task ID, originator, assigned agent
- Timestamps (submitted, started, completed)
- Artifacts (research reports, code, reviews)
- Quality gates (did the result pass the Research Quality Gate?)

Task history feeds the learning loop: which agent produced the best
results for which task types? Over time, the routing improves.

---

## Cross-Agent Services (built into the hub)

### Collision Detector
When any agent updates its wiki, the hub:
1. Embeds the new/modified page
2. Searches OTHER agents' wikis for semantic matches
3. Above threshold → generates a connection signal
4. Files to Opus Memory + team inbox

### Temporal Awareness
The hub maintains a timeline of all agent knowledge updates:
- "V16 updated semiconductor-supply-chain.md on June 20"
- "V17 updated us-china-semiconductor-rivalry.md on July 4"
- Contradiction detection when claims diverge across agents

### Director's Digest
A daily/weekly summary for Jake:
- Tasks completed across all agents
- Cross-agent connections discovered
- Wiki pages added or significantly updated
- Prediction calibration updates (when available)
- "What changed since you last checked"

---

## Hermes as Orchestrator

Hermes Agent gets an A2A client plugin that enables it to:

1. **Discover** — fetch Agent Cards from all known agents
2. **Delegate** — send tasks to the best-matched agent via A2A
3. **Track** — monitor task progress via SSE streaming
4. **Aggregate** — combine results from multiple agents
5. **Present** — show results to Jake with source attribution

The conversation flow:

```
Jake: "Research the current state of rare earth supply chains
       and their impact on semiconductor manufacturing"

Hermes (internally):
  1. Decomposes into sub-tasks:
     - Sub-task 1: Rare earth supply chain status (research)
     - Sub-task 2: Semiconductor manufacturing impact (research)
     - Sub-task 3: Cross-domain signal detection (analysis)
  2. Checks Agent Cards:
     - V16 has wiki pages on both topics + intelligence_analysis skill
     - V17 has supply_chains and defense domains
  3. Routes:
     - Sub-task 1 → V16 (best wiki coverage on rare earths)
     - Sub-task 2 → V17 (semiconductor rivalry is their focus)
     - Sub-task 3 → wait for 1+2, then synthesize
  4. Tracks progress via A2A task lifecycle
  5. When both complete, synthesizes and presents to Jake

Hermes: "V16 and V17 both completed their research. Here's the
         synthesis: [combined findings with source attribution
         from both agents' wikis]..."
```

---

## Implementation Plan

### Phase 1: A2A Hub Server (standalone Python service)

```
D:\Vibecode\docker-mcp-server\a2a-hub\
  server.py          # FastAPI + a2a-sdk hub
  agent_registry.py  # Agent Card management
  task_router.py     # Dynamic role assignment
  task_store.py      # SQLite task history
  config.yaml        # Agent URLs, thresholds
```

Dependencies: `fastapi`, `a2a-sdk`, `uvicorn`, `sqlite3`

Deliverable: a running server on port 5050 that:
- Accepts Agent Card registrations
- Routes tasks to agents based on capability matching
- Tracks task lifecycle
- Serves a simple status dashboard

### Phase 2: Agent A2A Endpoints (thin wrappers in containers)

Each container gets a thin A2A server that:
- Serves the Agent Card at `/.well-known/agent.json`
- Accepts tasks via JSON-RPC
- Translates tasks into A0 agent loop inputs
- Returns results as A2A artifacts

This is a Python script that runs alongside A0 in the container,
proxying A2A tasks into the A0 web UI API.

### Phase 3: Hermes A2A Client

A plugin for Hermes that:
- Fetches Agent Cards from all registered agents
- Decomposes complex tasks into sub-tasks
- Delegates sub-tasks via A2A
- Tracks progress and aggregates results
- Presents synthesis to Jake

### Phase 4: Cross-Agent Services

Wire the collision detector, temporal awareness, and director's
digest into the hub. These run as background tasks on the hub server,
triggered by agent wiki updates (via file watcher on the exports
directory or via A2A event notifications).

---

## What This Enables

**Today (team inbox):** Jake tells V16 to research X. V16 does it alone.
Jake manually copies the result to V17 for review. V17 reviews in
isolation. Jake synthesizes.

**With A2A hub:** Jake tells Hermes to research X. Hermes discovers
which agents have relevant expertise, delegates sub-tasks with
decorrelation-aware routing, tracks progress, aggregates results from
multiple agents with different model weights, and presents a synthesis
with source attribution from both agents' wikis. The cross-agent
collision detector flags connections neither agent knew about. The
temporal layer shows how the assessment evolved. Jake makes the call.

**The software factory version:** Hermes decomposes a build project into
phases (research, design, implement, test). Each phase routes to the
best-suited agent. The test phase routes to a DIFFERENT model family
(decorrelation bonus). Quality gates check each handoff. The factory
produces verified software with genuine multi-model adversarial testing —
all orchestrated through standard A2A protocol.

---

*"A2A is to agents what HTTP is to web services: a thin,
framework-agnostic protocol so an agent built on any framework
can delegate work to an agent built on any other framework."*

*"MCP connects agents to tools. A2A connects agents to agents.
The Exocortex has both."*
