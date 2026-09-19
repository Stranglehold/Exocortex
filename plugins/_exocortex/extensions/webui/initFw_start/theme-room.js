/**
 * theme-room.js — the room: a theme's background, panel and overlay blocks, rendered for the whole Agent Zero UI.
 *
 * Exocortex plugin webui extension for the initFw_start point (A0 calls the default export once, before Alpine).
 * Deploys to plugins/_exocortex/extensions/webui/initFw_start/theme-room.js; no core file is touched.
 *
 * Measured 2026-09-15 (Fable): theme-store.js applies only the 17 colours and the 2 fonts. The background / panel /
 * overlay blocks that every atmospheric theme declares were rendered by nothing, because their consumer was the core
 * patch patches/webui/js/themes.js, retired with install step 13. This module is that patch's room part, rebuilt in
 * the plugin tree against THEME_ENGINE_SPEC_L3 (2026-03-28: the layer stack, the two panel variables, the overlay
 * formulas) and the retired patch's one hard-won choice (the image on html::before, because a position:fixed body
 * makes an injected z -10 div unreliable).
 *
 * Consumes ONLY   background  image / opacity / blur / blend_mode / position / size
 *                 panel       opacity / backdrop_blur / instrument
 *                 overlay     scanlines / vignette / noise / watermark
 * Reads nothing from widgets, cursor_trail, parallax, message_reveal, animation: those blocks are motion for
 * atmosphere (FRAMEWORK rule 4, no fake liveness) and stay unrendered on purpose.
 *
 * panel.instrument (new, optional) is the opacity floor for report surfaces: panes that show data over the room.
 * Published as --panel-instrument on :root only when the theme declares it, so a consumer without it keeps its own
 * floor. --panel-opacity and --panel-backdrop-blur keep the spec's names.
 *
 * Panel translucency names the live selectors (A0 v1.6 webui, measured in agent-zero-v2 2026-09-15): body and
 * #right-panel paint --color-background, #right-panel.chat-active paints --color-chat-background, #left-panel
 * (components/sidebar) and #input-section (components/chat/input) paint --color-panel. The right canvas (the host of
 * every plugin pane, components/canvas/right-canvas.css; Kestrel's reading 2026-09-15 22:4x, verified at the file) is
 * two opaque layers, .right-canvas painting --right-canvas-chrome and .right-canvas-panels painting
 * --right-canvas-surface, both tokens declared ON .right-canvas, so a value published from html can never reach them;
 * they are named here directly, the way the file itself makes the host transparent when closed or in mobile mode.
 * Each element gets its own token back through color-mix at panel.opacity, so the theme editor's live colour edits
 * still show through the glass. The retired patch's .right-panel / .panel names are kept: a selector that matches
 * nothing costs nothing.
 *
 * Change signal: theme-store.js writes the palette onto documentElement.style; that mutation, the storage event
 * (another tab) and the initial call are the three readers. The theme id is the store's own localStorage key.
 * Fail toward the plain palette: a theme that will not load, or a block that will not parse, leaves no room.
 *
 * Headless: roomSpec(theme) is pure (no DOM) and is what harness/theme-room/ctrl_theme_room.mjs tests.
 * Diagnostics: one console line at load naming the version, one per room applied or cleared.
 */
export const VERSION = "theme-room v1.1 (2026-09-15)";

const THEMES_URL   = "/usr/plugins/_exocortex/webui/themes/";
const STORAGE_KEY  = "exocortex_theme";       // theme-store.js's key: the active theme id, absent for Default
const STYLE_ID     = "exo-theme-room";
const OVERLAY_ID   = "exo-theme-overlay";
const WATERMARK_ID = "exo-theme-watermark";
const STAMP        = "exoRoom";               // <html data-exo-room="<id>"> while a room is up; consumers gate on it

const PAINTS = [
  ["#right-panel, .right-panel",       "--color-background"],
  ["#right-panel.chat-active",         "--color-chat-background"],
  ["#left-panel, #input-section, .panel", "--color-panel"],
  [".right-canvas",                    "--right-canvas-chrome"],    // the pane host's outer layer (v1.1)
  [".right-canvas-panels",             "--right-canvas-surface"],   // and its inner one; both opaque in core
];

const BLENDS = new Set(["normal", "multiply", "screen", "overlay", "darken", "lighten", "color-dodge", "color-burn",
  "hard-light", "soft-light", "difference", "exclusion", "hue", "saturation", "color", "luminosity"]);
const TOKEN = /^[a-z0-9 %.\-]{1,40}$/i;       // background-size / background-position values we will pass through
const NOISE_TILE = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'>"
  + "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter>"
  + "<rect width='120' height='120' filter='url(%23n)'/></svg>";

const obj = (v) => (v && typeof v === "object" && !Array.isArray(v)) ? v : {};
const num = (v, d) => { const n = typeof v === "boolean" ? NaN : Number(v); return Number.isFinite(n) ? n : d; };
const clamp01 = (n) => Math.max(0, Math.min(1, n));
const token = (v, d) => (typeof v === "string" && TOKEN.test(v.trim())) ? v.trim() : d;
const blend = (v) => (typeof v === "string" && BLENDS.has(v.trim())) ? v.trim() : "normal";
const cssUrl = (s) => String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/[\n\r]/g, "");

/**
 * The room as CSS + the overlay layers it needs. Pure. Returns an empty spec (css "") for a theme that declares
 * none of the three blocks, so palette-only themes get no room at all, not an empty one.
 */
export function roomSpec(theme) {
  const empty = { css: "", layers: [], vars: {}, image: null };
  if (!theme || typeof theme !== "object" || Array.isArray(theme)) return empty;
  if (!(theme.background || theme.panel || theme.overlay)) return empty;
  const bg = obj(theme.background), pn = obj(theme.panel), ov = obj(theme.overlay);

  const vars = {};
  const pOp = clamp01(num(pn.opacity, 1));
  const pBlur = Math.max(0, num(pn.backdrop_blur, 0));
  vars["--panel-opacity"] = String(pOp);
  vars["--panel-backdrop-blur"] = pBlur + "px";
  const inst = num(pn.instrument, NaN);
  if (Number.isFinite(inst)) vars["--panel-instrument"] = String(clamp01(inst));

  let css = ":root{" + Object.entries(vars).map(([k, v]) => k + ":" + v).join(";") + "}\n";
  // html carries the palette colour so a translucent body / panel always sits over the theme, never over white
  css += "html{background-color:var(--color-background) !important}\n";

  let image = null;
  if (bg.type === "image" && typeof bg.src === "string" && bg.src.trim()) {
    const op = clamp01(num(bg.opacity, 1)), bl = Math.max(0, num(bg.blur, 0));
    const inset = bl > 0 ? -(bl * 2) : 0;   // a blurred edge feathers inward; oversize the layer to hide it
    image = { src: bg.src.trim(), opacity: op, blur: bl, blend: blend(bg.blend_mode),
              size: token(bg.size, "cover"), position: token(bg.position, "center") };
    css += 'html::before{content:"";position:fixed;inset:' + inset + "px;z-index:-1;pointer-events:none;"
      + 'background-image:url("' + cssUrl(image.src) + '");background-size:' + image.size
      + ";background-position:" + image.position + ";background-repeat:no-repeat;opacity:" + op + ";"
      + (bl > 0 ? "filter:blur(" + bl + "px);" : "") + "mix-blend-mode:" + image.blend + "}\n";
    css += "body{background-color:transparent !important}\n";
  }

  if (pOp < 1 || pBlur > 0) {
    const pct = Math.round(pOp * 1000) / 10;
    const blurCss = pBlur > 0
      ? "backdrop-filter:blur(" + pBlur + "px) !important;-webkit-backdrop-filter:blur(" + pBlur + "px) !important;" : "";
    for (const [sel, tok] of PAINTS) {
      css += sel + "{background-color:color-mix(in srgb, var(" + tok + ") " + pct + "%, transparent) !important;" + blurCss + "}\n";
    }
  }

  const layers = [];
  const sc = obj(ov.scanlines);
  if (sc.enabled) {
    const s = Math.max(1, Math.round(num(sc.spacing, 2))), o = clamp01(num(sc.opacity, 0.04));
    layers.push("scanlines");
    css += "#" + OVERLAY_ID + " .exo-scanlines{background:repeating-linear-gradient(0deg,transparent,transparent "
      + s + "px,rgba(0,0,0," + o + ") " + s + "px,rgba(0,0,0," + o + ") " + (s + 1) + "px)}\n";
  }
  const vg = obj(ov.vignette);
  if (vg.enabled) {
    const o = clamp01(num(vg.opacity, 0.3));
    layers.push("vignette");
    css += "#" + OVERLAY_ID + " .exo-vignette{background:radial-gradient(ellipse at center,transparent 60%,rgba(0,0,0," + o + ") 100%)}\n";
  }
  const nz = obj(ov.noise);
  if (nz.enabled) {
    const o = clamp01(num(nz.opacity, 0.02));
    layers.push("noise");
    css += "#" + OVERLAY_ID + ' .exo-noise{opacity:' + o + ';background-image:url("' + NOISE_TILE + '")}\n';
  }
  const wm = obj(ov.watermark);
  if (wm.enabled && typeof wm.src === "string" && wm.src.trim()) {
    const o = clamp01(num(wm.opacity, 0.05));
    layers.push("watermark");
    css += "#" + WATERMARK_ID + "{position:fixed;inset:0;z-index:9998;pointer-events:none;opacity:" + o
      + ';background-image:url("' + cssUrl(wm.src.trim()) + '");background-repeat:no-repeat;background-position:'
      + token(wm.position, "center") + ";background-size:" + token(wm.size, "40%") + ";mix-blend-mode:" + blend(wm.blend_mode) + "}\n";
  }
  if (layers.some((l) => l !== "watermark")) {
    css += "#" + OVERLAY_ID + "{position:fixed;inset:0;z-index:9999;pointer-events:none}\n"
      + "#" + OVERLAY_ID + ">div{position:absolute;inset:0}\n";
  }
  return { css, layers, vars, image };
}

// ── DOM side ────────────────────────────────────────────────────────────────────────────────────────────────────
let applied = null;      // theme id whose room is up, null when none
let inflight = 0;        // read counter: a slower fetch must not overwrite a newer read

function styleEl() {
  let el = document.getElementById(STYLE_ID);
  if (!el) { el = document.createElement("style"); el.id = STYLE_ID; (document.head || document.documentElement).appendChild(el); }
  return el;
}

function removeLayers() {
  for (const id of [OVERLAY_ID, WATERMARK_ID]) { const el = document.getElementById(id); if (el) el.remove(); }
}

export function clearRoom() {
  const el = document.getElementById(STYLE_ID);
  if (el) el.textContent = "";
  removeLayers();
  delete document.documentElement.dataset[STAMP];
  if (applied !== null) console.info("[THEME-ROOM] room cleared (was " + applied + ")");
  applied = null;
}

function applyRoom(id, spec) {
  if (!spec.css) { clearRoom(); return; }
  styleEl().textContent = spec.css;
  removeLayers();
  const fx = spec.layers.filter((l) => l !== "watermark");
  if (fx.length) {
    const ov = document.createElement("div"); ov.id = OVERLAY_ID;
    for (const l of fx) { const d = document.createElement("div"); d.className = "exo-" + l; ov.appendChild(d); }
    document.body.appendChild(ov);
  }
  if (spec.layers.includes("watermark")) { const w = document.createElement("div"); w.id = WATERMARK_ID; document.body.appendChild(w); }
  document.documentElement.dataset[STAMP] = id;
  applied = id;
  console.info("[THEME-ROOM] room " + id + ": image " + (spec.image ? spec.image.src.split("/").pop() + " @" + spec.image.opacity : "none")
    + "; panel " + spec.vars["--panel-opacity"] + "/" + spec.vars["--panel-backdrop-blur"]
    + (spec.vars["--panel-instrument"] ? " instrument " + spec.vars["--panel-instrument"] : "")
    + "; overlays " + (spec.layers.join(",") || "none"));
}

/** Re-read the active theme id and render its room; force re-reads the JSON even when the id is unchanged. */
export async function refresh(force = false) {
  let id = null;
  try { id = localStorage.getItem(STORAGE_KEY); } catch (e) { /* storage unavailable: no room */ }
  if (!id || id === "default") { if (applied !== null) clearRoom(); return; }
  if (id === applied && !force) return;
  const mine = ++inflight;
  let theme = null;
  try {
    const r = await fetch(THEMES_URL + encodeURIComponent(id) + ".json", { cache: "no-cache" });
    if (r.ok) theme = await r.json();
  } catch (e) { theme = null; }
  if (mine !== inflight) return;
  if (!theme) { clearRoom(); return; }
  applyRoom(id, roomSpec(theme));
}

/** initFw_start entry: A0 calls this once. Safe to call again (a second call is a no-op). */
export default function initThemeRoom() {
  if (typeof document === "undefined" || window.exoThemeRoom) return;
  window.exoThemeRoom = { VERSION, refresh, clear: clearRoom, roomSpec };
  console.info("[THEME-ROOM] " + VERSION + " loaded (initFw_start)");
  const start = () => {
    new MutationObserver(() => refresh()).observe(document.documentElement, { attributes: true, attributeFilter: ["style"] });
    window.addEventListener("storage", (ev) => { if (ev.key === STORAGE_KEY) refresh(); });
    refresh();
  };
  if (document.body) start(); else document.addEventListener("DOMContentLoaded", start, { once: true });
}
