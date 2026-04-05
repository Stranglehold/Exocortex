"""
oss_panel — OSS V2 Analyst Interface Panel
==========================================

Emits a live, interactive OSS analyst panel as an artifact in the chat.

Views:
  dashboard — active questions, claim velocity, recent staged claims,
              rejection summary, health badge, quick synthesis input
  questions  — question management: create, evolve, list, attention weights
  claims     — claim feed with trust badges, topic filter, promote/irrelevant actions
  sources    — source credibility editor, domain overrides, claim counts

Args:
  view (str): dashboard | questions | claims | sources   (default: dashboard)
"""

from helpers.tool import Tool, Response

_API = "/api/plugins/oss"

_STYLE = """<style>
.oss{font:12px/1.4 inherit;color:var(--color-text)}
.oss-hdr{display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-bottom:1px solid var(--color-border)}
.oss-title{font-size:13px;font-weight:600}
.oss-nav{display:flex;gap:4px}
.oss-badge{font-size:10px;padding:2px 8px;border-radius:10px;background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text-muted)}
.oss-badge-ok{background:#1a3a1a;border-color:#2d6e2d;color:#5fb85f}
.oss-badge-warn{background:#3a2a00;border-color:#7a5500;color:#d4a017}
.oss-badge-err{background:#3a1a1a;border-color:#7a2d2d;color:#d46060}
.oss-body{padding:8px 12px;overflow-y:auto;max-height:540px}
.oss-sec{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--color-text-muted);padding:6px 0 3px;border-top:1px solid var(--color-border);margin-top:6px}
.oss-sec:first-child{border-top:none;margin-top:0}
.oss-row{display:grid;align-items:center;gap:6px;padding:4px 6px;border-radius:4px;cursor:pointer}
.oss-row:hover,.oss-row-sel{background:var(--color-background-hover)}
.oss-row-head{font-size:10px;font-weight:600;text-transform:uppercase;color:var(--color-text-muted);padding:2px 6px;border-bottom:1px solid var(--color-border);margin-bottom:3px}
.oss-trust-staged{background:#3a3000;border-color:#7a6500;color:#d4b820}
.oss-trust-promoted{background:#1a3a1a;border-color:#2d6e2d;color:#5fb85f}
.oss-trust-returned{background:#3a2000;border-color:#7a4a00;color:#d48020}
.oss-trust-irrelevant{background:var(--color-message-bg);border-color:var(--color-border);color:var(--color-text-muted)}
.oss-trust-falsified{background:#3a1a1a;border-color:#7a2d2d;color:#d46060}
.oss-pill{font-size:9px;padding:1px 6px;border-radius:8px;border:1px solid;white-space:nowrap}
.oss-btn{background:none;border:1px solid var(--color-border);color:var(--color-text-muted);padding:2px 8px;border-radius:4px;cursor:pointer;font-size:11px}
.oss-btn:hover{background:var(--color-background-hover);color:var(--color-text)}
.oss-btn-on{background:var(--color-primary,#5050c0)!important;border-color:transparent!important;color:#fff!important}
.oss-btn-sm{padding:1px 6px;font-size:10px}
.oss-detail{background:var(--color-message-bg);border:1px solid var(--color-border);border-radius:4px;margin:2px 0 8px 2px;padding:8px 10px}
.oss-claimtext{font-size:11px;line-height:1.5;color:var(--color-text-muted);margin-bottom:6px;white-space:pre-wrap}
.oss-frow{display:flex;flex-direction:column;gap:4px;margin-bottom:8px}
.oss-lbl{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:var(--color-text-muted)}
.oss-inp{background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:3px 8px;border-radius:4px;font-size:11px;flex:1;min-width:0}
.oss-ta{width:100%;box-sizing:border-box;background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:5px 8px;border-radius:4px;font-size:11px;font-family:inherit;resize:vertical}
.oss-sel{background:var(--color-message-bg);border:1px solid var(--color-border);color:var(--color-text);padding:3px 8px;border-radius:4px;font-size:11px}
.oss-load{padding:16px;text-align:center;color:var(--color-text-muted);font-size:11px}
.oss-err{padding:6px;color:#d46060;font-size:11px}
.oss-msg{font-size:11px;color:var(--color-text-muted);padding-top:3px}
.oss-result{background:var(--color-message-bg);border:1px solid var(--color-border);border-radius:4px;padding:10px;margin-top:8px;font-size:11px;line-height:1.6;white-space:pre-wrap;color:var(--color-text-muted)}
.oss-vel{display:flex;gap:10px;flex-wrap:wrap;padding:4px 0}
.oss-vel-item{font-size:11px;padding:3px 8px;border-radius:4px;background:var(--color-message-bg);border:1px solid var(--color-border)}
.oss-wt-row{display:flex;align-items:center;gap:8px;margin:3px 0;font-size:11px}
.oss-wt-lbl{width:90px;color:var(--color-text-muted)}
.oss-range{flex:1;accent-color:var(--color-primary,#5050c0)}
.oss-range-val{width:30px;text-align:right;font-size:10px;color:var(--color-text-muted)}
.oss-src-row{display:grid;gap:6px;align-items:center;padding:4px 6px;border-radius:3px;font-size:11px}
.oss-src-row:hover{background:var(--color-background-hover)}
.oss-id{font-family:monospace;font-size:10px;color:var(--color-text-muted)}
</style>"""


# ── Dashboard view ───────────────────────────────────────────────────────────

def _dashboard_html() -> str:
    return f"""{_STYLE}
<div class="oss" x-data="{{
  health:null,questions:[],staged:[],rejections:null,
  loading:true,error:null,
  synQ:'',synResult:null,synLoading:false,synErr:null,
  healthCls(s){{
    if(!s)return'oss-badge';
    return s==='NOMINAL'?'oss-badge oss-badge-ok':s==='DEGRADED'?'oss-badge oss-badge-warn':'oss-badge oss-badge-err';
  }},
  async init(){{
    this.loading=true;this.error=null;
    try{{
      const [h,q,s,r]=await Promise.all([
        ExoArtifact.fetchJson('{_API}/api_oss_health',{{}}),
        ExoArtifact.fetchJson('{_API}/api_oss_questions',{{action:'list'}}),
        ExoArtifact.fetchJson('{_API}/api_oss_staging',{{action:'list',limit:5}}),
        ExoArtifact.fetchJson('{_API}/api_oss_rejections',{{action:'summary'}}),
      ]);
      this.health=h.ok?h:null;
      this.questions=(q.ok&&q.questions)||[];
      this.staged=(s.ok&&s.claims)||[];
      this.rejections=r.ok?r:null;
    }}catch(e){{this.error=String(e);}}
    finally{{this.loading=false;}}
  }},
  async synthesize(){{
    if(!this.synQ.trim())return;
    this.synLoading=true;this.synErr=null;this.synResult=null;
    try{{
      const r=await ExoArtifact.fetchJson('{_API}/api_oss_synthesis',
        {{question:this.synQ,limit:30}});
      if(!r.ok)throw new Error(r.error||'Synthesis failed');
      this.synResult=r;
    }}catch(e){{this.synErr=String(e);}}
    finally{{this.synLoading=false;}}
  }},
  trustCls(t){{
    const m={{STAGED:'oss-pill oss-trust-staged',PROMOTED:'oss-pill oss-trust-promoted',
      RETURNED_TO_STAGED:'oss-pill oss-trust-returned',IRRELEVANT:'oss-pill oss-trust-irrelevant',
      FALSIFIED:'oss-pill oss-trust-falsified'}};
    return m[t]||'oss-pill oss-trust-irrelevant';
  }}
}}">
  <div class="oss-hdr">
    <span class="oss-title">OSS Intelligence Ledger</span>
    <div style="display:flex;gap:6px;align-items:center;">
      <span :class="healthCls(health&&health.health_signal)"
        x-text="health?health.health_signal:'…'"></span>
      <button class="oss-btn" @click="init()">↻</button>
    </div>
  </div>
  <div class="oss-body">
    <div x-show="loading" class="oss-load">Loading OSS dashboard…</div>
    <div x-show="!loading&&error" class="oss-err" x-text="error"></div>
    <template x-if="!loading&&!error">
      <div>
        <!-- Active questions -->
        <div class="oss-sec">Active Questions (<span x-text="questions.length"></span>)</div>
        <div x-show="questions.length===0" style="padding:4px 6px;font-size:11px;color:var(--color-text-muted);">
          No active questions. Open the Questions view to create one.
        </div>
        <template x-for="q in questions.slice(0,4)" :key="q.id">
          <div style="padding:3px 6px;font-size:11px;">
            <span style="font-family:monospace;font-size:10px;color:var(--color-text-muted);"
              x-text="q.id.slice(0,8)"></span>
            <span style="margin-left:6px;" x-text="q.text"></span>
            <span style="margin-left:8px;font-size:10px;color:var(--color-text-muted);"
              x-text="(q.last_updated||'').slice(0,16)"></span>
          </div>
        </template>

        <!-- Claim velocity by topic -->
        <div class="oss-sec">Recent Activity</div>
        <div class="oss-vel">
          <div x-show="health&&health.claim_counts" class="oss-vel-item">
            <strong x-text="health&&(health.claim_counts&&health.claim_counts.PROMOTED)||0"></strong> promoted
          </div>
          <div x-show="health&&health.claim_counts" class="oss-vel-item">
            <strong x-text="health&&(health.claim_counts&&health.claim_counts.STAGED)||0"></strong> staged
          </div>
          <div x-show="health" class="oss-vel-item">
            Ingestion: <strong x-text="health&&health.ingestion_status"></strong>
          </div>
        </div>

        <!-- New staged claims -->
        <div class="oss-sec">New Staged Claims</div>
        <div x-show="staged.length===0" style="padding:4px 6px;font-size:11px;color:var(--color-text-muted);">
          No staged claims.
        </div>
        <template x-for="c in staged" :key="c.id">
          <div style="padding:3px 6px;font-size:11px;border-bottom:1px solid var(--color-border);">
            <span :class="trustCls(c.trust_level)" x-text="c.trust_level"></span>
            <span style="margin-left:6px;" x-text="(c.claim_text||'').slice(0,120)"></span>
            <div style="font-size:10px;color:var(--color-text-muted);margin-top:1px;"
              x-text="c.source_name+' · '+(c.extracted_at||'').slice(0,16)"></div>
          </div>
        </template>

        <!-- Rejection summary -->
        <div class="oss-sec">Rejection Summary</div>
        <div x-show="!rejections||!rejections.total" style="padding:4px 6px;font-size:11px;color:var(--color-text-muted);">
          No rejection data.
        </div>
        <template x-if="rejections&&rejections.total">
          <div style="padding:4px 6px;font-size:11px;">
            <span x-text="rejections.total"></span> total rejections:
            <template x-for="[reason,n] in Object.entries(rejections.by_reason||{{}})" :key="reason">
              <span style="margin-left:8px;font-size:10px;color:var(--color-text-muted);"
                x-text="reason+'='+n"></span>
            </template>
          </div>
        </template>

        <!-- Quick synthesis -->
        <div class="oss-sec">Ask the Ledger</div>
        <div style="display:flex;gap:6px;align-items:center;margin-top:2px;">
          <input class="oss-inp" placeholder="What is the evidence for…"
            x-model="synQ" @keydown.enter="synthesize()">
          <button class="oss-btn oss-btn-on"
            :disabled="!synQ.trim()||synLoading"
            @click="synthesize()"
            x-text="synLoading?'…':'Ask'"></button>
        </div>
        <div x-show="synErr" class="oss-err" x-text="synErr"></div>
        <template x-if="synResult">
          <div class="oss-result">
            <div style="font-size:10px;color:var(--color-text-muted);margin-bottom:4px;">
              <span x-text="(synResult.supporting||[]).length"></span> supporting ·
              <span x-text="(synResult.contradicting||[]).length"></span> contradicting ·
              <span x-text="(synResult.neutral||[]).length"></span> neutral
            </div>
            <div x-text="synResult.synthesis_text||''"></div>
            <button class="oss-btn oss-btn-sm" style="margin-top:6px;"
              @click="synResult=null;synQ=''">Clear</button>
          </div>
        </template>
      </div>
    </template>
  </div>
</div>"""


# ── Questions view ───────────────────────────────────────────────────────────

_ATTENTION_DOMAINS = ["logistics", "diplomatic", "economic", "military", "social"]

def _questions_html() -> str:
    domains_js = str(_ATTENTION_DOMAINS).replace("'", '"')
    return f"""{_STYLE}
<div class="oss" x-data="{{
  questions:[],loading:true,error:null,
  showForm:false,newText:'',evolveId:null,
  weights:{{{', '.join(f'"{d}":0.5' for d in _ATTENTION_DOMAINS)}}},
  domains:{domains_js},
  saving:false,msg:null,
  async init(){{await this.load();}},
  async load(){{
    this.loading=true;this.error=null;
    try{{
      const r=await ExoArtifact.fetchJson('{_API}/api_oss_questions',{{action:'list'}});
      if(!r.ok)throw new Error(r.error);
      this.questions=r.questions||[];
    }}catch(e){{this.error=String(e);}}
    finally{{this.loading=false;}}
  }},
  async save(){{
    if(!this.newText.trim())return;
    this.saving=true;this.msg=null;
    try{{
      const payload=this.evolveId
        ?{{action:'evolve',question_id:this.evolveId,text:this.newText,attention_weights:this.weights}}
        :{{action:'create',text:this.newText,attention_weights:this.weights}};
      const r=await ExoArtifact.fetchJson('{_API}/api_oss_questions',payload);
      if(!r.ok)throw new Error(r.error||'Failed');
      this.msg='Saved.';this.newText='';this.evolveId=null;this.showForm=false;
      await this.load();
    }}catch(e){{this.msg='Error: '+String(e);}}
    finally{{this.saving=false;}}
  }},
  async deactivate(id){{
    try{{
      const r=await ExoArtifact.fetchJson('{_API}/api_oss_questions',{{action:'deactivate',question_id:id}});
      if(!r.ok)throw new Error(r.error);
      await this.load();
    }}catch(e){{alert(String(e));}}
  }},
  startEvolve(q){{
    this.evolveId=q.id;this.newText=q.text;this.showForm=true;
  }},
  parseWeights(raw){{
    try{{return JSON.parse(raw)||{{}};}}catch{{return{{}};}}
  }}
}}">
  <div class="oss-hdr">
    <span class="oss-title">OSS — Active Questions</span>
    <div style="display:flex;gap:6px;">
      <button class="oss-btn" :class="showForm?'oss-btn-on':''"
        @click="showForm=!showForm;evolveId=null;newText=''">
        + New Question
      </button>
      <button class="oss-btn" @click="load()">↻</button>
    </div>
  </div>
  <div class="oss-body">

    <!-- Create / evolve form -->
    <template x-if="showForm">
      <div class="oss-detail" style="margin-bottom:8px;">
        <div class="oss-lbl" x-text="evolveId?'Evolve Question':'New Question'"></div>
        <textarea class="oss-ta" rows="2" style="margin:4px 0;"
          placeholder="What is the question the ledger should organize around?"
          x-model="newText"></textarea>
        <div class="oss-lbl" style="margin-top:6px;">Attention Weights</div>
        <template x-for="d in domains" :key="d">
          <div class="oss-wt-row">
            <span class="oss-wt-lbl" x-text="d"></span>
            <input type="range" class="oss-range" min="0" max="1" step="0.05"
              :value="weights[d]" @input="weights[d]=parseFloat($event.target.value)">
            <span class="oss-range-val" x-text="weights[d].toFixed(2)"></span>
          </div>
        </template>
        <div style="display:flex;gap:6px;margin-top:8px;align-items:center;">
          <button class="oss-btn oss-btn-on" :disabled="!newText.trim()||saving"
            @click="save()" x-text="saving?'Saving…':'Save'"></button>
          <button class="oss-btn" @click="showForm=false;evolveId=null;newText=''">Cancel</button>
          <span x-show="msg" class="oss-msg" x-text="msg"></span>
        </div>
      </div>
    </template>

    <div x-show="loading" class="oss-load">Loading questions…</div>
    <div x-show="!loading&&error" class="oss-err" x-text="error"></div>
    <div x-show="!loading&&!error&&questions.length===0"
      style="padding:10px 6px;font-size:11px;color:var(--color-text-muted);">
      No active questions. Create one above.
    </div>

    <template x-for="q in questions" :key="q.id">
      <div class="oss-detail" style="margin-bottom:6px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
          <div style="flex:1;">
            <div style="font-size:11px;font-weight:500;" x-text="q.text"></div>
            <div style="font-size:10px;color:var(--color-text-muted);margin-top:2px;">
              id: <span class="oss-id" x-text="q.id.slice(0,12)"></span>
              · updated <span x-text="(q.last_updated||'').slice(0,16)"></span>
            </div>
          </div>
          <div style="display:flex;gap:4px;flex-shrink:0;">
            <button class="oss-btn oss-btn-sm" @click.stop="startEvolve(q)">Evolve</button>
            <button class="oss-btn oss-btn-sm" @click.stop="deactivate(q.id)">Deactivate</button>
          </div>
        </div>
        <template x-if="q.attention_weights && Object.keys(parseWeights(q.attention_weights)||{{}}).length">
          <div style="display:flex;gap:5px;flex-wrap:wrap;margin-top:5px;">
            <template x-for="[k,v] in Object.entries(parseWeights(q.attention_weights)||{{}})" :key="k">
              <span class="oss-pill oss-trust-staged"
                x-text="k+': '+parseFloat(v).toFixed(2)"></span>
            </template>
          </div>
        </template>
        <template x-if="q.evolved_from&&JSON.parse(q.evolved_from||'[]').length">
          <div style="font-size:10px;color:var(--color-text-muted);margin-top:3px;">
            evolved from:
            <template x-for="pid in JSON.parse(q.evolved_from||'[]')" :key="pid">
              <span class="oss-id" x-text="pid.slice(0,12)"></span>
            </template>
          </div>
        </template>
      </div>
    </template>
  </div>
</div>"""


# ── Claims view ──────────────────────────────────────────────────────────────

def _claims_html() -> str:
    return f"""{_STYLE}
<div class="oss" x-data="{{
  claims:[],topics:[],topicFilter:'',loading:true,error:null,
  selId:null,actionMsg:{{}},
  trustCls(t){{
    const m={{STAGED:'oss-pill oss-trust-staged',PROMOTED:'oss-pill oss-trust-promoted',
      RETURNED_TO_STAGED:'oss-pill oss-trust-returned',IRRELEVANT:'oss-pill oss-trust-irrelevant',
      FALSIFIED:'oss-pill oss-trust-falsified'}};
    return m[t]||'oss-pill oss-trust-irrelevant';
  }},
  async init(){{await this.loadTopics();await this.load();}},
  async loadTopics(){{
    try{{
      const r=await ExoArtifact.fetchJson('{_API}/api_oss_topics',{{}});
      this.topics=(r.ok&&r.topics)||[];
    }}catch{{}}
  }},
  async load(){{
    this.loading=true;this.error=null;
    try{{
      const payload={{action:'list',limit:50}};
      if(this.topicFilter)payload.topic=this.topicFilter;
      const r=await ExoArtifact.fetchJson('{_API}/api_oss_feed',payload);
      if(!r.ok)throw new Error(r.error);
      this.claims=r.claims||[];
    }}catch(e){{this.error=String(e);}}
    finally{{this.loading=false;}}
  }},
  toggle(id){{this.selId=this.selId===id?null:id;}},
  async promote(id){{
    try{{
      const r=await ExoArtifact.fetchJson('{_API}/api_oss_staging',
        {{action:'promote',claim_id:id}});
      this.actionMsg[id]=r.ok?'Promoted':'Error: '+(r.error||'?');
      if(r.ok)await this.load();
    }}catch(e){{this.actionMsg[id]=String(e);}}
  }},
  async markIrrelevant(id){{
    try{{
      const r=await ExoArtifact.fetchJson('{_API}/api_oss_staging',
        {{action:'mark_irrelevant',claim_id:id,reason:'analyst_review'}});
      this.actionMsg[id]=r.ok?'Marked irrelevant':'Error: '+(r.error||'?');
      if(r.ok)await this.load();
    }}catch(e){{this.actionMsg[id]=String(e);}}
  }}
}}">
  <div class="oss-hdr">
    <span class="oss-title">OSS — Claims Feed</span>
    <div style="display:flex;gap:6px;align-items:center;">
      <select class="oss-sel" x-model="topicFilter" @change="load()">
        <option value="">all topics</option>
        <template x-for="t in topics" :key="t.tag">
          <option :value="t.tag" x-text="t.tag"></option>
        </template>
      </select>
      <button class="oss-btn" @click="load()">↻</button>
    </div>
  </div>
  <div class="oss-body">
    <div x-show="loading" class="oss-load">Loading claims…</div>
    <div x-show="!loading&&error" class="oss-err" x-text="error"></div>
    <div x-show="!loading&&!error&&claims.length===0"
      style="padding:10px 6px;font-size:11px;color:var(--color-text-muted);">
      No claims found for this filter.
    </div>
    <template x-for="c in claims" :key="c.id">
      <div>
        <div class="oss-row" style="grid-template-columns:70px 1fr 90px;"
          @click="toggle(c.id)" :class="selId===c.id?'oss-row-sel':''">
          <span :class="trustCls(c.trust_level)" x-text="c.trust_level"></span>
          <span style="font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
            x-text="(c.claim_text||'').slice(0,120)"></span>
          <span style="font-size:10px;color:var(--color-text-muted);text-align:right;"
            x-text="(c.extracted_at||'').slice(0,10)"></span>
        </div>
        <div x-show="selId===c.id" class="oss-detail">
          <div class="oss-claimtext" x-text="c.claim_text"></div>
          <div style="font-size:10px;color:var(--color-text-muted);margin-bottom:6px;">
            Source: <strong x-text="c.source_name||'?'"></strong>
            · Technique: <span x-text="c.technique_class||'none'"></span>
            · Cui bono: <span x-text="JSON.parse(c.cui_bono||'[]').join(', ')||'?'"></span>
          </div>
          <div x-show="c.article_url" style="font-size:10px;color:var(--color-text-muted);margin-bottom:6px;">
            <a :href="c.article_url" target="_blank" style="color:inherit;" x-text="c.article_url"></a>
          </div>
          <div x-show="c.trust_level==='STAGED'" style="display:flex;gap:6px;align-items:center;">
            <button class="oss-btn oss-btn-sm" @click.stop="promote(c.id)">Promote</button>
            <button class="oss-btn oss-btn-sm" @click.stop="markIrrelevant(c.id)">Mark Irrelevant</button>
            <span x-show="actionMsg[c.id]" class="oss-msg" x-text="actionMsg[c.id]"></span>
          </div>
        </div>
      </div>
    </template>
  </div>
</div>"""


# ── Sources view ─────────────────────────────────────────────────────────────

def _sources_html() -> str:
    return f"""{_STYLE}
<div class="oss" x-data="{{
  sources:[],loading:true,error:null,
  saving:{{}},msgs:{{}},
  async init(){{await this.load();}},
  async load(){{
    this.loading=true;this.error=null;
    try{{
      const r=await ExoArtifact.fetchJson('{_API}/api_oss_sources',{{}});
      if(!r.ok)throw new Error(r.error);
      this.sources=(r.sources||[]).map(s=>{{
        s._cred=s.credibility_overall!=null?s.credibility_overall:s.confidence_score||0.7;
        s._domain=s.domain_overrides||'';
        return s;
      }});
    }}catch(e){{this.error=String(e);}}
    finally{{this.loading=false;}}
  }},
  async saveCred(s){{
    this.saving[s.id]=true;this.msgs[s.id]=null;
    try{{
      const r=await ExoArtifact.fetchJson('{_API}/api_oss_credibility',
        {{action:'set',source_id:s.id,overall:s._cred}});
      this.msgs[s.id]=r.ok?'Saved':'Error: '+(r.error||'?');
    }}catch(e){{this.msgs[s.id]=String(e);}}
    finally{{this.saving[s.id]=false;}}
  }},
  typeCls(t){{
    const m={{wire:'oss-trust-staged',official:'oss-trust-promoted',
      outlet:'oss-trust-returned',social:'oss-trust-falsified',
      independent:'oss-trust-irrelevant'}};
    return'oss-pill '+(m[t]||'oss-trust-irrelevant');
  }}
}}">
  <div class="oss-hdr">
    <span class="oss-title">OSS — Sources</span>
    <button class="oss-btn" @click="load()">↻</button>
  </div>
  <div class="oss-body">
    <div x-show="loading" class="oss-load">Loading sources…</div>
    <div x-show="!loading&&error" class="oss-err" x-text="error"></div>
    <div x-show="!loading&&!error&&sources.length===0"
      style="padding:10px 6px;font-size:11px;color:var(--color-text-muted);">
      No sources registered.
    </div>
    <div x-show="!loading&&sources.length" class="oss-row oss-row-head"
      style="grid-template-columns:140px 60px 60px 1fr 70px;">
      <span>Source</span><span>Type</span><span>Claims</span><span>Credibility</span><span></span>
    </div>
    <template x-for="s in sources" :key="s.id">
      <div class="oss-src-row" style="grid-template-columns:140px 60px 60px 1fr 70px;">
        <span style="font-size:11px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
          x-text="s.name"></span>
        <span :class="typeCls(s.source_type)" x-text="s.source_type"></span>
        <span style="font-size:11px;color:var(--color-text-muted);" x-text="s.total_claims||0"></span>
        <div style="display:flex;align-items:center;gap:6px;">
          <input type="range" class="oss-range" min="0" max="1" step="0.05"
            :value="s._cred" @input="s._cred=parseFloat($event.target.value)">
          <span class="oss-range-val" x-text="s._cred.toFixed(2)"></span>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;">
          <button class="oss-btn oss-btn-sm" :disabled="saving[s.id]"
            @click="saveCred(s)" x-text="saving[s.id]?'…':'Save'"></button>
          <span x-show="msgs[s.id]" style="font-size:9px;color:var(--color-text-muted);"
            x-text="msgs[s.id]"></span>
        </div>
      </div>
    </template>
  </div>
</div>"""


# ── Build ────────────────────────────────────────────────────────────────────

def _build_html(view: str) -> str:
    if view == "questions":
        return _questions_html()
    if view == "claims":
        return _claims_html()
    if view == "sources":
        return _sources_html()
    return _dashboard_html()


# ── Tool class ───────────────────────────────────────────────────────────────

class OssPanel(Tool):
    """
    Open the OSS V2 analyst interface in the artifact panel.

    Views:
      dashboard — active questions, claim velocity, recent staged claims,
                  rejection summary, health badge, quick synthesis input
      questions — question management: create, evolve, list, attention weights
      claims    — claim feed with trust badges, topic filter, analyst actions
      sources   — source credibility editor, domain overrides, claim counts

    Args:
        view (str): dashboard | questions | claims | sources   (default: dashboard)
    """

    async def execute(self, **kwargs) -> Response:
        view = (self.args.get("view") or "dashboard").strip().lower()

        if view not in ("dashboard", "questions", "claims", "sources"):
            view = "dashboard"

        titles = {
            "dashboard": "OSS Intelligence Ledger — Dashboard",
            "questions": "OSS Intelligence Ledger — Questions",
            "claims":    "OSS Intelligence Ledger — Claims",
            "sources":   "OSS Intelligence Ledger — Sources",
        }

        html = _build_html(view)

        self.agent.context.log.log(
            type="artifact",
            heading=titles[view],
            content=html,
        )
        return Response(message=f"OSS {view} panel emitted.", break_loop=False)
