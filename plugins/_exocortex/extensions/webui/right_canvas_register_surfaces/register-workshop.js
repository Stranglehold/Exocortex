/**
 * register-workshop.js — Office / Workshop surface registrar
 *
 * Deploy to:
 *   /a0/usr/plugins/_exocortex/extensions/webui/right_canvas_register_surfaces/
 *
 * Registers the Workshop panel as a tab in the Agent Zero right-canvas,
 * adjacent to the Intel tab. Controls the idle-time engine (enable/disable,
 * pause/resume) and shows recent workshop/field cycle activity.
 *
 * No Alpine store needed — panel manages its own state with plain JS.
 */

export default async function registerWorkshopSurface(canvas) {
  canvas.registerSurface({
    id:    "workshop",
    title: "Office",
    icon:  "self_improvement",
    order: 35,   // after Intel (30)

    async open() {
      // Trigger a refresh when the panel becomes visible
      const panel = document.querySelector('[data-surface-id="workshop"]');
      if (panel) {
        const ev = new CustomEvent("workshop-panel-open");
        panel.dispatchEvent(ev);
      }
    },

    async close() {},
  });
}
