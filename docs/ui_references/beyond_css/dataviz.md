# Data Visualization Libraries — Vendoring Decision Report

*Research date: 2026-04-13. For the mission-control dashboard: static HTML + Alpine.js + Flask, no React, no build system.*

## TL;DR Recommendation

**Use two libraries, no build system, total ≈ 130 KB minified:**

1. **uPlot** (~50 KB min) — for sparklines and histograms (high-frequency line/bar work). Canvas-based, exceptional perf, dead-easy script-tag include.
2. **Apache ECharts custom build** (~140 KB min if you only ship Scatter + Bar + Graph + Canvas renderer; full bundle is ~1 MB) — for the SWARMFISH calibration scatter (with confidence intervals, reference lines, tooltips) and the entity-relationship graph. ECharts has a native `dark` theme and a force-directed `graph` series, so one library covers both the scatter and the network case.

Skip D3 unless you find a chart that ECharts genuinely cannot render. D3 is the right answer when the spec is "draw something nobody has drawn before"; it is the wrong answer when the spec is "draw a scatter with a reference line and look premium." You will write 5–10× more code in D3 for the same output, and the polish ceiling is identical.

If you want a single-library answer (worth the size budget for the simplicity), **ECharts custom build covers all four use cases** at ~150–180 KB and looks like Linear out of the box once you pass `'dark'` to `echarts.init()`.

---

## 1. D3.js — The Reference Implementation

| Property | Value |
| --- | --- |
| Latest version | **7.9.0** (March 2024; v8 has not shipped) |
| License | **ISC** (permissive, equivalent to MIT for our purposes) |
| Full UMD bundle | ~250 KB min / ~85 KB gzipped |
| Custom modular bundle | 13–40 KB depending on modules used |
| Vanilla JS | Yes — designed for it. Originally built before React existed. |
| Script-tag drop-in | **Yes**, two ways (UMD or ESM, see below) |

### What modules you'd actually need for the four use cases

D3 is not a chart library; it is a **toolkit**. Every chart is hand-built. For your use cases, the minimum import set is:

| Use case | Modules |
| --- | --- |
| Calibration scatter | `d3-selection`, `d3-scale`, `d3-axis`, `d3-shape` (line for reference diagonal), `d3-array` (extent), optionally `d3-format` |
| Drift histogram | `d3-selection`, `d3-scale`, `d3-axis`, `d3-array` (`bin()` / `histogram`), `d3-time-format` if x-axis is dates |
| Sparklines | `d3-selection`, `d3-scale`, `d3-shape` (`line()`) — that's it, ~12 KB total |
| Force-directed graph | `d3-selection`, `d3-force`, `d3-drag`, `d3-zoom`, `d3-shape` |

A scatter + sparkline + histogram custom bundle lands at roughly **40–55 KB minified**. Adding `d3-force` + `d3-drag` + `d3-zoom` for the graph pushes it to ~75–90 KB.

### How to use it without a build system

**UMD (creates a `d3` global):**
```html
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script>
  const svg = d3.create("svg").attr("width", 640).attr("height", 400);
  // ...
</script>
```

**ESM (no global, no build):**
```html
<script type="module">
  import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";
  // tree-shaken by the CDN
</script>
```

For a **vendored** install (no CDN at runtime — which is the right call for a sovereignty project), download `d3.v7.min.js` once and serve it from Flask static. No import maps required for the UMD path.

### Premium scatter plot in D3 (illustrative)

```html
<div id="cal"></div>
<script src="/static/vendor/d3.v7.min.js"></script>
<script>
  const data = [
    {pred: 0.62, actual: 0.71, conf: 0.85},
    {pred: 0.30, actual: 0.18, conf: 0.40},
    // ...
  ];

  const W = 640, H = 480, M = {top: 20, right: 20, bottom: 40, left: 50};
  const svg = d3.select("#cal").append("svg")
      .attr("viewBox", `0 0 ${W} ${H}`)
      .style("background", "#0a1929")
      .style("font", "12px ui-monospace, monospace")
      .style("color", "#7dd3fc");

  const x = d3.scaleLinear([0, 1], [M.left, W - M.right]);
  const y = d3.scaleLinear([0, 1], [H - M.bottom, M.top]);
  const c = d3.scaleSequential(d3.interpolateCubehelix("#1e3a5f", "#67e8f9"))
              .domain([0, 1]);

  // Perfect-calibration diagonal
  svg.append("line")
      .attr("x1", x(0)).attr("y1", y(0))
      .attr("x2", x(1)).attr("y2", y(1))
      .attr("stroke", "#67e8f9")
      .attr("stroke-dasharray", "4 4")
      .attr("stroke-opacity", 0.4);

  // Axes — manual styling needed for premium look
  const xAxis = svg.append("g")
      .attr("transform", `translate(0,${H - M.bottom})`)
      .call(d3.axisBottom(x).tickSize(-H + M.top + M.bottom));
  xAxis.selectAll(".tick line").attr("stroke", "#1e3a5f");
  xAxis.selectAll(".domain").attr("stroke", "#1e3a5f");
  xAxis.selectAll("text").attr("fill", "#7dd3fc");

  // Points
  svg.append("g").selectAll("circle")
      .data(data).join("circle")
      .attr("cx", d => x(d.pred))
      .attr("cy", d => y(d.actual))
      .attr("r", 4)
      .attr("fill", d => c(d.conf))
      .attr("stroke", "#0a1929")
      .attr("stroke-width", 1);
</script>
```

That's ~40 lines for one chart with no tooltips, no legend, no confidence intervals yet. Multiply that by four chart types. **D3's cost is in code, not in bytes.**

### Verdict on D3

- **Aesthetic ceiling: very high.** The Observable/NYT/Pudding gallery is the high-water mark of web visualization. D3 *can* match Linear/Vercel — but only if you write the styling yourself.
- **Default appearance: academic.** A bare D3 chart looks like a textbook figure. The "premium feel" is entirely your responsibility.
- **Effort:** Highest of any option here. Every tooltip, legend, and animation is hand-rolled.
- **Use it when:** You need a chart no library supports (custom radial layouts, the geometry instrument's UMAP plot with response vectors and off-map cones, etc.). For your four documented use cases, **it's overkill**.

---

## 2. Observable Plot — D3's Friendly Cousin

| Property | Value |
| --- | --- |
| Latest version | **0.6.17** (still pre-1.0 after 4 years) |
| License | ISC |
| Bundle (UMD) | ~140 KB min including its bundled D3 deps |
| Vanilla JS | Yes |
| Script-tag drop-in | **Yes**, two ways |

Observable Plot is from Mike Bostock (D3's creator). It's a **grammar-of-graphics** layer over D3 — you describe marks declaratively (`Plot.dot`, `Plot.line`, `Plot.ruleX`) and it produces an SVG.

### Drop-in usage

```html
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6"></script>
<script>
  document.getElementById("cal").appendChild(
    Plot.plot({
      width: 640, height: 480,
      style: { background: "#0a1929", color: "#7dd3fc", fontFamily: "ui-monospace" },
      x: { domain: [0, 1], grid: true, label: "predicted" },
      y: { domain: [0, 1], grid: true, label: "actual" },
      color: { scheme: "cubehelix", domain: [0, 1] },
      marks: [
        Plot.ruleY([0]), Plot.ruleX([0]),
        Plot.line([[0,0],[1,1]], { stroke: "#67e8f9", strokeOpacity: 0.4, strokeDasharray: "4 4" }),
        Plot.dot(data, { x: "pred", y: "actual", fill: "conf", r: 4, stroke: "#0a1929" }),
      ],
    })
  );
</script>
```

That's the *full* premium scatter — diagonal reference line, axes, grid, color scale, all in 12 lines. It's an order of magnitude less code than D3 for the same output.

### Capabilities for your use cases

| Use case | Plot supports? |
| --- | --- |
| Calibration scatter w/ reference line | **Yes**, native (`Plot.dot` + `Plot.line` or `Plot.linearRegressionY`) |
| Drift histogram | **Yes** (`Plot.rectY` + `Plot.binX`) |
| Sparklines | **Yes**, but it's a full Plot per sparkline — not as cheap as uPlot |
| Force-directed graph | **No.** Plot does not implement network layouts. You'd need D3-force or a separate library. |

### Dark theme

Plot honors `prefers-color-scheme: dark` automatically and exposes `--plot-background` and `--plot-foreground` CSS variables for explicit control. Setting `style: { background: "#0a1929", color: "#7dd3fc" }` on each plot is the no-CSS path.

### Verdict

- **Aesthetic ceiling: high.** Defaults are tasteful; premium look reachable without much custom CSS.
- **Effort: low to medium.** The grammar covers your scatter/histogram/sparkline cases in tens of lines, not hundreds.
- **Cost: 140 KB min total** (Plot + d3) — heavier than a custom D3 build but lighter than ECharts full.
- **Disqualified by:** No graph layout. You'd need a second library for the entity-relationship use case anyway.

---

## 3. Apache ECharts — The Heavyweight That Earns It

| Property | Value |
| --- | --- |
| Latest version | **6.0.0** |
| License | Apache 2.0 |
| Full UMD bundle | ~1 MB min / ~280 KB gzipped |
| Custom build (online builder, only what you need) | **~140–200 KB min** for your use cases |
| Vanilla JS | Yes — vanilla-first, was built for this |
| Script-tag drop-in | **Yes**, with both full and custom builds |

ECharts is Apache Software Foundation–maintained, originally from Baidu, and is the most feature-complete OSS chart library in existence. Every chart type you'd ever want is built in: scatter with regression, time-series, candlesticks, heatmaps, sankeys, treemaps, sunbursts, **graph (force-directed)**, parallel coords, gauges, geo maps, 3D via WebGL.

### Bundle math for your use cases

Full bundle is fat. Custom bundle (built via [echarts.apache.org/builder.html](https://echarts.apache.org/en/builder.html)) ships only what you select. For your four use cases you need:

- **Charts:** Scatter, Bar (for histogram), Line (for sparkline), Graph (for the force-directed network)
- **Components:** Title, Tooltip, Grid, Legend (optional), MarkLine (for the diagonal reference), DataZoom (optional)
- **Renderer:** Canvas (smaller and faster than SVG for this load)

That custom bundle weighs in around **140–180 KB minified**, ~50–60 KB gzipped. That's heavier than a custom D3 bundle but you get **everything pre-built**: tooltips, legends, animations, dark theme, responsive resize, accessibility.

### Built-in dark theme

```html
<script src="/static/vendor/echarts-custom.min.js"></script>
<div id="cal" style="width:640px;height:480px"></div>
<script>
  const chart = echarts.init(document.getElementById('cal'), 'dark');
  chart.setOption({
    backgroundColor: '#0a1929',
    grid: { top: 30, right: 30, bottom: 40, left: 50 },
    xAxis: { type: 'value', min: 0, max: 1, name: 'predicted',
             splitLine: { lineStyle: { color: '#1e3a5f' } } },
    yAxis: { type: 'value', min: 0, max: 1, name: 'actual',
             splitLine: { lineStyle: { color: '#1e3a5f' } } },
    tooltip: { trigger: 'item' },
    visualMap: {
      min: 0, max: 1, dimension: 2,
      inRange: { color: ['#1e3a5f', '#67e8f9'] },
      textStyle: { color: '#7dd3fc' },
    },
    series: [{
      type: 'scatter',
      symbolSize: 8,
      data: data.map(d => [d.pred, d.actual, d.conf]),
      markLine: {
        symbol: 'none',
        lineStyle: { type: 'dashed', color: '#67e8f9', opacity: 0.4 },
        data: [[{ coord: [0, 0] }, { coord: [1, 1] }]],
      },
    }],
  });
</script>
```

That's the entire scatter — dark themed, with tooltips on hover, animated entry, color scale via `visualMap`, reference diagonal via `markLine`, fully responsive on `chart.resize()`. ~25 lines total.

### Aesthetic ceiling

ECharts looks **genuinely premium** out of the box once you pass `'dark'`. The default dark theme is closer to Linear than to Excel. Examples like the [bubble chart on Air Quality](https://echarts.apache.org/examples/en/editor.html?c=bubble-gradient) demonstrate the ceiling — gradients, soft shadows, smooth animation. It's not academic-looking by default.

### Verdict

- **Aesthetic ceiling: very high.** The dark theme is production-grade.
- **Effort: low.** Declarative config; the hard things (tooltips, legend, theme) are free.
- **Cost: 140–180 KB custom** (worth it for the feature density).
- **Single-library answer for all four use cases**, including the graph.
- **Force-directed graph quality: good** (`type: 'graph', layout: 'force'`) — fine for 50 nodes, possibly fine to 500.

---

## 4. uPlot — The Specialist

| Property | Value |
| --- | --- |
| Latest version | **1.6.32** |
| License | MIT |
| Bundle | **~48 KB min / ~16 KB gzipped** |
| Vanilla JS | Yes |
| Script-tag drop-in | **Yes**, IIFE bundle in `dist/` |

uPlot is the **fastest** time-series chart library on the web. Canvas-based, can render 150K points in 25 ms, livestream at 60fps with single-digit CPU usage. It is *narrow*: lines, areas, OHLC, bars. The author intentionally **excludes** scatter plots, sparklines (technically), animations, and stacked series in pursuit of leanness.

### Capabilities for your use cases

| Use case | uPlot fit |
| --- | --- |
| Calibration scatter | **No.** uPlot does not do XY scatter. Hard pass. |
| Drift histogram | **Yes** via bar paths — fine for time-bucketed bars. |
| Sparklines | **Yes, perfect.** Set `legend: false`, `axes: [{show:false},{show:false}]`, ~12 KB of code, 60 fps even with 100 inline sparklines on a page. |
| Force-directed graph | **No.** Out of scope. |

### Sparkline example

```html
<script src="/static/vendor/uPlot.iife.min.js"></script>
<link rel="stylesheet" href="/static/vendor/uPlot.min.css">
<div id="spark" style="width:120px;height:32px"></div>
<script>
  const data = [
    [0,1,2,3,4,5,6,7,8,9],            // x (time)
    [0.4,0.5,0.55,0.6,0.58,0.65,0.7,0.72,0.75,0.78], // confidence
  ];
  new uPlot({
    width: 120, height: 32,
    cursor: { show: false },
    legend: { show: false },
    axes: [{ show: false }, { show: false }],
    scales: { x: { time: false } },
    series: [
      {},
      { stroke: "#67e8f9", width: 1.5, fill: "rgba(103,232,249,0.15)" },
    ],
  }, data, document.getElementById('spark'));
</script>
```

That's a complete sparkline. Background is whatever the parent CSS sets — pure transparency, so it inherits your dark theme automatically.

### Dark theme

There is no built-in theme system; you style via the `stroke`/`fill` series options and CSS for grid lines. Because Canvas takes its colors from the JS config, theming is just configuration, not a stylesheet override.

### Verdict

- **Aesthetic ceiling: very high for what it does.** Looks clean and modern out of the box; cursor and crosshair behavior is best-in-class.
- **Cost: trivial.** 48 KB min.
- **Coverage: narrow.** It will not do scatter or graph at all. Use it for sparklines and possibly the histogram.
- **Pair with:** ECharts custom build for the things uPlot can't do, OR D3 if you really want minimum bytes.

---

## 5. Chart.js — The Default

| Property | Value |
| --- | --- |
| Latest version | **4.5.1** |
| License | MIT |
| Bundle | ~200 KB min / ~60 KB gzipped (full); tree-shakeable but not as aggressively as ECharts |
| Vanilla JS | Yes |
| Script-tag drop-in | Yes |

Chart.js is the most popular charting library by NPM downloads. It's a Canvas-based library covering the standard chart types (line, bar, scatter, doughnut, radar, polar). It does **not** do force-directed graphs.

### Aesthetic honesty

Chart.js looks **fine but generic**. The defaults are rounded, friendly, slightly Material-Design-flavored. To get a Linear-tier dark dashboard look you have to override `Chart.defaults.color`, the grid colors, font family, tooltip colors, and animation curves manually. The ceiling exists but you're climbing it yourself, and you'll never quite get there — Chart.js's geometry is "approachable" by design, while Linear/Vercel is "spare and architectural." It's a real aesthetic mismatch.

### Verdict

- **Aesthetic ceiling: medium.** Genuinely difficult to make this look like Linear.
- **Cost: 200 KB.**
- **Coverage: scatter, histogram (via bar), sparkline (via line) — yes; graph — no.**
- **Recommendation: skip.** ECharts costs the same and looks dramatically better; uPlot costs 1/4 and is faster.

---

## 6. Cytoscape.js / Sigma.js / vis-network — Graph Specialists

For the **entity relationship graph** (~50 nodes, force-directed, dark theme):

| Library | Version | Bundle | License | Strengths | Weaknesses |
| --- | --- | --- | --- | --- | --- |
| **Cytoscape.js** | 3.33.2 | ~330 KB min | MIT | Best-in-class graph algorithms, layouts (cose, fcose, force), graph theory ops, rich style selectors (CSS-like), excellent docs | Heavyweight; built for biology / bioinformatics aesthetic by default |
| **Sigma.js** | 3.0.2 | ~120 KB min (+ Graphology ~80 KB) | MIT | WebGL renderer = fastest for large graphs (10K+ nodes); good performance | Less out-of-box layout variety; uses Graphology as a separate data model |
| **vis-network** | 10.0.2 | ~700 KB min | Apache 2.0 / MIT dual | Easiest to drop in, nice physics, decent looks | Heavy; UI components feel slightly dated |
| **D3-force** (modules) | 7.x | ~25 KB min | ISC | Smallest bundle; full control; same library as your other charts | You're hand-coding everything: drag, zoom, hit testing, styling |
| **ECharts graph series** | 6.0 | included in custom build | Apache 2.0 | If you're already loading ECharts, the graph type is **free** | Less algorithmic depth than Cytoscape if you ever need analytics on the graph |

### For 50 nodes specifically

Performance is a non-issue at this scale — anything works. The decision is **what's already in your bundle**.

- If you commit to **ECharts**, the graph series is free. Use it. **This is the recommendation.**
- If you commit to **D3** for charts, use **d3-force** for the graph too. ~25 KB extra; same idiom.
- If you want the **best graph library purely on its own merits**, Cytoscape.js. The selector system is gorgeous, the layouts are first-class, and the docs are the cleanest in the space. But it's 330 KB and a separate idiom from your charts.

### What dark Cytoscape looks like

```js
cytoscape({
  container: document.getElementById('graph'),
  elements: [
    { data: { id: 'iran' } },
    { data: { id: 'hormuz' } },
    { data: { source: 'iran', target: 'hormuz', id: 'e1' } },
  ],
  style: [
    { selector: 'core', style: { 'background-color': '#0a1929' } },
    { selector: 'node', style: {
        'background-color': '#67e8f9',
        'border-color': '#0a1929', 'border-width': 2,
        'label': 'data(id)', 'color': '#7dd3fc',
        'font-family': 'ui-monospace', 'font-size': 11,
    }},
    { selector: 'edge', style: {
        'line-color': '#1e3a5f', 'width': 1,
        'curve-style': 'bezier',
    }},
  ],
  layout: { name: 'cose', animate: true },
});
```

Premium-feeling out of the box once you set the colors.

---

## 7. Live Examples / Aesthetic Reality Check

Verdict on whether each library can match Linear/Vercel polish:

| Library | Default look | Premium ceiling | Effort to reach ceiling |
| --- | --- | --- | --- |
| D3 | Academic / textbook | Maximum — NYT/Pudding-tier | Very high (every pixel is yours) |
| Observable Plot | Tasteful, slightly cartographic | High | Low (set CSS vars + style prop) |
| ECharts | **Already premium** with `'dark'` | Very high | Very low — config-driven |
| uPlot | Spare, technical, modern | High *for line/area* | Low |
| Chart.js | Friendly, rounded, slightly Material | Medium — never quite "spare" | High and the ceiling is lower |
| Cytoscape | Graph-paper-academic by default | High | Medium (lots of selectors) |

ECharts is the **only** library in this list whose defaults already look Linear-tier without any custom work. D3 can match it but you write the CSS. The others can approach it but each has a tell.

---

## 8. The Recommendation, Stated as a Decision

### Option A — Single library (recommended)

**Apache ECharts custom build, ~150 KB minified.**

```
Charts:    Scatter, Bar, Line, Graph
Components: Title, Tooltip, Grid, MarkLine, VisualMap, DataZoom
Renderer:  Canvas
```

Use the [online builder](https://echarts.apache.org/en/builder.html) once, vendor the resulting `echarts-custom.min.js` into `static/vendor/`, never touch it again. Initialize every chart with `echarts.init(el, 'dark')`. Done. All four use cases covered with ~30 lines of config per chart.

**This is the right answer if you want to stop thinking about the dataviz layer and ship.**

### Option B — Two libraries, minimum bytes

**uPlot (~48 KB) for sparklines + histogram, custom D3 build (~75 KB) for scatter + force graph. Total ~125 KB.**

Choose this if:
- You expect to need something visually unusual later (the geometry instrument lives in your repo and it's already off-the-map territory)
- You want to write more JavaScript in exchange for fewer bytes
- You believe the dataviz layer will become a long-term distinguishing surface and want low-level control

The cost is **author-time**: every chart is hand-built. The benefit is total architectural control and the smallest possible footprint.

### Option C — Pure D3, ~90 KB custom bundle

Skip unless you have a specific chart that requires custom geometry (the response-vector / off-map cone visualizations from the Output Geometry Instrument come to mind). For a dashboard with a calibration scatter, a histogram, sparklines, and a small graph, this is the option that takes 4× longer to build for no aesthetic gain.

### What I would do

Take **Option A**. ECharts custom build. Ship it. The ~50 KB you'd save going to D3 will not matter on a localhost-served Flask dashboard, and the ~10–20 hours of implementation time you'd spend hand-rolling tooltips and legends is real and recoverable. If a chart someday needs to do something ECharts can't (the Geometry Instrument's UMAP scatter with 768-dim trajectories), add D3 as a *second* library at that moment for *that* chart — D3's modular nature makes it cheap to add later for a single unusual use.

---

## 9. Vendoring Notes (No Build System)

For every option, vendor the assets into `static/vendor/` rather than relying on a CDN at runtime. This is a sovereignty project; the dashboard should run with no external network calls.

```
static/vendor/
├── echarts-custom.min.js     # 150 KB — covers all four use cases (Option A)
├── uPlot.iife.min.js         # 48 KB — only if Option B
├── uPlot.min.css             # 3 KB
└── d3.v7.min.js              # only if Option B or C
```

ECharts custom builds are produced by the online builder as a single file. uPlot ships an IIFE bundle in `dist/` ready to go. D3 ships `d3.v7.min.js` ready to go. None require a build system on your end.

CSP-wise: all three are pure JS with no `eval()`. They work under strict CSP without `unsafe-eval`.

---

## Sources

- [D3.js v7.9.0 GitHub release](https://github.com/d3/d3) — version, license, modular structure
- [D3 Getting Started](https://d3js.org/getting-started) — UMD vs ESM CDN usage
- [Observable Plot v0.6.17 GitHub](https://github.com/observablehq/plot) — license, capabilities
- [Observable Plot Getting Started](https://observablehq.com/plot/getting-started) — UMD/ESM usage, dark theme
- [Apache ECharts homepage](https://echarts.apache.org/en/feature.html) — feature list
- [Apache ECharts Online Builder](https://echarts.apache.org/en/builder.html) — custom bundle composition
- [Apache ECharts Theme Builder](https://echarts.apache.org/en/theme-builder.html) — built-in dark theme
- [Apache ECharts Import Handbook](https://apache.github.io/echarts-handbook/en/basics/import/) — tree-shakeable component imports
- [uPlot homepage](https://leeoniya.github.io/uPlot/) — bundle size, perf benchmarks, API
- [uPlot GitHub v1.6.32](https://github.com/leeoniya/uPlot) — license, capabilities
- [Chart.js v4.5.1 GitHub](https://github.com/chartjs/Chart.js) — version
- [Cytoscape.js v3.33.2 GitHub](https://github.com/cytoscape/cytoscape.js) — license, MIT, full-feature graph library
- [Sigma.js v3.0.2 GitHub](https://github.com/jacomyal/sigma.js) — WebGL renderer, version
- [vis-network v10.0.2 GitHub](https://github.com/visjs/vis-network) — version
- [Best Libraries for Force-Directed Graphs](https://weber-stephen.medium.com/the-best-libraries-and-methods-to-render-large-network-graphs-on-the-web-d122ece2f4dc) — comparative analysis
- [Cylynx: JS Graph Visualization Comparison](https://www.cylynx.io/blog/a-comparison-of-javascript-graph-network-visualisation-libraries/) — graph library tradeoffs
- [Metabase: Best Open-Source Charting Libraries](https://www.metabase.com/blog/best-open-source-chart-library) — feature comparisons
- [OpenReplay: Choosing a JavaScript Charting Library](https://blog.openreplay.com/choosing-javascript-charting-library/) — bundle size data points
- [DEV: Optimizing ECharts Bundle Size](https://dev.to/manufac/using-apache-echarts-with-react-and-typescript-optimizing-bundle-size-29l8) — custom-build metrics
