import tempfile
from pathlib import Path
import unittest

from engine_cli.infrastructure.agent_runtime import InMemoryAgentRuntimeSupervisor
from engine_cli.application.composition import create_app_runtime
from engine_cli.infrastructure.persistence import (
    SqliteAgentRuntimeRepository,
    SqliteServerInstanceRepository,
)
from engine_cli.infrastructure.persistence.sqlite import SqliteTaskRunRepository


class TestAppComposition(unittest.TestCase):
    def test_create_app_runtime_builds_persistence_config_and_services(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_root = Path(temp_dir)

            runtime = create_app_runtime(app_root=app_root)

            self.assertEqual(runtime.app_paths.db_path, app_root / "db" / "engine.db")
            self.assertIs(runtime.session_coordinator.context, runtime.session_context)
            self.assertEqual(runtime.session_context.active_agent_profile_id, "base-default")
            self.assertIsInstance(runtime.server_manager.catalog, SqliteServerInstanceRepository)
            self.assertIsInstance(
                runtime.agent_runtime_manager.catalog,
                SqliteAgentRuntimeRepository,
            )
            self.assertIsInstance(
                runtime.lifecycle_service.execution_service.task_repository,
                SqliteTaskRunRepository,
            )
            self.assertIs(
                runtime.server_manager.runtime_catalog,
                runtime.agent_runtime_manager.catalog,
            )
            self.assertIs(
                runtime.agent_runtime_lifecycle_service.runtime_catalog,
                runtime.agent_runtime_manager.catalog,
            )
            self.assertIsInstance(
                runtime.agent_runtime_lifecycle_service.supervisor,
                InMemoryAgentRuntimeSupervisor,
            )
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
