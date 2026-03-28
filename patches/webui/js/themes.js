// Theme Management Module for Agent Zero
// Extended Aesthetic Theme Engine — Tier 1/2/3 support
// Handles CSS variables, background layers, overlay effects, and canvas animations

const ThemeManager = {
    currentTheme: 'dark',
    _animationId: null,
    _animationInstance: null,
    _reducedMotion: false,

    // Initialize theme system
    async init() {
        try {
            this._setupPerformanceListeners();
            const savedTheme = localStorage.getItem('agent-zero-theme') || 'dark';
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

        // Remove background layer
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

        // Remove canvas layer
        const cv = document.getElementById('theme-canvas');
        if (cv) {
            if (cv._resizeHandler) {
                window.removeEventListener('resize', cv._resizeHandler);
            }
            cv.remove();
        }
    },

    // Inject #theme-background div for background image
    _injectBackground(themeData) {
        const bg = themeData.background || {};
        const type = bg.type || 'none';
        if (type === 'none' || !bg.src) return;

        const div = document.createElement('div');
        div.id = 'theme-background';
        div.style.cssText = [
            'position: fixed',
            'inset: 0',
            'z-index: -10',
            'pointer-events: none',
            `background-image: url(${bg.src})`,
            `background-size: ${bg.size || 'cover'}`,
            `background-position: ${bg.position || 'center'}`,
            `background-repeat: no-repeat`,
            `opacity: ${bg.opacity != null ? bg.opacity : 0.15}`,
            `filter: blur(${bg.blur || 0}px)`,
            bg.blend_mode && bg.blend_mode !== 'normal' ? `mix-blend-mode: ${bg.blend_mode}` : ''
        ].filter(Boolean).join('; ') + ';';

        document.body.prepend(div);
    },

    // Inject #theme-overlay div with scanlines/vignette/noise/watermark children
    _injectOverlay(themeData) {
        const overlay = themeData.overlay || {};
        const scanlines = overlay.scanlines || {};
        const vignette = overlay.vignette || {};
        const noise = overlay.noise || {};
        const watermark = overlay.watermark || {};

        const hasAny = scanlines.enabled || vignette.enabled || noise.enabled || watermark.enabled;
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

        // Watermark child
        if (watermark.enabled && watermark.src) {
            const op = watermark.opacity != null ? watermark.opacity : 0.05;
            const position = watermark.position || 'center';
            const size = watermark.size || '40%';

            const wm = document.createElement('div');
            wm.style.position = 'absolute';
            wm.style.inset = '0';
            wm.style.backgroundImage = `url(${watermark.src})`;
            wm.style.backgroundSize = size;
            wm.style.backgroundRepeat = 'no-repeat';
            wm.style.backgroundPosition = position;
            wm.style.opacity = String(op);
            div.appendChild(wm);
        }

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
            this._injectCanvas(themeData);

            this.currentTheme = themeName;
            localStorage.setItem('agent-zero-theme', themeName);
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

        let css = `:root {\n`;
        css += `  /* Theme: ${themeData.name} by ${themeData.author} */\n`;
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

        // Panel translucency CSS override when opacity < 1 or blur > 0
        if (panelOpacity < 1.0 || backdropBlur > 0) {
            const panelColor = colors.panel || '#1a1a1a';
            const pct = Math.round(panelOpacity * 100);
            css += `\n`;
            css += `/* Panel translucency for atmospheric/immersive themes */\n`;
            css += `#left-panel, .right-panel, .panel {\n`;
            css += `  background-color: color-mix(in srgb, ${panelColor} ${pct}%, transparent) !important;\n`;
            css += `  backdrop-filter: blur(${backdropBlur}px) !important;\n`;
            css += `  -webkit-backdrop-filter: blur(${backdropBlur}px) !important;\n`;
            css += `}\n`;
        }

        return css;
    },

    getCurrentTheme() {
        return this.currentTheme;
    },

    async switchTheme(themeName) {
        if (this.currentTheme === themeName) return true;
        return await this.applyTheme(themeName);
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
