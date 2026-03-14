from textual.app import ComposeResult
from textual.containers import Container

from engine_cli.application import ServerTerminalStore, SessionContext
from engine_cli.domain import OperatingMode
from engine_cli.interfaces.tui.body import ConversationBody, TerminalBody


class Body(Container):
    """Mode-aware primary workspace container."""

    def __init__(
        self,
        session_context: SessionContext,
        terminal_store: ServerTerminalStore,
    ) -> None:
        super().__init__()
        self.session_context = session_context
        self.terminal_store = terminal_store

    def compose(self) -> ComposeResult:
        if self.session_context.mode is OperatingMode.SERVER:
            yield TerminalBody(self.session_context, self.terminal_store)
            return
        yield ConversationBody(self.session_context.mode)
