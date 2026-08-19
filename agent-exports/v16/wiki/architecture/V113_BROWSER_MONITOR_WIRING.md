# V1.13 Browser Monitor Pipeline — Wiring Reference

*How the live browser tab view works: from CDP screencast to `<img>` tag.*

**Companion to:** [V113_UI_PANEL_SYSTEM_WIRING.md](V113_UI_PANEL_SYSTEM_WIRING.md)

---

## Overview

The browser panel shows a live ~20fps JPEG stream of whatever browser tab the agent is using. This is not a screenshot-on-demand system — it is a genuine streaming pipeline powered by Chrome's CDP (Chrome DevTools Protocol) `Page.Screencast` API.

```
Playwright Page (CDP)
  │  Page.startScreencast → JPEG frames at quality=92, everyNthFrame=1
  │  Page.screencastFrameAck → keeps CDP sending more frames
  ▼
_BrowserScreencast (runtime.py)
  │  asyncio.Queue (latest-frame-only: drops stale frames on push)
  │  _on_frame CDP callback → _handle_frame task → _queue_latest
  ▼
BrowserRuntime.pop_screencast_frame()  ← polled every 50ms (FRAME_IDLE_POLL_SECONDS)
  ▼
_stream_frames() asyncio task (ws_browser.py)
  │  emit_to(sid, "browser_viewer_frame", {image, mime, state, browsers, ...})
  ▼
Socket.io WebSocket → browser namespace (/ws)
  ▼
browser-store.js frame handler
  │  queueFrameRender() → requestAnimationFrame → flushFrameRender()
  │  renderDecodedFrame() → loadFrameDimensions() → viewport check
  │  store.frameSrc = "data:image/jpeg;base64,..."
  ▼
<img :src="$store.browserStore.frameSrc"> in browser-panel.html
```

---

## Key Constants

All constants are defined at the top of their respective files.

### Backend — `ws_browser.py`
| Constant | Value | Meaning |
|---|---|---|
| `FRAME_IDLE_POLL_SECONDS` | `0.05` | How often to call `pop_screencast_frame` when queue is empty (50ms) |
| `FRAME_RETRY_DELAY_SECONDS` | `0.5` | Sleep before retry when browser/runtime is unavailable |
| `FRAME_STATE_REFRESH_SECONDS` | `0.75` | How often to re-query tab listing mid-stream |
| `SCREENCAST_QUALITY` | `92` | JPEG quality sent to `Page.startScreencast` |

### Backend — `runtime.py`
| Constant | Value | Meaning |
|---|---|---|
| `SCREENCAST_MAX_WIDTH` | `4096` | CDP screencast max dimension cap |
| `SCREENCAST_MAX_HEIGHT` | `4096` | CDP screencast max dimension cap |
| `DEFAULT_VIEWPORT` | `{"width": 1280, "height": 800}` | Fallback viewport if none specified |

### Frontend — `browser-store.js`
| Constant | Value | Meaning |
|---|---|---|
| `BROWSER_SUBSCRIBE_TIMEOUT_MS` | `60000` | Timeout for initial `browser_viewer_subscribe` WebSocket request |
| `BROWSER_CONFIG_REFRESH_MS` | `15000` | How long browser extension config is cached (15s) |
| `VIEWPORT_SYNC_DEBOUNCE_MS` | `220` | Debounce delay before sending viewport resize to backend |
| `VIEWPORT_SYNC_SIZE_TOLERANCE` | `4` | ±px tolerance for frame dimension matching |
| `CANVAS_VIEWPORT_SETTLE_MS` | `520` | Wait after surface opens before measuring viewport |
| `SURFACE_VIEWPORT_STABLE_FRAMES` | `4` | Consecutive frames with same size = stable |
| `SURFACE_VIEWPORT_MAX_WAIT_MS` | `1200` | Max time waiting for viewport to stabilize |
| `FRAME_REJECT_SYNC_COOLDOWN_MS` | `600` | Min time between viewport syncs after rejected frame |

---

## Backend Pipeline in Detail

### Step 1: CDP Screencast Start (`runtime.py`)

`_BrowserScreencast.start()` sends two CDP commands:

```python
# 1. Set the browser viewport dimensions via Emulation API
await session.send("Emulation.setDeviceMetricsOverride", {
    "width": width, "height": height,
    "deviceScaleFactor": 1, "mobile": False,
})

# 2. Start the screencast stream
await session.send("Page.startScreencast", {
    "format": "jpeg",
    "quality": 92,        # SCREENCAST_QUALITY
    "maxWidth": 4096,     # SCREENCAST_MAX_WIDTH
    "maxHeight": 4096,    # SCREENCAST_MAX_HEIGHT
    "everyNthFrame": 1,   # every frame (≈20fps)
})
```

**Viewport remount quirk:** Before starting screencast, the viewport is set three times with a nudge in the middle (`_apply_cdp_viewport_with_remount`). This forces Chrome to repaint and stabilize before streaming begins. Each step has a small `VIEWPORT_REMOUNT_PAUSE_SECONDS` sleep.

### Step 2: CDP Frame → asyncio Queue

CDP fires `Page.screencastFrame` events. The handler:

```python
def _on_frame(self, params):
    task = asyncio.create_task(self._handle_frame(params))

async def _handle_frame(self, params):
    data = params.get("data")  # base64 JPEG
    metadata = params.get("metadata")  # {timestamp, pageScaleFactor, ...}
    # Decode JPEG header to get actual dimensions
    size = self._jpeg_size(data)
    metadata["jpegWidth"], metadata["jpegHeight"] = size
    metadata["expectedWidth"] = self._expected_width
    metadata["expectedHeight"] = self._expected_height
    # Drop any queued frame, put this one in
    self._queue_latest({"browser_id": ..., "mime": "image/jpeg",
                        "image": data, "metadata": metadata})
    # ACK so CDP sends the next frame
    await session.send("Page.screencastFrameAck", {"sessionId": sessionId})
```

**Latest-frame-only queue:** `_queue_latest()` calls `_drop_queued_frames()` before enqueuing. The queue holds at most 1 frame — if the consumer is slow, stale frames are dropped rather than accumulated. This keeps the live view current at the cost of potentially skipping frames.

### Step 3: `_stream_frames()` — The Polling Loop (`ws_browser.py`)

This is an `asyncio.Task` created per (sid, context_id) pair when a client subscribes:

```python
async def _stream_frames(self, sid, context_id, browser_id, viewer_id):
    while True:
        # Get the runtime (Playwright browser wrapper)
        runtime = await get_runtime(context_id, create=False)

        # Start the CDP screencast
        screencast = await runtime.call("start_screencast", active_id,
            quality=SCREENCAST_QUALITY, every_nth_frame=1)
        stream_id = screencast["stream_id"]

        # Inner loop: poll for frames
        last_state_refresh = 0.0
        while True:
            now = time.monotonic()
            # Refresh tab listing every 750ms
            if now - last_state_refresh >= FRAME_STATE_REFRESH_SECONDS:
                listing = await runtime.call("list")
                browsers = listing.get("browsers") or []
                # If active tab closed, break to outer loop
                if str(active_id) not in {str(b["id"]) for b in browsers}:
                    break
                state = self._state_for_browser(browsers, active_id, state)
                last_state_refresh = now

            # Poll queue — non-blocking (pop_frame returns None if empty)
            frame = await runtime.call("pop_screencast_frame", stream_id)
            if frame is None:
                await asyncio.sleep(FRAME_IDLE_POLL_SECONDS)  # 50ms
                continue

            # Attach routing metadata and emit
            frame["context_id"] = context_id
            frame["viewer_id"] = viewer_id
            frame["browser_id"] = active_id
            frame["browsers"] = browsers
            frame["state"] = state
            frame["frame_source"] = "screencast"
            await self.emit_to(sid, "browser_viewer_frame", frame)
```

**Cancellation:** `_streams` is a class-level dict keyed by `(sid, context_id)`. On `browser_viewer_unsubscribe` or disconnect, the task is cancelled. The `finally` block sends `Page.stopScreencast`.

### Step 4: Socket.io Emission

`emit_to(sid, "browser_viewer_frame", frame)` sends via the `/ws` Socket.io namespace. The frame payload:

```json
{
  "context_id": "abc123",
  "viewer_id": "uuid-token",
  "browser_id": 1,
  "browsers": [{"id": 1, "currentUrl": "https://...", "title": "..."}],
  "state": {"id": 1, "currentUrl": "https://...", "title": "..."},
  "frame_source": "screencast",
  "image": "<base64 JPEG>",
  "mime": "image/jpeg",
  "metadata": {
    "timestamp": 1234567890.0,
    "jpegWidth": 1280,
    "jpegHeight": 800,
    "expectedWidth": 1280,
    "expectedHeight": 800
  }
}
```

---

## Frontend Pipeline in Detail

### Step 5: WebSocket Subscription (`browser-store.js`)

When the browser surface opens, `connectViewer()` is called:

```javascript
// 1. Register frame listener (once per surface mount)
const frameHandler = ({ data }) => {
    // Filter by viewer_id to ignore frames from other subscriptions
    if (data?.viewer_id && data.viewer_id !== this._viewerToken) return;
    // Filter by browser_id to ignore frames from non-active tab
    if (incomingBrowserId && this.activeBrowserId
        && !this.sameBrowserTab(...)) return;

    if (data.state) this.frameState = data.state;
    if (!this.addressFocused && data.state?.currentUrl)
        this.address = data.state.currentUrl;

    if (data.image) {
        this.queueFrameRender(
            `data:${data.mime || "image/jpeg"};base64,${data.image}`,
            { browserId, contextId, onAccepted: () => { ... } }
        );
    }
};
await websocket.on("browser_viewer_frame", frameHandler);

// 2. Send subscribe request to backend
const response = await websocket.request("browser_viewer_subscribe", {
    context_id: contextId,
    browser_id: requestedBrowserId,
    viewer_id: this._viewerToken,         // UUID — filters out stale frames
    viewport_width: viewport.width,
    viewport_height: viewport.height,
}, { timeoutMs: BROWSER_SUBSCRIBE_TIMEOUT_MS });
```

**Viewer token:** Each surface open generates a fresh UUID (`makeViewerToken()`). The backend echoes this in every frame. The frontend ignores frames whose `viewer_id` doesn't match — prevents stale subscriptions from bleeding into new ones.

### Step 6: requestAnimationFrame Queue

Frames don't update `frameSrc` directly — they go through an rAF-synchronized render queue:

```javascript
queueFrameRender(frameSrc, options) {
    // Always replace pending — keeps only the latest
    this._pendingFrameSrc = frameSrc;
    this._pendingFrameOptions = options;
    // Schedule one rAF flush if none pending
    if (this._frameRenderHandle) return;
    this._frameRenderHandle = requestAnimationFrame(
        () => this.flushFrameRender()
    );
},

flushFrameRender() {
    // Increment sequence — in-flight decodes with old sequence are abandoned
    const sequence = ++this._frameRenderSequence;
    const frameSrc = this._pendingFrameSrc;
    this._pendingFrameSrc = "";
    void this.renderDecodedFrame(frameSrc, options, sequence);
},
```

Multiple incoming frames coalesce into a single rAF slot. If 3 frames arrive before the next animation frame fires, only the last one is rendered.

### Step 7: Viewport Dimension Check

Before updating `frameSrc`, the frame is validated against the expected viewport:

```javascript
async renderDecodedFrame(frameSrc, options, sequence) {
    // Decode image to get natural dimensions
    const dimensions = await loadFrameDimensions(frameSrc);

    // Abandon if a newer frame arrived while we were decoding
    if (sequence !== this._frameRenderSequence) return;

    const viewport = this.currentViewportSize();
    if (!this.frameMatchesViewport(dimensions, viewport)) {
        // Frame dimensions don't match — request viewport sync and discard
        this.requestViewportSyncAfterRejectedFrame();
        return;
    }

    // Accept the frame
    this.frameSrc = frameSrc;
    this._lastFrameDimensions = dimensions;
    options?.onAccepted?.();
},

frameMatchesViewport(dimensions, viewport) {
    return (
        Math.abs(dimensions.width - viewport.width) <= VIEWPORT_SYNC_SIZE_TOLERANCE   // ±4px
        && Math.abs(dimensions.height - viewport.height) <= VIEWPORT_SYNC_SIZE_TOLERANCE
    );
},
```

**Why this matters:** If the user resizes the right canvas panel, the backend hasn't caught up yet. Frames from the old viewport size are rejected until the backend acknowledges the new size.

---

## Viewport Sync Protocol

This is how panel size and browser viewport stay in sync.

### Frontend → Backend (on resize)

A `ResizeObserver` watches the panel's `.browser-stage` element. On resize:

1. 220ms debounce (`VIEWPORT_SYNC_DEBOUNCE_MS`) fires
2. If size changed by more than ±4px (`VIEWPORT_SYNC_SIZE_TOLERANCE`)
3. Send `browser_viewer_input` with `input_type: "viewport"`:

```javascript
await websocket.request("browser_viewer_input", {
    context_id: this.contextId,
    browser_id: this.activeBrowserId,
    input_type: "viewport",
    width: newWidth,
    height: newHeight,
    restart_stream: true,   // force screencast restart at new size
}, { timeoutMs: 10000 });
```

### Backend — Viewport Application (`runtime.py`)

`set_viewport()` calls `_apply_cdp_viewport_with_remount()` which sets `Emulation.setDeviceMetricsOverride` three times (set → nudge → set) to force Chrome to repaint, then stops and restarts the screencast at the new dimensions.

### Frame Rejection Loop

When a resized frame arrives before the backend catches up:
1. Frame dimensions don't match viewport → `renderDecodedFrame` rejects it
2. `requestViewportSyncAfterRejectedFrame()` fires (gated by 600ms cooldown: `FRAME_REJECT_SYNC_COOLDOWN_MS`)
3. Sends another viewport sync to backend
4. Process repeats until frames match

---

## Tab Listing — Cross-Context Aggregation

The `browsers` array in every frame/state payload contains tabs from **all** browser runtimes across **all** agent contexts, not just the current one. This is how the tab bar at the top of the browser panel shows every open browser.

Backend aggregation in `ws_browser.py`:

```python
async def _all_browser_tabs(self) -> list[dict]:
    browsers = []
    for session in await list_runtime_sessions():  # all contexts
        context_id = str(session.get("context_id") or "")
        for browser in session.get("browsers") or []:
            entry = dict(browser or {})
            entry.setdefault("context_id", context_id)
            browsers.append(entry)
    return browsers
```

Each browser tab entry:
```json
{
  "id": 1,
  "context_id": "abc123",
  "currentUrl": "https://example.com",
  "title": "Example Domain",
  "favicon": "data:image/png;base64,...",
  "loading": false
}
```

Tab state refreshes every `FRAME_STATE_REFRESH_SECONDS` (750ms) during streaming.

---

## Snapshot Endpoint (for Chat Thumbnails)

The `browser_viewer_snapshot` WebSocket event is separate from the streaming pipeline. It's used by `browser-tool-handler.js` to show screenshots in chat message thumbnails — a one-shot request, not a stream.

```javascript
// In browser-tool-handler.js (chat message rendering)
const response = await websocket.request("browser_viewer_snapshot", {
    context_id: contextId,
    browser_id: browserId,
    quality: 75,     // lower quality for thumbnails
}, { timeoutMs: 10000 });
const snapshot = firstOk(response)?.snapshot;
// snapshot.image = base64 JPEG
// snapshot.mime  = "image/jpeg"
```

Backend: `_snapshot()` in `ws_browser.py` calls `runtime.call("screenshot", browser_id, quality=quality)` — a single CDP screenshot, not a screencast frame.

**Chat thumbnail refresh cycle:** `browser-tool-handler.js` polls this endpoint every ~2.5 seconds while the tool message is visible, using a shimmer animation placeholder while loading.

---

## Interactive Input — User Controls the Browser

The browser panel supports mouse, keyboard, scroll, and clipboard input sent back to the agent's browser. These go through `browser_viewer_input`:

| `input_type` | Parameters | CDP equivalent |
|---|---|---|
| `mouse` | `event_type`, `x`, `y`, `button` | `page.mouse.*` |
| `keyboard` | `key`, `text` | `page.keyboard.*` |
| `wheel` | `x`, `y`, `delta_x`, `delta_y` | `page.mouse.wheel()` |
| `clipboard` | `action`, `text` | `page.evaluate()` |
| `viewport` | `width`, `height`, `restart_stream` | `Emulation.setDeviceMetricsOverride` |

These go through `_input()` in `ws_browser.py` → `runtime.call(...)`.

Note: mouse input returns a snapshot (one-shot screenshot) so the user can see what changed immediately, without waiting for the next screencast frame.

---

## Browser Command Events

Navigation commands (open, navigate, back, forward, reload, close) go through `browser_viewer_command`. Unlike input events, commands emit a separate `browser_viewer_state` event to all subscribers in addition to returning a response:

```python
# ws_browser.py _command()
await self.emit_to(sid, "browser_viewer_state", {
    "context_id": context_id,
    "viewer_id": viewer_id,
    "command": command,
    "result": result,
    "snapshot": snapshot,
    "browsers": all_browsers,
    "last_interacted_browser_id": last_interacted_id,
})
```

The frontend `stateHandler` updates the tab listing and active browser state from this event.

---

## WsBrowser Registration

`WsBrowser` is a `WsHandler` subclass. It registers itself by being imported in the plugin's hooks:

```python
# /a0/plugins/_browser/hooks.py
from plugins._browser.api.ws_browser import WsBrowser

# Agent Zero discovers WsHandler subclasses and routes /ws events to them
```

The `/ws` Socket.io namespace is shared across all plugins. `WsBrowser.process()` claims events prefixed with `browser_` and returns `None` for everything else, passing them on to the next handler.

---

## Python Extension Hooks

Two Python extensions in `extensions/python/` complete the browser plugin's backend wiring:

### `webui_ws_event/_50_browser.py`
Fires when any WebSocket message arrives at the server. Handles `browser_action` events that arrive from the UI (distinct from the `browser_viewer_*` events handled by `WsBrowser`).

### `webui_ws_disconnect/_50_browser.py`
Fires when a WebSocket client disconnects. Cleans up any screencast streams tied to that session ID — prevents background streaming tasks from running indefinitely for disconnected clients.

---

## Building Your Own Streaming Panel

To add a panel that streams live data (e.g., OSS ingestion feed, SWARMFISH prediction updates), the browser panel is the reference pattern:

**Backend pattern:**
1. Create a `WsHandler` subclass in `your_plugin/api/ws_yourplugin.py`
2. Claim events with a unique prefix (`yourplugin_*`)
3. For streaming: create an `asyncio.Task` per subscriber, emit events with `emit_to(sid, event, data)`
4. Cancel tasks on `on_disconnect(sid)` and on explicit unsubscribe
5. Register via `hooks.py` import

**Frontend pattern:**
1. Subscribe in `onOpen()`, unsubscribe in `onClose()`
2. Use `websocket.on("yourplugin_update", handler)` for streaming
3. Use `websocket.request("yourplugin_query", data, {timeoutMs})` for request-response
4. Store the cleanup function: `this._off = () => websocket.off(...)`

**Key difference from browser:** For data feeds (not video), skip the viewport sync, rAF queue, and dimension check. Just update reactive Alpine state directly in the WebSocket handler.

---

## File Map

| File | Layer | Purpose |
|---|---|---|
| `plugins/_browser/helpers/runtime.py` | CDP | `_BrowserScreencast` class, `start_screencast()`, `pop_screencast_frame()`, `set_viewport()` |
| `plugins/_browser/api/ws_browser.py` | WebSocket | `WsBrowser` handler, `_stream_frames()` task, event routing |
| `plugins/_browser/webui/browser-store.js` | Alpine Store | `frameHandler`, `queueFrameRender()`, `renderDecodedFrame()`, viewport sync |
| `plugins/_browser/extensions/webui/right_canvas_register_surfaces/register-browser.js` | Surface | Surface registration, `open()`/`close()` lifecycle, `connectViewer()` call |
| `plugins/_browser/extensions/webui/get_tool_message_handler/browser-tool-handler.js` | Chat | Chat thumbnail snapshots, "Open Browser" button, tool message override |
| `plugins/_browser/extensions/webui/set_messages_after_loop/auto-open-browser-results.js` | Auto-sync | Auto-opens browser surface after focus actions |
| `plugins/_browser/extensions/python/webui_ws_disconnect/_50_browser.py` | Cleanup | Cancels streams on client disconnect |

---

*Written 2026-05-05. v1.13 source. CDP screencast is Playwright's `Page.Screencast` CDP domain. Alpine store pattern matches `right-canvas-store.js` for right-canvas integration. See V113_UI_PANEL_SYSTEM_WIRING.md for surface registration and panel injection.*
