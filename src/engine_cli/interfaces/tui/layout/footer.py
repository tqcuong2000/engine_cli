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
        if (
            session_coordinator is not None
            and session_coordinator.context is not session_context
        ):
            raise ValueError(
                "Footer session_context must match the coordinator's canonical context."
            )
        self.session_context = (
            session_coordinator.context if session_coordinator is not None else session_context
        )
        self.session_coordinator = session_coordinator
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.session_context.mode is OperatingMode.SERVER:
            yield TerminalFooter()
            return
        yield PromptFooter()
