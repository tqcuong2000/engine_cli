import tempfile
from pathlib import Path
import unittest

from engine_cli.application import (
    AgentRuntimeLifecycleError,
    AgentRuntimeLifecycleService,
    AgentRuntimeValidationError,
    ExecutionService,
)
from engine_cli.domain import (
    AgentRuntime,
    AgentRuntimeLifecycleState,
    ServerInstance,
    ServerInstanceLifecycleState,
    TaskStatus,
    TaskTargetType,
)
from engine_cli.infrastructure.agent_runtime import InMemoryAgentRuntimeSupervisor
from engine_cli.infrastructure.persistence import SqliteAgentRuntimeRepository
from engine_cli.infrastructure.persistence.sqlite import SqliteTaskRunRepository


class FailingAgentRuntimeSupervisor(InMemoryAgentRuntimeSupervisor):
    def activate(self, runtime: AgentRuntime, server: ServerInstance):
        raise RuntimeError("boom")


class TestAgentRuntimeLifecycleService(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self._temp_dir.name) / "engine.db"
        self.runtime_repository = SqliteAgentRuntimeRepository(database_path)
        self.task_repository = SqliteTaskRunRepository(database_path)
        self.execution_service = ExecutionService(task_repository=self.task_repository)
        self.supervisor = InMemoryAgentRuntimeSupervisor()
        self.lifecycle_service = AgentRuntimeLifecycleService(
            execution_service=self.execution_service,
            runtime_catalog=self.runtime_repository,
            supervisor=self.supervisor,
        )

    def tearDown(self) -> None:
        self._temp_dir.cleanup()

    def create_runtime(
        self,
        *,
        agent_runtime_id: str = "runtime-1",
        server_instance_id: str = "srv-1",
        lifecycle_state: AgentRuntimeLifecycleState = AgentRuntimeLifecycleState.ATTACHED,
    ) -> AgentRuntime:
        return AgentRuntime(
            agent_runtime_id=agent_runtime_id,
            name="Ops Bot",
            agent_profile_id="profile-1",
            server_instance_id=server_instance_id,
            agent_kind="server_ops",
            lifecycle_state=lifecycle_state,
        )

    def create_server(
        self,
        *,
        server_instance_id: str = "srv-1",
        lifecycle_state: ServerInstanceLifecycleState = ServerInstanceLifecycleState.RUNNING,
    ) -> ServerInstance:
        return ServerInstance(
            server_instance_id=server_instance_id,
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar fabric.jar --nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=lifecycle_state,
        )

    def test_validate_transitions_draft_runtime_to_attached(self):
        runtime = self.create_runtime(lifecycle_state=AgentRuntimeLifecycleState.DRAFT)
        server = self.create_server()

        validated_runtime = self.lifecycle_service.validate(runtime, server)

        self.assertEqual(
            validated_runtime.lifecycle_state,
            AgentRuntimeLifecycleState.ATTACHED,
        )
        persisted_runtime = self.runtime_repository.get_runtime(runtime.agent_runtime_id)
        self.assertIsNotNone(persisted_runtime)
        assert persisted_runtime is not None
        self.assertEqual(
            persisted_runtime.lifecycle_state,
            AgentRuntimeLifecycleState.ATTACHED,
        )

    def test_validate_rejects_mismatched_server(self):
        runtime = self.create_runtime(
            server_instance_id="srv-1",
            lifecycle_state=AgentRuntimeLifecycleState.DRAFT,
        )
        self.runtime_repository.save_runtime(runtime)
        server = self.create_server(server_instance_id="srv-2")

        with self.assertRaises(AgentRuntimeValidationError):
            self.lifecycle_service.validate(runtime, server)

        persisted_runtime = self.runtime_repository.get_runtime(runtime.agent_runtime_id)
        self.assertIsNotNone(persisted_runtime)
        assert persisted_runtime is not None
        self.assertEqual(
            persisted_runtime.lifecycle_state,
            AgentRuntimeLifecycleState.DRAFT,
        )

    def test_start_persists_start_task_and_transitions_to_active(self):
        runtime = self.create_runtime()
        self.runtime_repository.save_runtime(runtime)
        server = self.create_server()

        task = self.lifecycle_service.start(runtime, server)

        self.assertEqual(task.task_kind, "agent_runtime.start")
        self.assertEqual(task.target_type, TaskTargetType.AGENT_RUNTIME)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(self.lifecycle_service.get_handle(runtime.agent_runtime_id))
        persisted_runtime = self.runtime_repository.get_runtime(runtime.agent_runtime_id)
        self.assertIsNotNone(persisted_runtime)
        assert persisted_runtime is not None
        self.assertEqual(
            persisted_runtime.lifecycle_state,
            AgentRuntimeLifecycleState.ACTIVE,
        )

    def test_stop_persists_stop_task_and_transitions_to_stopped(self):
        runtime = self.create_runtime()
        self.runtime_repository.save_runtime(runtime)
        server = self.create_server()
        self.lifecycle_service.start(runtime, server)

        task = self.lifecycle_service.stop(runtime)

        self.assertEqual(task.task_kind, "agent_runtime.stop")
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNone(self.lifecycle_service.get_handle(runtime.agent_runtime_id))
        persisted_tasks = self.execution_service.list_tasks_for_target(
            TaskTargetType.AGENT_RUNTIME,
            runtime.agent_runtime_id,
        )
        self.assertEqual(
            [persisted_task.task_kind for persisted_task in persisted_tasks],
            ["agent_runtime.start", "agent_runtime.stop"],
        )
        persisted_runtime = self.runtime_repository.get_runtime(runtime.agent_runtime_id)
        self.assertIsNotNone(persisted_runtime)
        assert persisted_runtime is not None
        self.assertEqual(
            persisted_runtime.lifecycle_state,
            AgentRuntimeLifecycleState.STOPPED,
        )

    def test_start_rejects_when_server_not_running(self):
        runtime = self.create_runtime()
        self.runtime_repository.save_runtime(runtime)
        server = self.create_server(
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )

        with self.assertRaises(AgentRuntimeLifecycleError):
            self.lifecycle_service.start(runtime, server)

        self.assertEqual(
            self.execution_service.list_tasks_for_target(
                TaskTargetType.AGENT_RUNTIME,
                runtime.agent_runtime_id,
            ),
            [],
        )

    def test_start_rejects_from_draft(self):
        runtime = self.create_runtime(lifecycle_state=AgentRuntimeLifecycleState.DRAFT)
        self.runtime_repository.save_runtime(runtime)
        server = self.create_server()

        with self.assertRaises(AgentRuntimeLifecycleError):
            self.lifecycle_service.start(runtime, server)

        self.assertEqual(
            self.execution_service.list_tasks_for_target(
                TaskTargetType.AGENT_RUNTIME,
                runtime.agent_runtime_id,
            ),
            [],
        )

    def test_start_failure_moves_runtime_to_failed(self):
        runtime = self.create_runtime()
        self.runtime_repository.save_runtime(runtime)
        server = self.create_server()
        lifecycle_service = AgentRuntimeLifecycleService(
            execution_service=self.execution_service,
            runtime_catalog=self.runtime_repository,
            supervisor=FailingAgentRuntimeSupervisor(),
        )

        task = lifecycle_service.start(runtime, server)

        self.assertEqual(task.status, TaskStatus.FAILED)
        persisted_runtime = self.runtime_repository.get_runtime(runtime.agent_runtime_id)
        self.assertIsNotNone(persisted_runtime)
        assert persisted_runtime is not None
        self.assertEqual(
            persisted_runtime.lifecycle_state,
            AgentRuntimeLifecycleState.FAILED,
        )

    def test_stop_rejects_without_handle(self):
        runtime = self.create_runtime(lifecycle_state=AgentRuntimeLifecycleState.ACTIVE)
        self.runtime_repository.save_runtime(runtime)

        with self.assertRaises(AgentRuntimeLifecycleError):
            self.lifecycle_service.stop(runtime)

        self.assertEqual(
            self.execution_service.list_tasks_for_target(
                TaskTargetType.AGENT_RUNTIME,
                runtime.agent_runtime_id,
            ),
            [],
        )
