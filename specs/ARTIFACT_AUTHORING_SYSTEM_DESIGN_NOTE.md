# Artifact Authoring System — Design Note
## "The model decides what to say. The system decides how it looks."

**Status:** Design note → spec. Ready for Kestrel build.
**Motivated by:** Qwopus3.5-27B-v3 cannot reliably produce quality HTML/CSS/JS artifacts from natural language prompts. Output truncation at ~25 lines, limited aesthetic reasoning under token pressure, and cognitive load of simultaneous design + implementation = consistently poor results.
**Principle:** Same as BST enrichment philosophy — separate what the model is good at (content reasoning, data organization) from what the model is bad at (generating pixel-perfect CSS, managing 300-line HTML files, making aesthetic decisions under token constraints). Make the mechanical parts deterministic. Let the model focus on what it can actually do.

---

## 1. The Problem

When asked to "make a nice dashboard," the agent must simultaneously:
1. Choose an aesthetic direction (colors, typography, layout)
2. Write correct HTML structure
3. Write CSS that implements the aesthetic
4. Write JavaScript for interactivity and animation
5. Load external libraries via CDN
6. Populate with content/data
7. Stay under the 16384-token output ceiling
8. Manage write_file calls if the artifact exceeds ~25 lines

Tasks 1-5 are identical for every dashboard ever created. Task 6 is the only one that changes per request. Tasks 7-8 are transport-layer constraints. The model is doing 8 things when it should be doing 1.

The fix: pre-build tasks 1-5 as templates. Give the model a tool that accepts task 6 as structured input. Handle tasks 7-8 in the tool's implementation. The model's cognitive budget goes entirely to "what content should this artifact show?" — the only question that requires reasoning.

---

## 2. Architecture

```
Operator says: "Show me a dashboard of the current stack status"
  ↓
Agent reasons about content:
  - What template? → "dashboard"
  - What theme? → "indigo" (or auto from BST/personality)
  - What data? → [{ name: "BST", status: "healthy", metric: "v3.3" }, ...]
  ↓
Agent calls: artifact_create tool with structured args
  ↓
Tool implementation:
  1. Reads template from /a0/usr/artifact_templates/dashboard.html
  2. Reads theme from /a0/usr/artifact_templates/themes/indigo.json
  3. Injects CSS variables from theme
  4. Injects data into template's marked injection points
  5. Writes assembled HTML to /a0/work/artifacts/artifact_[timestamp].html
  6. Returns file path for agent to present
  ↓
Artifact renders in browser panel — premium quality, zero model CSS authoring
```

### Components

**Template Library** (`/a0/usr/artifact_templates/`)
- Pre-built HTML files with CDN libraries, CSS, JavaScript, animations
- Each template is a complete, working, premium-quality artifact
- Placeholder markers (`{{TITLE}}`, `{{ITEMS}}`, `{{ACCENT_COLOR}}`) for data injection
- Templates are authored once by a capable model (Opus/Claude) or human designer
- The local model never modifies template code — only fills data slots

**Theme System** (`/a0/usr/artifact_templates/themes/`)
- JSON files defining CSS variable sets (colors, fonts, spacing)
- Templates reference CSS variables, themes define the values
- Switching themes changes the entire look without touching template code
- Ships with 4-6 themes covering the most useful aesthetics

**Artifact Creation Tool** (`/a0/usr/plugins/artifact_tool/`)
- Agent Zero tool callable by the model
- Accepts: template name, theme name (optional), structured data object
- Validates data against template's expected schema
- Performs injection, writes file, returns path
- Handles all file I/O — model never calls write_file for artifacts

**Template Manifest** (`/a0/usr/artifact_templates/manifest.json`)
- Describes each template: name, description, expected data schema, preview thumbnail
- The model reads the manifest to select the right template
- BST skill surfacing can recommend templates based on domain

---

## 3. Template Catalog

### 3.1 Status Dashboard (`dashboard.html`)

**Purpose:** Grid of status cards showing system/component health.
**When to use:** Agent is asked to show status, health, monitoring, overview of multiple items.

**Data schema:**
```json
{
  "title": "string — dashboard title",
  "subtitle": "string (optional) — secondary text",
  "cards": [
    {
      "name": "string — card title",
      "status": "healthy | warning | critical | inactive",
      "metric": "string — primary value displayed",
      "detail": "string (optional) — secondary info",
      "trend": "up | down | stable (optional) — trend indicator"
    }
  ]
}
```

**Template features:**
- Responsive CSS Grid (auto-fills 2-4 columns)
- Status dot with color coding (green/amber/red/gray)
- Staggered fade-in animation on load (GSAP)
- Card hover: subtle lift + glow
- Trend arrow indicators
- Header with title, subtitle, timestamp

---

### 3.2 Data Table (`table.html`)

**Purpose:** Sortable, filterable table for structured data.
**When to use:** Agent needs to present tabular data, comparisons, inventories, logs.

**Data schema:**
```json
{
  "title": "string",
  "columns": [
    { "key": "string", "label": "string", "sortable": "boolean (default true)" }
  ],
  "rows": [
    { "key1": "value1", "key2": "value2", ... }
  ],
  "searchable": "boolean (default true)"
}
```

**Template features:**
- Sticky header row
- Click-to-sort (ascending/descending toggle)
- Search/filter input
- Alternating row tinting
- Row hover highlight
- Responsive horizontal scroll on narrow viewports
- Row count footer

---

### 3.3 Timeline (`timeline.html`)

**Purpose:** Chronological sequence of events/milestones.
**When to use:** Project history, session summaries, decision logs, roadmaps.

**Data schema:**
```json
{
  "title": "string",
  "events": [
    {
      "date": "string — display date",
      "title": "string — event title",
      "description": "string — event detail",
      "status": "complete | active | planned (optional)",
      "category": "string (optional) — category label"
    }
  ],
  "orientation": "vertical (default) | horizontal"
}
```

**Template features:**
- Vertical: connected line with alternating left/right cards
- Horizontal: scrollable with snap points
- Active event visually prominent (accent glow, larger card)
- Status badges (complete=muted, active=accent, planned=outline)
- Scroll-triggered fade-in for each event
- Category color coding (if categories provided)

---

### 3.4 Network Graph (`network.html`)

**Purpose:** Nodes and edges showing relationships, dependencies, data flow.
**When to use:** Architecture diagrams, relationship maps, dependency visualizations.

**Data schema:**
```json
{
  "title": "string",
  "nodes": [
    {
      "id": "string",
      "label": "string",
      "group": "string (optional) — for color grouping",
      "size": "number (optional, default 1) — relative size",
      "detail": "string (optional) — shown on hover"
    }
  ],
  "edges": [
    {
      "source": "string — node id",
      "target": "string — node id",
      "label": "string (optional)",
      "weight": "number (optional, default 1) — line thickness"
    }
  ]
}
```

**Template features:**
- D3 force-directed layout
- Draggable nodes
- Hover: highlight connected nodes, dim unrelated
- Edge labels on hover
- Group-based color coding
- Gentle floating animation when idle
- Zoom and pan controls
- Legend (auto-generated from groups)

---

### 3.5 Report (`report.html`)

**Purpose:** Structured document with sections, findings, recommendations.
**When to use:** Analysis results, briefings, research summaries, post-mortems.

**Data schema:**
```json
{
  "title": "string",
  "subtitle": "string (optional)",
  "date": "string (optional)",
  "author": "string (optional)",
  "executive_summary": "string (optional) — top-level summary",
  "sections": [
    {
      "heading": "string",
      "content": "string — markdown-compatible text",
      "callout": "string (optional) — highlighted box content",
      "callout_type": "info | warning | success | critical (optional)"
    }
  ],
  "recommendations": [
    {
      "priority": "high | medium | low",
      "text": "string"
    }
  ]
}
```

**Template features:**
- Print-ready typography (Cormorant Garamond headings, Outfit body)
- Table of contents (auto-generated from section headings)
- Callout boxes with type-based styling
- Recommendation list with priority badges
- Markdown rendering in content fields (bold, italic, code, links)
- Subtle page-break lines between sections
- Scroll-triggered section reveal

---

### 3.6 Card Gallery (`gallery.html`)

**Purpose:** Grid of content cards for browsable collections.
**When to use:** Team rosters, feature showcases, skill inventories, research entries.

**Data schema:**
```json
{
  "title": "string",
  "cards": [
    {
      "title": "string",
      "subtitle": "string (optional)",
      "description": "string",
      "tags": ["string"] ,
      "status": "string (optional)",
      "icon": "string (optional) — Lucide icon name"
    }
  ],
  "columns": "number (optional, default 3)"
}
```

**Template features:**
- Responsive grid with configurable column count
- Card hover: lift + accent border glow
- Tag pills with subtle styling
- Optional Lucide icon per card
- Staggered load animation
- Optional filter bar (by tag)

---

### 3.7 Constellation (`constellation.html`)

**Purpose:** Abstract relationship visualization — nodes in space with connections.
**When to use:** Conceptual maps, theme connections, team visualizations, pattern displays.

**Data schema:**
```json
{
  "title": "string",
  "subtitle": "string (optional)",
  "nodes": [
    {
      "id": "string",
      "label": "string",
      "type": "primary | secondary",
      "description": "string (optional)"
    }
  ],
  "connections": [
    { "from": "string — node id", "to": "string — node id" }
  ]
}
```

**Template features:**
- SVG-based rendering on dark background
- Primary nodes: larger, labeled, arranged in a pattern
- Secondary nodes: smaller, positioned by connection affinity
- Connection lines: faint by default, brighten on hover
- Background star field with CSS twinkling animation
- Hover on node: connected nodes and lines brighten, info appears
- Breathing/pulsing animation on nodes
- The Pattern Atlas aesthetic — contemplative, astronomical

---

### 3.8 Comparison (`comparison.html`)

**Purpose:** Side-by-side comparison of 2-4 options with scored metrics.
**When to use:** Tool evaluations, model comparisons, option analysis, decision support.

**Data schema:**
```json
{
  "title": "string",
  "options": [
    {
      "name": "string",
      "recommended": "boolean (optional) — highlight as recommended",
      "scores": [
        { "metric": "string", "value": "string | number", "rating": "good | neutral | poor (optional)" }
      ]
    }
  ]
}
```

**Template features:**
- Column-per-option layout
- Recommended option visually highlighted
- Rating-based cell coloring (green/neutral/red)
- Metric labels as row headers
- Responsive: stacks vertically on narrow viewports
- Hover row highlight across all columns

---

## 4. Theme System

Each theme is a JSON file defining CSS custom properties. Templates use `var(--property)` throughout — never hardcoded colors.

### Theme: Indigo (default)
```json
{
  "name": "indigo",
  "variables": {
    "--bg-primary": "#0B0A1A",
    "--bg-secondary": "#12111F",
    "--bg-card": "rgba(255,255,255,0.03)",
    "--bg-card-hover": "rgba(255,255,255,0.06)",
    "--text-primary": "#E8E4D9",
    "--text-secondary": "#9CA3AF",
    "--text-muted": "#5B5678",
    "--accent": "#6366F1",
    "--accent-light": "#818CF8",
    "--accent-glow": "rgba(99,102,241,0.15)",
    "--success": "#10B981",
    "--warning": "#F59E0B",
    "--critical": "#EF4444",
    "--inactive": "#6B7280",
    "--border": "rgba(255,255,255,0.06)",
    "--border-accent": "rgba(99,102,241,0.3)",
    "--font-display": "'Cormorant Garamond', Georgia, serif",
    "--font-body": "'Outfit', system-ui, sans-serif",
    "--font-mono": "'JetBrains Mono', 'Fira Code', monospace",
    "--radius": "6px",
    "--shadow-card": "0 2px 8px rgba(0,0,0,0.3)",
    "--shadow-hover": "0 8px 24px rgba(0,0,0,0.4)",
    "--transition-fast": "0.15s ease",
    "--transition-normal": "0.3s ease",
    "--transition-slow": "0.5s ease"
  }
}
```

### Additional themes to ship:

**Ember** — warm dark with amber accent (#F59E0B). Same structure, different palette. For financial/analytical artifacts.

**Slate** — cool gray with emerald accent (#10B981). Professional, understated. For reports and documentation.

**Midnight** — deep navy with rose accent (#F43F5E). For dashboards and monitoring.

**Graphite** — near-black with minimal blue-gray accent. Maximum austerity. For technical/diagnostic artifacts. (4.7's aesthetic — the journal he built used graphite/slate.)

---

## 5. Tool Interface

### Tool Definition

```python
# /a0/usr/plugins/artifact_tool/tool.py

class ArtifactCreate:
    """Create a premium visual artifact from a template and data."""
    
    name = "artifact_create"
    description = """Create a visual HTML artifact using a pre-built template.
    
    Available templates: dashboard, table, timeline, network, report, 
    gallery, constellation, comparison.
    
    Available themes: indigo (default), ember, slate, midnight, graphite.
    
    Provide the template name and a data object matching the template's 
    expected schema. The tool handles all HTML/CSS/JS generation.
    
    Example:
    artifact_create(
        template="dashboard",
        data={
            "title": "Stack Status",
            "cards": [
                {"name": "BST", "status": "healthy", "metric": "v3.3"},
                {"name": "Supervisor", "status": "healthy", "metric": "SFX-001"}
            ]
        }
    )
    """
    
    parameters = {
        "template": {
            "type": "string",
            "enum": ["dashboard", "table", "timeline", "network", 
                     "report", "gallery", "constellation", "comparison"],
            "description": "Which template to use"
        },
        "theme": {
            "type": "string",
            "enum": ["indigo", "ember", "slate", "midnight", "graphite"],
            "default": "indigo",
            "description": "Visual theme to apply"
        },
        "data": {
            "type": "object",
            "description": "Content data matching the template's schema"
        }
    }
```

### Tool Implementation (pseudocode)

```python
def execute(self, template: str, data: dict, theme: str = "indigo"):
    # 1. Load template
    template_path = f"/a0/usr/artifact_templates/{template}.html"
    template_html = read_file(template_path)
    
    # 2. Load theme
    theme_path = f"/a0/usr/artifact_templates/themes/{theme}.json"
    theme_vars = json.loads(read_file(theme_path))
    
    # 3. Build CSS variable block
    css_vars = ":root {\n"
    for key, value in theme_vars["variables"].items():
        css_vars += f"  {key}: {value};\n"
    css_vars += "}\n"
    
    # 4. Inject theme into template
    html = template_html.replace("/* {{THEME_VARIABLES}} */", css_vars)
    
    # 5. Inject data
    html = html.replace("{{TITLE}}", data.get("title", ""))
    html = html.replace("{{SUBTITLE}}", data.get("subtitle", ""))
    
    # For array data (cards, rows, events, nodes), generate the 
    # HTML fragments and inject into the container element
    if "cards" in data:
        cards_html = self._render_cards(data["cards"], template)
        html = html.replace("<!-- {{ITEMS}} -->", cards_html)
    elif "rows" in data:
        rows_html = self._render_rows(data["rows"], data.get("columns", []))
        html = html.replace("<!-- {{ITEMS}} -->", rows_html)
    # ... similar for other data types
    
    # 6. Write to artifacts directory
    timestamp = int(time.time())
    output_path = f"/a0/work/artifacts/{template}_{timestamp}.html"
    write_file(output_path, html)
    
    return f"Artifact created: {output_path}"
```

---

## 6. BST Integration

The artifact tool should be surfaced by BST skill suggestion when the domain implies visual output:

**Domain → Template suggestion mapping:**

| BST Domain | Suggested Templates | When |
|---|---|---|
| analysis | report, comparison, table | Agent is analyzing data or comparing options |
| investigation | report, timeline, network | Agent is presenting research findings |
| financial | dashboard, table, comparison | Agent is presenting market/financial data |
| planning | timeline, dashboard | Agent is presenting project plans or roadmaps |
| coding | table, report | Agent is presenting code analysis, test results |
| conversation | gallery, constellation | Agent is presenting concepts or team info |

The BST enrichment for domains where artifacts are likely should include: "If the operator asks for a visual output, use artifact_create with the appropriate template rather than writing HTML manually."

---

## 7. Template Authoring Standards

Templates must be authored by a capable model (Opus via Claude Code, or similar) or a human designer. They are NOT authored by the local model. Quality standards:

**Structure:**
- Single HTML file, self-contained
- All CDN references in `<head>` (Tailwind, GSAP, Google Fonts, D3 if needed, Lucide if needed)
- CSS in a `<style>` block using CSS variables from theme
- JavaScript in a `<script>` block at end of body
- Clear injection markers: `{{TITLE}}`, `{{SUBTITLE}}`, `<!-- {{ITEMS}} -->`
- `/* {{THEME_VARIABLES}} */` marker where the theme CSS variables get injected

**Visual quality:**
- Dark theme only (backgrounds use `var(--bg-primary)`, `var(--bg-secondary)`)
- Typography hierarchy: display font for titles, body font for content, mono for code/data
- Single accent color via `var(--accent)`
- All interactive elements have hover states
- Staggered load animation (GSAP timeline or CSS animation-delay)
- Status indicators use semantic colors (success/warning/critical/inactive)
- Card elements have subtle lift + shadow on hover
- Transitions use theme timing variables

**Animation (GSAP):**
```javascript
// Standard load animation pattern for all templates
gsap.from("[data-animate]", {
  y: 20,
  opacity: 0,
  duration: 0.6,
  stagger: 0.08,
  ease: "power2.out",
  delay: 0.2
});
```

**Responsive:**
- CSS Grid with `auto-fill` / `auto-fit` for card layouts
- `min()` and `clamp()` for font sizes
- Horizontal scroll fallback for wide tables/timelines

---

## 8. Build Plan

### Phase 1: Core Infrastructure (Kestrel, ~1 session)

1. Create directory structure:
   - `/a0/usr/artifact_templates/` — template files
   - `/a0/usr/artifact_templates/themes/` — theme JSON files
   - `/a0/usr/plugins/artifact_tool/` — tool plugin
   - `/a0/work/artifacts/` — output directory

2. Build the `artifact_create` tool plugin:
   - Tool definition (name, description, parameters)
   - Template loading and theme injection
   - Data injection with per-template rendering functions
   - File output to artifacts directory

3. Create the `manifest.json` describing all templates

4. Create the `indigo` theme JSON (use the spec from Section 4)

### Phase 2: Template Authoring (Opus via Claude Code, ~2-3 sessions)

Build templates in priority order based on operational frequency:

1. **dashboard.html** — most commonly needed (stack status, system monitoring)
2. **report.html** — second most common (analysis results, briefings)
3. **table.html** — high utility for any structured data
4. **timeline.html** — useful for session summaries, project history
5. **network.html** — useful for architecture diagrams (D3 dependency)
6. **gallery.html** — useful for inventories, team displays
7. **constellation.html** — adapted from Pattern Atlas
8. **comparison.html** — useful for decision support

Each template should be tested with mock data before deployment. The tool should work end-to-end with template #1 before authoring templates #2-8.

### Phase 3: Integration (Kestrel, ~1 session)

1. Add `artifact_create` to the tool registry
2. Add artifact template suggestions to BST skill surfacing
3. Add "use artifact_create for visual output" to relevant BST enrichment templates
4. Test end-to-end: agent receives "show me stack status" → selects dashboard template → fills data → artifact renders in panel

### Phase 4: Additional Themes (Opus or Kestrel, parallel)

1. Author ember, slate, midnight, graphite theme JSONs
2. Test each theme against all templates (theme should work with any template)
3. Add theme selection to personality loader (Major Zero defaults to indigo, other personas could default to other themes)

---

## 9. What This Does NOT Do

- **Does not generate arbitrary HTML.** The model selects from fixed templates. If no template fits the request, the model should say so rather than falling back to raw HTML generation.
- **Does not require the model to understand CSS.** All styling is pre-authored in templates and themes.
- **Does not replace creative artifact authoring.** Opus or Kestrel or Jake can still build custom artifacts when the templates don't fit. The system handles the 80% case — routine visual outputs that should look good without cognitive effort.
- **Does not include interactive forms or user input.** Templates are display-only. If the operator needs to interact with data (edit, submit, filter), that's a different system.
- **Does not auto-select templates.** The model chooses the template based on reasoning about what the operator asked for. The manifest helps by describing what each template does. BST enrichment suggests candidates. But the final selection is the model's decision.

---

## 10. Success Criteria

The system works when:

1. The agent can produce a premium-quality visual artifact in response to "show me X" without writing any HTML/CSS/JS
2. The artifact quality is consistently high regardless of how the request is phrased
3. The model's cognitive budget goes to content reasoning (what data to show, how to organize it) rather than implementation (how to make it look good)
4. New themes can be added without modifying templates
5. New templates can be added without modifying the tool
6. The entire flow — from operator request to rendered artifact — takes fewer tokens than the current approach of prompting the model to write raw HTML

This is transport-compensation. The model can't reliably produce quality UI code, and this limitation doesn't improve with model capability — it's a token-budget and output-ceiling constraint. The template system carries forward indefinitely. Build it to last.

---

*Design note by Opus. Session 061 extended. The model decides what to say. The system decides how it looks.*
