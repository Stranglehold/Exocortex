# Theme Editor — Specification

**Status:** Ready to build
**Priority:** UI quality-of-life
**Scope:** In-browser visual editor for Exocortex theme JSON files

---

## Problem

Theme customization currently requires hand-editing JSON files and reloading the browser. Opacity values are not intuitive without live feedback. Image positioning requires trial-and-error. Widget placement has no visual reference. The workflow is inaccessible to anyone who didn't write the theme engine.

---

## Solution

A collapsible editor panel in the Agent Zero webUI that exposes all theme parameters as live controls. Every change is reflected immediately in the background via `ThemeEngine.apply(draftConfig)`. Saving writes the JSON back to the server.

---

## Architecture

### Data flow

```
[Editor UI controls]
      ↓  onChange
[draftConfig object]  ←  deep copy of loaded theme JSON
      ↓  ThemeEngine.apply(draftConfig)
[Live preview — no page reload]
      ↓  on Save
[POST /api/themes/save  { name, config }]
      ↓
[Server writes /a0/webui/themes/{name}.json]
```

### Components

| Component | File | Role |
|-----------|------|------|
| Editor panel HTML | `webui/theme-editor.html` (fragment injected into index) | Structure |
| Editor logic | `webui/js/theme-editor.js` | Controls, state, save |
| Save endpoint | `webui/server_extension.py` or patched into `run_ui.py` | Flask route |
| Image upload | Same Flask endpoint, multipart | Asset management |

---

## UI Layout

Triggered by a small edit icon (✏) next to the active theme name in the sidebar.
Opens as a **right-side drawer** (360px wide), scrollable, non-modal — user can still chat while editing.

### Sections

#### 1. Header
- Theme name (editable text field)
- `[ Save ]` `[ Reset ]` `[ Export JSON ]` buttons
- Active theme indicator

#### 2. Background
```
Image source:  [ /themes/assets/mgs-delta...  ] [Browse...]
Opacity:       [========•==] 0.55
Blur:          [===•=======] 5px
Position:      [ center ▼ ]   (center / top / bottom / top left / top right / custom)
Size:          [ cover  ▼ ]   (cover / contain / auto / [custom %])
```
Browse opens a file picker. Selected file is uploaded to `/a0/webui/themes/assets/` via POST, then src is updated.

#### 3. Panels
```
Panel opacity:     [=======•===] 0.60
Backdrop blur:     [==•========] 2px
```
Live: updates `#left-panel, .right-panel, #input-section` CSS in real time.

#### 4. Overlays
```
Scanlines:   [ off ● ] opacity [===] spacing [===]
Noise:       [ off ● ] opacity [===]
Vignette:    [ on  ● ] opacity [========•==]
Watermark:   [ on  ● ]
  └ Image:   [ FOX_logo...  ] [Browse...]
  └ Opacity: [==•========] 0.08
  └ Position:[ top right ▼ ]
  └ Size:    [===•=======] 11%
  └ Blend:   [ multiply ▼ ]  (normal / multiply / screen / overlay)
```

Blend mode exposed as a dropdown. Solves the white-background PNG problem visually — user can switch to multiply and see it live.

#### 5. Widgets
Collapsible list. Each widget shows:
```
[Widget type: corner-label]  [✕ remove]
  Position:  [ bottom-right ▼ ]
  Text:      [ FREQ: 140.85        ]
  Color:     [🟧 #a08860 ]
  Font size: [ 11px ]
```
`[+ Add widget]` button opens a type picker.

#### 6. Colors (collapsed by default)
Grid of color swatches for all named color keys (`background`, `accent`, `text`, etc.). Each swatch opens a color picker on click.

#### 7. Animation / Effects
```
Animation type:  [ none    ▼ ]
Cursor trail:    [ sparks  ▼ ]  color [🟧]  intensity [===•=]
Message reveal:  [ scan    ▼ ]  speed [====•]
Idle escalation: [ on  ● ]  threshold [ 5 ] min  message [ CODEC SIGNAL LOST ]
```

---

## Save Endpoint

**Route:** `POST /api/themes/save`
**Auth:** Same X-API-KEY header as `/api_message`
**Body:**
```json
{
  "filename": "codec.json",
  "config": { ...full theme JSON... }
}
```
**Response:** `{ "ok": true }` or `{ "error": "..." }`

**Server logic (Flask, ~15 lines):**
```python
@app.route('/api/themes/save', methods=['POST'])
def save_theme():
    key = request.headers.get('X-API-KEY', '')
    if key != get_auth_token():
        return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json()
    filename = data.get('filename', '').replace('..', '').replace('/', '')
    if not filename.endswith('.json'):
        return jsonify({'error': 'invalid filename'}), 400
    path = os.path.join(WEBUI_DIR, 'themes', filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data['config'], f, indent=2, ensure_ascii=False)
    return jsonify({'ok': True})
```

Path traversal is blocked by stripping `..` and `/`. Only `.json` files accepted.

---

## Image Upload Endpoint

**Route:** `POST /api/themes/upload`
**Body:** `multipart/form-data`, field `file`
**Saves to:** `/a0/webui/themes/assets/{original_filename}`
**Returns:** `{ "src": "/themes/assets/filename.png" }`

Allowed extensions: `.jpg .jpeg .png .webp .svg .gif`
Size limit: 10MB (configurable)

---

## Live Preview Implementation

`theme-editor.js` maintains a `draftConfig` object. On every control change:

```javascript
function applyDraft() {
    ThemeEngine.apply(draftConfig);
}
```

`ThemeEngine.apply()` already handles full re-render. The editor just feeds it a modified config object — no reload, no flicker on most changes (background swaps will flash briefly).

For color changes, a more targeted path updates only the CSS custom properties rather than full re-render.

---

## State Management

- On open: `draftConfig = JSON.parse(JSON.stringify(ThemeEngine.currentConfig))`  — deep copy, no mutation of live config
- Reset: re-copy from `ThemeEngine.currentConfig`
- Save: POST draftConfig, on success `ThemeEngine.currentConfig = draftConfig`
- Unsaved changes indicator: compare draftConfig to currentConfig (JSON.stringify both)

---

## File Structure

```
patches/webui/
  js/
    theme-editor.js       ← new
  theme-editor-panel.html ← new (injected fragment)
  themes/
    (JSON files, already exist)
patches/
  run_ui_theme_patch.py   ← new Flask routes (2 endpoints)
scripts/
  install_theme_editor.sh ← new install script
```

---

## Install Script

```bash
#!/bin/bash
CONTAINER="flamboyant_bell"
WEBUI="/a0/webui"

docker cp patches/webui/js/theme-editor.js        $CONTAINER:$WEBUI/js/theme-editor.js
docker cp patches/webui/theme-editor-panel.html   $CONTAINER:$WEBUI/theme-editor-panel.html
docker cp patches/run_ui_theme_patch.py            $CONTAINER:/a0/python/run_ui_theme_patch.py

# Inject script tag into index.html if not already present
docker exec $CONTAINER python3 -c "
import re
path = '$WEBUI/index.html'
html = open(path).read()
tag = '<script src=\"/js/theme-editor.js\"></script>'
if tag not in html:
    html = html.replace('</body>', tag + '\n</body>')
    open(path, 'w').write(html)
    print('Injected theme-editor.js')
else:
    print('Already injected')
"

echo "Theme editor installed. Restart container to activate Flask routes."
```

---

## What This Does NOT Do

- Does not modify the base Agent Zero source files (all patched via extension points)
- Does not provide a "create new theme from scratch" wizard — editing existing themes only
- Does not sync changes across multiple browser tabs (last save wins)
- Does not version-control theme history (that's what git is for)
- Does not support animated GIF backgrounds or video (the `weapons_nocursor.mp4` in assets is out of scope for this editor)

---

## Build Order

1. Flask endpoints (`run_ui_theme_patch.py`) — 30 lines, testable with curl
2. `ThemeEngine.apply()` audit — confirm it handles full config re-render cleanly
3. Editor panel HTML structure — static, no logic
4. `theme-editor.js` — controls → draftConfig → applyDraft loop
5. Save/reset wiring
6. Image upload + browse button
7. Widget add/remove
8. Color picker integration (browser native `<input type="color">` is sufficient)

Steps 1–5 are the useful MVP. Steps 6–8 are polish.
