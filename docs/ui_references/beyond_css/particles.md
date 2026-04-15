# Particle / Canvas Backdrop Libraries — Research Report

**Scope:** Evaluate particle/canvas ambient-motion libraries for a dark cyan/navy "mission control" dashboard. Vanilla JS, one HTML file, Flask backend, Alpine.js reactivity, no build system.

**TL;DR verdict:** **Hand-roll ~150 lines of Canvas 2D.** No library on the market beats a focused, 150-line starfield-with-constellation-lines for this use case once you factor in the aesthetic risk, bundle weight, and Alpine.js main-thread competition. Second choice: **tsParticles slim** if you want "drop a script tag and configure JSON." Third choice: **Vanta NET** if you accept a 600KB Three.js runtime for a prettier but more generic look.

---

## 1. Library Landscape (April 2026)

### Data collected directly from GitHub API and CDN HEAD requests

| Library | Stars | Last code commit | Archived? | License | Runtime | Min bundle (CDN) |
|---|---|---|---|---|---|---|
| **tsParticles** (`tsparticles/tsparticles`) | 8,787 | **2026-04-13** (active) | No | MIT | Canvas 2D only | engine 85KB + slim 153KB = **~238KB min** |
| **particles.js** (`VincentGarreau/particles.js`) | 30,260 | **2017-03-25** (nine years dead) | No (but effectively) | MIT | Canvas 2D | **23KB min** |
| **Vanta.js** (`tengbao/vanta`) | 6,485 | **2023-01-12** (three years dead) | No | MIT | **Three.js (~600KB) or p5.js** | effect file 10–15KB + runtime |
| **proton-engine** (`drawcall/proton`) | 2,472 | 2026-03-06 (active-ish) | No | MIT | Canvas 2D / WebGL adapters | **~65KB min** |
| **VFX-JS** (`fand/vfx-js`) | 1,021 | 2026-04-13 (active) | No | MIT | **WebGL shaders** (attaches to `<img>`/`<video>`/text) | small core, shader-based |

**Critical correction to the "particles.js is still popular" myth.** The 30,260 stars are legacy. Last *code* commit was March 25, 2017. The recent `pushed_at` timestamp Google shows is a README touch; the source hasn't moved. Open 2024/2025 issues are users filing bug reports into the void. Do not vendor particles.js for a new 2026 project — it has no ES module build, no TypeScript, no security maintenance, and tsParticles exists as its officially-endorsed successor (original author Vincent Garreau publicly pointed people at tsParticles after leaving the project).

**Vanta.js is in a similar state** — last code commit January 12, 2023, though it at least still works and the Three.js dependency it relies on is stable.

**tsParticles and VFX-JS are the only two libraries here with commits this week.**

### Sources
- [tsparticles/tsparticles](https://github.com/tsparticles/tsparticles) — homepage [particles.js.org](https://particles.js.org/)
- [VincentGarreau/particles.js](https://github.com/VincentGarreau/particles.js/)
- [tengbao/vanta](https://github.com/tengbao/vanta)
- [drawcall/proton](https://github.com/drawcall/proton)
- [fand/vfx-js](https://github.com/fand/vfx-js) — [VFX-JS: WebGL Effects Made Easy (Codrops 2025)](https://tympanus.net/codrops/2025/01/20/vfx-js-webgl-effects-made-easy/)

---

## 2. Renderer Breakdown: Canvas 2D vs WebGL

Empirically verified by grepping the minified bundles served from jsDelivr:

| Library | Context |
|---|---|
| tsParticles engine | `getContext("2d")` — confirmed by inspection of `@tsparticles/engine@3/tsparticles.engine.min.js` |
| particles.js | `getContext("2d")` |
| Vanta.js (NET, DOTS, WAVES, HALO, RINGS, GLOBE, TOPOLOGY, CELLS, BIRDS) | **WebGL** via Three.js |
| Vanta.js (FOG, CLOUDS, CLOUDS2, TRUNK) | **WebGL** via p5.js |
| proton-engine | Canvas 2D by default; pluggable renderers |
| VFX-JS | **WebGL shaders** (fragment shaders attached to DOM elements) |

**Implication for your dashboard:** Canvas 2D animations run on the main thread. So does Alpine.js reactivity. So does every `fetch()` JSON parse. Everything fights for the same thread unless you use `OffscreenCanvas` + a Web Worker (which none of these libraries do out of the box in their documented default configurations).

The good news: a starfield with ~80 particles and ~200 constellation line checks per frame is nothing. At 60fps, that's ~12,000 distance calculations per second — microseconds of main-thread time. Alpine.js won't notice.

The bad news: **Vanta effects upload geometry to the GPU each frame and carry a ~600KB Three.js runtime.** That's a 5–10x heavier library load, and it only helps if you're doing something GPU-worthy (displacement shaders, volumetric fog). For a quiet drifting starfield, WebGL is overkill — the thing you're saving (main thread cycles) wasn't a bottleneck.

### Performance rule of thumb for this use case
- **<200 particles, simple geometry → Canvas 2D is the right answer.** Main-thread cost is sub-millisecond.
- **>500 particles or fragment shaders → WebGL becomes worth the runtime weight.**
- **OffscreenCanvas + Worker** is the "do it right" answer if you ever hit a bottleneck, but you won't with 80 drifting stars.

### Sources
- [A look at 2D vs WebGL canvas performance (semisignal)](https://semisignal.com/a-look-at-2d-vs-webgl-canvas-performance/)
- [OffscreenCanvas (web.dev)](https://web.dev/articles/offscreen-canvas)
- [Faster WebGL/Three.js with OffscreenCanvas and Web Workers (Evil Martians)](https://evilmartians.com/chronicles/faster-webgl-three-js-3d-graphics-with-offscreencanvas-and-web-workers)

---

## 3. Aesthetic Register: Mission Control vs Crypto Landing Page

This is the most important axis and the hardest to measure. My read, after surveying showcase sites:

### "Crypto landing page" signals (avoid)
- Hot saturated gradients (purple → pink → cyan)
- Mouse-follow "repulse" interactions where particles flee the cursor
- Rotating 3D globes with connecting "data lines"
- Fast particles with "link" distance > ~120px
- Dense networks (>150 particles on screen at once)
- Animated bloom / postprocessing
- "Matrix rain" at full density

### "Mission control" signals (want)
- Low saturation, near-monochrome (cyan on navy works; so does amber on black for a different register)
- Slow drift speeds (0.05–0.2 px/frame range)
- Sparse particle counts (40–100 total)
- Thin, short constellation lines at moderate opacity (~0.15–0.3 alpha)
- No mouse interaction, or only very subtle parallax
- Static or nearly-static — the motion should be noticed only if you stop and look
- Consistent grid structures (Vanta TOPOLOGY comes close but is too "busy")
- Flicker / scanline suggestions (not libraries, but CSS overlays)

### Library-by-library aesthetic verdict

| Library | Default aesthetic | Can it do mission control? |
|---|---|---|
| tsParticles (slim preset) | Defaults to crypto; 30,000 config knobs lets you dial it down | **Yes**, with effort — disable hover/click interactions, reduce particle count to ~60, set low opacity, use `twinkle` off, `links.distance: 140`, `move.speed: 0.3` |
| Vanta NET | Crypto — fast, interactive, glowy | **Maybe** — set `color: 0x66ccff`, `backgroundColor: 0x0a1520`, `maxDistance: 18`, `spacing: 22`, kill mouseControls. Still has a "webapp hero" feel. |
| Vanta DOTS | Close — floating dots on dark background | **Yes** — probably the closest Vanta option for this aesthetic. |
| Vanta TOPOLOGY | Wireframe grid that ripples — inherently "tactical map" feeling | **Closest to mission control of any stock preset.** Worth a serious look. |
| Vanta HALO | Bloom / glow circles | No — concert poster energy |
| Vanta GLOBE | Rotating wireframe earth | Only if your dashboard literally is a globe tracker |
| proton-engine | Emitter/particle system — geared toward explosions/confetti | No — wrong primitive |
| VFX-JS | Shader effects on text/images (distortion, glitch, RGB shift) | **Different category entirely** — it doesn't do "backdrop," it does "retro CRT distortion on your H1." Worth knowing about for text treatment, not background. |
| Hand-rolled Canvas 2D | Whatever you write | **Yes** — you control every knob |

**The "dark ops" feel comes from restraint, not from library features.** Every library listed here defaults to too much. The work is tuning down, not tuning up. Hand-rolling wins this axis because the default *is* tuned down — you add only what you need.

---

## 4. Effect Type Coverage

| Effect | tsParticles | particles.js | Vanta | Hand-roll effort |
|---|---|---|---|---|
| Drifting point field (slow stars) | Yes (slim) | Yes | DOTS | ~40 lines |
| Constellation/network lines (proximity connections) | Yes (slim, `links` config) | Yes (original use case) | NET | ~60 lines (adds O(n²) distance check) |
| Slow noise field (sonar grid warping) | No direct preset — would need custom path shape + wave plugin | No | **TOPOLOGY** (closest) | ~100 lines with simplex noise; or CSS `filter: url(#turbulence)` SVG |
| Falling code rain (Matrix) | No | No | No | ~80 lines — classic one-pager canvas trick |
| Parallax layered stars | Via `parallax` option | No | No | ~60 lines |
| Conic / radar sweep | No | No | No | ~30 lines (single rotating arc gradient) |
| Scanline / CRT distortion on text | No | No | No | **VFX-JS** is the answer here |

**Cleanest "drop-in, configure, done" option:** tsParticles slim with the `links` preset. You write ~30 lines of JSON and get an acceptable constellation background. But you still have to spend an hour tuning it away from the crypto default.

**Best aesthetic coverage per line of custom code:** hand-roll. You'll hit "exactly right" in 150 lines and it will match the rest of your dashboard better than any library preset.

---

## 5. Performance & Accessibility Checklist

These apply to any approach you choose — they're not library features.

### Frame rate
- **Ambient backdrops target 30fps or less, not 60fps.** This is deliberate. The motion should feel slow and contemplative. Drop the target to 30fps and you cut CPU in half.
- Use `setInterval(tick, 1000/30)` or gate `requestAnimationFrame` with a timestamp delta check.

### `prefers-reduced-motion`
```js
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (reduceMotion) {
  // Render one static frame and stop. Don't animate at all.
  renderFrame();
  return;
}
```
None of the libraries listed handle this automatically in their defaults. tsParticles has a `reduceMotion` option you must enable. Vanta does not respect it. Hand-rolled code gives you complete control.

### Pause when tab hidden
```js
document.addEventListener('visibilitychange', () => {
  if (document.hidden) cancelAnimationFrame(rafId);
  else rafId = requestAnimationFrame(tick);
});
```
Browsers already throttle `requestAnimationFrame` to ~1fps in background tabs since Chrome 57 / Firefox 50, so this is belt-and-suspenders — but it's worth adding to also stop your own timers and release the CPU completely. tsParticles handles this. Vanta does not.

### Mobile / battery saver
- Detect `navigator.connection?.saveData === true` and skip animation entirely.
- Detect `window.innerWidth < 768` and reduce particle count by half (or skip).
- On iOS, WebGL contexts can get torn down when the tab loses focus — Canvas 2D is more forgiving.

### DPR handling
Set `canvas.width = cssWidth * devicePixelRatio` and `ctx.scale(dpr, dpr)` or your stars will look fuzzy on retina.

### Sources
- [MDN: prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion)
- [Animated particle constellations in 42 lines (slicker.me)](https://slicker.me/javascript/particles.htm)

---

## 6. Concrete Recommendation

### Primary: Hand-roll ~150 lines of Canvas 2D

**Why:**
1. Aesthetic control is the dominant concern and hand-roll wins that axis.
2. The perf profile of this effect (≤100 particles, drift-only) is trivial — there is no library-level optimization that matters.
3. Zero bundle cost, zero dependency risk, zero version drift. It will still work in 2030.
4. Alpine.js on the same thread is fine — distance math on 80 particles is sub-millisecond.
5. You already have a CSS reference library and you'll want the backdrop to honor the same design tokens (`--color-accent-cyan`, etc). Library configs can't read CSS variables cleanly; hand-roll can.
6. It fits your entire stated design ethos — one HTML file, vanilla JS, no build system. Adding a library to that stack fights the ethos.

**What to write:**
- `starfield.js` — ~150 lines, single IIFE or ES module
- Configurable via `data-*` attributes or a small options object
- Honors `prefers-reduced-motion` (renders single static frame)
- Pauses on `visibilitychange`
- 30fps target (not 60)
- Reads CSS variables for colors so theme changes propagate automatically
- Fixed-position full-viewport canvas behind `main` content (`z-index: -1; pointer-events: none`)

### Reference skeleton (paste into `starfield.js`, tune to taste)

```js
// starfield.js — ambient drifting point field with optional constellation lines.
// ~150 lines hand-rolled Canvas 2D. No deps.

(function(){
  const cfg = {
    count: 70,                 // particle count
    maxSpeed: 0.12,            // px per frame at 30fps
    color: null,               // null = read CSS var --bg-particle
    linkColor: null,           // null = read CSS var --bg-particle-link
    linkDistance: 130,         // px threshold for drawing a line
    size: [0.6, 1.8],          // radius range
    targetFps: 30,
    respectReducedMotion: true,
  };

  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:fixed;inset:0;z-index:-1;pointer-events:none';
  document.body.prepend(canvas);
  const ctx = canvas.getContext('2d');

  let W, H, dpr, particles = [], rafId = null, lastTick = 0;
  const frameInterval = 1000 / cfg.targetFps;

  const css = getComputedStyle(document.documentElement);
  const colorParticle = cfg.color  || css.getPropertyValue('--bg-particle').trim() || 'rgba(140,220,255,0.55)';
  const colorLink     = cfg.linkColor || css.getPropertyValue('--bg-particle-link').trim() || 'rgba(140,220,255,0.12)';

  function resize(){
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W * dpr; canvas.height = H * dpr;
    canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function seed(){
    particles = Array.from({length: cfg.count}, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * cfg.maxSpeed * 2,
      vy: (Math.random() - 0.5) * cfg.maxSpeed * 2,
      r: cfg.size[0] + Math.random() * (cfg.size[1] - cfg.size[0]),
    }));
  }

  function step(){
    for (const p of particles){
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > W) p.vx *= -1;
      if (p.y < 0 || p.y > H) p.vy *= -1;
    }
  }

  function draw(){
    ctx.clearRect(0, 0, W, H);

    // constellation lines — O(n²) but fine at n=70
    ctx.strokeStyle = colorLink;
    ctx.lineWidth = 0.5;
    for (let i = 0; i < particles.length; i++){
      for (let j = i + 1; j < particles.length; j++){
        const a = particles[i], b = particles[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const d2 = dx*dx + dy*dy;
        if (d2 < cfg.linkDistance * cfg.linkDistance){
          const alpha = 1 - Math.sqrt(d2) / cfg.linkDistance;
          ctx.globalAlpha = alpha * 0.4;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }
    ctx.globalAlpha = 1;

    // points
    ctx.fillStyle = colorParticle;
    for (const p of particles){
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function tick(ts){
    rafId = requestAnimationFrame(tick);
    if (ts - lastTick < frameInterval) return;
    lastTick = ts;
    step();
    draw();
  }

  function start(){
    const reduce = cfg.respectReducedMotion &&
                   window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce){ draw(); return; }  // one static frame, done
    lastTick = 0;
    rafId = requestAnimationFrame(tick);
  }

  function stop(){
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
  }

  window.addEventListener('resize', () => { resize(); seed(); });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop(); else start();
  });

  resize(); seed(); start();
})();
```

Add to your theme CSS:
```css
:root {
  --bg-particle:      rgba(140, 220, 255, 0.55);
  --bg-particle-link: rgba(140, 220, 255, 0.12);
}
```

Include in the dashboard:
```html
<script src="/static/js/starfield.js" defer></script>
```

Done. No build step, no dependency, reads your theme tokens, respects reduced motion, pauses when hidden.

### Fallback recommendation (if you don't want to hand-roll)

**tsParticles slim** — CDN script tag, ~238KB minified. Actively maintained. Canvas 2D so it won't fight Alpine any harder than hand-rolled would. The cost is that the default config looks like a crypto page and you'll spend 30–60 minutes tuning it down. Usage:

```html
<div id="tsparticles" style="position:fixed;inset:0;z-index:-1;pointer-events:none"></div>
<script src="https://cdn.jsdelivr.net/npm/@tsparticles/engine@3/tsparticles.engine.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@tsparticles/slim@3/tsparticles.slim.bundle.min.js"></script>
<script>
  tsParticles.load({
    id: 'tsparticles',
    options: {
      fpsLimit: 30,
      particles: {
        number: { value: 70 },
        color: { value: '#8ccdff' },
        size: { value: { min: 0.6, max: 1.8 } },
        move: { enable: true, speed: 0.3, outModes: 'bounce' },
        links: { enable: true, distance: 130, color: '#8ccdff', opacity: 0.15, width: 0.5 },
      },
      interactivity: { events: { onHover: { enable: false }, onClick: { enable: false } } },
      detectRetina: true,
      pauseOnBlur: true,
      pauseOnOutsideViewport: true,
      motion: { reduce: { factor: 1000, value: true } },
    }
  });
</script>
```

That's ~25 lines of config vs ~150 lines of custom code. Trade: less control, more bundle weight, one external dependency, but zero custom JS to maintain.

### Rejected options and why

- **particles.js (original)** — rejected: nine years without a code commit. Do not start a 2026 project on it.
- **Vanta NET / TOPOLOGY** — rejected as primary: 600KB Three.js runtime for an effect you can get in 150 lines of Canvas 2D. The extra weight doesn't buy anything for the drift-and-connect aesthetic. Worth considering if you specifically want the topology grid warp — no library or hand-roll beats it for that exact effect. Use it only for the *feature* page where it's the hero element, not as the global dashboard backdrop.
- **proton-engine** — rejected: designed for emitters/explosions, not ambient fields. Wrong primitive for this job.
- **VFX-JS** — rejected as backdrop, **noted as a separate tool** for possible future use on text elements (scanline distortion on headers, RGB shift on error states). It's not a competitor here; it's a different category.

---

## 7. Open Questions / Things to Revisit

- **If the dashboard adds a map or globe widget**, reconsider Vanta GLOBE or a Three.js hand-roll — that's the regime where GPU starts earning its weight.
- **If you want Matrix rain as an easter egg** (error pages, boot screens, etc.) — ~80 lines of Canvas 2D, no library needed. Classic snippet.
- **If Alpine.js + starfield ever conflict** (unlikely at n=70), the escape hatch is `OffscreenCanvas` + a Web Worker — still hand-rolled, just moved off the main thread. ~30 lines of additional plumbing.
- **If you want a "sonar sweep" effect** alongside the stars — ~30 lines: one rotating conic gradient on a second canvas layer. Worth prototyping.

---

## Appendix: Bundle size summary (CDN, minified, not gzipped)

Measured directly with `curl | wc -c` against jsDelivr, April 2026:

| Package | File | Bytes |
|---|---|---|
| `@tsparticles/engine@3` | `tsparticles.engine.min.js` | 85,223 |
| `@tsparticles/slim@3`   | `tsparticles.slim.bundle.min.js` | 152,671 |
| `particles.js@2`        | `particles.min.js` | 23,016 |
| `vanta@latest`          | `vanta.net.min.js` | 13,225 |
| `vanta@latest`          | `vanta.dots.min.js` | 10,654 |
| `three@0.160`           | `three.min.js` | 669,884 |
| `proton-engine`         | `proton.min.js` | 64,768 |
| **hand-rolled starfield.js** | (reference skeleton above) | **~4,000** |

Gzipped sizes are typically 25–35% of minified. tsParticles slim gzips to roughly 45KB. A hand-rolled 150-line Canvas 2D starfield gzips to roughly 1.5KB.
