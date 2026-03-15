from contextlib import closing
import sqlite3
import tempfile
from pathlib import Path
import unittest

from engine_cli.domain import AgentRuntime, AgentRuntimeLifecycleState
from engine_cli.infrastructure.persistence import (
    AgentRuntimeStorageError,
    SqliteAgentRuntimeRepository,
)


class TestSqliteAgentRuntimeRepository(unittest.TestCase):
    def create_repository(self, database_path: Path) -> SqliteAgentRuntimeRepository:
        return SqliteAgentRuntimeRepository(database_path)

    def create_runtime(
        self,
        *,
        agent_runtime_id: str = "runtime-1",
        server_instance_id: str = "srv-1",
        lifecycle_state: AgentRuntimeLifecycleState = AgentRuntimeLifecycleState.ATTACHED,
        name: str = "Ops Bot",
    ) -> AgentRuntime:
        return AgentRuntime(
            agent_runtime_id=agent_runtime_id,
            name=name,
            agent_profile_id="profile-1",
            server_instance_id=server_instance_id,
            agent_kind="server_ops",
            lifecycle_state=lifecycle_state,
        )

    def test_sqlite_repository_bootstraps_missing_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "db" / "engine.db"

            self.create_repository(database_path)

            self.assertTrue(database_path.is_file())

    def test_sqlite_repository_persists_and_lists_runtimes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "engine.db"
            repository = self.create_repository(database_path)
            runtime = self.create_runtime()
            other_runtime = self.create_runtime(
                agent_runtime_id="runtime-2",
                server_instance_id="srv-2",
                name="Data Bot",
            )
            repository.save_runtime(runtime)
            repository.save_runtime(other_runtime)

            reloaded_repository = self.create_repository(database_path)

            loaded_runtime = reloaded_repository.get_runtime(runtime.agent_runtime_id)
            self.assertIsNotNone(loaded_runtime)
            assert loaded_runtime is not None
            self.assertEqual(loaded_runtime.name, runtime.name)
            self.assertEqual(
                reloaded_repository.list_runtimes_for_server("srv-1"),
                [runtime],
            )
            self.assertEqual(reloaded_repository.list_runtimes(), [runtime, other_runtime])

    def test_sqlite_repository_rejects_blank_identifier_fields_on_save(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = self.create_repository(Path(temp_dir) / "engine.db")
            runtime = self.create_runtime(agent_runtime_id="  ")

            with self.assertRaises(AgentRuntimeStorageError):
                repository.save_runtime(runtime)

    def test_sqlite_repository_rejects_unknown_lifecycle_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "engine.db"
            repository = self.create_repository(database_path)
            repository.save_runtime(self.create_runtime())
            with closing(sqlite3.connect(database_path)) as connection:
                connection.execute(
                    "UPDATE agent_runtimes SET lifecycle_state = ? WHERE agent_runtime_id = ?",
                    ("unknown", "runtime-1"),
                )
                connection.commit()

            with self.assertRaises(AgentRuntimeStorageError):
                repository.get_runtime("runtime-1")

    def test_repository_remove_missing_runtime_is_stable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = self.create_repository(Path(temp_dir) / "engine.db")

            self.assertIsNone(repository.remove_runtime("missing"))

    def test_repository_remove_runtime_returns_deleted_runtime(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = self.create_repository(Path(temp_dir) / "engine.db")
            runtime = self.create_runtime()
            repository.save_runtime(runtime)

            removed_runtime = repository.remove_runtime(runtime.agent_runtime_id)

            self.assertEqual(removed_runtime, runtime)
            self.assertIsNone(repository.get_runtime(runtime.agent_runtime_id))
