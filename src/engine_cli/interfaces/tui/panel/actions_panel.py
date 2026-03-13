from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget


class ActionsPanelView(Widget):
    """Empty actions panel placeholder."""

    def __init__(self, _session_context: object) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Container(classes="panel-view")
