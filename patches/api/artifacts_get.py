"""
Artifacts Get API
=================
POST /artifacts_get

Returns the full HTML content of a named artifact from the artifacts directory.
The frontend calls this when a user clicks an artifact in the sidebar, then
passes the content to window.artifactPanel.update() to render it in the iframe.

Input:  {"name": "network_graph.html"}
Output: {"content": "...", "type": "html", "title": "OpenPlanter Network Graph"}
"""

import json
import os
import re

from flask import Request, Response

from python.helpers.api import ApiHandler
from python.helpers.print_style import PrintStyle

ARTIFACTS_DIR = "/a0/usr/workdir/artifacts"


class ArtifactsGet(ApiHandler):

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            name = (input.get("name") or "").strip()
            if not name:
                return Response(
                    json.dumps({"error": "name is required"}),
                    status=400,
                    mimetype="application/json",
                )

            # Security: only allow .html files, no path traversal
            if not name.endswith(".html") or "/" in name or "\\" in name or ".." in name:
                return Response(
                    json.dumps({"error": "invalid artifact name"}),
                    status=400,
                    mimetype="application/json",
                )

            path = os.path.join(ARTIFACTS_DIR, name)
            if not os.path.isfile(path):
                return Response(
                    json.dumps({"error": f"artifact not found: {name}"}),
                    status=404,
                    mimetype="application/json",
                )

            with open(path, encoding="utf-8") as f:
                content = f.read()

            # Read sidecar for metadata
            stem = name[:-5]
            sidecar_path = os.path.join(ARTIFACTS_DIR, f"{stem}.json")
            meta: dict = {}
            if os.path.exists(sidecar_path):
                try:
                    with open(sidecar_path, encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass

            # Fallback title extraction
            title = meta.get("title") or ""
            if not title:
                m = re.search(r"<title[^>]*>([^<]+)</title>", content[:4096], re.IGNORECASE)
                if m:
                    title = m.group(1).strip()
            if not title:
                title = stem.replace("_", " ").title()

            PrintStyle(background_color="#2ECC71", font_color="white", bold=True, padding=True).print(
                f"[ARTIFACTS] Served {name} ({len(content)} bytes)"
            )
            return {
                "content": content,
                "type": meta.get("type", "html"),
                "title": title,
            }

        except Exception as e:
            PrintStyle.error(f"[ARTIFACTS] Get error: {e}")
            return Response(
                json.dumps({"error": str(e)}),
                status=500,
                mimetype="application/json",
            )
