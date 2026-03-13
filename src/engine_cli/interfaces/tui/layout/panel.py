from textual.app import ComposeResult
from textual.containers import Container
from textual.events import Click
from textual.widget import Widget
from textual.widgets import Static

from engine_cli.application import SessionContext
from engine_cli.interfaces.tui.panel.tabs import PanelTab
from engine_cli.interfaces.tui.panel import get_panel_tabs


class Panel(Widget):
    """Mode-aware cycling utility panel."""

    def __init__(self, session_context: SessionContext) -> None:
        super().__init__()
        self.session_context = session_context
        self.active_tab_index = 0

    def compose(self) -> ComposeResult:
        self._ensure_valid_index()
        active_tab = self.active_tab
        with Container(classes="header"):
            yield Static("<", classes="nav-btn", id="panel-nav-prev")
            yield Static(active_tab.title, classes="title")
            yield Static(">", classes="nav-btn", id="panel-nav-next")
        yield active_tab.view_factory(self.session_context)

    @property
    def tabs(self) -> tuple[PanelTab, ...]:
        return get_panel_tabs(self.session_context.mode)

    @property
    def active_tab(self) -> PanelTab:
        return self.tabs[self.active_tab_index]

    def previous_tab(self) -> None:
        """Cycle to the previous valid panel tab."""
        self.active_tab_index = (self.active_tab_index - 1) % len(self.tabs)
        self.refresh(recompose=True)

    def next_tab(self) -> None:
        """Cycle to the next valid panel tab."""
        self.active_tab_index = (self.active_tab_index + 1) % len(self.tabs)
        self.refresh(recompose=True)

    def on_click(self, event: Click) -> None:
        """Handle clicks on the panel navigation controls."""
        widget = event.widget
        if widget is None:
            return
        if widget.id == "panel-nav-prev":
            self.previous_tab()
        elif widget.id == "panel-nav-next":
            self.next_tab()

    def _ensure_valid_index(self) -> None:
        if self.active_tab_index >= len(self.tabs):
            self.active_tab_index = 0
