from dataclasses import dataclass

from engine_cli.application import ServerInstanceManager, SessionContext


@dataclass(frozen=True)
class PanelViewContext:
    """Shared context object passed into panel views."""

    session_context: SessionContext
    server_manager: ServerInstanceManager
