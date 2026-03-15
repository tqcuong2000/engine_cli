from dataclasses import dataclass

from engine_cli.application import (
    ServerInstanceLifecycleService,
    ServerInstanceManager,
    SessionContext,
)


@dataclass(frozen=True)
class PanelViewContext:
    """Shared context object passed into panel views."""

    session_context: SessionContext
    server_manager: ServerInstanceManager
    lifecycle_service: ServerInstanceLifecycleService | None = None
