import os
from helpers.api import ApiHandler, Request, Response
from helpers.security import safe_filename


BACKGROUNDS_DIR = "/a0/usr/plugins/exocortex/webui/backgrounds"
BACKGROUNDS_URL = "/usr/plugins/exocortex/webui/backgrounds"

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif", ".avif"}


class ThemeUpload(ApiHandler):
    """Upload a background image to the plugin's webui/backgrounds/ directory.

    URL: POST /api/plugins/exocortex/api_theme_upload  (multipart/form-data)
    Field: file (image file)
    Returns: { "ok": true, "url": "/usr/plugins/exocortex/webui/backgrounds/<name>" }
    """

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict:
        if "file" not in request.files:
            return {"ok": False, "error": "no file in request"}

        file = request.files["file"]
        if not file or not file.filename:
            return {"ok": False, "error": "empty file"}

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXT:
            return {"ok": False, "error": f"unsupported type: {ext}"}

        filename = safe_filename(file.filename)
        if not filename:
            return {"ok": False, "error": "invalid filename"}

        try:
            os.makedirs(BACKGROUNDS_DIR, exist_ok=True)
            dest = os.path.join(BACKGROUNDS_DIR, filename)
            file.save(dest)
            return {"ok": True, "url": f"{BACKGROUNDS_URL}/{filename}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
