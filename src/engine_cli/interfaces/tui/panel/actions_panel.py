from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from engine_cli.interfaces.tui.panel.context import PanelViewContext


class ActionsPanelView(Widget):
    """Actions panel providing contextual operations."""

    def __init__(self, panel_context: PanelViewContext) -> None:
        super().__init__()
        self.panel_context = panel_context

    def compose(self) -> ComposeResult:
        yield Static("Actions", classes="panel-label")
