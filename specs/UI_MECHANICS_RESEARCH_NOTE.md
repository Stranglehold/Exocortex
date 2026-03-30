# UI_MECHANICS_RESEARCH_NOTE.md
# Web UI Implementation Mechanics: A Nuts-and-Bolts Reference

*Companion to AESTHETICS_DESIGN_BRIEF.md (which governs feel) and THEME_ENGINE_SPEC_L3.md (which governs the theme system). This document governs how things are actually built — the implementation layer beneath the design layer. Every principle here is traced to a source, a repo, or a measurable browser behavior.*

*Researched and written March 2026. Motivated by the theme system work: we know what we want the interface to feel like. This document establishes how to achieve that technically.*

---

## 1. The Browser Rendering Pipeline — Foundation of Every Performance Decision

Every animation and visual effect decision traces back to four browser pipeline stages:

```
JavaScript → Style → Layout → Paint → Composite
```

Each stage you skip per animation frame is a direct performance win. The practical tier list:

| Tier | Properties | Triggers | Thread | Cost |
|------|-----------|----------|--------|------|
| **S** | `transform`, `opacity` | Composite only | GPU (compositor thread) | ~Free |
| **S** | `filter`, `clip-path` | Composite only | GPU | ~Free |
| **A** | JS writes to compositor props via rAF | Skips paint | Main, then GPU | Good |
| **B** | FLIP layout animations | One layout measurement, then compositor | Main + GPU | Acceptable |
| **C** | `background-color`, `border-radius`, CSS custom properties | Paint | Main | Medium cost |
| **D** | `width`, `height`, `margin`, `top`, `left` | Layout + Paint | Main | Expensive |
| **F** | Reading layout inside a write loop | Style/layout thrashing | Main | Catastrophic |

**The golden rule**: animate `transform` and `opacity` only. These properties skip Layout and Paint entirely and go straight to Composite — they run on the GPU on a separate thread. Heavy JavaScript cannot jank them. This is not a best practice suggestion. It is a hard capability boundary of how browsers work.

**`will-change: transform`** promotes an element to its own GPU layer. The browser usually handles this automatically for actively-animating transforms. Use it explicitly and sparingly — each layer consumes GPU VRAM, and over-promotion causes memory pressure on lower-end hardware.

**Style/layout thrashing** (F-tier) is the most common performance failure in custom UI code:
```js
// Catastrophic: read forces layout recalc, write invalidates it, repeat
elements.forEach(el => {
    const height = el.offsetHeight;       // READ: forces synchronous layout
    el.style.height = height + 10 + 'px'; // WRITE: invalidates layout for next read
});

// Correct: batch all reads, then all writes
const heights = elements.map(el => el.offsetHeight);     // all reads
elements.forEach((el, i) => el.style.height = heights[i] + 10 + 'px'); // all writes
```

**CSS custom properties** are a trap at scale. Updating one inherited CSS variable triggers paint for every element that inherits it. One production site measured 8ms/frame updating a single CSS variable across 1300+ elements. Scope custom property updates tightly, or animate their consuming `transform`/`opacity` properties directly instead.

Source: [motion.dev/blog/web-animation-performance-tier-list](https://motion.dev/blog/web-animation-performance-tier-list), [developers.google.com/web/fundamentals/performance/rendering](https://developers.google.com/web/fundamentals/performance/rendering).

---

## 2. How Animation Engines Work

### 2.1 The Global Ticker Pattern (GSAP)

GSAP maintains **one `requestAnimationFrame` loop** that drives all active tweens. Not one rAF per animation. Every new tween registers into a shared queue. Each frame:

1. Compute `progress = elapsed / duration` (clamped 0→1)
2. Run through easing function: `easedProgress = ease(progress)`
3. Interpolate each animated property: `value = start + (end - start) * easedProgress`
4. Write directly to DOM via `.style`

The performance consequence: the rAF overhead is constant regardless of how many tweens are active. 1 tween or 200 tweens — one rAF callback per frame.

GSAP's `x`, `y`, `scale`, `rotation`, `skewX/Y` properties all map to `transform` under the hood. You never write `left: 200px`. You write `x: 200` and GSAP writes `transform: translateX(200px)`. The GPU path is automatic.

`ScrollTrigger` converts scroll position to a 0→1 progress value, then drives tweens with that value instead of time. The tween system doesn't know or care whether it's being driven by a clock or a scroll position.

Source: [gsap.com/docs/v3/GSAP](https://gsap.com/docs/v3/GSAP/), GSAP source at [github.com/greensock/GSAP](https://github.com/greensock/GSAP).

### 2.2 Spring Physics

Spring-based motion (react-spring, Framer Motion) uses Hooke's Law integrated numerically per frame:

```
F_spring  = -k * displacement          // restoring force
F_damping = -d * velocity              // resistance
acceleration = (F_spring + F_damping) / mass
velocity += acceleration * deltaTime
position += velocity * deltaTime
```

Parameters: `k` = stiffness (how strong the pull), `d` = damping (how much resistance), `m` = mass.

**Springs have no fixed duration.** They run until velocity and displacement fall below a convergence threshold (typically 0.001 units). This is what makes spring-based animation categorically different from CSS easing curves:

- **CSS `transition`**: fixed duration, easing curve, cannot be interrupted cleanly
- **Spring**: runs until settled, can be interrupted mid-animation and retargeted while carrying current velocity

When you change a target mid-spring, the current velocity carries into the new direction. This is the physical basis for UI motion that reads as "natural" — the animation doesn't snap to a new curve, it flows through the change. This behavior is physically impossible to replicate with `transition-timing-function`.

Source: [blog.maximeheckel.com/posts/the-physics-behind-spring-animations](https://blog.maximeheckel.com/posts/the-physics-behind-spring-animations/), [pmndrs/react-spring](https://github.com/pmndrs/react-spring).

### 2.3 FLIP — Layout Animation Without Layout Cost

Framer Motion's layout animations use FLIP (First, Last, Inverse, Play) to animate expensive layout changes using cheap compositor operations:

1. **First**: `getBoundingClientRect()` before the change — store position and size
2. **Last**: `getBoundingClientRect()` after React re-renders with new layout
3. **Inverse**: compute the position delta; apply a `transform` that undoes the change — the element now visually appears in its old position despite having re-rendered
4. **Play**: animate the transform from the inverted state back to `translate(0,0) scale(1,1)`

The DOM layout change happens at full cost once. FLIP hides the jump with a compositor-only transform animation. The result looks like the element traveled smoothly from old position to new position.

**Child correction**: when a parent scales, children appear distorted (they inherit the scale). Framer Motion applies an inverse scale to each child every frame: `childScale = 1 / parentScale`. This must be recalculated per frame, not pre-computed.

`transform-origin` must be `top left` so that the transform vector aligns with the measured distances from `getBoundingClientRect()`.

Source: [nan.fyi/magic-motion](https://nan.fyi/magic-motion), Framer Motion source at [github.com/framer/motion](https://github.com/framer/motion).

---

## 3. How Specific High-Profile UIs Are Built

### 3.1 Stripe's Animated Gradient

Not CSS. Not a video. A `<canvas>` element with a WebGL context.

The container div uses `transform: skewY(-12deg)` with `overflow: hidden` to create the diagonal edge. The canvas itself is a full rectangle inside it.

**Vertex shader**: defines a mesh of vertices displaced by a sinusoidal function — `sin(position + u_time * speed)`. The displacement creates the "moving fabric" topology.

**Fragment shader**: uses Fractal Brownian Motion (fBm) for color — layered octaves of Simplex noise, each octave at twice the frequency and half the amplitude:
```glsl
float fbm(vec2 p) {
    float value = 0.0;
    float amplitude = 0.5;
    for (int i = 0; i < 6; i++) {
        value += amplitude * noise(p);
        p *= 2.0;           // double frequency
        amplitude *= 0.5;   // halve amplitude
    }
    return value;
}
```

One uniform `u_time` increments each rAF frame. The CPU does nothing after initialization. The GPU handles all math at 60fps.

Stripe wrote an internal ~800-line class called `MiniGL` — a minimal WebGL wrapper without Three.js. The reverse-engineered implementation: [bram.us/2021/10/13/how-to-create-the-stripe-website-gradient-effect](https://www.bram.us/2021/10/13/how-to-create-the-stripe-website-gradient-effect/).

### 3.2 Linear's Application UI

Source: [pustelto.com/blog/reverse-engineer-linear-1-header](https://pustelto.com/blog/reverse-engineer-linear-1-header/).

Key implementation patterns:
- **MobX** for reactive state — small context-scoped stores, not global state. Granular reactivity without full component re-renders.
- **`ResizeObserver` everywhere** instead of CSS media queries. Components measure their own available width and reconfigure themselves dynamically. This is why Linear's UI reflows gracefully at any viewport size without breakpoint jumps.
- **Overflow tabs** use `visibility: hidden` + `overflow: hidden`, not `display: none`. Elements that don't fit are hidden but still occupy DOM space — avoids reflow, preserves layout measurement.
- **`useLayoutEffect`** fires synchronously after DOM mutation and before the browser paints. Used for measurement-before-render operations (FLIP setup, overflow detection) where a `useEffect` would show a flash of intermediate state.

### 3.3 Vercel's Design Engineering Approach

Source: [vercel.com/blog/design-engineering-at-vercel](https://vercel.com/blog/design-engineering-at-vercel).

Animation preference hierarchy (explicit, enforced):
1. **CSS** — for simple transitions, no JS cost
2. **Web Animations API** — for controlled, interruptible animations with JS access to playback state
3. **JS animation libraries** — only when the above are insufficient

Vercel explicitly avoids `transition: all` — every animated property is enumerated. Unspecified properties that happen to change (from a class toggle, from a state update) should not animate unexpectedly.

Three.js for 3D elements, GLSL shaders for visual effects, Blender for static 3D assets. Prototypes built in code, not Figma.

---

## 4. Scroll-Driven Animations — The Native Implementation

CSS-native since 2024. Now baseline across Chrome 115+, Safari 18+, Firefox 144+.

```css
@keyframes fade-up {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}

.element {
    animation: fade-up linear both;
    animation-timeline: view();
    animation-range: entry 0% entry 60%;
}
```

- **`animation-timeline: scroll()`** — ties animation progress to the scroll position of the nearest scrollable ancestor
- **`animation-timeline: view()`** — ties animation progress to how much of this element is visible in the viewport
- **`animation-range`** — defines which portion of the scroll/visibility range drives the full 0→100% of the animation

These run on the **compositor thread** — no JavaScript, no main thread involvement, no `IntersectionObserver` polling. Measured CPU cost: ~2% vs ~50% for equivalent rAF-based JS scroll handlers.

The JavaScript `ViewTimeline` API gives programmatic access to the same mechanism:
```js
const timeline = new ViewTimeline({ subject: element, axis: 'block' });
element.animate(keyframes, { timeline, rangeStart: 'entry 0%', rangeEnd: 'entry 60%' });
```

The GSAP/ScrollTrigger approach still covers cases where you need complex scrub logic, velocity-based triggers, or support for older browsers. But for straightforward scroll reveals, CSS-native is now the correct default.

Source: [developer.chrome.com/docs/css-ui/scroll-driven-animations](https://developer.chrome.com/docs/css-ui/scroll-driven-animations), [smashingmagazine.com/2024/12/introduction-css-scroll-driven-animations](https://www.smashingmagazine.com/2024/12/introduction-css-scroll-driven-animations/).

---

## 5. WebGL UI Architecture

For effects beyond what CSS can produce — particle systems, shader-based color grading, 3D scenes, procedural backgrounds — the architecture is:

### 5.1 Layer Architecture

A `<canvas>` element is either:
- **Full-page background**: `position: fixed; inset: 0; z-index: -1; pointer-events: none`
- **Synced to a DOM element**: `position: absolute` inside a container, using `getBoundingClientRect()` each frame to match an element's position

The render loop is a `requestAnimationFrame` callback:
```js
function render(timestamp) {
    gl.clear(gl.COLOR_BUFFER_BIT);
    uniformTime.value = timestamp * 0.001;  // seconds
    uniformMouse.value = mousePosition;
    draw();
    requestAnimationFrame(render);
}
requestAnimationFrame(render);
```

### 5.2 Core GLSL Patterns Used in Production

**Signed Distance Fields (SDFs)** — define shapes analytically rather than with polygons. Resolution-independent. Smooth boolean operations (union, intersection, subtraction). Used for reticles, HUD elements, sharp UI shapes.

```glsl
float circle(vec2 p, float r) { return length(p) - r; }
float box(vec2 p, vec2 b) {
    vec2 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}
```

**Fractal Brownian Motion (fBm)** — layered noise for organic texture (clouds, terrain, Stripe-style gradients). Stack noise octaves: each at 2× the frequency and 0.5× the amplitude of the previous.

**Render targets / framebuffer objects (FBOs)** — render the scene to an offscreen texture, then apply post-processing in a second pass. How blur, bloom, color grading, and feedback effects are implemented. In Three.js: `WebGLRenderTarget`.

**Multi-pass architecture**:
```
Pass 1: render scene → FBO texture A
Pass 2: apply blur to A → FBO texture B
Pass 3: composite B over background → screen
```

### 5.3 Three.js in React (react-three-fiber)

The `useFrame` hook runs inside the R3F render loop — not React's render cycle. Animation state lives in refs, not component state, so no React re-renders are triggered per frame:

```js
const meshRef = useRef();
useFrame((state) => {
    meshRef.current.rotation.y = state.clock.elapsedTime;
    meshRef.current.material.uniforms.uTime.value = state.clock.elapsedTime;
});
```

Source: [github.com/pmndrs/react-three-fiber](https://github.com/pmndrs/react-three-fiber), [blog.maximeheckel.com](https://blog.maximeheckel.com).

---

## 6. Smooth Scroll Architecture (Lenis)

Source: [github.com/darkroomengineering/lenis](https://github.com/darkroomengineering/lenis).

Lenis maintains three scroll states:

| State | Description |
|-------|-------------|
| `targetScroll` | Where the user wants to be (updated on wheel/touch events) |
| `animatedScroll` | Current lerped position (the smooth value) |
| `actualScroll` | Real browser scroll position |

Each rAF frame:
```js
animatedScroll = lerp(animatedScroll, targetScroll, lerpFactor); // default 0.1
window.scrollTo(0, animatedScroll);
```

A `VirtualScroll` component intercepts wheel and touch events with `preventDefault()`, preventing native scroll, then translates them into `targetScroll` updates. The browser never handles scroll natively — Lenis owns the scroll position completely.

The lerp factor determines inertia character. `0.1` = heavy momentum. `0.2` = lighter. The effect feels different at 60fps vs 120fps because lerp is framerate-dependent. Production use requires framerate compensation: `lerpFactor = 1 - Math.exp(-damping * deltaTime)`.

---

## 7. View Transitions API

Now baseline: Chrome 111+, Safari 18+, Firefox 144+.

```js
document.startViewTransition(() => {
    // make DOM changes — update innerHTML, swap classes, navigate
});
```

The browser takes a **screenshot before** the callback and captures the **live state after**. It cross-fades by default using a `@keyframes` pair it generates automatically.

**Element morphing** — assign matching `view-transition-name` to elements in both states. The browser applies FLIP automatically, smoothly animating position, size, and content:
```css
.card { view-transition-name: card-thumbnail; }
.detail-image { view-transition-name: card-thumbnail; }
```

The same name in both views tells the browser to treat them as the same element and animate between them.

**`::view-transition-old()` and `::view-transition-new()`** pseudoelements let you override the default cross-fade with custom keyframes.

Source: [github.com/WICG/view-transitions](https://github.com/WICG/view-transitions), [developer.chrome.com/docs/web-platform/view-transitions](https://developer.chrome.com/docs/web-platform/view-transitions).

---

## 8. Signals vs Virtual DOM — When It Matters for UI

Signal-based reactivity (SolidJS, Svelte 5 runes, Vue's Composition API) makes surgical DOM updates — only the specific DOM nodes that depend on a changed signal re-render, with no component tree reconciliation. Benchmarks show SolidJS and Svelte 5 are 50–60% faster than React on heavy DOM mutation workloads.

For animation specifically, the practical answer is: **bypass the framework entirely**.

Both GSAP and react-spring write directly to DOM refs rather than going through React state. The animation lives outside React's awareness:

```js
const ref = useRef(null);

useEffect(() => {
    // Direct DOM write. React never knows this happened.
    // No re-render. No vdom diff. No reconciliation.
    gsap.to(ref.current, { x: 200, opacity: 1, duration: 0.5 });
}, []);
```

`useRef` is a DOM handle that doesn't trigger reconciliation. Animations that pass values through `useState` and update on every frame will hit the virtual DOM at 60fps — 60 full component re-renders per second — and will drop frames under any meaningful load.

**The rule**: animation state lives in refs. Component state (which drives rendering) does not update during animation. These are separate channels.

---

## 9. Reference Repos — Code Worth Reading

| Repo | Why it matters |
|------|---------------|
| [pmndrs org](https://github.com/pmndrs) | Highest density of production creative web code on GitHub: react-spring, react-three-fiber, drei, uikit. All open source. |
| [darkroomengineering/lenis](https://github.com/darkroomengineering/lenis) | ~600 lines. Complete virtual scroll architecture — lerp loop, event interception, framerate compensation. |
| [emilkowalski/sonner](https://github.com/emilkowalski/sonner) | Toast notifications: CSS transitions vs keyframes, gesture handling, stack layout with FLIP. Small enough to read completely. |
| [radix-ui/primitives](https://github.com/radix-ui/primitives) | Accessible component internals: focus management, ARIA state machines, portal rendering, animation with presence detection. |
| [mrdoob/three.js](https://github.com/mrdoob/three.js) | The `/examples` directory — every WebGL technique cleanly implemented. |
| [greensock/GSAP](https://github.com/greensock/GSAP) | The ticker architecture, property interpolation, plugin system. Production-grade at every layer. |
| [framer/motion](https://github.com/framer/motion) | FLIP implementation, spring engine, gesture handling, layout animation with child correction. |
| [WICG/view-transitions](https://github.com/WICG/view-transitions) | The spec explainer is the best explanation of *why* the API works as it does, not just *how* to use it. |

---

## 10. Primary Reference Sources

| Source | What it covers |
|--------|---------------|
| [motion.dev/blog/web-animation-performance-tier-list](https://motion.dev/blog/web-animation-performance-tier-list) | The definitive browser rendering pipeline + property tier list |
| [blog.maximeheckel.com](https://blog.maximeheckel.com) | Production WebGL: render targets, refraction, halftone, CMYK, WebGPU/TSL. Best single blog for implementation depth. |
| [nan.fyi/magic-motion](https://nan.fyi/magic-motion) | Best single resource on FLIP: the math, the child correction problem, the transform-origin constraint. Interactive. |
| [blog.maximeheckel.com/posts/the-physics-behind-spring-animations](https://blog.maximeheckel.com/posts/the-physics-behind-spring-animations/) | Spring physics derivation from Hooke's Law through to production implementation. |
| [bram.us/2021/10/13/how-to-create-the-stripe-website-gradient-effect](https://www.bram.us/2021/10/13/how-to-create-the-stripe-website-gradient-effect/) | Stripe gradient reverse engineering — MiniGL, vertex shader, fBm fragment shader. |
| [pustelto.com/blog/reverse-engineer-linear-1-header](https://pustelto.com/blog/reverse-engineer-linear-1-header/) | Linear UI reverse engineering — MobX, ResizeObserver, visibility overflow, useLayoutEffect. |
| [vercel.com/blog/design-engineering-at-vercel](https://vercel.com/blog/design-engineering-at-vercel) | Vercel's animation hierarchy, Three.js + GLSL pipeline, design-in-code approach. |
| [developer.chrome.com/docs/css-ui/scroll-driven-animations](https://developer.chrome.com/docs/css-ui/scroll-driven-animations) | Scroll-driven animations official reference. |
| [threejs-journey.com](https://threejs-journey.com) | Bruno Simon's GLSL + Three.js course — vertex shaders, fragment shaders, particles, post-processing. |
| [tympanus.net/codrops](https://tympanus.net/codrops) | Full implementation tutorials with GitHub source. WebGL effects, scroll animations, transitions. |
| [emilkowal.ski](https://emilkowal.ski) | UI animation implementation depth: Sonner, Vaul, gesture handling. |

---

## 11. Images and Backgrounds — Implementation Mechanics

*This section was added in a second research pass after the first draft omitted it. The theme system works directly with background images, opacity, blur, watermarks, and overlays — this is the mechanically relevant layer.*

### 11.1 `background-image` vs `<img>` with `object-fit: cover`

**The decisive difference is discovery timing and responsive delivery.**

`<img>` tags are found by the browser's preload scanner before full DOM/CSSOM parsing — the fetch begins immediately in parallel with everything else. `background-image` is discovered during CSS parsing, which is gated behind CSSOM construction. On any page with significant CSS, this delay is measurable.

More importantly: `<img srcset="...">` delivers a mobile-sized crop to a mobile screen. A `background-image` with a 1800px source delivers the same 227KB file to a 375px phone — a 72% wasted transfer. `image-set()` partially solves this for backgrounds but has worse browser support than `srcset`.

**For a theme system's full-page background image, `<img>` with `object-fit: cover` is the correct implementation:**
```css
.bg-container { position: relative; overflow: hidden; }

.bg-image {
    position: absolute;
    inset: 0;
    width: 100%; height: 100%;
    object-fit: cover;
    object-position: center;
    z-index: 0;
}
```

**When `background-image` is correct:** Repeating tile textures (scanlines, noise, grain patterns), decorative overlays where the same small tile is intentional. These are exactly how the theme engine uses it now — correct.

`decoding="async"` — tells the browser to decode the image off the main thread. Prevents jank on large images. Pair with `loading="lazy"` for below-fold images, `loading="eager"` for the background image (it needs to appear immediately).

Source: [jasonyingling.me/better-performing-background-images-with-object-fit](https://jasonyingling.me/better-performing-background-images-with-object-fit/).

### 11.2 `backdrop-filter: blur()` — How It Actually Works

`backdrop-filter` applies filter effects to the pixels **directly behind** the element, not the entire page. The element must have some transparency for the effect to show. The blur samples the compositor's snapshot of everything at a lower z-position.

**The edge artifact:** The algorithm only samples pixels directly behind the element at the moment of compositing. Content near the border of a blurred panel — peeking around the edges — is not included in the blur calculation. This creates inconsistent blur near panel boundaries. The fix: extend the backdrop element slightly beyond its visible bounds using a `mask-image` clip, so the algorithm samples a wider area while the visible output is correct.

**Performance cost — this matters for the panel overlay system:**

| Count | Cost |
|-------|------|
| 1–3 backdrop-filter elements | Fine on most hardware |
| 4–8 | Test on mid-range mobile; reduce blur radius |
| Nested backdrop-filter | Each nesting level doubles repaint cycles |
| Blur radius > 40px on large elements | Expensive regardless of count |

Practical limit: keep blur radius under 20px. Cost scales nonlinearly with radius. Keep simultaneous `backdrop-filter` elements under 4 on any given screen state.

Every element with `backdrop-filter` automatically becomes its own compositor layer. `will-change: transform` on elements that also animate reduces per-frame recalculation but increases VRAM usage — only add it when the panel actually moves or scales.

Firefox-specific: `backdrop-filter` stops working on `position: sticky` elements when ancestors have both `overflow` and `border-radius`. Use `-webkit-backdrop-filter` alongside `backdrop-filter` for Safari.

Source: [joshwcomeau.com/css/backdrop-filter](https://www.joshwcomeau.com/css/backdrop-filter/).

### 11.3 `mix-blend-mode` vs `background-blend-mode` — The Critical Distinction

These are not the same property doing different things. They operate on entirely different compositing units:

**`mix-blend-mode`** — blends an **element** against everything behind it in the stacking context. Affects the entire element.

**`background-blend-mode`** — blends an element's **CSS backgrounds against each other** (only). A `background-blend-mode` cannot blend a CSS background against a sibling element — the backgrounds are isolated from the page by definition.

```css
/* background-blend-mode: gradient blends with image, entirely within the element */
.panel {
    background-image:
        linear-gradient(rgba(30,10,60,0.5), rgba(30,10,60,0.5)),
        url('bg.jpg');
    background-blend-mode: multiply;
}

/* mix-blend-mode: this element's pixels blend against whatever is behind it */
.color-tint {
    background: rgba(30, 10, 60, 0.4);
    mix-blend-mode: multiply;
}
```

### 11.4 `isolation: isolate` — Containing Blend Modes

This is the architectural key for layered compositing systems. `isolation: isolate` creates a new stacking context **with no visual side effects** — no opacity change, no transform, no z-index required. It confines `mix-blend-mode` children to blend only within the isolated group, not against everything on the page:

```css
/* Without isolation: tint blends against the entire page */
.scene { }
.color-tint { mix-blend-mode: multiply; }

/* With isolation: tint only blends against .scene's own background */
.scene { isolation: isolate; }
.color-tint { mix-blend-mode: multiply; }
```

**Critical limitation:** `isolation: isolate` only contains `mix-blend-mode`. It does not affect `background-blend-mode` (which is already isolated by definition).

### 11.5 The Complete Layer Architecture for Theme Backgrounds

The correct stacking order for a theme background + overlay system:

```html
<!-- Outermost isolation container: contains ALL background blend modes -->
<div class="scene-root" style="isolation: isolate; position: relative;">

    <!-- Layer 0: base background image -->
    <img class="bg-image" src="bg.jpg" alt=""
         loading="eager" decoding="async"
         style="position: absolute; inset: 0;
                width: 100%; height: 100%;
                object-fit: cover; object-position: center; z-index: 0;">

    <!-- Layer 1: color tint — blends against bg-image -->
    <div style="position: absolute; inset: 0; z-index: 1;
                background: var(--theme-tint);
                mix-blend-mode: multiply;
                pointer-events: none;"></div>

    <!-- Layer 2: scanlines — no blend mode, additive opacity only -->
    <div style="position: absolute; inset: 0; z-index: 2;
                pointer-events: none; opacity: var(--scanline-opacity);
                background-image: repeating-linear-gradient(
                    0deg, transparent, transparent 2px,
                    rgba(0,0,0,0.15) 2px, rgba(0,0,0,0.15) 4px);"></div>

    <!-- Layer 3: vignette -->
    <div style="position: absolute; inset: 0; z-index: 3;
                pointer-events: none;
                background: radial-gradient(ellipse at center,
                    transparent 40%, rgba(0,0,0,0.6) 100%);"></div>

    <!-- Layer 4: UI content with frosted-glass panels -->
    <main style="position: relative; z-index: 10;">
        <div style="backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    background: rgba(0,0,0,0.3);">
            Content
        </div>
    </main>

</div>

<!-- Watermark: OUTSIDE the isolation container -->
<!-- If it were inside, the tint blend mode would color-shift it -->
<div class="watermark" style="position: fixed; inset: 0; z-index: 9999;
     pointer-events: none; opacity: 0.06;
     background: url('watermark.svg') no-repeat;
     background-size: 11%;
     background-position: top right;"></div>
```

**The non-obvious rule:** Anything that should be unaffected by scene blend modes — the watermark, UI chrome, notification badges — must live **outside** the `isolation: isolate` container.

### 11.6 Parallax — What Actually Works

**`background-attachment: fixed` is broken and should not be used.** iOS Safari has never properly supported it with `background-size: cover`. It also causes scroll jank on desktop because the fixed background is updated on the main thread while scrolling happens on the compositor thread.

The correct transform-based parallax (pure JS, rAF loop):
```js
function initParallax(el, speed = 0.3) {
    let target = 0, current = 0;
    window.addEventListener('scroll', () => { target = window.scrollY * speed; });
    (function loop() {
        current += (target - current) * 0.1; // lerp — smooth follow
        el.style.transform = `translateY(${current}px)`;
        requestAnimationFrame(loop);
    })();
}
```

Animating `transform: translateY()` on a GPU-composited element is compositor-only — the cheapest possible operation. Never animate `background-position` for parallax — it triggers paint on every frame.

When using Lenis smooth scroll: read scroll position from `lenis.scroll`, not `window.scrollY`. They diverge during the lerp phase.

### 11.7 CSS Masking and Clipping

**`clip-path`** — binary visibility, geometric shapes, GPU-compositable for animations. Use for hard-edged shaped containers, reveal animations, polygon cutouts.

```css
/* Angled bottom edge */
.panel { clip-path: polygon(0 0, 100% 0, 100% 90%, 90% 100%, 0 100%); }

/* Animatable reveal */
.hidden { clip-path: inset(0 100% 0 0); }
.revealed { clip-path: inset(0 0% 0 0); transition: clip-path 0.6s ease; }
```

**`mask-image`** — supports gradients and soft alpha edges. Triggers paint (more expensive than clip-path). Use for feathered fades, vignette shapes, gradient-masked images.

```css
/* Fade out bottom edge */
.fading { mask-image: linear-gradient(to bottom, black 60%, transparent 100%);
          -webkit-mask-image: linear-gradient(to bottom, black 60%, transparent 100%); }

/* Circular vignette */
.vignetted { mask-image: radial-gradient(ellipse at center, black 50%, transparent 90%); }
```

**SVG `<mask>`** — most expensive; use only when the mask shape is genuinely complex (arbitrary paths, multiple combined shapes, or when the mask must be shared across multiple elements).

Decision matrix: `clip-path` for geometry and performance → `mask-image` for soft edges → SVG mask for complexity.

### 11.8 Image Loading — Progressive Enhancement

The LQIP (Low Quality Image Placeholder) / blur-up pattern: a tiny (16–40px) base64-encoded image is inlined as a data URI and displayed with `filter: blur(20px)` while the full image loads. On load, crossfade. Used by Medium, Next.js `<Image>`, Gatsby Image.

The data URI must be **inlined in HTML**, not referenced as a URL — an external file defeats the purpose (it's a second request).

For a theme system loading background images: the background container can show the theme's `colors.background` CSS variable while the image loads. No LQIP needed — the background color is always available immediately.

`IntersectionObserver` with `rootMargin: '200px'` starts loading images 200px before they enter the viewport, so users never see the placeholder at normal scroll speed.

### 11.9 Stacking Contexts — The Complete Trigger List

Every one of these creates a new stacking context. Elements inside cannot z-index against elements outside.

- `position: fixed` or `position: sticky` (no z-index needed)
- `position: absolute|relative` + `z-index` other than `auto`
- `opacity < 1`
- `mix-blend-mode` other than `normal`
- Any non-`none` value of: `transform`, `filter`, `perspective`, `clip-path`, `mask`
- `will-change` with any animatable property as value
- `isolation: isolate`
- `contain: layout|paint|strict|content`
- z-index on a flex child or grid child (even without `position`)

**The common failure mode:** An element with `opacity: 0.99` (for a subtle effect) silently creates a stacking context that traps everything inside it. A modal or tooltip inside that element cannot escape above the page-level chrome, regardless of z-index value.

Source: [joshwcomeau.com/css/stacking-contexts](https://www.joshwcomeau.com/css/stacking-contexts/).

### 11.10 WebGL Post-Processing for Image Backgrounds

For applying real-time effects (film grain, chromatic aberration, CRT scanlines, color grading) to a background image, the render-target pattern:

```
Background image → WebGL RenderTarget (FBO) → fullscreen quad + effect shader → canvas output
```

In Three.js via [pmndrs/postprocessing](https://github.com/pmndrs/postprocessing): all effects in a single `EffectPass` are automatically merged into one GLSL shader — 5 effects, 1 fragment shader invocation per pixel. The alternative (chained `ShaderPass`) runs one full-screen pass per effect.

Key effects for atmospheric themes:
- **Film grain**: `NoiseEffect({ premultiply: true })` — temporal noise, changes each frame
- **Chromatic aberration**: `ChromaticAberrationEffect({ offset: Vector2(0.001, 0.001) })` — RGB channel separation
- **Scanlines**: `ScanlineEffect({ density: 1.5 })` — horizontal line overlay
- **Vignette**: `VignetteEffect({ offset: 0.35, darkness: 0.9 })` — edge darkening
- **LUT color grading**: `LUTEffect` with a 3D texture — maps input RGB to output RGB. Designed in Photoshop/DaVinci Resolve, applied at near-zero runtime cost.

CSS-only alternative for grain: a small tiled noise PNG (200×200, ~3KB) as `background-image` with `mix-blend-mode: overlay` on an overlay div. Near-zero runtime cost, no WebGL.

CSS-only scanlines:
```css
.scanlines::after {
    content: '';
    position: absolute; inset: 0;
    pointer-events: none;
    background-image: repeating-linear-gradient(
        0deg,
        transparent, transparent 2px,
        rgba(0,0,0,0.15) 2px, rgba(0,0,0,0.15) 4px
    );
}
```

### 11.11 Gotchas Summary

| Gotcha | Rule |
|--------|------|
| `background-attachment: fixed` | Never. Broken on iOS, main-thread jank on desktop. |
| `backdrop-filter` nesting | Each nesting level doubles repaint cost. |
| `mix-blend-mode` broken by ancestors | Any `opacity`, `transform`, or `filter` on an ancestor creates a stacking context that confines blending. |
| `isolation: isolate` scope | Only contains `mix-blend-mode`. Does not affect `background-blend-mode`. |
| Watermark inside `isolation: isolate` | Gets color-shifted by tint blend modes. Always place watermark outside the scene isolation container. |
| `clip-path` vs `mask-image` | `clip-path` is GPU-compositable and cheaper. `mask-image` supports gradients but triggers paint. |
| LQIP data URIs | Must be inlined in HTML. External file URL defeats the purpose. |
| `will-change` overuse | Creates GPU layers consuming VRAM. Only on actively-animating elements. |
| CSS custom property updates | Updating one inherited variable triggers paint on all inheriting elements. Scope tightly. |
| Too many compositor layers | Use Chrome DevTools > Layers panel to audit. >20 layers is usually a problem. |

Sources: [joshwcomeau.com/css/backdrop-filter](https://www.joshwcomeau.com/css/backdrop-filter/), [joshwcomeau.com/css/stacking-contexts](https://www.joshwcomeau.com/css/stacking-contexts/), [css-tricks.com/masking-vs-clipping-use](https://css-tricks.com/masking-vs-clipping-use/), [github.com/pmndrs/postprocessing](https://github.com/pmndrs/postprocessing), [web.dev/learn/css/blend-modes](https://web.dev/learn/css/blend-modes).

---

## 12. Application to the Exocortex Theme System

What this research implies for our current theme work, in order of impact:

**12.1 Widget animations should use transform-only motion**

The stamina gauge and status badge currently animate via CSS class changes. If those class changes affect `width`, `height`, or `background-color`, they're hitting Paint on every frame. The fix: animate `transform: scaleX()` for gauge fills (preserving the element's full width, scaling from origin), `opacity` for badge transitions.

**12.2 The watermark is architecturally misplaced**

The current theme engine renders the watermark as a child of the main overlay container — inside the same stacking context as the scanlines and vignette. If a tint `mix-blend-mode` is ever added (which the layer architecture above supports), the watermark will be color-shifted by it. The watermark should live **outside** the `isolation: isolate` scene container, as a `position: fixed` sibling at the page root level. This is a structural fix, not a visual one — it future-proofs the layer system.

**12.3 Background images should switch from `background-image` to `<img>`**

The theme engine currently applies background images via `element.style.backgroundImage`. For full-page theme backgrounds, this is a CSS discovery timing problem. Switching to an absolutely-positioned `<img loading="eager" decoding="async">` with `object-fit: cover` is the correct architecture. The `<img>` approach also enables `srcset` for responsive delivery if themes ever ship multiple resolution variants.

**12.4 The procedural background problem**

The MGS3 tactical map background is an SVG — static, correct for the GPU path. But for themes with truly animated backgrounds (particle systems, organic motion, procedural color), the SVG/CSS path runs out. The architecture for that is a `<canvas id="theme-bg">` with `position: fixed; inset: 0; z-index: -1; pointer-events: none`, driven by a theme-provided fragment shader or particle update function. This is the Stripe pattern applied to a theme system.

The theme JSON could declare:
```json
"background": {
    "type": "shader",
    "src": "/themes/shaders/mgs3-terrain.glsl",
    "uniforms": { "speed": 0.3, "palette": ["#2e3d1e", "#4a5740", "#c97d2e"] }
}
```

The theme engine initializes a WebGL canvas, compiles the shader, and runs the rAF loop. Static image themes continue working as-is. This is not a current-sprint item — it is the correct long-term architecture.

**12.5 Smooth scroll for the chat log**

The chat message list currently scrolls natively. A Lenis instance scoped to the `#chat-messages` container would give it the smooth inertia feel without affecting page scroll. ~20 lines of setup code.

**12.6 Message reveal animations should use CSS scroll-driven animations**

New messages appearing in the chat log are currently handled by the `message_reveal` theme property. The `fade` and `typewriter` types work. The correct implementation for the fade type uses a CSS `@keyframes` animation triggered on element insertion, not a JavaScript `setTimeout` chain. For a near-future enhancement, the `entry` range of `animation-timeline: view()` handles this natively: new messages fade in as they enter the viewport, old messages fade out as they scroll away.

**12.7 The FLIP pattern for widget state changes**

The status badge transitions between states (CAUTION → ALERT → COMPROMISED). Currently this is a text/color swap. Using FLIP for this transition would make the badge appear to morph between states rather than cut. Worth implementing when the widget system gets its next major revision.

---

*This document is a living reference. When a new implementation decision is made in the theme system or UI layer that relies on a technique covered here, note it in section 11. When a new technique is discovered that changes a current approach, update the relevant section.*
