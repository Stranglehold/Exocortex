# V1.13 Right-Canvas Panel System — Wiring Reference

*Written 2026-05-05. Sourced from live container `exocortex_v17` running `agent0ai/agent-zero:latest` v1.13.*

---

## What This Document Is

A wiring reference for the v1.13 right-canvas plugin panel system — the dockable surfaces that appear to the right of the chat log (Browser panel, Desktop panel, and any new panel we build). This documents exactly what files exist, what each one does, and how they connect, so we can build new surfaces without guessing.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Browser (index.html)                         │
│                                                                     │
│  ┌──────────────┐   ┌──────────────────────────────────────────┐   │
│  │   Left Sidebar│   │              Right Canvas                │   │
│  │  (nav/chats) │   │  ┌──────┐ ┌──────┐ ┌──────┐             │   │
│  │              │   │  │ Surf.│ │ Surf.│ │ Surf.│  ← tabs     │   │
│  │              │   │  │  1   │ │  2   │ │  ...  │             │   │
│  │              │   │  └──────┘ └──────┘ └──────┘             │   │
│  │              │   │  ┌──────────────────────────┐            │   │
│  │              │   │  │   Active Panel Content   │            │   │
│  │  ┌─────────┐ │   │  │   (plugin panel HTML)   │            │   │
│  │  │  Chat   │ │   │  └──────────────────────────┘            │   │
│  │  │  Log    │ │   └──────────────────────────────────────────┘   │
│  │  │         │ │                                                   │
│  │  └─────────┘ │                                                   │
│  └──────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

The right canvas is a **persistent dockable surface area**. Panels are registered at page load by plugins via extension hooks. Once registered they persist for the session — they open and close without being destroyed or recreated from scratch.

This is fundamentally different from the old emit_artifact approach, which created a new panel per chat message. Here the panel is stable; data flows into it.

---

## File Map — Complete

### Framework (A0 core)

| File | Role |
|------|------|
| `/a0/webui/index.html` | Page template. Injects `<x-extension id="page-head">` and `<x-extension id="right-canvas-panels">` slots |
| `/a0/webui/index.js` | Alpine.js init. Loads extension hooks. Calls `initFw()` |
| `/a0/webui/js/initFw.js` | Framework init: loads all `extensions/webui/` hook dirs, calls each registered JS module |
| `/a0/webui/js/websocket.js` | Socket.io client wrapper. `getNamespacedClient(ns)` → namespaced ws client |
| `/a0/webui/js/api.js` | `fetchApi()`, `callJsonApi()` — CSRF-aware fetch helpers |
| `/a0/webui/components/canvas/right-canvas.html` | Right canvas shell: tab bar + surface slot container |
| `/a0/webui/components/canvas/right-canvas-store.js` | Alpine store: `rightCanvasStore`. Manages which surface is active, open/close lifecycle |

### Browser Plugin

| File | Role |
|------|------|
| `/a0/plugins/_browser/extensions/webui/right_canvas_register_surfaces/register-browser.js` | **Surface registration** — calls `canvas.registerSurface({id:"browser",...})` at page load |
| `/a0/plugins/_browser/extensions/webui/right-canvas-panels/browser-panel.html` | Panel content HTML. Injected into `#right-canvas-panels` slot |
| `/a0/plugins/_browser/extensions/webui/get_tool_message_handler/browser-tool-handler.js` | Custom message renderer for `tool_name="browser"`. Adds screenshot thumbnail + "Open Browser" button to chat messages |
| `/a0/plugins/_browser/extensions/webui/set_messages_after_loop/auto-open-browser-results.js` | Auto-syncs open browser canvas to the right tab after agent loop completes |
| `/a0/plugins/_browser/extensions/webui/chat-input-bottom-actions-start/browser-button.html` | "Open Browser" shortcut button in input toolbar |
| `/a0/plugins/_browser/webui/browser-store.js` | **Alpine store** (2603 lines): all browser panel state, frame queue, viewport sync, tab switching |
| `/a0/plugins/_browser/webui/browser-panel.html` | Standalone modal version of panel (used when undocked) |
| `/a0/plugins/_browser/webui/main.html` | Modal wrapper for undocked floating window |
| `/a0/plugins/_browser/api/ws_browser.py` | **Backend WebSocket handler** (507 lines): screencast streaming, input routing, tab listing |
| `/a0/plugins/_browser/helpers/runtime.py` | Playwright runtime: `start_screencast`, `pop_screencast_frame`, `mouse`, `click`, etc. |

### Office Plugin

| File | Role |
|------|------|
| `/a0/plugins/_office/extensions/webui/right_canvas_register_surfaces/register-office.js` | Surface registration: `{id:"office", icon:"desktop_windows", order:20}` |
| `/a0/plugins/_office/extensions/webui/right-canvas-panels/office-panel.html` | Office panel content HTML |
| `/a0/plugins/_office/extensions/webui/get_tool_message_handler/document-artifact-handler.js` | Custom renderer for document tool outputs |
| `/a0/plugins/_office/extensions/webui/set_messages_after_loop/auto-open-document-results.js` | Auto-opens panel when agent produces document output |
| `/a0/plugins/_office/extensions/webui/right-canvas-toolbar-start/office-new-menu.html` | "New Document" menu in right canvas toolbar |
| `/a0/plugins/_office/webui/office-store.js` | Alpine store for office panel state |
| `/a0/plugins/_office/helpers/desktop_state.py` | Desktop capture: xdotool + xwd + PIL |
| `/a0/plugins/_office/api/ws_office.py` | Backend WebSocket handler for office/document sessions |

### Exocortex (our plugin)

| File | Role |
|------|------|
| `/a0/usr/plugins/exocortex/extensions/webui/get_message_handler/artifact-handler.js` | Routes `type="artifact"` log entries to `window.artifactPanel.update()` |
| `/a0/usr/plugins/exocortex/extensions/webui/sidebar-bottom-wrapper-start/theme-picker.html` | Theme picker button in sidebar |
| `/a0/usr/plugins/exocortex/tools/emit_artifact.py` | Tool that creates a `type="artifact"` log entry |
| `/a0/usr/plugins/exocortex/webui/exo-artifact.js` | ExoArtifact runtime: `fetchJson`, `message`, `action` |

---

## Extension Hook Directories (webui)

These are the hooks the framework calls at page load. A plugin places a file in the matching directory and the framework loads it automatically.

| Hook Directory | When Called | What It Does |
|----------------|-------------|--------------|
| `right_canvas_register_surfaces/` | Page init | Register a named surface in the right canvas |
| `right-canvas-panels/` | Page init | Inject panel HTML into the canvas container |
| `right-canvas-toolbar-start/` | Page init | Add buttons to the canvas toolbar (left side) |
| `chat-input-bottom-actions-start/` | Page init | Add buttons to the chat input toolbar |
| `get_tool_message_handler/` | Per message | Custom HTML renderer for a specific tool's output |
| `get_message_handler/` | Per message | Custom renderer for a specific log `type` |
| `set_messages_after_loop/` | After agent loop | Runs JS after agent completes a turn (auto-open, sync) |
| `page-head/` | Page init | Inject into `<head>` (scripts, styles, meta) |
| `sidebar-bottom-wrapper-start/` | Page init | Add elements at bottom of sidebar |

---

## Surface Registration — How It Works

At page load, the framework calls every JS file in `right_canvas_register_surfaces/`. Each file must export a default function that receives the `canvas` API object:

```javascript
// /plugins/_browser/extensions/webui/right_canvas_register_surfaces/register-browser.js

export default async function registerBrowserSurface(canvas) {
  canvas.registerSurface({
    id: "browser",          // unique ID, used by rightCanvasStore.open("browser", ...)
    title: "Browser",       // tab label
    icon: "language",       // material symbols icon name
    order: 10,              // tab sort order (lower = left)
    modalPath: "/plugins/_browser/webui/main.html",  // undocked modal URL

    // Called when the tab is activated
    async open(payload = {}) {
      // Wait for the panel HTML to be in the DOM and visible
      const panel = await waitForVisibleCanvasPanel('[data-surface-id="browser"] .browser-panel');
      await browserStore.onOpen(panel, {
        mode: "canvas",
        browserId: payload.browserId || null,
        contextId: payload.contextId || null,
      });
    },

    // Called when the tab is closed or another tab is activated
    async close() {
      await browserStore.cleanup?.();
    },

    // Dock/undock handoff lifecycle (optional)
    beginDockHandoff() { browserStore.beginSurfaceHandoff?.(); },
    finishDockHandoff() { browserStore.finishSurfaceHandoff?.(); },
    cancelDockHandoff() { browserStore.cancelSurfaceHandoff?.(); },
  });
}
```

**Important**: The `open()` function receives a `payload` object. This is how you pass context — e.g., `rightCanvasStore.open("browser", { browserId: 5, contextId: "abc" })` → that object arrives as `payload` in `open()`.

---

## Panel HTML — Injection Point and Alpine Wiring

The framework injects panel HTML from `right-canvas-panels/` into a container with `data-surface-id="<id>"`. The Alpine lifecycle hooks for panel init/destroy are `x-create` and `x-destroy`:

```html
<!-- right-canvas-panels/browser-panel.html -->
<div class="browser-panel"
     x-create="$store.browserPage.onOpen($el, xAttrs($el) || {})"
     x-destroy="$store.browserPage.cleanup()"
     @keydown.window="$store.browserPage.handleKeydown($event)">

    <!-- Tab bar: one button per open browser tab -->
    <div class="browser-meta">
        <template x-for="browser in $store.browserPage.browsers" :key="browser.id">
            <button @click="$store.browserPage.selectBrowser(browser.id, browser.context_id)">
                <span x-text="$store.browserPage.browserTabTitle(browser)"></span>
            </button>
        </template>
    </div>

    <!-- Live frame display -->
    <div class="browser-stage">
        <img class="browser-frame" :src="$store.browserPage.frameSrc" />
    </div>

    <!-- Address bar, controls -->
    <input class="browser-address" :value="$store.browserPage.address"
           @change="$store.browserPage.navigate($event.target.value)" />
</div>
```

The store (`$store.browserPage`) is registered via Alpine's `Alpine.store('browserPage', model)`. The `x-create` / `x-destroy` hooks fire when the panel DOM element enters/leaves the active surface slot.

---

## Open/Close Lifecycle — Sequence

```
User clicks "Browser" tab in right canvas
  │
  ▼
rightCanvasStore.open("browser", payload)        [right-canvas-store.js]
  │  sets activeSurfaceId = "browser"
  │  shows the panel HTML slot
  │
  ▼
registered surface's open(payload) called        [register-browser.js]
  │  waitForElement('[data-surface-id="browser"] .browser-panel')
  │  waitForVisibleCanvasPanel(...)  ← polls for stable dimensions (2 stable frames)
  │
  ▼
browserStore.onOpen(panelEl, { mode:"canvas", browserId, contextId })  [browser-store.js]
  │  calls connectViewer({ browserId, contextId, viewport })
  │
  ▼
websocket.request("browser_viewer_subscribe", { context_id, browser_id,
                   viewer_id, viewport_width, viewport_height })        [ws_browser.py]
  │  backend creates asyncio task: _stream_frames(sid, context_id, ...)
  │
  ▼
stream runs → browser_viewer_frame events → frameSrc updates → <img> renders
  │
  ▼
User closes tab or navigates away
  │
  ▼
registered surface's close() called             [register-browser.js]
  │
  ▼
browserStore.cleanup()                          [browser-store.js]
  │  websocket.emit("browser_viewer_unsubscribe", { viewer_id })
  │  off("browser_viewer_frame", frameHandler)
  └  clears frameSrc, active state
```

---

## rightCanvasStore API

The global Alpine store that controls which surface is shown:

```javascript
// Open a surface (can be called from anywhere, including tool handlers)
await rightCanvasStore.open("browser", { browserId: 5, contextId: "abc" });

// Check what's open
rightCanvasStore.isOpen          // boolean
rightCanvasStore.activeSurfaceId // "browser" | "office" | null | custom id
rightCanvasStore.isMobileMode    // boolean (mobile = modal instead of sidebar)

// Close
await rightCanvasStore.close();
```

Import path:
```javascript
import { store as rightCanvasStore } from "/components/canvas/right-canvas-store.js";
```

---

## get_tool_message_handler — Custom Chat Message Rendering

When the agent calls a tool, A0 logs a message of type `"tool"` with `tool_name="browser"`. Normally this renders as a plain process step in the chat log. The `get_tool_message_handler` hook lets a plugin intercept and replace that rendering.

```javascript
// get_tool_message_handler/browser-tool-handler.js

export default async function registerBrowserToolHandler(extData) {
  if (extData?.tool_name === "browser") {
    extData.handler = drawBrowserTool;   // replace default renderer
  }
}

function drawBrowserTool({ id, heading, content, kvps, timestamp, ... }) {
  // Parses tool result JSON from content
  // Adds a live screenshot thumbnail to the "Screenshot" KVP cell
  // Adds "Open Browser" action button
  // Calls rightCanvasStore.open("browser", payload) on click
  // Returns a rendered DOM element
}
```

Key behaviors in the browser handler:
- Renders a `16:10` thumbnail placeholder with a shimmer animation while loading
- Fetches a preview snapshot via `websocket.request("browser_viewer_snapshot", {quality:62})`
- Refreshes the thumbnail every 2.5s (`PREVIEW_REFRESH_MS`)
- Only auto-syncs the open canvas on focus actions: `open`, `navigate`, `set_active`, `activate`, `focus`
- Background actions (click, type, evaluate, mouse) do NOT steal the canvas view

---

## set_messages_after_loop — Post-Turn Sync

After each agent turn, `set_messages_after_loop/` hooks run. The browser plugin uses this to sync the panel to the correct tab when the agent was doing browser work:

```javascript
export default async function syncBrowserResultsIntoOpenCanvas(context) {
  if (!isBrowserCanvasAlreadyOpen()) return;   // only if panel is visible
  for (const { args } of context.results) {
    if (getToolName(payload) !== "browser") continue;
    if (!shouldSyncOpenBrowserCanvas(args, payload, result)) continue;
    // open the canvas to the correct browser tab
    await rightCanvasStore.open("browser", { browserId, contextId });
  }
}
```

This is what makes the panel automatically jump to whichever tab the agent just navigated to.

---

## WebSocket Client Pattern

Both panel stores use the same WebSocket client:

```javascript
import { getNamespacedClient } from "/js/websocket.js";

const websocket = getNamespacedClient("/ws");
websocket.addHandlers(["ws_webui"]);  // register handler group

// Request-response (returns promise, timeoutMs support)
const response = await websocket.request(
  "browser_viewer_subscribe",
  { context_id, viewer_id, viewport_width, viewport_height },
  { timeoutMs: 60000 }
);

// Subscribe to streaming events
await websocket.on("browser_viewer_frame", (data) => {
  // handle frame
});

// Unsubscribe
websocket.off("browser_viewer_frame", handler);
```

Backend handler base class:
```python
# /helpers/ws.py
class WsHandler:
    async def process(self, event: str, data: dict, sid: str):
        """Override this — called for every event. Return value sent back as response."""

    async def emit_to(self, sid, event, data, correlation_id=None):
        """Push event to specific connected client."""

    async def on_disconnect(self, sid):
        """Called when client disconnects — clean up streaming tasks here."""
```

The backend WsHandler registers itself via `hooks.py` in the plugin root:

```python
# /plugins/_browser/hooks.py
from helpers.ws import WsHandler
from .api.ws_browser import WsBrowser

def register(ws_handlers):
    ws_handlers.register(WsBrowser())
```

---

## Recipe: Building a New Surface

Minimum files required for a new surface named `"intelligence"`:

```
/a0/usr/plugins/exocortex/
├── extensions/
│   └── webui/
│       ├── right_canvas_register_surfaces/
│       │   └── register-intelligence.js     ← surface registration
│       ├── right-canvas-panels/
│       │   └── intelligence-panel.html      ← panel HTML (Alpine)
│       └── get_tool_message_handler/        ← (optional) custom tool renderer
│           └── intelligence-handler.js
├── webui/
│   └── intelligence-store.js               ← Alpine store
└── api/  (optional — if you need backend WS)
    └── ws_intelligence.py
```

`register-intelligence.js`:
```javascript
import { store as intelStore } from "/usr/plugins/exocortex/webui/intelligence-store.js";

export default async function registerIntelligenceSurface(canvas) {
  canvas.registerSurface({
    id: "intelligence",
    title: "Intel",
    icon: "radar",
    order: 30,
    async open() {
      await intelStore.connect();
    },
    async close() {
      await intelStore.disconnect();
    },
  });
}
```

`intelligence-panel.html` (in `right-canvas-panels/`):
```html
<div class="intelligence-panel"
     x-create="$store.intelligence.onMount($el)"
     x-destroy="$store.intelligence.onUnmount()">
  <!-- panel content here -->
</div>
```

`intelligence-store.js`:
```javascript
import Alpine from "/vendor/alpine.js";

const model = {
  connected: false,
  async connect() { this.connected = true; /* subscribe to events */ },
  async disconnect() { this.connected = false; },
  onMount(el) { this._el = el; },
  onUnmount() { this._el = null; },
};

Alpine.store("intelligence", model);
export const store = model;
```

To open programmatically from anywhere:
```javascript
import { store as rightCanvasStore } from "/components/canvas/right-canvas-store.js";
await rightCanvasStore.open("intelligence", { /* payload */ });
```

---

## Key Constants

| Constant | Value | Location | Meaning |
|----------|-------|----------|---------|
| `VIEWPORT_SYNC_DEBOUNCE_MS` | 220ms | browser-store.js | Resize debounce before requesting viewport sync |
| `VIEWPORT_SYNC_SIZE_TOLERANCE` | 4px | browser-store.js | Frame dimension mismatch tolerance |
| `SURFACE_VIEWPORT_STABLE_FRAMES` | 2 | register-browser.js | Stable frames before open() fires |
| `AUTO_OPEN_WINDOW_MS` | 10 min | browser-tool-handler.js | Age threshold for auto-opening canvas |
| `PREVIEW_REFRESH_MS` | 2500ms | browser-tool-handler.js | Thumbnail refresh rate in chat messages |
| `PREVIEW_QUALITY` | 62 | browser-tool-handler.js | JPEG quality for chat thumbnails |
| `PREVIEW_FRAME_LIMIT` | 16 | browser-tool-handler.js | Max concurrent live thumbnail frames |

---

## What We Know About the Old emit_artifact Approach

Our previous `emit_artifact` tool created a `type="artifact"` log entry per message. The artifact handler routed it to `window.artifactPanel.update()`. The problems:

1. **Not a registered surface** — `window.artifactPanel` was a manual injection, not a first-class canvas surface. It had no stable lifecycle (no `open`/`close`/`x-create`/`x-destroy` hooks).
2. **Per-message recreation** — each artifact emission tried to update a shared panel, causing race conditions when multiple tools ran.
3. **Alpine reinit** — because the HTML was injected as content (not as a stable DOM element in the canvas slot), Alpine's lifecycle hooks fired unreliably on each update.

The v1.13 surface registration system solves all three. The panel is registered once at page load, has stable DOM lifecycle, and data is pushed into it rather than the panel being rebuilt per message. Our existing `emit_artifact` tool and `artifact-handler.js` are still valid for simple one-off HTML panels in the chat log — they just shouldn't be used as the primary UI surface for a persistent dashboard.
