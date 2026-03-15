import json
import tempfile
from pathlib import Path
import unittest

from engine_cli.config import ConfigResolver
from engine_cli.config.errors import ConfigResolutionError
from engine_cli.domain import OperatingMode


class TestConfigResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = ConfigResolver()

    def test_config_resolver_uses_defaults_when_global_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            global_config_dir = Path(temp_dir)

            settings = self.resolver.resolve(global_config_dir=global_config_dir)

            self.assertEqual(settings.default_agent_profile_id, "base-default")
            self.assertEqual(
                settings.default_profile_id_for(OperatingMode.SERVER),
                "server-default",
            )
            self.assertEqual(
                settings.default_profile_for(OperatingMode.DATAPACK).agent_kind,
                "datapack_dev",
            )

    def test_config_resolver_materializes_agent_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = self.resolver.resolve(global_config_dir=Path(temp_dir))

            profile = settings.get_profile("server-default")

            self.assertIsNotNone(profile)
            assert profile is not None
            self.assertEqual(profile.name, "Server Ops")
            self.assertEqual(profile.mode, OperatingMode.SERVER)
            self.assertEqual(profile.agent_kind, "server_ops")

    def test_config_resolver_applies_layer_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            global_config_dir = root / "global"
            global_config_dir.mkdir()
            workspace_root = root / "workspace"
            (workspace_root / ".engine_cli" / "config").mkdir(parents=True)
            (global_config_dir / "settings.json").write_text(
                json.dumps(
                    self._build_settings_payload(
                        base_profile_id="global-base",
                        base_profile_name="Global Base",
                    )
                ),
                encoding="utf-8",
            )
            (workspace_root / ".engine_cli" / "config" / "settings.json").write_text(
                json.dumps(
                    self._build_settings_payload(
                        base_profile_id="workspace-base",
                        base_profile_name="Workspace Base",
                    )
                ),
                encoding="utf-8",
            )

            settings = self.resolver.resolve(
                global_config_dir=global_config_dir,
                workspace_root=workspace_root,
            )

            self.assertEqual(settings.default_agent_profile_id, "workspace-base")
            self.assertEqual(
                settings.default_profile_for(OperatingMode.BASE).name,
                "Workspace Base",
            )

    def test_config_resolver_reads_only_canonical_settings_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            global_config_dir = Path(temp_dir)
            (global_config_dir / "ignored.json").write_text(
                json.dumps(self._build_settings_payload(base_profile_id="ignored-base")),
                encoding="utf-8",
            )

            settings = self.resolver.resolve(global_config_dir=global_config_dir)

            self.assertEqual(settings.default_agent_profile_id, "base-default")

    def test_config_resolver_allows_missing_workspace_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            global_config_dir = root / "global"
            global_config_dir.mkdir()
            workspace_root = root / "workspace"
            workspace_root.mkdir()
            (global_config_dir / "settings.json").write_text(
                json.dumps(
                    self._build_settings_payload(
                        base_profile_id="global-base",
                        base_profile_name="Global Base",
                    )
                ),
                encoding="utf-8",
            )

            settings = self.resolver.resolve(
                global_config_dir=global_config_dir,
                workspace_root=workspace_root,
            )

            self.assertEqual(settings.default_agent_profile_id, "global-base")

    def test_config_resolver_rejects_duplicate_profile_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            global_config_dir = Path(temp_dir)
            payload = self._build_settings_payload()
            payload["agent_profiles"] = [
                {
                    "agent_profile_id": "duplicate",
                    "name": "Base One",
                    "mode": "base",
                    "agent_kind": "system_assistant",
                },
                {
                    "agent_profile_id": "duplicate",
                    "name": "Server One",
                    "mode": "server",
                    "agent_kind": "server_ops",
                },
            ]
            (global_config_dir / "settings.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigResolutionError):
                self.resolver.resolve(global_config_dir=global_config_dir)

    def test_config_resolver_rejects_unknown_mode_default_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            global_config_dir = Path(temp_dir)
            payload = self._build_settings_payload()
            payload["default_agent_profiles"] = {
                "base": "missing-profile",
                "server": "server-default",
                "datapack": "datapack-default",
            }
            (global_config_dir / "settings.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigResolutionError):
                self.resolver.resolve(global_config_dir=global_config_dir)

    def test_config_resolver_rejects_mismatched_mode_default_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            global_config_dir = Path(temp_dir)
            payload = self._build_settings_payload()
            payload["default_agent_profiles"] = {
                "base": "server-default",
                "server": "server-default",
                "datapack": "datapack-default",
            }
            (global_config_dir / "settings.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigResolutionError):
                self.resolver.resolve(global_config_dir=global_config_dir)

    def _build_settings_payload(
        self,
        *,
        base_profile_id: str = "base-default",
        base_profile_name: str = "Base Assistant",
    ) -> dict[str, object]:
        return {
            "default_agent_profiles": {
                "base": base_profile_id,
                "server": "server-default",
                "datapack": "datapack-default",
            },
            "agent_profiles": [
                {
                    "agent_profile_id": base_profile_id,
                    "name": base_profile_name,
                    "mode": "base",
                    "agent_kind": "system_assistant",
                },
                {
                    "agent_profile_id": "server-default",
                    "name": "Server Ops",
                    "mode": "server",
                    "agent_kind": "server_ops",
                },
                {
                    "agent_profile_id": "datapack-default",
                    "name": "Datapack Dev",
                    "mode": "datapack",
                    "agent_kind": "datapack_dev",
                },
            ],
        }
