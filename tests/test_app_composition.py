import tempfile
from contextlib import closing
from pathlib import Path
import sqlite3
import unittest

from engine_cli.infrastructure.agent_runtime import InMemoryAgentRuntimeSupervisor
from engine_cli.application.composition import create_app_runtime
from engine_cli.domain import (
    AgentRuntime,
    AgentRuntimeLifecycleState,
    ServerInstance,
    ServerInstanceLifecycleState,
)
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

    def test_create_app_runtime_reconciles_transient_agent_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_root = Path(temp_dir)
            runtime_repository = SqliteAgentRuntimeRepository(app_root / "db" / "engine.db")
            runtime_repository.save_runtime(
                AgentRuntime(
                    agent_runtime_id="runtime-1",
                    name="Ops Bot",
                    agent_profile_id="profile-1",
                    server_instance_id="srv-1",
                    agent_kind="server_ops",
                    lifecycle_state=AgentRuntimeLifecycleState.ACTIVE,
                )
            )

            runtime = create_app_runtime(app_root=app_root)

            persisted_runtime = runtime.agent_runtime_manager.get_runtime("runtime-1")
            self.assertIsNotNone(persisted_runtime)
            assert persisted_runtime is not None
            self.assertEqual(
                persisted_runtime.lifecycle_state,
                AgentRuntimeLifecycleState.STOPPED,
            )
            self.assertIsNone(
                runtime.agent_runtime_lifecycle_service.get_handle("runtime-1")
            )

    def test_create_app_runtime_reconciles_transient_server_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_root = Path(temp_dir)
            server_repository = SqliteServerInstanceRepository(app_root / "db" / "engine.db")
            server_repository.save_server(
                ServerInstance(
                    server_instance_id="srv-1",
                    name="Lobby",
                    location="X:/servers/lobby",
                    command="java -jar fabric.jar --nogui",
                    minecraft_version="1.21.11",
                    server_distribution="fabric",
                    lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
                )
            )
            with closing(sqlite3.connect(app_root / "db" / "engine.db")) as connection:
                connection.execute(
                    "UPDATE server_instances SET lifecycle_state = ? WHERE server_instance_id = ?",
                    ("running", "srv-1"),
                )
                connection.commit()

            runtime = create_app_runtime(app_root=app_root)

            persisted_server = runtime.server_manager.get_server("srv-1")
            self.assertIsNotNone(persisted_server)
            assert persisted_server is not None
            self.assertEqual(
                persisted_server.lifecycle_state,
                ServerInstanceLifecycleState.STOPPED,
            )
