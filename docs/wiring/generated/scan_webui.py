#!/usr/bin/env python3
"""
scan_webui.py — the web UI section for Kestrel's generated wiring map (docs/wiring/generated/scan_container.py).

Fable, 2026-09-03. Same contract as scan_container.py: runs INSIDE the container, read-only, emits JSON on stdout
(or import `scan_webui()` and add its dict under a "webui" key). Same rule: the instrument states its own limits.

What it measures, from /a0/webui and the plugin roots:
  * CSS custom properties: every `--name:` defined in index.css and css/*.css, and where each is read
    (var(--name)) across css/html/js. Defined-but-never-read is a candidate, not a verdict (see limits).
  * Extension points: HTML `<x-extension id="…">` in index.html and components; JS `callJsExtensions("…")`
    calls in js/*.js. Per point: which plugin folders provide files for it (`<plugin>/extensions/webui/<point>/`).
  * Plugin UI parts: `<plugin>/webui/*` files (stores, modals, thumbnails), the other mechanism.
  * The JS surface: file sizes, so the reader knows where the weight is (messages.js is a third of it).
  * Known upstream constants that decide behaviour Jake feels: the message window sizes and the smooth-stream
    flag (grep-derived; if the file changes shape they read as null, never as a guess).

Limits, stated on purpose:
  * A custom property read through JavaScript (`getComputedStyle(...).getPropertyValue("--x")`) or built by
    string concatenation is invisible to the var(--name) regex; such properties will show zero reads.
  * Tailwind-style or Alpine-bound class names are not tokens and are not counted.
  * Extension points are found by literal string; a point name passed through a variable is missed.
  * Reads inside vendor/ are ignored (third-party CSS defines and reads its own properties).
"""
import json, os, re, sys

WEBUI = "/a0/webui"
PLUGIN_ROOTS = ["/a0/plugins", "/a0/usr/plugins"]

DEF_RE = re.compile(r"(--[a-zA-Z0-9_-]+)\s*:")
USE_RE = re.compile(r"var\(\s*(--[a-zA-Z0-9_-]+)")
XEXT_RE = re.compile(r'<x-extension[^>]*\bid="([^"]+)"')
JSEXT_RE = re.compile(r'callJsExtensions\(\s*["\']([^"\']+)["\']')
MAXWIN_RE = re.compile(r"const DEFAULT_MAX_WINDOW\s*=\s*([^;]+);")
PAGE_RE = re.compile(r"const DEFAULT_PAGE_SIZE\s*=\s*(\d+)")
SMOOTH_RE = re.compile(r"smoothStream:\s*(false|true)\s*,\s*//\s*([^\n]{0,80})")


def read(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        return ""


def walk(root, exts, skip=("vendor", "node_modules", "public")):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in skip]
        for fn in sorted(fns):
            if fn.lower().endswith(exts):
                yield os.path.join(dp, fn)


def scan_webui():
    if not os.path.isdir(WEBUI):
        return {"error": f"{WEBUI} not found", "limits": ["webui root missing; nothing measured"]}

    # ── tokens ───────────────────────────────────────────────────────────────────────────────────────
    defined = {}
    for p in [os.path.join(WEBUI, "index.css")] + list(walk(os.path.join(WEBUI, "css"), (".css",))):
        for name in DEF_RE.findall(read(p)):
            defined.setdefault(name, []).append(os.path.relpath(p, WEBUI))
    reads = {}
    for p in walk(WEBUI, (".css", ".html", ".js", ".mjs")):
        for name in USE_RE.findall(read(p)):
            reads[name] = reads.get(name, 0) + 1
    tokens = {
        "defined": len(defined),
        "read_somewhere": sum(1 for n in defined if reads.get(n)),
        "defined_never_read_candidates": sorted(n for n in defined if not reads.get(n)),
        "read_never_defined": sorted(n for n in reads if n not in defined),
        "pairs_dark_light": sum(1 for n in defined if n.endswith("-dark") and (n[:-5] + "-light") in defined),
    }

    # ── extension points ─────────────────────────────────────────────────────────────────────────────
    html_points, js_points = set(), set()
    for p in walk(WEBUI, (".html",)):
        html_points.update(XEXT_RE.findall(read(p)))
    for p in walk(WEBUI, (".js", ".mjs")):
        js_points.update(JSEXT_RE.findall(read(p)))
    providers = {}
    for root in PLUGIN_ROOTS:
        if not os.path.isdir(root):
            continue
        for plugin in sorted(os.listdir(root)):
            base = os.path.join(root, plugin, "extensions", "webui")
            if not os.path.isdir(base):
                continue
            for point in sorted(os.listdir(base)):
                files = sorted(os.listdir(os.path.join(base, point)))
                providers.setdefault(point, []).append({"plugin": os.path.join(root, plugin), "files": files})
    points = {}
    for name in sorted(html_points | js_points | set(providers)):
        points[name] = {
            "kind": "html" if name in html_points else "js" if name in js_points else "provider-only",
            "providers": providers.get(name, []),
        }

    # ── plugin UI parts (the other mechanism) ────────────────────────────────────────────────────────
    parts = []
    for root in PLUGIN_ROOTS:
        if not os.path.isdir(root):
            continue
        for plugin in sorted(os.listdir(root)):
            w = os.path.join(root, plugin, "webui")
            if os.path.isdir(w):
                files = [os.path.relpath(f, w) for f in walk(w, (".js", ".html", ".css", ".mjs"))]
                if files:
                    parts.append({"plugin": os.path.join(root, plugin), "files": files})

    # ── weight ───────────────────────────────────────────────────────────────────────────────────────
    js_sizes = {os.path.relpath(p, WEBUI): os.path.getsize(p) for p in walk(WEBUI, (".js", ".mjs"))}
    css_total = sum(os.path.getsize(p) for p in [os.path.join(WEBUI, "index.css")] + list(walk(os.path.join(WEBUI, "css"), (".css",))) if os.path.exists(p))

    # ── behaviour constants Jake feels ───────────────────────────────────────────────────────────────
    mw = read(os.path.join(WEBUI, "js", "message-window.js")); ms = read(os.path.join(WEBUI, "js", "messages.js"))
    m1, m2, m3 = MAXWIN_RE.search(mw), PAGE_RE.search(mw), SMOOTH_RE.search(ms)
    behaviour = {
        "message_window_page_size": int(m2.group(1)) if m2 else None,
        "message_window_max_expr": m1.group(1).strip() if m1 else None,
        "smooth_stream": (m3.group(1) + "  // " + m3.group(2).strip()) if m3 else None,
        # local patches leave dated markers in the file; the count says whether the patch is applied (Kestrel's
        # naming suggestion, 2026-09-03: a key that ages better than a person's name).
        "local_patch_markers_in_messages_js": ms.count("fable 2026-09-03"),
    }

    return {
        "root": WEBUI,
        "tokens": tokens,
        "extension_points": points,
        "plugin_ui_parts": parts,
        "weight": {
            "js_files": len(js_sizes),
            "js_bytes": sum(js_sizes.values()),
            "js_largest": sorted(js_sizes.items(), key=lambda kv: -kv[1])[:6],
            "css_bytes": css_total,
        },
        "behaviour": behaviour,
        "limits": [
            "token reads via getPropertyValue()/string-building are invisible to the var(--x) regex: zero-read tokens are candidates, not dead",
            "extension points named through a variable are missed",
            "vendor/, node_modules/, public/ excluded from reads",
        ],
    }


if __name__ == "__main__":
    print(json.dumps({"generated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()[:19] + "Z",
                      "webui": scan_webui()}, indent=1))
