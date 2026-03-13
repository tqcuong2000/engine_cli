from textual.widgets import Static, TextArea
from textual.app import ComposeResult
from textual.widget import Widget


class UserInputs(Widget):
    def __init__(self, placeholder: str, button_label: str) -> None:
        super().__init__()
        self.placeholder = placeholder
        self.button_label = button_label

    def compose(self) -> ComposeResult:
        yield TextArea(classes="text-input", placeholder=self.placeholder)
        yield Static(self.button_label, classes="send-btn")
