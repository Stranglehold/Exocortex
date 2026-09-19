/**
 * register-office.js — OFFICE right-canvas surface registrar (v1.20 canvas).
 *
 * Deploy to /a0/usr/plugins/_exocortex/extensions/webui/right_canvas_register_surfaces/, replacing
 * register-workshop.js; remove register-exo-ops.js in the same deploy (EXO·OPS retired, 2026-09-14).
 *
 * The Office is the watcher's report on the idle engine: one surface, fixed situation-awareness zones, every source
 * with its own freshness and failure state (office_feed v2). It polls only while visible.
 */
export default async function registerOfficeSurface(canvas) {
  // id "exo-office", never "office": A0's /webui/js/surfaces.js keeps LEGACY_SURFACE_IDS = { "office" -> "desktop" }, so a
  // surface registered as "office" is normalised INTO the core Desktop surface (it re-titled Desktop "Office" and made
  // this panel active whenever Desktop was; found live 2026-09-16 00:3x UTC, one hour after the first deploy).
  canvas.registerSurface({
    id:    "exo-office",
    title: "Office",
    icon:  "self_improvement",
    order: 35,

    async open() {
      window.dispatchEvent(new CustomEvent("office-open"));
    },

    async close() {},
  });
}
