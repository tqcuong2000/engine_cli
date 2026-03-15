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
        if (
            session_coordinator is not None
            and session_coordinator.context is not session_context
        ):
            raise ValueError(
                "Body session_context must match the coordinator's canonical context."
            )
        self._canonical_session_context = (
            session_coordinator.context if session_coordinator is not None else session_context
        )
        self.session_context = self._canonical_session_context
        self.terminal_store = terminal_store
        self.session_coordinator = session_coordinator
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.session_context is not self._canonical_session_context:
            raise ValueError(
                "Body session_context drifted from the canonical session context."
            )
        if self.session_context.mode is OperatingMode.SERVER:
            yield TerminalBody(self.session_context, self.terminal_store)
            return
        yield ConversationBody(self.session_context.mode)
