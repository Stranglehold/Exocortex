/**
 * Exocortex anim-throttle
 * =======================
 * Pauses ALL CSS animations — this stack's panels (sys-monitor breathing dot,
 * pulsing status dots, shimmer) AND Agent Zero core (spinners, the `.shiny-text`
 * background-position shine, the heartbeat indicator) — whenever the tab is hidden
 * or the window is unfocused.
 *
 * WHY: the A0 web UI animates continuously, and the agents cycle 24/7, so the
 * "active processing" animations essentially never stop. Those are compositor-driven
 * CSS animations (no JS), which keep Firefox's shared GPU process compositing at
 * ~60fps forever — an open dashboard was pegging the GPU's 3D engine (~60%) for hours
 * even with nobody watching, which lagged the whole desktop (the 3D engine also
 * composits Windows via dwm). Diagnosed 2026-07-10.
 *
 * FIX: gate a single global rule on <html class="exo-anim-paused">, toggled by
 * visibilitychange + window focus/blur. `animation-play-state: paused` freezes
 * animations in place (no layout thrash, no JS) until the window is looked at again,
 * at which point they resume instantly. An unwatched dashboard now costs ~zero GPU.
 *
 * Loaded once at framework init (initFw_start webui hook — A0 calls the default export).
 */
export default function initAnimThrottle() {
  if (window.__exoAnimThrottle) return;
  window.__exoAnimThrottle = true;

  var style = document.createElement("style");
  style.id = "exo-anim-throttle";
  style.textContent =
    "html.exo-anim-paused *, html.exo-anim-paused *::before, html.exo-anim-paused *::after" +
    " { animation-play-state: paused !important; }";
  (document.head || document.documentElement).appendChild(style);

  var root = document.documentElement;
  function update() {
    var unwatched = document.visibilityState === "hidden" || !document.hasFocus();
    root.classList.toggle("exo-anim-paused", unwatched);
  }
  document.addEventListener("visibilitychange", update, { passive: true });
  window.addEventListener("blur", update, { passive: true });
  window.addEventListener("focus", update, { passive: true });
  update();

  console.log("[exo-anim-throttle] active — animations pause when tab hidden/unfocused");
}
