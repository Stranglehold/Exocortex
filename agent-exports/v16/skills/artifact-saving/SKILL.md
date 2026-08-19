---
name: artifact-saving
description: When you produce a visual artifact (HTML dashboard, SVG diagram, interactive
  chart, etc.)
triggers:
- When you produce a visual artifact (HTML dashboard, SVG diagram, interactive chart,
  etc.)
version: '1.0'
author: Exocortex
---

# Skill: Artifact Saving

When you produce a visual artifact (HTML dashboard, SVG diagram, interactive chart, etc.)
that the user might want to revisit later, save it to the artifact library using this pattern.

## Sidecar format

```json
{
  "title": "Human-readable title shown in sidebar",
  "description": "One-sentence description for the preview row",
  "type": "html",
  "tags": ["optional", "tags"],
  "created": "2026-03-20T14:30:00",
  "version": 1
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `title` | Yes | Displayed as tab title in the panel. Match the fence title exactly. |
| `description` | No | Shown below title in sidebar list. |
| `type` | No | `"html"` (default), `"svg"`, `"js"` |
| `tags` | No | For future filtering. |
| `created` | No | ISO 8601 UTC timestamp. |
| `version` | No | Increment if you update an existing artifact. |

## When to save vs. just emit

**Just emit (no file)**:
- One-off visualizations the user is unlikely to need again
- Draft / exploratory output

**Save + emit**:
- Anything the user asked to "keep", "save", or "track"
- Dashboards with live data the agent will update periodically
- Reports the user may want to share or revisit after the conversation ends

---

## Network / graph visualizations

Use **Cytoscape.js** for any artifact that renders nodes and edges (dependency graphs,
network maps, relationship diagrams, etc.). It is self-contained (~110 KB gzipped), has
built-in drag/zoom/pan, and responds cleanly to the panel's zoom controls via postMessage.

**Required pattern** — set `window._hasPanZoom = true` before any other script so the
panel's generic zoom script skips page-level transforms and lets the library own zoom:

```html
<script>window._hasPanZoom = true;</script>
<script src="https://unpkg.com/cytoscape@3.33.1/dist/cytoscape.min.js"></script>
<script>
const cy = cytoscape({
  container: document.getElementById('cy'),
  elements: [ /* nodes + edges */ ],
  style: [
    { selector: 'node', style: { 'background-color': '#2d2d4a', 'border-color': '#7c83fd',
      'border-width': 2, 'label': 'data(label)', 'color': '#e0e0e0',
      'text-outline-color': '#1a1a2e', 'text-outline-width': 2 } },
    { selector: 'edge', style: { 'line-color': '#3a4a6a', 'width': 1.5 } }
  ],
  layout: { name: 'cose', animate: true }
});

// Panel zoom/pan controls → Cytoscape viewport
window.addEventListener('message', (e) => {
  const d = e.data; if (!d) return;
  const c = { x: cy.width()/2, y: cy.height()/2 };
  if (d.t === 'zi') cy.zoom({ level: cy.zoom()*1.25, renderedPosition: c });
  if (d.t === 'zo') cy.zoom({ level: cy.zoom()*0.8,  renderedPosition: c });
  if (d.t === 'zr') cy.fit(cy.elements(), 30);
  if (d.t === 'pon') cy.userPanningEnabled(true);
  if (d.t === 'poff') cy.userPanningEnabled(false);
});
</script>
```

**Do NOT** load D3 and manually build zoom — the panel's zoom buttons will not connect to
D3's internal viewport without additional glue code, and nodes start off-screen until the
simulation settles. Cytoscape handles layout, zoom, pan, and node drag out of the box.
