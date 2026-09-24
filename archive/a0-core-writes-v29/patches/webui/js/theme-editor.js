// Theme Editor — Exocortex
// Visual modal editor for theme JSON files.
// Trigger: Ctrl+Shift+T  or the ✏ button injected into the Themes sidebar section.

const ThemeEditor = {
    _modal: null,
    _draft: null,
    _original: null,
    _themeName: null,
    _activeTab: 'background',
    _livePreview: false,
    _dirty: false,

    // ─── Bootstrap ───────────────────────────────────────────────────────────

    init() {
        this._injectStyles();
        this._injectModal();
        this._bindGlobalShortcut();
        this._watchSidebar();
    },

    _bindGlobalShortcut() {
        document.addEventListener('keydown', e => {
            if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.open(ThemeManager.currentTheme);
            }
            if (e.key === 'Escape' && this._modal && !this._modal.classList.contains('te-hidden')) {
                this._cancel();
            }
        });
    },

    // Inject ✏ button next to "Themes" heading in the sidebar
    _watchSidebar() {
        const inject = () => {
            if (document.getElementById('te-sidebar-btn')) return;
            // Find the element that contains the "Themes" heading text
            const all = document.querySelectorAll('#left-panel *');
            for (const el of all) {
                if (el.childNodes.length === 1 &&
                    el.textContent.trim() === 'Themes' &&
                    el.tagName.match(/^(SPAN|DIV|H\d|P)$/i)) {
                    const btn = document.createElement('button');
                    btn.id = 'te-sidebar-btn';
                    btn.title = 'Edit theme (Ctrl+Shift+T)';
                    btn.textContent = '✏';
                    btn.style.cssText = `
                        background: none; border: none; cursor: pointer;
                        color: var(--text-muted, #888); font-size: 12px;
                        padding: 0 0 0 6px; opacity: 0.6; vertical-align: middle;
                        transition: opacity 0.2s;
                    `;
                    btn.onmouseenter = () => btn.style.opacity = '1';
                    btn.onmouseleave = () => btn.style.opacity = '0.6';
                    btn.onclick = e => { e.stopPropagation(); this.open(ThemeManager.currentTheme); };
                    el.parentNode.insertBefore(btn, el.nextSibling);
                    break;
                }
            }
        };

        const obs = new MutationObserver(inject);
        obs.observe(document.body, { childList: true, subtree: true });
        setTimeout(inject, 800);
    },

    // ─── Open / Close ─────────────────────────────────────────────────────

    async open(themeName) {
        if (!themeName) return;
        try {
            const res = await fetch(`/themes/${themeName}.json`);
            if (!res.ok) throw new Error(`Could not load ${themeName}`);
            const config = await res.json();
            this._themeName = themeName;
            this._draft = JSON.parse(JSON.stringify(config));
            this._original = JSON.parse(JSON.stringify(config));
            this._dirty = false;
            this._activeTab = 'background';
            this._render();
            this._modal.classList.remove('te-hidden');
        } catch (err) {
            console.error('[ThemeEditor] open error:', err);
            alert(`Could not open theme: ${err.message}`);
        }
    },

    _cancel() {
        if (this._dirty) {
            if (!confirm('Discard unsaved changes?')) return;
        }
        ThemeManager.applyConfig(this._original);
        this._modal.classList.add('te-hidden');
    },

    // ─── Render ───────────────────────────────────────────────────────────

    _render() {
        document.getElementById('te-name').textContent =
            (this._draft.name || this._themeName).toUpperCase();
        // Rebuild tabs
        document.querySelectorAll('.te-tab').forEach(t =>
            t.classList.toggle('te-tab-active', t.dataset.tab === this._activeTab)
        );
        const content = document.getElementById('te-content');
        content.innerHTML = '';
        content.appendChild(this._renderTab(this._activeTab));
    },

    _renderTab(tab) {
        switch (tab) {
            case 'background': return this._tabBackground();
            case 'panels':     return this._tabPanels();
            case 'overlays':   return this._tabOverlays();
            case 'widgets':    return this._tabWidgets();
            case 'colors':     return this._tabColors();
            case 'effects':    return this._tabEffects();
            default:           return document.createElement('div');
        }
    },

    // ─── Tab: Background ─────────────────────────────────────────────────

    _tabBackground() {
        const bg = this._draft.background || {};
        const f = document.createDocumentFragment();

        f.appendChild(this._fieldRow('Image source', () => {
            const wrap = document.createElement('div');
            wrap.style.cssText = 'display:flex;gap:6px;align-items:center;width:100%';

            const inp = this._textInput('te-bg-src', bg.src || '', v => {
                this._set('background.src', v);
            });
            inp.style.flex = '1';

            const browse = this._btn('Browse…', () => fileInp.click());
            const fileInp = document.createElement('input');
            fileInp.type = 'file';
            fileInp.accept = '.jpg,.jpeg,.png,.webp,.svg,.gif';
            fileInp.style.display = 'none';
            fileInp.onchange = () => {
                if (fileInp.files[0]) this._uploadFile(fileInp.files[0], src => {
                    inp.value = src;
                    this._set('background.src', src);
                });
            };

            wrap.append(inp, browse, fileInp);
            return wrap;
        }));

        f.appendChild(this._slider('te-bg-opacity', 'Opacity', 0, 1, 0.01,
            bg.opacity ?? 0.5, v => this._set('background.opacity', parseFloat(v))));

        f.appendChild(this._slider('te-bg-blur', 'Blur (px)', 0, 20, 1,
            bg.blur ?? 0, v => this._set('background.blur', parseInt(v))));

        f.appendChild(this._select('te-bg-size', 'Size',
            ['cover','contain','auto','50%','75%','100%'],
            bg.size || 'cover',
            v => this._set('background.size', v)));

        f.appendChild(this._toggle('te-bg-parallax', 'Parallax drift',
            bg.parallax ?? false,
            v => this._set('background.parallax', v)));

        // ── Visual position picker ──────────────────────────────────────
        f.appendChild(this._fieldRow('Position', () => {
            const self = this;

            // Parse position string → [x%, y%]
            const parsePos = (s) => {
                const named = {
                    'center':       [50, 50], 'top':          [50, 0],
                    'bottom':       [50,100], 'left':         [0, 50],
                    'right':        [100,50], 'top left':     [0,  0],
                    'top right':    [100, 0], 'bottom left':  [0, 100],
                    'bottom right': [100,100],
                };
                if (named[s]) return named[s];
                const p = s.split(' ');
                return [parseFloat(p[0]) || 50, parseFloat(p[1]) || 50];
            };

            let [px, py] = parsePos(bg.position || 'center');

            const wrap = document.createElement('div');

            // Preview area — 16:9 drag target
            const preview = document.createElement('div');
            preview.style.cssText = [
                'position:relative', 'width:100%', 'aspect-ratio:16/9',
                'overflow:hidden', 'border:1px solid #444', 'border-radius:4px',
                'background:#111', 'cursor:crosshair', 'margin-bottom:4px',
                'user-select:none',
            ].join(';');

            const imgLayer = document.createElement('div');
            imgLayer.style.cssText = 'position:absolute;inset:0;pointer-events:none;background-repeat:no-repeat;';
            const refreshImg = () => {
                const d = self._draft.background || {};
                imgLayer.style.backgroundImage = d.src ? `url(${d.src})` : 'none';
                imgLayer.style.backgroundSize = d.size || 'cover';
                imgLayer.style.backgroundPosition = `${px}% ${py}%`;
            };
            refreshImg();

            // SVG crosshair
            const cross = document.createElement('div');
            cross.style.cssText = 'position:absolute;width:16px;height:16px;transform:translate(-50%,-50%);pointer-events:none;';
            cross.innerHTML = '<svg viewBox="0 0 16 16" style="width:100%;height:100%">' +
                '<line x1="8" y1="0" x2="8" y2="16" stroke="#fff" stroke-width="1" stroke-dasharray="2 2" opacity="0.8"/>' +
                '<line x1="0" y1="8" x2="16" y2="8" stroke="#fff" stroke-width="1" stroke-dasharray="2 2" opacity="0.8"/>' +
                '<circle cx="8" cy="8" r="3" fill="none" stroke="#fff" stroke-width="1.5"/>' +
                '</svg>';
            const moveCross = () => {
                cross.style.left = px + '%';
                cross.style.top  = py + '%';
            };
            moveCross();

            // Readout label below the box
            const readout = document.createElement('div');
            readout.style.cssText = 'font-size:10px;color:#888;font-family:monospace;text-align:center;margin-bottom:6px;';
            const updateReadout = () => { readout.textContent = `${Math.round(px)}% ${Math.round(py)}%`; };
            updateReadout();

            const commit = () => {
                const v = `${Math.round(px)}% ${Math.round(py)}%`;
                self._set('background.position', v);
            };

            // Drag logic
            let dragging = false;
            const applyMouse = (e) => {
                const rect = preview.getBoundingClientRect();
                px = Math.max(0, Math.min(100, ((e.clientX - rect.left)  / rect.width)  * 100));
                py = Math.max(0, Math.min(100, ((e.clientY - rect.top)   / rect.height) * 100));
                moveCross();
                updateReadout();
                imgLayer.style.backgroundPosition = `${px}% ${py}%`;
            };
            preview.addEventListener('mousedown', (e) => { dragging = true; applyMouse(e); e.preventDefault(); });
            document.addEventListener('mousemove', (e) => { if (dragging && document.contains(preview)) applyMouse(e); });
            document.addEventListener('mouseup',   ()  => { if (dragging) { dragging = false; commit(); refreshImg(); } });

            // Snap buttons row
            const snaps = document.createElement('div');
            snaps.style.cssText = 'display:grid;grid-template-columns:repeat(3,1fr);gap:3px;margin-bottom:2px;';
            const snapPoints = [
                ['↖', 0,   0  ], ['↑', 50,  0  ], ['↗', 100, 0  ],
                ['←', 0,   50 ], ['·', 50,  50 ], ['→', 100, 50 ],
                ['↙', 0,   100], ['↓', 50,  100], ['↘', 100, 100],
            ];
            for (const [label, sx, sy] of snapPoints) {
                const btn = document.createElement('button');
                btn.textContent = label;
                btn.title = `${sx}% ${sy}%`;
                btn.style.cssText = 'background:#2a2a2a;border:1px solid #444;color:#ccc;border-radius:3px;padding:3px;font-size:12px;cursor:pointer;';
                btn.onmouseenter = () => btn.style.background = '#3a3a3a';
                btn.onmouseleave = () => btn.style.background = '#2a2a2a';
                btn.onclick = () => {
                    px = sx; py = sy;
                    moveCross(); updateReadout();
                    refreshImg();
                    commit();
                };
                snaps.appendChild(btn);
            }

            preview.append(imgLayer, cross);
            wrap.append(preview, readout, snaps);

            // Keep preview in sync when src/size sliders change (live preview fires _schedulePreview
            // which updates the page, but we also need to update the local imgLayer)
            const syncInterval = setInterval(() => {
                if (!document.contains(preview)) { clearInterval(syncInterval); return; }
                const d = self._draft.background || {};
                const curSrc = d.src ? `url(${d.src})` : 'none';
                if (imgLayer.style.backgroundImage !== curSrc || imgLayer.style.backgroundSize !== (d.size || 'cover')) {
                    imgLayer.style.backgroundImage = curSrc;
                    imgLayer.style.backgroundSize  = d.size || 'cover';
                }
            }, 500);

            return wrap;
        }));

        return f;
    },

    // ─── Tab: Panels ────────────────────────────────────────────────────

    _tabPanels() {
        const panel = this._draft.panel || {};
        const f = document.createDocumentFragment();

        f.appendChild(this._slider('te-panel-opacity', 'Panel opacity  (0 = see-through, 1 = solid)', 0, 1, 0.01,
            panel.opacity ?? 0.7, v => this._set('panel.opacity', parseFloat(v))));

        f.appendChild(this._slider('te-panel-blur', 'Backdrop blur (px)', 0, 12, 0.5,
            panel.backdrop_blur ?? 2, v => this._set('panel.backdrop_blur', parseFloat(v))));

        return f;
    },

    // ─── Tab: Overlays ──────────────────────────────────────────────────

    _tabOverlays() {
        const ov = this._draft.overlay || {};
        const f = document.createDocumentFragment();

        f.appendChild(this._sectionHeader('Scanlines'));
        const sl = ov.scanlines || {};
        f.appendChild(this._toggle('te-sl-enabled', 'Enabled', sl.enabled,
            v => this._set('overlay.scanlines.enabled', v)));
        f.appendChild(this._slider('te-sl-opacity', 'Opacity', 0, 0.2, 0.005,
            sl.opacity ?? 0.04, v => this._set('overlay.scanlines.opacity', parseFloat(v))));
        f.appendChild(this._slider('te-sl-spacing', 'Spacing (px)', 1, 6, 1,
            sl.spacing ?? 2, v => this._set('overlay.scanlines.spacing', parseInt(v))));

        f.appendChild(this._sectionHeader('Noise'));
        const ns = ov.noise || {};
        f.appendChild(this._toggle('te-ns-enabled', 'Enabled', ns.enabled,
            v => this._set('overlay.noise.enabled', v)));
        f.appendChild(this._slider('te-ns-opacity', 'Opacity', 0, 0.15, 0.005,
            ns.opacity ?? 0.02, v => this._set('overlay.noise.opacity', parseFloat(v))));

        f.appendChild(this._sectionHeader('Vignette'));
        const vi = ov.vignette || {};
        f.appendChild(this._toggle('te-vi-enabled', 'Enabled', vi.enabled,
            v => this._set('overlay.vignette.enabled', v)));
        f.appendChild(this._slider('te-vi-opacity', 'Opacity', 0, 0.8, 0.01,
            vi.opacity ?? 0.3, v => this._set('overlay.vignette.opacity', parseFloat(v))));

        f.appendChild(this._sectionHeader('Watermark'));
        const wm = ov.watermark || {};
        f.appendChild(this._toggle('te-wm-enabled', 'Enabled', wm.enabled,
            v => this._set('overlay.watermark.enabled', v)));

        f.appendChild(this._fieldRow('Image source', () => {
            const wrap = document.createElement('div');
            wrap.style.cssText = 'display:flex;gap:6px;align-items:center;width:100%';

            const inp = this._textInput('te-wm-src', wm.src || '', v => {
                this._set('overlay.watermark.src', v);
            });
            inp.style.flex = '1';

            const browse = this._btn('Browse…', () => fileInp.click());
            const fileInp = document.createElement('input');
            fileInp.type = 'file';
            fileInp.accept = '.jpg,.jpeg,.png,.webp,.svg,.gif';
            fileInp.style.display = 'none';
            fileInp.onchange = () => {
                if (fileInp.files[0]) this._uploadFile(fileInp.files[0], src => {
                    inp.value = src;
                    this._set('overlay.watermark.src', src);
                });
            };
            wrap.append(inp, browse, fileInp);
            return wrap;
        }));

        f.appendChild(this._slider('te-wm-opacity', 'Opacity', 0, 0.5, 0.005,
            wm.opacity ?? 0.07, v => this._set('overlay.watermark.opacity', parseFloat(v))));

        f.appendChild(this._select('te-wm-position', 'Position',
            ['center','top','bottom','top left','top right','bottom left','bottom right','50% 20%'],
            wm.position || 'center',
            v => this._set('overlay.watermark.position', v)));

        f.appendChild(this._textFieldRow('te-wm-size', 'Size', wm.size || '40%',
            v => this._set('overlay.watermark.size', v)));

        // ── Tint ────────────────────────────────────────────────────────
        f.appendChild(this._sectionHeader('Tint'));
        const ti = ov.tint || {};
        f.appendChild(this._toggle('te-ti-enabled', 'Enabled', ti.enabled,
            v => this._set('overlay.tint.enabled', v)));
        f.appendChild(this._fieldRow('Color', () => {
            const wrap = document.createElement('div');
            wrap.style.cssText = 'display:flex;gap:6px;align-items:center;';
            const swatch = document.createElement('input');
            swatch.type = 'color';
            swatch.value = (ti.color || '#888888').substring(0, 7);
            swatch.style.cssText = 'width:36px;height:28px;border:none;background:none;cursor:pointer;padding:0;';
            swatch.oninput = () => { this._set('overlay.tint.color', swatch.value); };
            const lbl = document.createElement('span');
            lbl.style.cssText = 'font-size:11px;color:#888;font-family:monospace;';
            lbl.textContent = ti.color || '#888888';
            swatch.oninput = () => { lbl.textContent = swatch.value; this._set('overlay.tint.color', swatch.value); };
            wrap.append(swatch, lbl);
            return wrap;
        }));
        f.appendChild(this._slider('te-ti-opacity', 'Strength', 0, 0.3, 0.005,
            ti.opacity ?? 0.08, v => this._set('overlay.tint.opacity', parseFloat(v))));
        f.appendChild(this._select('te-ti-mode', 'Blend mode',
            ['color', 'overlay', 'multiply', 'screen', 'soft-light', 'hue'],
            ti.mode || 'color',
            v => this._set('overlay.tint.mode', v)));

        return f;
    },

    // ─── Tab: Widgets ────────────────────────────────────────────────────

    _tabWidgets() {
        const widgets = this._draft.widgets || [];
        const f = document.createDocumentFragment();

        if (widgets.length === 0) {
            const msg = document.createElement('p');
            msg.style.cssText = 'color:var(--text-muted,#888);padding:12px 0;font-size:13px';
            msg.textContent = 'No widgets defined for this theme.';
            f.appendChild(msg);
            return f;
        }

        widgets.forEach((w, i) => {
            const card = document.createElement('div');
            card.className = 'te-widget-card';

            const hdr = document.createElement('div');
            hdr.className = 'te-widget-hdr';
            hdr.innerHTML = `<strong>${w.type || 'widget'}</strong>`;

            const posLabel = document.createElement('span');
            posLabel.textContent = w.position || '';
            posLabel.style.cssText = 'margin-left:8px;color:var(--text-muted,#888);font-size:12px';
            hdr.appendChild(posLabel);

            card.appendChild(hdr);

            // Position picker for widgets that have one
            if (w.position !== undefined) {
                card.appendChild(this._select(`te-w${i}-pos`, 'Position',
                    ['top-left','top-right','bottom-left','bottom-right','top-center','bottom-center'],
                    w.position,
                    v => { this._draft.widgets[i].position = v; this._markDirty(); }));
            }

            // Color picker for widgets that have one
            if (w.color !== undefined) {
                card.appendChild(this._colorField(`te-w${i}-color`, 'Color', w.color,
                    v => { this._draft.widgets[i].color = v; this._markDirty(); }));
            }

            // Size for applicable widgets
            if (w.size !== undefined) {
                card.appendChild(this._slider(`te-w${i}-size`, 'Size', 20, 120, 1,
                    w.size, v => { this._draft.widgets[i].size = parseInt(v); this._markDirty(); }));
            }

            f.appendChild(card);
        });

        return f;
    },

    // ─── Tab: Colors ─────────────────────────────────────────────────────

    _tabColors() {
        const colors = this._draft.colors || {};
        const f = document.createDocumentFragment();

        const grid = document.createElement('div');
        grid.className = 'te-color-grid';

        Object.entries(colors).forEach(([key, val]) => {
            const row = document.createElement('div');
            row.className = 'te-color-row';

            const label = document.createElement('label');
            label.textContent = key;
            label.style.cssText = 'flex:1;font-size:12px;color:var(--text-muted,#888)';

            // color input only accepts 6-digit hex — strip alpha for display
            const hex6 = (val || '#000000').substring(0, 7);

            const swatch = document.createElement('input');
            swatch.type = 'color';
            swatch.value = hex6;
            swatch.className = 'te-color-swatch';
            swatch.title = 'Click to pick color (use text field for alpha)';

            // Editable text field — shows full value including alpha suffix
            const hexInput = document.createElement('input');
            hexInput.type = 'text';
            hexInput.value = val || '#000000';
            hexInput.className = 'te-color-hex-input';
            hexInput.spellcheck = false;

            const commit = (newVal) => {
                this._draft.colors[key] = newVal;
                this._markDirty();
                if (this._livePreview) ThemeManager.applyConfig(this._draft);
            };

            // Swatch updates text field (6-char only; preserves existing alpha suffix)
            swatch.oninput = () => {
                const alpha = hexInput.value.length > 7 ? hexInput.value.substring(7) : '';
                hexInput.value = swatch.value + alpha;
                commit(hexInput.value);
            };

            // Text field updates swatch when valid
            hexInput.oninput = () => {
                const v = hexInput.value.trim();
                if (/^#[0-9a-fA-F]{6}/.test(v)) {
                    swatch.value = v.substring(0, 7);
                }
                commit(v);
            };

            row.append(label, swatch, hexInput);
            grid.appendChild(row);
        });

        f.appendChild(grid);
        return f;
    },

    // ─── Tab: Effects ─────────────────────────────────────────────────────

    _tabEffects() {
        const f = document.createDocumentFragment();
        const anim = this._draft.animation || {};
        const ct = this._draft.cursor_trail || {};
        const mr = this._draft.message_reveal || {};
        const ie = this._draft.idle_escalation || {};

        f.appendChild(this._sectionHeader('Animation'));
        f.appendChild(this._select('te-anim-type', 'Type',
            ['none','snow','rain','matrix','particles','embers','fireflies'],
            anim.type || 'none',
            v => this._set('animation.type', v)));
        f.appendChild(this._slider('te-anim-intensity', 'Intensity', 0, 1, 0.05,
            anim.intensity ?? 0.5, v => this._set('animation.intensity', parseFloat(v))));

        f.appendChild(this._sectionHeader('Cursor Trail'));
        f.appendChild(this._select('te-ct-type', 'Type',
            ['none','sparks','dust','snow','matrix-dots','embers'],
            ct.type || 'none',
            v => this._set('cursor_trail.type', v)));
        if (ct.color !== undefined) {
            f.appendChild(this._colorField('te-ct-color', 'Color', ct.color,
                v => this._set('cursor_trail.color', v)));
        }
        f.appendChild(this._slider('te-ct-intensity', 'Intensity', 0, 1, 0.05,
            ct.intensity ?? 0.5, v => this._set('cursor_trail.intensity', parseFloat(v))));

        f.appendChild(this._sectionHeader('Message Reveal'));
        f.appendChild(this._select('te-mr-type', 'Type',
            ['none','fade','typewriter','scan'],
            mr.type || 'none',
            v => this._set('message_reveal.type', v)));
        f.appendChild(this._slider('te-mr-speed', 'Speed', 0.1, 3, 0.1,
            mr.speed ?? 1.0, v => this._set('message_reveal.speed', parseFloat(v))));

        f.appendChild(this._sectionHeader('Idle Escalation'));
        f.appendChild(this._toggle('te-ie-enabled', 'Enabled', ie.enabled,
            v => this._set('idle_escalation.enabled', v)));
        f.appendChild(this._slider('te-ie-threshold', 'Threshold (minutes)', 1, 30, 1,
            ie.threshold_minutes ?? 5, v => this._set('idle_escalation.threshold_minutes', parseInt(v))));
        f.appendChild(this._textFieldRow('te-ie-message', 'Message', ie.message || '',
            v => this._set('idle_escalation.message', v)));

        return f;
    },

    // ─── State helpers ───────────────────────────────────────────────────

    _set(path, value) {
        const keys = path.split('.');
        let obj = this._draft;
        for (let i = 0; i < keys.length - 1; i++) {
            if (obj[keys[i]] === undefined) obj[keys[i]] = {};
            obj = obj[keys[i]];
        }
        obj[keys[keys.length - 1]] = value;
        this._markDirty();
        if (this._livePreview) ThemeManager.applyConfig(this._draft);
    },

    _markDirty() {
        this._dirty = true;
        const saveBtn = document.getElementById('te-btn-save');
        if (saveBtn) saveBtn.classList.add('te-btn-dirty');
    },

    // ─── Actions ─────────────────────────────────────────────────────────

    async _preview() {
        await ThemeManager.applyConfig(this._draft);
    },

    async _save() {
        const saveBtn = document.getElementById('te-btn-save');
        const origText = saveBtn.textContent;
        saveBtn.textContent = 'Saving…';
        saveBtn.disabled = true;

        try {
            const res = await fetch('/api_theme_save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: `${this._themeName}.json`,
                    config: this._draft
                })
            });
            const data = await res.json();
            if (data.ok) {
                this._original = JSON.parse(JSON.stringify(this._draft));
                this._dirty = false;
                saveBtn.classList.remove('te-btn-dirty');
                saveBtn.textContent = 'Saved ✓';
                await ThemeManager.applyConfig(this._draft);
                setTimeout(() => {
                    saveBtn.textContent = origText;
                    this._modal.classList.add('te-hidden');
                }, 800);
            } else {
                alert(`Save failed: ${data.error || 'unknown error'}`);
                saveBtn.textContent = origText;
            }
        } catch (err) {
            alert(`Save error: ${err.message}`);
            saveBtn.textContent = origText;
        } finally {
            saveBtn.disabled = false;
        }
    },

    async _uploadFile(file, onSuccess) {
        const form = new FormData();
        form.append('file', file);
        try {
            const res = await fetch('/api_theme_upload', { method: 'POST', body: form });
            const data = await res.json();
            if (data.ok) {
                onSuccess(data.src);
            } else {
                alert(`Upload failed: ${data.error}`);
            }
        } catch (err) {
            alert(`Upload error: ${err.message}`);
        }
    },

    // ─── UI helpers ──────────────────────────────────────────────────────

    _fieldRow(label, buildInput) {
        const row = document.createElement('div');
        row.className = 'te-field';
        const lbl = document.createElement('label');
        lbl.className = 'te-label';
        lbl.textContent = label;
        row.appendChild(lbl);
        row.appendChild(buildInput());
        return row;
    },

    _slider(id, label, min, max, step, value, onChange) {
        const row = document.createElement('div');
        row.className = 'te-field';

        const lbl = document.createElement('label');
        lbl.className = 'te-label';

        const valSpan = document.createElement('span');
        valSpan.id = `${id}-val`;
        valSpan.className = 'te-val';
        valSpan.textContent = value;

        lbl.textContent = label + ' ';
        lbl.appendChild(valSpan);

        const inp = document.createElement('input');
        inp.type = 'range';
        inp.id = id;
        inp.min = min;
        inp.max = max;
        inp.step = step;
        inp.value = value;
        inp.className = 'te-slider';
        inp.oninput = () => {
            valSpan.textContent = inp.value;
            onChange(inp.value);
        };

        row.append(lbl, inp);
        return row;
    },

    _select(id, label, options, selected, onChange) {
        const row = document.createElement('div');
        row.className = 'te-field';

        const lbl = document.createElement('label');
        lbl.className = 'te-label';
        lbl.textContent = label;

        const sel = document.createElement('select');
        sel.id = id;
        sel.className = 'te-select';
        options.forEach(opt => {
            const o = document.createElement('option');
            o.value = opt;
            o.textContent = opt;
            if (opt === selected) o.selected = true;
            sel.appendChild(o);
        });
        sel.onchange = () => onChange(sel.value);

        row.append(lbl, sel);
        return row;
    },

    _toggle(id, label, checked, onChange) {
        const row = document.createElement('div');
        row.className = 'te-field te-field-toggle';

        const lbl = document.createElement('label');
        lbl.className = 'te-label';
        lbl.textContent = label;

        const inp = document.createElement('input');
        inp.type = 'checkbox';
        inp.id = id;
        inp.checked = !!checked;
        inp.className = 'te-toggle';
        inp.onchange = () => onChange(inp.checked);

        row.append(lbl, inp);
        return row;
    },

    _textInput(id, value, onChange) {
        const inp = document.createElement('input');
        inp.type = 'text';
        inp.id = id;
        inp.value = value;
        inp.className = 'te-text-input';
        inp.oninput = () => onChange(inp.value);
        return inp;
    },

    _textFieldRow(id, label, value, onChange) {
        return this._fieldRow(label, () => this._textInput(id, value, onChange));
    },

    _colorField(id, label, value, onChange) {
        const row = document.createElement('div');
        row.className = 'te-field';

        const lbl = document.createElement('label');
        lbl.className = 'te-label';
        lbl.textContent = label;

        const inp = document.createElement('input');
        inp.type = 'color';
        inp.id = id;
        inp.value = (value || '#000000').substring(0, 7);
        inp.className = 'te-color-swatch';
        inp.oninput = () => onChange(inp.value);

        row.append(lbl, inp);
        return row;
    },

    _btn(text, onClick) {
        const b = document.createElement('button');
        b.textContent = text;
        b.className = 'te-btn-secondary';
        b.onclick = onClick;
        return b;
    },

    _sectionHeader(text) {
        const h = document.createElement('div');
        h.className = 'te-section-hdr';
        h.textContent = text;
        return h;
    },

    // ─── DOM injection ───────────────────────────────────────────────────

    _injectModal() {
        const overlay = document.createElement('div');
        overlay.id = 'te-overlay';
        overlay.className = 'te-overlay te-hidden';

        overlay.innerHTML = `
        <div class="te-modal" role="dialog" aria-modal="true" aria-label="Theme Editor">
          <div class="te-header">
            <div class="te-title">THEME EDITOR — <span id="te-name"></span></div>
            <div class="te-header-right">
              <label class="te-live-label" title="Apply changes instantly as you adjust controls">
                <input type="checkbox" id="te-live-toggle"> Live
              </label>
              <button class="te-btn-secondary" id="te-btn-preview">Preview</button>
              <button class="te-btn-primary te-btn-save" id="te-btn-save">Save</button>
              <button class="te-btn-ghost" id="te-btn-cancel">Cancel</button>
            </div>
          </div>
          <div class="te-tabs">
            <button class="te-tab te-tab-active" data-tab="background">Background</button>
            <button class="te-tab" data-tab="panels">Panels</button>
            <button class="te-tab" data-tab="overlays">Overlays</button>
            <button class="te-tab" data-tab="widgets">Widgets</button>
            <button class="te-tab" data-tab="colors">Colors</button>
            <button class="te-tab" data-tab="effects">Effects</button>
          </div>
          <div id="te-content" class="te-content"></div>
        </div>
        `;

        document.body.appendChild(overlay);
        this._modal = overlay;

        // Tab switching
        overlay.querySelectorAll('.te-tab').forEach(tab => {
            tab.onclick = () => {
                this._activeTab = tab.dataset.tab;
                this._render();
            };
        });

        // Backdrop click to cancel
        overlay.onclick = e => { if (e.target === overlay) this._cancel(); };

        // Buttons
        document.getElementById('te-btn-preview').onclick = () => this._preview();
        document.getElementById('te-btn-save').onclick = () => this._save();
        document.getElementById('te-btn-cancel').onclick = () => this._cancel();
        document.getElementById('te-live-toggle').onchange = e => {
            this._livePreview = e.target.checked;
        };
    },

    _injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
        .te-hidden { display: none !important; }

        .te-overlay {
            position: fixed; inset: 0; z-index: 9999;
            background: rgba(0,0,0,0.75);
            display: flex; align-items: center; justify-content: center;
            backdrop-filter: blur(3px);
        }

        .te-modal {
            background: #111;
            border: 1px solid #2a2a2a;
            border-radius: 6px;
            width: min(860px, 96vw);
            max-height: 88vh;
            display: flex; flex-direction: column;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #d4d0c8;
            box-shadow: 0 8px 40px rgba(0,0,0,0.7);
            overflow: hidden;
        }

        .te-header {
            display: flex; align-items: center; justify-content: space-between;
            padding: 12px 16px;
            border-bottom: 1px solid #222;
            background: #0d0d0d;
            flex-shrink: 0;
        }

        .te-title {
            font-size: 11px; letter-spacing: 2px;
            color: #888; font-weight: bold;
        }

        .te-title span { color: var(--accent, #c9922e); }

        .te-header-right {
            display: flex; align-items: center; gap: 8px;
        }

        .te-live-label {
            font-size: 11px; color: #666; display: flex;
            align-items: center; gap: 4px; cursor: pointer;
            user-select: none;
        }

        .te-tabs {
            display: flex; gap: 0;
            border-bottom: 1px solid #222;
            background: #0a0a0a;
            flex-shrink: 0;
            overflow-x: auto;
        }

        .te-tab {
            background: none; border: none; border-bottom: 2px solid transparent;
            color: #666; cursor: pointer; padding: 10px 18px;
            font-family: inherit; font-size: 12px; letter-spacing: 1px;
            white-space: nowrap;
            transition: color 0.15s, border-color 0.15s;
        }

        .te-tab:hover { color: #aaa; }

        .te-tab-active {
            color: var(--accent, #c9922e) !important;
            border-bottom-color: var(--accent, #c9922e) !important;
        }

        .te-content {
            flex: 1; overflow-y: auto; padding: 16px 20px;
            scrollbar-width: thin; scrollbar-color: #333 #111;
        }

        .te-field {
            display: flex; flex-direction: column; gap: 5px;
            margin-bottom: 14px;
        }

        .te-field-toggle {
            flex-direction: row; align-items: center; justify-content: space-between;
        }

        .te-label {
            font-size: 11px; color: #888; letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        .te-val {
            color: var(--accent, #c9922e); font-weight: bold;
        }

        .te-slider {
            width: 100%; accent-color: var(--accent, #c9922e);
            cursor: pointer;
        }

        .te-select, .te-text-input {
            background: #1a1a1a; border: 1px solid #2a2a2a;
            color: #d4d0c8; padding: 5px 8px; border-radius: 3px;
            font-family: inherit; font-size: 12px;
            width: 100%;
        }

        .te-select:focus, .te-text-input:focus {
            outline: none; border-color: var(--accent, #c9922e);
        }

        .te-toggle { width: 16px; height: 16px; cursor: pointer; accent-color: var(--accent, #c9922e); }

        .te-color-swatch {
            width: 36px; height: 24px; border: 1px solid #333;
            border-radius: 3px; cursor: pointer; padding: 1px;
            background: none;
        }

        .te-color-grid { display: flex; flex-direction: column; gap: 8px; }

        .te-color-row {
            display: flex; align-items: center; gap: 10px;
            padding: 4px 0; border-bottom: 1px solid #1a1a1a;
        }

        .te-color-hex-input {
            background: #1a1a1a; border: 1px solid #2a2a2a;
            color: #d4d0c8; padding: 3px 6px; border-radius: 3px;
            font-family: monospace; font-size: 11px;
            width: 90px;
        }

        .te-color-hex-input:focus {
            outline: none; border-color: var(--accent, #c9922e);
        }

        .te-section-hdr {
            font-size: 10px; letter-spacing: 2px; color: #555;
            text-transform: uppercase; padding: 10px 0 6px;
            border-top: 1px solid #1e1e1e; margin-top: 6px;
        }

        .te-section-hdr:first-child { border-top: none; margin-top: 0; }

        .te-widget-card {
            border: 1px solid #1e1e1e; border-radius: 4px;
            padding: 10px 12px; margin-bottom: 10px;
            background: #0d0d0d;
        }

        .te-widget-hdr { margin-bottom: 8px; font-size: 12px; }

        /* Buttons */
        .te-btn-primary, .te-btn-secondary, .te-btn-ghost {
            font-family: inherit; font-size: 11px; letter-spacing: 1px;
            padding: 6px 14px; border-radius: 3px; cursor: pointer;
            border: 1px solid transparent; transition: all 0.15s;
            white-space: nowrap;
        }

        .te-btn-primary {
            background: var(--accent, #c9922e);
            border-color: var(--accent, #c9922e);
            color: #0d0d0d; font-weight: bold;
        }

        .te-btn-primary:hover { filter: brightness(1.15); }
        .te-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
        .te-btn-dirty { animation: te-pulse 1.5s ease-in-out infinite; }

        @keyframes te-pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(201,146,46,0.4); }
            50%       { box-shadow: 0 0 0 4px rgba(201,146,46,0); }
        }

        .te-btn-secondary {
            background: #1a1a1a; border-color: #2a2a2a; color: #aaa;
        }
        .te-btn-secondary:hover { border-color: #444; color: #ccc; }

        .te-btn-ghost {
            background: none; border-color: transparent; color: #555;
        }
        .te-btn-ghost:hover { color: #888; }
        `;
        document.head.appendChild(style);
    },
};

// Auto-init when DOM is ready
document.addEventListener('DOMContentLoaded', () => ThemeEditor.init());
