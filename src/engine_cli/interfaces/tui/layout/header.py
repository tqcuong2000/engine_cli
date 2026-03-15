from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Static

from engine_cli.application import SessionContext


class Header(Widget):
    def __init__(self, session_context: SessionContext) -> None:
        super().__init__()
        self.session_context = session_context

    @property
    def badge_text(self) -> str:
        """Return the compact mode label for the current session."""
        return self.session_context.mode.value.upper()

    @property
    def title_text(self) -> str:
        """Return the primary shell title while preserving the current design tone."""
        if self.session_context.active_server_instance_id:
            return f"Engine // {self.session_context.active_server_instance_id}"
        return "Engine // No server selected"

    @property
    def context_text(self) -> str:
        """Return the trailing shell context summary."""
        profile = self.session_context.active_agent_profile_id or "none"
        return f"profile: {profile}"

    def compose(self) -> ComposeResult:
        with Horizontal(classes="header"):
            yield Static(self.badge_text, classes="badge")
            yield Static(self.title_text, classes="title")
            yield Static(self.context_text, classes="context")
