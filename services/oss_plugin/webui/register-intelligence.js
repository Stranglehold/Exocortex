/**
 * register-intelligence.js — v1.13 right-canvas surface registrar
 *
 * Deploy to:
 *   /a0/usr/plugins/oss/extensions/webui/right_canvas_register_surfaces/
 *
 * Registers the Intelligence Panel as a dockable surface in the Agent Zero
 * right-canvas system. The Alpine store is created once and lives for the
 * session; open/close hooks wire its lifecycle to the panel visibility.
 */

import { createIntelStore } from "/plugins/oss/webui/intelligence-store.js";

export default async function registerIntelligenceSurface(canvas) {
  // Register store once — panel HTML accesses it via $store.intelligence
  if (!Alpine.store("intelligence")) {
    Alpine.store("intelligence", createIntelStore());
  }

  canvas.registerSurface({
    id:    "intelligence",
    title: "Intel",
    icon:  "radar",
    order: 30,

    async open(_payload) {
      await Alpine.store("intelligence").connect();
    },

    async close() {
      Alpine.store("intelligence").disconnect();
    },
  });
}
