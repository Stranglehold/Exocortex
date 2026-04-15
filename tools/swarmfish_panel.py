"""
swarmfish_panel — SWARMFISH Interactive Panel
=============================================

Emits a fully interactive, self-contained SWARMFISH panel as an artifact.
Single Alpine.js root with 3 in-panel tabs — no agent round-trip to switch views.

Tabs:
  Sessions    — session browser with inline detail expansion + outcome logging
  Calibration — per-profile consensus weights and domain Brier scores
  Predict     — prediction form → full committee result with all profiles expandable

Args:
  view       (str): sessions | calibration | predict   (default: sessions)
  domain     (str): domain filter for sessions view (optional)
  session_id (str): pre-expand this session in sessions view (optional)
"""

from helpers.tool import Tool, Response

_API = "/api/plugins/swarmfish"

_STYLE = """<style>
.sf{font:12px/1.4 inherit;color:var(--color-text)}
.sf-hdr{display:flex;align-items:center;justify-content:space-between;padding:7px 12px;border-bottom:1px solid var(--color-border)}
.sf-title{font-size:13px;font-weight:600}
.sf-badge{font-size:10px;padding:2px 8px;border-radius:10px;background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text-muted)}
.sf-tabs{display:flex;gap:0;padding:3px 8px 0;border-bottom:1px solid var(--color-border);overflow-x:auto;flex-shrink:0}
.sf-tab{background:none;border:none;border-bottom:2px solid transparent;color:var(--color-text-muted);padding:4px 9px;cursor:pointer;font-size:11px;margin-bottom:-1px;white-space:nowrap;font:inherit}
.sf-tab:hover{color:var(--color-text)}
.sf-tab-on{color:var(--color-text);border-bottom-color:var(--color-primary,#5050c0);font-weight:600}
.sf-body{padding:8px 12px;overflow-y:auto;max-height:520px}
.sf-row{display:grid;align-items:center;gap:6px;padding:4px 6px;border-radius:4px;cursor:pointer}
.sf-row:hover,.sf-row-sel{background:var(--color-background-hover)}
.sf-row-head{font-size:10px;font-weight:600;text-transform:uppercase;color:var(--color-text-muted);padding:2px 6px;border-bottom:1px solid var(--color-border);margin-bottom:3px}
.sf-id{font-family:monospace;font-size:10px;color:var(--color-text-muted)}
.sf-domain{font-size:10px;padding:1px 6px;border-radius:10px;background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text-muted);white-space:nowrap}
.sf-q{font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sf-conf{font-size:12px;font-weight:700;text-align:right}
.sf-high{color:#4caf50}.sf-mid{color:#ff9800}.sf-low{color:#f44336}
.sf-btn{background:none;border:1px solid var(--color-border);color:var(--color-text-muted);padding:2px 8px;border-radius:4px;cursor:pointer;font-size:11px;font:inherit}
.sf-btn:hover{background:var(--color-background-hover);color:var(--color-text)}
.sf-btn-on{background:var(--color-primary,#5050c0)!important;border-color:transparent!important;color:#fff!important}
.sf-detail{background:var(--color-message-bg);border:1px solid var(--color-border);border-radius:4px;margin:2px 0 8px 2px;padding:8px 10px}
.sf-brief{font-size:11px;line-height:1.5;white-space:pre-wrap;color:var(--color-text-muted);margin-bottom:6px}
.sf-sec{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--color-text-muted);padding:5px 0 3px;border-top:1px solid var(--color-border);margin-top:4px}
.sf-sec-first{border-top:none;margin-top:0}
.sf-prow{display:grid;grid-template-columns:140px 46px 1fr;gap:6px;align-items:start;padding:3px 4px;border-radius:3px;font-size:11px;cursor:pointer}
.sf-prow:hover{background:var(--color-background-hover)}
.sf-pname{font-weight:500;display:flex;align-items:center;gap:3px}
.sf-psum{color:var(--color-text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sf-out{display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:6px 0;border-top:1px solid var(--color-border);margin-top:6px}
.sf-inp{background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:3px 8px;border-radius:4px;font-size:11px;flex:1;min-width:0;font:inherit}
.sf-msg{font-size:11px;color:var(--color-text-muted);padding-top:3px}
.sf-load{padding:16px;text-align:center;color:var(--color-text-muted);font-size:11px}
.sf-err{padding:6px;color:#f44336;font-size:11px}
.sf-calr{display:grid;gap:8px;align-items:center;padding:3px 6px;border-radius:3px;font-size:11px}
.sf-calr:hover{background:var(--color-background-hover)}
.sf-frow{display:flex;flex-direction:column;gap:4px;margin-bottom:8px}
.sf-lbl{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--color-text-muted)}
.sf-ta{width:100%;box-sizing:border-box;background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:5px 8px;border-radius:4px;font-size:11px;font-family:inherit;resize:vertical}
.sf-sel{background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:3px 8px;border-radius:4px;font-size:11px;font:inherit}
.sf-result{background:var(--color-message-bg);border:1px solid var(--color-border);border-radius:4px;padding:10px;margin-top:8px;font-size:11px;line-height:1.5;white-space:pre-wrap;color:var(--color-text-muted)}
</style>"""

_PROFILE_NAMES = [
    "Base Rate Analyst", "Contrarian", "Historian",
    "Reflexivity Modeler", "Decomposer", "Network Analyst",
    "Sentiment Decoder", "Risk Manager",
]

# ── JavaScript data object ─────────────────────────────────────────────────────

_JS_DATA = """
{
  view: '__VIEW__',
  _ld: {},
  go(v) {
    this.view = v;
    if (!this._ld[v]) {
      this._ld[v] = 1;
      const fn = this['_i_' + v];
      if (fn) fn.call(this);
    }
  },

  // ── Shared helpers ──────────────────────────────────────────────────────────
  confCls(c) { return c == null ? '' : c >= 0.7 ? 'sf-high' : c >= 0.45 ? 'sf-mid' : 'sf-low'; },
  pct(c) { return c != null ? Math.round(c * 100) + '%' : '—'; },

  // ── Sessions (prefix: ss) ───────────────────────────────────────────────────
  ssSessions: [], ssDomain: '__DOMAIN__', ssL: true, ssE: null,
  ssSel: '__PRESEL__', ssDetail: null, ssDetL: false, ssDetE: null, ssLevel: 2,
  ssOutVal: null, ssOutNotes: '', ssOutSaving: false, ssOutMsg: null,
  async _i_sessions() {
    this.ssL = true; this.ssE = null;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_swarmfish_sessions',
        {limit: 40, domain: this.ssDomain || undefined});
      if (!r.ok) throw new Error(r.error);
      this.ssSessions = r.sessions || [];
    } catch(e) { this.ssE = String(e); }
    this.ssL = false;
    if (this.ssSel) this.ssLoadDetail(this.ssSel);
  },
  async ssToggle(id) {
    if (this.ssSel === id) { this.ssSel = null; this.ssDetail = null; return; }
    this.ssSel = id;
    await this.ssLoadDetail(id);
  },
  async ssLoadDetail(id) {
    this.ssDetail = null; this.ssDetL = true; this.ssDetE = null;
    this.ssOutVal = null; this.ssOutNotes = ''; this.ssOutMsg = null;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_swarmfish_session',
        {session_id: id, level: this.ssLevel});
      if (!r.ok) throw new Error(r.error);
      this.ssDetail = r;
    } catch(e) { this.ssDetE = String(e); }
    this.ssDetL = false;
  },
  async ssSetLevel(l) { this.ssLevel = l; if (this.ssSel) await this.ssLoadDetail(this.ssSel); },
  async ssLogOutcome() {
    if (this.ssOutVal == null) return;
    this.ssOutSaving = true; this.ssOutMsg = null;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_swarmfish_outcome',
        {session_id: this.ssSel, outcome: parseFloat(this.ssOutVal), notes: this.ssOutNotes || null});
      this.ssOutMsg = r.ok ? '✓ Outcome logged' : 'Error: ' + (r.error || 'unknown');
    } catch(e) { this.ssOutMsg = String(e); }
    this.ssOutSaving = false;
  },

  // ── Calibration (prefix: cal) ───────────────────────────────────────────────
  calData: null, calL: true, calE: null,
  async _i_calibration() {
    this.calL = true; this.calE = null;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_swarmfish_calibration', {});
      if (!r.ok) throw new Error(r.error);
      this.calData = r;
    } catch(e) { this.calE = String(e); }
    this.calL = false;
  },
  calBrierCls(b) { return b == null ? '' : b <= 0.10 ? 'sf-high' : b <= 0.20 ? 'sf-mid' : 'sf-low'; },
  calWt(pw) { return pw && pw.default != null ? pw.default.toFixed(2) : '1.00'; },

  // ── Predict (prefix: pr) ────────────────────────────────────────────────────
  prQ: '', prDomain: 'general', prCtx: '',
  prCommittee: [], prAllProfiles: __PROFILES__,
  prL: false, prE: null, prResult: null, prSessId: null,
  prOutVal: null, prOutNotes: '', prOutSaving: false, prOutMsg: null,
  prExpanded: null,
  prSavedCommittee: [], prSavedDomain: 'general', prCommitteeMsg: null,
  _i_predict() {
    try {
      const saved = JSON.parse(localStorage.getItem('sf_committee') || 'null');
      if (saved) { this.prSavedCommittee = saved.profiles || []; this.prSavedDomain = saved.domain || 'general'; }
    } catch {}
  },
  prToggleProfile(p) {
    const i = this.prCommittee.indexOf(p);
    if (i === -1) this.prCommittee.push(p); else this.prCommittee.splice(i, 1);
  },
  prSaveCommittee() {
    localStorage.setItem('sf_committee', JSON.stringify({profiles: this.prCommittee, domain: this.prDomain}));
    this.prSavedCommittee = [...this.prCommittee]; this.prSavedDomain = this.prDomain;
    this.prCommitteeMsg = 'Saved'; setTimeout(() => this.prCommitteeMsg = null, 2000);
  },
  prLoadCommittee() {
    this.prCommittee = [...this.prSavedCommittee]; this.prDomain = this.prSavedDomain;
    this.prCommitteeMsg = 'Loaded'; setTimeout(() => this.prCommitteeMsg = null, 2000);
  },
  prExpand(n) { this.prExpanded = this.prExpanded === n ? null : n; },
  async prSubmit() {
    if (!this.prQ.trim()) return;
    this.prL = true; this.prE = null; this.prResult = null; this.prSessId = null;
    this.prOutVal = null; this.prOutNotes = ''; this.prOutMsg = null; this.prExpanded = null;
    try {
      const payload = {
        question: this.prQ, domain: this.prDomain,
        context: this.prCtx || undefined,
        committee: this.prCommittee.length ? this.prCommittee : undefined,
      };
      const r = await ExoArtifact.fetchJson('_API_/api_swarmfish_predict', payload);
      if (!r.ok) throw new Error(r.error || 'Prediction failed');
      this.prSessId = r.session_id; this.prResult = r;
    } catch(e) { this.prE = String(e); }
    this.prL = false;
  },
  async prLogOutcome() {
    if (this.prOutVal == null || !this.prSessId) return;
    this.prOutSaving = true; this.prOutMsg = null;
    try {
      const r = await ExoArtifact.fetchJson('_API_/api_swarmfish_outcome',
        {session_id: this.prSessId, outcome: parseFloat(this.prOutVal), notes: this.prOutNotes || null});
      this.prOutMsg = r.ok ? '✓ Logged' : 'Error: ' + (r.error || '?');
    } catch(e) { this.prOutMsg = String(e); }
    this.prOutSaving = false;
  },
  get prProfiles() {
    if (!this.prResult) return [];
    return (this.prResult.profiles && this.prResult.profiles.length)
      ? this.prResult.profiles
      : (this.prResult.dissenters || []);
  },
  get prHasFullCommittee() {
    return this.prResult && this.prResult.profiles && this.prResult.profiles.length > 0;
  },

  // ── Init ────────────────────────────────────────────────────────────────────
  init() { this._ld = {}; this.go(this.view); }
}
"""


def _swarmfish_panel_html(
    initial_view: str = "sessions",
    domain: str | None = None,
    session_id: str | None = None,
) -> str:
    profiles_json = str(_PROFILE_NAMES).replace("'", '"')
    js = (
        _JS_DATA
        .replace("__VIEW__", initial_view)
        .replace("__DOMAIN__", domain or "")
        .replace("'__PRESEL__'", f'"{session_id}"' if session_id else "null")
        .replace("__PROFILES__", profiles_json)
        .replace("_API_", _API)
    )

    return f"""{_STYLE}
<div class="sf" x-data="{js}" x-init="init()">

  <!-- ── Header ─────────────────────────────────────────────────────────── -->
  <div class="sf-hdr">
    <span class="sf-title">SWARMFISH Forecast Panel</span>
    <div style="display:flex;gap:6px;align-items:center;">
      <span class="sf-badge" x-show="calData"
        x-text="calData?(calData.session_count+' sessions, '+calData.scored_session_count+' scored'):''"></span>
      <button class="sf-btn" style="font-size:11px;padding:2px 7px;"
        @click="_ld[view]=0;go(view)" title="Refresh current view">↻</button>
    </div>
  </div>

  <!-- ── Tab bar ────────────────────────────────────────────────────────── -->
  <div class="sf-tabs">
    <button class="sf-tab" :class="view==='sessions'?'sf-tab-on':''" @click="go('sessions')">Sessions</button>
    <button class="sf-tab" :class="view==='calibration'?'sf-tab-on':''" @click="go('calibration')">Calibration</button>
    <button class="sf-tab" :class="view==='predict'?'sf-tab-on':''" @click="go('predict')">Predict</button>
  </div>

  <!-- ── Body ───────────────────────────────────────────────────────────── -->
  <div class="sf-body">

    <!-- ════════════════════════════════════════════════════════════════════
         SESSIONS
         ════════════════════════════════════════════════════════════════════ -->
    <div x-show="view==='sessions'">
      <div x-show="ssL" class="sf-load">Loading sessions…</div>
      <div x-show="!ssL&&ssE" class="sf-err" x-text="ssE"></div>
      <div x-show="!ssL&&!ssE">

        <!-- Filters -->
        <div style="display:flex;gap:6px;align-items:center;padding:5px 0 6px;border-bottom:1px solid var(--color-border);">
          <select class="sf-sel" x-model="ssDomain" @change="ssSel=null;ssDetail=null;_ld['sessions']=0;_i_sessions()">
            <option value="">all domains</option>
            <option value="geopolitical">geopolitical</option>
            <option value="economic">economic</option>
            <option value="military">military</option>
            <option value="general">general</option>
          </select>
          <span style="flex:1;font-size:10px;color:var(--color-text-muted);">
            <span x-text="ssSessions.length"></span> session(s)
          </span>
          <button class="sf-btn" style="font-size:11px;padding:2px 7px;"
            @click="ssSel=null;ssDetail=null;_ld['sessions']=0;_i_sessions()">↻</button>
        </div>

        <!-- Empty -->
        <div x-show="ssSessions.length===0" style="padding:12px 6px;color:var(--color-text-muted);font-size:11px;">
          No sessions yet — run a prediction to begin.
        </div>

        <!-- Column header -->
        <div x-show="ssSessions.length>0" class="sf-row sf-row-head"
          style="grid-template-columns:56px 86px 1fr 50px;">
          <span>ID</span><span>Domain</span><span>Question</span><span>Conf</span>
        </div>

        <!-- Session rows -->
        <template x-for="s in ssSessions" :key="s.id">
          <div>
            <div class="sf-row" :class="ssSel===s.id?'sf-row-sel':''"
              style="grid-template-columns:56px 86px 1fr 50px;"
              @click="ssToggle(s.id)">
              <span class="sf-id" x-text="s.id.slice(0,8)"></span>
              <span class="sf-domain" x-text="s.domain"></span>
              <span class="sf-q" x-text="s.question"></span>
              <span class="sf-conf" :class="confCls(s.consensus_confidence)"
                x-text="pct(s.consensus_confidence)"></span>
            </div>

            <!-- Expanded detail -->
            <div x-show="ssSel===s.id">
              <div x-show="ssDetL" class="sf-load" style="padding:8px;">Loading detail…</div>
              <div x-show="!ssDetL&&ssDetE" class="sf-err" x-text="ssDetE"></div>
              <div x-show="!ssDetL&&!ssDetE&&ssDetail" class="sf-detail">

                <!-- Consensus summary -->
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                  <div style="font-size:11px;color:var(--color-text-muted);">
                    <span x-text="ssDetail&&ssDetail.domain"></span>
                    <template x-if="ssDetail&&ssDetail.consensus_confidence!=null">
                      <span> · Consensus:
                        <strong :class="confCls(ssDetail&&ssDetail.consensus_confidence)"
                          x-text="ssDetail&&pct(ssDetail.consensus_confidence)"></strong>
                      </span>
                    </template>
                    <template x-if="ssDetail&&ssDetail.consensus_range_low!=null">
                      <span style="font-size:10px;">
                        (<span x-text="ssDetail&&pct(ssDetail.consensus_range_low)"></span>–<span
                          x-text="ssDetail&&pct(ssDetail.consensus_range_high)"></span>)
                      </span>
                    </template>
                    <template x-if="ssDetail&&ssDetail.meta_confidence">
                      <span style="font-size:10px;"> · <span x-text="ssDetail&&ssDetail.meta_confidence"></span></span>
                    </template>
                  </div>
                  <div style="display:flex;gap:4px;">
                    <template x-for="l in [1,2,3]" :key="l">
                      <button class="sf-btn" :class="ssLevel===l?'sf-btn-on':''"
                        @click.stop="ssSetLevel(l)" x-text="'L'+l"></button>
                    </template>
                  </div>
                </div>

                <!-- Brief -->
                <div x-show="ssDetail&&ssDetail.operator_brief" class="sf-brief"
                  x-text="ssDetail&&(ssDetail.operator_brief||'').slice(0,600)"></div>

                <!-- Profiles -->
                <div class="sf-sec">Profiles (Level <span x-text="ssLevel"></span>)</div>
                <template x-for="p in (ssDetail&&ssDetail.profiles||[])" :key="p.assessment_id||p.profile_name">
                  <div class="sf-prow" @click.stop="ssExpId=ssExpId===p.profile_name?null:p.profile_name">
                    <span class="sf-pname">
                      <span style="font-size:9px;color:var(--color-text-muted);"
                        x-text="(ssDetail&&ssDetail._ssExpId===p.profile_name)?'▼':'▶'"></span>
                      <span x-text="p.profile_name"></span>
                      <span x-show="p.confidence_capped" style="font-size:9px;color:var(--color-text-muted);"> ⚠</span>
                    </span>
                    <span class="sf-conf" :class="confCls(p.confidence)"
                      x-text="p.error?'ERR':pct(p.confidence)"></span>
                    <span class="sf-psum" x-text="p.error||p.reasoning_summary||p.prediction||''"></span>
                  </div>
                </template>

                <!-- Outcome logging -->
                <div class="sf-out">
                  <span style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--color-text-muted);flex-shrink:0;">Outcome:</span>
                  <template x-for="o in [['Wrong','0'],['Partial','0.5'],['Correct','1']]" :key="o[1]">
                    <button class="sf-btn" :class="ssOutVal===o[1]?'sf-btn-on':''"
                      @click.stop="ssOutVal=o[1]" x-text="o[0]"></button>
                  </template>
                  <input class="sf-inp" placeholder="notes (optional)"
                    x-model="ssOutNotes" @click.stop>
                  <button class="sf-btn" :class="ssOutVal!=null?'sf-btn-on':''"
                    :disabled="ssOutVal==null||ssOutSaving"
                    @click.stop="ssLogOutcome()" x-text="ssOutSaving?'…':'Log'"></button>
                </div>
                <div x-show="ssOutMsg" class="sf-msg" x-text="ssOutMsg"></div>

              </div>
            </div>
          </div>
        </template>

      </div>
    </div><!-- /sessions -->


    <!-- ════════════════════════════════════════════════════════════════════
         CALIBRATION
         ════════════════════════════════════════════════════════════════════ -->
    <div x-show="view==='calibration'">
      <div x-show="calL" class="sf-load">Loading calibration…</div>
      <div x-show="!calL&&calE" class="sf-err" x-text="calE"></div>
      <div x-show="!calL&&!calE&&calData">

        <!-- Consensus weights -->
        <div class="sf-sec sf-sec-first">Consensus Weights
          <span style="font-weight:400;text-transform:none;letter-spacing:0;font-size:10px;">
            (updates after 5+ scored sessions per profile)
          </span>
        </div>
        <div class="sf-calr sf-row-head" style="grid-template-columns:160px 52px 60px 1fr;">
          <span>Profile</span><span>Weight</span><span>Scored</span><span>Status</span>
        </div>
        <template x-for="p in (calData&&calData.profile_weights||[])" :key="p.name">
          <div class="sf-calr" style="grid-template-columns:160px 52px 60px 1fr;">
            <span x-text="p.name"></span>
            <span x-text="calWt(p.consensus_weight)"></span>
            <span x-text="p.n_scored||0"></span>
            <span style="color:var(--color-text-muted);font-size:10px;"
              x-text="(p.n_scored||0)>=5?'calibrated':'warming up'"></span>
          </div>
        </template>

        <!-- Domain Brier scores -->
        <div x-show="calData&&calData.calibration_by_domain&&calData.calibration_by_domain.length">
          <div class="sf-sec">Domain Brier Scores
            <span style="font-weight:400;text-transform:none;letter-spacing:0;font-size:10px;">
              (lower = more accurate; random baseline = 0.25)
            </span>
          </div>
          <div class="sf-calr sf-row-head" style="grid-template-columns:160px 90px 54px 40px;">
            <span>Profile</span><span>Domain</span><span>Brier</span><span>n</span>
          </div>
          <template x-for="row in (calData&&calData.calibration_by_domain||[])"
            :key="row.profile_name+row.domain">
            <div class="sf-calr" style="grid-template-columns:160px 90px 54px 40px;">
              <span x-text="row.profile_name"></span>
              <span class="sf-domain" x-text="row.domain"></span>
              <span :class="calBrierCls(row.avg_brier)"
                x-text="row.avg_brier!=null?row.avg_brier.toFixed(3):'n/a'"></span>
              <span x-text="row.n_predictions||0"></span>
            </div>
          </template>
        </div>

        <div x-show="!calData||!calData.calibration_by_domain||!calData.calibration_by_domain.length"
          style="padding:8px 6px;color:var(--color-text-muted);font-size:11px;">
          No Brier scores yet. Log session outcomes to build calibration history.
        </div>

      </div>
    </div><!-- /calibration -->


    <!-- ════════════════════════════════════════════════════════════════════
         PREDICT
         ════════════════════════════════════════════════════════════════════ -->
    <div x-show="view==='predict'">

      <!-- ── Prediction form (shown when no result) ── -->
      <div x-show="!prResult">

        <div class="sf-frow" style="margin-top:4px;">
          <label class="sf-lbl">Question <span style="color:#f44336;">*</span></label>
          <textarea class="sf-ta" rows="3"
            placeholder="What is the probability that…"
            x-model="prQ"></textarea>
        </div>

        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
          <div class="sf-frow" style="flex:0 0 auto;margin-bottom:0;">
            <label class="sf-lbl">Domain</label>
            <select class="sf-sel" x-model="prDomain">
              <option value="general">general</option>
              <option value="geopolitical">geopolitical</option>
              <option value="economic">economic</option>
              <option value="military">military</option>
            </select>
          </div>
        </div>

        <div class="sf-frow">
          <label class="sf-lbl">Context / Evidence (optional)</label>
          <textarea class="sf-ta" rows="2"
            placeholder="Analyst context, curated evidence, caveats…"
            x-model="prCtx"></textarea>
        </div>

        <div class="sf-frow">
          <label class="sf-lbl">Committee
            <span style="font-weight:400;text-transform:none;letter-spacing:0;font-size:10px;">
              — leave empty for full 8-profile committee
            </span>
          </label>
          <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:2px;">
            <template x-for="p in prAllProfiles" :key="p">
              <button class="sf-btn" :class="prCommittee.includes(p)?'sf-btn-on':''"
                @click="prToggleProfile(p)" x-text="p"></button>
            </template>
          </div>
          <div style="display:flex;gap:5px;align-items:center;margin-top:5px;flex-wrap:wrap;">
            <button class="sf-btn" style="font-size:10px;" @click="prSaveCommittee()"
              title="Save committee + domain">▲ Save</button>
            <button class="sf-btn" style="font-size:10px;"
              :disabled="prSavedCommittee.length===0"
              @click="prLoadCommittee()"
              :title="prSavedCommittee.length?'Load: '+prSavedDomain+' / '+prSavedCommittee.join(', '):'No saved committee'">
              ▼ Load
            </button>
            <button class="sf-btn" style="font-size:10px;" @click="prCommittee=[]">Clear</button>
            <span x-show="prCommitteeMsg" class="sf-msg" x-text="prCommitteeMsg"></span>
            <span x-show="prSavedCommittee.length>0&&!prCommitteeMsg"
              style="font-size:10px;color:var(--color-text-muted);"
              x-text="'saved: '+prSavedDomain+' / '+(prSavedCommittee.length===8?'full committee':prSavedCommittee.map(p=>p.split(' ')[0]).join(', '))">
            </span>
          </div>
        </div>

        <div x-show="prE" class="sf-err" x-text="prE"></div>

        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:4px;">
          <button class="sf-btn sf-btn-on" :disabled="!prQ.trim()||prL"
            @click="prSubmit()"
            x-text="prL?'Deliberating…':'Run Prediction'"></button>
          <span x-show="prL" style="font-size:11px;color:var(--color-text-muted);">
            Full committee may take 1–3 min. Partial results returned if any profiles time out.
          </span>
        </div>

      </div><!-- /form -->

      <!-- ── Result ── -->
      <div x-show="prResult">

        <!-- Consensus header -->
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;flex-wrap:wrap;gap:6px;">
          <div>
            <span style="font-size:11px;font-weight:600;">Consensus: </span>
            <span class="sf-conf" :class="confCls(prResult&&prResult.consensus_confidence)"
              x-text="pct(prResult&&prResult.consensus_confidence)"></span>
            <template x-if="prResult&&prResult.consensus_range_low!=null">
              <span style="font-size:10px;color:var(--color-text-muted);margin-left:4px;">
                (<span x-text="pct(prResult&&prResult.consensus_range_low)"></span>–<span
                  x-text="pct(prResult&&prResult.consensus_range_high)"></span>)
              </span>
            </template>
            <span x-show="prResult&&prResult.meta_confidence"
              style="font-size:10px;color:var(--color-text-muted);margin-left:6px;"
              x-text="prResult&&prResult.meta_confidence"></span>
          </div>
          <button class="sf-btn"
            @click="prResult=null;prSessId=null;prOutVal=null;prOutMsg=null;prExpanded=null">
            New Prediction
          </button>
        </div>

        <!-- Operator brief -->
        <div class="sf-result" x-text="(prResult&&prResult.operator_brief||'').slice(0,1200)"></div>

        <!-- Full committee results -->
        <div class="sf-sec">
          Committee
          <span x-show="prHasFullCommittee" style="font-weight:400;text-transform:none;letter-spacing:0;font-size:10px;">
            — all <span x-text="prProfiles.length"></span> profiles · click to expand
          </span>
          <span x-show="!prHasFullCommittee" style="font-weight:400;text-transform:none;letter-spacing:0;font-size:10px;">
            — dissenters · click to expand
          </span>
        </div>

        <template x-for="p in prProfiles" :key="p.assessment_id||p.profile_name">
          <div>
            <div class="sf-prow" @click="prExpand(p.profile_name)">
              <span class="sf-pname">
                <span style="font-size:9px;color:var(--color-text-muted);"
                  x-text="prExpanded===p.profile_name?'▼':'▶'"></span>
                <span x-text="p.profile_name"></span>
                <span x-show="p.confidence_capped" style="font-size:9px;color:var(--color-text-muted);"> ⚠</span>
              </span>
              <span class="sf-conf" :class="confCls(p.confidence)"
                x-text="p.error?'ERR':pct(p.confidence)"></span>
              <span class="sf-psum" x-text="p.error||p.reasoning_summary||p.prediction||''"></span>
            </div>
            <div x-show="prExpanded===p.profile_name" class="sf-detail"
              style="margin:2px 0 6px 16px;font-size:11px;line-height:1.6;">
              <div x-show="p.error" style="color:#f44336;" x-text="p.error||''"></div>
              <div x-show="!p.error" x-text="p.prediction||p.reasoning_summary||''"></div>
              <div x-show="p.risk_flags&&p.risk_flags.length"
                style="font-size:10px;color:var(--color-text-muted);margin-top:4px;">
                Risk flags: <span x-text="(p.risk_flags||[]).join(', ')"></span>
              </div>
            </div>
          </div>
        </template>

        <!-- Outcome logging -->
        <div style="padding-top:8px;border-top:1px solid var(--color-border);margin-top:8px;">
          <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
            <span style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--color-text-muted);flex-shrink:0;">Outcome:</span>
            <template x-for="o in [['Wrong','0'],['Partial','0.5'],['Correct','1']]" :key="o[1]">
              <button class="sf-btn" :class="prOutVal===o[1]?'sf-btn-on':''"
                @click="prOutVal=o[1]" x-text="o[0]"></button>
            </template>
            <input class="sf-inp" placeholder="notes (optional)" x-model="prOutNotes">
            <button class="sf-btn" :class="prOutVal!=null?'sf-btn-on':''"
              :disabled="prOutVal==null||prOutSaving"
              @click="prLogOutcome()" x-text="prOutSaving?'…':'Log'"></button>
          </div>
          <div x-show="prOutMsg" class="sf-msg" x-text="prOutMsg"></div>
          <div x-show="prSessId" style="padding-top:4px;">
            <span style="font-size:10px;color:var(--color-text-muted);">Session: </span>
            <code style="font-size:10px;" x-text="prSessId"></code>
          </div>
        </div>

      </div><!-- /result -->

    </div><!-- /predict -->

  </div><!-- /sf-body -->
</div><!-- /root -->"""


# ── Tool class ────────────────────────────────────────────────────────────────

class SwarmfishPanel(Tool):
    """
    Open the SWARMFISH geopolitical prediction panel. Call this whenever the user asks
    about SWARMFISH predictions, forecasts, probability estimates, or geopolitical
    assessments. Do NOT use emit_artifact with custom HTML or hardcoded probability
    numbers — call this tool. It connects to the real SWARMFISH backend and runs
    the actual analytical committee with real calibrated predictions.

    Tabs: Sessions | Calibration | Predict
    No agent round-trip needed to switch between views.
    Predict tab shows full committee results with all profiles expandable.

    Args:
        view       (str): sessions | calibration | predict   (default: sessions)
        domain     (str): domain filter for sessions view (optional)
        session_id (str): pre-expand this session in sessions view (optional)
    """

    async def execute(self, **kwargs) -> Response:
        view       = (self.args.get("view") or "sessions").strip().lower()
        domain     = (self.args.get("domain") or "").strip() or None
        session_id = (self.args.get("session_id") or "").strip() or None

        if view not in ("sessions", "calibration", "predict"):
            view = "sessions"

        html = _swarmfish_panel_html(view, domain=domain, session_id=session_id)

        self.agent.context.log.log(
            type="artifact",
            heading="SWARMFISH Forecast Panel",
            content=html,
        )
        return Response(message=f"SWARMFISH panel opened at {view}.", break_loop=False)
