from dataclasses import replace
from uuid import uuid4

from engine_cli.application.agent_runtimes.catalog import InMemoryAgentRuntimeCatalog
from engine_cli.application.agent_runtimes.errors import (
    AgentRuntimeAttachedServerNotFoundError,
    AgentRuntimeAttachmentProjectionMismatchError,
    AgentRuntimeNotFoundError,
    InvalidAgentRuntimeProfileModeError,
)
from engine_cli.application.agent_runtimes.repository import AgentRuntimeRepository
from engine_cli.application.server_instances.repository import ServerInstanceRepository
from engine_cli.domain import (
    AgentProfile,
    AgentRuntime,
    AgentRuntimeLifecycleState,
    OperatingMode,
    ServerInstance,
)


VALID_RUNTIME_PROFILE_MODES = frozenset(
    {OperatingMode.SERVER, OperatingMode.DATAPACK}
)


class AgentRuntimeManager:
    """Application service for creating and removing managed agent runtimes."""

    def __init__(
        self,
        catalog: AgentRuntimeRepository | None = None,
        server_catalog: ServerInstanceRepository | None = None,
    ) -> None:
        self.catalog = catalog or InMemoryAgentRuntimeCatalog()
        self.server_catalog = server_catalog

    def create_runtime(
        self,
        *,
        name: str,
        agent_profile: AgentProfile,
        server: ServerInstance,
    ) -> AgentRuntime:
        """Create and store one attached runtime definition."""
        self._validate_profile_mode(agent_profile)
        self._assert_server_projection_matches(server.server_instance_id)

        runtime = AgentRuntime(
            agent_runtime_id=uuid4().hex,
            name=name,
            agent_profile_id=agent_profile.agent_profile_id,
            server_instance_id=server.server_instance_id,
            agent_kind=agent_profile.agent_kind,
            lifecycle_state=AgentRuntimeLifecycleState.ATTACHED,
        )
        saved_runtime = self.catalog.save_runtime(runtime)
        try:
            self._write_server_projection(server.server_instance_id)
        except Exception:
            self.catalog.remove_runtime(saved_runtime.agent_runtime_id)
            raise
        return saved_runtime

    def get_runtime(self, agent_runtime_id: str) -> AgentRuntime | None:
        """Return one runtime if it exists."""
        return self.catalog.get_runtime(agent_runtime_id)

    def list_runtimes(self) -> list[AgentRuntime]:
        """Return all known runtimes."""
        return self.catalog.list_runtimes()

    def list_runtimes_for_server(self, server_instance_id: str) -> list[AgentRuntime]:
        """Return all runtimes attached to one server."""
        return self.catalog.list_runtimes_for_server(server_instance_id)

    def remove_runtime(self, agent_runtime_id: str) -> AgentRuntime:
        """Remove one runtime and update any retained server projection."""
        runtime = self.catalog.get_runtime(agent_runtime_id)
        if runtime is None:
            raise AgentRuntimeNotFoundError(agent_runtime_id)

        self._assert_server_projection_matches(runtime.server_instance_id)
        removed_runtime = self.catalog.remove_runtime(agent_runtime_id)
        assert removed_runtime is not None
        try:
            self._write_server_projection(runtime.server_instance_id)
        except Exception:
            self.catalog.save_runtime(removed_runtime)
            raise
        return removed_runtime

    def _validate_profile_mode(self, agent_profile: AgentProfile) -> None:
        if agent_profile.mode not in VALID_RUNTIME_PROFILE_MODES:
            raise InvalidAgentRuntimeProfileModeError(
                agent_profile.agent_profile_id,
                agent_profile.mode,
            )

    def _assert_server_projection_matches(self, server_instance_id: str) -> None:
        if self.server_catalog is None:
            return
        server = self.server_catalog.get_server(server_instance_id)
        if server is None:
            raise AgentRuntimeAttachedServerNotFoundError(server_instance_id)
        if server.attached_agents != self._runtime_ids_for_server(server_instance_id):
            raise AgentRuntimeAttachmentProjectionMismatchError(server_instance_id)

    def _write_server_projection(self, server_instance_id: str) -> None:
        if self.server_catalog is None:
            return
        server = self.server_catalog.get_server(server_instance_id)
        if server is None:
            raise AgentRuntimeAttachedServerNotFoundError(server_instance_id)
        synced_server = replace(
            server,
            attached_agents=self._runtime_ids_for_server(server_instance_id),
        )
        self.server_catalog.save_server(synced_server)

    def _runtime_ids_for_server(self, server_instance_id: str) -> list[str]:
        return [
            runtime.agent_runtime_id
            for runtime in self.catalog.list_runtimes_for_server(server_instance_id)
        ]
