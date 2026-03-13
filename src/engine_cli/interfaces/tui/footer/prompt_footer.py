from textual.app import ComposeResult
from textual.widget import Widget

from engine_cli.interfaces.tui.main.user_inputs import UserInputs


class PromptFooter(Widget):
    """Prompt-style footer used by conversation modes."""

    def compose(self) -> ComposeResult:
        yield UserInputs(placeholder="Enter your prompt here...", button_label="GENERATE")
