import json
import tempfile
from pathlib import Path
import unittest

from engine_cli.config import ConfigResolver


class TestConfigResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = ConfigResolver()

    def test_config_resolver_uses_defaults_when_global_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            global_config_dir = Path(temp_dir)

            settings = self.resolver.resolve(global_config_dir=global_config_dir)

            self.assertEqual(settings.default_agent_profile_id, "default-profile")

    def test_config_resolver_applies_layer_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            global_config_dir = root / "global"
            global_config_dir.mkdir()
            workspace_root = root / "workspace"
            (workspace_root / ".engine_cli" / "config").mkdir(parents=True)
            (global_config_dir / "settings.json").write_text(
                json.dumps({"default_agent_profile_id": "global-profile"}),
                encoding="utf-8",
            )
            (workspace_root / ".engine_cli" / "config" / "settings.json").write_text(
                json.dumps({"default_agent_profile_id": "workspace-profile"}),
                encoding="utf-8",
            )

            settings = self.resolver.resolve(
                global_config_dir=global_config_dir,
                workspace_root=workspace_root,
            )

            self.assertEqual(settings.default_agent_profile_id, "workspace-profile")

    def test_config_resolver_reads_only_canonical_settings_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            global_config_dir = Path(temp_dir)
            (global_config_dir / "ignored.json").write_text(
                json.dumps({"default_agent_profile_id": "ignored-profile"}),
                encoding="utf-8",
            )

            settings = self.resolver.resolve(global_config_dir=global_config_dir)

            self.assertEqual(settings.default_agent_profile_id, "default-profile")

    def test_config_resolver_allows_missing_workspace_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            global_config_dir = root / "global"
            global_config_dir.mkdir()
            workspace_root = root / "workspace"
            workspace_root.mkdir()
            (global_config_dir / "settings.json").write_text(
                json.dumps({"default_agent_profile_id": "global-profile"}),
                encoding="utf-8",
            )

            settings = self.resolver.resolve(
                global_config_dir=global_config_dir,
                workspace_root=workspace_root,
            )

            self.assertEqual(settings.default_agent_profile_id, "global-profile")
