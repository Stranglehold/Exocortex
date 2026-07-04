"""
oss_panel — OSS V2 Analyst Interface Panel
==========================================

Emits a fully interactive, self-contained OSS analyst panel as an artifact.
Single Alpine.js root with 5 in-panel tabs — no agent round-trip to switch views.

Tabs:
  Dashboard  — health status, active questions, staged claims preview, synthesis
  Questions  — create/evolve questions with attention weight sliders
  Claims     — full feed with trust filters, inline promote/discard, expandable detail
  Sources    — credibility sliders (auto-save on release, no separate Save button)
  Control    — pipeline toggle, claim queue triage, topics management, source weights

Args:
  view (str): dashboard | questions | claims | sources | control  (default: dashboard)
"""

from helpers.tool import Tool, Response

_API = "/api/plugins/oss"

_STYLE = """<style>
.oss{font:12px/1.4 inherit;color:var(--color-text)}
.oss-hdr{display:flex;align-items:center;justify-content:space-between;padding:7px 12px;border-bottom:1px solid var(--color-border)}
.oss-title{font-size:13px;font-weight:600}
.oss-badge{font-size:10px;padding:2px 8px;border-radius:10px;background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text-muted)}
.oss-badge-ok{background:#1a3a1a;border-color:#2d6e2d;color:#5fb85f}
.oss-badge-warn{background:#3a2a00;border-color:#7a5500;color:#d4a017}
.oss-badge-err{background:#3a1a1a;border-color:#7a2d2d;color:#d46060}
.oss-tabs{display:flex;gap:0;padding:3px 8px 0;border-bottom:1px solid var(--color-border);overflow-x:auto;flex-shrink:0}
.oss-tab{background:none;border:none;border-bottom:2px solid transparent;color:var(--color-text-muted);padding:4px 9px;cursor:pointer;font-size:11px;margin-bottom:-1px;white-space:nowrap;font:inherit}
.oss-tab:hover{color:var(--color-text)}
.oss-tab-on{color:var(--color-text);border-bottom-color:var(--color-primary,#5050c0);font-weight:600}
.oss-tab-badge{background:#7a5500;color:#d4a017;border-radius:8px;padding:0 5px;font-size:9px;margin-left:3px;display:inline-block;line-height:1.4}
.oss-body{padding:8px 12px;overflow-y:auto;max-height:520px}
.oss-sec{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--color-text-muted);padding:6px 0 3px;border-top:1px solid var(--color-border);margin-top:6px}
.oss-sec:first-child,.oss-sec-first{border-top:none;margin-top:0}
.oss-row{display:grid;align-items:center;gap:6px;padding:4px 6px;border-radius:4px;cursor:pointer}
.oss-row:hover,.oss-row-sel{background:var(--color-background-hover)}
.oss-row-head{font-size:10px;font-weight:600;text-transform:uppercase;color:var(--color-text-muted);padding:2px 6px;border-bottom:1px solid var(--color-border);margin-bottom:3px}
.oss-trust-staged{background:#3a3000;border-color:#7a6500;color:#d4b820}
.oss-trust-promoted{background:#1a3a1a;border-color:#2d6e2d;color:#5fb85f}
.oss-trust-returned{background:#3a2000;border-color:#7a4a00;color:#d48020}
.oss-trust-irrelevant{background:var(--color-message-bg);border-color:var(--color-border);color:var(--color-text-muted)}
.oss-trust-falsified{background:#3a1a1a;border-color:#7a2d2d;color:#d46060}
.oss-pill{font-size:9px;padding:1px 6px;border-radius:8px;border:1px solid;white-space:nowrap}
.oss-btn{background:none;border:1px solid var(--color-border);color:var(--color-text-muted);padding:2px 8px;border-radius:4px;cursor:pointer;font-size:11px;font:inherit}
.oss-btn:hover{background:var(--color-background-hover);color:var(--color-text)}
.oss-btn-on{background:var(--color-primary,#5050c0)!important;border-color:transparent!important;color:#fff!important}
.oss-btn-sm{padding:1px 6px;font-size:10px}
.oss-detail{background:var(--color-message-bg);border:1px solid var(--color-border);border-radius:4px;margin:2px 0 8px 2px;padding:8px 10px}
.oss-claimtext{font-size:11px;line-height:1.5;color:var(--color-text-muted);margin-bottom:6px;white-space:pre-wrap}
.oss-frow{display:flex;flex-direction:column;gap:4px;margin-bottom:8px}
.oss-lbl{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--color-text-muted)}
.oss-inp{background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:3px 8px;border-radius:4px;font-size:11px;flex:1;min-width:0;font:inherit}
.oss-ta{width:100%;box-sizing:border-box;background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:5px 8px;border-radius:4px;font-size:11px;font-family:inherit;resize:vertical}
.oss-sel{background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:3px 8px;border-radius:4px;font-size:11px;font:inherit}
.oss-load{padding:16px;text-align:center;color:var(--color-text-muted);font-size:11px}
.oss-err{padding:6px;color:#d46060;font-size:11px}
.oss-msg{font-size:11px;color:var(--color-text-muted);padding-top:3px}
.oss-result{background:var(--color-message-bg);border:1px solid var(--color-border);border-radius:4px;padding:10px;margin-top:8px;font-size:11px;line-height:1.6;white-space:pre-wrap;color:var(--color-text-muted)}
.oss-vel{display:flex;gap:8px;flex-wrap:wrap;padding:4px 0}
.oss-vel-item{font-size:11px;padding:3px 8px;border-radius:4px;background:var(--color-message-bg);border:1px solid var(--color-border)}
.oss-wt-row{display:flex;align-items:center;gap:8px;margin:3px 0;font-size:11px}
.oss-wt-lbl{width:90px;color:var(--color-text-muted)}
.oss-range{flex:1;accent-color:var(--color-primary,#5050c0)}
.oss-range-val{width:30px;text-align:right;font-size:10px;color:var(--color-text-muted)}
.oss-src-row{display:grid;gap:6px;align-items:center;padding:4px 6px;border-radius:3px;font-size:11px}
.oss-src-row:hover{background:var(--color-background-hover)}
.oss-id{font-family:monospace;font-size:10px;color:var(--color-text-muted)}
</style>"""

_ATTENTION_DOMAINS = ["logistics", "diplomatic", "economic", "military", "social"]


# ── JavaScript data object (plain string — no f-string escaping needed) ────────
# Placeholders: __VIEW__ → initial view, _API_ → API base path

_JS_DATA = """
{
  view: '__VIEW__',
  _ld: {}, _healthDot: 'unknown', _healthTs: 0, _toast: null, _toastTimer: null, cPending: {},
  go(v) {
    this.view = v;
    if (!this._ld[v]) {
      this._ld[v] = 1;
      const fn = this['_i_' + v];
      if (fn) fn.call(this);
    }
  },
  async refreshHeader() {
    try {
      const h = await ExoArtifact.fetchJson('_API_/api_oss_health', {});
      if (h.ok) { this.dH = h; this._healthTs = Date.now(); this._healthDot = 'ok'; }
      else { this._healthDot = 'err'; }
    } catch { this._healthDot = 'err'; }
  },

  // ── Shared helpers ──────────────────────────────────────────────────────────
  tCls(t) {
    const m = {
      STAGED: 'oss-pill oss-trust-staged',
      PROMOTED: 'oss-pill oss-trust-promoted',
      RETURNED_TO_STAGED: 'oss-pill oss-trust-returned',
      IRRELEVANT: 'oss-pill oss-trust-irrelevant',
      FALSIFIED: 'oss-pill oss-trust-falsified'
    };
    return m[t] || 'oss-pill oss-trust-irrelevant';
  },
  hCls(s) {
    if (!s) return 'oss-badge';
    return s === 'NOMINAL' ? 'oss-badge oss-badge-ok'
         : s === 'DEGRADED' ? 'oss-badge oss-badge-warn'
         : 'oss-badge oss-badge-err';
  },
  hDotCls() {
    if (this._healthDot === 'ok') return 'color:#5fb85f';
    if (this._healthDot === 'err') return 'color:#d46060';
    return 'color:#666';
  },
  toast(msg, type) {
    this._toast = {msg, type: type||'info'};
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => { this._toast = null; }, 3500);
  },

  // ── Dashboard (prefix: d) ───────────────────────────────────────────────────
  dH: null, dQ: [], dSt: [], dRej: null,
  dL: false, dE: null,
  dSynQ: '', dSynR: null, dSynL: false, dSynE: null,
  get dTotal() {
    const cc = (this.dH && this.dH.claim_counts) || {};
    return (cc.PROMOTED || 0) + (cc.STAGED || 0) + (cc.IRRELEVANT || 0);
  },
  async _i_dashboard() {
    this.dL = true; this.dE = null;
    try {
      const [h, q, s, r] = await Promise.all([
        ExoArtifact.fetchJson('_API_/api_oss_health', {}),
        ExoArtifact.fetchJson('_API_/api_oss_questions', {action: 'list'}),
        ExoArtifact.fetchJson('_API_/api_oss_staging', {action: 'list', limit: 5}),
        ExoArtifact.fetchJson('_API_/api_oss_rejections', {action: 'summary'}),
      ]);
      this.dH = h.ok ? h : null;
      this.dQ = (q.ok && q.questions) || [];
      this.dSt = (s.ok && (Array.isArray(s.result) ? s.result : s.claims)) || [];
      this.dRej = r.ok ? r : null;
    } catch(e) { this.dE = String(e); }
    this.dL = false;
  },
  dSprint() {
    ExoArtifact.message('Run oss_ingest_sprint for 7 minutes, then report what was found.');
  },
  async dSynthesize() {
    if (!this.dSynQ.trim()) return;
    this.dSynL = true; this.dSynE = null; this.dSynR = null;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_synthesis', {question: this.dSynQ, limit: 30});
      if (!r.ok) throw new Error(r.error || 'Synthesis failed');
      this.dSynR = r;
    } catch(e) { this.dSynE = String(e); }
    this.dSynL = false;
  },
  dToSF() {
    const ctx = (this.dSynR && this.dSynR.synthesis_text || '').slice(0, 600);
    ExoArtifact.message('Open swarmfish_panel predict view. Question: "' + this.dSynQ + '"\\n\\nOSS evidence context:\\n' + ctx);
  },

  // ── Questions (prefix: q) ───────────────────────────────────────────────────
  qQ: [], qL: false, qE: null,
  qForm: false, qText: '', qEvId: null,
  qWts: {logistics: 0.5, diplomatic: 0.5, economic: 0.5, military: 0.5, social: 0.5},
  qSaving: false, qMsg: null,
  async _i_questions() {
    this.qL = true; this.qE = null;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_questions', {action: 'list'});
      if (!r.ok) throw new Error(r.error);
      this.qQ = r.questions || [];
    } catch(e) { this.qE = String(e); }
    this.qL = false;
  },
  async qSave() {
    if (!this.qText.trim()) return;
    this.qSaving = true; this.qMsg = null;
    try {
      const p = this.qEvId
        ? {action: 'evolve', question_id: this.qEvId, text: this.qText, attention_weights: this.qWts}
        : {action: 'create', text: this.qText, attention_weights: this.qWts};
      const r = await ExoArtifact.fetchJson('_API_/api_oss_questions', p);
      if (!r.ok) throw new Error(r.error || 'Failed');
      this.qMsg = 'Saved.'; this.qText = ''; this.qEvId = null; this.qForm = false;
      this._ld['questions'] = 0; await this._i_questions();
    } catch(e) { this.qMsg = 'Error: ' + String(e); }
    this.qSaving = false;
  },
  async qDeactivate(id) {
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_questions', {action: 'deactivate', question_id: id});
      if (!r.ok) throw new Error(r.error);
      this._ld['questions'] = 0; await this._i_questions();
    } catch(e) { alert(String(e)); }
  },
  qEvolve(q) { this.qEvId = q.id; this.qText = q.text; this.qForm = true; },
  qPW(raw) { try { return JSON.parse(raw) || {}; } catch { return {}; } },

  // ── Claims (prefix: c) ──────────────────────────────────────────────────────
  cClaims: [], cTopics: [], cTopic: '', cTrust: '',
  cL: false, cE: null, cSel: null, cAct: {},
  async _i_claims() {
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_topics', {});
      this.cTopics = (r.ok && r.topics) || [];
    } catch {}
    await this.cFetch();
  },
  async cFetch() {
    this.cL = true; this.cE = null;
    try {
      const p = {action: 'list', limit: 100};
      if (this.cTopic) p.topic = this.cTopic;
      if (this.cTrust) p.trust_level = this.cTrust;
      const r = await ExoArtifact.fetchJson('_API_/api_oss_feed', p);
      if (!r.ok) throw new Error(r.error);
      this.cClaims = r.claims || [];
    } catch(e) { this.cE = String(e); }
    this.cL = false;
  },
  cToggle(id) { this.cSel = this.cSel === id ? null : id; },
  async cPromote(id) {
    this.cPending[id] = true;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_staging', {action: 'promote', claim_id: id});
      if (r.ok) { this.cAct[id] = '✓'; this.cClaims = this.cClaims.map(c => c.id === id ? {...c, trust_level: 'PROMOTED'} : c); }
      else { this.toast('Promote failed: ' + (r.error||'unknown error'), 'err'); }
    } catch(e) { this.toast('Promote failed: ' + String(e), 'err'); }
    this.cPending[id] = false;
  },
  async cDrop(id) {
    this.cPending[id] = true;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_staging', {action: 'mark_irrelevant', claim_id: id, reason: 'analyst_review'});
      if (r.ok) { this.cAct[id] = '✗'; this.cClaims = this.cClaims.filter(c => c.id !== id); }
      else { this.toast('Discard failed: ' + (r.error||'unknown error'), 'err'); }
    } catch(e) { this.toast('Discard failed: ' + String(e), 'err'); }
    this.cPending[id] = false;
  },
  get cStaged() { return this.cClaims.filter(c => c.trust_level === 'STAGED').length; },

  // ── Sources (prefix: s) ─────────────────────────────────────────────────────
  sSrcs: [], sL: false, sE: null, sSaved: {},
  async _i_sources() {
    this.sL = true; this.sE = null;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_sources', {});
      if (!r.ok) throw new Error(r.error);
      this.sSrcs = (r.sources || []).map(s => {
        s._c = s.credibility_overall != null ? s.credibility_overall : 0.7;
        return s;
      });
    } catch(e) { this.sE = String(e); }
    this.sL = false;
  },
  async sSave(s) {
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_credibility', {action: 'set', source_id: s.id, overall: s._c});
      if (r.ok) { this.sSaved[s.id] = true; setTimeout(() => { this.sSaved[s.id] = false; }, 1500); }
      else { this.toast('Credibility save failed: ' + (r.error||'unknown error'), 'err'); }
    } catch(e) { this.toast('Credibility save failed: ' + String(e), 'err'); }
  },
  sTCls(t) {
    const m = {wire: 'oss-trust-staged', official: 'oss-trust-promoted', outlet: 'oss-trust-returned', social: 'oss-trust-falsified', independent: 'oss-trust-irrelevant'};
    return 'oss-pill ' + (m[t] || 'oss-trust-irrelevant');
  },

  // ── Control (prefix: x) ─────────────────────────────────────────────────────
  xH: null, xT: [], xS: [], xSt: [],
  xL: false, xE: null,
  xPaused: false, xTog: false,
  xMsg: null, xBatch: false,
  xTag: '', xDn: '', xAW: false, xAM: null,
  xSaving: {}, xMsgs: {},
  async _i_control() {
    this.xL = true; this.xE = null;
    try {
      const [h, t, s, st] = await Promise.all([
        ExoArtifact.fetchJson('_API_/api_oss_health', {}),
        ExoArtifact.fetchJson('_API_/api_oss_topics', {}),
        ExoArtifact.fetchJson('_API_/api_oss_sources', {}),
        ExoArtifact.fetchJson('_API_/api_oss_staging', {action: 'list', limit: 100}),
      ]);
      this.xH = h.ok ? h : null;
      this.xPaused = this.xH && this.xH.ingestion_status === 'paused';
      this.xT = (t.ok && t.topics) || [];
      this.xS = (s.ok && s.sources || []).map(src => {
        src._c = src.credibility_overall != null ? src.credibility_overall : 0.7;
        return src;
      });
      const raw = st.ok ? (Array.isArray(st.result) ? st.result : st.claims) || [] : [];
      this.xSt = raw.filter(c => c.trust_level === 'STAGED');
    } catch(e) { this.xE = String(e); }
    this.xL = false;
  },
  async xToggle() {
    this.xTog = true;
    const wasP = this.xPaused;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_ingest', {action: wasP ? 'resume' : 'pause'});
      if (r.ok) this.xPaused = r.paused;
      else { this.toast('Ingest toggle failed: ' + (r.error||'unknown error'), 'err'); }
    } catch(e) { this.toast('Ingest toggle failed: ' + String(e), 'err'); }
    this.xTog = false;
  },
  xSprint(m) {
    ExoArtifact.message('Run oss_ingest_sprint for ' + m + ' minutes then report what was found.');
  },
  async xPromote(id) {
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_staging', {action: 'promote', claim_id: id});
      if (r.ok) { this.xSt = this.xSt.filter(c => c.id !== id); this.xMsg = 'Promoted'; }
      else { this.toast('Promote failed: ' + (r.error||'unknown error'), 'err'); }
    } catch(e) { this.toast('Promote failed: ' + String(e), 'err'); }
  },
  async xDiscard(id) {
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_staging', {action: 'mark_irrelevant', claim_id: id, reason: 'analyst_review'});
      if (r.ok) { this.xSt = this.xSt.filter(c => c.id !== id); this.xMsg = 'Discarded'; }
      else { this.toast('Discard failed: ' + (r.error||'unknown error'), 'err'); }
    } catch(e) { this.toast('Discard failed: ' + String(e), 'err'); }
  },
  async xPromoteAll() {
    this.xBatch = true; this.xMsg = null; let n = 0, e = 0;
    for (const c of [...this.xSt]) {
      try {
        const r = await ExoArtifact.fetchJson('_API_/api_oss_staging', {action: 'promote', claim_id: c.id});
        if (r.ok) n++; else e++;
      } catch { e++; }
    }
    this.xMsg = n + ' promoted' + (e ? ', ' + e + ' errors' : '');
    this.xSt = []; this.xBatch = false;
    await this.refreshHeader();
    if (this._ld['dashboard']) { this._ld['dashboard'] = 0; this._i_dashboard(); }
  },
  async xDiscardAll() {
    this.xBatch = true; this.xMsg = null; let n = 0, e = 0;
    for (const c of [...this.xSt]) {
      try {
        const r = await ExoArtifact.fetchJson('_API_/api_oss_staging', {action: 'mark_irrelevant', claim_id: c.id, reason: 'batch_discard'});
        if (r.ok) n++; else e++;
      } catch { e++; }
    }
    this.xMsg = n + ' discarded' + (e ? ', ' + e + ' errors' : '');
    this.xSt = []; this.xBatch = false;
  },
  async xAddTopic() {
    if (!this.xTag.trim() || !this.xDn.trim()) return;
    this.xAW = true; this.xAM = null;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_add_topic', {tag: this.xTag.trim(), display_name: this.xDn.trim()});
      if (!r.ok) throw new Error(r.error || 'Failed');
      this.xAM = r.created ? 'Added.' : 'Already exists.'; this.xTag = ''; this.xDn = '';
      const t = await ExoArtifact.fetchJson('_API_/api_oss_topics', {});
      if (t.ok) this.xT = t.topics;
    } catch(e) { this.xAM = 'Error: ' + String(e); }
    this.xAW = false;
  },
  async xSaveCred(s) {
    this.xSaving[s.id] = true; this.xMsgs[s.id] = null;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_oss_credibility', {action: 'set', source_id: s.id, overall: s._c});
      this.xMsgs[s.id] = r.ok ? '✓' : 'Err';
    } catch { this.xMsgs[s.id] = '!'; }
    this.xSaving[s.id] = false;
  },

  // ── Init ────────────────────────────────────────────────────────────────────
  init() { this._ld = {}; this.go(this.view); setInterval(() => this.refreshHeader(), 5000); }
}
"""


def _oss_panel_html(initial_view: str = "dashboard") -> str:
    wts_js = ", ".join(f'"{d}":0.5' for d in _ATTENTION_DOMAINS)
    js = (
        _JS_DATA
        .replace("__VIEW__", initial_view)
        .replace("_API_", _API)
        .replace("{logistics: 0.5, diplomatic: 0.5, economic: 0.5, military: 0.5, social: 0.5}", "{" + wts_js + "}")
    )

    return f"""{_STYLE}
<div class="oss" x-data="{js}" x-init="init()">

  <!-- ── Header ─────────────────────────────────────────────────────────── -->
  <div class="oss-hdr">
    <span class="oss-title">OSS Intelligence Ledger</span>
    <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
      <span :style="hDotCls()" style="font-size:9px;line-height:1;" title="Backend connection status">●</span>
      <span :class="hCls(dH&&dH.health_signal)" x-text="dH?dH.health_signal:'—'"></span>
      <span x-show="dH&&dH.claim_counts" style="font-size:10px;color:var(--color-text-muted);">
        <span x-text="dH&&dH.claim_counts?(dH.claim_counts.PROMOTED||0)+' ✓':''"></span>
        <template x-if="dH&&dH.claim_counts&&(dH.claim_counts.STAGED||0)>0">
          <span style="color:#d4a017;margin-left:4px;"
            x-text="'· '+(dH.claim_counts.STAGED)+' staged'"></span>
        </template>
      </span>
      <span x-show="dH&&dH.ingestion_status"
        :style="dH&&dH.ingestion_status==='active'?'color:#5fb85f;font-size:10px;':'color:#d4a017;font-size:10px;'"
        x-text="dH?(dH.ingestion_status==='active'?'● ingesting':'○ paused'):''"></span>
      <span x-show="_healthTs>0" style="font-size:9px;color:var(--color-text-muted);"
        x-text="'↻ '+new Date(_healthTs).toLocaleTimeString()"></span>
      <button class="oss-btn oss-btn-sm" title="Refresh current view"
        @click="_ld[view]=0;go(view)">↻</button>
    </div>
  </div>

  <!-- ── Tab bar ────────────────────────────────────────────────────────── -->
  <div class="oss-tabs">
    <button class="oss-tab" :class="view==='dashboard'?'oss-tab-on':''" @click="go('dashboard')">Dashboard</button>
    <button class="oss-tab" :class="view==='questions'?'oss-tab-on':''" @click="go('questions')">Questions</button>
    <button class="oss-tab" :class="view==='claims'?'oss-tab-on':''" @click="go('claims')">
      Claims
      <span x-show="cStaged>0" class="oss-tab-badge" x-text="cStaged"></span>
    </button>
    <button class="oss-tab" :class="view==='sources'?'oss-tab-on':''" @click="go('sources')">Sources</button>
    <button class="oss-tab" :class="view==='control'?'oss-tab-on':''" @click="go('control')">
      Control
      <span x-show="xSt.length>0" class="oss-tab-badge" x-text="xSt.length"></span>
    </button>
  </div>

  <!-- ── Body ───────────────────────────────────────────────────────────── -->
  <div class="oss-body">

    <!-- ════════════════════════════════════════════════════════════════════
         DASHBOARD
         ════════════════════════════════════════════════════════════════════ -->
    <div x-show="view==='dashboard'">
      <div x-show="dL" class="oss-load">Loading dashboard…</div>
      <div x-show="!dL&&dE" class="oss-err" x-text="dE"></div>
      <div x-show="!dL&&!dE">

        <!-- Empty ledger CTA -->
        <div x-show="dTotal===0&&!dL"
          style="border:1px solid #7a5500;background:#241c00;border-radius:4px;padding:14px 12px;text-align:center;margin-bottom:8px;">
          <div style="font-size:13px;font-weight:600;color:#d4a017;margin-bottom:5px;">Ledger is Empty</div>
          <div style="font-size:11px;color:var(--color-text-muted);margin-bottom:10px;line-height:1.5;">
            No intelligence claims collected yet.<br>
            Run an ingestion sprint to fetch RSS feeds and extract claims.
          </div>
          <button class="oss-btn oss-btn-on" @click="dSprint()">Run Ingestion Sprint (7 min)</button>
        </div>

        <!-- Active questions -->
        <div class="oss-sec oss-sec-first">Active Questions (<span x-text="dQ.length"></span>)</div>
        <div x-show="dQ.length===0" style="padding:4px 6px;font-size:11px;color:var(--color-text-muted);">
          No active questions — open the Questions tab to create one.
        </div>
        <template x-for="q in dQ.slice(0,4)" :key="q.id">
          <div style="display:flex;align-items:center;gap:8px;padding:3px 6px;font-size:11px;">
            <span class="oss-id" x-text="q.id.slice(0,8)"></span>
            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" x-text="q.text"></span>
            <span style="font-size:10px;color:var(--color-text-muted);flex-shrink:0;"
              x-text="(q.last_updated||'').slice(0,10)"></span>
          </div>
        </template>

        <!-- Intelligence status -->
        <div class="oss-sec">Intelligence Status</div>
        <div class="oss-vel">
          <div class="oss-vel-item">
            <strong x-text="dH&&(dH.claim_counts&&dH.claim_counts.PROMOTED)||0"></strong> promoted
          </div>
          <div class="oss-vel-item"
            x-show="dH&&dH.claim_counts&&(dH.claim_counts.STAGED||0)>0"
            style="border-color:#7a5500;background:#241c00;color:#d4a017;">
            <strong x-text="dH&&(dH.claim_counts&&dH.claim_counts.STAGED)||0"></strong>
            staged <span style="font-size:10px;">(needs review)</span>
          </div>
          <div class="oss-vel-item" x-show="dH&&dH.source_count">
            <strong x-text="dH&&dH.source_count||0"></strong> sources
          </div>
          <div class="oss-vel-item" x-show="dH&&dH.last_claim">
            last: <span x-text="dH&&(dH.last_claim||'').slice(5,16)"></span>
          </div>
        </div>

        <!-- Recent staged claims -->
        <div class="oss-sec" x-show="dSt.length>0">
          Staged (<span x-text="dSt.length"></span>)
          <span style="font-weight:400;text-transform:none;letter-spacing:0;font-size:10px;">— needs review · open Claims tab for actions</span>
        </div>
        <template x-for="c in dSt" :key="c.id">
          <div style="display:flex;align-items:flex-start;gap:6px;padding:3px 6px;border-bottom:1px solid var(--color-border);font-size:11px;">
            <span :class="tCls(c.trust_level)" x-text="c.trust_level" style="flex-shrink:0;"></span>
            <span style="flex:1;color:var(--color-text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
              x-text="(c.claim_text||'').slice(0,100)"></span>
            <span style="font-size:10px;color:var(--color-text-muted);flex-shrink:0;white-space:nowrap;"
              x-text="c.source_name||''"></span>
          </div>
        </template>

        <!-- Rejection summary -->
        <div x-show="dRej&&dRej.total">
          <div class="oss-sec">Rejection Summary</div>
          <div style="padding:4px 6px;font-size:11px;color:var(--color-text-muted);">
            <span x-text="dRej&&dRej.total"></span> total —
            <template x-for="[k,v] in Object.entries((dRej&&dRej.by_reason)||{{}})" :key="k">
              <span style="margin-left:6px;" x-text="k+': '+v"></span>
            </template>
          </div>
        </div>

        <!-- Ask the ledger -->
        <div class="oss-sec">Ask the Ledger</div>
        <div style="display:flex;gap:6px;align-items:center;margin-top:2px;">
          <input class="oss-inp" placeholder="What is the evidence for…"
            x-model="dSynQ" @keydown.enter="dSynthesize()" :disabled="dTotal===0">
          <button class="oss-btn oss-btn-on" :disabled="!dSynQ.trim()||dSynL||dTotal===0"
            @click="dSynthesize()" x-text="dSynL?'…':'Ask'"></button>
        </div>
        <div x-show="dTotal===0&&!dL"
          style="font-size:10px;color:var(--color-text-muted);margin-top:3px;">
          Populate the ledger first — run an ingestion sprint.
        </div>
        <div x-show="dSynE" class="oss-err" x-text="dSynE"></div>
        <div x-show="dSynR" class="oss-result">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px;">
            <div style="font-size:10px;color:var(--color-text-muted);">
              <span x-text="(dSynR&&dSynR.supporting||[]).length"></span> supporting ·
              <span x-text="(dSynR&&dSynR.contradicting||[]).length"></span> contradicting ·
              <span x-text="(dSynR&&dSynR.neutral||[]).length"></span> neutral
            </div>
            <div style="display:flex;gap:4px;">
              <button class="oss-btn oss-btn-sm" @click="dToSF()"
                title="Send to SWARMFISH for probability assessment">→ SWARMFISH</button>
              <button class="oss-btn oss-btn-sm" @click="dSynR=null;dSynQ=''">Clear</button>
            </div>
          </div>
          <div x-text="dSynR&&dSynR.synthesis_text||''"></div>
        </div>

      </div><!-- /dashboard content -->
    </div><!-- /dashboard -->


    <!-- ════════════════════════════════════════════════════════════════════
         QUESTIONS
         ════════════════════════════════════════════════════════════════════ -->
    <div x-show="view==='questions'">
      <div x-show="qL" class="oss-load">Loading questions…</div>
      <div x-show="!qL&&qE" class="oss-err" x-text="qE"></div>
      <div x-show="!qL&&!qE">

        <!-- Toolbar -->
        <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0 4px;border-bottom:1px solid var(--color-border);">
          <span style="font-size:11px;color:var(--color-text-muted);">
            <span x-text="qQ.length"></span> active question(s)
          </span>
          <div style="display:flex;gap:5px;">
            <button class="oss-btn oss-btn-sm" :class="qForm&&!qEvId?'oss-btn-on':''"
              @click="qForm=!qForm;qEvId=null;qText=''">+ New</button>
            <button class="oss-btn oss-btn-sm" @click="_ld['questions']=0;_i_questions()">↻</button>
          </div>
        </div>

        <!-- Create / evolve form -->
        <div x-show="qForm" class="oss-detail" style="margin-top:8px;margin-bottom:8px;">
          <div class="oss-lbl" x-text="qEvId?'Evolve Question':'New Question'"></div>
          <textarea class="oss-ta" rows="2" style="margin:5px 0;"
            placeholder="What question should this ledger organize evidence around?"
            x-model="qText"></textarea>
          <div class="oss-lbl" style="margin-top:4px;">Attention Weights</div>
          <template x-for="d in ['logistics','diplomatic','economic','military','social']" :key="d">
            <div class="oss-wt-row">
              <span class="oss-wt-lbl" x-text="d"></span>
              <input type="range" class="oss-range" min="0" max="1" step="0.05"
                :value="qWts[d]" @input="qWts[d]=parseFloat($event.target.value)">
              <span class="oss-range-val" x-text="qWts[d].toFixed(2)"></span>
            </div>
          </template>
          <div style="display:flex;gap:6px;margin-top:8px;align-items:center;">
            <button class="oss-btn oss-btn-on" :disabled="!qText.trim()||qSaving"
              @click="qSave()" x-text="qSaving?'Saving…':'Save'"></button>
            <button class="oss-btn" @click="qForm=false;qEvId=null;qText=''">Cancel</button>
            <span x-show="qMsg" class="oss-msg" x-text="qMsg"></span>
          </div>
        </div>

        <!-- Question list -->
        <div x-show="qQ.length===0&&!qForm"
          style="padding:12px 6px;font-size:11px;color:var(--color-text-muted);">
          No active questions. Create one above to start directing the ledger's attention.
        </div>
        <template x-for="q in qQ" :key="q.id">
          <div class="oss-detail" style="margin-bottom:6px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
              <div style="flex:1;">
                <div style="font-size:11px;font-weight:500;" x-text="q.text"></div>
                <div style="font-size:10px;color:var(--color-text-muted);margin-top:2px;">
                  <span class="oss-id" x-text="q.id.slice(0,12)"></span>
                  · updated <span x-text="(q.last_updated||'').slice(0,10)"></span>
                </div>
              </div>
              <div style="display:flex;gap:4px;flex-shrink:0;">
                <button class="oss-btn oss-btn-sm" @click.stop="qEvolve(q)">Evolve</button>
                <button class="oss-btn oss-btn-sm" @click.stop="qDeactivate(q.id)">Deactivate</button>
              </div>
            </div>
            <div x-show="q.attention_weights&&Object.keys(qPW(q.attention_weights)||{{}}).length>0"
              style="display:flex;gap:5px;flex-wrap:wrap;margin-top:5px;">
              <template x-for="[k,v] in Object.entries(qPW(q.attention_weights)||{{}})" :key="k">
                <span class="oss-pill oss-trust-staged" x-text="k+': '+parseFloat(v).toFixed(2)"></span>
              </template>
            </div>
          </div>
        </template>

      </div>
    </div><!-- /questions -->


    <!-- ════════════════════════════════════════════════════════════════════
         CLAIMS
         ════════════════════════════════════════════════════════════════════ -->
    <div x-show="view==='claims'">
      <div x-show="cL" class="oss-load">Loading claims…</div>
      <div x-show="!cL&&cE" class="oss-err" x-text="cE"></div>
      <div x-show="!cL&&!cE">

        <!-- Filters -->
        <div style="display:flex;gap:5px;align-items:center;padding:5px 0 6px;border-bottom:1px solid var(--color-border);flex-wrap:wrap;">
          <select class="oss-sel" x-model="cTrust" @change="cFetch()">
            <option value="">all states</option>
            <option value="STAGED">STAGED</option>
            <option value="PROMOTED">PROMOTED</option>
            <option value="IRRELEVANT">IRRELEVANT</option>
          </select>
          <select class="oss-sel" x-model="cTopic" @change="cFetch()">
            <option value="">all topics</option>
            <template x-for="t in cTopics" :key="t.tag">
              <option :value="t.tag" x-text="t.tag"></option>
            </template>
          </select>
          <button class="oss-btn oss-btn-sm" @click="cFetch()">↻</button>
          <span style="flex:1;"></span>
          <span style="font-size:10px;color:var(--color-text-muted);">
            <span x-text="cClaims.length"></span> shown
            <span x-show="cStaged>0" style="color:#d4a017;margin-left:4px;">
              · <span x-text="cStaged"></span> staged
            </span>
          </span>
        </div>

        <!-- Empty states -->
        <div x-show="cClaims.length===0&&!cTopic&&!cTrust"
          style="padding:20px;text-align:center;font-size:11px;">
          <div style="color:var(--color-text-muted);margin-bottom:8px;">No claims in ledger.</div>
          <button class="oss-btn oss-btn-on"
            @click="ExoArtifact.message('Run oss_ingest_sprint for 7 minutes then report what was found.')">
            Run Ingestion Sprint
          </button>
        </div>
        <div x-show="cClaims.length===0&&(cTopic||cTrust)"
          style="padding:10px 6px;font-size:11px;color:var(--color-text-muted);">
          No claims match this filter.
        </div>

        <!-- Column header -->
        <div x-show="cClaims.length>0" class="oss-row oss-row-head"
          style="grid-template-columns:76px 1fr 70px 52px;">
          <span>State</span><span>Claim</span><span>Date</span><span>Act</span>
        </div>

        <!-- Claim rows -->
        <template x-for="c in cClaims" :key="c.id">
          <div>
            <div class="oss-row" style="grid-template-columns:76px 1fr 70px 52px;"
              @click="cToggle(c.id)" :class="cSel===c.id?'oss-row-sel':''">
              <span :class="tCls(c.trust_level)" x-text="c.trust_level"></span>
              <span style="font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                x-text="(c.claim_text||'').slice(0,120)"></span>
              <span style="font-size:10px;color:var(--color-text-muted);text-align:right;"
                x-text="(c.extracted_at||'').slice(0,10)"></span>
              <div style="display:flex;gap:2px;justify-content:flex-end;" @click.stop>
                <div x-show="c.trust_level==='STAGED'" style="display:flex;gap:2px;">
                  <button class="oss-btn oss-btn-sm"
                    style="color:#5fb85f;padding:1px 5px;min-width:0;"
                    :disabled="cPending[c.id]"
                    title="Promote" @click.stop="cPromote(c.id)"
                    x-text="cPending[c.id]?'…':'✓'"></button>
                  <button class="oss-btn oss-btn-sm"
                    style="color:#d46060;padding:1px 5px;min-width:0;"
                    :disabled="cPending[c.id]"
                    title="Mark irrelevant" @click.stop="cDrop(c.id)">✕</button>
                </div>
                <span x-show="cAct[c.id]"
                  style="font-size:10px;color:var(--color-text-muted);padding:1px 3px;"
                  x-text="cAct[c.id]"></span>
              </div>
            </div>
            <!-- Expanded claim detail -->
            <div x-show="cSel===c.id" class="oss-detail">
              <div class="oss-claimtext" x-text="c.claim_text"></div>
              <div style="display:flex;gap:12px;flex-wrap:wrap;font-size:10px;color:var(--color-text-muted);margin-bottom:5px;">
                <span>Source: <strong x-text="c.source_name||'?'"></strong></span>
                <span x-show="c.technique_class">Technique: <span x-text="c.technique_class"></span></span>
                <span x-show="c.cui_bono&&c.cui_bono!=='[]'">
                  Cui bono: <span x-text="JSON.parse(c.cui_bono||'[]').join(', ')"></span>
                </span>
              </div>
              <div x-show="c.article_url" style="font-size:10px;margin-bottom:5px;">
                <a :href="c.article_url" target="_blank"
                  style="color:var(--color-text-muted);word-break:break-all;"
                  x-text="c.article_url"></a>
              </div>
              <div x-show="c.trust_level==='STAGED'" style="display:flex;gap:5px;margin-top:6px;">
                <button class="oss-btn oss-btn-sm" style="color:#5fb85f;"
                  :disabled="cPending[c.id]" @click="cPromote(c.id)"
                  x-text="cPending[c.id]?'…':'✓ Promote'"></button>
                <button class="oss-btn oss-btn-sm" style="color:#d46060;"
                  :disabled="cPending[c.id]" @click="cDrop(c.id)">✕ Mark Irrelevant</button>
              </div>
            </div>
          </div>
        </template>

      </div>
    </div><!-- /claims -->


    <!-- ════════════════════════════════════════════════════════════════════
         SOURCES
         ════════════════════════════════════════════════════════════════════ -->
    <div x-show="view==='sources'">
      <div x-show="sL" class="oss-load">Loading sources…</div>
      <div x-show="!sL&&sE" class="oss-err" x-text="sE"></div>
      <div x-show="!sL&&!sE">

        <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0 6px;border-bottom:1px solid var(--color-border);">
          <span style="font-size:11px;color:var(--color-text-muted);">
            <span x-text="sSrcs.length"></span> registered source(s) — drag slider to set credibility, auto-saves on release
          </span>
          <button class="oss-btn oss-btn-sm" @click="_ld['sources']=0;_i_sources()">↻</button>
        </div>

        <div x-show="sSrcs.length===0&&!sL"
          style="padding:10px 6px;font-size:11px;color:var(--color-text-muted);">
          No sources registered yet.
        </div>

        <div x-show="sSrcs.length>0" class="oss-row oss-row-head"
          style="grid-template-columns:130px 58px 48px 1fr 44px;margin-top:4px;">
          <span>Source</span><span>Type</span><span>Claims</span><span>Credibility</span><span></span>
        </div>

        <template x-for="s in sSrcs" :key="s.id">
          <div class="oss-src-row" style="grid-template-columns:130px 58px 48px 1fr 44px;">
            <span style="font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
              x-text="s.name"></span>
            <span :class="sTCls(s.source_type)" x-text="s.source_type"></span>
            <span style="color:var(--color-text-muted);" x-text="s.total_claims||0"></span>
            <div style="display:flex;align-items:center;gap:6px;">
              <input type="range" class="oss-range" min="0" max="1" step="0.05"
                :value="s._c"
                @input="s._c=parseFloat($event.target.value)"
                @change="sSave(s)">
              <span class="oss-range-val" x-text="s._c.toFixed(2)"></span>
            </div>
            <span style="font-size:10px;text-align:right;"
              :style="sSaved[s.id]?'color:#5fb85f;':'color:var(--color-text-muted);'"
              x-text="sSaved[s.id]?'✓ saved':''"></span>
          </div>
        </template>

      </div>
    </div><!-- /sources -->


    <!-- ════════════════════════════════════════════════════════════════════
         CONTROL
         ════════════════════════════════════════════════════════════════════ -->
    <div x-show="view==='control'">
      <div x-show="xL" class="oss-load">Loading control panel…</div>
      <div x-show="!xL&&xE" class="oss-err" x-text="xE"></div>
      <div x-show="!xL&&!xE">

        <!-- Pipeline -->
        <div class="oss-sec oss-sec-first">Pipeline</div>
        <div class="oss-detail">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap;">
            <span class="oss-lbl" style="width:64px;">Ingestion</span>
            <button style="cursor:pointer;min-width:110px;border-radius:10px;padding:3px 12px;font-size:11px;font-weight:600;border:1px solid;font:inherit;"
              :style="xPaused?'background:#3a2a00;border-color:#7a5500;color:#d4a017;':'background:#1a3a1a;border-color:#2d6e2d;color:#5fb85f;'"
              :disabled="xTog" @click="xToggle()"
              x-text="xTog?'…':xPaused?'▶  PAUSED':'⏸  ACTIVE'"></button>
            <span x-show="xH&&xH.last_claim" style="font-size:10px;color:var(--color-text-muted);"
              x-text="xH?'last: '+(xH.last_claim||'').slice(5,16):''"></span>
          </div>
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
            <span class="oss-lbl" style="width:64px;">Sprint</span>
            <button class="oss-btn oss-btn-sm" @click="xSprint(3)">3 min</button>
            <button class="oss-btn oss-btn-sm" @click="xSprint(7)">7 min</button>
            <button class="oss-btn oss-btn-sm" @click="xSprint(10)">10 min</button>
            <span style="font-size:10px;color:var(--color-text-muted);">bounded ingestion run via agent</span>
          </div>
        </div>

        <!-- Claim queue -->
        <div class="oss-sec">Claim Queue
          <span style="font-weight:400;text-transform:none;letter-spacing:0;margin-left:4px;">
            — <span x-text="xSt.length"></span> staged
          </span>
        </div>
        <div class="oss-detail">
          <div style="display:flex;gap:6px;align-items:center;margin-bottom:6px;flex-wrap:wrap;">
            <button class="oss-btn oss-btn-on" :disabled="xSt.length===0||xBatch"
              @click="xPromoteAll()"
              x-text="xBatch?'Working…':'Promote All ('+xSt.length+')'"></button>
            <button class="oss-btn" :disabled="xSt.length===0||xBatch"
              @click="xDiscardAll()"
              x-text="xBatch?'…':'Discard All ('+xSt.length+')'"></button>
            <span x-show="xMsg" class="oss-msg" x-text="xMsg"></span>
          </div>
          <div x-show="xSt.length===0"
            style="font-size:11px;color:var(--color-text-muted);padding:2px 0;">
            Queue empty — all staged claims processed.
          </div>
          <template x-for="c in xSt.slice(0,15)" :key="c.id">
            <div style="display:flex;align-items:flex-start;gap:6px;padding:3px 0;border-bottom:1px solid var(--color-border);font-size:11px;">
              <span style="font-size:10px;color:var(--color-text-muted);white-space:nowrap;padding-top:1px;min-width:68px;"
                x-text="(c.extracted_at||'').slice(5,16)"></span>
              <span style="flex:1;color:var(--color-text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                x-text="(c.claim_text||'').slice(0,90)"></span>
              <div style="display:flex;gap:2px;flex-shrink:0;">
                <button class="oss-btn oss-btn-sm" style="color:#5fb85f;padding:1px 6px;"
                  title="Promote" @click="xPromote(c.id)">✓</button>
                <button class="oss-btn oss-btn-sm" style="color:#d46060;padding:1px 6px;"
                  title="Discard" @click="xDiscard(c.id)">✕</button>
              </div>
            </div>
          </template>
          <div x-show="xSt.length>15"
            style="font-size:10px;color:var(--color-text-muted);padding-top:4px;">
            +<span x-text="xSt.length-15"></span> more — open Claims tab to see all
          </div>
        </div>

        <!-- Topics -->
        <div class="oss-sec">Topics
          <span style="font-weight:400;text-transform:none;letter-spacing:0;margin-left:4px;">
            — <span x-text="xT.filter(t=>t.active).length"></span> active
          </span>
        </div>
        <div class="oss-detail">
          <div x-show="xT.length===0" style="font-size:11px;color:var(--color-text-muted);">
            No topics configured.
          </div>
          <template x-for="t in xT" :key="t.tag">
            <div style="display:flex;align-items:center;gap:8px;padding:3px 0;border-bottom:1px solid var(--color-border);font-size:11px;">
              <span style="min-width:110px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                :style="t.active?'':'opacity:.4'" x-text="t.tag"></span>
              <span style="font-size:10px;color:var(--color-text-muted);min-width:60px;"
                x-text="(t.live_claim_count||0)+' claims'"></span>
              <span style="flex:1;font-size:10px;color:var(--color-text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                x-text="t.display_name||''"></span>
              <span class="oss-pill"
                :class="t.active?'oss-trust-promoted':'oss-trust-irrelevant'"
                x-text="t.active?'active':'off'"></span>
            </div>
          </template>
          <div style="display:flex;gap:5px;align-items:center;margin-top:8px;flex-wrap:wrap;">
            <input class="oss-inp" placeholder="tag-slug" x-model="xTag"
              style="width:90px;flex:none;">
            <input class="oss-inp" placeholder="Display Name" x-model="xDn"
              @keydown.enter="xAddTopic()" style="flex:1;min-width:100px;">
            <button class="oss-btn oss-btn-sm oss-btn-on"
              :disabled="!xTag.trim()||!xDn.trim()||xAW"
              @click="xAddTopic()" x-text="xAW?'…':'+ Add'"></button>
            <span x-show="xAM" class="oss-msg" x-text="xAM"></span>
          </div>
        </div>

        <!-- Sources -->
        <div class="oss-sec">Sources
          <span style="font-weight:400;text-transform:none;letter-spacing:0;margin-left:4px;">
            — <span x-text="xS.length"></span> registered
          </span>
        </div>
        <div class="oss-detail">
          <div x-show="xS.length===0" style="font-size:11px;color:var(--color-text-muted);">
            No sources registered.
          </div>
          <template x-for="s in xS" :key="s.id">
            <div style="display:flex;align-items:center;gap:6px;padding:3px 0;border-bottom:1px solid var(--color-border);">
              <span style="font-size:11px;font-weight:500;min-width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                x-text="s.name"></span>
              <span style="font-size:10px;color:var(--color-text-muted);min-width:44px;"
                x-text="s.source_type||''"></span>
              <input type="range" class="oss-range" min="0" max="1" step="0.05" style="flex:1;"
                :value="s._c"
                @input="s._c=parseFloat($event.target.value)"
                @change="xSaveCred(s)">
              <span style="font-size:10px;color:var(--color-text-muted);width:28px;text-align:right;"
                x-text="s._c.toFixed(2)"></span>
              <span style="font-size:10px;min-width:18px;text-align:right;"
                :style="xMsgs[s.id]==='✓'?'color:#5fb85f;':'color:#d46060;'"
                x-text="xMsgs[s.id]||''"></span>
            </div>
          </template>
        </div>

      </div>
    </div><!-- /control -->

  </div><!-- /oss-body -->

  <!-- Toast notification -->
  <div x-show="_toast" x-cloak
    style="position:fixed;bottom:14px;left:50%;transform:translateX(-50%);
      padding:6px 16px;border-radius:4px;font-size:11px;z-index:999;
      pointer-events:none;max-width:90%;text-align:center;white-space:nowrap;"
    :style="_toast&&_toast.type==='err'
      ? 'background:#3a1a1a;border:1px solid #7a2d2d;color:#d46060;'
      : 'background:#1a3a1a;border:1px solid #2d6e2d;color:#5fb85f;'"
    x-text="_toast&&_toast.msg">
  </div>

</div><!-- /root -->"""


# ── Tool class ────────────────────────────────────────────────────────────────

class OssPanel(Tool):
    """
    Open the OSS V2 analyst interface — a self-contained panel with 5 in-panel tabs.

    Tabs: Dashboard | Questions | Claims | Sources | Control
    No agent round-trip needed to switch between views.

    Args:
        view (str): dashboard | questions | claims | sources | control  (default: dashboard)
    """

    async def execute(self, **kwargs) -> Response:
        view = (self.args.get("view") or "dashboard").strip().lower()
        if view not in ("dashboard", "questions", "claims", "sources", "control"):
            view = "dashboard"

        html = _oss_panel_html(view)

        self.agent.context.log.log(
            type="artifact",
            heading="OSS Intelligence Ledger",
            content=html,
        )
        return Response(message=f"OSS panel opened at {view}.", break_loop=False)
