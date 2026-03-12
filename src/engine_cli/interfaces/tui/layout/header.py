from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import Static


class Header(Widget):
    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Engine CLI")
