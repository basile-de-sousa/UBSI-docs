"""Read the Vite manifest rather than guessing generated asset names."""
import json
from pathlib import PurePosixPath

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def frontend_assets():
    try:
        manifest = json.loads((settings.FRONTEND_ROOT / ".vite/manifest.json").read_text())
        entry = manifest["frontend/main.ts"]
        # Dynamic editor chunks must be present too, not only the reader entry.
        paths = list(dict.fromkeys(path for item in manifest.values() for path in [item["file"], *item.get("css", [])]))
        if any(not isinstance(path, str) or not path.startswith("assets/") or ".." in PurePosixPath(path).parts for path in paths):
            raise ValueError
        if not all((settings.FRONTEND_ROOT / path).is_file() for path in paths):
            raise ValueError
        return {"script": entry["file"], "styles": entry.get("css", []), "files": paths}
    except (OSError, ValueError, KeyError, TypeError):
        raise ImproperlyConfigured("Frontend build missing or invalid. Run npm run build in portal/.") from None
