from dataclasses import dataclass

from engine_cli.application.session.errors import InvalidModeSwitchError
from engine_cli.domain import OperatingMode


@dataclass
class SessionContext:
    """Runtime-only application state for the current user session."""

    mode: OperatingMode = OperatingMode.BASE
    active_server_instance_id: str | None = None
    active_agent_profile_id: str | None = None

    def switch_mode(self, mode: OperatingMode) -> None:
        """Switch the current session mode after local-state validation."""
        if mode in (OperatingMode.SERVER, OperatingMode.DATAPACK):
            if self.active_server_instance_id is None:
                raise InvalidModeSwitchError(
                    f"{mode.value!r} mode requires an active server selection"
                )
        self.mode = mode

    def select_server(self, server_instance_id: str) -> None:
        """Select the active server target for the session."""
        self.active_server_instance_id = server_instance_id

    def clear_server_selection(self) -> None:
        """Clear the active server, falling back to base mode if required."""
        if self.mode in (OperatingMode.SERVER, OperatingMode.DATAPACK):
            self.mode = OperatingMode.BASE
        self.active_server_instance_id = None

    def set_agent_profile(self, agent_profile_id: str | None) -> None:
        """Set or clear the active agent profile reference."""
        self.active_agent_profile_id = agent_profile_id
