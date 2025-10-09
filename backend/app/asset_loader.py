import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

from flask import current_app, url_for


class MissingManifest(Exception):
    """Raised when the Vite manifest is missing in production."""


def _manifest_path() -> Path:
    static_folder = Path(current_app.static_folder)
    return static_folder / "dist" / ".vite" / "manifest.json"


@lru_cache(maxsize=1)
def _load_manifest() -> Dict[str, Dict[str, object]]:
    manifest_file = _manifest_path()
    if not manifest_file.exists():
        raise MissingManifest(
            f"Vite manifest not found at {manifest_file}. "
            "Run `npm run build` in frontend/ and copy the contents of frontend/dist to backend/static/dist."
        )
    with manifest_file.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def asset_url(entry: str) -> str:
    manifest = _load_manifest()
    data = manifest.get(entry)
    if not data:
        raise KeyError(f"Asset entry '{entry}' not found in Vite manifest")
    return url_for("static", filename=f"dist/{data['file']}")


def asset_css(entry: str) -> list[str]:
    manifest = _load_manifest()
    data = manifest.get(entry, {})
    css_files = data.get("css", [])
    return [url_for("static", filename=f"dist/{href}") for href in css_files]


def reset_manifest_cache() -> None:
    _load_manifest.cache_clear()
