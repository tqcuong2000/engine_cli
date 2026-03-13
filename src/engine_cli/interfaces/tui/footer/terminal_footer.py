from textual.app import ComposeResult
from textual.widget import Widget

from engine_cli.interfaces.tui.main.user_inputs import UserInputs


class TerminalFooter(Widget):
    """Command-style footer used by server mode."""

    def compose(self) -> ComposeResult:
        yield UserInputs(placeholder="Enter a server command...", button_label="EXECUTE")
