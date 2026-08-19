/**
 * register-sys-monitor.js — SYS·MONITOR right-canvas surface registrar (v1.20 canvas).
 *
 * Deploy to:
 *   /a0/usr/plugins/_exocortex/extensions/webui/right_canvas_register_surfaces/
 *
 * The MAGI System Monitor as a dockable right-canvas surface. Situation-awareness
 * instrument (per WEBUI/AESTHETICS/INFO-ENV briefs): fixed SA zones, comparison
 * telemetry (value + trend + normal-band + Δ), trajectory, alert hierarchy,
 * dossier drill-down. Mirrors the Intelligence panel contract: the Alpine store
 * is created once and lives for the session; open/close start/stop the live tick.
 */
import { createSysMonStore } from "/plugins/_exocortex/webui/sys-monitor-store.js";

export default async function registerSysMonitorSurface(canvas) {
  // Create the store once — panel HTML binds to $store.sysMon
  if (!Alpine.store("sysMon")) {
    Alpine.store("sysMon", createSysMonStore());
  }

  canvas.registerSurface({
    id:    "sys-monitor",
    title: "SYS·MON",
    icon:  "monitoring",
    order: 37,   // right after EXO·OPS (36)

    async open() {
      Alpine.store("sysMon").start();   // begin the live telemetry tick while visible
    },

    async close() {
      Alpine.store("sysMon").stop();    // pause the tick when the surface is hidden
    },
  });
}
