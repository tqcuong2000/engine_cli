from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Mapping

from engine_cli.config.defaults import DEFAULT_SETTINGS
from engine_cli.config.json_loader import JsonConfigLoader
from engine_cli.config.models import ResolvedSettings


CANONICAL_SETTINGS_FILE = "settings.json"


class ConfigResolver:
    """Resolve layered config from built-in defaults plus file-backed overrides."""

    def __init__(self, loader: JsonConfigLoader | None = None) -> None:
        self.loader = loader or JsonConfigLoader()

    def resolve(
        self,
        *,
        global_config_dir: Path,
        workspace_root: Path | None = None,
    ) -> ResolvedSettings:
        """Resolve settings with precedence defaults < global < workspace."""
        merged = deepcopy(DEFAULT_SETTINGS)
        self._merge_objects(
            merged,
            self.loader.load_object(global_config_dir / CANONICAL_SETTINGS_FILE),
        )
        if workspace_root is not None:
            workspace_config_path = (
                workspace_root / ".engine_cli" / "config" / CANONICAL_SETTINGS_FILE
            )
            self._merge_objects(merged, self.loader.load_object(workspace_config_path))
        return ResolvedSettings.from_mapping(merged)

    def _merge_objects(
        self,
        base: dict[str, object],
        override: Mapping[str, object],
    ) -> None:
        for key, value in override.items():
            existing = base.get(key)
            if isinstance(existing, dict) and isinstance(value, dict):
                nested = deepcopy(existing)
                self._merge_objects(nested, value)
                base[key] = nested
                continue
            base[key] = deepcopy(value)
