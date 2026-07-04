# EXOCORTEX PANEL DESIGN — Operating Principle
## The Interface IS the Experience
### Author: Opus + Jake — June 21, 2026

---

## 1. The Vision

The Exocortex panels should feel like **diegetic game interfaces** — UI that exists within its own world, not overlaid on top of it. The inspiration is not corporate SaaS dashboards or glassmorphism trends. The inspiration is the iDroid from Metal Gear Solid V, the MAGI system monitor from Evangelion, the YoRHa intel codex from NieR: Automata, the CRT command console from HighFleet, and the RPG character sheets from Elden Ring, Witcher 3, and Bravely Default.

These interfaces share four qualities that make them feel premium:

1. **The interface belongs to a world.** It has texture, atmosphere, and character. It feels like a physical object — a holographic projection, a worn parchment codex, a military-grade CRT monitor — not a flat digital screen.

2. **Information density without visual overload.** RPG stat screens pack enormous amounts of data into clean hierarchies. The eye knows where to go. Visual weight guides attention without competing elements.

3. **Every element earns its presence.** No decoration without function. The scanlines on the MAGI monitor reinforce the CRT aesthetic while providing visual rhythm. The parchment texture on NieR's intel screen signals "this is a record, a codex" — it carries meaning.

4. **The UI rewards engagement.** Selecting an item in the iDroid rotates a 3D model. Scrolling through NieR's codex reveals lore. The interface invites exploration, not just operation.

The Exocortex is a sovereign AI operations center — the bunker. Its panels should feel like you're sitting at the command console of that bunker: purposeful, atmospheric, information-rich, and alive.

---

## 2. Reference Material

### Primary References (Jake's UI folder)
Location: `C:\Users\Jake\Pictures\UI examples\`

| Reference | What to study | Translate to |
|-----------|---------------|--------------|
| **MGSV iDroid** (database, development, map, music player, report) | Holographic blue projection, breadcrumb nav, 3D model viewer, status bar, translucent layers over environment | Office panel — agent management, cycle status, wiki navigation |
| **NieR: Automata** (intel, skills-chips, controls, chapter-select, loading) | Parchment texture, serif typography, tree-view navigation, tab bar, the worn quality, chip-based skill system | Intel panel — field reports, research codex, skill catalog |
| **Evangelion MAGI** (system monitor, command screens) | Amber monochrome on dark, hexagonal grid background, Japanese + English bilingual labels, real-time telemetry, angular bordered sections | System panel — inference metrics, VRAM, thermal, cycle telemetry |
| **HighFleet** (map screen) | Skeuomorphic military hardware, CRT radar scope, physical buttons, metal textures, ELINT danger indicators | SWARMFISH — threat assessment, confidence radar, prediction tracking |
| **Elden Ring** (equipment, level-up) | Clean stat displays, equipment slots as visual hierarchy, progress bars with precise numbers | Agent stats — skill inventory, methodology performance, capability levels |
| **Witcher 3** (character, map) | Rich map with layered information, character sheet with nested categories | Wiki map — knowledge graph visualization, research domain navigation |
| **Bravely Default** (jobs, equipment) | Job class cards with visual identity, clean inventory management | Cycle type cards — BUILD/EXPLORE/MAINTAIN with visual identity per type |

### Evangelion Sub-folder
Location: `C:\Users\Jake\Pictures\UI examples\Evangelion\`
Contains NERV command center screens, MAGI system displays, and ambient command center atmosphere references.

### Online Resources

| Resource | URL | Use |
|----------|-----|-----|
| Game UI Database | gameuidatabase.com | 55,000+ screenshots, filterable by game, category, style |
| NieR Automata React Library | github.com/Kndgy/NieR-Automata-Design-System | React components implementing NieR's UI — directly usable |
| NieR Automata Figma Kit | figma.com/community/file/1598348131070316402 | Base components for reference and adaptation |
| Three.js CRT Shader | github.com/unframework/threejs-crt-shader | React + Three.js CRT monitor with scanlines — MAGI aesthetic |
| Diegetic UI Guide | yamii.shop/2026/04/04/diegetic-ui-guide | Design principles for world-embedded interfaces |

---

## 3. Technology Stack

### Core
| Library | Role | Why |
|---------|------|-----|
| **React** | Component architecture | Already in A0's web UI stack |
| **Three.js** (r171+) | 3D rendering, shaders, particle effects | WebGPU support with automatic WebGL 2 fallback |
| **React Three Fiber** | Three.js in React/JSX | Declarative 3D, composable with React state |
| **GSAP** | Animation, camera transitions, spring physics | Industry standard for web animation, timeline control |
| **Tailwind CSS** | 2D layout and utility styling | Already in use, pairs with the Theme system |

### Effects & Shaders
| Technique | Implementation | Panel Application |
|-----------|---------------|-------------------|
| CRT scanlines | Custom fragment shader (see threejs-crt-shader) | MAGI-style system monitor |
| Holographic projection | Additive blending + fresnel + depth blur | iDroid-style agent management |
| Particle fields | GPU instanced particles (Three.js InstancedMesh) | Agent activity visualization |
| Parchment/paper texture | Canvas noise generation + CSS filters | NieR-style intel codex |
| Ambient lighting | Three.js PointLight + bloom pass | Atmospheric depth on all panels |
| Hex grid background | SVG pattern or procedural geometry | NERV command center aesthetic |
| Depth of field | Three.js postprocessing (BokehPass) | Focus attention, blur periphery |
| Data-driven motion | Bind animation parameters to real data | Particle speed = inference tok/s |

### Fonts (Variable, self-hosted)
| Font | Role | Aesthetic |
|------|------|-----------|
| **Share Tech Mono** | System readouts, telemetry, version numbers | Military/technical monospace |
| **Rajdhani** | Headers, section titles, navigation | Angular, technical, readable |
| **EB Garamond** | Codex/report body text, field reports | Elegant serif for NieR-style parchment |
| **Inter** | UI controls, labels, form elements | Clean, readable utility face |

---

## 4. Theme Integration

The panels connect to the existing three-tier theme system:

**Tier 1 (Palette)** — Each theme provides CSS custom properties for colors and fonts. The panels read these properties, so switching from "YoRHa" to "Diamond Dogs" to "iDroid" changes the entire panel aesthetic without touching component code.

**Tier 2 (Atmospheric)** — Background images, panel translucency, overlay effects. The theme provides the atmospheric layer; the panel renders data on top of it.

**Tier 3 (Immersive)** — Canvas animations, particle effects, shader passes. This is where Three.js lives. Each theme can provide its own immersive layer: the YoRHa theme gets parchment noise and subtle grain. The iDroid theme gets holographic glow and scan lines. The MAGI theme gets amber CRT scanlines and hex grid.

### Theme-Panel Mapping (Showcase)

```
YoRHa Theme     → Parchment codex panels, serif typography, worn texture
iDroid Theme    → Holographic blue projection, translucent data cards, 3D elements
MAGI Theme      → Amber monochrome, CRT scanlines, hex grid, system telemetry
Diamond Dogs    → Military dark ops, emblem watermark, tactical grid
Codec Theme     → Green-on-black terminal, waveform visualizer, radio static
Kaer Morhen     → Warm stone, heraldic borders, aged manuscript
```

The theme selector in the UI becomes a mode switch — not just colors but the entire visual language of the interface.

---

## 5. Design Principles (Non-negotiable)

### From the Aesthetic-Integrity Stack (established March 2026)

```
1. INTEGRITY    — Every control does what it says. No beautiful lies.
2. FUNCTION     — Shows the right information. User accomplishes their task.
3. CLARITY      — Information hierarchy is clear. Eye knows where to go.
4. AESTHETICS   — Feels good. Matches the atmospheric theme.
5. MECHANICS    — Performant. Animations smooth. Scrolling buttery.
6. DELIGHT      — Surprises pleasantly. Micro-interactions feel alive.
```

Build bottom-up. Never start with delight if integrity isn't solid.

### From Diegetic Game UI

- **The UI belongs to the world.** It's the Exocortex's command console, not a webpage.
- **Texture is meaning.** Parchment means "record." CRT means "live system." Hologram means "projected intelligence." The material tells you what kind of data you're looking at.
- **Progressive disclosure, not information overload.** Show the overview first. Let the analyst drill into detail. Three levels of depth — summary → detail → raw data.
- **Data-driven atmosphere.** The particle field's energy level reflects actual agent activity. The CRT's refresh rate maps to inference speed. The interface is alive because the data is alive.
- **An effect that you notice is an effect that has failed.** The theme engine authoring principle applies here too. Atmosphere should be felt, not seen. Scanlines at 3% opacity. Grain at 2%. The feeling registers before the technique is identified.

### From the Research

- **"3D that works in 2026 does not chase the 'wow factor' — it solves comprehension and navigation problems."** (Midrocket, March 2026). Every Three.js element must serve understanding, not decoration.
- **WebGPU with automatic WebGL 2 fallback.** Design for WebGPU, degrade gracefully. One renderer swap, zero user-facing changes.
- **Performance budget.** Target 60 FPS on mid-range hardware. Particle counts, shader complexity, and postprocessing passes must be profiled and capped. The MAGI monitor ran on an RTX 3080 Ti — our panels should run on a laptop.

---

## 6. Panel Architecture

### Panel Types

| Panel | Primary Aesthetic | Data Source |
|-------|-------------------|-------------|
| **Office** | iDroid holographic | Agent cycles, wiki index, skill catalog, methodology trends |
| **Intel** | NieR codex + MAGI telemetry | Field reports, research wiki, SWARMFISH predictions |
| **System** | MAGI/HighFleet operations | Inference metrics, VRAM, thermal, model status, container health |
| **SWARMFISH** | HighFleet tactical + NieR intel | Committee deliberation, prediction tracking, confidence radar |

### Shared Components

| Component | Description | Theme-Aware |
|-----------|-------------|-------------|
| `DataCard` | Frosted/textured card with title, value, trend | Background material from theme |
| `TreeNav` | NieR-style tree navigation with expand/collapse | Typography from theme |
| `StatusBar` | iDroid-style bottom bar with TIME, model, VRAM | Color from theme palette |
| `BreadcrumbNav` | iDroid breadcrumb (OFFICE > CYCLES > #1344) | Typography + color |
| `DetailPanel` | Right-side detail view with image/model + description | Full theme treatment |
| `CycleTypeCard` | BUILD/EXPLORE/MAINTAIN with visual identity | Per-type color + icon from theme |
| `TelemetryGauge` | Circular/linear gauge for system metrics | CRT/holographic from theme tier |
| `ParticleField` | Background particle system driven by agent data | Density from theme tier 3 |

---

## 7. Implementation Approach for Kestrel

### Phase 1: Component Library (1-2 sessions)
Build the shared components (`DataCard`, `TreeNav`, `StatusBar`, etc.) as theme-aware React components that read CSS custom properties from the theme system. No Three.js yet — just clean React + Tailwind that looks good in every theme.

### Phase 2: One Panel End-to-End (2-3 sessions)
Build the **System panel** first — it's the most data-driven (inference metrics, VRAM, thermal) and maps directly to the MAGI aesthetic. Wire it to real data from the Docker container MCP. Verify against the integrity stack: every value is real, every control works.

### Phase 3: Three.js Integration (2-3 sessions)
Add the immersive layer to the System panel: CRT scanlines, hex grid background, amber glow, particle field. This is Tier 3 of the theme system. Build it as a composable layer that can be enabled/disabled per theme.

### Phase 4: Remaining Panels (3-4 sessions)
Office panel (iDroid aesthetic), Intel panel (NieR codex), SWARMFISH panel (HighFleet tactical). Each builds on the shared component library from Phase 1 and the Three.js integration from Phase 3.

### Phase 5: Theme Selector Integration
Wire the theme selector to swap the entire visual language — not just colors but materials, textures, shaders, and atmospheric effects. YoRHa → parchment. iDroid → holographic. MAGI → CRT. The selector becomes a mode switch for the entire Exocortex UI experience.

---

## 8. What "Premium" Feels Like

The test is not "does it look cool?" The test is: **does it feel like you're sitting at the command console of a sovereign AI operations center?**

The MAGI monitor makes someone monitoring CPU temperature feel like they're in NERV headquarters. The iDroid makes someone browsing a database feel like they're a field operative projecting intelligence. The NieR codex makes someone reading a report feel like they're consulting an ancient archive.

Our panels should make someone watching their agents work feel like they're operating the Exocortex. Not using a tool. Operating a system. The difference is atmosphere, texture, and the sense that every visual element was placed with intent.

The spirit is: **the Exocortex deserves an interface as thoughtful as its architecture.**

---

*"An effect that you notice is an effect that has failed."*
*— Theme Engine Authoring Guide, March 2026*
