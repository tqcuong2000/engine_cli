import tempfile
from pathlib import Path
import unittest

from engine_cli.application import (
    InMemoryAgentRuntimeCatalog,
    ServerInstanceManager,
    ServerInstanceHasAttachedRuntimesError,
    ServerInstanceNotFoundError,
)
from engine_cli.domain import AgentRuntime, AgentRuntimeLifecycleState
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
