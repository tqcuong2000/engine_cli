from engine_cli.application.lifecycle import (
    ServerInstanceLifecycleService,
)
from engine_cli.application.server_commands.errors import ServerCommandError
from engine_cli.application.terminal import ServerTerminalStore
from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState
from engine_cli.infrastructure.process import ProcessCommandError


class ServerCommandService:
    """Application service for sending commands to a running managed server."""

    def __init__(
        self,
        lifecycle_service: ServerInstanceLifecycleService,
        terminal_store: ServerTerminalStore,
    ) -> None:
        self.lifecycle_service = lifecycle_service
        self.terminal_store = terminal_store

    def send(self, server: ServerInstance, command: str) -> None:
        """Validate and send one command to the server stdin."""
        normalized_command = command.strip()
        if not normalized_command:
            raise ServerCommandError("Server command is required.")
        if server.lifecycle_state is not ServerInstanceLifecycleState.RUNNING:
            raise ServerCommandError("Server must be running before commands can be sent.")
        handle = self.lifecycle_service.get_handle(server.server_instance_id)
        if handle is None:
            raise ServerCommandError("No active process handle is available for this server.")

        terminal_buffer = self.terminal_store.get_buffer(server.server_instance_id)
        terminal_buffer.append(f"> {normalized_command}")
        try:
            self.lifecycle_service.process_manager.send_command(handle, normalized_command)
        except ProcessCommandError as exc:
            raise ServerCommandError(str(exc)) from exc
