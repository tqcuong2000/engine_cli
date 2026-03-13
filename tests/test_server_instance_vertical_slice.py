import sys
import tempfile
import unittest

from engine_cli.application import (
    ExecutionService,
    ServerInstanceLifecycleError,
    ServerInstanceLifecycleService,
)
from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState, TaskStatus
from engine_cli.infrastructure.process import LocalProcessManager


class TestServerInstanceVerticalSlice(unittest.TestCase):
    def setUp(self):
        self.execution_service = ExecutionService()
        self.process_manager = LocalProcessManager()
        self.lifecycle_service = ServerInstanceLifecycleService(
            execution_service=self.execution_service,
            process_manager=self.process_manager,
            observation_timeout=0.5,
            poll_interval=0.05,
        )

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
        command = f'"{sys.executable}" -c "import time; time.sleep(30)"'
        with tempfile.TemporaryDirectory() as temp_dir:
            server = self._build_server(temp_dir, command)

            task = self.lifecycle_service.start(server)

            self.assertEqual(server.lifecycle_state, ServerInstanceLifecycleState.RUNNING)
            self.assertEqual(task.task_kind, "server_instance.start")
            self.assertEqual(task.status, TaskStatus.COMPLETED)

            self.lifecycle_service.stop(server)

    def test_stop_running_server_transitions_to_stopped(self):
        command = f'"{sys.executable}" -c "import time; time.sleep(30)"'
        with tempfile.TemporaryDirectory() as temp_dir:
            server = self._build_server(temp_dir, command)

            self.lifecycle_service.start(server)
            task = self.lifecycle_service.stop(server)

            self.assertEqual(server.lifecycle_state, ServerInstanceLifecycleState.STOPPED)
            self.assertEqual(task.task_kind, "server_instance.stop")
            self.assertEqual(task.status, TaskStatus.COMPLETED)

    def test_start_failure_moves_server_to_failed(self):
        command = f'"{sys.executable}" -c "import sys; sys.exit(1)"'
        with tempfile.TemporaryDirectory() as temp_dir:
            server = self._build_server(temp_dir, command)

            task = self.lifecycle_service.start(server)

            self.assertEqual(server.lifecycle_state, ServerInstanceLifecycleState.FAILED)
            self.assertEqual(task.status, TaskStatus.FAILED)

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
