---
artifact_type: source_code + self_test_results + library_research
produced_by: execution
project: exocortex-panel-ui
milestone: 1.5
date: 2026-07-04
builder: kestrel
driver: client feedback at the M1 aesthetic gate — "aesthetic is good but the
  interactive capability isn't there... click a tab, it doesn't expand, things
  don't happen, I don't get new information."
deliverables:
  - plugins/_exocortex/webui/panel-kit.css        # + Interactivity section (additive)
  - plugins/_exocortex/webui/panel-kit-interactive.html
library_research:
  recommend_now:
    - name: Alpine.js
      id: /websites/alpinejs_dev
      role: reactive core — x-data/@click/x-for/x-show/x-transition. Master→detail.
      weight: 0 (already loaded in A0)
    - name: uPlot
      id: /leeoniya/uplot
      role: live telemetry charts — setData(data,false) streams; stroke themeable
      weight: ~50KB, MIT, canvas
    - name: exocortex.css graduated patterns
      role: scale feedback (#3), CSS tooltip (#5), instant-state (#12), anim presets
      weight: 0 (already in repo)
  recommend_with_caveat:
    - name: "@alpinejs/collapse"
      role: height-animated accordion
      caveat: measures 0 height inside an initially-hidden tab; used x-transition
        for the tree instead. Good for single-view accordions.
  deferred:
    - Tabulator (sortable/filterable/expandable data grids — claim ledger, hypotheses)
    - GSAP (number roll-ups — already ratified in the stack)
    - Tippy.js (rich popovers — only if CSS tooltips prove insufficient)
evidence:
  - type: render_test
    method: served over http, loaded in Playwright (Docker), full-page screenshots
    results:
      - m15-magi-monitor.png     -> MAGI: live cards, gauges, radial, streaming uPlot chart, live clock
      - m15-wiki-drilldown.png   -> click iran-hormuz -> detail repopulates + breadcrumb updates
      - m15-yorha-monitor.png    -> theme toggle re-skins everything INCLUDING the chart (rebuild)
      - m15-yorha-vram-focus.png -> click VRAM card -> chart re-titles + re-scales to VRAM range
  - type: interaction_trace
    verified:
      - real tab bar switches views (Monitor/Wiki/Cycles)
      - metric cards are data-bound selectable; selection drives chart + breadcrumb + detail
      - tree master->detail: click node -> detail panel repopulates (new info)
      - gauges/cards/clock update every second (live loop)
      - theme swap rebuilds uPlot with the new accent (destroy+rebuild)
  - type: console_check
    errors: 1
    detail: "favicon.ico 404 (benign). No JS/Alpine/uPlot errors."
  - type: bug_found_and_fixed
    detail: "x-collapse measured 0 height inside the initially-hidden Wiki tab, and the
      kit's base .pk-children{display:none} fought x-show. Switched the tree to
      x-show + x-transition, overrode the base display, added per-tab default focus."
depends_on:
  - artifact: M1_component_library.md
---

# M1.5 — Interactivity — Milestone Summary

**Why:** at the M1 aesthetic gate Jake approved the look but flagged the feel —
clicking didn't expand anything, nothing happened, no new information surfaced.
Correct diagnosis: the M1 showcase never used Alpine; it was raw `onclick`
toggling one class, so nothing was *bound* to state. A command console has to
reward engagement (the design principle's own point #4).

**What changed:**
- **`panel-kit.css`** — additive `INTERACTIVITY` section: `.pk-clickable` tactile
  scale feedback (ROADMAP #3), `.pk-selected` data-bound selection (#12),
  `.pk-tip` CSS-only tooltip (#5), `.pk-flash` live-value pulse, uPlot theming,
  and a real `.pk-tabs` switcher. Every M1 component renders identically without
  these classes.
- **`panel-kit-interactive.html`** — the fix demonstrated. One Alpine `console()`
  component drives:
  - **Real tabs** (Monitor / Wiki / Cycles) that switch the whole lower view.
  - **Data-bound metric cards** — click one → it selects, the breadcrumb updates,
    the detail panel explains it, and the **live chart re-points and re-scales** to it.
  - **Master→detail tree** — expand a group, click an entry, the detail panel
    repopulates with that entry's content (the MGSV iDroid pattern). *This is the
    "new information on click" that was missing.*
  - **Live streaming uPlot chart** — 60s rolling, `setData(data,false)`, themed to
    `--color-accent`. The "it feels alive" piece.
  - **Live gauges / radial / clock / status bar** — nudged every second.
  - **Theme toggle** — re-skins the entire kit *and* rebuilds the chart in the new
    palette, zero code change (verified MAGI↔YoRHa).

**Library verdict:** the stack is native and light — Alpine (already in A0) is the
reactive engine; uPlot (~50KB) is the only new vendor for live charts; the rest
are patterns the repo already graduated. Nothing heavier is justified — the
diegetic aesthetic + the ROADMAP's "commit harder to one vibe" lesson argue
against a component-framework mismatch.

**Production integration note:** in A0, Alpine is already loaded — register
`console()` on `alpine:init` and drop the CDN `<script>`. Vendor `uPlot`
(+ optional `@alpinejs/collapse`) locally like Mermaid in the wiring doc — no CDN
dependency in-container.

**GATE (before M2):** awaiting (1) Jake's approval that the *feel* now lands, and
(2) fresh-context verification. Live demo served at `panel-kit-interactive.html`.
