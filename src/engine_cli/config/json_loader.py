from __future__ import annotations

import json
from pathlib import Path

from engine_cli.config.errors import JsonConfigError


class JsonConfigLoader:
    """Load canonical JSON object config files."""

    def load_object(self, path: Path) -> dict[str, object]:
        """Return a decoded JSON object or an empty override when the file is absent."""
        if not path.is_file():
            return {}

        try:
            decoded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise JsonConfigError(f"Invalid JSON config file: {path}") from exc

        if not isinstance(decoded, dict):
            raise JsonConfigError(f"Config file must decode to a JSON object: {path}")

        return decoded
