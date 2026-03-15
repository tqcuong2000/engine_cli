import sys
import tempfile
from pathlib import Path
import unittest

from engine_cli.application import (
    ExecutionService,
    ServerTerminalStore,
    ServerInstanceLifecycleError,
    ServerInstanceLifecycleService,
)
from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState, TaskStatus
from engine_cli.infrastructure.persistence import SqliteServerInstanceRepository
from engine_cli.infrastructure.process import LocalProcessManager
from engine_cli.infrastructure.persistence.sqlite import SqliteTaskRunRepository


class TestServerInstanceVerticalSlice(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self._temp_dir.name) / "engine.db"
        self.task_repository = SqliteTaskRunRepository(self.database_path)
        self.server_repository = SqliteServerInstanceRepository(self.database_path)
        self.execution_service = ExecutionService(task_repository=self.task_repository)
        self.process_manager = LocalProcessManager()
        self.terminal_store = ServerTerminalStore()
        self.lifecycle_service = ServerInstanceLifecycleService(
            execution_service=self.execution_service,
            process_manager=self.process_manager,
            server_catalog=self.server_repository,
            terminal_store=self.terminal_store,
            observation_timeout=0.5,
            poll_interval=0.05,
        )

    def tearDown(self):
        self._temp_dir.cleanup()

    def _build_server(self, temp_dir: str, command: str) -> ServerInstance:
        return ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location=temp_dir,
            command=command,
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )

    def test_start_configured_server_transitions_to_running(self):
        command = (
            f'"{sys.executable}" -u -c "import time; print(\'server booted\'); time.sleep(30)"'
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            server = self._build_server(temp_dir, command)
            self.server_repository.save_server(server)
            try:
                task = self.lifecycle_service.start(server)

                self.assertEqual(server.lifecycle_state, ServerInstanceLifecycleState.RUNNING)
                self.assertEqual(task.task_kind, "server_instance.start")
                self.assertEqual(task.status, TaskStatus.COMPLETED)
                persisted_tasks = self.execution_service.list_tasks_for_target(
                    task.target_type,
                    task.target_id,
                )
                self.assertEqual(len(persisted_tasks), 1)
                self.assertEqual(persisted_tasks[0].task_run_id, task.task_run_id)
                self.assertEqual(persisted_tasks[0].status, TaskStatus.COMPLETED)
                self.assertEqual(
                    [line.raw for line in self.terminal_store.get_buffer("srv-1").snapshot()],
                    ["server booted"],
                )
                persisted_server = self.server_repository.get_server("srv-1")
                self.assertIsNotNone(persisted_server)
                assert persisted_server is not None
                self.assertEqual(
                    persisted_server.lifecycle_state,
                    ServerInstanceLifecycleState.CONFIGURED,
                )
            finally:
                if server.lifecycle_state is ServerInstanceLifecycleState.RUNNING:
                    self.lifecycle_service.stop(server)

    def test_stop_running_server_transitions_to_stopped(self):
        command = f'"{sys.executable}" -c "import time; time.sleep(30)"'
        with tempfile.TemporaryDirectory() as temp_dir:
            server = self._build_server(temp_dir, command)
            self.server_repository.save_server(server)

            self.lifecycle_service.start(server)
            task = self.lifecycle_service.stop(server)

            self.assertEqual(server.lifecycle_state, ServerInstanceLifecycleState.STOPPED)
            self.assertEqual(task.task_kind, "server_instance.stop")
            self.assertEqual(task.status, TaskStatus.COMPLETED)
            persisted_tasks = self.execution_service.list_tasks_for_target(
                task.target_type,
                task.target_id,
            )
            self.assertEqual(
                [persisted_task.task_kind for persisted_task in persisted_tasks],
                ["server_instance.start", "server_instance.stop"],
            )
            self.assertEqual(
                [persisted_task.status for persisted_task in persisted_tasks],
                [TaskStatus.COMPLETED, TaskStatus.COMPLETED],
            )
            persisted_server = self.server_repository.get_server("srv-1")
            self.assertIsNotNone(persisted_server)
            assert persisted_server is not None
            self.assertEqual(
                persisted_server.lifecycle_state,
                ServerInstanceLifecycleState.STOPPED,
            )

    def test_start_failure_moves_server_to_failed(self):
        command = f'"{sys.executable}" -c "import sys; sys.exit(1)"'
        with tempfile.TemporaryDirectory() as temp_dir:
            server = self._build_server(temp_dir, command)
            self.server_repository.save_server(server)

            task = self.lifecycle_service.start(server)

            self.assertEqual(server.lifecycle_state, ServerInstanceLifecycleState.FAILED)
            self.assertEqual(task.status, TaskStatus.FAILED)
            persisted_tasks = self.execution_service.list_tasks_for_target(
                task.target_type,
                task.target_id,
            )
            self.assertEqual(len(persisted_tasks), 1)
            self.assertEqual(persisted_tasks[0].status, TaskStatus.FAILED)
            persisted_server = self.server_repository.get_server("srv-1")
            self.assertIsNotNone(persisted_server)
            assert persisted_server is not None
            self.assertEqual(
                persisted_server.lifecycle_state,
                ServerInstanceLifecycleState.FAILED,
            )

    def test_invalid_start_and_stop_requests_are_rejected(self):
        command = f'"{sys.executable}" -c "import time; time.sleep(30)"'
        with tempfile.TemporaryDirectory() as temp_dir:
            server = self._build_server(temp_dir, command)
            server.lifecycle_state = ServerInstanceLifecycleState.RUNNING

            with self.assertRaises(ServerInstanceLifecycleError):
                self.lifecycle_service.start(server)

            server.lifecycle_state = ServerInstanceLifecycleState.CONFIGURED
            with self.assertRaises(ServerInstanceLifecycleError):
                self.lifecycle_service.stop(server)
