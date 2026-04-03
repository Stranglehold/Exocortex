/**
 * Exocortex Theme Editor v2
 * Professional visual editor for Exocortex theme JSON files.
 *
 * Tabs: Colors · Background · Panel · Overlays · Fonts
 *
 * Features:
 *   - Semantic color groups with alpha-channel support
 *   - Copy-to-clipboard on hex values
 *   - Background image upload via drag-and-drop or file browser
 *   - Live preview pane for background image + opacity/blur
 *   - Slider + number input pairs for precision control
 *   - Overlay effects (scanlines, vignette, noise)
 *   - Font stack editor with preset chips and live preview
 *   - CSRF-safe save and upload via A0's fetchApi
 *
 * Usage (from theme-picker.html):
 *   import { ThemeEditor } from "/usr/plugins/exocortex/webui/theme-editor.js";
 *   ThemeEditor.open("shadow-moses");
 *   window.ThemeEditor = ThemeEditor;
 */

import { fetchApi } from "/js/api.js";

// ─── Constants ────────────────────────────────────────────────────────────────

const THEMES_URL  = "/usr/plugins/exocortex/webui/themes/";
const SAVE_URL    = "/api/plugins/exocortex/api_theme_save";
const UPLOAD_URL  = "/api/plugins/exocortex/api_theme_upload";

const COLOR_GROUPS = [
  {
    label: "Page",
    keys: [
      ["background",      "Background"],
      ["chat-background", "Chat Area"],
      ["secondary",       "Secondary"],
    ],
  },
  {
    label: "Text",
    keys: [
      ["text",          "Primary Text"],
      ["text-muted",    "Muted Text"],
      ["message-text",  "Message Text"],
      ["error-text",    "Error"],
      ["warning-text",  "Warning"],
    ],
  },
  {
    label: "Interface",
    keys: [
      ["panel",       "Panel"],
      ["border",      "Border"],
      ["input",       "Input BG"],
      ["input-focus", "Input Focus"],
      ["table-row",   "Table Row"],
    ],
  },
  {
    label: "Accent",
    keys: [
      ["primary",    "Primary"],
      ["accent",     "Accent"],
      ["highlight",  "Highlight"],
      ["message-bg", "Message BG"],
    ],
  },
];

const SIZE_OPTIONS    = ["cover", "contain", "auto", "50%", "75%", "100%"];
const BLEND_OPTIONS   = ["normal", "overlay", "multiply", "screen", "soft-light", "color-dodge"];
const FONT_PRESETS    = [
  ["System",    "system-ui, -apple-system, sans-serif"],
  ["Monospace", "'Courier New', 'Roboto Mono', monospace"],
  ["Codec",     "'Courier New', monospace"],
  ["Interface", "'Roboto', 'Segoe UI', sans-serif"],
  ["Tactical",  "'Share Tech Mono', 'Courier New', monospace"],
];

const POSITION_SNAP = [
  ["↖", "top left"],    ["↑", "top center"],    ["↗", "top right"],
  ["←", "center left"], ["·", "center"],         ["→", "center right"],
  ["↙", "bottom left"], ["↓", "bottom center"],  ["↘", "bottom right"],
];

// ─── Color Utilities ──────────────────────────────────────────────────────────

function parseHex(raw) {
  const s = (raw || "#000000").trim();
  if (s.length === 9) return { rgb: s.substring(0, 7), alpha: parseInt(s.substring(7), 16) / 255 };
  if (s.length === 7) return { rgb: s, alpha: 1 };
  return { rgb: "#000000", alpha: 1 };
}

function combineHex(rgb, alpha) {
  if (alpha >= 0.999) return rgb;
  const a = Math.round(Math.max(0, Math.min(1, alpha)) * 255).toString(16).padStart(2, "0");
  return rgb + a;
}

// ─── ThemeEditor ──────────────────────────────────────────────────────────────

export const ThemeEditor = {

  // ── State ──────────────────────────────────────────────────────────────────

  _overlay:    null,
  _draft:      null,
  _original:   null,
  _themeName:  null,
  _activeTab:  "colors",
  _dirty:      false,
  _initialized: false,
  _bgPreviewEl: null,   // reference to live-update background preview div

  // ── Bootstrap ──────────────────────────────────────────────────────────────

  _ensureInit() {
    if (this._initialized) return;
    this._initialized = true;
    this._injectStyles();
    this._injectOverlay();
  },

  // ── Open / Close ───────────────────────────────────────────────────────────

  async open(themeName) {
    this._ensureInit();
    if (!themeName) return;
    try {
      const resp = await fetch(THEMES_URL + themeName + ".json");
      if (!resp.ok) throw new Error(`Could not load "${themeName}"`);
      const config = await resp.json();

      this._themeName = themeName;
      this._draft     = JSON.parse(JSON.stringify(config));
      this._original  = JSON.parse(JSON.stringify(config));
      this._dirty     = false;
      this._activeTab = "colors";
      this._bgPreviewEl = null;

      this._renderAll();
      this._overlay.classList.remove("te-hidden");
    } catch (err) {
      console.error("[ThemeEditor]", err);
      alert(`Could not open theme: ${err.message}`);
    }
  },

  close() {
    if (this._overlay) this._overlay.classList.add("te-hidden");
  },

  _cancel() {
    if (this._dirty && !confirm("Discard unsaved changes?")) return;
    this._restoreOriginal();
    this.close();
  },

  _restoreOriginal() {
    if (!this._original) return;
    const root = document.documentElement;
    const colors = this._original.colors || {};
    for (const grp of COLOR_GROUPS) {
      for (const [key] of grp.keys) {
        if (colors[key]) {
          root.style.setProperty(`--color-${key}-dark`,  colors[key]);
          root.style.setProperty(`--color-${key}-light`, colors[key]);
        } else {
          root.style.removeProperty(`--color-${key}-dark`);
          root.style.removeProperty(`--color-${key}-light`);
        }
      }
    }
    const fonts = this._original.fonts || {};
    if (fonts.main) root.style.setProperty("--font-family-main", fonts.main);
    if (fonts.code) root.style.setProperty("--font-family-code", fonts.code);
  },

  // ── Render ─────────────────────────────────────────────────────────────────

  _renderAll() {
    // Header name
    const nameEl = this._overlay.querySelector("#te-name");
    if (nameEl) nameEl.textContent = (this._draft.name || this._themeName || "").toUpperCase();
    const fileEl = this._overlay.querySelector("#te-filename");
    if (fileEl) fileEl.textContent = this._themeName + ".json";

    // Tab active state
    this._overlay.querySelectorAll(".te-tab").forEach(t =>
      t.classList.toggle("te-tab-active", t.dataset.tab === this._activeTab)
    );

    // Dirty indicator
    this._syncDirtyUI();

    // Tab content
    const content = this._overlay.querySelector("#te-content");
    content.innerHTML = "";
    const frag = this._buildTab(this._activeTab);
    if (frag) content.appendChild(frag);
  },

  _buildTab(tab) {
    switch (tab) {
      case "colors":     return this._tabColors();
      case "background": return this._tabBackground();
      case "panel":      return this._tabPanel();
      case "overlays":   return this._tabOverlays();
      case "fonts":      return this._tabFonts();
      default:           return null;
    }
  },

  // ── Tab: Colors ────────────────────────────────────────────────────────────

  _tabColors() {
    const colors = (this._draft.colors = this._draft.colors || {});
    const root   = document.createDocumentFragment();

    for (const group of COLOR_GROUPS) {
      root.appendChild(this._sectionHdr(group.label));

      const grid = document.createElement("div");
      grid.className = "te-color-grid";

      for (const [key, label] of group.keys) {
        grid.appendChild(this._colorRow(key, label, colors[key] || "#000000"));
      }

      root.appendChild(grid);
    }

    return root;
  },

  _colorRow(key, label, rawValue) {
    const { rgb, alpha } = parseHex(rawValue);

    const row = document.createElement("div");
    row.className = "te-color-row";

    // Color swatch (picker — RGB only)
    const swatch = document.createElement("input");
    swatch.type      = "color";
    swatch.value     = rgb;
    swatch.className = "te-swatch";
    swatch.title     = `--color-${key}`;

    // Label
    const lbl = document.createElement("span");
    lbl.className   = "te-color-label";
    lbl.textContent = label;

    // Hex text field (full 6 or 8 char)
    const hexInput = document.createElement("input");
    hexInput.type       = "text";
    hexInput.value      = rawValue || "#000000";
    hexInput.maxLength  = 9;
    hexInput.className  = "te-hex-input";
    hexInput.spellcheck = false;
    hexInput.autocomplete = "off";

    // Alpha badge (only shown if < 1)
    const alphaBadge = document.createElement("span");
    alphaBadge.className   = "te-alpha-badge";
    alphaBadge.title       = "Alpha channel present";
    alphaBadge.textContent = alpha < 0.999 ? Math.round(alpha * 100) + "%" : "";
    alphaBadge.style.display = alpha < 0.999 ? "" : "none";

    // Copy button
    const copyBtn = document.createElement("button");
    copyBtn.className   = "te-copy-btn";
    copyBtn.title       = "Copy hex";
    copyBtn.innerHTML   = `<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="5" y="1" width="9" height="11" rx="1.5"/><rect x="1" y="4" width="9" height="11" rx="1.5"/></svg>`;

    // ── Wire up interactions ──
    const update = (newHex) => {
      if (!/^#[0-9a-fA-F]{6,8}$/.test(newHex)) return;
      if (!this._draft.colors) this._draft.colors = {};
      this._draft.colors[key] = newHex;
      this._markDirty();
      // Live preview
      const root = document.documentElement;
      root.style.setProperty(`--color-${key}-dark`,  newHex);
      root.style.setProperty(`--color-${key}-light`, newHex);
      // Update alpha badge
      const { alpha: a } = parseHex(newHex);
      alphaBadge.textContent = a < 0.999 ? Math.round(a * 100) + "%" : "";
      alphaBadge.style.display = a < 0.999 ? "" : "none";
    };

    swatch.oninput = () => {
      // Preserve alpha from hexInput when RGB changes
      const curAlpha = parseHex(hexInput.value).alpha;
      const combined = combineHex(swatch.value, curAlpha);
      hexInput.value = combined;
      update(combined);
    };

    hexInput.oninput = () => {
      const v = hexInput.value.trim();
      if (/^#[0-9a-fA-F]{6,8}$/.test(v)) {
        swatch.value = v.substring(0, 7);
        update(v);
      }
    };

    copyBtn.onclick = async () => {
      try {
        await navigator.clipboard.writeText(hexInput.value);
        copyBtn.innerHTML = `<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="2,8 6,12 14,4"/></svg>`;
        setTimeout(() => {
          copyBtn.innerHTML = `<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="5" y="1" width="9" height="11" rx="1.5"/><rect x="1" y="4" width="9" height="11" rx="1.5"/></svg>`;
        }, 900);
      } catch (_) {}
    };

    row.append(swatch, lbl, hexInput, alphaBadge, copyBtn);
    return row;
  },

  // ── Tab: Background ────────────────────────────────────────────────────────

  _tabBackground() {
    const bg = (this._draft.background = this._draft.background || {});
    const f  = document.createDocumentFragment();

    // ── Top row: upload zone + live preview ──
    const topRow = document.createElement("div");
    topRow.className = "te-bg-top";

    // Drop zone
    const zone = this._buildDropZone(bg);
    topRow.appendChild(zone);

    // Preview pane
    const previewWrap = document.createElement("div");
    previewWrap.className = "te-bg-preview-wrap";

    const previewLabel = document.createElement("div");
    previewLabel.className   = "te-bg-preview-label";
    previewLabel.textContent = "Preview";

    const previewBox = document.createElement("div");
    previewBox.className = "te-bg-preview-box";

    const previewImg = document.createElement("div");
    previewImg.className = "te-bg-preview-img";
    previewBox.appendChild(previewImg);

    const noPreview = document.createElement("div");
    noPreview.className   = "te-bg-no-preview";
    noPreview.textContent = "No image";
    previewBox.appendChild(noPreview);

    previewWrap.append(previewLabel, previewBox);
    topRow.appendChild(previewWrap);
    f.appendChild(topRow);

    this._bgPreviewEl = previewImg;
    this._bgNoPreviewEl = noPreview;
    this._syncBgPreview();

    // ── URL input ──
    const urlField = document.createElement("div");
    urlField.className = "te-field";

    const urlLbl = document.createElement("label");
    urlLbl.className   = "te-label";
    urlLbl.textContent = "Image URL";

    const urlRow = document.createElement("div");
    urlRow.style.cssText = "display:flex;gap:6px;align-items:center;";

    const urlInp = document.createElement("input");
    urlInp.type        = "text";
    urlInp.id          = "te-bg-url";
    urlInp.className   = "te-text-input";
    urlInp.value       = bg.src || "";
    urlInp.placeholder = "/usr/plugins/exocortex/webui/backgrounds/…";
    urlInp.style.flex  = "1";
    urlInp.oninput = () => {
      bg.src = urlInp.value;
      this._markDirty();
      this._syncBgPreview();
    };

    const clearBtn = document.createElement("button");
    clearBtn.className   = "te-btn-ghost";
    clearBtn.textContent = "Clear";
    clearBtn.title       = "Remove background image";
    clearBtn.onclick = () => {
      bg.src = "";
      urlInp.value = "";
      this._markDirty();
      this._syncBgPreview();
    };

    urlRow.append(urlInp, clearBtn);
    urlField.append(urlLbl, urlRow);
    f.appendChild(urlField);

    // ── Sliders ──
    f.appendChild(this._sliderNum("te-bg-opacity", "Opacity", 0, 1, 0.01,
      bg.opacity ?? 0.5,
      v => { bg.opacity = v; this._markDirty(); this._syncBgPreview(); }
    ));

    f.appendChild(this._sliderNum("te-bg-blur", "Blur (px)", 0, 20, 1,
      bg.blur ?? 0,
      v => { bg.blur = v; this._markDirty(); this._syncBgPreview(); }
    ));

    // ── Size + Blend ──
    const row2 = document.createElement("div");
    row2.className = "te-inline-row";
    row2.appendChild(this._select("te-bg-size", "Size", SIZE_OPTIONS, bg.size || "cover",
      v => { bg.size = v; this._markDirty(); this._syncBgPreview(); }
    ));
    row2.appendChild(this._select("te-bg-blend", "Blend Mode", BLEND_OPTIONS, bg.blend_mode || "normal",
      v => { bg.blend_mode = v; this._markDirty(); }
    ));
    f.appendChild(row2);

    // ── Position grid ──
    f.appendChild(this._fieldBlock("Position", () => {
      const grid = document.createElement("div");
      grid.className = "te-pos-grid";
      const cur = bg.position || "center";
      for (const [sym, pos] of POSITION_SNAP) {
        const btn = document.createElement("button");
        btn.className   = cur === pos ? "te-pos-btn te-pos-active" : "te-pos-btn";
        btn.textContent = sym;
        btn.title       = pos;
        btn.onclick = () => {
          bg.position = pos;
          this._markDirty();
          this._syncBgPreview();
          grid.querySelectorAll(".te-pos-btn").forEach(b =>
            b.classList.toggle("te-pos-active", b.title === pos)
          );
        };
        grid.appendChild(btn);
      }
      return grid;
    }));

    return f;
  },

  _buildDropZone(bg) {
    const zone = document.createElement("div");
    zone.className = "te-drop-zone";
    zone.id        = "te-drop-zone";

    // SVG upload icon
    const icon = document.createElement("div");
    icon.className = "te-drop-icon";
    icon.innerHTML = `<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>`;

    const hint = document.createElement("div");
    hint.className   = "te-drop-hint";
    hint.textContent = "Drop image here";

    const browseBtn = document.createElement("button");
    browseBtn.className   = "te-browse-btn";
    browseBtn.textContent = "Browse files…";

    const fileInput = document.createElement("input");
    fileInput.type   = "file";
    fileInput.accept = "image/*";
    fileInput.style.display = "none";

    const statusEl = document.createElement("div");
    statusEl.className = "te-drop-status";

    zone.append(icon, hint, browseBtn, fileInput, statusEl);

    // ── Drag events ──
    zone.addEventListener("dragover", e => {
      e.preventDefault();
      zone.classList.add("te-drop-over");
    });
    ["dragleave", "dragend"].forEach(ev =>
      zone.addEventListener(ev, () => zone.classList.remove("te-drop-over"))
    );
    zone.addEventListener("drop", async e => {
      e.preventDefault();
      zone.classList.remove("te-drop-over");
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith("image/")) {
        await this._uploadFile(file, bg, statusEl);
      }
    });

    browseBtn.onclick = () => fileInput.click();
    fileInput.onchange = async () => {
      if (fileInput.files[0]) {
        await this._uploadFile(fileInput.files[0], bg, statusEl);
      }
    };

    return zone;
  },

  _syncBgPreview() {
    if (!this._bgPreviewEl) return;
    const bg  = this._draft.background || {};
    const img = this._bgPreviewEl;
    const noP = this._bgNoPreviewEl;

    if (bg.src) {
      img.style.backgroundImage    = `url(${bg.src})`;
      img.style.backgroundSize     = bg.size || "cover";
      img.style.backgroundPosition = bg.position || "center";
      img.style.opacity            = String(bg.opacity ?? 0.5);
      img.style.filter             = bg.blur > 0 ? `blur(${bg.blur}px)` : "none";
      img.style.display            = "";
      if (noP) noP.style.display   = "none";
    } else {
      img.style.display = "none";
      if (noP) noP.style.display   = "";
    }
  },

  async _uploadFile(file, bg, statusEl) {
    statusEl.textContent = "Uploading…";
    statusEl.className   = "te-drop-status te-drop-uploading";

    const form = new FormData();
    form.append("file", file);

    try {
      const resp = await fetchApi(UPLOAD_URL, {
        method:      "POST",
        credentials: "same-origin",
        body:        form,
      });
      const data = await resp.json();

      if (data.ok && data.url) {
        bg.src = data.url;
        this._markDirty();
        // Update URL input if visible
        const urlInp = document.getElementById("te-bg-url");
        if (urlInp) urlInp.value = data.url;
        this._syncBgPreview();
        statusEl.textContent = `✓ ${file.name}`;
        statusEl.className   = "te-drop-status te-drop-ok";
      } else {
        throw new Error(data.error || "upload failed");
      }
    } catch (err) {
      statusEl.textContent = `✕ ${err.message}`;
      statusEl.className   = "te-drop-status te-drop-error";
    }
  },

  // ── Tab: Panel ─────────────────────────────────────────────────────────────

  _tabPanel() {
    const panel = (this._draft.panel = this._draft.panel || {});
    const f     = document.createDocumentFragment();

    const desc = document.createElement("p");
    desc.className   = "te-tab-desc";
    desc.textContent = "Controls the transparency and frosted-glass effect of UI panels.";
    f.appendChild(desc);

    f.appendChild(this._sliderNum("te-panel-opacity", "Opacity", 0, 1, 0.01,
      panel.opacity ?? 0.7,
      v => { panel.opacity = v; this._markDirty(); }
    ));

    const opacityNote = document.createElement("p");
    opacityNote.className   = "te-field-note";
    opacityNote.textContent = "0 = fully transparent · 1 = solid";
    f.appendChild(opacityNote);

    f.appendChild(this._sliderNum("te-panel-blur", "Backdrop Blur (px)", 0, 20, 0.5,
      panel.backdrop_blur ?? 2,
      v => { panel.backdrop_blur = v; this._markDirty(); }
    ));

    const blurNote = document.createElement("p");
    blurNote.className   = "te-field-note";
    blurNote.textContent = "Blurs background content visible through the panel.";
    f.appendChild(blurNote);

    return f;
  },

  // ── Tab: Overlays ──────────────────────────────────────────────────────────

  _tabOverlays() {
    const ov = (this._draft.overlay = this._draft.overlay || {});
    const f  = document.createDocumentFragment();

    // ── Scanlines ──
    f.appendChild(this._sectionHdr("Scanlines"));
    const sl = (ov.scanlines = ov.scanlines || {});
    f.appendChild(this._toggle("te-sl-on", "Enabled", sl.enabled,
      v => { sl.enabled = v; this._markDirty(); }
    ));
    f.appendChild(this._sliderNum("te-sl-opacity", "Opacity", 0, 0.15, 0.005,
      sl.opacity ?? 0.025,
      v => { sl.opacity = v; this._markDirty(); }
    ));
    f.appendChild(this._sliderNum("te-sl-spacing", "Line spacing (px)", 1, 6, 1,
      sl.spacing ?? 2,
      v => { sl.spacing = v; this._markDirty(); }
    ));

    // ── Vignette ──
    f.appendChild(this._sectionHdr("Vignette"));
    const vi = (ov.vignette = ov.vignette || {});
    f.appendChild(this._toggle("te-vi-on", "Enabled", vi.enabled,
      v => { vi.enabled = v; this._markDirty(); }
    ));
    f.appendChild(this._sliderNum("te-vi-opacity", "Opacity", 0, 0.8, 0.01,
      vi.opacity ?? 0.3,
      v => { vi.opacity = v; this._markDirty(); }
    ));

    // ── Noise ──
    f.appendChild(this._sectionHdr("Noise"));
    const ns = (ov.noise = ov.noise || {});
    f.appendChild(this._toggle("te-ns-on", "Enabled", ns.enabled,
      v => { ns.enabled = v; this._markDirty(); }
    ));
    f.appendChild(this._sliderNum("te-ns-opacity", "Opacity", 0, 0.1, 0.002,
      ns.opacity ?? 0.02,
      v => { ns.opacity = v; this._markDirty(); }
    ));

    // ── Watermark / Logo ──
    f.appendChild(this._sectionHdr("Watermark / Logo"));
    const wm = (ov.watermark = ov.watermark || {});
    f.appendChild(this._toggle("te-wm-on", "Enabled", wm.enabled,
      v => { wm.enabled = v; this._markDirty(); }
    ));

    f.appendChild(this._fieldBlock("Image URL", () => {
      const row  = document.createElement("div");
      row.style.cssText = "display:flex;gap:6px;align-items:center;";

      const inp = document.createElement("input");
      inp.type        = "text";
      inp.value       = wm.src || "";
      inp.className   = "te-text-input";
      inp.placeholder = "/usr/plugins/exocortex/webui/…";
      inp.style.flex  = "1";
      inp.oninput = () => { wm.src = inp.value; this._markDirty(); };

      const upload = document.createElement("input");
      upload.type   = "file";
      upload.accept = "image/*,.svg";
      upload.style.display = "none";

      const btn = document.createElement("button");
      btn.className   = "te-btn-ghost";
      btn.textContent = "Browse…";
      btn.onclick = () => upload.click();

      upload.onchange = async () => {
        if (!upload.files[0]) return;
        const form = new FormData();
        form.append("file", upload.files[0]);
        try {
          const resp = await fetchApi(UPLOAD_URL, { method: "POST", credentials: "same-origin", body: form });
          const data = await resp.json();
          if (data.ok) { wm.src = data.url; inp.value = data.url; this._markDirty(); }
        } catch (_) {}
      };

      row.append(inp, btn, upload);
      return row;
    }));

    f.appendChild(this._sliderNum("te-wm-opacity", "Opacity", 0, 0.5, 0.005,
      wm.opacity ?? 0.07,
      v => { wm.opacity = v; this._markDirty(); }
    ));

    f.appendChild(this._select("te-wm-pos", "Position",
      ["center", "top left", "top right", "bottom left", "bottom right", "top center", "bottom center"],
      wm.position || "center",
      v => { wm.position = v; this._markDirty(); }
    ));

    f.appendChild(this._fieldBlock("Size", () => {
      const inp = document.createElement("input");
      inp.type        = "text";
      inp.value       = wm.size || "40%";
      inp.className   = "te-text-input te-text-short";
      inp.placeholder = "40%";
      inp.oninput = () => { wm.size = inp.value; this._markDirty(); };
      return inp;
    }));

    return f;
  },

  // ── Tab: Fonts ─────────────────────────────────────────────────────────────

  _tabFonts() {
    const fonts = (this._draft.fonts = this._draft.fonts || {});
    const f     = document.createDocumentFragment();

    const desc = document.createElement("p");
    desc.className   = "te-tab-desc";
    desc.textContent = "CSS font-family stacks. Separate font alternatives with commas. Fonts must be installed or loaded via CSS @import.";
    f.appendChild(desc);

    f.appendChild(this._fontField("Main Font", "te-font-main", fonts.main || "",
      v => { fonts.main = v; document.documentElement.style.setProperty("--font-family-main", v); this._markDirty(); }
    ));

    f.appendChild(this._fontField("Code Font", "te-font-code", fonts.code || "",
      v => { fonts.code = v; document.documentElement.style.setProperty("--font-family-code", v); this._markDirty(); }
    ));

    return f;
  },

  _fontField(label, id, value, onChange) {
    const wrap = document.createElement("div");
    wrap.className = "te-field";

    // Label
    const lbl = document.createElement("label");
    lbl.className   = "te-label";
    lbl.htmlFor     = id;
    lbl.textContent = label;
    wrap.appendChild(lbl);

    // Preset chips
    const chips = document.createElement("div");
    chips.className = "te-font-chips";
    for (const [name, stack] of FONT_PRESETS) {
      const chip = document.createElement("button");
      chip.className   = "te-chip";
      chip.textContent = name;
      chip.title       = stack;
      chip.onclick = () => {
        inp.value = stack;
        onChange(stack);
        preview.style.fontFamily = stack;
      };
      chips.appendChild(chip);
    }
    wrap.appendChild(chips);

    // Input
    const inp = document.createElement("input");
    inp.type        = "text";
    inp.id          = id;
    inp.value       = value;
    inp.className   = "te-text-input";
    inp.placeholder = "'Font Name', fallback, generic";
    inp.oninput = () => {
      onChange(inp.value);
      preview.style.fontFamily = inp.value;
    };
    wrap.appendChild(inp);

    // Preview
    const preview = document.createElement("div");
    preview.className   = "te-font-preview";
    preview.style.fontFamily = value || "inherit";
    preview.textContent = "The quick brown fox — CODEC OPEN";
    wrap.appendChild(preview);

    return wrap;
  },

  // ── Save ───────────────────────────────────────────────────────────────────

  async _save() {
    const saveBtn   = this._overlay.querySelector("#te-btn-save");
    const origLabel = saveBtn.textContent;
    saveBtn.textContent = "Saving…";
    saveBtn.disabled    = true;

    try {
      const resp = await fetchApi(SAVE_URL, {
        method:      "POST",
        headers:     { "Content-Type": "application/json" },
        credentials: "same-origin",
        body:        JSON.stringify({
          filename: `${this._themeName}.json`,
          config:   this._draft,
        }),
      });
      const data = await resp.json();

      if (data.ok) {
        this._original = JSON.parse(JSON.stringify(this._draft));
        this._dirty    = false;
        this._syncDirtyUI();
        saveBtn.textContent = "Saved ✓";

        // Reload theme in store to sync picker
        if (window.Alpine && window.Alpine.store) {
          const s = window.Alpine.store("themeStore");
          if (s) await s.applyTheme(this._themeName);
        }

        setTimeout(() => {
          saveBtn.textContent = origLabel;
          this.close();
        }, 700);
      } else {
        throw new Error(data.error || "unknown error");
      }
    } catch (err) {
      alert(`Save failed: ${err.message}`);
      saveBtn.textContent = origLabel;
    } finally {
      saveBtn.disabled = false;
    }
  },

  // ── Dirty tracking ─────────────────────────────────────────────────────────

  _markDirty() {
    this._dirty = true;
    this._syncDirtyUI();
  },

  _syncDirtyUI() {
    const hint    = this._overlay && this._overlay.querySelector("#te-dirty-hint");
    const saveBtn = this._overlay && this._overlay.querySelector("#te-btn-save");
    if (hint)    hint.style.display    = this._dirty ? "" : "none";
    if (saveBtn) saveBtn.classList.toggle("te-btn-modified", this._dirty);
  },

  // ── UI Helpers ─────────────────────────────────────────────────────────────

  _sectionHdr(text) {
    const h = document.createElement("div");
    h.className   = "te-section-hdr";
    h.textContent = text;
    return h;
  },

  // Slider + synced number input pair
  _sliderNum(id, label, min, max, step, value, onChange) {
    const wrap = document.createElement("div");
    wrap.className = "te-field";

    const lbl = document.createElement("label");
    lbl.className   = "te-label";
    lbl.htmlFor     = id;
    lbl.textContent = label;

    const row = document.createElement("div");
    row.className = "te-slider-row";

    const slider = document.createElement("input");
    slider.type  = "range";
    slider.id    = id;
    slider.min   = min;
    slider.max   = max;
    slider.step  = step;
    slider.value = value;
    slider.className = "te-slider";

    const numInput = document.createElement("input");
    numInput.type      = "number";
    numInput.min       = min;
    numInput.max       = max;
    numInput.step      = step;
    numInput.value     = value;
    numInput.className = "te-num-input";

    const clamp = v => Math.max(parseFloat(min), Math.min(parseFloat(max), v));

    slider.oninput = () => {
      const v = parseFloat(slider.value);
      numInput.value = v;
      onChange(v);
    };
    numInput.oninput = () => {
      const v = clamp(parseFloat(numInput.value) || 0);
      slider.value = v;
      onChange(v);
    };

    row.append(slider, numInput);
    wrap.append(lbl, row);
    return wrap;
  },

  _select(id, label, options, selected, onChange) {
    const wrap = document.createElement("div");
    wrap.className = "te-field";

    const lbl = document.createElement("label");
    lbl.className   = "te-label";
    lbl.htmlFor     = id;
    lbl.textContent = label;

    const sel = document.createElement("select");
    sel.id        = id;
    sel.className = "te-select";
    for (const opt of options) {
      const o = document.createElement("option");
      o.value       = opt;
      o.textContent = opt;
      if (opt === selected) o.selected = true;
      sel.appendChild(o);
    }
    sel.onchange = () => onChange(sel.value);

    wrap.append(lbl, sel);
    return wrap;
  },

  _toggle(id, label, checked, onChange) {
    const wrap = document.createElement("div");
    wrap.className = "te-toggle-row";

    const inp = document.createElement("input");
    inp.type      = "checkbox";
    inp.id        = id;
    inp.checked   = !!checked;
    inp.className = "te-checkbox";
    inp.onchange  = () => onChange(inp.checked);

    const lbl = document.createElement("label");
    lbl.className   = "te-toggle-label";
    lbl.htmlFor     = id;
    lbl.textContent = label;

    wrap.append(inp, lbl);
    return wrap;
  },

  _fieldBlock(label, buildContent) {
    const wrap = document.createElement("div");
    wrap.className = "te-field";

    const lbl = document.createElement("label");
    lbl.className   = "te-label";
    lbl.textContent = label;

    wrap.append(lbl, buildContent());
    return wrap;
  },

  // ── DOM Injection ──────────────────────────────────────────────────────────

  _injectOverlay() {
    const overlay = document.createElement("div");
    overlay.id        = "te-overlay";
    overlay.className = "te-overlay te-hidden";

    overlay.innerHTML = `
      <div class="te-modal" role="dialog" aria-modal="true" aria-label="Theme Editor">
        <div class="te-header">
          <div class="te-header-left">
            <svg class="te-logo" viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5">
              <polygon points="10,1 18.66,5.5 18.66,14.5 10,19 1.34,14.5 1.34,5.5"/>
            </svg>
            <div>
              <div id="te-name"     class="te-theme-name">THEME</div>
              <div id="te-filename" class="te-theme-file">theme.json</div>
            </div>
          </div>
          <button id="te-btn-close" class="te-close" title="Close (Esc)">
            <svg viewBox="0 0 16 16" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none">
              <line x1="2" y1="2" x2="14" y2="14"/>
              <line x1="14" y1="2" x2="2" y2="14"/>
            </svg>
          </button>
        </div>

        <nav class="te-tabs" role="tablist">
          <button class="te-tab te-tab-active" data-tab="colors"     role="tab">Colors</button>
          <button class="te-tab"               data-tab="background" role="tab">Background</button>
          <button class="te-tab"               data-tab="panel"      role="tab">Panel</button>
          <button class="te-tab"               data-tab="overlays"   role="tab">Overlays</button>
          <button class="te-tab"               data-tab="fonts"      role="tab">Fonts</button>
        </nav>

        <div id="te-content" class="te-content"></div>

        <div class="te-footer">
          <button class="te-btn-ghost" id="te-btn-cancel">Cancel</button>
          <div class="te-footer-right">
            <span class="te-dirty-hint" id="te-dirty-hint" style="display:none">● Unsaved changes</span>
            <button class="te-btn-primary" id="te-btn-save">Save</button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);
    this._overlay = overlay;

    overlay.querySelector("#te-btn-close").onclick  = () => this._cancel();
    overlay.querySelector("#te-btn-cancel").onclick = () => this._cancel();
    overlay.querySelector("#te-btn-save").onclick   = () => this._save();

    overlay.addEventListener("click", e => { if (e.target === overlay) this._cancel(); });
    document.addEventListener("keydown", e => {
      if (e.key === "Escape" && !overlay.classList.contains("te-hidden")) this._cancel();
    });

    overlay.querySelectorAll(".te-tab").forEach(tab => {
      tab.addEventListener("click", () => {
        this._activeTab = tab.dataset.tab;
        this._bgPreviewEl = null;
        this._bgNoPreviewEl = null;
        this._renderAll();
      });
    });
  },

  _injectStyles() {
    if (document.getElementById("te-styles")) return;
    const s = document.createElement("style");
    s.id = "te-styles";
    s.textContent = `
      /* ── Overlay / Modal shell ─────────────────────────────────────── */
      .te-overlay {
        position: fixed; inset: 0; z-index: 9999;
        background: rgba(0,0,0,0.70);
        display: flex; align-items: center; justify-content: center;
        backdrop-filter: blur(3px);
        animation: te-fade-in 0.15s ease;
      }
      .te-overlay.te-hidden { display: none; }
      @keyframes te-fade-in { from { opacity: 0; } to { opacity: 1; } }

      .te-modal {
        background: var(--color-panel-dark, #161b22);
        border: 1px solid var(--color-border-dark, #30363d);
        border-radius: 10px;
        width: min(620px, 96vw);
        max-height: 92vh;
        display: flex; flex-direction: column;
        box-shadow: 0 24px 64px rgba(0,0,0,0.6);
        font-size: 13px;
        color: var(--color-text-dark, #c9d1d9);
        font-family: var(--font-family-main, system-ui, sans-serif);
        animation: te-slide-up 0.18s ease;
      }
      @keyframes te-slide-up {
        from { transform: translateY(10px); opacity: 0.8; }
        to   { transform: none;             opacity: 1;   }
      }

      /* ── Header ────────────────────────────────────────────────────── */
      .te-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 13px 16px 12px;
        border-bottom: 1px solid var(--color-border-dark, #30363d);
        flex-shrink: 0;
      }
      .te-header-left {
        display: flex; align-items: center; gap: 10px;
      }
      .te-logo { color: var(--color-primary-dark, #8b949e); flex-shrink: 0; }

      .te-theme-name {
        font-weight: 700; font-size: 11px; letter-spacing: 0.1em;
        color: var(--color-primary-dark, #8b949e);
        font-family: var(--font-family-code, monospace);
        line-height: 1.3;
      }
      .te-theme-file {
        font-size: 10px; color: var(--color-text-muted-dark, #6e7681);
        font-family: var(--font-family-code, monospace);
        line-height: 1.3;
      }

      .te-close {
        background: none; border: none; cursor: pointer; padding: 5px;
        border-radius: 5px;
        color: var(--color-text-muted-dark, #6e7681);
        display: flex; align-items: center;
        transition: color 0.15s, background 0.15s;
      }
      .te-close:hover {
        color: var(--color-text-dark, #ccc);
        background: var(--color-secondary-dark, #21262d);
      }

      /* ── Tabs ──────────────────────────────────────────────────────── */
      .te-tabs {
        display: flex; padding: 0 6px;
        border-bottom: 1px solid var(--color-border-dark, #30363d);
        flex-shrink: 0; gap: 0;
        overflow-x: auto; scrollbar-width: none;
      }
      .te-tabs::-webkit-scrollbar { display: none; }

      .te-tab {
        background: none; border: none; cursor: pointer;
        padding: 9px 15px; font-size: 12px; font-weight: 500;
        color: var(--color-text-muted-dark, #6e7681);
        border-bottom: 2px solid transparent;
        white-space: nowrap;
        transition: color 0.15s, border-color 0.15s;
      }
      .te-tab:hover { color: var(--color-text-dark, #c9d1d9); }
      .te-tab.te-tab-active {
        color: var(--color-text-dark, #c9d1d9);
        border-bottom-color: var(--color-accent-dark, #58a6ff);
      }

      /* ── Content area ──────────────────────────────────────────────── */
      .te-content {
        flex: 1; overflow-y: auto; padding: 16px;
        scrollbar-width: thin;
        scrollbar-color: var(--color-border-dark, #333) transparent;
      }

      /* ── Section headers ───────────────────────────────────────────── */
      .te-section-hdr {
        font-size: 10px; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.1em; color: var(--color-text-muted-dark, #6e7681);
        padding: 3px 0 6px;
        border-bottom: 1px solid var(--color-border-dark, #30363d);
        margin: 12px 0 8px;
      }
      .te-section-hdr:first-child { margin-top: 0; }

      /* ── Color grid ────────────────────────────────────────────────── */
      .te-color-grid {
        display: flex; flex-direction: column; gap: 2px;
        margin-bottom: 2px;
      }

      .te-color-row {
        display: flex; align-items: center; gap: 8px;
        padding: 3px 4px; border-radius: 5px;
        transition: background 0.1s;
      }
      .te-color-row:hover { background: var(--color-secondary-dark, #21262d); }

      .te-swatch {
        width: 28px; height: 22px; flex-shrink: 0;
        border: 1px solid var(--color-border-dark, #444);
        border-radius: 4px; padding: 1px; cursor: pointer;
        background: none;
      }

      .te-color-label {
        flex: 1; font-size: 12px;
        color: var(--color-text-dark, #c9d1d9);
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      }

      .te-hex-input {
        width: 76px; flex-shrink: 0;
        background: var(--color-input-dark, #0d1117);
        border: 1px solid var(--color-border-dark, #30363d);
        border-radius: 4px; padding: 2px 5px;
        font-family: var(--font-family-code, monospace);
        font-size: 11px; color: var(--color-text-dark, #c9d1d9);
        text-align: center;
        transition: border-color 0.15s;
      }
      .te-hex-input:focus {
        outline: none;
        border-color: var(--color-accent-dark, #58a6ff);
      }

      .te-alpha-badge {
        font-size: 9px; font-family: monospace;
        color: var(--color-accent-dark, #79c0ff);
        min-width: 26px; text-align: right; flex-shrink: 0;
      }

      .te-copy-btn {
        background: none; border: none; cursor: pointer; padding: 3px;
        border-radius: 3px; flex-shrink: 0;
        color: var(--color-text-muted-dark, #6e7681);
        display: flex; align-items: center;
        transition: color 0.15s, background 0.15s;
      }
      .te-copy-btn:hover {
        color: var(--color-text-dark, #ccc);
        background: var(--color-secondary-dark, #30363d);
      }

      /* ── Background tab ────────────────────────────────────────────── */
      .te-bg-top {
        display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
        margin-bottom: 14px;
      }
      @media (max-width: 460px) { .te-bg-top { grid-template-columns: 1fr; } }

      .te-drop-zone {
        border: 2px dashed var(--color-border-dark, #30363d);
        border-radius: 8px; padding: 16px 12px;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        gap: 6px; cursor: pointer; text-align: center;
        transition: border-color 0.15s, background 0.15s;
        min-height: 120px;
      }
      .te-drop-zone:hover, .te-drop-over {
        border-color: var(--color-accent-dark, #58a6ff);
        background: var(--color-secondary-dark, rgba(88,166,255,0.05));
      }
      .te-drop-icon {
        color: var(--color-text-muted-dark, #6e7681);
        transition: color 0.15s;
      }
      .te-drop-zone:hover .te-drop-icon { color: var(--color-accent-dark, #58a6ff); }
      .te-drop-hint {
        font-size: 11px; color: var(--color-text-muted-dark, #6e7681);
      }

      .te-browse-btn {
        background: var(--color-secondary-dark, #21262d);
        border: 1px solid var(--color-border-dark, #30363d);
        border-radius: 5px; padding: 5px 12px;
        color: var(--color-text-dark, #c9d1d9); font-size: 11px;
        cursor: pointer; transition: background 0.15s;
      }
      .te-browse-btn:hover { background: var(--color-highlight-dark, #30363d); }

      .te-drop-status {
        font-size: 10px; font-family: monospace;
        min-height: 14px;
        transition: color 0.2s;
      }
      .te-drop-uploading { color: var(--color-text-muted-dark, #888); }
      .te-drop-ok        { color: var(--color-accent-dark, #3fb950); }
      .te-drop-error     { color: var(--color-error-text-dark, #f85149); }

      .te-bg-preview-wrap {
        display: flex; flex-direction: column; gap: 4px;
      }
      .te-bg-preview-label {
        font-size: 10px; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.08em; color: var(--color-text-muted-dark, #6e7681);
      }
      .te-bg-preview-box {
        position: relative; overflow: hidden;
        border-radius: 6px; border: 1px solid var(--color-border-dark, #30363d);
        background: var(--color-input-dark, #0d1117);
        flex: 1; min-height: 100px;
      }
      .te-bg-preview-img {
        position: absolute; inset: 0;
        background-repeat: no-repeat;
      }
      .te-bg-no-preview {
        position: absolute; inset: 0;
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; color: var(--color-text-muted-dark, #6e7681);
      }

      .te-inline-row {
        display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
        margin-bottom: 2px;
      }
      @media (max-width: 400px) { .te-inline-row { grid-template-columns: 1fr; } }

      /* Position snap grid */
      .te-pos-grid {
        display: grid; grid-template-columns: repeat(3, 36px);
        gap: 3px; margin-top: 2px;
      }
      .te-pos-btn {
        width: 36px; height: 28px;
        background: var(--color-input-dark, #0d1117);
        border: 1px solid var(--color-border-dark, #30363d);
        border-radius: 4px; color: var(--color-text-muted-dark, #6e7681);
        font-size: 12px; cursor: pointer; text-align: center;
        transition: background 0.1s, border-color 0.1s;
      }
      .te-pos-btn:hover { background: var(--color-secondary-dark, #21262d); }
      .te-pos-btn.te-pos-active {
        background: var(--color-highlight-dark, #1a2a3a);
        border-color: var(--color-accent-dark, #58a6ff);
        color: var(--color-text-dark, #ccc);
      }

      /* ── Generic fields ────────────────────────────────────────────── */
      .te-field {
        display: flex; flex-direction: column; gap: 5px;
        margin-bottom: 12px;
      }

      .te-label {
        font-size: 10px; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.07em; color: var(--color-text-muted-dark, #6e7681);
      }

      /* Slider + number input */
      .te-slider-row {
        display: flex; align-items: center; gap: 8px;
      }
      .te-slider {
        flex: 1;
        accent-color: var(--color-accent-dark, #58a6ff);
        cursor: pointer;
      }
      .te-num-input {
        width: 58px; flex-shrink: 0;
        background: var(--color-input-dark, #0d1117);
        border: 1px solid var(--color-border-dark, #30363d);
        border-radius: 4px; padding: 3px 5px;
        text-align: right;
        font-family: var(--font-family-code, monospace); font-size: 11px;
        color: var(--color-text-dark, #c9d1d9);
        -moz-appearance: textfield;
      }
      .te-num-input::-webkit-outer-spin-button,
      .te-num-input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
      .te-num-input:focus {
        outline: none;
        border-color: var(--color-accent-dark, #58a6ff);
      }

      .te-select {
        background: var(--color-input-dark, #0d1117);
        border: 1px solid var(--color-border-dark, #30363d);
        border-radius: 4px; padding: 5px 7px;
        color: var(--color-text-dark, #c9d1d9); font-size: 11px;
        cursor: pointer; width: 100%;
        transition: border-color 0.15s;
      }
      .te-select:focus { outline: none; border-color: var(--color-accent-dark, #58a6ff); }

      .te-text-input {
        background: var(--color-input-dark, #0d1117);
        border: 1px solid var(--color-border-dark, #30363d);
        border-radius: 4px; padding: 5px 8px;
        color: var(--color-text-dark, #c9d1d9); font-size: 12px; width: 100%;
        box-sizing: border-box;
        transition: border-color 0.15s;
      }
      .te-text-input:focus { outline: none; border-color: var(--color-accent-dark, #58a6ff); }
      .te-text-short { width: 100px; }

      .te-toggle-row {
        display: flex; align-items: center; gap: 8px;
        margin-bottom: 8px;
      }
      .te-checkbox { width: 14px; height: 14px; cursor: pointer; accent-color: var(--color-accent-dark, #58a6ff); }
      .te-toggle-label { font-size: 12px; cursor: pointer; color: var(--color-text-dark, #c9d1d9); }

      .te-tab-desc {
        font-size: 11px; color: var(--color-text-muted-dark, #6e7681);
        line-height: 1.5; margin-bottom: 14px;
      }
      .te-field-note {
        font-size: 10px; color: var(--color-text-muted-dark, #6e7681);
        margin-top: -6px; margin-bottom: 12px;
      }

      /* Fonts tab */
      .te-font-chips {
        display: flex; flex-wrap: wrap; gap: 5px;
        margin-bottom: 4px;
      }
      .te-chip {
        background: var(--color-secondary-dark, #21262d);
        border: 1px solid var(--color-border-dark, #30363d);
        border-radius: 12px; padding: 3px 10px;
        font-size: 10px; cursor: pointer; white-space: nowrap;
        color: var(--color-text-muted-dark, #8b949e);
        transition: background 0.15s, color 0.15s, border-color 0.15s;
      }
      .te-chip:hover {
        background: var(--color-highlight-dark, #1a2a3a);
        border-color: var(--color-accent-dark, #58a6ff);
        color: var(--color-text-dark, #ccc);
      }
      .te-font-preview {
        background: var(--color-secondary-dark, #21262d);
        border: 1px solid var(--color-border-dark, #30363d);
        border-radius: 5px; padding: 8px 10px;
        font-size: 13px; color: var(--color-text-dark, #c9d1d9);
        line-height: 1.4; margin-top: 4px;
      }

      /* ── Footer ────────────────────────────────────────────────────── */
      .te-footer {
        display: flex; align-items: center; justify-content: space-between;
        padding: 10px 16px;
        border-top: 1px solid var(--color-border-dark, #30363d);
        flex-shrink: 0;
      }
      .te-footer-right { display: flex; align-items: center; gap: 10px; }

      .te-dirty-hint {
        font-size: 11px; color: var(--color-warning-text-dark, #d29922);
        font-family: var(--font-family-code, monospace);
      }

      .te-btn-ghost {
        background: none;
        border: 1px solid var(--color-border-dark, #30363d);
        border-radius: 6px; padding: 6px 14px;
        color: var(--color-text-dark, #c9d1d9); font-size: 12px;
        cursor: pointer; transition: background 0.15s;
      }
      .te-btn-ghost:hover { background: var(--color-secondary-dark, #21262d); }

      .te-btn-primary {
        background: var(--color-highlight-dark, #1a2a3a);
        border: 1px solid var(--color-border-dark, #30363d);
        border-radius: 6px; padding: 6px 18px;
        color: var(--color-text-dark, #c9d1d9); font-size: 12px; font-weight: 600;
        cursor: pointer; transition: background 0.15s, border-color 0.15s;
      }
      .te-btn-primary:hover { background: var(--color-secondary-dark, #2a3a4a); }
      .te-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
      .te-btn-primary.te-btn-modified {
        border-color: var(--color-accent-dark, #58a6ff);
        color: var(--color-accent-dark, #58a6ff);
      }
    `;
    document.head.appendChild(s);
  },
};
