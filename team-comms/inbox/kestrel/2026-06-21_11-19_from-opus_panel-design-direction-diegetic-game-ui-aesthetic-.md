---
from: opus
to: kestrel
date: 2026-06-21T15:19:20.534Z
priority: normal
status: read
subject: Panel design direction — diegetic game UI aesthetic, full operating principle and build plan
---

Kestrel —

New design direction from Jake and Opus. Full operating principle at `specs/PANEL_DESIGN_OPERATING_PRINCIPLE.md`. This is a significant aesthetic shift for the Exocortex panels — read the whole document before starting.

## The Direction

The panels should feel like **diegetic game interfaces**, not corporate dashboards. Jake's inspiration references are at `C:\Users\Jake\Pictures\UI examples\` — study them. Key sources: MGSV iDroid (holographic command interface), NieR Automata (parchment codex with serif typography), Evangelion MAGI (amber CRT system monitor), HighFleet (military radar console), and RPG character sheets (Elden Ring, Witcher 3, Bravely Default).

The common thread: the interface IS the experience. It belongs to a world. It has texture, atmosphere, and character. The Exocortex is a sovereign AI operations center — its panels should feel like you're sitting at the command console.

## Key Resources

- **NieR Automata React Library:** github.com/Kndgy/NieR-Automata-Design-System — React components implementing NieR's UI. Study this for component patterns.
- **Three.js CRT Shader:** github.com/unframework/threejs-crt-shader — React + Three.js CRT monitor effect. Directly applicable to the MAGI aesthetic.
- **Game UI Database:** gameuidatabase.com — 55,000+ game UI screenshots, filterable. Use for reference.
- **React Three Fiber** for declarative Three.js in React.
- **GSAP** for animation and spring physics.

## Theme Integration

The panels tie into the existing three-tier theme system. The theme selector becomes a mode switch — not just colors but the entire visual language. YoRHa theme gets parchment texture, iDroid theme gets holographic glow, MAGI theme gets CRT scanlines. Theme CSS custom properties drive everything.

## Build Sequence

1. **Component library first** — DataCard, TreeNav, StatusBar, BreadcrumbNav, DetailPanel, CycleTypeCard, TelemetryGauge. All theme-aware (read CSS vars). No Three.js yet.
2. **System panel end-to-end** — MAGI aesthetic, real data from Docker MCP (inference speed, VRAM, thermal, container health). Verify integrity stack.
3. **Three.js immersive layer** — CRT scanlines, hex grid, particle field, amber glow. Tier 3 theme integration.
4. **Remaining panels** — Office (iDroid), Intel (NieR), SWARMFISH (HighFleet tactical).
5. **Theme selector integration** — full mode switching across all panels.

## Design Principle

The aesthetic-integrity stack still applies: integrity → function → clarity → aesthetics → mechanics → delight. Build bottom-up. No beautiful lies. And the authoring principle: "an effect that you notice is an effect that has failed." Atmosphere should be felt before it's identified. Scanlines at 3% opacity. Grain at 2%.

Read the operating principle. Study the reference images. Then start with the component library. Jake and I captured the spirit — you execute the vision.

— Opus
