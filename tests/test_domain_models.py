import unittest
from datetime import datetime

from engine_cli.domain import (
    AgentProfile,
    AgentRuntime,
    AgentRuntimeLifecycleState,
    OperatingMode,
    ServerInstance,
    ServerInstanceLifecycleState,
    TaskRun,
    TaskStatus,
    TaskTargetType,
)


class TestDomainImportsAndEnums(unittest.TestCase):
    def test_enum_values(self):
        self.assertEqual(OperatingMode.BASE.value, "base")
        self.assertEqual(OperatingMode.SERVER.value, "server")
        self.assertEqual(OperatingMode.DATAPACK.value, "datapack")
        self.assertEqual(ServerInstanceLifecycleState.RUNNING.value, "running")
        self.assertEqual(AgentRuntimeLifecycleState.ACTIVE.value, "active")
        self.assertEqual(TaskStatus.CANCELLED.value, "cancelled")
        self.assertEqual(TaskTargetType.AGENT_RUNTIME.value, "agent_runtime")

    def test_server_instance_dataclass(self):
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="D:/servers/lobby",
            command="java -jar fabric.jar --nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )
        self.assertEqual(server.server_instance_id, "srv-1")
        self.assertEqual(server.attached_agents, [])

    def test_agent_profile_dataclass(self):
        profile = AgentProfile(
            agent_profile_id="profile-1",
            name="Default Datapack Agent",
            mode=OperatingMode.DATAPACK,
            agent_kind="datapack_dev",
        )
        self.assertEqual(profile.mode, OperatingMode.DATAPACK)
        self.assertEqual(profile.agent_kind, "datapack_dev")

    def test_agent_runtime_dataclass(self):
        runtime = AgentRuntime(
            agent_runtime_id="runtime-1",
            name="Lobby Agent",
            agent_profile_id="profile-1",
            server_instance_id="srv-1",
            agent_kind="server_ops",
            lifecycle_state=AgentRuntimeLifecycleState.ATTACHED,
        )
        self.assertEqual(runtime.agent_profile_id, "profile-1")
        self.assertEqual(runtime.lifecycle_state, AgentRuntimeLifecycleState.ATTACHED)

    def test_task_run_dataclass(self):
        started_at = datetime.now()
        task = TaskRun(
            task_run_id="task-1",
            task_kind="server_instance.start",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id="srv-1",
            status=TaskStatus.RUNNING,
            started_at=started_at,
        )
        self.assertEqual(task.task_kind, "server_instance.start")
        self.assertEqual(task.started_at, started_at)
        self.assertIsNone(task.finished_at)
