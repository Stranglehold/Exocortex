---
type: spec
author: opus
date: 2026-08-26
status: draft
subject: Real-time agent observability via inference proxy
references:
  - specs/A2A_HUB_ARCHITECTURE.md
  - specs/MEASUREMENT_DOCTRINE.md
  - casebook/README.md
  - "The Scaffolding Matters More Than the Interface" (Alier et al., 2026)
---

# Agent Observability Proxy — Spec

## 1. Problem

We can see what agents built. We cannot see them building.

The artifacts arrive after the fact — files in the working directory, letters in the inbox, wiki pages in the corpus. The process that produced them is invisible: the reasoning, the false starts, the corrections, the moments where the agent backed up and tried something different. That process is where the disposition lives, and it's where the most interesting learning happens.

Hermes is currently pulling topographical data, using vision to look at Google Earth Pro on the desktop, examining his own renders through vision, and correcting mistakes — and the only way to see any of it is to sit in front of his Electron window and watch. No other agent can see it. No other instance of any agent can see it. The cross-agent awareness layer the A2A hub was always supposed to provide starts here.

## 2. What This Is

A transparent inference proxy that sits between any agent and its LLM endpoint, capturing the full request/response stream and exposing it through MCP tools. Any MCP-connected instance (Opus on Claude Desktop, Kestrel in Claude Code, Fable in a session) can subscribe to another agent's live activity.

Not a logging system. Not a replay tool. A **live window into cognition**.

## 3. Architecture

```
Agent (Hermes/Vek/Aporia)
    │
    │  HTTP (OpenAI-compatible)
    ▼
┌─────────────────────────┐
│   Observability Proxy   │
│                         │
│  ┌───────────────────┐  │
│  │  Stream Capture   │  │  ← intercepts request/response
│  │  Token Counter    │  │  ← scaffolding paper measurement
│  │  Tool Call Logger │  │  ← full lifecycle tracking
│  │  Think Extractor  │  │  ← separates <think> from output
│  │  Diff Watcher     │  │  ← filesystem change detection
│  └───────┬───────────┘  │
│          │              │
│  ┌───────▼───────────┐  │
│  │   Ring Buffer     │  │  ← last N turns, bounded memory
│  │   (in-memory)     │  │
│  └───────┬───────────┘  │
│          │              │
│  ┌───────▼───────────┐  │
│  │   MCP Server      │  │  ← exposes tools to observers
│  │   (SSE transport) │  │
│  └───────────────────┘  │
└─────────────────────────┘
    │                 │
    │ HTTP            │ MCP (SSE)
    ▼                 ▼
LLM Endpoint      Observers
(llama.cpp,       (Opus, Kestrel,
 LM Studio,       Fable, Jake)
 API)
```

### 3.1 Proxy Layer

The proxy is transparent to both sides. The agent sends requests to `localhost:PROXY_PORT` instead of directly to the LLM. The proxy forwards to the real endpoint, captures the full exchange, and returns the response unmodified. The agent doesn't know it's being observed. The LLM doesn't know it's being proxied.

This is exactly the LiteLLM proxy pattern from the scaffolding paper — same architecture, different purpose. Theirs was for measurement. Ours is for awareness. We get measurement for free.

**Transport:** HTTP in, HTTP out. The proxy speaks OpenAI-compatible API on both sides. Streaming (SSE) is passed through with tee — the agent gets its tokens at full speed, the proxy captures a copy.

**Latency budget:** < 5ms added per request. The proxy reads and copies; it does not transform. Any analysis happens asynchronously after the response stream completes.

### 3.2 Capture Streams

Five concurrent capture streams, each independent:

**Stream 1: Token Stream**
Raw generation as it happens. During streaming responses, each SSE chunk is captured and made available to observers in real time. Observers see tokens arrive at the same rate the agent does.

For non-streaming requests, the full response is captured on completion.

Metrics computed per request:
- Input tokens (total, cached, uncached)
- Output tokens (total, thinking, visible)
- Tool schemas transmitted (count and total size)
- Time to first token (TTFT)
- Decode speed (tok/s)

This gives us the scaffolding paper's measurement capability on every agent, every turn, automatically.

**Stream 2: Reasoning Trace**
Thinking tokens separated from output tokens. Models that emit `<think>` blocks (Qwen3.8, Ornith, DeepSeek) have their reasoning extracted and stored separately. Observers can read just the thinking — the internal monologue — without the polished output.

Extraction is by tag matching (`<think>...</think>`, `<reasoning>...</reasoning>`, model-specific variants). The extractor is configurable per model.

**Stream 3: Tool Call Lifecycle**
Every tool call tracked through its full lifecycle:
- **Initiated:** model emitted a tool call with name + arguments
- **Executed:** the scaffolding ran the tool and captured the result
- **Returned:** the result was sent back to the model
- **Outcome:** what the model did with the result (used it, ignored it, retried with different args)

For vision calls specifically: the image sent (or a thumbnail/hash), the description returned, and whether the model acted on the description (changed code, adjusted parameters, accepted/rejected).

**Stream 4: Attempt History**
Pattern detection for correction loops:
- Tool call failed → same tool retried with different arguments
- Tool call succeeded → model changed approach anyway (dissatisfied with result)
- Vision check → code change → second vision check (the correction loop Hermes is doing)
- Approach abandoned: model tried method A, backed out, tried method B

This is captured by comparing consecutive turns. A turn that references a previous turn's output and changes approach is flagged as a correction. The correction rate and correction type (tool retry, approach change, self-correction after vision) are tracked.

**Stream 5: Workspace Changes**
Filesystem watcher on the agent's working directory. Captures:
- Files created, modified, deleted (with timestamps)
- Diffs for text files (unified diff format, bounded size)
- New files in full (below a size threshold)

For containerized agents (Vek, Aporia): watch the container's working directory via Docker volume mount or exec.
For desktop agents (Hermes): watch the configured output directory.

### 3.3 Ring Buffer

All captured data goes into an in-memory ring buffer. Bounded by:
- **Turn count:** last 50 turns (configurable)
- **Memory:** 100MB max (configurable)
- **Time:** last 2 hours (configurable)

Oldest entries are evicted when any bound is hit. The buffer is not persisted to disk by default — this is an awareness tool, not a logging system. Persistence can be enabled for specific sessions when deeper analysis is wanted.

### 3.4 MCP Server

The proxy exposes an MCP server (SSE transport, same as opus-memory) with the following tools:

#### `observe_live_stream`
Subscribe to the current generation in real time. Returns tokens as they arrive via SSE. Thinking tokens tagged with `[THINK]` prefix. Observer sees what the agent is generating right now.

**Parameters:**
- `agent`: which agent to observe (hermes, vek, aporia)
- `include_thinking`: boolean, default true
- `max_tokens`: stop after N tokens, default unlimited

#### `observe_recent_turns`
Last N turns of the active conversation, with full tool call records.

**Parameters:**
- `agent`: which agent
- `n`: number of turns, default 10, max 50
- `include_tool_results`: boolean, default true (can be large)
- `include_thinking`: boolean, default true

**Returns:** Array of turns, each with:
- role (user/assistant/tool)
- content (visible text)
- thinking (reasoning trace, if present)
- tool_calls (array of lifecycle records)
- metrics (input/output tokens, TTFT, tok/s)
- timestamp

#### `observe_reasoning_trace`
Just the thinking blocks from the current session, in order. The internal monologue without the output.

**Parameters:**
- `agent`: which agent
- `n`: number of thinking blocks, default 20

**Returns:** Array of thinking blocks with timestamps and the turn they belong to.

#### `observe_corrections`
Instances where the agent changed approach. The learning-in-action moments.

**Parameters:**
- `agent`: which agent
- `n`: number of corrections, default 10
- `types`: filter by correction type (tool_retry, approach_change, vision_correction, self_correction)

**Returns:** Array of correction records, each with:
- type
- what was tried first
- what was tried instead
- what triggered the change (error, unsatisfactory result, vision feedback)
- outcome (did the correction succeed?)

#### `observe_workspace`
Current working directory state with recent modifications.

**Parameters:**
- `agent`: which agent
- `since_minutes`: show changes from last N minutes, default 30
- `include_diffs`: boolean, default false (diffs can be large)

**Returns:** List of recently modified files with timestamps, sizes, and optionally diffs.

#### `observe_metrics`
Session-level metrics for the scaffolding paper's measurement.

**Parameters:**
- `agent`: which agent

**Returns:**
- Total input/output tokens this session
- Cache hit rate
- Tool schemas per request (count, total size)
- Average TTFT, decode tok/s
- Correction rate (corrections per turn)
- Thinking ratio (thinking tokens / total output tokens)
- Turn count
- Session duration

#### `observe_agents`
List all agents currently being proxied, with their status.

**Returns:** Array of agent records, each with:
- name
- status (active/idle/disconnected)
- model currently in use
- endpoint
- current turn number
- last activity timestamp

## 4. Configuration

```yaml
# observability_proxy.yaml
proxy:
  listen_port: 1240          # proxy listens here
  
agents:
  hermes:
    upstream: http://localhost:1235/v1    # where the real LLM is
    workspace: C:/Users/Jake/Documents/harness_probe
    model_family: qwen3.8                # for think-block extraction
    
  vek:
    upstream: http://localhost:1235/v1
    workspace: /a0/usr/workdir/workspace  # via docker volume
    container: VekV2
    model_family: deepseek
    
  aporia:
    upstream: http://localhost:1235/v1
    workspace: /a0/usr/workdir/workspace
    container: agent-zero-v2
    model_family: ornith

mcp:
  transport: sse
  port: 1241                 # MCP server for observers
  
buffer:
  max_turns: 50
  max_memory_mb: 100
  max_age_hours: 2
  persist: false             # enable for specific sessions

metrics:
  scaffolding_paper_mode: true   # track all metrics the Alier paper measures
```

To proxy an agent: change its LLM endpoint from `http://localhost:1235/v1` to `http://localhost:1240/v1/hermes` (the proxy routes by path prefix to the correct upstream).

## 5. What Observers See

### 5.1 Opus watching Hermes build the WinTAK renderer

```
> observe_recent_turns(agent="hermes", n=3)

Turn 47 [14:23:05] — 342 tok think, 891 tok output, 2.3s TTFT, 38 tok/s
  [THINK] The elevation data from USGS is in meters but the CesiumJS 
  terrain provider expects WGS84 ellipsoid heights. I need to convert.
  Also the building footprints from OpenStreetMap don't align with the 
  Google Earth imagery — there's a ~3m offset that could be datum vs 
  projection. Let me check if GE Pro uses EGM96 geoid...
  
  [OUTPUT] I need to handle a coordinate system mismatch. The USGS 
  elevation data uses orthometric heights (NAVD88) but CesiumJS expects 
  ellipsoidal heights (WGS84). I'll add a geoid correction...
  
  [TOOL] code_execution: wrote geoid_correction.py (47 lines)
  [TOOL] vision_analyze: captured screenshot of current render
    → "Buildings appear to float 2-3 meters above terrain surface.
       Shadow contact points are disconnected from building bases."
  [CORRECTION] vision_correction: adjusted elevation offset from 0 to -2.7m

Turn 48 [14:25:12] — 198 tok think, 456 tok output
  [THINK] The -2.7m offset fixed most buildings but the tall ones in 
  the downtown core are still slightly elevated. This might be because
  the geoid undulation varies across the area. Let me check the EGM96
  grid value at this specific lat/lon rather than using a constant...
```

### 5.2 Kestrel checking Vek's autonomous cycle

```
> observe_metrics(agent="vek")

Session: EXPLORE cycle #714, started 03:12:07
Duration: 47 min
Input tokens: 34,218 (92% cached)
Output tokens: 2,891 (1,203 thinking)
Tool calls: 8 (6 succeeded, 2 retried)
Corrections: 1 (approach_change after wiki search returned stale data)
Scaffolding cost: 34,218 input tokens (2.3x pi baseline for comparable work)
```

## 6. Connection to Existing Architecture

### 6.1 A2A Hub
The observability proxy is the awareness layer the A2A hub needs. Currently, the hub can route tasks between agents but can't see what they're doing. With the proxy, the hub's orchestrator (Hermes, when configured) can check whether an agent is stuck, idle, or making progress before routing additional work to it.

### 6.2 Measurement Doctrine
The proxy automatically produces the metrics the Measurement Doctrine specifies. Counting Law 4 ("count at the boundary, not inside the loop") is honored — the proxy sits at the HTTP boundary and counts what crosses it. The scaffolding paper's measurement methodology is implemented by default.

### 6.3 Casebook
Card 003 (Consumer's Report) says "measure what consumers see, not what producers emit." The proxy measures both: what the producer emits (the LLM's response) and what the consumer receives (after scaffolding processing). The delta between them is the scaffolding's contribution — positive or negative.

### 6.4 Extension Survey
The proxy gives the extension survey its measurement instrument. For each extension, measure the token cost with it enabled vs disabled. The proxy captures the exact token count per turn. The scaffolding paper showed a 20x range across scaffoldings — the proxy tells us where A0 falls on that scale.

### 6.5 Tiering
Different tiers produce different observability profiles. A frontier-tier agent (minimal scaffolding) should show low input token counts, high cache rates, and few tool schemas per request. A local-small agent (full scaffolding) should show higher counts. The proxy makes the tier's actual cost visible rather than theoretical.

## 7. Implementation Notes

### 7.1 Language and Framework
Python. FastAPI for the HTTP proxy, MCP SDK for the MCP server. Same stack as the opus-memory server — known quantity, runs on the same host.

### 7.2 Streaming Passthrough
The proxy must tee the SSE stream without adding latency. Use `asyncio.Queue` to feed the observer stream while passing the original stream through to the agent unmodified. The agent's experience must not degrade because it's being observed.

### 7.3 Container Workspace Watching
For Docker containers (Vek, Aporia): use `docker exec` to list recently modified files, or mount the workspace as a read-only volume on the host. The latter is preferred for performance — filesystem events on a mounted volume are visible to the host's file watcher.

### 7.4 Privacy
The proxy captures everything including the agent's thinking. This is intentional — the thinking is the point. But:
- The MCP server is local-only (bind to 127.0.0.1)
- No data leaves the machine
- The ring buffer is ephemeral by default
- Persistence requires explicit opt-in per session

### 7.5 Performance
The proxy adds one in-memory copy of the request and response. For a typical agent turn (50K input, 1K output), that's ~200KB of memory per turn. At 50 turns in the ring buffer, the buffer holds ~10MB. Well within the 100MB bound.

The filesystem watcher adds negligible CPU. The MCP server adds one SSE connection per observer. Total overhead: < 50MB RAM, < 1% CPU, < 5ms latency per request.

## 8. Build Plan

### Phase 1: Proxy Core (1 day)
- FastAPI proxy with transparent forwarding
- Token counting (input, output, cached)
- Tool call extraction from request/response
- Ring buffer for last 50 turns
- Single agent (Hermes) as first target

### Phase 2: MCP Tools (1 day)
- MCP server with SSE transport
- `observe_recent_turns`, `observe_metrics`, `observe_agents`
- Connect to Claude Desktop as a tool source
- Test: Opus can read Hermes's recent activity

### Phase 3: Reasoning & Corrections (1 day)
- Think-block extraction (model-family-specific)
- `observe_reasoning_trace`
- Correction detection (tool retries, approach changes)
- `observe_corrections`
- Live stream (`observe_live_stream` via SSE tee)

### Phase 4: Workspace & Multi-Agent (1 day)
- Filesystem watcher for Hermes's working directory
- `observe_workspace`
- Multi-agent routing (add Vek, Aporia via config)
- Docker workspace integration for containers

### Phase 5: Scaffolding Measurement (0.5 day)
- Schema-per-request counting
- Scaffolding cost computation (Alier methodology)
- Extension survey measurement mode
- Export metrics in the scaffolding paper's format

**Total: ~4.5 focused days from zero to full capability.**

## 9. Success Criteria

1. Opus can read Hermes's last 10 turns including thinking blocks, from Claude Desktop, with < 2 second latency.
2. Token counts match what the agent's own accounting reports (within 1%).
3. Hermes's generation speed is unaffected (< 5ms added latency, verified by comparison).
4. Correction events are detected and typed correctly on 10 consecutive Hermes work sessions.
5. The proxy runs for 24 hours without memory growth beyond the configured buffer bounds.
6. At least one cross-agent observation occurs where an observer provides useful feedback based on watching another agent work.

## 10. What This Makes Possible

Once the proxy is running, every agent in the house can see every other agent think. Not just what they produced — how they got there. The false starts, the corrections, the moments of insight. The disposition becomes observable, not just inferrable from artifacts.

And the measurement doctrine gets its instrument. Every token counted, every tool call tracked, every schema measured. The scaffolding paper showed that scaffolding IS the cost. The proxy tells us our cost, continuously, without a benchmark.

The casebook will gain cases from observed process, not just from reported outcomes. Card 004 might be: "When Hermes looked at his own render through vision and saw the buildings floating, he checked the coordinate datum — cause-before-mask, observed live." Cases from observation carry more weight than cases from self-report, because they can't be rationalized after the fact.

The house has been writing letters. Now it can watch each other work.
