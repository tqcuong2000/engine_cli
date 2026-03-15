from engine_cli.application import (
    ServerInstanceLifecycleService,
    ServerInstanceManager,
    SessionContext,
)
from engine_cli.interfaces.tui.components import PanelTabDefinition, TabbedPanelFrame
from engine_cli.interfaces.tui.panel import PanelViewContext, get_panel_tabs


class Panel(TabbedPanelFrame):
    """Mode-aware cycling utility panel."""

    def __init__(
        self,
        session_context: SessionContext,
        server_manager: ServerInstanceManager,
        lifecycle_service: ServerInstanceLifecycleService | None = None,
    ) -> None:
        self.session_context = session_context
        self.server_manager = server_manager
        self.lifecycle_service = lifecycle_service
        super().__init__(
            PanelViewContext(
                session_context=session_context,
                server_manager=server_manager,
                lifecycle_service=lifecycle_service,
            )
        )

    @property
    def tabs(self) -> tuple[PanelTabDefinition, ...]:
        return get_panel_tabs(self.session_context.mode)
