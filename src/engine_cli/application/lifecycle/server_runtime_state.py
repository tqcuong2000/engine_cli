from copy import deepcopy

from engine_cli.application.lifecycle.server_instance import (
    ServerInstanceLifecycleService,
)
from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState


class ServerRuntimeStateResolver:
    """Resolve the effective runtime state for a server without persisting it."""

    def __init__(self, lifecycle_service: ServerInstanceLifecycleService) -> None:
        self.lifecycle_service = lifecycle_service

    def overlay(self, server: ServerInstance) -> ServerInstance:
        """Return a copied server instance with the effective lifecycle state."""
        overlaid_server = deepcopy(server)
        if self.lifecycle_service.get_handle(server.server_instance_id) is not None:
            overlaid_server.lifecycle_state = ServerInstanceLifecycleState.RUNNING
        return overlaid_server
