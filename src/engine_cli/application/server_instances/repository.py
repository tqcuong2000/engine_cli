from typing import Protocol

from engine_cli.domain import ServerInstance


class ServerInstanceRepository(Protocol):
    """Application-facing persistence contract for server instances."""

    def list_servers(self) -> list[ServerInstance]:
        """Return all persisted server instances."""
        ...

    def get_server(self, server_instance_id: str) -> ServerInstance | None:
        """Return one persisted server instance if it exists."""
        ...

    def save_server(self, server: ServerInstance) -> ServerInstance:
        """Insert or replace a persisted server instance."""
        ...

    def remove_server(self, server_instance_id: str) -> ServerInstance | None:
        """Remove and return a persisted server instance if it exists."""
        ...
