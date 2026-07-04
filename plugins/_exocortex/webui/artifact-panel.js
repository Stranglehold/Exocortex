/**
 * Artifact Panel — Agent Zero WebUI Extension
 *
 * Collapsible right-side panel that renders HTML/SVG/JS artifacts emitted by
 * the agent inside a sandboxed iframe. Supports multiple artifact tabs with
 * deduplication by title and localStorage persistence.
 *
 * Artifact fence format:
 *   ```artifact            → html (default)
 *   ```artifact:html Title → full html doc
 *   ```artifact:svg Title  → SVG centred on dark bg
 *   ```artifact:js Title   → JS executed in blank doc
 *
 * Phase 1: resize sash, opacity fade, width persistence, spring transition
 * Phase 2: multi-tab bar, dedup by title, tab close, scroll-into-view
 * Phase 3: skeleton loader, zoom/pan injection, recently closed tabs, service links
 */

const ARTIFACT_LS_KEY = 'agent_artifact_panel_v1';

function loadArtifactState() {
  try {
    return JSON.parse(localStorage.getItem(ARTIFACT_LS_KEY)) || {};
  } catch {
    return {};
  }
}

function saveArtifactState(state) {
  try {
    localStorage.setItem(ARTIFACT_LS_KEY, JSON.stringify(state));
  } catch { /* storage full or blocked */ }
}

// ─── Zoom/pan script injected into every artifact ─────────────────────────
// Wraps content in #az-content-wrapper and transforms THAT, not
// documentElement — so internal layout/scroll is never disturbed.
//
// Zoom: ctrl+wheel (natural), or postMessage {t:'zi'|'zo'|'zr'}
// Pan:  middle-button drag anywhere, OR space+left-drag anywhere
//       NOT on interactive elements (a, button, input, select, textarea,
//       [contenteditable]) or scrollable regions — those get native events.
//
// If the artifact sets window._hasPanZoom = true, this whole script is
// a no-op — D3/Leaflet/etc. handle their own zoom.
const AZ_ZOOM_SCRIPT = `<script>
(function(){
  if(window._hasPanZoom)return;

  // Wrap body content in a transformable container
  var wrap=document.createElement('div');
  wrap.id='az-content-wrapper';
  wrap.style.cssText='transform-origin:0 0;width:100%;min-height:100%;';
  while(document.body.firstChild)wrap.appendChild(document.body.firstChild);
  document.body.appendChild(wrap);
  document.body.style.overflow='hidden';

  var s=1,tx=0,ty=0,drag=false,spaceDown=false,sx=0,sy=0,stx=0,sty=0;

  function ap(){
    wrap.style.transform='translate('+tx+'px,'+ty+'px) scale('+s+')';
  }

  // Respond to header button postMessages
  window.addEventListener('message',function(e){
    if(window._hasPanZoom)return;
    var d=e.data;if(!d||typeof d!=='object')return;
    if(d.t==='zi'){s=Math.min(s*1.25,10);ap();}
    if(d.t==='zo'){s=Math.max(s/1.25,0.1);ap();}
    if(d.t==='zr'){s=1;tx=0;ty=0;ap();}
  });

  // Ctrl+wheel zooms (standard browser pattern)
  document.addEventListener('wheel',function(e){
    if(window._hasPanZoom||!e.ctrlKey)return;
    e.preventDefault();
    var delta=e.deltaY<0?1.1:0.9;
    s=Math.min(Math.max(s*delta,0.1),10);ap();
  },{passive:false});

  // Determine if an element should receive native events
  function isInteractive(el){
    if(!el||el===document.body)return false;
    var tag=el.tagName;
    if(/^(A|BUTTON|INPUT|SELECT|TEXTAREA|LABEL|SUMMARY)$/.test(tag))return true;
    if(el.isContentEditable)return true;
    // Scrollable region: has overflow scroll/auto and scrollable content
    var cs=window.getComputedStyle(el);
    var ov=cs.overflow+cs.overflowY+cs.overflowX;
    if(/scroll|auto/.test(ov)&&(el.scrollHeight>el.clientHeight||el.scrollWidth>el.clientWidth))return true;
    return isInteractive(el.parentElement);
  }

  // Middle-button drag (button 1) or space+left-drag
  document.addEventListener('keydown',function(e){if(e.code==='Space'&&!isInteractive(document.activeElement)){spaceDown=true;document.body.style.cursor='grab';e.preventDefault();}});
  document.addEventListener('keyup',function(e){if(e.code==='Space'){spaceDown=false;if(!drag)document.body.style.cursor='';}});

  document.addEventListener('mousedown',function(e){
    var useMiddle=e.button===1;
    var useLeft=e.button===0&&spaceDown;
    if(!useMiddle&&!useLeft)return;
    if(!useMiddle&&isInteractive(e.target))return;
    drag=true;sx=e.clientX;sy=e.clientY;stx=tx;sty=ty;
    document.body.style.cursor='grabbing';e.preventDefault();
  });
  document.addEventListener('mousemove',function(e){
    if(!drag)return;tx=stx+(e.clientX-sx);ty=sty+(e.clientY-sy);ap();
  });
  document.addEventListener('mouseup',function(e){
    if(!drag)return;drag=false;
    document.body.style.cursor=spaceDown?'grab':'';
  });
})();
<\/script>`;

function injectZoomScript(html) {
  // Insert before </body> if present, otherwise append
  if (/<\/body>/i.test(html)) {
    return html.replace(/<\/body>/i, AZ_ZOOM_SCRIPT + '</body>');
  }
  return html + AZ_ZOOM_SCRIPT;
}

function buildArtifactSrcdoc(content, type) {
  if (!content) {
    return '<!DOCTYPE html><html><body style="margin:0;background:#1e1e1e;"></body></html>';
  }

  const darkBase = `
    <style>
      * { box-sizing: border-box; }
      body { margin: 0; padding: 12px; background: #1e1e1e; color: #e0e0e0; font-family: system-ui, sans-serif; font-size: 14px; line-height: 1.5; }
      a { color: #7aadff; }
      pre, code { background: #2d2d2d; border-radius: 4px; padding: 2px 6px; font-family: monospace; }
      pre { padding: 10px; white-space: pre-wrap; }
      ::-webkit-scrollbar { width: 6px; height: 6px; }
      ::-webkit-scrollbar-track { background: transparent; }
      ::-webkit-scrollbar-thumb { background: rgba(155,155,155,0.4); border-radius: 3px; }
    </style>`;

  let t = (type || 'html').toLowerCase();

  if (t === 'auto' || t === 'artifact') {
    const trimmed = content.trimStart();
    if (trimmed.startsWith('<svg')) t = 'svg';
    else t = 'html';
  }

  if (t === 'html') {
    if (/<!DOCTYPE|<html/i.test(content)) return injectZoomScript(content);
    return injectZoomScript(`<!DOCTYPE html><html><head><meta charset="utf-8">${darkBase}</head><body>${content}</body></html>`);
  }

  if (t === 'svg') {
    return injectZoomScript(`<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      * { box-sizing: border-box; }
      body { margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; background: #1e1e1e; }
      svg { max-width: 100%; max-height: 100vh; }
    </style></head><body>${content}</body></html>`);
  }

  if (t === 'js') {
    return injectZoomScript(`<!DOCTYPE html><html><head><meta charset="utf-8">${darkBase}</head><body><script>\n${content}\n<\/script></body></html>`);
  }

  return injectZoomScript(`<!DOCTYPE html><html><head><meta charset="utf-8">${darkBase}</head><body>${content}</body></html>`);
}

// ─── Alpine component ─────────────────────────────────────────────────────

function artifactPanelComponent() {
  const saved = loadArtifactState();

  // Migration: wrap legacy single-artifact state into tabs array
  let initialTabs = saved.tabs || [];
  if (initialTabs.length === 0 && saved.content) {
    initialTabs = [{
      id: 'legacy-0',
      title: saved.title || 'Artifact',
      type: saved.type || 'html',
      content: saved.content,
    }];
  }
  const initialActive = Math.min(
    saved.activeTab || 0,
    Math.max(0, initialTabs.length - 1)
  );

  return {
    open: saved.open || false,
    title: saved.title || '',
    content: saved.content || '',
    type: saved.type || 'html',
    hasContent: !!(saved.content) || initialTabs.length > 0,
    panelWidth: saved.panelWidth || 440,
    tabs: initialTabs,
    activeTab: initialActive,
    closedTabs: [],   // recently closed tab objects (max 8, session-only)
    panMode: false,

    // Quick-links to service UIs — opened in new browser tab
    serviceLinks: [
      { label: 'OSS', url: 'http://localhost:7731', icon: 'monitoring' },
      { label: 'SWARMFISH', url: 'http://localhost:7732', icon: 'analytics' },
    ],

    init() {
      window.artifactPanel = this;
      this.$nextTick(() => {
        if (this.open) this._applyWidth();
        if (this.hasContent) this._renderFrame();
        this._initSash();
      });
      // Allow artifacts to request loading a sibling artifact by name.
      // Artifacts rendered in srcdoc iframes cannot navigate via href (no server
      // path exists), so they postMessage instead:
      //   parent.postMessage({ type: 'load-artifact', name: 'foo.html' }, '*')
      window.addEventListener('message', async (e) => {
        if (!e.data || e.data.type !== 'load-artifact') return;
        const name = (e.data.name || '').trim();
        if (!name || !name.endsWith('.html') || name.includes('/')) return;
        try {
          const { fetchApi } = await import('/js/api.js');
          const resp = await fetchApi('/artifacts_get', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name }),
          });
          if (!resp.ok) return;
          const data = await resp.json();
          if (data.content) this.update(data.content, data.type || 'html', data.title || name);
        } catch (_) { /* ignore */ }
      });
    },

    // ─── Open / close ──────────────────────────────────────────────────

    toggle() {
      this.open = !this.open;
      if (this.open) {
        this.$nextTick(() => this._applyWidth());
      } else {
        const panel = document.getElementById('artifact-panel');
        if (panel) panel.style.removeProperty('--artifact-open-width');
      }
      this._persist();
    },

    // ─── Artifact update (called by messages.js) ───────────────────────

    /**
     * Load or refresh an artifact. Deduplicates by title — calling update()
     * with a title that already has a tab replaces that tab's content in-place
     * rather than opening a duplicate.
     */
    update(content, type = 'html', title = 'Artifact') {
      const existingIdx = this.tabs.findIndex(t => t.title === title);
      if (existingIdx >= 0) {
        this.tabs[existingIdx].content = content;
        this.tabs[existingIdx].type = type;
        this.activeTab = existingIdx;
      } else {
        const id = Date.now() + '-' + Math.random().toString(36).slice(2, 7);
        this.tabs.push({ id, title, type, content });
        this.activeTab = this.tabs.length - 1;
      }

      // Keep legacy scalar fields in sync for header binding
      this.title = title;
      this.type = type;
      this.content = content;
      this.hasContent = true;
      this.open = true;

      this._persist();
      this.$nextTick(() => {
        this._applyWidth();
        this._renderFrame();
        this._scrollTabIntoView(this.activeTab);
      });
      this._pulseTab();
    },

    // ─── Tab management ────────────────────────────────────────────────

    switchTab(index) {
      if (index === this.activeTab) return;
      this.activeTab = index;
      this.panMode = false;
      const tab = this.tabs[index];
      if (tab) {
        this.title = tab.title;
        this.type = tab.type;
        this.content = tab.content;
      }
      this._renderFrame();
      this._scrollTabIntoView(index);
      this._persist();
    },

    closeTab(index) {
      // Save to recently-closed stack before removing (session-only, max 8)
      const removed = this.tabs[index];
      if (removed) {
        this.closedTabs.unshift({ ...removed });
        if (this.closedTabs.length > 8) this.closedTabs.pop();
      }
      this.tabs.splice(index, 1);

      if (this.tabs.length === 0) {
        this.open = false;
        this.hasContent = false;
        this.title = '';
        this.content = '';
        this.type = 'html';
        this.activeTab = 0;
        const panel = document.getElementById('artifact-panel');
        if (panel) panel.style.removeProperty('--artifact-open-width');
      } else {
        // Clamp active tab index
        if (this.activeTab >= this.tabs.length) {
          this.activeTab = this.tabs.length - 1;
        }
        const tab = this.tabs[this.activeTab];
        this.title = tab.title;
        this.type = tab.type;
        this.content = tab.content;
        this._renderFrame();
      }
      this._persist();
    },

    closeActiveTab() {
      this.closeTab(this.activeTab);
    },

    reopenLastTab() {
      if (this.closedTabs.length === 0) return;
      const tab = this.closedTabs.shift();
      // Give it a fresh id to avoid key conflicts
      tab.id = Date.now() + '-r' + Math.random().toString(36).slice(2, 5);
      this.tabs.push(tab);
      this.activeTab = this.tabs.length - 1;
      this.title = tab.title;
      this.type = tab.type;
      this.content = tab.content;
      this.hasContent = true;
      this.open = true;
      this._persist();
      this.$nextTick(() => {
        this._applyWidth();
        this._renderFrame();
        this._scrollTabIntoView(this.activeTab);
      });
    },

    // ─── Zoom / pan ─────────────────────────────────────────────────────

    zoomIn()    { this._sendToFrame({ t: 'zi' }); },
    zoomOut()   { this._sendToFrame({ t: 'zo' }); },
    zoomReset() { this._sendToFrame({ t: 'zr' }); },

    togglePan() {
      this.panMode = !this.panMode;
      this._sendToFrame({ t: this.panMode ? 'pon' : 'poff' });
    },

    _sendToFrame(msg) {
      const iframe = document.getElementById('artifact-frame');
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage(msg, '*');
      }
    },

    /** Legacy: remove all tabs and collapse */
    clear() {
      this.tabs = [];
      this.content = '';
      this.title = '';
      this.type = 'html';
      this.hasContent = false;
      this.activeTab = 0;
      this._persist();
      this._renderFrame();
    },

    openInNewTab() {
      const tab = this.tabs[this.activeTab];
      const c = tab ? tab.content : this.content;
      const t = tab ? tab.type : this.type;
      if (!c) return;
      const srcdoc = buildArtifactSrcdoc(c, t);
      const blob = new Blob([srcdoc], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    },

    // ─── Width / resize ────────────────────────────────────────────────

    _applyWidth() {
      const panel = document.getElementById('artifact-panel');
      if (panel) {
        panel.style.setProperty('--artifact-open-width', this.panelWidth + 'px');
      }
    },

    _initSash() {
      const panel = document.getElementById('artifact-panel');
      if (!panel) return;

      const sash = document.createElement('div');
      sash.className = 'artifact-sash';
      panel.appendChild(sash);

      let startX = 0;
      let startWidth = 0;

      sash.addEventListener('pointerdown', (e) => {
        if (!this.open) return;
        startX = e.clientX;
        startWidth = panel.offsetWidth;
        sash.setPointerCapture(e.pointerId);
        sash.classList.add('dragging');
        panel.classList.add('resizing');
        e.preventDefault();
      });

      sash.addEventListener('pointermove', (e) => {
        if (!sash.hasPointerCapture(e.pointerId)) return;
        const dx = startX - e.clientX; // drag left = wider
        const minW = 280;
        const maxW = Math.floor(window.innerWidth * 0.6);
        const newWidth = Math.min(Math.max(startWidth + dx, minW), maxW);
        this.panelWidth = newWidth;
        panel.style.setProperty('--artifact-open-width', newWidth + 'px');
      });

      sash.addEventListener('pointerup', (e) => {
        if (!sash.hasPointerCapture(e.pointerId)) return;
        sash.releasePointerCapture(e.pointerId);
        sash.classList.remove('dragging');
        panel.classList.remove('resizing');
        this._persist();
      });

      sash.addEventListener('pointercancel', () => {
        sash.classList.remove('dragging');
        panel.classList.remove('resizing');
      });
    },

    // ─── Frame rendering ────────────────────────────────────────────────

    _renderFrame() {
      const iframe = document.getElementById('artifact-frame');
      if (!iframe) return;

      const tab = this.tabs[this.activeTab];
      const c = tab ? tab.content : this.content;
      const t = tab ? tab.type : this.type;

      // Show skeleton behind, hide iframe
      const skeleton = document.getElementById('artifact-skeleton');
      if (skeleton) skeleton.classList.add('visible');
      iframe.style.opacity = '0';

      const onLoad = () => {
        iframe.style.opacity = '1';
        if (skeleton) skeleton.classList.remove('visible');
        iframe.removeEventListener('load', onLoad);
      };
      iframe.addEventListener('load', onLoad);

      iframe.srcdoc = buildArtifactSrcdoc(c, t);
    },

    _scrollTabIntoView(index) {
      this.$nextTick(() => {
        const bar = document.querySelector('.artifact-tabs-bar');
        if (!bar) return;
        const tabEl = bar.children[index];
        if (tabEl) tabEl.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
      });
    },

    // ─── Persistence ────────────────────────────────────────────────────

    _persist() {
      saveArtifactState({
        open: this.open,
        title: this.title,
        content: this.content,
        type: this.type,
        panelWidth: this.panelWidth,
        tabs: this.tabs,
        activeTab: this.activeTab,
      });
    },

    _pulseTab() {
      const dot = document.querySelector('.artifact-dot');
      if (!dot) return;
      dot.classList.remove('pulse');
      void dot.offsetWidth;
      dot.classList.add('pulse');
      setTimeout(() => dot.classList.remove('pulse'), 800);
    },
  };
}

// ─── Export factory for direct use ────────────────────────────────────────
// Named Alpine.data registration only works before Alpine.start().
// When loaded via initFw_end (after start), we expose the factory on window
// so the init module can wire it directly: x-data="artifactPanelFactory()"
window.artifactPanelFactory = artifactPanelComponent;

export { artifactPanelComponent };
