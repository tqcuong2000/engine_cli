from engine_cli.application import (
    ServerInstanceManager,
    SessionContext,
    SessionCoordinator,
)
from engine_cli.application.lifecycle import ServerRuntimeStateResolver
from engine_cli.interfaces.tui.components import PanelTabDefinition, TabbedPanelFrame
from engine_cli.interfaces.tui.panel import PanelViewContext, get_panel_tabs
from engine_cli.interfaces.tui.session_aware import SessionAwareRecomposeMixin


class Panel(SessionAwareRecomposeMixin, TabbedPanelFrame):
    """Mode-aware cycling utility panel."""

    def __init__(
        self,
        session_context: SessionContext,
        server_manager: ServerInstanceManager,
        server_runtime_state_resolver: ServerRuntimeStateResolver | None = None,
        session_coordinator: SessionCoordinator | None = None,
    ) -> None:
        self.session_context = session_context
        self.session_coordinator = session_coordinator
        self.server_manager = server_manager
        self.server_runtime_state_resolver = server_runtime_state_resolver
        super().__init__(
            PanelViewContext(
                session_context=session_context,
                server_manager=server_manager,
                server_runtime_state_resolver=server_runtime_state_resolver,
            )
        )

    @property
    def tabs(self) -> tuple[PanelTabDefinition, ...]:
        return get_panel_tabs(self.session_context.mode)
