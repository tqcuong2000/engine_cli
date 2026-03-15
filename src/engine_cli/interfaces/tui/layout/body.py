from textual.app import ComposeResult
from textual.containers import Container

from engine_cli.application import ServerTerminalStore, SessionContext, SessionCoordinator
from engine_cli.domain import OperatingMode
from engine_cli.interfaces.tui.body import ConversationBody, TerminalBody
from engine_cli.interfaces.tui.session_aware import SessionAwareRecomposeMixin


class Body(SessionAwareRecomposeMixin, Container):
    """Mode-aware primary workspace container."""

    def __init__(
        self,
        session_context: SessionContext,
        terminal_store: ServerTerminalStore,
        session_coordinator: SessionCoordinator | None = None,
    ) -> None:
        self.session_context = session_context
        self.terminal_store = terminal_store
        self.session_coordinator = session_coordinator
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.session_context.mode is OperatingMode.SERVER:
            yield TerminalBody(self.session_context, self.terminal_store)
            return
        yield ConversationBody(self.session_context.mode)
