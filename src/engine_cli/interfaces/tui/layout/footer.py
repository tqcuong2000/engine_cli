from textual.app import ComposeResult
from textual.widget import Widget

from engine_cli.application import SessionContext, SessionCoordinator
from engine_cli.domain import OperatingMode
from engine_cli.interfaces.tui.footer import PromptFooter, TerminalFooter
from engine_cli.interfaces.tui.session_aware import SessionAwareRecomposeMixin


class Footer(SessionAwareRecomposeMixin, Widget):
    """Mode-aware footer container."""

    def __init__(
        self,
        session_context: SessionContext,
        session_coordinator: SessionCoordinator | None = None,
    ) -> None:
        super().__init__()
        self.session_context = session_context
        self.session_coordinator = session_coordinator

    def compose(self) -> ComposeResult:
        if self.session_context.mode is OperatingMode.SERVER:
            yield TerminalFooter()
            return
        yield PromptFooter()
