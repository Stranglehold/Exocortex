# INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md
# Design Brief: Information Environments for Intelligence Analysis

*Synthesized from deep research across Palantir Gotham/Foundry, i2 Analyst's Notebook, Maltego, ATAK/WinTAK, Obsidian, OneNote, Google Earth, Gephi, Neo4j Bloom, ArcGIS/QGIS, Kumu, VirusTotal Graph, Miro/FigJam, Cambridge Intelligence tools, and the academic literature on information visualization.*

*Third pillar of the Exocortex design foundation. Companion to WEBUI_DESIGN_BRIEF.md (functional/safety) and AESTHETICS_DESIGN_BRIEF.md (aesthetics and design system).*

---

## 1. The Fundamental Problem

Every system in this category is wrestling with the same core tension: **the human visual field is a narrow window, but the information space is vast and non-linear.**

An analyst investigating a financial network may have 40,000 transactions, 3,000 individuals, 500 organizations, and 200 locations. These exist in a space that is simultaneously:

- **Relational** — who is connected to whom, and how
- **Temporal** — when did connections form, strengthen, break
- **Geographic** — where did events happen, where do entities operate
- **Hierarchical** — cells inside networks inside movements inside geopolitical contexts
- **Evidentiary** — each fact has a source, a confidence, a timestamp

No single visualization can represent all of this simultaneously. The design problem is not "how do I show everything" — it is: **how do I give the analyst navigational control over a space too large to see at once, while preserving enough context that they do not get lost?**

Every design decision in this brief is an answer to some aspect of that question.

---

## 2. The Science

### 2.1 Shneiderman's Visual Information-Seeking Mantra

Ben Shneiderman's canonical formulation: **"Overview first, zoom and filter, then details on demand."**

This three-step sequence describes the cognitive process of analytical exploration:

1. **Overview:** establish the shape of the information space — where are the clusters, where are the outliers, what is the scale?
2. **Zoom and filter:** narrow to the region of interest; suppress irrelevant information
3. **Details on demand:** retrieve full information about specific elements of interest

The mantra is correct for confirmation tasks (analyst knows what they are looking for) but incomplete for discovery tasks (analyst does not know what they are looking for). Discovery requires an additional step: **comparison** — placing two elements side by side to ask whether a relationship exists. The extended mantra for analytical environments: Overview → Zoom/Filter → Relate/Compare → Details on Demand.

**Implication for Exocortex:** The OSS ledger and ontology layer contain entities whose relationships are the primary analytical object. The interface must support all four stages, not just progressive detail disclosure.

### 2.2 Tufte's Principles in Analytical Environments

Tufte's core principle — maximize data-ink ratio — applies with modification to interactive analytical systems. In static print, ink is finite and every mark must carry information. In interactive systems, the equivalent principle is: **visual weight must be earned by analytical value.**

Key applications:
- **Chartjunk in graphs:** decorative node borders, gradient fills, drop shadows that carry no information are chartjunk. They add visual weight without adding information. In a graph with 200 nodes, unnecessary decoration compounds across every element and degrades the signal-to-noise ratio severely.
- **Small multiples:** showing the same graph structure at different time periods side by side is more cognitively efficient than animated change. The analyst can make comparisons without memory load.
- **Layering and separation:** visual variables (color, shape, size) must be used for different types of information. If color encodes entity type and also encodes relationship strength, the encoding collapses and neither dimension is readable.

### 2.3 Preattentive Attributes and Graph Comprehension

Colin Ware's research identifies the visual properties processed pre-consciously — before deliberate attention is engaged. These are the properties that "pop out":

| Attribute | Strength | Best use in graphs |
|-----------|---------|-------------------|
| **Color hue** | Strong | Entity type categories (max 8) |
| **Shape** | Strong | Entity type categories (max 8) |
| **Size** | Medium | Node degree, importance weight |
| **Color saturation** | Medium | Confidence, certainty |
| **Orientation** | Weak | Edge direction (arrowhead) |
| **Motion** | Strong (but disruptive) | Active/updating elements only |

**The 8-category limit:** Research consistently shows that categorical visual encoding becomes ineffective beyond 7–8 categories. Beyond that count, users cannot reliably distinguish categories at a glance — they must consult a legend. Consulting a legend is a System 2 task that interrupts analytical flow. Design entity type systems to be resolvable without a legend.

**Node size encodes importance:** degree centrality (number of connections), betweenness centrality (how often a node lies on paths between other nodes), or analyst-assigned importance. Size is the most natural encoding for "this node matters more."

### 2.4 Focus + Context Techniques

The fundamental tension in information environments: the analyst needs detail (zoom in) AND context (zoom out) simultaneously. Several techniques address this:

**Overview + Detail (two-window approach):** A separate small overview panel shows the full graph; the main canvas shows a zoomed-in region. The overview highlights the currently visible region. Research shows this outperforms distortion-based approaches for most analytical tasks because the two views operate at clearly distinct scales without compromise.

**Fisheye / rubber-sheet distortion:** The center of the display is magnified; the periphery is compressed to fit. This keeps context visible around the focal point without requiring a separate panel. In practice, fisheye distortion disorients analysts in large graphs because the compression warps spatial relationships they have already memorized. The research consensus favors overview+detail for analytical work.

**Semantic zoom:** As the user zooms in (higher spatial resolution), qualitatively different information is displayed. At low zoom: nodes as shapes only. At medium zoom: nodes with labels. At high zoom: nodes with labels and secondary properties. At maximum zoom: full property display. This matches the cognitive process of investigation: start with structure, then identity, then detail.

### 2.5 Coordinated Multiple Views

The canonical four-view combination for analytical systems: **Graph + Map + Timeline + Table**

These four views represent the four primary dimensions of most analytical data:
- Graph → relational structure
- Map → geographic context
- Timeline → temporal sequence
- Table → raw data with sortable/filterable attributes

**The critical requirement: synchronization.** Selecting an entity in any view highlights it in all views simultaneously. Filtering in one view filters all views. This is non-negotiable for multi-dimensional analytical data. An analyst who finds an entity in the timeline must be able to see it in the graph and map instantly, without a separate search step.

The cognitive mechanism: coordinated views offload memory. Instead of mentally maintaining the relationship between a node's position in the graph and its position on the map, the interface maintains it. The analyst's working memory is freed for analytical judgment.

### 2.6 Dual-Process Theory Applied to Interface Design

System 1 (fast, automatic, pattern recognition) and System 2 (slow, deliberate, reasoning) must be assigned the right operations:

**System 1 operations (should require no conscious effort):**
- Entity type identification (color + shape preattentive encoding)
- Connection presence detection (edges)
- Cluster identification (spatial proximity)
- Relative importance assessment (node size)
- Active vs. inactive status (subtle motion or saturation)

**System 2 operations (require deliberate engagement):**
- Reading node labels and properties
- Following complex multi-hop paths
- Evaluating evidence quality
- Forming analytical conclusions

**Design requirement:** Every System 1 operation that is forced into System 2 (e.g., requiring the analyst to read a legend to identify an entity type) is a cognitive tax. Minimize these taxes to reserve System 2 capacity for actual analysis.

### 2.7 Cognitive Fit Theory

A representation cognitively fits a task when the format of the representation matches the mental model required for the task. Mismatch between representation and task degrades performance.

| Task | Best representation |
|------|-------------------|
| Identify connections between entities | Node-link graph |
| Compare values across entities | Bar chart or table |
| Show geographic distribution | Map |
| Show change over time | Timeline or line chart |
| Navigate hierarchy | Tree / nested containers |
| Identify clusters | Graph with community coloring |

**The implication:** An analytical system that shows everything as a graph is not serving all analytical tasks. A system that offers multiple representations and allows the analyst to switch based on task will outperform a single-representation system.

---

## 3. The Node-Click Interaction — Full Specification

The node-click interaction is the most important micro-interaction in link analysis software. It defines the cognitive rhythm of investigation. The ideal interaction has five distinct phases:

### Phase 1: Immediate Selection (< 100ms)
- Node changes to selection visual state (distinct border color, slight glow)
- **Connected edges highlight** — the selected node's immediate connections become more salient
- **Unconnected nodes dim** — gentle reduction in opacity (not hide — the analyst needs to know they are still there)
- Connected neighbor nodes receive a subtle secondary highlight (lighter than the selected node, but distinguishable from unselected nodes)

The effect: the analyst's ego-network (the selected node and its immediate neighbors) becomes the visual foreground. The rest of the graph recedes to context.

### Phase 2: Identity Confirmation (< 300ms)
A **hover card** (or appears automatically on click) shows the minimal identifying information needed to answer: "is this the entity I'm interested in?"

For the OSS ledger: claim text (first 100 characters), source, date, topic tags, confidence level
For the ontology layer: entity name, type, aliases, mention count, first/last seen

The hover card is not a full property sheet. It is the minimum necessary to confirm identity. If the answer is "no, wrong entity," the analyst should be able to dismiss and continue without having committed to a full investigation of this node.

### Phase 3: Full Properties (< 500ms, on deliberate click)
A **detail panel** appears — not a modal (modals interrupt context), but a panel that slides in alongside the canvas. The canvas reflows or the panel overlaps a side zone. The graph remains visible and interactive.

The detail panel shows:
- All entity properties
- Data source and provenance
- Confidence/reliability indicators
- Timestamps (created, modified, last updated)
- A list of **available expansions** with counts: "Associates (14)," "Documents (3)," "Events (7)"

The counts are critical: they tell the analyst whether expansion is worth pursuing before committing to it. An expansion of "Associates (0)" can be dismissed at a glance. An expansion of "Associates (847)" signals either a hub node or bad data — both useful signals.

### Phase 4: Expansion (on expand button click)
The analyst clicks an expansion category (e.g., "Associates (14)"). The system:
1. **Queries the backend** for the connected entities of that type
2. **Animates** new nodes into position — they travel from the source node outward, not teleport in. The animation preserves the user's spatial sense of where these entities "come from."
3. **Runs gentle layout adjustment** — the graph reflows slightly to accommodate the new nodes. Not a full relayout (which destroys all spatial memory) — a local adjustment that moves existing nodes minimally while making room for the new ones.
4. **Preserves selection state** — the original selected node remains selected; new nodes are shown in a distinct "just expanded" visual state

### Phase 5: Navigation
From the expanded view, the analyst can:
- Click any new node to begin the same five-phase cycle on it (recursive exploration)
- See a **breadcrumb trail** showing the exploration path: Entity A → Associates → Entity B → Documents → Document C
- Return to a previous node in the trail (not back-button — jumping to a specific prior node in the path)
- Pin important nodes (mark them as anchor points in the investigation)

### What to Avoid
- **Modal dialogs** for node details — they interrupt context and hide the graph
- **Full relayout on expansion** — destroys the analyst's spatial memory of where nodes are
- **Instant teleportation of new nodes** — removes the visual connection between new nodes and their source
- **Hiding filtered nodes** rather than dimming them — removes context the analyst needs
- **Expansion without counts** — analyst cannot assess whether expansion is worth pursuing

---

## 4. Graph Layout Algorithms — Semantic Choice

Layout choice is semantic, not cosmetic. The layout communicates something about the data structure. Choosing the wrong layout obscures the structure it should reveal.

| Layout | What it communicates | When to use | Failure mode |
|--------|---------------------|-------------|--------------|
| **Force-directed** | Emergent clusters based on connection density | Unknown topology, exploratory analysis | "Hairball" on large dense graphs |
| **Hierarchical (Sugiyama)** | Flow, command, causation | Organizational trees, workflow, supply chains | Poor for cyclic or reciprocal relationships |
| **Radial** | Centrality of a focal node | Ego-network analysis, one entity's connections | Poor for multi-hub or flat networks |
| **Geographic** | Spatial distribution | Any data with location attributes | Loses relational structure when entities cluster geographically |
| **Temporal** | Sequence, change over time | Event timelines, network evolution | Loss of spatial relationship information |
| **Circular (chord)** | All-to-all relationships | Trade flows, communication matrices | Unreadable above ~20 nodes |

**The hairball problem:** Force-directed layouts on large, dense graphs produce visually useless tangles. Solutions:
1. Pre-filter to minimum degree threshold before layout
2. Run community detection and layout at cluster level, then within clusters
3. Use Force Atlas 2 with LinLog mode to reduce hub dominance
4. Impose geographic or hierarchical structure when it exists in the data

---

## 5. Layering and Filtering

### 5.1 The Filter vs. Delete Distinction

This is the most important operational distinction in analytical interfaces.

**Filtering** makes elements temporarily invisible while preserving them in the data model. The analyst knows the filtered elements exist. They can be restored with a single gesture. The "grey but visible" variant keeps filtered elements visible at reduced opacity — the analyst can see the complete information space while focusing on the filtered subset.

**Deletion** removes elements from the graph permanently (within the session). The analyst cannot easily determine what was removed.

**Design requirement:** Analytical tools must always use filtering, never deletion, for display purposes. Permanent removal of entities from an investigation is a documented action requiring confirmation — it is not the result of a filter operation.

### 5.2 Non-Destructive Filter Implementation

```
Full graph (all entities, all relationships)
     ↓ filter operation
Active layer (filtered view)
     ↓ display
Visual canvas (filtered entities shown; filtered-out entities grayed at 20% opacity)
```

The analyst sees everything. The attention is directed to the unfiltered subset. The context is preserved.

### 5.3 Layer Categories for Intelligence Analysis

Translating ATAK/GIS layer architecture to an intelligence analysis context:

| Layer | Content | Default state |
|-------|---------|---------------|
| **Entities: Persons** | Individual human entities | Visible |
| **Entities: Organizations** | Groups, companies, agencies | Visible |
| **Entities: Locations** | Locations, facilities, geopoints | Visible |
| **Entities: Events** | Discrete events, incidents | Visible |
| **Entities: Documents** | Source documents, reports | Hidden (on demand) |
| **Relationships: Confirmed** | High-confidence connections | Visible |
| **Relationships: Inferred** | Analytically inferred connections | Hidden (on demand) |
| **Relationships: Contested** | Low-confidence or disputed | Hidden (on demand) |
| **Analyst annotations** | Notes, highlights, bookmarks | Visible |
| **Evidence provenance** | Source document links | Hidden (on demand) |
| **Temporal: Historical** | Pre-date-filter events | Grayed (visible, reduced) |

### 5.4 Filter Persistence and Compound Filters

Filters should be:
- **Visible:** the current filter state is always shown (what is filtered, not just that something is filtered)
- **Composable:** multiple filters stack. "Persons AND confirmed relationships AND 2024 onwards" is a compound filter, each component removable independently
- **Named and saveable:** analysts return to the same filter configurations repeatedly. Named filters are bookmarks into the information space.

---

## 6. The Analyst Workflow

### 6.1 The Intelligence Analysis Cycle

The canonical cycle: **Direction → Collection → Processing → Analysis → Dissemination**

The interface supports different stages differently:

| Stage | Interface need |
|-------|--------------|
| **Direction** | Task framing: what question are we answering? Explicit recording of the analytical question |
| **Collection** | Ingestion interface: adding sources, entities, claims to the investigation |
| **Processing** | Entity resolution, deduplication, relationship extraction |
| **Analysis** | Graph exploration, temporal analysis, pattern identification |
| **Dissemination** | Export, briefing package generation, graph snapshots with annotations |

### 6.2 The Sensemaking Loop

Pirolli and Card's sensemaking model describes the analyst's actual cognitive process:

```
Foraging loop (find relevant information):
Search sources → filter → extract → organize

Sensemaking loop (build understanding):
Organize → hypothesize → evaluate evidence → update model
```

The interface must support both loops without forcing the analyst to switch between separate tools. The foraging loop uses search, filter, and ingestion. The sensemaking loop uses the graph canvas, annotation, and hypothesis tracking.

**The investigative pivot:** The moment an analyst identifies a connection that reframes the investigation — a node that connects two previously separate clusters, a timeline anomaly that changes the sequence of events. The interface must make pivots easy: the analyst should be able to follow any discovered connection immediately without losing context.

### 6.3 The Analytical Record

The investigation is not just the current graph state — it is the history of how the analyst arrived at it. The analytical record includes:
- What entities were added, and when
- What queries were run
- What hypotheses were formed
- What evidence was reviewed
- What conclusions were reached

This record is both an audit trail (methodological rigor) and a continuity mechanism (another analyst can take over). Systems that track only current state lose the analytical provenance.

---

## 7. Geospatial Integration

### 7.1 The Two-Space Problem

Most analytical data has both relational attributes (connections) and geographic attributes (locations). Showing both simultaneously requires fusing two incompatible visual grammars:

- **Graph space:** position conveys relationship (connected nodes are near each other)
- **Geographic space:** position conveys actual physical location (nodes are where they are on the earth)

These grammars are contradictory. An organization in Dubai and one in London cannot be near each other in both geographic space AND in relationship space simultaneously.

### 7.2 Hybrid Design Patterns

**Approach 1: Geographic layout as default, relationship overlay on demand.**
Nodes are placed at their geographic positions. Relationship edges are overlaid. The spatial position carries geographic meaning; the edges carry relational meaning. Works well when geography is the primary analytical dimension.

**Approach 2: Force-directed with geographic clustering.**
Nodes are laid out by relationship (force-directed) but geographic grouping is enforced: nodes with the same country cluster in the same screen region. Relationship edges connect across regions. A compromise that degrades both spatial grammars but makes both legible.

**Approach 3: Synchronized dual view.**
Left panel: geographic map with entity pins. Right panel: relationship graph with force-directed or hierarchical layout. Selection propagates across both. This is the cleanest approach but requires screen real estate.

### 7.3 Temporal-Geographic Fusion

ATAK's model: the map is the primary view; time controls (animation, scrubber) apply to all entities on the map. Entities appear, move, and disappear as the timeline advances. This is highly effective for tracking movement and event sequences but requires pre-processed temporal data.

---

## 8. The Canvas vs. Feed vs. Graph Metaphor

### 8.1 Three Primary Interface Metaphors

**The feed metaphor** (chat interfaces, Twitter, email): information arrives chronologically, newest first. Best for: sequential processes, notifications, agent outputs. Fails for: relational data, non-sequential analysis, spatial comparison.

**The canvas metaphor** (OneNote, Miro, Obsidian's graph view): information is placed in 2D space by the user or by layout algorithms. Spatial position is meaningful (or can be). Best for: freeform thinking, visual arrangement, spatial memory. Fails at scale through "spatial archaeology" — the analyst cannot remember where they put things, and search degrades to spatial navigation.

**The graph metaphor** (Palantir, Maltego, Neo4j Bloom): entities are nodes, relationships are edges, position conveys structure. Best for: relational data where the connections are the analytical object. Fails for non-relational data and degrades to hairball at scale without careful layout management.

### 8.2 The Spatial Archaeology Failure Mode

Canvas interfaces fail at scale because they rely on spatial memory. The analyst places notes, entities, and diagrams on a 2D canvas. As the canvas grows:
- **Navigation becomes archaeology:** the analyst searches by moving around the canvas rather than by query
- **Spatial memory degrades:** the analyst forgets where things are
- **Orphaned information:** nodes and clusters get placed and forgotten

Mitigations: robust search that jumps to entities on the canvas, zoomed-out overview that shows the entire canvas with navigable minimap, tagging/filing systems that provide non-spatial retrieval.

Obsidian's graph view addresses this by making the canvas algorithmic rather than manual — the graph is generated from link structure, not placed by hand. The analyst navigates by traversing links, not by spatial memory.

### 8.3 When Each Metaphor Is Right

| Use case | Best metaphor |
|----------|--------------|
| Monitoring ongoing agent activity | Feed |
| Exploring entity relationships | Graph |
| Open-ended investigation | Canvas (with search) |
| Structured analysis with known data types | Coordinated views (graph + map + timeline + table) |
| Writing and note-taking | Canvas (Obsidian/OneNote) |
| Briefing/output | Document |

The Exocortex interface should support multiple metaphors and allow the analyst to switch based on task, not force all interaction through a single metaphor.

---

## 9. What Fails and Why

### 9.1 The Hairball Problem

Large force-directed graphs inevitably produce dense tangles where no analytical signal is visible. The visual is correct — a highly interconnected network IS visually complex — but the representation fails the analyst because it produces no new insight.

**Prevention:**
- Pre-filter to the subgraph relevant to the current question before display
- Community detection first; display at the cluster level with expand-to-detail
- Never show a raw unfiltered large graph as the default view
- Apply Force Atlas 2 with LinLog mode for large graphs

### 9.2 The Legend Problem

Any visualization with more than ~8 categorical entity types requires a legend. Reading a legend is a System 2 task that interrupts analytical flow. When the legend is required for basic comprehension, the preattentive advantage of visual encoding is lost.

**Prevention:**
- Limit categorical visual dimensions to ≤8 per dimension
- Use a universal icon language (person silhouette, building, flag, document) that reads without a legend
- Design icons to be legible at 16px minimum

### 9.3 Context Destruction During Navigation

The most common analytical failure mode: the analyst clicks through several nodes, expanding and exploring, and loses track of where they are and how they got there. The graph has reflowed; previous spatial relationships are gone; the analyst cannot find their way back to the original context.

**Prevention:**
- Never do full relayout after expansion — local adjustment only
- Maintain a breadcrumb trail of exploration path
- Provide "collapse expansion" — undo the last expansion to return to the previous state
- Offer named "views" — snapshots of graph state the analyst can return to
- Keep the original anchor node visible and pinned

### 9.4 The Overloaded Node Label

Node labels that are too long, too numerous, or styled incorrectly destroy graph readability. At 200 nodes, if every label is 30 characters, the labels become the dominant visual element and the graph structure — which is the actual information — is buried.

**Prevention:**
- Display labels only above a zoom threshold (semantic zoom)
- Truncate labels to 15–20 characters with full name in tooltip
- Use font size and weight to distinguish entity types (person names in regular weight; organization names in bold) without requiring color for this dimension

---

## 10. Application to Exocortex

The Exocortex stack already contains the architectural components for a sophisticated information environment:

| Exocortex component | Information environment role |
|--------------------|------------------------------|
| **OSS intelligence ledger** | Claims and topics as nodes; co-occurrence and thematic relationships as edges |
| **Ontology layer** | Entity graph (persons, organizations, events, locations) with JSONL relationship store |
| **Network graph artifact** | Current graph visualization (needs design system integration) |
| **Investigation report tool** | Dissemination output of the sensemaking loop |
| **Evidence ledger** | Provenance and source tracking for all claims |
| **Epistemic integrity layer** | Confidence and temporal volatility metadata for nodes |
| **Memory system** | Analytical record (what the agent has found and when) |

### 10.1 The Exocortex Information Architecture

The analyst's information environment should present three views of the same underlying data:

**View 1 — Graph Canvas**
Node-link visualization of the entity and claim network. Supports:
- Node click → five-phase interaction (identity → properties → expansions → animate → breadcrumb)
- Layer controls (entity types, relationship confidence, temporal filter)
- Layout switching (force-directed for exploration, geographic for spatial analysis, temporal for sequence)
- Community detection to surface clusters
- Export for briefing packages

**View 2 — Timeline**
Events, claims, and entity appearances arranged on a temporal axis. Synchronized with graph canvas — selecting a date range filters the graph to entities active in that period. Supports:
- "Animate forward" to show network evolution
- Anomaly highlighting (events that fall outside expected temporal patterns)
- Source ingestion timestamps to distinguish "when did this happen" from "when did we learn this"

**View 3 — Table**
The raw claims and entities with sortable, filterable columns. Synchronized with graph canvas. Supports bulk operations, export, and precise filtering that the spatial graph view makes difficult.

### 10.2 The Node Click Model for the OSS Ledger

When the analyst clicks a claim node in the OSS graph:

**Immediate:** Claim highlights; connected claims (same topic, same source, same entities mentioned) highlight; unconnected claims dim

**Hover card:** Claim text (first 150 chars), source, date, topic, confidence, EI verdict (fabrication risk)

**Detail panel:** Full claim text, all metadata, source document link, SWARMFISH prediction if available, analyst notes, available expansions: "Same source (N)," "Same entities (N)," "Same topic (N)," "Related claims (N)"

**Expand:** New claim nodes animate in from the source node; related claims revealed; the investigation deepens from the selected claim outward

### 10.3 Design System Connection

The information environment components must use the token system established in AESTHETICS_DESIGN_BRIEF.md:

- **Node colors** use the semantic token `--color-entity-{type}` variants — defined per theme, so TACTICAL theme uses amber/green entity type encoding, TERMINAL theme uses warm beige greyscale differentiation
- **Graph canvas background** uses `--color-surface-ground` — the deepest surface in the elevation system
- **Selected node state** uses `--color-accent-primary` — consistent with interactive element selection across the whole interface
- **Detail panel** is the standard panel component from the design system, not a bespoke graph-specific element
- **Breadcrumb trail** uses the `--font-mono` setting — the analytical navigation path is treated as structured data, not prose

### 10.4 The Analytical Register

From AESTHETICS_DESIGN_BRIEF.md: the Exocortex interface register is "the calm experienced operative who has run this operation before." This extends to the information environment:

- Graph nodes have weight and intentionality — they are not arbitrary dots but entities with significance
- Expansion animations feel like intelligence arriving, not UI animating
- The layout algorithm serves the analyst's mental model of the network structure — it earns its position
- The detail panel is a dossier, not a properties window
- The breadcrumb trail is a case file path, not a browser history

---

## 11. Design Patterns Reference

### 11.1 Detail-on-Demand

| Level | Trigger | Content | Goal |
|-------|---------|---------|------|
| **Hover card** | Mouse hover 200ms | Identity fields only | "Is this the entity I want?" |
| **Click panel** | Deliberate click | All properties + expansion counts | "What do I know about this?" |
| **Expand** | Expand button | Connected entities by type | "What connects to this?" |
| **Drill-through** | Link in panel | Full source document | "Where did this come from?" |

### 11.2 Semantic Zoom Levels

| Zoom level | Node display | Edge display |
|-----------|-------------|-------------|
| **Overview** (< 50%) | Shape only, no label | Lines only |
| **Structure** (50–75%) | Shape + truncated label | Lines + direction arrow |
| **Identity** (75–100%) | Shape + full label | Lines + type label |
| **Detail** (> 100%) | Shape + label + key properties | Lines + full relationship label |
| **Document** (maximum) | Full property card | Full annotation |

### 11.3 Coordinated View Interaction Model

```
User action in any view → event emitted → all views receive event
Event types:
  SELECT(entity_id)       → highlight in all views
  FILTER(criteria)        → apply to all views
  RANGE(start, end, dim)  → restrict temporal/spatial range in all views
  HOVER(entity_id)        → show hover card in all views
  DESELECT()              → clear selection in all views
```

### 11.4 Non-Destructive Filter State

```
Filter state is a first-class object:
{
  name: "Iran-Hormuz: High confidence, 2024 only",
  conditions: [
    { type: "topic", value: "iran-hormuz" },
    { type: "confidence", operator: ">=", value: 0.7 },
    { type: "date", operator: ">=", value: "2024-01-01" }
  ],
  display_mode: "grey_filtered"  // vs. "hide_filtered"
}
```

Saved filters are named bookmark views into the information space. The analyst can return to any saved filter state in one click.

---

## 12. What This Brief Does Not Cover

- This brief does not specify layout algorithm implementations (those belong in technical specs for the graph visualization component)
- This brief does not specify the data pipeline for populating the entity graph (that is the ontology layer spec domain)
- This brief does not define the briefing package export format
- This brief does not specify how machine-generated entities (from the ontology layer) are visually distinguished from analyst-added entities — this requires a separate design decision (recommendation: opacity or border treatment distinguishing provenance)

---

## 13. The Ten Design Principles of an Excellent Information Environment

From the synthesis across all surveyed systems:

1. **Domain-native ontology.** The system understands its domain's entity and relationship types natively. Analysts think in domain terms, not graph terms.

2. **Query-driven exploration.** The graph grows as the analyst explores. The full data is not loaded at once — the analyst pulls information toward them by asking questions.

3. **Progressive disclosure at every level.** Overview shows structure. Filter shows subsets. Click shows properties. Expand reveals relationships. Every level reveals only what is needed at that stage.

4. **Coordinated views synchronize.** Map, graph, timeline, and table are views of the same underlying reality. Selection in one propagates to all.

5. **Node interaction is crafted at every phase.** Selection highlights neighbors and dims strangers. Hover confirms identity. Click shows properties in a non-modal panel. Expand offers typed relationship categories with counts. The analyst always knows what is available before accessing it.

6. **Filtering is non-destructive and visually honest.** Filtered elements are shown at reduced opacity, not hidden. The analyst retains a sense of the complete information space.

7. **Layout algorithm matches data structure.** The system offers multiple layouts. Switching layouts is non-destructive to selection and filter state.

8. **Annotations and provenance are first-class.** Every entity has a source. Every conclusion has an author and timestamp. Data is distinguishable from analysis.

9. **The cognitive overhead of the interface is minimized.** Entity types are distinguishable without a legend. Common operations are available without menus. Visual feedback is immediate. The interface reserves working memory for analysis, not navigation.

10. **The analytical record is preserved.** The path the analyst took through the information space is tracked, navigable, and attributable. Another analyst can reconstruct the investigation.

---

## 14. Research Sources

**Foundational academic:**
- Shneiderman, B. (1996). The eyes have it: a task by data type taxonomy for information visualizations. *IEEE Symposium on Visual Languages.*
- Ware, C. (2004). *Information Visualization: Perception for Design, 2nd ed.* Morgan Kaufmann.
- Tufte, E.R. (1983). *The Visual Display of Quantitative Information.*
- Pirolli, P. & Card, S. (2005). The sensemaking process and leverage points for analyst technology. *Proceedings of Intelligence Analysis.*
- Roberts, J.C. (2007). State of the art: Coordinated and multiple views in exploratory visualization. *CMV 2007.*

**Focus+context:**
- Furnas, G.W. (1986). Generalized fisheye views. *CHI 1986.*
- Cockburn, A., Karlson, A., & Bederson, B.B. (2008). A review of overview+detail, zooming, and focus+context interfaces. *ACM CSUR 41(1).*

**Network visualization:**
- Herman, I., Melançon, G., & Marshall, M.S. (2000). Graph visualization and navigation in information visualization. *IEEE TVCG 6(1).*
- Jacomy, M. et al. (2014). ForceAtlas2: A continuous graph layout algorithm for handy network visualization. *PLOS ONE.*

**Intelligence analysis and sensemaking:**
- Heuer, R.J. (1999). *Psychology of Intelligence Analysis.* CIA Center for the Study of Intelligence.
- Chang, R. et al. (2008). Scalable and interactive visual analysis of financial wire transactions. *Information Visualization 7(1).*

**Systems (public documentation):**
- Palantir Technologies product documentation and public case studies.
- Maltego documentation and training materials.
- TAK Product Center, ATAK official documentation.
- Cambridge Intelligence ReGraph/KeyLines developer documentation.
- Obsidian.md documentation and community wiki.

---

*Research conducted March 2026. Raw synthesis: D:\tmp\information_viz_research.md (111KB).*
*See also: WEBUI_DESIGN_BRIEF.md, AESTHETICS_DESIGN_BRIEF.md.*
