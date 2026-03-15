from dataclasses import dataclass, field

from engine_cli.domain import ServerInstance


@dataclass
class InMemoryServerCatalog:
    """In-memory implementation of the server-instance repository contract."""

    _servers: dict[str, ServerInstance] = field(default_factory=dict)

    def list_servers(self) -> list[ServerInstance]:
        """Return all known servers in insertion order."""
        return list(self._servers.values())

    def get_server(self, server_instance_id: str) -> ServerInstance | None:
        """Return one server by identifier if it exists."""
        return self._servers.get(server_instance_id)

    def save_server(self, server: ServerInstance) -> ServerInstance:
        """Insert or replace a server in the catalog."""
        self._servers[server.server_instance_id] = server
        return server

    def remove_server(self, server_instance_id: str) -> ServerInstance | None:
        """Remove and return a server if it exists."""
        return self._servers.pop(server_instance_id, None)
