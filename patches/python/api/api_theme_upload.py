import os
from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files
from python.helpers.security import safe_filename

ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif"}
ALLOWED_AUDIO = {".wav", ".mp3", ".ogg"}
ALLOWED_EXT   = ALLOWED_IMAGE | ALLOWED_AUDIO
MAX_BYTES = 20 * 1024 * 1024  # 20 MB


class ApiThemeUpload(ApiHandler):
    """Upload an image or audio asset into the themes/assets directory.

    Images are saved to webui/themes/assets/.
    Audio files (.wav, .mp3, .ogg) are saved to webui/themes/assets/sounds/.
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict:
        if "file" not in request.files:
            return {"error": "No file in request"}

        upload = request.files["file"]
        if not upload or not upload.filename:
            return {"error": "Empty file"}

        filename = safe_filename(upload.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXT:
            return {"error": f"File type not allowed: {ext}. Allowed: {', '.join(ALLOWED_EXT)}"}

        # Check size before saving
        upload.seek(0, 2)
        size = upload.tell()
        upload.seek(0)
        if size > MAX_BYTES:
            return {"error": f"File too large ({size // 1024}KB). Max 20MB."}

        # Audio files go into a sounds/ subdirectory to keep assets organised
        if ext in ALLOWED_AUDIO:
            assets_dir = files.get_abs_path("webui/themes/assets/sounds")
            url_path   = f"/themes/assets/sounds/{filename}"
        else:
            assets_dir = files.get_abs_path("webui/themes/assets")
            url_path   = f"/themes/assets/{filename}"

        os.makedirs(assets_dir, exist_ok=True)

        dest = os.path.join(assets_dir, filename)
        upload.save(dest)

        return {"ok": True, "src": url_path, "filename": filename}
