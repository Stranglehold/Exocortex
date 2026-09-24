// Theme Store - Manages theme list and switching
import { createStore } from "/js/AlpineStore.js";

const model = {
    themes: [],
    current: null,

    async init() {
        // Load available themes from server
        try {
            const knownThemes = ['dark', 'light', 'cyberpunk', 'ocean', 'forest', 'mgs3', 'yorha', 'diamond-dogs', 'idroid', 'codec', 'big-shell', 'kaer-morhen', 'shadow-moses'];
            this.themes = [];

            for (const themeName of knownThemes) {
                try {
                    const resp = await fetch(`/themes/${themeName}.json`);
                    if (resp.ok) {
                        const themeData = await resp.json();
                        themeData._key = themeName;  // lowercase filename key
                        this.themes.push(themeData);
                    }
                } catch (e) {
                    // Theme doesn't exist, skip
                }
            }

            console.log(`[ThemeStore] Loaded ${this.themes.length} themes`);
        } catch (error) {
            console.error('[ThemeStore] Failed to load themes:', error);
        }

        this.current = localStorage.getItem('agent-zero-theme') || 'dark';
    },

    async switchTheme(themeKey) {
        // themeKey is the lowercase filename (e.g. "mgs3", "cyberpunk")
        if (typeof ThemeManager !== 'undefined') {
            await ThemeManager.switchTheme(themeKey);
            this.current = themeKey;
            console.log(`[ThemeStore] Switched to theme: ${themeKey}`);
        }
    },

    getThemeByName(name) {
        return this.themes.find(t => t.name.toLowerCase() === name.toLowerCase()) ||
               this.themes.find(t => t.name.toLowerCase().includes(name));
    }
};

export const store = createStore("theme", model);
