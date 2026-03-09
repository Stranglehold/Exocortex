"""
build_visualization.py — Build the unified interactive visualization HTML.

Reads all analysis outputs and generates a single self-contained HTML page
with a 3D scatter plot, timeline range filter, layer toggles, and side panels.

Requires:
    data/umap_full.json
    data/session_signatures.json
    data/recurrence_matrix.json
    data/speaker_coupling.json
    data/sliding_window_trajectory.json
    data/information_flow.json
    data/entropy_trace.json
    data/cumulative_drift.json
    data/transition_matrix.json
    data/response_vectors_full.json   (optional — from response vector pipeline)

Output:
    data/full_suite_visualization.html
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"

OUT_HTML = DATA / "full_suite_visualization.html"

DOMAIN_COLORS = {
    'philosophical': '#9b59b6',
    'operational':   '#e67e22',
    'reflective':    '#2ecc71',
    'relational':    '#3498db',
    'mixed':         '#95a5a6',
}

DATE_COLOR_MAP = {
    'Feb 17': '#1a1a2e', 'Feb 18': '#16213e', 'Feb 19': '#0f3460',
    'Feb 20': '#533483', 'Feb 21': '#e94560', 'Feb 22': '#c84b31',
    'Feb 23': '#ecb365', 'Feb 24': '#f5cba7', 'Feb 25': '#a8e6cf',
    'Feb 26': '#3d84a8', 'Feb 27': '#46cdcf', 'Feb 28': '#48466d',
    'Mar 1':  '#3c3f58', 'Mar 2':  '#2b4162', 'Mar 3':  '#12a4d9',
    'Mar 4':  '#00b4d8', 'Mar 5':  '#90e0ef', 'Mar 6':  '#caf0f8',
    'unknown': '#aaaaaa',
}


def safe_load(path: Path, default=None):
    """Load JSON file if it exists."""
    if not path.exists():
        print(f"  [MISSING] {path.name}")
        return default
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def truncate(text: str, n: int = 150) -> str:
    return text[:n] + '...' if len(text) > n else text


def build_html(data: dict) -> str:
    """Generate the full HTML page."""

    # Serialize data for JavaScript embedding
    js_data = json.dumps(data, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Exocortex — Full Collaboration Analysis Suite</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js" charset="utf-8"></script>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #0a0c12; color: #ccc; font-family: 'Courier New', monospace; font-size: 12px; overflow: hidden; }}

#layout {{ display: flex; height: 100vh; }}
#left-panel {{ width: 220px; flex-shrink: 0; background: #111318; border-right: 1px solid #222; display: flex; flex-direction: column; overflow: hidden; }}
#main-area {{ flex: 1; display: flex; flex-direction: column; overflow: hidden; }}
#right-panel {{ width: 300px; flex-shrink: 0; background: #0e1018; border-left: 1px solid #222; overflow-y: auto; }}

/* Left panel */
#title-bar {{ padding: 10px 12px; border-bottom: 1px solid #222; }}
#title-bar h2 {{ font-size: 11px; color: #7ec8e3; letter-spacing: 0.5px; }}
#title-bar p {{ font-size: 10px; color: #555; margin-top: 2px; }}

#layer-toggles {{ padding: 10px 12px; border-bottom: 1px solid #222; }}
#layer-toggles h3 {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
.toggle-row {{ display: flex; align-items: center; margin-bottom: 6px; cursor: pointer; }}
.toggle-row input {{ margin-right: 8px; cursor: pointer; }}
.toggle-label {{ font-size: 11px; color: #bbb; }}
.toggle-dot {{ width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; flex-shrink: 0; }}

#color-mode {{ padding: 10px 12px; border-bottom: 1px solid #222; }}
#color-mode h3 {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
.color-btn {{ background: #1a1d25; border: 1px solid #333; color: #aaa; padding: 4px 8px; cursor: pointer; font-family: inherit; font-size: 10px; margin-bottom: 4px; width: 100%; text-align: left; }}
.color-btn.active {{ border-color: #7ec8e3; color: #7ec8e3; }}

#presets {{ padding: 10px 12px; border-bottom: 1px solid #222; }}
#presets h3 {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
.preset-btn {{ background: #1a1d25; border: 1px solid #333; color: #aaa; padding: 4px 8px; cursor: pointer; font-family: inherit; font-size: 10px; margin-bottom: 4px; width: 100%; text-align: left; }}
.preset-btn:hover {{ border-color: #555; color: #ddd; }}

#inspector {{ flex: 1; padding: 10px 12px; overflow-y: auto; }}
#inspector h3 {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
#inspector-content {{ font-size: 11px; line-height: 1.6; color: #aaa; }}
#inspector-content .field {{ margin-bottom: 4px; }}
#inspector-content .label {{ color: #666; }}
#inspector-content .value {{ color: #ccc; }}
#inspector-content .preview {{ margin-top: 8px; color: #999; border-top: 1px solid #222; padding-top: 8px; line-height: 1.5; }}

/* Main area */
#plot-container {{ flex: 1; position: relative; }}
#plot {{ width: 100%; height: 100%; }}

#timeline-bar {{ height: 80px; background: #0d0f18; border-top: 1px solid #1e2130; padding: 8px 12px; display: flex; flex-direction: column; }}
#timeline-labels {{ display: flex; justify-content: space-between; font-size: 9px; color: #555; margin-bottom: 4px; }}
#timeline-slider-wrap {{ position: relative; height: 24px; }}
#timeline-track {{ position: absolute; top: 10px; left: 0; right: 0; height: 4px; background: #1e2130; border-radius: 2px; }}
#timeline-range {{ position: absolute; top: 10px; left: 0; right: 0; height: 4px; background: #3a8ec4; border-radius: 2px; }}
#handle-left, #handle-right {{ position: absolute; top: 4px; width: 16px; height: 16px; background: #7ec8e3; border-radius: 50%; cursor: ew-resize; transform: translateX(-8px); border: 2px solid #0a0c12; }}
#timeline-info {{ font-size: 10px; color: #7ec8e3; margin-top: 4px; }}

/* Side panel */
#right-panel h3 {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; padding: 10px 12px; border-bottom: 1px solid #222; }}
.chart-panel {{ padding: 8px 12px; border-bottom: 1px solid #1a1d25; }}
.chart-panel .chart-title {{ font-size: 10px; color: #7ec8e3; margin-bottom: 6px; }}
.chart-div {{ height: 100px; }}
.stat-row {{ font-size: 10px; color: #aaa; margin: 2px 0; }}
.stat-label {{ color: #555; }}
.matrix-wrap {{ overflow-x: auto; padding: 4px 0; }}
.matrix-cell {{ display: inline-block; width: 40px; height: 28px; line-height: 28px; text-align: center; font-size: 9px; margin: 1px; }}

/* Scrollbar */
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: #0a0c12; }}
::-webkit-scrollbar-thumb {{ background: #333; border-radius: 2px; }}
</style>
</head>
<body>
<div id="layout">

<!-- Left Panel -->
<div id="left-panel">
  <div id="title-bar">
    <h2>EXOCORTEX</h2>
    <p>Full Collaboration — Sessions 001–051</p>
    <p id="turn-count-display" style="color:#555; margin-top:4px;"></p>
  </div>

  <div id="layer-toggles">
    <h3>Layers</h3>
    <label class="toggle-row"><input type="checkbox" id="tog-corpus" checked><span class="toggle-dot" style="background:#f39c12;"></span><span class="toggle-label">Corpus (51)</span></label>
    <label class="toggle-row"><input type="checkbox" id="tog-jake" checked><span class="toggle-dot" style="background:#94c4a8;"></span><span class="toggle-label">Jake turns</span></label>
    <label class="toggle-row"><input type="checkbox" id="tog-opus" checked><span class="toggle-dot" style="background:#b07cc6;"></span><span class="toggle-label">Opus turns</span></label>
    <label class="toggle-row"><input type="checkbox" id="tog-sessions" checked><span class="toggle-dot" style="background:#7ec8e3;"></span><span class="toggle-label">Session signatures</span></label>
    <label class="toggle-row"><input type="checkbox" id="tog-trajectory"><span class="toggle-dot" style="background:#e74c3c;"></span><span class="toggle-label">Trajectory path</span></label>
    <label class="toggle-row"><input type="checkbox" id="tog-vectors"><span class="toggle-dot" style="background:#3498db;"></span><span class="toggle-label">Response vectors</span></label>
    <label class="toggle-row"><input type="checkbox" id="tog-bridges" checked><span class="toggle-dot" style="background:#f39c12;"></span><span class="toggle-label">Corpus bridge sizes</span></label>
    <label class="toggle-row"><input type="checkbox" id="tog-spikes"><span class="toggle-dot" style="background:#ff6b6b;"></span><span class="toggle-label">Novelty spikes</span></label>
  </div>

  <div id="color-mode">
    <h3>Color By</h3>
    <button class="color-btn active" id="col-speaker" onclick="setColorMode('speaker')">Speaker (Jake/Opus)</button>
    <button class="color-btn" id="col-register" onclick="setColorMode('register')">Register</button>
    <button class="color-btn" id="col-date" onclick="setColorMode('date')">Date / Session</button>
  </div>

  <div id="presets">
    <h3>Jump To</h3>
    <button class="preset-btn" onclick="setPreset('all')">All Turns</button>
    <button class="preset-btn" onclick="setPreset('hinge')">Feb 24 (Hinge)</button>
    <button class="preset-btn" onclick="setPreset('feb17')">Feb 17 (Start)</button>
    <button class="preset-btn" onclick="setPreset('late')">Mar 7-8 (Latest)</button>
    <button class="preset-btn" onclick="setPreset('feb22')">Feb 22 (Longest Day)</button>
  </div>

  <div id="inspector">
    <h3>Inspector</h3>
    <div id="inspector-content">
      <div style="color:#555; font-style:italic;">Click any point to inspect</div>
    </div>
  </div>
</div>

<!-- Main Area -->
<div id="main-area">
  <div id="plot-container">
    <div id="plot"></div>
  </div>

  <div id="timeline-bar">
    <div id="timeline-labels" id="tl-labels"></div>
    <div id="timeline-slider-wrap">
      <div id="timeline-track"></div>
      <div id="timeline-range"></div>
      <div id="handle-left"></div>
      <div id="handle-right"></div>
    </div>
    <div id="timeline-info">Showing all 1,934 turns — drag handles to filter</div>
  </div>
</div>

<!-- Right Panel -->
<div id="right-panel">
  <h3>Analysis Panels</h3>

  <div class="chart-panel">
    <div class="chart-title">A3: Inter-Speaker Distance</div>
    <div id="chart-coupling" class="chart-div"></div>
  </div>

  <div class="chart-panel">
    <div class="chart-title">A6: Register Entropy</div>
    <div id="chart-entropy" class="chart-div"></div>
  </div>

  <div class="chart-panel">
    <div class="chart-title">A7: Cumulative Drift</div>
    <div id="chart-drift" class="chart-div"></div>
  </div>

  <div class="chart-panel">
    <div class="chart-title">A5: Information Flow</div>
    <div id="chart-flow" class="chart-div"></div>
  </div>

  <div class="chart-panel">
    <div class="chart-title">A8: Transition Matrix (Full)</div>
    <div id="chart-matrix" class="chart-div" style="height:160px;"></div>
    <div id="matrix-stats" style="margin-top:4px;"></div>
  </div>

  <div class="chart-panel">
    <div class="chart-title">A1: Session Arc Lengths</div>
    <div id="chart-sessions" class="chart-div"></div>
  </div>

  <div class="chart-panel">
    <div class="chart-title">A2: Recurrence Heatmap</div>
    <div id="chart-recurrence" class="chart-div" style="height:180px;"></div>
  </div>

  <div class="chart-panel">
    <div class="chart-title">A15: Signal Density (Novelty)</div>
    <div id="chart-novelty" class="chart-div"></div>
    <div id="novelty-stats" style="margin-top:4px;font-size:10px;color:#666;"></div>
  </div>

  <div class="chart-panel">
    <div class="chart-title">A10: Betti Numbers (Topology)</div>
    <div id="chart-betti" class="chart-div"></div>
  </div>

  <div class="chart-panel">
    <div class="chart-title">A11: Top Bridging Concepts</div>
    <div id="chart-bridges" class="chart-div" style="height:160px;"></div>
  </div>

</div>

</div>

<script>
// ── Embedded data ──────────────────────────────────────────────────────────
const SUITE = {js_data};

// ── Constants ───────────────────────────────────────────────────────────────
const SPEAKER_COLORS = {{ Jake: '#94c4a8', Opus: '#b07cc6' }};
const DOMAIN_COLORS = {{
  philosophical: '#9b59b6', operational: '#e67e22',
  reflective: '#2ecc71', relational: '#3498db', mixed: '#95a5a6'
}};
const DATE_COLORS = {json.dumps(DATE_COLOR_MAP)};

// ── State ───────────────────────────────────────────────────────────────────
let colorMode = 'speaker';
let rangeMin = 0, rangeMax = 1;
let totalTurns = (SUITE.umap && SUITE.umap.turns) ? SUITE.umap.turns.length : 0;

function turnRange() {{
  return [
    Math.round(rangeMin * totalTurns),
    Math.round(rangeMax * totalTurns)
  ];
}}

// ── Layer visibility ────────────────────────────────────────────────────────
function getLayerVisibility() {{
  return {{
    corpus:     document.getElementById('tog-corpus').checked,
    jake:       document.getElementById('tog-jake').checked,
    opus:       document.getElementById('tog-opus').checked,
    sessions:   document.getElementById('tog-sessions').checked,
    trajectory: document.getElementById('tog-trajectory').checked,
    vectors:    document.getElementById('tog-vectors').checked,
    bridges:    document.getElementById('tog-bridges').checked,
    spikes:     document.getElementById('tog-spikes').checked,
  }};
}}

['tog-corpus','tog-jake','tog-opus','tog-sessions','tog-trajectory','tog-vectors','tog-bridges','tog-spikes'].forEach(id => {{
  document.getElementById(id).addEventListener('change', redrawMain);
}});

// ── Color mode ───────────────────────────────────────────────────────────────
function setColorMode(mode) {{
  colorMode = mode;
  ['speaker','register','date'].forEach(m => {{
    document.getElementById('col-'+m).classList.toggle('active', m === mode);
  }});
  redrawMain();
}}

function turnColor(t) {{
  if (colorMode === 'speaker') return SPEAKER_COLORS[t.speaker] || '#888';
  if (colorMode === 'register') return DOMAIN_COLORS[t.dominant_register] || '#888';
  if (colorMode === 'date') return DATE_COLORS[t.date] || '#888';
  return '#888';
}}

// ── Presets ──────────────────────────────────────────────────────────────────
const DATE_RANGE_MAP = {{
  all:   [0, 1],
  feb17: null, hinge: null, feb22: null, late: null,
}};

function setPreset(name) {{
  if (!SUITE.umap || !SUITE.umap.turns) return;
  const turns = SUITE.umap.turns;
  const n = turns.length;
  let start = 0, end = n;
  if (name === 'all') {{ start = 0; end = n; }}
  else if (name === 'hinge') {{
    const f24 = turns.filter(t => t.date === 'Feb 24');
    if (f24.length) {{
      const indices = f24.map(t => turns.indexOf(t));
      start = Math.max(0, Math.min(...indices) - 5);
      end = Math.min(n, Math.max(...indices) + 5);
    }}
  }} else if (name === 'feb17') {{
    const f17 = turns.filter(t => t.date === 'Feb 17');
    if (f17.length) {{
      const indices = f17.map(t => turns.indexOf(t));
      start = 0; end = Math.min(n, Math.max(...indices) + 5);
    }}
  }} else if (name === 'feb22') {{
    const f22 = turns.filter(t => t.date === 'Feb 22');
    if (f22.length) {{
      const indices = f22.map(t => turns.indexOf(t));
      start = Math.max(0, Math.min(...indices) - 5);
      end = Math.min(n, Math.max(...indices) + 5);
    }}
  }} else if (name === 'late') {{
    start = Math.max(0, n - 120); end = n;
  }}
  rangeMin = start / n;
  rangeMax = end / n;
  updateSliderUI();
  redrawMain();
}}

// ── Timeline slider ──────────────────────────────────────────────────────────
const hL = document.getElementById('handle-left');
const hR = document.getElementById('handle-right');
const tRange = document.getElementById('timeline-range');
const tInfo = document.getElementById('timeline-info');
const tWrap = document.getElementById('timeline-slider-wrap');

function updateSliderUI() {{
  const leftPct = rangeMin * 100;
  const rightPct = rangeMax * 100;
  hL.style.left = leftPct + '%';
  hR.style.left = rightPct + '%';
  tRange.style.left = leftPct + '%';
  tRange.style.width = (rightPct - leftPct) + '%';

  const [s, e] = turnRange();
  const count = e - s;
  tInfo.textContent = `Showing turns ${{s}}-${{e}} (${{count}} turns)`;
  document.getElementById('turn-count-display').textContent = `${{count}} / ${{totalTurns}} turns`;
}}

function makeDraggable(handle, isLeft) {{
  let dragging = false;
  handle.addEventListener('mousedown', e => {{ dragging = true; e.preventDefault(); }});
  document.addEventListener('mousemove', e => {{
    if (!dragging) return;
    const rect = tWrap.getBoundingClientRect();
    let pct = (e.clientX - rect.left) / rect.width;
    pct = Math.max(0, Math.min(1, pct));
    if (isLeft) {{
      rangeMin = Math.min(pct, rangeMax - 0.01);
    }} else {{
      rangeMax = Math.max(pct, rangeMin + 0.01);
    }}
    updateSliderUI();
    redrawMain();
  }});
  document.addEventListener('mouseup', () => {{ dragging = false; }});
}}
makeDraggable(hL, true);
makeDraggable(hR, false);

// Timeline labels
function buildTimelineLabels() {{
  const labelDiv = document.getElementById('timeline-labels');
  if (!SUITE.sessions) return;
  const sessions = SUITE.sessions.sessions;
  const n = totalTurns;
  sessions.forEach(s => {{
    const pct = s.turn_range[0] / n * 100;
    const span = document.createElement('span');
    span.textContent = s.date;
    span.style.position = 'absolute';
    span.style.left = pct + '%';
    span.style.transform = 'translateX(-50%)';
    labelDiv.style.position = 'relative';
    labelDiv.appendChild(span);
  }});
}}

// ── 3D Plot ──────────────────────────────────────────────────────────────────
const PLOTLY_LAYOUT = {{
  paper_bgcolor: '#0a0c12',
  plot_bgcolor: '#0a0c12',
  font: {{ color: '#888', size: 10 }},
  margin: {{ l: 0, r: 0, t: 0, b: 0 }},
  scene: {{
    xaxis: {{ title: '', backgroundcolor: '#0d0f18', gridcolor: '#1a1d25', color: '#444', showticklabels: false }},
    yaxis: {{ title: '', backgroundcolor: '#0d0f18', gridcolor: '#1a1d25', color: '#444', showticklabels: false }},
    zaxis: {{ title: '', backgroundcolor: '#0d0f18', gridcolor: '#1a1d25', color: '#444', showticklabels: false }},
    bgcolor: '#0d0f18',
    camera: {{ eye: {{ x: 1.5, y: 1.5, z: 1.2 }} }}
  }},
  showlegend: false,
  uirevision: 'keep',
}};

function buildTraces() {{
  const traces = [];
  const vis = getLayerVisibility();
  const [rStart, rEnd] = turnRange();

  if (!SUITE.umap) return traces;
  const umap = SUITE.umap;

  // Filter function
  const inRange = (t, idx) => idx >= rStart && idx < rEnd;

  // Corpus
  if (vis.corpus && umap.corpus) {{
    const cx = [], cy = [], cz = [], ct = [];
    umap.corpus.forEach(c => {{
      cx.push(c.umap_x); cy.push(c.umap_y); cz.push(c.umap_z);
      ct.push(`<b>${{c.source_file}}</b><br>Author: ${{c.author}}<br>Quality: ${{c.quality_signal}}`);
    }});
    traces.push({{
      type: 'scatter3d', mode: 'markers', name: 'Corpus',
      x: cx, y: cy, z: cz,
      marker: {{ size: 6, color: '#f39c12', opacity: 0.9,
                 symbol: 'diamond', line: {{ color: '#333', width: 0.5 }} }},
      hovertext: ct, hoverinfo: 'text',
      customdata: umap.corpus.map((c,i) => ({{ type:'corpus', idx:i, data:c }})),
    }});
  }}

  // Jake turns
  if (vis.jake && umap.turns) {{
    const turns = umap.turns.filter((t,i) => t.speaker === 'Jake' && inRange(t,i));
    if (turns.length) {{
      traces.push({{
        type: 'scatter3d', mode: 'markers', name: 'Jake',
        x: turns.map(t=>t.umap_x), y: turns.map(t=>t.umap_y), z: turns.map(t=>t.umap_z),
        marker: {{ size: 2.5, color: turns.map(t => turnColor(t)), opacity: 0.5 }},
        hovertext: turns.map(t => `<b>Jake T${{t.turn}}</b> [${{t.date}}]<br>${{t.word_count}}w<br><br>${{t.content_preview.slice(0,120)}}`),
        hoverinfo: 'text',
        customdata: turns.map(t => ({{ type:'turn', data:t }})),
      }});
    }}
  }}

  // Opus turns
  if (vis.opus && umap.turns) {{
    const turns = umap.turns.filter((t,i) => t.speaker === 'Opus' && inRange(t,i));
    if (turns.length) {{
      traces.push({{
        type: 'scatter3d', mode: 'markers', name: 'Opus',
        x: turns.map(t=>t.umap_x), y: turns.map(t=>t.umap_y), z: turns.map(t=>t.umap_z),
        marker: {{ size: 2.5, color: turns.map(t => turnColor(t)), opacity: 0.5 }},
        hovertext: turns.map(t => `<b>Opus T${{t.turn}}</b> [${{t.date}}]<br>${{t.word_count}}w<br><br>${{t.content_preview.slice(0,120)}}`),
        hoverinfo: 'text',
        customdata: turns.map(t => ({{ type:'turn', data:t }})),
      }});
    }}
  }}

  // Session signatures
  if (vis.sessions && SUITE.sessions) {{
    const sessions = SUITE.sessions.sessions;
    const filtered = sessions.filter(s => {{
      const midTurn = (s.turn_range[0] + s.turn_range[1]) / 2;
      return midTurn >= rStart && midTurn <= rEnd;
    }});
    if (filtered.length) {{
      traces.push({{
        type: 'scatter3d', mode: 'markers+text', name: 'Sessions',
        x: filtered.map(s=>s.umap_x), y: filtered.map(s=>s.umap_y), z: filtered.map(s=>s.umap_z),
        marker: {{
          size: filtered.map(s => 8 + s.internal_arc_length * 0.5),
          color: filtered.map(s => DATE_COLORS[s.date] || '#7ec8e3'),
          opacity: 0.9,
          line: {{ color: '#7ec8e3', width: 2 }},
        }},
        text: filtered.map(s => s.date),
        textposition: 'top center',
        textfont: {{ size: 9, color: '#7ec8e3' }},
        hovertext: filtered.map(s =>
          `<b>${{s.date}}</b><br>${{s.turn_count}} turns (Opus: ${{s.opus_count}}, Jake: ${{s.jake_count}})<br>`+
          `Register: ${{s.dominant_register}}<br>`+
          `Arc length: ${{s.internal_arc_length.toFixed(2)}}<br>`+
          `Entropy: ${{s.entropy.toFixed(3)}}`
        ),
        hoverinfo: 'text',
        customdata: filtered.map(s => ({{ type:'session', data:s }})),
      }});

      // Connect sessions chronologically
      traces.push({{
        type: 'scatter3d', mode: 'lines', name: 'Session arc',
        x: filtered.map(s=>s.umap_x), y: filtered.map(s=>s.umap_y), z: filtered.map(s=>s.umap_z),
        line: {{ color: '#7ec8e3', width: 1 }}, opacity: 0.3, hoverinfo: 'none',
      }});
    }}
  }}

  // Sliding window trajectory
  if (vis.trajectory && SUITE.trajectory) {{
    const pts = SUITE.trajectory.points.filter(p => {{
      const idx = umap.turns ? umap.turns.findIndex(t => t.turn === p.center_turn) : -1;
      return idx >= rStart && idx < rEnd;
    }});
    if (pts.length) {{
      // Color by velocity (normalized)
      const vels = pts.map(p => p.velocity_magnitude);
      const maxV = Math.max(...vels, 0.001);
      traces.push({{
        type: 'scatter3d', mode: 'lines', name: 'Trajectory',
        x: pts.map(p=>p.umap_x), y: pts.map(p=>p.umap_y), z: pts.map(p=>p.umap_z),
        line: {{ color: '#e74c3c', width: 3 }}, opacity: 0.7, hoverinfo: 'none',
      }});
      // Peak acceleration markers
      const peaks = (SUITE.trajectory.peak_accelerations || []).filter(p => {{
        const idx = umap.turns ? umap.turns.findIndex(t => t.turn === p.center_turn) : -1;
        return idx >= rStart && idx < rEnd;
      }});
      if (peaks.length) {{
        const peakPts = peaks.map(pa => pts.find(p => p.center_turn === pa.center_turn)).filter(Boolean);
        if (peakPts.length) {{
          traces.push({{
            type: 'scatter3d', mode: 'markers', name: 'Turn points',
            x: peakPts.map(p=>p.umap_x), y: peakPts.map(p=>p.umap_y), z: peakPts.map(p=>p.umap_z),
            marker: {{ size: 6, color: '#ff6b6b', opacity: 0.9, symbol: 'cross' }},
            hovertext: peakPts.map(p => `<b>Register shift</b><br>T${{p.center_turn}} [${{p.center_date}}]<br>Register: ${{p.dominant_register}}<br>Accel: ${{p.acceleration_magnitude.toFixed(3)}}`),
            hoverinfo: 'text',
          }});
        }}
      }}
    }}
  }}

  // Response vectors
  if (vis.vectors && SUITE.response_vectors && umap.turns) {{
    const pairs = (SUITE.response_vectors.pairs || []);
    const turnByNum = {{}};
    umap.turns.forEach((t,i) => {{ turnByNum[t.turn] = i; }});

    const xs=[], ys=[], zs=[], hover=[];
    pairs.forEach(p => {{
      const ji = turnByNum[p.jake_turn];
      const oi = turnByNum[p.opus_turn];
      if (ji === undefined || oi === undefined) return;
      if (ji < rStart || ji >= rEnd) return;
      const jt = umap.turns[ji], ot = umap.turns[oi];
      xs.push(jt.umap_x, ot.umap_x, null);
      ys.push(jt.umap_y, ot.umap_y, null);
      zs.push(jt.umap_z, ot.umap_z, null);
    }});
    if (xs.length) {{
      traces.push({{
        type: 'scatter3d', mode: 'lines', name: 'Response vectors',
        x: xs, y: ys, z: zs,
        line: {{ color: '#3498db', width: 1 }}, opacity: 0.4, hoverinfo: 'none',
      }});
    }}
  }}

  // A11: Corpus markers sized by bridge score (replaces flat corpus layer when tog-bridges on)
  if (vis.bridges && SUITE.bridges && umap.corpus) {{
    const docs = SUITE.bridges.documents || [];
    const maxBridge = Math.max(...docs.map(d => d.bridge_score), 0.01);
    traces.push({{
      type: 'scatter3d', mode: 'markers', name: 'Bridge anchors',
      x: umap.corpus.map(c => c.umap_x),
      y: umap.corpus.map(c => c.umap_y),
      z: umap.corpus.map(c => c.umap_z),
      marker: {{
        size: umap.corpus.map((c, i) => {{
          const d = docs.find(dd => dd.corpus_idx === i);
          return d ? 4 + d.bridge_score / maxBridge * 16 : 4;
        }}),
        color: umap.corpus.map((c, i) => {{
          const d = docs.find(dd => dd.corpus_idx === i);
          if (!d) return '#555';
          if (d.bridge_score > 0.6) return '#e67e22';
          if (d.bridge_score > 0.3) return '#f39c12';
          return '#7f8c8d';
        }}),
        opacity: 0.9,
        line: {{ color: '#333', width: 0.5 }},
      }},
      hovertext: umap.corpus.map((c, i) => {{
        const d = docs.find(dd => dd.corpus_idx === i);
        return d
          ? `<b>${{c.source_file}}</b><br>Bridge: ${{d.bridge_score.toFixed(2)}}<br>${{d.session_count}} sessions, ${{d.total_references}} refs`
          : `<b>${{c.source_file}}</b>`;
      }}),
      hoverinfo: 'text',
      customdata: umap.corpus.map((c,i) => ({{ type:'corpus', idx:i, data:c }})),
    }});
  }}

  // A15: Novelty spike markers in 3D space
  if (vis.spikes && SUITE.novelty && umap.turns) {{
    const spikes = SUITE.novelty.novelty_spikes || [];
    const turnByNum = {{}};
    umap.turns.forEach((t,i) => {{ turnByNum[t.turn] = i; }});
    const spikePoints = spikes
      .filter(s => {{ const idx = turnByNum[s.turn]; return idx !== undefined && idx >= rStart && idx < rEnd; }})
      .map(s => ({{ ...s, umap: umap.turns[turnByNum[s.turn]] }}));
    if (spikePoints.length) {{
      traces.push({{
        type: 'scatter3d', mode: 'markers', name: 'Novelty spikes',
        x: spikePoints.map(s => s.umap.umap_x),
        y: spikePoints.map(s => s.umap.umap_y),
        z: spikePoints.map(s => s.umap.umap_z),
        marker: {{ size: 7, color: '#ff6b6b', symbol: 'cross', opacity: 0.9,
                   line: {{ color: '#ff0000', width: 1 }} }},
        hovertext: spikePoints.map(s =>
          `<b>NOVELTY SPIKE</b> T${{s.turn}} [${{s.date}}]<br>${{s.speaker}} | novelty: ${{s.novelty.toFixed(3)}}<br><br>${{s.text_preview}}`),
        hoverinfo: 'text',
      }});
    }}
  }}

  return traces;
}}

function redrawMain() {{
  const traces = buildTraces();
  Plotly.react('plot', traces, PLOTLY_LAYOUT, {{
    responsive: true, displayModeBar: false,
  }});
}}

// Inspector on click
document.getElementById('plot').on = undefined;
document.addEventListener('DOMContentLoaded', () => {{
  const plotDiv = document.getElementById('plot');
  plotDiv.on('plotly_click', function(data) {{
    const pt = data.points[0];
    if (!pt || !pt.customdata) return;
    const d = pt.customdata;
    const el = document.getElementById('inspector-content');

    if (d.type === 'corpus') {{
      const c = d.data;
      el.innerHTML = `
        <div class="field"><span class="label">Type: </span><span class="value">Corpus document</span></div>
        <div class="field"><span class="label">File: </span><span class="value">${{c.source_file}}</span></div>
        <div class="field"><span class="label">Author: </span><span class="value">${{c.author || 'unknown'}}</span></div>
        <div class="field"><span class="label">Quality: </span><span class="value">${{c.quality_signal || 'unrated'}}</span></div>
      `;
    }} else if (d.type === 'turn') {{
      const t = d.data;
      el.innerHTML = `
        <div class="field"><span class="label">Turn: </span><span class="value">#${{t.turn}}</span></div>
        <div class="field"><span class="label">Speaker: </span><span class="value" style="color:${{SPEAKER_COLORS[t.speaker]}}">${{t.speaker}}</span></div>
        <div class="field"><span class="label">Date: </span><span class="value">${{t.date}}</span></div>
        <div class="field"><span class="label">Words: </span><span class="value">${{t.word_count}}</span></div>
        <div class="field"><span class="label">Register: </span><span class="value" style="color:${{DOMAIN_COLORS[t.dominant_register] || '#888'}}">${{t.dominant_register || 'unclassified'}}</span></div>
        <div class="preview">${{t.content_preview}}</div>
      `;
    }} else if (d.type === 'session') {{
      const s = d.data;
      el.innerHTML = `
        <div class="field"><span class="label">Date: </span><span class="value">${{s.date}}</span></div>
        <div class="field"><span class="label">Turns: </span><span class="value">${{s.turn_count}} (Opus: ${{s.opus_count}}, Jake: ${{s.jake_count}})</span></div>
        <div class="field"><span class="label">Register: </span><span class="value" style="color:${{DOMAIN_COLORS[s.dominant_register]}}">${{s.dominant_register}}</span></div>
        <div class="field"><span class="label">Arc length: </span><span class="value">${{s.internal_arc_length.toFixed(3)}}</span></div>
        <div class="field"><span class="label">Entropy: </span><span class="value">${{s.entropy.toFixed(3)}}</span></div>
      `;
    }}
  }});
}});

// ── Side panel charts ────────────────────────────────────────────────────────
const PANEL_LAYOUT = {{
  paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
  font: {{ color: '#666', size: 9 }}, margin: {{ l: 35, r: 8, t: 5, b: 25 }},
  xaxis: {{ gridcolor: '#1a1d25', color: '#444', tickfont: {{ size: 8 }} }},
  yaxis: {{ gridcolor: '#1a1d25', color: '#444', tickfont: {{ size: 8 }} }},
  showlegend: false,
}};

function buildSidePanels() {{
  // A3: Speaker coupling
  if (SUITE.coupling && SUITE.coupling.smoothed_distance) {{
    const sd = SUITE.coupling.smoothed_distance;
    Plotly.newPlot('chart-coupling', [{{
      type: 'scatter', mode: 'lines',
      x: SUITE.coupling.pairs.map(p => p.position),
      y: sd,
      line: {{ color: '#7ec8e3', width: 1 }},
      fill: 'tozeroy', fillcolor: 'rgba(126,200,227,0.1)',
    }}], {{ ...PANEL_LAYOUT, yaxis: {{ ...PANEL_LAYOUT.yaxis, title: 'dist' }} }},
    {{ displayModeBar: false, responsive: true }});
  }}

  // A6: Entropy
  if (SUITE.entropy && SUITE.entropy.trace) {{
    const tr = SUITE.entropy.trace;
    Plotly.newPlot('chart-entropy', [{{
      type: 'scatter', mode: 'lines',
      x: tr.map(p => p.center_turn),
      y: tr.map(p => p.entropy),
      line: {{ color: '#9b59b6', width: 1 }},
      fill: 'tozeroy', fillcolor: 'rgba(155,89,182,0.1)',
    }}], {{ ...PANEL_LAYOUT, yaxis: {{ ...PANEL_LAYOUT.yaxis, range: [0, 2.5] }} }},
    {{ displayModeBar: false, responsive: true }});
  }}

  // A7: Cumulative drift
  if (SUITE.drift) {{
    const traces = [];
    if (SUITE.drift.jake) traces.push({{
      type: 'scatter', mode: 'lines', name: 'Jake',
      x: SUITE.drift.jake.map(p => p.turn),
      y: SUITE.drift.jake.map(p => p.cumulative_distance),
      line: {{ color: '#94c4a8', width: 1 }},
    }});
    if (SUITE.drift.opus) traces.push({{
      type: 'scatter', mode: 'lines', name: 'Opus',
      x: SUITE.drift.opus.map(p => p.turn),
      y: SUITE.drift.opus.map(p => p.cumulative_distance),
      line: {{ color: '#b07cc6', width: 1 }},
    }});
    if (traces.length) {{
      Plotly.newPlot('chart-drift', traces,
        {{ ...PANEL_LAYOUT, showlegend: true,
           legend: {{ font: {{ size: 8, color: '#666' }}, bgcolor: 'transparent' }} }},
        {{ displayModeBar: false, responsive: true }});
    }}
  }}

  // A5: Information flow
  if (SUITE.flow && SUITE.flow.smoothed_ratio) {{
    const pairs = SUITE.flow.pairs;
    Plotly.newPlot('chart-flow', [{{
      type: 'scatter', mode: 'lines',
      x: pairs.map(p => p.position),
      y: SUITE.flow.smoothed_ratio,
      line: {{ color: '#e67e22', width: 1 }},
    }}, {{
      type: 'scatter', mode: 'lines', x: [0, pairs.length],
      y: [1, 1], line: {{ color: '#333', width: 1, dash: 'dot' }},
    }}], {{ ...PANEL_LAYOUT, yaxis: {{ ...PANEL_LAYOUT.yaxis, title: 'ratio' }} }},
    {{ displayModeBar: false, responsive: true }});
  }}

  // A8: Transition matrix
  if (SUITE.markov && SUITE.markov.full) {{
    const mat = SUITE.markov.full;
    const labels = mat.labels;
    Plotly.newPlot('chart-matrix', [{{
      type: 'heatmap', z: mat.matrix, x: labels, y: labels,
      colorscale: [['0','#0d0f18'],['1','#9b59b6']],
      showscale: false,
      hovertemplate: '%{{y}} -> %{{x}}: %{{z:.2f}}<extra></extra>',
    }}], {{
      ...PANEL_LAYOUT,
      margin: {{ l: 70, r: 8, t: 5, b: 60 }},
      xaxis: {{ ...PANEL_LAYOUT.xaxis, tickangle: -30, tickfont: {{ size: 7 }} }},
      yaxis: {{ ...PANEL_LAYOUT.yaxis, tickfont: {{ size: 7 }} }},
    }}, {{ displayModeBar: false, responsive: true }});

    document.getElementById('matrix-stats').innerHTML =
      `<span class="stat-label">Self-transition: </span><span>${{mat.self_transition_rate.toFixed(2)}}</span>`;
  }}

  // A1: Session arc lengths
  if (SUITE.sessions) {{
    const s = SUITE.sessions.sessions;
    Plotly.newPlot('chart-sessions', [{{
      type: 'bar',
      x: s.map(ss => ss.date),
      y: s.map(ss => ss.internal_arc_length),
      marker: {{ color: s.map(ss => DATE_COLORS[ss.date] || '#7ec8e3'), opacity: 0.8 }},
    }}], {{ ...PANEL_LAYOUT, xaxis: {{ ...PANEL_LAYOUT.xaxis, tickangle: -45, tickfont: {{ size: 7 }} }} }},
    {{ displayModeBar: false, responsive: true }});
  }}

  // A2: Recurrence heatmap
  if (SUITE.recurrence && SUITE.recurrence.matrix) {{
    const mat = SUITE.recurrence.matrix;
    const n = mat.length;
    // Downsample to 50x50 for display
    const step = Math.max(1, Math.floor(n / 50));
    const mini = [];
    for (let i = 0; i < n; i += step) {{
      const row = [];
      for (let j = 0; j < n; j += step) {{
        row.push(mat[i][j]);
      }}
      mini.push(row);
    }}
    Plotly.newPlot('chart-recurrence', [{{
      type: 'heatmap', z: mini,
      colorscale: [['0','#0d0f18'],['0.5','#1a4060'],['1','#7ec8e3']],
      showscale: false,
      hoverinfo: 'none',
    }}], {{
      ...PANEL_LAYOUT,
      margin: {{ l: 35, r: 8, t: 5, b: 35 }},
    }}, {{ displayModeBar: false, responsive: true }});
  }}

  // A15: Signal Density (novelty trace)
  if (SUITE.novelty && SUITE.novelty.turns) {{
    const nov = SUITE.novelty.turns;
    const ov = SUITE.novelty.overall || {{}};
    Plotly.newPlot('chart-novelty', [
      {{
        type: 'scatter', mode: 'lines', name: 'Smoothed',
        x: nov.map(t => t.turn),
        y: nov.map(t => t.smoothed_novelty),
        line: {{ color: '#7ec8e3', width: 1.5 }},
      }},
      {{
        type: 'scatter', mode: 'lines', name: 'Jake',
        x: nov.filter(t=>t.speaker==='Jake').map(t=>t.turn),
        y: nov.filter(t=>t.speaker==='Jake').map(t=>t.smoothed_novelty),
        line: {{ color: '#94c4a8', width: 0.8, dash: 'dot' }},
        visible: 'legendonly',
      }},
      {{
        type: 'scatter', mode: 'lines', name: 'Opus',
        x: nov.filter(t=>t.speaker==='Opus').map(t=>t.turn),
        y: nov.filter(t=>t.speaker==='Opus').map(t=>t.smoothed_novelty),
        line: {{ color: '#b07cc6', width: 0.8, dash: 'dot' }},
        visible: 'legendonly',
      }},
      // Threshold line
      {{
        type: 'scatter', mode: 'lines',
        x: [0, nov.length ? nov[nov.length-1].turn : 0],
        y: [ov.threshold||0, ov.threshold||0],
        line: {{ color: '#ff6b6b', width: 0.8, dash: 'dot' }},
        hoverinfo: 'none',
      }},
    ], {{
      ...PANEL_LAYOUT,
      showlegend: false,
      yaxis: {{ ...PANEL_LAYOUT.yaxis, title: 'novelty' }},
    }}, {{ displayModeBar: false, responsive: true }});

    document.getElementById('novelty-stats').innerHTML =
      `<span style="color:#555">Jake: </span><span style="color:#94c4a8">${{(ov.jake_mean||0).toFixed(3)}}</span>` +
      `&nbsp;&nbsp;<span style="color:#555">Opus: </span><span style="color:#b07cc6">${{(ov.opus_mean||0).toFixed(3)}}</span>` +
      `&nbsp;&nbsp;<span style="color:#555">Spikes: </span><span style="color:#ff6b6b">${{(SUITE.novelty.novelty_spikes||[]).length}}</span>`;
  }}

  // A10: Betti numbers across sessions
  if (SUITE.homology && SUITE.homology.sessions) {{
    const sss = SUITE.homology.sessions.filter(s => !s.skipped);
    if (sss.length) {{
      Plotly.newPlot('chart-betti', [
        {{
          type: 'scatter', mode: 'lines+markers', name: 'beta-0 (components)',
          x: sss.map(s => s.date), y: sss.map(s => s.betti_0),
          line: {{ color: '#3498db', width: 1.5 }},
          marker: {{ size: 4 }},
        }},
        {{
          type: 'scatter', mode: 'lines+markers', name: 'beta-1 (loops)',
          x: sss.map(s => s.date), y: sss.map(s => s.betti_1),
          line: {{ color: '#e74c3c', width: 1.5 }},
          marker: {{ size: 4 }},
        }},
      ], {{
        ...PANEL_LAYOUT,
        showlegend: true,
        legend: {{ font: {{ size: 8, color: '#666' }}, bgcolor: 'transparent' }},
        xaxis: {{ ...PANEL_LAYOUT.xaxis, tickangle: -45, tickfont: {{ size: 7 }} }},
        yaxis: {{ ...PANEL_LAYOUT.yaxis, title: 'Betti' }},
      }}, {{ displayModeBar: false, responsive: true }});
    }}
  }}

  // A11: Top bridging concepts (horizontal bar)
  if (SUITE.bridges && SUITE.bridges.documents) {{
    const docs = SUITE.bridges.documents.slice(0, 15);
    Plotly.newPlot('chart-bridges', [{{
      type: 'bar', orientation: 'h',
      x: docs.map(d => d.bridge_score),
      y: docs.map(d => d.name.replace('.md','').slice(0,25)),
      marker: {{
        color: docs.map(d => d.bridge_score > 0.6 ? '#e67e22' : d.bridge_score > 0.3 ? '#f39c12' : '#7f8c8d'),
        opacity: 0.85,
      }},
      hovertext: docs.map(d => `${{d.name}}<br>Bridge: ${{d.bridge_score.toFixed(2)}}<br>${{d.session_count}} sessions / ${{d.total_references}} refs`),
      hoverinfo: 'text',
    }}], {{
      ...PANEL_LAYOUT,
      margin: {{ l: 130, r: 8, t: 5, b: 30 }},
      xaxis: {{ ...PANEL_LAYOUT.xaxis, title: 'bridge score', range: [0, 1] }},
      yaxis: {{ ...PANEL_LAYOUT.yaxis, tickfont: {{ size: 7 }}, automargin: true }},
    }}, {{ displayModeBar: false, responsive: true }});
  }}
}}

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {{
  updateSliderUI();
  buildTimelineLabels();
  redrawMain();
  buildSidePanels();
}});

window.addEventListener('resize', () => {{
  Plotly.Plots.resize(document.getElementById('plot'));
}});
</script>
</body>
</html>
"""


def main():
    print("=== Building Full Suite Visualization ===")
    print()

    # Load all data files
    data = {}

    print("[LOAD] umap_full.json...")
    umap = safe_load(DATA / "umap_full.json")
    if umap:
        data['umap'] = umap
        print(f"  corpus: {len(umap.get('corpus',[]))}, turns: {len(umap.get('turns',[]))}")

    print("[LOAD] session_signatures.json...")
    sess = safe_load(DATA / "session_signatures.json")
    if sess:
        data['sessions'] = sess
        print(f"  {len(sess.get('sessions',[]))} sessions")

    print("[LOAD] recurrence_matrix.json...")
    rec = safe_load(DATA / "recurrence_matrix.json")
    if rec:
        # Only include matrix, not high_recurrence_pairs in JS (saves space)
        data['recurrence'] = {
            'matrix': rec.get('matrix', []),
            'n_blocks': rec.get('n_blocks', 0),
            'session_boundaries': rec.get('session_boundaries', []),
            'high_recurrence_pairs': rec.get('high_recurrence_pairs', [])[:20],
        }
        print(f"  {rec.get('n_blocks',0)}x{rec.get('n_blocks',0)} blocks")

    print("[LOAD] speaker_coupling.json...")
    coupling = safe_load(DATA / "speaker_coupling.json")
    if coupling:
        # Trim pairs to save space (keep summary fields, not full content)
        data['coupling'] = {
            'smoothed_distance': coupling.get('smoothed_distance', []),
            'pairs': [{'position': p['position'], 'jake_turn': p['jake_turn'],
                       'date': p['date'], 'distance': p['distance'],
                       'smoothed_distance': p.get('smoothed_distance', 0)}
                      for p in coupling.get('pairs', [])],
            'convergence_points': coupling.get('convergence_points', [])[:10],
            'divergence_points': coupling.get('divergence_points', [])[:10],
            'mean_distance': coupling.get('mean_distance', 0),
        }
        print(f"  {len(coupling.get('pairs',[]))} pairs")

    print("[LOAD] sliding_window_trajectory.json...")
    traj = safe_load(DATA / "sliding_window_trajectory.json")
    if traj:
        data['trajectory'] = traj
        print(f"  {traj.get('n_points',0)} window points")

    print("[LOAD] information_flow.json...")
    flow = safe_load(DATA / "information_flow.json")
    if flow:
        data['flow'] = {
            'smoothed_ratio': flow.get('smoothed_ratio', []),
            'pairs': [{'position': p['position'], 'ratio': p['ratio'],
                       'leader': p['leader'], 'date': p['date']}
                      for p in flow.get('pairs', [])],
            'jake_lead_percentage': flow.get('jake_lead_percentage', 0),
            'opus_lead_percentage': flow.get('opus_lead_percentage', 0),
            'by_date': flow.get('by_date', []),
        }
        print(f"  Jake {flow.get('jake_lead_percentage',0):.0f}% / Opus {flow.get('opus_lead_percentage',0):.0f}%")

    print("[LOAD] entropy_trace.json...")
    entropy = safe_load(DATA / "entropy_trace.json")
    if entropy:
        data['entropy'] = {
            'trace': entropy.get('trace', []),
            'mean_entropy': entropy.get('mean_entropy', 0),
            'max_theoretical_entropy': entropy.get('max_theoretical_entropy', 0),
        }
        print(f"  mean entropy: {entropy.get('mean_entropy',0):.3f}")

    print("[LOAD] cumulative_drift.json...")
    drift = safe_load(DATA / "cumulative_drift.json")
    if drift:
        data['drift'] = drift
        print(f"  Jake: {drift.get('total_jake_distance',0):.2f}, Opus: {drift.get('total_opus_distance',0):.2f}")

    print("[LOAD] transition_matrix.json...")
    markov = safe_load(DATA / "transition_matrix.json")
    if markov:
        data['markov'] = markov
        print(f"  self-transition: {markov.get('full',{}).get('self_transition_rate',0):.2f}")

    print("[LOAD] response_vectors_full.json (optional)...")
    rvec = safe_load(DATA / "response_vectors_full.json")
    if rvec:
        data['response_vectors'] = {
            'pairs': [{'jake_turn': p['jake_turn'], 'opus_turn': p['opus_turn'],
                       'magnitude': p['magnitude'], 'cosine_similarity': p['cosine_similarity'],
                       'top_response_direction': p.get('top_response_direction', '')}
                      for p in rvec.get('pairs', [])],
        }
        print(f"  {len(rvec.get('pairs',[]))} response vector pairs")
    else:
        data['response_vectors'] = None

    # Check if we have the minimum required data
    if not data.get('umap'):
        print("\nERROR: umap_full.json is required. Run compute_all_analyses.py first.")
        return 1

    # Add domain classification to turns (from session signatures if available)
    if data.get('umap') and data.get('sessions'):
        # Build a date -> dominant_register map
        date_to_reg = {s['date']: s['dominant_register']
                       for s in data['sessions'].get('sessions', [])}
        for turn in data['umap'].get('turns', []):
            turn['dominant_register'] = date_to_reg.get(turn['date'], 'unknown')

    print()
    print("[BUILD] Generating HTML...")
    html = build_html(data)

    OUT_HTML.write_text(html, encoding='utf-8')
    size_kb = OUT_HTML.stat().st_size // 1024
    print(f"[BUILD] Written: {OUT_HTML} ({size_kb} KB)")
    print(f"\nOpen in browser: file:///{OUT_HTML}")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
