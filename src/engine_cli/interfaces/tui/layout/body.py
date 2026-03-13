from textual.app import ComposeResult
from textual.widget import Widget

from engine_cli.application import SessionContext
from engine_cli.domain import OperatingMode
from engine_cli.interfaces.tui.body import ConversationBody, TerminalBody


class Body(Widget):
    """Mode-aware primary workspace container."""

    def __init__(self, session_context: SessionContext) -> None:
        super().__init__()
        self.session_context = session_context

    def compose(self) -> ComposeResult:
        if self.session_context.mode is OperatingMode.SERVER:
            yield TerminalBody()
            return
        yield ConversationBody(self.session_context.mode)
