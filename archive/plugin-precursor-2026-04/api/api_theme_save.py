import json
import os
from helpers.api import ApiHandler, Request, Response


class ThemeSave(ApiHandler):
    """Save an edited theme JSON to the Exocortex plugin themes directory.

    URL: POST /api/plugins/exocortex/api_theme_save
    Body: { "filename": "shadow-moses.json", "config": { ... } }
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict:
        filename = input.get("filename", "")
        config = input.get("config", {})

        if not filename or not isinstance(config, dict):
            return {"ok": False, "error": "missing fields"}

        # Sanitize: basename only, must end in .json
        filename = os.path.basename(filename)
        if not filename.endswith(".json") or not filename:
            return {"ok": False, "error": "invalid filename"}

        theme_dir = "/a0/usr/plugins/exocortex/webui/themes"
        path = os.path.join(theme_dir, filename)

        try:
            os.makedirs(theme_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
