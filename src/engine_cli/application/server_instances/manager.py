from uuid import uuid4

from engine_cli.application.agent_runtimes.errors import (
    ServerInstanceHasAttachedRuntimesError,
)
from engine_cli.application.agent_runtimes.repository import AgentRuntimeRepository
from engine_cli.application.server_instances.catalog import InMemoryServerCatalog
from engine_cli.application.server_instances.errors import ServerInstanceNotFoundError
from engine_cli.application.server_instances.repository import ServerInstanceRepository
from engine_cli.application.session import SessionContext
from engine_cli.domain import ServerInstance
from engine_cli.infrastructure.minecraft.inspection import (
    MinecraftServerInspector,
    ServerInspectionResult,
)


class ServerInstanceManager:
    """Application service for creating, selecting, and removing servers."""

    def __init__(
        self,
        catalog: ServerInstanceRepository | None = None,
        runtime_catalog: AgentRuntimeRepository | None = None,
        inspector: MinecraftServerInspector | None = None,
    ) -> None:
        self.catalog = catalog or InMemoryServerCatalog()
        self.runtime_catalog = runtime_catalog
        self.inspector = inspector or MinecraftServerInspector()

    def list_servers(self) -> list[ServerInstance]:
        """Return the current session server list."""
        return self.catalog.list_servers()

    def get_server(self, server_instance_id: str) -> ServerInstance | None:
        """Return one server instance if it exists."""
        return self.catalog.get_server(server_instance_id)

    def inspect_server(self, location: str) -> ServerInspectionResult:
        """Inspect a candidate server location before import."""
        return self.inspector.inspect(location)

    def suggest_start_command(self, location: str) -> str | None:
        """Return a default start command suggestion for a valid server root."""
        return self.inspector.suggest_start_command(location)

    def import_server(self, name: str, location: str, command: str) -> ServerInstance:
        """Create and store a managed server from an inspected location."""
        server = self.inspector.import_server(
            server_instance_id=uuid4().hex,
            name=name,
            location=location,
            command=command,
        )
        return self.catalog.save_server(server)

    def add_server(self, name: str, location: str, command: str) -> ServerInstance:
        """Alias for import-style server creation."""
        return self.import_server(name=name, location=location, command=command)

    def remove_server(
        self,
        server_instance_id: str,
        session_context: SessionContext | None = None,
    ) -> ServerInstance:
        """Remove a server and clear session focus if it was active."""
        attached_runtimes = self._list_attached_runtime_ids(server_instance_id)
        if attached_runtimes:
            raise ServerInstanceHasAttachedRuntimesError(
                server_instance_id,
                attached_runtimes,
            )
        server = self.catalog.remove_server(server_instance_id)
        if server is None:
            raise ServerInstanceNotFoundError(server_instance_id)
        if (
            session_context is not None
            and session_context.active_server_instance_id == server_instance_id
        ):
            session_context.clear_server_selection()
        return server

    def select_server(
        self,
        server_instance_id: str,
        session_context: SessionContext,
    ) -> ServerInstance:
        """Select an existing server as the active session target."""
        server = self.get_server(server_instance_id)
        if server is None:
            raise ServerInstanceNotFoundError(server_instance_id)
        session_context.select_server(server.server_instance_id)
        return server

    def _list_attached_runtime_ids(self, server_instance_id: str) -> list[str]:
        if self.runtime_catalog is None:
            return []
        return [
            runtime.agent_runtime_id
            for runtime in self.runtime_catalog.list_runtimes_for_server(server_instance_id)
        ]
