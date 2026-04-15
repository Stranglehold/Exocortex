# SVG Animation — Beyond CSS

*A toolkit report for the Exocortex mission-control dashboard. Static HTML + Alpine.js + Flask. No build system, no React.*
*Researched 2026-04-14.*

---

## 1. Core SVG Animation Techniques

### 1.1 stroke-dasharray + stroke-dashoffset (the draw-in trick)

The single most useful SVG animation technique. Works in pure CSS, no library required.

**How it works.** SVG strokes can be rendered as a dash pattern via `stroke-dasharray`. If you set the dash length equal to the path's total length and the gap equal to the path's total length, you get one long dash followed by an equally long gap. Then `stroke-dashoffset` shifts where that pattern starts along the path. At `offset = pathLength`, the gap is covering the entire visible path — it looks invisible. At `offset = 0`, the dash has slid into place and the path appears fully drawn. Animating `stroke-dashoffset` from `pathLength` to `0` produces a "drawing itself" animation.

**Math.** The path length is measured in user units along the curve. For a straight line from (0,0) to (100,0), length is 100. For a circle, it's `2 * π * r`. For an arbitrary path (`<path d="...">`), you cannot compute it by hand reliably — use the DOM API:

```javascript
const path = document.querySelector('#my-path');
const length = path.getTotalLength();  // works on <path>, <line>, <polyline>, <polygon>, <circle>, <ellipse>, <rect>
```

**Concrete example — draw a 100px horizontal line over 2 seconds:**

```html
<svg width="120" height="20">
  <line x1="10" y1="10" x2="110" y2="10"
        stroke="#4dd0e1" stroke-width="2"
        stroke-dasharray="100"
        stroke-dashoffset="100">
  </line>
</svg>

<style>
line {
  animation: draw 2s ease-out forwards;
}
@keyframes draw {
  to { stroke-dashoffset: 0; }
}
</style>
```

**Concrete example — draw an arbitrary path over its natural length:**

```html
<svg width="200" height="200" viewBox="0 0 200 200">
  <path id="curve"
        d="M 10 100 Q 100 10, 190 100 T 370 100"
        fill="none" stroke="#4dd0e1" stroke-width="2"/>
</svg>

<script>
const path = document.getElementById('curve');
const len = path.getTotalLength();
path.style.strokeDasharray = len;
path.style.strokeDashoffset = len;
// Force a reflow so the browser picks up the starting state, then animate.
path.getBoundingClientRect();
path.style.transition = 'stroke-dashoffset 2s ease-out';
path.style.strokeDashoffset = '0';
</script>
```

**Gotcha — `pathLength` attribute.** SVG lets you normalize lengths by setting `pathLength="100"` on the element. Then you can use `stroke-dasharray="100"` regardless of the actual geometry. This is the cleanest approach when you don't want to measure at runtime, and it composes well with CSS percentages conceptually.

**Gotcha — non-uniform scaling.** If the SVG is scaled non-uniformly via `transform` or a non-square viewBox with `preserveAspectRatio="none"`, the visual stroke length will differ from `getTotalLength()`'s value. Keep scaling uniform when using this technique.

**Gotcha — `vector-effect="non-scaling-stroke"`.** If you set this to keep stroke width constant under zoom, the dash pattern scales with the path but the stroke doesn't, which can look odd at extreme zoom levels. Usually fine for dashboards.

### 1.2 Path morphing (animating `d`)

CSS cannot interpolate the `d` attribute. The browser sees `d="M 0 0 L 100 100"` and `d="M 0 0 Q 50 0 100 100"` as unrelated strings. You need one of:

**SMIL `<animate>`.** Native browser support. Can interpolate `d` between two values if the paths have the same number and type of segments. Fragile — any structural mismatch and it silently fails or looks wrong.

**Flubber** (~20 KB min+gz, MIT). Veltman's library, specifically designed to interpolate between arbitrary SVG paths with different segment counts. It normalizes both paths to the same topology, then you get an interpolator function: `const interp = flubber.interpolate(pathA, pathB); requestAnimationFrame(t => path.setAttribute('d', interp(t/1000)));`. This is the gold standard for morphing dissimilar shapes. Maintained lightly — last meaningful release was years ago, but the library is feature-complete and the math doesn't rot.

**GSAP MorphSVGPlugin** (commercial, Club GreenSock required, ~$99/year for business tier). Highest quality morphs, handles edge cases Flubber doesn't, integrates with the GSAP timeline. Overkill unless you're doing heavy motion graphics.

**anime.js path animation** (~17 KB min+gz, MIT). Has a `morphTo`-style feature via its timeline. Less robust than Flubber for topology-mismatched paths but works for simple cases. anime.js itself went through a maintenance lull and was forked; the `animejs/anime` repo is active again as of 2024-2025.

**Raw requestAnimationFrame + manual interpolation.** Viable only if both paths are structured as the same sequence of commands with the same number of points. Then you just lerp each coordinate. Tedious but zero-dependency.

**Recommendation for the dashboard.** You probably don't need morphing. If you do — say, a gauge needle transitioning between two visual states — you can almost always achieve it with `transform: rotate()` instead.

### 1.3 SMIL — is it dead in 2026?

No, and the story is clearer than it was five years ago. Chrome deprecated SMIL in 2015, then un-deprecated it in 2016 after Web Animations API fell behind. Since then SMIL has been quietly supported in all modern browsers except IE. The one hard exception is that SMIL was never implemented in IE at all.

**Current status:** SMIL works in Chrome, Firefox, Safari, and all Chromium-derived browsers. It is not going away. There was a push to replace it with Web Animations API (which is excellent) but SMIL's feature set — motion along a path, synchronized timelines, begin/end event syncing — was never fully ported, so SMIL persists.

**When to use SMIL.** When you want a self-contained, copy-pasteable animated SVG (think: an animated loading spinner as a single `.svg` file you drop into an `<img>` tag). SMIL animations play even when the SVG is loaded as an image, where CSS and JS cannot run. For dashboard use where you already have JS on the page, SMIL offers nothing you can't do better with CSS + Web Animations API + `requestAnimationFrame`.

**Example — pulsing circle in pure SMIL:**

```html
<svg width="100" height="100">
  <circle cx="50" cy="50" r="10" fill="#4dd0e1">
    <animate attributeName="r" values="10;30;10" dur="2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;0;1" dur="2s" repeatCount="indefinite"/>
  </circle>
</svg>
```

### 1.4 CSS transforms on SVG elements

Modern browsers support CSS `transform`, `transform-origin`, `transform-box`, and `transition` on SVG elements. This was broken in Safari until around 2019; now it's reliable across all current browsers.

**What works:**
- `transform: rotate(deg)`, `scale(x, y)`, `translate(x, y)`, `skew()`, `matrix()`
- `transform-origin` (with the gotcha below)
- `transition` on transform, opacity, fill, stroke, stroke-width, stroke-dashoffset
- `@keyframes` animations targeting any of the above

**What doesn't work (or is flaky):**
- Animating `d`, `points`, `cx`, `cy`, `x`, `y`, `width`, `height` via CSS transitions. These are SVG attributes, not CSS properties, and CSS transitions don't touch them. **Exception:** Chrome and Firefox added CSS-transition support for presentation attributes like `cx` and `r` around 2020-2021, but Safari was late and edge cases still exist. Safest to animate these via JS or SMIL.
- `transform` on `<g>` elements works, but older browsers (Edge Legacy, pre-2019 Safari) had bugs. Not a concern in 2026.

### 1.5 transform-origin gotchas on SVG

This is the single most confusing thing about SVG transforms.

**The problem.** By default, CSS `transform-origin` on an SVG element is computed relative to the element's bounding box **in the user coordinate system of the SVG root**, not relative to the element itself. So if you have a `<rect x="100" y="100" width="50" height="50">` and write `transform-origin: center; transform: rotate(45deg);`, the rectangle rotates around the center of the SVG viewport, not around its own center. It goes flying offscreen.

**The fix.** Set `transform-box: fill-box;` on the element. This redefines `transform-origin` to be relative to the element's own bounding box. Then `transform-origin: center` (or `50% 50%`) means the actual center of the element.

```css
.gauge-needle {
  transform-box: fill-box;
  transform-origin: center;
  transition: transform 600ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

**Browser support for `transform-box`.** All modern browsers, solid since ~2020. In 2026 you can rely on it.

**Alternative fix for older browsers or when you want absolute precision.** Compute the origin in user units yourself: `transform-origin: 125px 125px;` (the absolute center of a rect at x=100, y=100, w=50, h=50). Works everywhere, forever. More verbose.

**SVG attribute transforms (not CSS).** If you write `<g transform="rotate(45 125 125)">` — rotating 45 degrees around the point (125, 125) — the origin is baked into the transform. This predates CSS-on-SVG support and still works. Useful when you can't control the CSS or when you want to keep the transform inside the SVG file itself.

### 1.6 Animating viewBox for pan/zoom

`viewBox` is an attribute, not a CSS property, so CSS transitions don't apply. Animate it with JS or SMIL.

```javascript
function animateViewBox(svg, from, to, duration) {
  const start = performance.now();
  function step(now) {
    const t = Math.min((now - start) / duration, 1);
    const eased = t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2)/2;  // easeInOutQuad
    const vb = from.map((f, i) => f + (to[i] - f) * eased);
    svg.setAttribute('viewBox', vb.join(' '));
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

animateViewBox(mySvg, [0, 0, 200, 200], [50, 50, 100, 100], 800);
```

Use this for map-like zoom effects, camera follows, and focus transitions on a data visualization.

---

## 2. Specific Effects for Mission Control

### 2.1 Animated gauge / dial

Two components: a background arc (full range) and a foreground arc (current value) that grows, plus an optional needle.

**Simplest implementation.** Two `<circle>` elements with `stroke-dasharray`, or two `<path>` arcs. The foreground stroke uses `stroke-dashoffset` to show "current / max" of its circumference.

```html
<svg width="200" height="200" viewBox="0 0 200 200">
  <!-- background ring -->
  <circle cx="100" cy="100" r="80"
          fill="none" stroke="#1a2332" stroke-width="12"/>
  <!-- value ring -->
  <circle id="gauge-value" cx="100" cy="100" r="80"
          fill="none" stroke="#4dd0e1" stroke-width="12"
          stroke-dasharray="502.65"
          stroke-dashoffset="502.65"
          stroke-linecap="round"
          transform="rotate(-90 100 100)"/>
  <!-- needle -->
  <line id="gauge-needle" x1="100" y1="100" x2="100" y2="30"
        stroke="#fff" stroke-width="2"
        style="transform-box: fill-box; transform-origin: center;"/>
</svg>

<script>
const CIRC = 2 * Math.PI * 80;  // 502.65
const valueRing = document.getElementById('gauge-value');
const needle = document.getElementById('gauge-needle');
valueRing.style.transition = 'stroke-dashoffset 600ms cubic-bezier(0.4,0,0.2,1)';
needle.style.transition = 'transform 600ms cubic-bezier(0.4,0,0.2,1)';

function setGauge(pct) {  // 0..1
  valueRing.style.strokeDashoffset = CIRC * (1 - pct);
  needle.style.transform = `rotate(${pct * 270 - 135}deg)`;  // 270° sweep
}

setGauge(0.72);
</script>
```

Two details worth noting. `stroke-linecap="round"` gives the ring rounded ends, which looks premium. The `transform="rotate(-90 100 100)"` on the ring starts the arc at 12 o'clock instead of 3 o'clock (SVG's default angular zero).

If you want a partial arc (say 270° sweep, not a full circle), compute the desired arc length and use it as the dasharray max: `stroke-dasharray="${arcLen} ${CIRC}"`.

### 2.2 Sweeping radar line with trail fade

The radar sweep is a rotating line with a trailing fade. Two approaches:

**Approach A — CSS rotate + SVG linearGradient for the trail.**

```html
<svg width="200" height="200" viewBox="-100 -100 200 200">
  <defs>
    <linearGradient id="sweep-grad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#4dd0e1" stop-opacity="0"/>
      <stop offset="100%" stop-color="#4dd0e1" stop-opacity="1"/>
    </linearGradient>
    <clipPath id="radar-clip">
      <circle cx="0" cy="0" r="90"/>
    </clipPath>
  </defs>
  <circle cx="0" cy="0" r="90" fill="#0a1520" stroke="#1a2332"/>
  <g id="sweep" style="transform-origin: center;">
    <path d="M 0 0 L 90 0 A 90 90 0 0 0 45 -78 Z" fill="url(#sweep-grad)"/>
  </g>
</svg>

<style>
#sweep {
  animation: rotate 4s linear infinite;
}
@keyframes rotate {
  to { transform: rotate(360deg); }
}
</style>
```

The wedge is a pie slice; the gradient fades it from opaque (at the leading edge) to transparent (trailing). The whole group rotates. Uses the `viewBox="-100 -100 200 200"` trick so the origin is (0,0) at the center, which makes the path math cleaner.

**Approach B — multiple lines with staggered opacities.** Render 20 lines at angles `θ, θ-1°, θ-2°, ...` with decreasing opacity, animate `θ` in JS. More expensive, looks more like an old CRT radar. Overkill for most uses.

**For blips on the radar.** Place `<circle>` elements at (x, y) computed from your data, and use the pulse/ping technique below (§2.5).

### 2.3 Animated sparkline

A time-series line chart where new data slides in from the right and old data falls off the left.

**Simplest approach — redraw the path on every update.** Keep the last N data points in a JS array. When a new point arrives, shift the oldest off and append the new one. Rebuild the `d` attribute as a polyline. Animate the `viewBox` or the path's `transform` to slide left by one data unit.

```html
<svg id="spark" width="200" height="40" viewBox="0 0 100 40" preserveAspectRatio="none">
  <path id="spark-path" fill="none" stroke="#4dd0e1" stroke-width="1.5"/>
</svg>

<script>
const MAX_POINTS = 50;
const data = [];
const path = document.getElementById('spark-path');

function addPoint(y) {
  data.push(y);
  if (data.length > MAX_POINTS) data.shift();
  const d = data.map((v, i) => `${i === 0 ? 'M' : 'L'} ${i * (100 / (MAX_POINTS - 1))} ${40 - v * 40}`).join(' ');
  path.setAttribute('d', d);
}

setInterval(() => addPoint(Math.random()), 500);
</script>
```

The "sliding" effect is subtle but present — because the x-axis is indexed 0..N, new points always appear at the right edge and old ones fall off. For a smoother visual slide, animate a `transform: translateX(-Δ)` over the interval between updates, then reset on point add. Most dashboards don't bother; the natural rhythm of updates is enough.

**Alternative — use a library.** D3 handles this beautifully with its enter/update/exit pattern, but D3 is ~80 KB min+gz and wildly overkill if you're just drawing sparklines. **Chartist.js** (~10 KB) and **uPlot** (~40 KB) are both small and specifically good at fast time-series redraws. uPlot uses canvas (not SVG) but is the fastest small charting library by a wide margin.

### 2.4 Connection line draw-in

When new data arrives and you want to draw a line from a source to a target (e.g., a network graph, a data flow visualization), use the stroke-dasharray trick from §1.1. Each new line element gets created with `stroke-dasharray = length, stroke-dashoffset = length`, then transitions to offset 0 over 400-800ms. That's it — this is the canonical use case.

```javascript
function drawConnection(svg, x1, y1, x2, y2) {
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  line.setAttribute('x1', x1);
  line.setAttribute('y1', y1);
  line.setAttribute('x2', x2);
  line.setAttribute('y2', y2);
  line.setAttribute('stroke', '#4dd0e1');
  line.setAttribute('stroke-width', '1.5');
  svg.appendChild(line);

  const len = line.getTotalLength();
  line.style.strokeDasharray = len;
  line.style.strokeDashoffset = len;
  line.getBoundingClientRect();  // force reflow
  line.style.transition = 'stroke-dashoffset 600ms ease-out';
  line.style.strokeDashoffset = '0';
}
```

For curved connections (think a cable between two nodes with a natural bow), replace `<line>` with `<path d="M x1 y1 Q cx cy x2 y2"/>` where `(cx, cy)` is a control point. Everything else is identical.

### 2.5 Pulse / ping indicator

The "radar blip" / Google Maps "you are here" expanding circle.

**Pure SVG + CSS:**

```html
<svg width="40" height="40">
  <circle cx="20" cy="20" r="4" fill="#4dd0e1"/>
  <circle cx="20" cy="20" r="4" fill="none" stroke="#4dd0e1" stroke-width="1" class="ping"/>
</svg>

<style>
.ping {
  transform-box: fill-box;
  transform-origin: center;
  animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;
}
@keyframes ping {
  0%   { transform: scale(1); opacity: 1; }
  80%  { transform: scale(4); opacity: 0; }
  100% { transform: scale(4); opacity: 0; }
}
</style>
```

Tailwind's `animate-ping` utility is literally this. For multiple simultaneous pings with staggered starts, add `animation-delay` on each copy.

---

## 3. The stroke-dasharray Trick — Deep Dive

Already covered in §1.1, but one more level of depth:

**Dasharray as a pattern, not a length.** `stroke-dasharray="10 5 2 5"` means: 10-unit dash, 5-unit gap, 2-unit dash, 5-unit gap, then repeat. The draw-in trick is a special case where the pattern is `[total, total]` — one dash of full length, one gap of full length, shifted by the offset.

**Why the offset direction matters.** `stroke-dashoffset` is positive in the direction the path is drawn (from start to end). For a line from A to B, offset > 0 pushes the pattern toward B. Animating from `+length` to `0` means the dash slides in from A to B — the line appears to draw from start to end. Animating from `-length` to `0` draws it from end to start. This is sometimes what you want (e.g., an arrow pointing from B back to A that draws toward A).

**Easing matters more than you'd think.** `linear` looks robotic. `ease-out` (the default `cubic-bezier(0, 0, 0.58, 1)`) looks natural for draw-in — the line decelerates as it completes. For "launch" animations, `cubic-bezier(0.4, 0, 0.2, 1)` (Material standard) feels crisp.

**Combining with opacity.** For a draw-in-then-fade-out (a connection appears, then becomes ambient), chain two transitions:

```css
.connection {
  transition:
    stroke-dashoffset 600ms ease-out,
    opacity 400ms ease-in 600ms;  /* opacity starts after draw completes */
}
```

**Dashed draw-in.** Nothing stops you from having a visible dash pattern *and* animating the draw. Use `stroke-dasharray="5 3"` for a dashed style, then... wait, this breaks the trick. The draw-in requires the full-length dash pattern. To get both a dashed visual style and a draw-in animation, use two overlaid strokes: a solid one that animates in, then swap it for a dashed one. Or use SMIL, which can animate `stroke-dasharray` values directly. Or just accept that draw-in lines are solid.

---

## 4. Libraries

| Library | Size (min+gz) | License | Maintenance | Niche |
|---|---|---|---|---|
| **GSAP core** | ~23 KB | Free for most uses (new 2024 license) | Active | General animation, not SVG-specific |
| **GSAP DrawSVG** | +3 KB | Club GreenSock ($99/yr business) | Active | Perfect stroke-dasharray automation |
| **GSAP MorphSVG** | +8 KB | Club GreenSock | Active | Best-in-class path morphing |
| **Vivus** | ~9 KB | MIT | Light (feature complete) | Path drawing only, dead simple |
| **Snap.svg** | ~75 KB | Apache-2.0 | **Abandoned** since ~2017 | — |
| **SVG.js** (v3) | ~20 KB | MIT | Active | Full SVG DSL for creation/manipulation |
| **anime.js** | ~17 KB | MIT | Active (revived) | General animation, good SVG support |
| **Flubber** | ~20 KB | MIT | Dormant but complete | Path morphing between dissimilar shapes |
| **Lottie-web** | ~250 KB | MIT | Active (Airbnb/LottieFiles) | After Effects exports |
| **Two.js** | ~75 KB | MIT | Active | Drawing API over SVG/Canvas/WebGL |

**Notes on each:**

- **GSAP** — In early 2024, GSAP was acquired by Webflow and the license was loosened significantly. Core GSAP is now free for commercial use including many cases that previously required Club GreenSock. DrawSVG and MorphSVG are still paid plugins. For the Exocortex dashboard, GSAP core would be the closest thing to a "do everything animation" dependency, but it's 23 KB you almost certainly don't need.

- **Vivus** — Does exactly one thing (path drawing) and does it well. If you want sequential/delayed/oneByOne path-drawing effects across many SVG paths and don't want to hand-roll the orchestration, Vivus is the smallest thing that gets you there. For a single line draw-in, it's overkill — CSS is 5 lines.

- **Snap.svg** — Abandoned. Last meaningful release 2017. Adobe moved on. Don't vendor it.

- **SVG.js** — Still alive, still good. It's a fluent API for building and animating SVG imperatively (`SVG().addTo('#app').rect(100, 100).fill('#f06')`). Use it if you're procedurally generating SVG and find the raw DOM API painful. For Alpine.js + server-rendered SVG, you don't need it.

- **anime.js** — Had a maintenance lull from 2020-2023 but is active again. Good for general animation with decent SVG support (line drawing, morphing simple paths). 17 KB is middleweight. If you find yourself wanting a timeline API and don't want GSAP, this is the alternative.

- **Flubber** — The only reason to vendor this is if you genuinely need to morph between two structurally different SVG paths and can't achieve the visual effect with rotation/scale. Rare in dashboard UI.

- **Lottie** — Designed for designers to export After Effects compositions and have them play in the browser. 250 KB runtime. Completely overkill for programmatically-driven dashboard UI. Use it if a designer hands you a `.json` lottie file and you want it to play. Otherwise skip.

- **Two.js** — Drawing library that abstracts over SVG/Canvas/WebGL renderers. Nice API but adds a layer you don't need if you're comfortable with raw SVG.

---

## 5. SVG vs Canvas vs CSS — Decision Tree

**Use CSS when:**
- The effect is on rectangular UI elements (cards, panels, buttons)
- You're transforming, fading, or sliding existing DOM
- You don't need to draw custom shapes
- You want the browser to handle everything with zero JS overhead
- Accessibility matters (CSS-animated DOM inherits semantics)

**Use SVG when:**
- You have many individually-interactive elements (each is a DOM node, can receive events, can be styled)
- Element count is low-to-moderate (< ~500 elements animating simultaneously)
- You need crisp vector rendering at any zoom level
- You're drawing shapes that don't map to CSS boxes (arcs, curves, polygons, custom paths)
- You want accessibility (each SVG element can have `<title>`, ARIA, etc.)
- Data-driven visualization where each datum is a discrete visual object
- You want to author effects declaratively in the markup

**Use Canvas when:**
- Element count is high (thousands of particles, dense scatter plots, terrain)
- You need pixel-level control (custom blending, shaders via WebGL)
- You're rendering continuous fields (heatmaps, flow fields, audio waveforms)
- You don't need to hit-test individual elements (or you're willing to implement hit-testing yourself)
- Maximum performance matters more than DOM integration

**For the Exocortex dashboard specifically.** Most of what you're building — gauges, rings, sparklines, connection diagrams, radar sweeps, status indicators — is textbook SVG territory. Low element counts, data-driven, each element is logically distinct, you want to style them from CSS, you want them to scale cleanly. Canvas would only make sense if you later added a dense visualization like a particle field, a WebGL terrain, or a chart with 10,000+ points. Even then, uPlot (canvas-based but with a tiny API) or a dedicated canvas component in one corner of the dashboard would be the right move, not a wholesale switch.

---

## 6. Concrete Recommendation for Exocortex

**Bring in nothing. Use raw SVG + CSS + a little vanilla JS.**

Reasoning:

1. **The stroke-dasharray trick is ~10 lines of CSS + one `getTotalLength()` call.** It covers gauges, rings, connection draw-ins, and path reveals. That's 80% of your animation budget right there.

2. **Alpine.js is already on the page.** You can drive reactive SVG updates via `x-bind` on `stroke-dashoffset`, `transform`, `cx`/`cy`, etc. No need for a DOM manipulation library when Alpine already does the bindings.

3. **The heavy techniques (morphing, timelines, synchronized multi-element choreography) are not what dashboards actually need.** Dashboards need smooth value transitions, periodic pulses, and occasional draw-in reveals. All achievable in CSS.

4. **Adding GSAP is 23 KB + a mental model to teach yourself and future contributors.** The amount of animation work you'd need to justify that is more than a dashboard produces.

5. **The one thing raw SVG+CSS can't do elegantly is path morphing.** If a use case arrives — say, a topology diagram that reshapes when the graph structure changes — reach for Flubber at that point. Keep it as a known fallback, not a default dependency.

6. **For sparklines, if hand-rolled SVG feels like it's getting slow (> ~100 points, > 10 Hz updates), drop in uPlot in just that component.** uPlot is ~40 KB and is one of the fastest charting libraries in existence. It's canvas, not SVG, which fits the "right tool for the job" principle — dense real-time charts are canvas territory.

**Concrete toolkit:**

- **Baseline:** Hand-rolled SVG in templates, CSS animations for pulses/spins, `stroke-dasharray` for draw-ins, `transform` for rotations, Alpine's `x-bind` for reactive updates.
- **Utility function:** A tiny shared `drawIn(element, duration)` helper that does the `getTotalLength` + dasharray + offset + transition dance. Five lines. Put it in your main JS file.
- **Escape hatches (don't vendor until needed):**
  - uPlot — if a chart component gets slow
  - Flubber — if a morph becomes necessary
  - anime.js — if you end up needing timeline orchestration across many elements

Everything in the hand-rolled approach composes with CSS, with Alpine, and with server-side rendering. Nothing breaks if JavaScript fails — the SVG is in the DOM, visible, accessible. That's the right foundation for a "mission control" aesthetic where reliability is part of the look.

---

## Quick Reference — The Three Techniques You'll Use 80% of the Time

**1. Draw in a line:**
```javascript
const len = path.getTotalLength();
path.style.cssText = `stroke-dasharray: ${len}; stroke-dashoffset: ${len}; transition: stroke-dashoffset 600ms ease-out;`;
requestAnimationFrame(() => path.style.strokeDashoffset = '0');
```

**2. Rotate something around its own center:**
```css
.spinner {
  transform-box: fill-box;
  transform-origin: center;
  animation: spin 2s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
```

**3. Pulse/ping:**
```css
.ping {
  transform-box: fill-box;
  transform-origin: center;
  animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;
}
@keyframes ping {
  0%  { transform: scale(1); opacity: 1; }
  80%,100% { transform: scale(4); opacity: 0; }
}
```

Master these three, add `requestAnimationFrame` for the cases where CSS can't reach (animating `d`, `viewBox`, `cx`/`cy` reliably across browsers), and you have a complete animation toolkit for mission-control UI with zero library dependencies.
