# Beyond CSS — Phase 4 research

*Phase 4 of the UI Reference Library, started 2026-04-14.*

## Scope

Phases 1-3 of the reference library covered **CSS-only design systems** — frameworks that ship tokens and components we could grep and extract. That phase produced `exocortex.css` and proved the 9-grep methodology.

Phase 4 expands the scope to **everything else that contributes to premium web aesthetics**: shader backdrops, canvas particle systems, JavaScript animation libraries, data visualization toolkits, SVG animation techniques, and real production dashboards that demonstrate these tools composing into a coherent "feels premium" experience.

The research question stays the same: *What combinations produce interfaces that feel good to use?* But the toolbox widens to include anything that runs in a browser, not just CSS.

## Structure

This folder collects research reports, not curated tokens. Each file covers one category of technique, documents the state of the art, and ends with a concrete recommendation for the Exocortex dashboard.

| File | Topic | Key question |
|------|-------|--------------|
| [shaders.md](shaders.md) | WebGL fragment shader backdrops (mesh gradients) | What's the best path to a Linear/Stripe-style mesh gradient backdrop? |
| [particles.md](particles.md) | Canvas/particle backdrop libraries | tsParticles, Vanta, hand-rolled? Which produces "mission control" instead of "crypto landing page"? |
| [animation.md](animation.md) | JavaScript animation libraries | GSAP vs Motion One vs WAAPI vs CSS-only — when is each the right choice? |
| [dataviz.md](dataviz.md) | D3 and alternatives for dashboard charts | Best toolkit for swarmfish calibration, drift histograms, entity graphs? |
| [svg_animation.md](svg_animation.md) | SVG animation techniques | stroke-dasharray, path morphing, gauges, radar sweeps — toolkit vs hand-rolled |
| [application_sites.md](application_sites.md) | Premium production dashboards | What do Linear, Grafana, Palantir, Figma actually do that makes them feel expensive? |

## Synthesis (deferred)

After all six reports land, a `SYNTHESIS.md` will pull together:
- Cross-cutting patterns that appear in multiple categories
- The short list of tools actually worth vendoring
- Which techniques are "immediately actionable" vs "archive for future"
- Updated Phase 4 section in the main `ROADMAP.md`

The synthesis will inform a concrete prototype pass on the OSS panel — most likely starting with the shader mesh gradient backdrop (highest leverage, bounded scope) and one or two additions from the dataviz / application sites findings.

## Constraints to keep in mind

Every recommendation in these reports must respect the Exocortex stack constraints:

1. **No build system.** Single HTML file served from Flask, embedded CSS, Alpine.js via `<script src>`. Any library must work dropped in via `<script>` tag — no bundler, no transpiler, no import maps unless absolutely necessary.
2. **Alpine.js is the reactivity runtime.** Anything added must not fight Alpine's MutationObserver-based DOM tracking.
3. **Main-thread budget.** The panel already runs Alpine reactivity plus periodic `fetch()` polls. Animation libraries that starve the main thread are disqualified.
4. **Bundle size matters.** Each new dependency is served from the Flask app or a CDN. Keeping the total page weight under ~500KB is the rough target.
5. **License compatibility.** Exocortex is not currently distributed but may be in the future. Avoid GPL. Prefer MIT / BSD / Apache.
6. **Aesthetic register.** Target is dark cyan/navy "mission control" — not crypto landing, not startup marketing, not consumer app. Techniques that only produce the wrong register get noted but not adopted.

## Status

- 2026-04-14: Folder created. Six research agents launched in parallel. Reports pending.
