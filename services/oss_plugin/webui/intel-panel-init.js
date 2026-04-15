/**
 * Intel Panel — initFw_start hook
 * ================================
 * Injects the persistent OSS + SWARMFISH intelligence control panel
 * into Agent Zero's web UI. Panel lives in the flex row alongside the
 * chat area and the artifact panel — always accessible, no agent prompts needed.
 *
 * Architecture: Alpine.js in the PAGE context (not an iframe).
 * All mouse/scroll/keyboard interactions work natively.
 * Calls OSS and SWARMFISH services directly via fetch().
 */

const OSS_URL = "http://localhost:7731";
const SWF_URL = "http://localhost:7732";
const TOKEN   = "dev_analyst_token";
const PANEL_WIDTH = "520px";

// ── API helpers ──────────────────────────────────────────────────────────────

async function ossApi(endpoint, method = "GET", body = null) {
    const opts = {
        method,
        headers: { "X-Analyst-Token": TOKEN, "Content-Type": "application/json" },
    };
    if (body) opts.body = JSON.stringify(body);
    const r = await fetch(OSS_URL + endpoint, opts);
    if (!r.ok) throw new Error(`OSS ${endpoint}: ${r.status} ${r.statusText}`);
    return r.json();
}

async function swfApi(endpoint, method = "GET", body = null) {
    const opts = {
        method,
        headers: { "X-Analyst-Token": TOKEN, "Content-Type": "application/json" },
    };
    if (body) opts.body = JSON.stringify(body);
    const r = await fetch(SWF_URL + endpoint, opts);
    if (!r.ok) throw new Error(`SWF ${endpoint}: ${r.status} ${r.statusText}`);
    return r.json();
}

// ── Alpine component factory ─────────────────────────────────────────────────

function intelPanelFactory() {
    return {
        open: false,
        tab: "claims",
        loading: false,
        error: null,

        // Tab data
        claims: [],
        claimsTotal: 0,
        claimsTopic: "",
        sources: [],
        topics: [],
        hypotheses: [],
        swfProfiles: [],
        swfCalibration: [],
        newCount: 0,
        ossHealth: null,

        // ── Open / toggle ──────────────────────────────────────────────────
        toggle() {
            this.open = !this.open;
            if (this.open && this.claims.length === 0) this.loadTab("claims");
        },

        // ── Load a tab ─────────────────────────────────────────────────────
        async loadTab(name) {
            this.tab = name;
            this.loading = true;
            this.error = null;
            try {
                await this._load(name);
            } catch (e) {
                this.error = e.message;
                console.error("[INTEL-PANEL]", e);
            }
            this.loading = false;
        },

        async refresh() { await this.loadTab(this.tab); },

        async _load(name) {
            if (name === "claims") {
                const d = await ossApi("/api/staging", "POST",
                    { limit: 50, ...(this.claimsTopic ? { topic: this.claimsTopic } : {}) });
                this.claims      = d.claims || [];
                this.claimsTotal = d.total  || 0;
                this.newCount    = this.claimsTotal;
            } else if (name === "hypotheses") {
                const d = await ossApi("/api/hypotheses");
                this.hypotheses = d.hypotheses || [];
            } else if (name === "sources") {
                const d = await ossApi("/api/sources_list");
                this.sources = d.result || d.sources || [];
            } else if (name === "topics") {
                const d = await ossApi("/api/topics");
                this.topics = d.topics || [];
            } else if (name === "swarmfish") {
                const [prof, stat] = await Promise.all([
                    swfApi("/acp/profiles"),
                    swfApi("/acp/status"),
                ]);
                this.swfProfiles     = Array.isArray(prof) ? prof : [];
                this.swfCalibration  = stat.calibration || [];
            }
        },

        // ── Claim actions ──────────────────────────────────────────────────
        async promote(id) {
            try {
                await ossApi("/admin/quick_promote", "POST", { claim_id: id });
                this.claims = this.claims.filter(c => c.id !== id);
                this.claimsTotal = Math.max(0, this.claimsTotal - 1);
            } catch (e) { alert("Promote failed: " + e.message); }
        },

        async dismiss(id) {
            try {
                await ossApi("/admin/mark_irrelevant", "POST", { claim_id: id, reason: "dismissed from panel" });
                this.claims = this.claims.filter(c => c.id !== id);
                this.claimsTotal = Math.max(0, this.claimsTotal - 1);
            } catch (e) { alert("Dismiss failed: " + e.message); }
        },

        // ── Ingest control ─────────────────────────────────────────────────
        async pauseIngest() {
            try {
                await ossApi("/admin/ingest/pause", "POST");
                this.ossHealth = { ...this.ossHealth, ingest_paused: true };
            } catch (e) { alert("Pause failed: " + e.message); }
        },
        async resumeIngest() {
            try {
                await ossApi("/admin/ingest/resume", "POST");
                this.ossHealth = { ...this.ossHealth, ingest_paused: false };
            } catch (e) { alert("Resume failed: " + e.message); }
        },

        // ── Helpers ────────────────────────────────────────────────────────
        truncate(s, n = 120) {
            if (!s) return "";
            return s.length > n ? s.slice(0, n) + "…" : s;
        },
        tagList(tags) {
            if (!tags) return [];
            if (Array.isArray(tags)) return tags;
            try { return JSON.parse(tags); } catch { return [String(tags)]; }
        },
        confColor(v) {
            v = parseFloat(v) || 0;
            if (v >= 0.75) return "#4caf93";
            if (v >= 0.50) return "#f0b429";
            return "#e05c5c";
        },
        statusBadge(s) {
            const map = { ACTIVE: "#4caf93", PENDING: "#f0b429", FALSIFIED: "#e05c5c", PROMOTED: "#6fa3ef" };
            return map[s] || "#888";
        },
        acuracyColor(v) {
            v = parseFloat(v) || 0;
            if (v >= 0.75) return "#4caf93";
            if (v >= 0.50) return "#f0b429";
            return "#e05c5c";
        },
    };
}

// ── CSS ──────────────────────────────────────────────────────────────────────

const CSS = `
#intel-panel {
  display: flex;
  flex-direction: row;
  flex-shrink: 0;
  width: 28px;
  height: 100%;
  background: var(--color-panel);
  border-left: 1px solid var(--color-border);
  transition: width 0.3s cubic-bezier(0.22,1,0.36,1);
  overflow: hidden;
  position: relative;
  z-index: 100;
}
#intel-panel.open { width: var(--intel-open-width, ${PANEL_WIDTH}); }

.intel-sash {
  position: absolute; left: 0; top: 0; width: 4px; height: 100%;
  cursor: col-resize; touch-action: none; z-index: 20;
  background: transparent; transition: background 0.15s;
}
.intel-sash:hover, .intel-sash.dragging { background: var(--color-primary, rgba(120,130,255,0.45)); }
#intel-panel:not(.open) .intel-sash { pointer-events: none; opacity: 0; }

.intel-strip {
  display: flex; flex-direction: column; align-items: center;
  justify-content: flex-start; width: 28px; flex-shrink: 0; height: 100%;
  cursor: pointer; user-select: none; gap: 0;
  border-right: 1px solid var(--color-border);
  transition: background 0.15s;
  padding-top: 8px;
}
.intel-strip:hover { background: var(--color-background-hover); }
.intel-strip-icon {
  color: var(--color-primary);
  font-family: 'Material Symbols Outlined';
  font-weight: normal; font-style: normal; font-size: 18px;
  line-height: 1; letter-spacing: normal; text-transform: none;
  white-space: nowrap; direction: ltr;
  -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
  margin-bottom: 8px;
}
.intel-strip-label {
  writing-mode: vertical-rl; text-orientation: mixed;
  transform: rotate(180deg); font-size: 10px; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--color-text-muted); white-space: nowrap; margin-bottom: 8px;
}
.intel-strip-badge {
  background: var(--color-primary); color: #fff;
  border-radius: 8px; font-size: 9px; font-weight: 700;
  padding: 1px 4px; min-width: 16px; text-align: center;
  display: none;
}
.intel-strip-badge.visible { display: block; }

.intel-body {
  display: flex; flex-direction: column; flex: 1; overflow: hidden;
  padding-top: 0;
}
.intel-header {
  display: flex; align-items: center; padding: 8px 10px 6px;
  border-bottom: 1px solid var(--color-border); flex-shrink: 0;
  gap: 6px;
}
.intel-header-title {
  font-size: 12px; font-weight: 700; letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--color-text); flex: 1;
}
.intel-hbtn {
  background: none; border: none; cursor: pointer; padding: 2px 5px;
  border-radius: 4px; color: var(--color-text-muted); font-size: 11px;
  font-family: 'Material Symbols Outlined'; font-weight: normal;
  font-style: normal; line-height: 1; letter-spacing: normal;
  -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
  transition: color 0.15s, background 0.15s;
}
.intel-hbtn:hover { color: var(--color-text); background: var(--color-background-hover); }

.intel-tabs {
  display: flex; flex-shrink: 0; border-bottom: 1px solid var(--color-border);
  overflow-x: auto; gap: 0;
}
.intel-tab-btn {
  background: none; border: none; border-bottom: 2px solid transparent;
  cursor: pointer; padding: 6px 10px; font-size: 11px; font-weight: 600;
  color: var(--color-text-muted); white-space: nowrap;
  transition: color 0.15s, border-color 0.15s;
}
.intel-tab-btn:hover { color: var(--color-text); }
.intel-tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.intel-content {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  padding: 8px;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}
.intel-content::-webkit-scrollbar { width: 5px; }
.intel-content::-webkit-scrollbar-track { background: transparent; }
.intel-content::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 3px; }

.intel-loading {
  display: flex; align-items: center; justify-content: center;
  height: 80px; color: var(--color-text-muted); font-size: 12px; gap: 8px;
}
.intel-error {
  margin: 8px; padding: 8px 10px; border-radius: 4px;
  background: rgba(224,92,92,0.12); border: 1px solid rgba(224,92,92,0.3);
  color: #e05c5c; font-size: 11px; word-break: break-all;
}
.intel-empty {
  color: var(--color-text-muted); font-size: 12px;
  text-align: center; padding: 24px 8px;
}

/* Claim cards */
.iclaim {
  background: var(--color-background, rgba(255,255,255,0.03));
  border: 1px solid var(--color-border); border-radius: 5px;
  padding: 8px 10px; margin-bottom: 6px; font-size: 11px;
  transition: border-color 0.15s;
}
.iclaim:hover { border-color: var(--color-primary); }
.iclaim-meta {
  display: flex; align-items: center; gap: 6px; margin-bottom: 4px; flex-wrap: wrap;
}
.iclaim-source { font-weight: 700; color: var(--color-text); font-size: 11px; }
.iclaim-tag {
  background: rgba(111,163,239,0.18); color: #6fa3ef;
  border-radius: 3px; padding: 1px 5px; font-size: 10px; font-weight: 600;
}
.iclaim-technique {
  background: rgba(240,180,41,0.15); color: #f0b429;
  border-radius: 3px; padding: 1px 5px; font-size: 10px;
}
.iclaim-conf { font-size: 10px; font-weight: 700; margin-left: auto; }
.iclaim-text { color: var(--color-text); line-height: 1.4; margin-bottom: 6px; }
.iclaim-actions { display: flex; gap: 5px; }
.iclaim-btn {
  background: none; border: 1px solid var(--color-border);
  border-radius: 3px; cursor: pointer; padding: 2px 8px;
  font-size: 10px; font-weight: 600; color: var(--color-text-muted);
  transition: all 0.15s;
}
.iclaim-btn:hover { border-color: var(--color-primary); color: var(--color-text); }
.iclaim-btn.promote:hover { border-color: #4caf93; color: #4caf93; }
.iclaim-btn.dismiss:hover { border-color: #e05c5c; color: #e05c5c; }
.iclaim-url { font-size: 9px; color: var(--color-text-muted); margin-top: 3px; }
.iclaim-url a { color: inherit; text-decoration: none; }
.iclaim-url a:hover { text-decoration: underline; }

/* Filter bar */
.intel-filter {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 8px 0; font-size: 11px; flex-shrink: 0;
}
.intel-filter select {
  background: var(--color-input, #1e1e1e); border: 1px solid var(--color-border);
  border-radius: 3px; color: var(--color-text); font-size: 11px;
  padding: 2px 6px; cursor: pointer; flex: 1;
}
.intel-total { color: var(--color-text-muted); font-size: 10px; }

/* Hypothesis cards */
.ihyp {
  background: var(--color-background, rgba(255,255,255,0.03));
  border: 1px solid var(--color-border); border-radius: 5px;
  padding: 8px 10px; margin-bottom: 6px; font-size: 11px;
}
.ihyp-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.ihyp-status {
  border-radius: 3px; padding: 1px 6px; font-size: 10px; font-weight: 700;
  color: #fff;
}
.ihyp-conf { font-weight: 700; font-size: 11px; margin-left: auto; }
.ihyp-obs { color: var(--color-text-muted); font-size: 10px; margin-bottom: 3px; }
.ihyp-text { color: var(--color-text); line-height: 1.4; }
.ihyp-preds { color: var(--color-text-muted); font-size: 10px; margin-top: 4px; }

/* Source table */
.isrc-table { width: 100%; border-collapse: collapse; font-size: 10.5px; }
.isrc-table th {
  text-align: left; padding: 4px 6px; font-size: 10px; font-weight: 700;
  color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.05em;
  border-bottom: 1px solid var(--color-border); white-space: nowrap;
}
.isrc-table td {
  padding: 4px 6px; border-bottom: 1px solid rgba(255,255,255,0.04);
  color: var(--color-text); vertical-align: middle;
}
.isrc-table tr:hover td { background: var(--color-background-hover); }
.isrc-cluster {
  border-radius: 3px; padding: 1px 4px; font-size: 9px; font-weight: 600;
  background: rgba(111,163,239,0.15); color: #6fa3ef;
}

/* Topics grid */
.itopic-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.itopic-card {
  background: var(--color-background, rgba(255,255,255,0.03));
  border: 1px solid var(--color-border); border-radius: 5px; padding: 8px;
}
.itopic-tag { font-weight: 700; font-size: 11px; color: var(--color-primary); margin-bottom: 2px; }
.itopic-name { font-size: 10px; color: var(--color-text); margin-bottom: 3px; }
.itopic-count { font-size: 10px; color: var(--color-text-muted); }
.itopic-active {
  display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: #4caf93; margin-right: 4px;
}

/* SWARMFISH */
.iswf-profile {
  background: var(--color-background, rgba(255,255,255,0.03));
  border: 1px solid var(--color-border); border-radius: 5px;
  padding: 8px 10px; margin-bottom: 6px; font-size: 11px;
}
.iswf-pname { font-weight: 700; color: var(--color-text); margin-bottom: 4px; }
.iswf-domains { display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 4px; }
.iswf-domain {
  background: rgba(76,175,147,0.15); color: #4caf93;
  border-radius: 3px; padding: 1px 5px; font-size: 9px; font-weight: 600;
}
.iswf-cal-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 10px; padding: 2px 0; border-top: 1px solid rgba(255,255,255,0.04);
  color: var(--color-text-muted);
}
.iswf-cal-acc { font-weight: 700; }
.iswf-section-title {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--color-text-muted);
  padding: 6px 0 4px; border-bottom: 1px solid var(--color-border);
  margin-bottom: 6px;
}

/* Ingest control bar */
.intel-ingest-bar {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 8px; border-top: 1px solid var(--color-border);
  flex-shrink: 0; font-size: 10px; color: var(--color-text-muted);
}
.intel-ingest-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #4caf93; flex-shrink: 0;
}
.intel-ingest-dot.paused { background: #e05c5c; }
.intel-ingest-label { flex: 1; }
.intel-ingest-btn {
  background: none; border: 1px solid var(--color-border);
  border-radius: 3px; cursor: pointer; padding: 1px 7px;
  font-size: 10px; color: var(--color-text-muted); transition: all 0.15s;
}
.intel-ingest-btn:hover { border-color: var(--color-primary); color: var(--color-text); }
`;

// ── Panel HTML ───────────────────────────────────────────────────────────────

const PANEL_HTML = `
<div class="intel-sash" id="intel-sash"></div>

<!-- Strip (always visible, click to toggle) -->
<div class="intel-strip" @click="toggle()" title="Toggle Intelligence Panel">
  <span class="intel-strip-icon">radar</span>
  <span class="intel-strip-label">Intel</span>
  <span class="intel-strip-badge" :class="newCount > 0 ? 'visible' : ''" x-text="newCount > 99 ? '99+' : newCount"></span>
</div>

<!-- Panel body (shown when open) -->
<div class="intel-body" x-show="open" x-cloak>

  <!-- Header -->
  <div class="intel-header">
    <span class="intel-header-title">Intelligence</span>
    <button class="intel-hbtn" @click="refresh()" title="Refresh" :disabled="loading">refresh</button>
    <button class="intel-hbtn" @click="open = false" title="Close">close</button>
  </div>

  <!-- Tab bar -->
  <div class="intel-tabs">
    <button class="intel-tab-btn" :class="tab==='claims' ? 'active' : ''" @click="loadTab('claims')">
      Claims <template x-if="claimsTotal > 0"><span x-text="'('+claimsTotal+')'"></span></template>
    </button>
    <button class="intel-tab-btn" :class="tab==='hypotheses' ? 'active' : ''" @click="loadTab('hypotheses')">Hypotheses</button>
    <button class="intel-tab-btn" :class="tab==='sources' ? 'active' : ''" @click="loadTab('sources')">Sources</button>
    <button class="intel-tab-btn" :class="tab==='topics' ? 'active' : ''" @click="loadTab('topics')">Topics</button>
    <button class="intel-tab-btn" :class="tab==='swarmfish' ? 'active' : ''" @click="loadTab('swarmfish')">SWARMFISH</button>
  </div>

  <!-- Claims filter -->
  <div class="intel-filter" x-show="tab==='claims'">
    <select x-model="claimsTopic" @change="loadTab('claims')">
      <option value="">All topics</option>
      <template x-for="t in topics" :key="t.tag">
        <option :value="t.tag" x-text="t.display_name || t.tag"></option>
      </template>
    </select>
    <span class="intel-total" x-show="claimsTotal > 0" x-text="claimsTotal + ' staged'"></span>
  </div>

  <!-- Loading / error -->
  <div class="intel-loading" x-show="loading">
    <span class="intel-strip-icon" style="animation: spin 1s linear infinite; display:inline-block">progress_activity</span>
    Loading...
  </div>
  <div class="intel-error" x-show="!loading && error" x-text="error"></div>

  <!-- Content area -->
  <div class="intel-content" x-show="!loading">

    <!-- Claims tab -->
    <div x-show="tab==='claims'">
      <div class="intel-empty" x-show="claims.length === 0 && !loading">No staged claims</div>
      <template x-for="c in claims" :key="c.id">
        <div class="iclaim">
          <div class="iclaim-meta">
            <span class="iclaim-source" x-text="c.source_name || 'Unknown'"></span>
            <template x-for="tag in tagList(c.topic_tags)" :key="tag">
              <span class="iclaim-tag" x-text="tag"></span>
            </template>
            <span class="iclaim-technique" x-text="c.technique_class || 'unknown'" x-show="c.technique_class"></span>
            <span class="iclaim-conf" :style="'color:' + confColor(c.staging_confidence || c.confidence_score)"
                  x-text="((c.staging_confidence || c.confidence_score || 0)*100).toFixed(0) + '%'"></span>
          </div>
          <div class="iclaim-text" x-text="truncate(c.claim_text, 180)"></div>
          <div class="iclaim-actions">
            <button class="iclaim-btn promote" @click.stop="promote(c.id)">Promote</button>
            <button class="iclaim-btn dismiss" @click.stop="dismiss(c.id)">Dismiss</button>
          </div>
          <div class="iclaim-url" x-show="c.article_url">
            <a :href="c.article_url" target="_blank" x-text="truncate(c.article_url, 60)"></a>
          </div>
        </div>
      </template>
    </div>

    <!-- Hypotheses tab -->
    <div x-show="tab==='hypotheses'">
      <div class="intel-empty" x-show="hypotheses.length === 0 && !loading">No hypotheses</div>
      <template x-for="h in hypotheses" :key="h.id">
        <div class="ihyp">
          <div class="ihyp-header">
            <span class="ihyp-status" :style="'background:' + statusBadge(h.status)" x-text="h.status"></span>
            <span class="ihyp-obs" x-text="h.observation_label || ('Obs #' + h.observation_id)"></span>
            <span class="ihyp-conf" :style="'color:' + confColor(h.current_confidence)"
                  x-text="((h.current_confidence || 0)*100).toFixed(0) + '% conf'"></span>
          </div>
          <div class="ihyp-text" x-text="truncate(h.candidate_explanation || h.explanation, 200)"></div>
          <div class="ihyp-preds" x-show="h.predictions_generated > 0">
            Predictions: <span x-text="h.predictions_confirmed"></span>✓
            <span x-text="h.predictions_falsified"></span>✗
            / <span x-text="h.predictions_generated"></span> total
          </div>
        </div>
      </template>
    </div>

    <!-- Sources tab -->
    <div x-show="tab==='sources'">
      <div class="intel-empty" x-show="sources.length === 0 && !loading">No sources</div>
      <table class="isrc-table" x-show="sources.length > 0">
        <thead>
          <tr>
            <th>Source</th>
            <th>Cluster</th>
            <th>Cred</th>
            <th>Claims</th>
          </tr>
        </thead>
        <tbody>
          <template x-for="s in sources" :key="s.source_id">
            <tr>
              <td x-text="s.source_name || s.name"></td>
              <td><span class="isrc-cluster" x-text="s.cluster || '—'"></span></td>
              <td :style="'color:' + confColor(s._c || s.overall || s.confidence_score)"
                  x-text="((s._c || s.overall || s.confidence_score || 0)*100).toFixed(0) + '%'"></td>
              <td x-text="s.total_claims || 0"></td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Topics tab -->
    <div x-show="tab==='topics'">
      <div class="intel-empty" x-show="topics.length === 0 && !loading">No topics</div>
      <div class="itopic-grid">
        <template x-for="t in topics" :key="t.tag">
          <div class="itopic-card">
            <div class="itopic-tag">
              <span class="itopic-active" x-show="t.active"></span>
              <span x-text="t.tag"></span>
            </div>
            <div class="itopic-name" x-text="t.display_name"></div>
            <div class="itopic-count" x-text="(t.claim_count || 0) + ' claims'"></div>
          </div>
        </template>
      </div>
    </div>

    <!-- SWARMFISH tab -->
    <div x-show="tab==='swarmfish'">
      <div class="intel-empty" x-show="swfProfiles.length === 0 && !loading">SWARMFISH unavailable</div>
      <div x-show="swfProfiles.length > 0">
        <div class="iswf-section-title">Analyst Profiles</div>
        <template x-for="p in swfProfiles" :key="p.name">
          <div class="iswf-profile">
            <div class="iswf-pname" x-text="p.name"></div>
            <div class="iswf-domains">
              <template x-for="d in (p.domain_affinities || [])" :key="d">
                <span class="iswf-domain" x-text="d"></span>
              </template>
            </div>
            <div class="iswf-cal-row" x-show="(p.consensus_weight || {}).default !== undefined">
              <span>Consensus weight</span>
              <span x-text="((p.consensus_weight || {}).default || 1).toFixed(2)"></span>
            </div>
            <!-- Calibration rows for this profile -->
            <template x-for="cal in swfCalibration.filter(c => c.profile_name === p.name)" :key="cal.domain">
              <div class="iswf-cal-row">
                <span x-text="cal.domain"></span>
                <span>
                  <span class="iswf-cal-acc" :style="'color:' + acuracyColor(cal.avg_accuracy)"
                        x-text="(parseFloat(cal.avg_accuracy)*100).toFixed(0) + '%'"></span>
                  acc · <span x-text="cal.n_predictions"></span> pred
                </span>
              </div>
            </template>
          </div>
        </template>
      </div>
    </div>

  </div><!-- /intel-content -->

  <!-- Ingest status bar -->
  <div class="intel-ingest-bar" x-show="tab === 'claims' || tab === 'topics'">
    <span class="intel-ingest-dot" :class="ossHealth && ossHealth.ingest_paused ? 'paused' : ''"></span>
    <span class="intel-ingest-label" x-text="ossHealth && ossHealth.ingest_paused ? 'Ingest: PAUSED' : 'Ingest: ACTIVE'"></span>
    <button class="intel-ingest-btn" x-show="!ossHealth || !ossHealth.ingest_paused" @click="pauseIngest()">Pause</button>
    <button class="intel-ingest-btn" x-show="ossHealth && ossHealth.ingest_paused" @click="resumeIngest()">Resume</button>
  </div>

</div><!-- /intel-body -->

<style>
@keyframes spin { to { transform: rotate(360deg); } }
</style>
`;

// ── Resize handle ────────────────────────────────────────────────────────────

function attachResizeHandle(panelEl) {
    const sash = panelEl.querySelector("#intel-sash");
    if (!sash) return;
    let startX = 0, startW = 0;
    sash.addEventListener("pointerdown", e => {
        startX = e.clientX;
        startW = panelEl.offsetWidth;
        panelEl.classList.add("resizing");
        sash.classList.add("dragging");
        document.addEventListener("pointermove", onMove);
        document.addEventListener("pointerup", onUp, { once: true });
    });
    function onMove(e) {
        const w = Math.max(280, Math.min(900, startW - (e.clientX - startX)));
        panelEl.style.setProperty("--intel-open-width", w + "px");
    }
    function onUp() {
        panelEl.classList.remove("resizing");
        sash.classList.remove("dragging");
        document.removeEventListener("pointermove", onMove);
    }
}

// ── Main init ────────────────────────────────────────────────────────────────

export default async function initIntelPanel() {
    // Inject CSS
    const style = document.createElement("style");
    style.id = "intel-panel-css";
    style.textContent = CSS;
    document.head.appendChild(style);

    // Register Alpine component before Alpine initializes
    document.addEventListener("alpine:init", () => {
        Alpine.data("intelPanel", intelPanelFactory);
    });

    // Inject panel DOM into .container flex row
    const container = document.querySelector(".container");
    if (!container || document.getElementById("intel-panel")) return;

    const panelEl = document.createElement("div");
    panelEl.id = "intel-panel";
    panelEl.setAttribute("x-data", "intelPanel");
    panelEl.setAttribute(":class", "{ open }");
    panelEl.innerHTML = PANEL_HTML;

    // Insert before artifact-panel if it exists; otherwise append
    const artifactPanel = document.getElementById("artifact-panel");
    if (artifactPanel) {
        container.insertBefore(panelEl, artifactPanel);
    } else {
        container.appendChild(panelEl);
        // Also watch for artifact panel to be added later
        const obs = new MutationObserver(() => {
            const ap = document.getElementById("artifact-panel");
            if (ap && panelEl.parentNode === container) {
                container.insertBefore(panelEl, ap);
                obs.disconnect();
            }
        });
        obs.observe(container, { childList: true });
    }

    attachResizeHandle(panelEl);

    // Apply top offset matching the A0 chrome bar
    function applyTopOffset() {
        const topBar = document.getElementById("time-date-container");
        if (!topBar) return;
        const r = topBar.getBoundingClientRect();
        const offset = Math.ceil(r.bottom) + 4;
        if (offset > 10) panelEl.style.paddingTop = offset + "px";
    }
    requestAnimationFrame(() => {
        applyTopOffset();
        setTimeout(applyTopOffset, 800);
    });

    // Pre-load topics list for the filter dropdown (fires after Alpine init)
    document.addEventListener("alpine:initialized", async () => {
        try {
            const d = await ossApi("/api/topics");
            const comp = Alpine.$data(panelEl);
            if (comp) {
                comp.topics = d.topics || [];
                comp.newCount = 0;
                // Quick badge count from staging
                const s = await ossApi("/api/staging", "POST", { limit: 1 });
                comp.newCount = s.total || 0;
                comp.claimsTotal = s.total || 0;
                // Load ingest state
                const h = await fetch(OSS_URL + "/api/health", {
                    headers: { "X-Analyst-Token": TOKEN }
                });
                if (h.ok) comp.ossHealth = await h.json();
            }
        } catch (e) {
            console.warn("[INTEL-PANEL] Background init failed:", e.message);
        }
    });
}
