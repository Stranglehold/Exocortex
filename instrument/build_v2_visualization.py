"""
build_v2_visualization.py — V2 chunk-level 3D UMAP visualizer.

Reads V2 pipeline outputs and generates a self-contained interactive HTML:
  - 3D UMAP of 4036 chunks + 46 corpus documents
  - Layer toggles: Corpus / Jake / Opus / by source (doc1/doc2/doc3)
  - Color modes: Speaker | Date | Dominant Domain | Source
  - Timeline bar filter by date
  - Click inspector with chunk text + 5-channel domain bars
  - Jump-to presets for key sessions

Output: instrument/data/v2/v2_visualization.html
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
V2   = DATA / "v2"

OUT = V2 / "v2_visualization.html"

# ── Load data ──────────────────────────────────────────────────────────────────

umap_pts    = json.loads((V2   / "umap_v2.json").read_text(encoding="utf-8"))["points"]
chunks_raw  = json.loads((V2   / "chunks.json").read_text(encoding="utf-8"))["chunks"]
ch5_raw     = json.loads((V2   / "chunk_5channel.json").read_text(encoding="utf-8"))["chunks"]
corpus_meta = json.loads((DATA / "corpus_metadata.json").read_text(encoding="utf-8"))

chunk_by_id = {c["chunk_id"]: c for c in chunks_raw}
ch5_by_id   = {c["chunk_id"]: c["channels"] for c in ch5_raw}

DOMAINS = ["philosophical", "operational", "reflective", "relational", "mixed"]
DOMAIN_COLORS = {
    "philosophical": "#9b59b6",
    "operational":   "#e67e22",
    "reflective":    "#2ecc71",
    "relational":    "#3498db",
    "mixed":         "#95a5a6",
}
DATE_COLORS = {
    "Feb 17": "#1a1a2e", "Feb 18": "#16213e", "Feb 19": "#0f3460",
    "Feb 20": "#533483", "Feb 21": "#e94560", "Feb 22": "#c84b31",
    "Feb 23": "#ecb365", "Feb 24": "#f5cba7",
    "Feb 25": "#a8e6cf", "Feb 26": "#3d84a8", "Feb 27": "#46cdcf",
    "Feb 28": "#48466d",
    "Mar 1":  "#3c3f58", "Mar 2":  "#2b4162", "Mar 3":  "#12a4d9",
    "Mar 4":  "#00b4d8", "Mar 5":  "#90e0ef", "Mar 6":  "#caf0f8",
    "Mar 7":  "#ffe082", "Mar 8":  "#ffb74d", "Mar 9":  "#ff8a65",
    "unknown": "#555566",
}
DATE_ORDER = [
    "Feb 17","Feb 18","Feb 19","Feb 20","Feb 21","Feb 22","Feb 23","Feb 24",
    "Feb 25","Feb 26","Feb 27","Feb 28",
    "Mar 1","Mar 2","Mar 3","Mar 4","Mar 5","Mar 6","Mar 7","Mar 8","Mar 9",
    "unknown",
]
SOURCE_COLORS = {"doc1": "#4a9eda", "doc2": "#e6a12a", "doc3": "#5ec76e"}

def truncate(s, n=180):
    return s[:n] + "..." if len(s) > n else s

# ── Build enriched point list ──────────────────────────────────────────────────
date_idx_map = {d: i for i, d in enumerate(DATE_ORDER)}
points = []

for p in umap_pts:
    if p["type"] == "chunk":
        cid = p["chunk_id"]
        c   = chunk_by_id.get(cid, {})
        ch5 = ch5_by_id.get(cid, {d: 0.5 for d in DOMAINS})
        dom_scores = sorted([(d, ch5.get(d, 0)) for d in DOMAINS], key=lambda x: -x[1])
        dominant   = dom_scores[0][0]
        record = {
            "t":   "chunk",
            "id":  cid,
            "tid": p["turn_id"],
            "sp":  p["speaker"],
            "dt":  p["date"],
            "src": p["source"],
            "x":   round(p["x"], 4),
            "y":   round(p["y"], 4),
            "z":   round(p["z"], 4),
            "wc":  c.get("word_count", 0),
            "ci":  c.get("chunk_within_turn", 0),
            "tc":  c.get("total_chunks_in_turn", 1),
            "tx":  truncate(c.get("text", "")),
            "dom": dominant,
            "ch5": [round(ch5.get(d, 0), 4) for d in DOMAINS],
            "di":  date_idx_map.get(p["date"], len(DATE_ORDER) - 1),
        }
    else:
        doc_id = p["doc_id"]
        m      = corpus_meta[doc_id] if doc_id < len(corpus_meta) else {}
        label  = m.get("source_file", f"corpus_{doc_id}")
        label  = label.rsplit(".", 1)[0] if "." in label else label
        record = {
            "t":  "corpus",
            "id": doc_id,
            "x":  round(p["x"], 4),
            "y":  round(p["y"], 4),
            "z":  round(p["z"], 4),
            "lb": label,
            "dt": m.get("document_type", ""),
            "au": m.get("author", ""),
            "tx": truncate(m.get("text_preview", ""), 220),
            "di": len(DATE_ORDER) - 1,
        }
    points.append(record)

n_chunks = sum(1 for p in points if p["t"] == "chunk")
n_corpus = sum(1 for p in points if p["t"] == "corpus")
n_jake   = sum(1 for p in points if p.get("sp") == "Jake")
n_opus   = sum(1 for p in points if p.get("sp") == "Opus")

payload = json.dumps({
    "points":        points,
    "date_order":    DATE_ORDER,
    "domains":       DOMAINS,
    "domain_colors": DOMAIN_COLORS,
    "date_colors":   DATE_COLORS,
    "source_colors": SOURCE_COLORS,
}, ensure_ascii=False, separators=(",", ":"))

# ── HTML ───────────────────────────────────────────────────────────────────────
html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Exocortex V2 — Chunk-Level Collaboration Map</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js" charset="utf-8"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0c12;color:#ccc;font-family:'Courier New',monospace;font-size:12px;overflow:hidden}
#layout{display:flex;height:100vh}
#left-panel{width:210px;flex-shrink:0;background:#111318;border-right:1px solid #222;display:flex;flex-direction:column;overflow:hidden}
#main-area{flex:1;display:flex;flex-direction:column;overflow:hidden}
#right-panel{width:280px;flex-shrink:0;background:#0e1018;border-left:1px solid #222;display:flex;flex-direction:column;overflow:hidden}
#title-bar{padding:10px 12px;border-bottom:1px solid #222}
#title-bar h2{font-size:11px;color:#7ec8e3;letter-spacing:.5px}
#title-bar p{font-size:10px;color:#555;margin-top:2px}
#layer-toggles{padding:10px 12px;border-bottom:1px solid #222}
#layer-toggles h3{font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.trow{display:flex;align-items:center;margin-bottom:5px;cursor:pointer;user-select:none}
.trow input{margin-right:7px;cursor:pointer;accent-color:#7ec8e3}
.tdot{width:8px;height:8px;border-radius:50%;margin-right:6px;flex-shrink:0}
.tlabel{font-size:11px;color:#bbb}
#color-mode{padding:10px 12px;border-bottom:1px solid #222}
#color-mode h3{font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.cbtn{background:#1a1d25;border:1px solid #333;color:#aaa;padding:4px 8px;cursor:pointer;font-family:inherit;font-size:10px;margin-bottom:3px;width:100%;text-align:left}
.cbtn.active{border-color:#7ec8e3;color:#7ec8e3}
#presets{padding:10px 12px;border-bottom:1px solid #222}
#presets h3{font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.pbtn{background:#1a1d25;border:1px solid #2a2d35;color:#999;padding:3px 8px;cursor:pointer;font-family:inherit;font-size:10px;margin-bottom:3px;width:100%;text-align:left}
.pbtn:hover{border-color:#555;color:#ddd}
#stats-panel{flex:1;padding:10px 12px;overflow-y:auto}
#stats-panel h3{font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.stat{font-size:10px;color:#aaa;margin:2px 0}
.stat-l{color:#666}
#plot-container{flex:1;position:relative}
#plot{width:100%;height:100%}
#timeline-bar{height:72px;background:#0d0f18;border-top:1px solid #1e2130;padding:6px 14px}
#tl-labels{display:flex;justify-content:space-between;font-size:9px;color:#555;margin-bottom:3px}
#tl-slider-wrap{position:relative;height:20px}
#tl-track{position:absolute;top:8px;left:0;right:0;height:4px;background:#1e2130;border-radius:2px}
#tl-range{position:absolute;top:8px;height:4px;background:#3a8ec4;border-radius:2px}
.tl-handle{position:absolute;top:2px;width:16px;height:16px;background:#7ec8e3;border-radius:50%;cursor:ew-resize;transform:translateX(-8px);border:2px solid #0a0c12}
#tl-info{font-size:9px;color:#7ec8e3;margin-top:4px}
#inspector{flex:1;padding:10px 12px;overflow-y:auto;border-bottom:1px solid #222}
#inspector h3{font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.ifield{margin-bottom:4px;font-size:11px}
.ilabel{color:#666}
.ival{color:#ccc}
.itext{margin-top:8px;font-size:11px;color:#999;border-top:1px solid #1e2130;padding-top:8px;line-height:1.5}
#domain-bars{padding:10px 12px;border-top:1px solid #1e2130;flex-shrink:0}
#domain-bars h3{font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.dbar-row{display:flex;align-items:center;margin-bottom:5px;font-size:10px}
.dbar-name{width:80px;color:#888;flex-shrink:0}
.dbar-bg{flex:1;height:8px;background:#1e2130;border-radius:4px;overflow:hidden}
.dbar-fill{height:100%;border-radius:4px;transition:width .3s}
.dbar-val{width:38px;text-align:right;color:#777}
::-webkit-scrollbar{width:3px}
::-webkit-scrollbar-track{background:#0a0c12}
::-webkit-scrollbar-thumb{background:#333;border-radius:2px}
</style>
</head>
<body>
<div id="layout">
<div id="left-panel">
  <div id="title-bar">
    <h2>EXOCORTEX V2</h2>
    <p>Chunk-Level Map &mdash; Sessions 001&ndash;052</p>
    <p style="color:#444;margin-top:3px;font-size:10px">NCHUNKS chunks &middot; NCORPUS corpus &middot; Feb 17&ndash;Mar 9</p>
  </div>
  <div id="layer-toggles">
    <h3>Layers</h3>
    <label class="trow"><input type="checkbox" id="tog-corpus" checked><span class="tdot" style="background:#f39c12"></span><span class="tlabel">Corpus (NCORPUS)</span></label>
    <label class="trow"><input type="checkbox" id="tog-jake" checked><span class="tdot" style="background:#94c4a8"></span><span class="tlabel">Jake (NJAKE)</span></label>
    <label class="trow"><input type="checkbox" id="tog-opus" checked><span class="tdot" style="background:#b07cc6"></span><span class="tlabel">Opus (NOPUS)</span></label>
    <hr style="border-color:#1e2130;margin:6px 0">
    <label class="trow"><input type="checkbox" id="tog-doc1" checked><span class="tdot" style="background:#4a9eda"></span><span class="tlabel">Doc1 &mdash; 001&ndash;051</span></label>
    <label class="trow"><input type="checkbox" id="tog-doc2" checked><span class="tdot" style="background:#e6a12a"></span><span class="tlabel">Doc2 &mdash; 049&ndash;051</span></label>
    <label class="trow"><input type="checkbox" id="tog-doc3" checked><span class="tdot" style="background:#5ec76e"></span><span class="tlabel">Doc3 &mdash; 052</span></label>
  </div>
  <div id="color-mode">
    <h3>Color By</h3>
    <button class="cbtn active" id="col-speaker" onclick="setColor('speaker')">Speaker (Jake / Opus)</button>
    <button class="cbtn" id="col-date" onclick="setColor('date')">Date / Session</button>
    <button class="cbtn" id="col-domain" onclick="setColor('domain')">Dominant Domain</button>
    <button class="cbtn" id="col-source" onclick="setColor('source')">Source (Doc1 / 2 / 3)</button>
  </div>
  <div id="presets">
    <h3>Jump To</h3>
    <button class="pbtn" onclick="setPreset('all')">All dates</button>
    <button class="pbtn" onclick="setPreset('hinge')">Feb 24 &mdash; Hinge</button>
    <button class="pbtn" onclick="setPreset('start')">Feb 17 &mdash; Start</button>
    <button class="pbtn" onclick="setPreset('feb22')">Feb 22 &mdash; Longest</button>
    <button class="pbtn" onclick="setPreset('late')">Mar 7&ndash;9 &mdash; Latest</button>
    <button class="pbtn" onclick="setPreset('doc3')">Session 052 only</button>
  </div>
  <div id="stats-panel">
    <h3>Visible</h3>
    <div class="stat"><span class="stat-l">Chunks: </span><span id="vis-chunks">&ndash;</span></div>
    <div class="stat"><span class="stat-l">Jake: </span><span id="vis-jake">&ndash;</span></div>
    <div class="stat"><span class="stat-l">Opus: </span><span id="vis-opus">&ndash;</span></div>
    <div class="stat"><span class="stat-l">Dates: </span><span id="vis-dates">&ndash;</span></div>
  </div>
</div>
<div id="main-area">
  <div id="plot-container"><div id="plot"></div></div>
  <div id="timeline-bar">
    <div id="tl-labels"></div>
    <div id="tl-slider-wrap">
      <div id="tl-track"></div>
      <div id="tl-range"></div>
      <div class="tl-handle" id="handle-l"></div>
      <div class="tl-handle" id="handle-r"></div>
    </div>
    <div id="tl-info">All dates selected</div>
  </div>
</div>
<div id="right-panel">
  <div id="inspector">
    <h3>Inspector</h3>
    <div id="inspector-content"><div style="color:#444;font-size:11px">Click a point to inspect</div></div>
  </div>
  <div id="domain-bars">
    <h3>Domain Profile</h3>
    <div id="domain-bar-content"><div style="color:#444;font-size:10px">Select a chunk point</div></div>
  </div>
</div>
</div>
<script>
const DATA = PAYLOAD_PLACEHOLDER;
const DOMAINS = DATA.domains;
const DOM_COL = DATA.domain_colors;
const DATE_COL = DATA.date_colors;
const SRC_COL = DATA.source_colors;
const DATE_ORDER = DATA.date_order;
const chunkPts = DATA.points.filter(p => p.t === 'chunk');
const corpusPts = DATA.points.filter(p => p.t === 'corpus');
let colorMode = 'speaker';
let tlLeft = 0, tlRight = DATE_ORDER.length - 1;
let vis = { corpus:true, jake:true, opus:true, doc1:true, doc2:true, doc3:true };

function getChunkColor(p) {
  if (colorMode === 'speaker') return p.sp === 'Jake' ? '#94c4a8' : '#b07cc6';
  if (colorMode === 'date')    return DATE_COL[p.dt] || '#888';
  if (colorMode === 'domain')  return DOM_COL[p.dom] || '#888';
  if (colorMode === 'source')  return SRC_COL[p.src] || '#888';
  return '#888';
}

function buildTraces() {
  const filtered = chunkPts.filter(p =>
    p.di >= tlLeft && p.di <= tlRight &&
    (p.sp === 'Jake' ? vis.jake : vis.opus) &&
    vis[p.src]
  );
  const traces = [{
    type: 'scatter3d', mode: 'markers',
    x: filtered.map(p=>p.x), y: filtered.map(p=>p.y), z: filtered.map(p=>p.z),
    marker: { size:2.2, color: filtered.map(getChunkColor), opacity:0.76, line:{width:0} },
    text: filtered.map(p => '[' + p.sp + '] ' + p.tx.slice(0,80)),
    customdata: filtered.map(p=>p.id),
    hovertemplate: '%{text}<extra></extra>',
    name: 'Chunks',
  }];
  if (vis.corpus) {
    const ct = { essay:'#f39c12', design_note:'#e74c3c', design_doc:'#e74c3c',
                 letter:'#3498db', journal:'#2ecc71', field_note:'#9b59b6',
                 analysis:'#1abc9c', log:'#95a5a6', index:'#ecf0f1' };
    traces.push({
      type: 'scatter3d', mode: 'markers+text',
      x: corpusPts.map(p=>p.x), y: corpusPts.map(p=>p.y), z: corpusPts.map(p=>p.z),
      marker: { size:5, color: corpusPts.map(p=>ct[p.dt]||'#f39c12'), opacity:0.9,
                symbol:'diamond', line:{width:1,color:'rgba(255,255,255,0.15)'} },
      text: corpusPts.map(p=>p.lb.replace(/_/g,' ').slice(0,22)),
      textfont: {size:7, color:'#aaa'}, textposition:'top center',
      customdata: corpusPts.map(p=>'C:'+p.id),
      hovertemplate: '<b>%{text}</b><extra></extra>',
      name: 'Corpus',
    });
  }
  return traces;
}

const layout = {
  paper_bgcolor:'#0a0c12', plot_bgcolor:'#0a0c12',
  margin:{l:0,r:0,t:0,b:0}, showlegend:false,
  scene:{
    xaxis:{showgrid:false,zeroline:false,showticklabels:false,title:'',backgroundcolor:'#0a0c12'},
    yaxis:{showgrid:false,zeroline:false,showticklabels:false,title:'',backgroundcolor:'#0a0c12'},
    zaxis:{showgrid:false,zeroline:false,showticklabels:false,title:'',backgroundcolor:'#0a0c12'},
    bgcolor:'#0a0c12', camera:{eye:{x:1.4,y:1.4,z:0.9}},
  },
  uirevision:'camera',
};
const cfg = {responsive:true, displayModeBar:false};
Plotly.newPlot('plot', buildTraces(), layout, cfg);

document.getElementById('plot').on('plotly_click', function(evt) {
  const pt = evt.points[0]; if(!pt) return;
  const cid = pt.customdata;
  if (typeof cid === 'string' && cid.startsWith('C:')) {
    const idx = parseInt(cid.slice(2));
    showCorpus(corpusPts[idx]);
  } else {
    const p = DATA.points.find(x => x.t==='chunk' && x.id===cid);
    if (p) showChunk(p);
  }
});

function showChunk(p) {
  document.getElementById('inspector-content').innerHTML =
    fld('Speaker', p.sp) + fld('Date', p.dt) + fld('Source', p.src.toUpperCase()) +
    fld('Turn', '#'+p.tid) + fld('Chunk', (p.ci+1)+' / '+p.tc) + fld('Words', p.wc) +
    fld('Domain', '<span style="color:'+DOM_COL[p.dom]+'">'+p.dom+'</span>') +
    '<div class="itext">'+escHtml(p.tx)+'</div>';
  document.getElementById('domain-bar-content').innerHTML = DOMAINS.map((d,i) => {
    const v = p.ch5[i];
    const pct = Math.min(100, Math.max(0, Math.round(((v-0.35)/0.55)*100)));
    return '<div class="dbar-row">' +
      '<div class="dbar-name" style="color:'+(d===p.dom?DOM_COL[d]:'#888')+'">'+d.slice(0,7)+'</div>' +
      '<div class="dbar-bg"><div class="dbar-fill" style="width:'+pct+'%;background:'+DOM_COL[d]+'"></div></div>' +
      '<div class="dbar-val">'+v.toFixed(3)+'</div></div>';
  }).join('');
}

function showCorpus(p) {
  document.getElementById('inspector-content').innerHTML =
    fld('Type','CORPUS') + fld('Doc', p.lb) + fld('Kind', p.dt) + fld('Author', p.au) +
    '<div class="itext">'+escHtml(p.tx)+'</div>';
  document.getElementById('domain-bar-content').innerHTML =
    '<div style="color:#444;font-size:10px">No domain data for corpus docs</div>';
}

function fld(label, val) {
  return '<div class="ifield"><span class="ilabel">'+label+': </span><span class="ival">'+val+'</span></div>';
}
function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function setColor(mode) {
  colorMode = mode;
  document.querySelectorAll('.cbtn').forEach(b=>b.classList.remove('active'));
  document.getElementById('col-'+mode).classList.add('active');
  redraw();
}

['corpus','jake','opus','doc1','doc2','doc3'].forEach(id => {
  document.getElementById('tog-'+id).addEventListener('change', function() {
    vis[id] = this.checked; redraw();
  });
});

function redraw() {
  Plotly.react('plot', buildTraces(), layout, cfg);
  updateStats();
}

function updateStats() {
  const f = chunkPts.filter(p =>
    p.di >= tlLeft && p.di <= tlRight &&
    (p.sp==='Jake'?vis.jake:vis.opus) && vis[p.src]
  );
  const jc = f.filter(p=>p.sp==='Jake').length;
  const oc = f.filter(p=>p.sp==='Opus').length;
  const dates = [...new Set(f.map(p=>p.dt))].sort((a,b)=>DATE_ORDER.indexOf(a)-DATE_ORDER.indexOf(b));
  document.getElementById('vis-chunks').textContent = f.length.toLocaleString();
  document.getElementById('vis-jake').textContent   = jc.toLocaleString();
  document.getElementById('vis-opus').textContent   = oc.toLocaleString();
  const dl = dates.slice(0,3).join(', ')+(dates.length>3?'...':'');
  document.getElementById('vis-dates').textContent = dates.length+' ('+dl+')';
}

(function() {
  const N = DATE_ORDER.length;
  const tlabels = ['Feb 17','Feb 22','Feb 27','Mar 3','Mar 9'];
  const lDiv = document.getElementById('tl-labels');
  tlabels.forEach(l => { const s=document.createElement('span'); s.textContent=l; lDiv.appendChild(s); });
  const wrap=document.getElementById('tl-slider-wrap');
  const rangeEl=document.getElementById('tl-range');
  const hl=document.getElementById('handle-l');
  const hr=document.getElementById('handle-r');
  let drag=null;
  function posOf(i){ return (i/(N-1))*100; }
  function idxOf(pct){ return Math.round(pct*(N-1)/100); }
  function sync() {
    const lp=posOf(tlLeft), rp=posOf(tlRight);
    rangeEl.style.left=lp+'%'; rangeEl.style.width=(rp-lp)+'%';
    hl.style.left=lp+'%'; hr.style.left=rp+'%';
    document.getElementById('tl-info').textContent =
      (tlLeft===0&&tlRight===N-1) ? 'All dates selected'
        : DATE_ORDER[tlLeft]+' \u2192 '+DATE_ORDER[tlRight];
    redraw();
  }
  function onMove(e) {
    if (!drag) return;
    const rect=wrap.getBoundingClientRect();
    const cx=e.touches?e.touches[0].clientX:e.clientX;
    let pct=Math.max(0,Math.min(100,((cx-rect.left)/rect.width)*100));
    const idx=idxOf(pct);
    if (drag==='l') tlLeft=Math.min(idx,tlRight); else tlRight=Math.max(idx,tlLeft);
    sync();
  }
  hl.addEventListener('mousedown',()=>drag='l');
  hr.addEventListener('mousedown',()=>drag='r');
  document.addEventListener('mouseup',()=>drag=null);
  document.addEventListener('mousemove',onMove);
  hl.addEventListener('touchstart',()=>drag='l',{passive:true});
  hr.addEventListener('touchstart',()=>drag='r',{passive:true});
  document.addEventListener('touchend',()=>drag=null);
  document.addEventListener('touchmove',onMove,{passive:true});
  sync();
})();

function setPreset(name) {
  const p={
    all:[0,DATE_ORDER.length-1],
    hinge:[DATE_ORDER.indexOf('Feb 24'),DATE_ORDER.indexOf('Feb 24')],
    start:[DATE_ORDER.indexOf('Feb 17'),DATE_ORDER.indexOf('Feb 17')],
    feb22:[DATE_ORDER.indexOf('Feb 22'),DATE_ORDER.indexOf('Feb 22')],
    late:[DATE_ORDER.indexOf('Mar 7'),DATE_ORDER.indexOf('Mar 9')],
    doc3:[DATE_ORDER.indexOf('Mar 8'),DATE_ORDER.indexOf('Mar 9')],
  };
  [tlLeft,tlRight]=p[name]||[0,DATE_ORDER.length-1];
  tlLeft=Math.max(0,tlLeft); tlRight=Math.min(DATE_ORDER.length-1,tlRight);
  const N=DATE_ORDER.length;
  document.getElementById('handle-l').style.left=(tlLeft/(N-1)*100)+'%';
  document.getElementById('handle-r').style.left=(tlRight/(N-1)*100)+'%';
  document.getElementById('tl-range').style.left=(tlLeft/(N-1)*100)+'%';
  document.getElementById('tl-range').style.width=((tlRight-tlLeft)/(N-1)*100)+'%';
  document.getElementById('tl-info').textContent =
    (tlLeft===0&&tlRight===N-1)?'All dates selected':DATE_ORDER[tlLeft]+' \u2192 '+DATE_ORDER[tlRight];
  redraw();
}

updateStats();
</script>
</body>
</html>"""

# Substitute placeholders
html = (html
    .replace("NCHUNKS", str(n_chunks))
    .replace("NCORPUS", str(n_corpus))
    .replace("NJAKE",   str(n_jake))
    .replace("NOPUS",   str(n_opus))
    .replace("PAYLOAD_PLACEHOLDER", payload)
)

OUT.write_text(html, encoding="utf-8")
print(f"Written: {OUT}")
print(f"Size: {OUT.stat().st_size // 1024} KB")
