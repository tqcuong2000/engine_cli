from dataclasses import dataclass

from engine_cli.application.session.context import SessionContext
from engine_cli.domain import OperatingMode


@dataclass(frozen=True)
class SessionSnapshot:
    """Immutable view of session state passed to listeners."""

    mode: OperatingMode
    active_server_instance_id: str | None
    active_agent_profile_id: str | None

    @classmethod
    def from_context(cls, context: SessionContext) -> "SessionSnapshot":
        """Build a snapshot from the current mutable session context."""
        return cls(
            mode=context.mode,
            active_server_instance_id=context.active_server_instance_id,
            active_agent_profile_id=context.active_agent_profile_id,
        )
