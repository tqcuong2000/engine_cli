from contextlib import closing
import sqlite3
import tempfile
from pathlib import Path
import unittest

from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState
from engine_cli.infrastructure.persistence import (
    ServerInstanceStorageError,
    SqliteServerInstanceRepository,
)


class TestSqliteServerInstanceRepository(unittest.TestCase):
    def create_repository(self, database_path: Path) -> SqliteServerInstanceRepository:
        return SqliteServerInstanceRepository(database_path)

    def create_server(
        self,
        *,
        server_instance_id: str = "srv-1",
        lifecycle_state: ServerInstanceLifecycleState = ServerInstanceLifecycleState.CONFIGURED,
        attached_agents: list[str] | None = None,
    ) -> ServerInstance:
        return ServerInstance(
            server_instance_id=server_instance_id,
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar fabric.jar --nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=lifecycle_state,
            attached_agents=attached_agents or [],
        )

    def test_sqlite_repository_bootstraps_missing_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "db" / "engine.db"

            self.create_repository(database_path)

            self.assertTrue(database_path.is_file())

    def test_sqlite_repository_persists_server_instances_across_instances(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "engine.db"
            repository = self.create_repository(database_path)
            server = self.create_server(attached_agents=["agent-1"])
            repository.save_server(server)

            reloaded_repository = self.create_repository(database_path)
            loaded_server = reloaded_repository.get_server(server.server_instance_id)

            self.assertIsNotNone(loaded_server)
            assert loaded_server is not None
            self.assertEqual(loaded_server.name, "Lobby")
            self.assertEqual(loaded_server.attached_agents, ["agent-1"])

    def test_sqlite_repository_rejects_transient_runtime_state_on_save(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = self.create_repository(Path(temp_dir) / "engine.db")
            server = self.create_server(
                lifecycle_state=ServerInstanceLifecycleState.RUNNING,
            )

            with self.assertRaises(ServerInstanceStorageError):
                repository.save_server(server)

    def test_sqlite_repository_rejects_unknown_lifecycle_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "engine.db"
            repository = self.create_repository(database_path)
            repository.save_server(self.create_server())
            with closing(sqlite3.connect(database_path)) as connection:
                connection.execute(
                    "UPDATE server_instances SET lifecycle_state = ? WHERE server_instance_id = ?",
                    ("starting", "srv-1"),
                )
                connection.commit()

            with self.assertRaises(ServerInstanceStorageError):
                repository.get_server("srv-1")

    def test_sqlite_repository_round_trips_empty_attached_agents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = self.create_repository(Path(temp_dir) / "engine.db")
            server = self.create_server(attached_agents=[])
            repository.save_server(server)

            loaded_server = repository.get_server(server.server_instance_id)

            self.assertIsNotNone(loaded_server)
            assert loaded_server is not None
            self.assertEqual(loaded_server.attached_agents, [])

    def test_repository_remove_missing_server_is_stable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = self.create_repository(Path(temp_dir) / "engine.db")

            self.assertIsNone(repository.remove_server("missing"))

    def test_reconcile_transient_states_normalizes_runtime_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "engine.db"
            repository = self.create_repository(database_path)
            repository.save_server(self.create_server())
            with closing(sqlite3.connect(database_path)) as connection:
                connection.execute(
                    "UPDATE server_instances SET lifecycle_state = ? WHERE server_instance_id = ?",
                    ("running", "srv-1"),
                )
                connection.commit()

            updated_count = repository.reconcile_transient_states()
            loaded_server = repository.get_server("srv-1")

            self.assertEqual(updated_count, 1)
            self.assertIsNotNone(loaded_server)
            assert loaded_server is not None
            self.assertEqual(
                loaded_server.lifecycle_state,
                ServerInstanceLifecycleState.STOPPED,
            )
