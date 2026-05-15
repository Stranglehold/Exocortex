# Architecture Diagram Skill — Adaptation Brief

**Purpose:** Briefing document for the agent to use when running `extract-and-adapt` on the
Cocoon-AI architecture-diagram-generator. Defines the target output, component palette,
key patterns to preserve, and adaptation decisions already made.

**Source:** https://github.com/Cocoon-AI/architecture-diagram-generator  
**Target output:** `/a0/usr/skills/architecture-diagram/SKILL.md`  
**Output format:** Exocortex skill, following design-buildplan conventions  
**Reference format:** `/a0/usr/skills/extract-and-adapt/SKILL.md`

---

## What the Source Does

The Cocoon skill teaches an agent a complete SVG design system, then the agent generates
standalone HTML/SVG architecture diagrams from plain-text descriptions. Output is a single
self-contained HTML file — embedded CSS, inline SVG, no JavaScript, no build tools.

The core insight: you don't need a diagramming library. You need a set of rules the agent
knows well enough to emit correct SVG markup directly. The SKILL.md is those rules.

---

## Adaptation Decisions (Pre-Resolved)

### 1. Output delivery: emit_artifact, not file save

The Cocoon version saves a `.html` file the user downloads. Exocortex has `emit_artifact`,
which renders HTML panels directly in the Agent Zero chat UI. The adapted skill should
emit the diagram as an artifact, not write it to disk.

**Pattern to use:**
```json
{
  "tool_name": "emit_artifact",
  "tool_args": {
    "html": "[full HTML content]",
    "title": "[diagram title]"
  }
}
```

The full HTML can still be written to `/a0/usr/workdir/diagrams/{name}.html` as a
persistent copy — but the primary delivery is `emit_artifact` so the diagram appears
in the chat immediately.

### 2. Scope: general architecture diagrams, not Exocortex-only

The skill should work for **any project** the agent is analyzing, not just Exocortex.
Use cases:
- Diagramming an external GitHub repo after analyzing its structure
- Mapping a system described by the user in plain text
- Visualizing a deployment the user describes conversationally
- Auto-generating an architecture diagram from code analysis

The Exocortex-specific component palette (below) is **one optional palette** the agent
can use when the subject is Exocortex. For other projects, it should use the general
palette from the source (frontend/backend/database/cloud/security/message-bus).

### 3. Font dependency: keep Google Fonts JetBrains Mono

The Google Fonts call (`fonts.googleapis.com`) is the one acceptable external dependency.
It loads in-browser when the artifact is rendered. Not a security concern — it is not
executed code, just a stylesheet. Keep it.

### 4. SVG masking technique: preserve exactly

The z-order rule is a real SVG gotcha that must be documented verbatim:
- Draw background grid first
- Draw connection arrows second
- Draw component boxes third (each component = opaque backing rect + colored styled rect on top)
- This ensures arrows don't bleed through semi-transparent component fills

This is non-obvious and must be in the skill's critical rules section.

### 5. Iteration pattern: preserve

The agent retains diagram state within the conversation. User says "add a Redis cache",
agent regenerates the full HTML and re-emits. No versioning needed. Document this pattern
explicitly — users should know they can iterate conversationally.

---

## Component Palettes

### General palette (for non-Exocortex diagrams — from source)

| Type | Fill | Stroke | Use for |
|------|------|--------|---------|
| Frontend | `rgba(8, 51, 68, 0.4)` | `#22d3ee` | Client apps, UIs, browsers |
| Backend | `rgba(6, 78, 59, 0.4)` | `#34d399` | APIs, servers, application logic |
| Database | `rgba(76, 29, 149, 0.4)` | `#a78bfa` | Databases, storage, data layers |
| Cloud/Infra | `rgba(120, 53, 15, 0.3)` | `#fbbf24` | Cloud services, infrastructure |
| Security | `rgba(136, 19, 55, 0.4)` | `#fb7185` | Auth, security groups, encryption |
| Message Bus | `rgba(251, 146, 60, 0.3)` | `#fb923c` | Kafka, queues, event buses |
| External | `rgba(30, 41, 59, 0.5)` | `#94a3b8` | External systems, 3rd-party |

### Exocortex palette (when diagramming Exocortex itself)

| Type | Fill | Stroke | Use for |
|------|------|--------|---------|
| Extension | `rgba(8, 51, 68, 0.4)` | `#22d3ee` | BST, Supervisor, Tool Registry, extensions |
| Service | `rgba(6, 78, 59, 0.4)` | `#34d399` | OSS, SWARMFISH, Sleep Consolidation |
| Memory | `rgba(76, 29, 149, 0.4)` | `#a78bfa` | FAISS, episodic, procedural, ontology |
| Agent | `rgba(120, 53, 15, 0.3)` | `#fbbf24` | Agent Zero, subordinates, browser agent |
| Infrastructure | `rgba(30, 41, 59, 0.5)` | `#94a3b8` | Docker, LM Studio, Postgres, Redis |
| Security gate | `rgba(136, 19, 55, 0.4)` | `#fb7185` | Action Boundary, Irreversibility Gate, EI |
| Hook point | `rgba(251, 146, 60, 0.3)` | `#fb923c` | before_main_llm_call, monologue_end, etc. |

---

## Design System Constants (preserve from source)

```
Background: #020617 (slate-950)
Grid pattern: 40px, stroke #1e293b, weight 0.5px
Component rx: 6px corner radius
Stroke width: 1.5px
Font: JetBrains Mono via Google Fonts
Font sizes: 12px labels (600 weight), 9px sublabels, 8px annotations
Arrow marker: polygon, fill #64748b
Dashed security boundary: stroke-dasharray="4,4"
Dashed region boundary: stroke-dasharray="8,4"
Min vertical gap between components: 40px
Standard component height: 60px (services), 80-120px (larger groups)
```

---

## Skill Trigger Patterns

The skill should activate on:
- "draw an architecture diagram of..."
- "diagram this system"
- "visualize the architecture"
- "create a diagram showing..."
- "map out how X connects to Y"
- "show me the architecture of this repo/project/codebase"
- "generate an architecture diagram"

---

## Output Structure

The generated HTML should always include:

1. **Header** — diagram title with pulsing dot indicator
2. **SVG diagram** — inside a rounded border card, viewBox minimum 1000x680 (expand as needed)
3. **Legend** — always included, outside all boundary boxes, showing color → component type mapping
4. **Summary cards** (optional, 2-3) — key facts about the architecture below the diagram

---

## What the Source Gets Right That Must Be Preserved

1. The masking trick (opaque backing rect + styled rect layered on top)
2. Arrow-first draw order in SVG
3. Legend placement outside all boundaries
4. Single-file portability
5. Iterative conversational workflow
6. Teaching approach: rules the agent internalized, not a library

## What to Adapt

1. File save → `emit_artifact` as primary delivery (file copy optional)
2. Generic palette → two palettes (general + Exocortex-specific)
3. Claude-only framing → Agent Zero tool surface (emit_artifact, text_editor, code_execution_tool)
4. No mention of `call_subordinate` in source → add delegation pattern for complex multi-zone diagrams

## What to Drop

- Claude.ai-specific skill packaging (.zip, SKILL.md as Claude skill)
- Hardcoded example outputs (the source's SKILL.md has inline HTML examples — replace with tool-surface examples)
- AWS-specific component names (keep as examples, not as primary vocabulary)
