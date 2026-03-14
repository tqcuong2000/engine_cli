from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget

from engine_cli.interfaces.tui.panel.context import PanelViewContext


class ContextPanelView(Widget):
    """Empty context panel placeholder."""

    def __init__(self, _panel_context: PanelViewContext) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Container(classes="panel-view")
