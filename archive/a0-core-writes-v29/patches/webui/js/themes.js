// Theme Management Module for Agent Zero
// Extended Aesthetic Theme Engine — Tier 1/2/3 support
// Handles CSS variables, background layers, overlay effects, and canvas animations

const ThemeManager = {
    currentTheme: 'dark',
    _animationId: null,
    _animationInstance: null,
    _reducedMotion: false,
    _widgetState: 'idle',
    _stateTimer: null,
    _agentObserver: null,
    _widgetElements: [],
    _parallaxHandler: null,
    _cursorCanvas: null,
    _cursorParticles: [],
    _cursorRafId: null,
    _cursorMouseHandler: null,
    _idleTimer: null,
    _idleEscalated: false,
    _idleResetHandler: null,
    _msgRevealObserver: null,
    _msgRevealType: null,
    _audioCtx: null,
    _soundEnabled: false,
    _soundVolume: 0.3,
    _audioUnlocked: false,
    _soundUnlockHandler: null,
    _soundBuffers: null,   // Map<src, AudioBuffer> — cached decoded files
    _soundSrcs: null,      // { codec_connect, alert_ping, caution } → src path from theme JSON

    // Initialize theme system
    async init() {
        try {
            this._setupPerformanceListeners();
            const cookieTheme = document.cookie.split('; ').find(r => r.startsWith('agent-zero-theme='))?.split('=')[1];
            const savedTheme = localStorage.getItem('agent-zero-theme') || cookieTheme || 'dark';
            await this.applyTheme(savedTheme);
            console.log(`[ThemeManager] Initialized with theme: ${savedTheme}`);
        } catch (error) {
            console.error('[ThemeManager] Initialization error:', error);
            await this.applyTheme('dark');
        }
    },

    // Load a specific theme from JSON file
    async loadTheme(themeName) {
        try {
            const response = await fetch(`/themes/${themeName}.json`);
            if (!response.ok) throw new Error(`Failed to load theme: ${themeName}`);
            return await response.json();
        } catch (error) {
            console.error(`[ThemeManager] Error loading theme ${themeName}:`, error);
            return null;
        }
    },

    // Remove all injected effect layers and cancel any running animation
    _setupPerformanceListeners() {
        document.addEventListener('visibilitychange', () => {
            if (!this._animationInstance) return;
            if (document.hidden) {
                this._animationInstance.pause();
            } else {
                this._animationInstance.resume();
            }
        });
        const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
        this._reducedMotion = mq.matches;
        mq.addEventListener('change', (e) => {
            this._reducedMotion = e.matches;
            if (e.matches) {
                if (this._animationInstance) { this._animationInstance.stop(); this._animationInstance = null; }
                const cv = document.getElementById('theme-canvas');
                if (cv) cv.remove();
            }
        });
    },

    _clearEffectLayers() {
        // Stop any running animation
        if (this._animationInstance) {
            try {
                this._animationInstance.stop();
            } catch (e) {
                // ignore
            }
            this._animationInstance = null;
        }
        if (this._animationId) {
            cancelAnimationFrame(this._animationId);
            this._animationId = null;
        }

        // Remove background layers
        const bgColor = document.getElementById('theme-background-color');
        if (bgColor) bgColor.remove();
        const bg = document.getElementById('theme-background');
        if (bg) {
            // Remove attached resize handler if any
            if (bg._resizeHandler) {
                window.removeEventListener('resize', bg._resizeHandler);
            }
            bg.remove();
        }

        // Remove overlay layer
        const ov = document.getElementById('theme-overlay');
        if (ov) ov.remove();

        // Remove watermark layer (now outside overlay)
        const wm = document.getElementById('theme-watermark');
        if (wm) wm.remove();

        // Remove tint layer
        const tn = document.getElementById('theme-tint');
        if (tn) tn.remove();

        // Remove canvas layer
        const cv = document.getElementById('theme-canvas');
        if (cv) {
            if (cv._resizeHandler) {
                window.removeEventListener('resize', cv._resizeHandler);
            }
            cv.remove();
        }

        // Remove phase 3 effects
        this._clearParallax();
        this._clearCursorTrail();
        this._clearIdleEscalation();
        this._clearMessageReveal();
        this._clearSounds();

        // Remove widget layer
        this._clearWidgets();
    },

    // Background image themes are handled entirely via CSS on the html element
    // (see generateThemeCSS). No div injection needed — it avoids all z-index
    // stacking-context issues that arise when body/html are position:fixed.
    _injectBackground(themeData) {
        // no-op: background is set on html via generateThemeCSS
    },

    // Inject #theme-overlay div with scanlines/vignette/noise/watermark children
    _injectOverlay(themeData) {
        const overlay = themeData.overlay || {};
        const scanlines = overlay.scanlines || {};
        const vignette = overlay.vignette || {};
        const noise = overlay.noise || {};
        const watermark = overlay.watermark || {};

        const hasAny = scanlines.enabled || vignette.enabled || noise.enabled;
        if (!hasAny) return;

        const div = document.createElement('div');
        div.id = 'theme-overlay';
        div.style.cssText = 'position: fixed; inset: 0; z-index: 9999; pointer-events: none;';

        // Scanlines child
        if (scanlines.enabled) {
            const spacing = scanlines.spacing != null ? scanlines.spacing : 2;
            const op = scanlines.opacity != null ? scanlines.opacity : 0.04;
            const sl = document.createElement('div');
            sl.style.cssText = [
                'position: absolute',
                'inset: 0',
                `background: repeating-linear-gradient(`,
                `  0deg,`,
                `  transparent,`,
                `  transparent ${spacing}px,`,
                `  rgba(0,0,0,${op}) ${spacing}px,`,
                `  rgba(0,0,0,${op}) ${spacing + 1}px`,
                `)`
            ].join(' ');
            // Rewrite as valid inline style
            sl.style.position = 'absolute';
            sl.style.inset = '0';
            sl.style.background = `repeating-linear-gradient(0deg, transparent, transparent ${spacing}px, rgba(0,0,0,${op}) ${spacing}px, rgba(0,0,0,${op}) ${spacing + 1}px)`;
            div.appendChild(sl);
        }

        // Vignette child
        if (vignette.enabled) {
            const op = vignette.opacity != null ? vignette.opacity : 0.3;
            const vig = document.createElement('div');
            vig.style.position = 'absolute';
            vig.style.inset = '0';
            vig.style.background = `radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,${op}) 100%)`;
            div.appendChild(vig);
        }

        // Noise child — SVG feTurbulence + overlay div
        if (noise.enabled) {
            const op = noise.opacity != null ? noise.opacity : 0.02;

            // Inject SVG filter definition
            const svgNS = 'http://www.w3.org/2000/svg';
            const svg = document.createElementNS(svgNS, 'svg');
            svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            svg.style.cssText = 'position: absolute; width: 0; height: 0; overflow: hidden;';

            const defs = document.createElementNS(svgNS, 'defs');
            const filter = document.createElementNS(svgNS, 'filter');
            filter.setAttribute('id', 'theme-noise-filter');
            filter.setAttribute('x', '0%');
            filter.setAttribute('y', '0%');
            filter.setAttribute('width', '100%');
            filter.setAttribute('height', '100%');

            const turbulence = document.createElementNS(svgNS, 'feTurbulence');
            turbulence.setAttribute('type', 'fractalNoise');
            turbulence.setAttribute('baseFrequency', '0.65');
            turbulence.setAttribute('numOctaves', '3');
            turbulence.setAttribute('stitchTiles', 'stitch');

            const colorMatrix = document.createElementNS(svgNS, 'feColorMatrix');
            colorMatrix.setAttribute('type', 'saturate');
            colorMatrix.setAttribute('values', '0');

            filter.appendChild(turbulence);
            filter.appendChild(colorMatrix);
            defs.appendChild(filter);
            svg.appendChild(defs);
            div.appendChild(svg);

            // Noise overlay div
            const noisediv = document.createElement('div');
            noisediv.style.position = 'absolute';
            noisediv.style.inset = '0';
            noisediv.style.filter = 'url(#theme-noise-filter)';
            noisediv.style.background = 'white';
            noisediv.style.opacity = String(op);
            div.appendChild(noisediv);
        }

        document.body.appendChild(div);
    },

    // Inject #theme-watermark as a direct child of body — outside any isolation
    // container so future tint blend modes cannot color-shift it.
    _injectWatermark(themeData) {
        const watermark = (themeData.overlay || {}).watermark || {};
        if (!watermark.enabled || !watermark.src) return;

        const op = watermark.opacity != null ? watermark.opacity : 0.05;
        const position = watermark.position || 'center';
        const size = watermark.size || '40%';

        const wm = document.createElement('div');
        wm.id = 'theme-watermark';
        wm.style.position = 'fixed';
        wm.style.inset = '0';
        wm.style.zIndex = '9997';
        wm.style.pointerEvents = 'none';
        wm.style.backgroundImage = `url(${watermark.src})`;
        wm.style.backgroundSize = size;
        wm.style.backgroundRepeat = 'no-repeat';
        wm.style.backgroundPosition = position;
        wm.style.opacity = String(op);
        document.body.appendChild(wm);
    },

    // Inject #theme-tint — a fixed color overlay using mix-blend-mode.
    // Sits above the background but below canvas/overlay/widgets.
    // With mode "color" it shifts the hue of everything beneath it (bg image
    // AND UI chrome) toward the theme's accent palette, making the UI feel
    // like it exists inside the world rather than on top of it.
    _injectTint(themeData) {
        const tint = (themeData.overlay || {}).tint || {};
        if (!tint.enabled || !tint.color) return;
        const div = document.createElement('div');
        div.id = 'theme-tint';
        div.style.position = 'fixed';
        div.style.inset = '0';
        div.style.zIndex = '9996';
        div.style.pointerEvents = 'none';
        div.style.background = tint.color;
        div.style.opacity = String(tint.opacity ?? 0.08);
        div.style.mixBlendMode = tint.mode || 'color';
        document.body.appendChild(div);
    },

    // Inject #theme-canvas and start animation
    _injectCanvas(themeData) {
        const anim = themeData.animation || {};
        const type = anim.type || 'none';
        if (type === 'none') return;

        const canvas = document.createElement('canvas');
        canvas.id = 'theme-canvas';
        canvas.style.cssText = 'position: fixed; inset: 0; z-index: 9998; pointer-events: none; width: 100%; height: 100%;';
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        // Resize handler
        const resizeHandler = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        canvas._resizeHandler = resizeHandler;
        window.addEventListener('resize', resizeHandler);

        document.body.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        const intensity = anim.intensity != null ? anim.intensity : 0.5;
        const color = anim.color || '#ffffff';

        let instance = null;
        if (type === 'rain') {
            instance = new RainAnimation(ctx, canvas, intensity, color);
        } else if (type === 'snow') {
            instance = new SnowAnimation(ctx, canvas, intensity, color);
        } else if (type === 'particles') {
            instance = new ParticleAnimation(ctx, canvas, intensity, color);
        } else if (type === 'static') {
            instance = new StaticAnimation(ctx, canvas, intensity);
        }

        if (instance) {
            instance.start();
            this._animationInstance = instance;
        }
    },

    // Apply a theme by name
    // Apply a raw config object directly — used by theme editor for live preview
    // Does not update currentTheme or localStorage
    async applyConfig(config) {
        try {
            this._clearEffectLayers();
            const existing = document.getElementById('dynamic-theme-style');
            if (existing) existing.remove();
            const style = document.createElement('style');
            style.id = 'dynamic-theme-style';
            style.textContent = this.generateThemeCSS(config);
            document.head.appendChild(style);
            document.body.classList.remove('light-mode');
            this._injectBackground(config);
            this._injectOverlay(config);
            this._injectWatermark(config);
            this._injectTint(config);
            this._injectCanvas(config);
            this._injectWidgets(config);
            this._setupParallax(config);
            this._setupCursorTrail(config);
            this._setupIdleEscalation(config);
            this._setupMessageReveal(config);
            this._setupSounds(config);
            return true;
        } catch (e) {
            console.error('[ThemeManager] applyConfig error:', e);
            return false;
        }
    },

    async applyTheme(themeName) {
        try {
            const themeData = await this.loadTheme(themeName);
            if (!themeData) {
                console.error(`[ThemeManager] Theme "${themeName}" not found, using dark`);
                if (themeName !== 'dark') return this.applyTheme('dark');
                return false;
            }

            // Step 1: Clear all effect layers from previous theme
            this._clearEffectLayers();

            // Step 2: Remove existing dynamic theme style
            const existingStyle = document.getElementById('dynamic-theme-style');
            if (existingStyle) existingStyle.remove();

            // Step 3: Generate and inject CSS variables
            const style = document.createElement('style');
            style.id = 'dynamic-theme-style';
            style.textContent = this.generateThemeCSS(themeData);
            document.head.appendChild(style);

            // Step 4: Update body class for legacy light-mode styles
            document.body.classList.remove('light-mode');
            if (themeName === 'light') {
                document.body.classList.add('light-mode');
            }

            // Step 5: Inject effect layers
            this._injectBackground(themeData);
            this._injectOverlay(themeData);
            this._injectWatermark(themeData);
            this._injectTint(themeData);
            this._injectCanvas(themeData);
            this._injectWidgets(themeData);
            this._setupParallax(themeData);
            this._setupCursorTrail(themeData);
            this._setupIdleEscalation(themeData);
            this._setupMessageReveal(themeData);
            this._setupSounds(themeData);

            this.currentTheme = themeName;
            localStorage.setItem('agent-zero-theme', themeName);
            document.cookie = `agent-zero-theme=${themeName}; path=/; max-age=31536000; SameSite=Lax`;
            console.log(`[ThemeManager] Applied theme: ${themeData.name} by ${themeData.author}`);
            return true;
        } catch (error) {
            console.error('[ThemeManager] Error applying theme:', error);
            return false;
        }
    },

    // Generate CSS variables from theme data
    generateThemeCSS(themeData) {
        const colors = themeData.colors || {};
        const panel = themeData.panel || {};
        const panelOpacity = panel.opacity != null ? panel.opacity : 1.0;
        const backdropBlur = panel.backdrop_blur != null ? panel.backdrop_blur : 0;

        // @property — register key color vars as typed <color> so the browser
        // can interpolate them when :root transitions fire on theme switch.
        // Gracefully ignored by browsers that don't support @property.
        const colorDefaults = {
            '--color-background': '#131313', '--color-text': '#ffffff',
            '--color-accent':     '#cf6679', '--color-primary': '#737a81',
            '--color-secondary':  '#656565', '--color-message-bg': '#2d2d2d',
        };
        let css = '';
        for (const [prop, init] of Object.entries(colorDefaults)) {
            css += `@property ${prop} { syntax: '<color>'; inherits: true; initial-value: ${init}; }\n`;
        }
        css += `:root {\n`;
        css += `  /* Theme: ${themeData.name} by ${themeData.author} */\n`;
        // Animate color custom properties on theme switch (works only for @property-registered vars)
        css += `  transition: --color-background 0.35s ease, --color-text 0.35s ease,\n`;
        css += `    --color-accent 0.35s ease, --color-primary 0.35s ease,\n`;
        css += `    --color-secondary 0.35s ease, --color-message-bg 0.35s ease;\n`;
        css += `  --color-background: ${colors.background || '#131313'};\n`;
        css += `  --color-text: ${colors.text || '#ffffff'};\n`;
        css += `  --color-text-muted: ${colors['text-muted'] || '#d4d4d4e4'};\n`;
        css += `  --color-primary: ${colors.primary || '#737a81'};\n`;
        css += `  --color-secondary: ${colors.secondary || '#656565'};\n`;
        css += `  --color-accent: ${colors.accent || '#cf6679'};\n`;
        css += `  --color-message-bg: ${colors['message-bg'] || '#2d2d2d'};\n`;
        css += `  --color-highlight: ${colors.highlight || '#2b5ab9'};\n`;
        css += `  --color-message-text: ${colors['message-text'] || '#e0e0e0'};\n`;
        css += `  --color-panel: ${colors.panel || '#1a1a1a'};\n`;
        css += `  --color-border: ${colors.border || '#444444a8'};\n`;
        css += `  --color-input: ${colors.input || '#131313'};\n`;
        css += `  --color-input-focus: ${colors['input-focus'] || '#101010'};\n`;
        css += `  --color-chat-background: ${colors['chat-background'] || '#212121'};\n`;
        css += `  --color-error-text: ${colors['error-text'] || '#e72323'};\n`;
        css += `  --color-warning-text: ${colors['warning-text'] || '#e79c23'};\n`;
        css += `  --color-table-row: ${colors['table-row'] || '#272727'};\n`;

        if (themeData.fonts && themeData.fonts.main) {
            css += `  --font-family-main: ${themeData.fonts.main};\n`;
        }
        if (themeData.fonts && themeData.fonts.code) {
            css += `  --font-family-code: ${themeData.fonts.code};\n`;
        }

        // Panel translucency vars
        css += `  --panel-opacity: ${panelOpacity};\n`;
        css += `  --panel-backdrop-blur: ${backdropBlur}px;\n`;

        // Background hover from border color
        const borderColor = colors.border || '#444444a8';
        css += `  --color-background-hover: color-mix(in srgb, ${borderColor} 50%, transparent);\n`;
        css += `}\n`;

        // Background image via html::before pseudo-element.
        // Using ::before instead of html { background-image } lets us apply
        // filter: blur() to the image alone without blurring page content.
        // html::before is a child of the root stacking context and paints
        // before body, so it always appears behind all UI elements.
        // html retains only the fallback background-color.
        const hasBgImage = (themeData.background || {}).type === 'image' && (themeData.background || {}).src;
        if (hasBgImage) {
            const bg = themeData.background;
            const baseColor = colors.background || '#131313';
            const src     = bg.src;
            const size    = bg.size || 'cover';
            const pos     = bg.position || 'center';
            const blur     = bg.blur     != null ? Number(bg.blur)    : 0;
            const opacity  = bg.opacity  != null ? Number(bg.opacity) : 1;
            const parallax = bg.parallax ?? false;
            // Expand beyond viewport: 2× blur-radius to hide feathered edges,
            // plus 30px extra when parallax drift is active to hide drift edges.
            const blurInset = blur > 0 ? blur * 2 : 0;
            const inset = (blurInset > 0 || parallax)
                ? `${-(blurInset + (parallax ? 30 : 0))}px`
                : '0';
            css += `\n/* Background image on html::before — blur-safe, never affects UI */\n`;
            css += `html { background-color: ${baseColor} !important; }\n`;
            css += `html::before {\n`;
            css += `  content: '' !important;\n`;
            css += `  position: fixed !important;\n`;
            css += `  inset: ${inset} !important;\n`;
            css += `  background-image: url(${src}) !important;\n`;
            css += `  background-size: ${size} !important;\n`;
            css += `  background-position: ${pos} !important;\n`;
            css += `  background-repeat: no-repeat !important;\n`;
            css += `  pointer-events: none !important;\n`;
            if (opacity < 1) css += `  opacity: ${opacity} !important;\n`;
            if (blur > 0)    css += `  filter: blur(${blur}px) !important;\n`;
            css += `}\n`;
            css += `body { background-color: transparent !important; }\n`;
        }

        // Panel + chat area translucency CSS override when opacity < 1 or blur > 0.
        // #chat-history must be included — it has its own background-color that
        // covers the SVG background layer unless made semi-transparent too.
        if (panelOpacity < 1.0 || backdropBlur > 0) {
            const panelColor = colors.panel || '#1a1a1a';
            const chatBgColor = colors['chat-background'] || '#212121';
            const pct = Math.round(panelOpacity * 100);
            css += `\n`;
            css += `/* Panel + chat translucency for atmospheric/immersive themes */\n`;
            css += `#left-panel, .right-panel, .panel, #input-section {\n`;
            css += `  background-color: color-mix(in srgb, ${panelColor} ${pct}%, transparent) !important;\n`;
            css += `  backdrop-filter: blur(${backdropBlur}px) !important;\n`;
            css += `  -webkit-backdrop-filter: blur(${backdropBlur}px) !important;\n`;
            css += `}\n`;
            css += `#chat-history {\n`;
            css += `  background-color: color-mix(in srgb, ${chatBgColor} ${pct}%, transparent) !important;\n`;
            css += `  backdrop-filter: blur(${backdropBlur}px) !important;\n`;
            css += `  -webkit-backdrop-filter: blur(${backdropBlur}px) !important;\n`;
            css += `}\n`;
        }

        // Scrollbar theming — themed thumb using primary/accent colors.
        // ::-webkit-scrollbar targets Chrome/Edge/Safari; scrollbar-* targets Firefox.
        const sc  = colors.primary  || '#737a81';
        const sca = colors.accent   || '#cf6679';
        const scb = colors.background || '#131313';
        css += `\n/* Scrollbar theming */\n`;
        css += `::-webkit-scrollbar { width: 5px; height: 5px; }\n`;
        css += `::-webkit-scrollbar-track { background: transparent; }\n`;
        css += `::-webkit-scrollbar-thumb { background: ${sc}88; border-radius: 3px; }\n`;
        css += `::-webkit-scrollbar-thumb:hover { background: ${sca}; }\n`;
        css += `html { scrollbar-width: thin; scrollbar-color: ${sc}88 transparent; }\n`;

        // Parallax drift animation on the background pseudo-element.
        // Uses transform (Composite path only — no Layout/Paint cost).
        // Requires extra inset to prevent edge peep when element drifts.
        const bgParallax = (themeData.background || {}).parallax;
        if (bgParallax) {
            css += `\n/* Background parallax drift */\n`;
            css += `html::before { animation: theme-bg-drift 50s ease-in-out infinite !important; }\n`;
        }

        return css;
    },

    // ─── Widget System ──────────────────────────────────────────────────────

    _clearWidgets() {
        const container = document.getElementById('theme-widgets');
        if (container) container.remove();
        this._widgetElements = [];
        if (this._agentObserver) {
            this._agentObserver.disconnect();
            this._agentObserver = null;
        }
        if (this._stateTimer) {
            clearTimeout(this._stateTimer);
            this._stateTimer = null;
        }
    },

    notifyState(state) {
        const prev = this._widgetState;
        this._widgetState = state;

        // Sound triggers — play on state transitions only (not on repeated same state)
        if (this._soundEnabled && this._audioUnlocked && state !== prev) {
            if (state === 'active') {
                this._playSound('codec_connect');
            } else if (state === 'thinking' && prev === 'idle') {
                this._playSound('alert_ping');
            } else if (state === 'escalated') {
                this._playSound('caution');
            }
        }

        for (const widget of this._widgetElements) {
            if (widget._onStateChange) {
                try { widget._onStateChange(state); } catch(e) {}
            }
        }
    },

    _setupAgentObserver() {
        // MutationObserver: detect new AI message blocks.
        // Grace period: ignore mutations for the first 1500ms — that's history
        // replay on page load (all existing messages flood the DOM at once and
        // would otherwise spam the exclamation widget / state machine).
        const observerStart = Date.now();
        const observer = new MutationObserver((mutations) => {
            if (Date.now() - observerStart < 1500) return;
            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType !== 1) continue;
                    const cls = (node.className || '') + (node.getAttribute?.('data-role') || '');
                    const hasContent = node.children?.length > 0 && (node.innerHTML?.length || 0) > 80;
                    if (hasContent && (cls.includes('agent') || cls.includes('assistant') ||
                        node.querySelector?.('[class*="agent-message"]') ||
                        node.querySelector?.('[class*="ai-message"]'))) {
                        this.notifyState('active');
                        clearTimeout(this._stateTimer);
                        this._stateTimer = setTimeout(() => this.notifyState('idle'), 3000);
                    }
                }
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
        this._agentObserver = observer;

        // Input → thinking state
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey && e.target.tagName === 'TEXTAREA') {
                this.notifyState('thinking');
            }
        }, true);
        document.addEventListener('click', (e) => {
            if (e.target.closest('#send-message-button, [data-send], button[type="submit"]')) {
                this.notifyState('thinking');
            }
        }, true);
    },

    _positionStyle(position) {
        // Named slots with sensible defaults
        const named = {
            'top-left':     'top: 14px; left: 14px;',
            'top-right':    'top: 14px; right: 14px;',
            'bottom-left':  'bottom: 70px; left: 14px;',
            'bottom-right': 'bottom: 70px; right: 14px;',
        };
        if (typeof position === 'string') return named[position] || named['bottom-right'];

        // Object format: { top, right, bottom, left } with arbitrary CSS values.
        // Allows game-accurate placement that clears Agent Zero chrome exactly.
        // Example: { "top": "68px", "right": "14px" }
        if (typeof position === 'object' && position !== null) {
            return Object.entries(position)
                .map(([k, v]) => `${k}: ${v}`)
                .join('; ') + ';';
        }
        return named['bottom-right'];
    },

    _ensureKeyframes() {
        if (document.getElementById('theme-widget-keyframes')) return;
        const kf = document.createElement('style');
        kf.id = 'theme-widget-keyframes';
        kf.textContent = [
            '@keyframes theme-blink { 0%,100%{opacity:0.85} 50%{opacity:0.15} }',
            '@keyframes theme-bob { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-3px)} }',
            '@keyframes theme-shake { 0%,100%{transform:rotate(0deg)} 25%{transform:rotate(-2.5deg)} 75%{transform:rotate(2.5deg)} }',
            '@keyframes theme-widget-enter { 0%{opacity:0;transform:scale(0.72)} 65%{opacity:1;transform:scale(1.05)} 82%{transform:scale(0.97)} 100%{opacity:1;transform:scale(1)} }',
            '@keyframes theme-ca { 0%,100%{text-shadow:none} 20%{text-shadow:-2px 0 2px rgba(255,0,0,0.75),2px 0 2px rgba(0,100,255,0.75)} 45%{text-shadow:2px 0 3px rgba(255,0,0,0.5),-2px 0 3px rgba(0,200,255,0.5)} 70%{text-shadow:-1px 0 1px rgba(255,50,50,0.35),1px 0 1px rgba(50,50,255,0.35)} }',
            '@keyframes theme-scan-left { from{clip-path:inset(0 100% 0 0)} to{clip-path:inset(0 0% 0 0)} }',
            '@keyframes theme-scan-top  { from{clip-path:inset(100% 0 0 0)} to{clip-path:inset(0 0 0 0)} }',
            '@keyframes theme-fade-in-msg { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }',
            '@keyframes theme-bg-drift { 0%{transform:translate(0,0)} 25%{transform:translate(10px,-10px)} 50%{transform:translate(0,-16px)} 75%{transform:translate(-10px,-10px)} 100%{transform:translate(0,0)} }',
            // View Transitions — asymmetric fade: quick out, slower in
            '::view-transition-old(root) { animation: 180ms ease-in both theme-vt-out; }',
            '::view-transition-new(root) { animation: 320ms ease-out both theme-vt-in; }',
            '@keyframes theme-vt-out { from{opacity:1} to{opacity:0} }',
            '@keyframes theme-vt-in  { from{opacity:0} to{opacity:1} }',
        ].join('\n');
        document.head.appendChild(kf);
    },

    _injectWidgets(themeData) {
        const widgets = themeData.widgets;
        if (!widgets || !widgets.length) return;
        this._ensureKeyframes();

        const container = document.createElement('div');
        container.id = 'theme-widgets';
        container.style.cssText = 'position: fixed; inset: 0; z-index: 10000; pointer-events: none; overflow: hidden;';

        const bootDef = widgets.find(w => w.type === 'boot-sequence');

        for (const def of widgets) {
            if (def.type === 'boot-sequence') continue;
            try {
                const el = this._createWidget(def, themeData);
                if (el) {
                    container.appendChild(el);
                    if (!this._reducedMotion) {
                        el.style.animation = 'theme-widget-enter 0.4s cubic-bezier(0.34,1.56,0.64,1) both';
                    }
                    if (el._onStateChange) this._widgetElements.push(el);
                }
            } catch(e) {
                console.warn('[ThemeManager] Widget error:', def.type, e);
            }
        }

        document.body.appendChild(container);
        this._setupAgentObserver();

        if (bootDef) this._runBootSequence(bootDef);
    },

    _createWidget(def, themeData) {
        const map = {
            'status-badge':  () => this._widgetStatusBadge(def),
            'gauge':         () => this._widgetGauge(def),
            'corner-label':  () => this._widgetCornerLabel(def),
            'ping-radar':    () => this._widgetPingRadar(def),
            'cassette':      () => this._widgetCassette(def),
            'moon-phase':    () => this._widgetMoonPhase(def),
            'exclamation':   () => this._widgetExclamation(def),
            'compass':       () => this._widgetCompass(def),
            'water-gauge':   () => this._widgetWaterGauge(def),
            'cctv-badge':    () => this._widgetCCTV(def),
            'pod-badge':     () => this._widgetPodBadge(def),
        };
        return map[def.type] ? map[def.type]() : null;
    },

    _widgetStatusBadge(def) {
        const el = document.createElement('div');
        el.style.cssText = `position: absolute; ${this._positionStyle(def.position)}
            font-family: monospace; font-size: 11px; font-weight: bold;
            padding: 4px 10px; border-radius: 3px; letter-spacing: 1.5px;
            border: 1px solid currentColor; transition: color 0.3s, background-color 0.3s;`;
        const states = def.states || {};
        const update = (state) => {
            const s = states[state] || states['idle'] || { text: state.toUpperCase(), color: '#888' };
            el.textContent = s.text;
            el.style.color = s.color;
            el.style.backgroundColor = s.color + '18';
            el.style.borderColor = s.color + '88';
            el.style.animation = s.blink ? 'theme-blink 0.9s step-end infinite' : 'none';
        };
        update('idle');
        el._onStateChange = update;
        return el;
    },

    _widgetGauge(def) {
        const color = def.color || '#4a7c3f';
        const lowColor = def.low_color || '#c0392b';
        const lowThreshold = def.low_threshold || 0.2;
        const depleteRate = (def.deplete_rate || 0.6) / 60;

        const wrapper = document.createElement('div');
        wrapper.style.cssText = `position: absolute; ${this._positionStyle(def.position)} font-family: monospace; font-size: 10px; letter-spacing: 1px;`;

        const label = document.createElement('div');
        label.textContent = def.label || 'GAUGE';
        label.style.cssText = `color: ${color}; margin-bottom: 3px;`;

        const track = document.createElement('div');
        track.style.cssText = `width: ${def.width || 110}px; height: 5px; background: rgba(255,255,255,0.08); border: 1px solid ${color}44; border-radius: 2px; overflow: hidden;`;

        const fill = document.createElement('div');
        fill.style.cssText = `height: 100%; width: 100%; background: ${color}; border-radius: 2px; transform: scaleX(1); transform-origin: left center; transition: background 0.5s;`;
        track.appendChild(fill);
        wrapper.appendChild(label);
        wrapper.appendChild(track);

        let value = 1.0;
        let lastTime = Date.now();
        let active = false;
        let escalated = false;

        const tick = () => {
            if (!document.getElementById('theme-widgets')) return;
            const now = Date.now();
            const dt = (now - lastTime) / 1000;
            lastTime = now;
            if (active) {
                const mult = escalated ? 3.0 : 1.0;
                value = Math.max(0, value - depleteRate * dt * mult);
            } else value = Math.min(1.0, value + depleteRate * 1.5 * dt);
            fill.style.transform = `scaleX(${value})`;
            const c = value < lowThreshold ? lowColor : color;
            fill.style.background = c;
            label.style.color = c;
            requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);

        wrapper._onStateChange = (state) => {
            active = (state !== 'idle');
            escalated = (state === 'escalated');
        };
        return wrapper;
    },

    _widgetCornerLabel(def) {
        const el = document.createElement('div');
        el.style.cssText = `position: absolute; ${this._positionStyle(def.position)}
            font-family: monospace; font-size: ${def.font_size || '10px'};
            color: ${def.color || '#888'}; letter-spacing: 1px; opacity: 0.75;`;
        const texts = def.cycle || [def.text || ''];
        let idx = 0;
        el.textContent = texts[0];
        if (def.cycle_trigger === 'agent-response') {
            el._onStateChange = (state) => {
                if (state === 'active') { idx = (idx + 1) % texts.length; el.textContent = texts[idx]; }
            };
        } else if (def.cycle_interval) {
            setInterval(() => { idx = (idx + 1) % texts.length; el.textContent = texts[idx]; }, def.cycle_interval * 1000);
        }
        return el;
    },

    _widgetPingRadar(def) {
        const size = def.size || 56;
        const color = def.color || '#00ccaa';
        const canvas = document.createElement('canvas');
        canvas.width = canvas.height = size;
        canvas.style.cssText = `position: absolute; ${this._positionStyle(def.position)} opacity: 0.55;`;
        const ctx = canvas.getContext('2d');
        const cx = size / 2, cy = size / 2, maxR = size / 2 - 2;
        const rings = [];

        const addRing = () => rings.push({ r: 3, alpha: 0.9 });
        addRing();
        setInterval(addRing, def.interval || 18000);

        const draw = () => {
            if (!document.getElementById('theme-widgets')) return;
            ctx.clearRect(0, 0, size, size);
            ctx.strokeStyle = color; ctx.lineWidth = 1;
            ctx.globalAlpha = 0.35;
            ctx.beginPath(); ctx.arc(cx, cy, maxR * 0.5, 0, Math.PI * 2); ctx.stroke();
            ctx.beginPath(); ctx.arc(cx, cy, maxR, 0, Math.PI * 2); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(cx - 7, cy); ctx.lineTo(cx + 7, cy); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(cx, cy - 7); ctx.lineTo(cx, cy + 7); ctx.stroke();
            ctx.fillStyle = color; ctx.globalAlpha = 0.6;
            ctx.beginPath(); ctx.arc(cx, cy, 2, 0, Math.PI * 2); ctx.fill();
            for (let i = rings.length - 1; i >= 0; i--) {
                const p = rings[i];
                p.r += 0.6; p.alpha = (1 - p.r / maxR) * 0.85;
                if (p.alpha <= 0) { rings.splice(i, 1); continue; }
                ctx.globalAlpha = p.alpha;
                ctx.beginPath(); ctx.arc(cx, cy, p.r, 0, Math.PI * 2); ctx.stroke();
            }
            ctx.globalAlpha = 1;
            requestAnimationFrame(draw);
        };
        draw();
        return canvas;
    },

    _widgetCassette(def) {
        const color = def.color || '#c8a96e';
        const size = def.size || 52;
        const h = Math.round(size * 0.65);
        const canvas = document.createElement('canvas');
        canvas.width = size; canvas.height = h;
        canvas.style.cssText = `position: absolute; ${this._positionStyle(def.position)} opacity: 0.7;`;
        const ctx = canvas.getContext('2d');
        let angle = 0; let spinning = false;

        const draw = () => {
            if (!document.getElementById('theme-widgets')) return;
            ctx.clearRect(0, 0, size, h);
            ctx.strokeStyle = color; ctx.lineWidth = 1.2; ctx.globalAlpha = 0.85;
            // Body
            ctx.strokeRect(2, 2, size - 4, h - 4);
            // Reels
            const r = h * 0.27;
            for (const rx of [size * 0.3, size * 0.7]) {
                const ry = h * 0.5;
                ctx.beginPath(); ctx.arc(rx, ry, r, 0, Math.PI * 2); ctx.stroke();
                ctx.beginPath(); ctx.arc(rx, ry, r * 0.28, 0, Math.PI * 2); ctx.stroke();
                for (let i = 0; i < 3; i++) {
                    const a = angle + (i * Math.PI * 2) / 3;
                    ctx.beginPath();
                    ctx.moveTo(rx + Math.cos(a) * r * 0.28, ry + Math.sin(a) * r * 0.28);
                    ctx.lineTo(rx + Math.cos(a) * r * 0.83, ry + Math.sin(a) * r * 0.83);
                    ctx.stroke();
                }
            }
            // Tape window arc
            ctx.beginPath(); ctx.arc(size * 0.5, h * 1.12, h * 0.72, Math.PI * 1.08, Math.PI * 1.92); ctx.stroke();
            if (spinning) angle += 0.05;
            requestAnimationFrame(draw);
        };
        draw();
        canvas._onStateChange = (state) => { spinning = (state === 'thinking'); };
        return canvas;
    },

    _widgetMoonPhase(def) {
        const el = document.createElement('div');
        el.style.cssText = `position: absolute; ${this._positionStyle(def.position)}
            font-size: ${def.font_size || '20px'}; color: ${def.color || '#c8b88a'};
            opacity: 0.65; font-family: serif; line-height: 1; cursor: default;`;
        const known = new Date(2000, 0, 6);
        const diff = (Date.now() - known) / 86400000;
        const cycle = 29.530588853;
        const phase = ((diff % cycle) + cycle) % cycle;
        const glyphs = ['🌑','🌒','🌓','🌔','🌕','🌖','🌗','🌘'];
        el.textContent = glyphs[Math.floor(phase / (cycle / 8))];
        el.title = `Moon phase — day ${Math.round(phase)} of ${Math.round(cycle)}`;
        return el;
    },

    _widgetExclamation(def) {
        const el = document.createElement('div');
        el.style.cssText = `position: absolute; top: 50%; left: 50%;
            transform: translate(-50%, -180px);
            font-family: 'Arial Black', Arial, sans-serif; font-size: 48px; font-weight: 900;
            color: ${def.color || '#ffcc00'}; opacity: 0; pointer-events: none;
            text-shadow: 0 0 12px ${def.color || '#ffcc00'}, 2px 2px 0 #000;
            transition: opacity 0.08s;`;
        el.textContent = '!';
        el._onStateChange = (state) => {
            if (state === 'active' || state === 'escalated') {
                el.style.opacity = '1';
                el.style.animation = 'theme-ca 0.35s ease-out';
                clearTimeout(el._timer);
                el._timer = setTimeout(() => {
                    el.style.opacity = '0';
                    el.style.animation = 'none';
                }, 700);
            }
        };
        return el;
    },

    _widgetCompass(def) {
        const size = def.size || 44;
        const color = def.color || '#4a9eff';
        const canvas = document.createElement('canvas');
        canvas.width = canvas.height = size;
        canvas.style.cssText = `position: absolute; ${this._positionStyle(def.position)} opacity: 0.5;`;
        const ctx = canvas.getContext('2d');
        const cx = size / 2, cy = size / 2, r = size / 2 - 2;
        const speed = (def.rotation_speed || 1.5) * Math.PI / 180 / 60;
        let angle = 0;

        const draw = () => {
            if (!document.getElementById('theme-widgets')) return;
            ctx.clearRect(0, 0, size, size);
            ctx.save(); ctx.translate(cx, cy); ctx.rotate(angle);
            ctx.strokeStyle = color; ctx.lineWidth = 1;
            ctx.globalAlpha = 0.5; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
            ctx.font = `bold ${Math.round(size * 0.18)}px monospace`;
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = color;
            for (const [lbl, a] of [['N',0],['E',Math.PI/2],['S',Math.PI],['W',-Math.PI/2]]) {
                ctx.save(); ctx.rotate(a); ctx.globalAlpha = lbl === 'N' ? 0.9 : 0.4;
                ctx.fillText(lbl, 0, -(r * 0.62)); ctx.restore();
            }
            ctx.globalAlpha = 1;
            ctx.beginPath(); ctx.moveTo(0,-(r*0.5)); ctx.lineTo(3,0); ctx.lineTo(0,r*0.28); ctx.lineTo(-3,0); ctx.closePath();
            ctx.fillStyle = color; ctx.fill();
            ctx.restore();
            angle += speed;
            requestAnimationFrame(draw);
        };
        draw();
        return canvas;
    },

    _widgetWaterGauge(def) {
        const color = def.color || 'rgba(0,120,200,0.5)';
        const el = document.createElement('div');
        el.style.cssText = `position: absolute; ${def.position === 'right' ? 'top: 20%; right: 0;' : 'top: 20%; left: 0;'}
            width: 4px; height: 60%; background: rgba(255,255,255,0.06);
            border-${def.position === 'right' ? 'left' : 'right'}: 1px solid ${color};`;
        const fill = document.createElement('div');
        fill.style.cssText = `position: absolute; bottom: 0; left: 0; right: 0; height: 100%; background: ${color}; transform: scaleY(0); transform-origin: bottom center;`;
        el.appendChild(fill);
        const duration = (def.fill_duration || 3600) * 1000;
        const start = performance.now();
        const update = () => {
            if (!document.getElementById('theme-widgets')) return;
            const pct = Math.min(1, (performance.now() - start) / duration);
            fill.style.transform = `scaleY(${pct})`;
            if (pct < 1) setTimeout(update, 10000);
        };
        setTimeout(update, 100);
        return el;
    },

    _widgetCCTV(def) {
        const color = def.color || '#ff4444';
        const cameras = def.cameras || ['CAM 01','CAM 02','CAM 03','CAM 04'];
        let camIdx = 0;

        const el = document.createElement('div');
        el.style.cssText = `position: absolute; ${this._positionStyle(def.position)} font-family: monospace; font-size: 10px; letter-spacing: 1px; opacity: 0.8;`;

        const row = document.createElement('div');
        row.style.cssText = 'display: flex; align-items: center; gap: 6px;';

        const dot = document.createElement('span');
        dot.style.cssText = `width: 6px; height: 6px; background: ${color}; border-radius: 50%; display: inline-block; flex-shrink: 0; animation: theme-blink 1.4s step-end infinite;`;

        const text = document.createElement('span');
        text.style.color = color;
        text.textContent = `${cameras[0]} MONITORING`;

        row.appendChild(dot); row.appendChild(text);
        el.appendChild(row);

        setInterval(() => {
            camIdx = (camIdx + 1) % cameras.length;
            if (this._widgetState === 'idle') text.textContent = `${cameras[camIdx]} MONITORING`;
        }, (def.switch_interval || 8) * 1000);

        el._onStateChange = (state) => {
            if (state === 'thinking') { text.textContent = 'ALERT — SCANNING'; text.style.color = '#ff8800'; dot.style.background = '#ff8800'; }
            else if (state === 'active') { text.textContent = 'SIGNAL DETECTED'; text.style.color = '#ffcc00'; dot.style.background = '#ffcc00'; }
            else { text.textContent = `${cameras[camIdx]} MONITORING`; text.style.color = color; dot.style.background = color; }
        };
        return el;
    },

    _widgetPodBadge(def) {
        const baseColor = def.color || '#dddddd';
        const el = document.createElement('div');
        el.style.cssText = `position: absolute; ${this._positionStyle(def.position)}
            font-family: monospace; font-size: 10px; letter-spacing: 1.5px;
            color: ${baseColor}; border: 1px solid ${baseColor}33; padding: 4px 10px; border-radius: 2px;`;
        const pod = def.pod || 'POD 042';
        const states = {
            idle:     { text: `${pod}: STANDBY`,            color: baseColor },
            thinking: { text: `${pod}: ANALYZING`,          color: '#88ccff' },
            active:   { text: `${pod}: DIRECTIVE COMPLETE`, color: '#88ffaa' },
        };
        const update = (state) => {
            const s = states[state] || states.idle;
            el.textContent = s.text; el.style.color = s.color; el.style.borderColor = s.color + '33';
        };
        update('idle');
        el._onStateChange = update;
        return el;
    },

    _runBootSequence(def) {
        const overlay = document.createElement('div');
        overlay.style.cssText = `position: fixed; inset: 0; z-index: 99999;
            background: ${def.background || 'rgba(0,0,0,0.97)'};
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            font-family: monospace; font-size: 14px; letter-spacing: 2px;
            color: ${def.color || '#ffffff'}; gap: 10px; transition: opacity 0.5s;`;
        const lines = def.lines || [];
        const lineEls = lines.map(text => {
            const div = document.createElement('div');
            div.textContent = text; div.style.opacity = '0'; div.style.transition = 'opacity 0.35s';
            overlay.appendChild(div); return div;
        });
        document.body.appendChild(overlay);
        const duration = def.duration || 2600;
        const delay = duration / (lines.length + 2);
        lineEls.forEach((el, i) => setTimeout(() => { el.style.opacity = '1'; }, i * delay + 200));
        setTimeout(() => {
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 500);
        }, duration);
    },

    // ─── Phase 3: Parallax, Cursor Trails, Idle Escalation, Message Reveal ──

    _setupParallax(themeData) {
        const cfg = themeData.parallax;
        if (!cfg || !cfg.enabled || this._reducedMotion) return;
        const strength = cfg.strength != null ? cfg.strength : 1.0;
        // Background is now on html via CSS background-image, not a translate-able div.
        // Parallax for the background layer is achieved by animating backgroundPosition.
        const bgCoeff    = 0.025 * strength;
        const divLayers  = [
            { id: 'theme-overlay',  coeff: 0.012 * strength },
            { id: 'theme-canvas',   coeff: 0.006 * strength },
            { id: 'theme-widgets',  coeff: 0.003 * strength },
        ];
        let targetX = 0, targetY = 0, curX = 0, curY = 0;
        const mousemoveHandler = (e) => {
            targetX = e.clientX - window.innerWidth  / 2;
            targetY = e.clientY - window.innerHeight / 2;
        };
        document.addEventListener('mousemove', mousemoveHandler, { passive: true });
        this._parallaxHandler = mousemoveHandler;
        const tick = () => {
            if (!this._parallaxHandler) return;
            curX += (targetX - curX) * 0.08;
            curY += (targetY - curY) * 0.08;
            // Slide the html background-image to create depth
            const xOff = (curX * bgCoeff).toFixed(2);
            const yOff = (curY * bgCoeff).toFixed(2);
            document.documentElement.style.backgroundPosition =
                `calc(50% + ${xOff}px) calc(50% + ${yOff}px)`;
            // Translate overlay / canvas / widget divs
            for (const { id, coeff } of divLayers) {
                const el = document.getElementById(id);
                if (el) el.style.transform = `translate(${(curX * coeff).toFixed(2)}px,${(curY * coeff).toFixed(2)}px)`;
            }
            requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
    },

    _clearParallax() {
        if (this._parallaxHandler) {
            document.removeEventListener('mousemove', this._parallaxHandler);
            this._parallaxHandler = null;
        }
        // Reset html background-position
        document.documentElement.style.backgroundPosition = '';
        // Reset overlay/canvas/widget transforms
        for (const id of ['theme-overlay','theme-canvas','theme-widgets']) {
            const el = document.getElementById(id);
            if (el) el.style.transform = '';
        }
    },

    _setupCursorTrail(themeData) {
        const cfg = themeData.cursor_trail;
        if (!cfg || this._reducedMotion) return;
        const type = cfg.type || 'dots';
        const color = cfg.color || '#ffffff';
        const intensity = cfg.intensity != null ? cfg.intensity : 0.6;

        const canvas = document.createElement('canvas');
        canvas.id = 'theme-cursor-trail';
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        canvas.style.cssText = 'position:fixed;inset:0;z-index:99997;pointer-events:none;width:100%;height:100%;';
        document.body.appendChild(canvas);
        this._cursorCanvas = canvas;
        this._cursorParticles = [];
        const ctx = canvas.getContext('2d');

        window.addEventListener('resize', () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }, { passive: true });

        const spawnParticles = (mx, my) => {
            const count = Math.ceil(3 * intensity);
            for (let i = 0; i < count; i++) {
                const p = { x: mx, y: my, life: 1.0, radius: 1.5 + Math.random() * 1.5 };
                if (type === 'snow') {
                    p.vx = (Math.random() - 0.5) * 1.2;
                    p.vy = 0.6 + Math.random() * 1.5;
                    p.decay = 0.025 + Math.random() * 0.02;
                } else if (type === 'sparks') {
                    const a = Math.random() * Math.PI * 2;
                    const s = 1.5 + Math.random() * 3;
                    p.vx = Math.cos(a) * s; p.vy = Math.sin(a) * s;
                    p.radius = 1 + Math.random() * 1.5;
                    p.decay = 0.05 + Math.random() * 0.04;
                } else if (type === 'dust') {
                    p.vx = (Math.random() - 0.5) * 0.9;
                    p.vy = -(0.4 + Math.random() * 1.2);
                    p.radius = 1 + Math.random() * 2.5;
                    p.decay = 0.018 + Math.random() * 0.015;
                } else { // dots / matrix-dots
                    p.vx = (Math.random() - 0.5) * 0.4;
                    p.vy = (Math.random() - 0.5) * 0.4;
                    p.decay = 0.022 + Math.random() * 0.015;
                }
                this._cursorParticles.push(p);
            }
        };

        const mouseHandler = (e) => spawnParticles(e.clientX, e.clientY);
        document.addEventListener('mousemove', mouseHandler, { passive: true });
        this._cursorMouseHandler = mouseHandler;

        const draw = () => {
            if (!this._cursorRafId) return;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            for (let i = this._cursorParticles.length - 1; i >= 0; i--) {
                const p = this._cursorParticles[i];
                p.life -= p.decay; p.x += p.vx; p.y += p.vy;
                if (p.life <= 0) { this._cursorParticles.splice(i, 1); continue; }
                ctx.globalAlpha = p.life * 0.75;
                ctx.fillStyle = color;
                ctx.beginPath(); ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2); ctx.fill();
            }
            ctx.globalAlpha = 1;
            this._cursorRafId = requestAnimationFrame(draw);
        };
        this._cursorRafId = requestAnimationFrame(draw);
    },

    _clearCursorTrail() {
        if (this._cursorRafId) { cancelAnimationFrame(this._cursorRafId); this._cursorRafId = null; }
        if (this._cursorMouseHandler) {
            document.removeEventListener('mousemove', this._cursorMouseHandler);
            this._cursorMouseHandler = null;
        }
        if (this._cursorCanvas) { this._cursorCanvas.remove(); this._cursorCanvas = null; }
        this._cursorParticles = [];
    },

    _setupIdleEscalation(themeData) {
        const cfg = themeData.idle_escalation;
        if (!cfg || !cfg.enabled) return;
        const thresholdMs = (cfg.threshold_minutes || 5) * 60 * 1000;
        const color = cfg.color || '#ff8800';

        const badge = document.createElement('div');
        badge.id = 'theme-idle-badge';
        badge.style.cssText = `position:fixed;${this._positionStyle(cfg.position || 'bottom-left')}
            z-index:10001;font-family:monospace;font-size:11px;font-weight:bold;
            letter-spacing:1.5px;padding:4px 10px;border-radius:3px;
            border:1px solid ${color}88;color:${color};background:${color}18;
            opacity:0;transition:opacity 0.4s;pointer-events:none;
            animation:theme-blink 1.3s step-end infinite;`;
        badge.textContent = cfg.message || 'IDLE';
        document.body.appendChild(badge);

        const arm = () => {
            this._idleTimer = setTimeout(() => {
                this._idleEscalated = true;
                badge.style.opacity = '1';
                this.notifyState('escalated');
            }, thresholdMs);
        };

        const reset = () => {
            if (this._idleEscalated) {
                this._idleEscalated = false;
                badge.style.opacity = '0';
                this.notifyState('idle');
            }
            clearTimeout(this._idleTimer);
            arm();
        };

        this._idleResetHandler = reset;
        document.addEventListener('mousemove', reset, { passive: true });
        document.addEventListener('keydown',   reset, { passive: true });
        arm();
    },

    _clearIdleEscalation() {
        clearTimeout(this._idleTimer); this._idleTimer = null;
        if (this._idleResetHandler) {
            document.removeEventListener('mousemove', this._idleResetHandler);
            document.removeEventListener('keydown',   this._idleResetHandler);
            this._idleResetHandler = null;
        }
        this._idleEscalated = false;
        const badge = document.getElementById('theme-idle-badge');
        if (badge) badge.remove();
    },

    _setupMessageReveal(themeData) {
        const cfg = themeData.message_reveal;
        if (!cfg) return;
        const type = cfg.type || 'fade';
        const speed = cfg.speed != null ? cfg.speed : 1.0;
        this._msgRevealType = type;

        const applyReveal = (el) => {
            if (type === 'typewriter') {
                // Only typewriter if message contains plain <p> elements (no complex HTML)
                const paras = Array.from(el.querySelectorAll('p')).filter(p => !p.closest('pre') && !p.closest('code'));
                if (!paras.length) {
                    // Fallback to fade for complex content
                    el.style.animation = `theme-fade-in-msg ${(0.5/speed).toFixed(2)}s ease-out both`;
                    return;
                }
                let delay = 0;
                const charMs = Math.max(8, Math.round(22 / speed));
                for (const p of paras) {
                    const text = p.textContent;
                    if (!text.trim()) continue;
                    p.textContent = '';
                    for (let i = 0; i < Math.min(text.length, 400); i++) {
                        setTimeout((ch) => { p.textContent += ch; }, delay, text[i]);
                        delay += charMs;
                    }
                    if (text.length > 400) {
                        setTimeout(() => { p.textContent = text; }, delay);
                    }
                }
            } else if (type === 'scan') {
                el.style.clipPath = 'inset(0 100% 0 0)';
                el.style.animation = `theme-scan-left ${(0.55/speed).toFixed(2)}s ease-out both`;
            } else {
                el.style.opacity = '0';
                el.style.animation = `theme-fade-in-msg ${(0.45/speed).toFixed(2)}s ease-out both`;
            }
        };

        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType !== 1 || node.dataset?.themeRevealed) continue;
                    const cls = node.className || '';
                    const inner = (node.innerHTML || '');
                    if (inner.length < 80) continue;
                    if (cls.includes('agent') || cls.includes('assistant') || cls.includes('ai-') ||
                        node.querySelector?.('[class*="agent-message"]') ||
                        node.querySelector?.('[class*="ai-message"]')) {
                        node.dataset.themeRevealed = 'true';
                        try { applyReveal(node); } catch(e) {}
                    }
                }
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
        this._msgRevealObserver = observer;
    },

    _clearMessageReveal() {
        if (this._msgRevealObserver) { this._msgRevealObserver.disconnect(); this._msgRevealObserver = null; }
        this._msgRevealType = null;
    },

    // ─── Sound Design ────────────────────────────────────────────────────────
    // Supports both file-based audio (WAV/MP3/OGG via fetch+decodeAudioData)
    // and built-in synthesis fallbacks when no file is configured.
    // AudioContext is lazy-initialized on first user gesture (browser policy).
    //
    // Theme JSON:
    //   "sounds": {
    //     "enabled": true,
    //     "volume": 0.25,
    //     "codec_connect": "/themes/assets/sounds/codec.wav",
    //     "alert_ping":    "/themes/assets/sounds/alert.wav",
    //     "caution":       null
    //   }
    //
    // Event types: codec_connect, alert_ping, caution
    // If a src string is provided for an event, that file is used.
    // If null/absent, the built-in synthesized sound plays instead.

    _setupSounds(themeData) {
        const cfg = themeData.sounds || {};
        this._soundEnabled = cfg.enabled === true;
        this._soundVolume = cfg.volume != null ? Math.max(0, Math.min(1, cfg.volume)) : 0.3;

        // Collect per-event src paths from the theme config
        this._soundSrcs = {
            codec_connect: typeof cfg.codec_connect === 'string' ? cfg.codec_connect : null,
            alert_ping:    typeof cfg.alert_ping    === 'string' ? cfg.alert_ping    : null,
            caution:       typeof cfg.caution       === 'string' ? cfg.caution       : null,
        };

        if (!this._soundEnabled) return;

        // Initialise buffer cache for this theme (clears buffers from previous theme)
        this._soundBuffers = new Map();

        // AudioContext requires a user gesture. Register unlock on first interaction.
        // Once unlocked the handler removes itself and we pre-load any declared files.
        if (!this._audioUnlocked && !this._soundUnlockHandler) {
            const unlock = () => {
                if (!this._audioCtx) {
                    try {
                        this._audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    } catch(e) {
                        console.warn('[ThemeManager] Web Audio API unavailable');
                        this._soundEnabled = false;
                        return;
                    }
                }
                if (this._audioCtx.state === 'suspended') this._audioCtx.resume().catch(() => {});
                this._audioUnlocked = true;
                document.removeEventListener('click',   unlock);
                document.removeEventListener('keydown', unlock);
                this._soundUnlockHandler = null;
                // Pre-load files now that the AudioContext is live
                this._preloadSoundFiles();
            };
            document.addEventListener('click',   unlock, { passive: true });
            document.addEventListener('keydown', unlock, { passive: true });
            this._soundUnlockHandler = unlock;
        } else if (this._audioUnlocked) {
            // AudioContext already live from a previous theme — pre-load immediately
            this._preloadSoundFiles();
        }
    },

    // Fetch and decode each src declared in _soundSrcs.
    // Runs async in the background; _playSound falls back to synthesis until
    // the buffer is ready. Errors are silent — synthesis takes over.
    _preloadSoundFiles() {
        if (!this._soundSrcs || !this._audioCtx) return;
        const seen = new Set();
        for (const [, src] of Object.entries(this._soundSrcs)) {
            if (!src || seen.has(src)) continue;
            seen.add(src);
            if (this._soundBuffers.has(src)) continue; // already loaded
            fetch(src)
                .then(r => { if (!r.ok) throw new Error(r.status); return r.arrayBuffer(); })
                .then(ab => this._audioCtx.decodeAudioData(ab))
                .then(buf => {
                    this._soundBuffers.set(src, buf);
                    console.log(`[ThemeManager] Sound loaded: ${src}`);
                })
                .catch(e => console.warn(`[ThemeManager] Sound load failed (${src}): ${e.message}`));
        }
    },

    _clearSounds() {
        this._soundEnabled = false;
        this._soundSrcs = null;
        this._soundBuffers = null;
        if (this._soundUnlockHandler) {
            document.removeEventListener('click',   this._soundUnlockHandler);
            document.removeEventListener('keydown', this._soundUnlockHandler);
            this._soundUnlockHandler = null;
        }
        // AudioContext is kept alive — cheap to resume, expensive to recreate.
    },

    // Play a sound by event type.
    // If the theme provides a loaded AudioBuffer for this event, use it.
    // Otherwise fall back to the built-in synthesized sound.
    //
    //   codec_connect  — MGS codec squelch: two ascending square-wave chirps
    //   alert_ping     — Radar ping: single sine tone, fast decay
    //   caution        — Double beep: two low square pulses (CAUTION state)
    _playSound(type) {
        if (!this._soundEnabled || !this._audioCtx) return;
        if (this._audioCtx.state === 'suspended') { this._audioCtx.resume().catch(() => {}); return; }

        const ac  = this._audioCtx;
        const vol = this._soundVolume;
        const now = ac.currentTime;

        // File-based playback — if a decoded buffer is available, use it
        const src = this._soundSrcs?.[type];
        if (src && this._soundBuffers?.has(src)) {
            const source = ac.createBufferSource();
            const gain   = ac.createGain();
            source.buffer = this._soundBuffers.get(src);
            source.connect(gain); gain.connect(ac.destination);
            gain.gain.setValueAtTime(vol, now);
            source.start(now);
            return;
        }

        // Synthesis fallback — used when no file is configured or file not yet loaded
        if (type === 'codec_connect') {
            // Two-chirp codec squelch: 880 Hz → 1108 Hz, square wave, 80ms each
            for (const [freq, offset] of [[880, 0], [1108, 0.1]]) {
                const osc  = ac.createOscillator();
                const gain = ac.createGain();
                osc.connect(gain); gain.connect(ac.destination);
                osc.type = 'square';
                osc.frequency.setValueAtTime(freq, now + offset);
                gain.gain.setValueAtTime(0, now + offset);
                gain.gain.linearRampToValueAtTime(vol * 0.35, now + offset + 0.008);
                gain.gain.exponentialRampToValueAtTime(0.0001, now + offset + 0.08);
                osc.start(now + offset);
                osc.stop(now + offset + 0.09);
            }
        } else if (type === 'alert_ping') {
            // Single sine ping, 660 Hz, 180ms decay — soft radar pulse
            const osc  = ac.createOscillator();
            const gain = ac.createGain();
            osc.connect(gain); gain.connect(ac.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(660, now);
            gain.gain.setValueAtTime(0, now);
            gain.gain.linearRampToValueAtTime(vol * 0.28, now + 0.006);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.18);
            osc.start(now);
            osc.stop(now + 0.2);
        } else if (type === 'caution') {
            // Double beep at 440 Hz — CAUTION/STALEMATE state
            for (const offset of [0, 0.14]) {
                const osc  = ac.createOscillator();
                const gain = ac.createGain();
                osc.connect(gain); gain.connect(ac.destination);
                osc.type = 'square';
                osc.frequency.setValueAtTime(440, now + offset);
                gain.gain.setValueAtTime(0, now + offset);
                gain.gain.linearRampToValueAtTime(vol * 0.22, now + offset + 0.005);
                gain.gain.exponentialRampToValueAtTime(0.0001, now + offset + 0.06);
                osc.start(now + offset);
                osc.stop(now + offset + 0.07);
            }
        }
    },

    // ────────────────────────────────────────────────────────────────────────

    getCurrentTheme() {
        return this.currentTheme;
    },

    async switchTheme(themeName) {
        if (this.currentTheme === themeName) return true;
        if (!document.startViewTransition) return this.applyTheme(themeName);
        const t = document.startViewTransition(() => this.applyTheme(themeName));
        return t.finished.then(() => true).catch(() => this.applyTheme(themeName));
    }
};

// ─── Animation Classes ──────────────────────────────────────────────────────

class RainAnimation {
    constructor(ctx, canvas, intensity, color) {
        this.ctx = ctx;
        this.canvas = canvas;
        this.intensity = intensity != null ? intensity : 0.5;
        this.color = color || '#8aafc0';
        this._rafId = null;
        this._paused = false;
        this._drops = [];
        this._initDrops();
    }

    _initDrops() {
        const count = Math.floor(80 * this.intensity);
        this._drops = [];
        for (let i = 0; i < count; i++) this._drops.push(this._newDrop(true));
    }

    _newDrop(randomY) {
        const speed = 4 + Math.random() * 8;
        const length = 10 + Math.random() * 20;
        const alpha = 0.1 + Math.random() * 0.3;
        return { x: Math.random() * this.canvas.width, y: randomY ? Math.random() * this.canvas.height : -length, speed, length, alpha };
    }

    _draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        for (const drop of this._drops) {
            this.ctx.beginPath();
            this.ctx.strokeStyle = this.color;
            this.ctx.globalAlpha = drop.alpha;
            this.ctx.lineWidth = 1;
            this.ctx.moveTo(drop.x, drop.y);
            this.ctx.lineTo(drop.x - drop.length * 0.2, drop.y + drop.length);
            this.ctx.stroke();
            drop.y += drop.speed;
            drop.x -= drop.speed * 0.2;
            if (drop.y > this.canvas.height + drop.length) {
                Object.assign(drop, this._newDrop(false));
                drop.x = Math.random() * this.canvas.width;
            }
        }
        this.ctx.globalAlpha = 1;
        this._rafId = requestAnimationFrame(() => this._draw());
    }

    start() { if (this._rafId) return; this._paused = false; this._initDrops(); this._draw(); }
    stop() { if (this._rafId) { cancelAnimationFrame(this._rafId); this._rafId = null; } if (this.ctx) this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height); }
    pause() { if (this._rafId) { cancelAnimationFrame(this._rafId); this._rafId = null; this._paused = true; } }
    resume() { if (this._paused) { this._paused = false; this.start(); } }
}

class SnowAnimation {
    constructor(ctx, canvas, intensity, color) {
        this.ctx = ctx;
        this.canvas = canvas;
        this.intensity = intensity != null ? intensity : 0.5;
        this.color = color || '#ddeeff';
        this._rafId = null;
        this._paused = false;
        this._t = 0;
        this._flakes = [];
        this._initFlakes();
    }

    _initFlakes() {
        const count = Math.floor(60 * this.intensity);
        this._flakes = [];
        for (let i = 0; i < count; i++) {
            this._flakes.push({ x: Math.random() * this.canvas.width, y: Math.random() * this.canvas.height, radius: 1 + Math.random() * 2.5, speed: 0.5 + Math.random() * 1.5, drift: (Math.random() - 0.5) * 0.5, alpha: 0.4 + Math.random() * 0.5, phase: Math.random() * Math.PI * 2 });
        }
    }

    _draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        for (const f of this._flakes) {
            this.ctx.beginPath();
            this.ctx.fillStyle = this.color;
            this.ctx.globalAlpha = f.alpha;
            this.ctx.arc(f.x, f.y, f.radius, 0, Math.PI * 2);
            this.ctx.fill();
            f.y += f.speed;
            f.x += f.drift + Math.sin(this._t * 0.01 + f.phase) * 0.3;
            if (f.y > this.canvas.height) { f.y = -f.radius; f.x = Math.random() * this.canvas.width; }
        }
        this.ctx.globalAlpha = 1;
        this._t++;
        this._rafId = requestAnimationFrame(() => this._draw());
    }

    start() { if (this._rafId) return; this._paused = false; this._initFlakes(); this._draw(); }
    stop() { if (this._rafId) { cancelAnimationFrame(this._rafId); this._rafId = null; } if (this.ctx) this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height); }
    pause() { if (this._rafId) { cancelAnimationFrame(this._rafId); this._rafId = null; this._paused = true; } }
    resume() { if (this._paused) { this._paused = false; this.start(); } }
}

class ParticleAnimation {
    constructor(ctx, canvas, intensity, color) {
        this.ctx = ctx;
        this.canvas = canvas;
        this.intensity = intensity != null ? intensity : 0.5;
        this.color = color || '#ffffff';
        this._rafId = null;
        this._paused = false;
        this._particles = [];
        this._initParticles();
    }

    _initParticles() {
        const count = Math.floor(40 * this.intensity);
        this._particles = [];
        for (let i = 0; i < count; i++) {
            this._particles.push({ x: Math.random() * this.canvas.width, y: Math.random() * this.canvas.height, radius: 0.5 + Math.random() * 1.5, vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4, alpha: 0.1 + Math.random() * 0.4 });
        }
    }

    _draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        for (const p of this._particles) {
            this.ctx.beginPath();
            this.ctx.fillStyle = this.color;
            this.ctx.globalAlpha = p.alpha;
            this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            this.ctx.fill();
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0) p.x = this.canvas.width;
            if (p.x > this.canvas.width) p.x = 0;
            if (p.y < 0) p.y = this.canvas.height;
            if (p.y > this.canvas.height) p.y = 0;
        }
        this.ctx.globalAlpha = 1;
        this._rafId = requestAnimationFrame(() => this._draw());
    }

    start() { if (this._rafId) return; this._paused = false; this._initParticles(); this._draw(); }
    stop() { if (this._rafId) { cancelAnimationFrame(this._rafId); this._rafId = null; } if (this.ctx) this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height); }
    pause() { if (this._rafId) { cancelAnimationFrame(this._rafId); this._rafId = null; this._paused = true; } }
    resume() { if (this._paused) { this._paused = false; this.start(); } }
}

class StaticAnimation {
    constructor(ctx, canvas, intensity) {
        this.ctx = ctx;
        this.canvas = canvas;
        this.intensity = intensity != null ? intensity : 0.5;
        this._rafId = null;
        this._paused = false;
        this._frame = 0;
    }

    _draw() {
        this._frame++;
        if (this._frame % 3 === 0) {
            const imageData = this.ctx.createImageData(this.canvas.width, this.canvas.height);
            const data = imageData.data;
            const density = this.intensity * 0.03;
            for (let i = 0; i < data.length; i += 4) {
                if (Math.random() < density) {
                    const v = Math.random() * 255;
                    data[i] = v; data[i+1] = v; data[i+2] = v;
                    data[i+3] = Math.random() * 60;
                }
            }
            this.ctx.putImageData(imageData, 0, 0);
        }
        this._rafId = requestAnimationFrame(() => this._draw());
    }

    start() { if (this._rafId) return; this._paused = false; this._draw(); }
    stop() { if (this._rafId) { cancelAnimationFrame(this._rafId); this._rafId = null; } if (this.ctx) this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height); }
    pause() { if (this._rafId) { cancelAnimationFrame(this._rafId); this._rafId = null; this._paused = true; } }
    resume() { if (this._paused) { this._paused = false; this.start(); } }
}


if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => ThemeManager.init());
