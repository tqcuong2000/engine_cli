import unittest

from engine_cli.domain import (
    AgentRuntime,
    AgentRuntimeLifecycleState,
    ServerInstance,
    ServerInstanceLifecycleState,
)
from engine_cli.infrastructure.agent_runtime import InMemoryAgentRuntimeSupervisor


class TestInMemoryAgentRuntimeSupervisor(unittest.TestCase):
    def test_activate_rejects_duplicate_runtime_id(self) -> None:
        supervisor = InMemoryAgentRuntimeSupervisor()
        runtime = AgentRuntime(
            agent_runtime_id="runtime-1",
            name="Ops Bot",
            agent_profile_id="profile-1",
            server_instance_id="srv-1",
            agent_kind="server_ops",
            lifecycle_state=AgentRuntimeLifecycleState.ATTACHED,
        )
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar fabric.jar --nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.RUNNING,
        )
        supervisor.activate(runtime, server)

        with self.assertRaises(RuntimeError):
            supervisor.activate(runtime, server)
