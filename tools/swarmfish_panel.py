"""
swarmfish_panel — SWARMFISH Interactive Panel
=============================================

Emits a live, interactive SWARMFISH panel as an artifact in the chat.

Views:
  sessions    — session browser with inline detail expansion + outcome logging
  calibration — per-profile consensus weights and domain Brier scores
  predict     — prediction submission form (question → committee → result)

Args:
  view       (str): sessions | calibration | predict   (default: sessions)
  domain     (str): domain filter for sessions view (optional)
  session_id (str): pre-expand this session in the sessions view (optional)
"""

from helpers.tool import Tool, Response


_API = "/api/plugins/swarmfish"

_STYLE = """<style>
.sf{font:12px/1.4 inherit;color:var(--color-text)}
.sf-hdr{display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-bottom:1px solid var(--color-border)}
.sf-title{font-size:13px;font-weight:600}
.sf-badge{font-size:10px;padding:2px 8px;border-radius:10px;background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text-muted)}
.sf-body{padding:8px 12px;overflow-y:auto;max-height:520px}
.sf-row{display:grid;align-items:center;gap:6px;padding:4px 6px;border-radius:4px;cursor:pointer}
.sf-row:hover,.sf-row-sel{background:var(--color-background-hover)}
.sf-row-head{font-size:10px;font-weight:600;text-transform:uppercase;color:var(--color-text-muted);padding:2px 6px;border-bottom:1px solid var(--color-border);margin-bottom:3px}
.sf-id{font-family:monospace;font-size:10px;color:var(--color-text-muted)}
.sf-domain{font-size:10px;padding:1px 6px;border-radius:10px;background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text-muted);white-space:nowrap;text-align:center}
.sf-q{font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sf-conf{font-size:12px;font-weight:700;text-align:right}
.sf-high{color:#4caf50}.sf-mid{color:#ff9800}.sf-low{color:#f44336}
.sf-btn{background:none;border:1px solid var(--color-border);color:var(--color-text-muted);padding:2px 8px;border-radius:4px;cursor:pointer;font-size:11px}
.sf-btn:hover{background:var(--color-background-hover);color:var(--color-text)}
.sf-btn-on{background:var(--color-primary,#5050c0)!important;border-color:transparent!important;color:#fff!important}
.sf-detail{background:var(--color-message-bg);border:1px solid var(--color-border);border-radius:4px;margin:2px 0 8px 2px;padding:8px 10px}
.sf-brief{font-size:11px;line-height:1.5;white-space:pre-wrap;color:var(--color-text-muted);margin-bottom:6px}
.sf-sec{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--color-text-muted);padding:5px 0 3px;border-top:1px solid var(--color-border);margin-top:4px}
.sf-prow{display:grid;grid-template-columns:140px 42px 1fr;gap:6px;align-items:start;padding:2px 3px;border-radius:3px;font-size:11px}
.sf-prow:hover{background:var(--color-background-hover)}
.sf-pname{font-weight:500}
.sf-psum{color:var(--color-text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sf-out{display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:6px 0;border-top:1px solid var(--color-border);margin-top:6px}
.sf-inp{background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:3px 8px;border-radius:4px;font-size:11px;flex:1;min-width:0}
.sf-msg{font-size:11px;color:var(--color-text-muted);padding-top:3px}
.sf-load{padding:16px;text-align:center;color:var(--color-text-muted);font-size:11px}
.sf-err{padding:6px;color:#f44336;font-size:11px}
.sf-calr{display:grid;gap:8px;align-items:center;padding:3px 6px;border-radius:3px;font-size:11px}
.sf-calr:hover{background:var(--color-background-hover)}
.sf-frow{display:flex;flex-direction:column;gap:4px;margin-bottom:8px}
.sf-lbl{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--color-text-muted)}
.sf-ta{width:100%;box-sizing:border-box;background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:5px 8px;border-radius:4px;font-size:11px;font-family:inherit;resize:vertical}
.sf-sel{background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:4px 8px;border-radius:4px;font-size:11px}
.sf-result{background:var(--color-message-bg);border:1px solid var(--color-border);border-radius:4px;padding:10px;margin-top:8px;font-size:11px;line-height:1.5;white-space:pre-wrap;color:var(--color-text-muted)}
</style>"""


# ── Shared Alpine helpers (inlined JS, not a separate file) ──────────────────

_SHARED_JS = """
confCls(c){return c==null?'':c>=0.7?'sf-high':c>=0.45?'sf-mid':'sf-low'},
pct(c){return c!=null?Math.round(c*100)+'%':'—'},
"""


# ── Sessions view ────────────────────────────────────────────────────────────

def _sessions_html(domain: str | None, preselect: str | None) -> str:
    domain_init = f'"{domain}"' if domain else '""'
    preselect_init = f'"{preselect}"' if preselect else 'null'
    return f"""{_STYLE}
<div class="sf" x-data="{{
  sessions:[],domain:{domain_init},loading:true,error:null,
  selId:{preselect_init},detail:null,detLoading:false,detErr:null,level:2,
  outVal:null,outNotes:'',outSaving:false,outMsg:null,
  {_SHARED_JS}
  async init(){{await this.load();if(this.selId)await this.loadDetail(this.selId);}},
  async load(){{
    this.loading=true;this.error=null;
    try{{const r=await ExoArtifact.fetchJson('{_API}/api_swarmfish_sessions',
      {{limit:30,domain:this.domain||undefined}});
      if(!r.ok)throw new Error(r.error);
      this.sessions=r.sessions||[];
    }}catch(e){{this.error=String(e);}}
    finally{{this.loading=false;}}
  }},
  async toggle(id){{
    if(this.selId===id){{this.selId=null;this.detail=null;return;}}
    this.selId=id;await this.loadDetail(id);
  }},
  async loadDetail(id){{
    this.detail=null;this.detLoading=true;this.detErr=null;
    this.outVal=null;this.outNotes='';this.outMsg=null;
    try{{const r=await ExoArtifact.fetchJson('{_API}/api_swarmfish_session',
      {{session_id:id,level:this.level}});
      if(!r.ok)throw new Error(r.error);this.detail=r;
    }}catch(e){{this.detErr=String(e);}}
    finally{{this.detLoading=false;}}
  }},
  async setLevel(l){{this.level=l;if(this.selId)await this.loadDetail(this.selId);}},
  async saveOutcome(){{
    if(this.outVal==null)return;
    this.outSaving=true;this.outMsg=null;
    try{{const r=await ExoArtifact.fetchJson('{_API}/api_swarmfish_outcome',
      {{session_id:this.selId,outcome:parseFloat(this.outVal),notes:this.outNotes||null}});
      this.outMsg=r.ok?'✓ Outcome logged':'Error: '+(r.error||'unknown');
    }}catch(e){{this.outMsg=String(e);}}
    this.outSaving=false;
  }}
}}">
  <div class="sf-hdr">
    <span class="sf-title">SWARMFISH Sessions</span>
    <div style="display:flex;gap:6px;align-items:center;">
      <select class="sf-sel" x-model="domain" @change="selId=null;detail=null;load()">
        <option value="">all domains</option>
        <option value="geopolitical">geopolitical</option>
        <option value="economic">economic</option>
        <option value="military">military</option>
        <option value="general">general</option>
      </select>
      <button class="sf-btn" @click="selId=null;detail=null;load()">↻</button>
    </div>
  </div>
  <div class="sf-body">
    <div x-show="loading" class="sf-load">Loading sessions…</div>
    <div x-show="!loading && error" class="sf-err" x-text="error"></div>
    <div x-show="!loading && !error">
      <div class="sf-row sf-row-head" style="grid-template-columns:56px 86px 1fr 46px;">
        <span>ID</span><span>Domain</span><span>Question</span><span>Conf</span>
      </div>
      <div x-show="sessions.length===0" style="padding:10px 6px;color:var(--color-text-muted);font-size:11px;">
        No sessions yet — run a prediction to begin.
      </div>
      <template x-for="s in sessions" :key="s.id">
        <div>
          <div class="sf-row" :class="selId===s.id?'sf-row-sel':''"
            style="grid-template-columns:56px 86px 1fr 46px;"
            @click="toggle(s.id)">
            <span class="sf-id" x-text="s.id.slice(0,8)"></span>
            <span class="sf-domain" x-text="s.domain"></span>
            <span class="sf-q" x-text="s.question"></span>
            <span class="sf-conf" :class="confCls(s.consensus_confidence)"
              x-text="pct(s.consensus_confidence)"></span>
          </div>
          <div x-show="selId===s.id">
            <div x-show="detLoading" class="sf-load" style="padding:8px;">Loading detail…</div>
            <div x-show="!detLoading && detErr" class="sf-err" x-text="detErr"></div>
            <div x-show="!detLoading && !detErr && detail" class="sf-detail">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <div style="font-size:11px;color:var(--color-text-muted);">
                  <span x-text="detail&&detail.domain"></span>
                  <template x-if="detail&&detail.consensus_confidence!=null">
                    <span> · Consensus:
                      <strong :class="confCls(detail&&detail.consensus_confidence)"
                        x-text="detail&&pct(detail.consensus_confidence)"></strong>
                    </span>
                  </template>
                  <template x-if="detail&&detail.meta_confidence">
                    <span> · <span x-text="detail&&detail.meta_confidence"></span></span>
                  </template>
                  <template x-if="detail&&detail.consensus_range_low!=null">
                    <span style="color:var(--color-text-muted);font-size:10px;">
                      (<span x-text="detail&&pct(detail.consensus_range_low)"></span>–<span x-text="detail&&pct(detail.consensus_range_high)"></span>)
                    </span>
                  </template>
                </div>
                <div style="display:flex;gap:4px;">
                  <template x-for="l in [1,2,3]" :key="l">
                    <button class="sf-btn" :class="level===l?'sf-btn-on':''"
                      @click.stop="setLevel(l)" x-text="'L'+l"></button>
                  </template>
                </div>
              </div>
              <div x-show="detail&&detail.operator_brief" class="sf-brief"
                x-text="detail&&(detail.operator_brief||'').slice(0,600)"></div>
              <div class="sf-sec">Profiles (Level <span x-text="level"></span>)</div>
              <template x-for="p in (detail&&detail.profiles||[])" :key="p.assessment_id">
                <div class="sf-prow">
                  <span class="sf-pname">
                    <span x-text="p.profile_name"></span>
                    <template x-if="p.confidence_capped"><span style="font-size:10px;color:var(--color-text-muted);"> ⚠</span></template>
                  </span>
                  <span class="sf-conf" :class="confCls(p.confidence)"
                    x-text="p.error?'ERR':pct(p.confidence)"></span>
                  <span class="sf-psum"
                    x-text="p.error||p.reasoning_summary||p.prediction||''"></span>
                </div>
              </template>
              <div class="sf-out">
                <span style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--color-text-muted);flex-shrink:0;">Outcome:</span>
                <template x-for="o in [['Wrong','0'],['Partial','0.5'],['Correct','1']]" :key="o[1]">
                  <button class="sf-btn" :class="outVal===o[1]?'sf-btn-on':''"
                    @click.stop="outVal=o[1]" x-text="o[0]"></button>
                </template>
                <input class="sf-inp" placeholder="notes (optional)" x-model="outNotes" @click.stop>
                <button class="sf-btn" :class="outVal!=null?'sf-btn-on':''"
                  :disabled="outVal==null||outSaving"
                  @click.stop="saveOutcome()">Save</button>
              </div>
              <div x-show="outMsg" class="sf-msg" x-text="outMsg"></div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</div>"""


# ── Calibration view ─────────────────────────────────────────────────────────

def _calibration_html() -> str:
    return f"""{_STYLE}
<div class="sf" x-data="{{
  data:null,loading:true,error:null,
  {_SHARED_JS}
  async init(){{
    try{{const r=await ExoArtifact.fetchJson('{_API}/api_swarmfish_calibration',{{}});
      if(!r.ok)throw new Error(r.error);this.data=r;
    }}catch(e){{this.error=String(e);}}
    finally{{this.loading=false;}}
  }},
  brierCls(b){{return b==null?'':b<=0.10?'sf-high':b<=0.20?'sf-mid':'sf-low'}},
  wt(pw){{return pw&&pw.default!=null?pw.default.toFixed(2):'1.00'}}
}}">
  <div class="sf-hdr">
    <span class="sf-title">SWARMFISH Calibration</span>
    <span class="sf-badge" x-show="data"
      x-text="data?(data.session_count+' sessions, '+data.scored_session_count+' scored'):''"></span>
  </div>
  <div class="sf-body">
    <div x-show="loading" class="sf-load">Loading calibration…</div>
    <div x-show="!loading && error" class="sf-err" x-text="error"></div>
    <template x-if="!loading && !error && data">
      <div>
        <div class="sf-sec" style="margin-top:0;border-top:none;">Consensus Weights
          <span style="font-weight:400;text-transform:none;letter-spacing:0;font-size:10px;">
            (updates after 5+ scored sessions)
          </span>
        </div>
        <div class="sf-calr sf-row-head" style="grid-template-columns:160px 56px 60px 1fr;">
          <span>Profile</span><span>Weight</span><span>Scored</span><span>Status</span>
        </div>
        <template x-for="p in (data.profile_weights||[])" :key="p.name">
          <div class="sf-calr" style="grid-template-columns:160px 56px 60px 1fr;">
            <span x-text="p.name"></span>
            <span x-text="wt(p.consensus_weight)"></span>
            <span x-text="p.n_scored||0"></span>
            <span style="color:var(--color-text-muted);font-size:10px;"
              x-text="(p.n_scored||0)>=5?'calibrated':'warming up'"></span>
          </div>
        </template>
        <div x-show="data.calibration_by_domain && data.calibration_by_domain.length">
          <div class="sf-sec">Domain Brier Scores
            <span style="font-weight:400;text-transform:none;letter-spacing:0;font-size:10px;">
              (lower = more accurate; random baseline = 0.25)
            </span>
          </div>
          <div class="sf-calr sf-row-head" style="grid-template-columns:160px 86px 56px 56px;">
            <span>Profile</span><span>Domain</span><span>Brier</span><span>n</span>
          </div>
          <template x-for="row in (data.calibration_by_domain||[])"
            :key="row.profile_name+row.domain">
            <div class="sf-calr" style="grid-template-columns:160px 86px 56px 56px;">
              <span x-text="row.profile_name"></span>
              <span class="sf-domain" x-text="row.domain"></span>
              <span :class="brierCls(row.avg_brier)"
                x-text="row.avg_brier!=null?row.avg_brier.toFixed(3):'n/a'"></span>
              <span x-text="row.n_predictions||0"></span>
            </div>
          </template>
        </div>
        <div x-show="!data.calibration_by_domain||!data.calibration_by_domain.length"
          style="padding:8px 6px;color:var(--color-text-muted);font-size:11px;">
          No calibration data yet. Score sessions using the outcome form in the Sessions panel.
        </div>
      </div>
    </template>
  </div>
</div>"""


# ── Predict view ─────────────────────────────────────────────────────────────

_PROFILE_NAMES = [
    "Base Rate Analyst", "Contrarian", "Historian",
    "Reflexivity Modeler", "Decomposer", "Network Analyst",
    "Sentiment Decoder", "Risk Manager",
]
_PROFILES_JSON = str(_PROFILE_NAMES).replace("'", '"')


def _predict_html() -> str:
    return f"""{_STYLE}
<div class="sf" x-data="{{
  question:'',domain:'general',context:'',
  committee:[],allProfiles:{_PROFILES_JSON},
  loading:false,error:null,result:null,sessionId:null,
  {_SHARED_JS}
  toggleProfile(p){{
    const i=this.committee.indexOf(p);
    if(i===-1)this.committee.push(p);else this.committee.splice(i,1);
  }},
  async submit(){{
    if(!this.question.trim())return;
    this.loading=true;this.error=null;this.result=null;this.sessionId=null;
    try{{
      const payload={{question:this.question,domain:this.domain,
        context:this.context||undefined,
        committee:this.committee.length?this.committee:undefined}};
      const r=await ExoArtifact.fetchJson('{_API}/api_swarmfish_predict',payload);
      if(!r.ok)throw new Error(r.error||'Prediction failed');
      this.sessionId=r.session_id;this.result=r;
    }}catch(e){{this.error=String(e);}}
    finally{{this.loading=false;}}
  }}
}}">
  <div class="sf-hdr">
    <span class="sf-title">SWARMFISH — New Prediction</span>
  </div>
  <div class="sf-body">
    <template x-if="!result">
      <div>
        <div class="sf-frow">
          <label class="sf-lbl">Question <span style="color:#f44336;">*</span></label>
          <textarea class="sf-ta" rows="3" placeholder="What is the probability that…"
            x-model="question"></textarea>
        </div>
        <div class="sf-frow">
          <label class="sf-lbl">Domain</label>
          <select class="sf-sel" x-model="domain">
            <option value="general">general</option>
            <option value="geopolitical">geopolitical</option>
            <option value="economic">economic</option>
            <option value="military">military</option>
          </select>
        </div>
        <div class="sf-frow">
          <label class="sf-lbl">Context / Evidence (optional)</label>
          <textarea class="sf-ta" rows="2" placeholder="Analyst-supplied context, caveats, recent evidence…"
            x-model="context"></textarea>
        </div>
        <div class="sf-frow">
          <label class="sf-lbl">Committee
            <span style="font-weight:400;text-transform:none;letter-spacing:0;font-size:10px;">
              — leave empty for full 8-profile committee
            </span>
          </label>
          <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:2px;">
            <template x-for="p in allProfiles" :key="p">
              <button class="sf-btn" :class="committee.includes(p)?'sf-btn-on':''"
                @click="toggleProfile(p)" x-text="p"></button>
            </template>
          </div>
        </div>
        <div x-show="error" class="sf-err" x-text="error"></div>
        <div style="display:flex;gap:8px;align-items:center;margin-top:4px;">
          <button class="sf-btn sf-btn-on" :disabled="!question.trim()||loading"
            @click="submit()"
            x-text="loading?'Running committee…':'Run Prediction'"></button>
          <span x-show="loading" style="font-size:11px;color:var(--color-text-muted);">
            ~30s for full committee…
          </span>
        </div>
      </div>
    </template>
    <template x-if="result">
      <div>
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
          <div>
            <span style="font-size:11px;font-weight:600;">Consensus: </span>
            <span class="sf-conf" :class="confCls(result.consensus_confidence)"
              x-text="pct(result.consensus_confidence)"></span>
            <span style="font-size:10px;color:var(--color-text-muted);margin-left:6px;"
              x-text="result.meta_confidence"></span>
          </div>
          <button class="sf-btn" @click="result=null;sessionId=null;">New Prediction</button>
        </div>
        <div class="sf-result" x-text="(result.operator_brief||'').slice(0,1200)"></div>
        <template x-if="result.dissenters && result.dissenters.length">
          <div>
            <div class="sf-sec">Dissenters</div>
            <template x-for="d in result.dissenters" :key="d.profile_name">
              <div class="sf-prow">
                <span class="sf-pname">⚡ <span x-text="d.profile_name"></span></span>
                <span class="sf-conf sf-low" x-text="pct(d.confidence)"></span>
                <span class="sf-psum" x-text="d.reasoning_summary||''"></span>
              </div>
            </template>
          </div>
        </template>
        <div x-show="sessionId" style="padding-top:8px;border-top:1px solid var(--color-border);margin-top:8px;">
          <span style="font-size:10px;color:var(--color-text-muted);">Session ID: </span>
          <code style="font-size:10px;" x-text="sessionId"></code>
        </div>
      </div>
    </template>
  </div>
</div>"""


# ── Build ────────────────────────────────────────────────────────────────────

def _build_html(view: str, domain: str | None, session_id: str | None) -> str:
    if view == "calibration":
        return _calibration_html()
    if view == "predict":
        return _predict_html()
    return _sessions_html(domain, session_id)


# ── Tool class ───────────────────────────────────────────────────────────────

class SwarmfishPanel(Tool):
    """
    Emit an interactive SWARMFISH panel artifact into the chat.

    view=sessions    — session browser with inline detail expansion + outcome logging
    view=calibration — per-profile consensus weights and domain Brier scores
    view=predict     — prediction submission form

    Args:
        view       (str): sessions | calibration | predict   (default: sessions)
        domain     (str): domain filter for sessions view (optional)
        session_id (str): pre-expand this session in the sessions view (optional)
    """

    async def execute(self, **kwargs) -> Response:
        view       = (self.args.get("view") or "sessions").strip().lower()
        domain     = (self.args.get("domain") or "").strip() or None
        session_id = (self.args.get("session_id") or "").strip() or None

        if view not in ("sessions", "calibration", "predict"):
            view = "sessions"

        titles = {
            "sessions":    "SWARMFISH — Sessions",
            "calibration": "SWARMFISH — Calibration",
            "predict":     "SWARMFISH — New Prediction",
        }

        html = _build_html(view, domain=domain, session_id=session_id)

        self.agent.context.log.log(
            type="artifact",
            heading=titles[view],
            content=html,
        )
        return Response(message=f"SWARMFISH {view} panel emitted.", break_loop=False)
