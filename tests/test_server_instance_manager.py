import tempfile
from pathlib import Path
import unittest

from engine_cli.application import (
    InMemoryAgentRuntimeCatalog,
    ServerInspectionError,
    ServerInstanceManager,
    ServerInstanceHasAttachedRuntimesError,
    ServerInstanceNotFoundError,
)
from engine_cli.domain import (
    AgentRuntime,
    AgentRuntimeLifecycleState,
    ServerInstance,
    ServerInstanceLifecycleState,
)
from engine_cli.infrastructure.persistence import SqliteServerInstanceRepository


class TestServerInstanceManager(unittest.TestCase):
    def _write_server_files(self, root: Path) -> None:
        (root / "logs").mkdir()
        (root / "versions" / "1.21.11").mkdir(parents=True)
        (root / "server.properties").write_text("motd=Lobby\n", encoding="utf-8")
        (root / "logs" / "latest.log").write_text(
            "[22:37:58] [main/INFO]: Loading Minecraft 1.21.11 with Fabric Loader 0.18.4\n",
            encoding="utf-8",
        )
        (root / "versions" / "1.21.11" / "server-1.21.11.jar").write_text(
            "",
            encoding="utf-8",
        )

    def test_import_server_adds_it_to_session_catalog(self):
        manager = ServerInstanceManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_server_files(root)

            server = manager.import_server(
                name="Lobby",
                location=str(root),
                command="java -jar fabric.jar --nogui",
            )

            self.assertEqual(server.name, "Lobby")
            self.assertEqual(len(manager.list_servers()), 1)
            self.assertIs(manager.get_server(server.server_instance_id), server)

    def test_inspect_server_raises_application_error(self):
        manager = ServerInstanceManager()

        with self.assertRaises(ServerInspectionError):
            manager.inspect_server("X:/missing-server-root")

    def test_require_server_returns_existing_server(self):
        manager = ServerInstanceManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_server_files(root)
            server = manager.import_server(
                name="Lobby",
                location=str(root),
                command="java -jar fabric.jar --nogui",
            )

            selected = manager.require_server(server.server_instance_id)

            self.assertEqual(selected.server_instance_id, server.server_instance_id)

    def test_select_missing_server_raises(self):
        manager = ServerInstanceManager()

        with self.assertRaises(ServerInstanceNotFoundError):
            manager.require_server("missing")

    def test_remove_server_uses_server_projection_when_runtime_catalog_is_unset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            server_catalog = SqliteServerInstanceRepository(Path(temp_dir) / "engine.db")
            manager = ServerInstanceManager(catalog=server_catalog)
            server = ServerInstance(
                server_instance_id="srv-1",
                name="Lobby",
                location="X:/servers/lobby",
                command="java -jar fabric.jar --nogui",
                minecraft_version="1.21.11",
                server_distribution="fabric",
                lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
                attached_agents=["runtime-1"],
            )
            server_catalog.save_server(server)

            with self.assertRaises(ServerInstanceHasAttachedRuntimesError):
                manager.remove_server(server.server_instance_id)

    def test_remove_server_prefers_runtime_catalog_over_stale_server_projection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            server_catalog = SqliteServerInstanceRepository(Path(temp_dir) / "engine.db")
            runtime_catalog = InMemoryAgentRuntimeCatalog()
            manager = ServerInstanceManager(
                catalog=server_catalog,
                runtime_catalog=runtime_catalog,
            )
            server = ServerInstance(
                server_instance_id="srv-1",
                name="Lobby",
                location="X:/servers/lobby",
                command="java -jar fabric.jar --nogui",
                minecraft_version="1.21.11",
                server_distribution="fabric",
                lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
                attached_agents=["stale-runtime"],
            )
            server_catalog.save_server(server)

            removed_server = manager.remove_server(server.server_instance_id)

            self.assertEqual(removed_server.server_instance_id, server.server_instance_id)
            self.assertIsNone(server_catalog.get_server(server.server_instance_id))

    def test_manager_works_with_sqlite_repository_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = SqliteServerInstanceRepository(Path(temp_dir) / "engine.db")
            manager = ServerInstanceManager(catalog=repository)
            root = Path(temp_dir) / "server"
            root.mkdir()
            self._write_server_files(root)

            server = manager.import_server(
                name="Lobby",
                location=str(root),
                command="java -jar fabric.jar --nogui",
            )

            loaded = manager.get_server(server.server_instance_id)

            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.name, "Lobby")
            self.assertEqual(len(manager.list_servers()), 1)
            removed = manager.remove_server(server.server_instance_id)
            self.assertEqual(removed.server_instance_id, server.server_instance_id)
            self.assertEqual(manager.list_servers(), [])

    def test_remove_server_rejects_when_runtime_repository_reports_attached_runtimes(self):
        runtime_catalog = InMemoryAgentRuntimeCatalog()
        manager = ServerInstanceManager(runtime_catalog=runtime_catalog)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_server_files(root)
            server = manager.import_server(
                name="Lobby",
                location=str(root),
                command="java -jar fabric.jar --nogui",
            )
            runtime_catalog.save_runtime(
                AgentRuntime(
                    agent_runtime_id="runtime-1",
                    name="Ops Bot",
                    agent_profile_id="profile-1",
                    server_instance_id=server.server_instance_id,
                    agent_kind="server_ops",
                    lifecycle_state=AgentRuntimeLifecycleState.ATTACHED,
                )
            )

            with self.assertRaises(ServerInstanceHasAttachedRuntimesError):
                manager.remove_server(server.server_instance_id)
