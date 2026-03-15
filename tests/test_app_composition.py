import tempfile
from pathlib import Path
import unittest

from engine_cli.application.composition import create_app_runtime
from engine_cli.infrastructure.persistence import SqliteServerInstanceRepository


class TestAppComposition(unittest.TestCase):
    def test_create_app_runtime_builds_persistence_config_and_services(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_root = Path(temp_dir)

            runtime = create_app_runtime(app_root=app_root)

            self.assertEqual(runtime.app_paths.db_path, app_root / "db" / "engine.db")
            self.assertEqual(runtime.session_context.active_agent_profile_id, "base-default")
            self.assertIsInstance(runtime.server_manager.catalog, SqliteServerInstanceRepository)
            self.assertIs(runtime.server_command_service.lifecycle_service, runtime.lifecycle_service)

    def test_create_app_runtime_accepts_explicit_workspace_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_root = Path(temp_dir)
            workspace_root = app_root / "workspace"
            workspace_root.mkdir()

            runtime = create_app_runtime(
                app_root=app_root,
                workspace_root=workspace_root,
            )

            self.assertEqual(runtime.workspace_root, workspace_root.resolve())
