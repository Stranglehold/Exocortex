/**
 * intelligence-store.js — Alpine store for the Intelligence Panel
 *
 * Manages all state and API calls for the 6-tab right-canvas surface.
 * Import createIntelStore() from register-intelligence.js and register
 * it as Alpine.store("intelligence") before the panel HTML renders.
 */

const OSS_URL = "http://localhost:7731";
const TOKEN   = "dev_analyst_token";

async function ossGet(path) {
  const r = await fetch(OSS_URL + path, {
    headers: { "X-Analyst-Token": TOKEN },
  });
  if (!r.ok) throw new Error(`OSS ${r.status} — ${path}`);
  return r.json();
}

async function ossPost(path, body = {}) {
  const r = await fetch(OSS_URL + path, {
    method: "POST",
    headers: { "X-Analyst-Token": TOKEN, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`OSS ${r.status} — ${path}`);
  return r.json();
}

export function createIntelStore() {
  return {
    // ── Core ─────────────────────────────────────────────────────────────────
    tab:       "status",
    loading:   false,
    error:     null,
    toast:     null,
    connected: false,
    _toastTimer: null,
    _pollTimer:  null,
    _sse:        null,

    // ── Status tab ───────────────────────────────────────────────────────────
    health:        null,
    topics:        [],
    sources:       [],
    addTopicInput: "",
    addTopicOpen:  false,

    // ── Triage tab ───────────────────────────────────────────────────────────
    staged:        [],
    stagedTotal:   0,
    triageTopic:   "",
    triageSel:     [],    // array of selected claim IDs

    // ── Ledger tab ───────────────────────────────────────────────────────────
    ledger:      [],
    ledgerTopic: "",
    ledgerTotal: 0,

    // ── Analysis tab ─────────────────────────────────────────────────────────
    analysisTopic: "",
    drift:         null,
    silence:       null,
    activation:    null,
    contradictions: [],

    // ── Hypotheses tab ───────────────────────────────────────────────────────
    hypotheses: [],
    hypStatus:  "ACTIVE",
    hypTopic:   "",

    // ── Predict tab ──────────────────────────────────────────────────────────
    predictTopic:  "",
    swfRunning:    false,
    swfProfiles:   [],
    swfConsensus:  null,

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    async connect() {
      this.connected = true;
      await this.refresh();
      this._pollTimer = setInterval(() => this._tick(), 30_000);
    },

    disconnect() {
      this.connected = false;
      clearInterval(this._pollTimer);
      this._pollTimer = null;
      if (this._sse) { this._sse.close(); this._sse = null; }
    },

    async refresh() {
      await Promise.allSettled([this._loadHealth(), this._loadTopics()]);
      await this.refreshTab();
    },

    async refreshTab() {
      this.error   = null;
      this.loading = true;
      try {
        const map = {
          status:     () => this._loadSources(),
          triage:     () => this.loadStaged(),
          ledger:     () => this.loadLedger(),
          analysis:   () => this.loadAnalysis(),
          hypotheses: () => this.loadHypotheses(),
          predict:    () => Promise.resolve(),
        };
        await (map[this.tab] ?? (() => Promise.resolve()))();
      } catch (e) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },

    async setTab(t) {
      this.tab = t;
      await this.refreshTab();
    },

    async _tick() {
      if (!this.connected) return;
      try { await this._loadHealth(); } catch (_) {}
    },

    // ── Health / Status ───────────────────────────────────────────────────────

    async _loadHealth() {
      this.health = await ossGet("/api/health");
    },

    async _loadTopics() {
      const d = await ossGet("/api/topics");
      this.topics = d.topics ?? (Array.isArray(d) ? d : []);
    },

    async _loadSources() {
      const d = await ossGet("/api/sources");
      this.sources = d.sources ?? (Array.isArray(d) ? d : []);
    },

    get ingestPaused() { return this.health?.ingest_paused ?? true; },

    get healthBadge() {
      if (!this.health) return "unknown";
      const { failing = 0, stale = 0 } = this.health.source_health ?? {};
      if (failing > 0) return "failing";
      if (stale   > 0) return "stale";
      return "ok";
    },

    async pauseIngest() {
      await ossPost("/api/ingest/pause");
      if (this.health) this.health.ingest_paused = true;
      this.notify("Ingest paused", "warn");
    },

    async resumeIngest() {
      await ossPost("/api/ingest/resume");
      if (this.health) this.health.ingest_paused = false;
      this.notify("Ingest resumed", "ok");
    },

    async runIngestNow() {
      this.loading = true;
      try {
        await ossPost("/api/ingest/run");
        this.notify("Ingest cycle triggered", "ok");
        setTimeout(() => this._loadHealth(), 3000);
      } finally {
        this.loading = false;
      }
    },

    async addTopic() {
      const tag = this.addTopicInput.trim().toLowerCase().replace(/\s+/g, "-");
      if (!tag) return;
      try {
        await ossPost("/admin/add_topic", { tag, analyst_token: TOKEN });
        this.notify(`Topic "${tag}" added`, "ok");
        this.addTopicInput = "";
        this.addTopicOpen  = false;
        await this._loadTopics();
      } catch (e) {
        this.notify(e.message, "danger");
      }
    },

    // ── Triage ────────────────────────────────────────────────────────────────

    async loadStaged() {
      const q = this.triageTopic
        ? `?topic=${encodeURIComponent(this.triageTopic)}&limit=100`
        : "?limit=100";
      const d    = await ossGet(`/api/feed${q}`);
      const all  = d.claims ?? (Array.isArray(d) ? d : []);
      this.staged      = all.filter(c => c.trust_level === "STAGED");
      this.stagedTotal = this.staged.length;
      this.triageSel   = [];
    },

    toggleSel(id) {
      const i = this.triageSel.indexOf(id);
      if (i >= 0) this.triageSel.splice(i, 1); else this.triageSel.push(id);
    },

    isSel(id) { return this.triageSel.includes(id); },

    selectAll()    { this.triageSel = this.staged.map(c => c.id); },
    clearSel()     { this.triageSel = []; },

    async bulkPromote() {
      if (!this.triageSel.length) return;
      const ids   = [...this.triageSel];
      const topic = this.triageTopic || null;
      await ossPost("/admin/bulk_promote", { ids, topic });
      this.notify(`${ids.length} claims promoted`, "ok");
      await this.loadStaged();
    },

    // ── Ledger ────────────────────────────────────────────────────────────────

    async loadLedger() {
      const q = this.ledgerTopic
        ? `?topic=${encodeURIComponent(this.ledgerTopic)}&limit=100`
        : "?limit=100";
      const d        = await ossGet(`/api/feed${q}`);
      const all      = d.claims ?? (Array.isArray(d) ? d : []);
      this.ledger      = all.filter(c => c.trust_level === "PROMOTED");
      this.ledgerTotal = this.ledger.length;
    },

    // ── Analysis ──────────────────────────────────────────────────────────────

    async loadAnalysis() {
      if (!this.analysisTopic) return;
      const since72h = new Date(Date.now() - 72 * 3600_000).toISOString();
      const topic    = this.analysisTopic;

      const [dr, si, ac, co] = await Promise.allSettled([
        ossPost("/api/drift",          { topic, since: since72h }),
        ossPost("/api/silence",        { topic, since: since72h }),
        ossPost("/api/activation",     { topic, since: since72h }),
        ossPost("/api/contradictions", { topic, analyst_token: TOKEN }),
      ]);

      this.drift         = dr.status === "fulfilled" ? dr.value : null;
      this.silence       = si.status === "fulfilled" ? si.value : null;
      this.activation    = ac.status === "fulfilled" ? ac.value : null;
      this.contradictions = co.status === "fulfilled"
        ? (co.value.pairs ?? [])
        : [];
    },

    // ── Hypotheses ────────────────────────────────────────────────────────────

    async loadHypotheses() {
      let url = `/api/hypotheses?status=${this.hypStatus}&limit=50`;
      const d = await ossGet(url);
      this.hypotheses = d.hypotheses ?? (Array.isArray(d) ? d : []);
    },

    async setHypStatus(s) {
      this.hypStatus = s;
      await this.loadHypotheses();
    },

    async promoteHyp(id) {
      await ossPost(`/api/hypothesis/${id}/promote`);
      this.notify(`Hypothesis #${id} promoted`, "ok");
      await this.loadHypotheses();
    },

    async falsifyHyp(id) {
      const ev = window.prompt(`Falsification evidence for hypothesis #${id}:`);
      if (!ev) return;
      await ossPost(`/api/hypothesis/${id}/falsify`, { evidence: ev });
      this.notify(`Hypothesis #${id} falsified`, "warn");
      await this.loadHypotheses();
    },

    async suspendHyp(id) {
      await ossPost(`/api/hypothesis/${id}/suspend`, { reason: "Analyst suspension" });
      this.notify(`Hypothesis #${id} suspended`, "info");
      await this.loadHypotheses();
    },

    // ── Predict (SWARMFISH via OSS proxy) ─────────────────────────────────────

    async runPredict() {
      if (!this.predictTopic) { this.notify("Select a topic first", "warn"); return; }
      this.swfRunning   = true;
      this.swfProfiles  = [];
      this.swfConsensus = null;
      this.error        = null;
      try {
        const d = await ossPost("/api/swarmfish/predict", { topic: this.predictTopic });
        this.swfProfiles  = d.profiles   ?? [];
        this.swfConsensus = d.consensus  ?? null;
      } catch (e) {
        this.error = e.message;
      } finally {
        this.swfRunning = false;
      }
    },

    // ── Helpers ───────────────────────────────────────────────────────────────

    timeSince(ts) {
      if (!ts) return "never";
      const secs = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
      if (secs < 60)   return `${secs}s ago`;
      if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
      if (secs < 86400) return `${Math.floor(secs / 3600)}h ${Math.floor((secs % 3600) / 60)}m ago`;
      return `${Math.floor(secs / 86400)}d ago`;
    },

    fmtDate(ts) {
      if (!ts) return "—";
      const d = new Date(ts);
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric" })
        + " "
        + d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
    },

    fmtConf(v) {
      return v != null ? (v * 100).toFixed(0) + "%" : "—";
    },

    confBarW(v) {
      return v != null ? Math.round(v * 100) + "%" : "0%";
    },

    techniqueLabel(t) {
      const map = {
        neutral_framing:  "neutral",
        loaded_language:  "loaded",
        false_balance:    "false-bal",
        selective_omit:   "omit",
        fear_appeal:      "fear",
        appeal_to_authority: "authority",
        unclassified:     "unclassed",
      };
      return map[t] ?? t ?? "—";
    },

    notify(msg, type = "info") {
      clearTimeout(this._toastTimer);
      this.toast = { msg, type };
      this._toastTimer = setTimeout(() => { this.toast = null; }, 3500);
    },
  };
}
