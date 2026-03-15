from dataclasses import dataclass

from engine_cli.application import (
    ServerInstanceManager,
    SessionContext,
)
from engine_cli.application.lifecycle import ServerRuntimeStateResolver


@dataclass(frozen=True)
class PanelViewContext:
    """Shared context object passed into panel views."""

    session_context: SessionContext
    server_manager: ServerInstanceManager
    server_runtime_state_resolver: ServerRuntimeStateResolver | None = None
