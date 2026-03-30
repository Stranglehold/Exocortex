import json
import os
from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files


class ApiThemeSave(ApiHandler):
    """Save a modified theme JSON back to disk."""

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
        filename = input.get("filename", "")
        config = input.get("config", {})

        # Security: strip any path components, only .json allowed
        filename = os.path.basename(filename)
        if not filename or not filename.endswith(".json"):
            return {"error": "Invalid filename — must be a .json file"}

        themes_dir = files.get_abs_path("webui/themes")
        path = os.path.join(themes_dir, filename)

        # Only overwrite existing themes, never create arbitrary files
        if not os.path.exists(path):
            return {"error": f"Theme not found: {filename}"}

        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return {"ok": True, "saved": filename}
