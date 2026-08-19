/**
 * sys-monitor-store.js — Alpine store for the SYS·MONITOR right-canvas surface.
 *
 * Mirrors the Intelligence panel pattern: the registrar creates this store once
 * (Alpine is guaranteed available at registration), the content HTML binds to
 * $store.sysMon with real directives — no x-data hydration race.
 *
 * State is a LIVE SYNTHETIC telemetry stream for now (design shell). M2 swaps the
 * synthetic tick for real endpoints:  GPU metrics need a host-side bridge (the
 * container can't see the 3090); cycle/domain/role come from /api/office_feed.
 * Until then the panel is clearly marked SAMPLE and never dresses fake as real.
 */
export function createSysMonStore() {
  const AMP   = { tput: 6, vram: 2.4, temp: 1.8, draft: 2.6 };
  const CLAMP = { tput: [70, 158], vram: [38, 98], temp: [52, 86], draft: [80, 99] };

  return {
    // ---- lifecycle (driven by the registrar's open()/close()) ----
    _timer: null, _seeded: false, live_since: null,
    start() {
      if (!this._seeded) this._seed();
      this._tick();
      if (!this._timer) this._timer = setInterval(() => this._tick(), 1000);
    },
    stop() { if (this._timer) { clearInterval(this._timer); this._timer = null; } },

    // ---- state ----
    reduced: false,
    clock: '--:--:--',
    armed: 'BUILD',
    stackState: { domain: 'investigation', role: 'ANALYST', gate: 'PASS' },
    live: { tput: 112, vram: 71, temp: 70, draft: 92, cycles: 1344 },
    buf: {},

    metrics: [
      { key: 'tput', label: 'Throughput', jp: '処理速度', unit: 'tok/s', min: 60, max: 160, normal: [95, 132],
        title: 'Throughput', desc: 'Decode speed at the inference head. Normal band 95–132 tok/s for Ornith-35B at 150K ctx.',
        exps: [['peak · 1h', '147'], ['p50 · session', '118'], ['history', '60s']] },
      { key: 'draft', label: 'Draft Accept', jp: '採択率', unit: '%', min: 70, max: 100, normal: [85, 97],
        title: 'Draft Acceptance', desc: 'Fraction of speculatively-drafted tokens the target accepts. Below 85% erodes the speedup.',
        exps: [['by depth', '4'], ['rejections', '112'], ['history', '60s']] },
      { key: 'vram', label: 'VRAM', jp: '記憶', unit: '%', min: 0, max: 100, normal: [40, 80],
        title: 'VRAM Commitment', desc: '3090 memory in use. >90% risks evicting Ornith’s KV cache — the atmosphere layer is gated on this.',
        exps: [['KV cache', '11.2G'], ['weights', '5.1G'], ['headroom', '6.6G']] },
      { key: 'temp', label: 'GPU Thermal', jp: '温度', unit: '°C', min: 40, max: 90, normal: [55, 75],
        title: 'GPU Thermal', desc: 'Core temperature under sustained inference. Throttle risk above 83°C.',
        exps: [['fan', '62%'], ['throttle pt', '83°'], ['history', '60s']] },
    ],

    traj: { goal: 'deepen semiconductors → STABLE', steps: [
      { lbl: 'frame', state: 'done' }, { lbl: 'collect', state: 'done' }, { lbl: 'cross-ref', state: 'now' },
      { lbl: 'verify', state: '' }, { lbl: 'promote', state: '' }] },

    alerts: [
      { id: 1, sev: 'warn',  ic: '▲', t: 'GPU thermal rising —', d: '70°C, band ceiling 75°C. Watching.' },
      { id: 2, sev: 'info',  ic: '■', t: 'Role switch —',        d: 'org kernel → ANALYST for investigation.' },
      { id: 3, sev: 'info',  ic: '■', t: 'BST domain —',         d: 'investigation (0.91), slot: semiconductors.' },
      { id: 4, sev: 'trace', ic: '·', t: 'evidence ledger',      d: '+3 · EI verdict: clean.' },
      { id: 5, sev: 'trace', ic: '·', t: 'memory classify',      d: '2 stored · 1 deduped.' },
    ],

    tree: [
      { id: 'wiki', label: 'WIKI', meta: 339, open: true, children: [
        { id: 'semi', label: 'semiconductors', meta: 'STABLE', title: 'SEMICONDUCTORS', sub: 'WIKI · STABLE · rev 7',
          body: 'Cross-referenced field record. Rare-earth supply chains constrain advanced-node fabrication; <em>export-control regimes</em> are the dominant near-term variable. Linked cycles: BUILD #1344, #1331.',
          expansions: [['linked cycles', 2], ['sources', 9], ['contradictions', 0], ['related', 4]] },
        { id: 'horm', label: 'iran-hormuz', meta: 'DRAFT', title: 'IRAN · HORMUZ', sub: 'WIKI · DRAFT · rev 2',
          body: 'Strait-of-Hormuz transit risk. <em>Falsifiable forecast</em> open in SWARMFISH; resolves on the dated question at deadline.',
          expansions: [['forecasts', 1], ['sources', 14], ['contradictions', 2]] },
        { id: 'rare', label: 'rare-earths', meta: 'STABLE', title: 'RARE EARTHS', sub: 'WIKI · STABLE · rev 4',
          body: 'Refining concentration is the choke point, not raw reserves. <em>Downstream separation capacity</em> dominates.',
          expansions: [['sources', 11], ['related', 3]] },
      ] },
      { id: 'field', label: 'FIELD REPORTS', meta: 88, open: false, children: [
        { id: 'fr1', label: '2026-07-04 · grid', title: 'FIELD REPORT · GRID', sub: 'REPORT · 2026-07-04',
          body: 'EXPLORE cycle #1344. Grid-stability signals cross-referenced against the claim ledger.',
          expansions: [['claims', 6], ['promoted', 2]] },
      ] },
      { id: 'skills', label: 'SKILLS', meta: 14, leaf: true, title: 'SKILLS', sub: 'PROCEDURAL · 14 captured',
        body: 'Procedural skills promoted from field reports. Each carries a <em>.memory.md</em> the agent meets before repeating a task.',
        expansions: [['captured', 14], ['fired · wk', 7]] },
    ],

    focus: { id: 'semi', kind: 'wiki', title: 'SEMICONDUCTORS', sub: 'WIKI · STABLE · rev 7',
      body: 'Cross-referenced field record. Rare-earth supply chains constrain advanced-node fabrication; <em>export-control regimes</em> are the dominant near-term variable. Linked cycles: BUILD #1344, #1331.',
      expansions: [['linked cycles', 2], ['sources', 9], ['contradictions', 0], ['related', 4]],
      crumbs: ['OFFICE', 'KNOWLEDGE', 'SEMICONDUCTORS'] },

    // ---- internals ----
    _seed() {
      const now = Date.now() / 1000;
      this.metrics.forEach(m => {
        const ys = [];
        for (let i = 0; i < 60; i++) ys.push(this.live[m.key] + (Math.random() - 0.5) * AMP[m.key]);
        this.buf[m.key] = ys;
      });
      this._seeded = true;
      this.live_since = now;
    },
    _tick() {
      this.metrics.forEach(m => {
        const b = CLAMP[m.key];
        const nv = Math.max(b[0], Math.min(b[1], this.live[m.key] + (Math.random() - 0.5) * AMP[m.key]));
        this.live[m.key] = nv;
        const buf = this.buf[m.key]; buf.push(nv); if (buf.length > 60) buf.shift();
        m.sev = nv > m.max * 0.94 ? 'crit' : (nv > m.normal[1] * 1.02 || nv < m.normal[0] * 0.98) ? 'warn' : '';
      });
      if (Math.random() < 0.06) this.live.cycles++;
      const d = new Date();
      this.clock = d.toTimeString().slice(0, 8);
    },

    // ---- view helpers (called from bindings) ----
    fmt(m) { return Math.round(this.live[m.key]); },
    spark(m) {
      const b = this.buf[m.key] || []; const n = b.length; if (!n) return '';
      return b.map((v, i) => {
        const x = (i / (n - 1)) * 100;
        const y = 26 - ((v - m.min) / (m.max - m.min)) * 26;
        return x.toFixed(1) + ',' + Math.max(1, Math.min(25, y)).toFixed(1);
      }).join(' ');
    },
    bandNormL(m) { return (m.normal[0] - m.min) / (m.max - m.min) * 100; },
    bandNormW(m) { return (m.normal[1] - m.normal[0]) / (m.max - m.min) * 100; },
    bandMark(m) { return Math.max(0, Math.min(100, (this.live[m.key] - m.min) / (m.max - m.min) * 100)); },
    deltaTxt(m) { const b = this.buf[m.key]; if (!b || b.length < 11) return ''; const d = b[b.length - 1] - b[b.length - 11]; return (d > 0 ? '▲ ' : d < 0 ? '▼ ' : '■ ') + Math.abs(d).toFixed(1); },
    deltaCls(m) { const b = this.buf[m.key]; if (!b || b.length < 11) return 'flat'; const d = b[b.length - 1] - b[b.length - 11]; return d > 0.4 ? 'up' : d < -0.4 ? 'down' : 'flat'; },

    pick(n) {
      this.focus = { id: n.id, kind: 'wiki', title: n.title, sub: n.sub, body: n.body,
        expansions: n.expansions || [], crumbs: ['OFFICE', 'KNOWLEDGE', n.title] };
    },
    pickMetric(m) {
      this.focus = { id: m.key, kind: 'metric', title: m.title, sub: 'LIVE METRIC · ' + m.unit, body: m.desc,
        expansions: m.exps || [], crumbs: ['OFFICE', 'TELEMETRY', m.title.toUpperCase()] };
    },
  };
}
