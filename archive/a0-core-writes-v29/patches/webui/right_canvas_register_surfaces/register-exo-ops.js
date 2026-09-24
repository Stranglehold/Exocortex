/**
 * register-exo-ops.js — EXO·OPS diegetic operations surface
 *
 * Deploy to:
 *   /a0/usr/plugins/exocortex/extensions/webui/right_canvas_register_surfaces/
 *
 * Registers the EXO·OPS panel as a right-canvas tab. It renders the REAL idle
 * cycle feed (/api/office_feed) in the diegetic iDroid aesthetic with expandable
 * per-cycle report dossiers, and drives the REAL idle engine (/api/idle_control).
 * Sits next to the plain "Office" tab so the two can be compared.
 *
 * No Alpine store — the panel manages its own state with plain JS (mirrors the
 * Workshop panel contract).
 */

export default async function registerExoOpsSurface(canvas) {
  canvas.registerSurface({
    id:    "exo-ops",
    title: "EXO·OPS",
    icon:  "radar",
    order: 36,   // right after Office (35)

    async open() {
      // inner content component listens on window for this
      window.dispatchEvent(new CustomEvent("exo-ops-open"));
    },

    async close() {},
  });
}
