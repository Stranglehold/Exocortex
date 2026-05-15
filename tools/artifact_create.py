"""
artifact_create — Exocortex Artifact Authoring System
======================================================
Creates premium visual artifacts from pre-built templates and structured data.

"The model decides what to say. The system decides how it looks."

Separates content reasoning (what the model is good at) from HTML/CSS/JS
authoring (what local models do poorly under token pressure and output ceilings).
The model selects a template, provides structured data, and the tool handles
all rendering.

Available templates: dashboard, table, timeline, network, report, gallery,
                     constellation, comparison

Available themes: indigo (default), ember, slate, midnight, graphite

Usage:
    artifact_create(
        template="dashboard",
        data={
            "title": "Stack Status",
            "cards": [
                {"name": "BST",        "status": "healthy",  "metric": "v3.3"},
                {"name": "Supervisor", "status": "healthy",  "metric": "active"},
                {"name": "OSS",        "status": "warning",  "metric": "paused"},
            ]
        }
    )

See /a0/usr/artifact_templates/manifest.json for full schema documentation
for each template type.

Template injection markers (used by Opus-authored templates):
    /* {{THEME_VARIABLES}} */  — inside a CSS <style> block
    <!-- {{DATA_JSON}} -->     — anywhere in <body> (injects <script> tag)
    {{TITLE}}                  — plain string replacement
    {{SUBTITLE}}               — plain string replacement
    {{DATE}}                   — plain string replacement
    {{AUTHOR}}                 — plain string replacement
"""

import json
import time
from pathlib import Path

from helpers.tool import Tool, Response


class ArtifactCreate(Tool):
    """Create a premium visual artifact from a template and structured data."""

    TEMPLATE_DIR = Path("/a0/usr/artifact_templates")
    THEMES_DIR   = Path("/a0/usr/artifact_templates/themes")
    OUTPUT_DIR   = Path("/a0/work/artifacts")

    VALID_TEMPLATES = frozenset({
        "dashboard", "table", "timeline", "network",
        "report", "gallery", "constellation", "comparison",
    })
    VALID_THEMES = frozenset({"indigo", "ember", "slate", "midnight", "graphite"})

    async def execute(
        self,
        template: str = "dashboard",
        theme: str = "indigo",
        data: dict | None = None,
        **kwargs,
    ) -> Response:
        data = data or {}

        # ── Allow data as JSON string (defensive — A0 parses args from JSON) ──
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}

        # ── Validate template ────────────────────────────────────────────────
        template = (template or "dashboard").lower().strip()
        if template not in self.VALID_TEMPLATES:
            return Response(
                message=(
                    f"artifact_create: unknown template '{template}'.\n"
                    f"Valid templates: {', '.join(sorted(self.VALID_TEMPLATES))}\n"
                    f"See manifest: {self.TEMPLATE_DIR / 'manifest.json'}"
                ),
                break_loop=False,
            )

        # ── Validate/default theme ───────────────────────────────────────────
        theme = (theme or "indigo").lower().strip()
        if theme not in self.VALID_THEMES:
            theme = "indigo"

        # ── Load template ────────────────────────────────────────────────────
        template_path = self.TEMPLATE_DIR / f"{template}.html"
        if not template_path.exists():
            return Response(
                message=(
                    f"artifact_create: template '{template}' not yet authored.\n"
                    f"Expected at: {template_path}\n"
                    f"Templates are authored in Phase 2 (Opus via Claude Code).\n"
                    f"Currently available: "
                    + ", ".join(
                        p.stem for p in self.TEMPLATE_DIR.glob("*.html")
                    ) or "none"
                ),
                break_loop=False,
            )

        try:
            html = template_path.read_text(encoding="utf-8")
        except Exception as e:
            return Response(
                message=f"artifact_create: failed to read template '{template}': {e}",
                break_loop=False,
            )

        # ── Load theme and build CSS variables block ─────────────────────────
        css_vars_block = ""
        theme_path = self.THEMES_DIR / f"{theme}.json"
        if theme_path.exists():
            try:
                theme_cfg  = json.loads(theme_path.read_text(encoding="utf-8"))
                variables  = theme_cfg.get("variables", {})
                css_vars_block = ":root {\n"
                for k, v in variables.items():
                    css_vars_block += f"  {k}: {v};\n"
                css_vars_block += "}"
            except Exception:
                pass  # theme failure is non-fatal; template falls back to its own defaults

        # ── Inject theme ─────────────────────────────────────────────────────
        # Templates place the marker inside an existing <style> block:
        #   <style> /* {{THEME_VARIABLES}} */ </style>
        # OR as a standalone block comment in <head>:
        #   <!-- {{THEME_VARIABLES}} -->
        html = html.replace("/* {{THEME_VARIABLES}} */", css_vars_block)
        html = html.replace(
            "<!-- {{THEME_VARIABLES}} -->",
            f"<style>\n{css_vars_block}\n</style>",
        )

        # ── Inject scalar fields ─────────────────────────────────────────────
        html = html.replace("{{TITLE}}",    str(data.get("title",    "")))
        html = html.replace("{{SUBTITLE}}", str(data.get("subtitle", "")))
        html = html.replace("{{DATE}}",     str(data.get("date",     "")))
        html = html.replace("{{AUTHOR}}",   str(data.get("author",   "")))

        # ── Inject full data as JSON (template JS reads from #artifact-data) ─
        # This is the primary data channel. Templates read:
        #   const data = JSON.parse(document.getElementById('artifact-data').textContent)
        data_script = (
            '<script id="artifact-data" type="application/json">\n'
            + json.dumps(data, ensure_ascii=False)
            + "\n</script>"
        )
        html = html.replace("<!-- {{DATA_JSON}} -->", data_script)

        # ── Persist to output directory ──────────────────────────────────────
        try:
            self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            ts   = int(time.time())
            path = self.OUTPUT_DIR / f"{template}_{ts}.html"
            path.write_text(html, encoding="utf-8")
        except Exception:
            pass  # file write failure is non-fatal; artifact still emits to panel

        # ── Emit artifact to panel ───────────────────────────────────────────
        title = str(data.get("title", template.title()))
        self.agent.context.log.log(
            type="artifact",   # type: ignore[arg-type]
            heading=title,
            content=html,
        )

        return Response(
            message=f"Artifact '{title}' emitted using {template}/{theme} template.",
            break_loop=False,
        )
