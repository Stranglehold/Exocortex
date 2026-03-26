"""
Artifacts List API
==================
GET /artifacts_list

Returns a JSON manifest of all saved artifacts in the artifacts directory.
For each .html file found, reads a sidecar .json for metadata, or falls back
to extracting the <title> tag from the HTML itself.

Used by the artifacts sidebar component to populate the library without
requiring the agent to re-emit full HTML content.
"""

import json
import os
import re
from datetime import datetime

from flask import Request, Response

from python.helpers.api import ApiHandler
from python.helpers.print_style import PrintStyle

ARTIFACTS_DIR = "/a0/usr/workdir/artifacts"


class ArtifactsList(ApiHandler):

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
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            if not os.path.isdir(ARTIFACTS_DIR):
                return {"artifacts": []}

            artifacts = []
            for fname in sorted(os.listdir(ARTIFACTS_DIR)):
                if not fname.endswith(".html"):
                    continue

                stem = fname[:-5]
                path = os.path.join(ARTIFACTS_DIR, fname)

                # Read sidecar metadata if present
                sidecar_path = os.path.join(ARTIFACTS_DIR, f"{stem}.json")
                meta: dict = {}
                if os.path.exists(sidecar_path):
                    try:
                        with open(sidecar_path, encoding="utf-8") as f:
                            meta = json.load(f)
                    except Exception:
                        pass

                # Fallback: extract <title> from the HTML
                title = meta.get("title") or ""
                if not title:
                    try:
                        with open(path, encoding="utf-8") as f:
                            html_head = f.read(4096)
                        m = re.search(r"<title[^>]*>([^<]+)</title>", html_head, re.IGNORECASE)
                        if m:
                            title = m.group(1).strip()
                    except Exception:
                        pass
                if not title:
                    title = stem.replace("_", " ").title()

                stat = os.stat(path)
                artifacts.append({
                    "name": fname,
                    "stem": stem,
                    "title": title,
                    "description": meta.get("description", ""),
                    "type": meta.get("type", "html"),
                    "tags": meta.get("tags", []),
                    "size": stat.st_size,
                    "modified": datetime.utcfromtimestamp(stat.st_mtime).isoformat(),
                })


            return {"artifacts": artifacts}

        except Exception as e:
            PrintStyle.error(f"[ARTIFACTS] List error: {e}")
            return Response(
                json.dumps({"error": str(e)}),
                status=500,
                mimetype="application/json",
            )
