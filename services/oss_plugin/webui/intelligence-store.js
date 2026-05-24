/**
 * intelligence-store.js — Alpine store for the Intelligence Panel
 *
 * Uses A0's fetchApi (CSRF token auth, same-origin) — no hardcoded tokens.
 * All endpoints hit the V2 plugin API at /api/plugins/oss/.
 */

import { fetchApi } from "/js/api.js";

const OSS = "/api/plugins/oss";

async function ossGet(path, body = {}) {
  const r = await fetchApi(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(body),
  });
  if (!r || !r.ok) throw new Error(`OSS ${r?.status ?? "?"} — ${path}`);
  return r.json();
}

async function ossPost(path, body = {}) {
  const r = await fetchApi(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(body),
  });
  if (!r || !r.ok) throw new Error(`OSS ${r?.status ?? "?"} — ${path}`);
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
    triageSel:     [],

    // ── Ledger tab ───────────────────────────────────────────────────────────
    ledger:      [],
    ledgerTopic: "",
    ledgerTotal: 0,

    // ── Analysis tab ─────────────────────────────────────────────────────────
    analysisTopic:  "",
    drift:          null,
    silence:        null,
    activation:     null,
    contradictions: [],

    // ── Hypotheses tab ───────────────────────────────────────────────────────
    hypotheses: [],
    hypStatus:  "ACTIVE",
    hypTopic:   "",

    // ── Predict tab ──────────────────────────────────────────────────────────
    predictTopic:    "",
    swfRunning:      false,
    swfProfiles:     [],
    swfConsensus:    null,
    swfSessions:     [],
    swfSessionsTotal: 0,

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    async connect() {
      this.connected = true;
      if (this._pollTimer) clearInterval(this._pollTimer);  // guard: re-open must not stack intervals
      await this.refresh();
      // Live auto-update: _tick refreshes health every cycle, and the visible
      // tab's data when the Intel surface is the active canvas tab.
      this._pollTimer = setInterval(() => this._tick(), 12_000);
    },

    disconnect() {
      this.connected = false;
      clearInterval(this._pollTimer);
      this._pollTimer = null;
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
          predict:    () => this.loadSwfSessions(),
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

      // Refresh tab data only while the Intel surface is actually visible —
      // avoids wasted calls when another canvas tab is open. Falls back to
      // page-visibility if the canvas store isn't reachable.
      let visible = true;
      try {
        const rc = (typeof Alpine !== "undefined") ? Alpine.store("rightCanvas") : null;
        visible = rc ? rc.isSurfaceVisible("intelligence") : !document.hidden;
      } catch (_) {}
      if (!visible) return;

      // Non-destructive auto-refresh of the visible tab (no loading skeleton).
      // Skip triage while items are selected (don't clear the user's checkboxes);
      // skip analysis (heavy, run on demand via the Analyze button).
      try {
        if (this.tab === "triage")          { if (this.triageSel.length === 0) await this.loadStaged(); }
        else if (this.tab === "ledger")     await this.loadLedger();
        else if (this.tab === "hypotheses") await this.loadHypotheses();
        else if (this.tab === "predict")    await this.loadSwfSessions();
        else if (this.tab === "status")     await this._loadSources();
      } catch (_) {}
    },

    // ── Health / Status ───────────────────────────────────────────────────────

    async _loadHealth() {
      this.health = await ossGet(`${OSS}/api_oss_health`);
    },

    async _loadTopics() {
      const d = await ossGet(`${OSS}/api_oss_topics`);
      this.topics = d.topics ?? (Array.isArray(d) ? d : []);
    },

    async _loadSources() {
      const d = await ossGet(`${OSS}/api_oss_sources`);
      this.sources = d.sources ?? (Array.isArray(d) ? d : []);
    },

    get ingestPaused()   { return this.health?.ingest_paused ?? true; },
    get claimsStaged()   { return this.health?.claims?.staged   ?? 0; },
    get claimsPromoted() { return this.health?.claims?.promoted ?? 0; },
    get sourcesCount()   { return this.health?.sources_count    ?? 0; },
    get hypothesisCount(){ return this.health?.hypothesis_count ?? 0; },

    get healthBadge() {
      if (!this.health) return "unknown";
      const { failing = 0, stale = 0 } = this.health.source_health ?? {};
      if (failing > 0) return "failing";
      if (stale   > 0) return "stale";
      return "ok";
    },

    async pauseIngest() {
      await ossPost(`${OSS}/api_oss_ingest`, { action: "pause" });
      if (this.health) this.health.ingest_paused = true;
      this.notify("Ingest paused", "warn");
    },

    async resumeIngest() {
      await ossPost(`${OSS}/api_oss_ingest`, { action: "resume" });
      if (this.health) this.health.ingest_paused = false;
      this.notify("Ingest resumed", "ok");
    },

    async runIngestNow() {
      this.loading = true;
      try {
        await ossPost(`${OSS}/api_oss_ingest`, { action: "run" });
        this.notify("Ingest cycle triggered", "ok");
        setTimeout(() => this._loadHealth(), 3000);
      } catch (e) {
        this.notify(e.message, "danger");
      } finally {
        this.loading = false;
      }
    },

    async addTopic() {
      const tag = this.addTopicInput.trim().toLowerCase().replace(/\s+/g, "-");
      if (!tag) return;
      try {
        await ossPost(`${OSS}/api_oss_add_topic`, { tag, display_name: tag });
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
      const body = { limit: 100 };
      if (this.triageTopic) body.topic = this.triageTopic;
      const d   = await ossGet(`${OSS}/api_oss_feed`, body);
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

    selectAll() { this.triageSel = this.staged.map(c => c.id); },
    clearSel()  { this.triageSel = []; },

    async bulkPromote() {
      if (!this.triageSel.length) return;
      const ids = [...this.triageSel];
      await Promise.all(ids.map(id =>
        ossPost(`${OSS}/api_oss_staging`, { action: "promote", claim_id: id })
      ));
      this.notify(`${ids.length} claims promoted`, "ok");
      await this.loadStaged();
    },

    // ── Ledger ────────────────────────────────────────────────────────────────

    async loadLedger() {
      const body = { limit: 100 };
      if (this.ledgerTopic) body.topic = this.ledgerTopic;
      const d    = await ossGet(`${OSS}/api_oss_feed`, body);
      const all  = d.claims ?? (Array.isArray(d) ? d : []);
      this.ledger      = all.filter(c => c.trust_level === "PROMOTED");
      this.ledgerTotal = this.ledger.length;
    },

    // ── Analysis ──────────────────────────────────────────────────────────────

    async loadAnalysis() {
      if (!this.analysisTopic) return;
      const since72h = new Date(Date.now() - 72 * 3600_000).toISOString();
      const topic    = this.analysisTopic;

      const [dr, si, ac, co] = await Promise.allSettled([
        ossPost(`${OSS}/api_oss_drift`,          { topic, since: since72h }),
        ossPost(`${OSS}/api_oss_silence`,        { topic, since: since72h }),
        ossPost(`${OSS}/api_oss_activation`,     { topic, since: since72h }),
        ossPost(`${OSS}/api_oss_contradictions`, { topic }),
      ]);

      this.drift          = dr.status === "fulfilled" ? dr.value : null;
      this.silence        = si.status === "fulfilled" ? si.value : null;
      this.activation     = ac.status === "fulfilled" ? ac.value : null;
      this.contradictions = co.status === "fulfilled"
        ? (co.value.pairs ?? [])
        : [];
    },

    // ── Hypotheses ────────────────────────────────────────────────────────────

    async loadHypotheses() {
      const d = await ossPost(`${OSS}/api_oss_hypotheses`, {
        action: "list",
        status: this.hypStatus,
        limit:  50,
      });
      this.hypotheses = d.hypotheses ?? (Array.isArray(d) ? d : []);
    },

    async setHypStatus(s) {
      this.hypStatus = s;
      await this.loadHypotheses();
    },

    async promoteHyp(id) {
      await ossPost(`${OSS}/api_oss_hypotheses`, { action: "promote", hypothesis_id: id });
      this.notify(`Hypothesis #${id} promoted`, "ok");
      await this.loadHypotheses();
    },

    async falsifyHyp(id) {
      const ev = window.prompt(`Falsification evidence for hypothesis #${id}:`);
      if (!ev) return;
      await ossPost(`${OSS}/api_oss_hypotheses`, { action: "falsify", hypothesis_id: id, evidence: ev });
      this.notify(`Hypothesis #${id} falsified`, "warn");
      await this.loadHypotheses();
    },

    // ── Predict (SWARMFISH committee) ─────────────────────────────────────────

    async loadSwfSessions() {
      try {
        const d = await ossPost("/api/plugins/swarmfish/api_swarmfish_sessions", { limit: 10 });
        this.swfSessions      = d.sessions ?? [];
        this.swfSessionsTotal = d.count    ?? 0;
      } catch (_) {
        this.swfSessions = [];
      }
    },

    async runPredict() {
      if (!this.predictTopic) { this.notify("Select a topic first", "warn"); return; }
      this.swfRunning   = true;
      this.swfProfiles  = [];
      this.swfConsensus = null;
      this.error        = null;
      try {
        const d = await ossPost("/api/plugins/swarmfish/api_swarmfish_predict", {
          question: this.predictTopic,
          domain:   "geopolitical",
        });
        this.swfProfiles  = d.assessments ?? [];
        this.swfConsensus = d.consensus   ?? null;
        this.notify("SWARMFISH committee complete", "ok");
        await this.loadSwfSessions();
      } catch (e) {
        this.error = e.message;
        this.notify(e.message, "danger");
      } finally {
        this.swfRunning = false;
      }
    },

    // ── Helpers ───────────────────────────────────────────────────────────────

    timeSince(ts) {
      if (!ts) return "never";
      const secs = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
      if (secs < 60)    return `${secs}s ago`;
      if (secs < 3600)  return `${Math.floor(secs / 60)}m ago`;
      if (secs < 86400) return `${Math.floor(secs / 3600)}h ${Math.floor((secs % 3600) / 60)}m ago`;
      return `${Math.floor(secs / 86400)}d ago`;
    },

    fmtDate(ts) {
      if (!ts) return "—";
      const d = new Date(ts);
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric" })
        + " " + d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
    },

    fmtConf(v)  { return v != null ? (v * 100).toFixed(0) + "%" : "—"; },
    confBarW(v) { return v != null ? Math.round(v * 100) + "%" : "0%"; },

    techniqueLabel(t) {
      const map = {
        neutral_framing: "neutral", loaded_language: "loaded",
        false_balance: "false-bal", selective_omit: "omit",
        fear_appeal: "fear", appeal_to_authority: "authority",
        unclassified: "unclassed",
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
