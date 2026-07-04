/**
 * Exocortex Theme Store
 * Alpine.js store for theme management in Agent Zero v1.6.
 *
 * Themes define CSS color variables. Applying a theme sets both
 * the -dark and -light variants on :root, so the preferences
 * dark/light toggle continues to work within the theme's palette.
 *
 * "Default" clears all overrides and restores A0's built-in colors.
 */

import { createStore } from "/js/AlpineStore.js";

const THEMES_URL  = "/usr/plugins/_exocortex/webui/themes/";
const STORAGE_KEY = "exocortex_theme";

// All CSS color property names (without --color- prefix and without -dark/-light suffix)
const COLOR_KEYS = [
  "background", "text", "text-muted", "primary", "secondary", "accent",
  "message-bg", "highlight", "message-text", "panel", "border",
  "input", "input-focus", "chat-background", "error-text", "warning-text", "table-row",
];

// All font property names
const FONT_KEYS = [
  ["font-family-main", "main"],
  ["font-family-code", "code"],
];

const model = {
  themes: [],
  activeTheme: null,
  pickerOpen: false,
  loading: false,
  _initialized: false,

  async init() {
    if (this._initialized) return;
    this._initialized = true;
    await this._loadIndex();
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && saved !== "default") {
      await this.applyTheme(saved);
    }
    this._registerShortcut();
  },

  _registerShortcut() {
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === "T") {
        e.preventDefault();
        this.pickerOpen = !this.pickerOpen;
      }
    });
  },

  togglePicker() {
    this.pickerOpen = !this.pickerOpen;
  },

  async _loadIndex() {
    try {
      const resp = await fetch(THEMES_URL + "index.json");
      const data = await resp.json();
      this.themes = data.themes || [];
    } catch (e) {
      this.themes = [];
    }
  },

  async applyTheme(themeId) {
    if (!themeId || themeId === "default") {
      this.resetTheme();
      return;
    }
    this.loading = true;
    try {
      const resp = await fetch(THEMES_URL + themeId + ".json");
      if (!resp.ok) throw new Error("theme not found");
      const theme = await resp.json();
      this._applyColors(theme.colors || {});
      this._applyFonts(theme.fonts || {});
      this.activeTheme = themeId;
      localStorage.setItem(STORAGE_KEY, themeId);
    } catch (e) {
      console.warn("[THEME] Failed to load theme:", themeId, e);
    } finally {
      this.loading = false;
    }
  },

  resetTheme() {
    const root = document.documentElement;
    for (const key of COLOR_KEYS) {
      root.style.removeProperty(`--color-${key}-dark`);
      root.style.removeProperty(`--color-${key}-light`);
    }
    for (const [cssKey] of FONT_KEYS) {
      root.style.removeProperty(`--${cssKey}`);
    }
    this.activeTheme = null;
    localStorage.removeItem(STORAGE_KEY);
  },

  _applyColors(colors) {
    const root = document.documentElement;
    for (const [key, value] of Object.entries(colors)) {
      if (!value) continue;
      // Set both variants so the dark/light toggle works within the theme
      root.style.setProperty(`--color-${key}-dark`,  value);
      root.style.setProperty(`--color-${key}-light`, value);
    }
  },

  _applyFonts(fonts) {
    const root = document.documentElement;
    for (const [cssKey, jsonKey] of FONT_KEYS) {
      if (fonts[jsonKey]) {
        root.style.setProperty(`--${cssKey}`, fonts[jsonKey]);
      }
    }
  },

  isActive(themeId) {
    return this.activeTheme === themeId;
  },
};

export const store = createStore("themeStore", model);
