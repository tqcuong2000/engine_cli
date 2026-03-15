import unittest

from engine_cli.application import (
    AgentRuntimeAttachmentProjectionMismatchError,
    AgentRuntimeManager,
    InMemoryServerCatalog,
    InvalidAgentRuntimeProfileModeError,
)
from engine_cli.domain import (
    AgentProfile,
    AgentRuntimeLifecycleState,
    OperatingMode,
    ServerInstance,
    ServerInstanceLifecycleState,
)


class TestAgentRuntimeManager(unittest.TestCase):
    def create_profile(
        self,
        *,
        agent_profile_id: str = "profile-1",
        mode: OperatingMode = OperatingMode.SERVER,
    ) -> AgentProfile:
        return AgentProfile(
            agent_profile_id=agent_profile_id,
            name="Ops Profile",
            mode=mode,
            agent_kind="server_ops",
        )

    def create_server(
        self,
        *,
        server_instance_id: str = "srv-1",
        attached_agents: list[str] | None = None,
    ) -> ServerInstance:
        return ServerInstance(
            server_instance_id=server_instance_id,
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar fabric.jar --nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
            attached_agents=attached_agents or [],
        )

    def test_create_runtime_persists_attachment_and_updates_server_projection(self):
        server_catalog = InMemoryServerCatalog()
        server = self.create_server()
        server_catalog.save_server(server)
        manager = AgentRuntimeManager(server_catalog=server_catalog)

        runtime = manager.create_runtime(
            name="Ops Bot",
            agent_profile=self.create_profile(),
            server=server,
        )

        self.assertEqual(runtime.name, "Ops Bot")
        self.assertEqual(runtime.lifecycle_state, AgentRuntimeLifecycleState.ATTACHED)
        self.assertEqual(manager.list_runtimes(), [runtime])
        synced_server = server_catalog.get_server(server.server_instance_id)
        self.assertIsNotNone(synced_server)
        assert synced_server is not None
        self.assertEqual(synced_server.attached_agents, [runtime.agent_runtime_id])

    def test_remove_runtime_detaches_runtime_and_updates_server_projection(self):
        server_catalog = InMemoryServerCatalog()
        server = self.create_server()
        server_catalog.save_server(server)
        manager = AgentRuntimeManager(server_catalog=server_catalog)
        runtime = manager.create_runtime(
            name="Ops Bot",
            agent_profile=self.create_profile(),
            server=server,
        )

        removed_runtime = manager.remove_runtime(runtime.agent_runtime_id)

        self.assertEqual(removed_runtime.agent_runtime_id, runtime.agent_runtime_id)
        self.assertEqual(manager.list_runtimes(), [])
        synced_server = server_catalog.get_server(server.server_instance_id)
        self.assertIsNotNone(synced_server)
        assert synced_server is not None
        self.assertEqual(synced_server.attached_agents, [])

    def test_create_runtime_rejects_base_mode_profile(self):
        server_catalog = InMemoryServerCatalog()
        server = self.create_server()
        server_catalog.save_server(server)
        manager = AgentRuntimeManager(server_catalog=server_catalog)

        with self.assertRaises(InvalidAgentRuntimeProfileModeError):
            manager.create_runtime(
                name="Base Bot",
                agent_profile=self.create_profile(mode=OperatingMode.BASE),
                server=server,
            )

    def test_create_runtime_rejects_projection_mismatch(self):
        server_catalog = InMemoryServerCatalog()
        server = self.create_server(attached_agents=["stale-runtime"])
        server_catalog.save_server(server)
        manager = AgentRuntimeManager(server_catalog=server_catalog)

        with self.assertRaises(AgentRuntimeAttachmentProjectionMismatchError):
            manager.create_runtime(
                name="Ops Bot",
                agent_profile=self.create_profile(),
                server=server,
            )
