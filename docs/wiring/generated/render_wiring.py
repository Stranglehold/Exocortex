#!/usr/bin/env python3
"""Render wiring.json -> a self-contained HTML wiring map."""
import io, json, html, sys, os

S = os.path.dirname(os.path.abspath(__file__))
d = json.load(io.open(os.path.join(S, "wiring.json"), encoding="utf-8"))
e = html.escape

# Hooks in rough message-loop execution order; the rest follow alphabetically.
ORDER = ["agent_init", "start", "monologue_start", "message_loop_start",
         "before_main_llm_call", "message_loop_prompts_before",
         "message_loop_prompts_after", "system_prompt", "hist_add_before",
         "reasoning_stream", "reasoning_stream_chunk", "reasoning_stream_end",
         "response_stream", "response_stream_chunk", "response_stream_end",
         "tool_execute_before", "tool_execute_after", "hist_add_tool_result",
         "error_format", "message_loop_end", "monologue_end",
         "process_chain_end", "end"]
hooks = d["hooks"]
ordered = [h for h in ORDER if h in hooks] + sorted(h for h in hooks if h not in ORDER)
c = d["counts"]; sk = d["state_keys"]

# ── web UI section (scan_webui.py; absent key renders nothing) ─────────────────────────────────────────────
webui_html = ""; webui_stat = ""
w = d.get("webui")
if w and not w.get("error"):
    t = w["tokens"]; pts = w["extension_points"]; parts = w["plugin_ui_parts"]; wt = w["weight"]; b = w["behaviour"]
    kinds = {k: sum(1 for v in pts.values() if v["kind"] == k) for k in ("html", "js", "provider-only")}
    with_prov = sum(1 for v in pts.values() if v["providers"])
    prow = []
    for name, v in sorted(pts.items(), key=lambda kv: (-len(kv[1]["providers"]), kv[0])):
        if not v["providers"]:
            continue
        provs = " · ".join(f"{p['plugin'].rsplit('/', 1)[-1]}: {', '.join(p['files'])}" for p in v["providers"])
        prow.append(f"<tr class=plug><td class=fn>{e(name)}</td>"
                    f"<td><span class='tag core'>{e(v['kind'])}</span></td>"
                    f"<td class=doc>{e(provs)}</td></tr>")
    empty = sorted(n for n, v in pts.items() if not v["providers"])
    parts_rows = "".join(
        f"<tr class={'plug' if p['plugin'].endswith('_exocortex') else 'core'}>"
        f"<td class=fn>{e(p['plugin'].rsplit('/', 1)[-1])}</td><td class=doc>{e(', '.join(p['files']))}</td></tr>"
        for p in sorted(parts, key=lambda p: (not p['plugin'].endswith('_exocortex'), p['plugin'])))
    largest = " · ".join(f"{e(n)} {sz//1024} KB" for n, sz in wt["js_largest"][:4])
    webui_stat = f'<div class="stat"><b>{len(pts)}</b><span>web ui points</span></div>'
    webui_html = f'''<section class="hook">
      <h2>web ui <span class="hc">{len(pts)} extension points · <b>{with_prov} provided</b> · {t["defined"]} css tokens · {wt["js_files"]} js files</span></h2>
      <div class="note">
      <b>Measured by <code>scan_webui.py</code> inside the container from <code>{e(w["root"])}</code>.</b>
      Extension points: {kinds["html"]} HTML (<code>&lt;x-extension&gt;</code>), {kinds["js"]} JS (<code>callJsExtensions</code>),
      {kinds["provider-only"]} provider-only folders; {with_prov} have at least one provider, {len(empty)} are empty today.
      CSS custom properties: {t["defined"]} defined, {t["read_somewhere"]} read somewhere, {t["pairs_dark_light"]} dark/light pairs;
      never-read candidates: <code>{e(", ".join(t["defined_never_read_candidates"]) or "none")}</code>;
      read but never defined in index.css or css/: {len(t["read_never_defined"])} names (vendor or runtime; a limit, not a finding).
      JS weight {wt["js_bytes"]//1024} KB over {wt["js_files"]} files ({largest}); CSS {wt["css_bytes"]//1024} KB.
      Behaviour constants read from source: message window page {b["message_window_page_size"]}, max <code>{e(str(b["message_window_max_expr"]))}</code>,
      smooth stream <code>{e(str(b["smooth_stream"]))}</code>; local patch markers in messages.js: {b.get("local_patch_markers_in_messages_js", b.get("fable_patch_markers_in_messages_js", "?"))}.
      <br><br><b>Limits of this section:</b> {e(" · ".join(w["limits"]))}
      </div>
      <table><thead><tr><th>extension point</th><th>kind</th><th>provided by (plugin: files)</th></tr></thead>
      <tbody>{"".join(prow)}</tbody></table>
      <div class="note" style="border-left-color:var(--faint)"><b>Empty points</b> ({len(empty)}): <code>{e(", ".join(empty) or "none")}</code></div>
      <h2 style="margin-top:18px">plugin ui parts <span class="hc">the other mechanism: <code>&lt;plugin&gt;/webui/*</code> · {len(parts)} plugins</span></h2>
      <table><thead><tr><th>plugin</th><th>files</th></tr></thead><tbody>{parts_rows}</tbody></table>
    </section>'''

rows = []
for h in ordered:
    items = hooks[h]
    npl = sum(1 for x in items if x["kind"] == "plugin")
    rows.append(f'''<section class="hook{' pipeline' if h in ORDER else ''}">
      <h2>{e(h)} <span class="hc">{len(items)} ext · <b>{npl} ours</b> · {len(items)-npl} core</span></h2>
      <table><thead><tr><th>#</th><th>extension</th><th>owner</th><th>does</th>
      <th>writes</th><th>reads</th><th>obs</th></tr></thead><tbody>''')
    for x in items:
        cls = "plug" if x["kind"] == "plugin" else "core"
        obs = ("<span class=nolog title='zero stdout prints — cannot be observed in docker logs'>·</span>"
               if x["n_prints"] == 0 else
               "<span class=erronly title='prints only inside except — silence means healthy'>!</span>"
               if x["error_only_prints"] else
               "<span class=ok title='emits on the happy path'>●</span>")
        miss = (f"<span class=miss title='{e(', '.join(x['paths_missing']))}'>"
                f"{len(x['paths_missing'])} missing path</span>") if x["paths_missing"] else ""
        rows.append(
            f"<tr class={cls}><td class=num>{x['order'] if x['order'] is not None else ''}</td>"
            f"<td class=fn>{e(x['file'])}{miss}</td>"
            f"<td><span class='tag {cls}'>{'PLUGIN' if cls=='plug' else 'core'}</span></td>"
            f"<td class=doc>{e(x['purpose'] or '—')}</td>"
            f"<td class=k>{e(', '.join(x['writes'][:3])) or '—'}</td>"
            f"<td class=k>{e(', '.join(x['reads'][:3])) or '—'}</td>"
            f"<td class=obs>{obs}</td></tr>")
    rows.append("</tbody></table></section>")

doc = f"""<title>Agent Zero Wiring Map</title>
<link rel=stylesheet href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
:root{{--bg:#14161a;--panel:#1b1e24;--line:#2c313a;--ink:#d7dbe2;--dim:#858d9b;
--faint:#5a616e;--plug:#6ea8fe;--core:#7a8496;--ok:#7fb069;--warn:#d19a48;--miss:#c8624f}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font-family:'Barlow Condensed',Arial Narrow,sans-serif;font-size:15px}}
.mono,.fn,.k,.num{{font-family:'JetBrains Mono',ui-monospace,monospace}}
header{{padding:22px 26px;border-bottom:1px solid var(--line);background:var(--panel)}}
h1{{margin:0 0 4px;font-size:26px;letter-spacing:.06em;font-weight:600}}
.sub{{color:var(--dim);font-size:13px;font-family:'JetBrains Mono',monospace}}
.stats{{display:flex;flex-wrap:wrap;gap:26px;margin-top:16px}}
.stat b{{display:block;font-size:24px;font-family:'JetBrains Mono',monospace;font-weight:500}}
.stat span{{color:var(--faint);font-size:11px;letter-spacing:.14em;text-transform:uppercase}}
main{{padding:0 26px 60px;max-width:1500px}}
.note{{background:var(--panel);border-left:3px solid var(--warn);padding:12px 16px;
margin:22px 0;color:var(--dim);font-size:13px;line-height:1.65;max-width:100ch}}
.note b{{color:var(--ink)}}
.hook{{margin:26px 0}}
.hook.pipeline h2{{border-left:3px solid var(--plug);padding-left:10px}}
h2{{font-size:17px;letter-spacing:.1em;text-transform:uppercase;margin:0 0 8px;font-weight:600}}
.hc{{color:var(--faint);font-size:12px;letter-spacing:.06em;text-transform:none;font-weight:400}}
.hc b{{color:var(--plug);font-weight:500}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;color:var(--faint);font-size:10px;letter-spacing:.16em;
text-transform:uppercase;border-bottom:1px solid var(--line);padding:5px 8px;font-weight:400}}
td{{padding:4px 8px;border-bottom:1px solid rgba(44,49,58,.5);vertical-align:top}}
tr.core{{opacity:.62}}
.num{{color:var(--faint);width:34px;text-align:right;font-size:11px}}
.fn{{font-size:12px;white-space:nowrap}}
tr.plug .fn{{color:#cfe0ff}}
.tag{{font-size:9px;letter-spacing:.12em;padding:1px 5px;border:1px solid var(--line)}}
.tag.plug{{color:var(--plug);border-color:var(--plug)}}
.tag.core{{color:var(--core)}}
.doc{{color:var(--dim);max-width:56ch}}
.k{{font-size:11px;color:var(--faint);max-width:26ch;overflow:hidden;text-overflow:ellipsis}}
.obs{{text-align:center;width:30px}}
.ok{{color:var(--ok)}} .erronly{{color:var(--warn)}} .nolog{{color:var(--faint)}}
.miss{{display:block;color:var(--miss);font-size:10px;font-family:'Barlow Condensed',sans-serif}}
code{{background:#0f1114;padding:1px 5px;color:var(--ink);font-family:'JetBrains Mono',monospace;font-size:12px}}
@media(max-width:900px){{.doc{{display:none}}}}
</style>

<header>
  <h1>Agent Zero — Wiring Map</h1>
  <div class="sub">GENERATED {e(d['generated'])} · agent-zero-v2 · not hand-written</div>
  <div class="stats">
    <div class="stat"><b>{c['extensions_total']}</b><span>extensions</span></div>
    <div class="stat"><b style="color:var(--plug)">{c['plugin']}</b><span>ours (exocortex)</span></div>
    <div class="stat"><b style="color:var(--core)">{c['core']}</b><span>agent zero core</span></div>
    <div class="stat"><b>{c['hooks']}</b><span>hooks</span></div>
    <div class="stat"><b>{sk['written']}/{sk['read']}</b><span>state keys w/r</span></div>
    <div class="stat"><b style="color:var(--miss)">{c['paths_missing']}</b><span>unresolved paths</span></div>
    {webui_stat}
  </div>
</header>
<main>
<div class="note">
<b>This page is generated by <code>scan_container.py</code> running inside the container, not written by hand.</b>
The previous wiring document drifted from the system for four months because it was a description.
This is a measurement with a timestamp — re-run it and it re-renders.
<br><br>
<b>What the observability column means.</b>
<span class=ok>●</span> emits on the happy path, so its silence is meaningful ·
<span class=erronly>!</span> prints only inside <code>except</code>, so silence means healthy ·
<span class=nolog>·</span> <b>{c['undetectable']} of {c['extensions_total']}</b> have zero stdout prints and are
structurally invisible to <code>docker logs</code> — for these, "silent" and "never fired" cannot be distinguished.
<br><br>
<b>Known limits of this instrument, stated so they are not mistaken for findings.</b>
State keys reached through module constants resolve only when the constant is a plain
string literal in the same file; <code>_recall_memories_task</code> appears in the severed list below and
is demonstrably read by <code>_91_recall_wait.py</code>. Treat that list as candidates to check, never a verdict.
Six earlier instruments in this codebase each reported a clean result because their null case
was indistinguishable from health.
</div>

<div class="note" style="border-left-color:var(--miss)">
<b>Severed candidates</b> (written, no reader found): <code>{e(', '.join(sk['severed_write_no_read']) or 'none')}</code><br>
<b>Read but never written here</b>: {len(sk['read_never_written'])} keys — most are set by A0 core outside these trees.
</div>
{''.join(rows)}
{webui_html}
</main>"""

out = os.path.join(S, "wiring_map.html")
io.open(out, "w", encoding="utf-8", newline="\n").write(doc)
print("wrote", out, os.path.getsize(out), "bytes")
