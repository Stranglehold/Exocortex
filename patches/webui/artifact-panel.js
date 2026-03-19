/**
 * Artifact Panel — Agent Zero WebUI Extension
 *
 * Adds a collapsible right-side panel that renders interactive HTML/SVG/JS
 * artifacts emitted by the agent inside a sandboxed iframe. State persists
 * to localStorage across page loads and conversations.
 *
 * Artifact fence format in agent output:
 *   ```artifact
 *   <html content>
 *   ```
 *
 *   ```artifact:svg Title goes here
 *   <svg .../>
 *   ```
 *
 *   ```artifact:js
 *   document.body.innerHTML = '<h1>Hello</h1>';
 *   ```
 *
 * Supported types: html (default), svg, js
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

  // auto-detect from content if type is generic
  if (t === 'auto' || t === 'artifact') {
    const trimmed = content.trimStart();
    if (trimmed.startsWith('<svg')) t = 'svg';
    else t = 'html';
  }

  if (t === 'html') {
    // If it's already a full document, use as-is
    if (/<!DOCTYPE|<html/i.test(content)) return content;
    return `<!DOCTYPE html><html><head><meta charset="utf-8">${darkBase}</head><body>${content}</body></html>`;
  }

  if (t === 'svg') {
    return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      * { box-sizing: border-box; }
      body { margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; background: #1e1e1e; }
      svg { max-width: 100%; max-height: 100vh; }
    </style></head><body>${content}</body></html>`;
  }

  if (t === 'js') {
    return `<!DOCTYPE html><html><head><meta charset="utf-8">${darkBase}</head><body><script>\n${content}\n<\/script></body></html>`;
  }

  // fallback: treat as html fragment
  return `<!DOCTYPE html><html><head><meta charset="utf-8">${darkBase}</head><body>${content}</body></html>`;
}

// ─── Alpine component ─────────────────────────────────────────────────────

function artifactPanelComponent() {
  const saved = loadArtifactState();

  return {
    open: saved.open || false,
    title: saved.title || '',
    content: saved.content || '',
    type: saved.type || 'html',
    hasContent: !!(saved.content),

    init() {
      // Expose globally so messages.js can call update()
      window.artifactPanel = this;

      // Render saved content on init
      this.$nextTick(() => {
        if (this.content) this._renderFrame();
      });
    },

    toggle() {
      this.open = !this.open;
      this._persist();
    },

    /**
     * Called by the message pipeline when an artifact fence is detected.
     * @param {string} content  - raw artifact content
     * @param {string} type     - 'html' | 'svg' | 'js'
     * @param {string} title    - display label
     */
    update(content, type = 'html', title = 'Artifact') {
      this.content = content;
      this.type = type;
      this.title = title;
      this.hasContent = true;
      this.open = true;
      this._persist();
      this._renderFrame();
      this._pulseTab();
    },

    clear() {
      this.content = '';
      this.title = '';
      this.type = 'html';
      this.hasContent = false;
      this._persist();
      this._renderFrame();
    },

    openInNewTab() {
      if (!this.content) return;
      const srcdoc = buildArtifactSrcdoc(this.content, this.type);
      const blob = new Blob([srcdoc], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
      // revoke after a moment
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    },

    _renderFrame() {
      const iframe = document.getElementById('artifact-frame');
      if (!iframe) return;
      iframe.srcdoc = buildArtifactSrcdoc(this.content, this.type);
    },

    _persist() {
      saveArtifactState({
        open: this.open,
        title: this.title,
        content: this.content,
        type: this.type,
      });
    },

    _pulseTab() {
      const dot = document.querySelector('.artifact-dot');
      if (!dot) return;
      dot.classList.remove('pulse');
      // force reflow to restart animation
      void dot.offsetWidth;
      dot.classList.add('pulse');
      setTimeout(() => dot.classList.remove('pulse'), 800);
    },
  };
}

// ─── Register with Alpine ─────────────────────────────────────────────────

document.addEventListener('alpine:init', () => {
  Alpine.data('artifactPanel', artifactPanelComponent);
});
